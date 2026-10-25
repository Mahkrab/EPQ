# Evolved neighbour traversal evidence

Two separate primary-PC campaigns assessed cell lookup reuse without changing
numerical work. The [decision record](/docs/project/development/milestones/05/performance-neighbour-traversal.md)
explains the result and limitations. Nothing here is a hosted check or a new Git checkpoint.

## Campaigns and decisions

- `merged/` is the original continuous-range scan. Its large pairs were all slower;
  its recorded engineering decision is **do not retain**.
- `cell-runs/` keeps the three cell scans separate and advances one cursor between
  them. All five large pairs improved; its engineering decision is **retain**,
  with the mixed smaller-workload timings explicitly retained.

Each directory has its own exact source/executable identities, original protocol,
summary, paired evidence, independent audit and assessment. Do not pool campaigns
or present the first version as a pass. Machine state readings surround individual
invocations and remain outside their timers; Linux counters do not describe all
Windows activity. Unavailable GPU fields are not passes.

Requests use CUDA device 0, 128 lanes, 480 steps, timestep refinement 4 and eight
iterations. The 8,000-particle case keeps checkpoints 0/1/120/240/480; the 110,592
case omits checkpoint audits. Seven smaller fixtures and five capacity sizes retain
their original physical controls and warning schedules. Larger warnings are a
fluid-quality limitation, even when every value agrees exactly.

The follow-up reused the unchanged control executable and its qualification;
both variants received fresh timing samples. Candidate qualification ran again.
The PC suites each report 259 passes and the same three existing CLI failures.
Early setup failures are retained privately: an ambiguous empty-vector test type
was corrected, and a personal scene-library error was removed by isolating test
configuration. No production scene or test assertion was weakened.

## Reading or independently checking the data

For each campaign, extract its archives into a separate empty directory and copy
its readable JSON/Markdown files alongside them:

- `primary.tar.xz`: paired small requests, regression fixtures, telemetry and environment.
- `large-control.tar.xz` and `large-candidate.tar.xz`: all large warm-ups and samples.
- `capacity.tar.xz`: independent serial pilots and CUDA capacity trajectories.
- `traces.tar.xz`: full evolved timelines and their physical results.
- `verification.tar.xz`: original qualification commands, exits and logs.

`merged/references.tar.xz` contains the shared physical reference results. Extract
it into **both** reconstructed campaign directories. The follow-up's
`reference-reuse.json` checks all 54 reference files and identifies that exact archive;
the duplicate archive is intentionally omitted. `inputs.tar.xz` and
`input-hashes.json` preserve the actual scene/configuration inputs separately.

Run `python3 -m tests.performance.audit_arithmetic DIRECTORY DIRECTORY/summary.json`
from EPQ to recompute physical comparisons and timing evidence. The independent
trace reader is `tests/performance/audit_neighbour_bands.py`. Its checks use raw
kernel timestamps, correlations, transfer counts and completion counts; false
window durations, operation totals and counts are rejected. False medians, pair
savings and automatic retention verdicts are rejected separately.

`source-review.json` checks the retained candidate against the current 152-file
source snapshot. Sources differ only in `native/neighbours.cuh`; the tests and
pre-existing graphics work are shared. The unrelated custom scene is excluded.
Snapshot `tree_sha256` values hash `json.dumps(files_sha256, sort_keys=True).encode()`
with Python's default separators. They are file-manifest hashes, not Git tree IDs.

Native profiler reports, executables and raw source snapshots remain in private
operational storage. Published SQLite exports remove process environment/private
metadata and vacuum old text; analytical table hashes are checked before and after
that change. They independently reproduce the reported operation windows. Original
and shareable hashes are distinguished in `privacy.json`. CPU bridge ASan/UBSan
checks do not establish device-memory sanitiser or real device-loss qualification.

`local-verification.json` identifies laptop checks separately from PC evidence.
The root manifest hashes the published files; an annotated tag or GitHub CI result
is not implied by those hashes.
