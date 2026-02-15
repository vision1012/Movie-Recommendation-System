"""Preprocessing: time split, recency weighting, feature preparation."""
from pathlib import Path

import numpy as np
import pandas as pd


def _ensure_numeric_timestamp(ratings: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Convert datetime/string timestamps to unix seconds for downstream use."""
    r = ratings.copy()
    if timestamp_col not in r.columns:
        return r
    ts = r[timestamp_col]
    # Check if already numeric (int/float)
    if pd.api.types.is_numeric_dtype(ts):
        # If large int (unix ms), convert to seconds
        if ts.max() > 1e12:
            r[timestamp_col] = ts // 1000
        return r
    r[timestamp_col] = pd.to_datetime(ts).astype("int64") // 10**9
    return r


def standardize_columns(ratings: pd.DataFrame, movies: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Standardize column names to user_id, item_id, timestamp, rating."""
    r = ratings.copy()
    m = movies.copy()
    col_map_r = {"userid": "user_id", "userId": "user_id", "movieid": "item_id", "movieId": "item_id"}
    col_map_r.update({"timestamp": "timestamp", "rating": "rating"})
    for old, new in col_map_r.items():
        if old in r.columns and new not in r.columns:
            r = r.rename(columns={old: new})
    if "item_id" not in r.columns and "movieid" in r.columns:
        r = r.rename(columns={"movieid": "item_id"})
    if "user_id" not in r.columns and "userid" in r.columns:
        r = r.rename(columns={"userid": "user_id"})
    col_map_m = {"movieid": "item_id", "movieId": "item_id"}
    for old, new in col_map_m.items():
        if old in m.columns:
            m = m.rename(columns={old: new})
    return r, m


def time_split(
    ratings: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    time_col: str = "timestamp",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split by time (chronological).
    Assumes timestamp column exists and is numeric (unix).
    """
    r = ratings.copy()
    if time_col not in r.columns:
        raise ValueError(f"Column {time_col} not found")
    r = r.sort_values(time_col).reset_index(drop=True)
    n = len(r)
    t1 = int(n * train_ratio)
    t2 = int(n * (train_ratio + val_ratio))
    train = r.iloc[:t1]
    val = r.iloc[t1:t2]
    test = r.iloc[t2:]
    return train, val, test


def add_recency_weight(
    ratings: pd.DataFrame,
    timestamp_col: str = "timestamp",
    half_life_days: float = 90,
) -> pd.DataFrame:
    """
    Add recency weight: recent interactions count more.
    weight = 0.5 ^ (days_since / half_life_days)
    """
    r = ratings.copy()
    max_ts = r[timestamp_col].max()
    # Convert to days (assume unix seconds)
    r["days_ago"] = (max_ts - r[timestamp_col]) / 86400
    r["recency_weight"] = np.power(0.5, r["days_ago"] / half_life_days)
    return r


def prepare_item_metadata(movies: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare item metadata: extract genres, year from title if present.
    MovieLens title format: "Title (Year)"
    """
    m = movies.copy()
    if "title" in m.columns:
        # Extract year from "Title (Year)"
        m["year"] = m["title"].str.extract(r"\((\d{4})\)").astype("Int64")
    if "genres" in m.columns:
        m["genres_list"] = m["genres"].str.split("|").fillna("").apply(lambda x: [g.strip() for g in x if g])
    return m


def build_item_genre_matrix(movies: pd.DataFrame, genre_col: str = "genres") -> tuple[pd.DataFrame, list[str]]:
    """
    Build item x genre matrix and return (item_ids, genre_names).
    """
    all_genres = set()
    for gs in movies[genre_col].dropna():
        for g in str(gs).replace("|", ",").split(","):
            g = g.strip()
            if g and g != "(no genres listed)":
                all_genres.add(g)
    all_genres = sorted(all_genres)
    n_genres = len(all_genres)
    item_ids = movies["item_id"].values
    mat = np.zeros((len(item_ids), n_genres))
    for i, row in movies.iterrows():
        gs = row.get(genre_col, "")
        if pd.isna(gs):
            continue
        for g in str(gs).replace("|", ",").split(","):
            g = g.strip()
            if g in all_genres:
                mat[i, all_genres.index(g)] = 1.0
    df = pd.DataFrame(mat, index=item_ids, columns=all_genres)
    return df, all_genres


def preprocess(
    ratings: pd.DataFrame,
    movies: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    recency_enabled: bool = True,
    half_life_days: float = 90,
) -> dict:
    """
    Full preprocessing pipeline.
    Returns dict with train, val, test, movies, item_genre_matrix, genre_names.
    """
    r, m = standardize_columns(ratings, movies)
    r = _ensure_numeric_timestamp(r)
    m = prepare_item_metadata(m)
    train, val, test = time_split(r, train_ratio, val_ratio, test_ratio)
    if recency_enabled:
        train = add_recency_weight(train, half_life_days=half_life_days)
    item_genre, genre_names = build_item_genre_matrix(m, "genres")
    return {
        "train": train,
        "val": val,
        "test": test,
        "movies": m,
        "item_genre_matrix": item_genre,
        "genre_names": genre_names,
    }


def save_processed(output_dir: Path, data: dict) -> None:
    """Save processed data to parquet and CSV."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data["train"].to_parquet(output_dir / "train.parquet", index=False)
    data["val"].to_parquet(output_dir / "val.parquet", index=False)
    data["test"].to_parquet(output_dir / "test.parquet", index=False)
    data["movies"].to_parquet(output_dir / "item_metadata.parquet", index=False)
    data["item_genre_matrix"].to_parquet(output_dir / "item_genre_matrix.parquet")
