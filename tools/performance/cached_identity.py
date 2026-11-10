"""Reject source exports whose executable embeds another tree's source digest.

Build.rs hashes component-ordered paths, lengths and contents. Repeating that
contract independently also catches a successful Cargo build using stale artefacts.
"""
import argparse
import hashlib
import json
from pathlib import Path


def source(root: Path) -> dict:
    paths=[root/name for name in ["Cargo.toml","Cargo.lock","build.rs"]]
    for directory in ["src","native","build_support","scenes","config"]:
        paths.extend(p for p in (root/directory).rglob("*") if p.is_file())
    digest=hashlib.sha256()
    files={}
    for path in sorted(paths,key=lambda p:p.relative_to(root).parts):
        name=path.relative_to(root).as_posix()
        data=path.read_bytes()
        files[name]=hashlib.sha256(data).hexdigest()
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(len(data).to_bytes(8,"little"))
        digest.update(data)
    return dict(source_sha256="sha256:"+digest.hexdigest(),files=files)


def check(root: Path, variant: str) -> dict:
    expected=source(root/variant)
    binary=root/f"{variant}-maelstrom"
    data=binary.read_bytes()
    if expected["source_sha256"].encode() not in data:
        raise ValueError(f"{variant}: executable does not embed its expected source identity")
    ptx={hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/"target/release/build").glob("maelstrom-*/out/*.ptx") if p.read_bytes() in data}
    if len(ptx)!=1:
        raise ValueError(f"{variant}: expected one distinct current embedded PTX")
    return dict(**expected,binary_sha256=hashlib.sha256(data).hexdigest(),ptx_sha256=ptx.pop())


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    parser.add_argument("variants",nargs="+",choices=["control","candidate","delivery","gpu-probe","final"])
    args=parser.parse_args()
    result={variant:check(args.root.resolve(),variant) for variant in args.variants}
    (args.root/"source-binary-identity.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({name:{k:v for k,v in row.items() if k!="files"} for name,row in result.items()},indent=2))
