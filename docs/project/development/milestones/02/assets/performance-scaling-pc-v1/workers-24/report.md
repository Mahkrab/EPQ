# Threaded uniform-grid, 24 workers performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-18T15:36:58.671329+00:00 to 2026-10-18T15:46:45.656399+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 15.896396 | 15.893162–16.289763 | 0.228050 | 33.117491 | 1,933 |
| 216 | 16.558731 | 16.501569–16.662565 | 0.081618 | 34.497357 | 6,261 |
| 512 | 13.446401 | 13.274090–13.620330 | 0.173121 | 28.013335 | 18,277 |
| 1,000 | 12.057045 | 11.882381–12.064994 | 0.103214 | 25.118845 | 39,811 |
| 1,728 | 12.530067 | 12.518484–12.957187 | 0.250009 | 26.104307 | 66,196 |
| 4,096 | 16.583034 | 16.434477–16.591471 | 0.088306 | 34.547988 | 118,560 |
| 8,000 | 27.019083 | 26.982083–27.100183 | 0.060407 | 56.289756 | 142,122 |

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
| 64 | 480 | 16.173583 | 0.00% | 0.00% | 0.21% | 99.66% | 0.10% | 0.02% | 0.001782345 |
| 216 | 480 | 16.536601 | 0.01% | 0.01% | 0.80% | 98.77% | 0.33% | 0.05% | 0.005713706 |
| 512 | 480 | 13.264461 | 0.03% | 0.02% | 2.57% | 96.22% | 0.95% | 0.13% | 0.010863625 |
| 1,000 | 480 | 11.884664 | 0.07% | 0.05% | 6.38% | 91.04% | 2.00% | 0.28% | 0.020532330 |
| 1,728 | 480 | 12.772224 | 0.10% | 0.10% | 11.26% | 84.58% | 3.22% | 0.47% | 0.033920607 |
| 4,096 | 480 | 16.743152 | 0.17% | 0.11% | 23.05% | 69.65% | 5.71% | 0.83% | 0.079295763 |
| 8,000 | 480 | 27.052316 | 0.22% | 0.21% | 29.78% | 61.32% | 6.83% | 1.03% | 0.162463951 |

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
