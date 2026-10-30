"""Add diagnostic boundaries to an isolated source export, never to production.

An extra queue drain separates draw completion from texture transfer. Its clocks
include driver waits and scheduling, so they are not GPU execution timestamps.
"""

from pathlib import Path
import argparse
import hashlib
import json
import shutil
import statistics


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ValueError(f"expected one profiling anchor in {path}: {old[:60]}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def prepare(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination)
    gpu = destination / "src/render/gpu.rs"
    replace(gpu, '    uniform: wgpu::Buffer,',
            '    probe_queries: Option<(wgpu::QuerySet, wgpu::Buffer, wgpu::Buffer)>,\n    uniform: wgpu::Buffer,')
    replace(gpu, '        let (device, queue) = adapter', '''        let probe_requested = wgpu::Features::TIMESTAMP_QUERY | wgpu::Features::TIMESTAMP_QUERY_INSIDE_ENCODERS;
        let probe_features = adapter.features() & probe_requested;
        let probe_features = if probe_features == probe_requested { probe_features } else { wgpu::Features::empty() };
        eprintln!("TIMESTAMP_SUPPORT {}", !probe_features.is_empty());
        let (device, queue) = adapter''')
    replace(gpu, '                required_limits: limits,', '                required_limits: limits,\n                required_features: probe_features,')
    replace(gpu, '        Ok(Self {\n            device,', '''        let probe_queries = if probe_features.is_empty() { None } else {
            Some((device.create_query_set(&wgpu::QuerySetDescriptor { label:Some("probe timestamps"), ty:wgpu::QueryType::Timestamp, count:2 }),
                device.create_buffer(&wgpu::BufferDescriptor { label:Some("probe query resolve"), size:16,
                    usage:wgpu::BufferUsages::QUERY_RESOLVE | wgpu::BufferUsages::COPY_SRC, mapped_at_creation:false }),
                device.create_buffer(&wgpu::BufferDescriptor { label:Some("probe query readback"), size:16,
                    usage:wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST, mapped_at_creation:false })))
        };
        Ok(Self {
            probe_queries,
            device,''')
    replace(gpu, "        self.check()?;\n        scene", "        let probe_start = std::time::Instant::now();\n        self.check()?;\n        scene")
    replace(gpu, '        let centres_buffer = make_buffer("accepted centres", &centres)?;',
            '        let probe_prepared = probe_start.elapsed().as_secs_f64();\n        let centres_buffer = make_buffer("accepted centres", &centres)?;')
    replace(gpu, '        let mut encoder = self.device.create_command_encoder(&Default::default());',
            '        let probe_uploaded = probe_start.elapsed().as_secs_f64();\n        let mut encoder = self.device.create_command_encoder(&Default::default());\n        self.probe_begin_gpu(&mut encoder);')
    replace(gpu, '        self.queue.submit([encoder.finish()]);\n        self.check()',
            '''        self.probe_end_gpu(&mut encoder);
        self.queue.submit([encoder.finish()]);
        let probe_submitted = probe_start.elapsed().as_secs_f64();
        eprintln!("DRAW_PROFILE {{\\\"cpu_prepare_s\\\":{},\\\"buffer_upload_s\\\":{},\\\"render_submit_s\\\":{}}}", probe_prepared, probe_uploaded-probe_prepared, probe_submitted-probe_uploaded);
        self.check()''')
    with gpu.open("a", encoding="utf-8") as out:
        out.write(GPU_TIMESTAMPS)
    pixels = destination / "src/export/offscreen.rs"
    replace(pixels, '        let frame = super::Frame {', '''        let probe_hash_start = std::time::Instant::now();
        let probe_json = snapshot.to_json().map_err(fail)?;
        let probe_json_s = probe_hash_start.elapsed().as_secs_f64();
        let probe_snapshot_hash = super::hash(probe_json.as_bytes());
        let probe_sha_s = probe_hash_start.elapsed().as_secs_f64()-probe_json_s;
        eprintln!("HASH_PROFILE {{\\\"snapshot_json_s\\\":{},\\\"snapshot_sha_s\\\":{},\\\"snapshot_json_bytes\\\":{}}}",probe_json_s,probe_sha_s,probe_json.len());
        let frame = super::Frame {''')
    replace(pixels, 'snapshot_sha256: super::hash(snapshot.to_json().map_err(fail)?.as_bytes()),',
            'snapshot_sha256: probe_snapshot_hash,')
    replace(pixels, '    graphics.check().map_err(fail)?;\n    let depth',
            '    let probe_start = std::time::Instant::now();\n    graphics.check().map_err(fail)?;\n    let depth')
    replace(pixels, '    graphics\n        .draw(', '    let probe_allocated = probe_start.elapsed().as_secs_f64();\n    graphics\n        .draw(')
    replace(pixels, '    let row = scene.width * 4;', '''    let probe_drawn = probe_start.elapsed().as_secs_f64();
    let probe_gpu_render = graphics.probe_gpu_seconds().map_err(fail)?;
    graphics.device.poll(wgpu::PollType::Wait {
        submission_index: None, timeout: Some(Duration::from_secs(30)),
    }).map_err(fail)?;
    let probe_drained = probe_start.elapsed().as_secs_f64();
    let row = scene.width * 4;''')
    replace(pixels, '    encoder.copy_texture_to_buffer(', '    graphics.probe_begin_gpu(&mut encoder);\n    encoder.copy_texture_to_buffer(')
    replace(pixels, '    graphics.queue.submit([encoder.finish()]);',
            '    graphics.probe_end_gpu(&mut encoder);\n    graphics.queue.submit([encoder.finish()]);')
    replace(pixels, '    let (tx, rx) = mpsc::sync_channel(1);',
            '    let probe_copied = probe_start.elapsed().as_secs_f64();\n    let (tx, rx) = mpsc::sync_channel(1);')
    replace(pixels, '    let mapped = buffer.get_mapped_range(..).map_err(fail)?;',
            '    let probe_mapped = probe_start.elapsed().as_secs_f64();\n    let mapped = buffer.get_mapped_range(..).map_err(fail)?;')
    replace(pixels, '    Ok(rgba)\n}', '''    let probe_done = probe_start.elapsed().as_secs_f64();
    let probe_gpu_copy = graphics.probe_gpu_seconds().map_err(fail)?;
    eprintln!("GPU_PROFILE {}", serde_json::json!({"render_gpu_s":probe_gpu_render,"texture_copy_gpu_s":probe_gpu_copy}));
    eprintln!("PIXEL_PROFILE {{\\\"target_allocation_s\\\":{},\\\"draw_call_s\\\":{},\\\"draw_drain_s\\\":{},\\\"transfer_submit_s\\\":{},\\\"transfer_wait_map_s\\\":{},\\\"row_unpack_s\\\":{}}}", probe_allocated, probe_drawn-probe_allocated, probe_drained-probe_drawn, probe_copied-probe_drained, probe_mapped-probe_copied, probe_done-probe_mapped);
    Ok(rgba)
}''')
    export = destination / "src/export/mod.rs"
    with export.open("a", encoding="utf-8") as out:
        out.write('''
/// Diagnostic access in this isolated export only.
pub fn probe_pixels(g: &Graphics, scene: &crate::render::DrawScene<'_>) -> Result<Vec<u8>, ExportError> {
    offscreen::pixels(g, scene)
}
/// Diagnostic access in this isolated export only.
pub fn probe_encode(w: u32, h: u32, rgba: &[u8]) -> Result<Vec<u8>, ExportError> {
    offscreen::encode(w, h, rgba)
}
''')
    binary = destination / "src/bin/render-probe.rs"
    binary.parent.mkdir(exist_ok=True)
    binary.write_text(PROBE, encoding="utf-8")


def requests(previous: Path, output: Path) -> None:
    """Select saved states also present in the original 60 Hz image sequence."""
    output.mkdir(parents=True, exist_ok=False)
    for scene in ("resolved", "large"):
        for mode in ("reference", "fast"):
            manifest = json.loads((previous / "compiled" / f"{scene}-r3-{mode}" / "bundle/manifest.json").read_bytes())
            frames = {int(f["step"]): f for f in manifest["frames"]}
            native = previous / "runs" / f"physical-{scene}-{mode}"
            states = sorted((p for p in native.glob("state-*.bin") if p.stem.removeprefix("state-").isdecimal()),
                            key=lambda p: int(p.stem.split("-")[-1]))
            states = [p for p in states if int(p.stem.split("-")[-1]) in frames]
            request = dict(input=manifest["input"], render=manifest["render"], states=list(map(str, states)),
                           expected={str(p): frames[int(p.stem.split("-")[-1])] for p in states},
                           state_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in states})
            (output / f"{scene}-{mode}.json").write_text(json.dumps(request) + "\n", encoding="utf-8")


