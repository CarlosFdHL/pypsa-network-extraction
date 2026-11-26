#!/usr/bin/env bash
# Extract data from the PyPSA networks on Sophia. All settings are in extract_config.yaml.
# Interactive: ./extract.sh      Batch job: sbatch extract.sh
#SBATCH --job-name=extract
#SBATCH --partition=workq
#SBATCH --time=04:00:00
#SBATCH --mem=32G
#SBATCH --output=extract_%j.log

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")}"
PYTHONPATH=src python -m network_extraction.cli
