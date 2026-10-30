"""Isolate architectural PBF experiments from the production checkout.

Native replays use frozen inputs and device sources. Their timing and failure
contracts are explicitly different from Simulation's complete-step boundary.
All subprocesses use the existing bounded, raw-output evidence collector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import statistics
import struct
import sys
import tarfile

from .capture import invoke, write_json

VARIANTS = ("control", "pow64", "pow32", "fma", "soa", "cell32", "combined")
FLAGS = ["--std=c++17", "--ftz=false", "--prec-div=true", "--prec-sqrt=true", "-O3",
         "--gpu-architecture=compute_89"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def settings(document: dict) -> bytes:
    """Encode the inspected C ABI, reproducing the host Poly6 f32 operations."""
    config = document["input"]["configuration"]
    model, derived = config["numerical"], config["derived"]
    h, distance = map(f32, (derived["support_radius_m"], derived["artificial_pressure_reference_separation_m"]))
    h2 = f32(h * h)
    h4 = f32(h2 * h2)
    h8 = f32(h4 * h4)
    term = f32(h2 - f32(distance * distance))
    coefficient = f32(315 / f32(f32(64 * f32(math.pi)) * f32(h * h8)))
    reference = f32(coefficient * f32(term * f32(term * term)))
    count = len(document["input"]["particles"])
    acceleration = model["external_acceleration_m_s2"]
    return struct.pack("<4I12fd2IQ2f", count, 1 << (count - 1).bit_length(),
                       len(document["input"]["planes"]), 0,
                       model["fixed_timestep_s"], h, derived["normalised_rest_density_per_m3"],
                       derived["relaxation_per_m2"],
                       derived["artificial_pressure_strength_m2"] if model["artificial_pressure_enabled"] else 0,
                       reference, model["artificial_pressure_exponent"], model["correction_scale"],
                       derived["particle_mass_kg"], *(acceleration[k] for k in "xyz"),
                       0.125, 0, 0, 0,
                       model.get("xsph_viscosity_coefficient", .01) if model["xsph_viscosity_enabled"] else 0,
                       model.get("vorticity_confinement_strength_m_s", .1) if model["vorticity_confinement_enabled"] else 0)


def snapshot_bytes(particles: list[dict]) -> bytes:
    return b"".join(struct.pack("<fff", *(p[field][k] for k in "xyz"))
                    for field in ("position_m", "velocity_m_s") for p in particles)


def encode_input(document: dict, destination: Path) -> None:
    """Export actual resolved particles and parameters, never a lattice guess."""
    raw = settings(document) + snapshot_bytes(document["input"]["particles"])
    for plane in document["input"]["planes"]:
        raw += struct.pack("<4f", *(plane["normal"][k] for k in "xyz"), plane["offset_m"])
    destination.write_bytes(raw)


def soa_access(source: str) -> str:
    """Change position accesses only; retain every numerical expression/order."""
    pattern = re.compile(r"b\.(old_position|position)\[")
    result, cursor = [], 0
    while match := pattern.search(source, cursor):
        end, depth = match.end(), 1
        while end < len(source) and depth:
            depth += (source[end] == "[") - (source[end] == "]")
            end += 1
        if depth:
            raise ValueError("unclosed position index")
        index = source[match.end():end - 1]
        tail = end
        while tail < len(source) and source[tail].isspace():
            tail += 1
        result.append(source[cursor:match.start()])
        pointer = "b." + match.group(1)
        if source[tail:tail + 1] == "=" and source[tail:tail + 2] != "==":
            stop = source.index(";", tail)
            value = soa_access(source[tail + 1:stop])
            result.append(f"arch_store({pointer},{index},{value})")
            cursor = stop
        else:
            result.append(f"arch_load({pointer},{index})")
            cursor = end
    result.append(source[cursor:])
    return "".join(result)


def overlay(directory: Path, variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError("unknown experimental source")
    power = directory / "power.cuh"
    if variant in ("pow32", "combined"):
        source = power.read_text()
        anchor = "__device__ float ordered_power(float x,float exponent) {"
        if source.count(anchor) != 1:
            raise ValueError("power anchor changed")
        source = source[:source.index(anchor)] + anchor + "\n    if (exponent==4.0f) { float square=x*x;return square*square; }\n    return powf(x,exponent);\n}\n"
        power.write_text(source)
    elif variant == "pow64":
        source = power.read_text()
        power.write_text(source.replace("if (exponent==4.0f && try_power_four(x,result)) return result;", "(void)result;"))
    if variant in ("soa", "combined"):
        helper = """
