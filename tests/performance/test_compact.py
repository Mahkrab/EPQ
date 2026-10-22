"""Compact-row measurements must retain work identity and their limited memory scope."""

import copy
import unittest

from tools.performance.compact import capacity_estimate, qualified


class CompactTests(unittest.TestCase):
    def test_initial_lattice_estimate_is_not_the_old_bitset_or_a_dense_guarantee(self):
        self.assertEqual(capacity_estimate(8000), 6982248)
        self.assertLess(capacity_estimate(512000), 500 * 1024**2)
        for value in (0, -1, True, 1.5, 1000001):
            with self.assertRaises(ValueError):
                capacity_estimate(value)

    def test_exit_zero_cannot_admit_wrong_resources_work_revision_or_warnings(self):
        document = {"status": "completed", "failures": [], "execution": {"mode": "cuda", "device": 0, "threads": 128},
                    "backend": "cuda-uniform-grid-pbf-binary32-8-jacobi-v1",
                    "metadata": {"backend": "cuda-uniform-grid-pbf-binary32-8-jacobi-v1", "build_revision": "fixture", "debug_assertions": False},
                    "request": {"steps": "1", "checkpoints": []}, "completed_steps": "1",
                    "steps": [{"completed_steps": "1", "warning": False}], "checkpoints": [],
                    "input": {"particles": [0]}, "final_snapshot": {"particles": [0]}}
        request = dict(particles=1, steps=1, observation=False, revision="fixture")
        self.assertTrue(qualified({"exit_code": 0}, document, **request))
        for mutate in (lambda d: d["execution"].update(threads=64),
                       lambda d: d["steps"][0].update(warning=True),
                       lambda d: d["metadata"].update(build_revision="other"),
                       lambda d: d.update(completed_steps="0")):
            bad = copy.deepcopy(document)
            mutate(bad)
            self.assertFalse(qualified({"exit_code": 0}, bad, **request))
        self.assertFalse(qualified({"exit_code": 0, "timed_out": True}, document, **request))


if __name__ == "__main__":
    unittest.main()
