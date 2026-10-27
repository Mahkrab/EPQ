# Numerical-iteration evidence

This supports the [assessment](/docs/project/development/milestones/05/performance-numerical-iterations.md)
and [prospective final protocol](/docs/project/development/milestones/05/assets/numerical-iterations-v1/protocol.md).
Every benchmark request starts a new simulation on the primary PC. No stored observations
are treated as resumed state. Explorations, the earlier coefficient-only campaign and the
final guarded-power campaign remain separate.

## Source and numerical equivalence

`control-source.json` exactly matches the 186-file retained
[neighbour-construction candidate](/docs/project/development/milestones/05/assets/neighbour-construction-v1/README.md).
Reconstruct that export through its documented predecessors, then apply `candidate.patch`
with `patch -p1` to obtain the 187-file final source. Only `native/power.cuh`, `docs/cuda.md`
and the added `native/power_exhaustive.cu` differ. All final live hashes match. These are
uncommitted exports based on Maelstrom `87145510a9e5d812066138c35f1fac82e4f593b0`, not new
Git checkpoints. Ordinary PC checkouts and installed commands were left alone.

The original power approximation is unchanged except for its function name. The wrapper
uses a guarded quartic only at exponent exactly four. `power-qualification/` contains the
reference-prefix check, precise compilation command, binary hash and exhaustive results
at block sizes 32/64/128/256. Each compares all 2,147,483,648 non-negative binary32 words
with zero bit mismatches. The unguarded quartic differs on 354,191 normal-output inputs,
showing why fallback matters. The guard accepts 529,216,975 words in that enumeration;
that number is not a simulation call-rate measurement. Other exponents and excluded
inputs call the retained function. Neither convergence nor a numerical tolerance changed.

## Final observations

`observations.tar.xz` holds all 50 regression/warm-up/sample records, four separate full
480-step profiles, source/input/binary/embedded-PTX identities, environment/resource
admission, commands/exits, original compressed outputs, summaries and custom capacity
inputs. Fresh PTX bytes were found in each corresponding executable before collection;
source freezes were checked again afterwards. No sample was replaced.

Primary totals sum completed-step clocks, including validation, transfers, launches,
completion, cancellation and acceptance. Construction/teardown, audits, output and
collector compression are separate. `wall_s` ends before compression; `collector_wall_s`
includes storage. The separate profiles use ordinary binaries without checkpoints.
GPU stage intervals sum kernel activity, exclude host gaps and do not replace primary
sample medians. Density/lambda is one kernel. Per-iteration and early/late timings remain
in `independent-audit.json`.

`measurements/activity.sqlite` contains only variant, particle count, API/kernel name,
start/end time, correlation ID and copy byte count/direction. Addresses and private
profiler metadata are excluded; original native reports remain on the PC. The reader
correlates device activity with host APIs, validates each transfer against the source
schedule and checks every kernel's order/type, launches and explicit waits.

`verification.tar.xz` holds ordinary/explicit CUDA qualification, strict Clippy, formatting,
control/candidate native ASan/UBSan, local CPU feature isolation, exhaustive power checks,
loaded-function resources, platform observations and collection/audit scripts. Local CPU
exit/output are recorded; its complete child duration was not. Compute Sanitizer exited
97 with eight WDDM debugger/device-support errors despite the selected correction test
completing. This is **not a device-memory diagnostic pass**; racecheck was not run.

## Investigation and negative outcomes

`investigation.tar.xz` preserves the initial individual-kernel/eight-iteration profiles,
eleven separate two-pair exploratory cohorts (**132 records**), the earlier complete
coefficient-only campaign (**50 records plus profiles**), failed guard qualifications,
source manifests, focused patches, fresh post-collection exploratory PTX/binary binding,
commands, raw compressed results and summaries. The main final comparison uses independent
pre-collection identity guards. The integer-guard exploration's PTX equals final PTX after
helper renaming; its recorded binary identity refers to the final equivalent executable.

The initial profile's legacy `apply`, `planes`, `project` labels mean mass validation,
candidate formation and plane projection. Its command `wall_s` includes output compression
and is not used as a primary solver duration. Numerical figures use actual GPU intervals.
The row-validation exploration's control warm-up briefly overlapped a CPU audit; the audit
was suspended before its measured pairs and resumed afterwards. It supplies no final gain
claim. Original observations remain unchanged.

The coefficient campaign retains its original reader and a portable reader whose only
adaptation resolves earlier exploratory runs from their archived variant directories.
`portable-reader.json` records that change and exact reproduction of the original audit.
The discarded tighter floating guards retain non-zero mismatch counts and exit 2; they
are failed candidates, not tolerated differences. Source patches reconstruct each
exploration from the common retained control. Executables, whole source trees, PTX,
private reports and build caches are excluded.

## Readback

`files-sha256.json` indexes every uncompressed member across the three archives;
`investigation-files.json` is its investigation subset. `SHA256SUMS` covers archives,
protocol, manifests, patch, audit and reconstruction/readback receipts.

From the EPQ root, these commands inspect evidence without running a simulation:

```sh
cd docs/project/development/milestones/05/assets/numerical-iterations-v1
sha256sum -c SHA256SUMS
numerical_evidence=$(mktemp -d)
tar -xJf observations.tar.xz -C "$numerical_evidence"
tar -xJf verification.tar.xz -C "$numerical_evidence"
tar -xJf investigation.tar.xz -C "$numerical_evidence"
python3 "$numerical_evidence/audit.py" "$numerical_evidence/measurements"
python3 "$numerical_evidence/investigation/coefficient-campaign/audit.py" \
  "$numerical_evidence/investigation/coefficient-campaign/measurements"
```

The final reader reconstructs all original output hashes, complete workloads, exact
canonical physical/diagnostic agreement, timing medians/ranges/pairs, profiled physical
agreement, individual stages/iterations and source-owned copy/launch/wait counts.
The collection script separately reads and compares every exploratory cohort. Checks
on one device do not establish other-GPU performance, device-loss recovery, worst-case
cancellation latency, statistical significance or independent fluid quality.
