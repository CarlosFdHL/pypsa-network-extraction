"""prices.parquet: marginal price of the buses whose carrier is in `price_carriers` (extract_config.yaml).

One column per bus; the carrier of each bus is in buses.csv.
"""

from network_extraction.flat_snapshots import flat_snapshots
from network_extraction.registry import extractor


@extractor("prices")
def extract_prices(n, cfg):
    buses = n.buses.index[n.buses["carrier"].isin(cfg["price_carriers"])]
    df = n.buses_t.marginal_price.reindex(columns=buses)
    df.index = flat_snapshots(n)
    df.columns.name = "bus"
    return {"prices.parquet": df.astype("float32")}
