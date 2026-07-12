from datetime import datetime
from pathlib import Path
import os

from helpers.format import format_week_id

REPO_ROOT: Path = Path(__file__).resolve().parents[2] # The root of the `EPQ` repo.
WEEKLY_DIR: Path = REPO_ROOT / "docs" / "log" / "weekly" # The path to the weeklt logging directory. 
STATE_DIR: Path = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "epq-clock" # Path to the state logging directory. 
STATE_FILE: Path = STATE_DIR / "session.json" # File in which current state is stored. 

def weekly_log_path(value: datetime) -> Path: 
    """
    Returns the path to the weeks .md file
    """
    return WEEKLY_DIR / f"{format_week_id(value)}.md"
