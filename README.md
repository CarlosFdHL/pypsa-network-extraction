# pypsa-network-extraction

Reduces solved PyPSA-Eur networks to small data files, so that each network is opened only once.
Runs on Sophia. The files are downloaded and analysed by the paper repo **pypsa-multiyear-analysis**
(its `sync.bat` reads `~/projects/pypsa-network-extraction/data` on Sophia).

## Use

1. Edit `extract_config.yaml`: results folder, runs, scenarios, networks, detail level.
2. Run `bash extract.sh` (interactive, e.g. in tmux after `salloc`) or `sbatch extract.sh`.
   If the results are under `/groups`: `sg extremes -c 'bash extract.sh'`.

There are no command-line options: everything is in `extract_config.yaml`.

Extraction is incremental per dataset: a network is opened only if one of the requested datasets is
missing or the network file changed. `force: true` extracts everything again.

## Detail levels

`detail_levels` in the config lists the datasets of each level; levels are cumulative
(`full` = `standard` + `full`). Run entries are `standard` by default. To go deeper into a few
networks of a sweep that is already extracted, add an entry for the same run:

```yaml
runs:
  - name: multi_year_greedy                     # whole sweep, standard
  - name: multi_year_greedy                     # added later
    scenarios: [weather_years_1958_1941_1252seg]
    networks: [design, val_wy1962_3H]
    detail: full
```

Only those networks are opened and only their missing datasets are read.

## Output

See the data layout in the README of pypsa-multiyear-analysis. Per run: `config/` (copy of the run
configs); per scenario: `meta.json`, `capacities.csv`, `buses.csv`; per network (`design`,
`val_wy<year>_<res>`): `snapshots.csv`, `summary.csv`, prices, energy balances and time series.

## Checks (stored in meta.json, printed as warnings)

- weightings: the three columns agree, match the timestamps, each weather year has 8760/8784 h
- capacities_match (validation networks): same capacities as the design network

## Adding a dataset

A new file in `src/network_extraction/datasets/` with an `@extractor` function returning
`{file_name: DataFrame}`, imported in that folder's `__init__.py`, and its name added to a detail
level in `extract_config.yaml`. One functionality per file.

## Layout

```
extract.sh, extract_config.yaml
src/network_extraction/
  cli.py registry.py selection.py discover.py incremental.py meta.py writer.py
  run_configs.py run_checks.py flat_snapshots.py shedding_generators.py weather_year.py config.py
  checks/    capacities_match.py weightings.py
  datasets/  snapshots buses capacities summary shedding prices global_constraints timeseries energy_balance
scripts/make_toy_data.py   toy extracted data, used as test fixture by the paper repo
tests/                     toy PyPSA networks solved with HiGHS
```

## Setup

```bash
pip install -e ".[dev]"     # in the PyPSA environment
pytest
```
