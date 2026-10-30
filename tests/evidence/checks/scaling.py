"""Independently audit retained worker measurements without importing the collector.

This executable check derives statistics and physical comparisons directly from raw
JSON. Run from any directory with the campaign path as its sole argument.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
STAGES = ("validation_and_acceleration_s", "prediction_s", "neighbour_search_s",
          "jacobi_s", "projection_s", "acceptance_s")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical(result):
    value = copy.deepcopy(result)
    for key in ("measurements", "backend", "execution"):
        value.pop(key, None)
    for key in ("backend", "run_id", "build_revision", "target_arch", "target_os", "debug_assertions"):
        value["metadata"].pop(key, None)
    return value


def bits(value):
    if isinstance(value, float):
        assert math.isfinite(value)
        return struct.pack("!f", value)
    if isinstance(value, list):
        return [bits(item) for item in value]
    if isinstance(value, dict):
        return {key: bits(item) for key, item in value.items()}
    return value


def near(actual, expected):
    assert math.isfinite(actual) and math.isfinite(expected)
    assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (actual, expected)


def clean(a):
    r = a["result"]
    return bool(r and a["exit_code"] == 0 and not a["timed_out"] and not a["interrupted"]
                and r["status"] == "completed" and r["completed_steps"] == "480"
                and len(r["steps"]) == 480 and not r["failures"]
                and not any(s["warning"] for s in r["steps"])
                and [c["snapshot"]["completed_steps"] for c in r["checkpoints"]] == ["0", "1", "120", "240", "480"]
                and a.get("numerical_agreement", True))


def audit(directory):
    campaign = read(directory / "campaign.json")
    calculated = read(directory / "scaling.json")
    sizes = [64, 216, 512, 1000, 1728, 4096, 8000]
    assert digest(directory / "protocol.md") == campaign["protocol_sha256"]
    assert campaign["default_workers"] in campaign["workers"]
    results, primary, references = {}, {}, {}
    clock_observations = []
    counts = dict(attempts=0, exact_complete_attempts=0, timeouts=0, incomplete_or_unclean=0,
                  correctness_results=0, source_hashes=0, collector_hashes=0, profiles=0)
    first = None
    for name in campaign["collection_order"]:
        path = directory / name
        dataset = read(path / "dataset.json")
        assert digest(path / "dataset.json") == calculated["datasets_sha256"][name]
        assert dataset["source_unchanged"] and dataset["binary_unchanged"] and not dataset["interrupted"]
        if first is None:
            first = dataset
            for file, expected in dataset["source"]["files_sha256"].items():
                assert digest(ROOT / "Maelstrom" / file) == expected, file
                counts["source_hashes"] += 1
            for file, expected in dataset["collector_files_sha256"].items():
                assert digest(ROOT / file) == expected, file
                counts["collector_hashes"] += 1
        else:
            for field in ("source", "binary_sha256", "policy", "manifest", "manifest_sha256", "build_revision", "collector_files_sha256"):
                assert dataset[field] == first[field], field
            for field in ("cpu_model", "architecture", "kernel", "cpu_topology", "cpu_affinity", "rustc", "cargo", "rustflags"):
                assert dataset["environment"][field] == first["environment"][field], field
        assert digest(ROOT / "Maelstrom/reference/manifest.json") == dataset["manifest_sha256"]
        manifest = dataset["manifest"]
        for case in manifest["cases"]:
            scene_path = ROOT / "Maelstrom" / case["scene"]
            if case["scene"].startswith("scenes/") and not scene_path.exists():
                scene_path = ROOT / "Maelstrom/reference" / case["scene"]
            assert digest(scene_path) == case["sha256"]
            if case["golden"]:
                assert digest(ROOT / "Maelstrom" / case["golden"]) == case["golden_sha256"]
        assert digest(ROOT / "Maelstrom" / manifest["configuration"]) == manifest["configuration_sha256"]
        assert digest(path / "correctness.json") == dataset["correctness"]["result_sha256"]
        correct = read(path / "correctness.json")
        golden = read(ROOT / "Maelstrom" / manifest["cases"][1]["golden"])
        assert bits(physical(correct)) == bits(physical(golden))
        counts["correctness_results"] += 1
        attempts = []
        seen = set()
        previous = None
        for entry in dataset["raw"]:
            raw_path = path / entry["file"]
            assert raw_path.resolve().is_relative_to(path.resolve())
            assert digest(raw_path) == entry["sha256"]
            a = read(raw_path)
            if previous is not None:
                delta = (dt.datetime.fromisoformat(a["started_utc"])
                         - dt.datetime.fromisoformat(previous["finished_utc"])).total_seconds()
                if delta < 0:
                    clock_observations.append({"series": name, "previous_file": previous["file"],
                                               "next_file": entry["file"], "backward_utc_s": -delta})
            previous = {"file": entry["file"], "finished_utc": a["finished_utc"]}
            key = a["particles"], a["kind"], a["index"]
            assert key not in seen
            seen.add(key)
            counts["attempts"] += 1
            counts["timeouts"] += a["timed_out"]
            counts["incomplete_or_unclean"] += not clean(a)
            r = a["result"]
            if r:
                workers = None if name == "serial-grid" else int(name.split("-")[1])
                assert r.get("execution", {"mode": "serial"}) == ({"mode": "threaded", "workers": workers} if workers else {"mode": "serial"})
                assert r["metadata"]["build_revision"] == dataset["build_revision"]
                assert r["metadata"]["debug_assertions"] is False
                assert r["request"] == {"steps": "480", "checkpoints": ["0", "1", "120", "240", "480"]}
                assert len(r["steps"]) == int(r["completed_steps"])
            attempts.append(a)
        for size, stored in zip(sizes, dataset["summaries"], strict=True):
            values = [a for a in attempts if a["particles"] == size]
            warmups = [a for a in values if a["kind"] == "warmup"]
            samples = [a for a in values if a["kind"] == "sample"]
            if name == "serial-grid" and len(warmups) == 1 and clean(warmups[0]):
                references[size] = bits(physical(warmups[0]["result"]))
            exact = 0
            for a in values:
                if clean(a) and size in references:
                    assert bits(physical(a["result"])) == references[size], (name, size, a["kind"], a["index"])
                    exact += 1
            counts["exact_complete_attempts"] += exact
            row = next(r for r in calculated["rows"] if r["particles"] == size and r["series"] == name)
            assert row["exact_complete_attempts"] == exact
            complete = len(warmups) == 1 and clean(warmups[0]) and len(samples) == 3 and all(clean(a) for a in samples)
            p = stored["primary"]
            assert (p is not None) == complete
            if complete:
                totals = [math.fsum(s["total_s"] for s in a["result"]["measurements"]["steps"]) for a in samples]
                median = statistics.median(totals)
                for field, value in {"median_s": median, "mean_s": statistics.mean(totals), "minimum_s": min(totals),
                                     "maximum_s": max(totals), "sample_standard_deviation_s": statistics.stdev(totals),
                                     "median_step_s": median / 480, "particle_updates_per_s": size * 480 / median}.items():
                    near(p[field], value)
                for actual, expected in zip(p["sample_totals_s"], totals, strict=True):
                    near(actual, expected)
                primary[name, size] = median
            assert row["primary"] == (p if size in references else None)
            if complete and size in references:
                near(row["invocation_median_s"], statistics.median(a["wall_s"] for a in samples))
            else:
                assert row["invocation_median_s"] is None
            expected_speedup = primary["serial-grid", size] / primary[name, size] if complete and ("serial-grid", size) in primary else None
            if expected_speedup is None:
                assert row["serial_grid_speedup"] is None
            else:
                near(row["serial_grid_speedup"], expected_speedup)
            if name.startswith("workers-") and complete and ("workers-1", size) in primary and size in references:
                scaling = primary["workers-1", size] / primary[name, size]
                near(row["one_worker_scaling"], scaling)
                near(row["requested_worker_efficiency"], scaling / int(name.split("-")[1]))
            else:
                assert row["one_worker_scaling"] is None
                assert row["requested_worker_efficiency"] is None
            for a in values:
                if a["kind"] != "profile" or a["result"] is None:
                    continue
                steps = a["result"]["measurements"]["steps"]
                profile = stored["profile"]
                total = math.fsum(s["total_s"] for s in steps)
                near(profile["total_s"], total)
                sums = {k: math.fsum(s["stages"][k] for s in steps) for k in STAGES}
                for key, value in sums.items():
                    near(profile["stages_s"][key], value)
                    if total:
                        near(profile["proportions"][key], value / total)
                near(profile["residual_s"], total - math.fsum(sums.values()))
                assert profile["complete"] == clean(a)
                counts["profiles"] += 1
        results[name] = digest(path / "dataset.json")
    return {"passed": True, "method": "independent raw JSON, binary32 bits, hashlib, math.fsum and statistics; no collector imports",
            "checker_sha256": digest(Path(__file__)), "datasets_sha256": results, "checks": counts,
            "clock_observations": clock_observations}


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1]).resolve()), indent=2, allow_nan=False))
