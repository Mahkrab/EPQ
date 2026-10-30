"""Seal application measurements and images without copying build/source trees."""
import argparse
import os
from pathlib import Path
import shutil

from tools.performance.frontier_retain import seal, verify


def retain(root, destination):
    staging = root.with_name(root.name+"-seal-input")
    if staging.exists() or destination.exists():
        raise ValueError("retention requires fresh staging and destination paths")
    excluded = {"target", "source", "build", "__pycache__", "retained", "native-tests", "power-exhaustive"}
    files = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()
             and not p.name.endswith(".tar.gz")
             and not any(part in excluded for part in p.relative_to(root).parts)]
    staging.mkdir()
    for source in files:
        target = staging/source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, target)
        except OSError:
            shutil.copy2(source, target)
    seal(staging, destination)
    return verify(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(retain(args.root.resolve(), args.destination.resolve()))
