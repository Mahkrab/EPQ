# CUDA timestep critical-path evidence

The [engineering assessment](/docs/project/development/milestones/05/performance-timestep-critical-path.md)
retains identity-ordered neighbour rows interleaved in tiles of 32 for inputs of
at least 32,000 particles. The reviewed PC comparison improves large-scene viewer
advancement by 21.88%, from 0.420063 to 0.511983 simulated s/wall s. Complete
live solver calls fall from 9.838930 to 8.029561 ms. This does not establish real
time, sustained particle capacity or a universal crossover for other scenes.

## Identities and source reconstruction

Parent starts at `e7664ee354246507928ac0d80758cffceef0072d`; Maelstrom starts at
`6bf2682325b7665e48f8a8647ce087d48ff13f0b`. Both local trees were initially clean.
The original PC checkout remains separate and unmodified; `environment.json`
records its current identities and pre-existing parent changes. No installed CLI,
clock/power policy, driver, commit, branch, tag, remote or parent gitlink changed.
Experiments live under `/home/oliver/.cache/maelstrom-critical-path-20261109`.

`checks/*-identity.json` records every production-file digest, independently
reproduces the build script's source hash, locates that hash inside the executable,
and hashes its exact NUL-terminated embedded PTX. The ordinary controls and every
admitted ordinary candidate passed this check. The reviewed implementation is:

- source: `a37050dedbc13e1dc4847ac769ff825255d2122297b7c01a87a026e56944f792`;
- executable: `21098e6b9bb405636e7d82760a1daf4f15618f691bdd1c0b39c2fbdae9d1ff14`;
- PTX: 317,123 bytes, `cf4a83d08b2db15e1576a975759b41844d853b2b52e69235890cc254dce45b8b`.

The control source is `c39ac6562e15f6542f7f7271ba6c82ea88708c7e3968456c081a53b2e952667a`,
executable `93fdfdf245cdbc528501a73ae480c2afdde8bfeafaef166d9dd40c3b2472f182`,
and 218,499-byte PTX `2bb95233ef4e5aa5d7f328a3e93715855f8d7dea026c053acc1be8ba666d6203`.

`implementation.patch`, `row8.patch`, `tiled-prototype.patch` and `pre-review.patch`
apply to the Maelstrom base above. `patch-readback.json` records fresh application
of all four patches to isolated base exports and exact production source hashes.
These patches are review/reconstruction evidence, not commits or copied repositories.
The old `final-*` label means the size-selective build **before** the empty-row
pointer guard; `reviewed-*` identifies the actual retained implementation.

The diagnostic-control cache failure is preserved in `diagnostic-cache-failure.md`.
The first `nvtx-*-control` captures used the pre-review candidate executable and are
excluded. `nvtx-rebuilt-*-control` are correct recaptures. A build-script timestamp
refresh forces compilation when sharing a Cargo target cache across exports;
executable/source verification is still required before admission. The ordinary
comparison binaries were correct, so their samples were not replaced.

## Measurement blocks

`protocol.md` records the prospective comparison and subsequent bounded layout
trial/review follow-up. `inputs/` retains the exact three scene/config fixtures.
All ordinary viewer invocations use experimental, CUDA device 0/block 128, the
hardware GL/X11 impostor renderer and all 1,200 timesteps. They use one warm-up
pair (p0) then three measured alternating pairs (p1–p3). No build, test, trace or
hashing work overlaps primary collection. Do not pool the blocks:

| Run prefix | Meaning | Assessment |
| --- | --- | --- |
| `baseline-*` | Fresh control session check | Context only |
| `row8-*` | Eight lanes calculate pair contributions, then consume ordered sums | Reject |
| `tiled-*` | Tiled rows at every size, using a prototype settings selector | Reject as a universal policy |
| `final-*` | Explicit layout setting; compact below 32,000, tiled above | Qualified pre-review comparison |
| `reviewed-*` | Size-selective implementation with empty-row pointer guard | Retain |
| `headless-*` | Separate pre-review `run --unpaced --measure` comparison | Explanatory headless evidence |
| `reviewed-trace-*` | Exact reviewed-source full-motion diagnostic | Attribution only |

