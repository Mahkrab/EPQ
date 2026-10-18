# Threaded uniform-grid, 8 workers performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-18T15:25:26.087873+00:00 to 2026-10-18T15:30:41.996134+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 4.837695 | 4.807344–4.863606 | 0.028160 | 10.078530 | 6,350 |
| 216 | 4.378485 | 4.342946–4.468238 | 0.064571 | 9.121843 | 23,679 |
| 512 | 4.191353 | 4.187075–4.193091 | 0.003097 | 8.731986 | 58,635 |
| 1,000 | 5.132384 | 5.101920–5.164133 | 0.031109 | 10.692466 | 93,524 |
| 1,728 | 6.821368 | 6.812556–6.862763 | 0.026808 | 14.211184 | 121,594 |
| 4,096 | 12.897303 | 12.641621–12.901488 | 0.148841 | 26.869381 | 152,441 |
| 8,000 | 23.242135 | 23.127404–23.251506 | 0.069104 | 48.421114 | 165,217 |

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
| 64 | 480 | 4.834554 | 0.01% | 0.01% | 0.67% | 98.86% | 0.35% | 0.06% | 0.002394104 |
| 216 | 480 | 4.362573 | 0.04% | 0.03% | 2.87% | 95.56% | 1.20% | 0.17% | 0.005471250 |
| 512 | 480 | 4.164062 | 0.09% | 0.05% | 7.88% | 88.36% | 2.94% | 0.39% | 0.011237227 |
| 1,000 | 480 | 5.071858 | 0.14% | 0.10% | 14.44% | 79.65% | 4.66% | 0.63% | 0.019201479 |
| 1,728 | 480 | 6.767072 | 0.18% | 0.17% | 20.89% | 71.29% | 6.08% | 0.88% | 0.035578435 |
| 4,096 | 480 | 12.847690 | 0.22% | 0.14% | 29.99% | 60.50% | 7.46% | 1.05% | 0.081047683 |
| 8,000 | 480 | 23.359624 | 0.30% | 0.29% | 34.51% | 55.00% | 7.98% | 1.17% | 0.174702735 |

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
