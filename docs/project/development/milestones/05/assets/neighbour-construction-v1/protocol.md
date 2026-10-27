# CUDA neighbour construction, 27 October 2026

Control is the exact 186-file retained state-transfer final source, based on
Maelstrom 87145510a9e5d812066138c35f1fac82e4f593b0. Do not pool prior timings.
First profile the ordinary control's complete 480-step trajectories at 8000 and
110592 particles, separately attributing sorted kernel launch sequences to cell
generation, spatial sort, count, three prefix stages, fill and row sort. These
instrumented GPU intervals explain cost; they are not primary solver timings.

First trial chosen after that profile: schedule count/fill owners in existing
spatial cell order, retaining identity-indexed rows and all traversal equations.
No extra allocation, capacity limit, floating arithmetic change, launch or wait.
Run one warmup and two alternating exploratory pairs at both sizes, then assess
whether a more complex lookup/cache/cooperative rewrite is warranted. Preserve
all explorations and failures. Final candidate qualification must compare exact
rows with independent CPU oracles across permuted identities, discontinuous cells,
strict support edges, dense rows, all four block sizes, tails and storage reuse.
Preserve checked quantities and stage/particle priority, allocation/capacity faults,
completed-stage cancellation, retry, poisoning and accepted snapshot ownership.

Freeze complete final source including tests/comments before final qualification
and measurement. Run ordinary release PC suite, explicit CUDA library/boundary/
integration tests, strict Clippy, formatting, native ASan/UBSan, CPU feature
isolation. Attempt device sanitiser separately; unsupported tooling is no pass.
Locked offline precise compute_89 release builds and isolated scene/config roots.

Final campaign: seven sizes64..8000,480steps,checkpoints0/1/120/240/480; primary
8000 with checkpoints,110592 without,110592 with XSPH.01/confinement.1 without.
Device0/block128/refinement4/eight iterations/unpaced/no graphics. Each request
starts anew. One warmup each and five alternating pairs, first measured candidate
then control. Check exact canonical physical/ordered diagnostic results excluding
measurements/buildrevision; stop and retain mismatches/incomplete runs, no
replacement samples. Record hardware, inputs, source, binary, embedded PTX hashes,
command exits, monotonic child durations, separate collector/storage durations.
Require4GiB host/2GiB GPU free; timeout120s request,600s test,180s profiler.
Primary time sums completed solver steps including validation/transfers/waits/
acceptance; construction,teardown,audits,serialization excluded. Preserve every
sample, paired effects, medians/ranges/slower pairs, no significance claim.

Final separate full480step traces for both variants/sizes using ordinary binaries
(no event overlay) must report early/late/full stage GPU times and launches,
explicit stream waits, transfer bytes/counts. Verify launch order and source byte
models, and physical equivalence of profile runs. Retain privacy-limited SQLite
activity and all compressed child outputs; raw nsys reports stay on PC. Inspect
kernel resource attributes and source-owned allocation cost. Retention follows
performance-assessment.md: correctness, measured benefit, uncertainty and engineering
cost, not an automatic threshold. Do not claim device-loss recovery, worst-case
cancellation latency, other GPU performance or fluid quality from equivalence.
