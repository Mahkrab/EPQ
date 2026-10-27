# Guarded quartic qualification and primary comparison

Retained baseline is the exact186-file neighbour-construction candidate on
Maelstrom87145510a9e5d812066138c35f1fac82e4f593b0. Initial individual-kernel and
eight-iteration profiles and all earlier alternatives remain in the separate
/tmp/maelstrom-jacobi-20261027 investigation and its named sibling workspaces.
Their sampling is not pooled with this final candidate. Initial profile legacy
apply/planes/project labels mean mass-check/candidate/projection.

Final change: exponent4 only, form a binary64 quartic, cast to binary32, then use
integer mantissa distance to its rounding midpoint. Accept when distance>2^21
binary64 mantissa units; otherwise call the retained approximation. Other
exponents, non-positive/non-finite inputs and subnormal/extreme results retain the
original path. Never approximate or change solver iterations/convergence. Every
original arithmetic operation in the fallback and every Checked call in solver.cu
remain intact. No interface/buffer/launch/neighbour/ordering change. The margin
is qualified by exhaustive comparison, not an assumed analytic error bound.

Before performance, require zero bit mismatches for all2^31 non-negative binary32
words with exponent4 against the retained function. Raw quartic negative control
must expose differences. Original broad floating midpoint guard passed but slowed
large runs. Fixed prospective margins2^-28,-30,-32,-34,-36 were all exhaustively
compared: the last two failed and remain failed. Integer distance2^21 passed all
words and fixed exploratory one-warmup/two-pair samples improved at both sizes.
No failed guard is retained. Header reference prefix must match the baseline body
apart from its function name. Qualify final exhaustive tool at all four block sizes,
retain commands, source/binary hashes, raw output, failures and counts. Test tool
uses Runtime API only; no production dependency is added.

Freeze final source including documentation/tool before qualification/sampling.
Locked offline precise compute_89 CUDA release builds with separate targets and
fresh embedded-PTX correspondence, source/input/binary identities. PC ordinary
suite, explicit CUDA library/boundary/integration tests, strict Clippy, formatting,
native ASan/UBSan. Existing independent CPU corrections exercise diverse exponents,
current support, coincidences, ordered sums, invalid inputs and all blocks. Retain
cancellation/rollback/panic/error-priority checks and CPU feature isolation. Attempt
Compute Sanitizer separately; unsupported WDDM tooling is no diagnostic pass.

Final workloads: seven64..8000 regression scenes480steps/checkpoints0,1,120,240,480.
Primary8000 with checkpoints,110592 without,110592 with XSPH.01/confinement.1
without. New simulations,480 unpaced steps,device0,block128,refinement4,eight
Jacobi iterations,no graphics. One warmup each then five alternating measured
pairs, first measured candidate/control. Preserve every slower sample/failure;
stop mismatches/incomplete runs, no replacements. Canonical physical/diagnostic
JSON must agree exactly excluding measurements/buildrevision. Require4GiB host/
2GiB GPU free,120s request/600s qualification/180s profiler limits. Record environment,
commands/exits and monotonic child/collector durations. Primary time sums completed
solver steps including validation, transfers, submission/completion, cancellation,
acceptance. Construction/teardown/audits/output remain separate.

After ordinary timing, full480step ordinary-binary profiles at both sizes/variants
without checkpoints. Attribute each numerical stage, each iteration and early/
late motion. Density/lambda share one kernel and must not be mislabelled as
separately measured. Reconstruct kernel types/order, launches, waits and every
copy size from privacy-limited activity rows; compare profiled physical records.
Observe actual driver-loaded resources and fresh PTX outside timed work. Retain
all exploratory patches, manifests and observations separately, including the full
coefficient-only campaign and negative outcomes. Reproduce audits after archive
readback and verify final live source hashes. Assess retention with performance-
assessment.md from correctness, measured effect, complexity, memory, variability
and limits. No fixed threshold, significance claim, other-GPU performance, fluid-
quality, device-loss or worst-case cancellation qualification is implied.
