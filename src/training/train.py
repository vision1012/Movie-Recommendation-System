"""Training pipeline: fit all models and save artifacts."""
import json
import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.config import load_config
from src.models.baselines import GenreBasedRecommender, ItemItemRecommender, PopularityRecommender
from src.models.hybrid import HybridRecommender
from src.models.implicit_als import ImplicitALSRecommender

logger = logging.getLogger(__name__)


def load_processed_data(processed_dir: Path) -> dict:
    """Load preprocessed train, val, test, metadata."""
    train = pd.read_parquet(processed_dir / "train.parquet")
    val = pd.read_parquet(processed_dir / "val.parquet")
    test = pd.read_parquet(processed_dir / "test.parquet")
    movies = pd.read_parquet(processed_dir / "item_metadata.parquet")
    item_genre = pd.read_parquet(processed_dir / "item_genre_matrix.parquet")
    return {"train": train, "val": val, "test": test, "movies": movies, "item_genre_matrix": item_genre}


def train_models(config: dict[str, Any], data: dict) -> dict:
    """Train all models and return them."""
    models = {}
    cfg = config.get("models", {})

    # Popularity
    pop = PopularityRecommender(min_interactions=cfg.get("popularity", {}).get("min_interactions", 5))
    pop.fit(data["train"], weight_col="recency_weight" if "recency_weight" in data["train"].columns else None)
    models["popularity"] = pop

    # Genre-based
    genre = GenreBasedRecommender()
    genre.fit(
        data["train"],
        data["item_genre_matrix"],
        weight_col="recency_weight" if "recency_weight" in data["train"].columns else None,
    )
    models["genre"] = genre

    # Item-item
    ii_cfg = cfg.get("item_item", {})
    item_item = ItemItemRecommender(
        n_similar=ii_cfg.get("n_similar", 50),
        min_similarity=ii_cfg.get("min_similarity", 0.0),
    )
    item_item.fit(data["train"])
    models["item_item"] = item_item

    # Implicit ALS
    try:
        als_cfg = cfg.get("implicit_als", {})
        als = ImplicitALSRecommender(
            factors=als_cfg.get("factors", 64),
            regularization=als_cfg.get("regularization", 0.01),
            iterations=als_cfg.get("iterations", 15),
            random_state=config.get("project", {}).get("seed"),
        )
        als.fit(data["train"], weight_col="recency_weight" if "recency_weight" in data["train"].columns else None)
        models["implicit_als"] = als
    except ImportError:
        logger.warning("implicit not installed, skipping ImplicitALS")

    # Hybrid
    hyb_cfg = cfg.get("hybrid", {})
    hybrid = HybridRecommender(
        cf_weight=hyb_cfg.get("cf_weight", 0.7),
        content_weight=hyb_cfg.get("content_weight", 0.3),
    )
    als_params = None
    if "implicit_als" in models:
        als_params = cfg.get("implicit_als", {})
    hybrid.fit(
        data["train"],
        data["item_genre_matrix"],
        weight_col="recency_weight" if "recency_weight" in data["train"].columns else None,
        als_params=als_params,
    )
    models["hybrid"] = hybrid

    return models


def save_artifacts(models_dir: Path, models: dict, metadata: dict) -> None:
    """Save model artifacts and metadata."""
    models_dir.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        path = models_dir / f"{name}.joblib"
        joblib.dump(model, path)
        logger.info("Saved %s to %s", name, path)
    with open(models_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)


def run_training(config: dict[str, Any] | None = None) -> dict:
    """Run full training pipeline."""
    if config is None:
        config = load_config()
    root = Path(__file__).resolve().parent.parent.parent
    processed_dir = Path(config["paths"]["processed_data"])
    if not processed_dir.is_absolute():
        processed_dir = root / processed_dir
    models_dir = Path(config["paths"]["models_dir"])
    if not models_dir.is_absolute():
        models_dir = root / models_dir

    data = load_processed_data(processed_dir)
    models = train_models(config, data)
    metadata = {
        "n_users": int(data["train"]["user_id"].nunique()),
        "n_items": int(data["train"]["item_id"].nunique()),
        "n_interactions": len(data["train"]),
    }
    save_artifacts(models_dir, models, metadata)
    return models
