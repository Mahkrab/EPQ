"""Counter replay must select the intended correction and preserve exported values."""

import unittest
from unittest.mock import patch

from tools.performance.correction_profile import _accepted, launch_index, metric_rows


class CorrectionProfileTests(unittest.TestCase):
    def test_large_first_and_evolved_corrections_have_exact_launch_offsets(self):
        self.assertEqual(launch_index(110592, 1, 1), 160)
        self.assertEqual(launch_index(110592, 1, 8), 202)
        self.assertEqual(launch_index(110592, 241, 1), 49840)
        self.assertEqual(launch_index(110592, 241, 8), 49882)

    def test_small_tail_and_no_sort_cases_keep_their_own_sequence(self):
        self.assertEqual(launch_index(8000, 1, 1), 98)
        self.assertEqual(launch_index(1, 1, 1), 7)
        self.assertEqual(launch_index(2, 2, 1), 63)

    def test_invalid_launch_requests_fail_before_tool_execution(self):
        for request in ((True, 1, 1), (0, 1, 1), (1000001, 1, 1), (4, 0, 1),
                        (4, 481, 1), (4, 1, 0), (4, 1, 9), (4, 1.5, 1)):
            with self.assertRaises(ValueError):
                launch_index(*request)

    def test_counter_export_preserves_quoted_numbers_and_units(self):
        rows = metric_rows('Profiler notice\n"Metric Name","Metric Unit","Metric Value"\n"count","inst","1,024"\n')
        self.assertEqual(rows, [{"Metric Name": "count", "Metric Unit": "inst", "Metric Value": "1,024"}])

    def test_missing_or_empty_metric_tables_are_not_successful_captures(self):
        for text in ("==ERROR== unavailable", '"Metric Name","Metric Unit","Metric Value"\n'):
            with self.assertRaises(ValueError):
                metric_rows(text)

    def test_failed_diagnostic_status_is_rejected_even_with_complete_step_count(self):
        process = {"exit_code": 0, "timed_out": False, "interrupted": False}
        document = {"status": "failed", "completed_steps": "241", "failures": [],
                    "metadata": {"build_revision": "synthetic", "debug_assertions": False},
                    "execution": {"mode": "cuda", "device": 0, "threads": 128}}
        with patch("tools.performance.correction_profile.compare", return_value={"passed": True}):
            with self.assertRaises(ValueError):
                _accepted(process, document, document, "synthetic", 241)


if __name__ == "__main__":
    unittest.main()
