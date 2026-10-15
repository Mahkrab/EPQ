# Serial brute-force performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-15T18:07:42.757376+00:00 to 2026-10-15T18:20:04.515252+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.253382 | 0.253360–0.254562 | 0.000688 | 0.527879 | 121,240 |
| 216 | 0.933837 | 0.901912–0.975991 | 0.037157 | 1.945494 | 111,026 |
| 512 | 2.541016 | 2.490085–2.549645 | 0.032186 | 5.293783 | 96,717 |
| 1,000 | 5.720826 | 5.301589–5.813765 | 0.272862 | 11.918387 | 83,904 |
| 1,728 | 11.250372 | 10.957881–11.366018 | 0.210357 | 23.438276 | 73,726 |
| 4,096 | 33.599465 | 33.286479–33.602681 | 0.181638 | 69.998885 | 58,515 |
| 8,000 | 86.410862 | 85.730299–92.501003 | 3.728168 | 180.022630 | 44,439 |

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
| 64 | 480 | 0.250627 | 0.11% | 0.07% | 2.99% | 91.14% | 4.83% | 0.72% | 0.000364459 |
| 216 | 480 | 0.913536 | 0.10% | 0.06% | 5.85% | 89.00% | 4.27% | 0.60% | 0.001082113 |
| 512 | 480 | 2.559636 | 0.08% | 0.05% | 9.60% | 85.76% | 3.87% | 0.53% | 0.002601081 |
| 1,000 | 480 | 5.683001 | 0.07% | 0.04% | 14.22% | 81.70% | 3.40% | 0.48% | 0.004956668 |
| 1,728 | 480 | 11.247736 | 0.06% | 0.04% | 19.97% | 76.46% | 2.97% | 0.43% | 0.008470798 |
| 4,096 | 480 | 33.693482 | 0.04% | 0.03% | 33.64% | 63.65% | 2.26% | 0.32% | 0.018878364 |
| 8,000 | 480 | 85.703767 | 0.03% | 0.02% | 48.54% | 49.40% | 1.72% | 0.25% | 0.036401682 |

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
