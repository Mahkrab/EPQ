//! Failure and capacity probes for the isolated device-owned interface.
use maelstrom::{workflow::RecordedInput, scene::ResolvedScene, math::Vec3, boundary::Plane, simulation::{Simulation, experimental_device::DeviceSimulation}, neighbours::SearchBackend, execution::ExecutionMode};
use std::fs;

fn compare(scene: &ResolvedScene, failure: bool) -> Result<(),Box<dyn std::error::Error>> {
    let mut host=Simulation::from_scene_with_execution(scene,SearchBackend::UniformGrid,ExecutionMode::Cuda {device:0,threads:128})?;
    let mut device=DeviceSimulation::from_scene(scene)?;
    for _ in 0..3 {
        let before=device.observe()?;
        let a=host.step();let b=device.step(|| false);
        match (a,b) {
            (Ok(a),Ok((b,_))) => {assert!(!failure);assert_eq!(a,b);assert_eq!(host.snapshot(),&device.observe()?);}
            (Err(a),Err(b)) => {assert!(failure);assert_eq!(a.to_string(),b.to_string());assert_eq!(before,device.observe()?);assert_eq!(host.snapshot(),&device.observe()?);}
            (a,b) => panic!("paths disagree: {a:?} {b:?}"),
        }
    }
    Ok(())
}

fn main()->Result<(),Box<dyn std::error::Error>> {
    let args:Vec<_>=std::env::args().collect();let value:serde_json::Value=serde_json::from_slice(&fs::read(&args[1])?)?;
    let input:RecordedInput=serde_json::from_value(value["input"].clone())?;let base=input.resolve()?;
    let mut names=Vec::new();
    let mut scene=base.clone();scene.particles.clear();compare(&scene,false)?;names.push("empty");
    let mut scene=base.clone();scene.particles.truncate(1);compare(&scene,false)?;names.push("one particle");
    let mut scene=base.clone();scene.particles.truncate(1);scene.planes.clear();scene.particles[0].position_m=Vec3::new(f32::MAX,0.,0.);compare(&scene,false)?;names.push("extent width growth");
    let mut scene=base.clone();let p=scene.particles[0];scene.particles=(0..600).map(|i|maelstrom::scene::Particle {identity:i,position_m:p.position_m,velocity_m_s:Vec3::ZERO}).collect();compare(&scene,false)?;names.push("599 neighbours per row, dynamic growth");
    let mut scene=base.clone();scene.particles.truncate(1);scene.particles[0].velocity_m_s=Vec3::new(f32::MAX,0.,0.);compare(&scene,true)?;names.push("numerical failure retry");
    let mut scene=base.clone();scene.particles.truncate(1);scene.planes=vec![Plane::new(Vec3::new(0.,1.,0.),1.,0.)?,Plane::new(Vec3::new(0.,-1.,0.),0.,0.)?];compare(&scene,true)?;names.push("ordered plane fallback failure retry");
    let mut scene=base.clone();scene.particles.truncate(33);scene.configuration.numerical.xsph_viscosity_enabled=true;scene.configuration.numerical.vorticity_confinement_enabled=true;compare(&scene,false)?;names.push("velocity effects");
    let mut device=DeviceSimulation::from_scene(&scene)?;let mut calls=0;let _=device.step(||{calls+=1;false})?;
    for limit in 1..=calls {let mut device=DeviceSimulation::from_scene(&scene)?;let initial=device.observe()?;let mut k=0;assert!(device.step(||{k+=1;k==limit}).is_err());assert_eq!(initial,device.observe()?);let _=device.step(||false)?;}
    println!("{}",serde_json::json!({"passed":names,"velocity_effect_cancellation_polls":calls}));
    Ok(())
}
