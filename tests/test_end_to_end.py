"""Extraction of toy networks: files, checks, incremental behaviour and agreement with pypsa."""

import copy
import json

import numpy as np
import pandas as pd
import pypsa
import pytest

from network_extraction.cli import run
from network_extraction.config import load_extract_config
from read_output import read
from toy_networks import write_results

RUN, SCEN = "toy_run", "weather_years_2000_2003_seg"
VAL = "val_wy2001_3H"
STANDARD_NETWORK = {
    "snapshots.csv", "summary.csv", "prices.parquet", "global_constraints.csv",
    "generation_by_carrier.parquet", "availability_by_carrier.parquet",
    "link_p0_by_carrier.parquet", "link_p1_by_carrier.parquet", "link_p2_by_carrier.parquet",
    "link_p3_by_carrier.parquet", "link_p4_by_carrier.parquet", "store_e_by_carrier.parquet",
    "store_p_by_carrier.parquet", "storage_unit_p_by_carrier.parquet",
    "storage_unit_soc_by_carrier.parquet", "load_by_carrier.parquet",
    "supply_by_carrier.parquet", "withdrawal_by_carrier.parquet",
    "ac_load.parquet", "energy_totals.csv", "solver_stats.csv",
}


@pytest.fixture(scope="module")
def extracted(tmp_path_factory):
    root = tmp_path_factory.mktemp("work")
    results, data = root / "results", root / "data"
    write_results(results, RUN, SCEN, design_years=[2000, 2003], validation_years=[2001])
    write_results(results, RUN, "single_year_1990", design_years=[1990], validation_years=[1991, 1992])
    cfg = load_extract_config()            # the real extract_config.yaml of the repo
    cfg.update(results_root=results, data_dir=data, runs=[{"name": RUN}])
    cfg["price_carriers"] = ["AC", "urban central heat"]
    run(cfg)
    return cfg, results, data


def network(results, scenario, name):
    return pypsa.Network(str(results / RUN / scenario / "networks" / name))


def test_files_and_meta(extracted):
    _, _, data = extracted
    scen = data / RUN / SCEN
    assert (data / RUN / "config" / "configs" / "config.base.yaml").exists()
    assert {p.name for p in scen.iterdir()} == {"meta.json", "capacities.csv", "buses.csv", "design", VAL}
    assert {p.name for p in (scen / "design").iterdir()} == STANDARD_NETWORK
    assert {p.name for p in (scen / VAL).iterdir()} == STANDARD_NETWORK | {
        "shedding.parquet", "shedding_generators.csv", "marginal_costs.csv"}
    meta = json.loads((scen / "meta.json").read_text())
    for name, entry in meta["networks"].items():
        assert all(v == "ok" for v in entry["checks"].values()), (name, entry["checks"])


def test_second_run_is_incremental(extracted, capsys):
    cfg, _, _ = extracted
    run(cfg)
    assert capsys.readouterr().out.count("up to date") == 5


def test_summary_matches_pypsa(extracted):
    _, results, data = extracted
    n = network(results, SCEN, "weather_year_2001_3H_base_s_1___2050.nc")
    w = n.snapshot_weightings.generators
    shed = n.generators.index[n.generators.carrier.isin(["elec load", "heat shed"])]
    p = n.generators_t.p[shed]
    energy = p.mul(w, axis=0).sum().groupby(n.generators.carrier[shed]).sum()
    cost = (p * n.generators.marginal_cost[shed]).mul(w, axis=0).sum().sum()
    assert energy.sum() > 0, "toy validation network should shed load"

    row = read(data / RUN / SCEN / VAL, "summary").iloc[0]
    assert row.shed_energy_electricity == pytest.approx(energy["elec load"])
    assert row.shed_energy_heat == pytest.approx(energy["heat shed"])
    assert row.shed_cost == pytest.approx(cost)
    assert row.voll_electricity == 1e4 and row.voll_heat == 5e4
    assert row.shed_peak_electricity == pytest.approx(p[shed[n.generators.carrier[shed] == "elec load"]].sum(axis=1).max())
    assert row.objective == pytest.approx(row.opex_excl_shed + row.shed_cost, rel=1e-6)
    assert row.capex == pytest.approx(n.statistics.capex().sum())
    assert row.nyears == pytest.approx(1.0)

    shedding = read(data / RUN / SCEN / VAL, "shedding")
    assert np.allclose(shedding[shed].to_numpy(), p.to_numpy())


