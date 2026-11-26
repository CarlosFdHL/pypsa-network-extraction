"""Dataset extractors. Importing this package registers all of them.

To add a dataset: create a file here with a function decorated with @extractor,
import it below and add its name to a detail level in extract_config.yaml.
"""

from network_extraction.datasets import (  # noqa: F401
    ac_load,
    buses,
    capacities,
    energy_balance,
    energy_totals,
    global_constraints,
    marginal_costs,
    prices,
    shedding,
    snapshots,
    solver_stats,
    summary,
    timeseries,
)
