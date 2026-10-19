# Threaded uniform-grid, 12 workers performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-19T09:59:42.868559+00:00 to 2026-10-19T10:05:59.037124+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 8.426217 | 8.414887–8.454735 | 0.020533 | 17.554620 | 3,646 |
| 216 | 8.417105 | 8.405137–8.545483 | 0.077805 | 17.535636 | 12,318 |
| 512 | 7.330407 | 7.270381–7.359987 | 0.045657 | 15.271681 | 33,526 |
| 1,000 | 6.948293 | 6.940534–6.971709 | 0.016229 | 14.475610 | 69,082 |
| 1,728 | 7.997439 | 7.965664–8.014916 | 0.024969 | 16.661331 | 103,713 |
| 4,096 | 12.681015 | 12.670127–12.692886 | 0.011383 | 26.418781 | 155,041 |
| 8,000 | 21.519382 | 21.515115–21.579094 | 0.035770 | 44.832046 | 178,444 |

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
| 64 | 480 | 8.587982 | 0.00% | 0.00% | 0.38% | 99.36% | 0.19% | 0.03% | 0.001948108 |
| 216 | 480 | 8.513558 | 0.02% | 0.01% | 1.52% | 97.66% | 0.63% | 0.09% | 0.005525849 |
| 512 | 480 | 7.259468 | 0.06% | 0.03% | 4.62% | 93.17% | 1.72% | 0.25% | 0.011212628 |
| 1,000 | 480 | 6.983277 | 0.12% | 0.10% | 10.63% | 84.94% | 3.46% | 0.48% | 0.018914149 |
| 1,728 | 480 | 8.102737 | 0.15% | 0.17% | 17.71% | 75.73% | 5.13% | 0.70% | 0.033574584 |
| 4,096 | 480 | 12.880583 | 0.27% | 0.13% | 29.87% | 60.45% | 7.53% | 1.16% | 0.076817635 |
| 8,000 | 480 | 21.715664 | 0.27% | 0.20% | 36.88% | 52.13% | 8.53% | 1.21% | 0.171351614 |

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
