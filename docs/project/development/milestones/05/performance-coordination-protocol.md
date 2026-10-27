# Host coordination attribution protocol

Measure the remaining host bounds, CFL and neighbour-prefix costs before choosing a device-side
reduction or scan. The control retains [cooperative sorting](/docs/project/development/milestones/05/performance-cooperative-sort.md)
and gradient-prefix reuse on `phase/05-03-optimisation`. Keep the normal Maelstrom source unchanged.

## Diagnostic export

Freeze the current source and create a separate diagnostic export with monotonic CPU clocks.
Gate its logging with an internal environment switch present only during diagnostic requests;
this is temporary instrumentation, not a new supported simulator setting. Record source and overlay
hashes. Use separate Cargo targets, locked offline release CUDA builds, target 89 and precise
arithmetic. Independently compile CUDA code and check its bytes in each executable. Both exports
must contain identical CUDA code: this experiment changes host observation only.

Time these disjoint intervals once per completed step:

- preparation reservations, CPU packing and uploads;
- accelerated-velocity download, repacking and CPU CFL calculation;
- predicted-position download, repacking and CPU bounds/width selection;
- neighbour-count download, CPU prefix calculation, membership reservation and offset upload.

Download intervals include host allocation, context binding, waiting and the blocking copy;
they are not isolated bandwidth measurements. Reservation and upload intervals similarly include
their native wrappers. CPU calculation intervals exclude those transfers. Logging stays outside
the component intervals but remains inside the instrumented whole-step time. Do not add nested
intervals or equate the unmeasured remainder with GPU idle time.

Preserve numerical expressions, input order, calls, error precedence, cancellation and accepted
state. Require exact physical records and warning schedules between control and probe. Report
instrumented totals alongside control totals to expose observer/code-generation effects; their
ratio is not an optimisation result. A hypothetical completely removable fraction is only an
opportunity bound, not a promised device-side gain.

## Collection fixed before measurement

Use the primary PC, explicit CUDA device zero, block size 128, 480 unpaced steps, refinement 4,
eight Jacobi iterations and no rendering. Keep the preceding three workloads: bundled 8,000
particles with checkpoints 0/1/120/240/480; capacity-block-48 with 110,592 particles and no
checkpoints; and that same capacity geometry with XSPH 0.01 and confinement 0.1 m/s enabled.
Retain larger-run warnings and keep the enabled case a separate identity.

Each workload receives one warm-up per variant and three alternating diagnostic pairs, control
first on odd samples and probe first on even samples. Retain every sample and failure. Bound each
simulation to 120 seconds plus 30 seconds cancellation grace. Require 4 GiB available guest RAM
and 2 GiB free GPU memory before collection. Capture environment, commands, exits, source/binary,
input/protocol/collector identities and machine readings outside the invocation timer.

Run the diagnostic release suite and explicitly selected CUDA library/application checks with
logging disabled, plus formatting and strict Clippy. The unchanged native implementation retains
its preceding qualification; do not claim a fresh native or device-memory-sanitiser pass here.
Keep laptop parser/overlay tests separate from primary-PC qualification.

## Analysis and next decision

Require preparation, row and step probe records with explicit step ordinals in order for all 480 steps. Reject malformed,
duplicate, missing, negative or non-finite fields and overlapping totals exceeding the enclosing
solver step. Independently reconstruct component sums, first-step and early/evolved windows,
per-component medians and fractions from raw observations. Reject changed timing and physical
summaries; preserve original failures and sanitise personal paths before publication.

Rank the pure CPU calculations separately from their transfer/packing bundles. Use their measured
share, implementation complexity and contract obligations to select the next bounded prototype.
Bounds must preserve conservative widths and unsafe-domain handling; CFL must preserve finite
checks, exact speed/limit values and failure precedence; prefixes must preserve row bounds,
overflow and allocation decisions. This diagnostic stage does not itself move accepted state,
implement a scan, change physics or establish a retained optimisation.

Record whether the evidence supports a follow-up and what remains uncertain. Follow the
[assessment policy](/docs/project/development/milestones/05/performance-assessment.md); a percentage
cutoff or timing-range overlap must not independently select or reject future work. No commits,
tags, pushes, branch changes, merges or gitlink updates are authorised by this protocol.
