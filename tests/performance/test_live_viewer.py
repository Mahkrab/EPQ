"""Presentation cadence cannot stand in for accepted simulation advancement."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from tools.performance.live_report import reading
from tools.performance.live_viewer import percentile, summarise
from tools.performance.live_probe import prepare
from tools.performance.particle_visuals import compare
from tools.performance.particle_capacity import assess


class LiveViewerMeasurements(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / "frames.csv"
        self.rows = [dict(wall_s=t,generation=1,step=step,simulated_s=step/240,
                         solver_s=step*.0001,snapshot_s=step*.00001,status="Running",
                         **{key:.001 for key in ("acquire_s","prepare_s","upload_s",
                                                "submit_s","present_s","redraw_s")})
                     for t,step in [(0,0),(.1,24),(.3,72),(.6,144)]]

    def write(self):
        with self.path.open("w") as stream:
            writer = csv.DictWriter(stream,fieldnames=self.rows[0].keys())
            writer.writeheader()
            writer.writerows(self.rows)

    def test_known_intervals_and_independent_physics_rate(self):
        self.write()
        result = summarise(self.path)
        self.assertEqual(result["presentation_fps"],5)
        self.assertAlmostEqual(result["frame_mean_ms"],200)
        self.assertAlmostEqual(result["frame_p95_ms"],300)
        self.assertAlmostEqual(result["frame_p99_ms"],300)
        self.assertEqual(result["steps_s"],240)
        self.assertEqual(result["simulated_s_per_wall_s"],1)
        self.assertAlmostEqual(result["solver_ms_per_step"],.1)
        self.assertEqual(result["stutters_over_50ms"],3)

    def test_representing_the_same_state_does_not_invent_steps(self):
        self.rows[1].update(step=0,simulated_s=0,solver_s=0,snapshot_s=0)
        self.write()
        self.assertEqual(summarise(self.path)["steps_s"],240)
        self.assertEqual(summarise(self.path)["presentation_fps"],5)

    def test_pause_and_generation_changes_cannot_enter_one_rate(self):
        for key,value in [("status","Paused"),("generation",2)]:
            with self.subTest(key=key):
                original = self.rows[1][key]
                self.rows[1][key] = value
                self.write()
                with self.assertRaisesRegex(ValueError,"pause or generation"):
                    summarise(self.path)
                self.rows[1][key] = original

    def test_wrong_timestep_or_no_simulation_work_is_rejected(self):
        for row in self.rows:
            row["simulated_s"] = row["step"]/480
        self.write()
        with self.assertRaisesRegex(ValueError,"240 Hz"):
            summarise(self.path)
        for row in self.rows:
            row.update(step=0,simulated_s=0)
        self.write()
        with self.assertRaisesRegex(ValueError,"did not advance"):
            summarise(self.path)

    def test_report_recomputes_and_rejects_a_manipulated_summary(self):
        self.write()
        result = summarise(self.path)
        result["presentation_fps"] = 60
        (self.root / "summary.json").write_text(json.dumps(result))
        with self.assertRaisesRegex(ValueError,"stored frame summary disagrees"):
            reading(self.root)

    def test_nearest_rank_exposes_the_small_sample_tail(self):
        self.assertEqual(percentile([1,2,20],.95),20)

    def test_non_monotone_presentation_timestamps_are_rejected(self):
        self.rows[2]["wall_s"] = .05
        self.write()
        with self.assertRaisesRegex(ValueError,"strictly increasing"):
            summarise(self.path)

    def test_unsupported_probe_source_is_left_unchanged(self):
        gpu = self.root / "src/render/gpu.rs"
        gpu.parent.mkdir(parents=True)
        source = "    uniform: wgpu::Buffer,\n"
        gpu.write_text(source,encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"profiling insertion"):
            prepare(self.root)
        self.assertEqual(gpu.read_text(encoding="utf-8"),source)

    def test_visual_difference_uses_foreground_union_and_rgb_units(self):
        before=bytes([16,24,32,255, 100,0,0,255])
        after=bytes([16,24,32,255, 90,0,0,255])
        result=compare(before,after)
        self.assertEqual(result["changed_pixels"],1)
        self.assertEqual(result["changed_percent"],50)
        self.assertEqual(result["changed_active_percent"],100)
        self.assertEqual(result["max_channel_delta"],10)
        self.assertAlmostEqual(result["active_rgb_rmse"],(100/3)**.5)
        self.assertEqual(compare(before,before)["changed_pixels"],0)

    def test_capacity_checks_every_boundary_instead_of_only_the_overall_rate(self):
        path=self.root/"accepted.csv"
        def write(times):
            path.write_text("step,wall_ns\n"+"".join(f"{i},{t}\n" for i,t in enumerate(times)),encoding="utf-8")
        write([i*10_000_000 for i in range(201)])
        result=assess(path,200,.01)
        self.assertEqual(result["minimum_steps_in_one_second"],100)
        self.assertTrue(result["qualifies"])
        # A long initial pause is hidden by a faster finish in the overall mean.
        write([i*10_000_000 for i in range(51)]+[1_000_000_000+(i-51)*2_000_000 for i in range(51,301)])
        result=assess(path,300,.01)
        self.assertGreater(result["simulated_s_per_wall_s"],1)
        self.assertEqual(result["minimum_steps_in_one_second"],51)
        self.assertFalse(result["qualifies"])

    def test_capacity_rejects_missing_acceptances(self):
        path=self.root/"accepted.csv"
        path.write_text("step,wall_ns\n0,0\n2,1000000000\n",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"skips required steps"):
            assess(path,2,.01)


if __name__ == "__main__":
    unittest.main()
