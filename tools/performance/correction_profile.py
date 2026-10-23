"""Locate correction costs in early and evolved CUDA motion.

Counter replay and CPU sampling stay separate from primary timings. The launch
selection follows the inspected solver sequence and is checked against a full
timeline before interpreting a correction capture.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys

from tools.cuda.compare import compare
from .capture import digest, invoke, load_attempt, write_json
from .compact_trace import analyse
from .contract import arguments
from .timeline import union


def launch_index(particles: int, step: int, iteration: int) -> int:
    """Return the zero-based launch of a correction, with one-based step/iteration."""
    if (any(type(v) is not int for v in (particles, step, iteration))
            or not 1 <= particles <= 1_000_000 or not 1 <= step <= 480 or not 1 <= iteration <= 8):
        raise ValueError("positive bounded particle/step counts and iteration 1..8 are required")
    bits = (particles - 1).bit_length()
    sorting = bits * (bits + 1) // 2
    return (step - 1) * (54 + sorting) + 7 + sorting + (iteration - 1) * 6


def metric_rows(text: str) -> list[dict[str, str]]:
    """Read exported raw metrics without treating profiler notices as CSV data."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if {"Metric Name", "Metric Value", "Metric Unit"} <= set(next(csv.reader([line])))), None)
    if start is None:
        raise ValueError("no raw metric table was exported")
    rows = list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))
    if not rows or any(not row.get("Metric Name") or row.get("Metric Value") is None for row in rows):
        raise ValueError("empty or incomplete counter export")
    return rows


