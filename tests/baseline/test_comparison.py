"""Paired timings need independently owned, identical physical observations."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.baseline import compare, data, main
from tests.baseline.test_baseline import series


def campaign(directory, backend, scale=1.0, mutate=None):
    directory.mkdir()
    attempts = series()
    for value in attempts:
        result = value["result"]
        result.update(backend=data.BACKENDS[backend], input={"position": -0.0},
                      final_snapshot={"position": 1.25},
                      metadata={"backend": data.BACKENDS[backend], "run_id": backend,
                                "input_id": "same-physical-input", "configuration_id": "same-config"})
        if "measurements" in result:
            for step in result["measurements"]["steps"]:
                step["total_s"] *= scale
                if step["stages"]:
                    step["stages"] = {k: v * scale for k, v in step["stages"].items()}
    correctness = copy.deepcopy(attempts[0]["result"])
    if mutate:
        mutate(attempts)
    entries = []
    for index, value in enumerate(attempts):
        value["result"] = data.compact_result(value["result"])
        path = directory / f"{index}.json"
        main.write_json(path, value)
        entries.append({"file": path.name, "sha256": data.sha256(path.read_bytes())})
    main.write_json(directory / "correctness.json", correctness)
    env = dict.fromkeys(("cpu_model", "architecture", "kernel", "os_release", "cpu_topology", "cpu_affinity",
                         "rustc", "cargo", "profile", "rustflags", "scheduling_controls", "virtualisation"), "synthetic")
    dataset = {"schema_version": 1, "backend": backend, "interrupted": False,
               "source_unchanged": True, "binary_unchanged": True,
               "source": {"base_commit": "synthetic", "tree_sha256": "synthetic"},
               "binary_sha256": "synthetic", "manifest": {}, "manifest_sha256": "synthetic",
               "collector_files_sha256": {}, "policy": data.POLICY,
               "environment": env, "started_utc": "synthetic", "finished_utc": "synthetic",
               "raw": entries, "summaries": data.summarise(attempts),
               "correctness": {"result_sha256": data.sha256((directory / "correctness.json").read_bytes()),
                               "observations": data.correctness_observations(correctness)}}
    main.write_json(directory / "dataset.json", dataset)


class ComparisonTests(unittest.TestCase):
    def pair(self, directory, mutate=None):
        campaign(directory / "brute-force", "brute-force")
        campaign(directory / "uniform-grid", "uniform-grid", 0.5, mutate)

    def test_ratio_uses_primary_medians_and_requires_shared_complete_sizes(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            self.pair(directory)
            result, text = compare.report(directory)
            row = result["rows"][0]
            self.assertAlmostEqual(row["speedup"], 2.0)
            self.assertEqual(row["exact_complete_attempts"], 10)
            self.assertIn("2.000×", text)
            self.assertIsNone(result["rows"][1]["speedup"])

    def test_signed_zero_checkpoint_and_cfl_disagreements_reject_timings(self):
        mutations = [lambda a: a[1]["result"]["input"].update(position=0.0),
                     lambda a: a[1]["result"]["checkpoints"][2]["snapshot"]["particles"][0]["position_m"].update(x=0.01),
                     lambda a: a[1]["result"]["steps"][10].update(maximum_speed_m_s=0.01)]
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as name:
                directory = Path(name)
                self.pair(directory, mutate)
                with self.assertRaises(ValueError):
                    compare.report(directory)

    def test_changed_machine_source_backend_and_duplicate_samples_are_rejected(self):
        for field in ("environment", "source", "backend"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as name:
                directory = Path(name)
                self.pair(directory)
                path = directory / "uniform-grid/dataset.json"
                dataset = data.read_json(path)
                if field == "environment":
                    dataset[field]["cpu_model"] = "different CPU"
                elif field == "source":
                    dataset[field]["base_commit"] = "different revision"
                else:
                    dataset[field] = "brute-force"
                path.write_text(json.dumps(dataset), encoding="utf-8")
                with self.assertRaises(ValueError):
                    compare.report(directory)
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            self.pair(directory, lambda a: a[2].update(index=1))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                compare.report(directory)

    def test_interrupted_full_result_is_not_a_clean_sample(self):
        value = series()[1]
        value["interrupted"] = True
        self.assertFalse(data.clean(value))

    def test_timeout_and_missing_primary_sets_have_no_speedup(self):
        for mutate in (lambda a: a[0].update(timed_out=True), lambda a: a.pop(2)):
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as name:
                directory = Path(name)
                self.pair(directory, mutate)
                self.assertIsNone(compare.report(directory)[0]["rows"][0]["speedup"])

    def test_backend_is_explicit_and_profile_overhead_is_separate(self):
        case = {"scene": "synthetic.toml", "steps": 480, "refine_timestep": 4, "checkpoints": [0, 480]}
        for backend in data.BACKENDS:
            args = main.solver_args(Path("solver"), case, "sample", backend)
            self.assertEqual(args[args.index("--backend") + 1], backend)
            self.assertIn("--measure", args)
            self.assertNotIn("--stage-profile", args)
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "new"
            with self.assertRaisesRegex(ValueError, "unsupported"):
                main.collect(path, "unknown")
            self.assertFalse(path.exists())

    def test_interruption_stops_before_launching_the_other_backend(self):
        def interrupted(directory, backend):
            directory.mkdir()
            main.write_json(directory / "dataset.json", {"interrupted": True})

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name) / "new"
            with patch.object(main, "collect", side_effect=interrupted) as collector:
                with self.assertRaisesRegex(ValueError, "interrupted"):
                    compare.collect(directory)
                self.assertEqual(collector.call_count, 1)
            self.assertTrue((directory / "brute-force/dataset.json").is_file())
            self.assertFalse((directory / "uniform-grid").exists())


if __name__ == "__main__":
    unittest.main()
