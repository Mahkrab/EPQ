"""Compare an opt-in Rust ThinLTO build without changing release defaults.

Native compiler flags and numerical work remain fixed. This tests host compiler
settings on the declared CUDA workloads, not a universal compiler configuration.
"""

import argparse
import json
import os
from pathlib import Path
import statistics
import sys

from tools.cuda.compare import compare
from .capture import digest, invoke, write_json
from .contract import arguments
from .machine_state import capture
from .report import metrics


def collect(source: Path, inputs: Path, root: Path) -> None:
    root.mkdir(parents=True, exist_ok=False)
    baseline = source / "target/release/maelstrom"
    candidate = root / "target/release/maelstrom"
    env = dict(os.environ, CUDA_HOME="/usr/local/cuda", CARGO_TARGET_DIR=str(root / "target"),
               CARGO_PROFILE_RELEASE_LTO="thin", CARGO_PROFILE_RELEASE_CODEGEN_UNITS="1")
    write_json(root / "settings.json", {"candidate": {k: env[k] for k in ("CARGO_PROFILE_RELEASE_LTO", "CARGO_PROFILE_RELEASE_CODEGEN_UNITS")},
               "native_flags_changed": False, "production_defaults_changed": False,
               "rustflags": os.environ.get("RUSTFLAGS"), "cpu_target": "unchanged portable default"})
    p, _ = invoke(["cargo", "build", "--release", "--locked", "--features", "cuda"], source, root / "build", timeout=600, env=env)
    if p["exit_code"] != 0:
        raise ValueError("ThinLTO build failed")
    p, _ = invoke(["cargo", "test", "--release", "--locked", "--features", "cuda", "--lib", "cuda::", "--", "--include-ignored"], source, root / "tests", timeout=600, env=env)
    if p["exit_code"] != 0:
        raise ValueError("ThinLTO CUDA tests failed")
    results = sample(source, baseline, candidate, inputs, root)
    write_json(root / "summary.json", {"exact_physical_agreement": True, "results": results,
        "binary_sha256": {"release": digest(baseline.read_bytes()), "thin": digest(candidate.read_bytes())},
        "binary_bytes": {"release": baseline.stat().st_size, "thin": candidate.stat().st_size},
        "limitations": ["CUDA workloads measure host effects only; native device flags unchanged", "no CPU-backend performance claim", "large workload retains known CFL warnings", "build durations are not matched cold-build comparisons"]})


def sample(source: Path, baseline: Path, candidate: Path, inputs: Path, root: Path,
           workloads: tuple[tuple[int, int], ...] = ((8000, 20), (110592, 48))) -> dict:
    """Retain fresh alternating pairs, without rebuilding or pooling campaigns."""
    results = {}
    for particles, side in workloads:
        scene = inputs / f"scenes/capacity-block-{side:02}.toml"
        reference = None
        samples = {"release": [], "thin": []}
        for index in range(6):
            for label in (("release", "thin") if index % 2 else ("thin", "release")):
                binary = baseline if label == "release" else candidate
                directory = root / f"{particles}/{label}/{'warmup' if index == 0 else f'sample-{index}'}"
                capture(source, root / f"telemetry/{particles}-{label}-{index}")
                p, _ = invoke([str(binary), *arguments(scene, "cuda", observation=False, kind="warmup" if index == 0 else "sample"), "--output", str(directory / "solver.json")], source, directory)
                document = json.loads((directory / "solver.json").read_bytes())
                if (p["exit_code"] != 0 or p["timed_out"] or p["interrupted"] or document["completed_steps"] != "480"
                        or document["failures"] or document["metadata"]["debug_assertions"]
                        or document["status"] not in ("completed", "completed_with_warnings")
                        or document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}):
                    raise ValueError("compiler comparison changed execution or failed")
                if reference is None:
                    reference = document
                if not compare(reference, document, exact=True)["passed"]:
                    raise ValueError("compiler settings changed physical results")
                if index:
                    samples[label].append(metrics(p, document, "sample"))
        results[str(particles)] = {label: {"samples": rows, "median_solver_s": statistics.median(row["solver_s"] for row in rows)}
                                   for label, rows in samples.items()}
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("inputs", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        collect(args.source.resolve(), args.inputs.resolve(), args.output.resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Compiler trial: {error}", file=sys.stderr)
        raise SystemExit(1)
