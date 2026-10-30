"""Binary64 all-pairs PBF oracle independent of device kernels and grid search.

Small fixtures deliberately use direct summation and elementary kernel formulae.
Spiky is a substituted direction, not the derivative of the Poly6 constraint.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import struct
import sys

from tools.performance.physical_accuracy import LAYOUT, execute, lattice_rest


def stage(points: list[tuple[float, ...]], h: float, rest: float,
          epsilon: float, pressure: float, scale: float) -> tuple[list, dict]:
    gradients, constraints, denominators = [], [], []
    for i, p in enumerate(points):
        row = []
        density = 0.0
        for j, q in enumerate(points):
            d = tuple(a-b for a, b in zip(p, q))
            r = math.sqrt(sum(x*x for x in d))
            if r < h:
                density += 315/(64*math.pi*h**9)*(h*h-r*r)**3
            g = tuple(-45/(math.pi*h**6)*(h-r)**2*x/r/rest for x in d) if 0 < r < h else (0.,)*3
            row.append(g)
        owner = [sum(g[k] for g in row) for k in range(3)]
        denominators.append(sum(x*x for g in row for x in g)+sum(x*x for x in owner))
        constraints.append(density/rest-1)
        gradients.append(row)
    lam = [-c/(d+epsilon) for c, d in zip(constraints, denominators)]
    result = []
    for i, p in enumerate(points):
        delta = [0.]*3
        for j, q in enumerate(points):
            r2 = sum((a-b)**2 for a, b in zip(p, q))
            scorr = -pressure*((max(0., h*h-r2)/(h*h-(.2*h)**2))**3)**4
            for k in range(3):
                delta[k] += (lam[i]+lam[j]+scorr)*gradients[i][j][k]
        result.append(tuple(p[k]+scale*delta[k] for k in range(3)))
    ordered = sorted(max(0., c) for c in constraints)
    return result, {"compression_p95": ordered[int(.95*(len(ordered)-1))],
                    "mean_squared_constraint": sum(c*c for c in constraints)/len(points),
                    "gradient_denominator_min": min(denominators),
                    "gradient_denominator_max": max(denominators),
                    "regularisation_fraction_min": min(epsilon/(epsilon+d) for d in denominators),
                    "regularisation_fraction_max": max(epsilon/(epsilon+d) for d in denominators)}


def main(root: Path) -> None:
    source = (root / "inputs/1000.bin").read_bytes()
    values = list(LAYOUT.unpack_from(source))
    points = [tuple(struct.unpack("<f", struct.pack("<f", .3+.045*a))[0] for a in (x,y,z))
              for x in range(4) for y in range(4) for z in range(4)]
    values[0:3] = [64,64,0]
    values[13:16] = [0,0,0]
    raw = LAYOUT.pack(*values)+b"".join(struct.pack("<3f", *p) for p in points)+bytes(64*12)
    fixture = root / "oracle.bin"
    fixture.write_bytes(raw)
    checks = {}
    for iterations in (1, 8, 32):
        expected = points
        trace = []
        for _ in range(iterations):
            expected, metrics = stage(expected, values[5], values[6], values[7], values[8], values[11])
            trace.append(metrics)
        prefix = root / f"oracle-{iterations}"
        request = execute([str(root / "control/driver"), str(fixture), "1", str(iterations),
                           "checked", str(prefix), "0", "0"], root / f"oracle-request-{iterations}.json")
        if request["exit_code"] != 0:
            raise RuntimeError(request["stderr"])
        actual = list(struct.iter_unpack("<3f", Path(str(prefix)+"-1.bin").read_bytes()[:64*12]))
        error = max(abs(a-b) for p, q in zip(actual, expected) for a, b in zip(p,q))
        checks[str(iterations)] = {"maximum_position_error_m": error, "trace": trace}
    # Numerical Poly6 derivative and substituted Spiky differ even for one pair.
    h, r, rest = .1,.05,lattice_rest(.05,.1)
    poly_derivative = -6*315/(64*math.pi*h**9)*r*(h*h-r*r)**2/rest
    spiky = -45/(math.pi*h**6)*(h-r)**2/rest
    checks["analytic"] = {"lattice_rest_per_m3": rest, "mass_kg": 1000/rest,
                           "mass_to_rho_dx_cubed": 1/(rest*.05**3),
                           "poly6_derivative_per_m": poly_derivative, "spiky_per_m": spiky,
                           "spiky_to_poly6": spiky/poly_derivative}
    (root / "oracle.json").write_text(json.dumps(checks, indent=2)+"\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