__device__ __constant__ unsigned int arch_count;
__device__ Vector arch_load(const Vector *p,unsigned int i) {
    const auto *v=reinterpret_cast<const float *>(p);
    return {v[i],v[arch_count+i],v[2*arch_count+i]};
}
__device__ void arch_store(Vector *p,unsigned int i,Vector a) {
    auto *v=reinterpret_cast<float *>(p);v[i]=a.x;v[arch_count+i]=a.y;v[2*arch_count+i]=a.z;
}
"""
        for name in ("solver.cu", "neighbours.cuh", "state_observation.cuh"):
            path = directory / name
            path.write_text(soa_access(path.read_text()))
        path = directory / "solver.cu"
        path.write_text(path.read_text().replace('#include "power.cuh"', '#include "power.cuh"\n' + helper, 1))
    if variant == "cell32":
        path = directory / "neighbours.cuh"
        source = path.read_text()
        for axis in "xyz":
            source = source.replace(f"floor(static_cast<double>(p.{axis})/width)", f"floorf(p.{axis}/static_cast<float>(width))")
        path.write_text(source)


def build(root: Path) -> None:
    """Build task-owned native sources; never mutate an existing source export."""
    compiler = "/usr/local/cuda/bin/nvcc"
    here = Path(__file__).parent
    (root / "bin").mkdir(exist_ok=True)
    (root / "inputs").mkdir(exist_ok=True)
    for variant in VARIANTS:
        directory = root / "sources" / variant
        shutil.copytree(root / "native-control", directory)
        overlay(directory, variant)
        shutil.copyfile(here / "architecture_driver.cu", directory / "driver.cu")
        flags = FLAGS + (["--fmad=true"] if variant in ("fma", "combined") else ["--fmad=false"])
        if variant in ("soa", "combined"):
            flags += ["-DARCH_SOA"]
        process, _ = invoke([compiler, *flags, "driver.cu", "-o", str(root / "bin" / variant)],
                            directory, root / "build" / variant, timeout=180)
        if process["exit_code"] != 0:
            raise ValueError(f"native build failed: {variant}")
        process, _ = invoke([compiler, *flags, "--ptx", "driver.cu", "-o", str(root / "bin" / (variant + ".ptx"))],
                            directory, root / "ptx" / variant, timeout=120)
        if process["exit_code"] != 0:
            raise ValueError(f"PTX inspection build failed: {variant}")
        write_json(root / "build" / variant / "identity.json", {
            "sources": {p.name: digest(p) for p in sorted(directory.iterdir()) if p.is_file()},
            "binary_sha256": digest(root / "bin" / variant),
            "ptx_sha256": digest(root / "bin" / (variant + ".ptx")), "flags": flags})
        print("built", variant, flush=True)
    process, _ = invoke(["c++", "-std=c++17", "-O3", "-Wall", "-Wextra", "-Werror",
                         str(here / "architecture_quality.cpp"), "-o", str(root / "bin/quality")],
                        root, root / "build/quality")
    if process["exit_code"] != 0:
        raise ValueError("quality reader build failed")


def run_native(root: Path, label: str, variant: str, count: int, mode: str,
               *, steps: int = 480, iterations: int = 8, observations: bool = False,
               effects: bool = False) -> dict:
    destination = root / "runs" / label
    prefix = destination / "state"
    input_file = root / "inputs" / f"{count}{'-effects' if effects else ''}.bin"
    if not input_file.is_file():
        raise ValueError(f"resolved experiment input is missing: {input_file}")
    process, document = invoke([str(root / "bin" / variant), str(input_file),
                               str(steps), str(iterations), mode, str(prefix), str(int(observations)), str(int(effects))],
                              root, destination, timeout=120)
    if process["exit_code"] != 0 or document is None or document["steps"] != steps:
        raise ValueError(f"native experiment failed: {label}")
    document["final_sha256"] = digest(destination / f"state-{steps}.bin")
    write_json(destination / "metrics.json", document)
    return document


def collect(root: Path) -> None:
    """One warm-up and five alternating pairs; do not replace slow samples."""
    experiments = [("deferred", "control", "deferred"), ("snapshots", "control", "snapshots"),
                   ("resident", "control", "resident"),
                   *((v, v, "checked") for v in VARIANTS if v != "control"),
                   ("combined-resident", "combined", "resident")]
    summary = {}
    for count in (8000, 110592):
        for label, variant, mode in experiments:
            pairs = []
            for index in range(6):
                pair = {}
                for name in (("control", "candidate") if index % 2 == 0 else ("candidate", "control")):
                    which, boundary = ("control", "checked") if name == "control" else (variant, mode)
                    pair[name] = run_native(root, f"{count}/{label}/{index}/{name}", which, count, boundary)
                if index:
                    pairs.append(pair)
                print(count, label, index, {k: v["solver_s"] for k, v in pair.items()}, flush=True)
            values = {name: [pair[name]["solver_s"] for pair in pairs] for name in ("control", "candidate")}
            medians = {name: statistics.median(v) for name, v in values.items()}
            summary[f"{count}/{label}"] = {"samples_s": values, "median_s": medians,
                "speedup": medians["control"] / medians["candidate"],
                "ranges_s": {k: [min(v), max(v)] for k, v in values.items()},
                "paired_speedup": [p["control"]["solver_s"] / p["candidate"]["solver_s"] for p in pairs],
                "same_final_bits": [p["control"]["final_sha256"] == p["candidate"]["final_sha256"] for p in pairs]}
    write_json(root / "summary.json", summary)


def restore_evidence(assets: Path, destination: Path) -> None:
    """Restore hash-checked archives and deduplicated states into a new directory."""
    members = json.loads((assets / "archive-members.json").read_bytes())
    files = json.loads((assets / "file-sha256.json").read_bytes())
    blobs = json.loads((assets / "blob-index.json").read_bytes())

    def relative(name: str) -> Path:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("unsafe evidence member path")
        return Path(*path.parts)

    for name in [*members, "blob-index.json", "archive-members.json"]:
        path = relative(name)
        if len(path.parts) != 1 or digest(assets / path) != files[name]:
            raise ValueError("evidence archive or index changed")
    destination.mkdir(parents=True, exist_ok=False)
    for name, expected in members.items():
        with tarfile.open(assets / name, "r:xz") as archive:
            entries = archive.getmembers()
            if len(entries) != len(expected) or {e.name for e in entries} != set(expected):
                raise ValueError("evidence archive member set differs")
            for entry in entries:
                path = destination / relative(entry.name)
                if not entry.isfile() or path.exists():
                    raise ValueError("non-regular or duplicate evidence member")
                source = archive.extractfile(entry)
                if source is None:
                    raise ValueError("evidence member has no content")
                raw = source.read()
                record = expected[entry.name]
                if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
                    raise ValueError("evidence member bytes changed")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
    for name, record in blobs.items():
        target = destination / relative(name)
        if target.exists() or re.fullmatch(r"[0-9a-f]{64}", record["sha256"]) is None:
            raise ValueError("invalid or duplicate state binding")
        source = destination / "objects" / record["sha256"]
        if source.stat().st_size != record["bytes"] or digest(source) != record["sha256"]:
            raise ValueError("state object changed")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("build", "collect", "restore"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    try:
        root = args.directory.resolve()
        if args.operation == "build":
            build(root)
        elif args.operation == "collect":
            collect(root)
        else:
            if args.destination is None:
                raise ValueError("restore requires a new --destination")
            restore_evidence(root, args.destination.resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Architecture experiment: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
