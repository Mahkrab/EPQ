# /// script
# dependencies = ["pillow==12.2.0"]
# ///
"""Join matched application PNGs without rerendering the particle states."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def visualise(root, scene, policies):
    cases = []
    for policy in policies:
        folder = root / f"compile-{scene}-{policy}-0" / "bundle"
        manifest = json.loads((folder / "manifest.json").read_text())
        assert manifest["complete"]
        for frame in manifest["frames"]:
            assert "sha256:"+hashlib.sha256((folder/frame["file"]).read_bytes()).hexdigest() == frame["png_sha256"]
        cases.append((policy, folder, manifest))
    baseline = cases[0][2]
    for _, _, manifest in cases[1:]:
        assert {k: v for k, v in manifest["render"].items() if k != "step_stride"} == {
            k: v for k, v in baseline["render"].items() if k != "step_stride"
        }, "Camera/presentation differs"
        assert manifest["frames"][0]["snapshot_sha256"] == baseline["frames"][0]["snapshot_sha256"]
        assert manifest["frames"][0]["png_sha256"] == baseline["frames"][0]["png_sha256"]
    times = [0, .3, .6, 1, 2, round(baseline["frames"][-1]["simulated_seconds"])]
    sheet = Image.new("RGB", (480*len(times), 390*len(cases)), "white")
    for row, (policy, folder, manifest) in enumerate(cases):
        for col, t in enumerate(times):
            frame = min(manifest["frames"], key=lambda f: abs(f["simulated_seconds"]-t))
            with Image.open(folder/frame["file"]) as source:
                sheet.paste(source.convert("RGB"), (480*col, 390*row+30))
            ImageDraw.Draw(sheet).text((480*col+8, 390*row+8),
                                      f"{policy}: {frame['simulated_seconds']:.3f} s", fill="black")
    sheet.save(root / f"{scene}-contact.png")
    animation = []
    for i, ref in enumerate(baseline["frames"]):
        picture = Image.new("RGB", (480*len(cases), 390), "white")
        for col, (policy, folder, manifest) in enumerate(cases):
            frame = manifest["frames"][i]
            assert abs(frame["simulated_seconds"]-ref["simulated_seconds"]) < 1e-5
            with Image.open(folder/frame["file"]) as source:
                picture.paste(source.convert("RGB"), (480*col, 30))
            ImageDraw.Draw(picture).text((480*col+8, 8),
                                        f"{policy}: {frame['simulated_seconds']:.3f} s", fill="black")
        animation.append(picture)
    animation[0].save(root / f"{scene}-comparison.gif", save_all=True,
                      append_images=animation[1:], duration=33, loop=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("scene")
    parser.add_argument("policies", nargs="+")
    args = parser.parse_args()
    visualise(args.root, args.scene, args.policies)
