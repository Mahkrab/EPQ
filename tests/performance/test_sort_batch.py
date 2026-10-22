"""Sort batching must remove host waits, not kernel work or historical trace meaning."""

import unittest

from tools.performance.compact_trace import completion_count


class SortBatchTests(unittest.TestCase):
    def test_eight_thousand_trace_keeps_historical_counts_separate(self):
        self.assertEqual(completion_count(8000, 480, "bitset"), 105120)
        self.assertEqual(completion_count(8000, 480, "compact"), 108480)
        self.assertEqual(completion_count(8000, 480, "compact-batched"), 65280)

    def test_no_sort_or_single_pass_does_not_invent_a_removed_wait(self):
        self.assertEqual(completion_count(1, 1, "compact-batched"), 135)
        self.assertEqual(completion_count(2, 1, "compact-batched"), 136)
        self.assertEqual(completion_count(2, 1, "compact"), 136)
        self.assertEqual(completion_count(3, 1, "compact"), 138)
        self.assertEqual(completion_count(3, 1, "compact-batched"), 136)

    def test_invalid_trace_requests_are_rejected(self):
        for n, steps, layout in [(0, 1, "compact"), (True, 1, "compact"),
                                 (1, 0, "compact"), (1, 1, "unknown")]:
            with self.assertRaises(ValueError):
                completion_count(n, steps, layout)


if __name__ == "__main__":
    unittest.main()
