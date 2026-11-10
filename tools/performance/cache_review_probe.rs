//! Isolated cache experiment using the existing solver, offscreen renderer and
//! encoder. This is a measurement harness, not a supported cache or bundle format.

use super::*;
use crate::{math::Vec3, scene::Particle, workflow::StepDiagnostic};
use std::path::PathBuf;

fn frame_bytes(snapshot: &SnapshotRecord) -> Vec<u8> {
    let mut bytes = Vec::with_capacity(24 + snapshot.particles().len() * 24);
    bytes.extend_from_slice(b"MSCPRB01");
    bytes.extend_from_slice(&snapshot.completed_steps().to_le_bytes());
    bytes.extend_from_slice(&(snapshot.particles().len() as u64).to_le_bytes());
    for record in snapshot.particles() {
        let p = record.particle();
        for value in [p.position_m.x, p.position_m.y, p.position_m.z,
                      p.velocity_m_s.x, p.velocity_m_s.y, p.velocity_m_s.z] {
            bytes.extend_from_slice(&value.to_bits().to_le_bytes());
        }
    }
    bytes
}

fn read_frame(root: &Path, entry: &Value, scene: &ResolvedScene) -> Result<SnapshotRecord, ExportError> {
    let index = entry["index"].as_u64().ok_or_else(|| fail("invalid index"))?;
    let bytes = fs::read(root.join(format!("frame-{index:08}.bin"))).map_err(fail)?;
    let expected_len = scene.particles.len().checked_mul(24).and_then(|n| n.checked_add(24))
        .ok_or_else(|| fail("frame length overflow"))?;
    if bytes.len() != expected_len || &bytes[..8] != b"MSCPRB01" || hash(&bytes) != entry["binary_sha256"] {
        return Err(fail("cache frame length, magic or digest mismatch"));
    }
    let integer = |start| u64::from_le_bytes(bytes[start..start+8].try_into().unwrap());
    let step = integer(8);
    if integer(16) != scene.particles.len() as u64 || step.to_string() != entry["step"] {
        return Err(fail("cache frame count or step mismatch"));
    }
    let particles: Vec<_> = scene.particles.iter().zip(bytes[24..].chunks_exact(24)).map(|(initial, row)| {
        let v: Vec<_> = row.chunks_exact(4).map(|b| f32::from_bits(u32::from_le_bytes(b.try_into().unwrap()))).collect();
        Particle {identity: initial.identity, position_m: Vec3::new(v[0],v[1],v[2]), velocity_m_s: Vec3::new(v[3],v[4],v[5])}
    }).collect();
    SnapshotRecord::cache_review_from_particles(&particles, step).map_err(fail)
}