def assess(root: Path) -> list[dict]:
    """Reject changed replay images and retain per-state GPU and CPU attribution."""
    summaries = []
    for path in sorted((root / "probe-output").glob("*.jsonl")):
        request = json.loads((root / "probe-requests-v2" / (path.stem + ".json")).read_bytes())
        frames = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        streams = {tag: [] for tag in ("DRAW_PROFILE", "GPU_PROFILE", "PIXEL_PROFILE")}
        for line in path.with_suffix(".stderr").read_text(encoding="utf-8").splitlines():
            tag, _, value = line.partition(" ")
            if tag in streams:
                streams[tag].append(json.loads(value))
        if len(frames) != len(request["states"])*4 or any(len(v) != len(frames) for v in streams.values()):
            raise ValueError("incomplete saved-state profiling stream")
        for index, frame in enumerate(frames):
            expected = request["expected"][frame["state"]]
            if any("sha256:" + frame[key] != expected[key] for key in ("png_sha256", "rgba_sha256")):
                raise ValueError("replayed native state differs from the production compilation image")
            if frame["state_sha256"] != request["state_sha256"][frame["state"]]:
                raise ValueError("native replay input changed")
            frame.update({k: v for tag in streams for k,v in streams[tag][index].items()})
        measured = [f for f in frames if f["repeat"] > 0]
        keys = ("cpu_prepare_s", "buffer_upload_s", "render_submit_s", "render_gpu_s", "texture_copy_gpu_s",
                "target_allocation_s", "draw_drain_s", "transfer_submit_s", "transfer_wait_map_s", "row_unpack_s",
                "graphics_s", "encoding_s")
        median = lambda rows, key: statistics.median(f[key] for f in rows) if all(f[key] is not None for f in rows) else None
        states = [{"state": state, "step": request["expected"][state]["step"],
                   "simulated_s": request["expected"][state]["simulated_seconds"],
                   **{key: median([f for f in measured if f["state"] == state], key) for key in keys}}
                  for state in request["states"]]
        summaries.append(dict(case=path.stem, states=len(states), verified_frames=len(frames),
                              median_s={key: median(measured, key) for key in keys}, per_state=states))
    (root / "probe-summary.json").write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    return summaries


