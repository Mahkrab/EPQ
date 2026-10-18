"""Validate retained solver observations and derive the baseline's reported metrics.

Timing records never establish correctness by themselves. Successful samples must
also complete the frozen request, with the declared checkpoints and no warnings.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import statistics
import struct
from pathlib import Path

POLICY = {
    "id": "serial-baseline-v1",
    "steps": 480,
    "checkpoints": [0, 1, 120, 240, 480],
    "particles": [64, 216, 512, 1000, 1728, 4096, 8000],
    "warmups": 1,
    "samples": 3,
    "profiles": 1,
    "timeout_s": 120,
    "cancellation_grace_s": 30,
    "outliers": "retain_all",
    "memory_measurement": None,
}
STAGES = (
    "validation_and_acceleration_s", "prediction_s", "neighbour_search_s",
    "jacobi_s", "projection_s", "acceptance_s",
)
BACKENDS = {
    "brute-force": "serial-brute-force-pbf-binary32-8-jacobi-v2",
    "uniform-grid": "serial-uniform-grid-pbf-binary32-8-jacobi-v2",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: expected a JSON object")
    return value


def numerical_document(document: dict) -> dict:
    """Remove only optional timings and recorded build context for exact replay."""
    value = copy.deepcopy(document)
    value.pop("measurements", None)
    for key in ("build_revision", "target_os", "target_arch", "debug_assertions"):
        value["metadata"].pop(key, None)
    return value


def physical_document(document: dict, *, ignore_execution: bool = False) -> dict:
    """Compare either search while retaining physical identity and every observation."""
    value = numerical_document(document)
    if ignore_execution:
        value.pop("execution", None)
    value.pop("backend")
    for key in ("backend", "run_id"):
        value["metadata"].pop(key)
    return value


def require_exact(actual: object, expected: object, location: str = "result") -> None:
    """Compare complete JSON structures, preserving every binary32 bit and sign."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError(f"{location}: object fields differ")
        for key in expected:
            require_exact(actual[key], expected[key], f"{location}.{key}")
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f"{location}: array lengths differ")
        for index, (a, b) in enumerate(zip(actual, expected, strict=True)):
            require_exact(a, b, f"{location}[{index}]")
    elif isinstance(actual, (int, float)) and not isinstance(actual, bool) and isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if isinstance(actual, float) or isinstance(expected, float):
            if not math.isfinite(actual) or not math.isfinite(expected) or struct.pack("!f", actual) != struct.pack("!f", expected):
                raise ValueError(f"{location}: binary32 mismatch")
        elif actual != expected:
            raise ValueError(f"{location}: integer mismatch")
    elif type(actual) is not type(expected) or actual != expected:
        raise ValueError(f"{location}: value mismatch")


def _seconds(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("elapsed seconds must be finite and non-negative")
    return float(value)


def timing_totals(attempt: dict) -> dict | None:
    """Validate raw timings even when an invocation failed or was cancelled."""
    result = attempt.get("result")
    if result is None:
        return None
    count = int(result["completed_steps"])
    diagnostics = result["steps"]
    if count < 0 or len(diagnostics) != count:
        raise ValueError("accepted step count and diagnostics disagree")
    if [d["completed_steps"] for d in diagnostics] != [str(i) for i in range(1, count + 1)]:
        raise ValueError("accepted diagnostic order is invalid")
    measurements = result.get("measurements")
    if attempt["kind"] == "warmup":
        if measurements is not None:
            raise ValueError("warm-up unexpectedly contains measurements")
        return None
    mode = "stages" if attempt["kind"] == "profile" else "total"
    if measurements is None or measurements["schema_version"] != 1 or measurements["mode"] != mode:
        raise ValueError("measurement version or mode does not match sample")
    if len(measurements["steps"]) != count:
        raise ValueError("timings and accepted steps disagree")
    failed = measurements["failed_attempt_s"]
    if failed is not None:
        _seconds(failed)
    total = 0.0
    stages = dict.fromkeys(STAGES, 0.0)
    for step in measurements["steps"]:
        total += _seconds(step["total_s"])
        if mode == "total":
            if step["stages"] is not None:
                raise ValueError("primary sample includes profiling overhead")
        else:
            if not isinstance(step["stages"], dict) or set(step["stages"]) != set(STAGES):
                raise ValueError("profile stage fields differ")
            values = {key: _seconds(step["stages"][key]) for key in STAGES}
            if sum(values.values()) > step["total_s"] + 1e-12:
                raise ValueError("stage intervals exceed total step time")
            for key, value in values.items():
                stages[key] += value
    return {"total_s": total, "stages_s": stages if mode == "stages" else None}


def clean(attempt: dict) -> bool:
    result = attempt.get("result")
    return bool(
        result is not None and attempt["exit_code"] == 0 and not attempt["timed_out"]
        and not attempt.get("interrupted", False)
        and result["status"] == "completed" and result["failures"] == []
        and attempt.get("numerical_agreement", True)
        and result["completed_steps"] == str(POLICY["steps"])
        and result["request"] == {"steps": str(POLICY["steps"]), "checkpoints": [str(n) for n in POLICY["checkpoints"]]}
        and len(result["steps"]) == POLICY["steps"]
        and not any(step["warning"] for step in result["steps"])
        and [c["snapshot"]["completed_steps"] for c in result["checkpoints"]] == [str(n) for n in POLICY["checkpoints"]]
        and all(c["density"] is not None for c in result["checkpoints"])
    )


def compact_result(result: dict) -> dict:
    """Keep diagnostics and raw timings, replacing duplicate particle arrays by hashes."""
    result = copy.deepcopy(result)
    for holder, key in [(result, "input"), (result, "final_snapshot")]:
        value = holder.pop(key)
        holder[f"{key}_sha256"] = sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
    for checkpoint in result["checkpoints"]:
        snapshot = checkpoint["snapshot"]
        checkpoint["snapshot"] = {
            "completed_steps": snapshot["completed_steps"],
            "sha256": sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()),
        }
    return result


