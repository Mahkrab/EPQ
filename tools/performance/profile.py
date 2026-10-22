"""Collect diagnostic timelines independently of the primary timing samples.

Profiler stdout is not solver JSON. Keep the application's published result and
the profiler's raw files separately, including unsupported-feature failures.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from .capture import digest, invoke, write_json
from .contract import arguments
from .study import clean, verify


def collect(directory: Path, steps: int) -> None:
    """Capture early or full-motion CUDA work without checkpoint-audit interference."""
    if steps not in (4, 480):
        raise ValueError("timeline request must be the four-step pilot or 480-step trajectory")
    _, source, binary = verify(directory)
    target = directory / f"timelines/cuda-8000-{steps}"
    if target.exists():
        raise FileExistsError(target)
    result_path = target / "solver.json"
    report_path = target / "cuda"
    command = ["nsys", "profile", "--trace=cuda", "--sample=none", "--cpuctxsw=none",
               "--cuda-memory-usage=true", "--force-overwrite=false", "--output", str(report_path),
               str(binary), *arguments(source / "scenes/falling-block-20.toml", "cuda", steps=steps,
                                       observation=False, kind="trace"), "--output", str(result_path)]
    process, _ = invoke(command, source, target, timeout=180, grace=30)
    numerical = json.loads(result_path.read_bytes()) if result_path.is_file() else None
    admitted = clean(process, numerical, series="cuda", steps=steps, observation=False, particles=8000)
    write_json(target / "assessment.json", {"tool_exit_success": process["exit_code"] == 0,
               "solver_completed_cleanly": admitted, "primary_timing": False,
               "solver_sha256": digest(result_path.read_bytes()) if numerical else None})
    report = report_path.with_suffix(".nsys-rep")
    if not report.is_file():
        return
    reports = ["cuda_api_sum", "cuda_gpu_kern_sum", "cuda_gpu_mem_time_sum", "cuda_gpu_mem_size_sum"]
    invoke(["nsys", "stats", "--report", ",".join(reports), "--format", "csv", str(report)],
           source, target / "statistics", timeout=90, grace=10)
    sqlite = report_path.with_suffix(".sqlite")
    if not sqlite.exists():
        invoke(["nsys", "export", "--type=sqlite", "--output", str(sqlite), str(report)],
               source, target / "export", timeout=90, grace=10)
    files = {p.relative_to(target).as_posix(): digest(p.read_bytes())
             for p in sorted(target.rglob("*")) if p.is_file()}
    write_json(target / "files.json", files)
    verify(directory)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--steps", type=int, choices=(4, 480), default=4)
    args = parser.parse_args()
    try:
        collect(args.directory.resolve(), args.steps)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Timeline collection: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
