"""Snapshots of a network as a flat DatetimeIndex."""

import pandas as pd


def flat_snapshots(n):
    """Timestamps of the snapshots (last level if the snapshots are multi-indexed)."""
    sns = n.snapshots
    values = sns.get_level_values(-1) if isinstance(sns, pd.MultiIndex) else sns
    return pd.DatetimeIndex(values, name="snapshot")
