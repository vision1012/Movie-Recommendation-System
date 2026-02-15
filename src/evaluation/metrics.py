"""Ranking metrics: NDCG@K, Recall@K, Precision@K."""
import numpy as np


def dcg_at_k(relevance: np.ndarray, k: int) -> float:
    """Discounted Cumulative Gain at K. relevance: binary or graded (0/1 for binary)."""
    rel = np.asarray(relevance)[:k]
    if len(rel) == 0:
        return 0.0
    gains = (2**rel - 1) / np.log2(np.arange(2, len(rel) + 2))
    return float(np.sum(gains))


def ndcg_at_k(relevance: np.ndarray, k: int) -> float:
    """Normalized DCG at K. relevance: binary relevance (1=relevant, 0=not)."""
    dcg = dcg_at_k(relevance, k)
    ideal = np.sort(relevance)[::-1][:k]
    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg


def recall_at_k(relevant: set, recommended: np.ndarray, k: int) -> float:
    """Recall@K = |relevant ∩ recommended[:k]| / |relevant|."""
    if len(relevant) == 0:
        return 0.0
    rec_set = set(recommended[:k])
    hits = len(relevant & rec_set)
    return hits / len(relevant)


def precision_at_k(relevant: set, recommended: np.ndarray, k: int) -> float:
    """Precision@K = |relevant ∩ recommended[:k]| / k."""
    if k == 0:
        return 0.0
    rec_set = set(recommended[:k])
    hits = len(relevant & rec_set)
    return hits / k


def compute_metrics_for_user(
    recommended: np.ndarray,
    relevant: set,
    k: int = 10,
) -> dict[str, float]:
    """Compute NDCG, Recall, Precision for a single user."""
    rel_array = np.array([1 if i in relevant else 0 for i in recommended[:k]])
    return {
        f"ndcg@{k}": ndcg_at_k(rel_array, k),
        f"recall@{k}": recall_at_k(relevant, recommended, k),
        f"precision@{k}": precision_at_k(relevant, recommended, k),
    }


def compute_metrics_all_users(
    recommendations: dict,  # user_id -> list of recommended item ids
    ground_truth: dict,     # user_id -> set of relevant item ids
    k: int = 10,
) -> dict[str, float]:
    """Average NDCG, Recall, Precision across users."""
    ndcg_sum, recall_sum, prec_sum, n = 0.0, 0.0, 0.0, 0
    for uid, rec in recommendations.items():
        rel = ground_truth.get(uid, set())
        if len(rel) == 0:
            continue
        rec_arr = np.array(rec) if not isinstance(rec, np.ndarray) else rec
        m = compute_metrics_for_user(rec_arr, rel, k)
        ndcg_sum += m[f"ndcg@{k}"]
        recall_sum += m[f"recall@{k}"]
        prec_sum += m[f"precision@{k}"]
        n += 1
    if n == 0:
        return {f"ndcg@{k}": 0, f"recall@{k}": 0, f"precision@{k}": 0}
    return {
        f"ndcg@{k}": ndcg_sum / n,
        f"recall@{k}": recall_sum / n,
        f"precision@{k}": prec_sum / n,
    }
