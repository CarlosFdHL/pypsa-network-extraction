"""Minimal reader of the extracted files, for the tests (the paper repo has the full reader)."""

import pandas as pd

STATIC = {"summary", "capacities", "buses", "shedding_generators", "global_constraints"}


def read(folder, name):
    parquet, csv = folder / f"{name}.parquet", folder / f"{name}.csv"
    if parquet.exists():
        return pd.read_parquet(parquet)
    index_col = [0, 1] if name == "capacities" else 0
    df = pd.read_csv(csv, index_col=index_col)
    if name not in STATIC:
        df.index = pd.DatetimeIndex(df.index)
    return df