def test_design_snapshots_and_nyears(extracted):
    _, _, data = extracted
    row = read(data / RUN / SCEN / "design", "summary").iloc[0]
    assert row.n_shedding_generators == 0 and row.shed_cost == 0.0
    assert row.nyears == pytest.approx((8760 + 8784) / 8760)
    sns = read(data / RUN / SCEN / "design", "snapshots")
    assert sns.groupby("weather_year").generators.sum().to_dict() == {2000: 8760.0, 2003: 8784.0}


def test_capacities_and_buses(extracted):
    _, _, data = extracted
    caps = read(data / RUN / SCEN, "capacities")
    assert caps.loc[("Link", "DE0 0 heat pump"), "efficiency"] == 3.0
    assert "elec load" not in set(caps.carrier)
    assert read(data / RUN / SCEN, "buses").loc["DE0 0", "country"] == "DE"


def test_by_carrier_series(extracted):
    _, results, data = extracted
    n = network(results, SCEN, "weather_year_2001_3H_base_s_1___2050.nc")
    folder = data / RUN / SCEN / VAL
    p2 = read(folder, "link_p2_by_carrier")
    assert list(p2.columns) == ["CHP"]
    assert np.allclose(p2["CHP"], n.links_t.p2["DE0 0 CHP"], rtol=1e-6)
    assert set(read(folder, "load_by_carrier").columns) == {"electricity", "urban central heat"}
    avail = read(folder, "availability_by_carrier")
    expected = n.generators_t.p_max_pu["DE0 0 onwind"] * n.generators.p_nom_opt["DE0 0 onwind"]
    assert np.allclose(avail["wind"], expected, rtol=1e-6)
    assert set(read(folder, "prices").columns) == {"DE0 0", "DE0 0 heat"}


def test_energy_balance_matches_statistics(extracted):
    _, results, data = extracted
    n = network(results, SCEN, "weather_year_2001_3H_base_s_1___2050.nc")
    folder = data / RUN / SCEN / VAL
    w = n.snapshot_weightings.generators
    for name, method in [("supply_by_carrier", n.statistics.supply),
                         ("withdrawal_by_carrier", n.statistics.withdrawal)]:
        df = read(folder, name)
        expected = method(groupby=["carrier", "bus_carrier"], nice_names=False).abs()
        expected = expected.groupby(level=["bus_carrier", "carrier"]).sum()
        got = df.mul(w.to_numpy(), axis=0).sum()
        for key, value in expected[expected > 1].items():
            assert got[key] == pytest.approx(value, rel=1e-5), (name, key)


def test_full_detail_afterwards_only_opens_selected_network(extracted, capsys):
    cfg, _, data = extracted
    cfg = copy.deepcopy(cfg)
    cfg["runs"] = [{"name": RUN, "scenarios": ["single_year_1990"], "networks": ["val_wy1992_3H"],
                    "detail": "full"}]
    run(cfg)
    out = capsys.readouterr().out
    assert "val_wy1992_3H: generation, availability, link_p0" in out
    assert "val_wy1991_3H" not in out and SCEN not in out

    folder = data / RUN / "single_year_1990"
    assert (folder / "val_wy1992_3H" / "link_p2.parquet").exists()
    assert not (folder / "val_wy1991_3H" / "link_p2.parquet").exists()
    gen = read(folder / "val_wy1992_3H", "generation")
    assert "DE0 0 onwind" in gen.columns and gen.dtypes.eq("float32").all()

    run(cfg)
    assert "val_wy1992_3H: up to date" in capsys.readouterr().out
    meta = json.loads((folder / "meta.json").read_text())
    assert "link_p2" in meta["networks"]["val_wy1992_3H"]["datasets"]


