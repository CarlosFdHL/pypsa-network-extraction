"""Weather years are hydrological years, July to June, labelled by the year in which they start."""

import numpy as np
import pandas as pd

START_MONTH = 7


def weather_year(timestamps):
    """Weather-year label of each timestamp (July 1985 - June 1986 -> 1985)."""
    ts = pd.DatetimeIndex(timestamps)
    return pd.Index(np.where(ts.month >= START_MONTH, ts.year, ts.year - 1), name="weather_year")


def year_start(year):
    return pd.Timestamp(year=int(year), month=START_MONTH, day=1)


def hours_in_year(year):
    """Length of one weather year in hours (8784 if it contains 29 February)."""
    return (year_start(year + 1) - year_start(year)) / pd.Timedelta(hours=1)
