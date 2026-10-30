"""Compare application modes on immutable, matched frontier scenes.

CLI wall time includes resolution, startup, solver work and JSON publication.
Compilation additionally includes the real graphics, PNG and bundle paths.
Independent quality replays and audits run outside repeated timing samples.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import statistics

from tools.performance.frontier_campaign import encode, f32, invoke, state_bytes
from tools.performance.frontier_audit import audit


def write(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")


def prepare(root, previous):
    for name in ("config", "scenes"):
        shutil.copytree(previous/name, root/name)
    shutil.copy2(previous/"scenes.json", root/"scenes.json")
    for name in ("frontier-driver", "frontier-quality"):
        (root/name).symlink_to(previous/name)
    write(root/"protocol.json", {
        "comparison": "Explicit fast versus reference on the same scene, initial bytes, physical inputs, effects and simulated interval",
        "authority": "Application trade-off; 5% compression is a historical target, not a product veto. Reject destructive new behaviour; report all quality improvements and regressions.",
        "physical": "Five seconds: resolved8000,large110592,hydro3200,collision3456,surface3200. Shear8000:0.2 seconds. Independent current-neighbour audit and identical native replay per trajectory.",
        "headless": "Five seconds at both particle counts; warmup then five alternating pairs; complete CLI process and ordinary measured solver time separately",
        "compiled": "Five seconds at both counts,640x480,60Hz accepted observations,hardware graphics; warmup then three alternating pairs; complete process and disjoint export profile retained",
        "rendered_controls": "Same camera/geometry/output cadence for each mode; additional 10Hz hydro/collision/surface and60Hz shear bundles",
        "guardrails": "No solver/native kernel/default/history/system-setting changes; explicit refinement keeps dt/N and correction/N^2; warnings retained; full all-features regression including opt-in device tests before timings"
    })


def policy(mode):
    return dict(id=mode, dt=1/(240 if mode == "fast" else 480), iterations=8,
                scale=.5 if mode == "fast" else .0625, epsilon=2. if mode == "fast" else 20.)


def run(root, scene, mode, label, duration=5., quality=False):
    folder = root/"runs"/label
    folder.mkdir(parents=True)
    p = policy(mode)
    steps = round(duration/p["dt"])
    command = [str(root/"target/release/maelstrom"), "run", str(root/"scenes"/(scene+".toml")),
               "--runs-dir", str(root/"library/runs"), "--scenes-dir", str(root/"library/scenes"),
               "--numerical-mode", mode, "--backend", "cuda", "--device", "0", "--block-size", "128",
               "--steps", str(steps), "--unpaced", "--measure", "--format", "json", "--quiet"]
    response = invoke(command, folder/"production.json", folder/"production.stderr", timeout=300)
    write(folder/"production.process.json", response)
    if response["exit_code"] != 0:
        raise ValueError("application run failed "+label)
    d = json.loads((folder/"production.json").read_text(encoding="utf-8"))
    if int(d["completed_steps"]) != steps or d["status"] not in ("completed", "completed_with_warnings"):
        raise ValueError("application did not complete "+label)
    model = d["input"]["configuration"]["numerical"]
    derived = d["input"]["configuration"]["derived"]
    for field, key in (("fixed_timestep_s", "dt"), ("solver_iterations", "iterations"),
                       ("correction_scale", "scale"), ("relaxation_scale", "epsilon")):
        if f32(model[field]) != f32(p[key]):
            raise ValueError("application preset differs "+field)
    raw = encode(d)
    final = state_bytes(d["final_snapshot"]["particles"])
    (folder/"input.bin").write_bytes(raw)
    (folder/"initial.bin").write_bytes(state_bytes(d["input"]["particles"]))
    (folder/"production-final.bin").write_bytes(final)
    elapsed = steps*model["fixed_timestep_s"]
    solver = sum(s["total_s"] for s in d["measurements"]["steps"])
    m = dict(label=label, scene=scene, policy=p, particles=len(d["input"]["particles"]),
             completed=True, steps=steps, simulated_s=elapsed, production_solver_s=solver,
             process_wall_s=response["process_wall_s"], cost_s_per_sim_s=solver/elapsed,
             CLI_cost_s_per_sim_s=response["process_wall_s"]/elapsed,
             CFL_warning_steps=sum(s["warning"] for s in d["steps"]),
             resolved_numerical=model, resolved_derived=derived,
             input_sha256=hashlib.sha256(raw).hexdigest(), final_sha256=hashlib.sha256(final).hexdigest(),
             production_json_sha256=hashlib.sha256((folder/"production.json").read_bytes()).hexdigest(),
             native_endpoint_equal=None)
    write(folder/"request.json", dict(scene=scene, mode=mode, duration=duration, steps=steps))
    if quality:
        native = [str(root/"frontier-driver"), str(folder/"input.bin"), str(steps), "8", "checked",
                  str(folder/"state"), "1", "0", str(round(.125/p["dt"]))]
        result = invoke(native, folder/"native.json", folder/"native.stderr", timeout=300)
        write(folder/"native.process.json", result)
        m["native_endpoint_equal"] = result["exit_code"] == 0 and hashlib.sha256((folder/f"state-{steps}.bin").read_bytes()).hexdigest() == m["final_sha256"]
        if not m["native_endpoint_equal"]:
            raise ValueError("independent recorder trajectory differs "+label)
    with (folder/"production.json").open("rb") as source, gzip.open(folder/"production.json.gz", "xb") as out:
        shutil.copyfileobj(source, out)
    (folder/"production.json").unlink()
    write(folder/"metrics.json", m)
    print(label, "solver", solver/elapsed, "CLI", response["process_wall_s"]/elapsed, flush=True)
    return m


def physical(root):
    for scene in ("resolved", "large", "hydro", "collision", "surface", "shear"):
        for mode in ("reference", "fast"):
            run(root, scene, mode, f"physical-{scene}-{mode}", duration=.2 if scene == "shear" else 5., quality=True)


def headless(root):
    results = []
    expected = {p["label"]: p for p in [json.loads(f.read_text(encoding="utf-8")) for f in (root/"runs").glob("physical-*/metrics.json")]}
    for scene in ("resolved", "large"):
        for repeat in range(6):
            for mode in (("reference", "fast") if repeat%2 == 0 else ("fast", "reference")):
                m = run(root, scene, mode, f"headless-{scene}-r{repeat}-{mode}")
                if m["final_sha256"] != expected[f"physical-{scene}-{mode}"]["final_sha256"]:
                    raise ValueError("repeated endpoint differs")
                m.update(repeat=repeat, warmup=repeat == 0)
                results.append(m)
                write(root/"headless-results.json", results)


def compile_case(root, scene, mode, label, hz=60, duration=5.):
    folder = root/"compiled"/label
    folder.mkdir(parents=True)
    rate = 240 if mode == "fast" else 480
    steps = round(duration*rate)
    command = [str(root/"target/release/maelstrom"), "compile", str(root/"scenes"/(scene+".toml")),
               "--runs-dir", str(root/"library/runs"), "--scenes-dir", str(root/"library/scenes"),
               "--numerical-mode", mode, "--backend", "cuda", "--device", "0", "--block-size", "128",
               "--steps", str(steps), "--frame-stride", str(round(rate/hz)), "--width", "640", "--height", "480",
               "--fit-camera", "--output", str(folder/"bundle"), "--format", "json", "--quiet"]
    response = invoke(command, folder/"stdout.json", folder/"stderr", timeout=600)
    write(folder/"process.json", response)
    if response["exit_code"] != 0:
        raise ValueError("compilation failed "+label)
    manifest = json.loads((folder/"bundle/manifest.json").read_text(encoding="utf-8"))
    if not manifest["complete"]:
        raise ValueError("compilation is incomplete")
    m = dict(label=label, scene=scene, mode=mode, simulated_s=steps/rate,
             process_wall_s=response["process_wall_s"], cost_s_per_sim_s=response["process_wall_s"]/(steps/rate),
             frames=len(manifest["frames"]), timing_profile=manifest.get("timing_profile"),
             manifest_path=str(folder/"bundle/manifest.json"))
    write(folder/"metrics.json", m)
    print(label, "compiled", m["cost_s_per_sim_s"], "frames", m["frames"], flush=True)
    return m


def compiled(root):
    results = []
    for scene in ("resolved", "large"):
        for repeat in range(4):
            for mode in (("reference", "fast") if repeat%2 == 0 else ("fast", "reference")):
                m = compile_case(root, scene, mode, f"{scene}-r{repeat}-{mode}")
                m.update(repeat=repeat, warmup=repeat == 0)
                results.append(m)
                write(root/"compiled-results.json", results)


def controls(root):
    for scene in ("hydro", "collision", "surface", "shear"):
        for mode in ("reference", "fast"):
            compile_case(root, scene, mode, f"control-{scene}-{mode}",
                         hz=60 if scene == "shear" else 10, duration=.2 if scene == "shear" else 5.)


def assess(root):
    rows = []
    for family in ("headless", "compiled"):
        values = json.loads((root/(family+"-results.json")).read_text(encoding="utf-8"))
        for scene in ("resolved", "large"):
            pair = {}
            for r in values:
                if r["scene"] == scene and not r["warmup"]:
                    mode = r["mode"] if family == "compiled" else r["policy"]["id"]
                    pair.setdefault(r["repeat"], {})[mode] = r
            for metric in (["cost_s_per_sim_s"] if family == "compiled" else ["cost_s_per_sim_s", "CLI_cost_s_per_sim_s"]):
                a = [pair[k]["reference"][metric] for k in sorted(pair)]
                b = [pair[k]["fast"][metric] for k in sorted(pair)]
                rows.append(dict(family=family, scene=scene, metric=metric, reference=a, fast=b,
                                 speedups=[x/y for x,y in zip(a,b)],
                                 reference_median=statistics.median(a), fast_median=statistics.median(b),
                                 speedup=statistics.median(a)/statistics.median(b)))
    write(root/"performance-summary.json", rows)
    for row in rows:
        print(row["family"], row["scene"], row["metric"], row["reference_median"], row["fast_median"], row["speedup"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("phase", choices=("prepare", "physical", "headless", "compiled", "controls", "audit", "assess"))
    parser.add_argument("--previous", type=Path)
    args = parser.parse_args()
    if args.phase == "prepare":
        if args.previous is None:
            parser.error("prepare requires --previous")
        prepare(args.root, args.previous)
    else:
        {"physical": physical, "headless": headless, "compiled": compiled, "controls": controls,
         "audit": audit, "assess": assess}[args.phase](args.root.resolve())
