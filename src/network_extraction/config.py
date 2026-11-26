"""Load extract_config.yaml from the root of the repo."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTRACT_CONFIG = REPO_ROOT / "extract_config.yaml"


def resolve_path(path, base=REPO_ROOT):
    """Expand ~ and make relative paths relative to `base`."""
    path = Path(path).expanduser()
    return path if path.is_absolute() else base / path


def load_extract_config(path=EXTRACT_CONFIG):
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg["results_root"] = resolve_path(cfg["results_root"])
    cfg["data_dir"] = resolve_path(cfg.get("data_dir", "data"))
    cfg.setdefault("roles", ["design", "validation"])
    cfg.setdefault("force", False)
    cfg.setdefault("timeseries_format", "parquet")
    cfg.setdefault("check_rtol", 1e-4)
    cfg.setdefault("price_carriers", ["AC"])
    cfg["runs"] = [{"name": r} if isinstance(r, str) else r for r in cfg["runs"]]
    return cfg
