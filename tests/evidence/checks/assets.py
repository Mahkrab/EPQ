#!/usr/bin/env python3

from __future__ import annotations

import argparse, os, sys
from pathlib import Path

from constants import (
    MILESTONES_PATH,
    FORBIDDEN_DIRECTORIES,
    FORBIDDEN_FILES,
    AssetViolation,
)

def find_asset_violations(repository_root: Path) -> list[AssetViolation]:
    """
    Return forbidden entries beneath evry milestone asset directory.
    *sounds spooky*
    """
    
    milestones_root = repository_root / MILESTONES_PATH
    if not milestones_root.is_dir(): return []
    
    violations: list[AssetViolation] = []
    asset_roots = sorted(path for path in milestones_root.glob("*/assets") if path.is_dir())
    
    for asset_root in asset_roots:
        for current_name, directory_names, file_names in os.walk(asset_root, followlinks=False):
            current_path = Path(current_name)
            
            for directory_name in sorted(directory_names):
                reason = FORBIDDEN_DIRECTORIES.get(directory_name)
                if reason is None: continue
                
                violations.append(
                    AssetViolation(
                        path=(current_path / directory_name).relative_to(repository_root),
                        reason=reason,
                    )
                )
                directory_names.remove(directory_name)
                
            for file_name in sorted(file_names):
                reason = FORBIDDEN_FILES.get(file_name)
                if reason is None: continue
                
                violations.append(
                    AssetViolation(
                        path=(current_path / file_name).relative_to(repository_root),
                        reason=reason,
                    )
                )
                
    return sorted(violations, key=lambda violation: (violation.path.as_posix(), violation.reason))

def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check milestone assets for copied repositories and generated trees."
    )
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="repository root to inspect (defaults to this repo),"
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repository_root = args.repository.resolve()
    violations = find_asset_violations(repository_root)
    
    if violations:
        print("FAIL milestone assets contain FORBIDDEN repository or generated content:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation.path.as_posix()}: {violation.reason}", file=sys.stderr)
        return 1
    
    print("PASS milestone assets contain no copied repos or generated trees, no seeds watering allowed")
    return 0

if __name__ == "__main__": raise SystemExit(main())
