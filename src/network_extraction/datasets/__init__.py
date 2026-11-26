"""Dataset extractors. Importing this package registers all of them.

To add a dataset: create a file here with a function decorated with @extractor,
import it below and add its name to a detail level in extract_config.yaml.
"""

from network_extraction.datasets import (  # noqa: F401
    buses,
    capacities,
    energy_balance,
    global_constraints,
    prices,
    shedding,
    snapshots,
    summary,
    timeseries,
)
