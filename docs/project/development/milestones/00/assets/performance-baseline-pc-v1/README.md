# Primary PC performance baseline

This campaign is the primary serial-brute-force performance baseline. It was collected on the PC
reached through `ssh pc`, an AMD Ryzen 9 7900X under x86_64 WSL2 Ubuntu 24.04.5, from 18:07:42 to
18:20:04 UTC on 15 October 2026. The original `maelstrom-pc-baseline-v1` results from the PC's
`benchmark-results` directory are retained here byte for byte, with this explanatory file added.

The [report](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/report.md) gives human-readable results;
[dataset.json](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/dataset.json) records the policy,
environment, source and binary identities, summaries and raw-file hashes. `raw/` retains all 35
attempts. [correctness.json](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/correctness.json)
retains the full replayable correctness result.

## Results and scope

All seven sizes, from 64 to 8,000 particles, completed one warm-up, three primary samples and one
separate stage profile. Each request completed 480 steps with zero warnings, failures or timeouts.
Median solver totals range from 0.253382 s at 64 particles to 86.410862 s at 8,000. The latter is
the largest tested size, not an established limit. The correctness result matches the frozen golden
exactly after excluding recorded build context only.

The campaign uses Rust/Cargo 1.98.1, the standard release profile without custom Rust flags, and the
unchanged `serial-baseline-v1` policy: factor-four refinement, eight Jacobi iterations, checkpoints
0, 1, 120, 240 and 480, a 120-second invocation budget and a 30-second cancellation grace.
Profiles contain extra clocks and remain separate from the primary timings. Memory use is not measured.

## Provenance and validation

The clean measured implementation is Maelstrom
[`d8454231255133f732a682f83ecc14f83f256831`](https://github.com/Mahkrab/Maelstrom/tree/d8454231255133f732a682f83ecc14f83f256831).
Its 76 file hashes and combined tree fingerprint match the recorded source. Collector and policy hashes
refer to the files at EPQ
[`dae2a2070c825846a54bc515983aad3adfab634a`](https://github.com/Mahkrab/EPQ/tree/dae2a2070c825846a54bc515983aad3adfab634a).
The [current protocol](/docs/project/development/milestones/00/measurement-protocol.md) adds the device
designation after collection; no original dataset metadata or measured policy bytes were rewritten.

Raw-file and correctness hashes, independent summary statistics and byte-for-byte report regeneration
were checked when importing the evidence. This validates retained results, not a new benchmark run.
Shared WSL/Windows load, scheduling, thermal state and uncontrolled frequency remain limitations;
three samples describe variation without establishing statistical significance.

The [laptop campaign](/docs/project/development/milestones/00/assets/performance-baseline-v1/README.md)
and [laptop pilot](/docs/project/development/milestones/00/assets/performance-baseline-v1-pilot/README.md)
remain separate historical evidence. PC primacy is a device decision, not selection of the fastest
sample. Later backend comparisons must use the same device and policy rather than pooling machines.
Published checkpoint tags are unchanged; this campaign is additional evidence, not a rewritten checkpoint.
