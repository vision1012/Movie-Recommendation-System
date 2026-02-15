#!/usr/bin/env python3
"""Run training pipeline: fit models and save artifacts."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.training.train import run_training

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    run_training()
