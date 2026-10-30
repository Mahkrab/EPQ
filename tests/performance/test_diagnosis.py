"""Admission tests reject changed work, unsafe capacity and misleading process success."""

import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import tomllib
import unittest

from tools.performance import capture, context, contract, external, neighbours, report, retain, study, timeline
from tests.performance import audit


class ContractTests(unittest.TestCase):
    def test_allocation_matches_independently_summed_native_slots(self):
        n = 8000
        slots = [96000, 96000, 96000, 96000, 32000, 32000, 32000, 96000, 96000,
                 96, 262144, 8000000, 32000]
        self.assertEqual(contract.allocation(n)["membership_bytes"], 8000000)
        self.assertEqual(contract.allocation(n)["total_slot_bytes"], sum(slots))
        self.assertEqual(contract.allocation(100000)["membership_bytes"], 1250000000)
        for invalid in (0, -1, True, 1000001, 1.0):
            with self.assertRaises(ValueError):
                contract.allocation(invalid)

    def test_normal_path_operation_counts_are_not_claimed_as_measurements(self):
        result = contract.operations(8000)
        self.assertEqual(result["kernel_launches_per_step"], 144)
        self.assertEqual(result["error_array_downloads_per_step"], 52)
        self.assertEqual(result["download_calls_per_step"], 56)
        self.assertEqual(result["solver_wrapper_completions_per_step"], 219)
        self.assertEqual(result["reservation_calls_per_step"], 16)
        self.assertEqual(result["download_bytes_per_step"], 2048000)
        self.assertEqual(result["kind"], "source-derived-not-measured")

    def test_capacity_memory_admission_preserves_safety_margin(self):
        limits = dict(gpu_total=12 * contract.GIB, gpu_free=11 * contract.GIB,
                      host_available=8 * contract.GIB)
        self.assertTrue(contract.admit(110592, **limits)["admitted"])
        self.assertFalse(contract.admit(262144, **limits)["admitted"])
        self.assertFalse(contract.admit(512000, **limits)["admitted"])
        self.assertFalse(contract.admit(8000, **dict(limits, gpu_free=contract.GIB))["admitted"])
        self.assertFalse(contract.admit(8000, **dict(limits, host_available=3 * contract.GIB))["admitted"])
        with self.assertRaises(ValueError):
            contract.admit(8000, **dict(limits, gpu_free=13 * contract.GIB))

    def test_capacity_scene_has_exact_counts_geometry_and_plane_order(self):
        scene = tomllib.loads(contract.capacity_scene(48))
        self.assertEqual(scene["particles"]["counts"], [48, 48, 48])
        self.assertEqual(scene["particles"]["origin_m"], [0.2, 0.4, 0.2])
        self.assertEqual([p["offset_m"] for p in scene["planes"]], [0, -2.8, 0, -3.0, 0, -2.8])
        self.assertEqual([p["normal"] for p in scene["planes"]],
                         [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]])
        original = tomllib.loads(Path("Maelstrom/reference/scenes/falling-block-20.toml").read_text())
        capacity = tomllib.loads(contract.capacity_scene(20))
        for key in ("particles", "planes", "configuration", "randomness"):
            self.assertEqual(original[key], capacity[key])

    def test_every_request_is_explicit_and_core_requests_really_omit_audits(self):
        for series in contract.SERIES:
            args = contract.arguments("scene.toml", series)
            self.assertIn("--unpaced", args)
            self.assertEqual(args[args.index("--backend") + 1], series)
            self.assertEqual(args[args.index("--checkpoints") + 1], "0,1,120,240,480")
            self.assertNotIn("--stage-profile", args)
            core = contract.arguments("scene.toml", series, observation=False, kind="profile")
            self.assertNotIn("--checkpoints", core)
            self.assertIn("--stage-profile", core)
            self.assertIn("--measure", core)


