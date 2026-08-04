import argparse, os

try:
    from .constants import (
        FILES,
        DEFAULT_ENDPOINT
    )
except ImportError:
    from constants import (
        FILES,
        DEFAULT_ENDPOINT
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files",
        nargs="*",
        default=list(FILES),
        help="Markdown files to check (defaults to the Milestone 00 documents)",
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("GITHUB_MARKDOWN_ENDPOINT", DEFAULT_ENDPOINT),
        help="GitHub Markdown GFM endpoint (or GITHUB_MARKDOWN_ENDPOINT)",
    )
    return parser.parse_args(argv)
