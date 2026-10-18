"""Worker ratios require the declared resources and exact same-device controls."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.baseline import data, main, scaling
from tests.baseline.test_comparison import campaign


def fixture(directory):
    names = ["serial-grid", "workers-1", "workers-2"]
    for name, workers, scale in zip(names, [None, 1, 2], [1.0, 2.0, 0.5], strict=True):
        path = directory / name
        campaign(path, "uniform-grid", scale)
        dataset = data.read_json(path / "dataset.json")
        execution, identity = main.execution_settings("uniform-grid", workers)
        dataset.update(build_revision="synthetic", epq_base_commit="synthetic",
                       manifest={"cases": [{}, {"golden": "golden.json", "golden_sha256": "pending"}]})
        if workers:
            dataset["execution"] = execution
        for entry in dataset["raw"]:
            raw_path = path / entry["file"]
            a = data.read_json(raw_path)
            a["wall_s"] = 10.0
            a["result"]["backend"] = a["result"]["metadata"]["backend"] = identity
            a["result"]["metadata"].update(debug_assertions=False, build_revision="synthetic")
            if workers:
                a["result"]["execution"] = execution
            raw_path.write_text(json.dumps(a), encoding="utf-8")
            entry["sha256"] = data.sha256(raw_path.read_bytes())
        correct_path = path / "correctness.json"
        c = data.read_json(correct_path)
        c["backend"] = c["metadata"]["backend"] = identity
        c["metadata"].update(debug_assertions=False, build_revision="synthetic")
        if workers:
            c["execution"] = execution
        correct_path.write_text(json.dumps(c), encoding="utf-8")
        dataset["correctness"]["result_sha256"] = data.sha256(correct_path.read_bytes())
        (path / "dataset.json").write_text(json.dumps(dataset), encoding="utf-8")
    golden = data.read_json(directory / "serial-grid/correctness.json")
    (directory / "golden.json").write_text(json.dumps(golden), encoding="utf-8")
    for name in names:
        path = directory / name / "dataset.json"
        d = data.read_json(path)
        d["manifest"]["cases"][1]["golden_sha256"] = data.sha256((directory / "golden.json").read_bytes())
        path.write_text(json.dumps(d), encoding="utf-8")
    (directory / "protocol.md").write_text("synthetic protocol", encoding="utf-8")
    main.write_json(directory / "campaign.json", {
        "schema_version": 1, "workers": [1, 2], "collection_order": names, "default_workers": 2,
        "default_probe": {"exit_code": 0, "timed_out": False, "interrupted": False,
                          "result": {"execution": {"mode": "threaded", "workers": 2}}},
        "protocol_sha256": data.sha256((directory / "protocol.md").read_bytes()),
    })


def mutate_attempt(directory, name, change):
    path = directory / name
    d = data.read_json(path / "dataset.json")
    entry = d["raw"][1]
    raw = path / entry["file"]
    a = data.read_json(raw)
    change(a)
    raw.write_text(json.dumps(a), encoding="utf-8")
    entry["sha256"] = data.sha256(raw.read_bytes())
    d["summaries"] = data.summarise(main.load_attempts(path, d))
    (path / "dataset.json").write_text(json.dumps(d), encoding="utf-8")


class ScalingTests(unittest.TestCase):
    def test_worker_arguments_and_invalid_requests_before_mutation(self):
        case = {"scene": "fixture", "steps": 480, "refine_timestep": 4, "checkpoints": [0, 480]}
        args = main.solver_args(Path("solver"), case, "sample", "uniform-grid", 2)
        self.assertEqual(args[args.index("--threads") + 1], "2")
        self.assertEqual(args[args.index("--execution") + 1], "threaded")
        for workers in (0, 257, True):
            with self.assertRaises(ValueError):
                main.execution_settings("uniform-grid", workers)
        with self.assertRaises(ValueError):
            main.execution_settings("brute-force", 2)
        for workers in ([], [2], [1, 1], [1, 3, 2], [1, 257]):
            with self.assertRaises(ValueError):
                scaling.worker_sequence(workers)

    def test_ratios_use_fresh_serial_and_one_worker_denominators(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            fixture(directory)
            with patch.object(main, "SIMULATOR", directory):
                result, text = scaling.report(directory)
            row = result["rows"][2]
            self.assertAlmostEqual(row["serial_grid_speedup"], 2)
            self.assertAlmostEqual(row["one_worker_scaling"], 4)
            self.assertAlmostEqual(row["requested_worker_efficiency"], 2)
            self.assertEqual(row["exact_complete_attempts"], 5)
            self.assertEqual(row["invocation_median_s"], 10)
            self.assertIsNone(result["rows"][5]["serial_grid_speedup"])
            self.assertIn("No fresh brute-force", text)

    def test_changed_workers_components_audits_warnings_and_hashes_reject_acceptance(self):
        mutations = [lambda a: a["result"]["execution"].update(workers=3),
                     lambda a: a["result"]["steps"][10].update(maximum_speed_m_s=1.0),
                     lambda a: a["result"]["checkpoints"][2]["density"].update(mean_error=1.0),
                     lambda a: a["result"].update(final_snapshot_sha256="unequal"),
                     lambda a: a["result"].update(input_sha256="unequal"),
                     lambda a: a.update(numerical_agreement=False)]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as name:
                directory = Path(name)
                fixture(directory)
                mutate_attempt(directory, "workers-2", mutation)
                with patch.object(main, "SIMULATOR", directory), self.assertRaises(ValueError):
                    scaling.report(directory)
        for mutation in (lambda a: a.update(timed_out=True),
                         lambda a: a["result"]["steps"][0].update(warning=True)):
            with tempfile.TemporaryDirectory() as name:
                directory = Path(name)
                fixture(directory)
                mutate_attempt(directory, "workers-2", mutation)
                with patch.object(main, "SIMULATOR", directory):
                    self.assertIsNone(scaling.report(directory)[0]["rows"][2]["serial_grid_speedup"])

    def test_absent_or_timed_out_control_cannot_supply_any_ratio(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            fixture(directory)
            mutate_attempt(directory, "serial-grid", lambda a: a.update(timed_out=True))
            with patch.object(main, "SIMULATOR", directory):
                rows = scaling.report(directory)[0]["rows"]
            self.assertTrue(all(row["serial_grid_speedup"] is None for row in rows))

    def test_source_environment_and_duplicate_samples_are_rejected(self):
        for field in ("source", "environment", "duplicate"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as name:
                directory = Path(name)
                fixture(directory)
                path = directory / "workers-2/dataset.json"
                d = data.read_json(path)
                if field == "source":
                    d["source"]["base_commit"] = "different"
                elif field == "environment":
                    d["environment"]["cpu_affinity"] = [999]
                else:
                    d["raw"].append(copy.deepcopy(d["raw"][0]))
                path.write_text(json.dumps(d), encoding="utf-8")
                with patch.object(main, "SIMULATOR", directory), self.assertRaises(ValueError):
                    scaling.report(directory)

    def test_existing_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            with patch.object(main, "prepare_build") as build:
                with self.assertRaises(FileExistsError):
                    scaling.collect(directory, [1, 2])
                build.assert_not_called()

    def test_interruption_stops_before_next_series_and_reuses_prepared_binary(self):
        probe = {"exit_code": 0, "timed_out": False, "interrupted": False,
                 "result": data.read_json(main.SIMULATOR / main.checked_manifest()["cases"][1]["golden"])}
        probe["result"]["execution"] = {"mode": "threaded", "workers": 2}

        def interrupted(directory, backend, workers, *, build):
            directory.mkdir()
            main.write_json(directory / "dataset.json", {"interrupted": True})

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name) / "new"
            with (patch.object(main, "prepare_build", return_value={"prepared": True}) as builder,
                  patch.object(main, "invoke", return_value=probe),
                  patch.object(main, "collect", side_effect=interrupted) as collector):
                with self.assertRaisesRegex(ValueError, "interrupted"):
                    scaling.collect(directory, [1, 2])
                builder.assert_called_once()
                collector.assert_called_once_with(directory / "serial-grid", "uniform-grid", None,
                                                  build={"prepared": True})
                self.assertFalse((directory / "workers-1").exists())


if __name__ == "__main__":
    unittest.main()