def summarise(attempts: list[dict]) -> list[dict]:
    rows = []
    for particles in POLICY["particles"]:
        cases = [a for a in attempts if a["particles"] == particles]
        for attempt in cases:
            timing_totals(attempt)
        warmups = [a for a in cases if a["kind"] == "warmup"]
        samples = [a for a in cases if a["kind"] == "sample"]
        profiles = [a for a in cases if a["kind"] == "profile"]
        row = {"particles": particles, "primary": None, "profile": None,
               "attempts": [{"kind": a["kind"], "index": a["index"], "clean": clean(a),
                             "timed_out": a["timed_out"], "exit_code": a["exit_code"],
                             "completed_steps": a.get("result", {}).get("completed_steps") if a.get("result") else None} for a in cases]}
        if len(warmups) == 1 and clean(warmups[0]) and len(samples) == POLICY["samples"] and all(clean(a) for a in samples):
            totals = [timing_totals(a)["total_s"] for a in samples]
            median = statistics.median(totals)
            if median <= 0:
                raise ValueError("complete sample has no positive elapsed time")
            row["primary"] = {
                "sample_totals_s": totals, "median_s": median, "minimum_s": min(totals),
                "maximum_s": max(totals), "mean_s": statistics.mean(totals),
                "sample_standard_deviation_s": statistics.stdev(totals),
                "median_step_s": median / POLICY["steps"],
                "particle_updates_per_s": particles * POLICY["steps"] / median,
            }
        if len(profiles) == 1 and (totals := timing_totals(profiles[0])) is not None:
            total = totals["total_s"]
            stages = totals["stages_s"]
            row["profile"] = {
                "complete": clean(profiles[0]), "completed_steps": profiles[0]["result"]["completed_steps"],
                "total_s": total, "stages_s": stages,
                "proportions": {key: value / total if total else None for key, value in stages.items()},
                "residual_s": total - sum(stages.values()),
            }
        rows.append(row)
    return rows


def correctness_observations(result: dict) -> dict:
    """Describe finite-state, contact, separation and energy at recorded checkpoints.

    These observations complement the every-step independent health tests; they
    do not turn a sparse checkpoint set into a whole-trajectory qualification.
    """
    checkpoints = []
    for checkpoint in result["checkpoints"]:
        particles = checkpoint["snapshot"]["particles"]
        positions = [tuple(p["position_m"][axis] for axis in ("x", "y", "z")) for p in particles]
        velocities = [tuple(p["velocity_m_s"][axis] for axis in ("x", "y", "z")) for p in particles]
        finite = all(math.isfinite(x) for xyz in [*positions, *velocities] for x in xyz)
        if not finite:
            raise ValueError("non-finite correctness checkpoint")
        separation = min((math.dist(p, q) for i, p in enumerate(positions) for q in positions[i + 1:]), default=None)
        energy = sum(0.5 * sum(v * v for v in velocity) + 9.81 * position[1]
                     for position, velocity in zip(positions, velocities, strict=True)) / len(particles) if particles else None
        checkpoints.append({
            "completed_steps": checkpoint["snapshot"]["completed_steps"],
            "density": checkpoint["density"], "finite_state": finite,
            "minimum_separation_m": separation,
            "floor_contact": any(position[1] == 0 for position in positions),
            "mean_specific_mechanical_energy_j_kg": energy,
        })
    return {"status": result["status"], "completed_steps": result["completed_steps"],
            "warning_steps": sum(d["warning"] for d in result["steps"]),
            "maximum_post_acceleration_speed_m_s": max((d["maximum_speed_m_s"] for d in result["steps"]), default=None),
            "checkpoints": checkpoints}


