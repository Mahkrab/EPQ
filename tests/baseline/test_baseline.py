"""Exercise sample admission, independent arithmetic and bounded process failures."""

import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.baseline import data, main


def attempt(kind="sample", total=1.0, particles=64, index=1):
    steps = data.POLICY["steps"]
    mode = "stages" if kind == "profile" else "total"
    stages = dict.fromkeys(data.STAGES, total / steps / 8) if kind == "profile" else None
    result = {
        "completed_steps": str(steps), "status": "completed", "failures": [],
        "request": {"steps": str(steps), "checkpoints": [str(s) for s in data.POLICY["checkpoints"]]},
        "steps": [{"completed_steps": str(n), "warning": False, "maximum_speed_m_s": 0.0} for n in range(1, steps + 1)],
        "checkpoints": [{"snapshot": {"completed_steps": str(s), "particles": [{"position_m": {"x": 0.0, "y": 1.0, "z": 0.0}, "velocity_m_s": {"x": 0.0, "y": 0.0, "z": 0.0}},
                                                                 {"position_m": {"x": 1.0, "y": 1.0, "z": 0.0}, "velocity_m_s": {"x": 0.0, "y": 0.0, "z": 0.0}}]}, "density": {"sample_count": particles, "mean_error": 0.0, "maximum_error": 0.0}}
                        for s in data.POLICY["checkpoints"]],
    }
    if kind != "warmup":
        result["measurements"] = {
            "schema_version": 1, "mode": mode, "failed_attempt_s": None,
            "steps": [{"total_s": total / steps, "stages": stages} for _ in range(steps)],
        }
    return {"kind": kind, "particles": particles, "index": index, "timed_out": False,
            "exit_code": 0, "result": result}


def series():
    return [attempt("warmup"), attempt(total=1, index=1), attempt(total=2, index=2),
            attempt(total=9, index=3), attempt("profile", total=8)]


class MetricsTests(unittest.TestCase):
    def test_raw_totals_define_median_spread_throughput_and_profile(self):
        row = data.summarise(series())[0]
        p = row["primary"]
        self.assertAlmostEqual(p["median_s"], 2)
        self.assertAlmostEqual(p["minimum_s"], 1)
        self.assertAlmostEqual(p["maximum_s"], 9)
        self.assertAlmostEqual(p["mean_s"], 4)
        self.assertAlmostEqual(p["sample_standard_deviation_s"], math.sqrt(19))
        self.assertAlmostEqual(p["median_step_s"], 2 / 480)
        self.assertAlmostEqual(p["particle_updates_per_s"], 15360)
        self.assertAlmostEqual(row["profile"]["residual_s"], 2)
        self.assertAlmostEqual(row["profile"]["proportions"]["jacobi_s"], 0.125)
        self.assertEqual(len(row["primary"]["sample_totals_s"]), 3, "retain the 9-second outlier")

    def test_partial_warning_failed_and_missing_samples_cannot_become_a_baseline(self):
        for field, value in [("status", "cancelled"), ("completed_steps", "479"), ("failures", [{"message": "failed"}])]:
            a = series()
            a[1]["result"][field] = value
            if field == "completed_steps":
                a[1]["result"]["steps"].pop()
                a[1]["result"]["measurements"]["steps"].pop()
            self.assertIsNone(data.summarise(a)[0]["primary"])
        for mutate in [lambda a: a[0].update(timed_out=True), lambda a: a[1].update(exit_code=4),
                       lambda a: a[1]["result"]["steps"][3].update(warning=True),
                       lambda a: a[1]["result"]["checkpoints"].pop(), lambda a: a.pop(2)]:
            a = series()
            mutate(a)
            self.assertIsNone(data.summarise(a)[0]["primary"])

    def test_corrupt_or_profiled_primary_measurements_are_rejected(self):
        for value in [-1, math.inf, math.nan, True]:
            a = attempt()
            a["result"]["measurements"]["steps"][0]["total_s"] = value
            with self.assertRaises(ValueError):
                data.timing_totals(a)
        a = attempt()
        a["result"]["measurements"]["steps"][0]["stages"] = {}
        with self.assertRaisesRegex(ValueError, "profiling overhead"):
            data.timing_totals(a)
        a = attempt()
        a["result"]["measurements"]["steps"].pop()
        with self.assertRaisesRegex(ValueError, "timings and accepted steps"):
            data.timing_totals(a)
        a = attempt("profile")
        a["result"]["measurements"]["steps"][0]["stages"]["jacobi_s"] = 10
        with self.assertRaisesRegex(ValueError, "exceed total"):
            data.timing_totals(a)

    def test_partial_profiles_remain_labelled_and_counted(self):
        a = attempt("profile", total=2)
        a["timed_out"] = True
        a["exit_code"] = 130
        a["result"]["completed_steps"] = "2"
        a["result"]["steps"] = a["result"]["steps"][:2]
        a["result"]["measurements"]["steps"] = a["result"]["measurements"]["steps"][:2]
        a["result"]["measurements"]["failed_attempt_s"] = 0.25
        row = data.summarise([a])[0]
        self.assertFalse(row["profile"]["complete"])
        self.assertEqual(row["profile"]["completed_steps"], "2")
        self.assertAlmostEqual(row["profile"]["total_s"], 4 / 480)
        self.assertIsNone(row["primary"])

    def test_exact_comparison_detects_signed_zero_missing_and_intermediate_changes(self):
        data.require_exact({"a": [1.25, -0.0]}, {"a": [1.25, -0.0]})
        for actual in [{"a": [1.25, 0.0]}, {"a": [1.26, -0.0]}, {"b": [1.25, -0.0]}, {"a": [1.25]}]:
            with self.assertRaises(ValueError):
                data.require_exact(actual, {"a": [1.25, -0.0]})

    def test_compaction_preserves_raw_timings_and_sign_sensitive_hashes(self):
        value = attempt()["result"]
        value.update(input={"x": -0.0}, final_snapshot={"position": 1.25})
        compact = data.compact_result(value)
        self.assertEqual(compact["measurements"], value["measurements"])
        self.assertEqual(compact["steps"], value["steps"])
        other = copy.deepcopy(value)
        other["input"]["x"] = 0.0
        self.assertNotEqual(compact["input_sha256"], data.compact_result(other)["input_sha256"])
        self.assertIn("input", value, "input remains immutable")


