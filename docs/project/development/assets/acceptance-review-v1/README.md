# Retaining the checked plane-helper optimisation

**Decision: retain `#[inline(always)]` on `Plane::contains`.** This is an engineering
assessment under the [current policy](/docs/project/development/milestones/05/performance-assessment.md),
replacing the earlier automatic reversion. It does not rewrite that trial as a historical pass.

The [original bundle](/docs/project/development/assets/acceptance-inline-v1/README.md) is
unchanged, including raw measurements, protocols, manifests and failed automatic decisions.
Its statements about restoring the helper describe the earlier outcome. The
[development record](/docs/project/development/milestones/05/performance-host-acceptance.md) owns the current outcome.

## Reason for retention

All five confirmation pairs improved at both 8,000 and 110,592 particles. In the larger
case, each pair saved 2.355–3.862 s, while the workload median fell from 13.537 to
10.209 s: 24.6% less elapsed time, or 1.326× throughput. The smaller median fell from
2.099 to 1.897 s. These are separate workload results, not pooled campaigns.

The initial campaign was less consistent: the larger median improved by about 3%,
and one of its five pairs favoured the control. That limits confidence in the size of
the speed-up. It is retained as counterevidence, not removed in favour of the confirmation.

The mechanism is supported independently: instrumented large-case plane validation fell
from 2.714 to 0.304 s; full traces showed almost unchanged GPU busy time and shorter host
gaps. The source change is one annotation. Expressions, checks, iteration and plane order,
cancellation, accepted-state semantics and generated device code remain unchanged.

The substantial paired benefit and low implementation cost justify retention. Overall
range overlap and unresolved variability limit the performance claim; they do not erase
the paired evidence. No universal speed-up or statistical-significance claim is made.

## Identity and verification

The reinstated 151-file source matches the measured candidate fingerprint
`8c37d0e9c36fa6a8ff8f4a35916cf092570c76085ca6594ab0c5c355b580c2ad`,
based on Maelstrom `5120acfbcb07e94ebefd5957ad8f9afa47888be7`. It is an uncommitted
working tree, not a completion checkpoint. The custom scene remains unchanged.

The earlier candidate qualification is reused: 258 passing CUDA tests with the same
three known CLI failures as the control, CUDA Clippy and formatting, native ASan/UBSan,
five capacity comparisons, and independently checked physical outputs and warnings.
This reassessment does not claim another PC campaign or fresh hardware qualification.
New local verification and hashes are recorded in `verification.json` and `manifest.json`.

`paired-evidence.json` describes the initial campaign and confirmation separately.
`assessment.json` records the final decision and its limits. The independent audit checks
the quantities; it does not compute the engineering verdict. Tests preserve the old rule
for explicit historical replay and check that ordinary reports cannot silently invoke it.

Larger-scene CFL warnings, independent fluid-quality qualification, other platforms and
hosted verification remain outside this retention decision. No commits, tags or gitlink
updates are established here.
