import importlib.util
import json
import unittest
from pathlib import Path

# 测试了
ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "efsm_to_smv.py"
SPEC = importlib.util.spec_from_file_location("efsm_to_smv", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OutputEncodingTests(unittest.TestCase):
    def setUp(self) -> None:
        base = ROOT / "benchmarks" / "fsm_bench_20_fv" / "vending_machine"
        self.model = json.loads(
            (base / "oracle" / "gold_efsm.json").read_text(encoding="utf-8")
        )
        self.interface = json.loads(
            (base / "system_interface.json").read_text(encoding="utf-8")
        )

    def test_declared_outputs_become_instantaneous_defines(self) -> None:
        smv = MODULE.generate_smv(
            self.model,
            output_events=self.interface["output_events"],
        )

        self.assertIn("DEFINE", smv)
        self.assertIn("emit_DISPENSE_COFFEE :=", smv)
        self.assertIn(
            "state = CreditAvailable & event = press_coffee",
            smv,
        )
        self.assertIn("emit_RETURN_COIN :=", smv)

    def test_environment_event_is_ctl_observable(self) -> None:
        smv = MODULE.generate_smv(
            self.model,
            output_events=self.interface["output_events"],
        )

        self.assertNotIn("IVAR", smv)
        self.assertIn(
            "init(event) := {NONE, insert_coin, press_coffee, "
            "press_tea, cancel, dispense_complete};",
            smv,
        )
        self.assertIn(
            "next(event) := {NONE, insert_coin, press_coffee, "
            "press_tea, cancel, dispense_complete};",
            smv,
        )

    def test_missing_candidate_output_is_still_defined_false(self) -> None:
        candidate = json.loads(json.dumps(self.model))
        for transition in candidate["transitions"]:
            transition["outputs"] = [
                output_name
                for output_name in transition.get("outputs", [])
                if output_name != "RETURN_COIN"
            ]

        smv = MODULE.generate_smv(
            candidate,
            output_events=self.interface["output_events"],
        )

        self.assertIn("emit_RETURN_COIN := FALSE;", smv)

    def test_undeclared_output_is_rejected(self) -> None:
        candidate = json.loads(json.dumps(self.model))
        candidate["transitions"][0]["outputs"] = ["TYPO_OUTPUT"]

        with self.assertRaisesRegex(ValueError, "TYPO_OUTPUT"):
            MODULE.validate_semantics(
                candidate,
                declared_outputs=set(self.interface["output_events"]),
            )

    def test_smv_expression_sanitization(self) -> None:
        raw_guard = "creditStored == true && selectedDrink == NONE || flag == false"
        sanitized = MODULE.sanitize_smv_expression(raw_guard)
        self.assertEqual(
            sanitized,
            "creditStored = TRUE & selectedDrink = NONE | flag = FALSE",
        )


if __name__ == "__main__":
    unittest.main()
