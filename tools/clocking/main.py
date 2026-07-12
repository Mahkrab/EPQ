#!/usr/bin/env python3

from pathlib import Path
import argparse
import math
import sys

from session import read_active_session, write_active_session, parse_started
from parser import build_parser
from helpers.times import now
from helpers.format import format_week_id
from constants import weekly_log_path, STATE_FILE, REPO_ROOT

def create_weekly_log(path: Path, week_id: str) -> None:
    """
    Creates a new weekly log, with the same template seen in `TEMPLATE.md`.
    Automatically writes the week_id to this weekly log. 
    """
    path.write_text(
        f"""# EPQ Development Log - Week {week_id}

## Time spent

| Date     | Time (Mins) |
| -------- | ----------- |

## Intentions

#### Initial:

* 
*
*

#### Added:
 *
 *
 *

## Problems faced

*
*
*

## Work completed

*
*
*
""",
        encoding="utf-8",
    )
    
def append_time_row(path: Path, session_date: str, minutes: int) -> None:
    """
    Appends the finished session time to the bottom of the `Time spent` table.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    row = f"| {session_date} | {minutes:^11} |" # Centres the minutes in a column exactly 11 characters wide.
    
    try:
        section_start = next(index for index, line in enumerate(lines) if line.strip() == "## Time spent")
    except StopIteration as error:
        raise SystemExit(f"{path} does not contain a '## Time spent' section.") from error
    
    next_section = len(lines)
    
    for index in range(section_start + 1, len(lines)):
        if lines[index].startswith("## "):
            next_section = index
            break 
        
    cleaned = [
        line
        for line in lines[:next_section]
        if not line.strip().startswith("| DD/MM/YY |")
    ]
    cleaned.extend(lines[next_section:])
    lines = cleaned
    
    try: section_start = next(index for index, line in enumerate(lines) if line.strip() == "## Time spent")
    except StopIteration: raise SystemExit(f"{path} does not contain a '## Time spent' section.")
    
    next_section = len(lines)
    for index in range(section_start + 1, len(lines)):
        if lines[index].startswith("## "):
            next_section = index
            break
        
    insert_at = next_section
    while insert_at > section_start and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    
    lines.insert(insert_at, row)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

def display_path(path: Path) -> Path:
    """
    Shortens a path to show it from the project root folder.
    """
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path
    
def clock_in(_: argparse.Namespace) -> int:
    """
    Gets the active session as a string of json *poor jason*.
    If there is already an active session, prints the time previsouly clocked in. 
    Else writes the time started to the session statefile.
    """
    active_session = read_active_session()
    if active_session is not None:
        started_at = parse_started(active_session)
        print(f"Already clocked in at {started_at:%d/%m/%y %H:%M}.")
        return 1
    
    started_at = now()
    write_active_session(started_at)
    print(f"Clocked in at {started_at:%d/%m/%y %H:%M} ({format_week_id(started_at)}).")
    return 0

def clock_out(_: argparse.Namespace) -> int:
    """
    Reads the active session.
    If there is no active session, exits.
    Calculates the elapsed time. 
    """
    active_session = read_active_session()
    if active_session is None:
        print("No active EPQ clock session.")
        return 1
    
    started_at = parse_started(active_session)
    finished_at = now()
    time_taken_s = max(0, (finished_at - started_at).total_seconds())
    minutes = max(1, math.ceil(time_taken_s / 60))
    
    log_path = weekly_log_path(started_at)
    if not log_path.exists(): create_weekly_log(log_path, format_week_id(started_at))
    
    append_time_row(log_path, started_at.strftime("%d/%m/%y"), minutes)
    STATE_FILE.unlink()
    
    print(
        "Clocked out at "
        f"{finished_at:%d/%m/%y %H:%M}; logged {minutes} minute"
        f"{'' if minutes == 1 else 's'} to {display_path(log_path)}."
    )
    return 0

def status(_: argparse.Namespace) -> int:
    active_session = read_active_session()
    if active_session is None:
        print("No active EPQ clock session.")
        return 1
    
    started_at = parse_started(active_session)
    time_taken_s = max(0, (now() - started_at).total_seconds())
    minutes = max(1, math.ceil(time_taken_s / 60))
    print(
        f"Clocked in since {started_at:%d/%m/%y %H:%M}; "
        f"current duration is {minutes} minute"
        f"{'' if minutes == 1 else 's'}."
    )
    return 0

def cancel(_: argparse.Namespace) -> int:
    """
    Removes the state file without logging. 
    """
    if not STATE_FILE.exists():
        print("No active EPQ clock session.")
        return 1
    
    STATE_FILE.unlink()
    print("Cancelled the active EPQ clock session without logging it.")
    return 0

def main() -> int:
    parser = build_parser(clock_in, clock_out, status, cancel)
    args = parser.parse_args()
    return args.func(args)

# Boilerplae for showing this is executable. 
if __name__ == "__main__":
    sys.exit(main())
