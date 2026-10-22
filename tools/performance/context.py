"""Interpret CPU samples and external runs without admitting them as matched timings.

Sampling losses, different physics and rounded upstream counters stay visible in
the result. These observations guide investigation; they do not qualify a solver.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import re
import sqlite3
import sys

from .capture import digest, load_attempt, write_json
from .external import REVISION, position_bytes
from .neighbours import inspect


def external(directory: Path, count: int) -> dict:
    """Check imported geometry and fixed iteration work against original output."""
    package = directory / f"external/inputs/{count:06}"
    target = directory / f"external/runs/{count:06}"
    identity = json.loads((package / "identity.json").read_bytes())
    admission = json.loads((target / "input-admission.json").read_bytes())
    build = json.loads((directory / "external/build-identity.json").read_bytes())
    if (build["upstream_revision"] != REVISION
            or admission["comparator_sha256"] != build["binary_sha256"]):
        raise ValueError("external build identity differs")
    for name, key in (("particles.pts", "pts_sha256"), ("scene.json", "scene_sha256"),
                      ("box.obj", "geometry_sha256")):
        if digest((package / name).read_bytes()) != identity[key]:
            raise ValueError("external input changed")
    checked, points = load_attempt(target / "import-check")
    if (checked["exit_code"] != 0 or points is None or points["count"] != count
            or len(points["positions"]) != count
            or digest(position_bytes(points["positions"])) != identity["position_binary32_sha256"]
            or not admission["passed"] or admission["upstream_revision"] != REVISION):
        raise ValueError("external imported geometry disagrees")
    process, _ = load_attempt(target / "run")
    if process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]:
        raise ValueError("external run did not complete")
    text = gzip.decompress((target / "run/stdout.gz").read_bytes()).decode()

    def number(label: str) -> float:
        found = re.findall(r"^" + re.escape(label) + r": ([0-9.eE+-]+)(?: ms)?$", text, re.MULTILINE)
        if len(found) != 1:
            raise ValueError(f"missing or repeated external counter: {label}")
        return float(found[0])

    if number("Number of fluid particles") != count or number("Average number: PBF - iterations") != 8:
        raise ValueError("external particle/iteration request differs")
    iterations = number("Total number: PBF - iterations")
    if iterations != 3840:
        raise ValueError("external run did not perform 480 eight-iteration steps")
    solver = number("Time sum: SimStep") / 1000
    return {"particles": count, "boundary_particles": int(number("Number of boundary particles")),
            "steps_inferred_from_iteration_counters": int(iterations / 8), "iterations": int(iterations),
            "reported_simulated_s_rounded": number("Total number: Time step size"),
            "internal_simstep_s_rounded": solver, "invocation_s": process["wall_s"],
            "internal_pressure_s_rounded": number("Time sum: pressureSolve") / 1000,
            "internal_search_s_rounded": number("Time sum: neighborhood_search") / 1000,
            "input_coordinates_verified": True, "quality_equivalence_established": False,
            "observed_neighbour_counts": None,
            "timing_scope": "upstream SimStep; excludes boundary-simulator work, setup and output",
            "raw_stdout_sha256": process["stdout_sha256"]}


def cpu(directory: Path) -> dict:
    """Expose sample distribution and collection losses, not estimated wall shares."""
    database = directory / "cpu.sqlite"
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        total = connection.execute("SELECT count(*) FROM COMPOSITE_EVENTS").fetchone()[0]
        rows = connection.execute("SELECT s.value, count(*) AS n FROM COMPOSITE_EVENTS e "
            "JOIN SAMPLING_CALLCHAINS c ON c.id=e.id AND c.stackDepth=0 "
            "JOIN StringIds s ON s.id=c.symbol GROUP BY s.value ORDER BY n DESC LIMIT 20").fetchall()
        diagnostics = [row[0] for row in connection.execute("SELECT text FROM DIAGNOSTIC_EVENT")]
        waits = connection.execute("SELECT count(*), sum(a.end-a.start) FROM OSRT_API a "
            "JOIN StringIds s ON s.id=a.nameId WHERE s.value='futex'").fetchone()
    finally:
        connection.close()
    return {"raw_sqlite_sha256": digest(database.read_bytes()), "samples": total,
            "top_leaf_symbols": [{"symbol": name, "samples": n, "fraction_of_retained_samples": n / total}
                                 for name, n in rows],
            "futex_calls": waits[0], "aggregate_thread_futex_s": waits[1] / 1e9,
            "diagnostics": diagnostics,
            "limitation": "lost/throttled samples prevent precise cost shares; thread waits overlap and are not elapsed solver time"}


def analyse(directory: Path) -> dict:
    """Combine separately labelled contextual observations from retained processes."""
    counts = []
    for relative, states in (("capacity/008000/core", (True, False)),
                             ("capacity/032768/core", (True, False))):
        process, document = load_attempt(directory / relative)
        if document is None:
            raise ValueError("neighbour-count input is unavailable")
        for first in states:
            result = inspect(document, first_prediction=first)
            result.update(source_attempt=relative, source_stdout_sha256=process["stdout_sha256"])
            counts.append(result)
    return {"external": [external(directory, n) for n in (8000, 110592)],
            "cpu": cpu(directory / "timelines/threaded-8000-v2"), "neighbours": counts}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        write_json(args.output, analyse(args.directory.resolve()))
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"Context analysis: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
