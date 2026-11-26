"""Validation networks must have the capacities of their design network."""

import numpy as np
import pandas as pd

from network_extraction.datasets.capacities import capacity_table


def check_capacities_match(n, design_capacities_csv, shedding_carriers, rtol=1e-4):
    if not design_capacities_csv.exists():
        return ["design capacities.csv not found: capacities not compared"]

    design = pd.read_csv(design_capacities_csv, index_col=[0, 1])["nom_opt"]
    table = capacity_table(n)
    val = table.loc[~table["carrier"].isin(shedding_carriers), "nom_opt"]

    problems = []
    missing = design.index.difference(val.index)
    extra = val.index.difference(design.index)
    if len(missing):
        problems.append(f"{len(missing)} design assets missing in the validation network")
    if len(extra):
        problems.append(f"{len(extra)} validation assets not in the design (excluding shedding)")

    common = design.index.intersection(val.index)
    d, v = design[common].astype(float), val[common].astype(float)
    off = ~np.isclose(v, d, rtol=rtol, atol=1e-3)
    if off.any():
        worst = (v - d).abs()[off].sort_values(ascending=False).head(3)
        problems.append(f"{int(off.sum())} assets with different capacity, largest: {worst.round(3).to_dict()}")
    return problems