`row8-comparison.json`, `tiled-comparison.json`, `final-comparison.json` and
`reviewed-comparison.json` include every measured pair, median and range;
`results.md` provides readable tables. Each viewer directory retains raw frame
CSV, telemetry, command/summary and original log. The reader recomputes frame
summaries and checks completed steps and renderer selection. Surface presentations
are client-window events, not compositor acknowledgement or physical scan-out.

Absolute control rates change materially across blocks; the unchanged control
binary speeds up in the reviewed block. That environmental change is not credited
to the pointer guard or layout. Realtime clock adjustments are visible in command
metadata; elapsed timings use monotonic clocks throughout. No samples are removed
because they are slow. Neither physical-clock calibration nor the cause of the
machine variation was independently established.

`headless-comparison.json` summarises a separate warm-up/three-pair comparison at
all counts. Its raw `stdout.gz`, `stderr.txt` and `process.json` preserve the full
records, including every per-step timer and diagnostic. Physical inputs, accepted
CFL records and final snapshots match across all eight invocations per count.
These are pre-review timings; do not substitute them for reviewed-source viewer
results or add CLI/output time to solver time.

## Critical-path readback

`critical-path.md` exposes every required count and early/evolved windows. Each
admitted trace directory holds `analysis.json` and anonymous
`analysis.events.json.gz`: relative CPU ranges, API intervals and GPU intervals.
Native `.nsys-rep`/SQLite files remain on the PC because they include machine and
process details. No compiled executable, PTX blob or source tree is copied here.

`tools.performance.timestep_trace` adds scoped ranges to a disposable source
export. It never changes the working repository. Diagnostic PTX equals its
ordinary counterpart; the CPU range instrumentation affects scheduling and timing.
`tools.performance.timestep_report` checks complete launch patterns before
attributing general-entry kernels, clips events to complete steps, and subtracts
the GPU interval union when reporting time without solver activity. Inclusive
wait/copy APIs overlap GPU execution and must not be added to it. GPU activity
means this CUDA solver's activity, not utilisation of the whole graphics device.
No unavailable hardware counter is inferred.

Read back retained intervals without Nsight:

```sh
python3 - <<'PY'
import gzip, json
from pathlib import Path
from tools.performance.timestep_report import timeline, kernel_stages
p = Path('docs/project/development/milestones/05/assets/timestep-critical-path-v1/runs/reviewed-trace-110592-reviewed')
events = json.loads(gzip.decompress((p/'analysis.events.json.gz').read_bytes()))
result = timeline(events)
result.update(kernel_stages(events, 110592, True))
assert result == json.loads((p/'analysis.json').read_text())
PY
```

## Correctness witnesses and limits

`trajectories-reviewed/` contains source-identified raw-bit witnesses for 19 cases,
7,440 accepted steps plus initial states per executable. Experimental computes
1,200 steps per count; reference/fast/paper-baseline/scene each compute 240 steps
per count. Experimental/reference effects cases at 32,000/110,592 additionally
exercise XSPH 0.01 and vorticity 0.1. Every state and CFL diagnostic matches.
`equivalence.json` records case hashes/counts. `storage.json` derives actual row
padding and reserved capacities from the diagnostic logs. `trajectories/` retains
the earlier witnesses; all hashes agree with the reviewed counterparts.

`tools/performance/timestep_trajectory.rs` is copied only into isolated examples.
It hashes identity/position/velocity bits after each successful step and prints
its build source identity. `trajectory-probe.patch` adds only row-storage logging;
it changes no kernels. Hashing/logging are correctness diagnostics, never timing
samples. The earlier harness did not retain a source-identity reference in its
linked binary; the reviewed repetition explicitly prints it and passes the same
binary identity check as the CLI. PTX matches each ordinary counterpart.

