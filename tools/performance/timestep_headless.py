"""Measure alternating complete headless steps separately from graphics and traces."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import statistics

from .capture import invoke


def run(root: Path) -> None:
    records = []
    for count in (8000, 32000, 110592):
        physical = None
        for pair in range(4):
            variants = ("control", "final") if pair % 2 == 0 else ("final", "control")
            for variant in variants:
                command = [str(root / (variant + "-bin")), "run", str(root / "inputs" / f"{count}.toml"),
                           "--backend", "cuda", "--device", "0", "--block-size", "128",
                           "--numerical-mode", "experimental", "--steps", "1200", "--unpaced",
                           "--measure", "--format", "json"]
                directory = root / "results" / f"headless-{count}-p{pair}-{variant}"
                process, document = invoke(command, root, directory, timeout=180)
                if process["exit_code"] != 0 or document is None:
                    raise ValueError(f"failed headless invocation: {directory.name}")
                if document["completed_steps"] != "1200" or document["failures"]:
                    raise ValueError("headless workload did not complete")
                if document["checkpoints"]:
                    raise ValueError("headless timing unexpectedly contains checkpoint audits")
                witness = {k: document[k] for k in ("input", "request", "steps", "final_snapshot", "status", "failures")}
                digest = hashlib.sha256(json.dumps(witness, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                if physical is not None and digest != physical:
                    raise ValueError("headless accepted state or diagnostics differ")
                physical = digest
                steps = document["measurements"]["steps"]
                if len(steps) != 1200 or any(x["stages"] is not None for x in steps):
                    raise ValueError("headless timer mode differs")
                row = dict(particles=count, pair=pair, variant=variant, physical_sha256=digest,
                           complete_command_s=process["wall_s"],
                           solver_ms_per_step=statistics.mean(x["total_s"] for x in steps) * 1000)
                (directory / "summary.json").write_text(json.dumps(row, indent=2) + "\n")
                records.append(row)
                print(json.dumps(row), flush=True)
    (root / "results/headless-comparison.json").write_text(json.dumps(records, indent=2) + "\n")


def verify_reruns(root: Path) -> None:
    """Recompute saved control inputs with the reviewed executable from step zero."""
    records = []
    for count in (32000, 110592):
        original = gzip.decompress((root / f"results/headless-{count}-p1-control/stdout.gz").read_bytes())
        expected = json.loads(original)
        saved = root / "inputs" / f"rerun-{count}.json"
        with saved.open("xb") as stream:
            stream.write(original)
        process, actual = invoke([str(root / "reviewed-bin"), "rerun", str(saved), "--format", "json"],
                                 root, root / "results" / f"rerun-{count}", timeout=180)
        if process["exit_code"] != 0 or actual is None:
            raise ValueError("recorded-input rerun failed")
        for key in ("input", "request", "steps", "final_snapshot", "status", "failures"):
            # Canonical text also distinguishes negative zero, unlike Python's
            # numeric equality. Rust's recorded f32 values round-trip exactly.
            if json.dumps(actual[key], sort_keys=True) != json.dumps(expected[key], sort_keys=True):
                raise ValueError(f"rerun changed {key}")
        records.append(dict(particles=count, steps=int(actual["completed_steps"]),
                            exact_states_and_diagnostics=True))
    (root / "results/rerun-equivalence.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--rerun", action="store_true", help="recompute saved control inputs with reviewed-bin")
    args = parser.parse_args()
    (verify_reruns if args.rerun else run)(args.root.resolve())
