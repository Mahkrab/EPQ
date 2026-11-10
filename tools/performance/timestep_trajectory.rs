//! Export every accepted state's raw-bit digest from an isolated build.
//! Hashing deliberately sits outside stepping; these are correctness witnesses,
//! never throughput samples. The frozen control supplies the comparison oracle.
use maelstrom::{
    config::{ConfigurationOverlay, NumericalMode},
    execution::ExecutionMode,
    neighbours::SearchBackend,
    scene::load_resolved_scene,
    simulation::{Simulation, Snapshot},
};
use sha2::{Digest, Sha256};
use std::{
    fs::OpenOptions,
    io::{BufWriter, Write},
    path::Path,
};

fn digest(snapshot: &Snapshot) -> String {
    let mut hash = Sha256::new();
    hash.update(snapshot.completed_steps().to_le_bytes());
    for p in snapshot.particles() {
        hash.update(p.identity.to_le_bytes());
        for v in [
            p.position_m.x,
            p.position_m.y,
            p.position_m.z,
            p.velocity_m_s.x,
            p.velocity_m_s.y,
            p.velocity_m_s.z,
        ] {
            hash.update(v.to_bits().to_le_bytes());
        }
    }
    hash.finalize().iter().map(|b| format!("{b:02x}")).collect()
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    eprintln!("TRAJECTORY_SOURCE {}", env!("MAELSTROM_EXPORT_SOURCE"));
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 6 {
        return Err("require SCENE MODE STEPS EFFECTS OUTPUT".into());
    }
    let mut overlay = ConfigurationOverlay::default();
    args[2]
        .parse::<NumericalMode>()?
        .fill_overrides(&mut overlay.numerical);
    if args[4] == "effects" {
        overlay.numerical.xsph_viscosity_enabled = Some(true);
        overlay.numerical.xsph_viscosity_coefficient = Some(0.01);
        overlay.numerical.vorticity_confinement_enabled = Some(true);
        overlay.numerical.vorticity_confinement_strength_m_s = Some(0.1);
    } else if args[4] != "default" {
        return Err("EFFECTS must be effects or default".into());
    }
    let scene = load_resolved_scene(Path::new(&args[1]), Some(&overlay))?;
    let mut sim = Simulation::from_scene_with_execution(
        &scene,
        SearchBackend::UniformGrid,
        ExecutionMode::Cuda {
            device: 0,
            threads: 128,
        },
    )?;
    let mut output = BufWriter::new(
        OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&args[5])?,
    );
    writeln!(output, "0 {}", digest(sim.snapshot()))?;
    for _ in 0..args[3].parse::<usize>()? {
        match sim.step() {
            Ok(outcome) => writeln!(
                output,
                "{} {} {:?}",
                outcome.completed_steps,
                digest(sim.snapshot()),
                outcome.cfl
            )?,
            Err(error) => {
                writeln!(output, "ERROR {error} {}", digest(sim.snapshot()))?;
                output.flush()?;
                return Err(error.into());
            }
        }
    }
    output.flush()?;
    drop(sim);
    Ok(())
}
