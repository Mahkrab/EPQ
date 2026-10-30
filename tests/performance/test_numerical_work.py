"""The workload matrix reuses exact controls and preserves independent axes."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.performance.numerical_work import matrix, prepare, same_policy
from tools.performance.numerical_work_assessment import paired
from tools.performance.numerical_work_retain import retain


class NumericalWork(unittest.TestCase):
    def test_complete_independent_matrix(self):
        rows = matrix()
        self.assertEqual(len(rows), 12)
        self.assertEqual({(round(1/r["dt"]), r["iterations"]) for r in rows},
                         {(hz, i) for hz in (120, 240, 480) for i in (2, 3, 4, 8)})
        self.assertTrue(all(r["scale"] == .5 and r["epsilon"] == 2 for r in rows))

    def test_reuse_requires_both_numerical_controls(self):
        control = matrix()[0]
        self.assertTrue(same_policy(control, {**control, "id": "old-name"}))
        for key in ("dt", "iterations", "scale", "epsilon"):
            self.assertFalse(same_policy(control, {**control, key: control[key]*2}))

    def fixture(self, root, completed=True):
        previous = root/"previous"
        previous.mkdir()
        for name in ("config", "scenes", "target"):
            (previous/name).mkdir()
        (previous/"scenes.json").write_text("{}")
        source = previous/"runs/old-control"
        source.mkdir(parents=True)
        (source/"metrics.json").write_text(json.dumps({"native_endpoint_equal": True,
                                                      "completed": completed,
                                                      "production_json_sha256": "synthetic"}))
        (previous/"frontier.json").write_text(json.dumps([
            {"scene": "resolved", "label": "old-control", "policy": matrix()[0]},
            {"scene": "resolved", "label": "long-old-control", "policy": matrix()[0]},
        ]))
        return previous

    def test_reuse_never_writes_old_run_and_excludes_long_trajectories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = self.fixture(root)
            source = previous/"runs/old-control/metrics.json"
            original = source.read_bytes()
            prepare(root/"new", previous)
            plan = json.loads((root/"new/matrix-plan.json").read_text())
            self.assertEqual(len(plan), 24)
            reused = [r for r in plan if "reused_from" in r]
            self.assertEqual(len(reused), 1)
            self.assertEqual(Path(reused[0]["reused_from"]).name, "old-control")
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse((root/"new/runs").exists())
            with self.assertRaisesRegex(ValueError, "already exists"):
                prepare(root/"new", previous)

    def test_incomplete_reuse_fails_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = self.fixture(root, completed=False)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                prepare(root/"new", previous)
            self.assertFalse((root/"new").exists())

    def timing_rows(self):
        return [dict(scene=scene, candidate=candidate, repeat=repeat,
                     policy=policy, warmup=repeat == 0,
                     cost_s_per_sim_s=(1000 if repeat == 0 else
                                      (4 if policy == "production" else 2)))
                for scene in ("resolved", "large")
                for candidate in ("half-rate", "half-iterations")
                for repeat in range(6) for policy in ("production", candidate)]

    def test_paired_timings_exclude_warmups_and_keep_controls_separate(self):
        rows = paired(self.timing_rows())
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertEqual(row["control_median"], 4)
            self.assertEqual(row["candidate_median"], 2)
            self.assertEqual(row["paired_speedups"], [2]*5)
            self.assertEqual(row["speedup_ratio_of_medians"], 2)
            self.assertEqual(row["simulated_seconds_per_wall_second"], .5)

    def test_partial_or_duplicate_pairs_cannot_report_a_speedup(self):
        rows = self.timing_rows()
        with self.assertRaisesRegex(ValueError, "complete paired"):
            paired(rows[:-1])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            paired(rows+[rows[-1]])

    def test_seal_keeps_measurements_and_excludes_builds_and_external_links(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base/"raw"
            root.mkdir()
            (root/"result.json").write_text('{"steps": 480}')
            (root/"workload-probe").write_bytes(b"synthetic executable")
            (root/"build").mkdir()
            (root/"build/object").write_bytes(b"synthetic object")
            (base/"outside").write_bytes(b"external data")
            (root/"external-link").symlink_to(base/"outside")
            result = retain(root, base/"seal")
            self.assertEqual(result["files"], 1)
            manifest = json.loads((base/"seal/manifest.json").read_text())
            self.assertEqual([f["name"] for f in manifest["files"]], ["result.json"])
            self.assertEqual((root/"result.json").read_text(), '{"steps": 480}')


if __name__ == "__main__":
    unittest.main()
