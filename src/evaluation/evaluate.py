"""Evaluate models on test set."""
import json
import logging
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.evaluation.metrics import compute_metrics_all_users

logger = logging.getLogger(__name__)


def get_ground_truth(test: pd.DataFrame, user_col: str = "user_id", item_col: str = "item_id") -> dict:
    """Build user -> set of relevant items from test set."""
    gt = {}
    for _, row in test.iterrows():
        u = row[user_col]
        i = row[item_col]
        gt.setdefault(u, set()).add(i)
    return gt


def evaluate_model(
    model,
    test_users: list,
    ground_truth: dict,
    train: pd.DataFrame,
    k: int = 10,
    user_col: str = "user_id",
    item_col: str = "item_id",
) -> tuple[dict[str, float], dict]:
    """
    Evaluate a model. Returns (metrics, per_user_recs).
    Model must have recommend(user_id, k, exclude_ids) -> (ids, scores).
    """
    recommendations = {}
    for uid in test_users:
        exclude = set(train[train[user_col] == uid][item_col].tolist())
        ids, _ = model.recommend(uid, k=k, exclude_ids=exclude)
        recommendations[uid] = ids.tolist() if hasattr(ids, "tolist") else list(ids)

    metrics = compute_metrics_all_users(recommendations, ground_truth, k=k)
    return metrics, recommendations


def run_evaluation(
    config: dict[str, Any] | None = None,
    models: dict | None = None,
    models_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Run evaluation on test set. Load models from disk if not provided.
    Returns evaluation report dict.
    """
    import joblib

    if config is None:
        from src.config import load_config
        config = load_config()

    root = Path(__file__).resolve().parent.parent.parent
    processed_dir = Path(config["paths"]["processed_data"])
    if not processed_dir.is_absolute():
        processed_dir = root / processed_dir
    models_dir = models_dir or Path(config["paths"]["models_dir"])
    if not models_dir.is_absolute():
        models_dir = root / models_dir
    reports_dir = Path(config["paths"]["reports_dir"])
    if not reports_dir.is_absolute():
        reports_dir = root / reports_dir

    train = pd.read_parquet(processed_dir / "train.parquet")
    test = pd.read_parquet(processed_dir / "test.parquet")
    ground_truth = get_ground_truth(test)
    test_users = [u for u in test["user_id"].unique() if u in ground_truth and len(ground_truth[u]) > 0]
    k = config.get("inference", {}).get("default_k", 10)

    if models is None:
        models = {}
        for name in ["popularity", "genre", "item_item", "implicit_als", "hybrid"]:
            path = models_dir / f"{name}.joblib"
            if path.exists():
                models[name] = joblib.load(path)

    report = {"k": k, "n_test_users": len(test_users), "models": {}}
    for name, model in models.items():
        try:
            metrics, _ = evaluate_model(model, test_users, ground_truth, train, k=k)
            report["models"][name] = metrics
            logger.info("%s: %s", name, metrics)
        except Exception as e:
            logger.warning("Failed to evaluate %s: %s", name, e)
            report["models"][name] = {"error": str(e)}

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("Saved report to %s", report_path)
    return report
