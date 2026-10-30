"""Join matched physical cases and verify every compiled image after timing.

Historical target flags remain diagnostic data. Adoption is a written assessment
of the complete trade-off, never a Boolean derived from one compression budget.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def assess(root):
    rows = json.loads((root/"frontier.json").read_text(encoding="utf-8"))
    fields = ("p95_compression_peak", "max_compression_peak", "min_separation_over_dx",
              "volume_error_peak", "energy_excess_peak", "CFL_warning_steps", "stability")
    pairs = []
    for scene in ("resolved", "large", "hydro", "collision", "surface", "shear"):
        reference = next(r for r in rows if r["scene"] == scene and r["policy"]["id"] == "reference")
        fast = next(r for r in rows if r["scene"] == scene and r["policy"]["id"] == "fast")
        pair = dict(scene=scene, reference={k: reference[k] for k in fields},
                    fast={k: fast[k] for k in fields},
                    difference_fast_minus_reference={k: fast[k]-reference[k] for k in fields if k != "stability"})
        if scene == "hydro":
            pair["hydrostatic_centroid_error"] = dict(reference=reference["hydro_centroid_error"], fast=fast["hydro_centroid_error"])
        if scene == "shear":
            pair["retained_shear_mode"] = dict(reference=reference["final"]["shear_projection"], fast=fast["final"]["shear_projection"])
        pairs.append(pair)
    (root/"physical-comparison.json").write_text(json.dumps(pairs, indent=2)+"\n", encoding="utf-8")
    verification = []
    for directory in sorted((root/"compiled").iterdir()):
        path = directory/"bundle/manifest.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        for frame in document["frames"]:
            png = directory/"bundle"/frame["file"]
            sha = "sha256:"+hashlib.sha256(png.read_bytes()).hexdigest()
            if sha != frame["png_sha256"]:
                raise ValueError("compiled PNG differs from manifest "+str(png))
        validation = subprocess.run([str(root/"target/release/maelstrom"), "runs", "validate", str(path),
                                     "--runs-dir", str(root/"library/runs"), "--format", "json"],
                                    capture_output=True, text=True, timeout=120, check=False)
        (directory/"validation.stdout.json").write_text(validation.stdout, encoding="utf-8")
        (directory/"validation.stderr").write_text(validation.stderr, encoding="utf-8")
        if validation.returncode != 0:
            raise ValueError("application bundle validation failed "+directory.name)
        # Both modes must frame the same physical geometry. Stride differs only
        # to keep observation times equal at the two numerical rates.
        presentation = {k: v for k,v in document["render"].items() if k != "step_stride"}
        verification.append(dict(label=directory.name, frames=len(document["frames"]),
                                 graphics=document["graphics"], presentation=presentation,
                                 first_png=document["frames"][0]["png_sha256"],
                                 last_png=document["frames"][-1]["png_sha256"],
                                 all_png_hashes=[f["png_sha256"] for f in document["frames"]],
                                 valid=True))
    by_label = {r["label"]: r for r in verification}
    for label, row in by_label.items():
        if label.endswith("-reference"):
            other = by_label[label.removesuffix("-reference")+"-fast"]
            if row["presentation"] != other["presentation"] or row["frames"] != other["frames"]:
                raise ValueError("rendered mode comparison changed presentation or cadence")
            if row["first_png"] != other["first_png"]:
                raise ValueError("initial rendered geometry differs between modes")
    for scene in ("resolved", "large"):
        for mode in ("reference", "fast"):
            control = by_label[f"{scene}-r0-{mode}"]["all_png_hashes"]
            for repeat in (1, 2, 3):
                if by_label[f"{scene}-r{repeat}-{mode}"]["all_png_hashes"] != control:
                    raise ValueError("repeated rendered trajectory differs")
    (root/"render-verification.json").write_text(json.dumps(verification, indent=2)+"\n", encoding="utf-8")
    print("Matched physical cases:", len(pairs), "verified bundles:", len(verification),
          "verified images:", sum(r["frames"] for r in verification))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    assess(parser.parse_args().root.resolve())
