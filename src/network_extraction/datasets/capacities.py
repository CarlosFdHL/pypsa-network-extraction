"""capacities.csv (scenario level): every asset of the design network with its optimal capacity.

One row per asset. Columns: component, name, carrier, bus columns, country (of the first bus),
extendable, nom, nom_min, nom_max, nom_opt, capital_cost, efficiency columns and, where the
component has them, marginal_cost, p_min_pu, p_max_pu (static values), max_hours, length, lifetime.
"""

import re

import pandas as pd

from network_extraction.registry import extractor

# component: (list name, capacity attribute)
COMPONENTS = {
    "Generator": ("generators", "p_nom"),
    "Link": ("links", "p_nom"),
    "Store": ("stores", "e_nom"),
    "StorageUnit": ("storage_units", "p_nom"),
    "Line": ("lines", "s_nom"),
    "Transformer": ("transformers", "s_nom"),
}

BUS_COLUMN = re.compile(r"^bus\d*$")
EFFICIENCY_COLUMN = re.compile(r"^efficiency\d*$")
OPTIONAL_COLUMNS = ["marginal_cost", "p_min_pu", "p_max_pu", "max_hours", "length", "lifetime"]


def component_table(n, component, list_name, attr):
    df = getattr(n, list_name)
    if df.empty:
        return None
    bus_cols = sorted((c for c in df.columns if BUS_COLUMN.match(c)), key=lambda c: (len(c), c))
    eff_cols = sorted((c for c in df.columns if EFFICIENCY_COLUMN.match(c)), key=lambda c: (len(c), c))
    first_bus = df[bus_cols[0]]

    out = pd.DataFrame({
        "component": component,
        "carrier": df["carrier"],
        "country": first_bus.map(n.buses["country"]) if "country" in n.buses else None,
        "extendable": df[f"{attr}_extendable"].astype(bool),
        "nom": df[attr],
        "nom_min": df[f"{attr}_min"],
        "nom_max": df[f"{attr}_max"],
        "nom_opt": df[f"{attr}_opt"],
        "capital_cost": df["capital_cost"],
    }, index=df.index)
    for col in bus_cols + eff_cols:
        out[col] = df[col]
    for col in OPTIONAL_COLUMNS:
        if col in df:
            out[col] = df[col]
    return out


def capacity_table(n):
    parts = [component_table(n, comp, list_name, attr)
             for comp, (list_name, attr) in COMPONENTS.items()]
    table = pd.concat([p for p in parts if p is not None])
    table.index.name = "name"
    return table.set_index("component", append=True).swaplevel()


@extractor("capacities", level="scenario")
def extract_capacities(n, cfg):
    return {"capacities.csv": capacity_table(n)}
