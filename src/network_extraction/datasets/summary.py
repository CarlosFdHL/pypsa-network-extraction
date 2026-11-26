"""summary.csv: scalar results of one network, in EUR and MWh.

Cost definition (decided 2026-11-25):
  shed_cost       = sum p * marginal_cost * w over the shedding generators
  shed_energy     = sum p * sign * w
  opex_excl_shed  = statistics.opex(groupby="carrier", nice_names=False) without shedding carriers
                    (nice_names=False is required: nice names would not match the shedding carriers)
  total_cost      = capex + opex_excl_shed + shed_cost
All costs are totals over the modelled horizon. nyears = sum of objective weights / 8760 (as in
PyPSA-Eur, which scales capital costs by it); metrics.system_cost divides by it to get EUR per year.
shed_peak       = largest sum of p * sign over the generators of one type in one snapshot [MW]
VOLL per type = marginal cost of the shedding generators as stored in the network.
co2_atmosphere_net = level of the "co2 atmosphere" store at the last snapshot minus e_initial
                     [t CO2 over the horizon]; NaN if the network has no such store.
"""

import numpy as np
import pandas as pd

from network_extraction.registry import extractor
from network_extraction.shedding_generators import shedding_generators


def shedding_by_type(n, gens):
    """Energy [MWh], cost [EUR] and VOLL [EUR/MWh] of load shedding per type."""
    w = n.snapshot_weightings.generators
    p = n.generators_t.p.reindex(columns=gens.index, fill_value=0.0)
    sign = n.generators["sign"].reindex(gens.index).fillna(1.0) if "sign" in n.generators else 1.0
    mc = n.get_switchable_as_dense("Generator", "marginal_cost")[gens.index]

    energy = (p * sign).mul(w, axis=0).sum().groupby(gens).sum()
    peak = (p * sign).T.groupby(gens).sum().T.max()     # largest total shedding in one snapshot [MW]
    cost = (p * mc).mul(w, axis=0).sum().groupby(gens).sum()
    static_mc = n.generators.loc[gens.index, "marginal_cost"].groupby(gens)
    voll = static_mc.mean()
    # PyPSA-Eur adds a tiny random noise to marginal costs (~1e-2 EUR/MWh): only warn above 0.01 %
    spread = (static_mc.max() - static_mc.min()) / voll.abs()
    if (spread > 1e-4).any():
        print(f"    [WARNING] shedding generators of one type with different marginal costs: "
              f"{static_mc.agg(['min', 'max']).to_dict('index')}")
    return energy, cost, voll, peak


def co2_atmosphere_net(n, store="co2 atmosphere"):
    if store not in n.stores.index or store not in n.stores_t.e:
        return np.nan
    return float(n.stores_t.e[store].iloc[-1] - n.stores.at[store, "e_initial"])


def summary_row(n, cfg):
    gens = shedding_generators(n, cfg)
    kinds = list(cfg["shedding_carriers"])
    energy, cost, voll, peak = shedding_by_type(n, gens)

    opex = n.statistics.opex(groupby="carrier", nice_names=False)
    is_shed = opex.index.get_level_values("carrier").isin(cfg["shedding_carriers"].values())
    capex = float(n.statistics.capex().sum())
    opex_excl_shed = float(opex[~is_shed].sum())
    shed_cost = float(cost.sum())

    row = {
        "objective": float(n.objective) if n.objective is not None else np.nan,
        "capex": capex,
        "opex_excl_shed": opex_excl_shed,
        "shed_cost": shed_cost,
        "total_cost": capex + opex_excl_shed + shed_cost,
        "nyears": float(n.snapshot_weightings["objective"].sum() / 8760.0),
        "n_shedding_generators": len(gens),
        "co2_atmosphere_net": co2_atmosphere_net(n),
    }
    for kind in kinds:
        row[f"shed_energy_{kind}"] = float(energy.get(kind, 0.0))
        row[f"shed_cost_{kind}"] = float(cost.get(kind, 0.0))
        row[f"voll_{kind}"] = float(voll.get(kind, np.nan))
        row[f"shed_peak_{kind}"] = float(peak.get(kind, 0.0))
    return pd.DataFrame([row])


@extractor("summary")
def extract_summary(n, cfg):
    return {"summary.csv": summary_row(n, cfg)}
