"""Compare completed CUDA steps with fresh fixed-resource CPU controls.

The baseline collector owns sampling and timeouts. Full compressed observations
retain the components needed to qualify every timing independently of its hash.
"""

from __future__ import annotations

import argparse
import gzip
from itertools import chain
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys

from tools.baseline import main as baseline
from tools.baseline.data import POLICY, clean, compact_result, read_json, sha256
from tools.baseline.scaling import ENVIRONMENT_FIELDS
from tools.cuda.compare import compare

CONTRACT = baseline.ROOT / "docs/project/development/milestones/03/measurement-protocol.md"
SETTINGS = (("serial-grid", None, None), ("threaded-grid", 12, None), ("cuda-grid", None, (0, 128)))


def full_result(directory: Path, attempt: dict) -> dict:
    """Check the retained component payload against its compact observation."""
    entry = attempt["full_result"]
    path = (directory / entry["file"]).resolve()
    if not path.is_relative_to(directory.resolve()) or sha256(path.read_bytes()) != entry["sha256"]:
        raise ValueError("full result hash or path differs")
    value = json.loads(gzip.decompress(path.read_bytes()))
    # Timings are binary64; do not use the physical binary32 comparator here.
    if compact_result(value) != attempt["result"]:
        raise ValueError("full and compact result disagree")
    return value


def lifecycle(attempts: list[dict], key: str) -> float | None:
    values = [a["result"]["measurements"][key] for a in attempts
              if a["kind"] == "sample" and clean(a)]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("invalid solver lifecycle elapsed time")
    return statistics.median(values) if len(values) == 3 else None


