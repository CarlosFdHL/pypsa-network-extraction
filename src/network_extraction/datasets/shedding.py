"""Load shedding of a validation network.

shedding.parquet:          raw dispatch p of every shedding generator [MW as in the model, before sign]
shedding_generators.csv:   per generator: carrier, type, bus, sign, marginal_cost, time_varying_cost

Energy = p * sign * weight; cost = p * marginal_cost * weight (see metrics/shedding.py).
Design networks have no shedding generators, so this dataset is only extracted from validation networks.
"""

import pandas as pd

from network_extraction.flat_snapshots import flat_snapshots
from network_extraction.registry import extractor
from network_extraction.shedding_generators import shedding_generators


def shedding_static(n, gens):
    g = n.generators.loc[gens.index]
    sign = g["sign"] if "sign" in g else pd.Series(1.0, index=gens.index)
    return pd.DataFrame({
        "carrier": g["carrier"],
        "type": gens,
        "bus": g["bus"],
        "sign": sign.astype(float),
        "marginal_cost": g["marginal_cost"].astype(float),
        "time_varying_cost": gens.index.isin(n.generators_t.marginal_cost.columns),
    }).rename_axis("name")


def shedding_dispatch(n, gens):
    p = n.generators_t.p.reindex(columns=gens.index, fill_value=0.0)
    p.index = flat_snapshots(n)
    p.columns.name = "name"
    return p.astype(float)


@extractor("shedding", roles=("validation",))
def extract_shedding(n, cfg):
    gens = shedding_generators(n, cfg)
    if gens.empty:
        print("    [WARNING] validation network without load-shedding generators")
    static = shedding_static(n, gens)
    if static.time_varying_cost.any():
        print("    [WARNING] time-varying marginal cost on shedding generators: "
              "shedding_generators.csv only stores the static value")
    return {"shedding.parquet": shedding_dispatch(n, gens),
            "shedding_generators.csv": static}
