# Application lifecycle verification

This dataset assesses the non-visual controller and its separation from numerical execution.
It contains local correctness/build evidence, not graphics qualification or performance measurements.

The final CPU-only release suite passed **223 checks**: 13 library unit tests, 208 integration tests
and two doctests. Fifteen checks cover the new application boundary. Formatting, strict Clippy and
warning-free Rustdoc also passed. Documentation was parsed locally with table support, and internal
links/anchors resolved; this does not establish browser or hosted rendering.

- [Source manifest](/docs/project/development/milestones/04/assets/lifecycle-v1/source-manifest.json)
  names the Maelstrom base commit and SHA-256 of each assessed working-tree file. Sources, tests,
  fixtures and guides are hashed; no checkout or build output is copied into the evidence.
- [Final checks](/docs/project/development/milestones/04/assets/lifecycle-v1/checks.json) record commands,
  exits, environment and transcript filenames. The CPU-only release suite clears display variables and
  supplies unusable CUDA/compiler settings. These settings must not be discovered by a CPU build.
- [Initial debug transcript](/docs/project/development/milestones/04/assets/lifecycle-v1/initial-debug.txt)
  retains the earlier full regression. Final admission synchronisation, a stronger late-failure case
  and the independent motion test were checked subsequently in the manifest tree.

The tests use acknowledgements and barriers for ordering, independently retained old observations,
deliberately absent consumers and bounded queues held before dispatch. Timeouts detect a stranded
test; they do not drive numerical work or prove a shutdown deadline. Exact comparisons include
particle identities and all six binary32 components, including signed zero. A separate hand-calculated
single-particle trajectory checks exact numerical work without a second solver as its oracle.

Construction failures, a numerical overflow after an accepted step, cancellation, queued restart,
worker unwinding and teardown retain their own outcomes. An initial strict-Clippy needless-borrow
failure was corrected before final verification. Primary-PC SSH attempts both timed out with exit
255; fresh CUDA worker hardware checks were not run. CUDA selection is explicitly rejected in the
tested CPU-only build. No surface, adapter, offscreen rendering or encoder was qualified.

The [phase record](/docs/project/development/milestones/04/phases/phase-00-application-lifecycle.md)
owns the gate judgement; the [application contract](/docs/project/development/milestones/04/application-contract.md)
owns behaviour and the intended frame/export workflow. Hashes identify an assessed working tree,
not a durable completion checkpoint. Publication and checkpointing remain separate actions.
