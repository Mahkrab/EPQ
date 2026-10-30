"""Collect the frozen serial workload without putting orchestration inside solver timers.

The retained dataset identifies the local build and preserves failed attempts.
Collection requires a new directory; reporting can be repeated from raw JSON.
Run from the repository root as ``python3 -m tools.baseline.main``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

from .data import (
    BACKENDS, POLICY, clean, compact_result, correctness_observations, markdown, numerical_document,
    physical_document, read_json,
    require_exact, sha256, summarise, timing_totals,
)

ROOT = Path(__file__).resolve().parents[2]
SIMULATOR = ROOT / "Maelstrom"
PROTOCOL = ROOT / "docs/project/development/milestones/00/measurement-protocol.md"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def command_output(args: list[str], cwd: Path = SIMULATOR) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, timeout=60).strip()


def write_json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def source_identity() -> dict:
    """Identify actual worktree bytes, including new non-ignored source files."""
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=SIMULATOR, timeout=60,
    ).decode().split("\0")
    hashes = {name: sha256((SIMULATOR / name).read_bytes()) for name in sorted(set(names))
              if name and (SIMULATOR / name).is_file()}
    return {
        "base_commit": command_output(["git", "rev-parse", "HEAD"]),
        "worktree_status": command_output(["git", "status", "--short"]),
        "files_sha256": hashes,
        "tree_sha256": sha256(json.dumps(hashes, sort_keys=True).encode()),
    }


def checked_manifest() -> dict:
    manifest = read_json(SIMULATOR / "reference/manifest.json")
    if manifest["schema_version"] != 1 or manifest["family"] != "falling-block-refined-v1":
        raise ValueError("unsupported frozen family")
    if [c["particles"] for c in manifest["cases"][1:]] != POLICY["particles"]:
        raise ValueError("manifest and measurement size sequence disagree")
    files = [(manifest["configuration"], manifest["configuration_sha256"])]
    for case in manifest["cases"]:
        files.append((case["scene"], case["sha256"]))
        if case["golden"]:
            files.append((case["golden"], case["golden_sha256"]))
    for name, expected in files:
        path = (SIMULATOR / name).resolve()
        # The manifest keeps its historical paths and hashes; catalogue examples
        # now live separately from these byte-preserved regression fixtures.
        if name.startswith("scenes/") and not path.exists():
            path = (SIMULATOR / "reference" / name).resolve()
        if not path.is_relative_to(SIMULATOR) or sha256(path.read_bytes()) != expected:
            raise ValueError(f"frozen input/golden hash mismatch: {name}")
    for case in manifest["cases"][1:]:
        if case["steps"] != POLICY["steps"] or case["checkpoints"] != POLICY["checkpoints"] or case["refine_timestep"] != 4:
            raise ValueError("manifest and measurement request disagree")
    return manifest


def environment() -> dict:
    cpu = Path("/proc/cpuinfo").read_text(encoding="utf-8")
    model = next(line.split(":", 1)[1].strip() for line in cpu.splitlines() if line.startswith("model name"))
    release = platform.freedesktop_os_release()
    memory = Path("/proc/meminfo").read_text(encoding="utf-8").splitlines()
    return {
        "cpu_model": model, "architecture": platform.machine(), "kernel": platform.release(),
        "os_release": release.get("PRETTY_NAME", "unavailable"),
        "cpu_topology": command_output(["lscpu", "--json"]),
        "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "memory_context": [line for line in memory if line.startswith(("MemTotal:", "MemAvailable:"))],
        "python": platform.python_version(), "rustc": command_output(["rustc", "-Vv"]),
        "cargo": command_output(["cargo", "-V"]), "profile": "release",
        "rustflags": "", "scheduling_controls": "none applied; inherited affinity recorded",
        "virtualisation": "WSL2" if "microsoft" in platform.release().lower() else "see cpu_topology",
    }


def invoke(args: list[str], timeout_s: float = POLICY["timeout_s"], grace_s: float = POLICY["cancellation_grace_s"]) -> dict:
    """Bound an invocation, requesting publication of partial state before killing it."""
    started = now()
    start = time.monotonic()
    timed_out = False
    interrupted = False
    process = subprocess.Popen(args, cwd=SIMULATOR, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        timed_out = isinstance(error, subprocess.TimeoutExpired)
        interrupted = isinstance(error, KeyboardInterrupt)
        process.send_signal(signal.SIGINT)
        try:
            stdout, stderr = process.communicate(timeout=grace_s)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
    result = None
    parse_error = None
    if stdout:
        try:
            result = json.loads(stdout)
            if not isinstance(result, dict):
                raise ValueError("result must be an object")
        except (ValueError, UnicodeDecodeError) as error:
            result = None
            parse_error = str(error)
    return {
        "started_utc": started, "finished_utc": now(), "wall_s": time.monotonic() - start,
        "exit_code": process.returncode, "timed_out": timed_out, "interrupted": interrupted,
        "stderr": stderr.decode("utf-8", errors="replace"), "parse_error": parse_error,
        "stdout_sha256": sha256(stdout), "result": result,
    }


def execution_settings(backend: str, workers: int | None, cuda: tuple[int, int] | None = None) -> tuple[dict, str]:
    """Resolve explicit resources without changing historical serial identities."""
    if backend not in BACKENDS:
        raise ValueError("unsupported search backend")
    if cuda is not None:
        device, threads = cuda
        if (backend != "uniform-grid" or workers is not None or type(device) is not int
                or device < 0 or device > 0xffffffff or type(threads) is not int
                or threads not in (32, 64, 128, 256)):
            raise ValueError("CUDA requires uniform-grid, a u32 device, 32/64/128/256 lanes and no workers")
        return {"mode": "cuda", "device": device, "threads": threads}, "cuda-uniform-grid-pbf-binary32-8-jacobi-v1"
    if workers is None:
        return {"mode": "serial"}, BACKENDS[backend]
    if backend != "uniform-grid" or type(workers) is not int or not 1 <= workers <= 256:
        raise ValueError("threaded uniform-grid workers must be in 1..=256")
    return {"mode": "threaded", "workers": workers}, "threaded-uniform-grid-pbf-binary32-8-jacobi-v2"


def solver_args(binary: Path, case: dict, kind: str, backend: str = "brute-force",
                workers: int | None = None, cuda: tuple[int, int] | None = None) -> list[str]:
    execution_settings(backend, workers, cuda)
    args = [str(binary), "run", case["scene"], "--unpaced", "--backend", backend, "--steps", str(case["steps"]),
            "--refine-timestep", str(case["refine_timestep"]), "--checkpoints",
            ",".join(str(s) for s in case["checkpoints"]), "--format", "json", "--quiet"]
    if workers is not None:
        args += ["--execution", "threaded", "--threads", str(workers)]
    if cuda is not None:
        args += ["--execution", "cuda", "--device", str(cuda[0]), "--block-size", str(cuda[1])]
    if kind != "warmup":
        args.append("--measure")
    if kind == "profile":
        args.append("--stage-profile")
    return args


def load_attempts(directory: Path, dataset: dict) -> list[dict]:
    attempts = []
    for entry in dataset["raw"]:
        path = (directory / entry["file"]).resolve()
        if not path.is_relative_to(directory.resolve()) or sha256(path.read_bytes()) != entry["sha256"]:
            raise ValueError("raw sample is missing, changed or outside the dataset")
        attempts.append(read_json(path))
    return attempts


def report(directory: Path) -> str:
    dataset = read_json(directory / "dataset.json")
    if dataset["schema_version"] != 1 or dataset["policy"] != POLICY:
        raise ValueError("dataset policy/version is not supported")
    if not dataset["source_unchanged"] or not dataset["binary_unchanged"]:
        raise ValueError("source or binary changed during collection")
    correctness = directory / "correctness.json"
    if sha256(correctness.read_bytes()) != dataset["correctness"]["result_sha256"]:
        raise ValueError("correctness result hash mismatch")
    if correctness_observations(read_json(correctness)) != dataset["correctness"]["observations"]:
        raise ValueError("correctness observations disagree with retained result")
    rows = summarise(load_attempts(directory, dataset))
    if rows != dataset["summaries"]:
        raise ValueError("stored summaries disagree with raw samples")
    return markdown(dataset, rows)


def prepare_build(*, cuda: bool = False) -> dict:
    """Build once so all execution settings can use identical source and binary bytes."""
    if sys.platform != "linux":
        raise ValueError("environment collection currently requires Linux /proc and lscpu")
    prohibited = [key for key, value in os.environ.items() if value and (
        key in {"RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CARGO_BUILD_TARGET", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "RUSTC", "CARGO_TARGET_DIR"}
        or key.startswith(("CARGO_PROFILE_", "CARGO_TARGET_")))]
    if prohibited:
        raise ValueError("baseline requires default build settings; unset " + ", ".join(sorted(prohibited)))
    source = source_identity()
    binary = SIMULATOR / "target/release/maelstrom"
    label = source["base_commit"] + "+worktree-sha256:" + source["tree_sha256"]
    build_env = dict(os.environ, MAELSTROM_BUILD_REVISION=label)
    arguments = ["cargo", "build", "--release", "--locked", "--offline"]
    if cuda:
        arguments += ["--features", "cuda"]
    subprocess.run(arguments, cwd=SIMULATOR,
                   env=build_env, check=True, timeout=300)
    return {"source": source, "label": label, "binary_sha256": sha256(binary.read_bytes())}


def collect(directory: Path, backend: str = "brute-force", workers: int | None = None,
            *, build: dict | None = None, cuda: tuple[int, int] | None = None,
            retain_full_results: bool = False) -> None:
    execution, identity = execution_settings(backend, workers, cuda)
    manifest = checked_manifest()
    if directory.exists():
        raise FileExistsError(directory)
    if build is None:
        build = prepare_build(cuda=True) if cuda is not None else prepare_build()
    source, label = build["source"], build["label"]
    binary = SIMULATOR / "target/release/maelstrom"
    if source_identity() != source or sha256(binary.read_bytes()) != build["binary_sha256"]:
        raise ValueError("prepared source or binary changed before collection")
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "raw").mkdir()
    tool_hashes = {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes())
                   for path in [PROTOCOL, *sorted(Path(__file__).parent.glob("*.py"))]}
    dataset = {
        "schema_version": 1, "backend": backend, "policy": POLICY, "started_utc": now(), "environment": environment(),
        "epq_base_commit": command_output(["git", "rev-parse", "HEAD"], ROOT),
        "source": source, "collector_files_sha256": tool_hashes,
        "build_revision": label, "binary_sha256": sha256(binary.read_bytes()),
        "manifest": manifest, "manifest_sha256": sha256((SIMULATOR / "reference/manifest.json").read_bytes()),
        "raw": [], "correctness": {}, "interrupted": False,
    }
    if workers is not None or cuda is not None:
        dataset["execution"] = execution
    write_json(directory / "collection.json", dataset)
    attempts = []
    # Preserve a full replayable correctness result before compacting performance samples.
    correctness = invoke(solver_args(binary, manifest["cases"][1], "warmup", backend, workers, cuda))
    result = correctness["result"]
    if correctness["exit_code"] != 0 or correctness["timed_out"] or result is None:
        write_json(directory / "correctness-failure.json", correctness)
        raise ValueError("correctness request failed; retained correctness-failure.json")
    golden = read_json(SIMULATOR / manifest["cases"][1]["golden"])
    if (result["backend"] != identity or result["metadata"]["backend"] != identity
            or result.get("execution", {"mode": "serial"}) != execution):
        write_json(directory / "correctness-failure.json", correctness)
        raise ValueError("correctness request returned the wrong backend")
    try:
        require_exact(physical_document(result, ignore_execution=True), physical_document(golden, ignore_execution=True))
    except ValueError:
        write_json(directory / "correctness-failure.json", correctness)
        raise
    write_json(directory / "correctness.json", result)
    dataset["correctness"] = {
        "golden_exact": True, "result_sha256": sha256((directory / "correctness.json").read_bytes()),
        "observations": correctness_observations(result),
        "invocation": {key: value for key, value in correctness.items() if key != "result"},
    }
    identities = {}
    warmup_documents = {}
    for case in manifest["cases"][1:]:
        def attempt(kind: str, index: int) -> dict:
            print(f"{case['particles']} particles: {kind} {index}", file=sys.stderr, flush=True)
            args = solver_args(binary, case, kind, backend, workers, cuda)
            value = invoke(args)
            value.update(particles=case["particles"], kind=kind, index=index,
                         arguments=args[1:])
            if value["result"] is not None:
                metadata = value["result"]["metadata"]
                if (metadata["debug_assertions"] or metadata["build_revision"] != label
                        or metadata["backend"] != identity or value["result"]["backend"] != identity
                        or value["result"].get("execution", {"mode": "serial"}) != execution):
                    write_json(directory / f"raw/{case['particles']:05}-{kind}-{index}-rejected.json", value)
                    raise ValueError("solver result does not identify the expected release build")
                input_id = metadata["input_id"]
                if identities.setdefault(case["particles"], input_id) != input_id:
                    write_json(directory / f"raw/{case['particles']:05}-{kind}-{index}-rejected.json", value)
                    raise ValueError("sample input identity changed")
                if retain_full_results:
                    name = f"raw/{case['particles']:05}-{kind}-{index}-full.json.gz"
                    payload = gzip.compress(json.dumps(value["result"], allow_nan=False).encode(), mtime=0)
                    with (directory / name).open("xb") as stream:
                        stream.write(payload)
                    value["full_result"] = {"file": name, "sha256": sha256(payload)}
                value["result"] = compact_result(value["result"])
            if kind == "warmup" and clean(value):
                warmup_documents[case["particles"]] = numerical_document(value["result"])
            elif kind != "warmup" and clean(value):
                expected = warmup_documents.get(case["particles"])
                if expected is not None:
                    try:
                        require_exact(numerical_document(value["result"]), expected)
                        value["numerical_agreement"] = True
                    except ValueError as error:
                        value["numerical_agreement"] = False
                        value["comparison_error"] = str(error)
            name = f"raw/{case['particles']:05}-{kind}-{index}.json"
            write_json(directory / name, value)
            dataset["raw"].append({"file": name, "sha256": sha256((directory / name).read_bytes())})
            attempts.append(value)
            timing_totals(value)
            return value

        warmup = attempt("warmup", 1)
        if warmup["interrupted"]:
            dataset["interrupted"] = True
            break
        if clean(warmup):
            for index in range(1, POLICY["samples"] + 1):
                sample = attempt("sample", index)
                if sample["interrupted"]:
                    dataset["interrupted"] = True
                if not clean(sample):
                    break
        if dataset["interrupted"]:
            break
        profile = attempt("profile", 1)
        if profile["interrupted"]:
            dataset["interrupted"] = True
            break
    dataset["finished_utc"] = now()
    dataset["source_unchanged"] = source_identity() == source
    dataset["binary_unchanged"] = sha256(binary.read_bytes()) == dataset["binary_sha256"]
    dataset["summaries"] = summarise(attempts)
    write_json(directory / "dataset.json", dataset)
    with (directory / "report.md").open("x", encoding="utf-8") as stream:
        stream.write(report(directory))
    if not dataset["source_unchanged"] or not dataset["binary_unchanged"]:
        raise ValueError("source or binary changed during collection; dataset is not a valid baseline")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["collect", "report"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("--backend", choices=BACKENDS, default="brute-force",
                        help="discovery method to collect (default: brute-force)")
    parser.add_argument("--threads", type=int, help="explicit threaded uniform-grid worker count")
    args = parser.parse_args()
    try:
        if args.operation == "collect":
            collect(args.directory.resolve(), args.backend, args.threads)
        else:
            print(report(args.directory.resolve()), end="")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"baseline: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
