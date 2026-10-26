# XSPH velocity smoothing

## Starting point and scope

This is the XSPH part of Phase 02's [fluid-control work](/docs/project/development/milestones/05/scene-usability-plan.md).
This numerical revision was recorded before implementation, extending the uncommitted work on
`phase/05-02-scene-usability`. The committed baseline remains
Maelstrom [`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5) and EPQ
`812dea60d8527b8ed977c6bd5d865199397aa374`; neither contains these changes.

## Numerical decision

The PBF paper places XSPH after velocity reconstruction and describes a kernel-weighted correction
from neighbouring velocity differences in equation 17.<sup><a href="#ref-s004">S004</a></sup>
Maelstrom uses metre-based, normalised Poly6 kernels, so its coefficient multiplies a dimensionless
rest-volume weight. This normalisation is a project decision, not a claim that the paper specifies
the same units or coefficient calibration.

For final projected positions `p`, reconstructed velocities `u`, normalised rest density `rho0`
in inverse cubic metres and dimensionless coefficient `c`:

```math
w_{ij}=W_{\mathrm{Poly6}}(\lVert p_i-p_j\rVert,h)/\rho_0,
\qquad
v_i=u_i+c\sum_{j\in N_i,\;\lVert p_i-p_j\rVert<h}(u_j-u_i)w_{ij}.
```

`N_i` is the existing fixed timestep row discovered at predicted positions. Self is excluded;
final distances are recalculated, including coincident pairs and excluding exact support contact.
New contacts outside those fixed rows wait until the next timestep, preserving the existing search
contract. No additional discovery is introduced.

All arithmetic is binary32. Rows retain ascending particle identity. Each contribution calculates
Poly6, divides by `rho0`, subtracts velocities, multiplies by the weight and adds to an ordered sum;
the complete sum is multiplied by `c` once, then added to `u_i`. Every row reads the same immutable
position/velocity snapshot. All reconstructed velocities finish before smoothing begins, and all
smoothed velocities finish before replacement. Non-finite intermediates fail the whole timestep.

`xsph_viscosity_enabled` remains false by default. New `xsph_viscosity_coefficient` defaults to 0.01
and accepts finite `0 <= c <= 1`, even when disabled. Disabled or zero-coefficient inputs bypass
smoothing entirely, preserving existing bits and cancellation boundaries. Non-zero enabled smoothing
adds cancellation boundaries before and after the complete pass; acceptance remains atomic.
The existing acceptance timing interval includes this velocity work on both CPU and CUDA.

The correction runs once per timestep, without another timestep factor. Refining the timestep
therefore applies smoothing more often over the same simulated duration; coefficients require renewed
assessment. Rest-volume weights are symmetric for equal-mass reciprocal rows, but are not divided by
their row sum. Highly compressed states can oversmooth even within the accepted coefficient domain.
Start near 0.01; this is a numerical coherence control, not calibrated viscosity in Pa s.

Legacy serialisation and comparison identities remain unchanged at the disabled default. Enabled
inputs, or a non-default coefficient, append `xsph-rest-volume-poly6-v1` and the coefficient's exact
bits to the comparison key. Enabled zero still identifies the explicitly chosen model. Historical
goldens remain the disabled reference, rather than being regenerated for a different calculation.

## Implementation and verification

`src/velocity.rs` owns the checked calculation. Serial and threaded execution differ only in row
scheduling. CUDA reads reconstructed velocities into the existing candidate buffer, then replaces the
velocity snapshot in a separate stream-ordered pass. Disabled and zero-strength runs launch neither.
No dependency, precision flag, numerical reference file or measurement boundary changed.

Enabled records always contain the coefficient. Disabled-default records retain historical field order
and omission rules. Tests corrected a replay provenance mismatch without regenerating goldens. CLI
checks cover saved values, overrides, invalid coefficients and replay after deleting source files.

Qualification ran on the primary PC: Ryzen 9 7900X, RTX 4070, driver 610.88, CUDA 13.3.73 and Rust 1.96.0
on WSL2. The isolated source copy matched all 172 local source/input file hashes. It is a tested working
tree, not a Git checkpoint. [Commands and environment](/docs/project/development/milestones/05/assets/xsph-validation-v1/commands.json),
[raw results](/docs/project/development/milestones/05/assets/xsph-validation-v1/summary.json) and
[source hashes](/docs/project/development/milestones/05/assets/xsph-validation-v1/source-sha256.json) are retained.

| Check | Observed result |
| --- | --- |
| Complete CUDA-enabled suite | 277 passed across 34 targets; 23 opt-in checks ignored; historical numerical references passed unchanged |
| Explicit XSPH suite | Eight passed, including the hardware matrix; CPU/CUDA outputs matched every particle bit for counts 0, 1, 2, 33 and 257 at blocks 32, 64, 128 and 256 |
| Device stage | Coincidence, strict support edges, separate candidate output, numerical failure/retry and cancellation boundaries passed |
| Existing device execution | Seven regression checks passed when explicitly selected |
| Native bridge | Injected-driver checks passed with host ASan/UBSan |
| Local integration | 68 focused headless checks, 37 authoring/numerical checks and 71 viewer-enabled checks passed in separate runs |
| Static and document checks | Strict CUDA/viewer Clippy, Rustdoc, formatting, Markdown unit tests and local links passed |

The first PC suite exposed CPU tests relying on automatic backend selection; they now explicitly select
serial grid for their CPU assertions. A later check identified the new field's built-in provenance in
older configuration files. Native negative tests were updated to use an actually unsupported operation
ID after adding the smoothing passes. Earlier PC failures are retained.

Your edited bundled two-block scene was preserved. Small interaction tests now own a fixed 128-particle
fixture, so editing the example no longer changes their expected inputs. The larger example is not a
new capacity or performance result. Local checks used Rust 1.98.1; local log paths are redacted only.
No hosted, device-memory sanitizer or new rendering qualification is claimed.

## Outcome and remaining work

XSPH is implemented and independently checked across the supported execution modes. Vorticity
confinement is the next separate fluid-control change; the complete fluid-control step remains open.
Both repositories remain uncommitted on their existing branch, with the EPQ gitlink unchanged.

## References used

<a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*, algorithm 1
and equation 17. [Source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).
