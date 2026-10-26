# Vorticity confinement

## Starting point and numerical decision

This is the second fluid-control change in the Phase 02 [scene plan](/docs/project/development/milestones/05/scene-usability-plan.md),
following [XSPH](/docs/project/development/milestones/05/xsph-viscosity.md). The contract preceded implementation.
The committed starting points remain EPQ `812dea60d8527b8ed977c6bd5d865199397aa374` and Maelstrom
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5);
the accumulated usability and fluid-control work is uncommitted, rather than a historical checkpoint.

The PBF paper estimates curl from velocity differences and kernel gradients, then applies a force
in the direction `N × omega`, where `N` follows increasing curl magnitude. It places confinement
and XSPH after velocity reconstruction.<sup><a href="#ref-s004">S004</a></sup> The following rest-volume
normalisation, difference gradient, units and ordering are explicit Maelstrom choices.

For final projected positions `p`, reconstructed velocities `u`, fixed ordered neighbour rows,
normalised rest density `rho0` in inverse cubic metres and Spiky gradient with respect to `p_i`:

```math
g_{ij}=\nabla_{p_i}W_{\mathrm{Spiky}}(p_i-p_j,h)/\rho_0,
\quad \omega_i=\sum_j g_{ij}\times(u_j-u_i),
\quad \eta_i=\sum_j (|\omega_j|-|\omega_i|)g_{ij},
```

```math
N_i=\eta_i/|\eta_i|\quad (|\eta_i|>0),\qquad N_i=0\quad (|\eta_i|=0),
\qquad u'_i=u_i+\Delta t\,[\epsilon(N_i\times\omega_i)].
```

Every sum uses the existing fixed row, excludes self and recalculates strict final-distance support.
Coincidence gives a zero Spiky direction. The curl sign follows equation 15: the paper differentiates
with respect to the neighbour, so `(u_j-u_i) × (-g_ij)` equals `g_ij × (u_j-u_i)`.
No contacts are discovered again. Curl completes before its magnitudes and gradient are consumed;
confinement completes before optional XSPH reads `u'`. No pass reads partially replaced velocities.

All arithmetic is ordered binary32, including component-wise division of Spiky by `rho0`, cross
products, row sums, checked vector lengths and component-wise division of `eta` by its length.
Acceleration is calculated as `(N × omega) * epsilon`, then multiplied by the timestep before addition.
Every non-finite intermediate fails the attempt; the accepted state is unchanged. No fast maths,
normalisation epsilon or unrecorded clamping is introduced. Underflow to zero follows binary32.

`vorticity_confinement_enabled` defaults to false. New `vorticity_confinement_strength_m_s` defaults to
0.01 and accepts any finite non-negative value, including when disabled. Curl has units s^-1, so
`epsilon` has units m/s and the correction is an acceleration integrated once by `dt`. This is an
energy-restoration control, not a calibrated material property or a promise of stability. Large
strengths can inject excessive energy; timestep refinement is not guaranteed to preserve trajectories.
Uniform velocity, zero curl and zero magnitude gradient receive no correction.

Disabled or zero-strength inputs bypass all confinement work and extra cancellation polls. Active
work polls before curl, between curl and confinement, and after confinement; final acceptance remains
atomic. Its cost belongs to the existing acceptance timing interval on CPU and CUDA. Historical
disabled-default serialisation and comparison keys remain unchanged. Enabled or non-default strength
appends `vorticity-rest-volume-spiky-v1` plus exact strength bits; active records always store strength.
Historical reference outputs are preserved, not regenerated for this different model.

## Implementation and verification

`src/velocity/vorticity.rs` owns the checked CPU calculation; threaded execution only schedules
independent rows. CUDA reuses completed Jacobi scratch for curl and magnitude, writes confinement
into a separate candidate buffer, then replaces the complete velocity snapshot. XSPH consumes that
result. No dependency, reference input, precision flag or benchmark boundary changed.

Saved configuration, scene overrides and temporary `--set` selections use the existing resolver.
Active records retain strength and provenance, so reruns do not require the original scene package.
The Maelstrom input guide explains these controls.

Primary-PC qualification used Ryzen 9 7900X, RTX 4070, driver 610.88, CUDA 13.3.73 and Rust 1.96.0
on WSL2. All 175 source/input hashes matched the local working tree. The isolated copy
used a temporary build cache. Retained
[commands](/docs/project/development/milestones/05/assets/vorticity-validation-v1/commands.json),
[results](/docs/project/development/milestones/05/assets/vorticity-validation-v1/summary.json) and
[source hashes](/docs/project/development/milestones/05/assets/vorticity-validation-v1/source-sha256.json)
identify this working-tree qualification rather than a Git checkpoint.

| Check | Observed result |
| --- | --- |
| Complete CUDA-enabled suite | 287 passed across 35 targets; 26 opt-in checks ignored; historical reference outputs unchanged |
| Explicit confinement suite | 11 passed; independent double-precision oracle, sign, support edges, staging, invalid controls, cancellation and numerical rollback |
| Hardware comparisons | Bitwise CPU/CUDA agreement for counts 0, 1, 2, 33 and 257, with and without XSPH, at blocks 32, 64, 128 and 256 |
| Direct device stages | Separate output, coincidence, support edges and numerical failure/retry passed at all four blocks |
| Existing hardware regressions | Eight XSPH checks and seven CUDA execution checks passed when explicitly selected |
| Native bridge | Injected-driver checks passed under host ASan/UBSan |
| Local integration | 16 targeted headless checks and 71 viewer-enabled checks passed; five display/device checks remained opt-in |

The first full suite found a stale provenance assertion: older files do not contain
the new strength, so its source is the built-in default. That specific expectation was corrected;
the failure is retained. A local viewer run also failed a diagnostic assertion while CPU
and viewer builds shared the debug executable. A sequential rerun passed without changing viewer
behaviour. Both failures are retained.

## Outcome and limitations

Both fluid effects are implemented locally. Disabled defaults and zero strength retain legacy bits;
confinement and smoothing are distinct optional numerical models, rather than performance changes.
Strength is deliberately not advertised as a calibrated fluid property. This qualification covers
small deterministic cases, not long-running physical accuracy, competitive performance or new visual
hardware coverage. No hosted check or device-memory sanitizer result is claimed.

The remaining scene-usability work is the complete user-journey verification in the plan. No phase
completion or gate decision is established here. Both repositories remain on their existing branch,
uncommitted, with the EPQ gitlink unchanged.

## References used

<a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*, algorithm 1
and equations 15–17. [Source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).
