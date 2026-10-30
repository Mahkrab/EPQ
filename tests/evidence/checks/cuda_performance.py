"""Audit completed-step comparisons directly from retained components and clocks.

This check uses no collector imports. Pass the campaign directory as its argument;
the current source files and frozen inputs must still match their retained hashes.
"""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
STAGES = ("validation_and_acceleration_s", "prediction_s", "neighbour_search_s",
          "jacobi_s", "projection_s", "acceptance_s")
SIZES = [64, 216, 512, 1000, 1728, 4096, 8000]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical(result):
    value = copy.deepcopy(result)
    for key in ("measurements", "backend", "execution"):
        value.pop(key, None)
    for key in ("backend", "run_id", "build_revision", "target_arch", "target_os", "debug_assertions", "device"):
        value["metadata"].pop(key, None)
    return value


def bits(value):
    if isinstance(value, float):
        assert math.isfinite(value)
        return struct.pack("!f", value)
    if isinstance(value, list):
        return [bits(v) for v in value]
    if isinstance(value, dict):
        return {k: bits(v) for k, v in value.items()}
    return value


def seconds(value):
    assert type(value) in (int, float) and math.isfinite(value) and value >= 0
    return value


def near(actual, expected):
    assert math.isfinite(actual) and math.isfinite(expected)
    assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (actual, expected)


def clean(a):
    r = a["result"]
    return bool(r and a["exit_code"] == 0 and not a["timed_out"] and not a.get("interrupted", False)
                and r["status"] == "completed" and r["completed_steps"] == "480"
                and r["request"] == {"steps": "480", "checkpoints": ["0", "1", "120", "240", "480"]}
                and len(r["steps"]) == 480 and not r["failures"]
                and not any(s["warning"] for s in r["steps"])
                and [c["snapshot"]["completed_steps"] for c in r["checkpoints"]] == ["0", "1", "120", "240", "480"]
                and all(c["density"] is not None for c in r["checkpoints"])
                and a.get("numerical_agreement", True))


def compact(result):
    value = copy.deepcopy(result)
    def hashed(v):
        return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    for key in ("input", "final_snapshot"):
        value[f"{key}_sha256"] = hashed(value.pop(key))
    for c in value["checkpoints"]:
        snapshot = c["snapshot"]
        c["snapshot"] = {"completed_steps": snapshot["completed_steps"], "sha256": hashed(snapshot)}
    return value


