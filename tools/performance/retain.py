"""Retain shareable observations without publishing profiler process environments.

Native reports stay private. SQLite exports preserve every analytical row outside
environment/string metadata, with original and sanitised hashes kept separately.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import sqlite3
import sys

from .capture import digest, write_json


def rows_digest(connection: sqlite3.Connection, table: str) -> str:
    """Hash typed rows in their existing order to check the metadata-only boundary."""
    result = hashlib.sha256()
    for row in connection.execute(f'SELECT * FROM "{table}"'):
        result.update(repr(row).encode())
        result.update(b"\n")
    return result.hexdigest()


def sanitise(source: Path, destination: Path) -> dict:
    if destination.exists():
        raise FileExistsError(destination)
    original = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target = sqlite3.connect(destination)
    try:
        original.backup(target)
        tables = [r[0] for r in original.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        changed = []
        if "StringIds" in tables:
            for identity, value in target.execute("SELECT id,value FROM StringIds").fetchall():
                if any(marker in value for marker in ("\0", "/home/", "USER=", "HOME=", "SSH_", "TOKEN=", "PASSWORD=")):
                    target.execute("UPDATE StringIds SET value=? WHERE id=?", ("[redacted process environment or private path]", identity))
                    changed.append(identity)
        if "TARGET_INFO_SYSTEM_ENV" in tables:
            target.execute("UPDATE TARGET_INFO_SYSTEM_ENV SET value='[redacted]' WHERE name IN ('DeviceEnvironment','Hostname')")
        if "META_DATA_CAPTURE" in tables:
            target.execute("UPDATE META_DATA_CAPTURE SET value='[redacted]' WHERE name LIKE '%ENVIRONMENT%'")
        target.commit()
        unchanged = {}
        for table in tables:
            if table in ("StringIds", "TARGET_INFO_SYSTEM_ENV", "META_DATA_CAPTURE"):
                continue
            before = rows_digest(original, table)
            if before != rows_digest(target, table):
                raise ValueError("sanitisation changed analytical rows")
            unchanged[table] = before
        # Remove old text from free pages as well as live rows.
        target.execute("VACUUM")
    finally:
        original.close()
        target.close()
    return {"original_sha256": digest(source.read_bytes()), "shareable_sha256": digest(destination.read_bytes()),
            "redacted_string_ids": changed, "unchanged_table_sha256": unchanged,
            "redacted_metadata": ["StringIds process environments/private paths", "DeviceEnvironment", "Hostname",
                                  "META_DATA_CAPTURE environment variables"]}


def retain(source: Path, destination: Path) -> None:
    """Create a fresh evidence tree, never rewriting the original collection."""
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("*.nsys-rep", "*.ncu-rep", "perf.data", "*.sqlite"))
    excluded = {}
    exports = {}
    for path in sorted(source.rglob("*")):
        if path.suffix in (".nsys-rep", ".ncu-rep") or path.name == "perf.data":
            excluded[path.relative_to(source).as_posix()] = digest(path.read_bytes())
        elif path.suffix == ".sqlite":
            relative = path.relative_to(source)
            exports[relative.as_posix()] = sanitise(path, destination / relative)
    for path in sorted((destination / "timelines").glob("*/files.json")):
        path.rename(path.with_name("original-files.json"))
        files = {p.relative_to(path.parent).as_posix(): digest(p.read_bytes())
                 for p in sorted(path.parent.rglob("*")) if p.is_file()}
        write_json(path, files)
    write_json(destination / "privacy.json", {"native_reports_not_published": excluded,
               "sanitised_sqlite_exports": exports,
               "scope": "derived shareable export; original native reports and SQLite remain private"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        retain(args.source.resolve(), args.destination.resolve())
    except (OSError, ValueError, sqlite3.Error) as error:
        print(f"Evidence retention: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
