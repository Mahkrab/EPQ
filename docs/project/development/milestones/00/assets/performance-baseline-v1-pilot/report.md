# Serial brute-force performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-15T09:47:00.354621+00:00 to 2026-10-15T10:01:30.017046+00:00.

Environment: Intel(R) Core(TM) 7 150U; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.640901 | 0.628148–0.665030 | 0.018731 | 1.335210 | 47,933 |
| 216 | 2.338220 | 2.314905–2.358123 | 0.021632 | 4.871292 | 44,341 |
| 512 | 6.429935 | 6.417401–6.439170 | 0.010926 | 13.395698 | 38,221 |
| 1,000 | 14.264064 | 13.058510–14.421528 | 0.745651 | 29.716799 | 33,651 |
| 1,728 | 28.498777 | 24.404668–28.629300 | 2.402301 | 59.372453 | 29,104 |
| 4,096 | 60.273564 | 59.522330–60.345978 | 0.456069 | 125.569926 | 32,619 |
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
| 64 | 480 | 0.638796 | 0.11% | 0.08% | 3.92% | 90.78% | 4.26% | 0.66% | 0.001243124 |
| 216 | 480 | 2.430431 | 0.12% | 0.07% | 6.51% | 88.83% | 3.69% | 0.57% | 0.004884795 |
| 512 | 480 | 6.426190 | 0.09% | 0.05% | 9.98% | 85.83% | 3.32% | 0.55% | 0.010828801 |
| 1,000 | 480 | 14.431973 | 0.07% | 0.04% | 14.32% | 82.04% | 2.92% | 0.48% | 0.020132870 |
| 1,728 | 480 | 19.848913 | 0.05% | 0.03% | 19.61% | 77.16% | 2.59% | 0.44% | 0.024010919 |
| 4,096 | 480 | 59.504576 | 0.04% | 0.03% | 34.04% | 63.50% | 1.99% | 0.31% | 0.057251842 |
| 8,000 | 371 (partial) | 119.192943 | 0.03% | 0.02% | 48.49% | 49.70% | 1.46% | 0.23% | 0.086043944 |

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
| 8,000 | warmup 1 | 372 | 130 | True | False |
| 8,000 | profile 1 | 371 | 130 | True | False |
