# Serial brute-force performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-17T16:18:26.981628+00:00 to 2026-10-17T16:30:41.769103+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.256858 | 0.256728–0.263178 | 0.003687 | 0.535120 | 119,599 |
| 216 | 1.040863 | 1.000832–1.062058 | 0.031092 | 2.168464 | 99,610 |
| 512 | 2.659407 | 2.638062–2.662386 | 0.013267 | 5.540431 | 92,412 |
| 1,000 | 5.905200 | 5.898429–5.959772 | 0.033633 | 12.302500 | 81,284 |
| 1,728 | 11.568858 | 11.560358–11.986372 | 0.243543 | 24.101787 | 71,696 |
| 4,096 | 34.933192 | 34.774827–35.261180 | 0.248057 | 72.777482 | 56,281 |
| 8,000 | 90.021109 | 89.523530–92.218484 | 1.434040 | 187.543978 | 42,657 |

The 64-particle correctness run matched the golden exactly: 480 steps; 0 CFL warnings.

Checkpoint energy is mean specific kinetic plus gravitational potential energy, using 9.81 m/s² and floor height zero.
These sparse observations complement the separate every-step health tests.

| Step | Mean absolute relative density error | Maximum error | Minimum separation (m) | Mean energy (J/kg) | Floor contact |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.26401517 | 0.48484862 | 0.04999998 | 4.65975005 | False |
| 1 | 0.24676108 | 0.45804490 | 0.04870918 | 4.79024126 | False |
| 120 | 0.10724428 | 0.17493350 | 0.04106270 | 4.66863730 | False |
| 240 | 0.09295937 | 0.23792523 | 0.03926020 | 0.38376130 | True |
| 480 | 0.09173302 | 0.20032573 | 0.04117983 | 0.20486578 | True |

Instrumented profiles include additional clocks. Percentages divide stage sums by the profiled total.

| Particles | Profile steps | Total (s) | Validation/acceleration | Prediction | Search | Jacobi | Projection | Acceptance | Residual (s) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 480 | 0.257675 | 0.11% | 0.08% | 3.24% | 90.89% | 4.82% | 0.72% | 0.000374486 |
| 216 | 480 | 1.023958 | 0.11% | 0.06% | 6.14% | 88.62% | 4.34% | 0.60% | 0.001287290 |
| 512 | 480 | 2.645367 | 0.08% | 0.05% | 9.83% | 85.48% | 3.90% | 0.55% | 0.002776118 |
| 1,000 | 480 | 5.910986 | 0.07% | 0.04% | 14.27% | 81.66% | 3.40% | 0.48% | 0.005121556 |
| 1,728 | 480 | 11.554677 | 0.06% | 0.04% | 20.01% | 76.40% | 2.99% | 0.43% | 0.008509392 |
| 4,096 | 480 | 35.722129 | 0.04% | 0.03% | 33.17% | 64.14% | 2.24% | 0.32% | 0.019892567 |
| 8,000 | 480 | 89.740243 | 0.03% | 0.02% | 48.57% | 49.36% | 1.72% | 0.25% | 0.038611929 |

Largest fully sampled member under the 120-second invocation budget: **8,000 particles**.

This is an observed budget limit, not a universal maximum. No memory-use measurement was taken.
Three samples describe observed variation; they do not establish statistical significance or cross-machine performance.

| Particles | Attempt | Accepted steps | Exit | Timed out | Clean full request |
| ---: | --- | ---: | ---: | --- | --- |
| 64 | warmup 1 | 480 | 0 | False | True |
| 64 | sample 1 | 480 | 0 | False | True |
| 64 | sample 2 | 480 | 0 | False | True |
| 64 | sample 3 | 480 | 0 | False | True |
| 64 | profile 1 | 480 | 0 | False | True |
| 216 | warmup 1 | 480 | 0 | False | True |
| 216 | sample 1 | 480 | 0 | False | True |
| 216 | sample 2 | 480 | 0 | False | True |
| 216 | sample 3 | 480 | 0 | False | True |
| 216 | profile 1 | 480 | 0 | False | True |
| 512 | warmup 1 | 480 | 0 | False | True |
| 512 | sample 1 | 480 | 0 | False | True |
| 512 | sample 2 | 480 | 0 | False | True |
| 512 | sample 3 | 480 | 0 | False | True |
| 512 | profile 1 | 480 | 0 | False | True |
| 1,000 | warmup 1 | 480 | 0 | False | True |
| 1,000 | sample 1 | 480 | 0 | False | True |
| 1,000 | sample 2 | 480 | 0 | False | True |
| 1,000 | sample 3 | 480 | 0 | False | True |
| 1,000 | profile 1 | 480 | 0 | False | True |
| 1,728 | warmup 1 | 480 | 0 | False | True |
| 1,728 | sample 1 | 480 | 0 | False | True |
| 1,728 | sample 2 | 480 | 0 | False | True |
| 1,728 | sample 3 | 480 | 0 | False | True |
| 1,728 | profile 1 | 480 | 0 | False | True |
| 4,096 | warmup 1 | 480 | 0 | False | True |
| 4,096 | sample 1 | 480 | 0 | False | True |
| 4,096 | sample 2 | 480 | 0 | False | True |
| 4,096 | sample 3 | 480 | 0 | False | True |
| 4,096 | profile 1 | 480 | 0 | False | True |
| 8,000 | warmup 1 | 480 | 0 | False | True |
| 8,000 | sample 1 | 480 | 0 | False | True |
| 8,000 | sample 2 | 480 | 0 | False | True |
| 8,000 | sample 3 | 480 | 0 | False | True |
| 8,000 | profile 1 | 480 | 0 | False | True |
