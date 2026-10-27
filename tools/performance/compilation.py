"""Read complete command costs without conflating them with solver throughput.

Export profiles partition only the pre-manifest boundary. Raw invocation timing
owns the remaining CLI, finalisation and teardown work.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
import statistics

from .capture import digest, load_attempt

COMPONENTS = frozenset(("setup", "solver_steps", "snapshot_capture", "comparison",
    "frame_particle_copy", "graphics_readback", "png_encoding", "frame_publication",
    "frame_hashing", "progress", "other"))
BLOCKS = (32, 64, 128, 256)
COMPILES = (("candidate", 128, 1), ("candidate", 256, 1),
            ("candidate", 128, 4), ("candidate", 256, 4), ("control", 128, 1))


def duration(value: object, *, positive: bool = False) -> float:
    if type(value) not in (float, int) or not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError("duration must be finite and non-negative")
    return float(value)


def partition(manifest: dict, wall_s: float) -> dict:
    """Reject false scope, missing components, overlaps and changed legacy timers."""
    wall_s = duration(wall_s, positive=True)
    profile = manifest["timing_profile"]
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1 or profile["boundary"] != "export_entry_to_before_manifest":
        raise ValueError("unsupported export timing boundary")
    parts = profile["components_s"]
    if parts.keys() != COMPONENTS:
        raise ValueError("incomplete export timing components")
    parts = {k: duration(v) for k, v in parts.items()}
    total = duration(profile["total_s"], positive=True)
    if not math.isclose(math.fsum(parts.values()), total, rel_tol=1e-10, abs_tol=1e-9) or total > wall_s:
        raise ValueError("export components do not fit enclosing durations")
    for old, new in (("solver_steps", "solver_steps"), ("graphics_readback", "graphics_readback"), ("encoding", "png_encoding")):
        if duration(manifest["timing_seconds"][old]) != parts[new]:
            raise ValueError("legacy export timer changed meaning")
    return {"command_wall_s": wall_s, "pre_manifest_s": total, "components_s": parts,
            "outside_export_boundary_s": wall_s - total}


def physical_run(document: dict, particles: int, block: int, revision: str) -> str:
    """Keep all numerical observations, excluding declared resource metadata only."""
    if (document["completed_steps"] != "480" or document["request"]["steps"] != "480"
            or document["failures"] or document["status"] not in ("completed", "completed_with_warnings")
            or document["execution"] != {"mode": "cuda", "device": 0, "threads": block}
            or document["metadata"]["build_revision"] != revision or document["metadata"]["debug_assertions"]
            or len(document["input"]["particles"]) != particles
            or len(document["final_snapshot"]["particles"]) != particles
            or [s["completed_steps"] for s in document["steps"]] != [str(i) for i in range(1, 481)]):
        raise ValueError("wrong or incomplete headless request")
    value = {k: document[k] for k in ("schema_version", "backend", "input", "request", "steps", "checkpoints", "final_snapshot", "status", "failures")}
    return digest(json.dumps(value, sort_keys=True, allow_nan=False).encode())


def manifest(directory: Path) -> dict:
    """Verify retained manifest and publication receipts before interpreting them."""
    receipt = json.loads((directory / "bundle.json").read_bytes())
    compressed = (directory / "manifest.json.gz").read_bytes()
    raw = gzip.decompress(compressed)
    if digest(compressed) != receipt["manifest_gzip_sha256"] or digest(raw) != receipt["manifest_sha256"]:
        raise ValueError("retained manifest changed")
    result = json.loads(raw)
    if receipt["frames"] != [{"file": f["file"], "sha256": f["png_sha256"].removeprefix("sha256:")} for f in result["frames"]]:
        raise ValueError("published frame receipt differs")
    process, validation = load_attempt(directory / "validation")
    if process["exit_code"] != 0 or validation is None or validation.get("valid") is not True:
        raise ValueError("compiled bundle validation failed")
    return result


def compile_identity(value: dict, block: int, stride: int) -> tuple[str, dict]:
    expected = list(range(0, 481, stride))
    if (value["schema_version"] != 1 or value["complete"] is not True or value["accepted_steps"] != "480"
            or value["source_mode"] != "direct" or value["execution"] != {"mode": "cuda", "device": 0, "threads": block}
            or value["graphics"]["device_type"].lower() == "cpu" or value["graphics"]["software_requested"]
            or value["build"]["debug_assertions"] or len(value["input"]["particles"]) != 110592
            or value["render"]["width"] != 1280 or value["render"]["height"] != 720
            or value["frame_count"] != len(expected) or value["step_stride"] != str(stride)
            or [f["step"] for f in value["frames"]] != list(map(str, expected))
            or [d["completed_steps"] for d in value["accepted_diagnostics"]] != list(map(str, range(1, 481)))):
        raise ValueError("different or incomplete compile workload")
    render = dict(value["render"])
    render.pop("step_stride")
    identity = digest(json.dumps({"input": value["input"], "diagnostics": value["accepted_diagnostics"], "render": render,
        "graphics": value["graphics"], "status": value["status"]}, sort_keys=True, allow_nan=False).encode())
    frames = {f["step"]: {k: f[k] for k in ("simulated_seconds", "png_sha256", "rgba_sha256", "snapshot_sha256")} for f in value["frames"]}
    return identity, frames


def report(root: Path) -> dict:
    ids = json.loads((root / "identities.json").read_bytes())
    workloads = (("8000", 8000), ("110592", 110592), ("110592-effects", 110592))
    output = {"schema_version": 1, "assessment_required": True, "headless": {}, "compile": {}}
    for name, particles in workloads:
        reference = None
        variants = {}
        for block in BLOCKS:
            samples = []
            for i in range(4):
                directory = root / f"headless/{name}/{block}/" / (f"sample-{i}" if i else "warmup")
                process, document = load_attempt(directory)
                if process["exit_code"] != 0 or document is None or process["timed_out"] or process["interrupted"]:
                    raise ValueError("headless invocation failed")
                key = physical_run(document, particles, block, ids["candidate"]["revision"])
                if reference is None:
                    reference = key
                if key != reference:
                    raise ValueError("headless physical work differs between blocks")
                if i:
                    measured = document["measurements"]
                    if measured["mode"] != "total" or len(measured["steps"]) != 480 or measured["failed_attempt_s"] is not None or any(s["stages"] is not None for s in measured["steps"]):
                        raise ValueError("wrong solver measurement boundary")
                    samples.append({"solver_s": math.fsum(duration(s["total_s"], positive=True) for s in measured["steps"]),
                                    "command_wall_s": duration(process["wall_s"], positive=True)})
            variants[str(block)] = {"samples": samples, "median_solver_s": statistics.median(s["solver_s"] for s in samples)}
        output["headless"][name] = variants
    physical, frames = None, None
    for variant, block, stride in COMPILES:
        label = f"{variant}-{block}-stride-{stride}"
        samples = []
        for i in range(4):
            directory = root / f"compile/{label}/" / (f"sample-{i}" if i else "warmup")
            process, result = load_attempt(directory)
            if process["exit_code"] != 0 or result is None or result.get("complete") is not True or process["timed_out"] or process["interrupted"]:
                raise ValueError("compile invocation failed")
            value = manifest(directory)
            if value["run_metadata"]["build_revision"] != ids[variant]["revision"]:
                raise ValueError("different compile executable identity")
            key, observed = compile_identity(value, block, stride)
            if physical is None:
                physical, frames = key, observed
            if key != physical or any(frames[s] != f for s, f in observed.items()):
                raise ValueError("compiled physical records or common frames differ")
            if i:
                sample = partition(value, process["wall_s"]) if variant == "candidate" else {"command_wall_s": duration(process["wall_s"], positive=True)}
                samples.append(sample)
        output["compile"][label] = {"samples": samples, "median_command_wall_s": statistics.median(s["command_wall_s"] for s in samples)}
        if variant == "candidate":
            output["compile"][label]["median_components_s"] = {k: statistics.median(s["components_s"][k] for s in samples) for k in sorted(COMPONENTS)}
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(report(parser.parse_args().directory.resolve()), indent=2, allow_nan=False))
