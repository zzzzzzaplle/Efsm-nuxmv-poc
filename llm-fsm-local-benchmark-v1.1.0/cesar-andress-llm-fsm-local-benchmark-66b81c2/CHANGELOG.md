# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-02

### v0.1.0 – Initial Dataset and Experimental Framework

This release provides the first public version of the LLM-FSM Local Benchmark.

#### Dataset

- 20 software systems
- 10–20 requirements per system
- JSON representation
- Benchmark index and metadata (`dataset/index.json`)

Domains include:

- ATM, Vending Machine, Elevator, Login System, Parking Gate, Ticket Machine
- Hotel Booking, Library Loan, Access Control, Smart Thermostat
- E-commerce checkout, medical appointments, bike rental, warehouse inventory
- Online examination, car rental, package locker, restaurant reservation
- Train ticket booking, gym membership

#### Experimental Framework

- Prompt templates for FSM generation (`prompts/`)
- Benchmark execution scripts (`scripts/run_experiment.py`)
- Model availability checks (`scripts/check_models.py`)
- Evaluation pipeline (`scripts/evaluate.py`)
- Result aggregation utilities (`results/metrics.csv`)
- Figure generation utilities (`scripts/plot_results.py`)
- CI validation workflow (`.github/workflows/validate.yml`)

#### Research Documentation (included in v0.1.0)

- `docs/evaluation_protocol.md` — research questions, hypotheses, metrics, threats to validity
- `docs/gold_standard_strategy.md` — methodology for authoring and validating gold FSMs
- `benchmark/gold/*.json` — placeholders (20 systems; full gold FSMs pending)
- `REPRODUCIBILITY.md` — local Ollama reproduction guide
- `docs/dataset.md` — dataset schema and domain catalog

#### Research Goal

The project investigates the ability of local open-source large language models to generate deterministic finite state machines (FSMs) from natural language requirements.

The benchmark is designed to support reproducible experimentation using local models executed through Ollama.

#### Planned for Future Releases

- Completed gold-standard FSMs (replacing `{}` placeholders)
- Baseline model results (full 20 × 6 model matrix)
- Statistical analyses
- Publication artifacts and Zenodo DOI

#### Status

Initial infrastructure release establishing the benchmark dataset, experimental framework, and evaluation documentation.

The benchmark is under active development.

#### Citation

Please use the Zenodo DOI associated with this release once available. See `CITATION.cff`.

[0.1.0]: https://github.com/cesar-andress/llm-fsm-local-benchmark/releases/tag/v0.1.0