def test_shedding_is_compact_float32(extracted):
    cfg, results, data = extracted
    n = network(results, SCEN, "weather_year_2001_3H_base_s_1___2050.nc")
    shed = read(data / RUN / SCEN / VAL, "shedding")
    assert (shed.dtypes == "float32").all()
    raw = n.generators_t.p[shed.columns].to_numpy()
    small = np.abs(raw) < cfg["shedding_zero_tol"]
    assert (shed.to_numpy()[small] == 0).all()
    np.testing.assert_allclose(shed.to_numpy()[~small], raw[~small], rtol=1e-6)


def test_force_list_reextracts_only_listed_datasets(extracted, capsys):
    cfg, _, _ = extracted
    run(dict(cfg, force=["shedding"]))
    out = capsys.readouterr().out
    assert "val_wy2001_3H: shedding" in out          # validation: only shedding
    assert out.count(": shedding") == 3               # the three validation networks
    assert "design: " not in out.replace("design: up to date", "")


def test_new_light_datasets(extracted):
    _, results, data = extracted
    n = network(results, SCEN, "weather_year_2001_3H_base_s_1___2050.nc")
    folder = data / RUN / SCEN / VAL

    load = read(folder, "ac_load")
    assert list(load.columns) == ["DE0 0"]
    np.testing.assert_allclose(load["DE0 0"].to_numpy(), n.loads_t.p_set["DE0 0"].to_numpy(), rtol=1e-6)

    totals = pd.read_csv(folder / "energy_totals.csv", index_col=[0, 1, 2], keep_default_na=False)
    supply = n.statistics.supply(groupby=["bus_carrier", "carrier"], nice_names=False)
    assert totals["supply"].sum() == pytest.approx(supply.sum())
    assert totals.loc[("Generator", "AC", "elec load"), "supply"] > 0

    stats = pd.read_csv(folder / "solver_stats.csv")
    assert not stats.log_found.iloc[0]          # toy results have no solver logs

    mc = pd.read_csv(folder / "marginal_costs.csv", index_col=[0, 1])
    assert mc.loc[("Generator", "DE0 0 OCGT"), "marginal_cost"] == pytest.approx(80.0)

    assert np.isnan(read(folder, "summary").co2_atmosphere_net.iloc[0])


def test_light_detail_and_price_override(tmp_path):
    results, data = tmp_path / "results", tmp_path / "data"
    write_results(results, RUN, "single_year_1990", design_years=[1990], validation_years=[1991])
    cfg = load_extract_config()
    cfg.update(results_root=results, data_dir=data,
               runs=[{"name": RUN, "detail": "light", "price_carriers": ["urban central heat"]},
                     {"name": "missing_run"}])
    run(cfg)
    folder = data / RUN / "single_year_1990" / "val_wy1991_3H"
    assert not (folder / "shedding.parquet").exists()
    assert not (folder / "generation_by_carrier.parquet").exists()
    assert list(read(folder, "prices").columns) == ["DE0 0 heat"]


def test_explicit_dataset_list(tmp_path):
    results, data = tmp_path / "results", tmp_path / "data"
    write_results(results, RUN, "single_year_1990", design_years=[1990], validation_years=[1991, 1992])
    cfg = load_extract_config()
    cfg.update(results_root=results, data_dir=data,
               runs=[{"name": RUN, "networks": ["design", "val_wy1991_3H"],
                      "datasets": ["buses", "capacities", "summary", "energy_totals"]}])
    run(cfg)
    scen = data / RUN / "single_year_1990"
    assert {p.name for p in scen.iterdir()} == {"meta.json", "buses.csv", "capacities.csv", "design",
                                                "val_wy1991_3H"}
    assert {p.name for p in (scen / "val_wy1991_3H").iterdir()} == {"summary.csv", "energy_totals.csv"}
    with pytest.raises(ValueError, match="Unknown datasets"):
        run(dict(cfg, runs=[{"name": RUN, "datasets": ["sumary"]}]))


def test_force_per_run_entry(extracted, capsys):
    cfg, _, _ = extracted
    run(dict(cfg, runs=[{"name": RUN, "networks": ["val_wy2001_3H"], "force": ["summary"]}]))
    out = capsys.readouterr().out
    assert "val_wy2001_3H: summary" in out and "design" not in out.split("networks")[-1].split("\n", 1)[1]
