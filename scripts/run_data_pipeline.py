#!/usr/bin/env python3
"""Run data pipeline: ingest + preprocess + save."""
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.data.pipeline import run_data_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    config = load_config()
    run_data_pipeline(config)
    logger.info("Data pipeline complete.")


if __name__ == "__main__":
    main()
