# Host coordination costs

## Question and outcome

The next investigation separated CPU bounds, [CFL](https://en.wikipedia.org/wiki/Courant%E2%80%93Friedrichs%E2%80%93Lewy_condition) and neighbour-prefix calculations from the
copies and packing around them. The question was whether moving these calculations onto the
GPU should take priority over further kernel work. The
[protocol](/docs/project/development/milestones/05/performance-coordination-protocol.md) fixed the
host measurements before collection; the [evidence](/docs/project/development/milestones/05/assets/host-coordination-v1/README.md)
retains the observations and a separately declared GPU-ranking follow-up.

**Decision: defer standalone device reductions and scans for now.** The three CPU calculations
together occupied about 2% of the large disabled-effect run. Their surrounding work increased
that opportunity bound to about 5%, before allowing for replacement GPU work. These are useful
costs to know, but the fresh trace gives correction arithmetic a stronger claim on the next
investigation. This is a judgement about priority and implementation cost, not a percentage
threshold for rejecting future improvements.

## Method and source

The normal Maelstrom source was unchanged. An isolated diagnostic export added disjoint CPU
clocks, with logging outside the component intervals but inside the enclosing solver step.
Downloads include allocation, waiting and native copy wrappers; they are not bandwidth tests.
CPU calculation intervals exclude those downloads. An internal diagnostic switch belongs only
to this export and is not a new user setting.

Both exports start from Maelstrom
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0)
plus the retained prefix and cooperative-sort changes. The 180-file control fingerprint is
`0383da2a3781bfe8e7a4e1518fa38e258611a2502d7194c822a0ad9236b1c4e0`;
the diagnostic fingerprint is recorded with its patch and reconstruction checks. These are
uncommitted measured exports, not Git checkpoints. Separately compiled CUDA code was identical
in both executables.

Measurements ran on the primary PC: Ryzen 9 7900X, RTX 4070, WSL2, driver 610.88, CUDA 13.3.73
and Rust 1.96.0. Locked offline release builds used target 89 and precise arithmetic. Every
request ran 480 unpaced steps, refinement 4 and eight iterations, device zero and block size 128,
without rendering. Each workload had a warm-up per variant and three alternating measured pairs.
Only the 8,000-particle case kept checkpoints 0/1/120/240/480. The larger enabled case used
XSPH 0.01 and confinement 0.1 m/s.

## What the measurements showed

The following are medians across complete runs, in seconds. Component columns describe the
diagnostic export; ordinary control totals remain separate.

| Workload | Control solver | Diagnostic solver | CPU bounds | CPU CFL | CPU prefix |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8,000, effects disabled | 1.5871 | 1.6541 | 0.00643 | 0.00481 | 0.00147 |
| 110,592, effects disabled | 8.6748 | 8.7016 | 0.08842 | 0.06641 | 0.01685 |
| 110,592, both effects enabled | 8.9752 | 9.0368 | 0.08905 | 0.06665 | 0.01676 |

For the large disabled-effect case, bounds plus its position download/repacking took 0.180 s;
CFL plus velocity download/repacking took 0.159 s; prefix plus count download, reservation and
offset upload took 0.094 s. Preparation separately took 0.182 s. Bundle medians are calculated
from each sample's summed intervals. The raw component, first-step and early/evolved observations
remain available rather than being reduced to this table.

Instrumentation increased median solver time by 4.2% at 8,000 particles and 0.3%/0.7% in the
larger cases. These ratios describe observation effects, not optimisation results. Three pairs
cannot establish every source of variation, and results from earlier campaigns are not pooled.

After those measurements, a declared control-only full-motion GPU trace checked the ranking.
Its 8.888 s window included 2.566 s of correction kernels, 1.395 s of density/multiplier kernels
and 1.499 s of neighbour count/fill kernels. Correction remained largest in early and evolved
windows. The 2.144 s outside device activity is not all removable host arithmetic. This trace
is diagnostic evidence, separate from ordinary solver timing.

## Verification and next decision

All paired physical records and warning schedules agreed exactly. Large disabled/enabled runs
retained 259/181 warning-bearing steps; integrity does not establish final fluid quality.
The diagnostic PC release suite passed 292 ordinary tests, followed by 22 explicitly selected
CUDA library checks and two application checks with logging disabled. Strict Clippy and formatting
passed. Locally, 73 parent performance-tool tests passed. The first discovery invocation treated
a namespace directory as an importable package; the corrected invocation is retained with its result.

An independent reader reconstructed all component sums, windows, medians and fractions from
hashed raw outputs. Negative controls rejected false component totals, bundle fractions,
instrumented-as-primary labelling and changed physical results. A separate trace audit checked
launches, transfers, completions and operation windows, and rejected a changed correction duration.
Source/binary checks remained unchanged throughout collection.

The next bounded investigation should inspect correction's generated arithmetic and invariant
coefficients before adding pair caches or changing storage. Preserve floating-point order,
validation and the retained optimisations. Device bounds, CFL and checked prefixes remain possible
follow-ups, especially within a broader residency change, but require preserving error precedence,
overflow and allocation behaviour. No GPU reduction was implemented or rejected here. No fresh
native sanitiser, device-memory-sanitiser, hosted or other-GPU qualification is claimed. Both
repositories remain uncommitted on their existing branch; no Git checkpoint was advanced.
