# Vending Machine Execution Semantics

> Status: Draft Gold Oracle v0.1  
> Requirement source: `dataset/systems/vending_machine.json`  
> IR: Extended EFSM Schema (IR v2)

## 1. Scope

This model represents one drink vending machine and one transaction at a time.

- `insert_coin` represents insertion of a valid coin. Invalid-coin handling is outside the source requirements.
- A transaction begins when a coin is accepted in `Idle`.
- A transaction ends when the user cancels in `CreditAvailable`, or when `dispense_complete` occurs in `Dispensing`.
- The machine can store at most one credit.
- The available drinks are coffee and tea.

## 2. Step semantics

1. A configuration consists of the current control state and current variable values.
2. At each step, the environment supplies at most one input event. The generated SMV model may use `NONE` when no external event occurs.
3. Guards are evaluated over the current configuration.
4. If one transition is enabled, its target state and `updates` become effective in the next configuration.
5. The transition's `outputs` are instantaneous observable effects of that transition. They are emitted once and are not persistent state.
6. Variables not listed in `updates` retain their current values.
7. If no transition matches the current state and event, the machine stutters: state and variables remain unchanged and no output is emitted.
8. More than one enabled transition for the same configuration and event is invalid because the Gold EFSM must be deterministic.

## 3. State and transaction meaning

### Idle

- No transaction is active.
- `creditStored = FALSE`.
- `selectedDrink = NONE`.

### CreditAvailable

- Exactly one credit is stored.
- `creditStored = TRUE`.
- `selectedDrink = NONE`.

### Dispensing

- A paid dispense operation is in progress.
- `creditStored = TRUE` until `dispense_complete`.
- `selectedDrink` is either `COFFEE` or `TEA`.
- Drink-button and cancel events are ignored and produce no output.

## 4. Output semantics

- `DISPENSE_COFFEE`: issued once when a coffee selection starts.
- `DISPENSE_TEA`: issued once when a tea selection starts.
- `RETURN_COIN`: issued once when a stored credit is cancelled.
- `REJECT_COIN`: issued once when an additional coin is inserted while one credit is already stored.
- An empty `outputs` array means that the transition produces no observable business effect.

The current SMV converter does not yet encode transition outputs. The Gold EFSM nevertheless records them as the canonical observable effects for later model checking, code generation, and hidden tests. Output-aware verification must be implemented before the formal-verification treatment experiment.

## 5. Unspecified events

Only state-event combinations explicitly required by R2-R9 and R12-R13 are represented as transitions. Any other combination follows the default stutter rule in Section 2.

This policy avoids adding unsupported Gold transitions while still giving the EFSM a total execution semantics.

## 6. Required invariants

The Gold model is intended to maintain the following invariants:

- `state = Idle -> !creditStored & selectedDrink = NONE`
- `state = CreditAvailable -> creditStored & selectedDrink = NONE`
- `state = Dispensing -> creditStored & (selectedDrink = COFFEE | selectedDrink = TEA)`
- A transaction never selects both coffee and tea.
- A dispense output is never produced without stored credit.
- While dispensing, additional drink selections do not change `selectedDrink`.
- While dispensing, cancel does not terminate the transaction or return a coin.

These invariants will later be formalized in the independently frozen `gold_properties.json`.

## 7. Forbidden trace interpretation

Each `forbidden_behaviours[].trace` starts from the initial configuration and lists input events. The trace itself may be accepted; the `reason` identifies the forbidden state change or output that must not occur along that trace.
