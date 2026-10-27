"""A timing partition cannot silently omit publication or move its boundary."""

import copy
import unittest

from tools.performance.compilation import duration, partition


def sample():
    return {"timing_profile": {"schema_version": 1, "boundary": "export_entry_to_before_manifest",
        "total_s": 31, "components_s": {"setup": 2, "solver_steps": 3, "snapshot_capture": 0,
        "comparison": 0, "frame_particle_copy": 0, "graphics_readback": 0, "png_encoding": 0,
        "frame_publication": 5, "frame_hashing": 7, "progress": 11, "other": 3}},
        "timing_seconds": {"solver_steps": 3, "graphics_readback": 0, "encoding": 0}}


class CompilationTests(unittest.TestCase):
    def test_publication_hashing_and_external_work_remain_distinct(self):
        result = partition(sample(), 41)
        self.assertEqual(result["outside_export_boundary_s"], 10)
        self.assertEqual(result["components_s"]["frame_publication"], 5)
        self.assertEqual(result["components_s"]["frame_hashing"], 7)
        self.assertEqual(result["pre_manifest_s"], 31)

    def test_wrong_scope_version_fields_and_legacy_meaning_are_rejected(self):
        changes = [lambda v: v["timing_profile"].update(boundary="whole_command"),
            lambda v: v["timing_profile"].update(schema_version=True),
            lambda v: v["timing_profile"].update(schema_version=2),
            lambda v: v["timing_profile"]["components_s"].pop("frame_publication"),
            lambda v: v["timing_profile"]["components_s"].update(unreported=0),
            lambda v: v["timing_seconds"].update(encoding=1)]
        for change in changes:
            value = copy.deepcopy(sample())
            change(value)
            with self.assertRaises(ValueError):
                partition(value, 41)

    def test_nonfinite_negative_bool_and_enclosing_overruns_fail(self):
        for bad in (True, -1, float("nan"), float("inf"), "1"):
            value = sample()
            value["timing_profile"]["components_s"]["other"] = bad
            with self.assertRaises(ValueError):
                partition(value, 41)
            with self.assertRaises(ValueError):
                duration(bad)
        for wall in (30, 0):
            with self.assertRaises(ValueError):
                partition(sample(), wall)
        value = sample()
        value["timing_profile"]["total_s"] = 32
        with self.assertRaises(ValueError):
            partition(value, 41)


if __name__ == "__main__":
    unittest.main()
