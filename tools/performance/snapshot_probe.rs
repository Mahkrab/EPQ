//! Time canonical snapshot provenance on immutable production observations.
//! Loading, equivalence checks and write-call attribution stay outside timers.

use maelstrom::{math::Vec3, scene::Particle, workflow::SnapshotRecord};
use sha2::{Digest, Sha256};
use std::{fs, hint::black_box, path::Path, time::Instant};

fn hash(bytes: &[u8]) -> String {
    Sha256::digest(bytes).iter().map(|v| format!("{v:02x}")).collect()
}

fn digest_hex(digest: &[u8; 32]) -> String {
    digest.iter().map(|v| format!("{v:02x}")).collect()
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    let request: serde_json::Value = serde_json::from_slice(&fs::read(&args[1])?)?;
    let states = request["states"].as_array().ok_or("missing saved states")?;
    let ids: Vec<u64> = request["identities"].as_array().ok_or("missing identities")?
        .iter().map(|v| v.as_str().ok_or("invalid identity")?.parse().map_err(|_| "invalid decimal identity"))
        .collect::<Result<_, _>>()?;
    let mut snapshots = Vec::new();
    let mut lengths = Vec::new();
    for state in states {
        let path = Path::new(state["path"].as_str().ok_or("invalid native state path")?);
        let bytes = fs::read(path)?;
        let n = ids.len();
        if bytes.len() != n*24 || hash(&bytes) != state["state_sha256"].as_str().ok_or("missing state digest")? {
            return Err("saved native bytes changed".into());
        }
        let number = |offset: usize| f32::from_le_bytes(bytes[offset..offset+4].try_into().unwrap());
        let particles: Vec<_> = ids.iter().enumerate().map(|(i,id)| Particle {
            identity:*id,
            position_m:Vec3::new(number(i*12),number(i*12+4),number(i*12+8)),
            velocity_m_s:Vec3::new(number(n*12+i*12),number(n*12+i*12+4),number(n*12+i*12+8)),
        }).collect();
        let step = state["step"].as_str().ok_or("missing step")?.parse()?;
        let snapshot = SnapshotRecord::probe_native(&particles,step);
        let reference = snapshot.to_json()?;
        let specialised = snapshot.probe_canonical_bytes()?;
        if reference.as_bytes() != specialised || "sha256:".to_owned()+&hash(reference.as_bytes()) != state["snapshot_sha256"] {
            return Err("canonical bytes or original production provenance differs".into());
        }
        let digest = hash(reference.as_bytes());
        if digest_hex(&snapshot.probe_generic_hash()?) != digest || digest_hex(&snapshot.probe_specialised_hash()?) != digest {
            return Err("streamed provenance differs".into());
        }
        println!("{}",serde_json::json!({"kind":"equivalence","state":path,"step":step,
            "canonical_bytes":reference.len(),"snapshot_sha256":digest,
            "write_calls":snapshot.probe_write_counts()?}));
        lengths.push(reference.len());
        snapshots.push(snapshot);
    }
    // Rotate all implementations together; the warm-up is retained but excluded
    // from measured comparisons. Nothing is memoised between timed operations.
    let algorithms = ["original","reserved","generic_stream","specialised_stream","format_only","sha_only"];
    let canonical: Vec<_> = snapshots.iter().map(SnapshotRecord::to_json).collect::<Result<_,_>>()?;
    for repeat in 0..6 {
        for offset in 0..algorithms.len() {
            let algorithm = algorithms[(repeat+offset)%algorithms.len()];
            let start = Instant::now();
            for (i,snapshot) in snapshots.iter().enumerate() {
                match algorithm {
                    "original" => { let text = snapshot.to_json()?; black_box(Sha256::digest(black_box(text.as_bytes()))); }
                    "reserved" => { let text = snapshot.probe_reserved(lengths[i])?; black_box(Sha256::digest(black_box(&text))); }
                    "generic_stream" => { black_box(snapshot.probe_generic_hash()?); }
                    "specialised_stream" => { black_box(snapshot.probe_specialised_hash()?); }
                    "format_only" => { black_box(snapshot.to_json()?); }
                    "sha_only" => { black_box(Sha256::digest(black_box(canonical[i].as_bytes()))); }
                    _ => unreachable!(),
                }
            }
            println!("{}",serde_json::json!({"kind":"timing","algorithm":algorithm,"repeat":repeat,
                "warmup":repeat==0,"elapsed_s":start.elapsed().as_secs_f64(),
                "snapshots":snapshots.len(),"canonical_bytes":lengths.iter().sum::<usize>()}));
        }
    }
    Ok(())
}
