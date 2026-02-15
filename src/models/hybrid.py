"""Hybrid recommender: blend CF + content-based for cold start."""
from typing import Optional

import numpy as np

from src.models.baselines import GenreBasedRecommender, PopularityRecommender
from src.models.implicit_als import ImplicitALSRecommender


class HybridRecommender:
    """Blend implicit ALS (CF) with genre-based (content) for cold-start support."""

    def __init__(self, cf_weight: float = 0.7, content_weight: float = 0.3):
        self.cf_weight = cf_weight
        self.content_weight = content_weight
        self.cf_model_: Optional[ImplicitALSRecommender] = None
        self.content_model_: Optional[GenreBasedRecommender] = None
        self.popularity_: Optional[PopularityRecommender] = None

    def fit(
        self,
        train,
        item_genre_matrix,
        user_col: str = "user_id",
        item_col: str = "item_id",
        weight_col: Optional[str] = "recency_weight",
        als_params: Optional[dict] = None,
    ) -> "HybridRecommender":
        self.popularity_ = PopularityRecommender().fit(train, item_col=item_col, weight_col=weight_col)
        self.content_model_ = GenreBasedRecommender().fit(
            train, item_genre_matrix, user_col, item_col, weight_col
        )
        try:
            params = als_params or {}
            self.cf_model_ = ImplicitALSRecommender(**params).fit(
                train, user_col, item_col, weight_col
            )
        except ImportError:
            self.cf_model_ = None
        return self

    def recommend(
        self,
        user_id: int,
        k: int = 10,
        exclude_ids: Optional[set] = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        exclude_ids = exclude_ids or set()

        # Get CF scores
        cf_ids, cf_scores = np.array([]), np.array([])
        if self.cf_model_ is not None:
            cf_ids, cf_scores = self.cf_model_.recommend(user_id, k=k * 2, exclude_ids=exclude_ids)

        # Get content scores
        content_ids, content_scores = self.content_model_.recommend(
            user_id, k=k * 2, exclude_ids=exclude_ids
        )

        # Cold start: use content + popularity
        if len(cf_ids) == 0:
            if len(content_ids) > 0:
                return content_ids[:k], content_scores[:k]
            return self.popularity_.recommend(user_id, k, exclude_ids, *self._popularity_arrays())

        # Blend: normalize and combine
        all_ids = np.unique(np.concatenate([cf_ids, content_ids]))
        scores = np.zeros(len(all_ids))

        cf_map = dict(zip(cf_ids, cf_scores)) if len(cf_ids) > 0 else {}
        content_map = dict(zip(content_ids, content_scores)) if len(content_ids) > 0 else {}

        cf_max = max(cf_map.values()) if cf_map else 1
        content_max = max(content_map.values()) if content_map else 1

        for i, item_id in enumerate(all_ids):
            cf_s = cf_map.get(item_id, 0) / (cf_max or 1)
            content_s = content_map.get(item_id, 0) / (content_max or 1)
            scores[i] = self.cf_weight * cf_s + self.content_weight * content_s

        top_idx = np.argsort(-scores)[:k]
        return all_ids[top_idx], scores[top_idx]

    def _popularity_arrays(self):
        return (self.popularity_.item_ids_, self.popularity_.item_scores_)

    def similar_items(self, item_id: int, k: int = 10) -> tuple:
        """Delegate to CF model for item-to-item similarity."""
        import numpy as np
        if self.cf_model_ is not None and hasattr(self.cf_model_, "similar_items"):
            return self.cf_model_.similar_items(item_id, k)
        return np.array([]), np.array([])
