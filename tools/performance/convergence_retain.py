"""Read every retained observation back before claiming durable evidence."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

from tools.performance.convergence_campaign import digest


def verify(root: Path, auditor: Path, scratch: Path) -> dict:
    scratch.mkdir(parents=True,exist_ok=True)
    records={}
    for summary_path in sorted((root/"runs").glob("*/summary.json")):
        directory=summary_path.parent
        summary=json.loads(summary_path.read_text())
        compressed=directory/"states.bin.gz"
        if digest(compressed)!=summary["gzip_sha256"]:
            raise ValueError(f"compressed observation differs: {directory.name}")
        raw=scratch/(directory.name+".bin")
        checksum=hashlib.sha256()
        count=0
        with gzip.open(compressed,"rb") as src,raw.open("xb") as dst:
            for block in iter(lambda:src.read(1024*1024),b""):
                checksum.update(block)
                count+=len(block)
                dst.write(block)
        if checksum.hexdigest()!=summary["raw_sha256"]:
            raise ValueError(f"raw observation differs: {directory.name}")
        record={"raw_bytes":count,"raw_sha256":checksum.hexdigest(),"gzip_sha256":digest(compressed),
                "complete":summary["exit_code"]==0,"auditor_sha256":digest(auditor)}
        if summary["exit_code"]==0:
            destination=directory/"readback-audit.jsonl"
            request=json.loads((directory/"request.json").read_text())
            with destination.open("xb") as stdout:
                process=subprocess.run([str(auditor),str(raw),str(int(request["parameters"]["boundary"]))],
                                       stdout=stdout,capture_output=False,check=True,timeout=600)
            audited=[json.loads(line) for line in destination.read_text().splitlines()]
            if len(audited)!=summary["observations"]:
                raise ValueError(f"observation count differs: {directory.name}")
            original=[json.loads(line) for line in (directory/"audit.jsonl").read_text().splitlines()]
            different=[]
            for index,(old,new) in enumerate(zip(original,audited)):
                for key in old.keys() & new.keys():
                    if old[key]!=new[key]:
                        different.append([index,key])
            record.update(observations=len(audited),common_field_differences=different,
                          readback_audit_sha256=digest(destination))
        raw.unlink()
        records[directory.name]=record
        print("verified",directory.name,flush=True)
    result={"runs":records,"all_raw_hashes_verified":True,
            "successful_runs":sum(r["complete"] for r in records.values()),
            "failed_runs_with_retained_raw":sum(not r["complete"] for r in records.values()),
            "raw_bytes":sum(r["raw_bytes"] for r in records.values())}
    (root/"readback.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    parser.add_argument("auditor",type=Path)
    parser.add_argument("scratch",type=Path)
    args=parser.parse_args()
    verify(args.root.resolve(),args.auditor.resolve(),args.scratch.resolve())