class CaptureTests(unittest.TestCase):
    def test_original_output_is_hashed_and_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [sys.executable, "-c", "import json; print(json.dumps({'value': -0.0}))"]
            metadata, result = capture.invoke(command, root, root / "attempt")
            self.assertEqual(metadata["exit_code"], 0)
            self.assertEqual(result, {"value": -0.0})
            self.assertEqual(capture.load_attempt(root / "attempt"), (metadata, result))
            with self.assertRaises(FileExistsError):
                capture.invoke(command, root, root / "attempt")
            (root / "attempt/stderr.txt").write_text("changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                capture.load_attempt(root / "attempt")

    def test_malformed_output_and_launch_failure_are_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata, result = capture.invoke([sys.executable, "-c", "print('not json')"], root, root / "bad")
            self.assertIsNone(result)
            self.assertIsNotNone(metadata["parse_error"])
            self.assertTrue((root / "bad/stdout.gz").is_file())
            metadata, result = capture.invoke([str(root / "absent")], root, root / "absent-run")
            self.assertIsNone(metadata["exit_code"])
            self.assertIn("launch_error", metadata)
            self.assertIsNone(result)

    def test_timeout_reaps_process_and_retains_partial_or_incomplete_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata, _ = capture.invoke([sys.executable, "-c", "import time; print('{}', flush=True); time.sleep(30)"],
                                         root, root / "timeout", timeout=0.1, grace=1)
            self.assertTrue(metadata["timed_out"])
            self.assertNotEqual(metadata["exit_code"], 0)
            self.assertLess(metadata["wall_s"], 5)
            self.assertTrue((root / "timeout/stdout.gz").is_file())


class NeighbourTests(unittest.TestCase):
    def test_strict_boundary_self_exclusion_and_coincident_distinct_points(self):
        value = neighbours.counts([(0, 0, 0), (0.5, 0, 0), (1, 0, 0)], 1.0)
        self.assertEqual(value["directed_neighbours"], 4)
        self.assertEqual(value["minimum"], 1)
        self.assertEqual(value["maximum"], 2)
        self.assertEqual(neighbours.counts([(0, 0, 0), (0, 0, 0)], 1.0)["directed_neighbours"], 2)
        self.assertEqual(neighbours.counts([], 1.0)["directed_neighbours"], 0)
        # Shortest JSON decimals must first recover their binary32 coordinates:
        # f32(0.3)-f32(0.2) is outside f32(0.1), despite decimal subtraction.
        self.assertEqual(neighbours.counts([(0.2, 0, 0), (0.3, 0, 0)], 0.1)["directed_neighbours"], 0)
        with self.assertRaises(ValueError):
            neighbours.counts([(float("nan"), 0, 0)], 1.0)


class MetricTests(unittest.TestCase):
    def test_timeline_coverage_counts_overlap_only_once(self):
        self.assertEqual(timeline.union([(0, 10), (2, 4), (8, 12), (15, 20)]), 17)
        self.assertEqual(timeline.union([]), 0)
        with self.assertRaises(ValueError):
            timeline.union([(2, 1)])

    def test_solver_and_invocation_boundaries_remain_distinct(self):
        document = {"completed_steps": "2", "steps": [{"completed_steps": "1"}, {"completed_steps": "2"}],
                    "input": {"configuration": {"numerical": {"fixed_timestep_s": 0.25}}},
                    "measurements": {"schema_version": 1, "mode": "total", "failed_attempt_s": None,
                      "solver_construction_s": 0.1, "solver_teardown_s": 0.2,
                      "steps": [{"total_s": 0.25, "stages": None}, {"total_s": 0.75, "stages": None}]}}
        result = report.metrics({"wall_s": 2.0}, document, "sample")
        self.assertEqual(result["solver_s"], 1.0)
        self.assertEqual(result["solver_real_time_factor"], 0.5)
        self.assertEqual(result["invocation_real_time_factor"], 0.25)
        self.assertEqual(result["first_step_s"], 0.25)
        self.assertEqual(result["remaining_step_median_s"], 0.75)
        document["measurements"]["steps"][0]["stages"] = {}
        with self.assertRaisesRegex(ValueError, "profiling"):
            report.metrics({"wall_s": 2.0}, document, "sample")


class AdmissionTests(unittest.TestCase):
    def document(self):
        return {"status": "completed", "failures": [], "execution": {"mode": "cuda", "device": 0, "threads": 128},
                "backend": "cuda-uniform-grid-pbf-binary32-8-jacobi-v1",
                "request": {"steps": "1", "checkpoints": []}, "completed_steps": "1",
                "steps": [{"completed_steps": "1", "warning": False}], "checkpoints": [],
                "metadata": {"build_revision": contract.SOURCE_COMMIT, "debug_assertions": False,
                             "backend": "cuda-uniform-grid-pbf-binary32-8-jacobi-v1"},
                "input": {"particles": [{"identity": "0"}]},
                "final_snapshot": {"completed_steps": "1", "particles": [{"identity": "0"}]}}

    def test_success_exit_does_not_admit_wrong_resources_work_warnings_or_counts(self):
        process = {"exit_code": 0, "timed_out": False, "interrupted": False}
        arguments = dict(series="cuda", steps=1, observation=False, particles=1)
        self.assertTrue(study.clean(process, self.document(), **arguments))
        for mutate in (lambda d: d["execution"].update(threads=64),
                       lambda d: d["steps"][0].update(warning=True),
                       lambda d: d.update(completed_steps="0"),
                       lambda d: d["input"]["particles"].append({"identity": "1"}),
                       lambda d: d["metadata"].update(debug_assertions=True)):
            document = self.document()
            mutate(document)
            self.assertFalse(study.clean(process, document, **arguments))
        self.assertFalse(study.clean(dict(process, timed_out=True), self.document(), **arguments))

    def test_serial_execution_uses_the_record_formats_documented_omission(self):
        document = self.document()
        document.pop("execution")
        document["backend"] = document["metadata"]["backend"] = "serial-uniform-grid-pbf-binary32-8-jacobi-v2"
        self.assertTrue(study.clean({"exit_code": 0}, document, series="serial-grid", steps=1,
                                    observation=False, particles=1))


class EvidenceTests(unittest.TestCase):
    @staticmethod
    def record(path, document):
        path.mkdir(parents=True)
        raw = json.dumps(document).encode()
        packed = gzip.compress(raw, mtime=0)
        (path / "stdout.gz").write_bytes(packed)
        (path / "stderr.txt").write_bytes(b"")
        process = {"exit_code": 0, "timed_out": False, "interrupted": False, "parse_error": None,
                   "wall_s": 2, "stdout_sha256": hashlib.sha256(raw).hexdigest(),
                   "stdout_gzip_sha256": hashlib.sha256(packed).hexdigest(),
                   "stderr_sha256": hashlib.sha256(b"").hexdigest()}
        (path / "process.json").write_text(json.dumps(process))

    def test_independent_audit_rejects_false_median_and_corrupted_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = []
            for count in (64, 216, 512, 1000, 1728, 4096, 8000):
                for series in ("serial-grid", "threaded-grid", "cuda"):
                    for name in ("warmup", "sample-1", "sample-2", "sample-3", "profile"):
                        mode = "stages" if name == "profile" else "total"
                        document = {"metadata": {}, "request": {"steps": "480", "checkpoints": ["0", "1", "120", "240", "480"]},
                                    "status": "completed", "failures": [], "completed_steps": "480",
                                    "steps": [{"warning": False}] * 480,
                                    "measurements": {"mode": mode, "steps": [
                                        {"total_s": 0.125, "stages": {"work": 0.1} if mode == "stages" else None}] * 480}}
                        self.record(root / f"baseline/{series}/{count:06}/{name}", document)
                    rows.append({"series": series, "particles": count, "primary": {
                        "sample_totals_s": [60, 60, 60], "median_solver_s": 60, "minimum_s": 60, "maximum_s": 60}})
            summary = root / "summary.json"
            summary.write_text(json.dumps({"baseline": rows, "capacity": []}))
            self.assertEqual(audit.audit(root, summary)["component_equal_baseline_attempts"], 105)
            rows[0]["primary"]["median_solver_s"] = 59
            summary.write_text(json.dumps({"baseline": rows, "capacity": []}))
            with self.assertRaisesRegex(ValueError, "false median"):
                audit.audit(root, summary)
            rows[0]["primary"]["median_solver_s"] = 60
            summary.write_text(json.dumps({"baseline": rows, "capacity": []}))
            (root / "baseline/cuda/008000/sample-1/stderr.txt").write_text("changed")
            with self.assertRaisesRegex(ValueError, "evidence changed"):
                audit.audit(root, summary)
        self.assertFalse(audit.same(0.0, -0.0))
        self.assertFalse(audit.same(float("nan"), float("nan")))

    def test_native_profiler_files_stay_private_without_dropping_ordinary_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "original"
            source.mkdir()
            for name in ("cuda.nsys-rep", "correction.ncu-rep", "perf.data"):
                (source / name).write_bytes(b"synthetic private native report")
            (source / "observation.json").write_text('{"completed":true}')
            retain.retain(source, root / "shareable")
            self.assertEqual((root / "shareable/observation.json").read_text(), '{"completed":true}')
            for name in ("cuda.nsys-rep", "correction.ncu-rep", "perf.data"):
                self.assertFalse((root / "shareable" / name).exists())
            records = json.loads((root / "shareable/privacy.json").read_bytes())
            self.assertEqual(set(records["native_reports_not_published"]), {"cuda.nsys-rep", "correction.ncu-rep", "perf.data"})

    def test_sanitisation_removes_environment_bytes_but_preserves_timing_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "original.sqlite"
            with sqlite3.connect(source) as connection:
                connection.execute("CREATE TABLE StringIds(id INTEGER, value TEXT)")
                connection.executemany("INSERT INTO StringIds VALUES(?,?)",
                                       [(1, "TOKEN=synthetic-token\0HOME=/home/test"), (2, "cuLaunchKernel")])
                connection.execute("CREATE TABLE TARGET_INFO_SYSTEM_ENV(name TEXT,value TEXT)")
                connection.execute("INSERT INTO TARGET_INFO_SYSTEM_ENV VALUES('Hostname','synthetic-host')")
                connection.execute("CREATE TABLE META_DATA_CAPTURE(name TEXT,value TEXT)")
                connection.execute("INSERT INTO META_DATA_CAPTURE VALUES('PROCESS_0:ENVIRONMENT_VARIABLE','KEY=synthetic-private-value')")
                connection.execute("CREATE TABLE timing(start INTEGER,end INTEGER,nameId INTEGER)")
                connection.execute("INSERT INTO timing VALUES(10,20,2)")
            original_bytes = source.read_bytes()
            result = retain.sanitise(source, root / "shareable.sqlite")
            self.assertIn("timing", result["unchanged_table_sha256"])
            with sqlite3.connect(root / "shareable.sqlite") as connection:
                self.assertEqual(connection.execute("SELECT * FROM timing").fetchall(), [(10, 20, 2)])
                self.assertEqual(connection.execute("SELECT value FROM StringIds WHERE id=2").fetchone(), ("cuLaunchKernel",))
            for private in (b"synthetic-token", b"synthetic-host", b"/home/test", b"synthetic-private-value"):
                self.assertNotIn(private, (root / "shareable.sqlite").read_bytes())
            self.assertEqual(source.read_bytes(), original_bytes)
            with self.assertRaises(FileExistsError):
                retain.sanitise(source, root / "shareable.sqlite")

    def test_external_counters_cannot_hide_wrong_work_or_changed_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "external/inputs/000002"
            target = root / "external/runs/000002"
            package.mkdir(parents=True)
            identity = {"position_binary32_sha256": hashlib.sha256(external.position_bytes([[0, 1, 2], [3, 4, 5]])).hexdigest()}
            for name, key in (("particles.pts", "pts_sha256"), ("scene.json", "scene_sha256"), ("box.obj", "geometry_sha256")):
                (package / name).write_bytes(b"synthetic fixture")
                identity[key] = hashlib.sha256(b"synthetic fixture").hexdigest()
            (package / "identity.json").write_text(json.dumps(identity))
            (root / "external/build-identity.json").write_text(json.dumps({"upstream_revision": external.REVISION, "binary_sha256": "synthetic"}))
            self.record(target / "import-check", {"count": 2, "positions": [[0, 1, 2], [3, 4, 5]]})
            (target / "input-admission.json").write_text(json.dumps({"passed": True, "upstream_revision": external.REVISION, "comparator_sha256": "synthetic"}))
            raw = b"Number of fluid particles: 2\nNumber of boundary particles: 6\nAverage number: PBF - iterations: 8\nTotal number: PBF - iterations: 3840\nTime sum: SimStep: 1000 ms\nTotal number: Time step size: 1.00001\nTime sum: pressureSolve: 800 ms\nTime sum: neighborhood_search: 100 ms\n"
            self.record(target / "run", {})
            process = json.loads((target / "run/process.json").read_bytes())
            def log(payload):
                packed = gzip.compress(payload, mtime=0)
                (target / "run/stdout.gz").write_bytes(packed)
                process.update(stdout_sha256=hashlib.sha256(payload).hexdigest(), stdout_gzip_sha256=hashlib.sha256(packed).hexdigest(), parse_error="text log")
                (target / "run/process.json").write_text(json.dumps(process))
            log(raw)
            self.assertEqual(context.external(root, 2)["steps_inferred_from_iteration_counters"], 480)
            log(raw.replace(b"3840", b"3832"))
            with self.assertRaisesRegex(ValueError, "480"):
                context.external(root, 2)
            log(raw)
            (package / "particles.pts").write_bytes(b"different")
            with self.assertRaisesRegex(ValueError, "input changed"):
                context.external(root, 2)


if __name__ == "__main__":
    unittest.main()
