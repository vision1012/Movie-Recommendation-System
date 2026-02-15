#!/usr/bin/env python3
"""Show model output: recommendations and similar items."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.inference.predictor import RecommendationPredictor


def main() -> None:
    config = load_config()
    root = Path(__file__).resolve().parent.parent
    models_dir = Path(config["paths"]["models_dir"])
    processed_dir = Path(config["paths"]["processed_data"])
    if not models_dir.is_absolute():
        models_dir = root / models_dir
    if not processed_dir.is_absolute():
        processed_dir = root / processed_dir

    pred = RecommendationPredictor(
        models_dir=models_dir,
        processed_dir=processed_dir,
        model_name=config.get("inference", {}).get("model_name", "hybrid"),
    )
    pred.load()

    # Recommendations for user 1
    print("=" * 60)
    print("PERSONALIZED RECOMMENDATIONS (user_id=1, k=5)")
    print("=" * 60)
    recs = pred.recommend(user_id=1, k=5)
    print(json.dumps({"user_id": "1", "recommendations": recs}, indent=2))

    # Similar items for movie 1
    print("\n" + "=" * 60)
    print("SIMILAR ITEMS (item_id=1, k=5) – 'Because you watched'")
    print("=" * 60)
    similar = pred.similar_items(item_id=1, k=5)
    print(json.dumps({"item_id": "1", "similar_items": similar}, indent=2))

    # Another user
    print("\n" + "=" * 60)
    print("PERSONALIZED RECOMMENDATIONS (user_id=100, k=3)")
    print("=" * 60)
    recs2 = pred.recommend(user_id=100, k=3)
    print(json.dumps({"user_id": "100", "recommendations": recs2}, indent=2))


if __name__ == "__main__":
    main()
