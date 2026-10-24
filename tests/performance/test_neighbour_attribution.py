"""Synthetic timelines distinguish device costs from host completion intervals."""

from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.performance.neighbour_attribution import analyse, replace_once


class AttributionTests(unittest.TestCase):
    def test_invalid_particle_counts_fail_before_opening_a_trace(self):
        for count in (True, 0, -1, 1.5, 1_000_001):
            with self.assertRaisesRegex(ValueError, "particles"):
                analyse(Path("does-not-exist"), count, split=True)

    def test_missing_or_ambiguous_patch_boundary_is_rejected(self):
        for text in ("absent", "site site"):
            with self.assertRaises(ValueError):
                replace_once(text, "site", "new")

    def test_split_operations_are_attributed_to_their_actual_device_durations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.sqlite"
            with sqlite3.connect(path) as db:
                db.executescript("""
                    CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL(start,end,correlationId);
                    CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(start,nameId,correlationId);
                    CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY(copyKind,bytes);
                    CREATE TABLE StringIds(id,value);
                    INSERT INTO StringIds VALUES(1,'cuLaunchKernel'),(2,'cuStreamSynchronize');
                """)
                # One particle has no cell-sort passes. Each step has 56 launches:
                # three setup, count, dry/fill/sort, 48 iteration passes, velocity.
                rows = []
                for step in range(480):
                    for stage in range(56):
                        index = step * 56 + stage
                        duration = {3: 2, 4: 3, 5: 5, 6: 7}.get(stage, 1)
                        rows.append((index * 1000, index * 1000 + duration, index))
                db.executemany("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES(?,?,?)", rows)
                db.executemany("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES(?,1,?)", [(a, c) for a, _, c in rows])
                db.executemany("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES(?,2,0)", [(n,) for n in range(24_481)])
            result = analyse(path, 1, split=True)
            self.assertEqual(result["kernel_count"], 26_880)
            last = result["windows"]["241-480"]["operations_device_s"]
            self.assertEqual(last["4"], 480 / 1e9)
            self.assertEqual(last["15"], 720 / 1e9)
            self.assertEqual(last["12"], 1200 / 1e9)
            self.assertEqual(last["14"], 1680 / 1e9)
            self.assertFalse(result["primary_timing"])
            with sqlite3.connect(path) as db:
                db.execute("UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=-1 WHERE start=0")
            with self.assertRaisesRegex(ValueError, "correlation"):
                analyse(path, 1, split=True)
            with self.assertRaisesRegex(ValueError, "launch/completion"):
                analyse(path, 1, split=False)


if __name__ == "__main__":
    unittest.main()
