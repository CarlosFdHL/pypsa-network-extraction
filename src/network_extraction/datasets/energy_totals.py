"""energy_totals.csv: supply and withdrawal over the whole horizon [MWh].

statistics.supply / statistics.withdrawal grouped by (component, bus_carrier, carrier),
weighted by the snapshot weightings (nice_names=False). Loads without a carrier have carrier "".
Used for the consumption of the electricity + heat subsystem (unserved energy).
"""

import pandas as pd

from network_extraction.registry import extractor


def energy_totals(n):
    kw = dict(groupby=["bus_carrier", "carrier"], nice_names=False)
    df = pd.concat({"supply": n.statistics.supply(**kw),
                    "withdrawal": n.statistics.withdrawal(**kw)}, axis=1).fillna(0.0)
    df = df[(df.abs() > 0).any(axis=1)]
    df.index = df.index.set_names(["component", "bus_carrier", "carrier"])
    return df.sort_index()


@extractor("energy_totals")
def extract_energy_totals(n, cfg):
    return {"energy_totals.csv": energy_totals(n)}
