# Phase 7 implementation and verification record

## Starting point

Both repositories began clean on `phase/00-07-performance-baseline`, with Maelstrom at
`48c43e7dec3d18a94ab74cc5efcbb6de13760654` and EPQ at
`77d50782e414a8c36fb8799bc60b6709bece3f06`. The frozen comparison family and goldens existed;
the solver had no measurement hooks or controlled performance dataset.

## Scope and outcome

The [measurement protocol](/docs/project/development/milestones/00/measurement-protocol.md) freezes
`serial-baseline-v1`: unchanged manifest inputs, one complete warm-up, three total-only samples and
one separately instrumented profile per size. The
[parent collector](/tools/baseline/main.py) builds the release binary, validates frozen hashes,
records the environment and source identity, bounds each invocation and retains raw observations.
The numerical equations, accepted-state semantics, inputs and dependencies are unchanged.
The primary [PC baseline](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/report.md)
and [dataset index](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/dataset.json)
retain the results and raw-file hashes. The PC is the primary benchmark device; the earlier laptop
campaign remains separate historical evidence, not the basis for the performance summaries below.

The implementation is retained in Maelstrom commit
[`d8454231255133f732a682f83ecc14f83f256831`](https://github.com/Mahkrab/Maelstrom/tree/d8454231255133f732a682f83ecc14f83f256831).
EPQ's gitlink pins that exact revision. Implementation links below identify this committed tree.

## Decisions and implementation

Primary measurements time complete transactional steps, including mandatory CFL diagnostics and
validation. Loading, construction, fresh audits, snapshots and presentation remain outside the clocks.
Optional stage clocks follow the same solver body. This avoids maintaining a second implementation
whose arithmetic or cancellation behaviour could drift. Profiling remains separate from primary
samples because internal clock reads introduce overhead, especially at small sizes.

Maelstrom exposes `--measure` and `--measure --stage-profile` on ordinary runs. The additive JSON
measurement object retains every accepted-step duration and separately records an unsuccessful
attempt. Unmeasured documents keep their previous shape; replay keeps its numerical meaning.
The collector also compares each complete measured run with that size's unmeasured warm-up using
exact numerical values and hashes of duplicate particle arrays. Missing, warning-bearing, cancelled
or otherwise incomplete requests cannot become a clean three-sample result.

The 120-second invocation budget was chosen before collection as a practical limit for repeated
local experiments. It includes untimed overhead; the measured solver total remains a separate value.
Cooperative cancellation gets 30 seconds to finish a non-interruptible stage and publish accepted
state before forced termination. The collector retains unsuccessful attempts and continues the
frozen sequence. Memory use is not measured; guest memory availability is only environment context.

## Verification

Local verification used x86_64 WSL2 Ubuntu 24.04.5 and Rust/Cargo 1.98.1 on 15 October 2026.
The locked/offline debug and release suites each passed **159 integration tests, three unit tests
and two doctests**, with no failures or ignored tests. Formatting, all-target checking, strict
Clippy and strict Rustdoc passed. The parent tooling and Markdown suites passed 15 tests, including
independently calculated summary statistics, outlier retention, signed-zero comparison, partial-run
exclusion, cooperative timeout publication, forced termination and evidence-file protection.

The same verification passed on the PC before its collection: 159 integration tests, three unit tests
and two doctests in each profile, the 15 parent tests, formatting, checking, strict Clippy and Rustdoc.

The [reference tests](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/tests/reference_verification.rs) compare measured runs against both
complete frozen goldens, including intermediate checkpoints and signed zero. They cover zero steps,
empty state, invalid inputs, numerical failure and cancellation without changing polling order or
accepted work. The [CLI checks](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/tests/cli_workflow.rs) cover both measurement modes,
argument constraints, text/JSON output and replay. Existing independent every-step health checks
continue to qualify the correctness trajectory; sparse baseline checkpoints do not replace them.

### Baseline observations

The primary collection ran on the AMD Ryzen 9 7900X PC under x86_64 WSL2 Ubuntu 24.04.5,
from 18:07:42 to 18:20:04 UTC on 15 October 2026. Rust/Cargo 1.98.1, the standard release profile
and the frozen policy were unchanged. All seven sizes completed their warm-up, three primary samples
and profile without warnings, failures or timeouts. Median solver totals for 480 steps ranged from
**0.253382 s** at 64 particles to **86.410862 s** at 8,000; 4,096 particles took **33.599465 s**.
The report retains every sample, spread, throughput and stage proportion. All 35 attempts completed,
so 8,000 is the largest tested fully sampled member, not an established hardware or algorithmic limit.

Neighbour discovery rose from 2.99% of the instrumented total at 64 particles to 48.54% at 8,000;
Jacobi calculations remained the largest complete-run stage. The profile identifies costs but does
not isolate a justified neutral implementation repair, so no optimisation was made and before/after
optimisation evidence is inapplicable. Small cases contain little discovery work: later backends
must demonstrate their benefit under the same boundary rather than assume a speedup at every scale.
The correctness run matched its golden exactly; final mean/maximum absolute relative density errors
remained
`0.09173302`/`0.20032573`, with zero CFL warnings and observed floor contact.

The earlier [laptop collection](/docs/project/development/milestones/00/assets/performance-baseline-v1/README.md)
and [pilot](/docs/project/development/milestones/00/assets/performance-baseline-v1-pilot/README.md)
remain unchanged. The laptop's 8,000-particle timeouts describe that device, not the PC's limit.
No samples are pooled across machines, and differences are not claimed as an algorithmic optimisation.
The PC is selected as the primary device, rather than selecting whichever individual sample is fastest.

## Limitations and Gate G06

The PC measured the clean committed Maelstrom revision identified above, with tree SHA-256
`fafad4c4feed66cef8a571b454bca9e4edc9309850089fa71fdc7a84fd455b4c`.
The dataset records every source-file hash and the measured binary hash. All 76 recorded file hashes
match the committed implementation exactly, with no missing or extra files. The original PC source
identity and measured binary hash remain unchanged in the dataset; the laptop's worktree identity and
binary hash remain in its separate collection. Neither is relabelled as a later rebuild.

Shared WSL/Windows load, scheduling, thermal state and uncontrolled frequency limit the performance
claim to this recorded environment. Three primary samples expose variation without establishing
statistical significance. Stage profiling adds clock overhead; neither it nor invocation wall time
is substituted for the primary total. No process memory measurement, hardware-counter profile,
other platform, later backend, hosted verification or browser rendering is claimed. The milestone
remains open for its separate evaluation and handoff.

G06's protocol, correctness, scalability, raw-sample and summary evidence is satisfied locally for
this stated scope. Report regeneration reproduced the stored Markdown exactly; source, binary,
collector, protocol, correctness-result and raw-file hashes all matched. Independent sums and
statistics agreed within floating-point accumulation roundoff. The matching annotated
`milestone-00/phase-07/complete` tags retain the original implementation and laptop evidence checkpoint;
they are not moved to include the later PC campaign. The PC evidence is a subsequent addition using
the same committed implementation and policy. This record does not close the milestone.
