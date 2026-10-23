# Assessing optimisation results

An optimisation stays because the complete evidence supports a useful improvement at an
acceptable engineering cost. The implementing agent must make and record that assessment.
Automation validates observations and describes effects; it does not decide whether code stays.
This policy replaces automatic percentage and range-separation rules in earlier experiments.
Those protocols and their recorded outcomes remain historical evidence.

## Requirements that remain firm

Preserve the numerical and behavioural contract, equivalent workload, deterministic ordering,
error handling and accepted-state semantics. A numerical variant needs its own explicit contract
and qualification. Do not retain an optimisation with an unresolved correctness or safety
regression. Existing unrelated failures must be reproduced, disclosed and kept distinct from
new failures; a performance gain does not excuse weakening a test.
Explicit user requirements and established numerical, safety and resource budgets still apply.

Validate source, executable and input identities and keep every requested sample, including
failures, warnings and slow runs. State the timer boundary, device, resources and environment.
Important comparisons use the primary PC. Resource ceilings and timeouts still bound collection;
they are not automatic judgements about an implementation's value.

## Evidence to consider

- Compare equivalent runs in their intended pairs and retain their order. Report individual
  savings and ratios, workload medians, slower pairs and variability. Keep separate campaigns
  separate unless combining them was justified in the measurement design.
- Weigh the size and consistency of the whole-application benefit, relevant workload coverage,
  regressions, memory or capacity effects, and whether profiling supports the proposed mechanism.
  Component and instrumented timings explain a result; they do not replace primary timings.
- Consider complexity, maintenance, portability, compilation, code size and safety costs.
  A small reliable saving can justify a simple change; a complicated rewrite needs stronger
  justification. There is no universal minimum percentage improvement.
- Investigate drift, outliers and sensitivity to run order without silently discarding samples
  or assigning an unobserved cause. Overlapping individual timing ranges are information about
  spread, not an automatic veto. Neither a favourable median nor all-positive pairs alone
  guarantees a benefit on other workloads or machines.
- State how much uncertainty remains. If formal confidence intervals or tests are useful,
  choose the method and sample plan prospectively and check their assumptions. Descriptive
  reports must not present themselves as statistical significance tests.

## The written decision

Conclude **retain**, **do not retain**, or **needs more evidence**, with a concise rationale.
Name the assessed source, relevant checks, measured effect, costs, limitations and the scope
of the claim. Explain any important regression or contradictory observation. Retention must
be supported by evidence, not merely by the absence of an automatic rejection.

Use further measurements to resolve a specific uncertainty. An inconclusive timing comparison
is not proof of a regression and does not automatically require reverting an otherwise valid
change. A low-risk change with convincing local evidence may be retained with a bounded claim;
a high-risk or expensive change may warrant more evidence or rejection for the same gain.
Retaining code and publishing a final project-wide performance claim are separate decisions.

Prespecify workloads, repetitions and analytical methods before collecting new evidence.
If a decision rule proves unsuitable, explain the revision and preserve the original outcome;
do not rewrite it as a historical pass or keep resampling until an arbitrary threshold passes.
Review earlier candidates individually rather than restoring every rejected optimisation.

New reports expose quantities and require a written assessment. The arithmetic reporter's
`--historical-policy` option and explicitly named historical helpers exist only to reproduce
old outcomes. Independent readers continue to reject false summaries and changed observations.
The [host-acceptance reassessment](/docs/project/development/assets/acceptance-review-v1/README.md)
is the first decision under this policy; it reuses existing measurements explicitly.
