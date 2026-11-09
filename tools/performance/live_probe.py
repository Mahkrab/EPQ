"""Prepare a separate, deliberately synchronising live graphics timing build.

Never use this build for ordinary viewer throughput. The added query readback waits
for each draw; device timestamps explain GPU work while changing its scheduling.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def prepare(root: Path) -> None:
    gpu = root / "src/render/gpu.rs"
    source = gpu.read_text(encoding="utf-8")

    def replace(old: str, new: str) -> None:
        nonlocal source
        if source.count(old) != 1:
            raise ValueError(f"expected one profiling insertion in {gpu.name}: {old!r}")
        source = source.replace(old,new)

    if "let particle_mesh = if use_impostor" in source:
        replace("        let lines = scene\n", """        eprintln!("PARTICLE_PRIMITIVES {:?} {} {}", self.particle_renderer,
            particle_mesh.count as usize / 3 * scene.particles.len(), mesh_level);
        let lines = scene
""")

    replace( "    uniform: wgpu::Buffer,", "    probe_queries: Option<(wgpu::QuerySet, wgpu::Buffer, wgpu::Buffer)>,\n    uniform: wgpu::Buffer,")
    replace( "        let (device, queue) = adapter", """        let requested = wgpu::Features::TIMESTAMP_QUERY | wgpu::Features::TIMESTAMP_QUERY_INSIDE_ENCODERS;
        let probe_features = if adapter.features().contains(requested) { requested } else { wgpu::Features::empty() };
        eprintln!("GPU_TIMESTAMP_SUPPORTED {}", !probe_features.is_empty());
        let (device, queue) = adapter""")
    replace( "                required_limits: limits,", "                required_limits: limits,\n                required_features: probe_features,")
    replace( "        Ok(Self {\n            device,", """        let probe_queries = if probe_features.is_empty() { None } else {
            Some((device.create_query_set(&wgpu::QuerySetDescriptor { label:Some("live probe"), ty:wgpu::QueryType::Timestamp, count:2 }),
                device.create_buffer(&wgpu::BufferDescriptor { label:Some("live query resolve"), size:16,
                    usage:wgpu::BufferUsages::QUERY_RESOLVE | wgpu::BufferUsages::COPY_SRC, mapped_at_creation:false }),
                device.create_buffer(&wgpu::BufferDescriptor { label:Some("live query readback"), size:16,
                    usage:wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST, mapped_at_creation:false })))
        };
        Ok(Self {
            probe_queries,
            device,""")
    replace( "        let mut encoder = self.device.create_command_encoder(&Default::default());", """        let mut encoder = self.device.create_command_encoder(&Default::default());
        if let Some((query,_,_)) = &self.probe_queries { encoder.write_timestamp(query,0); }""")
    replace( "        self.queue.submit([encoder.finish()]);", """        if let Some((query,resolve,readback)) = &self.probe_queries {
            encoder.write_timestamp(query,1);
            encoder.resolve_query_set(query,0..2,resolve,0);
            encoder.copy_buffer_to_buffer(resolve,0,readback,0,16);
        }
        self.queue.submit([encoder.finish()]);
        if let Some((_,_,readback)) = &self.probe_queries {
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
            eprintln!("GPU_DRAW_S {}", end.wrapping_sub(start) as f64 * f64::from(self.queue.get_timestamp_period()) * 1e-9);
        }""")

    # Validate every insertion before replacing the caller's source file.
    temporary = None
    try:
        with NamedTemporaryFile(mode="w",encoding="utf-8",dir=gpu.parent,delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(source)
        os.chmod(temporary,gpu.stat().st_mode & 0o777)
        temporary.replace(gpu)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    try:
        prepare(args.source)
    except (OSError,ValueError) as error:
        parser.exit(1,f"live graphics probe: {error}\n")
