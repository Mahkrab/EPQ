"""Timing acceptance requires complete components, fixed resources and fresh controls."""

import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.baseline import data, main as baseline
from tools.cuda import performance
from tests.evidence.checks import cuda_performance as independent
from tests.baseline.test_baseline import series


def fixture(root):
    manifest = baseline.checked_manifest()
    golden = data.read_json(baseline.SIMULATOR / manifest["cases"][1]["golden"])
    golden["metadata"].update(build_revision="synthetic", debug_assertions=False)
    baseline.write_json(root / "campaign.json", {
        "schema_version": 1, "policy": "cuda-comparison-v1",
        "collection_order": [s[0] for s in performance.SETTINGS],
        "device": {"name": "synthetic", "ordinal": 0, "target": "compute_89"},
        "protocol_sha256": data.sha256(b"synthetic protocol"),
        "context": {"target": "89", "ptx_sha256": {"synthetic": "synthetic"}}, "collector_files_sha256": {},
    })
    (root / "protocol.md").write_bytes(b"synthetic protocol")
    for name, workers, cuda in performance.SETTINGS:
        directory = root / name
        directory.mkdir()
        execution, identity = baseline.execution_settings("uniform-grid", workers, cuda)
        correct = copy.deepcopy(golden)
        correct["backend"] = correct["metadata"]["backend"] = identity
        if execution["mode"] != "serial":
            correct["execution"] = execution
        if cuda:
            correct["metadata"]["device"] = {"name": "synthetic", "ordinal": 0, "target": "compute_89"}
        baseline.write_json(directory / "correctness.json", correct)
        attempts, entries = [], []
        for i, a in enumerate(series()):
            result = copy.deepcopy(correct)
            if a["kind"] != "warmup":
                result["measurements"] = a["result"]["measurements"]
                result["measurements"].update(solver_construction_s=0.1, solver_teardown_s=0.01)
            a.update(result=result, wall_s=10.0)
            payload = gzip.compress(json.dumps(result).encode(), mtime=0)
            (directory / f"{i}.gz").write_bytes(payload)
            a["full_result"] = {"file": f"{i}.gz", "sha256": data.sha256(payload)}
            a["result"] = data.compact_result(result)
            baseline.write_json(directory / f"{i}.json", a)
            attempts.append(a)
            entries.append({"file": f"{i}.json", "sha256": data.sha256((directory / f"{i}.json").read_bytes())})
        environment = dict.fromkeys(performance.ENVIRONMENT_FIELDS, "synthetic")
        baseline.write_json(directory / "dataset.json", {
            "schema_version": 1, "policy": data.POLICY, "backend": "uniform-grid", "execution": execution,
            "source_unchanged": True, "binary_unchanged": True, "interrupted": False,
            "source": {"files_sha256": {}, "tree_sha256": data.sha256(b"{}")},
            "binary_sha256": "synthetic", "build_revision": "synthetic", "epq_base_commit": "synthetic",
            "collector_files_sha256": {}, "manifest": manifest,
            "manifest_sha256": data.sha256((baseline.SIMULATOR / "reference/manifest.json").read_bytes()),
            "environment": environment, "started_utc": "synthetic", "finished_utc": "synthetic",
            "raw": entries, "summaries": data.summarise(attempts),
            "correctness": {"result_sha256": data.sha256((directory / "correctness.json").read_bytes()),
                            "observations": data.correctness_observations(correct)},
        })


def mutate(root, name, change, *, full=True):
    directory = root / name
    dataset = data.read_json(directory / "dataset.json")
    entry = dataset["raw"][1]
    path = directory / entry["file"]
    a = data.read_json(path)
    change(a)
    if full:
        original = json.loads(gzip.decompress((directory / a["full_result"]["file"]).read_bytes()))
        # Apply the same mutation to the original, preserving its particle arrays.
        wrapper = copy.deepcopy(a)
        wrapper["result"] = original
        change(wrapper)
        payload = gzip.compress(json.dumps(wrapper["result"]).encode(), mtime=0)
        (directory / a["full_result"]["file"]).write_bytes(payload)
        a["full_result"]["sha256"] = data.sha256(payload)
        a["result"] = data.compact_result(wrapper["result"])
    path.write_text(json.dumps(a), encoding="utf-8")
    entry["sha256"] = data.sha256(path.read_bytes())
    dataset["summaries"] = data.summarise(baseline.load_attempts(directory, dataset))
    (directory / "dataset.json").write_text(json.dumps(dataset), encoding="utf-8")


