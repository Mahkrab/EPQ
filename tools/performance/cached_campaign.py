"""Run alternating cached-playback controls from an isolated qualification directory.

The directory supplies control-maelstrom, candidate-maelstrom and cache32000.
Existing small and large caches are read from the previous cache-pipeline campaign.
No source checkout, installed binary or cache is overwritten.
"""
import argparse
import json
from pathlib import Path

from tools.performance.cached_playback import run


def campaign(root: Path, existing: Path, pairs: int, seconds: float):
    caches = {8000: existing / "runs/falling-block-20/b-1-cache",
              32000: root / "cache32000",
              110592: existing / "runs/large-impact/b-1-cache"}
    results = []
    for count, cache in caches.items():
        for pair in range(pairs):
            for width, height in [(1280, 720), (1920, 1080)]:
                for speed in [1, 4]:
                    for variant in (["control", "candidate"] if pair % 2 == 0 else ["candidate", "control"]):
                        name = f"{variant}-{count}-{height}-{speed}x-p{pair}"
                        if (root/name/"summary.json").exists():
                            result = json.loads((root/name/"summary.json").read_text())
                            results.append(dict(name=name, particles=count, variant=variant, **result))
                            continue
                        args = argparse.Namespace(binary=root/f"{variant}-maelstrom", cache=cache,
                                                  output=root/name, width=width, height=height,
                                                  speed=speed, seconds=seconds, terminal=5.000000260770321,
                                                  mode=None)
                        result = run(args)
                        results.append(dict(name=name, particles=count, variant=variant, **result))
                        (root/"playback-summary.json").write_text(json.dumps(results, indent=2)+"\n")
                        print(name, result["timeline_simulation_s_per_wall_s"], result["submissions_per_s"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--pairs", type=int, default=2)
    parser.add_argument("--seconds", type=float, default=8)
    args = parser.parse_args()
    campaign(args.root.resolve(), args.existing.resolve(), args.pairs, args.seconds)
