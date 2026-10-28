"""Verify retained observations and reconstruct source without a mutable checkout."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(assets, repo, extract):
    expected = json.loads((assets / "files-sha256.json").read_text())
    counts = json.loads((assets / "archive-members.json").read_text())
    seen = set()
    archives = {}
    if extract:
        extract.mkdir(parents=True, exist_ok=False)
    for name, count in counts.items():
        path = assets / name
        found = 0
        with tarfile.open(path) as archive:
            for member in archive:
                relative = Path(member.name)
                assert member.isfile() and not relative.is_absolute()
                assert ".." not in relative.parts and member.name not in seen
                data = archive.extractfile(member).read()
                assert digest(data) == expected[member.name], member.name
                seen.add(member.name)
                found += 1
                if extract:
                    target = extract / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
        assert found == count, (name, found, count)
        archives[name] = dict(
            sha256=digest(path.read_bytes()), members=found, bytes=path.stat().st_size
        )
    assert seen == set(expected)
    (assets / "archive-readback.json").write_text(
        json.dumps(dict(verified_members=len(seen), archives=archives,
                        all_member_hashes_match=True), indent=2) + "\n"
    )

    base = "1e0085926d05c42949bb76b55d177d42a1f8f94f"
    results = {}
    with tempfile.TemporaryDirectory(prefix="maelstrom-source-readback-") as temp:
        root = Path(temp)
        control = root / "control"
        control.mkdir()
        original = subprocess.run(
            ["git", "-C", str(repo), "archive", base], check=True, capture_output=True
        )
        with tarfile.open(fileobj=io.BytesIO(original.stdout)) as archive:
            archive.extractall(control, filter="data")

        def apply(tree, name):
            subprocess.run(
                ["patch", "--batch", "--forward", "-p1", "-i",
                 str((assets / (name + ".patch")).resolve())],
                cwd=tree, check=True, capture_output=True,
            )

        def check(tree, name):
            manifest = json.loads((assets / (name + "-source.json")).read_text())
            actual = {
                path.relative_to(tree).as_posix(): digest(path.read_bytes())
                for path in tree.rglob("*") if path.is_file()
            }
            assert actual == manifest, name
            results[name] = dict(files=len(actual), all_hashes_match=True)

        apply(control, "control")
        check(control, "control")
        for name, parent in [
            ("diagnostic", "control"), ("trial-0", "control"),
            ("candidate", "control"),
        ]:
            target = root / name
            shutil.copytree(root / parent, target)
            apply(target, name)
            check(target, name)
    (assets / "source-reconstruction.json").write_text(
        json.dumps(dict(base_commit=base, exports=results), indent=2) + "\n"
    )
    print(f"Verified {len(seen)} archive members and {len(results)} source exports.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", type=Path)
    parser.add_argument("repo", type=Path, help="Maelstrom repository with the base commit")
    parser.add_argument("--extract", type=Path, help="New directory for independent readers")
    args = parser.parse_args()
    verify(args.assets.resolve(), args.repo.resolve(), args.extract)
