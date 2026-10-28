# CUDA active-distance validation evidence

The [assessment](/docs/project/development/milestones/05/performance-active-distance.md)
records the retention decision, numerical argument, timings, regressions and limits.
The [prospective protocol](/docs/project/development/milestones/05/assets/active-distance-v1/protocol.md)
was written before implementation and collection. Every benchmark request starts a
new simulation on `ssh pc`; these measurements are separate from earlier campaigns.

The control exactly matches the retained
[density/lambda candidate](/docs/project/development/milestones/05/assets/density-lambda-v1/candidate-source.json),
including its existing uncommitted source, tests and documentation. Neither repository
was clean at the start: EPQ already held that untracked evidence and Maelstrom its
implementation. The Maelstrom base remains `1e0085926d05c42949bb76b55d177d42a1f8f94f`;
EPQ remains `1f76097a218266822cdf344c38db75ed128628a8`. This records two frozen source
exports, not a new historical checkpoint. No ordinary PC checkout, installed binary,
commit, branch, tag, remote or gitlink was changed.

`control.patch` applied with `patch -p1` to the base Git archive reconstructs all
188 control hashes. Applying `candidate.patch` next reconstructs all 189 candidate
hashes, including the final live tree. `source-reconstruction.json` records those
checks. The new delta changes only CUDA numerical source/layout, bridge capacity
validation, Rust storage sizing/test declaration, focused tests and CUDA documentation.
No whole source trees, binaries, caches, PTX or native profiler reports are here.

`initial-profile.tar.xz` contains fresh pre-implementation warm-ups and full 480-step
control profiles at both sizes, exact output checks, environment/admission/identity
records, raw compressed output, privacy-limited kernel activity, collection and
independent reader scripts. It establishes the validation cost before selecting fusion.
Fresh precise PTX was checked inside the control executable before profiling.

`observations.tar.xz` contains all 50 final regression/warm-up/measured records,
four ordinary-binary full-motion profiles, source/binary/PTX/input identities,
commands/exits/timeouts, monotonic child and collector clocks, summaries and inputs.
One warm-up pair and five alternating measured pairs were retained per primary
workload, alongside seven regression pairs. Source freezes were rechecked afterwards.
No failed, warning or slow result was silently replaced.

`measurements/activity.sqlite` retains only kernel/API names, times, correlation IDs
and copy sizes/directions. Stage labels are inferred from the source-owned submission
sequence, checked against kernel type/count and API correlation, rather than claiming
that profiler names distinguish each numerical branch. The reader reconstructs every
iteration, early/late intervals, launch counts, explicit waits and the complete host
copy schedule. Native Nsight reports/SQLite, binaries and frozen sources remain in
`/tmp/maelstrom-active-20261027` on the PC.

Completed-step clocks include preparation, validation, transfers, submission,
completion, cancellation and acceptance. Construction, teardown, output/storage and
physical audits are separate. Child `wall_s` ends before storage; `collector_wall_s`
includes it. GPU intervals exclude host gaps and come from separate profiled runs,
not the five primary samples. Hardware clocks and CPU affinity were not locked, nor
was exclusive-machine isolation qualified. A brief pre-change evidence-reader run
overlapped primary collection; no causal claim is made about its effect.

`verification.tar.xz` retains qualification commands/logs, collection and reader
scripts, resource probes, platform/build-environment observations, local CPU feature
isolation, and the independent retained-control test overlay. The overlay changes
only the test declaration and adds the same new test file. Its 189 source hashes and
the original CUDA equations are checked by `archive-readback.json`. Both fixtures
pass the retained implementation as well as the candidate. One initially incorrect
new three-particle fixture referenced itself; its raw failure, minimal correction
and successful rerun remain in the preliminary records. No production code changed
for that correction. Preliminary runs are not pooled into final timings.

Compute Sanitizer exited 97 with sixteen WDDM debugger/device-support errors,
although the two selected functional tests completed. This is no device-memory
pass; racecheck was not run. Other-device/compiler/block-size performance,
actual device loss, worst-case cancellation latency and independent fluid quality
remain unqualified.

`files-sha256.json` indexes all 370 uncompressed members. `SHA256SUMS` covers the
archives, manifests/deltas, readers' results, protocol and integrity receipts. Both
independent audits were rerun after archive extraction and reproduced their results.

From the EPQ root, these commands inspect saved evidence without running simulations:

```sh
cd docs/project/development/milestones/05/assets/active-distance-v1
sha256sum -c SHA256SUMS
active_evidence=$(mktemp -d)
tar -xJf observations.tar.xz -C "$active_evidence"
tar -xJf initial-profile.tar.xz -C "$active_evidence"
tar -xJf verification.tar.xz -C "$active_evidence"
cp control-source.json candidate-source.json "$active_evidence/"
python3 "$active_evidence/audit.py" "$active_evidence/measurements"
python3 "$active_evidence/initial-audit.py" "$active_evidence"
```

To reconstruct source without changing a checkout, export the named Maelstrom base
commit into a new empty directory, apply `control.patch` there, and verify every
`control-source.json` hash before applying `candidate.patch` and verifying its manifest.
Separate complete source copies and `CARGO_TARGET_DIR`s are necessary for the collectors.
`verify.py`, `reference-tests.py`, `initial.py`, `measure.py` and `postcheck.py` show exact
commands and environment. Their absolute scratch root and deliberately exclusive output
paths must be changed together for a fresh collection; existing result directories
must not be reused. Initial profiling precedes candidate measurement, and device probes
and sanitiser checks follow timed collection. The copied large scene/defaults are in
`inputs/`; bundled small scenes are bound by the control manifest. The primary
collector performs its own identity and resource admission checks before starting.
