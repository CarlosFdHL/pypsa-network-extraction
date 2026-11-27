"""What to extract for each entry of `runs` in extract_config.yaml.

Detail levels are cumulative, in the order written in `detail_levels`:
choosing "full" extracts the datasets of "light", "standard" and "full".
A run entry can instead list exactly the datasets it needs with `datasets: [...]`.
"""

DEFAULT_DETAIL = "standard"


def datasets_for_detail(detail_levels, detail):
    """Dataset names of `detail` and of every level listed before it."""
    names = list(detail_levels)
    if detail not in detail_levels:
        raise ValueError(f"Unknown detail level {detail!r}. Available: {names}")
    datasets = []
    for level in names[: names.index(detail) + 1]:
        datasets += [d for d in detail_levels[level] if d not in datasets]
    return datasets


def run_datasets(run_cfg, cfg):
    if "datasets" in run_cfg:             # explicit list: overrides detail
        known = {d for level in cfg["detail_levels"].values() for d in level}
        unknown = [d for d in run_cfg["datasets"] if d not in known]
        if unknown:
            raise ValueError(f"Unknown datasets {unknown} in run {run_cfg['name']}. Available: {sorted(known)}")
        return list(run_cfg["datasets"])
    return datasets_for_detail(cfg["detail_levels"], run_cfg.get("detail", DEFAULT_DETAIL))


def network_selected(network_file, run_cfg, cfg):
    """Role allowed (run entry or global `roles`) and name in the run entry's `networks`, if given."""
    roles = run_cfg.get("roles", cfg["roles"])
    networks = run_cfg.get("networks", "all")
    return network_file.role in roles and (networks == "all" or network_file.name in networks)
