"""Incomplete or overlapping observations cannot establish removable host cost."""

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.performance.coordination import diagnostic, probes
from tools.performance.coordination_overlay import instrument


TRIPLE = ("COORD_PREP,3,1,1,2,3\n"
          "COORD_ROWS,3,1,4,5,6,7,8\n"
          "COORD_STEP,3,1,9,10,11,12,13\n")


class CoordinationTests(unittest.TestCase):
    def test_complete_triples_keep_calculation_and_transfer_fields_separate(self):
        rows = probes("unrelated diagnostic\n" + TRIPLE + TRIPLE.replace(",3,1,", ",3,2,"), 3, 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["bounds_cpu"], 4)
        self.assertEqual(rows[0]["prefix_cpu"], 6)
        self.assertEqual(rows[0]["cfl_cpu"], 11)
        self.assertEqual(rows[0]["prediction_download"], 12)
        self.assertEqual(sum(rows[0].values()), 91)

    def test_missing_duplicate_reordered_and_wrong_ordinal_records_fail(self):
        lines = TRIPLE.splitlines(keepends=True)
        for text, steps in (("".join(lines[:2]), 1), (lines[0] + TRIPLE, 1),
                            (lines[1] + lines[0] + lines[2], 1), (TRIPLE * 2, 2),
                            (TRIPLE.replace(",3,1,", ",4,1,"), 1),
                            (TRIPLE.replace("COORD_ROWS", "COORD_UNKNOWN"), 1)):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    probes(text, 3, steps)

    def test_bad_durations_and_invalid_requests_fail(self):
        for value in ("-1", "nan", "inf", "1e999", "True", ""):
            with self.assertRaises(ValueError):
                probes(TRIPLE.replace("1,2,3\n", value + ",2,3\n"), 3, 1)
        for particles, steps in ((0, 1), (True, 1), (3, 0), (3, False)):
            with self.assertRaises(ValueError):
                probes(TRIPLE, particles, steps)

    def test_component_sums_and_windows_are_independent_of_reported_totals(self):
        text = "".join(f"COORD_PREP,3,{i},0.01,0.01,0.01\n"
                       f"COORD_ROWS,3,{i},0.01,0.01,0.01,0.01,0.01\n"
                       f"COORD_STEP,3,{i},0.01,0.01,0.01,0.01,0.01\n" for i in range(1, 481))
        document = {"measurements": {"steps": [{"total_s": 0.5} for _ in range(480)]}}
        with patch("tools.performance.coordination.accepted"), patch("tools.performance.coordination.metrics", return_value={"solver_s": 240}):
            result = diagnostic({}, document, {}, "synthetic", text, 3)
            self.assertAlmostEqual(result["components_s"]["prefix_cpu"], 4.8, places=12)
            self.assertAlmostEqual(result["windows"]["241-480"]["cfl_cpu"], 2.4, places=12)
            self.assertAlmostEqual(result["bundles_s"]["cfl"], 14.4, places=12)
            self.assertFalse(result["primary_timing"])
            document["measurements"]["steps"][0]["total_s"] = 0.12
            with self.assertRaisesRegex(ValueError, "exceed"):
                diagnostic({}, document, {}, "synthetic", text, 3)

    def test_overlay_rejects_source_drift_and_duplicate_application(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / "Maelstrom/src/cuda/solver.rs").read_text()
        output = instrument(source)
        self.assertIn('"MAELSTROM_COORDINATION_PROBE"', output)
        self.assertIn("self.coordination_step.checked_add(1)", output)
        with self.assertRaisesRegex(ValueError, "already instrumented"):
            instrument(output)
        with self.assertRaisesRegex(ValueError, "anchor changed"):
            instrument(source.replace("neighbour_capacity: usize", "different_capacity: usize"))


if __name__ == "__main__":
    unittest.main()
