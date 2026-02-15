"""Data pipeline: ingest -> preprocess -> save."""
import logging
from pathlib import Path
from typing import Any

from pathlib import Path

from src.config import load_config
from src.data.ingest import ingest
from src.data.preprocess import preprocess, save_processed

logger = logging.getLogger(__name__)


def run_data_pipeline(config: dict[str, Any] | None = None) -> dict:
    """
    Run full data pipeline: ingest, preprocess, save.
    Returns the preprocessed data dict.
    """
    if config is None:
        config = load_config()

    data_source = config["data"]["source"]
    root = Path(__file__).resolve().parent.parent.parent  # project root
    raw_dir = Path(config["paths"]["raw_data"])
    if not raw_dir.is_absolute():
        raw_dir = root / raw_dir
    processed_dir = Path(config["paths"]["processed_data"])
    if not processed_dir.is_absolute():
        processed_dir = root / processed_dir

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Ingesting data from source=%s", data_source)
    if data_source == "movielens":
        ratings, movies = ingest("movielens", raw_dir)
    else:
        syn = config["data"].get("synthetic", {})
        ratings, movies = ingest(
            "synthetic",
            raw_dir,
            synthetic_params={
                "n_users": syn.get("n_users", 5000),
                "n_movies": syn.get("n_movies", 2000),
                "n_interactions": syn.get("n_interactions", 100_000),
                "genres": syn.get("genres", ["Action", "Comedy", "Drama", "Horror", "Sci-Fi"]),
                "seed": config["project"].get("seed", 42),
            },
        )

    logger.info("Ratings shape=%s, movies shape=%s", ratings.shape, movies.shape)

    # Optional subsampling for large datasets
    subsample_cfg = config.get("data_subsample", {})
    if subsample_cfg.get("enabled") and subsample_cfg.get("max_interactions"):
        max_n = subsample_cfg["max_interactions"]
        if len(ratings) > max_n:
            seed = subsample_cfg.get("seed", config["project"].get("seed", 42))
            ratings = ratings.sample(n=max_n, random_state=seed)
            logger.info("Subsampled to %d interactions", len(ratings))

    split = config["split"]
    rec = config.get("recency", {})

    data = preprocess(
        ratings,
        movies,
        train_ratio=split.get("train_ratio", 0.7),
        val_ratio=split.get("val_ratio", 0.15),
        test_ratio=split.get("test_ratio", 0.15),
        recency_enabled=rec.get("enabled", True),
        half_life_days=rec.get("decay_half_life_days", 90),
    )

    save_processed(processed_dir, data)
    logger.info("Saved processed data to %s", processed_dir)
    return data