def markdown(dataset: dict, rows: list[dict]) -> str:
    env = dataset["environment"]
    backend = dataset.get("backend", "brute-force")
    execution = dataset.get("execution", {"mode": "serial"})
    title = (f"Threaded {backend}, {execution['workers']} workers"
             if execution["mode"] == "threaded" else f"Serial {backend}")
    text = [f"# {title} performance baseline", "",
            f"Policy: `{POLICY['id']}`. Collection: {dataset['started_utc']} to {dataset['finished_utc']}.", "",
            f"Environment: {env['cpu_model']}; {env['os_release']}; kernel `{env['kernel']}`; {env['architecture']}.",
            "Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.",
            "Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.", "",
            "| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        p = row["primary"]
        if p:
            text.append(f"| {row['particles']:,} | {p['median_s']:.6f} | {p['minimum_s']:.6f}–{p['maximum_s']:.6f} | {p['sample_standard_deviation_s']:.6f} | {p['median_step_s'] * 1000:.6f} | {p['particle_updates_per_s']:,.0f} |")
        else:
            text.append(f"| {row['particles']:,} | unavailable | incomplete clean sample set | — | — | — |")
    if "observations" in dataset["correctness"]:
        observation = dataset["correctness"]["observations"]
        text += ["", f"The 64-particle correctness run matched the golden exactly: {observation['completed_steps']} steps; {observation['warning_steps']} CFL warnings.", "",
                 "Checkpoint energy is mean specific kinetic plus gravitational potential energy, using 9.81 m/s² and floor height zero.",
                 "These sparse observations complement the separate every-step health tests.", "",
                 "| Step | Mean absolute relative density error | Maximum error | Minimum separation (m) | Mean energy (J/kg) | Floor contact |",
                 "| ---: | ---: | ---: | ---: | ---: | --- |"]
        for checkpoint in observation["checkpoints"]:
            density = checkpoint["density"]
            text.append(f"| {checkpoint['completed_steps']} | {density['mean_error']:.8f} | {density['maximum_error']:.8f} | {checkpoint['minimum_separation_m']:.8f} | {checkpoint['mean_specific_mechanical_energy_j_kg']:.8f} | {checkpoint['floor_contact']} |")
    text += ["", "Instrumented profiles include additional clocks. Percentages divide stage sums by the profiled total.", "",
             "| Particles | Profile steps | Total (s) | Validation/acceleration | Prediction | Search | Jacobi | Projection | Acceptance | Residual (s) |",
             "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        p = row["profile"]
        if p:
            percentages = " | ".join(f"{100 * p['proportions'][s]:.2f}%" if p['proportions'][s] is not None else "unavailable" for s in STAGES)
            label = "" if p["complete"] else " (partial)"
            text.append(f"| {row['particles']:,} | {p['completed_steps']}{label} | {p['total_s']:.6f} | {percentages} | {p['residual_s']:.9f} |")
    valid = [r["particles"] for r in rows if r["primary"]]
    text += ["", f"Largest fully sampled member under the 120-second invocation budget: **{max(valid):,} particles**." if valid else "No member completed the clean sampling policy.", "",
             "This is an observed budget limit, not a universal maximum. No memory-use measurement was taken.",
             "Three samples describe observed variation; they do not establish statistical significance or cross-machine performance.", "",
             "| Particles | Attempt | Accepted steps | Exit | Timed out | Clean full request |",
             "| ---: | --- | ---: | ---: | --- | --- |"]
    for row in rows:
        for a in row["attempts"]:
            text.append(f"| {row['particles']:,} | {a['kind']} {a['index']} | {a['completed_steps']} | {a['exit_code']} | {a['timed_out']} | {a['clean']} |")
    return "\n".join(text) + "\n"
