# PBF architectural investigation evidence

**No experimental implementation is retained in production.** The
[assessment](/docs/project/development/milestones/05/performance-architecture.md) explains
which costs were measured, why the published workloads are not equivalent, the independent
CUDA comparison, and the failed physical-health screens. All ten optimisations and production
semantics remain unchanged.

The [prospective protocol](protocol.md) preceded collection. Production source is Maelstrom
`250932784790ba26cdc55fc38a877ccefacbf054`, whose 191-file manifest matches the preceding
control. [Preservation receipt](production-preservation.json) records independent parent/submodule
states. The reused CLI has a null embedded build revision; source/embedded-PTX hashes
bind it to the control, rather than a fresh Cargo build. No commits, branches, tags, pushes, installed commands, drivers, registry or security
settings were changed. Ordinary build/JIT caches and private task contexts may change.

## Work and interpretation

Important GPU measurements ran on the primary PC through `ssh pc`: Ryzen 9 7900X, RTX 4070,
WSL2, driver 610.88 and CUDA 13.3.73. Main cases contain 8,000/110,592 particles,
480 steps, eight Jacobi iterations, refinement four, no rendering or pacing, CUDA zero/block 128.
Refinement resolves dt to 0.0020833334 s and correction scale to 0.0625. Effects checks
separately enable XSPH 0.01 and confinement 0.1. Parameter curves and five-second extensions
have their own requests.

The ordinary control is the production CLI, plus an explicitly different native replay driver.
Native trajectories match the admitted production snapshots, but the driver does not reproduce
the transactional API, cancellation callbacks, CFL warning publication, allocation decisions or
all host-validation costs. Its conservative row capacity is 512 per particle (216 MiB at large N);
production remains unrestricted. Resident execution changes observation/failure ownership and
uses the validated bounded-scene width 0.125 m. Experimental timings must not be relabelled as
production speedups. The large production request retains 259 CFL-warning steps.

Every primary case retained one warm-up and five alternating pairs. There are **140 measured
pairs**, with all slow samples retained. Curves and long runs are single diagnostic observations;
profiles explain mechanisms and do not replace unprofiled samples. Native completed-step clocks
include completion before return, not enqueue time. Cold setup, teardown, requested observations,
output and independent analysis are separate. [Production/native boundary samples](boundaries.json)
quantify the difference rather than silently treating the two APIs as identical.

## Material retained

| File | Purpose |
|---|---|
| [summary.json](summary.json), [extra-summary.json](extra-summary.json) | Every paired value, median, range, paired ratio and final-bit comparison |
| [admission.json](admission.json) | Control/checkpoint and exact architectural replay admission |
| [health.json](health.json), [final-health.json](final-health.json) | Independent current-position density/neighbour checks and relaxed arithmetic errors |
| [wall-health.json](wall-health.json) | Wall/bulk grouping; common metrics verified identical to the earlier reader |
| [external-primary-health.json](external-primary-health.json) | Independent solver's five measured endpoints, including physical variation |
| [curves.json](curves.json), [extended.json](extended.json) | Iteration/refinement cost-error points and five-second stability/error observations |
| [profiles-audited.json](profiles-audited.json) | Twelve source-correlated CUDA/NVTX timelines, disjoint wall accounting and overhead observations |
| [analytic-summary.json](analytic-summary.json), [contact-final.json](contact-final.json) | Free-fall accuracy failures, independent binary32 recurrence and corrected stationary contact |
| [comparator-cap-audit.json](comparator-cap-audit.json), [readback](comparator-cap-readback.json) | Supplementary full-trajectory cap checks and an effective positive control |
| [independent-audit-final-v2.json](independent-audit-final-v2.json) | Original-PC raw integrity, timing arithmetic, trajectory and identity checks |
| [production-identity.json](production-identity.json), [provenance.json](provenance.json) | Source/commit, binary and freshly embedded production PTX identity |
| [archive-members.json](archive-members.json), [blob-index.json](blob-index.json) | Complete member hashes and reconstruction of deduplicated binary observations |
| [trace-privacy.json](trace-privacy.json) | Original/exported SQLite identities and unchanged CUDA/NVTX/string-table fingerprints |

The archives contain the following, under their original task-relative paths:

- `observations.tar.xz`: raw process records, compressed stdout, stderr, metrics and quality results.
- `verification.tar.xz`: build commands/results, identities, environment, permission failure,
  device memory checks and PC reader tests; precise PTX is retained.
- `profiles.tar.xz`: sanitised SQLite CUDA/NVTX event tables, profiler commands, outputs,
  ordinary/profile overhead pairs, and analyses.
- `inputs.tar.xz`: actual resolved binary particles/settings, configurations, planes and
  separately labelled experimental inputs.
- `investigation.tar.xz`: frozen collection/analysis/adaptation scripts, measured tool versions,
  failed setup logs, source receipts and decisions. These are historical evidence; maintained
  tooling lives in `/tools/` and verification in `/tests/`.
