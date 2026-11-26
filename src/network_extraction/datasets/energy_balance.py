"""supply_by_carrier.parquet and withdrawal_by_carrier.parquet (standard detail).

n.statistics.supply / withdrawal with groupby=["carrier", "bus_carrier"], aggregate_time=False and
nice_names=False, summed over all of Europe. Columns: MultiIndex (bus_carrier, carrier); values in MW
(model units), positive in both files. Each asset is split into supply and withdrawal before summing,
so bidirectional assets (PHS, batteries, DC links) are not netted.
"""

from network_extraction.flat_snapshots import flat_snapshots
from network_extraction.registry import extractor


def balance_by_carrier(n, direction):
    stats = getattr(n.statistics, direction)(
        groupby=["carrier", "bus_carrier"], aggregate_time=False, nice_names=False)
    df = stats.groupby(level=["bus_carrier", "carrier"]).sum().T.abs()
    df.index = flat_snapshots(n)
    df.columns = df.columns.set_names(["bus_carrier", "carrier"])
    df = df.loc[:, (df != 0).any()]
    return df.astype("float32")


@extractor("supply_by_carrier")
def extract_supply(n, cfg):
    return {"supply_by_carrier.parquet": balance_by_carrier(n, "supply")}


@extractor("withdrawal_by_carrier")
def extract_withdrawal(n, cfg):
    return {"withdrawal_by_carrier.parquet": balance_by_carrier(n, "withdrawal")}
