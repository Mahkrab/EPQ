# Neighbour/traversal experiment evidence

The [assessment](/docs/project/development/milestones/05/performance-neighbour-reuse.md)
rejects three implemented prototypes and retains the current CUDA implementation.
No new production optimisation is installed. The real-time target remains unmet.

## Identity and reconstruction

Parent HEAD is `e7664ee354246507928ac0d80758cffceef0072d`; Maelstrom HEAD is
`6bf2682325b7665e48f8a8647ce087d48ff13f0b`. Both trees started dirty. These are base
commits, not complete experiment identities or new historical checkpoints.

From an isolated archive of that Maelstrom commit, `control.patch` reconstructs
the initial 266-file working export, including existing uncommitted tiled rows.
Then apply exactly one of `cooperative.patch`, `spatial.patch` or `geometry.patch`
for its rejected prototype. `checks/control-files.json` records all initial file
hashes. `checks/patch-readback.json` proves fresh application and matching source
digests; `checks/*-identity.json` independently identifies the ordinary executable,
its embedded source digest and exact embedded PTX. No source tree, executable,
PTX blob or installed CLI is included here.

| Export | Production-source SHA-256 |
| --- | --- |
| Control | `89ad00ed994f82d6c052e5bbebe9a5eec4f581cdc53293250244fc8fa412a529` |
| Cooperative discovery | `323befd1ef7f2aff3f6d810ce3133173d00b23ca973eebc7adb467b329b0f10e` |
| Spatial tiles | `a752a44aaf15f195ff99645369bc3ad9df6a8ea9cf220d5098ce3402d7e0354c` |
| Exact geometry cache | `b855ff9b807e68a27916b9a913dbe4a5f94dd12244129c7b3d5224fb92486df0` |

The PC exports remain under
`/home/oliver/.cache/maelstrom-neighbour-traversal-20261110`. They are disposable
measurement sources, not branches or published checkpoints. `environment.json`
in `checks/` records the actual device/toolchain. The ordinary checkout, installed
binary, driver, system policy, history and parent gitlink were not modified.

## Samples and independent readback

`protocol.md` records the prospective hypotheses, fixed measurement plan and
bounded closing comparison. `inputs/` contains the exact adjacent scene/config
fixtures. Every viewer invocation accepts 1,200 steps with experimental mode,
CUDA 0/block 128, hardware X11/GL at 1280×720 and analytic sphere impostors.

| Directory prefix in `runs/` | Meaning |
| --- | --- |
| `fresh-<count>-*` | Control warm-up and session baseline at all three sizes |
| `explore-<variant>-110592-p*` | Independent warm-up pair p0 and two measured alternating pairs p1/p2 |
| `final-spatial-<count>-p*` | Separate warm-up p0 and three measured pairs p1–p3 at every required size |
| `trace-<variant>-<count>` | Separate full-motion diagnostic, never a primary timing sample |

There are 48 ordinary viewer invocations and six diagnostic invocations. Keep
these blocks separate. All raw frame CSVs, telemetry, original viewer logs,
commands and summaries remain, including slower runs. `checks/spatial-comparison.json`
contains per-pair ratios, medians, ranges and command times. The exploratory
comparison is separate. Existing tools can recompute the final comparison:

```sh
python3 -m tools.performance.timestep_report compare \
  docs/project/development/milestones/05/assets/neighbour-cooperative-v1/runs \
  final-spatial spatial /tmp/spatial-readback.json
```

`checks/timing-readback.json` verifies the 24 final samples and independently
recomputes all six complete trace analyses from retained anonymous events.
Each trace contains `analysis.json` and `analysis.events.json.gz`. Native Nsight
reports/SQLite stay on the PC because they contain process/machine details.
`tools.performance.timestep_trace` supplies the diagnostic-only NVTX overlay;
trace PTX is checked against each corresponding ordinary executable. Launch
sequence checking assigns operations before summing kernel time. Inclusive
wait/API intervals are never added to GPU activity; idle means absence of this
solver's GPU activity, not device-wide inactivity.

## Qualification, memory and failures

`trajectories/` preserves each initial-state digest and every accepted raw-bit
identity/position/velocity digest with its CFL record. Seventeen control/spatial
pairs cover 6,960 steps per build across all numerical modes, required counts and
experimental effects. Cooperative and geometry prototypes additionally match the
1,200-step large control. These are correctness witnesses, not throughput samples.
The witness source is `tools/performance/timestep_trajectory.rs`.

`replay/` retains the original compressed run and two recorded-input rerun outputs,
process status and hashes. `checks/rerun-equivalence.json` records exact state and
diagnostic agreement. These commands recompute inputs from step zero, rather than
resuming saved observations. `checks/pixel-equivalence.json` records 27 exact
hardware impostor pixel/state matches. Original RGBA files remain on the PC.
The pixel test uses the existing test-only
[pixel harness overlay](/docs/project/development/milestones/05/assets/timestep-critical-path-v1/pixel-harness.patch).

Fresh ordinary, explicit CUDA/application/graphics, Clippy, native ASan/UBSan and
three zero-error device memcheck logs are retained under `checks/`. The assessment
gives exact counts and overlapping groups. Formatting fails only for the initial
user-authored trailing space in `Settings.count`; it is deliberately preserved.
Rejected prototypes receive component/trajectory checks, not a full production
retention or sanitizer qualification.

`checks/memory.json` records separate 1,200-step storage witnesses. The memory
probe patch adds explicit logical-total/readback and reservation logging; its
instrumented source receipts and logs are retained. Its state witnesses match
control, but none of its timings enter the benchmark. Driver-loaded register/local/
shared requirements are in `checks/resources.json`; these are not occupancy metrics.

Every preflight failure remains: attempted old-control reuse rejected for a source
mismatch; spatial scratch/width setup failures and subsequent corrected passing
runs; and the stale shared-Cargo trajectory artefact caught by its source receipt.
No invalid build enters an admitted ordinary timing or trajectory comparison.
`checks/collection-scripts.patch` records the task-only collection commands and
resource probe; `checks/parent-tools.json` identifies the reused parent tooling.
Those scripts are provenance for these exports, not new maintained production tools.

`SHA256SUMS` seals the retained artefacts. Production files were checked against
the initial manifest after the investigation. No prototype source edits are copied
into the working Maelstrom tree and no existing user work is discarded.