`rerun-equivalence.json` and raw `runs/rerun-*` records show that the reviewed
executable recomputes saved control inputs from zero at 32,000/110,592 for 1,200
steps, retaining exact final state and complete diagnostic history. This is
recorded-input recomputation, not saved-image playback or simulation resumption.

`reviewed-pixel-equivalence.json` contains 27 equal hardware impostor RGBA/state
digests at all counts, steps 0/240/1,200 and three cameras. `pixel-harness.patch`
selects impostors in the existing ignored hardware harness, identically in both
isolated test exports. Original RGBA files remain on the PC under `results/pixels-*`;
the unchanged rendering implementation and earlier visual galleries remain in
`particle-rendering-v1`. This is offscreen hardware rendering, not a desktop
visibility or keyboard-latency test.

`checks/` retains actual release results: reviewed suite 356 passed/67 opt-in
ignored; 39 explicit CUDA unit checks; strict all-target CUDA/viewer Clippy and
formatting; zero-error Compute Sanitizer memchecks for empty row/block/tail cases
and 16 full 32,000-particle timesteps. Earlier integration/model checks passed
24 CUDA/application/device and 12 viewer tests. Native ASan/UBSan fault injection
covers the added prefix launch, draining, completion/binding errors and poisoned
resources. Groups overlap; their counts are not unique additional tests.
Nineteen local Python checks include negative controls for stale binaries,
incorrect launch patterns, overlapping timing, wrong simulation schedules and
manipulated summaries. Initial failed preflights and the cache rejection remain.

The numerical contract and convincing reference appearance are preserved by exact
state/diagnostic and hardware-pixel equality for these workloads. No new physical
calibration or universal stability claim follows. General padding may approach
32× compact storage, so maximum memory capacity is not unchanged by construction.
Actual device loss, other platforms and hosted verification remain unqualified.
The large scene is about half real time; no 20-second/every-one-second real-time
capacity qualification was claimed.

## Reproduction

The following starts **fresh simulations**, computing every requested step, in an
isolated source export on the primary PC. It neither installs nor replaces a CLI:

```sh
# Run from EPQ; use a fresh, per-export target directory.
CARGO_TARGET_DIR=/path/to/new-target cargo build \
  --manifest-path /path/to/isolated/Maelstrom/Cargo.toml \
  --release --locked --features viewer,cuda
python3 -m tools.performance.timestep_report identity \
  /path/to/isolated/Maelstrom /path/to/new-target/release/maelstrom /new/identity.json
python3 -m tools.performance.live_viewer /path/to/new-target/release/maelstrom \
  docs/project/development/milestones/05/assets/timestep-critical-path-v1/inputs/110592.toml \
  /new/sample --steps 1200
```

Run the Python commands from an EPQ checkout or isolated parent-tool runner.
For an alternating campaign, preserve pair order and separate instrumentation.
The executable, fixtures and input-admission requirements are unchanged. The
headless collector expects `control-bin`, `final-bin`, `inputs/` and a new results
namespace; its `--rerun` mode explicitly recomputes stored control inputs with
`reviewed-bin`. It refuses existing output paths.

These commands only read retained observations and rerun deterministic reader tests:

```sh
python3 -m tools.performance.timestep_report compare \
  docs/project/development/milestones/05/assets/timestep-critical-path-v1/runs \
  reviewed reviewed /tmp/reviewed-comparison.json
python3 -m unittest tests.performance.test_timestep tests.performance.test_live_viewer tests.verification.test_display
```

`SHA256SUMS` covers this package. `audit.json` records local readback of hashes,
all paired summaries, every admitted timeline, state witnesses, source patches
and affected documentation links. The package supports a local engineering
retention decision, not a tagged checkpoint or final project evaluation.
