"""Configuration loader."""
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML config. Defaults to configs/config.yaml from project root."""
    if config_path is None:
        root = Path(__file__).resolve().parent.parent
        config_path = root / "configs" / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_path(config: dict[str, Any], key: str, base: Path | None = None) -> Path:
    """Resolve a path from config, optionally relative to base."""
    root = base or Path(__file__).resolve().parent.parent
    value = config["paths"][key]
    p = Path(value)
    if not p.is_absolute():
        p = root / p
    return p
