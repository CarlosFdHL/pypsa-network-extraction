"""Small solved PyPSA networks with the same file layout as the PyPSA-Eur results."""

import numpy as np
import pandas as pd
import pypsa

SHEDDING = {"elec load": 1e4, "heat shed": 5e4}


def weather_year_snapshots(years, freq):
    """Snapshots of whole weather years (1 July to 30 June) at a fixed frequency."""
    parts = [pd.date_range(f"{y}-07-01", f"{y + 1}-07-01", freq=freq, inclusive="left") for y in years]
    return parts[0].append(parts[1:]) if len(parts) > 1 else parts[0]


def base_network(snapshots, hours, seed):
    rng = np.random.default_rng(seed)
    n = pypsa.Network()
    n.set_snapshots(snapshots)
    n.snapshot_weightings.loc[:, :] = hours

    n.add("Carrier", ["AC", "urban central heat", "gas", "wind", "battery", "heat pump", "CHP", "gas supply",
                       "urban central water tanks", *SHEDDING])
    n.add("Bus", "DE0 0", carrier="AC", country="DE", location="DE0 0", x=10.0, y=51.0)
    n.add("Bus", "DE0 0 heat", carrier="urban central heat", country="DE", location="DE0 0", x=10.0, y=51.0)
    n.add("Bus", "DE0 0 gas", carrier="gas", country="DE", location="DE0 0", x=10.0, y=51.0)

    wind_cf = pd.Series(rng.uniform(0.0, 1.0, len(snapshots)), index=snapshots)
    elec = pd.Series(rng.uniform(50, 150, len(snapshots)), index=snapshots)
    heat = pd.Series(rng.uniform(20, 80, len(snapshots)), index=snapshots)

    n.add("Generator", "DE0 0 onwind", bus="DE0 0", carrier="wind", p_nom_extendable=True,
          capital_cost=1e5, p_max_pu=wind_cf, marginal_cost=0.1)
    n.add("Generator", "DE0 0 OCGT", bus="DE0 0", carrier="gas", p_nom_extendable=True,
          capital_cost=4e4, marginal_cost=80.0)
    n.add("Generator", "DE0 0 gas supply", bus="DE0 0 gas", carrier="gas supply",
          p_nom=1e5, marginal_cost=30.0)
    n.add("Link", "DE0 0 CHP", bus0="DE0 0 gas", bus1="DE0 0", bus2="DE0 0 heat", carrier="CHP",
          efficiency=0.4, efficiency2=0.45, p_nom_extendable=True, capital_cost=3e4)
    n.add("Link", "DE0 0 heat pump", bus0="DE0 0", bus1="DE0 0 heat", carrier="heat pump",
          efficiency=3.0, p_nom_extendable=True, capital_cost=2e4)
    n.add("Store", "DE0 0 battery", bus="DE0 0", carrier="battery", e_nom_extendable=True,
          e_cyclic=True, capital_cost=1e4)
    n.add("Store", "DE0 0 urban central water tanks", bus="DE0 0 heat", carrier="urban central water tanks",
          e_nom_extendable=True, e_cyclic=True, capital_cost=500)
    n.add("Load", "DE0 0 elec", bus="DE0 0", carrier="electricity", p_set=elec)
    n.add("Load", "DE0 0 heat", bus="DE0 0 heat", p_set=heat)   # no carrier: grouped by bus carrier
    return n


def solve(n):
    status, condition = n.optimize(solver_name="highs")
    assert status == "ok", condition
    return n


def design_network(years, freq="24h", hours=24.0, seed=0):
    return solve(base_network(weather_year_snapshots(years, freq), hours, seed))


def validation_network(design, year, freq="3h", hours=3.0, seed=1, demand_scale=2.2):
    """Design capacities fixed, another weather year, load shedding available."""
    n = base_network(weather_year_snapshots([year], freq), hours, seed)
    for list_name, attr in [("generators", "p_nom"), ("links", "p_nom"), ("stores", "e_nom")]:
        df = getattr(n, list_name)
        df[attr] = getattr(design, list_name)[f"{attr}_opt"].reindex(df.index)
        df[f"{attr}_extendable"] = False
    n.loads_t.p_set *= demand_scale

    n.add("Generator", "DE0 0 low voltage load shedding", bus="DE0 0", carrier="elec load",
          p_nom=1e9, marginal_cost=SHEDDING["elec load"])
    n.add("Generator", "DE0 0 heat shedding", bus="DE0 0 heat", carrier="heat shed",
          p_nom=1e6, marginal_cost=SHEDDING["heat shed"])
    return solve(n)


def write_results(results_root, run, scenario, design_years, validation_years):
    """results/<run>/<scenario>/networks/ with one design and its validation networks."""
    folder = results_root / run / scenario / "networks"
    folder.mkdir(parents=True)
    design = design_network(design_years)
    design.export_to_netcdf(folder / "base_s_1___2050.nc")
    for year in validation_years:
        val = validation_network(design, year)
        val.export_to_netcdf(folder / f"weather_year_{year}_3H_base_s_1___2050.nc")
    configs = results_root / run / "configs"
    configs.mkdir(exist_ok=True)
    (configs / "config.base.yaml").write_text("run:\n  name: toy\n")
    return folder
