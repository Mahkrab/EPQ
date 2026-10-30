"""Compilation evidence must reject changed output and exclude exploratory warmups."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.performance.render_pipeline import audit_bundle, fingerprint, summarise
from tools.performance.render_probe import assess


class RenderEvidenceTests(unittest.TestCase):
    def test_saved_state_audit_rejects_missing_timings_and_changed_pixels(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "probe-requests-v2").mkdir()
            (root / "probe-output").mkdir()
            state = "synthetic-state-0.bin"
            expected = dict(png_sha256="sha256:png", rgba_sha256="sha256:pixels", step="0", simulated_seconds=0)
            request = dict(states=[state], expected={state: expected}, state_sha256={state: "state"})
            (root / "probe-requests-v2/case.json").write_text(json.dumps(request), encoding="utf-8")
            frames = [dict(state=state, repeat=i, state_sha256="state", png_sha256="png",
                           rgba_sha256="pixels", graphics_s=1, encoding_s=2) for i in range(4)]
            log = root / "probe-output/case.jsonl"
            log.write_text("\n".join(map(json.dumps, frames)), encoding="utf-8")
            timings = dict(cpu_prepare_s=1, buffer_upload_s=2, render_submit_s=3, render_gpu_s=4,
                           texture_copy_gpu_s=5, target_allocation_s=6, draw_drain_s=7,
                           transfer_submit_s=8, transfer_wait_map_s=9, row_unpack_s=10)
            lines = [tag + " " + json.dumps(timings if tag == "DRAW_PROFILE" else {})
                     for _ in range(4) for tag in ("DRAW_PROFILE", "GPU_PROFILE", "PIXEL_PROFILE")]
            stderr = log.with_suffix(".stderr")
            stderr.write_text("\n".join(lines), encoding="utf-8")
            row, = assess(root)
            self.assertEqual(row["verified_frames"], 4)
            self.assertEqual(row["median_s"]["render_gpu_s"], 4)
            frames[1]["rgba_sha256"] = "altered"
            log.write_text("\n".join(map(json.dumps, frames)), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs"):
                assess(root)
            stderr.write_text("\n".join(lines[:-1]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "incomplete"):
                assess(root)

    def test_fingerprint_preserves_signed_zero_and_frame_and_diagnostic_changes(self):
        document = {key: {} for key in (
            "input", "accepted_steps", "accepted_diagnostics", "frames", "render", "status",
            "boundary_display_box", "encoder", "renderer", "graphics",
        )}
        document["input"] = {"velocity": 0.0}
        original = fingerprint(document)
        for key, value in (
            ("input", {"velocity": -0.0}),
            ("frames", [{"rgba_sha256": "altered"}]),
            ("accepted_diagnostics", [{"warning": True}]),
        ):
            changed = dict(document, **{key: value})
            self.assertNotEqual(fingerprint(changed), original)

    def test_bundle_rejects_incomplete_schedule_and_changed_png_before_external_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "bundle"
            bundle.mkdir()
            manifest = bundle / "manifest.json"
            manifest.write_text(json.dumps({"complete": True, "frames": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schedule"):
                audit_bundle(root / "absent-executable", root, None)
            document = {key: {} for key in (
                "input", "accepted_steps", "accepted_diagnostics", "render", "status",
                "boundary_display_box", "encoder", "renderer", "graphics",
            )}
            document.update(complete=True, frames=[{"file": "frame.png", "png_sha256": "sha256:invalid"}]*301)
            (bundle / "frame.png").write_bytes(b"changed encoded output")
            manifest.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest"):
                audit_bundle(root / "absent-executable", root, None)

    def test_paired_summary_keeps_worker_time_separate_and_excludes_warmups(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for repeat, control, candidate in ((0, 1000, 1), (1, 10, 5), (2, 20, 8)):
                for variant, elapsed in (("control", control), ("candidate", candidate)):
                    folder = root / "measure" / f"{repeat}-{variant}"
                    folder.mkdir(parents=True)
                    value = dict(scene="large", mode="fast", repeat=repeat, variant=variant,
                                 warmup=repeat == 0, wall_s=elapsed, cpu_user_s=2, cpu_system_s=1,
                                 profile={"components_s": {"solver_steps": 4},
                                          "worker_components_s": {"frame_hashing": 9}})
                    (folder / "metrics.json").write_text(json.dumps(value), encoding="utf-8")
            row, = summarise(root, "measure")
            self.assertEqual(row["paired_speedups"], [2.0, 2.5])
            self.assertEqual(row["control_median_s"], 15)
            self.assertEqual(row["candidate_median_s"], 6.5)
            self.assertEqual(row["candidate_stages_median_s"]["components_s"], {"solver_steps": 4})
            self.assertEqual(row["candidate_stages_median_s"]["worker_components_s"], {"frame_hashing": 9})


if __name__ == "__main__":
    unittest.main()
