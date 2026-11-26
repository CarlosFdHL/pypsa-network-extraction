import pandas as pd

from network_extraction.checks.weightings import check_weightings
from network_extraction.weather_year import weather_year


def snapshots(index, hours):
    hours = pd.Series(hours, index=index, dtype=float)
    return pd.DataFrame({"objective": hours, "generators": hours, "stores": hours,
                         "weather_year": weather_year(index).to_numpy()}, index=index)


def segmented_year(year):
    """Irregular segments (12 h and 36 h alternating) filling one weather year."""
    start, end = pd.Timestamp(f"{year}-07-01"), pd.Timestamp(f"{year + 1}-07-01")
    stamps, t, k = [], start, 0
    while t < end:
        stamps.append(t)
        t = min(t + pd.Timedelta(hours=12 if k % 2 == 0 else 36), end)
        k += 1
    idx = pd.DatetimeIndex(stamps)
    nxt = idx[1:].append(pd.DatetimeIndex([end]))
    return idx, (nxt - idx) / pd.Timedelta(hours=1)


def test_segmented_consecutive_years_pass():
    i1, h1 = segmented_year(1985)
    i2, h2 = segmented_year(1986)
    assert check_weightings(snapshots(i1.append(i2), list(h1) + list(h2))) == []


def test_wrong_weight_is_reported():
    idx, hours = segmented_year(1985)
    hours = list(hours)
    hours[3] += 1.0
    problems = check_weightings(snapshots(idx, hours))
    assert any("differs from the time to the next" in p for p in problems)


def test_columns_differ_is_reported():
    idx, hours = segmented_year(1985)
    df = snapshots(idx, hours)
    df["objective"] *= 2
    assert any("differ" in p for p in check_weightings(df))
