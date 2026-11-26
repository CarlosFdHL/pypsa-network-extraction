"""snapshots.csv: timestamps, the three snapshot weightings and the weather-year label."""

import pandas as pd

from network_extraction.flat_snapshots import flat_snapshots
from network_extraction.registry import extractor
from network_extraction.weather_year import weather_year


def snapshot_table(n):
    ts = flat_snapshots(n)
    w = n.snapshot_weightings
    return pd.DataFrame({
        "objective": w["objective"].to_numpy(float),
        "generators": w["generators"].to_numpy(float),
        "stores": w["stores"].to_numpy(float),
        "weather_year": weather_year(ts).to_numpy(),
    }, index=ts)


@extractor("snapshots")
def extract_snapshots(n, cfg):
    return {"snapshots.csv": snapshot_table(n)}
