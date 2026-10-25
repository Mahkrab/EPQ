# Neighbour attribution evidence

Primary-PC diagnostic collection on 25 October 2026. The
[decision record](/docs/project/development/milestones/05/performance-neighbour-attribution.md) owns the
interpretation. No production solver change, historical checkpoint or hosted check is claimed.

- `8000/` and `110592/` contain one warm-up and one full 480-step trace per variant.
  `analysis.json` records device intervals in early, middle and evolved windows.
- `control-source.json`, `split-source.json` and `exported-identity.json` identify the
  exported working source. Only three native files differ in the diagnostic export.
- `split/hardware-tests/` contains the explicitly enabled 18-test CUDA run. The earlier
  `split/tests/` run left hardware tests ignored and does not qualify them.
- `codegen-complete/` contains precise-flag PTX, disassembly, line-annotated disassembly,
  resource reports and their commands. The cubin stays on the PC; its original hash is recorded.
- `earlier-failures/` and `codegen/sass/` preserve the bridge-build and disassembler-option
  failures. `verification.json` records source rechecking and environment-command exits.
- `environment/` and `telemetry/` retain toolchain/device context and machine readings
  outside application timers. No new hardware-counter qualification is implied.

The collector is `tools.performance.neighbour_attribution`. Its `instrument` operation
is for a disposable export only; `collect` builds and compares separate control/split trees.
The split adds dry traversal and sorting launches, not a production speedup. Physical results
and diagnostic order agree exactly at both sizes, with existing large-run warnings retained.

Large solver JSON, PTX and sanitised SQLite files use lossless `.gz` compression. Restore
a SQLite file to a temporary location before querying it. Process stdout retains its existing
gzip encoding. `privacy.json` records original/derived identities and path/metadata redaction;
original native reports and raw outputs remain on the PC. Executables, source trees and caches
are excluded. `files.json` hashes the shareable evidence.

The separate test-side `audit_neighbour_attribution.audit` checks stage durations directly
against raw timestamps using independently inspected launch slots. Its result is in
`independent-audit.json`.
