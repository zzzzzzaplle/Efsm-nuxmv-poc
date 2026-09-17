# FSM-Bench-20

Benchmark dataset for evaluating how well large language models (LLMs) generate **deterministic finite state machines (FSMs)** from natural language software requirements.

The dataset contains **20 software systems** drawn from classic and contemporary software engineering domains. Each system is specified as a numbered list of unambiguous requirements suitable for formalization, model-based testing (MBT), and consistency checking against generated FSMs.

## Directory structure

```text
benchmark/
├── README.md                 # This file
├── index.json                # Dataset metadata and system catalog
└── systems/
    ├── vending_machine.json
    ├── atm.json
    ├── login_system.json
    ├── parking_gate.json
    ├── elevator.json
    ├── library_loan.json
    ├── hotel_booking.json
    ├── ticket_machine.json
    ├── ecommerce_checkout.json
    ├── smart_thermostat.json
    ├── access_control.json
    ├── medical_appointment_booking.json
    ├── bike_rental.json
    ├── warehouse_inventory.json
    ├── online_examination.json
    ├── car_rental.json
    ├── package_locker.json
    ├── restaurant_reservation.json
    ├── train_ticket_booking.json
    └── gym_membership.json
```

## System file schema

Each file in `systems/` is a JSON object with the following structure:

```json
{
  "system_name": "Human-readable name of the system",
  "domain": "Application domain label",
  "requirements": [
    "R1: ...",
    "R2: ...",
    "R3: ..."
  ]
}
```

### Field descriptions

| Field | Type | Description |
|-------|------|-------------|
| `system_name` | string | Descriptive name used in papers and experiment logs |
| `domain` | string | Domain category for stratified analysis |
| `requirements` | array of strings | Numbered requirements (`R1`, `R2`, …) in natural language |

## Dataset properties

| Property | Value |
|----------|-------|
| Number of systems | 20 |
| Requirements per system | 12–13 (within the 10–20 target range) |
| Requirement format | `R<n>: <single testable statement>` |
| Initial state | Every system defines an explicit initial state in `R1` |
| Safety/consistency rules | Most systems include invariant requirements (e.g., “must not … unless …”) |
| Domains covered | All 20 requested application domains |

## Domains

1. Vending machine — `vending_machine.json`
2. ATM — `atm.json`
3. Login system — `login_system.json`
4. Parking gate — `parking_gate.json`
5. Elevator — `elevator.json`
6. Library loan — `library_loan.json`
7. Hotel booking — `hotel_booking.json`
8. Ticket machine — `ticket_machine.json`
9. E-commerce checkout — `ecommerce_checkout.json`
10. Smart thermostat — `smart_thermostat.json`
11. Access control — `access_control.json`
12. Medical appointment booking — `medical_appointment_booking.json`
13. Bike rental — `bike_rental.json`
14. Warehouse inventory — `warehouse_inventory.json`
15. Online examination — `online_examination.json`
16. Car rental — `car_rental.json`
17. Package locker — `package_locker.json`
18. Restaurant reservation — `restaurant_reservation.json`
19. Train ticket booking — `train_ticket_booking.json`
20. Gym membership — `gym_membership.json`

## Requirement authoring guidelines

Requirements in this dataset follow these conventions to support reproducible LLM evaluation:

1. **Numbered identifiers** — Each requirement starts with `R1`, `R2`, etc.
2. **Single responsibility** — One state change, guard, or invariant per requirement where possible.
3. **Explicit states** — State names appear in `PascalCase` or descriptive phrases (e.g., `Idle`, `CreditAvailable`).
4. **Deterministic triggers** — Events are phrased as “When … while in …” to reduce ambiguity.
5. **Negative constraints** — Safety properties use “must not” for forbidden behaviour and negative test generation.
6. **Initial state in R1** — Enables automatic checking of `initial_state` in generated FSMs.

## Suggested experimental protocol

### 1. Prompt each LLM

Provide only the `requirements` array (or the full system JSON) and ask the model to produce a deterministic FSM, for example:

```json
{
  "states": [],
  "initial_state": "",
  "events": [],
  "transitions": [
    {
      "source": "",
      "event": "",
      "guard": "",
      "action": "",
      "target": "",
      "requirement": ""
    }
  ]
}
```

### 2. Evaluate generated FSMs

Recommended metrics:

- **Requirement coverage** — fraction of requirements mapped to at least one transition or state
- **Transition support** — fraction of transitions justified by a requirement
- **Determinism** — no `(source, event)` pair with multiple conflicting transitions
- **Reachability** — all states reachable from `initial_state`
- **Invariant violations** — negative traces that violate “must not” requirements

### 3. Stratify results

Use the `domain` field in `index.json` to compare performance across application types (transaction systems vs. access control vs. booking flows).

## Loading the dataset

Example (Python):

```python
import json
from pathlib import Path

root = Path("benchmark")
catalog = json.loads((root / "index.json").read_text())

systems = []
for entry in catalog["systems"]:
    path = root / entry["file"]
    systems.append(json.loads(path.read_text()))

print(f"Loaded {len(systems)} systems")
print(systems[0]["system_name"], len(systems[0]["requirements"]))
```

Example (Node.js):

```javascript
const fs = require("fs");
const path = require("path");

const root = path.join("benchmark");
const catalog = JSON.parse(fs.readFileSync(path.join(root, "index.json"), "utf8"));
const systems = catalog.systems.map((entry) =>
  JSON.parse(fs.readFileSync(path.join(root, entry.file), "utf8"))
);
console.log(`Loaded ${systems.length} systems`);
```

## Ground truth (optional extension)

This release contains **requirements only**. For supervised evaluation, you may extend the dataset with reference FSMs under `benchmark/gold/` using the same filenames. Reference machines should:

- Be deterministic
- Include a `requirement` traceability field on every transition
- Declare `forbidden_behaviours` for negative MBT cases

## Citation

If you use this dataset in a publication, cite it as:

> FSM-Bench-20: A benchmark of 20 natural-language requirement specifications for evaluating LLM-generated deterministic finite state machines.

## Version history

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-06-02 | Initial release with 20 systems |
