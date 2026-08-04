#!/usr/bin/env python3

from  __future__ import annotations

import argparse, json, os, sys, urllib.error, urllib.request
from pathlib import Path

try:
    from .constants import (
        MATH_OPEN_RE,
        MATH_HTML_RE,
        DEFAULT_API_VERSION,
        DEFAULT_ENDPOINT
    )
    from .parse import parse_args
except ImportError:
    from constants import (
        MATH_OPEN_RE,
        MATH_HTML_RE,
        DEFAULT_API_VERSION,
        DEFAULT_ENDPOINT
    )
    from parse import parse_args


def lint_markdown(text: str) -> list[str]:
    errors: list[str] = [] # List to store found errors. 
    if "$$" in text: errors.append("uses $$ display delimiters; use fenced ```math blocks") # Appends erorr if $$ is used, which github does not allow: GHerror.
    if r"\begin{cases}" in text or r"\end{cases}" in text: errors.append("uses a cases environment; use separate conditional equations") # Appends error if cases environment is used: GHerror.
    
    in_math = False # Flag to track whether we are in a math block. Denoted by ```math.
    math_blocks = 0
    
    for line in text.splitlines():
        if not in_math and MATH_OPEN_RE.match(line):
            in_math = True
            math_blocks += 1 # Increments thr count.
        elif in_math and line.strip() == "```": in_math = False # The end of a math block. 
        
    if in_math: errors.append("unfinished ``` math blokc") # Appends error if a math block is not closed. 
    if math_blocks == 0: errors.append("contains no fenced ``` math blocks") # Appends error if no math blocks are found, which is required for github to render math.
    
    return errors

def count_math_blocks(text: str) -> int:
    return sum(1 for line in text.splitlines() if MATH_OPEN_RE.match(line)) # Returns the count of math blocks by counting the number of lines that match the opening math block regex.

def count_rendered_math_blocks(html: str) -> int:
    return len(MATH_HTML_RE.findall(html)) # Returns the count of rendered math blocks by finding all matches of the math HTML regex in the rendered HTML.

def render(text: str, endpoint: str, token: str | None) -> str:
    payload = json.dumps({"text": text, "mode": "gfm"}).encode("utf-8") # Prepares the payload for the POST request to the GitHub Markdown API, encoding it as JSON.
    request = urllib.request.Request( 
        endpoint,
        data=payload,
        method="POST",
        headers={
            "Accept": "text/html",
            "Content-Type": "application/json",
            "X-Github-API-Version": os.environ.get(
                "GITHUB_API_VERSION", DEFAULT_API_VERSION
            ),
            "User-Agent": "EPQ-github-markdown-check",
        },
    )
    if token: request.add_header("Authorization", f"Bearer {token}") # Adds the authorsation header if a token is provided, allowing acces to the Github API.
    
    try: 
        with urllib.request.urlopen(request, timeout=30) as response: return response.read().decode("utf-8")
    except urllib.error.HTTPError as error: 
        detail = error.read().decode("utf-8")
        raise RuntimeError(
            f"Github Markdown endpoint returned HTTP {error.code}: {detail or error.reason}"
        ) from error
    except urllib.error.URLError as error: raise RuntimeError(f"could not reach Github MArkdown endpoint: {error.reason}") from error
    

def check_file(path: Path, endpoint: str, token: str | None) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error: return [f"{path}: cannot read file: {error}"] 

    failures = [f"{path}: {error}" for error in lint_markdown(text)] # Run the raw markdown through the linter to catrch syntax bugs. 
    if failures: return failures # Stop and return early if any linting errors are found.

    try: rendered = render(text, endpoint, token) # Send the markdown content to the API endpoint to generate the HTML output. 
    except RuntimeError as error: return [f"{path}: {error}"]

    # Count the math blocks in the source text vs the final rendered HTML.
    expected = count_math_blocks(text) 
    actual = count_rendered_math_blocks(rendered)
    # Verify that the GitHub render did not drop or break any math formatting. 
    if actual != expected:
        return [
            f"{path}: GitHub preserved {actual} math fences, expected {expected}"
        ]

    print(f"PASS {path}: GitHub preserved {actual} fenced math block(s)")
    return []

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    token = os.environ.get("GITHUB_TOKEN")
    failures: list[str] = []
    for filename in args.files:
        failures.extend(check_file(Path(filename), args.endpoint, token))

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
