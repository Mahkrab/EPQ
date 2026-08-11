from pathlib import Path
from dataclasses import dataclass

MILESTONES_PATH = Path("docs/project/development/milestones")

FORBIDDEN_DIRECTORIES = {
    ".git": "repository metadata",
    ".mypy_cache": "generated cache",
    ".pytest_cache": "generated cache",
    ".ruff_cache": "generated cache",
    ".venv": "dependency environment",
    "__pycache__": "generated cache",
    "node_modules": "dependency cache",
    "src": "copied source tree",
    "target": "generated build tree",
    "tests": "copied test tree",
    "achive": "arhived files",
}

FORBIDDEN_FILES = {
    ".git": "repository metadata",
    ".gitmodules": "repository metadata",
}

@dataclass(frozen=True)
class AssetViolation:
    path: Path
    reason: str