"""Audit raw architectural observations without importing their collectors.

This verifies retained evidence, not execution on unavailable hardware. Binary
identity checks are explicitly unavailable when auditing a packaged dataset.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_attempt(directory: Path) -> tuple[dict, dict | None]:
    metadata = json.loads((directory / "process.json").read_bytes())
    if "launch_error" in metadata:
        if metadata["exit_code"] is not None:
            raise ValueError("launch failure has a process exit")
        return metadata, None
    compressed = (directory / "stdout.gz").read_bytes()
    raw = gzip.decompress(compressed)
    if (sha(compressed) != metadata["stdout_gzip_sha256"]
            or sha(raw) != metadata["stdout_sha256"]
            or sha((directory / "stderr.txt").read_bytes()) != metadata["stderr_sha256"]):
        raise ValueError("raw process bytes changed")
    if metadata["parse_error"] is not None or not raw:
        return metadata, None
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("process result must be an object")
    return metadata, value


def packed_snapshot(particles: list[dict]) -> bytes:
    return b"".join(struct.pack("<3f", *(p[field][axis] for axis in "xyz"))
                    for field in ("position_m", "velocity_m_s") for p in particles)


def median(values: list[float]) -> float:
    if len(values) != 5 or any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("five positive timing samples are required")
    return sorted(values)[2]


def audit(root: Path) -> dict:
    processes = sorted(root.rglob("process.json"))
    failed, interrupted = [], []
    for path in processes:
        process, _ = read_attempt(path.parent)
        if process["exit_code"] != 0:
            failed.append(path.parent.relative_to(root).as_posix())
        if process["timed_out"] or process["interrupted"]:
            interrupted.append(path.parent.relative_to(root).as_posix())
    comparisons = 0
    for filename, extra in (("summary.json", False), ("extra-summary.json", True)):
        summary = json.loads((root / filename).read_bytes())
        for label, stated in summary.items():
            count = int(label.split("/")[0])
            totals = {side: [] for side in ("control", "candidate")}
            bits = []
            for index in range(6):
                hashes = {}
                for side in totals:
                    path = root / "runs"
                    if extra:
                        path /= "extra"
                    path = path / label / str(index) / side
                    process, result = read_attempt(path)
                    if (process["exit_code"] != 0 or process["timed_out"] or result is None
                            or result["steps"] != 480 or result["particles"] != count):
                        raise ValueError(f"invalid comparison attempt: {label}/{index}/{side}")
                    if (process["command"][2:4] != ["480", "8"]
                            or Path(process["command"][1]).name != f"{count}.bin"):
                        raise ValueError("comparison command changes the declared work")
                    if "step_s" in result and (len(result["step_s"]) != 480
                            or abs(sum(result["step_s"]) - result["solver_s"]) > 1e-12):
                        raise ValueError("completed-step total differs")
                    snapshot = (path / "state-480.bin").read_bytes()
                    if len(snapshot) != count * 24 or any(not math.isfinite(x[0]) for x in struct.iter_unpack("<f", snapshot)):
                        raise ValueError("invalid comparison snapshot")
                    hashes[side] = sha(snapshot)
                    if side == "control" and snapshot != (root / f"runs/admission/{count}/control/state-480.bin").read_bytes():
                        raise ValueError("timed control differs from the admitted trajectory")
                    metrics = json.loads((path / "metrics.json").read_bytes())
                    if hashes[side] != metrics["final_sha256"] or metrics["solver_s"] != result["solver_s"]:
                        raise ValueError("metrics disagree with raw observation")
                    if index:
                        totals[side].append(result["solver_s"])
                if index:
                    bits.append(hashes["control"] == hashes["candidate"])
                    comparisons += 1
            medians = {side: median(values) for side, values in totals.items()}
            pairs = [a / b for a, b in zip(totals["control"], totals["candidate"], strict=True)]
            if (stated["samples_s"] != totals or stated["median_s"] != medians
                    or stated["ranges_s"] != {k: [min(v), max(v)] for k, v in totals.items()}
                    or stated["speedup"] != medians["control"] / medians["candidate"]
                    or stated["paired_speedup"] != pairs or stated["same_final_bits"] != bits):
                raise ValueError("comparison summary is inconsistent")
    checkpoint_checks = 0
    for count in (1000, 8000, 110592):
        source = root / ("production-final" if count == 110592 else "production") / str(count)
        process, result = read_attempt(source)
        if process["exit_code"] != 0 or result is None or result["completed_steps"] != "480":
            raise ValueError("production reference is incomplete")
        for snapshot in [result["final_snapshot"], *(c["snapshot"] for c in result["checkpoints"])]:
            step = snapshot["completed_steps"]
            path = root / f"runs/admission/{count}/control/state-{step}.bin"
            if path.read_bytes() != packed_snapshot(snapshot["particles"]):
                raise ValueError("native replay differs from production")
            checkpoint_checks += 1
        raw = (root / f"inputs/{count}.bin").read_bytes()
        if len(raw) != 96 + count * 24 + len(result["input"]["planes"]) * 16:
            raise ValueError("resolved input length differs")
        if raw[96:96 + count * 24] != packed_snapshot(result["input"]["particles"]):
            raise ValueError("resolved initial particle bytes differ")
    for count in (8000, 110592):
        for step in (1, 120, 240, 480):
            path = root / f"runs/extra/{count}/independent/0/candidate/state-{step}-rows.json"
            rows = json.loads(path.read_bytes())
            if rows["capped"] or rows["duplicate_rows"] or rows["max"] >= 511:
                raise ValueError("independent comparator row check failed")
    identities = 0
    unavailable = []
    source_hashes = 0
    unavailable_sources = []
    for path in sorted((root / "build").glob("*/identity.json")):
        identity = json.loads(path.read_bytes())
        files = identity.get("sources", identity.get("adapted_source", identity.get("source", {})))
        source = root / "sources" / path.parent.name
        for name, expected in files.items():
            file = source / name
            if file.is_file():
                if sha(file.read_bytes()) != expected:
                    raise ValueError("experiment source changed")
                source_hashes += 1
            else:
                unavailable_sources.append(f"{path.parent.name}/{name}")
        binary = root / "bin" / path.parent.name
        if not binary.is_file():
            unavailable.append(path.parent.name)
        elif sha(binary.read_bytes()) != identity["binary_sha256"]:
            raise ValueError("experiment executable changed")
        else:
            identities += 1
    production = root / "bin/production"
    if production.is_file():
        identity = json.loads((root / "production-identity.json").read_bytes())
        if sha(production.read_bytes()) != identity["binary_sha256"]:
            raise ValueError("production executable changed")
        ptx = (root / "bin/production.ptx").read_bytes()
        if sha(ptx) != identity["ptx_sha256"] or ptx not in production.read_bytes():
            raise ValueError("fresh control PTX is not embedded")
        identities += 1
    else:
        unavailable.append("production")
    return {"passed": True, "raw_attempts": len(processes), "measured_pairs": comparisons,
            "production_snapshot_checks": checkpoint_checks, "binary_hashes_verified": identities,
            "binary_checks_unavailable": unavailable, "failed_attempts_retained": failed,
            "source_hashes_verified": source_hashes, "source_checks_unavailable": unavailable_sources,
            "interrupted_or_timed_out_attempts_retained": interrupted,
            "scope": "raw integrity, requests, finite states, exact production replay and independent timing arithmetic; not physical accuracy certification"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory.resolve()), indent=2, allow_nan=False))
