# Stream synchronisation evidence

This supports the [assessment](/docs/project/development/milestones/05/performance-stream-synchronisation.md).
The [protocol](/docs/project/development/milestones/05/assets/stream-synchronisation-v1/protocol.md)
was fixed before collecting timing samples on the primary PC. All requests start new
simulations; no saved observation is used as resumed solver state.

The control matches every file in the earlier
[resident-state export](/docs/project/development/milestones/05/assets/resident-state-v1/README.md).
Reconstruct that candidate from its documented base and patches, then apply this directory's
`candidate.patch`. The two source manifests identify all 182 files independently; these are
uncommitted source exports, not new Git checkpoints. The measured PTX was identical between
variants and found inside each executable. Ordinary PC checkouts and installed binaries were
left alone.

`observations.tar.xz` contains the 50 complete regression/warm-up/sample process outputs,
commands, monotonic elapsed times, output hashes, source/binary/PTX/input identities,
environment, summary and separate trace observations. `measurements/activity.sqlite`
retains API names/times/correlations and device activity times/correlations only; private profiler
metadata and original native reports remain on the PC. Kernel/transfer counts can be
reconstructed from those rows without trusting the summary. Instrumented times are separate
from primary samples.

`verification.tar.xz` contains qualification commands/logs, local CPU results, the original
ambient-environment suite failure and its baseline reproduction, the trace-reader schema
failure, collection/readback scripts, mutation-check result and independent audit. The expected
mutation failure demonstrates that the native test rejects missing host-access completion.
There was no failed physical comparison or substituted timing sample. Raw failures are preserved;
no successful device-memory sanitiser or actual device-loss recovery check is implied.

`files-sha256.json` indexes uncompressed archive members. `SHA256SUMS` covers the archives,
source delta, manifests, protocol, audit and reconstruction receipts. No whole source trees,
binaries or build caches are retained here.

From the EPQ root, verify and inspect without running a simulation:

```sh
cd docs/project/development/milestones/05/assets/stream-synchronisation-v1
sha256sum -c SHA256SUMS
stream_evidence=$(mktemp -d)
tar -xJf observations.tar.xz -C "$stream_evidence"
tar -xJf verification.tar.xz -C "$stream_evidence"
python3 "$stream_evidence/audit.py" "$stream_evidence/measurements"
```

The independent audit checks original output hashes and exact canonical physical records,
recomputes medians and paired changes, then reconstructs trace totals and per-step waits.