def windows(directory: Path, particles: int) -> dict:
    """Partition a validated full trace at kernel boundaries, retaining overlap."""
    whole = analyse(directory, particles, 480, "compact-stages")
    with sqlite3.connect(f"file:{directory / 'cuda.sqlite'}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        kernels = list(db.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start"))
        launches = list(db.execute("SELECT a.* FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuLaunchKernel' ORDER BY a.start"))
        waits = list(db.execute("SELECT a.* FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuStreamSynchronize' ORDER BY a.start"))
        copies = list(db.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_MEMCPY ORDER BY start"))
        memsets = list(db.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_MEMSET ORDER BY start"))
    bits = (particles - 1).bit_length()
    sorting = bits * (bits + 1) // 2
    sequence = [0, 1, 2] + [3] * sorting + [4, 12] + list(range(5, 11)) * 8 + [11]
    result = {}
    for first, last in ((1, 120), (121, 240), (241, 480)):
        begin, end = (first - 1) * len(sequence), last * len(sequence)
        start = launches[begin]["start"]
        stop = launches[end]["start"] if end < len(launches) else waits[-1]["end"]
        selected = kernels[begin:end]
        busy = union([(max(start, r["start"]), min(stop, r["end"]))
                      for r in [*selected, *copies, *memsets] if r["start"] < stop and r["end"] > start])
        operations = {str(op): sum(r["end"] - r["start"] for index, r in enumerate(selected)
                                  if sequence[index % len(sequence)] == op) / 1e9 for op in range(13)}
        result[f"{first}-{last}"] = {"window_s": (stop - start) / 1e9,
            "device_busy_union_s": busy / 1e9, "idle_gap_s": (stop - start - busy) / 1e9,
            "kernel_s": sum(r["end"] - r["start"] for r in selected) / 1e9,
            "operations_device_s": operations}
    # These offsets also identify the targeted counter captures in the trace.
    for step in (1, 241):
        for iteration in (1, 8):
            if sequence[launch_index(particles, step, iteration) % len(sequence)] != 7:
                raise ValueError("counter target is not a correction launch")
    return {"primary_timing": False, "boundary": "first acceleration launch to next window's first acceleration launch; final window ends at last completion",
            "whole": whole, "windows": result}


def _accepted(process: dict, document: dict, reference: dict, revision: str, steps: int) -> None:
    if (process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]
            or document["status"] not in ("completed", "completed_with_warnings")
            or document["completed_steps"] != str(steps) or document["failures"]
            or document["metadata"]["build_revision"] != revision or document["metadata"]["debug_assertions"]
            or document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
            or not compare(reference, document, exact=True)["passed"]):
        raise ValueError("diagnostic run changed physical work or failed")


def full_trace(directory: Path, source: Path, binary: Path, scene: Path,
               revision: str, reference: dict, env: dict[str, str]) -> dict:
    """Capture a full evolved workload without changing its production executable."""
    command = ["nsys", "profile", "--trace=cuda", "--sample=none", "--cpuctxsw=none",
               "--cuda-memory-usage=true", "--force-overwrite=false", "--output", str(directory / "cuda"),
               str(binary), *arguments(scene, "cuda", observation=False, kind="trace"), "--output", str(directory / "solver.json")]
    process, _ = invoke(command, source, directory, timeout=120, grace=30, env=env)
    document = json.loads((directory / "solver.json").read_bytes())
    _accepted(process, document, reference, revision, 480)
    process, _ = invoke(["nsys", "export", "--type=sqlite", "--output", str(directory / "cuda.sqlite"), str(directory / "cuda.nsys-rep")],
                        source, directory / "export", timeout=120, grace=30, env=env)
    if process["exit_code"] != 0:
        raise ValueError("full timeline export failed")
    result = windows(directory, 110592)
    write_json(directory / "windows.json", result)
    write_json(directory / "files.json", {p.relative_to(directory).as_posix(): digest(p.read_bytes()) for p in sorted(directory.rglob("*")) if p.is_file()})
    return result


def collect(work: Path, previous: Path, protocol: Path) -> None:
    """Run only bounded diagnostics against the existing verified control export."""
    root = work / "diagnosis"
    root.mkdir(exist_ok=False)
    source = previous / "control"
    binary = source / "target/release/maelstrom"
    identity = json.loads((previous / "control-source.json").read_bytes())
    old = json.loads((previous / "results/campaign.json").read_bytes())
    revision = old["implementations"]["control"]["revision"]
    if identity["tree_sha256"] != old["implementations"]["control"]["source"]["tree_sha256"]:
        raise ValueError("control source identity differs")
    def verify():
        if (digest(binary.read_bytes()) != old["implementations"]["control"]["binary_sha256"]
                or any(digest((source / n).read_bytes()) != h for n, h in identity["files_sha256"].items())):
            raise ValueError("diagnostic control changed")
    verify()
    shutil.copytree(previous / "reference/baseline/inputs", root / "inputs")
    scene = root / "inputs/scenes/capacity-block-48.toml"
    (root / "protocol.md").write_bytes(protocol.read_bytes())
    write_json(root / "identity.json", {"source": identity, "binary_sha256": digest(binary.read_bytes()),
        "revision": revision, "protocol_sha256": digest(protocol.read_bytes()),
        "collector_sha256": digest(Path(__file__).read_bytes())})
    env = dict(os.environ, XDG_CONFIG_HOME=str(root / "isolated-config"),
               MAELSTROM_SCENES_DIR=str(root / "isolated-scenes"), MAELSTROM_RUNS_DIR=str(root / "isolated-runs"))
    refs = {}
    for steps, path in ((4, previous / "results/capacity/110592/cpu-pilot"),
                        (480, previous / "results/paired-large/control/warmup")):
        shutil.copytree(path, root / f"references/{steps}")
        _, refs[steps] = load_attempt(root / f"references/{steps}")
    p, refs[241] = invoke([str(binary), *arguments(scene, "cuda", steps=241, observation=False, kind="warmup")],
                         source, root / "references/241", timeout=120, grace=30, env=env)
    _accepted(p, refs[241], refs[241], revision, 241)
    directory = root / "timelines/control-110592-480"
    command = ["nsys", "profile", "--trace=cuda", "--sample=none", "--cpuctxsw=none",
               "--cuda-memory-usage=true", "--force-overwrite=false", "--output", str(directory / "cuda"),
               str(binary), *arguments(scene, "cuda", observation=False, kind="trace"), "--output", str(directory / "solver.json")]
    p, _ = invoke(command, source, directory, timeout=120, grace=30, env=env)
    document = json.loads((directory / "solver.json").read_bytes())
    _accepted(p, document, refs[480], revision, 480)
    p, _ = invoke(["nsys", "export", "--type=sqlite", "--output", str(directory / "cuda.sqlite"), str(directory / "cuda.nsys-rep")],
                  source, directory / "export", timeout=120, grace=30, env=env)
    if p["exit_code"] != 0:
        raise ValueError("full timeline export failed")
    write_json(root / "windows.json", windows(directory, 110592))
    ncu = Path("/opt/nvidia/nsight-compute/2026.2.1/ncu")
    counter_runs = []
    if ncu.is_file():
        for label, args in (("version", ["--version"]), ("sections", ["--list-sections"]), ("help", ["--help"])):
            invoke([str(ncu), *args], source, root / f"counter-tool/{label}", timeout=30, grace=5, env=env)
        for step, iteration in ((1, 1), (1, 8), (241, 1), (241, 8)):
            directory = root / f"counters/step-{step}-iteration-{iteration}"
            steps = 4 if step == 1 else 241
            command = [str(ncu), "--clock-control", "none", "--cache-control", "none",
                "--kernel-name-base", "function", "--kernel-name", "solver", "--launch-skip", str(launch_index(110592, step, iteration)),
                "--launch-count", "1", "--export", str(directory / "correction")]
            for section in ("LaunchStats", "Occupancy", "ComputeWorkloadAnalysis", "InstructionStats", "MemoryWorkloadAnalysis", "WarpStateStats"):
                command += ["--section", section]
            command += [str(binary), *arguments(scene, "cuda", steps=steps, observation=False, kind="trace"), "--output", str(directory / "solver.json")]
            p, _ = invoke(command, source, directory, timeout=120, grace=30, env=env)
            available = p["exit_code"] == 0 and (directory / "correction.ncu-rep").is_file() and (directory / "solver.json").is_file()
            counter_runs.append({"step": step, "iteration": iteration, "launch_index": launch_index(110592, step, iteration), "collected": available})
            if not available:
                break
            _accepted(p, json.loads((directory / "solver.json").read_bytes()), refs[steps], revision, steps)
            p, _ = invoke([str(ncu), "--import", str(directory / "correction.ncu-rep"), "--page", "raw", "--csv"],
                          source, directory / "metrics", timeout=60, grace=10, env=env)
            import gzip
            text = gzip.decompress((directory / "metrics/stdout.gz").read_bytes()).decode()
            if p["exit_code"] != 0:
                raise ValueError("counter metric export failed")
            write_json(directory / "metrics.json", metric_rows(text))
    write_json(root / "counters.json", {"tool_found": ncu.is_file(), "runs": counter_runs})
    perf = shutil.which("perf")
    cpu = {"tool_found": perf is not None, "collected": False}
    if perf:
        directory = root / "cpu"
        p, _ = invoke([perf, "record", "-e", "cpu-clock:u", "-F", "99", "--call-graph", "dwarf", "-o", str(directory / "perf.data"),
            str(binary), *arguments(scene, "cuda", observation=False, kind="trace"), "--output", str(directory / "solver.json")],
            source, directory, timeout=120, grace=30, env=env)
        if p["exit_code"] == 0 and (directory / "solver.json").is_file():
            _accepted(p, json.loads((directory / "solver.json").read_bytes()), refs[480], revision, 480)
            q, _ = invoke([perf, "report", "--stdio", "--input", str(directory / "perf.data")], source, directory / "report", timeout=60, grace=10, env=env)
            cpu["collected"] = q["exit_code"] == 0
    write_json(root / "cpu.json", cpu)
    verify()
    write_json(root / "files.json", {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file()})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    try:
        collect(args.work.resolve(), args.previous.resolve(), args.protocol.resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Correction diagnosis: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
