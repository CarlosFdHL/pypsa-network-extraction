"""Find the scenarios and network files of a run in the PyPSA-Eur results folder."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NetworkFile:
    name: str               # folder name in data/: "design" or "val_wy1941_3H"
    role: str               # "design" or "validation"
    path: Path
    weather_year: int | None = None
    resolution: str | None = None


def find_scenarios(run_dir, selection="all"):
    """Scenario folders of a run (those with a networks/ subfolder)."""
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Run folder not found: {run_dir}")
    found = sorted(d for d in run_dir.iterdir() if (d / "networks").is_dir())
    if selection == "all":
        return found
    missing = set(selection) - {d.name for d in found}
    if missing:
        print(f"  [WARNING] scenarios not found in {run_dir}: {sorted(missing)}")
    return [d for d in found if d.name in selection]


def find_networks(scenario_dir, design_pattern, validation_pattern):
    """Design and validation network files of one scenario."""
    design_rx, val_rx = re.compile(design_pattern), re.compile(validation_pattern)
    networks = []
    for path in sorted((Path(scenario_dir) / "networks").glob("*.nc")):
        if m := val_rx.match(path.name):
            year, res = int(m.group("weather_year")), m.group("resolution")
            networks.append(NetworkFile(f"val_wy{year}_{res}", "validation", path, year, res))
        elif design_rx.match(path.name):
            networks.append(NetworkFile("design", "design", path))

    if sum(nf.role == "design" for nf in networks) > 1:
        raise ValueError(f"More than one design network in {scenario_dir}")
    # Design first, so that scenario-level files exist before the validation checks
    return sorted(networks, key=lambda nf: (nf.role != "design", nf.name))
