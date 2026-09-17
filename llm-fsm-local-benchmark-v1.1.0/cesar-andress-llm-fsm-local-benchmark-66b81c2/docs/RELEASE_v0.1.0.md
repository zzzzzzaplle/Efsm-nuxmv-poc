# Release v0.1.0 – Initial Dataset and Experimental Framework

**Date:** 2026-06-02  
**Tag:** `v0.1.0`

This release provides the first public version of the LLM-FSM Local Benchmark.

---

## Contents

### Dataset

- 20 software systems
- 10–20 requirements per system
- JSON representation
- Benchmark index and metadata

Domains include:

- ATM
- Vending Machine
- Elevator
- Login System
- Parking Gate
- Ticket Machine
- Hotel Booking
- Library Loan
- Access Control
- Smart Thermostat
- And additional software engineering benchmark systems

### Experimental Framework

- Prompt templates for FSM generation
- Benchmark execution scripts
- Evaluation pipeline
- Result aggregation utilities
- Figure generation utilities
- GitHub Actions validation workflow

### Research Documentation (included in v0.1.0)

This release already ships draft research artifacts:

| Document | Description |
|----------|-------------|
| `docs/evaluation_protocol.md` | Research questions, hypotheses, variables, metrics |
| `docs/gold_standard_strategy.md` | Gold FSM authoring, validation, and comparison methodology |
| `benchmark/gold/*.json` | Placeholder files for 20 systems (full gold FSMs pending) |
| `REPRODUCIBILITY.md` | Step-by-step local reproduction with Ollama |
| `docs/dataset.md` | Dataset schema and domain catalog |

### Research Goal

The project investigates the ability of local open-source large language models to generate deterministic finite state machines (FSMs) from natural language requirements.

The benchmark is designed to support reproducible experimentation using local models executed through Ollama.

### Planned for Future Releases

- Completed gold-standard FSMs
- Baseline model results (full experiment matrix)
- Statistical analyses
- Publication artifacts
- Zenodo DOI

### Status

This is an initial infrastructure release intended to establish the benchmark dataset and experimental framework.

The benchmark is currently under active development.

### Citation

Please use the Zenodo DOI associated with this release once available. See `CITATION.cff`.

### Quick Start

```bash
git clone git@github.com:cesar-andress/llm-fsm-local-benchmark.git
cd llm-fsm-local-benchmark
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3.12 scripts/validate_integrity.py
python3.12 scripts/check_models.py
```

See `REPRODUCIBILITY.md` for the full experiment pipeline.