GPU_TIMESTAMPS = r'''
impl Graphics {
    pub(crate) fn probe_begin_gpu(&self, encoder: &mut wgpu::CommandEncoder) {
        if let Some((query,_,_)) = &self.probe_queries { encoder.write_timestamp(query,0); }
    }
    pub(crate) fn probe_end_gpu(&self, encoder: &mut wgpu::CommandEncoder) {
        if let Some((query,resolve,readback)) = &self.probe_queries {
            encoder.write_timestamp(query,1);
            encoder.resolve_query_set(query,0..2,resolve,0);
            encoder.copy_buffer_to_buffer(resolve,0,readback,0,16);
        }
    }
    pub(crate) fn probe_gpu_seconds(&self) -> Result<Option<f64>,RenderError> {
        let Some((_,_,readback)) = &self.probe_queries else { return Ok(None) };
        let (tx,rx) = std::sync::mpsc::sync_channel(1);
        readback.map_async(wgpu::MapMode::Read,..,move |r| {let _=tx.send(r);});
        self.device.poll(wgpu::PollType::Wait {submission_index:None,timeout:Some(std::time::Duration::from_secs(30))})
            .map_err(|e|RenderError(e.to_string()))?;
        rx.recv_timeout(std::time::Duration::from_secs(30)).map_err(|e|RenderError(e.to_string()))?
            .map_err(|e|RenderError(e.to_string()))?;
        let mapped = readback.get_mapped_range(..).map_err(|e|RenderError(e.to_string()))?;
        let start = u64::from_ne_bytes(mapped[0..8].try_into().unwrap());
        let end = u64::from_ne_bytes(mapped[8..16].try_into().unwrap());
        drop(mapped); readback.unmap();
        Ok(Some(end.wrapping_sub(start) as f64 * f64::from(self.queue.get_timestamp_period()) * 1e-9))
    }
}
'''


