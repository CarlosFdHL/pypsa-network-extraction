"""solver_stats.csv: problem size and run time of the solve that produced the network.

Read from the files next to the network, not from the network itself:
  <scenario>/logs/<network stem>_solver.log          Gurobi log (last solve, Gurobi appends on re-runs)
  <scenario>/benchmarks/solve_*/<network stem>       snakemake benchmark (newest file)
Missing files give NaN. `optimal` is False if the last solve did not reach "Optimal objective".
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from network_extraction.registry import extractor

LOG_PATTERNS = {  # name: (regex, number of groups, names of the groups)
    "size": (r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros",
             ["rows", "cols", "nnz"]),
    "presolve": (r"Presolve time: ([\d.]+)s", ["presolve_time_s"]),
    "solve": (r"(?:Barrier solved model|Solved) in (\d+) iterations and ([\d.]+) seconds",
              ["iterations", "solve_time_s"]),
    "objective": (r"Optimal objective\s+([\d.eE+-]+)", ["objective"]),
    "threads": (r"using up to (\d+) threads", ["threads"]),
}


def last_solve_block(text):
    return text.split("Gurobi Optimizer version")[-1]


def parse_gurobi_log(text):
    block = last_solve_block(text)
    out = {"optimal": "Optimal objective" in block}
    for regex, names in LOG_PATTERNS.values():
        found = re.findall(regex, block)
        last = found[-1] if found else (np.nan,) * len(names)
        last = last if isinstance(last, tuple) else (last,)
        out.update({k: float(v) for k, v in zip(names, last)})
    cpu = re.search(r"CPU model: (.+?),", block)
    out["cpu"] = cpu.group(1) if cpu else None
    return out


def read_benchmark(path):
    if path is None:
        return {"wall_time_s": np.nan, "max_rss_mb": np.nan}
    b = pd.read_csv(path, sep="\t")
    return {"wall_time_s": float(b["s"].iloc[-1]), "max_rss_mb": float(b["max_rss"].iloc[-1])}


def solver_stats(network_path):
    network_path = Path(network_path)
    scenario_dir, stem = network_path.parents[1], network_path.stem
    log = scenario_dir / "logs" / f"{stem}_solver.log"
    row = {"log_found": log.exists()}
    if log.exists():
        row.update(parse_gurobi_log(log.read_text(errors="ignore")))
    benches = sorted(scenario_dir.glob(f"benchmarks/solve_*/{stem}"), key=lambda p: p.stat().st_mtime)
    row.update(read_benchmark(benches[-1] if benches else None))
    return pd.DataFrame([row])


@extractor("solver_stats", with_path=True)
def extract_solver_stats(n, cfg, network_file):
    return {"solver_stats.csv": solver_stats(network_file.path)}
