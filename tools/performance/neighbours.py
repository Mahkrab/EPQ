"""Count geometric neighbours in retained states without instrumenting timings.

The first prediction is reconstructed with explicit binary32 rounding. These are
independent derived counts, not a device-buffer readback or memory-traffic counter.
"""

from __future__ import annotations

from collections import defaultdict
import math
import statistics
import struct


def binary32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def counts(points: list[tuple[float, float, float]], radius: float) -> dict:
    """Count strict-support pairs, preserving the solver's rounded distance test."""
    if not math.isfinite(radius) or radius <= 0 or any(not math.isfinite(v) for p in points for v in p):
        raise ValueError("finite points and a positive finite radius are required")
    # JSON uses shortest round-trip f32 decimals, not their expanded f64 values.
    # Restore those binary32 inputs before differences or support comparisons.
    radius = binary32(radius)
    points = [tuple(binary32(v) for v in point) for point in points]
    cells = defaultdict(list)
    for index, point in enumerate(points):
        key = tuple(math.floor(value / radius) for value in point)
        cells[key].append(index)
    rows = []
    # Only reject clearly distant pairs before the exact rounded calculation.
    guard = radius * radius * (1 + 32 * 2 ** -23)
    for index, point in enumerate(points):
        origin = tuple(math.floor(value / radius) for value in point)
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for other in cells.get((origin[0] + dx, origin[1] + dy, origin[2] + dz), ()):
                        if index == other:
                            continue
                        target = points[other]
                        if sum((a - b) ** 2 for a, b in zip(point, target)) > guard:
                            continue
                        delta = [binary32(a - b) for a, b in zip(point, target)]
                        squared = [binary32(d * d) for d in delta]
                        length = binary32(math.sqrt(binary32(binary32(squared[0] + squared[1]) + squared[2])))
                        count += length < radius
        rows.append(count)
    ordered = sorted(rows)
    return {"kind": "independently-derived-geometric-counts-not-device-readback", "particles": len(points),
            "directed_neighbours": sum(rows), "minimum": min(rows) if rows else None,
            "maximum": max(rows) if rows else None, "mean": statistics.mean(rows) if rows else None,
            "median": statistics.median(rows) if rows else None,
            "p95": ordered[max(0, math.ceil(0.95 * len(rows)) - 1)] if rows else None}


def inspect(document: dict, *, first_prediction: bool) -> dict:
    """Inspect the actual request's first prediction or retained accepted final state."""
    configuration = document["input"]["configuration"]
    radius = configuration["derived"]["support_radius_m"]
    particles = document["input"]["particles"] if first_prediction else document["final_snapshot"]["particles"]
    timestep = binary32(configuration["numerical"]["fixed_timestep_s"])
    acceleration = configuration["numerical"]["external_acceleration_m_s2"]
    points = []
    for particle in particles:
        point = []
        for axis in ("x", "y", "z"):
            position = binary32(particle["position_m"][axis])
            if first_prediction:
                velocity = binary32(binary32(particle["velocity_m_s"][axis])
                                    + binary32(binary32(acceleration[axis]) * timestep))
                position = binary32(position + binary32(velocity * timestep))
            point.append(position)
        points.append(tuple(point))
    result = counts(points, radius)
    result["state"] = "reconstructed first prediction" if first_prediction else "accepted final snapshot; not the previous prediction's membership"
    return result
