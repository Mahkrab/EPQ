# CUDA position-correction integer quartic evidence

The [assessment](/docs/project/development/milestones/05/performance-correction-integer.md)
records diagnosis, implementation, measured gains, regressions and the retention
decision. The [protocol](/docs/project/development/milestones/05/assets/correction-integer-v1/protocol.md)
was written before profiling/candidate collection. The
[integer reconstruction argument](/docs/project/development/milestones/05/assets/correction-integer-v1/integer-quartic-proof.md)
explains why both retained rounding stages and the guard decision remain exact.
Every benchmark request starts a new simulation on the primary PC; campaigns are
not pooled with earlier work.

Control exactly matches the retained
[active-distance candidate](/docs/project/development/milestones/05/assets/active-distance-v1/candidate-source.json).
Both simulator exports contain 189 files. Maelstrom remains at
`1e0085926d05c42949bb76b55d177d42a1f8f94f` with the prior uncommitted density and
active-validation implementation; EPQ remains at `1f76097a218266822cdf344c38db75ed128628a8`
with its existing untracked evidence. These are frozen source exports, not new Git
checkpoints. No ordinary PC checkout, installed executable, history, branch, tag,
remote or gitlink changed.

Export that Maelstrom base into a new directory, apply `control.patch` with `patch -p1`
and verify every `control-source.json` hash. Applying `candidate.patch` next
reconstructs the complete final live candidate. Only the power helper, its exhaustive
test and CUDA documentation change. `source-reconstruction.json` also verifies the
three diagnostic and one exploratory patches against their manifests.

`investigation.tar.xz` contains four fresh pre-implementation control records,
six diagnostic records, twelve exploratory records, raw compressed outputs,
privacy-limited device activities, source identities/patches, commands, collectors,
readers and compiler analysis. Initial profiles cover both particle sizes. Probes
at large size add geometry, Spiky/Poly6, then pressure before original correction;
they reuse finished scratch without replacing the real numerical/diagnostic pass.
Eight extra launches per step and changed cache/scheduling conditions make their
interval differences attribution evidence rather than additive production costs.
All probe solver resources were 52 registers, matching control. No cache/bandwidth
or achieved-occupancy counters were collected. `compiler-analysis.json` records PTX
operations and its hash; full generated PTX stays on the PC.

Fresh precise PTX was checked inside the corresponding executable before each
profile/trial collection. `trial-final-binding.json` independently rechecks the
untouched exploratory executable and verifies its PTX equals final production PTX.
`trial-power-identity.json` records the preliminary exhaustive test's identities
after collection; its internal elapsed time is available, but full child duration
was not recorded. Final qualifiers have complete command/exit/duration records.

`observations.tar.xz` retains all 50 final regression/warm-up/measured outputs,
four ordinary-binary full-motion profiles, summaries, source/binary/PTX identities,
input copies/hashes, platform/resource admission, exact commands/exits/timeouts and
monotonic child/collector clocks. One warm-up pair and five alternating measured
pairs were retained per primary workload, plus seven regression pairs. Source hashes
were rechecked afterwards. Warnings and slower samples were not replaced.

Completed-step clocks include preparation, checks, transfers, launches, completion,
cancellation and acceptance. Construction, teardown, output/storage and audits are
separate. Child `wall_s` ends before storage; `collector_wall_s` includes it. GPU
intervals come from separate profiled runs and exclude host gaps. Own task probes,
qualification and audits were outside primary timed collection. CPU affinity,
clock locking and exclusive-machine isolation were not qualified.

`measurements/activity.sqlite` retains only kernel/API names/times/correlations and
copy sizes/directions. Stage attribution follows the source-owned submission sequence,
verified against kernel types, counts and API correlation. The independent reader
reconstructs every iteration, early/late bands, waits and the exact copy schedule.
Native Nsight reports/SQLite, frozen trees, PTX and executables remain under
`/tmp/maelstrom-correction-20261028` on the PC. No whole source trees, binaries,
build caches, full PTX or private native profiler metadata are archived here.

`verification.tar.xz` contains release/explicit CUDA, Clippy, formatting, native
ASan/UBSan, exhaustive qualifier, CPU feature-isolation and device-sanitiser logs,
plus resource probes and automation. The candidate's native exhaustive fixture is
also compiled against the retained header. Initially the control-labelled compile
used a test inside the candidate directory; its quoted include selected the local
candidate header before `-I`. Those outputs remain but are excluded as control
evidence. `reference-power.py` moves the same test outside both source trees,
checks dependency output selects the intended header, then builds/runs both variants
at blocks 32/64/128/256. Header and test hashes are checked against the source freezes.
`verification-notes.json` records this harness correction; production and timing
samples did not change.

Each corrected exhaustive run covers all 2,147,483,648 non-negative binary32 words:
zero result/guard mismatches, 529,216,975 accepted words and 354,191 unguarded-quartic
negative-control mismatches. The independent binary64 guard in that fixture is checked
against the original control body. Other exponents, negative fallback, surrounding
correction order and stage/error code remain unchanged.

Compute Sanitizer exited 97 with sixteen WDDM debugger/device-support errors even
though two functional tests passed. This is no device-memory diagnostic pass;
racecheck was not run. Other devices/compilers, other-block performance, real device
loss, worst-case cancellation latency and independent fluid quality remain unqualified.

`files-sha256.json` indexes all 578 uncompressed members. `archive-readback.json`
records their verification and reproduction of all three independent audits after
extraction. `SHA256SUMS` covers all asset files except itself.

These commands inspect saved evidence without starting a simulation:

```sh
cd docs/project/development/milestones/05/assets/correction-integer-v1
sha256sum -c SHA256SUMS
correction_evidence=$(mktemp -d)
tar -xJf observations.tar.xz -C "$correction_evidence"
tar -xJf investigation.tar.xz -C "$correction_evidence"
tar -xJf verification.tar.xz -C "$correction_evidence"
cp control-source.json candidate-source.json "$correction_evidence/"
python3 "$correction_evidence/audit.py" "$correction_evidence/measurements"
python3 "$correction_evidence/initial-audit.py" "$correction_evidence"
python3 "$correction_evidence/investigation-audit.py" "$correction_evidence"
```

For a fresh collection, reconstruct separate complete source copies and distinct
`CARGO_TARGET_DIR`s first. The archived `initial.py`, `build-probes.py`,
`profile-probes.py`, `trial.py`, `verify.py`, `measure.py`, `reference-power.py` and
`postcheck.py` retain exact commands/environment. Change their scratch root and
exclusive output locations together; do not reuse an existing result directory.
Run initial profiling before trials, qualification before primary collection, then
independent audits, correctly selected header qualification and device/resource
probes afterwards. `verify.py` retains the original include-selection mistake;
use the explicit `reference-power.py` overlay for actual retained-header evidence.
Copied large-scene/default inputs are in `inputs/`; small bundled scenes are bound
by the control manifest. Collection verifies identities and resource admission
before running and enforces bounded child times.
