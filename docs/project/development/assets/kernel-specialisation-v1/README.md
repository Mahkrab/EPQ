# CUDA kernel specialisation evidence

Two separately assessed primary-PC campaigns, collected on 25 October 2026.
The [development record](/docs/project/development/milestones/05/performance-kernel-specialisation.md)
owns the interpretation and decision. Neither candidate is retained in the production solver.

## Campaigns

- `full/` specialises all thirteen operations. It includes the original protocol,
  source/executable identities, function resources, tests, seven-size regression,
  five alternating timing pairs at each size and full 110,592-particle traces.
- `full/small-timelines/` is the separately declared diagnostic extension. It isolates
  the 8,000-particle fill/sort regression without replacing primary timing samples.
  `followup-reader-recovery.json` distinguishes reader/setup errors from solver results.
- `targeted/` retains shared search and specialises numerical passes. It has its own
  source identity, fresh samples, qualification and traces. The control executable is
  byte-identical to the first campaign; the two sets of samples were not pooled.
- `assessment.json` records the written engineering decisions. Lower register counts,
  a favourable small median or a fixed percentage do not independently decide retention.

Each primary campaign uses device 0, 128 lanes, 480 steps, refinement 4 and eight iterations.
The 8,000-particle case retains checkpoints 0/1/120/240/480. The 110,592-particle case omits
checkpoint audits and retains its known CFL warnings. Solver totals, constructor/teardown
and invocation boundaries are recorded separately. Diagnostic traces are not primary samples.

## Reconstructing the candidates

`full-candidate.patch` and `targeted-candidate.patch` apply independently to Maelstrom
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5).
Use a disposable export of that commit and apply one patch. `patch-verification.json`
confirms that each reconstruction matches all 155 assessed source-file hashes. These
patches are reproducible trial proposals, not completion commits or tags. The unrelated
custom scene was excluded from both exports and preserved in the working checkout.

The collector is `tools.performance.kernel_specialisation`; the second campaign uses its
explicit `--shared-search` option. The resource probe queries functions in a separate owned
driver context. Its register/local/shared figures are not achieved-occupancy measurements.
The test-side `audit_kernel_specialisation.audit` checks physical JSON, timing totals,
medians, raw kernel identities and component durations without the collector's report functions.
Both campaigns include their independent audit result.

## Retention and limits

Large solver JSON and sanitised SQLite use lossless `.gz` compression. Restore a SQLite
file to a temporary location before querying it. Process stdout keeps its original gzip
representation. `privacy.json` records original/derived hashes and metadata/path redaction;
analytical SQLite rows are unchanged. Raw originals and native profiler reports remain on
the PC. Source trees, executables, caches, PTX and cubins are excluded from this directory.
`files.json` hashes the complete shareable record.

Both candidates passed explicit CUDA hardware and native injected-failure checks; actual
device-loss recovery, device-memory sanitiser qualification and other platforms were not
tested. The EPQ starting checkpoint passed its hosted Markdown workflow. Candidate checks
here are PC/local evidence and were not run by GitHub Actions. The published solver and
previous graphics/playback repairs remain active.
