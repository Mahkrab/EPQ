# Serial uniform-grid performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-17T16:30:41.931607+00:00 to 2026-10-17T16:39:12.438593+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.268774 | 0.268319–0.278854 | 0.005955 | 0.559945 | 114,297 |
| 216 | 1.097272 | 1.055931–1.098519 | 0.024236 | 2.285984 | 94,489 |
| 512 | 2.673178 | 2.657146–2.703562 | 0.023575 | 5.569121 | 91,936 |
| 1,000 | 5.921604 | 5.695839–5.929063 | 0.132551 | 12.336676 | 81,059 |
| 1,728 | 10.851780 | 10.446765–10.872579 | 0.240065 | 22.607874 | 76,434 |
| 4,096 | 26.231439 | 26.183838–26.284729 | 0.050472 | 54.648831 | 74,951 |
| 8,000 | 55.621480 | 55.458316–55.814149 | 0.178120 | 115.878083 | 69,038 |

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
| 64 | 480 | 0.275125 | 0.11% | 0.08% | 7.80% | 86.62% | 4.56% | 0.69% | 0.000399581 |
| 216 | 480 | 1.055672 | 0.10% | 0.06% | 10.31% | 84.74% | 4.10% | 0.57% | 0.001294017 |
| 512 | 480 | 2.673905 | 0.08% | 0.05% | 11.22% | 84.18% | 3.84% | 0.53% | 0.002708559 |
| 1,000 | 480 | 5.695765 | 0.07% | 0.05% | 11.68% | 84.11% | 3.51% | 0.49% | 0.005082065 |
| 1,728 | 480 | 10.515062 | 0.06% | 0.04% | 12.09% | 83.97% | 3.27% | 0.48% | 0.008807921 |
| 4,096 | 480 | 26.198715 | 0.06% | 0.04% | 12.99% | 83.32% | 3.04% | 0.43% | 0.032317222 |
| 8,000 | 480 | 53.576505 | 0.06% | 0.04% | 13.71% | 82.83% | 2.88% | 0.42% | 0.038715657 |

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
