"""Baseline recommenders: popularity, genre-based, item-item."""
from collections import defaultdict
from typing import Optional

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


def build_user_item_matrix(
    train: pd.DataFrame,
    user_col: str = "user_id",
    item_col: str = "item_id",
    weight_col: Optional[str] = "recency_weight",
) -> tuple[csr_matrix, dict, dict, dict, dict]:
    """Build sparse user-item matrix with optional weights. Returns (matrix, user2idx, item2idx, idx2user, idx2item)."""
    users = sorted(train[user_col].unique())
    items = sorted(train[item_col].unique())
    user2idx = {u: i for i, u in enumerate(users)}
    item2idx = {i: j for j, i in enumerate(items)}

    if weight_col and weight_col in train.columns:
        weights = train[weight_col].values
    else:
        weights = np.ones(len(train))

    rows = train[user_col].map(user2idx).values
    cols = train[item_col].map(item2idx).values
    data = weights.astype(np.float32)

    mat = csr_matrix(
        (data, (rows, cols)),
        shape=(len(users), len(items)),
    )
    idx2user = {i: u for u, i in user2idx.items()}
    idx2item = {j: i for i, j in item2idx.items()}
    return mat, user2idx, item2idx, idx2user, idx2item


class PopularityRecommender:
    """Recommend most popular items (by interaction count, optionally recency-weighted)."""

    def __init__(self, min_interactions: int = 5):
        self.min_interactions = min_interactions
        self.item_scores_: Optional[np.ndarray] = None
        self.item_ids_: Optional[np.ndarray] = None

    def fit(self, train: pd.DataFrame, item_col: str = "item_id", weight_col: Optional[str] = None) -> "PopularityRecommender":
        if weight_col and weight_col in train.columns:
            scores = train.groupby(item_col)[weight_col].sum()
        else:
            scores = train.groupby(item_col).size()
        scores = scores[scores >= self.min_interactions].sort_values(ascending=False)
        self.item_ids_ = scores.index.values
        self.item_scores_ = scores.values.astype(np.float32)
        return self

    def recommend(
        self,
        user_id: int,
        k: int = 10,
        exclude_ids: Optional[set] = None,
        item_ids: Optional[np.ndarray] = None,
        scores: Optional[np.ndarray] = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        ids = item_ids if item_ids is not None else self.item_ids_
        sc = scores if scores is not None else self.item_scores_
        if exclude_ids:
            mask = np.array([i not in exclude_ids for i in ids])
            ids = ids[mask]
            sc = sc[mask]
        top_k = min(k, len(ids))
        return ids[:top_k], sc[:top_k]


class GenreBasedRecommender:
    """Content-based: recommend by genre affinity from user history."""

    def __init__(self):
        self.item_genre_matrix_: Optional[pd.DataFrame] = None
        self.user_genre_prefs_: Optional[dict] = None

    def fit(
        self,
        train: pd.DataFrame,
        item_genre_matrix: pd.DataFrame,
        user_col: str = "user_id",
        item_col: str = "item_id",
        weight_col: Optional[str] = "recency_weight",
    ) -> "GenreBasedRecommender":
        self.item_genre_matrix_ = item_genre_matrix
        prefs = defaultdict(lambda: np.zeros(item_genre_matrix.shape[1]))
        for _, row in train.iterrows():
            u = row[user_col]
            i = row[item_col]
            w = row.get(weight_col, 1.0) if weight_col and weight_col in train.columns else 1.0
            if i in item_genre_matrix.index:
                vec = item_genre_matrix.loc[i].values
                prefs[u] += w * vec
        self.user_genre_prefs_ = {u: v / (v.sum() + 1e-9) for u, v in prefs.items()}
        return self

    def recommend(
        self,
        user_id: int,
        k: int = 10,
        exclude_ids: Optional[set] = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        if user_id not in self.user_genre_prefs_:
            return np.array([]), np.array([])
        prefs = self.user_genre_prefs_[user_id]
        scores = self.item_genre_matrix_.values @ prefs
        ids = self.item_genre_matrix_.index.values
        if exclude_ids:
            mask = np.array([i not in exclude_ids for i in ids])
            ids = ids[mask]
            scores = scores[mask]
        top_idx = np.argsort(-scores)[:k]
        return ids[top_idx], scores[top_idx]


class ItemItemRecommender:
    """Item-item collaborative filtering using cosine similarity."""

    def __init__(self, n_similar: int = 50, min_similarity: float = 0.0):
        self.n_similar = n_similar
        self.min_similarity = min_similarity
        self.item_sim_: Optional[np.ndarray] = None
        self.item2idx_: Optional[dict] = None
        self.idx2item_: Optional[dict] = None
        self.user2idx_: Optional[dict] = None
        self.user_item_: Optional[csr_matrix] = None

    def fit(self, train: pd.DataFrame, user_col: str = "user_id", item_col: str = "item_id") -> "ItemItemRecommender":
        mat, user2idx, item2idx, _, _ = build_user_item_matrix(train, user_col, item_col, weight_col=None)
        self.user_item_ = mat
        self.user2idx_ = user2idx
        self.item2idx_ = item2idx
        self.idx2item_ = {j: i for i, j in item2idx.items()}
        # Item-item similarity: items x items (cosine normalization)
        item_counts = np.array((mat.T.multiply(mat.T)).sum(axis=1)).flatten()
        item_counts[item_counts == 0] = 1
        scale = 1.0 / np.sqrt(item_counts)
        X = mat.T.astype(np.float64)
        X = X.multiply(scale.reshape(-1, 1))  # scale each row
        sim = (X @ X.T).toarray()
        np.fill_diagonal(sim, 0)
        self.item_sim_ = np.clip(sim, self.min_similarity, None)
        return self

    def recommend(
        self,
        user_id: int,
        k: int = 10,
        exclude_ids: Optional[set] = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        if self.user2idx_ is None or user_id not in self.user2idx_:
            return np.array([]), np.array([])
        u_idx = self.user2idx_[user_id]
        user_vec = self.user_item_[u_idx].toarray().flatten()
        # Score = sum over (similarity to item j * user engagement with item i)
        scores = self.item_sim_.T @ user_vec  # shape (n_items,)
        ids = np.array([self.idx2item_[j] for j in range(len(scores))])
        if exclude_ids:
            mask = np.array([i not in exclude_ids for i in ids])
            ids = ids[mask]
            scores = scores[mask]
        top_idx = np.argsort(-scores)[:k]
        return ids[top_idx], scores[top_idx]
