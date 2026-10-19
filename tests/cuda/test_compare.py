"""Adversarial records must fail even if most particles agree."""

import copy
from contextlib import redirect_stdout, redirect_stderr
import io
import gzip
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

from tools.cuda.compare import compare, main

GOLDEN = Path(__file__).resolve().parents[2] / "Maelstrom/reference/falling-block-v1.json"


class ComponentComparisonTests(unittest.TestCase):
    def setUp(self):
        self.reference = json.loads(GOLDEN.read_text(encoding="utf-8"))
        self.candidate = copy.deepcopy(self.reference)

    def test_complete_exact_output_checks_all_components_and_diagnostics(self):
        report = compare(self.reference, self.candidate, exact=True)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["snapshots"]), 6)
        self.assertEqual(len(report["cfl"]), 480)
        self.assertEqual(report["snapshots"][0]["position_m"]["components"], 192)

    def test_one_bad_early_component_is_not_hidden_by_average_or_final_state(self):
        self.candidate["checkpoints"][1]["snapshot"]["particles"][17]["position_m"]["z"] += 0.00002
        report = compare(self.reference, self.candidate)
        self.assertFalse(report["passed"])
        self.assertEqual(report["first_divergent_checkpoint"], "1")
        self.assertEqual(report["snapshots"][1]["position_m"]["worst_identity"], "17")

    def test_exact_mode_keeps_signed_zero_while_parallel_budget_is_quantity_specific(self):
        self.candidate["checkpoints"][0]["snapshot"]["particles"][0]["velocity_m_s"]["x"] = -0.0
        self.assertFalse(compare(self.reference, self.candidate, exact=True)["passed"])
        self.assertTrue(compare(self.reference, self.candidate)["passed"])
        self.candidate["steps"][2]["cfl_limit"]["seconds"] += 0.000002
        self.assertFalse(compare(self.reference, self.candidate)["passed"])

    def test_missing_structure_wrong_identity_warning_and_nonfinite_always_fail(self):
        mutations = [lambda c: c["checkpoints"].pop(1),
                     lambda c: c.update(schema_version=99),
                     lambda c: c["final_snapshot"]["particles"][0].update(identity="9000"),
                     lambda c: c["steps"][10].update(warning=True),
                     lambda c: c["checkpoints"][1].update(density=None),
                     lambda c: c["steps"][1].update(maximum_speed_m_s=float("nan")),
                     lambda c: c.update(completed_steps="479"),
                     lambda c: c["input"]["particles"][0]["position_m"].update(x=0.1)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                candidate = copy.deepcopy(self.candidate)
                mutation(candidate)
                self.assertFalse(compare(self.reference, candidate)["passed"])

    def test_audit_and_speed_outliers_remain_failures(self):
        self.candidate["checkpoints"][2]["density"]["maximum_error"] += 0.0002
        self.candidate["steps"][34]["maximum_speed_m_s"] += 0.006
        report = compare(self.reference, self.candidate)
        self.assertFalse(report["passed"])
        self.assertFalse(report["audits"][2]["metrics"]["maximum_error"]["passed"])
        self.assertFalse(report["cfl"][34]["speed"]["passed"])
        self.assertEqual(report["first_divergent_checkpoint"], "120")
        self.assertEqual(report["first_divergent_step"], "35")

    def test_cli_rejects_nonobject_json_with_a_concise_diagnostic(self):
        with tempfile.TemporaryDirectory() as name:
            invalid=Path(name)/"invalid.json"
            invalid.write_text("[]",encoding="utf-8")
            error=io.StringIO()
            with patch("sys.argv",["compare",str(invalid),str(invalid)]), redirect_stdout(io.StringIO()),redirect_stderr(error):
                self.assertEqual(main(),2)
            self.assertIn("JSON objects",error.getvalue())
            damaged=Path(name)/"damaged.json.gz"
            damaged.write_bytes(gzip.compress(b"{}")[:-4])
            with patch("sys.argv",["compare",str(damaged),str(damaged)]),redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                self.assertEqual(main(),2)
