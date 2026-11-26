"""Read and write meta.json, the record of what was extracted from which network."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from network_extraction.config import REPO_ROOT

META_FILE = "meta.json"


def now():
    return datetime.now().isoformat(timespec="seconds")


def git_commit():
    """Commit of this repo, so that every file can be traced to the code that wrote it."""
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain", "src"], cwd=REPO_ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
        return out.stdout.strip() + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def load_meta(scenario_out, run, scenario):
    path = Path(scenario_out) / META_FILE
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"run": run, "scenario": scenario, "networks": {}, "scenario_datasets": {}}


def save_meta(scenario_out, meta):
    path = Path(scenario_out) / META_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def network_entry(meta, network_file):
    """Entry of one network in meta.json, created if missing and refreshed from the file."""
    entry = meta["networks"].setdefault(network_file.name, {"datasets": {}, "checks": {}})
    entry.update({
        "source": str(network_file.path),
        "source_mtime": network_file.path.stat().st_mtime,
        "role": network_file.role,
        "weather_year": network_file.weather_year,
        "resolution": network_file.resolution,
    })
    return entry


def record_dataset(datasets, name, files, source_mtime, extraction_info):
    datasets[name] = {"files": files, "source_mtime": source_mtime,
                      "extracted_at": now(), **extraction_info}
