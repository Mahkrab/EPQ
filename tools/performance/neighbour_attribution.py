"""Separate neighbour traversal, row writes and sorting in disposable CUDA builds.

The extra launches perturb scheduling and resources. Their device durations are
diagnostic evidence, never a replacement for production solver measurements.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys

from tools.cuda.compare import compare
from .capture import digest, invoke, write_json
from .contract import arguments, capacity_scene
from .machine_state import capture


def replace_once(text: str, old: str, new: str) -> str:
    """Refuse to instrument a source whose expected boundary has moved."""
    if text.count(old) != 1:
        raise ValueError(f"expected one instrumentation boundary: {old!r}")
    return text.replace(old, new, 1)


def instrument(source: Path) -> None:
    """Add dry traversal and separate row sorting to an exported source only."""
    path = source / "native/neighbours.cuh"
    text = path.read_text()
    text = replace_once(text, "Checked &c, bool fill)", "Checked &c, bool fill, bool dry=false)")
    text = replace_once(text, "b.neighbours[cursor]=j;", "if (!dry) b.neighbours[cursor]=j;")
    text = replace_once(text, "if (cursor>start) sort_row(b.neighbours+start,cursor-start);", "// Sorting is launched separately in this diagnostic export.")
    path.write_text(text)
    path = source / "native/solver.cu"
    text = path.read_text()
    text = replace_once(text, "    auto i=static_cast<unsigned int>(lane);\n    const auto pass=", """    auto i=static_cast<unsigned int>(lane);
    if (operation==14) {
        if ((b.diagnostic && b.diagnostic[0]!=ULLONG_MAX) || b.errors[i]) return;
        auto first=b.offsets[i], last=b.offsets[i+1];
        if (last>first) sort_row(b.neighbours+first,last-first);
        return;
    }
    const auto pass=""")
    text = replace_once(text, "operation==4 || operation==12", "operation==4 || operation==12 || operation==15")
    text = replace_once(text, "discover_row(b,s,i,c,operation==12);", "discover_row(b,s,i,c,operation!=4,operation==15);")
    path.write_text(text)
    path = source / "native/bridge.cpp"
    text = path.read_text()
    text = replace_once(text, "        if (!sort) {\n", """        if (operation==12) {
            // Dry traversal validates the exact row length without writing it.
            // All three passes share the original completion/diagnostic boundary.
            const unsigned int operations[]={15u,12u,14u};
            for (auto op : operations) {
                kernel_operation=op;
                auto status=launch();
                if (status.code) return status;
            }
            return {0,0};
        }
        if (!sort) {
""")
    path.write_text(text)


def analyse(database: Path, particles: int, *, split: bool) -> dict:
    """Require a complete correlated trace before attributing ordered operations."""
    if type(particles) is not int or not 1 <= particles <= 1_000_000:
        raise ValueError("particles must be an integer in 1..1000000")
    passes = (particles - 1).bit_length()
    sequence = [0, 1, 2] + [3] * (passes * (passes + 1) // 2) + [4]
    sequence += [15, 12, 14] if split else [12]
    sequence += list(range(5, 11)) * 8 + [11]
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as db:
        kernels = list(db.execute("SELECT start,end,correlationId FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start"))
        launches = list(db.execute("SELECT a.correlationId FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuLaunchKernel' ORDER BY a.start"))
        completions = db.execute("SELECT count(*) FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuStreamSynchronize'").fetchone()[0]
        transfers = list(db.execute("SELECT copyKind,count(*),sum(bytes) FROM CUPTI_ACTIVITY_KIND_MEMCPY GROUP BY copyKind ORDER BY copyKind"))
    if len(kernels) != 480 * len(sequence) or len(launches) != len(kernels) or completions != 24_481:
        raise ValueError("incomplete or unexpected diagnostic launch/completion model")
    if any(k[2] != call[0] or k[1] <= k[0] for k, call in zip(kernels, launches, strict=True)):
        raise ValueError("invalid kernel durations or launch correlation")
    windows = {}
    for first, last in ((1, 120), (121, 240), (241, 480)):
        selected = kernels[(first - 1) * len(sequence):last * len(sequence)]
        totals = {}
        for index, (start, end, _) in enumerate(selected):
            op = str(sequence[index % len(sequence)])
            totals[op] = totals.get(op, 0) + end - start
        windows[f"{first}-{last}"] = {"steps": last - first + 1,
            "operations_device_s": {op: ns / 1e9 for op, ns in totals.items()}}
    return {"primary_timing": False, "split": split, "particles": particles,
            "kernel_count": len(kernels), "completion_count": completions,
            "transfers": transfers, "windows": windows,
            "interpretation": "dry traversal includes checked distances and row-length validation; fill also writes rows; timing differences are not isolated store latency"}


def collect(control: Path, split: Path, root: Path) -> None:
    """Build isolated variants, compare full results, retain traces and offline code."""
    root.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, CUDA_HOME="/usr/local/cuda")
    revisions = {}
    for label, source in (("control", control), ("split", split)):
        files = {p.relative_to(source).as_posix(): digest(p.read_bytes())
                 for p in sorted(source.rglob("*")) if p.is_file() and "target" not in p.relative_to(source).parts}
        write_json(root / f"{label}-source.json", files)
        p, _ = invoke(["cargo", "build", "--release", "--locked", "--features", "cuda"], source, root / label / "build", timeout=600, env=env)
        if p["exit_code"] != 0:
            raise ValueError(f"{label} diagnostic build failed")
        revisions[label] = digest((source / "target/release/maelstrom").read_bytes())
    # These tests cover independent discovery, diagnostic precedence and retry.
    p, _ = invoke(["cargo", "test", "--release", "--locked", "--features", "cuda", "--lib", "cuda::", "--", "--include-ignored"], split, root / "split/tests", timeout=600, env=env)
    if p["exit_code"] != 0:
        raise ValueError("split diagnostic CUDA tests failed")
    inputs = root / "inputs"
    (inputs / "config").mkdir(parents=True)
    (inputs / "scenes").mkdir()
    (inputs / "config/defaults-v4.toml").write_bytes((control / "config/defaults-v4.toml").read_bytes())
    for side in (20, 48):
        scene = inputs / f"scenes/capacity-block-{side:02}.toml"
        scene.write_text(capacity_scene(side))
        documents, analyses = {}, {}
        for label, source in (("control", control), ("split", split)):
            destination = root / f"{side**3}/{label}"
            capture(source, root / f"telemetry/{side**3}-{label}-before")
            # Warm-up stays outside Nsight and outside the reported durations.
            p, _ = invoke([str(source / "target/release/maelstrom"), *arguments(scene, "cuda", observation=False, kind="warmup"), "--output", str(root / f"warmup-{side**3}-{label}.json")], source, destination / "warmup", env=env)
            if p["exit_code"] != 0:
                raise ValueError("diagnostic warm-up failed")
            p, _ = invoke(["nsys", "profile", "--trace=cuda", "--sample=none", "--cpuctxsw=none", "--cuda-memory-usage=true", "--force-overwrite=false", "--output", str(destination / "cuda"), str(source / "target/release/maelstrom"), *arguments(scene, "cuda", observation=False, kind="trace"), "--output", str(destination / "solver.json")], source, destination / "trace", env=env)
            if p["exit_code"] != 0 or p["timed_out"]:
                raise ValueError("diagnostic trace failed")
            doc = json.loads((destination / "solver.json").read_bytes())
            if (doc["completed_steps"] != "480" or doc["failures"] or doc["metadata"]["debug_assertions"]
                    or doc["status"] not in ("completed", "completed_with_warnings")
                    or doc["execution"] != {"mode": "cuda", "device": 0, "threads": 128}):
                raise ValueError("diagnostic run incomplete or wrong execution")
            warm = json.loads((root / f"warmup-{side**3}-{label}.json").read_bytes())
            if not compare(warm, doc, exact=True)["passed"]:
                raise ValueError("warm-up and trace physics differ")
            documents[label] = doc
            p, _ = invoke(["nsys", "export", "--type=sqlite", "--output", str(destination / "cuda.sqlite"), str(destination / "cuda.nsys-rep")], source, destination / "export", env=env)
            if p["exit_code"] != 0:
                raise ValueError("diagnostic trace export failed")
            analyses[label] = analyse(destination / "cuda.sqlite", side**3, split=label == "split")
            capture(source, root / f"telemetry/{side**3}-{label}-after")
        if not compare(documents["control"], documents["split"], exact=True)["passed"]:
            raise ValueError("split diagnostic changed physical results")
        if analyses["control"]["transfers"] != analyses["split"]["transfers"]:
            raise ValueError("split diagnostic changed transfer model")
        write_json(root / f"{side**3}/analysis.json", {"exact_physical_agreement": True, **analyses})
    codegen(control, root / "codegen-complete")
    write_json(root / "summary.json", {"primary_timing": False, "binary_sha256": revisions,
               "workloads": [8000, 110592], "exact_physical_agreement": True,
               "limitations": ["one trace per variant/size", "extra launches and changed compiler resources", "offline cubin is not the driver-loaded PTX JIT", "no new hardware counters", "large trajectory retains CFL warnings"]})


def codegen(source: Path, root: Path) -> None:
    """Retain offline code and tool output separately from driver-JIT evidence."""
    root.mkdir(parents=True, exist_ok=False)
    flags = ["--std=c++17", "--fmad=false", "--ftz=false", "--prec-div=true", "--prec-sqrt=true", "-O3", "--generate-line-info"]
    for kind, target in (("ptx", "compute_89"), ("cubin", "sm_89")):
        p, _ = invoke(["/usr/local/cuda/bin/nvcc", f"--{kind}", *flags, f"--gpu-architecture={target}", "native/kernels.cu", "-o", str(root / f"solver.{kind}")], source, root / kind, timeout=120)
        if p["exit_code"] != 0:
            raise ValueError("offline instruction generation failed")
    for name, flags in (("sass", ["--dump-sass"]), ("resources", ["--dump-resource-usage"])):
        p, _ = invoke(["/usr/local/cuda/bin/cuobjdump", *flags, str(root / "solver.cubin")], source, root / name)
        if p["exit_code"] != 0:
            raise ValueError("offline instruction inspection failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("instrument")
    p.add_argument("source", type=Path)
    p = sub.add_parser("collect")
    p.add_argument("control", type=Path)
    p.add_argument("split", type=Path)
    p.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "instrument":
            instrument(args.source.resolve())
        else:
            collect(args.control.resolve(), args.split.resolve(), args.output.resolve())
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"Neighbour attribution: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
