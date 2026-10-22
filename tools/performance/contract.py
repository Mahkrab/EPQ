"""Own the diagnostic requests and admission rules, not simulator behaviour.

The allocation and operation counts describe the inspected CUDA implementation.
They are labelled models; only retained process results establish measured costs.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

VERSION = "performance-diagnosis-v1"
SOURCE_COMMIT = "c17d8c586eba7455582ad9597cb23d7addc3c6d9"
SIDES = (20, 32, 48, 64, 80)
BASELINE_SIDES = (4, 6, 8, 10, 12, 16, 20)
SERIES = ("serial-grid", "threaded-grid", "cuda")
CHECKPOINTS = (0, 1, 120, 240, 480)
GIB = 1024 ** 3


def allocation(particles: int, planes: int = 6) -> dict:
    """Calculate the exact requested slot bytes, excluding driver/context storage."""
    if type(particles) is not int or not 1 <= particles <= 1_000_000:
        raise ValueError("particles must be an integer in 1..=1000000")
    if type(planes) is not int or not 0 <= planes <= 32:
        raise ValueError("planes must be an integer in 0..=32")
    words = (particles + 31) // 32
    padded = 1 << (particles - 1).bit_length()
    membership = 4 * particles * words
    return {"kind": "source-derived-not-measured", "membership_bytes": membership,
            "other_slot_bytes": 88 * particles + 32 * padded + 16 * planes,
            "total_slot_bytes": membership + 88 * particles + 32 * padded + 16 * planes}


def operations(particles: int, iterations: int = 8) -> dict:
    """Predict normal-path calls; source and trace counts must agree before attribution."""
    if type(iterations) is not int or not 1 <= iterations <= 64:
        raise ValueError("iterations must be an integer in 1..=64")
    storage = allocation(particles)
    bits = (particles - 1).bit_length()
    sort_passes = bits * (bits + 1) // 2
    kernels = 5 + 6 * iterations + sort_passes
    error_downloads = 4 + 6 * iterations
    # Acceleration velocity, predicted position, and final positions/velocities.
    downloads = error_downloads + 4
    uploads = 3
    # prepare reserves thirteen slots; each of its three uploads reserves again.
    reserves = 16
    return {"kind": "source-derived-not-measured", "sort_passes": sort_passes,
            "kernel_launches_per_step": kernels,
            "error_array_downloads_per_step": error_downloads,
            "download_calls_per_step": downloads, "upload_calls_per_step": uploads,
            "reservation_calls_per_step": reserves,
            "upload_bytes_per_step": 24 * particles + 6 * 16,
            "download_bytes_per_step": (4 * error_downloads + 48) * particles,
            "solver_wrapper_completions_per_step": reserves + uploads + downloads + kernels,
            "membership_bytes": storage["membership_bytes"],
            "membership_word_visits_per_full_row_pass": particles * ((particles + 31) // 32)}


def admit(particles: int, gpu_total: int, gpu_free: int, host_available: int) -> dict:
    """Reject unsafe pilots before allocating, without presenting a skip as exhaustion."""
    for value in (gpu_total, gpu_free, host_available):
        if type(value) is not int or value < 0:
            raise ValueError("available memory must be non-negative integer bytes")
    if gpu_free > gpu_total:
        raise ValueError("free GPU memory exceeds total memory")
    estimate = allocation(particles)
    ceiling = min(6 * GIB, gpu_total * 3 // 5, max(0, gpu_free - 2 * GIB))
    reasons = []
    if estimate["total_slot_bytes"] > ceiling:
        reasons.append("source-derived slot allocation exceeds declared GPU ceiling")
    if host_available < 4 * GIB:
        reasons.append("guest memory available is below 4 GiB")
    return {"admitted": not reasons, "reasons": reasons, "gpu_ceiling_bytes": ceiling,
            "gpu_total_bytes": gpu_total, "gpu_free_bytes": gpu_free,
            "host_available_bytes": host_available, "allocation_model": estimate}


def capacity_scene(side: int) -> str:
    """Write decimal bounds directly, avoiding host floating-point endpoint drift."""
    if type(side) is not int or side not in SIDES:
        raise ValueError("unsupported capacity lattice side")
    length = Decimal(side) * Decimal("0.05")
    upper = [length + Decimal(margin) for margin in ("0.4", "0.6", "0.4")]
    result = f'''schema_version = 1
name = "capacity-block-{side:02}"
description = "Counted {side}-by-{side}-by-{side} diagnostic fluid block"
randomness = "none"
allow_coincident_particles = false

[configuration]
source = "file"
path = "../config/defaults-v4.toml"

[particles]
construction = "lattice"
first_identity = 0
origin_m = [0.2, 0.4, 0.2]
counts = [{side}, {side}, {side}]
spacing_m = 0.05
endpoint_rule = "counted_half_open"
order = "x_then_y_then_z"
initial_velocity_m_s = [0.0, 0.0, 0.0]
'''
    for axis, maximum in enumerate(upper):
        for sign, offset in ((1, "0.0"), (-1, f"-{maximum}")):
            normal = [0.0, 0.0, 0.0]
            normal[axis] = float(sign)
            result += f"\n[[planes]]\nnormal = {normal}\noffset_m = {offset}\n"
    return result


def arguments(scene: Path | str, series: str, *, steps: int = 480,
              observation: bool = True, kind: str = "sample") -> list[str]:
    """Use explicit resources and pacing; empty checkpoints intentionally skip audits."""
    if series not in SERIES or kind not in ("warmup", "sample", "profile", "trace", "pilot"):
        raise ValueError("unknown diagnostic series or attempt kind")
    if type(steps) is not int or steps < 0:
        raise ValueError("steps must be a non-negative integer")
    if observation and steps != 480:
        raise ValueError("observation-rich requests retain 480 steps")
    args = ["run", str(scene), "--backend", series, "--unpaced", "--refine-timestep", "4",
            "--steps", str(steps), "--format", "json", "--quiet"]
    if series == "threaded-grid":
        args += ["--threads", "12"]
    elif series == "cuda":
        args += ["--device", "0", "--block-size", "128"]
    if observation:
        args += ["--checkpoints", ",".join(map(str, CHECKPOINTS))]
    if kind in ("sample", "profile", "pilot"):
        args.append("--measure")
    if kind == "profile":
        args.append("--stage-profile")
    return args
