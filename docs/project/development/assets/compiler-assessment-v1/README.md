# Compiler profile evidence

Primary-PC comparison of ordinary release against Rust ThinLTO with one code-generation
unit, collected on 25 October 2026. The
[assessment](/docs/project/development/milestones/05/performance-compiler-assessment.md) owns the decision.
Native flags and production profile defaults were unchanged.

`original/` contains the build, 18 explicitly enabled CUDA tests, settings, binary hashes,
five alternating sample pairs and one warm-up per variant at 8,000 and 110,592 particles.
Each invocation advances 480 steps with refinement 4, eight iterations, CUDA device 0 and
128 lanes, without checkpoint audits. Solver and invocation boundaries remain separate.

The original small campaign overlapped a separate playback-window check and is exploratory.
`confirmation/` contains its independently collected replacement: fresh warm-ups and five
small pairs after display testing ended. It is the small campaign used in the assessment.
The large original campaign began after the window closed; no samples were pooled or removed.
`confirmation/protocol.json` records the reason and unchanged executable identities.

The collector is `tools.performance.compiler_trial`. All accepted results agree exactly on
physical values and ordered diagnostics; larger-run CFL warnings remain. The trial does not
measure CPU-backend performance, viewer/export throughput or matched cold-build time.
It is not a new universal compiler baseline or hosted verification.

Raw solver JSON is losslessly compressed. Machine readings remain outside application timers.
`privacy.json` records shareable transformations; originals remain on the PC. `files.json`
hashes this evidence, excluding executable/target trees.

`independent-audit.json` recomputes every median from raw accepted-step intervals and
checks physical JSON across all samples without importing the collector's report functions.
