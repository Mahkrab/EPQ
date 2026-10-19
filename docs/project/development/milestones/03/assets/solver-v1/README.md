# CUDA solver qualification

This collection records numerical and workflow qualification on 18 October 2026 through `ssh pc`.
It supports the [implementation record](/docs/project/development/milestones/03/phases/phase-01-cuda-solver.md)
and local G01 decision. It contains no warm-up campaign, primary performance summary or speedup ratio.

The assessed source is an uncommitted working tree based on Maelstrom
`facf789e349a3dbbc42126504e150befe67cb519`. All 99 source, fixture, test and documentation hashes
were matched independently to the PC copy and the final local tree. EPQ began at
`c32bcfb9b59560f9dd49d5516295dc18fb9fed10`. Neither repository was committed, tagged or published;
the parent gitlink was not advanced. Source hashes identify tested bytes without creating a checkpoint.

| Evidence | Responsibility |
| --- | --- |
| [source-manifest.json](/docs/project/development/milestones/03/assets/solver-v1/source-manifest.json) | Full base commit, exact simulator file hashes and device compiler flags |
| [pc-checks.json](/docs/project/development/milestones/03/assets/solver-v1/pc-checks.json) | Commands, environment overrides, exits, stdout/stderr, binary/PTX hashes and hardware/toolchain checks |
| [local-checks.json](/docs/project/development/milestones/03/assets/solver-v1/local-checks.json) | CPU regression, final focused checks, formatting, strict Clippy and optional-build rejection boundaries |
| [parent-checks.json](/docs/project/development/milestones/03/assets/solver-v1/parent-checks.json) | Parent comparison/collector and existing baseline-tool regression checks |
| [qualification.json](/docs/project/development/milestones/03/assets/solver-v1/qualification/qualification.json) | Exact requests, all 86 raw-result filenames/hashes and 80 comparison-report filenames |
| [audit.json](/docs/project/development/milestones/03/assets/solver-v1/audit.json) | Independent local hash, source and complete physical-document checks for every comparison |
| [extra checks](/docs/project/development/milestones/03/assets/solver-v1/extra/checks.json) | Compiler/environment details, actual SIGINT cancellation, fresh CPU-prefix control and reproduced rejected arithmetic controls |
| [rejected observations](/docs/project/development/milestones/03/assets/solver-v1/rejected/README.md) | Original exploratory disagreements and their provenance limits |
| [integrity.json](/docs/project/development/milestones/03/assets/solver-v1/integrity.json) | Retained-file hashes and current parent verification-tool identities |

## Environment and verification

The PC used an RTX 4070 with 12,282 MiB visible memory, capability 8.9, Windows driver 610.88,
driver API 13030, CUDA 13.3.73, Rust/Cargo 1.96.0, GCC/G++ 13.3.0 and glibc 2.39 under WSL2.
The virtual target was compute_89. Device flags were `--ptx --std=c++17 -O3 --fmad=false
--ftz=false --prec-div=true --prec-sqrt=true`; the native bridge used C++17, `-O2 -fPIC
-Wall -Wextra -Werror`. No Cargo dependency or lockfile changed. The narrow vendored power
adaptation and its MIT licence are part of the assessed source. No driver/toolkit was installed.

The complete feature-enabled release suite passed 219 tests: 14 library tests, 203 integration
tests and two doctests, with hardware cases explicitly included and no ignored tests. The debug
device suite passed 23 tests. Strict feature-enabled all-target Clippy, Rustdoc, and native ASan/UBSan
injected-failure checks passed. Local CPU verification includes an earlier full 208-test regression
and final 54-test CLI/workflow/device-selection checks, strict Clippy, formatting and a release build
with deliberately invalid CUDA, target, C++ compiler and archive settings. Local checkout paths in
these logs are explicitly redacted. The parent suite passed 35 tests, including nine new tests.

