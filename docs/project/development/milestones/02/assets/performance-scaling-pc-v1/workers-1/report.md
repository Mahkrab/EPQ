# Threaded uniform-grid, 1 workers performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-18T15:03:48.616526+00:00 to 2026-10-18T15:14:20.032388+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.625012 | 0.618184–0.629566 | 0.005729 | 1.302108 | 49,151 |
| 216 | 1.637440 | 1.633477–1.639652 | 0.003128 | 3.411332 | 63,318 |
| 512 | 3.792018 | 3.787971–3.795850 | 0.003940 | 7.900037 | 64,810 |
| 1,000 | 7.710107 | 7.690247–7.721428 | 0.015784 | 16.062722 | 62,256 |
| 1,728 | 13.670132 | 13.603502–13.900543 | 0.155864 | 28.479441 | 60,675 |
| 4,096 | 32.793518 | 32.747059–32.811241 | 0.033146 | 68.319828 | 59,953 |
| 8,000 | 65.606625 | 65.593613–65.646354 | 0.027475 | 136.680469 | 58,531 |

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
| 64 | 480 | 0.628301 | 0.05% | 0.04% | 3.55% | 93.64% | 2.25% | 0.34% | 0.000864045 |
| 216 | 480 | 1.650275 | 0.07% | 0.04% | 6.76% | 89.67% | 2.91% | 0.40% | 0.002307331 |
| 512 | 480 | 3.805999 | 0.07% | 0.05% | 9.21% | 86.86% | 3.20% | 0.47% | 0.005255627 |
| 1,000 | 480 | 7.748384 | 0.07% | 0.05% | 10.21% | 85.91% | 3.21% | 0.45% | 0.007737876 |
| 1,728 | 480 | 13.706625 | 0.07% | 0.05% | 10.23% | 85.90% | 3.22% | 0.45% | 0.011803675 |
| 4,096 | 480 | 32.947090 | 0.06% | 0.05% | 10.75% | 85.35% | 3.27% | 0.44% | 0.026340911 |
| 8,000 | 480 | 66.007860 | 0.06% | 0.04% | 11.25% | 84.96% | 3.15% | 0.44% | 0.063792253 |

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
