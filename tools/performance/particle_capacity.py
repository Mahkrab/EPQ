"""Check every one-second interval from exact accepted-step completion timestamps.

The count is a step function. Its one-second difference changes only at an
acceptance or one second before an acceptance, so those boundaries and their
neighbouring nanoseconds cover the entire continuous measurement interval.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import csv
import json
import math
from pathlib import Path


def assess(path: Path, target: int, timestep_s: float) -> dict:
    if not 1<=target<1_000_000 or not math.isfinite(timestep_s) or timestep_s<=0:
        raise ValueError("require a bounded positive step count and finite positive timestep")
    with path.open(encoding="utf-8",newline="") as stream:
        rows=list(csv.DictReader(stream))
    indices=[int(row["step"]) for row in rows]
    times=[int(row["wall_ns"]) for row in rows]
    if indices!=list(range(target+1)) or not times or times[0]!=0:
        raise ValueError("acceptance trace is incomplete or skips required steps")
    if any(b<=a for a,b in zip(times,times[1:])):
        raise ValueError("acceptance timestamps must be strictly increasing")
    duration=times[-1];second=1_000_000_000
    if duration<second:
        raise ValueError("capacity qualification needs a full measured second")
    last=duration-second
    events={0,last}
    for t in times:
        for event in (t,t-second):
            events.update(x for x in (event-1,event,event+1) if 0<=x<=last)
    worst=target+1;worst_start=0
    for start in sorted(events):
        count=bisect_right(times,start+second)-bisect_right(times,start)
        if count<worst:worst=count;worst_start=start
    rate=target*timestep_s/(duration/second)
    minimum=worst*timestep_s
    return dict(accepted_steps=target,duration_s=duration/second,
                simulated_s_per_wall_s=rate,minimum_steps_in_one_second=worst,
                minimum_simulated_s_in_one_second=minimum,worst_window_start_s=worst_start/second,
                qualifies=rate>=1 and minimum>=1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace",type=Path);parser.add_argument("--steps",type=int,default=4800)
    args=parser.parse_args()
    try:
        print(json.dumps(assess(args.trace,args.steps,0.004166666883975267),indent=2))
    except (OSError,ValueError,KeyError) as error:
        parser.exit(1,f"particle capacity: {error}\n")


if __name__=="__main__":
    main()
