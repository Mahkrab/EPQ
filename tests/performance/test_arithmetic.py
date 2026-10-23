"""Arithmetic candidates cannot be retained by selecting favourable samples."""

import unittest
from unittest.mock import patch

from tools.performance.arithmetic import historical_decision, require_sample, summarise


def workload(control, candidate):
    return {name: {"samples": [{"solver_s": value} for value in values]}
            for name, values in (("control", control), ("candidate", candidate))}


class ArithmeticTests(unittest.TestCase):
    def test_warmup_is_validated_without_becoming_a_timing_sample(self):
        process = {"exit_code": 0, "timed_out": False, "interrupted": False}
        document = {"status": "completed", "failures": [], "completed_steps": "480",
                    "execution": {"mode": "cuda", "device": 0, "threads": 128},
                    "metadata": {"build_revision": "synthetic", "debug_assertions": False},
                    "steps": [{"completed_steps": str(i)} for i in range(1, 481)], "measurements": None}
        # Physical comparison is tested separately; isolate the warm-up/timer
        # boundary rather than copying a large simulator document into this case.
        with patch("tools.performance.arithmetic.compare", return_value={"passed": True}):
            self.assertEqual(require_sample(process, document, document, "synthetic", kind="warmup"), {})
            with self.assertRaises(ValueError):
                require_sample(process, document, document, "synthetic")

    def test_complete_finite_samples_and_outliers_are_required(self):
        samples = [{"solver_s": value} for value in (1, 2, 3, 4, 100)]
        self.assertEqual(summarise(samples)["maximum_s"], 100)
        self.assertEqual(summarise(samples)["samples"], samples)
        for values in ([], samples[:4], [{"solver_s": 0}] * 5, [{"solver_s": True}] * 5,
                       [{"solver_s": float("inf")}] * 5):
            with self.assertRaises(ValueError):
                summarise(values)

    def test_historical_rule_can_admit_a_neutral_small_workload(self):
        neutral = workload([10] * 5, [10] * 5)
        gain = workload([20] * 5, [18] * 5)
        result = historical_decision(neutral, gain)
        self.assertTrue(result["retained"])
        self.assertEqual(result["clear_gain"], {"8000": False, "110592": True})

    def test_historical_cutoffs_remain_reproducible(self):
        neutral = workload([10] * 5, [10] * 5)
        clear = workload([10] * 5, [9] * 5)
        for rejected in (workload([10] * 5, [9.9] * 5),
                         workload([10] * 5, [9, 9, 9, 9, 11])):
            self.assertFalse(historical_decision(rejected, neutral)["retained"])
        regression = workload([10] * 5, [10.31] * 5)
        self.assertFalse(historical_decision(clear, regression)["retained"])


if __name__ == "__main__":
    unittest.main()
