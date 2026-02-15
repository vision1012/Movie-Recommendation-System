"""Implicit ALS (Alternating Least Squares) for collaborative filtering."""
from typing import Optional

import numpy as np
from scipy.sparse import csr_matrix

try:
    from implicit.als import AlternatingLeastSquares
    from implicit.utils import item_user_matrix_from_user_item
    IMPLICIT_AVAILABLE = True
except ImportError:
    IMPLICIT_AVAILABLE = False


def build_implicit_matrix(
    train,
    user_col: str = "user_id",
    item_col: str = "item_id",
    weight_col: Optional[str] = "recency_weight",
) -> tuple[csr_matrix, dict, dict, dict, dict]:
    """
    Build user-item matrix for implicit. Returns (user_item, user2idx, item2idx, idx2user, idx2item).
    """
    users = sorted(train[user_col].unique())
    items = sorted(train[item_col].unique())
    user2idx = {u: i for i, u in enumerate(users)}
    item2idx = {i: j for j, i in enumerate(items)}
    idx2user = {i: u for u, i in user2idx.items()}
    idx2item = {j: i for i, j in item2idx.items()}

    if weight_col and weight_col in train.columns:
        weights = train[weight_col].values.astype(np.float32)
    else:
        weights = np.ones(len(train), dtype=np.float32)

    rows = train[user_col].map(user2idx).values
    cols = train[item_col].map(item2idx).values
    mat = csr_matrix((weights, (rows, cols)), shape=(len(users), len(items)))
    return mat, user2idx, item2idx, idx2user, idx2item


class ImplicitALSRecommender:
    """Wrapper around implicit.als.AlternatingLeastSquares."""

    def __init__(
        self,
        factors: int = 64,
        regularization: float = 0.01,
        iterations: int = 15,
        random_state: Optional[int] = None,
    ):
        if not IMPLICIT_AVAILABLE:
            raise ImportError("implicit library required. Install with: pip install implicit")
        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations
        self.random_state = random_state
        self.model_: Optional[AlternatingLeastSquares] = None
        self.user_item_: Optional[csr_matrix] = None
        self.user2idx_: Optional[dict] = None
        self.item2idx_: Optional[dict] = None
        self.idx2user_: Optional[dict] = None
        self.idx2item_: Optional[dict] = None

    def fit(
        self,
        train,
        user_col: str = "user_id",
        item_col: str = "item_id",
        weight_col: Optional[str] = "recency_weight",
    ) -> "ImplicitALSRecommender":
        mat, user2idx, item2idx, idx2user, idx2item = build_implicit_matrix(
            train, user_col, item_col, weight_col
        )
        self.user_item_ = mat
        self.user2idx_ = user2idx
        self.item2idx_ = item2idx
        self.idx2user_ = idx2user
        self.idx2item_ = idx2item

        # implicit expects item_user (items x users)
        item_user = item_user_matrix_from_user_item(mat)

        self.model_ = AlternatingLeastSquares(
            factors=self.factors,
            regularization=self.regularization,
            iterations=self.iterations,
            random_state=self.random_state,
        )
        self.model_.fit(item_user)
        return self

    def recommend(
        self,
        user_id: int,
        k: int = 10,
        exclude_ids: Optional[set] = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        if self.model_ is None or user_id not in self.user2idx_:
            return np.array([]), np.array([])
        u_idx = self.user2idx_[user_id]
        ids, scores = self.model_.recommend(
            u_idx,
            self.user_item_[u_idx],
            N=k + (len(exclude_ids) if exclude_ids else 0),
            filter_already_liked_items=True,
        )
        rec_ids = np.array([self.idx2item_[i] for i in ids])
        if exclude_ids:
            mask = np.array([i not in exclude_ids for i in rec_ids])
            rec_ids = rec_ids[mask][:k]
            scores = scores[mask][:k]
        else:
            rec_ids = rec_ids[:k]
            scores = scores[:k]
        return rec_ids, scores.astype(np.float64)

    def similar_items(self, item_id: int, k: int = 10) -> tuple[np.ndarray, np.ndarray]:
        """Return similar items for a given item."""
        if self.model_ is None or item_id not in self.item2idx_:
            return np.array([]), np.array([])
        i_idx = self.item2idx_[item_id]
        ids, scores = self.model_.similar_items(i_idx, N=k)
        rec_ids = np.array([self.idx2item_[i] for i in ids])
        return rec_ids, scores.astype(np.float64)
