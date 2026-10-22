"""Prepare a pinned PBF comparator using the actual retained Maelstrom inputs.

Partio's PTS reader swaps Y and Z; compensate when writing and verify the result
through that library before timing. Shared geometry does not imply shared physics.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import sys

from .capture import digest, invoke, load_attempt, write_json

REVISION = "7586ffa25948c6ce3bc6c238cda30ad8d35f60a0"
BOX = """v -0.5 -0.5 0.5
v 0.5 -0.5 0.5
v -0.5 0.5 0.5
v 0.5 0.5 0.5
v -0.5 -0.5 -0.5
v 0.5 -0.5 -0.5
v -0.5 0.5 -0.5
v 0.5 0.5 -0.5
f 1 2 3
f 3 2 4
f 3 4 7
f 7 4 8
f 7 8 5
f 5 8 6
f 5 6 1
f 1 6 2
f 2 6 4
f 4 6 8
f 5 1 7
f 7 1 3
"""


def position_bytes(points: list[list[float]]) -> bytes:
    if any(len(point) != 3 or any(not math.isfinite(v) for v in point) for point in points):
        raise ValueError("expected finite three-component points")
    return b"".join(struct.pack("<fff", *point) for point in points)


def prepare(directory: Path) -> None:
    """Generate an input package, not an unverified upstream block-generator guess."""
    for count, relative in ((8000, "capacity/008000/pilot"), (110592, "capacity/110592/pilot")):
        process, document = load_attempt(directory / relative)
        if process["exit_code"] != 0 or document is None:
            raise ValueError("reference capacity input is unavailable")
        points = [[p["position_m"][axis] for axis in ("x", "y", "z")] for p in document["input"]["particles"]]
        if len(points) != count:
            raise ValueError("capacity input particle count differs")
        target = directory / f"external/inputs/{count:06}"
        target.mkdir(parents=True, exist_ok=False)
        with (target / "particles.pts").open("x") as stream:
            stream.write(f"{count}\n")
            for x, y, z in points:
                stream.write(f"{x:.17g} {z:.17g} {y:.17g}\n")
        (target / "box.obj").write_text(BOX)
        planes = document["input"]["planes"]
        # These generated fixtures have their positive bounds on planes 1/3/5.
        upper = [-planes[index]["offset_m"] for index in (1, 3, 5)]
        timestep = document["input"]["configuration"]["numerical"]["fixed_timestep_s"]
        scene = {"Configuration": {"particleRadius": 0.025, "simulationMethod": 2,
                    "gravitation": [0, -9.81, 0], "timeStepSize": timestep, "cflMethod": 0,
                    "kernel": 2, "gradKernel": 3, "boundaryHandlingMethod": 0,
                    "PBF": {"minIterations": 8, "maxIterations": 8, "maxError": 0.01, "velocityUpdateMethod": 0}},
                 "Materials": [{"id": "Fluid", "density0": 1000, "viscosityMethod": 0,
                                "surfaceTensionMethod": 0, "vorticityMethod": 0, "dragMethod": 0}],
                 "RigidBodies": [{"geometryFile": "box.obj", "translation": [v / 2 for v in upper],
                                  "rotationAxis": [1, 0, 0], "rotationAngle": 0, "scale": upper,
                                  "isDynamic": False, "isWall": True}],
                 "FluidModels": [{"id": "Fluid", "particleFile": "particles.pts", "translation": [0, 0, 0],
                                  "rotationAxis": [1, 0, 0], "rotationAngle": 0, "scale": [1, 1, 1]}]}
        write_json(target / "scene.json", scene)
        write_json(target / "identity.json", {"upstream_revision": REVISION, "particles": count,
                   "position_binary32_sha256": digest(position_bytes(points)), "source_attempt": relative,
                   "source_stdout_sha256": process["stdout_sha256"],
                   "pts_sha256": digest((target / "particles.pts").read_bytes()),
                   "scene_sha256": digest((target / "scene.json").read_bytes()),
                   "geometry_sha256": digest((target / "box.obj").read_bytes()),
                   "quality_equivalence": "not established; constraint, mass, boundary, arithmetic and timer differences remain"})


def collect(directory: Path, upstream: Path, checker: Path) -> None:
    """Admit imported coordinates, then retain one contextual fixed-work run per size."""
    binary = upstream / "bin/SPHSimulator"
    for count in (8000, 110592):
        package = directory / f"external/inputs/{count:06}"
        identity = json.loads((package / "identity.json").read_bytes())
        target = directory / f"external/runs/{count:06}"
        process, points = invoke([str(checker), str(package / "particles.pts")], upstream, target / "import-check")
        passed = (process["exit_code"] == 0 and points is not None and points["count"] == count
                  and digest(position_bytes(points["positions"])) == identity["position_binary32_sha256"])
        write_json(target / "input-admission.json", {"passed": passed, "checker_sha256": digest(checker.read_bytes()),
                   "comparator_sha256": digest(binary.read_bytes()), "upstream_revision": REVISION,
                   "initial_position_binary32_sha256": identity["position_binary32_sha256"]})
        if not passed:
            raise ValueError("actual Partio import disagrees with retained initial geometry")
        output = target / "application-output"
        command = ["env", "OMP_NUM_THREADS=12", "OMP_DYNAMIC=FALSE", str(binary),
                   "--no-gui", "--no-initial-pause", "--no-cache", "--stopAt", "1.0",
                   "--output-dir", str(output), str(package / "scene.json")]
        invoke(command, upstream, target / "run", timeout=120, grace=30)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "collect"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--upstream", type=Path)
    parser.add_argument("--checker", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "prepare":
            prepare(args.directory.resolve())
        else:
            if args.upstream is None or args.checker is None:
                raise ValueError("collect requires the pinned upstream directory and Partio checker")
            collect(args.directory.resolve(), args.upstream.resolve(), args.checker.resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"External comparison: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
