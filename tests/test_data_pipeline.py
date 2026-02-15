"""Smoke tests for data pipeline."""
import tempfile
from pathlib import Path

import pytest

from src.config import load_config
from src.data.ingest import generate_synthetic, load_movielens
from src.data.preprocess import preprocess, time_split
from src.data.pipeline import run_data_pipeline


def test_synthetic_generation() -> None:
    """Synthetic data has expected shape and columns."""
    ratings, movies = generate_synthetic(
        n_users=100, n_movies=50, n_interactions=500, genres=["Action", "Comedy"], seed=42
    )
    assert len(ratings) == 500
    assert len(movies) == 50
    assert "userid" in ratings.columns
    assert "movieid" in ratings.columns
    assert "timestamp" in ratings.columns
    assert "movieid" in movies.columns
    assert "genres" in movies.columns


def test_preprocess_synthetic() -> None:
    """Preprocess produces train/val/test and metadata."""
    ratings, movies = generate_synthetic(
        n_users=200, n_movies=100, n_interactions=1000, genres=["Drama", "Horror"], seed=42
    )
    data = preprocess(
        ratings,
        movies,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        recency_enabled=True,
        half_life_days=90,
    )
    assert len(data["train"]) > 0
    assert len(data["val"]) > 0
    assert len(data["test"]) > 0
    assert "item_genre_matrix" in data
    assert "genre_names" in data
    if "recency_weight" in data["train"].columns:
        assert data["train"]["recency_weight"].min() > 0
        assert data["train"]["recency_weight"].max() <= 1


def test_time_split() -> None:
    """Time split is chronological and non-overlapping."""
    import pandas as pd

    df = pd.DataFrame(
        {"user_id": [1, 2, 3, 4, 5] * 2, "item_id": [1] * 10, "timestamp": list(range(1, 11))}
    )
    train, val, test = time_split(df, 0.6, 0.2, 0.2)
    assert len(train) == 6
    assert len(val) == 2
    assert len(test) == 2
    assert train["timestamp"].max() <= val["timestamp"].min()
    assert val["timestamp"].max() <= test["timestamp"].min()


def test_run_data_pipeline_synthetic() -> None:
    """Full pipeline runs with synthetic source."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = load_config()
        config["paths"]["raw_data"] = str(root / "raw")
        config["paths"]["processed_data"] = str(root / "processed")
        config["data"]["source"] = "synthetic"
        config["data"]["synthetic"] = {
            "n_users": 100,
            "n_movies": 50,
            "n_interactions": 500,
            "genres": ["Action", "Comedy"],
            "seed": 42,
        }
        data = run_data_pipeline(config)
        assert (root / "processed" / "train.parquet").exists()
        assert (root / "processed" / "item_metadata.parquet").exists()
