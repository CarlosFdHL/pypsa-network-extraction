"""Load-shedding generators of a network and their type (electricity, heat, ...)."""

import pandas as pd


def shedding_types(cfg):
    """{carrier: type} from shedding_carriers in extract_config.yaml."""
    return {carrier: kind for kind, carrier in cfg["shedding_carriers"].items()}


def shedding_generators(n, cfg):
    """Series generator name -> type, for the load-shedding generators of the network."""
    types = shedding_types(cfg)
    carriers = n.generators.carrier
    gens = carriers.index[carriers.isin(types)]
    return pd.Series(carriers[gens].map(types).values, index=gens, name="type")
