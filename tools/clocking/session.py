import json
from datetime import datetime
from constants import STATE_FILE, STATE_DIR, REPO_ROOT
from helpers.times import local_tz

def read_active_session() -> dict[str, str] | None: 
    """
    Reads the active session.
    If no session is active returns `None`.
    Returns the string returned by `json.loads`.
    """
    if not STATE_FILE.exists(): return None
    try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise SystemExit(
        f"Could not read active EPQ clock session: {error}"
    ) from error
    
def write_active_session(started: datetime) -> None:
    """
    Writes the json `payload` to the `STATE_FILE`
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "started": started.isoformat(),
        "repo_root": str(REPO_ROOT),
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

def parse_started(session: dict[str, str]) -> datetime:
    """
    Returns the sessions `started` `datetime`.
    """
    raw = session.get("started")
    if not raw: raise SystemExit("Active EPQ clock session is missing its start time.")
    try: started = datetime.fromisoformat(raw)
    except ValueError as error:
        raise SystemExit(
            f"Active EPQ clock session has an invalid start time: {raw}"
        ) from error
    if started.tzinfo is None: started = started.replace(tzinfo=local_tz())
    return started.astimezone(local_tz())
