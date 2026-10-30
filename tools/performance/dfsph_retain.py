"""Freeze DFSPH raw observations and experiment sources, then verify the seal.

The hard-link staging directory captures immutable completed runs. Native source
exports, build caches and executables stay outside the documentation archive;
their pinned source identities, build recipes and binary hashes are retained.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
if __package__:
    from .frontier_retain import seal
else:
    from frontier_retain import seal


def retain(root):
    excluded={'source','build','target','__pycache__','seal-input','retained'}
    paths=[p for p in sorted(root.rglob('*')) if p.is_file() and not any(k in excluded for k in p.relative_to(root).parts)]
    stage=root/'seal-input';stage.mkdir(exist_ok=False);omitted=[]
    for path in paths:
        if path.suffix in ['.o','.a','.so'] or path.name=='seal.log':continue
        with path.open('rb') as f:magic=f.read(4)
        if magic==b'\x7fELF':
            omitted.append({'name':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reason':'executable/build artifact; recipe and source retained'});continue
        name=path.relative_to(root);destination=stage/name;destination.parent.mkdir(parents=True,exist_ok=True);os.link(path,destination)
    (stage/'excluded-executables.json').write_text(json.dumps(omitted,indent=2)+'\n')
    seal(stage,root/'retained')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);retain(p.parse_args().root.resolve())
