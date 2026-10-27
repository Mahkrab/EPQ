# CUDA synchronisation comparison, 27 October 2026

Control is the complete initial dirty Maelstrom tree; candidate applies only this
synchronisation change. Preserve full per-file hashes, source delta, binary hashes,
PTX identities, command arguments, exits, monotonic elapsed times and raw outputs.
Use separate exported source/build directories on ssh pc; no installed binaries or
ordinary PC checkouts are changed. Build release, locked/offline, cuda, compute_89.

Verify native injected failures under ASan/UBSan, Rust tests, explicit CUDA library,
application and integration tests, formatting and strict Clippy. Any ordinary-suite
failure must be reproduced on control, retained, and diagnosed separately.

Before timing, compare seven existing lattice sizes (64 through 8000) for 480
steps with checkpoints 0,1,120,240,480. Timing workloads: 8000 with those checkpoints,
110592 without checkpoints, 110592 with XSPH 0.01 and confinement 0.1 m/s without
checkpoints. All start new simulations, device 0, block 128, refinement 4, eight
Jacobi iterations, 480 unpaced steps, no graphics. One warm-up per variant/workload;
five alternating measured pairs in control/candidate, candidate/control order.
Use completed solver step totals; setup, teardown, audits and output are separate.
Keep all samples and warnings. Require exact canonical physical and diagnostic
records after excluding measurements and build revision. Stop on incomplete work
or a physical mismatch; do not replace inconvenient samples. Report medians,
individual paired changes, ranges and slower pairs. No significance claim.

Run separate 8-step CUDA API traces at 8000 particles to count synchronisations,
launches and copies. Profiled elapsed times do not enter timing comparisons. Retain
analytical SQLite API counts and any trace failure, excluding private profiler metadata.
Conclude retention from correctness, observed effect, uncertainty and complexity.
