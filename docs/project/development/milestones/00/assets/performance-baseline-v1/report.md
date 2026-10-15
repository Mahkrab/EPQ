# Serial brute-force performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-15T10:01:57.560619+00:00 to 2026-10-15T10:15:17.782722+00:00.

Environment: Intel(R) Core(TM) 7 150U; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.446268 | 0.439448–0.446555 | 0.004023 | 0.929725 | 68,838 |
| 216 | 1.725730 | 1.714950–1.751431 | 0.018742 | 3.595270 | 60,079 |
| 512 | 4.478386 | 4.458518–4.481831 | 0.012584 | 9.329970 | 54,877 |
| 1,000 | 10.057480 | 9.953411–10.227825 | 0.138534 | 20.953083 | 47,726 |
| 1,728 | 19.121165 | 19.023582–19.130265 | 0.059142 | 39.835760 | 43,378 |
| 4,096 | 58.057931 | 57.979737–59.063870 | 0.604617 | 120.954023 | 33,864 |
| 8,000 | unavailable | incomplete clean sample set | — | — | — |

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
| 64 | 480 | 0.446323 | 0.10% | 0.07% | 3.46% | 91.11% | 4.39% | 0.67% | 0.000873242 |
| 216 | 480 | 1.737333 | 0.11% | 0.06% | 6.37% | 89.00% | 3.72% | 0.57% | 0.002869221 |
| 512 | 480 | 4.490080 | 0.10% | 0.05% | 9.73% | 86.06% | 3.34% | 0.55% | 0.007867866 |
| 1,000 | 480 | 10.023384 | 0.07% | 0.04% | 13.89% | 82.41% | 2.93% | 0.52% | 0.014425122 |
| 1,728 | 480 | 19.236834 | 0.05% | 0.03% | 19.58% | 77.22% | 2.56% | 0.44% | 0.022194806 |
| 4,096 | 480 | 58.111327 | 0.04% | 0.03% | 33.97% | 63.55% | 1.98% | 0.30% | 0.073862622 |
| 8,000 | 377 (partial) | 119.087782 | 0.03% | 0.02% | 48.65% | 49.53% | 1.47% | 0.22% | 0.092520596 |

Largest fully sampled member under the 120-second invocation budget: **4,096 particles**.

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
| 8,000 | warmup 1 | 377 | 130 | True | False |
| 8,000 | profile 1 | 377 | 130 | True | False |
