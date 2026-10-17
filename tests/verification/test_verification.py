"""Deliberate corruptions keep exact acceptance and component reports independent."""

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.verification import main
from tools.baseline.data import read_json, sha256


class VerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.golden = read_json(main.SIMULATOR / "reference/small-lattice-v1.json")

    def candidate(self):
        actual = copy.deepcopy(self.golden)
        actual["backend"] = "threaded-uniform-grid-pbf-binary32-8-jacobi-v2"
        actual["metadata"]["backend"] = actual["backend"]
        actual["metadata"]["run_id"] = "different-execution"
        actual["execution"] = {"mode": "threaded", "workers": 3}
        return actual

    def test_complete_exact_values_have_zero_error_and_all_components(self):
        report = main.compare(self.golden, self.candidate())
        self.assertTrue(report["passed"])
        self.assertIsNone(report["first_divergent_checkpoint"])
        self.assertEqual(len(report["checkpoints"]), 4)
        for checkpoint in report["checkpoints"]:
            for quantity in checkpoint["snapshot"]["quantities"].values():
                self.assertEqual(quantity["particles"], 27)
                self.assertEqual(quantity["components"], 81)
                self.assertEqual(quantity["maximum_absolute"], 0)
                self.assertEqual(quantity["rms"], 0)
                self.assertTrue(quantity["passed"])
            self.assertTrue(checkpoint["audit"]["passed"])

    def test_component_report_retains_worst_identity_axis_and_checkpoint(self):
        actual = self.candidate()
        p = actual["checkpoints"][1]["snapshot"]["particles"][4]
        p["position_m"]["z"] += 0.25
        report = main.compare(self.golden, actual)
        self.assertFalse(report["passed"])
        self.assertEqual(report["first_divergent_checkpoint"], "1")
        position = report["checkpoints"][1]["snapshot"]["quantities"]["position_m"]
        self.assertEqual(position["worst"], {"identity": p["identity"], "axis": "z"})
        self.assertAlmostEqual(position["maximum_absolute"], 0.25, places=6)
        self.assertAlmostEqual(position["rms"], 0.25 / 9, places=6)
        self.assertFalse(position["passed"])

    def test_signed_zero_nonfinite_structure_cfl_audit_and_status_cannot_hide(self):
        self.assertTrue(main.disagreements(-0.0, 0.0))
        self.assertTrue(main.disagreements(float("nan"), float("nan")))
        self.assertTrue(main.disagreements(0.0, 1e100))
        for change in (
            lambda d: d["checkpoints"].pop(1),
            lambda d: d["checkpoints"][0]["snapshot"]["particles"].reverse(),
            lambda d: d["steps"][0].update(warning=True),
            lambda d: d["checkpoints"][1].update(density=None),
            lambda d: d.update(status="cancelled"),
            lambda d: d["metadata"].update(input_id="wrong-input"),
        ):
            actual = self.candidate()
            change(actual)
            self.assertFalse(main.compare(self.golden, actual)["passed"])
        actual = self.candidate()
        actual["steps"][0]["warning"] = True
        report = main.compare(self.golden, actual)
        self.assertEqual(report["first_divergent_cfl_step"], "1")
        self.assertEqual(report["cfl_disagreements"][0]["actual"]["warning"], True)

    def test_report_rechecks_hashes_exit_and_execution_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            main.baseline.write_json(directory / "candidate.json", self.candidate())
            collection = {"attempts": [{
                "file": "candidate.json", "sha256": sha256((directory / "candidate.json").read_bytes()),
                "reference": "reference/small-lattice-v1.json",
                "reference_sha256": sha256((main.SIMULATOR / "reference/small-lattice-v1.json").read_bytes()),
                "execution": {"mode": "threaded", "workers": 3},
                "backend": self.candidate()["backend"], "exit_code": 0,
            }]}
            with patch.object(main, "read_json", side_effect=lambda p: collection if p.name == "collection.json" else read_json(p)):
                self.assertTrue(main.report(directory)["passed"])
                collection["attempts"][0]["execution"]["workers"] = 2
                self.assertFalse(main.report(directory)["passed"])
                collection["attempts"][0]["execution"]["workers"] = 3
                collection["attempts"][0]["exit_code"] = 4
                self.assertFalse(main.report(directory)["passed"])
                (directory / "candidate.json").write_text("{}")
                with self.assertRaisesRegex(ValueError, "bytes changed"):
                    main.report(directory)

    def test_invalid_workers_are_rejected_before_creating_a_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "evidence"
            for workers in ([], [0], [257], [1, 1]):
                with self.assertRaisesRegex(ValueError, "workers"):
                    main.collect(directory, Path("unused"), workers)
                self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()
