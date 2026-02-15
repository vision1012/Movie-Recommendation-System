"""Data ingestion: MovieLens and synthetic generator."""
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd


def load_movielens(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    """
    Load MovieLens format data.
    Expects: ratings.csv or rating.csv; movies.csv or movie.csv; tags.csv or tag.csv (optional).
    MovieLens columns: userId, movieId, rating, timestamp (ratings); movieId, title, genres (movies).
    """
    ratings_path = data_dir / "ratings.csv" if (data_dir / "ratings.csv").exists() else data_dir / "rating.csv"
    movies_path = data_dir / "movies.csv" if (data_dir / "movies.csv").exists() else data_dir / "movie.csv"
    tags_path = data_dir / "tags.csv" if (data_dir / "tags.csv").exists() else data_dir / "tag.csv"

    if not ratings_path.exists():
        raise FileNotFoundError(
            f"ratings.csv or rating.csv not found in {data_dir}. "
            "Download from https://grouplens.org/datasets/movielens/ or use synthetic data."
        )
    if not movies_path.exists():
        raise FileNotFoundError(f"movies.csv or movie.csv not found in {data_dir}")

    ratings = pd.read_csv(ratings_path)
    # Normalize column names to lowercase
    ratings.columns = [c.lower() for c in ratings.columns]
    # Handle movieid vs movieId
    col_map = {c: c.lower().replace(" ", "_") for c in ratings.columns}
    ratings = ratings.rename(columns=col_map)

    movies = pd.read_csv(movies_path)
    movies.columns = [c.lower().replace(" ", "_") for c in movies.columns]

    tags = None
    if tags_path.exists():
        tags = pd.read_csv(tags_path)
        tags.columns = [c.lower().replace(" ", "_") for c in tags.columns]

    return ratings, movies, tags


def generate_synthetic(
    n_users: int,
    n_movies: int,
    n_interactions: int,
    genres: list[str],
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate realistic synthetic ratings and movie metadata.
    Uses genre affinity to create coherent preferences.
    """
    rng = np.random.default_rng(seed)

    # Assign genres to movies (multi-genre)
    n_genres = len(genres)
    movie_genres = []
    for m in range(n_movies):
        n_g = rng.integers(1, 4)  # 1-3 genres per movie
        g_idx = rng.choice(n_genres, size=n_g, replace=False)
        movie_genres.append(",".join(genres[i] for i in sorted(g_idx)))
    movies = pd.DataFrame(
        {"movieid": np.arange(1, n_movies + 1), "title": [f"Movie {i}" for i in range(1, n_movies + 1)], "genres": movie_genres}
    )

    # User genre preferences (latent)
    user_prefs = rng.uniform(0, 1, size=(n_users, n_genres))
    user_prefs = user_prefs / user_prefs.sum(axis=1, keepdims=True)

    # Movie-genre matrix
    movie_genre_mat = np.zeros((n_movies, n_genres))
    for m, gs in enumerate(movie_genres):
        for g in gs.split(","):
            g = g.strip()
            if g in genres:
                movie_genre_mat[m, genres.index(g)] = 1.0

    # Sample unique (user, movie) pairs
    max_pairs = n_users * n_movies
    n_sample = min(n_interactions, max_pairs)
    all_pairs = np.arange(max_pairs)
    rng.shuffle(all_pairs)
    pairs = all_pairs[:n_sample]
    user_ids = pairs // n_movies
    movie_ids = pairs % n_movies

    # Timestamps: spread over ~2 years
    base_ts = 1_300_000_000  # ~2011
    span = 2 * 365 * 24 * 3600
    timestamps = (base_ts + rng.uniform(0, span, size=n_sample)).astype(int)

    ratings = pd.DataFrame(
        {"userid": user_ids, "movieid": movie_ids, "rating": 1.0, "timestamp": timestamps}
    )
    # MovieLens uses 1-indexed IDs
    ratings["userid"] = ratings["userid"] + 1
    ratings["movieid"] = ratings["movieid"] + 1
    movies["movieid"] = movies["movieid"]

    return ratings, movies


def ingest(
    source: Literal["movielens", "synthetic"],
    data_dir: Path,
    synthetic_params: dict | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ingest data from configured source.
    Returns (ratings, movies).
    """
    if source == "movielens":
        ratings, movies, _ = load_movielens(data_dir)
        return ratings, movies
    elif source == "synthetic":
        params = synthetic_params or {}
        ratings, movies = generate_synthetic(
            n_users=params.get("n_users", 5000),
            n_movies=params.get("n_movies", 2000),
            n_interactions=params.get("n_interactions", 100_000),
            genres=params.get("genres", ["Action", "Comedy", "Drama", "Horror", "Sci-Fi"]),
            seed=params.get("seed", 42),
        )
        return ratings, movies
    else:
        raise ValueError(f"Unknown source: {source}")
