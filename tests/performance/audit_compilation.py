"""Reconstruct block-size and export partitions without production reporters.

Raw outputs and manifests own the observations. Resource labels may differ;
physical inputs, diagnostics and common image/observation hashes must not.
"""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct

from tests.performance.audit_gradient_reassessment import read

PARTS = {"setup", "solver_steps", "snapshot_capture", "comparison", "frame_particle_copy",
         "graphics_readback", "png_encoding", "frame_publication", "frame_hashing", "progress", "other"}


def number(value, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError("invalid duration")
    return value


def equal(actual, expected):
    if not math.isclose(number(actual), number(expected), rel_tol=1e-10, abs_tol=1e-9):
        raise ValueError("false reported timing")


def request(value, block, particles, effects=False):
    if value["execution"] != {"mode": "cuda", "device": 0, "threads": block}:
        raise ValueError("wrong CUDA resources")
    model = value["input"]["configuration"]["numerical"]
    if (len(value["input"]["particles"]) != particles or model["solver_iterations"] != 8
            or struct.pack('f', model["fixed_timestep_s"]) != struct.pack('f', 0.008333334/4)):
        raise ValueError("wrong numerical work")
    if (model["xsph_viscosity_enabled"] is not effects
            or model["vorticity_confinement_enabled"] is not effects):
        raise ValueError("wrong fluid-effect workload")
    if effects and (struct.pack('f', model["xsph_viscosity_coefficient"]) != struct.pack('f', .01)
            or struct.pack('f', model["vorticity_confinement_strength_m_s"]) != struct.pack('f', .1)):
        raise ValueError("wrong fluid-effect coefficients")


def retained_manifest(directory):
    receipt = json.loads((directory / "bundle.json").read_bytes())
    packed = (directory / "manifest.json.gz").read_bytes()
    raw = gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest() != receipt["manifest_gzip_sha256"] or hashlib.sha256(raw).hexdigest() != receipt["manifest_sha256"]:
        raise ValueError("changed manifest")
    value = json.loads(raw)
    if receipt["frames"] != [{"file": f["file"], "sha256": f["png_sha256"][7:]} for f in value["frames"]]:
        raise ValueError("frame publication receipt differs")
    _, validated = read(directory / "validation")
    if validated.get("valid") is not True:
        raise ValueError("bundle was not validated")
    return value


def audit(root: Path, summary=None):
    if summary is None:
        summary = json.loads((root / "summary.json").read_bytes())
    ids = json.loads((root / "identities.json").read_bytes())
    if ids["control"]["fresh_ptx_sha256"] != ids["candidate"]["fresh_ptx_sha256"] or summary["assessment_required"] is not True:
        raise ValueError("changed CUDA code or automatic decision")
    checks = {"headless": {}, "compile": {}}
    for label, count in (("8000", 8000), ("110592", 110592), ("110592-effects", 110592)):
        reference = None
        checks["headless"][label] = {}
        for block in (32, 64, 128, 256):
            totals = []
            for index in range(4):
                directory = root / f"headless/{label}/{block}" / (f"sample-{index}" if index else "warmup")
                process, value = read(directory)
                request(value, block, count, effects=label.endswith("-effects"))
                if (value["completed_steps"] != "480" or value["request"]["steps"] != "480" or value["failures"]
                        or value["status"] not in ("completed", "completed_with_warnings")
                        or value["metadata"]["build_revision"] != ids["candidate"]["revision"] or value["metadata"]["debug_assertions"]
                        or len(value["final_snapshot"]["particles"]) != count
                        or [r["completed_steps"] for r in value["steps"]] != list(map(str, range(1, 481)))
                        or value["request"]["checkpoints"] != (["0", "1", "120", "240", "480"] if count == 8000 else [])):
                    raise ValueError("incomplete headless request")
                physical = json.dumps({k: value[k] for k in ("input", "steps", "checkpoints", "final_snapshot", "status", "failures")}, sort_keys=True, allow_nan=False)
                if reference is None:
                    reference = physical
                if physical != reference:
                    raise ValueError("physical results differ between blocks")
                if not index:
                    if value.get("measurements") is not None:
                        raise ValueError("warmup unexpectedly measured")
                    continue
                timing = value["measurements"]
                if timing["schema_version"] != 1 or timing["mode"] != "total" or len(timing["steps"]) != 480 or timing["failed_attempt_s"] is not None or any(s["stages"] is not None for s in timing["steps"]):
                    raise ValueError("incorrect solver timing scope")
                seconds = sum(number(s["total_s"], True) for s in timing["steps"])
                totals.append(seconds)
                claimed = summary["headless"][label][str(block)]["samples"][index-1]
                equal(claimed["solver_s"], seconds)
                equal(claimed["command_wall_s"], number(process["wall_s"], True))
            median = statistics.median(totals)
            equal(summary["headless"][label][str(block)]["median_solver_s"], median)
            checks["headless"][label][str(block)] = median
    physical, frames = None, None
    for variant, block, stride in (("candidate", 128, 1), ("candidate", 256, 1), ("candidate", 128, 4), ("candidate", 256, 4), ("control", 128, 1)):
        label = f"{variant}-{block}-stride-{stride}"
        totals, component_samples = [], []
        for index in range(4):
            directory = root / f"compile/{label}" / (f"sample-{index}" if index else "warmup")
            process, status = read(directory)
            value = retained_manifest(directory)
            request(value, block, 110592)
            expected = list(map(str, range(0, 481, stride)))
            if (status.get("complete") is not True or value["schema_version"] != 1 or value["complete"] is not True
                    or value["accepted_steps"] != "480" or value["source_mode"] != "direct"
                    or value["run_metadata"]["build_revision"] != ids[variant]["revision"] or value["build"]["debug_assertions"]
                    or value["graphics"]["device_type"].lower() == "cpu" or value["graphics"]["software_requested"]
                    or (value["render"]["width"], value["render"]["height"]) != (1280, 720)
                    or value["frame_count"] != len(expected) or value["step_stride"] != str(stride)
                    or [f["step"] for f in value["frames"]] != expected
                    or [s["completed_steps"] for s in value["accepted_diagnostics"]] != list(map(str, range(1, 481)))):
                raise ValueError("incorrect compile work")
            render = dict(value["render"])
            render.pop("step_stride")
            identity = json.dumps([value["input"], value["accepted_diagnostics"], render, value["graphics"], value["status"]], sort_keys=True, allow_nan=False)
            observed = {f["step"]: tuple(f[k] for k in ("simulated_seconds", "png_sha256", "rgba_sha256", "snapshot_sha256")) for f in value["frames"]}
            if physical is None:
                physical, frames = identity, observed
            if identity != physical or any(frames[k] != v for k, v in observed.items()):
                raise ValueError("compiled physical results or common frames differ")
            wall = number(process["wall_s"], True)
            if variant == "candidate":
                timing = value["timing_profile"]
                if type(timing["schema_version"]) is not int or timing["schema_version"] != 1 or timing["boundary"] != "export_entry_to_before_manifest" or timing["components_s"].keys() != PARTS:
                    raise ValueError("wrong export profile schema or scope")
                components = {k: number(v) for k, v in timing["components_s"].items()}
                total = number(timing["total_s"], True)
                equal(sum(components.values()), total)
                if total > wall:
                    raise ValueError("profile exceeds command wall time")
                for old, new in (("solver_steps", "solver_steps"), ("graphics_readback", "graphics_readback"), ("encoding", "png_encoding")):
                    equal(value["timing_seconds"][old], components[new])
                if index:
                    claimed = summary["compile"][label]["samples"][index-1]
                    equal(claimed["pre_manifest_s"], total)
                    equal(claimed["outside_export_boundary_s"], wall-total)
                    for key, v in components.items():
                        equal(claimed["components_s"][key], v)
                    component_samples.append(components)
            if index:
                totals.append(wall)
                equal(summary["compile"][label]["samples"][index-1]["command_wall_s"], wall)
        median = statistics.median(totals)
        equal(summary["compile"][label]["median_command_wall_s"], median)
        for key in PARTS if variant == "candidate" else ():
            equal(summary["compile"][label]["median_components_s"][key], statistics.median(s[key] for s in component_samples))
        checks["compile"][label] = median
    return {"exact_physical_and_frame_agreement": True, "independent_raw_timing_reconstruction": True, **checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(audit(parser.parse_args().directory.resolve()), indent=2, allow_nan=False))
