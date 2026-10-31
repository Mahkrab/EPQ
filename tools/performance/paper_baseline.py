"""Compare the published PBF baseline with retained application policies.

Run from the parent checkout with an explicit executable and a fresh evidence
root. Each case retains its command, process result and resolved application
output. Timing and rendering are separate operations; no score selects a policy.
"""

import argparse
import json
from pathlib import Path
import statistics
import struct
import subprocess
import time


# Only the published starting point and two single-mechanism controls are admitted.
POLICIES = {
    "reference": (480, 8, .0625, 20),
    "experimental": (240, 8, .25, 20),
    "paper-baseline": (240, 3, 1, 20),
    "paper-initial": (240, 3, 1, 1),
    "paper-epsilon20": (240, 3, 1, 20),
    "paper-pressure001": (240, 3, 1, 1),
}


def collect(root, binary, scene, policy, operation, duration, backend, repeat, scene_root, auditor, fixed_colour=False):
    rate, iterations, scale, relaxation = POLICIES[policy]
    folder = root / f"{operation}-{scene}-{policy}-{repeat}"
    folder.mkdir(parents=True, exist_ok=False)
    scene_input = str(scene_root / scene / "scene.toml") if scene_root else f"builtin:{scene}"
    mode = "paper-baseline" if policy.startswith("paper-") else policy
    command = [str(binary), "run" if operation == "audit" else operation, scene_input,
               "--backend", backend, "--numerical-mode", mode,
               "--steps", str(round(duration * rate)), "--format", "json", "--quiet",
               "--runs-dir", str(root / "library"),
               "--scenes-dir", str(root / "scenes")]
    for field, value in [("fixed_timestep_s", 1/rate), ("solver_iterations", iterations),
                         ("correction_scale", scale), ("relaxation_scale", relaxation)]:
        command += ["--set", f"{field}={value}"]
    if policy == "paper-pressure001":
        command += ["--set", "artificial_pressure_strength_scale=0.001"]
    if operation == "compile" and fixed_colour:
        render = root / "render-fixed.toml"
        content = 'schema_version = 2\ncamera_mode = "fit"\n[particles]\ncolour_mode = "fixed"\ncolour = "#2b9fd9"\n'
        if render.exists() and render.read_text() != content:
            raise ValueError("fixed presentation input already differs")
        render.write_text(content)
        command += ["--render-config", str(render)]
    if operation == "compile":
        command += ["--frame-stride", str(rate // 30), "--width", "480", "--height", "360",
                    "--output", str(folder / "bundle")]
        if backend != "cuda":
            command += ["--software"]
    else:
        command += ["--unpaced", "--measure"]
        if operation == "audit":
            checkpoints = sorted({0, round(.3*rate), round(.6*rate), rate, 2*rate,
                                  3*rate, round(duration*rate)})
            command += ["--checkpoints", ",".join(map(str, checkpoints))]
    (folder / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    start = time.perf_counter()
    with (folder / "stdout.json").open("w") as out, (folder / "stderr").open("w") as err:
        result = subprocess.run(command, stdout=out, stderr=err, timeout=1200, check=False)
    metrics = {"exit_code": result.returncode, "process_wall_s": time.perf_counter()-start,
               "scene": scene, "policy": policy, "backend": backend,
               "requested_simulated_s": duration, "repeat": repeat}
    if result.returncode == 0 and operation in ("run", "audit"):
        data = json.loads((folder / "stdout.json").read_text())
        assert int(data["completed_steps"]) == round(duration*rate)
        assert data["status"] in ("completed", "completed_with_warnings")
        model = data["input"]["configuration"]["numerical"]
        assert model["solver_iterations"] == iterations
        assert model.get("correction_scale", 1.0) == scale
        assert model["relaxation_scale"] == relaxation
        metrics["simulated_s"] = int(data["completed_steps"])*model["fixed_timestep_s"]
        metrics["solver_s"] = sum(s["total_s"] for s in data["measurements"]["steps"])
        metrics["completed_steps"] = data["completed_steps"]
        metrics["solver_s_per_sim_s"] = metrics["solver_s"] / metrics["simulated_s"]
        if operation == "audit":
            configuration = data["input"]["configuration"]
            model, derived = configuration["numerical"], configuration["derived"]
            records = []
            for checkpoint in data["checkpoints"]:
                snapshot = checkpoint["snapshot"]
                particles = snapshot["particles"]
                state = folder / f"state-{snapshot['completed_steps']}.bin"
                state.write_bytes(b"".join(struct.pack("<3f", *(p[field][axis] for axis in "xyz"))
                                           for field in ("position_m", "velocity_m_s") for p in particles))
                # Box maxima come from inward upper-bound half-spaces. The
                # application separately checks every plane, including slopes.
                planes = data["input"]["planes"]
                upper = [-next(p["offset_m"] for p in planes if p["normal"][axis] == -1)
                         for axis in "xyz"]
                audit_command = [str(auditor), str(state), str(len(particles)),
                                 str(derived["support_radius_m"]), str(derived["normalised_rest_density_per_m3"]),
                                 str(derived["particle_mass_kg"]), str(model["external_acceleration_m_s2"]["y"]),
                                 str(model["particle_spacing_m"]), ",".join(map(str, upper)),
                                 str(folder / "state-0.bin"), str(model["particle_spacing_m"]/2)]
                answer = subprocess.run(audit_command, capture_output=True, text=True, check=True)
                record = json.loads(answer.stdout)
                record["step"] = int(snapshot["completed_steps"])
                records.append(record)
            (folder / "audit.json").write_text(json.dumps(records, indent=2)+"\n")
    (folder / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics), flush=True)
    if result.returncode:
        raise RuntimeError(f"Failed case retained at {folder}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("binary", type=Path)
    parser.add_argument("operation", choices=["run", "compile", "audit"])
    parser.add_argument("--scenes", nargs="+", default=["slope-slide"])
    parser.add_argument("--policies", nargs="+", choices=POLICIES, default=["reference", "experimental", "paper-baseline"])
    parser.add_argument("--duration", type=float, default=3)
    parser.add_argument("--backend", default="serial-grid")
    parser.add_argument("--scene-root", type=Path)
    parser.add_argument("--auditor", type=Path)
    parser.add_argument("--fixed-colour", action="store_true",
                        help="Use equal blue colouring independent of particle mass")
    parser.add_argument("--pairs", type=int, default=0,
                        help="Timing pairs after one warmup; alternating order")
    args = parser.parse_args()
    for scene in args.scenes:
        for repeat in range(args.pairs+1):
            policies = args.policies if repeat % 2 == 0 else args.policies[::-1]
            for policy in policies:
                collect(args.root.resolve(), args.binary.resolve(), scene, policy,
                        args.operation, args.duration, args.backend, repeat, args.scene_root, args.auditor, args.fixed_colour)
    if args.operation == "run" and args.pairs:
        summary = []
        for scene in args.scenes:
            for policy in args.policies:
                samples = [json.loads((args.root / f"run-{scene}-{policy}-{r}" / "metrics.json").read_text())
                           for r in range(1, args.pairs+1)]
                summary.append(dict(scene=scene, policy=policy, samples=samples,
                                    median_solver_s_per_sim_s=statistics.median(
                                        s["solver_s_per_sim_s"] for s in samples)))
        (args.root / "timing-summary.json").write_text(json.dumps(summary, indent=2)+"\n")


if __name__ == "__main__":
    main()
