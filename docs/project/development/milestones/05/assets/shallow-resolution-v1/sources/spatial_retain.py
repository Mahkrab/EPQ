"""Verify complete raw streams without relying on a successful archive transfer."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct


def verify(root):
    records={}
    for path in sorted((root/"runs").glob("*/collection.json")):
        d=path.parent;c=json.loads(path.read_text());request=json.loads((d/"request.json").read_text())
        compressed=d/"states.bin.gz"
        with compressed.open("rb") as f:
            if hashlib.file_digest(f,"sha256").hexdigest()!=c["gzip_sha256"]:raise ValueError("compressed hash differs")
        digest=hashlib.sha256();count=0
        with gzip.open(compressed,"rb") as f:
            def read(n):
                value=f.read(n);digest.update(value)
                if len(value)!=n:raise ValueError("truncated raw observation")
                return value
            magic,n,w,steps=struct.unpack("<4I",read(16))
            if magic!=0x50424634:raise ValueError("unexpected observation schema")
            constants=struct.unpack("<11d",read(88))
            read(w*24)
            previous=-1;last=-1;observed_steps=[]
            while True:
                head=f.read(4)
                if not head:break
                digest.update(head)
                if len(head)!=4:raise ValueError("truncated step")
                step=struct.unpack("<I",head)[0]
                if step<=previous:raise ValueError("unordered observation")
                read(n*48);count+=1;previous=step;last=step;observed_steps.append(step)
        if digest.hexdigest()!=c["raw_sha256"]:raise ValueError("raw checksum differs")
        if c["exit_code"]==0 and last!=steps:raise ValueError("missing final observation")
        stride=max(1,round(.05/constants[0]));expected=1+steps//stride+int(steps%stride!=0)
        if c["exit_code"]==0 and count!=expected:raise ValueError("missing scheduled observation")
        schedule=list(range(0,steps+1,stride))
        if schedule[-1]!=steps:schedule.append(steps)
        if c["exit_code"]==0 and observed_steps!=schedule:raise ValueError("observation steps differ from schedule")
        records[d.name]={"raw_sha256":c["raw_sha256"],"gzip_sha256":c["gzip_sha256"],
            "observations":count,"complete":last==steps,"raw_bytes":c["raw_bytes"],
            "particles":n,"mass_kg":n*constants[3],"duration_s":steps*constants[0],
            "request_scene":request["parameters"]["scene"]}
    result={"runs":records,"all_checksums_and_schedules_valid":True,
            "complete_streams":sum(r["complete"] for r in records.values()),
            "retained_incomplete_streams":sum(not r["complete"] for r in records.values()),
            "total_observations":sum(r["observations"] for r in records.values()),
            "total_raw_bytes":sum(r["raw_bytes"] for r in records.values())}
    (root/"readback.json").write_text(json.dumps(result,indent=2)+"\n")
    print({k:v for k,v in result.items() if k!="runs"})
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("root",type=Path)
    verify(parser.parse_args().root)
