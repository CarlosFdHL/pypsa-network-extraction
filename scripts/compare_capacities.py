"""Compare the capacities of a design network with one of its validation networks.

Diagnostic for the capacities_match check: which components and carriers differ, by how much, and
whether they are extendable in the validation network. Edit the settings below and run on Sophia:

    PYTHONPATH=src python scripts/compare_capacities.py
"""

from pathlib import Path

import pandas as pd
import pypsa

from network_extraction.datasets.capacities import capacity_table

# ---- settings ---------------------------------------------------------------
RESULTS = Path("~/projects/pypsa-eur-aleks/results").expanduser()
RUN = "multi_year_greedy"
SCENARIO = "weather_year_1958_626seg"
DESIGN = "base_s_50___2050.nc"
VALIDATION = "weather_year_1941_3H_base_s_50___2050.nc"
RTOL, ATOL = 1e-4, 1e-3
OUTPUT = Path("compare_capacities.csv")
# -----------------------------------------------------------------------------


def main():
    folder = RESULTS / RUN / SCENARIO / "networks"
    design = capacity_table(pypsa.Network(str(folder / DESIGN)))
    val = capacity_table(pypsa.Network(str(folder / VALIDATION)))

    common = design.index.intersection(val.index)
    table = pd.DataFrame({
        "carrier": design.loc[common, "carrier"],
        "extendable_design": design.loc[common, "extendable"],
        "extendable_validation": val.loc[common, "extendable"],
        "design_opt": design.loc[common, "nom_opt"],
        "validation_nom": val.loc[common, "nom"],
        "validation_opt": val.loc[common, "nom_opt"],
    })
    table["diff"] = table.validation_opt - table.design_opt
    scale = table.design_opt.abs().clip(lower=1.0)
    table["differs"] = (table["diff"].abs() > ATOL) & (table["diff"].abs() / scale > RTOL)

    off = table[table.differs]
    summary = (off.groupby([off.index.get_level_values("component"), "carrier", "extendable_validation"])
               .agg(n=("diff", "size"), sum_diff=("diff", "sum"), max_abs_diff=("diff", lambda d: d.abs().max()))
               .sort_values("max_abs_diff", ascending=False))
    pd.set_option("display.width", 200)
    print(f"{len(off)} of {len(common)} common assets differ")
    print(f"only in design: {len(design.index.difference(val.index))}, "
          f"only in validation: {len(val.index.difference(design.index))}")
    print(summary.to_string())
    off.to_csv(OUTPUT)
    print(f"details: {OUTPUT}")


if __name__ == "__main__":
    main()
