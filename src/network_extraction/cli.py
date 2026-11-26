"""Entry point of the extraction. All settings come from extract_config.yaml (run ./extract.sh)."""

import gc

from network_extraction.config import load_extract_config
from network_extraction import datasets  # noqa: F401  (registers the extractors)
from network_extraction.discover import find_networks, find_scenarios
from network_extraction.incremental import needs_extraction
from network_extraction.meta import (git_commit, load_meta, network_entry, now,
                                             record_dataset, save_meta)
from network_extraction.registry import selected_extractors
from network_extraction.run_checks import run_checks
from network_extraction.run_configs import copy_run_configs
from network_extraction.selection import network_selected, run_datasets
from network_extraction.writer import write_files


def pending_extractors(extractors, network_file, entry, meta, network_out, scenario_out, cfg):
    """Extractors that apply to this network and are not up to date."""
    mtime = entry["source_mtime"]
    todo = []
    for ex in extractors:
        if network_file.role not in ex.roles:
            continue
        if ex.level == "scenario":
            record, folder = meta["scenario_datasets"].get(ex.name), scenario_out
        else:
            record, folder = entry["datasets"].get(ex.name), network_out
        if needs_extraction(record, folder, mtime, cfg["force"]):
            todo.append(ex)
    return todo


def extract_network(network_file, extractors, meta, scenario_out, cfg, info):
    import pypsa

    entry = network_entry(meta, network_file)
    network_out = scenario_out / network_file.name
    todo = pending_extractors(extractors, network_file, entry, meta, network_out, scenario_out, cfg)
    if not todo:
        print(f"  {network_file.name}: up to date")
        return

    print(f"  {network_file.name}: {', '.join(ex.name for ex in todo)}")
    n = pypsa.Network(str(network_file.path))
    for ex in todo:
        folder = scenario_out if ex.level == "scenario" else network_out
        files = write_files(ex.func(n, cfg), folder, cfg["timeseries_format"])
        target = meta["scenario_datasets"] if ex.level == "scenario" else entry["datasets"]
        record_dataset(target, ex.name, files, entry["source_mtime"], info)
        if ex.level == "scenario":
            meta["design_source"] = entry["source"]

    entry["checks"] = run_checks(n, network_file, scenario_out, cfg)
    entry["checked_at"] = now()
    save_meta(scenario_out, meta)
    del n
    gc.collect()


def extract_run(run, cfg, info):
    run_dir = cfg["results_root"] / run["name"]
    run_out = cfg["data_dir"] / run["name"]
    extractors = selected_extractors(run_datasets(run, cfg))
    print(f"Run {run['name']} (detail: {run.get('detail', 'standard')}, "
          f"scenarios: {run.get('scenarios', 'all')}, networks: {run.get('networks', 'all')})")

    copied = copy_run_configs(run_dir, run_out / "config", cfg.get("run_config_globs", []))
    if copied:
        print(f"  copied {len(copied)} config files")

    for scenario_dir in find_scenarios(run_dir, run.get("scenarios", "all")):
        print(f" Scenario {scenario_dir.name}")
        scenario_out = run_out / scenario_dir.name
        meta = load_meta(scenario_out, run["name"], scenario_dir.name)
        networks = find_networks(scenario_dir, cfg["design_pattern"], cfg["validation_pattern"])
        for network_file in networks:
            if network_selected(network_file, run, cfg):
                extract_network(network_file, extractors, meta, scenario_out, cfg, info)


def run(cfg):
    import pypsa

    info = {"code_commit": git_commit(), "pypsa_version": pypsa.__version__}
    print(f"Extracting into {cfg['data_dir']} "
          f"(code {info['code_commit']}, pypsa {info['pypsa_version']}, force={cfg['force']})")
    for run_cfg in cfg["runs"]:
        extract_run(run_cfg, cfg, info)
    print("Done")


def main():
    run(load_extract_config())


if __name__ == "__main__":
    main()
