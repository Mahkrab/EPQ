# Bounded DFSPH prototype and CUDA integration decision

**NO-GO for production CUDA integration of the tested candidate.** A working isolated CUDA prototype and an independent author-code harness were completed. They resolve the known wall-density calibration error, preserve unloaded shear and improve hydrostatic centroid accuracy. They do not deliver acceptable coupled fluid behaviour with less work at 110,592 particles. Particle clustering persists, and the large cubic case requires more pressure work and runs slower than production PBF.

No production source, interface, numerical policy or retained optimisation was changed. Both Git HEADs remain unchanged. The simulator experiment is in [Maelstrom's isolated source directory](/Maelstrom/experiments/dfsph/README.md); the [evidence README](/docs/project/development/milestones/05/assets/dfsph-prototype-v1/README.md) provides reproduction and archive verification instructions.

## Implementation and bounded protocol

The implementation follows the published DFSPH formulation and SPlisHSPlasH's scalar reference at `7586ffa25948c6ce3bc6c238cda30ad8d35f60a0`. It includes the density and divergence solves, reference warmstarts, mean-positive-residual convergence tests, deficiency handling and the reference's sampled-volume boundary equations. There is no new pressure formulation. <sup><a href="#ref-s060">S060</a>, <a href="#ref-s079">S079</a></sup>

The CUDA prototype reuses Maelstrom's unchanged cell sorting, device prefix, ordered neighbour rows and particle-vector layout. Neighbours are rebuilt at current positions, as DFSPH requires. Storage grows from actual counts; it has no fixed per-row neighbour ceiling. Density and factor calculation share one traversal; each pressure iteration computes acceleration and its density response in separate launch snapshots. Host observations occur at 60 Hz. All 14 native source files match the production control byte-for-byte, preserving the ten retained optimisations in production.

The prospective practical criteria retained the previous frontier's limits: p95 positive compression ≤5%, maximum compression ≤25%, no non-finite state or coincidences, separation ≥0.5 spacings, hydrostatic centroid and occupied-volume proxy error ≤10%, positive mechanical-energy excess ≤10%, shear-amplitude error ≤20%, and bulk timestep changes ≤10%. These are application budgets, not research-grade Navier–Stokes qualification. Earlier stricter failures remain unchanged.

The study tested 62 physical CUDA trajectories across hydrostatic, compression, falling-block, collision, spreading free-surface and shear scenes, with selected cases extended to five seconds. The screen used fixed 120/240/480 Hz timesteps, density tolerances 0.01/0.1/0.5% and divergence tolerance 0.1%, in the declared sparse matrix. Minimum density/divergence iterations were 2/1, with ceilings of 100/100. The original six-policy bound was explicitly amended once for a single Jacobi-weight repair. No additional parameter search followed its failure.

Spacing remained 0.05 m, physical density 1,000 kg/m³ and geometric mass 0.125 kg. Cubic support was 0.1 m. The explicit Wendland control used 0.15 m support without changing material spacing, mass, geometry or collision extent. The reference's radius-derived material volume was overridden explicitly to prevent an unnoticed mass change. There was no viscosity, XSPH, artificial pressure or arbitrary velocity damping.

## The wall issue was a setup error; boundary qualification still fails

An independent lattice calculation reproduces the previous surface-layer problem. Kernel-calibrated pseudo-volumes on a single sampled plane give approximately **1.5453 times rest density** at the first fluid layer. A sampled solid filled with geometric-volume cells outside the box instead completes the fluid lattice to **0.9999725 times rest density** with the cubic kernel. Corner cells are included once, rather than superposing independent face samples.

The reference controls varied collision treatment separately. Without the half-spacing inset, the filled-solid tank's two-second centroid error was 2.33%. With centres constrained half a spacing inside the physical box, it was 0.53%. Those are independent mass/area height references, not fitted boundary offsets. Normal collision velocity is removed at contact; tangential velocity is unchanged, and contact counts and kinetic-energy loss are recorded.

This corrects the large initial density bias, but does not qualify the complete boundary model. The reference controls still developed minimum separations of approximately 3.02 mm without the inset and 14.65 mm with it, below the required 25 mm. The inset therefore did not cure particle collapse. The filled-solid method is limited to the tested rectangular geometry; curved or moving boundaries were not implemented.

## Physical results and convergence

No coupled policy passed the practical criteria. The result does not depend on interpreting the occupied-volume proxy as an exact physical volume.

| Two-second cubic control | 120 Hz | 240 Hz | 480 Hz |
|---|---:|---:|---:|
| Tank worst sampled p95 compression | 3.05% | 0.93% | 0.35% |
| Tank centroid error | 1.09% | 0.64% | 0.46% |
| Tank minimum separation / spacing | 0.006 | 0.064 | 0.021 |
| Free-surface worst sampled p95 compression | 4.66% | 1.42% | 0.40% |
| Free-surface minimum separation / spacing | 0.001 | 0.008 | 0.013 |

Refinement improves density and centroid statistics while failing to recover particle separation. Tightening the mean density tolerance to 0.01% also failed the separation criterion. This is not just a collision-inset or large-timestep failure: the compression test has no walls or gravity, and the 240 Hz case collapsed to a minimum separation of **0.000217 spacings** at a maximum outgoing advection CFL of only **0.061**.

Unloaded analytical shear was a success. The cubic 240 Hz case retained **0.9999847** of the initial shear projection over 0.2 seconds, with approximately 0.0014% kinetic-energy loss. The repaired Wendland case retained **0.9999453**. These tests do not establish correct shear under arbitrary pressure loads, but they distinguish DFSPH from the previous PBF pressure-derived shear loss.

The default-reference Jacobi weight of 0.5 diverged for the larger-support Wendland tank. First-step kinetic energy was approximately **151.7 J/kg** in both the independent reference and CUDA implementation. A single control reduced only the two Jacobi update weights to 0.1; warmstart factors and pressure equations stayed unchanged. This removed the immediate iteration blowup, but did not solve the physical failure. At two seconds, its CUDA tank had 9 exact coincidences and a 0.29427 m³ occupied-support proxy against a mass-based volume of 0.4 m³. The separately patched reference also clustered: its minimum separation was about **3.9 µm**, centroid 0.19760 m and proxy 0.29497 m³. The CUDA centroid was 0.19754 m.

After five seconds, the cubic tank still had a centroid error of only 0.70%, but failed separation and the volume proxy. The repaired Wendland tank had 1.30% centroid error and 1.91% worst sampled p95 compression, yet exact coincidences and a 27.36% peak support-volume deficit. Low density residuals and plausible settled heights are insufficient acceptance evidence.

Particle number and mass were conserved. Kinetic/potential energy, mean velocity, pressure impulse and normal-contact energy loss are retained over time. Global conservation did not prevent local sample collapse. The cube-union volume is a labelled geometric proxy and can be biased by particle disorder; it is not proof of lost liquid mass. Exact or near-exact coincidences independently reject the cases. No damping was added to make the fluid quiet.

Final review found that the wall-free compression proxy had been clipped to an observation window. The original clipped results remain in the main seal. An append-only correction computes the unbounded cube union and does not treat observation-window excursions as physical wall violations. This does not change the pressure data, separation measurement or any policy's failed integration outcome. Original compression-window deficits must not be interpreted as liquid-volume loss. The bare-Wendland explosion produces extreme unbounded coordinates: its volume/grid diagnostics are not physically interpretable and are not used; its independently obvious kinetic-energy failure rejects it.

## Reference agreement and rejected explanations

For the cubic tank, first-step CUDA/reference errors were **1.49×10⁻⁸ m RMS** in position and **1.69×10⁻⁶ m/s RMS** in velocity. With the relaxed Wendland reference patch, they were **3.29×10⁻⁸ m** and **2.97×10⁻⁶ m/s**. Full particle trajectories subsequently separate as clustering develops; bitwise or long-time particlewise agreement was not used as physical acceptance.

The reference and GPU reproduce the large default-weight blowup and the repaired model's clustered equilibrium. This supports a failure of the tested pressure-only coupling and iteration policy rather than explaining it as a CUDA port defect. It does not prove every DFSPH implementation has the same limitation. The scalar reference, source patch and independent current-position audits remain the comparison authorities.

Fixed timesteps were measured, not inferred from requested values. Their binary32 values were approximately 8.333333768, 4.166666884 and 2.083333442 ms. Large-run outgoing CFL values exceeded the nominal 0.4 diagnostic budget, reaching 2.19 for cubic 240 Hz and 4.86 for the Wendland repair. Those runs are not admissible adaptive-timestep policies. Adapting timesteps was not pursued after low-CFL hydrostatic/compression cases already failed particle separation; it would be another unqualified coupling change, not an established real-time saving.

## Complete performance and numerical work

Important timing comparisons ran on the primary RTX 4070, with one warmup and five alternating pairs, optimised precise builds, no concurrent builds/audits/GPU workload and retained slow samples. The timer covers completed solver work, diagnostics, neighbour allocation/search and required host state. DFSPH's 60 Hz observation transfers are included. Construction, teardown, file writing and independent audits are excluded. Production PBF retains its per-step host-snapshot interface; DFSPH is an explicit device-owned prototype, so the interface difference favours the prototype and is disclosed.

| Fluid particles and interval | Production PBF median [range], wall s / simulated s | Cubic DFSPH 240 Hz median [range] | Result |
|---|---:|---:|---|
| 8,000, two seconds | 0.904 [0.897, 0.975] | 0.313 [0.309, 0.314] | Faster, but physically rejected |
| 110,592, five seconds | 3.923 [3.838, 3.943] | 4.317 [4.308, 4.331] | DFSPH slower in all five pairs |

The large result is approximately **10.1% slower** than production PBF. It advances **0.232 simulated seconds per wall second**, requiring about **4.32× more throughput**, or **76.8% less computation**, to reach real time for this rejected policy.

The measured work explains the loss of the small-scene advantage:

| Work per simulated second | PBF, 8,000 | DFSPH, 8,000 | PBF, 110,592 | DFSPH, 110,592 |
|---|---:|---:|---:|---:|
| Density/Jacobi iterations | 3,840 | 1,294.5 | 3,840 | 5,152.0 |
| Divergence iterations | — | 399.0 | — | 352.8 |
| Total iterations | 3,840 | 1,693.5 | 3,840 | 5,504.8 |
| Logical fluid-row sweeps | 9,600 | 4,587 | 9,600 | 12,209.6 |
| Fluid-row entry visits, billions | 2.271 | 1.046 | 37.424 | 42.432 |
| Search count/fill passes | 960 | 480 | 960 | 480 |

These are source-level logical counts, not hardware cache or bandwidth counters. The PBF replay counts the retained full owner/density pass, half suffix pass and full correction pass, giving exactly 2.5 row-entry traversals per iteration. Its endpoint matches production. The DFSPH trace counts each actual source, acceleration and density-response traversal. Reducing search frequency did not compensate for the large pressure solve's work.

At 110,592 fluid particles, cubic DFSPH also discovers **42,240 solid samples**; the larger-support boundary has **65,544**. These costs are included. At the same fluid count, the repaired Wendland run required **11,627.4 density-plus-divergence iterations per simulated second**, and **537 of 600 steps** exhausted the iteration ceiling without reaching tolerance. Its exploratory five-second cost was 25.65 s/s; that single collection included early concurrent CPU auditing and is not an admitted paired performance result. Its exact iteration/cap counts and physical rejection remain valid evidence.

The production PBF control itself fails the practical physical criteria. The [previous frontier](/docs/project/development/milestones/05/performance-frontier.md) is reused for its physical failures; current workload-replay endpoints match the current benchmark. Therefore these timings are **not an equivalent-accuracy speedup claim**. No accepted PBF or DFSPH configuration exists to support one. PBF's implicit mass calibration differs by approximately 0.97% from DFSPH's geometric mass; geometry, fluid count and initial velocities match, and physical references use each model's actual mass.

![Measured cost and workload, timestep refinement and clustered hydrostatic particle sites.](/docs/project/development/milestones/05/assets/dfsph-prototype-v1/dfsph-prototype.png)

## Decision and specific blockers

The prototype demonstrates that DFSPH can reduce work in smaller unloaded or weakly loaded cases. It does not show an acceptable 110,592-particle regime approaching real time. The blockers are concrete:

1. **Particle geometry:** sampled density/divergence convergence permits severe pairing or coincidences in compression, hydrostatic and free-surface cases. Corrected wall density and the established larger-support kernel did not remove it. The independent reference reproduces the failure.
2. **Pressure iteration stability and cost:** default-weight Jacobi diverges in the larger-support control; the single under-relaxation repair stabilises the immediate solve but requires excessive work and frequently misses tolerance in the large case.
3. **Timestep admissibility:** the cheap fixed-step large policies are not uniformly within the advection budget. Increasing temporal resolution does not solve the already observed low-CFL geometry failure and cannot be counted as a throughput improvement.

**Do not integrate this candidate into production or begin CUDA micro-optimisation of it.** If DFSPH is revisited, the entry condition should be a stable, pressure-loaded author-reference configuration that preserves particle geometry under the existing practical criteria and demonstrates a lower measured pressure workload. That is a specific prerequisite, not a request for another solver family, custom pressure discretisation or broad CFD investigation.

The existing PBF solver remains unchanged as the current artefact; this does not upgrade its physical qualification. No new model limitation was waived to claim real time. This study provides a working experimental implementation and a negative integration decision, not a qualified replacement.

## Verification and retention

Eight deterministic tooling/quadrature tests and five live prototype input-rejection cases passed; all sixteen combined new and inherited tool tests passed. The reference comparisons, actual step traces, all benchmark pairs, endpoint-matched PBF workload replays, failed controls, terminated runaway runs and independent audits are retained. Successful independent small-scene audits inspect every stored 60 Hz state. Rejected large trajectories inspect the available states within the first ten steps, aligned 0.125-second and final subset; the retained cadence's intersection gives 0.25-second regular spacing. These are not certified transient maxima over every step.

The raw-data seal contains **18,467 files**, **2,893,403,959 uncompressed bytes**, in **44 archives** totalling **2,258,852,644 bytes**; the largest is 59,350,803 bytes. Each member was read back on the primary PC. A local mirror and a source/reproduction supplement retain the durable handoff, with explicit verification results in the evidence directory. Build trees remain outside both repositories. No Git history, gitlink or system settings were changed.

## References used

<a name="ref-s060"></a> **S060** — Bender and contributors, *SPlisHSPlasH*, pinned author implementation. [Source record](/docs/research/sources/060-splishsplash-pbf-implementation.md).

<a name="ref-s079"></a> **S079** — Bender and Koschier (2017), *Divergence-Free SPH for Incompressible and Viscous Fluids*. [Source record](/docs/research/sources/079-bender-koschier-divergence-free-sph.md).
