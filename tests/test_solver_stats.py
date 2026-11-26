"""Parsing of Gurobi logs and snakemake benchmarks."""

import pandas as pd

from network_extraction.datasets.solver_stats import parse_gurobi_log, solver_stats

LOG = """Gurobi Optimizer version 11.0.0
Optimize a model with 10 rows, 20 columns and 30 nonzeros
Infeasible model
Gurobi Optimizer version 11.0.0 build v11.0.0rc2 (linux64 - "Rocky Linux")
CPU model: AMD EPYC 7351 16-Core Processor, instruction set [SSE2|AVX|AVX2]
Thread count: 32 physical cores, 32 logical processors, using up to 8 threads
Optimize a model with 1000 rows, 2000 columns and 5000 nonzeros
Presolve time: 12.5s
Barrier solved model in 45 iterations and 321.4 seconds (100.0 work units)
Optimal objective  1.23456789e+11
"""


def test_parse_last_solve_only():
    out = parse_gurobi_log(LOG)
    assert out["optimal"]
    assert (out["rows"], out["cols"], out["nnz"]) == (1000, 2000, 5000)
    assert out["solve_time_s"] == 321.4 and out["iterations"] == 45
    assert out["objective"] == 1.23456789e11
    assert out["threads"] == 8 and out["cpu"] == "AMD EPYC 7351 16-Core Processor"


def test_files_next_to_network(tmp_path):
    scen = tmp_path / "scenario"
    nc = scen / "networks" / "base_s_50___2050.nc"
    nc.parent.mkdir(parents=True)
    (scen / "logs").mkdir()
    (scen / "logs" / "base_s_50___2050_solver.log").write_text(LOG)
    bench = scen / "benchmarks" / "solve_sector_network" / "base_s_50___2050"
    bench.parent.mkdir(parents=True)
    pd.DataFrame({"s": [400.0], "max_rss": [12000.0]}).to_csv(bench, sep="\t", index=False)

    row = solver_stats(nc).iloc[0]
    assert row.log_found and row.optimal
    assert row.wall_time_s == 400.0 and row.max_rss_mb == 12000.0
