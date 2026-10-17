"""Collect paired serial searches and rebuild their comparison from retained samples.

Each search follows the unchanged baseline policy. Comparisons require the same
source, binary, machine context and physical outputs; incomplete sizes have no ratio.
Run as ``python3 -m tools.baseline.compare collect NEW_DIRECTORY`` on the primary PC.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from . import main as baseline
from .data import BACKENDS, POLICY, clean, physical_document, read_json, require_exact, sha256


def validate_pair(directory: Path) -> tuple[dict, dict, list[dict]]:
    """Recheck raw evidence and qualify each shared size before deriving speedup."""
    datasets = {}
    attempts = {}
    for backend, identity in BACKENDS.items():
        path = directory / backend
        baseline.report(path)
        dataset = read_json(path / "dataset.json")
        if dataset.get("backend") != backend or dataset["interrupted"]:
            raise ValueError("comparison requires identified, uninterrupted campaigns")
        values = baseline.load_attempts(path, dataset)
        keys = [(a["particles"], a["kind"], a["index"]) for a in values]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate sample identity")
        for result in [read_json(path / "correctness.json"),
                       *(a["result"] for a in values if a["result"] is not None)]:
            if result["backend"] != identity or result["metadata"]["backend"] != identity:
                raise ValueError("sample backend differs from the selected search")
        datasets[backend] = dataset
        attempts[backend] = values
    brute, grid = datasets.values()
    for field in ("source", "binary_sha256", "policy", "manifest", "manifest_sha256", "collector_files_sha256"):
        if brute[field] != grid[field]:
            raise ValueError(f"paired campaigns differ in {field}")
    for field in ("cpu_model", "architecture", "kernel", "os_release", "cpu_topology", "cpu_affinity",
                  "rustc", "cargo", "profile", "rustflags", "scheduling_controls", "virtualisation"):
        if brute["environment"][field] != grid["environment"][field]:
            raise ValueError(f"paired environment differs in {field}")
    require_exact(physical_document(read_json(directory / "brute-force/correctness.json")),
                  physical_document(read_json(directory / "uniform-grid/correctness.json")))
    rows = []
    for b, g in zip(brute["summaries"], grid["summaries"], strict=True):
        count = b["particles"]
        if count != g["particles"]:
            raise ValueError("paired size sequence differs")
        bv = [a for a in attempts["brute-force"] if a["particles"] == count]
        gv = [a for a in attempts["uniform-grid"] if a["particles"] == count]
        warmups = [a for a in bv if a["kind"] == "warmup" and clean(a)]
        reference = physical_document(warmups[0]["result"]) if len(warmups) == 1 else None
        checked = 0
        for attempt in [*bv, *gv]:
            if clean(attempt) and reference is not None:
                require_exact(physical_document(attempt["result"]), reference,
                              f"{count} particles {attempt['kind']} {attempt['index']}")
                checked += 1
        qualified = reference is not None and b["primary"] is not None and g["primary"] is not None
        rows.append({
            "particles": count, "exact_complete_attempts": checked,
            "qualified": qualified,
            "speedup": b["primary"]["median_s"] / g["primary"]["median_s"] if qualified else None,
            "brute_force": b, "uniform_grid": g,
        })
    return brute, grid, rows


def report(directory: Path) -> tuple[dict, str]:
    """Return machine-readable judgements and a readable same-device comparison."""
    brute, grid, rows = validate_pair(directory)
    result = {
        "schema_version": 1, "policy": POLICY["id"], "comparison_policy": "reference-comparison-v1",
        "datasets_sha256": {backend: sha256((directory / backend / "dataset.json").read_bytes())
                            for backend in BACKENDS},
        "rows": rows,
    }
    text = ["# Paired serial brute-force and uniform-grid measurements", "",
            f"Policy: `{POLICY['id']}`; exact serial acceptance: `reference-comparison-v1`.",
            f"CPU: {brute['environment']['cpu_model']}; {brute['environment']['os_release']}.",
            f"Source: `{brute['source']['base_commit']}`; tree SHA-256: `{brute['source']['tree_sha256']}`.",
            f"Collection: {brute['started_utc']} to {grid['finished_utc']}.", "",
            "Brute force was collected first, then the grid, using one binary and unchanged inputs.",
            "Each series retains one warm-up, three total-only samples and a separate profile per size.",
            "Every clean full attempt is checked against the brute-force warm-up at that size, including",
            "sign-sensitive hashes of all particle snapshots, physical inputs, audits, CFL and completion.",
            "A missing clean primary set or reference prevents a speedup ratio.", "",
            "| Particles | Brute force median (s) | Grid median (s) | Speedup | Exact complete attempts |",
            "| ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        medians = [f"{row[key]['primary']['median_s']:.6f}" if row[key]["primary"] else "unavailable"
                   for key in ("brute_force", "uniform_grid")]
        ratio = f"{row['speedup']:.3f}×" if row["qualified"] else "unavailable"
        text.append(f"| {row['particles']:,} | {medians[0]} | {medians[1]} | {ratio} | {row['exact_complete_attempts']} |")
    text += ["", "Raw totals, min–max ranges, sample standard deviations, throughput, profiles and every",
             "failed/partial attempt remain in the two backend reports and their hashed raw indexes.",
             "Profiles contain extra clocks and do not supply the primary speedup. Memory was not measured.",
             "The fixed collection order, shared host load, scheduling and thermal state remain confounders;",
             "three samples show observed variability, not statistical significance or a universal crossover."]
    return result, "\n".join(text) + "\n"


def collect(directory: Path) -> None:
    """Collect both searches sequentially into a new destination, preserving failures."""
    directory.mkdir(parents=True, exist_ok=False)
    for backend in BACKENDS:
        baseline.collect(directory / backend, backend)
        if read_json(directory / backend / "dataset.json")["interrupted"]:
            raise ValueError("collection interrupted; retained partial campaign without starting another search")
    result, markdown = report(directory)
    baseline.write_json(directory / "comparison.json", result)
    with (directory / "report.md").open("x", encoding="utf-8") as stream:
        stream.write(markdown)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["collect", "report"])
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        directory = args.directory.resolve()
        if args.operation == "collect":
            collect(directory)
        else:
            result, markdown = report(directory)
            if result != read_json(directory / "comparison.json"):
                raise ValueError("stored comparison disagrees with raw evidence")
            print(markdown, end="")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"comparison: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
