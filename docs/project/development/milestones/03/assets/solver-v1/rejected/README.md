# Rejected exploratory power results

`first-gpu.json.gz` preserves the initial 64-particle, 480-step GPU result using native CUDA
`powf`. `corrected-gpu.json.gz` preserves the next attempt, which evaluated library power in
binary64 before rounding to binary32. Both ran on the same RTX 4070/toolchain as the final collection.
Their full comparison reports apply the unchanged quantity-specific `reference-comparison-v1` limits.
The first violates the position limit at checkpoint 120; the second at checkpoint 480. Later
agreement or a small average error cannot admit either result.

These were exploratory uncommitted trees. Their exact complete historical source and binary hashes
were not captured, so the final source manifest must not be used as their source identity. Original
candidate and frozen-reference hashes are retained in each report. The first kernel-stage comparison
found a one-bit correction disagreement in Jacobi pass four; the expanded trace identified a power
rounding discrepancy at timestep 19, pass two, ratio bits `1058485772` (`0.59066844`). The host returned
`0.12172368`, whereas rounded binary64 library power returned `0.121723674`.

For reproducible evidence, both operations were subsequently rebuilt as deliberately rejected controls
of the final solver. The [extra collection](/docs/project/development/milestones/03/assets/solver-v1/extra/checks.json)
retains exact 99-file source manifests with the single altered expression, build commands, binary hashes,
complete results and disagreement reports. These reproduce the same failing checkpoints and largest
position discrepancies. They are labelled test variants, not supported implementations of the recorded
production backend contract. No acceptance limit or frozen reference was changed.
