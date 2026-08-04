import re

FILES = (
    "docs/project/development/milestones/00/explation.md",
    "docs/project/development/milestones/00/serial-brute-force.md",
)
DEFAULT_ENDPOINT = "https://api.github.com/markdown"
DEFAULT_API_VERSION = "2026-03-10"
MATH_OPEN_RE = re.compile(r"^[ \t]*```math[ \t]*$")
MATH_HTML_RE = re.compile(
    r"<math-renderer\b[^>]*\bclass=[\"'][^\"']*\bjs-display-math\b",
    re.IGNORECASE,
)
