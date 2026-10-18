# CUDA integration verification

This collection records local CPU checks and the optional CUDA boundary verified through `ssh pc`
on 18 October 2026. It qualifies a layout/launch probe and resource ownership, without implementing
the fluid solver or making a performance claim. The
[implementation record](/docs/project/development/milestones/03/phases/phase-00-cuda-integration.md)
explains the decision and limits.

| File | Evidence |
| --- | --- |
| [source-manifest.json](/docs/project/development/milestones/03/assets/integration-v1/source-manifest.json) | Full base commits and SHA-256 hashes for all 91 Maelstrom files, independently matched to the PC source copy |
| [pc-checks.json](/docs/project/development/milestones/03/assets/integration-v1/pc-checks.json) | Exact commands, relevant environment overrides, expected/observed exits, stdout and stderr for hardware, tests, tools, rejection paths and diagnostics |
| [local-checks.json](/docs/project/development/milestones/03/assets/integration-v1/local-checks.json) | CPU-only build, focused tests, formatting/Clippy, missing toolkit/driver rejection and CPU discovery/simulation without a driver |
| [hardware-roundtrip.json](/docs/project/development/milestones/03/assets/integration-v1/hardware-roundtrip.json) | Standalone release application report: device 0, 257 records, eight independent resource lifetimes |

The PC used an isolated temporary copy of the current source. Cargo dependencies were already
cached; all Cargo commands used the unchanged lockfile and offline mode. CPU-only operation was
also built locally without a toolkit, with invalid `CUDA_HOME`, target, `CXX` and `AR` values proving
that disabled CUDA does not invoke native tooling. The earlier complete local debug regression passed
196 integration tests, nine unit tests and two doctests; final focused CPU reruns are retained here.

The PC release suite explicitly included the hardware test: 196 integration tests, ten unit tests
and two doctests passed, with no ignored tests. Debug checks cover the ten unit tests and two CUDA
integration tests. Strict all-feature/all-target Clippy and Rustdoc also passed on the PC. The native
ASan/UBSan test executable uses private injected driver functions and does not need a GPU; its results
are distinct from the actual hardware round trips and real request rejections.

Expected nonzero exits are intentional negative evidence: missing toolkit 101, unavailable or
incompatible runtime requests 3. `sanitizer` exited 90 because its WDDM debugger interface could not
initialise; neither the target application's success report nor the tool's leak summary makes that
a passing diagnostic. `incomplete-driver` used a temporary library exporting only `cuInit`, to check
missing-symbol reporting. `incompatible-target` compiled compute_90 for the actual capability-8.9
device, then `restore-target` restored compute_89. No system configuration was changed.

The PC records include compiler/device details, binary and embedded PTX hashes. Source hashes identify
the uncommitted assessed files, not a commit or archived source snapshot. No repository, binary,
build tree or toolkit is copied into these assets. Commands containing `/tmp/maelstrom-cuda-*` name
the disposable verification directory, not a required installation path. Reproduction commands and
prerequisites are in the working-tree [CUDA guide](/Maelstrom/docs/cuda.md).
