"""Complete the independent timestep/iteration matrix using retained trajectories.

The production executable supplies throughput; the existing exact native replay
supplies sampled states for the independent physical audit. Reused measurements
keep their original identities and are never counted as fresh timing repeats.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

if __package__:
    from .frontier_campaign import run_case
    from .frontier_audit import audit
else:
    from frontier_campaign import run_case
    from frontier_audit import audit


def matrix():
    """Hold correction and regularisation fixed on both independent axes."""
    return [dict(id=f"hz{hz}-i{iterations}", dt=1/hz, iterations=iterations,
                 scale=.5, epsilon=2.)
            for hz in (120, 240, 480) for iterations in (2, 3, 4, 8)]


def same_policy(a, b):
    return all(a[k] == b[k] for k in ("dt", "iterations", "scale", "epsilon"))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")


def prepare(root, previous):
    """Create a new evidence root without writing through any previous run."""
    if root.exists():
        raise ValueError("evidence root already exists")
    old = json.loads((previous/"frontier.json").read_text())
    plan = []
    for scene in ("resolved", "large"):
        for policy in matrix():
            matches = [r for r in old if r["scene"] == scene
                       and not r["label"].startswith(("long-", "admission"))
                       and same_policy(r["policy"], policy)]
            if len(matches) > 1:
                raise ValueError("ambiguous retained trajectory")
            row = dict(scene=scene, policy=policy,
                       duration=2. if scene == "resolved" else 1.)
            if matches:
                source = previous/"runs"/matches[0]["label"]
                metrics = json.loads((source/"metrics.json").read_text())
                if not metrics["native_endpoint_equal"] or not metrics["completed"]:
                    raise ValueError("retained trajectory is incomplete")
                row.update(reused_from=str(source), summary=matches[0],
                           metrics_sha256=hashlib.sha256((source/"metrics.json").read_bytes()).hexdigest(),
                           production_json_sha256=metrics["production_json_sha256"])
            plan.append(row)
    root.mkdir(parents=True)
    for name in ("config", "scenes"):
        shutil.copytree(previous/name, root/name)
    shutil.copy2(previous/"scenes.json", root/"scenes.json")
    for name in ("target", "frontier-driver", "frontier-quality"):
        (root/name).symlink_to(previous/name, target_is_directory=name == "target")
    write_json(root/"matrix-plan.json", plan)
    write_json(root/"protocol.json", {
        "scope": "Independent numerical-work matrix; no production defaults or native kernels changed",
        "fixed": {"correction_scale": .5, "relaxation_scale": 2., "refine_timestep": 1},
        "reuse": "Five combinations per scene already covered. Preserve original measurements; run only seven missing combinations.",
        "practical": {"p95_compression": .05, "max_compression": .25,
                      "min_separation_over_dx": .5, "no_coincidences": True,
                      "contained_finite": True, "volume_proxy_error": .1,
                      "mechanical_energy_excess": .1},
        "strict_errors": "Hydrostatics, shear and convergence reported separately; historical failures retained.",
        "candidate_bound": "At most two stronger-correction/lower-regularisation policies after matrix, then one adaptive probe only if work elimination is plausible.",
        "sustained": "Five simulated seconds, 8000/110592 particles, 60 Hz observations, warmup then five alternating pairs; all samples retained.",
        "profiling": "Separate instrumented workload replay and CUDA trace; their clocks do not replace ordinary solver measurements."
    })


def screen(root):
    for row in json.loads((root/"matrix-plan.json").read_text()):
        if "reused_from" not in row:
            run_case(root, row["scene"], row["policy"], duration=row["duration"])


def candidates(root):
    # Restore the stronger response before asking whether fewer steps are usable.
    # This is a new declared policy, separate from the fixed-parameter matrix.
    for iterations in (4, 8):
        policy = dict(id=f"strong240-i{iterations}", dt=1/240,
                      iterations=iterations, scale=1., epsilon=.02)
        for scene in ("resolved", "large"):
            run_case(root, scene, policy, duration=2. if scene == "resolved" else 1.)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("phase", choices=("prepare", "screen", "candidates", "audit"))
    parser.add_argument("--previous", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.phase == "prepare":
        if args.previous is None:
            parser.error("prepare requires --previous")
        prepare(root, args.previous.resolve())
    else:
        {"screen": screen, "candidates": candidates, "audit": audit}[args.phase](root)


if __name__ == "__main__":
    main()
