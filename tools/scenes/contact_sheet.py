# /// script
# dependencies = ["pillow==13.0.0"]
# ///
"""Arrange actual compiled scene frames for a catalogue visual review."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw


def draw(root: Path, output: Path) -> None:
    scenes = sorted(root.glob("*-fast/manifest.json"))
    tile_w, tile_h = 320, 266
    sheet = Image.new("RGB", (tile_w * 4, tile_h * ((len(scenes) + 3) // 4)), "white")
    pen = ImageDraw.Draw(sheet)
    for index, manifest in enumerate(scenes):
        data = json.loads(manifest.read_text())
        frame = min(data["frames"], key=lambda row: abs(row["simulated_seconds"] - 0.5))
        x, y = index % 4 * tile_w, index // 4 * tile_h
        with Image.open(manifest.parent / frame["file"]) as image:
            sheet.paste(image.convert("RGB").resize((320, 240)), (x, y + 26))
        pen.text((x + 5, y + 6), manifest.parent.name.removesuffix("-fast") + " (0.5 s)", fill="black")
    sheet.save(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    draw(args.root, args.output)
