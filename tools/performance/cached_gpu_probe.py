"""Instrument an isolated source export for synchronous GPU timestamp diagnostics.

The probe changes no drawing expressions. Mapping each result serialises the GPU,
so its timings must remain separate from ordinary playback/export throughput.
"""
import argparse
from pathlib import Path
import shutil


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"probe anchor no longer unique: {old[:70]}")
    return text.replace(old, new)


def prepare(source: Path, destination: Path):
    shutil.copytree(source, destination)
    path = destination / "src/render/gpu.rs"
    text = path.read_text()
    text = replace_once(text, 'label: Some("particle viewer"),', '''label: Some("particle viewer"),
                required_features: wgpu::Features::TIMESTAMP_QUERY | wgpu::Features::TIMESTAMP_QUERY_INSIDE_ENCODERS,''')
    text = replace_once(text, 'let mut encoder = self.device.create_command_encoder(&Default::default());', '''let queries = self.device.create_query_set(&wgpu::QuerySetDescriptor {
            label: Some("qualification timestamps"), ty: wgpu::QueryType::Timestamp, count: 2,
        });
        let resolve = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: None, size: 16, usage: wgpu::BufferUsages::QUERY_RESOLVE | wgpu::BufferUsages::COPY_SRC, mapped_at_creation: false,
        });
        let readback = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: None, size: 16, usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ, mapped_at_creation: false,
        });
        let mut encoder = self.device.create_command_encoder(&Default::default());
        encoder.write_timestamp(&queries, 0);''')
    text = replace_once(text, 'self.queue.submit([encoder.finish()]);', '''encoder.write_timestamp(&queries, 1);
        encoder.resolve_query_set(&queries, 0..2, &resolve, 0);
        encoder.copy_buffer_to_buffer(&resolve, 0, &readback, 0, 16);
        self.queue.submit([encoder.finish()]);
        let (tx, rx) = std::sync::mpsc::sync_channel(1);
        readback.map_async(wgpu::MapMode::Read, .., move |result| { let _ = tx.send(result); });
        self.device.poll(wgpu::PollType::Wait { submission_index: None, timeout: Some(std::time::Duration::from_secs(10)) }).map_err(|e| RenderError(e.to_string()))?;
        rx.recv_timeout(std::time::Duration::from_secs(10)).map_err(|e| RenderError(e.to_string()))?.map_err(|e| RenderError(e.to_string()))?;
        let mapped = readback.get_mapped_range(..).map_err(|e| RenderError(e.to_string()))?;
        let begin = u64::from_ne_bytes(mapped[0..8].try_into().unwrap());
        let end = u64::from_ne_bytes(mapped[8..16].try_into().unwrap());
        eprintln!("gpu-draw-ns {}", (end - begin) as f64 * f64::from(self.queue.get_timestamp_period()));
        drop(mapped);
        readback.unmap();''')
    path.write_text(text)
    path = destination / "src/cli/video.rs"
    text = path.read_text()
    text = replace_once(text, '|i| cached_pixels(&opened, &settings, &graphics, &boundaries, i),', '''|i| {
                    let start = std::time::Instant::now();
                    let pixels = cached_pixels(&opened, &settings, &graphics, &boundaries, i);
                    eprintln!("video-frame-seconds {i} {}", start.elapsed().as_secs_f64());
                    pixels
                },''')
    path.write_text(text)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args=parser.parse_args()
    prepare(args.source, args.destination)
