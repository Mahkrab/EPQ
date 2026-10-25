# Dedicated CUDA entry-point trial

Start from EPQ `e6c5795b982e0079b1bb8ef212fac47114cf5947` and Maelstrom
`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`, published before implementation.
The [plan](/docs/project/development/performance-plan.md) and
[attribution](/docs/project/development/performance-neighbour-attribution.md) motivate this
separate experiment. No sorting, layout or arithmetic-reuse change is included.

## Hypothesis and boundaries

Replace the shared device entry with one named entry per existing operation. Keep the
stage bodies, precision flags, buffers, row ordering, launch sequence, block sizes,
completion boundaries and packed diagnostics unchanged. The old operation branch is
uniform across a launch; this tests compiler specialisation and per-operation resources,
not a claim of fixing warp divergence. Host operation 13 still batches cell-sort launches.

Keep the native operation mapping in one shared definition and test its correspondence
independently. Qualify every function-lookup failure, context cleanup, grouped launch failure
and deterministic numerical error path. Public Rust API and execution selection stay stable.

## Verification and measurement

Freeze separate source manifests and executable hashes from disposable exports. Exclude the
unrelated custom scene. Run the CUDA hardware suite explicitly, relevant CPU/CLI tests,
strict Clippy, formatting and native injected-failure tests with address/undefined sanitisers.
Check exact agreement with small independent cases and the unchanged control at all seven
bundled sizes, including dense rows, tails, all block sizes, cancellation and retry.

Use the primary PC, CUDA device 0 and 128 lanes. Both timing sizes use 480 steps,
timestep refinement 4 and eight iterations. At 8,000 particles retain checkpoints
0/1/120/240/480; the separately named 110,592-particle capacity scene omits audits.
Collect one warm-up per variant and five alternating matched pairs at each size.
Record solver-step totals, constructor/teardown and invocation durations separately.
Preserve all samples, warnings, failures and machine readings outside the timers.
Bound each invocation to 120 s with 30 s cancellation grace.

After ordinary sampling, collect one full 110,592-particle Nsight Systems trace per
variant. Check named functions against the original operation sequence, unchanged
launch/completion/transfer counts, early/evolved component costs and exact results.
Query actual driver-loaded function registers, local/shared storage and limits using
a separate resource probe. These are resource observations, not achieved occupancy
or hardware-counter measurements. Do not change counter permissions or installed executables.

Recheck source, executable and input hashes after collection. Keep native reports private
and publish only metadata-sanitised trace data with unchanged analytical rows. Retained
large-run warnings are an existing fluid-quality limitation, not a new qualification.

## Assessment

Apply the [engineering policy](/docs/project/development/performance-assessment.md).
Weigh complete-workload and component effects against constructor costs, code size,
maintenance and uncertainty. Keep the original samples and explain any follow-up before
collecting it. No percentage cutoff or timing-range overlap decides retention by itself.
Conclude retain, do not retain or needs more evidence in the decision record.

## Post-campaign diagnostic extension

The original campaign completed before this addition. Every small pair was slower
with the candidate: medians were 1.713/1.822 s for control/candidate. The large medians
were 10.085/10.124 s; all five large pairs were also slower, though by much less.
Actual function register counts fell from 46 to 12–43, so the proposed resource benefit
did not establish a runtime benefit. Preserve the original protocol, samples and traces.

Capture one additional full 8,000-particle trace per variant, without checkpoint audits,
to distinguish device costs from coordination gaps in the affected smaller workload.
Use the same binaries, resources, steps, refinement and iteration count. Compare exact
results and check unchanged launch/completion/transfer counts. These are diagnostic
traces, not replacement timing samples. Inspect kernel and launch API intervals, keeping
overlapping host/device clocks separate. Do not change code or collect new primary pairs
under this extension; use it to explain the existing evidence and conclude the assessment.

## Separately declared targeted follow-up

The small trace locates almost all additional device time in neighbour fill/sort:
0.126 s became 0.225 s over 480 steps. Other numerical kernels generally improved;
idle gaps were almost unchanged. The hardware reason for this code-generation sensitivity
is not established. Lower register counts did not predict this result.

Try a new candidate that keeps cell keys, cell sorting, neighbour count and neighbour fill
on the original shared dispatch, while specialising the numerical passes. Use the same
pass body for both forms; do not rewrite traversal or sort logic. This tests whether
isolating numerical work can avoid the observed search regression. A shared entry may
serve multiple operation IDs; validate that mapping rather than requiring unique names.

Preserve the first candidate patch, identities, samples and decision separately. Export
the follow-up with a new source identity and repeat hardware/native qualification,
seven-size regression, fresh warm-ups, five alternating pairs at both sizes and both
full-motion traces. Reuse the unchanged control executable explicitly. Do not pool
campaigns or reclassify the original full split as a pass. Assess the follow-up on its
complete results, including invocation costs and any remaining regression.
