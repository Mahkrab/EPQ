# Numerical-kernel experiments preserving ten retained optimisations

**Reject both qualified final variants.** The live source preserves all ten retained
optimisations exactly. The independent readback verifies 1,510 archive members
and reconstructs all eight source exports.

The [assessment](/docs/project/development/milestones/05/performance-numerical-kernels.md)
explains instruction analysis, resource limits, exact behaviour and retention decisions.
All measurements use the primary PC through `ssh pc`. Every request starts a new
simulation; this is neither playback nor resumption of a saved state.

The 191-file control exactly matches the tenth retained candidate. Source exports
include existing uncommitted work and reconstruct from Maelstrom
`1e0085926d05c42949bb76b55d177d42a1f8f94f`. EPQ HEAD remains
`1f76097a218266822cdf344c38db75ed128628a8`. No Git history, branch, tag,
remote or parent gitlink changes are part of this work.

## Source identities and experiments

Every patch below applies directly to reconstructed control, except `control.patch`,
which applies to the recorded Maelstrom base. Manifests describe complete source
exports, including tests, inputs and documentation; source exports are not commits.

| Export | Files | Purpose |
|---|---:|---|
| control | 191 | All ten retained optimisations |
| trial-0 | 191 | Explicit radius-coefficient hoisting |
| trial-1 | 191 | Coefficients and deferred invariant first errors |
| trial-2 | 191 | Reuse completed geometry validation in grouped correction |
| trial-3 | 191 | Also reuse geometry validation in the density/lambda suffix |
| trial-4 | 191 | Dedicated validated-correction entry with lower register demand |
| candidate | 192 | Qualified dedicated-entry variant, new fixture, native dispatch checks and documentation |
| validation-only | 192 | Separate qualified follow-up using the general entry and original dispatch |

`protocol.md` is the original prospective protocol. `validation-only-protocol.md`
records the adaptive follow-up before implementation/measurement. It preserves the
first candidate's failed primary campaign; its new samples are not replacements.

Both final campaigns use CUDA 0/block 128, refinement 4, eight iterations and 480
unpaced steps, at 8,000/110,592 particles with/without XSPH 0.01 and confinement 0.1.
Small primary/regression runs request checkpoints 0/1/120/240/480; large runs request
final state and ordered diagnostics. Primary completed-step clocks include checks,
transfers, launches, waits, cancellation and acceptance. Construction, teardown,
checkpoint processing, output and audits remain separate. Each final workload has
one warm-up and five alternating pairs, first measured candidate/control. Exploratory
variants each have one warm-up and two pairs. No samples are pooled or discarded.

## Retained evidence

| File | Contents |
|---|---|
| `observations.tar.xz` | Original campaign: all five exploratory variants, matched first-trial traces, primary warm-ups/samples, seven regression pairs and final traces |
| `verification.tar.xz` | Original release/CUDA/integration/Clippy/fmt/native tests, sanitizers, retained-control fixture and recorded arithmetic rerun |
| `investigation.tar.xz` | Compiler commands, PTX, toolkit cubins and annotated SASS, resource probe, microbenchmark source, scripts, logs, failed counter attempt and setup-failure explanation |
| `inputs.tar.xz` | Counted capacity scene and configuration; bundled scenes reconstruct from source |
| `validation-only.tar.xz` | Separate follow-up protocol, commands, qualification, primary samples, regressions, matched GPU profiles, device diagnostics and independent audit |
| `*-source.json`, `*.patch` | Complete source identities and reconstructible deltas |
| `independent-audit.json` | Original 198 exact trajectories, 286 process hashes, primary statistics, ordered GPU/copy/wait checks |
| `validation-only-audit.json` | Independent follow-up statistics, numerical identity and GPU accounting |
| `resources.json`, `gpu-stages.json`, `microbenchmark.json`, `exploratory-summary.json` | Static/theoretical resources, stage intervals, separate arithmetic-event samples and exploratory pairs |
| `qualification-counts.json`, `post-source-check.json` | Test totals and original post-measurement source receipt |
| `files-sha256.json`, `archive-members.json`, `SHA256SUMS` | Per-member hashes, exact archive counts and root-file identities |
| `archive-readback.json`, `source-reconstruction.json`, `final-verification.json` | Independent archive/source reconstruction and live-tree receipts |

Physical comparisons exclude measurements and build revision only. Requested state,
configuration, signed zero and ordered diagnostics remain in each comparison. Warnings
are preserved; exact agreement does not establish independently qualified fluid quality.
Source and fresh production PTX hashes are checked before and after each campaign;
the expected production PTX is found inside each measured executable.

The arithmetic probe includes the retained functions and cached-factor candidate from
trial-1. After reconstructing that source, compile the archived `factors_probe.cu`
with CUDA 13, C++17, `-O3 --gpu-architecture=sm_89 --fmad=false --ftz=false
--prec-div=true --prec-sqrt=true -I<reconstructed-trial-1>/native`. Its sampled bit/error
test and event timings are diagnostic; it does not reproduce solver traversal,
artificial pressure, neighbour distributions or host work. The initial run has a
complete output but no separately captured process exit. `postcheck/process.json`
records the full rerun's command, exit 0, binary/source/raw hashes and output.

Driver queries load production PTX and call the occupancy API. They establish static
resources and theoretical resident-block limits, not achieved occupancy. Annotated
SASS is toolkit lowering, not a captured production JIT module. Nsight Compute's
fresh `ERR_NVGPUCTRPERM` is retained as failed tool evidence; no privileged setting
was changed. Memcheck and selected race/sync/init checks are independently recorded
functional diagnostic passes.

Full native Nsight reports/databases, executables, Cargo products, mutable export
trees and unrelated machine/process metadata are not distributed. Profile archives
retain the bounded solver API/kernel/copy/memset tables and hashed raw CLI outputs.
Previous task build directories and ordinary caches were reused; installed commands
and system-wide settings were not changed.

## Independent reproduction

From EPQ, using Python 3 and a local Maelstrom repository containing the base commit:

```sh
python3 docs/project/development/milestones/05/assets/numerical-kernels-v1/verify-evidence.py \
  docs/project/development/milestones/05/assets/numerical-kernels-v1 Maelstrom \
  --extract /tmp/numerical-kernel-readback
```

The reader checks every archive member, forbids links/path traversal, checks counts
and hashes, and reconstructs every source export from the named commit and patches.
With `--extract`, it also writes the verified follow-up control/candidate trees
needed for the follow-up reader's final source-hash checks.
The extracted `audit.py` accepts the extraction directory as its argument and
independently recomputes the original campaign's numerical and timing checks.
`followup-audit.py /tmp/numerical-kernel-readback` recomputes the separate
follow-up calculation. No benchmark binary,
mutable worktree or remotely hosted result is assumed by these readers.