def audit(directory):
    campaign = read(directory / "campaign.json")
    calculated = read(directory / "comparison.json")
    assert campaign["policy"] == "cuda-comparison-v1"
    names = ["serial-grid", "threaded-grid", "cuda-grid"]
    assert campaign["collection_order"] == names
    assert len(calculated["rows"]) == 21
    assert {(r["particles"], r["series"]) for r in calculated["rows"]} == {(s, n) for s in SIZES for n in names}
    assert digest(directory / "protocol.md") == campaign["protocol_sha256"]
    assert campaign["device"]["ordinal"] == 0 and campaign["device"]["target"] == "compute_89"
    assert campaign["context"]["target"] == "89" and campaign["context"]["ptx_sha256"]
    counts = dict(attempts=0, exact_complete_attempts=0, timeouts=0, unclean=0,
                  source_hashes=0, collector_hashes=0, correctness_results=0, profiles=0)
    for file, expected in campaign["collector_files_sha256"].items():
        assert digest(ROOT / file) == expected, file
        counts["collector_hashes"] += 1
    first, references, primary = None, {}, {}
    expected_comparisons = set()
    for name in names:
        path = directory / name
        d = read(path / "dataset.json")
        assert digest(path / "dataset.json") == calculated["datasets_sha256"][name]
        assert d["source_unchanged"] and d["binary_unchanged"] and not d["interrupted"]
        if first is None:
            first = d
            current_paths = subprocess.check_output(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                cwd=ROOT / "Maelstrom", timeout=60,
            ).decode().split("\0")
            current_paths = {p for p in current_paths if p and (ROOT / "Maelstrom" / p).is_file()}
            assert current_paths == set(d["source"]["files_sha256"])
            assert hashlib.sha256(json.dumps(d["source"]["files_sha256"], sort_keys=True).encode()).hexdigest() == d["source"]["tree_sha256"]
            for file, expected in d["source"]["files_sha256"].items():
                assert digest(ROOT / "Maelstrom" / file) == expected, file
                counts["source_hashes"] += 1
        else:
            for field in ("source", "binary_sha256", "build_revision", "policy", "manifest", "manifest_sha256", "collector_files_sha256", "epq_base_commit"):
                assert d[field] == first[field], field
            for field in ("cpu_model", "architecture", "kernel", "os_release", "cpu_topology", "cpu_affinity", "rustc", "cargo", "profile", "rustflags", "scheduling_controls", "virtualisation"):
                assert d["environment"][field] == first["environment"][field], field
        assert d["policy"]["particles"] == SIZES and d["policy"]["steps"] == 480
        assert d["policy"]["timeout_s"] == 120 and d["policy"]["cancellation_grace_s"] == 30
        assert digest(ROOT / "Maelstrom/reference/manifest.json") == d["manifest_sha256"]
        m = d["manifest"]
        assert digest(ROOT / "Maelstrom" / m["configuration"]) == m["configuration_sha256"]
        for case in m["cases"]:
            scene_path = ROOT / "Maelstrom" / case["scene"]
            if case["scene"].startswith("scenes/") and not scene_path.exists():
                scene_path = ROOT / "Maelstrom/reference" / case["scene"]
            assert digest(scene_path) == case["sha256"]
            if case["golden"]:
                assert digest(ROOT / "Maelstrom" / case["golden"]) == case["golden_sha256"]
        correct = read(path / "correctness.json")
        assert digest(path / "correctness.json") == d["correctness"]["result_sha256"]
        golden = read(ROOT / "Maelstrom" / m["cases"][1]["golden"])
        assert bits(physical(correct)) == bits(physical(golden))
        counts["correctness_results"] += 1
        expected_comparisons.add(f"{name}/correctness")
        execution = {"serial-grid": {"mode": "serial"}, "threaded-grid": {"mode": "threaded", "workers": 12},
                     "cuda-grid": {"mode": "cuda", "device": 0, "threads": 128}}[name]
        identity = {"serial-grid": "serial", "threaded-grid": "threaded", "cuda-grid": "cuda"}[name]
        identity += "-uniform-grid-pbf-binary32-8-jacobi-v" + ("1" if name == "cuda-grid" else "2")
        values, full = [], {}
        assert d.get("execution", {"mode": "serial"}) == execution
        for entry in d["raw"]:
            raw = (path / entry["file"]).resolve()
            assert raw.is_relative_to(path.resolve()) and digest(raw) == entry["sha256"]
            a = read(raw)
            key = a["particles"], a["kind"], a["index"]
            assert key not in full
            assert key[0] in SIZES and key[1] in ("warmup", "sample", "profile")
            assert key[2] in (range(1, 4) if key[1] == "sample" else [1])
            counts["attempts"] += 1
            counts["timeouts"] += a["timed_out"]
            counts["unclean"] += not clean(a)
            seconds(a["wall_s"])
            if a["result"]:
                source = (path / a["full_result"]["file"]).resolve()
                assert source.is_relative_to(path.resolve()) and digest(source) == a["full_result"]["sha256"]
                r = json.loads(gzip.decompress(source.read_bytes()))
                assert compact(r) == a["result"]
                assert r.get("execution", {"mode": "serial"}) == execution
                assert r["backend"] == r["metadata"]["backend"] == identity
                assert r["metadata"]["build_revision"] == d["build_revision"]
                assert not r["metadata"]["debug_assertions"]
                assert r["metadata"].get("device") == (campaign["device"] if name == "cuda-grid" else None)
                assert [s["completed_steps"] for s in r["steps"]] == [str(i) for i in range(1, int(r["completed_steps"]) + 1)]
                full[key] = r
            else:
                full[key] = None
            values.append(a)
        for size, stored in zip(SIZES, d["summaries"], strict=True):
            assert stored["particles"] == size
            group = [a for a in values if a["particles"] == size]
            warmups = [a for a in group if a["kind"] == "warmup"]
            samples = [a for a in group if a["kind"] == "sample"]
            if name == "serial-grid" and len(warmups) == 1 and clean(warmups[0]):
                references[size] = bits(physical(full[size, "warmup", 1]))
            exact = 0
            for a in group:
                if clean(a) and size in references:
                    assert bits(physical(full[size, a["kind"], a["index"]])) == references[size]
                    exact += 1
                    expected_comparisons.add(f"{name}/{size}/{a['kind']}/{a['index']}")
            counts["exact_complete_attempts"] += exact
            row = next(r for r in calculated["rows"] if r["particles"] == size and r["series"] == name)
            assert row["exact_complete_attempts"] == exact
            complete = len(warmups) == 1 and clean(warmups[0]) and len(samples) == 3 and all(clean(a) for a in samples)
            p = stored["primary"]
            assert (p is not None) == complete
            if complete:
                totals = [math.fsum(seconds(s["total_s"]) for s in a["result"]["measurements"]["steps"]) for a in samples]
                median = statistics.median(totals)
                for field, value in {"median_s": median, "minimum_s": min(totals), "maximum_s": max(totals),
                                     "mean_s": statistics.mean(totals), "sample_standard_deviation_s": statistics.stdev(totals),
                                     "median_step_s": median / 480, "particle_updates_per_s": size * 480 / median}.items():
                    near(p[field], value)
                for actual, expected in zip(p["sample_totals_s"], totals, strict=True):
                    near(actual, expected)
                primary[name, size] = median
            assert row["primary"] == (p if size in references else None)
            if row["primary"]:
                near(row["invocation_median_s"], statistics.median(seconds(a["wall_s"]) for a in samples))
            else:
                assert row["invocation_median_s"] is None
            for field, key in (("solver_construction_median_s", "solver_construction_s"), ("solver_teardown_median_s", "solver_teardown_s")):
                timings = [seconds(a["result"]["measurements"][key]) for a in samples if clean(a)]
                if len(timings) == 3:
                    near(row[field], statistics.median(timings))
                else:
                    assert row[field] is None
            for a in group:
                if a["kind"] == "warmup" or not a["result"]:
                    continue
                times = a["result"]["measurements"]
                assert len(times["steps"]) == int(a["result"]["completed_steps"])
                if times["failed_attempt_s"] is not None:
                    seconds(times["failed_attempt_s"])
                if a["kind"] == "sample":
                    assert times["mode"] == "total" and all(s["stages"] is None for s in times["steps"])
                    continue
                assert times["mode"] == "stages"
                total = math.fsum(seconds(s["total_s"]) for s in times["steps"])
                sums = {k: math.fsum(seconds(s["stages"][k]) for s in times["steps"]) for k in STAGES}
                profile = stored["profile"]
                assert row["profile"] == profile and profile["complete"] == clean(a)
                near(profile["total_s"], total)
                for k, v in sums.items():
                    near(profile["stages_s"][k], v)
                    if total:
                        near(profile["proportions"][k], v / total)
                near(profile["residual_s"], total - math.fsum(sums.values()))
                counts["profiles"] += 1
    assert set(calculated["comparisons"]) == expected_comparisons
    assert all(c["passed"] and c["exact_required"] for c in calculated["comparisons"].values())
    for row in calculated["rows"]:
        key = row["series"], row["particles"]
        gpu = primary.get(("cuda-grid", row["particles"]))
        if row["primary"] and gpu:
            near(row["speedup_against_cuda"], primary[key] / gpu)
        else:
            assert row["speedup_against_cuda"] is None
    return {"passed": True, "method": "independent full components, binary32 bits, raw clocks, hashlib, math.fsum and statistics; no collector imports",
            "checker_sha256": digest(Path(__file__)), "checks": counts}


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1]).resolve()), indent=2, allow_nan=False))
