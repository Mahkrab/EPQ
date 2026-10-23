"""Repeat the declared pairs without replacing a variable first campaign.

The executable and numerical qualification are reused unchanged. Machine-state
readings finish outside each invocation, so they do not enter solver timing.
"""

import argparse
import json
import os
from pathlib import Path
import sys

from .arithmetic import require_sample, summarise
from .assessment import evidence
from .capture import digest, invoke, load_attempt, utc, write_json
from .compact import verify
from .contract import arguments


def state(source: Path, destination: Path) -> None:
    """Keep raw device readings and Linux counters, including unavailable fields."""
    invoke(["nvidia-smi", "--query-gpu=pstate,utilization.gpu,utilization.memory,temperature.gpu,clocks.sm,clocks.mem,power.draw,clocks_event_reasons.active",
            "--format=csv,noheader,nounits"], source, destination / "gpu", timeout=30, grace=5)
    write_json(destination / "linux.json", {"observed_utc": utc(),
        "cpu_counters": Path("/proc/stat").read_text(), "load": Path("/proc/loadavg").read_text(),
        "scope": "Linux counters only; not a complete view of Windows workload"})


def collect(work: Path, protocol: Path) -> dict:
    """Make one fresh collection; refuse existing output or changed implementations."""
    original = work / "results"
    campaign = json.loads((original / "campaign.json").read_bytes())
    verify(original, campaign)
    root = work / "confirmation"
    root.mkdir(exist_ok=False)
    (root / "protocol.md").write_bytes(protocol.read_bytes())
    write_json(root / "identity.json", {"prepared_utc": utc(), "protocol_sha256": digest(protocol.read_bytes()),
        "collector_sha256": digest(Path(__file__).read_bytes()), "implementations": campaign["implementations"],
        "original_summary_sha256": digest((original / "summary.json").read_bytes()),
        "reused_verification_sha256": digest((work / "verification/results.json").read_bytes())})
    result = {"experiment": "acceptance-inline-confirmation-v1"}
    env = dict(os.environ, XDG_CONFIG_HOME=str(root / "isolated-config"),
        MAELSTROM_SCENES_DIR=str(root / "isolated-scenes"), MAELSTROM_RUNS_DIR=str(root / "isolated-runs"))
    for n, side, name, relative in ((8000, 20, "primary", "controls/008000"),
                                    (110592, 48, "paired_large", "previous/110592")):
        _, reference = load_attempt(original / relative)
        samples = {v: [] for v in ("control", "candidate")}
        for i in range(6):
            label = "warmup" if i == 0 else f"sample-{i}"
            for variant in (("control", "candidate") if i % 2 else ("candidate", "control")):
                verify(original, campaign)
                selected = campaign["implementations"][variant]
                source = Path(selected["source_directory"])
                scene = (source / "scenes/falling-block-20.toml" if n == 8000 else
                         Path(campaign["baseline_directory"]) / f"inputs/scenes/capacity-block-{side:02}.toml")
                state(source, root / "telemetry" / name / variant / label / "before")
                kind = "warmup" if i == 0 else "sample"
                process, document = invoke([selected["binary"], *arguments(scene, "cuda", observation=n == 8000, kind=kind)],
                    source, root / name / variant / label, timeout=120, grace=30, env=env)
                state(source, root / "telemetry" / name / variant / label / "after")
                measured = require_sample(process, document, reference, selected["revision"], kind=kind)
                if i:
                    samples[variant].append(measured)
                print(f"{n} {variant} {label} complete", file=sys.stderr, flush=True)
        result[name] = {v: summarise(samples[v]) for v in samples}
    verify(original, campaign)
    result["performance_evidence"] = evidence(result["primary"], result["paired_large"])
    write_json(root / "summary.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(collect(args.work.resolve(), args.protocol.resolve()), indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError) as error:
        print(f"Acceptance confirmation: {error}", file=sys.stderr)
        raise SystemExit(1)
