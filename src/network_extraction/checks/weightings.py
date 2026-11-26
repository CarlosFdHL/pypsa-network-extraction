"""Snapshot weightings: the three columns agree, they match the timestamps and fill whole weather years."""

import numpy as np
import pandas as pd

from network_extraction.weather_year import hours_in_year, year_start


def durations_from_timestamps(snapshots):
    """Hours from each snapshot to the next one; the last snapshot of a year runs until 1 July."""
    ts = pd.DatetimeIndex(snapshots.index)
    years = snapshots["weather_year"].to_numpy()
    year_end = pd.DatetimeIndex([year_start(y + 1) for y in years])
    nxt = np.append(ts[1:].to_numpy(), year_end[-1].to_datetime64())
    last_in_year = np.r_[years[1:] != years[:-1], True]
    nxt = np.where(last_in_year, year_end.to_numpy(), nxt)
    return pd.Series((nxt - ts.to_numpy()) / np.timedelta64(1, "h"), index=snapshots.index)


def check_weightings(snapshots, atol_hours=1e-6):
    problems = []
    w = snapshots[["objective", "generators", "stores"]]

    if not np.allclose(w["objective"], w["generators"], atol=atol_hours) or \
            not np.allclose(w["stores"], w["generators"], atol=atol_hours):
        problems.append("objective, generators and stores weightings differ")

    first = snapshots.index.to_series().groupby(snapshots["weather_year"].to_numpy()).first()
    late = [int(y) for y, t in first.items() if t != year_start(y)]
    if late:
        problems.append(f"weather years not starting on 1 July 00:00: {late}")

    dur = durations_from_timestamps(snapshots)
    off = (dur - w["generators"]).abs() > atol_hours
    if off.any():
        problems.append(f"{int(off.sum())} snapshots whose weight differs from the time to the next one")

    per_year = w["generators"].groupby(snapshots["weather_year"]).sum()
    expected = pd.Series([hours_in_year(y) for y in per_year.index], index=per_year.index)
    wrong = per_year[(per_year - expected).abs() > atol_hours]
    if not wrong.empty:
        problems.append(f"hours per weather year != 8760/8784: {wrong.round(3).to_dict()}")
    return problems
