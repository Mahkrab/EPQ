"""Hydrostatic falsification and neighbour-refresh checks after the first screen."""
from __future__ import annotations

import json
from pathlib import Path
import struct
import sys

from tools.performance.physical_accuracy import LAYOUT, encode, execute, lattice_rest


def main(root: Path) -> None:
    raw = (root / "inputs/8000.bin").read_bytes()
    values = list(LAYOUT.unpack_from(raw))
    points = [(.025+.05*x,.025+.05*y,.025+.05*z)
              for x in range(20) for y in range(8) for z in range(20)]
    n = len(points)
    values[:3] = [n,4096,6]
    planes = (1,0,0,0,-1,0,0,-1,0,1,0,0,0,-1,0,-1,0,0,1,0,0,0,-1,-1)
    raw = (LAYOUT.pack(*values)+b"".join(struct.pack("<3f",*p) for p in points)
           + bytes(n*12)+struct.pack("<24f",*planes))
    (root / "inputs/hydro.bin").write_bytes(raw)
    cases = [("signed", "control", 1/480, .0625, 20, .1, 8),
             ("strong", "control", 1/480, 1, 20, .1, 8),
             ("clamp480", "clamp", 1/480, .5, 2, .1, 8),
             ("clamp240", "clamp", 1/240, .5, 2, .1, 4),
             ("clamp960", "clamp", 1/960, .5, 2, .1, 8),
             ("no-pressure240", "clamp", 1/240, .5, 2, 0, 4),
             ("no-pressure480", "clamp", 1/480, .5, 2, 0, 4)]
    results = {}
    for label, variant, dt, scale, eps, pressure, it in cases:
        label = "hydro-"+label
        inp = root / "inputs" / (label+".bin")
        inp.write_bytes(encode(raw,dt=dt,scale=scale,epsilon=eps,pressure=pressure))
        prefix = root / "states" / label
        steps = round(5/dt)
        request = execute([str(root/variant/"driver"),str(inp),str(steps),str(it),
                           "checked",str(prefix),"1","0"],root/"requests"/(label+".json"))
        health = {}
        for step in (0, round(1/dt), steps):
            snap = Path(str(prefix)+f"-{step}.bin")
            if not snap.exists():
                continue
            record = execute([str(root/"quality"),str(snap),str(n),str(values[5]),
                              str(values[6]),"1,1,1","none"],root/"health"/(snap.stem+".json"))
            h = json.loads(record["stdout"])
            p = list(struct.iter_unpack("<3f",snap.read_bytes()[:n*12]))
            # Full-width tank: M/(rho0*A) is the independent hydrostatic depth.
            expected_height = n*values[12]/1000
            mean_height = sum(a[1] for a in p)/n
            h["hydrostatic"] = {"expected_depth_m":expected_height,
                "mean_height_m":mean_height,
                "centroid_relative_error":abs(mean_height-expected_height/2)/(expected_height/2),
                "maximum_height_m":max(a[1] for a in p),
                "depth_from_centroid_m":2*mean_height}
            health[str(step)] = h
        results[label] = {"parameters":{"dt":dt,"scale":scale,"epsilon":eps,"pressure":pressure},
                          "iterations":it,"metrics":json.loads(request["stdout"]) if request["exit_code"]==0 else request,
                          "health":health}
        (root/"hydro.json").write_text(json.dumps(results,indent=2)+"\n")
        print(label, health.get(str(steps),{}).get("hydrostatic"),flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
