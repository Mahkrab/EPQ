"""Keep machine readings outside a solver invocation's measurement boundary.

GPU readings can be unavailable on WSL; preserve their failures. Linux counters
do not establish what other Windows applications were doing.
"""

from pathlib import Path

from .capture import invoke, utc, write_json


def capture(source: Path, destination: Path) -> None:
    """Retain one GPU reading and the accompanying Linux counters."""
    invoke(["nvidia-smi", "--query-gpu=pstate,utilization.gpu,utilization.memory,temperature.gpu,clocks.sm,clocks.mem,power.draw,clocks_event_reasons.active",
            "--format=csv,noheader,nounits"], source, destination / "gpu", timeout=30, grace=5)
    write_json(destination / "linux.json", {"observed_utc": utc(),
        "cpu_counters": Path("/proc/stat").read_text(), "load": Path("/proc/loadavg").read_text(),
        "scope": "Linux counters only; not a complete view of Windows workload"})
