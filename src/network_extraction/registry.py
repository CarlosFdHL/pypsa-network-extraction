"""Registry of dataset extractors.

An extractor is a function `func(n, cfg) -> {file_name: DataFrame}`. Register it with

    @extractor("name", level="network", roles=("design", "validation"))

with_path=True: the function also gets the NetworkFile, `func(n, cfg, network_file)`, for data
read from files next to the network (e.g. solver logs).

level="network":  files go to data/<run>/<scenario>/<network>/
level="scenario": files go to data/<run>/<scenario>/ and are taken from the design network only
"""

from dataclasses import dataclass
from typing import Callable

EXTRACTORS = {}


@dataclass(frozen=True)
class Extractor:
    name: str
    func: Callable
    level: str
    roles: tuple
    with_path: bool = False

    def run(self, n, cfg, network_file):
        return self.func(n, cfg, network_file) if self.with_path else self.func(n, cfg)


def extractor(name, level="network", roles=("design", "validation"), with_path=False):
    if level not in ("network", "scenario"):
        raise ValueError(f"Unknown level {level!r}")
    if level == "scenario":
        roles = ("design",)

    def register(func):
        if name in EXTRACTORS:
            raise ValueError(f"Extractor {name!r} registered twice")
        EXTRACTORS[name] = Extractor(name, func, level, tuple(roles), with_path)
        return func

    return register


def selected_extractors(names):
    """Extractors listed in the config, in that order."""
    unknown = [name for name in names if name not in EXTRACTORS]
    if unknown:
        raise ValueError(f"Unknown datasets in extract_config.yaml: {unknown}. "
                         f"Available: {sorted(EXTRACTORS)}")
    return [EXTRACTORS[name] for name in names]
