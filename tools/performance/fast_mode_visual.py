# /// script
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Present actual application frames at equal simulated times and camera settings."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont


def visualise(root):
    output = root/"visuals"
    output.mkdir(exist_ok=True)
    font = ImageFont.truetype(font_manager.findfont("DejaVu Sans"), 17)
    for scene in ("resolved", "large", "hydro", "collision", "surface", "shear"):
        label = f"{scene}-r3" if scene in ("resolved", "large") else f"control-{scene}"
        cases = []
        for mode in ("reference", "fast"):
            folder = root/"compiled"/(label+"-"+mode)/"bundle"
            document = json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
            cases.append((mode, folder, document["frames"]))
        times = [0, 1/60, .05, .1, .15, .2] if scene == "shear" else [0, .1, .3, .5, 1, 5]
        fig, axes = plt.subplots(2, len(times), figsize=(17, 5.5), layout="constrained")
        for row, (mode, folder, frames) in enumerate(cases):
            for col, t in enumerate(times):
                frame = min(frames, key=lambda f: abs(f["simulated_seconds"]-t))
                with Image.open(folder/frame["file"]) as picture:
                    axes[row, col].imshow(picture)
                axes[row, col].set_title(f'{mode}, {frame["simulated_seconds"]:.3g} s', fontsize=10)
                axes[row, col].axis("off")
        fig.suptitle(f"{scene}: matched application renderer, identical initial geometry and camera")
        fig.savefig(output/(scene+"-frames.png"), dpi=140)
        plt.close(fig)
        pictures = []
        count = len(cases[0][2])
        selected = list(range(0, count, 5 if scene in ("resolved", "large") else 1))
        if selected[-1] != count-1:
            selected.append(count-1)
        for index in selected:
            picture = Image.new("RGB", (960, 390), "#ffffff")
            draw = ImageDraw.Draw(picture)
            for col, (mode, folder, frames) in enumerate(cases):
                frame = frames[index]
                with Image.open(folder/frame["file"]) as original:
                    picture.paste(original.convert("RGB").resize((480, 360)), (480*col, 30))
                draw.text((10+480*col, 5), f'{mode}: t={frame["simulated_seconds"]:.3f} s', fill="black", font=font)
            pictures.append(picture)
        duration = 67 if scene == "shear" else round(5000/(len(pictures)-1))
        pictures[0].save(output/(scene+"-comparison.gif"), save_all=True, append_images=pictures[1:],
                         duration=duration, loop=0)
    metrics = json.loads((root/"performance-summary.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for axis, scene, title in zip(axes, ("resolved", "large"), ("8,000 particles", "110,592 particles")):
        selected = [next(r for r in metrics if r["scene"] == scene and r["family"] == family and r["metric"] == metric)
                    for family,metric in (("headless","cost_s_per_sim_s"), ("headless","CLI_cost_s_per_sim_s"), ("compiled","cost_s_per_sim_s"))]
        for i, r in enumerate(selected):
            axis.bar(i-.18, r["reference_median"], width=.36, color="tab:blue", label="Reference" if i == 0 else None)
            axis.bar(i+.18, r["fast_median"], width=.36, color="tab:orange", label="Fast" if i == 0 else None)
        axis.axhline(1, color="grey", ls=":")
        axis.set(xticks=range(3), xticklabels=["Solver", "Complete CLI", "Compile 60 Hz"],
                 ylabel="Wall seconds / simulated second", title=title)
        axis.legend()
    fig.savefig(output/"throughput.png", dpi=180)
    fig.savefig(output/"throughput.svg")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    visualise(parser.parse_args().root.resolve())
