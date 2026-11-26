"""buses.csv (scenario level): carrier, location, country, coordinates and unit of every bus."""

from network_extraction.registry import extractor

COLUMNS = ["carrier", "location", "country", "x", "y", "unit"]


@extractor("buses", level="scenario")
def extract_buses(n, cfg):
    return {"buses.csv": n.buses[[c for c in COLUMNS if c in n.buses]].rename_axis("name")}
