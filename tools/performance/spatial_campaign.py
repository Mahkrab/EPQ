"""Collect immutable spatial studies on durable storage, without timing audits.

The executable owns solver-only timings. Observation compression and subsequent
independent analysis are separate, and every completed or failed raw stream is
retained with a readback checksum before another request starts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from tools.performance.convergence_campaign import digest, persist, pin_binary


def run(root: Path, binary: Path, label: str, *, scene: str = "collision", n: int = 6,
        layers: float = 1, dt: float | None = None, duration: float = 6,
        iterations: int = 8, boundary: bool = True, inset: float = .5,
        threads: int = 8, timeout: int = 7200) -> dict:
    destination=root/"runs"/label
    destination.mkdir(parents=True,exist_ok=False)
    dt=dt if dt is not None else (1/240)*(6/n)
    solver=pin_binary(binary)
    parameters=dict(scene=scene,n=n,layers=layers,dt=dt,duration=duration,
                    iterations=iterations,boundary=boundary,inset_fraction=inset,threads=threads)
    command=[str(solver),scene,str(n),str(layers),str(dt),str(duration),str(iterations),str(int(boundary)),str(inset),str(threads)]
    persist(destination/"request.json",{"parameters":parameters,"command":command,
        "solver_sha256":digest(solver),"protocol_sha256":digest(root/"protocol.json"),
        "started_utc":datetime.now(timezone.utc).isoformat(),"timeout_s":timeout})
    raw=destination/"states.bin"
    timed_out=False
    with raw.open("xb") as stdout,(destination/"stderr.txt").open("xb") as stderr:
        try:
            result=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=timeout)
            code=result.returncode
        except subprocess.TimeoutExpired:
            code=None
            timed_out=True
        stdout.flush();os.fsync(stdout.fileno())
        stderr.flush();os.fsync(stderr.fileno())
    checksum=digest(raw)
    compressed=destination/"states.bin.gz"
    with raw.open("rb") as source,compressed.open("xb") as output:
        with gzip.GzipFile(fileobj=output,mode="wb",mtime=0) as target:
            shutil.copyfileobj(source,target)
        output.flush();os.fsync(output.fileno())
    with gzip.open(compressed,"rb") as source:
        if hashlib.file_digest(source,"sha256").hexdigest()!=checksum:
            raise RuntimeError("compressed raw readback differs")
    size=raw.stat().st_size
    raw.unlink()
    stderr_text=(destination/"stderr.txt").read_text()
    metrics=json.loads(stderr_text.splitlines()[-1]) if code==0 else None
    record={"exit_code":code,"timed_out":timed_out,"raw_sha256":checksum,
            "raw_bytes":size,"gzip_sha256":digest(compressed),"solver_metrics":metrics,
            "finished_utc":datetime.now(timezone.utc).isoformat()}
    persist(destination/"collection.json",record)
    print(label,"exit",code,"solver",metrics,flush=True)
    return record


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    parser.add_argument("binary",type=Path)
    parser.add_argument("phase",choices=("ladder","flat","controls","depth","timing"))
    args=parser.parse_args()
    root,binary=args.root.resolve(),args.binary.resolve()
    if args.phase == "ladder":
        for n in (6,12,18,24):
            run(root,binary,f"ladder-n{n}",n=n)
    elif args.phase=="flat":
        for n in (6,12,18):run(root,binary,f"valid-flat-n{n}",n=n,scene="flat-valid")
    elif args.phase=="controls":
        for n in (6,12):
            for inset in (0,.25):
                run(root,binary,f"inset{inset}-n{n}",n=n,inset=inset)
            run(root,binary,f"no-wall-n{n}",n=n,boundary=False)
    elif args.phase=="depth":
        for layers in (1,2,3,4):
            run(root,binary,f"depth-layers{layers}",scene="depth-valid",n=12,layers=layers)
    else:
        for sample in range(6):
            for n in ((6,12,18,24) if sample%2==0 else (24,18,12,6)):
                run(root,binary,f"timing-{sample}-n{n}",n=n,duration=.5)


if __name__=="__main__":
    main()
