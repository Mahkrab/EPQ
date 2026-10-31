"""Audit large timed trajectories using the retained native recorder.

The recorder's final bytes must equal the production endpoint before its samples
can supply quality evidence. Its clocks never enter the throughput comparison.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

if __package__:
    from .frontier_campaign import encode, state_bytes
else:
    from frontier_campaign import encode, state_bytes


def replay(root, recorder, auditor, policies=("reference", "four240")):
    for policy in policies:
        folder = root / "timing" / f"run-large-impact-{policy}-0"
        data = json.loads((folder / "stdout.json").read_text())
        output = root / "large-replay" / policy
        output.mkdir(parents=True, exist_ok=True)
        (output / "input.bin").write_bytes(encode(data))
        model = data["input"]["configuration"]["numerical"]
        derived = data["input"]["configuration"]["derived"]
        steps = int(data["completed_steps"])
        command = [str(recorder), str(output / "input.bin"), str(steps),
                   str(model["solver_iterations"]), "checked", str(output / "state"),
                   "1", "0", str(round(.5/model["fixed_timestep_s"]))]
        (output / "command.json").write_text(json.dumps(command)+"\n")
        if not (output / "verification.json").exists():
            with (output / "stdout.json").open("w") as out, (output / "stderr").open("w") as err:
                subprocess.run(command, stdout=out, stderr=err, check=True)
        expected = state_bytes(data["final_snapshot"]["particles"])
        actual = (output / f"state-{steps}.bin").read_bytes()
        assert actual == expected, "Recorder endpoint differs from production"
        verification = dict(endpoint_equal=True, sha256=hashlib.sha256(actual).hexdigest(),
                            recorder_sha256=hashlib.sha256(recorder.read_bytes()).hexdigest(),
                            auditor_sha256=hashlib.sha256(auditor.read_bytes()).hexdigest())
        (output / "verification.json").write_text(json.dumps(verification, indent=2)+"\n")
        planes = data["input"]["planes"]
        upper = [-next(p["offset_m"] for p in planes if p["normal"][axis] == -1) for axis in "xyz"]
        records = []
        states = [p for p in output.glob("state-*.bin") if p.stem.split("-")[-1].isdigit()]
        for state in sorted(states, key=lambda p: int(p.stem.split("-")[-1])):
            command = [str(auditor), str(state), str(len(data["input"]["particles"])),
                       str(derived["support_radius_m"]), str(derived["normalised_rest_density_per_m3"]),
                       str(derived["particle_mass_kg"]), str(model["external_acceleration_m_s2"]["y"]),
                       str(model["particle_spacing_m"]), ",".join(map(str, upper)),
                       str(output / "state-0.bin"), str(model["particle_spacing_m"]/2)]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            record = json.loads(result.stdout)
            record["step"] = int(state.stem.split("-")[-1])
            records.append(record)
        (output / "audit.json").write_text(json.dumps(records, indent=2)+"\n")
        print(policy, verification, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("recorder", type=Path)
    parser.add_argument("auditor", type=Path)
    parser.add_argument("--policies", nargs="+", default=["reference", "four240"])
    args = parser.parse_args()
    replay(args.root, args.recorder, args.auditor, args.policies)