Kernel/stage tests cover explicit membership rows, all adjacent cells at positive/negative boundaries,
strict support, coincidence, dense/sparse occupancy, subnormal and extreme coordinates, uneven blocks,
independent equations, fractional pressure exponents, immutable membership, order-sensitive reductions,
every cancellation poll, repeated rollback, error precedence and independent resource lifetimes.
The complete 480-step component trace checks densities, constraints, multipliers, corrections and
projection against CPU stages. Deliberately incorrect equations, ordering and membership controls
demonstrate that the fixtures can expose defects.

## Retained numerical matrix

| Particles | Steps | Checkpoints | Fresh CPU controls | CUDA requests |
| ---: | ---: | --- | --- | --- |
| 27 | 12 | 0, 1, 4, 12 | Brute force, serial grid, four-worker grid; frozen golden | 32/64/128/256 lanes, ordinary/total/profile, two repetitions; ordinary public replays |
| 64 | 480 | 0, 1, 120, 240, 480 | Brute force, serial grid, four-worker grid; frozen golden | Same launch/instrumentation/repetition matrix and public replays |
| 216, 512, 1,000, 1,728, 4,096, 8,000 | 480 each | 0, 1, 120, 240, 480 | Serial grid and four-worker grid at each size | 128 lanes, ordinary execution and public replay at each size |

All 80 comparisons passed exact binary32 checks, including signed zero, over **1,776,150 particle
position/velocity components**, every required audit, CFL value, warning, structural field and status.
The parallel budgets in `reference-comparison-v1` were not needed for accepted results. Records keep
full arrays, and reports retain counts, maxima, RMS errors, worst identities/axes, expected/actual
values and limits. Gzip files preserve original complete JSON output; their compressed and decompressed
hashes are indexed. Compact hashes alone did not establish tolerance acceptance.

The collection used the files identified in
[collection-tools.json](/docs/project/development/milestones/03/assets/solver-v1/collection-tools.json).
After copying the results locally, the current comparison tool re-evaluated every report and added
its optional first-divergent-step field. An independent pass through the established serial exact
comparator checked every physical value, removing only declared execution/build context. The audit
also matched all raw hashes, binary identity, source hashes and the complete current source path set.

Real SIGINT cancellation of a long GPU request exited 130 with 189 accepted steps. The complete
accepted snapshot and diagnostic prefix matched a fresh serial-grid run of exactly 189 steps.
Native injected failures are separate evidence from this actual hardware cancellation.

## Failures and limits

Compute Sanitizer memcheck and racecheck each exited 90: the WDDM debugger interface could not
initialise and the diagnostic reported an unsupported device. Successful application output within
those attempted runs does not make either tool a pass. No system configuration was changed to enable
the debugger. Native sanitizers and injected driver functions do not establish recovery from actual
hardware loss; uncertain device errors invalidate the resource.

Both rejected power operations were reproduced against the final solver using separately hashed
controlled source variants. Their full original outputs, source manifests, binary hashes and reports
are in `extra/`. Native CUDA `powf` failed from checkpoint 120; binary64 library power failed at
checkpoint 480. Neither is a supported CUDA arithmetic implementation. Original exploratory outputs
are also retained, with their incomplete historical-source provenance disclosed.

Exact agreement is qualified for this hardware, compiler/libm combination, workload and tested settings.
The larger-family runs used 128 lanes; the complete launch/repetition matrix applies to the goldens.
Membership storage is quadratic and no maximum feasible input size was established. Real device-loss
recovery, other GPUs/platforms, hosted checks and performance comparison remain unverified.

Reproduction uses the optional Cargo build and hardware-test commands in the assessed CUDA guide,
then, from EPQ with the same simulator tree and populated Cargo cache:

```sh
python3 -m tools.cuda.qualify Maelstrom/target/release/maelstrom Maelstrom \
  docs/project/development/milestones/03/assets/solver-v1/source-manifest.json NEW_DIRECTORY
python3 -m tools.cuda.compare \
  NEW_DIRECTORY/00064-serial-grid.json.gz NEW_DIRECTORY/00064-cuda-128-ordinary-1.json.gz --exact
```

Use the primary PC for this collection. These commands produce correctness evidence; they do not
implement the separate controlled performance protocol.
