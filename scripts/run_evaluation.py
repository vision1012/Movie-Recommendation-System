#!/usr/bin/env python3
"""Run evaluation pipeline and generate report."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.evaluate import run_evaluation

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    run_evaluation()
