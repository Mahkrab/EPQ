"""Performance reports must expose drift and regressions without choosing a verdict."""

import copy
import unittest
from unittest.mock import patch
from pathlib import Path

from tools.performance.assessment import evidence, paired
from tools.performance.arithmetic import report
from tests.performance.audit_assessment import validate
from tests.performance.audit_acceptance import validate_confirmation
from tests.performance.test_arithmetic import workload


class AssessmentTests(unittest.TestCase):
    def test_new_experiments_cannot_invoke_the_historical_decision_rule(self):
        with patch("tools.performance.arithmetic.json.loads", return_value={"experiment": "neighbour-bands-v1"}), \
                patch.object(Path, "read_bytes", return_value=b"{}"), \
                patch("tools.performance.arithmetic.coordination_report") as read:
            with self.assertRaisesRegex(ValueError, "no historical automatic decision"):
                report(Path("synthetic"), historical_policy=True)
            read.assert_not_called()

    def test_drift_preserves_all_pairs_even_when_ranges_overlap(self):
        result = paired([10, 20, 30], [8, 16, 24])
        self.assertEqual(result["control_median_s"], 20)
        self.assertEqual(result["candidate_median_s"], 16)
        self.assertEqual(result["median_paired_speedup"], 1.25)
        self.assertTrue(result["ranges_overlap"])
        self.assertEqual([r["saving_s"] for r in result["pairs"]], [2, 4, 6])
        self.assertEqual(result["faster_pairs"], 3)

    def test_small_gain_slow_pair_and_equal_pair_are_all_reported(self):
        result = paired([10, 10, 10], [9.9, 12, 10])
        self.assertEqual((result["faster_pairs"], result["slower_pairs"], result["equal_pairs"]), (1, 1, 1))
        self.assertEqual(result["pairs"][1]["saving_s"], -2)
        self.assertNotIn("retained", result)

    def test_workload_median_ratio_and_median_pair_ratio_are_distinct(self):
        result = paired([10, 20, 100], [5, 19, 50])
        self.assertEqual(result["median_speedup"], 20 / 19)
        self.assertEqual(result["median_paired_speedup"], 2)

    def test_invalid_or_incomplete_pairs_are_rejected(self):
        for a, b in (([1], [1]), ([1, 2], [1]), ([1, True], [1, 2]),
                     ([1, 2], [0, 1]), ([1, 2], [float("nan"), 1]), ([1, 2], [float("inf"), 1])):
            with self.assertRaises(ValueError):
                paired(a, b)

    def test_reader_rejects_false_pairs_counts_and_automatic_verdicts(self):
        raw = {"8000": {"control": [10] * 5, "candidate": [9] * 5},
               "110592": {"control": [20] * 5, "candidate": [18] * 5}}
        good = evidence(workload([10] * 5, [9] * 5), workload([20] * 5, [18] * 5))
        validate(raw, good)
        for kind in ("pair", "count", "decision"):
            changed = copy.deepcopy(good)
            if kind == "pair":
                changed["workloads"]["8000"]["pairs"][0]["saving_s"] = 2
            elif kind == "count":
                changed["workloads"]["8000"]["slower_pairs"] = 1
            else:
                changed["retained"] = True
            with self.assertRaises(ValueError):
                validate(raw, changed)

    def test_normal_report_never_uses_the_historical_rejection_rule(self):
        base = workload([10] * 5, [9.9] * 5)
        document = {"metadata": {}, "execution": {}}
        with patch("tools.performance.arithmetic.json.loads", return_value={"experiment": "acceptance-inline-v1", "implementations": {v: {"revision": v} for v in ("control", "candidate")}}), \
             patch.object(Path, "read_bytes", return_value=b"{}"), \
             patch("tools.performance.arithmetic.coordination_report", return_value={"primary": base}), \
             patch("tools.performance.arithmetic.load_attempt", return_value=({}, document)), \
             patch("tools.performance.arithmetic.require_sample", return_value={"solver_s": 10}), \
             patch("tools.performance.arithmetic.historical_decision", side_effect=AssertionError("historical policy invoked")):
            result = report(Path("synthetic"))
        self.assertNotIn("decision", result)
        self.assertTrue(result["performance_evidence"]["assessment_required"])

    def test_new_confirmation_checks_quantities_without_a_retention_verdict(self):
        large = workload([20] * 5, [18] * 5)
        small = workload([10] * 5, [9] * 5)
        for workload_data in (small, large):
            for side in workload_data.values():
                v = side["samples"][0]["solver_s"]
                side.update(median_solver_s=v, minimum_s=v, maximum_s=v, standard_deviation_s=0.)
        summary = {"primary": small, "paired_large": large, "performance_evidence": evidence(small, large)}
        raw = {name: {v: [s["solver_s"] for s in group[v]["samples"]] for v in ("control", "candidate")}
               for name, group in (("primary", small), ("paired_large", large))}
        self.assertEqual(validate_confirmation(raw, summary), {"assessment_required": True})
        summary["decision"] = {"retained": True}
        with self.assertRaisesRegex(ValueError, "cannot also decide retention"):
            validate_confirmation(raw, summary)
