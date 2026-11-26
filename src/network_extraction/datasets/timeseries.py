"""Time series of every component, at two levels of detail.

<name>.parquet             one column per asset (full detail). Assets that are zero in every snapshot
                           are dropped: a missing column means zero. Static data of each asset
                           (carrier, buses, capacity, efficiency...) is in capacities.csv.
<name>_by_carrier.parquet  summed by carrier over all of Europe (standard detail).

All values float32, in the units of the model (MW, MWh; t or kt for CO2 buses).
"""

import pandas as pd

from network_extraction.flat_snapshots import flat_snapshots
from network_extraction.registry import extractor

# name: (static list, dynamic list, attribute, also by carrier)
SPECS = {
    "generation": ("generators", "generators_t", "p", True),
    "link_p0": ("links", "links_t", "p0", True),
    "link_p1": ("links", "links_t", "p1", True),
    "link_p2": ("links", "links_t", "p2", True),
    "link_p3": ("links", "links_t", "p3", True),
    "link_p4": ("links", "links_t", "p4", True),
    "store_e": ("stores", "stores_t", "e", True),
    "store_p": ("stores", "stores_t", "p", True),
    "storage_unit_p": ("storage_units", "storage_units_t", "p", True),
    "storage_unit_soc": ("storage_units", "storage_units_t", "state_of_charge", True),
    "line_p0": ("lines", "lines_t", "p0", False),     # summing line flows has no meaning
    "load": ("loads", "loads_t", "p", True),
}


def assets_with_port(static, attr):
    """Links only have p2, p3, ... if the corresponding bus is set."""
    if not attr.startswith("p") or not attr[1:].isdigit() or attr == "p0":
        return static.index
    bus = f"bus{attr[1:]}"
    if bus not in static:
        return static.index[:0]
    return static.index[static[bus].fillna("").astype(str) != ""]


def asset_series(n, static_name, dynamic_name, attr):
    """Time series of one attribute for all assets (zero-filled for assets without a column)."""
    static = getattr(n, static_name)
    dynamic = getattr(getattr(n, dynamic_name), attr, pd.DataFrame())
    assets = assets_with_port(static, attr)
    df = dynamic.reindex(columns=assets, fill_value=0.0)
    df.index = flat_snapshots(n)
    df.columns.name = "name"
    return df.astype("float32")


def group_key(n, static_name, columns):
    """Carrier of each asset; loads without a carrier take the carrier of their bus."""
    static = getattr(n, static_name).loc[columns]
    carrier = static["carrier"].fillna("").astype(str)
    if static_name == "loads":
        carrier = carrier.where(carrier != "", static["bus"].map(n.buses["carrier"]))
    return carrier


def by_carrier(df, key):
    out = df.T.groupby(key.to_numpy()).sum().T
    out.columns.name = "carrier"
    return out.astype("float32")


def drop_zero_columns(df):
    return df.loc[:, (df != 0).any()]


def make_extractors(name, static_name, dynamic_name, attr, with_carrier):
    @extractor(name)
    def extract_assets(n, cfg):
        return {f"{name}.parquet": drop_zero_columns(asset_series(n, static_name, dynamic_name, attr))}

    if with_carrier:
        @extractor(f"{name}_by_carrier")
        def extract_by_carrier(n, cfg):
            df = asset_series(n, static_name, dynamic_name, attr)
            return {f"{name}_by_carrier.parquet": by_carrier(df, group_key(n, static_name, df.columns))}


for _name, _spec in SPECS.items():
    make_extractors(_name, *_spec)


# Availability of generators: p_max_pu per asset (full) and available power in MW by carrier (standard)

@extractor("availability")
def extract_availability(n, cfg):
    """Time-varying p_max_pu per generator (static values are in capacities.csv)."""
    df = n.generators_t.p_max_pu.copy()
    df.index = flat_snapshots(n)
    df.columns.name = "name"
    return {"availability.parquet": df.astype("float32")}


@extractor("availability_by_carrier")
def extract_availability_by_carrier(n, cfg):
    """Available power [MW] = p_max_pu * p_nom_opt, summed by carrier."""
    p_max_pu = n.get_switchable_as_dense("Generator", "p_max_pu")
    available = p_max_pu * n.generators["p_nom_opt"]
    available.index = flat_snapshots(n)
    key = group_key(n, "generators", available.columns)
    return {"availability_by_carrier.parquet": by_carrier(available, key)}
