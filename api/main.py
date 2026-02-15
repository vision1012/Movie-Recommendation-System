"""FastAPI recommendation service."""
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.inference.predictor import RecommendationPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Movie Recommendation API", version="0.1.0")

_predictor: Optional[RecommendationPredictor] = None


def get_predictor() -> RecommendationPredictor:
    global _predictor
    if _predictor is None:
        config = load_config()
        root = Path(__file__).resolve().parent.parent
        models_dir = Path(config["paths"]["models_dir"])
        processed_dir = Path(config["paths"]["processed_data"])
        if not models_dir.is_absolute():
            models_dir = root / models_dir
        if not processed_dir.is_absolute():
            processed_dir = root / processed_dir
        inf_cfg = config.get("inference", {})
        _predictor = RecommendationPredictor(
            models_dir=models_dir,
            processed_dir=processed_dir,
            model_name=config.get("inference", {}).get("model_name", "hybrid") or "hybrid",
            cache_max_size=inf_cfg.get("cache_max_size", 10000),
            diversity_factor=inf_cfg.get("diversity_factor", 0.3),
        )
        _predictor.load()
    return _predictor


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


@app.get("/recommend")
def recommend(
    user_id: int = Query(..., description="User ID"),
    k: int = Query(10, ge=1, le=100, description="Number of recommendations"),
    exclude_watched: bool = Query(True, description="Exclude already watched"),
    genre_filter: Optional[str] = Query(None, description="Comma-separated genres"),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
):
    """
    Get personalized recommendations for a user.
    Returns movie IDs + metadata + ranking reasons.
    """
    pred = get_predictor()
    genres = [g.strip() for g in genre_filter.split(",")] if genre_filter else None
    recs = pred.recommend(
        user_id=user_id,
        k=k,
        exclude_watched=exclude_watched,
        apply_diversity=True,
        genre_filter=genres,
        year_min=year_min,
        year_max=year_max,
    )
    return {"user_id": str(user_id), "recommendations": recs}


@app.get("/similar")
def similar(
    item_id: int = Query(..., description="Movie ID for similarity"),
    k: int = Query(10, ge=1, le=100, description="Number of similar items"),
):
    """Get similar items (because-you-watched)."""
    pred = get_predictor()
    recs = pred.similar_items(item_id, k=k)
    return {"item_id": str(item_id), "similar_items": recs}


if __name__ == "__main__":
    import uvicorn
    config = load_config()
    api_cfg = config.get("api", {})
    uvicorn.run(app, host=api_cfg.get("host", "0.0.0.0"), port=api_cfg.get("port", 8000))
