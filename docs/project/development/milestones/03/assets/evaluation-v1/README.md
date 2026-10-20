# CUDA evaluation verification

These checks were run locally on 20 October 2026 to support the
[evaluation record](/docs/project/development/milestones/03/phases/phase-03-evaluation-handoff.md).
They recheck CPU behaviour and retained primary-PC evidence; they are not new GPU tests or timings.
The assessed simulator is unchanged at
`afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b`, already pinned by the parent gitlink.

| Record | Result and responsibility |
| --- | --- |
| [environment.json](/docs/project/development/milestones/03/assets/evaluation-v1/environment.json) | Local WSL2 environment, Rust/Cargo 1.98.1, Python 3.12.3 and starting commit identities |
| [cpu-tests.json](/docs/project/development/milestones/03/assets/evaluation-v1/cpu-tests.json) | 208 CPU-only release Rust tests pass, including two doctests, with locked offline dependencies |
| [parent-tests.json](/docs/project/development/milestones/03/assets/evaluation-v1/parent-tests.json) | Root discovery runs 16 CUDA comparison/qualification/performance tests; baseline and verification directories need separate discovery |
| [baseline-tests.json](/docs/project/development/milestones/03/assets/evaluation-v1/baseline-tests.json) | All 26 baseline/comparison/scaling tests pass |
| [verification-tests.json](/docs/project/development/milestones/03/assets/evaluation-v1/verification-tests.json) | All five component-verification tests pass; total parent coverage is 47 tests |
| [independent-audit.json](/docs/project/development/milestones/03/assets/evaluation-v1/independent-audit.json) | All 105 attempts are clean and exact; three goldens, 21 profiles, 99 current source and nine collector hashes match; physical values, clocks, statistics and ratios are independently rechecked |
| [performance-report.json](/docs/project/development/milestones/03/assets/evaluation-v1/performance-report.json) | Full report succeeds, stored comparative JSON equals recomputation, and stdout matches the retained Markdown byte for byte |
| [source-check.json](/docs/project/development/milestones/03/assets/evaluation-v1/source-check.json) | Each of the 99 solver-manifest entries matches `git show 80cce8a8b8bb604ed988b176298211c6fed491f0:PATH`; each performance-manifest entry matches `git show afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b:PATH`, using SHA-256. The clean simulator, parent gitlink and existing checkpoint targets are recorded |
| [retained-integrity.json](/docs/project/development/milestones/03/assets/evaluation-v1/retained-integrity.json) | All 187 solver assets and 244 performance assets match the original manifests' `files_sha256` entries; original manifests are identified by hash |
| [document-checks.json](/docs/project/development/milestones/03/assets/evaluation-v1/document-checks.json) | Local link/anchor, pinned-source target, heading/fence/table and whitespace checks for the affected documents |

The command records retain exact arguments, process exit, monotonic elapsed duration and stdout/stderr.
Independent local checks may run concurrently; their elapsed times are verification context, not
solver measurements. The source check uses committed bytes, while the independent campaign audit
also checks the complete current simulator path set and hashes. Original collection-time base commits
and dirty-state descriptions remain historical provenance; the matched commits provide the later
durable source identities. Historical project-record hashes are not reinterpreted as current records.

Reproduce the command checks from the EPQ root using the commands in the evaluation record. The
independent auditor requires the assessed simulator and collector bytes. No retained observation,
campaign report, comparison budget or source manifest was rewritten. No final completion checkpoint
or remote publication was made.
