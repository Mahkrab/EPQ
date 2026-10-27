"""Cold initialisation remains timed when warm attempts reuse device inputs."""

import unittest

from tools.performance.compact_trace import completion_count


class ResidencyTests(unittest.TestCase):
    def test_only_following_steps_omit_fixed_preparation_calls(self):
        self.assertEqual(completion_count(110592, 1, "compact-resident"), 52)
        self.assertEqual(completion_count(110592, 2, "compact-resident"), 83)
        self.assertEqual(completion_count(110592, 480, "compact-resident"), 14901)
        self.assertEqual(completion_count(110592, 480, "compact-stages"), 24481)

    def test_single_particle_omits_the_sort_completion_only(self):
        self.assertEqual(completion_count(1, 1, "compact-resident"), 51)
        self.assertEqual(completion_count(1, 2, "compact-resident"), 81)
        for count, steps in ((0, 1), (1, 0), (True, 1)):
            with self.assertRaises(ValueError):
                completion_count(count, steps, "compact-resident")
