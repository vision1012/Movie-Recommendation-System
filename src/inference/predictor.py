"""Inference: load models, apply filters, diversity, caching."""
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd

logger = logging.getLogger(__name__)


class RecommendationPredictor:
    """
    Load models and metadata, serve recommendations with exclude-watched,
    diversity (MMR-style), and optional filters.
    """

    def __init__(
        self,
        models_dir: Path,
        processed_dir: Path,
        model_name: str = "hybrid",
        cache_max_size: int = 10000,
        diversity_factor: float = 0.3,
    ):
        self.models_dir = Path(models_dir)
        self.processed_dir = Path(processed_dir)
        self.model_name = model_name
        self.diversity_factor = diversity_factor
        self._model = None
        self._metadata = None
        self._movies = None
        self._item_genre = None
        self._train_user_items = None  # user_id -> set of item_ids
        self._cache: OrderedDict = OrderedDict()
        self._cache_max_size = cache_max_size

    def load(self) -> "RecommendationPredictor":
        """Load model and feature store."""
        self._model = joblib.load(self.models_dir / f"{self.model_name}.joblib")
        meta_path = self.models_dir / "metadata.json"
        if meta_path.exists():
            import json
            with open(meta_path) as f:
                self._metadata = json.load(f)
        self._movies = pd.read_parquet(self.processed_dir / "item_metadata.parquet")
        self._movies = self._movies.set_index("item_id")
        self._item_genre = pd.read_parquet(self.processed_dir / "item_genre_matrix.parquet")
        train = pd.read_parquet(self.processed_dir / "train.parquet")
        self._train_user_items = train.groupby("user_id")["item_id"].apply(set).to_dict()
        logger.info("Loaded model=%s, %d movies", self.model_name, len(self._movies))
        return self

    def _get_user_watched(self, user_id: int) -> set:
        return self._train_user_items.get(user_id, set())

    def _get_item_info(self, item_id: int) -> dict:
        if item_id not in self._movies.index:
            return {"movie_id": item_id, "title": "Unknown", "genres": [], "year": None}
        row = self._movies.loc[item_id]
        genres = row.get("genres", "")
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.replace("|", ",").split(",") if g.strip()]
        return {
            "movie_id": int(item_id),
            "title": str(row.get("title", "Unknown")),
            "genres": genres if isinstance(genres, list) else [],
            "year": int(row["year"]) if "year" in row and pd.notna(row.get("year")) else None,
        }

    def _apply_diversity(self, ids: list, scores: list, k: int) -> tuple[list, list]:
        """Simple MMR-like diversification: penalize items too similar to already selected."""
        if len(ids) <= k or self.diversity_factor <= 0:
            return ids[:k], scores[:k]
        selected_ids = []
        selected_scores = []
        remaining = list(zip(ids, scores))
        while len(selected_ids) < k and remaining:
            best_idx = -1
            best_score = -1e9
            for idx, (iid, sc) in enumerate(remaining):
                # Diversity penalty: reduce score if similar to already selected
                if self._item_genre is not None and iid in self._item_genre.index:
                    sim = 0
                    for sel in selected_ids:
                        if sel in self._item_genre.index:
                            sim += (self._item_genre.loc[iid] * self._item_genre.loc[sel]).sum()
                    penalty = self.diversity_factor * (sim / (len(selected_ids) + 1))
                else:
                    penalty = 0
                adj = sc - penalty
                if adj > best_score:
                    best_score = adj
                    best_idx = idx
            if best_idx >= 0:
                iid, sc = remaining.pop(best_idx)
                selected_ids.append(iid)
                selected_scores.append(sc)
            else:
                break
        return selected_ids, selected_scores

    def recommend(
        self,
        user_id: int,
        k: int = 10,
        exclude_watched: bool = True,
        apply_diversity: bool = True,
        genre_filter: Optional[list[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> list[dict]:
        """
        Return top-K recommendations with metadata and reasons.
        """
        cache_key = (user_id, k, exclude_watched, apply_diversity, tuple(genre_filter or []), year_min, year_max)
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        exclude = self._get_user_watched(user_id) if exclude_watched else set()
        ids, scores = self._model.recommend(user_id, k=k * 2, exclude_ids=exclude)

        ids = list(ids) if hasattr(ids, "tolist") else list(ids)
        scores = list(scores) if hasattr(scores, "tolist") else list(scores)

        # Filters
        filtered = []
        for i, (iid, sc) in enumerate(zip(ids, scores)):
            info = self._get_item_info(iid)
            if genre_filter and info["genres"]:
                if not any(g in info["genres"] for g in genre_filter):
                    continue
            if year_min is not None and info.get("year") is not None and info["year"] < year_min:
                continue
            if year_max is not None and info.get("year") is not None and info["year"] > year_max:
                continue
            filtered.append((iid, sc))
            if len(filtered) >= k:
                break
        ids = [x[0] for x in filtered]
        scores = [x[1] for x in filtered]

        if apply_diversity and self.diversity_factor > 0:
            ids, scores = self._apply_diversity(ids, scores, k)

        # Build response with reasons
        has_als = hasattr(self._model, "similar_items") and callable(getattr(self._model, "similar_items", None))
        results = []
        for iid, sc in zip(ids[:k], scores[:k]):
            info = self._get_item_info(iid)
            reason = "collaborative_filtering" if has_als else "content_based"
            reason_detail = "Based on your viewing history" if user_id in self._train_user_items else "Popular in your preferred genres"
            results.append({
                **info,
                "score": float(sc),
                "reason": reason,
                "reason_detail": reason_detail,
            })

        # Cache
        if len(self._cache) >= self._cache_max_size:
            self._cache.popitem(last=False)
        self._cache[cache_key] = results
        return results

    def similar_items(self, item_id: int, k: int = 10) -> list[dict]:
        """Return similar items (because-you-watched)."""
        if not hasattr(self._model, "similar_items"):
            return []
        ids, scores = self._model.similar_items(item_id, k=k)
        ids = list(ids) if hasattr(ids, "tolist") else list(ids)
        scores = list(scores) if hasattr(scores, "tolist") else list(scores)
        return [
            {**self._get_item_info(iid), "similarity_score": float(sc)}
            for iid, sc in zip(ids, scores)
        ]
