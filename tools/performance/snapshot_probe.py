"""Prepare isolated provenance probes without exposing benchmark APIs in production.

Saved native states and old per-frame snapshot hashes establish the independent
input and provenance boundary. Loading and byte checks are outside probe timers.
"""

from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import statistics


def prepare(source: Path, output: Path) -> None:
    shutil.copytree(source, output)
    module = output / "src/workflow/snapshot_json.rs"
    with module.open("a", encoding="utf-8") as stream:
        stream.write(WRAPPERS)
    binary = output / "src/bin/snapshot-probe.rs"
    binary.parent.mkdir(exist_ok=True)
    binary.write_bytes(Path(__file__).with_suffix(".rs").read_bytes())


def requests(previous: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for scene in ("resolved", "large"):
        for mode in ("reference", "fast"):
            manifest = json.loads((previous / "compiled" / f"{scene}-r3-{mode}" / "bundle/manifest.json").read_bytes())
            frames = {int(f["step"]): f for f in manifest["frames"]}
            native = previous / "runs" / f"physical-{scene}-{mode}"
            states = sorted((p for p in native.glob("state-*.bin") if p.stem.removeprefix("state-").isdecimal()),
                            key=lambda p: int(p.stem.split("-")[-1]))
            states = [p for p in states if int(p.stem.split("-")[-1]) in frames]
            request = dict(identities=[p["identity"] for p in manifest["input"]["particles"]], states=[dict(
                path=str(p), step=frames[int(p.stem.split("-")[-1])]["step"],
                state_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                snapshot_sha256=frames[int(p.stem.split("-")[-1])]["snapshot_sha256"],
            ) for p in states])
            (output / f"{scene}-{mode}.json").write_text(json.dumps(request, indent=2)+"\n", encoding="utf-8")


def assess(root: Path) -> list[dict]:
    summaries = []
    for path in sorted((root / "micro").glob("*.jsonl")):
        request = json.loads((root / "requests" / (path.stem+".json")).read_bytes())
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        checks = [r for r in records if r["kind"] == "equivalence"]
        timings = [r for r in records if r["kind"] == "timing"]
        if len(checks) != 21 or len(timings) != 36:
            raise ValueError("incomplete microbenchmark collection")
        expected = {s["path"]:s for s in request["states"]}
        if len(expected) != 21 or {r["state"] for r in checks} != set(expected):
            raise ValueError("saved-state coverage differs")
        for row in checks:
            state = expected[row["state"]]
            if str(row["step"]) != state["step"] or "sha256:"+row["snapshot_sha256"] != state["snapshot_sha256"]:
                raise ValueError("snapshot provenance differs from the production record")
            counts = row["write_calls"]
            if row["canonical_bytes"] <= 0 or any(counts[k]["bytes"] != row["canonical_bytes"] for k in ("generic","specialised")):
                raise ValueError("byte counts differ between serializers")
        algorithms = ["original","reserved","generic_stream","specialised_stream","format_only","sha_only"]
        observed = {(r["algorithm"],r["repeat"]) for r in timings}
        if observed != {(a,i) for a in algorithms for i in range(6)}:
            raise ValueError("missing or duplicate timing identity")
        total = sum(r["canonical_bytes"] for r in checks)
        for row in timings:
            if (row["warmup"] != (row["repeat"] == 0) or row["snapshots"] != 21
                    or row["canonical_bytes"] != total or not math.isfinite(row["elapsed_s"]) or row["elapsed_s"] <= 0):
                raise ValueError("invalid timing or workload boundary")
        measured = [r for r in timings if not r["warmup"]]
        medians = {a: statistics.median(r["elapsed_s"] for r in measured if r["algorithm"] == a) for a in algorithms}
        summaries.append(dict(case=path.stem, snapshots=21,
            medians_s=medians, samples_s={a:[r["elapsed_s"] for r in measured if r["algorithm"]==a] for a in algorithms},
            speedups={a:medians["original"]/medians[a] for a in algorithms},
            canonical_bytes=sum(r["canonical_bytes"] for r in checks), first_state_write_counts=checks[0]["write_calls"]))
    (root / "micro-summary.json").write_text(json.dumps(summaries,indent=2)+"\n",encoding="utf-8")
    return summaries


WRAPPERS = r'''
impl SnapshotRecord {
    pub fn probe_native(particles: &[crate::scene::Particle], step:u64) -> Self {
        Self {schema_version:1,completed_steps:step,particles:particles.iter().map(super::ParticleRecord::from).collect()}
    }
    pub fn probe_canonical_bytes(&self) -> Result<Vec<u8>,RecordError> {
        let mut bytes=Vec::new(); self.write_canonical_json(&mut bytes)?; Ok(bytes)
    }
    pub fn probe_specialised_hash(&self) -> Result<[u8;32],RecordError> { self.canonical_sha256() }
    pub fn probe_generic_hash(&self) -> Result<[u8;32],RecordError> {
        self.validate()?;
        let mut hash=HashWriter(Sha256::new());
        { let mut writer=BufWriter::with_capacity(64*1024,&mut hash);
          serde_json::to_writer_pretty(&mut writer,self)?;
          writer.flush().map_err(serde_json::Error::io)?; }
        Ok(hash.0.finalize().into())
    }
    pub fn probe_reserved(&self, capacity:usize) -> Result<Vec<u8>,RecordError> {
        self.validate()?; let mut bytes=Vec::with_capacity(capacity);
        serde_json::to_writer_pretty(&mut bytes,self)?; Ok(bytes)
    }
    pub fn probe_write_counts(&self) -> Result<serde_json::Value,RecordError> {
        #[derive(Default)] struct Count {bytes:usize,calls:usize,tiny:usize}
        impl Write for Count {
            fn write(&mut self,bytes:&[u8])->io::Result<usize>{self.bytes+=bytes.len();self.calls+=1;self.tiny+=usize::from(bytes.len()<=2);Ok(bytes.len())}
            fn flush(&mut self)->io::Result<()>{Ok(())}
        }
        let mut generic=Count::default();serde_json::to_writer_pretty(&mut generic,self)?;
        let mut specialised=Count::default();self.write_canonical_json(&mut specialised)?;
        Ok(serde_json::json!({"generic":{"bytes":generic.bytes,"calls":generic.calls,"tiny_calls":generic.tiny},
            "specialised":{"bytes":specialised.bytes,"calls":specialised.calls,"tiny_calls":specialised.tiny}}))
    }
}
'''


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("destination",type=Path)
    args=parser.parse_args()
    prepare(args.source,args.destination)