class PerformanceTests(unittest.TestCase):
    def test_cuda_arguments_and_rejections_before_creating_output(self):
        case = {"scene": "synthetic", "steps": 480, "refine_timestep": 4, "checkpoints": [0, 480]}
        args = baseline.solver_args(Path("solver"), case, "sample", "uniform-grid", cuda=(0, 128))
        self.assertEqual(args[args.index("--block-size") + 1], "128")
        self.assertEqual(args[args.index("--execution") + 1], "cuda")
        for backend, workers, cuda in [("brute-force", None, (0, 128)), ("uniform-grid", 12, (0, 128)),
                                       ("uniform-grid", None, (-1, 128)), ("uniform-grid", None, (0, 17))]:
            with self.assertRaises(ValueError):
                baseline.execution_settings(backend, workers, cuda)

    def test_components_lifecycle_and_missing_sizes(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            fixture(root)
            result, text = performance.report(root)
            self.assertEqual(len(result["comparisons"]), 18)
            for row in result["rows"][:3]:
                self.assertEqual(row["exact_complete_attempts"], 5)
                self.assertEqual(row["speedup_against_cuda"], 1)
                self.assertEqual(row["invocation_median_s"], 10)
                self.assertEqual(row["solver_construction_median_s"], 0.1)
            self.assertIsNone(result["rows"][3]["speedup_against_cuda"])
            self.assertIn("No fresh brute-force", text)

    def test_changed_device_build_execution_and_components_reject_timings(self):
        changes = [lambda a: a["result"]["metadata"]["device"].update(name="wrong"),
                   lambda a: a["result"]["metadata"].update(build_revision="wrong"),
                   lambda a: a["result"]["execution"].update(threads=64),
                   lambda a: a["result"]["steps"][10].update(maximum_speed_m_s=9.0),
                   lambda a: a["result"]["checkpoints"][2]["density"].update(mean_error=1.0)]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                fixture(root)
                mutate(root, "cuda-grid", change)
                with self.assertRaises(ValueError):
                    performance.report(root)

    def test_missing_control_warning_and_timeout_supply_no_ratio(self):
        changes = [lambda a: a.update(timed_out=True),
                   lambda a: a["result"]["steps"][0].update(warning=True)]
        for change in changes:
            with tempfile.TemporaryDirectory() as name:
                root = Path(name)
                fixture(root)
                mutate(root, "cuda-grid", change)
                result, _ = performance.report(root)
                self.assertTrue(all(r["speedup_against_cuda"] is None for r in result["rows"][:3]))

    def test_full_payload_and_duplicate_attempts_cannot_be_substituted(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            fixture(root)
            mutate(root, "cuda-grid", lambda a: a["result"]["measurements"].update(solver_construction_s=2.0), full=False)
            with self.assertRaisesRegex(ValueError, "full and compact"):
                performance.report(root)
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            fixture(root)
            path = root / "cuda-grid/dataset.json"
            d = data.read_json(path)
            d["raw"].append(d["raw"][0])
            path.write_text(json.dumps(d), encoding="utf-8")
            with self.assertRaises(ValueError):
                performance.report(root)

    def test_existing_destination_is_preserved_without_build(self):
        with tempfile.TemporaryDirectory() as name, patch.object(baseline, "prepare_build") as build:
            with self.assertRaises(FileExistsError):
                performance.collect(Path(name))
            build.assert_not_called()

    def test_independent_audit_rejects_coherently_rehashed_but_wrong_median(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            fixture(root)
            comparison, _ = performance.report(root)
            baseline.write_json(root / "comparison.json", comparison)
            with patch.object(independent.subprocess, "check_output", return_value=b""):
                self.assertTrue(independent.audit(root)["passed"])
                path = root / "serial-grid/dataset.json"
                dataset = data.read_json(path)
                dataset["summaries"][0]["primary"]["median_s"] += 1
                path.write_text(json.dumps(dataset), encoding="utf-8")
                comparison["rows"][0]["primary"]["median_s"] += 1
                comparison["datasets_sha256"]["serial-grid"] = data.sha256(path.read_bytes())
                (root / "comparison.json").write_text(json.dumps(comparison), encoding="utf-8")
                with self.assertRaises(AssertionError):
                    independent.audit(root)


if __name__ == "__main__":
    unittest.main()