def report(directory: Path) -> tuple[dict, str]:
    """Recheck every complete component observation before admitting its totals."""
    campaign = read_json(directory / "campaign.json")
    names = [s[0] for s in SETTINGS]
    if (campaign["schema_version"] != 1 or campaign["policy"] != "cuda-comparison-v1"
            or campaign["collection_order"] != names):
        raise ValueError("unsupported CUDA measurement campaign")
    if sha256((directory / "protocol.md").read_bytes()) != campaign["protocol_sha256"]:
        raise ValueError("measurement protocol hash differs")
    datasets, attempts, full, comparisons = {}, {}, {}, {}
    first = None
    for name, workers, cuda in SETTINGS:
        path = directory / name
        baseline.report(path)
        d = read_json(path / "dataset.json")
        execution, identity = baseline.execution_settings("uniform-grid", workers, cuda)
        if d["backend"] != "uniform-grid" or d.get("execution", {"mode": "serial"}) != execution or d["interrupted"]:
            raise ValueError("series execution or completion differs")
        if first is None:
            first = d
        else:
            for field in ("source", "binary_sha256", "build_revision", "policy", "manifest", "manifest_sha256",
                          "collector_files_sha256", "epq_base_commit"):
                if d[field] != first[field]:
                    raise ValueError(f"series differ in {field}")
            for field in ENVIRONMENT_FIELDS:
                if d["environment"][field] != first["environment"][field]:
                    raise ValueError(f"series environment differs in {field}")
        values = baseline.load_attempts(path, d)
        keys = [(a["particles"], a["kind"], a["index"]) for a in values]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate sample identity")
        full[name] = {}
        correctness = read_json(path / "correctness.json")
        for a, key in zip(values, keys, strict=True):
            size, kind, index = key
            if (size not in POLICY["particles"] or kind not in ("warmup", "sample", "profile")
                    or index not in (range(1, 4) if kind == "sample" else [1])):
                raise ValueError("unexpected sample identity")
            if a.get("numerical_agreement") is False:
                raise ValueError("sample failed exact comparison")
            if a["result"] is not None:
                full[name][key] = a
        for document in chain([correctness], (full_result(path, a) for a in values if a["result"] is not None)):
            metadata = document["metadata"]
            if (document["backend"] != identity or metadata["backend"] != identity
                    or document.get("execution", {"mode": "serial"}) != execution
                    or metadata["debug_assertions"] or metadata["build_revision"] != d["build_revision"]):
                raise ValueError("result execution/build context differs")
            if (metadata.get("device") != (campaign["device"] if cuda is not None else None)):
                raise ValueError("result device differs")
        golden_case = d["manifest"]["cases"][1]
        golden = baseline.SIMULATOR / golden_case["golden"]
        if sha256(golden.read_bytes()) != golden_case["golden_sha256"]:
            raise ValueError("frozen golden hash differs")
        agreement = compare(read_json(golden), correctness, exact=True)
        comparisons[f"{name}/correctness"] = agreement
        if not agreement["passed"]:
            raise ValueError(f"{name}: correctness result differs from golden: {json.dumps(agreement)}")
        datasets[name], attempts[name] = d, values
    rows = []
    for i, size in enumerate(POLICY["particles"]):
        controls = [a for a in attempts["serial-grid"] if a["particles"] == size and a["kind"] == "warmup" and clean(a)]
        reference = full_result(directory / "serial-grid", controls[0]) if len(controls) == 1 else None
        primaries = {}
        size_rows = []
        for name in names:
            values = [a for a in attempts[name] if a["particles"] == size]
            checked = 0
            for a in values:
                if clean(a) and reference is not None:
                    key = (size, a["kind"], a["index"])
                    agreement = compare(reference, full_result(directory / name, full[name][key]), exact=True)
                    label = f"{name}/{size}/{a['kind']}/{a['index']}"
                    comparisons[label] = agreement
                    if not agreement["passed"]:
                        raise ValueError(f"{label}: component comparison failed: {json.dumps(agreement)}")
                    checked += 1
            summary = datasets[name]["summaries"][i]
            primary = summary["primary"] if reference is not None else None
            primaries[name] = primary
            samples = [a["wall_s"] for a in values if a["kind"] == "sample" and clean(a)]
            size_rows.append({"particles": size, "series": name, "exact_complete_attempts": checked,
                              "primary": primary, "profile": summary["profile"],
                              "invocation_median_s": statistics.median(samples) if primary else None,
                              "solver_construction_median_s": lifecycle(values, "solver_construction_s"),
                              "solver_teardown_median_s": lifecycle(values, "solver_teardown_s")})
        gpu = primaries["cuda-grid"]
        for row in size_rows:
            row["speedup_against_cuda"] = row["primary"]["median_s"] / gpu["median_s"] if row["primary"] and gpu else None
        rows.extend(size_rows)
    result = {"schema_version": 1, "acceptance": "exact-binary32-including-signed-zero",
              "datasets_sha256": {n: sha256((directory / n / "dataset.json").read_bytes()) for n in names},
              "comparisons": comparisons, "rows": rows}
    text = ["# Completed CUDA and CPU solver comparison", "",
            "Fixed settings: serial grid, twelve CPU workers, CUDA device 0 / 128 lanes. Same release binary.",
            "Ratios divide each fresh CPU median by the CUDA median. Values below one mean CUDA is slower.",
            "Exact component checks qualify all admitted observations. No fresh brute-force ratio is available.", "",
            "| Particles | Series | Solver median (s) | Min–max (s) | Invocation median (s) | Construction median (s) | Teardown median (s) | CPU/CUDA |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in rows:
        p = r["primary"]
        timing = f"{p['median_s']:.6f} | {p['minimum_s']:.6f}–{p['maximum_s']:.6f}" if p else "unavailable | unavailable"
        fmt = lambda v: f"{v:.6f}" if v is not None else "unavailable"
        text.append(f"| {r['particles']:,} | {r['series']} | {timing} | {fmt(r['invocation_median_s'])} | {fmt(r['solver_construction_median_s'])} | {fmt(r['solver_teardown_median_s'])} | {fmt(r['speedup_against_cuda'])} |")
    text += ["", "Per-series reports retain throughput, spread, synchronised host stage profiles and residuals.",
             "Setup and teardown remain outside completed-step totals; first-step buffer allocations remain inside.",
             "Invocation includes audits, output and process costs. Profiles are not isolated device timings.",
             "Fixed order, shared host load, thermals and scheduling remain uncontrolled; three samples show observed spread.",
             "Memory use, bandwidth and utilisation were not measured. No tuning or numerical changes were made."]
    return result, "\n".join(text) + "\n"


def collect(directory: Path) -> None:
    """Freeze the protocol and build once before sequential independent invocations."""
    if directory.exists():
        raise FileExistsError(directory)
    if os.environ.get("MAELSTROM_CUDA_ARCH", "89") != "89":
        raise ValueError("the declared comparison requires MAELSTROM_CUDA_ARCH=89")
    build = baseline.prepare_build(cuda=True)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "protocol.md").write_bytes(CONTRACT.read_bytes())
    binary = baseline.SIMULATOR / "target/release/maelstrom"
    probe = baseline.invoke([str(binary), "cuda-check", "--device", "0", "--format", "json"])
    baseline.write_json(directory / "device-probe.json", probe)
    if probe["exit_code"] != 0 or probe["timed_out"] or probe["interrupted"] or probe["result"] is None:
        raise ValueError("device probe failed; retained device-probe.json")
    toolkit = Path(os.environ.get("CUDA_HOME", "/usr/local/cuda"))
    context = {"nvcc": baseline.command_output([str(toolkit / "bin/nvcc"), "--version"]),
               "cxx": baseline.command_output([os.environ.get("CXX", "c++"), "--version"]),
               "ar": baseline.command_output([os.environ.get("AR", "ar"), "--version"]),
               "gpu": baseline.command_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,compute_cap", "--format=csv,noheader"]),
               "build": "cargo build --release --locked --offline --features cuda",
               "cuda_home": str(toolkit), "target": "89",
               "native_flags": {"nvcc": "--ptx --std=c++17 --gpu-architecture=compute_89 -O3 --fmad=false --ftz=false --prec-div=true --prec-sqrt=true",
                                "bridge": "-std=c++17 -O2 -fPIC -Wall -Wextra -Werror"},
               "cuda_environment": {k: os.environ.get(k) for k in ("CUDA_VISIBLE_DEVICES", "CUDA_CACHE_DISABLE", "CUDA_CACHE_PATH", "CUDA_FORCE_PTX_JIT", "CUDA_MODULE_LOADING", "CXX", "AR")},
               "ptx_sha256": {str(p.relative_to(baseline.SIMULATOR)): sha256(p.read_bytes())
                              for p in sorted((baseline.SIMULATOR / "target/release/build").glob("maelstrom-*/out/roundtrip.ptx"))}}
    files = [CONTRACT, *sorted((baseline.ROOT / "tools/cuda").glob("*.py")),
             *sorted((baseline.ROOT / "tools/baseline").glob("*.py"))]
    campaign = {"schema_version": 1, "policy": "cuda-comparison-v1", "started_utc": baseline.now(),
                "collection_order": [s[0] for s in SETTINGS], "device": probe["result"]["report"]["device"],
                "protocol_sha256": sha256(CONTRACT.read_bytes()), "context": context,
                "collector_files_sha256": {str(p.relative_to(baseline.ROOT)): sha256(p.read_bytes()) for p in files}}
    baseline.write_json(directory / "campaign.json", campaign)
    for name, workers, cuda in SETTINGS:
        baseline.collect(directory / name, "uniform-grid", workers, build=build, cuda=cuda, retain_full_results=True)
        if read_json(directory / name / "dataset.json")["interrupted"]:
            raise ValueError("collection interrupted; no later series started")
    if any(sha256((baseline.ROOT / name).read_bytes()) != expected
           for name, expected in campaign["collector_files_sha256"].items()):
        raise ValueError("collector or protocol changed during collection")
    result, text = report(directory)
    baseline.write_json(directory / "comparison.json", result)
    (directory / "report.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("collect", "report"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "collect":
            collect(args.directory.resolve())
        else:
            result, text = report(args.directory.resolve())
            if result != read_json(args.directory / "comparison.json"):
                raise ValueError("stored comparison differs from recomputed evidence")
            print(text, end="")
    except (OSError, ValueError, KeyError, TypeError, EOFError, subprocess.SubprocessError) as error:
        print(f"CUDA performance: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
