#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3.12}"
VENV=".venv"

echo "==> Project root: $ROOT"

if [[ ! -d "$VENV" ]]; then
  echo "==> Creating virtual environment"
  "$PYTHON" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Checking Ollama models"
INCLUDE_OPT=()
if [[ "${INCLUDE_OPTIONAL:-0}" == "1" ]]; then
  INCLUDE_OPT=(--include-optional)
fi
python scripts/check_models.py "${INCLUDE_OPT[@]}"

echo "==> Running experiment"
RUN_OPT=()
if [[ "${INCLUDE_OPTIONAL:-0}" == "1" ]]; then
  RUN_OPT=(--include-optional)
fi
if [[ -n "${MODELS:-}" ]]; then
  # shellcheck disable=SC2206
  RUN_OPT+=(--models ${MODELS})
fi
if [[ -n "${SYSTEMS:-}" ]]; then
  # shellcheck disable=SC2206
  RUN_OPT+=(--systems ${SYSTEMS})
fi
python scripts/run_experiment.py "${RUN_OPT[@]}"

echo "==> Evaluating metrics"
python scripts/evaluate.py

echo "==> Plotting figures"
python scripts/plot_results.py

echo "==> Done"
echo "CSV:     results/metrics.csv"
echo "Figures: figures/"
