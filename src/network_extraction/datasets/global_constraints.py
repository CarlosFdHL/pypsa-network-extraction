"""global_constraints.csv: type, sense, constant and shadow price (mu) of each global constraint."""

from network_extraction.registry import extractor

COLUMNS = ["type", "carrier_attribute", "sense", "constant", "mu"]


@extractor("global_constraints")
def extract_global_constraints(n, cfg):
    gc = n.global_constraints
    return {"global_constraints.csv": gc[[c for c in COLUMNS if c in gc]].rename_axis("name")}
