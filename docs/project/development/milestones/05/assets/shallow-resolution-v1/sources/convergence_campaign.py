"""Retain isolated physical experiments before drawing any cost conclusions.

Each immutable request owns a complete binary observation stream, independent
all-pairs audit and checksums. Evidence lives outside temporary storage; partial
failed requests remain visible and cannot be overwritten by a retry.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024*1024), b""):
            value.update(block)
    return value.hexdigest()


def persist(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())


def pin_binary(path: Path) -> Path:
    """Keep a request's solver and later auditor fixed while tools evolve."""
    checksum = digest(path)
    destination = path.parent / "objects" / checksum
    destination.parent.mkdir(exist_ok=True)
    if not destination.exists():
        handle, temporary_name = tempfile.mkstemp(dir=destination.parent)
        os.close(handle)
        temporary = Path(temporary_name)
        try:
            shutil.copy2(path, temporary)
            if digest(temporary) != checksum:
                raise RuntimeError("executable changed while being pinned")
            with temporary.open("rb") as file:
                os.fsync(file.fileno())
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
    if digest(destination) != checksum:
        raise RuntimeError("pinned executable differs from its identity")
    return destination


def run(root: Path, binaries: Path, label: str, *, scene: str = "hydro", dt: float = 1/240,
        duration: float = 2, iterations: int = 8, boundary: bool = False,
        clamp: bool = False, epsilon: float = 20, scale: float = .0625,
        pressure: float = .1, poly: bool = False, refresh: bool = True, contact: bool = False,
        contact_distance: float = .0255, kernel: int | None = None, timeout_s: int = 600,
        wall_inset: float = 0) -> dict:
    directory = root / "runs" / label
    directory.mkdir(parents=True, exist_ok=False)
    parameters = dict(scene=scene, dt=dt, duration=duration, iterations=iterations,
                      boundary=boundary, clamp=clamp, epsilon=epsilon, scale=scale,
                      pressure=pressure, poly=poly, refresh=refresh, contact=contact, contact_distance=contact_distance,kernel=kernel,wall_inset=wall_inset)
    solver, auditor = pin_binary(binaries / "solver"), pin_binary(binaries / "audit")
    command = [str(solver), scene, str(dt), str(duration), str(iterations),
               str(int(boundary)), str(int(clamp)), str(epsilon), str(scale), str(pressure),
               str(int(poly) if kernel is None else kernel), str(int(refresh)), str(int(contact)), str(contact_distance)]
    if wall_inset:
        command.append(str(wall_inset))
    persist(directory / "request.json", {"parameters": parameters, "command": command,
            "solver_sha256": digest(solver),
            "auditor_sha256": digest(auditor),
            "contact_protocol_sha256": digest(root / "contact-protocol.json") if contact else None,
            "distribution_protocol_sha256": digest(root / "distribution-protocol.json") if contact_distance != .0255 else None,
            "kernel_protocol_sha256": digest(root / "kernel-protocol.json") if kernel==2 else None,
            "extent_protocol_sha256": digest(root / "extent-protocol.json") if wall_inset else None,
            "timeout_s": timeout_s,
            "protocol_sha256": digest(root / "protocol.json")})
    raw = directory / "states.bin"
    timed_out = False
    with raw.open("xb") as stdout, (directory / "stderr.txt").open("xb") as stderr:
        try:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=timeout_s)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = None
            timed_out = True
        stdout.flush()
        os.fsync(stdout.fileno())
        stderr.flush()
        os.fsync(stderr.fileno())
    audit_code = None
    observations = []
    if code == 0:
        with (directory / "audit.jsonl").open("xb") as output, (directory / "audit-stderr.txt").open("xb") as errors:
            audit = subprocess.run([str(auditor), str(raw), str(int(boundary))],
                                   stdout=output, stderr=errors, timeout=300)
            audit_code = audit.returncode
        if audit_code == 0:
            observations = [json.loads(line) for line in (directory / "audit.jsonl").read_text().splitlines()]
    raw_hash = digest(raw)
    compressed = directory / "states.bin.gz"
    with raw.open("rb") as source, compressed.open("xb") as target:
        with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as destination:
            shutil.copyfileobj(source, destination)
        target.flush()
        os.fsync(target.fileno())
    with gzip.open(compressed, "rb") as source:
        restored = hashlib.file_digest(source, "sha256").hexdigest()
    if restored != raw_hash:
        raise RuntimeError("raw observation compression failed readback")
    raw.unlink()
    final = observations[-1] if observations else None
    settled = [o for o in observations if o["time_s"] >= 5]
    summary = {"exit_code": code, "timed_out": timed_out, "audit_exit_code": audit_code,
               "raw_sha256": raw_hash, "gzip_sha256": digest(compressed),
               "observations": len(observations), "parameters": parameters, "final": final,
               "worst_p95_compression": max((o["p95_compression"] for o in observations), default=None),
               "worst_max_compression": max((o["max_compression"] for o in observations), default=None),
               "minimum_separation_m": min((o["minimum_separation_m"] for o in observations), default=None),
               "max_mechanical_energy_gain_J_kg": max((o["mechanical_J_kg"]-observations[0]["mechanical_J_kg"] for o in observations), default=None),
               "settled_kinetic_J_kg_max": max((o["kinetic_J_kg"] for o in settled), default=None)}
    persist(directory / "summary.json", summary)
    print(label, "p95", summary["worst_p95_compression"], "centroid", final["centroid_relative_error"] if final else code,
          "KE", final["kinetic_J_kg"] if final else None, flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("binaries", type=Path)
    parser.add_argument("phase", choices=("mechanisms", "gradient", "qualification", "contact"))
    args = parser.parse_args()
    base = dict()
    if args.phase == "mechanisms":
        cases = [("signed", {}), ("clamp", dict(clamp=True)),
                 ("clamp-wall", dict(clamp=True,boundary=True)),
                 ("clamp-wall-no-pressure", dict(clamp=True,boundary=True,pressure=0)),
                 ("wall-signed", dict(boundary=True)),
                 ("clamp-wall-scaled-pressure", dict(clamp=True,boundary=True,pressure=.1*(.004166666666666667/.0020833333333333333)**2))]
    elif args.phase == "gradient":
        base = dict(boundary=True,clamp=True,pressure=0)
        cases = [("eps2",dict(epsilon=2)),("eps.02",dict(epsilon=.02)),
                 ("eps.0001",dict(epsilon=.0001)),("scale.5",dict(scale=.5)),
                 ("scale1",dict(scale=1)),("poly",dict(poly=True)),
                 ("poly-low-eps",dict(poly=True,epsilon=.02)),
                 ("poly-low-eps-scale.5",dict(poly=True,epsilon=.02,scale=.5)),
                 ("spiky-low-eps-scale.5",dict(epsilon=.02,scale=.5))]
    elif args.phase == "contact":
        base = dict(boundary=True,clamp=True,pressure=0,poly=True,epsilon=.02,scale=.5,contact=True)
        cases = [("isolated",{}),("iter32",dict(iterations=32)),
                 ("iter128",dict(iterations=128)),("spiky",dict(poly=False,iterations=32))]
    else:
        base = dict(boundary=True,clamp=True,pressure=0,kernel=2,contact=True,epsilon=.02,scale=.5,duration=6)
        cases = []
        for scene in ("hydro", "fall", "collision"):
            for dt in (1/120,1/240,1/480):
                cases.append((f"{scene}-dt{round(1/dt)}",dict(scene=scene,dt=dt,iterations=32)))
        for it in (8,128):
            cases.append((f"hydro-iter{it}",dict(iterations=it)))
    for label, settings in cases:
        run(args.root.resolve(), args.binaries.resolve(), args.phase+"-"+label, **(base | settings))


if __name__ == "__main__":
    main()
