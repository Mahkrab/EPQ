"""Measure work and sustained costs separately from independent quality audits.

Native replay counters explain eliminated work. CUDA traces measure kernel time
in the production executable. Only unprofiled Simulation calls enter the paired
throughput comparison, with the retained 60 Hz observation contract.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import csv

if __package__:
    from .frontier_campaign import invoke, run_case, state_bytes
    from .numerical_work import write_json
else:
    from frontier_campaign import invoke, run_case, state_bytes
    from numerical_work import write_json


def cases(root):
    for row in json.loads((root/"matrix-plan.json").read_text()):
        path = Path(row["reused_from"]) if "reused_from" in row else root/"runs"/f'{row["scene"]}--{row["policy"]["id"]}'
        yield row, path


def workload(root):
    folder = root/"workload"
    folder.mkdir(exist_ok=True)
    rows = []
    selected = list(cases(root))
    previous = root.parent/"pbf-frontier-v1"
    for scene in ("resolved", "large"):
        for name, source in (
                ("production", previous/"runs"/f"long-{scene}--production"),
                ("half-rate", previous/"runs/long-resolved--anchor" if scene == "resolved"
                 else root/"runs/long-large--half-rate"),
                ("half-iterations", root/"runs"/f"long-{scene}--half-iterations")):
            metrics = json.loads((source/"metrics.json").read_text())
            selected.append((dict(scene=scene, policy={**metrics["policy"], "id": name}), source))
    for row, source in selected:
        name = f'{row["scene"]}--{row["policy"]["id"]}'
        path = folder/name
        m = json.loads((source/"metrics.json").read_text())
        command = [str(root/"workload-probe"), str(source/"input.bin"), str(m["steps"]),
                   str(row["policy"]["iterations"]), "checked", str(path), "0", "0", "0"]
        response = invoke(command, path.with_suffix(".json"), path.with_suffix(".stderr"))
        write_json(path.with_suffix(".process.json"), response)
        if response["exit_code"] != 0:
            raise ValueError("workload replay failed "+name)
        result = json.loads(path.with_suffix(".json").read_text())
        if hashlib.sha256(Path(str(path)+f'-{m["steps"]}.bin').read_bytes()).hexdigest() != m["final_sha256"]:
            raise ValueError("counted trajectory differs "+name)
        entries = result["neighbour_entries_sum"]
        if entries % 2:
            raise ValueError("prediction-neighbour symmetry count differs")
        iterations = row["policy"]["iterations"]
        rows.append(dict(scene=row["scene"], policy=row["policy"], steps=m["steps"],
                         simulated_s=m["simulated_s"], jacobi_iterations=result["jacobi_iterations"],
                         counted_neighbour_entries=entries,
                         derived_jacobi_entry_visits=entries*iterations*5//2,
                         derived_self_density_visits=m["steps"]*m["particles"]*iterations,
                         launches=result["launches"], endpoint_equal=True,
                         production_solver_s=m["production_solver_s"],
                         note="Two full directed-row traversals plus one upper-identity suffix per Jacobi iteration; self-density visits separate. Discovery candidate tests and row-sort comparisons are additional work."))
        print(name, "entries", entries, "Jacobi", result["jacobi_iterations"], flush=True)
    write_json(root/"workload-results.json", rows)


def traces(root):
    folder = root/"traces"
    folder.mkdir(exist_ok=True)
    results = []
    for row, source in cases(root):
        name = f'{row["scene"]}--{row["policy"]["id"]}'
        out = folder/name
        out.mkdir()
        original = json.loads((source/"production.process.json").read_text())["command"]
        command = ["nsys", "profile", "--trace=cuda", "--sample=none", "--cpuctxsw=none",
                   "--force-overwrite=false", "--output", str(out/"cuda"), *original,
                   "--output", str(out/"solver.json")]
        response = invoke(command, out/"profile.stdout", out/"profile.stderr", timeout=300)
        write_json(out/"profile.process.json", response)
        if response["exit_code"] != 0:
            raise ValueError("production trace failed "+name)
        response = invoke(["nsys", "export", "--type=sqlite", "--output", str(out/"cuda.sqlite"),
                           str(out/"cuda.nsys-rep")], out/"export.stdout", out/"export.stderr")
        write_json(out/"export.process.json", response)
        if response["exit_code"] != 0:
            raise ValueError("trace export failed "+name)
        with sqlite3.connect(f'file:{out/"cuda.sqlite"}?mode=ro', uri=True) as db:
            groups = list(db.execute("SELECT s.value, COUNT(*), SUM(k.end-k.start) "
                                     "FROM CUPTI_ACTIVITY_KIND_KERNEL k JOIN StringIds s ON s.id=k.shortName "
                                     "GROUP BY s.value"))
            kernels = list(db.execute("SELECT s.value, k.end-k.start FROM CUPTI_ACTIVITY_KIND_KERNEL k "
                                      "JOIN StringIds s ON s.id=k.shortName ORDER BY k.start"))
        # Context construction also launches its roundtrip probe. Keep that work
        # visible but outside the simulation-kernel total.
        simulation_groups = [g for g in groups if g[0] in ("solver", "spatial_sort", "observe_state", "prefix_counts")]
        count = sum(g[1] for g in simulation_groups)
        duration = sum(g[2] for g in simulation_groups)
        if not count:
            raise ValueError("trace kernel names differ from the measured source")
        with (out/"solver.json").open() as f:
            document = json.load(f)
        m = json.loads((source/"metrics.json").read_text())
        if int(document["completed_steps"]) != m["steps"]:
            raise ValueError("traced solver did not complete")
        if hashlib.sha256(state_bytes(document["final_snapshot"]["particles"])).hexdigest() != m["final_sha256"]:
            raise ValueError("traced trajectory differs")
        sequence = [k for k in kernels if k[0] in ("solver", "spatial_sort", "observe_state", "prefix_counts")]
        bits = (m["particles"]-1).bit_length()
        stride = bits+4+6*row["policy"]["iterations"]
        if len(sequence) != stride*m["steps"]:
            raise ValueError("traced launch count differs from the retained scheduling contract")
        jacobi_ns = sum(value for index, (_, value) in enumerate(sequence)
                        if bits+3 <= index%stride < stride-1)
        results.append(dict(scene=row["scene"], policy=row["policy"], steps=m["steps"],
                            simulated_s=m["simulated_s"], kernel_count=count,
                            kernel_execution_s=duration/1e9,
                            jacobi_kernel_s=jacobi_ns/1e9,
                            traced_solver_s=sum(x["total_s"] for x in document["measurements"]["steps"]),
                            kernel_groups=groups, endpoint_equal=True, primary_timing=False))
        with (out/"solver.json").open("rb") as inp, gzip.open(out/"solver.json.gz", "xb") as output:
            import shutil
            shutil.copyfileobj(inp, output)
        (out/"solver.json").unlink()
        print(name, "kernel_s", duration/1e9, "kernels", count, flush=True)
    write_json(root/"trace-results.json", results)


def extend(root):
    selected = [dict(id="half-iterations", dt=1/480, iterations=4, scale=.5, epsilon=2.),
                dict(id="half-rate", dt=1/240, iterations=8, scale=.5, epsilon=2.)]
    for policy in selected:
        for scene in ("resolved", "large", "hydro", "collision", "surface"):
            # The half-rate small trajectories already exist through five seconds.
            if policy["id"] == "half-rate" and scene != "large":
                continue
            run_case(root, scene, policy, label=f'long-{scene}--{policy["id"]}', duration=5.)


def sustained(root):
    previous = root.parent/"pbf-frontier-v1"
    binary = previous/"target/release/examples/frontier_resident"
    folder = root/"sustained"
    folder.mkdir(exist_ok=True)
    results = []
    for scene in ("resolved", "large"):
        sources = {
            "production": previous/"runs"/f"long-{scene}--production",
            "half-rate": (previous/"runs/long-resolved--anchor" if scene == "resolved"
                          else root/"runs/long-large--half-rate"),
            "half-iterations": root/"runs"/f"long-{scene}--half-iterations",
        }
        records = {}
        for mode, source in sources.items():
            m = json.loads((source/"metrics.json").read_text())
            record = folder/f"{scene}--{mode}.input.json"
            with gzip.open(source/"production.json.gz", "rb") as f:
                document = json.load(f)
            # RecordedInput resolution is sufficient; avoid parsing a second full snapshot.
            write_json(record, {"input": document["input"]})
            records[mode] = (record, m)
        for candidate in ("half-rate", "half-iterations"):
            for repeat in range(6):
                for mode in (("production", candidate) if repeat%2 == 0 else (candidate, "production")):
                    record, m = records[mode]
                    cadence = max(1, round(1/(60*m["policy"]["dt"])))
                    name = f"{scene}--{candidate}--r{repeat}--{mode}"
                    snapshot = folder/(name+".bin")
                    response = invoke([str(binary), str(record), str(m["steps"]), "normal",
                                       str(cadence), str(snapshot)], folder/(name+".json"), folder/(name+".stderr"))
                    write_json(folder/(name+".process.json"), response)
                    if response["exit_code"] != 0:
                        raise ValueError("sustained run failed "+name)
                    if hashlib.sha256(snapshot.read_bytes()).hexdigest() != m["final_sha256"]:
                        raise ValueError("sustained endpoint differs "+name)
                    result = json.loads((folder/(name+".json")).read_text())
                    result.update(scene=scene, policy=mode, candidate=candidate, repeat=repeat,
                                  warmup=repeat == 0, endpoint_equal=True, simulated_s=m["simulated_s"],
                                  cost_s_per_sim_s=(result["solver_s"]+result["observation_s"])/m["simulated_s"],
                                  binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
                    results.append(result)
                    write_json(root/"sustained-results.json", results)
                    print(name, result["cost_s_per_sim_s"], flush=True)


def residuals(root):
    """Bound early-exit opportunity on unchanged, fully iterated trajectories.

    These are optimistic scheduling estimates, not an adaptive trajectory or a
    measured speedup. Changing an earlier iteration changes every later state.
    """
    previous = root.parent/"pbf-frontier-v1"
    folder = root/"residuals"
    folder.mkdir(exist_ok=True)
    results = []
    for scene, label in (("resolved", "long-resolved--dt-0.0020833333333333333"),
                         ("large", "long-large--strong480")):
        source = previous/"runs"/label
        m = json.loads((source/"metrics.json").read_text())
        prefix = folder/scene
        response = invoke(["env", "WORK_RESIDUALS=1", str(root/"workload-probe"),
                           str(source/"input.bin"), str(m["steps"]), "8", "checked",
                           str(prefix), "0", "0", "0"], folder/(scene+".json"), folder/(scene+".stderr"))
        write_json(folder/(scene+".process.json"), response)
        if response["exit_code"] != 0:
            raise ValueError("residual probe failed "+scene)
        if hashlib.sha256(Path(str(prefix)+f'-{m["steps"]}.bin').read_bytes()).hexdigest() != m["final_sha256"]:
            raise ValueError("residual probe trajectory differs")
        by_step = {}
        with Path(str(prefix)+"-residuals.csv").open() as f:
            for row in csv.DictReader(f):
                by_step.setdefault(int(row["step"]), []).append(row)
        estimates = []
        for correction_check in (False, True):
            selected = []
            for rows in by_step.values():
                stop = 8
                for row in rows:
                    applied = int(row["iteration"])
                    if (applied >= 2 and float(row["p95_compression"]) <= .03
                            and float(row["max_compression"]) <= .15
                            and (not correction_check or float(row["max_correction_m"]) <= .0005)):
                        stop = applied
                        break
                selected.append(stop)
            estimates.append(dict(correction_check=correction_check,
                                  mean_applied_iterations=sum(selected)/len(selected),
                                  iterations_saved_fraction=1-sum(selected)/(8*len(selected)),
                                  max_iterations_steps=sum(x == 8 for x in selected),
                                  note="Optimistic oracle: excludes check/copy/reduction cost and the extra density/correction group used to observe the residual."))
        with gzip.open(source/"production.json.gz") as f:
            production = json.load(f)
        factor = production["input"]["configuration"]["numerical"]["cfl_factor"]
        diameter = production["input"]["configuration"]["derived"]["particle_diameter_m"]
        counts = {"120": 0, "240": 0, "480": 0, "finer_than_480": 0}
        for step in production["steps"]:
            required = step["maximum_speed_m_s"]/(factor*diameter)
            bucket = next((str(hz) for hz in (120, 240, 480) if hz >= required), "finer_than_480")
            counts[bucket] += 1
        results.append(dict(scene=scene, steps=m["steps"], estimates=estimates, endpoint_equal=True,
                            cfl_only_rate_histogram_on_fixed_trajectory=counts,
                            cfl_note="Velocity-only prospective bins, not a variable-timestep simulation. CFL does not bound density relaxation, volume or projection energy."))
        print(scene, estimates, flush=True)
    write_json(root/"residual-results.json", results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("phase", choices=("workload", "traces", "extend", "sustained", "residuals"))
    args = parser.parse_args()
    {"workload": workload, "traces": traces, "extend": extend, "sustained": sustained, "residuals": residuals}[args.phase](args.root.resolve())
