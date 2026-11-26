"""Write extracted data of small toy networks, used as test fixture by the paper repo.

Usage: python scripts/make_toy_data.py <output data folder>
"""

import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).resolve().parents[1] / "tests")]

from network_extraction.cli import run  # noqa: E402
from network_extraction.config import load_extract_config  # noqa: E402
from toy_networks import write_results  # noqa: E402


def main(out):
    with tempfile.TemporaryDirectory() as tmp:
        results = Path(tmp) / "results"
        write_results(results, "toy_run", "single", design_years=[2000], validation_years=[2001])
        write_results(results, "toy_run", "two_years", design_years=[2000, 2003], validation_years=[2001])
        cfg = load_extract_config()
        cfg.update(results_root=results, data_dir=Path(out), runs=[{"name": "toy_run"}])
        cfg["price_carriers"] = ["AC", "urban central heat"]
        run(cfg)


if __name__ == "__main__":
    main(sys.argv[1])
