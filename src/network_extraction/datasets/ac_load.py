"""ac_load.parquet: electricity demand at the AC buses [MW].

The loads whose name is an AC bus name (PyPSA-Eur names the main electricity load after its bus).
One column per AC bus. Used as weights of the load-weighted price RMSE.
"""

from network_extraction.flat_snapshots import flat_snapshots
from network_extraction.registry import extractor


def ac_load(n):
    ac = n.buses.index[n.buses["carrier"] == "AC"]
    loads = n.loads.index[n.loads.index.isin(ac)]
    df = n.loads_t.p_set.reindex(columns=loads).fillna(0.0)
    df.index = flat_snapshots(n)
    df.columns.name = "bus"
    return df.astype("float32")


@extractor("ac_load")
def extract_ac_load(n, cfg):
    return {"ac_load.parquet": ac_load(n)}