- `states.tar.xz`: 164 content-addressed objects reconstructing 1,099 binary state/offset files.
  Deduplication preserves every observation's exact bytes, not just a chosen endpoint.

`comparator-cap-audit.tar.xz` is a separate supplementary diagnostic: two builds,
twelve full trajectories and one cap-16 positive control (15 raw attempts). Every
ordinary trajectory recorded zero capacity events; the positive control recorded
7,779. Its source deltas, protocol, collector, commands and counter outputs remain
separate from the 140 primary pairs. Diagnostic endpoints remain on the PC with
retained fingerprints; their clocks are not used as performance samples. Tar owner
metadata is normalised; all member payloads passed independent readback.

Executable hashes are retained; disposable executables and unredacted `.nsys-rep` files remain
on the PC rather than in this publication. Complete source repositories, build caches and `.git`
are not included. The native deltas apply to the pinned Maelstrom native sources; FMA changes
only compilation flags. The unlicensed upstream archive is not redistributed: the independent
comparator has a full revision, file manifests, short alignment delta, our headless adapter and
reconstruction script. See [S070](/docs/research/sources/070-barnden-cuda-pbf.md).

The measured Python frontend is preserved as `architecture-measured.py`. Its later maintained
frontend explicitly selects effects-enabled input files and respects disabled artificial pressure;
those changes do not alter collected commands or native algorithms. Reader v1/v2 sources are
both retained. The second reader adds wall grouping only, with identical common metrics.
Byte comparisons enforce signed-zero bit identity; `equal_position_components` in the health
reader counts numeric equality and is not the bit oracle. Nearest separation is censored at h
for isolated particles.

## Failures, limitations and privacy

The failed missing-output-directory build, non-executable copied CLI, initial external constexpr
build, interrupted large checkpoint audit and denied counter attempt are preserved. Corrected
setups preceded admitted timing. The deliberate SIGINT and the reason for replacing the large
checkpoint request with final-state-only collection are in [actions.json](actions.json).

The binary32 free-fall test failed its declared 0.001 m/0.001 m/s bounds; those failures remain.
The initial contact fixture was outside its x/z planes. Its corrected input is a distinct retained
fixture; [input history](contact-input-history.json) records the exploratory path reuse and both
exact byte identities. No failing criterion was weakened. The original and partially aligned
independent solvers retain missing-self/duplicate-row results and are not admitted comparators.

The first timeline re-analysis incorrectly required entire GPU intervals to fit host ranges.
Clock alignment places some tails a few microseconds outside them. The corrected analysis uses
host launch correlation to preserve every kernel, excludes setup kernels, and clips only the
wall partition. Existing captures were re-analysed; no timing sample was replaced. Both scripts
and the failed re-analysis log remain.

Nsight captured process environment/account information by default. The retained SQLite exports
remove environment variables, usernames, hostname and unnecessary installation/network metadata,
then vacuum removed pages. All CUDA activity, NVTX and StringIds tables have identical before/after
fingerprints. Unredacted profiler reports are not published. No credentials or environment values
are printed by the privacy check.

Physical screening failed even for the unchanged control; archive/audit success does not certify
fluid accuracy. The reader independently checks density with current neighbours rather than frozen
rows or solver density buffers. Larger numerical errors, hardware counters, native Linux, actual
device-loss recovery, unrestricted comparator capacity and equivalent published-scene accuracy
remain unqualified. Full Rust tests were not rerun because production source did not change.

## Rechecking without launching a simulation

From the EPQ repository root, these commands read retained observations, restore them to a new
scratch directory, and audit their integrity. They do not start or resume a simulation.
The destination must not already exist. The commands restore the six main archives;
the supplementary counter archive has its own readback receipt.

```sh
python3 -m tools.performance.architecture restore docs/project/development/milestones/05/assets/architecture-v1 --destination /tmp/pbf-architecture-readback
python3 -m tests.performance.audit_architecture /tmp/pbf-architecture-readback
python3 -m unittest tests.performance.test_architecture_quality -v
```

Restoration verifies archive/index hashes, every member and every deduplicated state. It refuses
existing destinations, traversal paths, symlinks, duplicate members and changed bytes. Packaged
verification correctly reports source/executable checks unavailable when the corresponding
worktrees/binaries are absent; the original-PC receipt records **14 executable identities and
222 source hashes**, with **740 raw attempts**, **140 measured pairs** and **13 production snapshot
checks**. Do not interpret unavailable packaged checks as passes.

Rebuilding or collecting starts new simulations and requires the matching PC/toolchain, a fresh
output directory, the pinned native source, the retained resolved inputs and the recorded
variant flags. `/tools/performance/architecture.py`, its CUDA driver, independent reader and
headless adapter own the maintained experiment code. Collection refuses reused destinations.
Do not copy an experimental source or executable into Maelstrom or an installed command.
