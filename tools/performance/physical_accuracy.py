"""Controlled numerical experiments on disposable exports of the CUDA solver.

The native driver's timing excludes the production acceptance API. Inputs retain
the inspected transfer layout; changing a primary parameter also updates its
dependent kernel constants. No installed defaults or simulator source are edited.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import subprocess

LAYOUT = struct.Struct("<4I12fd2IQ2f")


def lattice_rest(dx: float, h: float) -> float:
    """Independent binary64 infinite-lattice Poly6 density, including self."""
    extent = math.ceil(h / dx)
    return sum(315 / (64 * math.pi * h**9) * (h*h - dx*dx*(x*x+y*y+z*z))**3
               for x in range(-extent, extent+1)
               for y in range(-extent, extent+1)
               for z in range(-extent, extent+1) if dx*dx*(x*x+y*y+z*z) < h*h)


def encode(source: bytes, *, dt: float, scale: float, epsilon: float = 20,
           pressure: float = .1, ratio: float = 2) -> bytes:
    """Vary independent controls at fixed spacing 0.05 m and rest density 1000."""
    values = list(LAYOUT.unpack_from(source))
    h = values[5] if ratio == 2 else .05 * ratio
    rest = values[6] if ratio == 2 else lattice_rest(.05, h)
    reference = values[9] if ratio == 2 else 315 / (64 * math.pi * h**9) * (h*h-(.2*h)**2)**3
    relaxation = values[7] if ratio == 2 and epsilon == 20 else epsilon / h**2
    values[4:12] = [dt, h, rest, relaxation, pressure * h**2,
                    reference, 4, scale]
    values[12] = 1000 / rest
    return LAYOUT.pack(*values) + source[LAYOUT.size:]


def execute(command: list[str], destination: Path, timeout: int = 300) -> dict:
    """Retain failed requests as well as successful measurements."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        record = {"command": command, "exit_code": result.returncode,
                  "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        record = {"command": command, "exit_code": None, "timeout_s": timeout,
                  "stdout": str(error.stdout), "stderr": str(error.stderr)}
    destination.write_text(json.dumps(record, indent=2) + "\n")
    return record


def campaign(root: Path, phase: str) -> None:
    """Screen one control at a time before spending work on larger scenes."""
    cases = []
    if phase == "screen":
        for scale in (.0625, .125, .25, .5, 1):
            cases.append((f"s{scale}", dict(scale=scale), 8, "control"))
        for eps in (.2, 2, 200):
            cases.append((f"eps{eps}", dict(scale=.25, epsilon=eps), 8, "control"))
        for dt in (1/120, 1/240, 1/960):
            cases.append((f"dt{round(1/dt)}", dict(scale=.25, dt=dt), 8, "control"))
        for it in (3, 4, 16, 32):
            cases.append((f"iter{it}", dict(scale=.25), it, "control"))
        for ratio in (1.5, 2.5):
            cases.append((f"h{ratio}", dict(scale=.25, ratio=ratio), 8, "control"))
        cases += [("no-pressure", dict(scale=.25, pressure=0), 8, "control"),
                  ("clamp", dict(scale=.25), 8, "clamp"),
                  ("clamp-low-eps", dict(scale=.5, epsilon=2), 8, "clamp"),
                  ("refresh", dict(scale=.25), 8, "refresh")]
        scenes = ("8000",)
    else:
        cases = [("baseline", dict(scale=.0625), 8, "control"),
                 ("strong", dict(scale=1), 8, "control"),
                 ("clamp-low-eps", dict(scale=.5, epsilon=2), 8, "clamp"),
                 ("clamp-coarse", dict(scale=.5, epsilon=2, dt=1/240), 4, "clamp")]
        scenes = ("1000", "8000", "110592", "collision", "settled")
    summary = {}
    for scene in scenes:
        raw = (root / "inputs" / f"{scene}.bin").read_bytes()
        count = LAYOUT.unpack_from(raw)[0]
        planes = struct.unpack_from("<24f", raw, LAYOUT.size + count*24)
        upper = ",".join(str(-planes[k*4+3]) for k in (1, 3, 5))
        for label, parameters, iterations, variant in cases:
            label = scene + "-" + label
            parameters = dict(dt=1/480) | parameters
            input_file = root / "inputs" / (label + ".bin")
            input_file.write_bytes(encode(raw, **parameters))
            prefix = root / "states" / label
            prefix.parent.mkdir(exist_ok=True)
            steps = round(5 / parameters["dt"])
            record = execute([str(root / variant / "driver"), str(input_file), str(steps),
                              str(iterations), "checked", str(prefix), "1", "0"],
                             root / "requests" / (label + ".json"))
            metrics = json.loads(record["stdout"]) if record["exit_code"] == 0 else None
            health = {}
            if metrics:
                for snapshot in sorted(prefix.parent.glob(label + "-*.bin")):
                    if snapshot.name.endswith("rows.bin"):
                        continue
                    request = execute([str(root / "quality"), str(snapshot), str(count),
                                       str(parameters.get("ratio", 2)*.05),
                                       str(lattice_rest(.05, parameters.get("ratio", 2)*.05)), upper, "none"],
                                      root / "health" / (snapshot.stem + ".json"))
                    health[snapshot.stem] = json.loads(request["stdout"]) if request["exit_code"] == 0 else request
            summary[label] = {"parameters": parameters, "iterations": iterations,
                              "variant": variant, "metrics": metrics, "health": health}
            (root / (phase + ".json")).write_text(json.dumps(summary, indent=2) + "\n")
            print(label, metrics["solver_s"] if metrics else record["stderr"], flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("phase", choices=("screen", "validate"))
    args = parser.parse_args()
    campaign(args.root, args.phase)


if __name__ == "__main__":
    main()
