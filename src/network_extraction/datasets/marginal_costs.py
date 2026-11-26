"""marginal_costs.csv (validation networks): static marginal cost of every generator, link,
store and storage unit [EUR/MWh].

The design values are in capacities.csv. Comparing both gives e.g. the CO2 price that was added
to the marginal costs of the validation runs.
"""

import pandas as pd

from network_extraction.registry import extractor

COMPONENTS = {"Generator": "generators", "Link": "links", "Store": "stores", "StorageUnit": "storage_units"}


def marginal_costs(n):
    parts = {comp: getattr(n, name)["marginal_cost"] for comp, name in COMPONENTS.items()
             if not getattr(n, name).empty}
    df = pd.concat(parts, names=["component", "name"]).rename("marginal_cost").to_frame()
    return df


@extractor("marginal_costs", roles=("validation",))
def extract_marginal_costs(n, cfg):
    return {"marginal_costs.csv": marginal_costs(n)}
