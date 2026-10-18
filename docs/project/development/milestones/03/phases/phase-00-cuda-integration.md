# Phase 0 CUDA integration and resource ownership

## Starting point

Work began from clean EPQ `7cd384ea4542906ad123b41f56a0db3cbcb73a06` and Maelstrom
[`60b9a767636428a26f39a1901e2cac4276c75c83`](https://github.com/Mahkrab/Maelstrom/tree/60b9a767636428a26f39a1901e2cac4276c75c83).
These are the existing `milestone-03/phase-00/start` checkpoints; `milestone-03/start` predates
the parent planning commit. The
[historical CUDA smoke test](/docs/project/infastructure/CUDA/README.md) had not established
application integration, optional builds or ownership across failures.

## Scope and outcome

Cargo now builds an optional Rust/CUDA C++ boundary. The library owns device resources through
`cuda::CudaContext`; `maelstrom cuda-check --device 0` runs and independently verifies a small
device transformation through that public boundary. CPU simulation, selection, defaults, records
and replay retain their existing behaviour. No GPU fluid solver or performance comparison was added.

The assessed implementation is an **uncommitted working tree** based on the full Maelstrom commit
above. The [source manifest](/docs/project/development/milestones/03/assets/integration-v1/source-manifest.json)
identifies all 91 assessed files, matched byte for byte to the isolated PC checkout. These hashes
identify reviewed content; they do not create a historical checkpoint. The
[build and ownership guide](/Maelstrom/docs/cuda.md) is a working-tree guide until separately committed.

## Decisions and implementation

### Optional compilation and explicit ownership

The Rust-host/CUDA C++ design was retained. Instead of the standalone test's Runtime API, the
bridge uses the Driver API to give each handle its own context, module and non-blocking stream.
NVIDIA documents context creation, thread binding and destruction of associated resources;
this informed the ownership choice.<sup><a href="#ref-s053">S053</a></sup> Independent handles can
be interleaved without resetting a shared primary context. Rust prevents moving or sharing a live
CUDA handle across threads, and native calls restore the caller's prior context.

Cargo invokes the installed nvcc to compile embedded PTX, then the host C++ compiler and archiver
to build a small bridge. The system driver is loaded at runtime. This keeps native compilation
within Cargo while allowing a CUDA-enabled binary to report a missing driver and still run CPU
commands. There are no new Cargo dependencies. The trade-off is a deliberately limited first
support target: native x86_64 Linux/WSL, CUDA 13-compatible interfaces and a driver able to load the
emitted PTX. The guide records prerequisites, environment overrides, target and every compiler flag.

CPU-only builds return before inspecting toolkit/compiler settings. Explicit CUDA requests never
fall back to CPU work. Invalid build settings, unavailable devices, missing driver symbols and
incompatible device capability produce actionable errors.

### Transfer and failure boundaries

The probe has an explicit 24-byte C layout, independently asserted in Rust and CUDA/C++, with exact
u64 identity, three binary32 coordinates and a marker. Counts, byte arithmetic and device indices
are bounded; empty input performs no device work. The launch uses 128 lanes per block and checks
the final partial block. Synchronous copies avoid outstanding borrows of Rust host storage.

Output becomes visible only after upload, submission, stream completion, download and release
succeed. Typed errors retain operation and native status, distinguishing submission from completion.
Allocation exhaustion permits retry. Other driver failures invalidate the handle; uncertain device
storage remains owned until context destruction. `close` reports teardown errors and consumes the
handle; `Drop` attempts cleanup without claiming recovery from hardware loss.

## Verification

All checks ran on 18 October 2026. The primary PC was rechecked through `ssh pc`: Ubuntu 24.04.5,
WSL kernel 6.6.87.2, RTX 4070 with 12,282 MiB reported memory and capability 8.9, driver 610.88,
nvcc 13.3.73, C++ compiler 13.3.0 and Rust/Cargo 1.96.0. `nvcc` was absent from the SSH command PATH;
explicit toolkit discovery through `/usr/local/cuda` worked without system changes.

The [retained evidence](/docs/project/development/milestones/03/assets/integration-v1/README.md)
separates these results:

- Local CPU debug regression passed 196 integration tests, nine unit tests and two doctests with
  Rust/Cargo 1.98.1. Final focused CPU checks passed with deliberately unusable CUDA/compiler settings;
  an explicit CUDA build rejected a missing toolkit.
- On the PC, the complete CUDA-enabled release suite passed **208 checks**, including the explicitly
  selected hardware test, existing goldens, CPU controls and replay. Debug boundary checks passed too.
  Formatting, strict Clippy and warning-free Rustdoc passed in the applicable environments.
- Actual hardware covered empty/single inputs, block boundaries through 1,025 records, signed zero,
  exact identities/markers, immutable input, repeated calls and independent explicit/implicit lifetimes.
  The release application independently verified 257 records over eight complete resource lifetimes.
  Hidden devices, invalid ordinals, missing driver symbols and a deliberately incompatible target
  were rejected. The enabled binary reported a missing driver locally while CPU discovery and threaded
  simulation worked.
- Separate native injections covered partial construction, context binding, allocation retry, upload,
  launch, completion, download, release, invalidation and teardown under AddressSanitizer/UBSan.
  These are host ownership checks, not observed device failures.

## Limitations and Gate G00

**G00 is satisfied for the tested working tree and hardware.** Compute Sanitizer failed to initialise
the WDDM debugger interface and exited 90; its apparent leak summary is not usable diagnostic evidence.
No driver or Windows configuration was changed. Actual device loss, driver exhaustion and teardown
failure were not induced. Other devices, toolkits and platforms remain unqualified. There is no
fluid arithmetic or speedup claim.

No commit, tag, branch, push or gitlink mutation was authorised or performed. The existing start
tags remain in place; intended `milestone-03/phase-00/complete` tags remain uncreated in both histories.
The parent still points to the inherited Maelstrom commit. Durable checkpointing and hosted
verification remain separate actions.

## References used

- <a name="ref-s053"></a> **S053 — NVIDIA (2026).** *CUDA Driver API*, CUDA Toolkit v13.3.0.
  [Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).
