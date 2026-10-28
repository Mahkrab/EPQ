# Active-distance validation investigation, 27 October 2026

Retained control is the 188-file density/lambda candidate, on Maelstrom HEAD
1e0085926d05c42949bb76b55d177d42a1f8f94f with the existing uncommitted density
patch and test file preserved. EPQ HEAD 1f76097a218266822cdf344c38db75ed128628a8.
No Git actions authorised. Separate frozen trees and targets on ssh pc.

Before implementation: fresh precise compute_89 release control, fresh embedded PTX
identity, one 480-step warmup and one ordinary-binary Nsight capture at 8000 and
110592 particles. Compare exact physical output; identify neighbour/geometry reuse
from source and stage timings. No unsupported hardware-counter claims.

Candidate may combine validation and numerical calculations speculatively only if
ordered geometry errors remain globally prior to all numerical errors and outputs
are published after successful validation. Preserve binary32 operation/reduction
order, row membership, checked expressions, deterministic errors and unchanged
Jacobi, diagnostic, host cancellation/acceptance boundaries. No check removal.

Before final collection freeze final source, test and public docs. Qualify ordinary
release suite, explicit CUDA lib/boundary/execution tests, strict Clippy, fmt, native
ASan/UBSan, CPU feature isolation and attempt device sanitiser. New deterministic
fixtures must pass retained equations as well.

Primary campaign: seven 64..8000 regression trajectories plus 8000 checkpoints
0,1,120,240,480;110592 and 110592 XSPH .01/confinement .1 without checkpoints.
Every request starts a new simulation, device0/block128/refinement4/eight iterations,
480 unpaced steps/no graphics. One warmup then five alternating pairs per workload,
first measured candidate/control; no sample replacement. Exact canonical physical
and ordered diagnostic equality excluding measurements/build_revision only.
Four GiB host/two GiB GPU admission; run120s,test600s,trace180s limits.
Completed-step totals include all preparation/checks/transfers/completion/acceptance;
construction/teardown/output/audits separate; child and collector wall clocks retained.
Separate full 480-step ordinary profiles both variants/sizes; early/late/per-iteration
GPU times, launches/waits/copy counts and sizes audited against source. Record resource
attributes, additional scratch bytes and all slow pairs. Five pairs are descriptive
observations, not statistical significance. No campaign pooling/resampling. Retention
requires a documented engineering assessment under performance-assessment.md.
