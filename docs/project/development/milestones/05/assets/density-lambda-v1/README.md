# Density/lambda evidence

This supports the [assessment](/docs/project/development/milestones/05/performance-density-lambda.md)
and [prospective protocol](/docs/project/development/milestones/05/assets/density-lambda-v1/protocol.md).
Every request starts a new simulation on the primary PC. Attribution, exploratory pairs
and final primary samples are distinct collections; none is pooled with earlier results.

`control-source.json` matches the complete 187-file Git archive of Maelstrom
`1e0085926d05c42949bb76b55d177d42a1f8f94f`, which matches the retained
[guarded-power candidate](/docs/project/development/milestones/05/assets/numerical-iterations-v1/README.md).
The starting EPQ commit is `1f76097a218266822cdf344c38db75ed128628a8`; both trees were clean.
Apply `candidate.patch` to that simulator source with `patch -p1` to reconstruct all 188
final hashes. Only the numerical CUDA source, CUDA documentation, test declaration and
added `src/cuda/density_tests.rs` change. The final live tree matches the frozen candidate.
No ordinary PC checkout, installed executable, Git history, branch, tag or gitlink changed.

`observations.tar.xz` retains all 50 final regression/warm-up/sample records, four
ordinary-binary full-motion profiles, environment/resource admission, commands/exits,
monotonic child/collector durations, raw compressed output, summaries, input identities
and the capacity scene/defaults. Fresh precise PTX was found inside the corresponding
executable before collection; source hashes were checked again afterwards. Original
results, warnings, slow samples and failures were not replaced.

Primary totals sum completed-step clocks including validation, preparation, transfers,
launches, completion, cancellation and acceptance. Construction/teardown, audits, output
and compression are separate. Child `wall_s` ends before storage; `collector_wall_s`
includes it. Profiled GPU intervals exclude host gaps and are not primary sample medians.
`measurements/activity.sqlite` retains only names/times/correlations and copy sizes/directions,
not addresses or private profiler metadata. Native reports remain on the PC. The reader
checks kernel order/type, every copy against its host API/size schedule, explicit waits,
individual iterations and early/late stage intervals.

`investigation.tar.xz` contains the fresh initial control and three-phase diagnostic
profiles, their eight warm-up/profile records, all twelve exploratory records, source
hashes, diagnostic/trial patches and original collection scripts. The diagnostic export
splits density/constraint, owner/lower-prefix/self-square and higher suffix/final lambda.
It carries private values through existing scratch, selects each row's first error before
the global minimum, and adds sixteen launches per step. Its 45-register requirement
matches control, but scheduling/cache state and launch overhead differ. Split timings
identify relative pass costs, not an isolated DRAM or arithmetic bottleneck or an additive
estimate of the unsplit kernel. No hardware-cache/occupancy counters were collected.

Fresh PTX binding was checked before attribution captures; explicit profile binary/PTX
hashes were recorded afterwards. The untouched exploratory binary was also bound after
collection, and its PTX equals final candidate PTX. The primary final collector separately
checks identities beforehand. The standalone investigation reader reconstructs all split
intervals and exact physical agreement, then reads every exploratory pair without using
the collector's claimed summary.

`verification.tar.xz` contains qualification commands/logs, readers/collectors, resource
probes, platform observation, local CPU feature-isolation output and the retained-control
test overlay. That overlay changes only `src/cuda/solver.rs` to declare the new test module
and adds its file; its CUDA equations remain original. Both new fixtures pass there and
in the fused candidate, comparing independent CPU intermediate bits and expected error
priority. Existing owner/prefix/suffix, cancellation, panic, rollback and retry tests remain.
The local CPU command's complete child duration was not recorded; its exit and per-test
logs are retained.

Compute Sanitizer exited 97 with sixteen WDDM debugger/device-support errors, although
its two selected tests completed. This is no device-memory diagnostic pass; racecheck
was not run. Device-loss recovery, worst-case cancellation latency, other-GPU/compiler
and other-block-size performance remain unqualified.

`files-sha256.json` indexes every uncompressed member. `SHA256SUMS` covers archives,
protocol, source identities/deltas, audit and integrity receipts. There are no whole
source trees, binaries, build caches, PTX or private native profiler reports here.

From the EPQ root, inspect the evidence without running a simulation:

```sh
cd docs/project/development/milestones/05/assets/density-lambda-v1
sha256sum -c SHA256SUMS
density_evidence=$(mktemp -d)
tar -xJf observations.tar.xz -C "$density_evidence"
tar -xJf investigation.tar.xz -C "$density_evidence"
tar -xJf verification.tar.xz -C "$density_evidence"
python3 "$density_evidence/audit.py" "$density_evidence/measurements"
python3 "$density_evidence/investigation-audit.py" "$density_evidence"
```

The final reader validates original hashes, exact particle counts, release/CUDA execution,
complete workloads, physical/diagnostic agreement, medians/ranges/paired changes and
source-owned device activity counts. The investigation reader independently checks its
profiles and pairs. Equivalence and timing gains do not establish independent fluid quality
or statistical significance.
