"""Install an explicit device-owned experiment into a disposable source export.

This cannot modify a Git checkout. The original Simulation API and native kernels
remain intact. The new owner exposes fallible observations and keeps stage waits,
diagnostics, dynamic neighbour allocation and transactional device acceptance.
"""
import argparse
from pathlib import Path


DEVICE='''//! Explicit device ownership for the isolated residency measurement.
use super::*;

pub struct DeviceSimulation { inner: Simulation, completed: u64 }
impl DeviceSimulation {
    pub fn from_scene(scene: &ResolvedScene) -> Result<Self, StepError> {
        Ok(Self { inner: Simulation::from_scene_with_execution(scene, SearchBackend::UniformGrid, ExecutionMode::Cuda { device: 0, threads: 128 })?, completed: 0 })
    }
    pub fn step(&mut self, mut cancelled: impl FnMut() -> bool) -> Result<(StepOutcome, StepMeasurement), StepError> {
        let start = Instant::now();
        check_cancellation(&mut cancelled)?;
        let next = self.completed.checked_add(1).ok_or(StepError::StepCountOverflow)?;
        let cuda = self.inner.cuda.as_mut().unwrap();
        let output = cuda.step_device(&self.inner.configuration, &self.inner.accepted.particles, &self.inner.planes, &mut cancelled, &mut StageClock::<false>::new())?;
        check_cancellation(&mut cancelled)?;
        cuda.accept()?;
        self.completed = next;
        Ok((StepOutcome { completed_steps: next, cfl: output.cfl }, StepMeasurement { total_s: start.elapsed().as_secs_f64(), stages: None }))
    }
    /// A failed observation leaves canonical accepted device state owned here.
    pub fn observe(&mut self) -> Result<Snapshot, StepError> {
        let particles = if self.completed == 0 { self.inner.accepted.particles.clone() } else { self.inner.cuda.as_mut().unwrap().experimental_materialise(&self.inner.accepted.particles, true)? };
        validate_particles(&particles)?;
        Ok(Snapshot { completed_steps: self.completed, particles })
    }
}
'''

EXAMPLE='''//! Full production coordination versus explicit device ownership, same kernels.
use maelstrom::{workflow::{RecordedInput, SnapshotRecord}, simulation::{Simulation, experimental_device::DeviceSimulation}, neighbours::SearchBackend, execution::ExecutionMode};
use std::{fs, time::Instant, io::Write};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    let value: serde_json::Value = serde_json::from_slice(&fs::read(&args[1])?)?;
    let input: RecordedInput = serde_json::from_value(value["input"].clone())?;
    let scene = input.resolve()?;
    let steps: usize = args[2].parse()?;
    let period: usize = args[4].parse()?;
    let mut times = Vec::new(); let mut observations = 0.;
    let start = Instant::now();
    let snapshot = if args[3] == "device" {
        let mut sim = DeviceSimulation::from_scene(&scene)?;
        for k in 1..=steps {
            times.push(sim.step(|| false)?.1.total_s);
            if period != 0 && k % period == 0 { let at=Instant::now(); std::hint::black_box(sim.observe()?); observations+=at.elapsed().as_secs_f64(); }
        }
        let at=Instant::now();let s=sim.observe()?;observations+=at.elapsed().as_secs_f64();s
    } else if args[3] == "check" {
        let mut standard=Simulation::from_scene_with_execution(&scene,SearchBackend::UniformGrid,ExecutionMode::Cuda {device:0,threads:128})?;
        let _ = standard.step()?;
        for limit in 1..=(5+2*scene.configuration.numerical.solver_iterations) {
            let mut sim=DeviceSimulation::from_scene(&scene)?;
            let initial=sim.observe()?;
            let mut calls=0;
            assert!(sim.step(|| { calls+=1;calls==limit }).is_err());
            assert_eq!(sim.observe()?,initial);
            let _ = sim.step(|| false)?;
            assert_eq!(&sim.observe()?,standard.snapshot());
        }
        println!("{{\\"cancellation_retry_polls\\":{},\\"passed\\":true}}",5+2*scene.configuration.numerical.solver_iterations);
        return Ok(());
    } else {
        let mut sim=Simulation::from_scene_with_execution(&scene,SearchBackend::UniformGrid,ExecutionMode::Cuda {device:0,threads:128})?;
        for k in 1..=steps {
            times.push(sim.step_measured_with_cancellation(false,|| false)?.1.total_s);
            if period != 0 && k % period == 0 {std::hint::black_box(sim.snapshot());}
        }
        sim.snapshot().clone()
    };
    let wall=start.elapsed().as_secs_f64();
    let mut out=fs::File::create(&args[5])?;
    for field in 0..2 { for p in snapshot.particles() {let a=if field==0 {p.position_m} else {p.velocity_m_s};for v in [a.x,a.y,a.z] {out.write_all(&v.to_le_bytes())?;} } }
    println!("{}",serde_json::json!({"steps":steps,"mode":args[3],"checkpoint_period":period,"solver_s":times.iter().sum::<f64>(),"observation_s":observations,"construction_solver_observation_wall_s":wall,"step_s":times,"snapshot_key":SnapshotRecord::capture(&snapshot).completed_steps()}));
    Ok(())
}
'''


def prepare(root):
    if (root/'.git').exists() or root.name!='residency-source':raise ValueError('requires isolated residency-source export')
    path=root/'src/cuda/solver.rs';source=path.read_text()
    if 'fn step_device' in source:raise ValueError('experiment already installed')
    begin=source.index('    pub(crate) fn step<const PROFILE: bool>')
    end=source.index('\n}\n\nconst QUANTITIES',begin)
    method=source[begin:end].replace('fn step<const','fn step_device<const',1)
    tail=method.index('        let positions: Vec<[f32; 3]> = self.context.inner.download(2, particles.len())?;')
    method=method[:tail]+'''        let record = if particles.is_empty() { u64::MAX } else {
            self.context.inner.download_at::<u64>(3, (3 * particles.len() + (particles.len() & 1)) / 2, 1)?[0]
        };
        if record != u64::MAX {
            let output = self.experimental_materialise(particles, false)?;
            for particle in &output {
                for (index, plane) in planes.iter().enumerate() {
                    if !plane.contains(particle.position_m)? {
                        return Err(StepError::OutsidePlane { identity: particle.identity, plane: index });
                    }
                }
            }
        }
        Ok(CudaStepOutput { particles: Vec::new(), cfl, planes_checked: true })
    }

    pub(crate) fn experimental_materialise(&mut self, identities: &[Particle], accepted: bool) -> Result<Vec<Particle>, StepError> {
        let slot = if accepted { 0 } else { 2 };
        let positions: Vec<[f32; 3]> = self.context.inner.download(slot, identities.len())?;
        let velocities: Vec<[f32; 3]> = self.context.inner.download(slot + 1, identities.len())?;
        Ok(host_values(identities.iter().zip(positions).zip(velocities).map(|((old,p),v)| Particle { identity: old.identity, position_m: vector(p), velocity_m_s: vector(v) }))?)
    }
'''
    path.write_text(source[:end]+ '\n'+method+source[end:])
    path=root/'src/simulation/mod.rs';path.write_text(path.read_text()+'\n#[cfg(feature = "cuda")]\npub mod experimental_device;\n')
    (root/'src/simulation/experimental_device.rs').write_text(DEVICE)
    (root/'examples').mkdir(exist_ok=True);(root/'examples/frontier_resident.rs').write_text(EXAMPLE)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source_export',type=Path);prepare(p.parse_args().source_export.resolve())