/// Runs only from a temporary source export prepared by cache_review.py.
pub fn run(mode: &str, request: &Path, cache: &Path, destination: &Path) -> Result<Value, ExportError> {
    let started = Instant::now();
    let document: Value = serde_json::from_slice(&fs::read(request).map_err(fail)?).map_err(fail)?;
    let input: RecordedInput = serde_json::from_value(document["input"].clone()).map_err(fail)?;
    let scene = input.resolve().map_err(fail)?;
    let execution = serde_json::from_value(document["execution"].clone()).map_err(fail)?;
    let steps: u64 = document["request"]["steps"].as_str().ok_or_else(||fail("missing steps"))?.parse().map_err(fail)?;
    let mut settings: Settings = serde_json::from_value(document["render"].clone()).map_err(fail)?;
    settings.validate().map_err(fail)?;
    let schedule = FrameSchedule::new(steps, settings.step_stride)?;
    if mode == "bake" || mode == "simulate" {
        if mode == "bake" { fs::create_dir(cache).map_err(fail)?; }
        let mut solver = Simulation::from_scene_with_execution(&scene, crate::neighbours::SearchBackend::UniformGrid, execution).map_err(fail)?;
        let mut frames = Vec::new();
        let mut diagnostics = Vec::new();
        let mut solver_s = 0.0;
        let mut write_s = 0.0;
        let mut canonical_s = 0.0;
        let mut next = 0;
        for step in 0..=steps {
            if step > 0 {
                let start = Instant::now();
                let outcome = solver.step().map_err(fail)?;
                solver_s += start.elapsed().as_secs_f64();
                diagnostics.push(StepDiagnostic::new(step, outcome.cfl));
            }
            if mode == "bake" && schedule.steps.get(next) == Some(&step) {
                let snapshot = SnapshotRecord::capture(solver.snapshot());
                let start = Instant::now();
                let canonical = format_digest(snapshot.canonical_sha256().map_err(fail)?);
                canonical_s += start.elapsed().as_secs_f64();
                let start = Instant::now();
                let bytes = frame_bytes(&snapshot);
                let binary_hash = hash(&bytes);
                publish_bytes(&cache.join(format!("frame-{next:08}.bin")), &bytes).map_err(fail)?;
                write_s += start.elapsed().as_secs_f64();
                frames.push(json!({"index":next,"step":step.to_string(),"binary_sha256":binary_hash,"snapshot_sha256":canonical,"bytes":bytes.len()}));
                next += 1;
                // Deliberate process failure for prefix recovery experiments only.
                if std::env::var("MAELSTROM_CACHE_REVIEW_STOP").ok().and_then(|s|s.parse::<usize>().ok()) == Some(next) {
                    return Err(fail("injected cache interruption"));
                }
            }
        }
        let result = json!({"probe_schema":1,"mode":mode,"complete":true,"frames":frames,"accepted_diagnostics":diagnostics,
            "solver_s":solver_s,"write_pack_hash_sync_s":write_s,"canonical_s":canonical_s,"inside_elapsed_s":started.elapsed().as_secs_f64()});
        if mode == "bake" {
            publish_bytes(&cache.join("cache.json"), &serde_json::to_vec_pretty(&result).map_err(fail)?).map_err(fail)?;
        }
        return Ok(result);
    }
    let cached: Value = serde_json::from_slice(&fs::read(cache.join("cache.json")).map_err(fail)?).map_err(fail)?;
    let entries = cached["frames"].as_array().ok_or_else(|| fail("missing cache index"))?;
    if cached["complete"] != true || entries.len() != schedule.steps.len() { return Err(fail("incomplete cache")); }
    if mode == "validate" {
        for (index, entry) in entries.iter().enumerate() {
            let snapshot = read_frame(cache, entry, &scene)?;
            if entry["index"] != index || snapshot.completed_steps() != schedule.steps[index]
                || format_digest(snapshot.canonical_sha256().map_err(fail)?) != entry["snapshot_sha256"] {
                return Err(fail("canonical cache mismatch"));
            }
        }
        return Ok(json!({"valid":true,"frames":entries.len()}));
    }
    if mode != "render" && mode != "render-alt" { return Err(fail("unknown probe mode")); }
    if mode == "render-alt" {
        settings.width = 1280; settings.height = 720;
    }
    let spacing = f64::from(scene.configuration.numerical.particle_spacing_m);
    let boundaries = BoundaryLines::new(&scene.particles, &scene.planes, spacing).map_err(fail)?;
    let instance = Graphics::instance();
    let graphics = pollster::block_on(Graphics::new(&instance, GraphicsSelection{index:0,software:false}, None, wgpu::TextureFormat::Rgba8UnormSrgb)).map_err(fail)?;
    fs::create_dir(destination).map_err(fail)?;
    let mut writer = offscreen::FrameWriter {operations:offscreen::FrameOperations::default(), graphics:&graphics, settings:&settings,
        boundaries:&boundaries, spacing, mass_kg:scene.configuration.derived.particle_mass_kg,
        dt:f64::from(scene.configuration.numerical.fixed_timestep_s),destination,timings:Default::default(),worker:encoding::Worker::new()?};
    let mut frames = Vec::new();
    let mut progress = json!({"complete":false,"source_mode":"saved","frames":[]});
    let mut progress_time = Default::default();
    let mut read_s = 0.0;
    for (index, entry) in entries.iter().enumerate() {
        let start = Instant::now();
        let snapshot = read_frame(cache, entry, &scene)?;
        read_s += start.elapsed().as_secs_f64();
        queue_frame(&mut writer,&snapshot,index,&mut frames,&mut progress,&mut progress_time)?;
    }
    collect_frame(&mut writer,&mut frames,&mut progress,&mut progress_time)?;
    graphics.check().map_err(fail)?;
    let t = writer.timings;
    let result = json!({"probe_schema":1,"mode":mode,"complete":true,"frames":frames,"read_decode_validate_s":read_s,
        "graphics_readback_s":t.graphics_readback.as_secs_f64(),"png_encoding_s":t.png_encoding.as_secs_f64(),"hashing_s":t.hashing.as_secs_f64(),
        "output_wait_s":t.output_wait.as_secs_f64(),"publication_s":t.publication.as_secs_f64(),"progress_s":progress_time.as_secs_f64(),
        "inside_elapsed_s":started.elapsed().as_secs_f64(),"render":settings});
    publish_bytes(&destination.join("probe-result.json"), &serde_json::to_vec_pretty(&result).map_err(fail)?).map_err(fail)?;
    Ok(result)
}

/// Small argument boundary keeps this experiment out of the application CLI.
pub fn main() -> Result<(), ExportError> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() != 4 { return Err(fail("MODE REQUEST CACHE DESTINATION")); }
    let result = run(&args[0], &PathBuf::from(&args[1]), &PathBuf::from(&args[2]), &PathBuf::from(&args[3]))?;
    println!("{}",serde_json::to_string(&result).map_err(fail)?);
    Ok(())
}
