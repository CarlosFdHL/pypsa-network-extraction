"""Run the consistency checks on a loaded network and record the result in meta.json."""

from network_extraction.checks.capacities_match import check_capacities_match
from network_extraction.checks.weightings import check_weightings
from network_extraction.datasets.snapshots import snapshot_table


def run_checks(n, network_file, scenario_out, cfg):
    """{check name: "ok" or list of problems}; problems are printed as warnings."""
    rtol = cfg["check_rtol"]
    results = {"weightings": check_weightings(snapshot_table(n))}
    if network_file.role == "validation":
        results["capacities_match"] = check_capacities_match(
            n, scenario_out / "capacities.csv", list(cfg["shedding_carriers"].values()), rtol)

    for name, problems in results.items():
        for p in problems:
            print(f"    [CHECK {name}] {p}")
    return {name: problems or "ok" for name, problems in results.items()}
