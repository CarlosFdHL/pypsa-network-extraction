"""Snapshot weightings: the three columns agree, they match the timestamps and fill whole weather years.

PyPSA-Eur drops 29 February by default (snapshots: drop_leap_day: true). A leap day without any
snapshot is treated as removed: it does not count in the time to the next snapshot nor in the
hours of its weather year (8760 h instead of 8784 h).
"""

import calendar

import numpy as np
import pandas as pd

from network_extraction.weather_year import hours_in_year, year_start


def dropped_leap_days(snapshots):
    """29 February of the covered weather years that has no snapshot."""
    ts = pd.DatetimeIndex(snapshots.index)
    present = set(ts.normalize())
    days = []
    for wy in np.unique(snapshots["weather_year"]):
        if calendar.isleap(int(wy) + 1):
            day = pd.Timestamp(year=int(wy) + 1, month=2, day=29)
            if day not in present:
                days.append(day)
    return days


def durations_from_timestamps(snapshots):
    """Hours from each snapshot to the next one, without dropped leap days;
    the last snapshot of a weather year runs until 1 July."""
    ts = pd.DatetimeIndex(snapshots.index)
    years = snapshots["weather_year"].to_numpy()
    year_end = pd.DatetimeIndex([year_start(y + 1) for y in years])
    nxt = np.append(ts[1:].to_numpy(), year_end[-1].to_datetime64())
    last_in_year = np.r_[years[1:] != years[:-1], True]
    nxt = pd.DatetimeIndex(np.where(last_in_year, year_end.to_numpy(), nxt))
    hours = (nxt - ts) / pd.Timedelta(hours=1)
    for day in dropped_leap_days(snapshots):
        hours = hours - 24.0 * ((ts <= day) & (nxt >= day + pd.Timedelta(days=1)))
    return pd.Series(np.asarray(hours, dtype=float), index=snapshots.index)


def expected_hours(snapshots):
    """Hours of each weather year in the model (8760, or 8784 if 29 February is kept)."""
    dropped = {d.year - 1 for d in dropped_leap_days(snapshots)}
    years = np.unique(snapshots["weather_year"])
    return pd.Series([hours_in_year(y) - (24.0 if y in dropped else 0.0) for y in years], index=years)


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
    expected = expected_hours(snapshots).reindex(per_year.index)
    wrong = per_year[(per_year - expected).abs() > atol_hours]
    if not wrong.empty:
        problems.append(f"hours per weather year differ from the model calendar: {wrong.round(3).to_dict()}")
    return problems