class ProcessAndFileTests(unittest.TestCase):
    def test_success_malformed_and_nonzero_process_outcomes_are_retained(self):
        good = main.invoke([sys.executable, "-c", 'print(\'{"status":"completed"}\')'])
        self.assertEqual(good["exit_code"], 0)
        self.assertFalse(good["timed_out"])
        self.assertEqual(good["result"]["status"], "completed")
        bad = main.invoke([sys.executable, "-c", 'print("broken"); raise SystemExit(4)'])
        self.assertEqual(bad["exit_code"], 4)
        self.assertIsNone(bad["result"])
        self.assertIsNotNone(bad["parse_error"])

    def test_timeout_requests_partial_publication_then_stops(self):
        script = ('import signal,time,json,sys; '
                  'signal.signal(signal.SIGINT, lambda *_: (print(json.dumps({"status":"cancelled"})),sys.exit(130))); '
                  'time.sleep(30)')
        result = main.invoke([sys.executable, "-c", script], timeout_s=0.3, grace_s=1)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["exit_code"], 130)
        self.assertEqual(result["result"], {"status": "cancelled"})
        self.assertLess(result["wall_s"], 5)

    def test_unresponsive_timeout_is_killed_and_cannot_look_complete(self):
        result = main.invoke([sys.executable, "-c", 'import signal,time; signal.signal(signal.SIGINT,signal.SIG_IGN); time.sleep(30)'], timeout_s=0.3, grace_s=0.1)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["exit_code"], -9)
        self.assertIsNone(result["result"])

    def test_publication_does_not_replace_existing_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "sample.json"
            main.write_json(path, {"original": True})
            with self.assertRaises(FileExistsError):
                main.write_json(path, {"replacement": True})
            self.assertEqual(data.read_json(path), {"original": True})

    def test_report_recomputes_raw_samples_and_rejects_changed_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            entries = []
            for index, value in enumerate(series()):
                path = directory / f"{index}.json"
                main.write_json(path, value)
                entries.append({"file": path.name, "sha256": data.sha256(path.read_bytes())})
            correctness = attempt()["result"]
            main.write_json(directory / "correctness.json", correctness)
            dataset = {"schema_version": 1, "source_unchanged": True, "binary_unchanged": True,
                       "correctness": {"result_sha256": data.sha256((directory / "correctness.json").read_bytes()),
                                       "observations": data.correctness_observations(correctness)}, "policy": data.POLICY, "raw": entries,
                       "summaries": data.summarise(series()), "started_utc": "synthetic", "finished_utc": "synthetic",
                       "environment": {"cpu_model": "fixture CPU", "os_release": "fixture OS", "kernel": "fixture", "architecture": "test"}}
            main.write_json(directory / "dataset.json", dataset)
            self.assertIn("15,360", main.report(directory))
            (directory / "1.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "raw sample is missing, changed"):
                main.report(directory)

    def test_manifest_hash_failure_prevents_collection_mutation(self):
        manifest = {"schema_version": 1, "family": "falling-block-refined-v1",
                    "configuration": "bad.toml", "configuration_sha256": "wrong", "cases": [
                        {"particles": p, "scene": "scene.toml", "sha256": "wrong", "golden": None}
                        for p in [27, *data.POLICY["particles"]]]}
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "reference").mkdir()
            main.write_json(root / "reference/manifest.json", manifest)
            (root / "bad.toml").write_text("synthetic", encoding="utf-8")
            with patch.object(main, "SIMULATOR", root):
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    main.collect(root / "output")
            self.assertFalse((root / "output").exists())


if __name__ == "__main__":
    unittest.main()