PROBE = r'''
//! Replay immutable native observations through the actual production draw path.
use maelstrom::{render::{Graphics,GraphicsSelection,Settings,DrawScene,BoundaryLines},
    workflow::RecordedInput, math::Vec3};
use sha2::{Digest,Sha256};
use std::{fs,path::PathBuf,time::Instant};
fn hash(bytes: &[u8]) -> String {
    Sha256::digest(bytes).iter().map(|b|format!("{b:02x}")).collect()
}
fn main() -> Result<(),Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    let request: serde_json::Value = serde_json::from_slice(&fs::read(&args[1])?)?;
    let input: RecordedInput = serde_json::from_value(request["input"].clone())?;
    let scene = input.resolve()?;
    let settings: Settings = serde_json::from_value(request["render"].clone())?;
    let boundaries = BoundaryLines::new(&scene.particles, &scene.planes,
        f64::from(scene.configuration.numerical.particle_spacing_m))?;
    let instance = Graphics::instance();
    let g = pollster::block_on(Graphics::new(&instance,GraphicsSelection::default(),None,wgpu::TextureFormat::Rgba8UnormSrgb))?;
    let mut particles = scene.particles.clone();
    let n = particles.len();
    for path in request["states"].as_array().ok_or("missing states")? {
        let path = PathBuf::from(path.as_str().ok_or("invalid state path")?);
        let raw = fs::read(&path)?;
        if raw.len() != n*24 { return Err("invalid native state size".into()); }
        let value = |offset:usize| f32::from_le_bytes(raw[offset..offset+4].try_into().unwrap());
        for (i,p) in particles.iter_mut().enumerate() {
            p.position_m = Vec3::new(value(i*12),value(i*12+4),value(i*12+8));
            p.velocity_m_s = Vec3::new(value(n*12+i*12),value(n*12+i*12+4),value(n*12+i*12+8));
        }
        for repeat in 0..4 {
            let start = Instant::now();
            let rgba = maelstrom::export::probe_pixels(&g,&DrawScene {
                particles:&particles, boundaries:&boundaries,
                radius_m:f64::from(scene.configuration.numerical.particle_spacing_m)/2.,
                camera:&settings.camera, colours:&settings.particles,
                particle_mass_kg:scene.configuration.derived.particle_mass_kg,
                width:settings.width,height:settings.height,
            })?;
            let graphics_s = start.elapsed().as_secs_f64();
            let start = Instant::now();
            let png = maelstrom::export::probe_encode(settings.width,settings.height,&rgba)?;
            let encoding_s = start.elapsed().as_secs_f64();
            println!("{}",serde_json::json!({"state":path,"repeat":repeat,
                "state_sha256":hash(&raw),"rgba_sha256":hash(&rgba),"png_sha256":hash(&png),
                "graphics_s":graphics_s,"encoding_s":encoding_s}));
        }
    }
    Ok(())
}
'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    prepare(args.source, args.destination)
