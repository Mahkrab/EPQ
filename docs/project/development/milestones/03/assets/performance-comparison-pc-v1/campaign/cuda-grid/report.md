# CUDA uniform-grid, device 0, 128 lanes performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-19T10:05:59.142872+00:00 to 2026-10-19T10:08:25.099471+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 1.993456 | 1.987259–1.995058 | 0.004119 | 4.153033 | 15,410 |
| 216 | 2.307267 | 2.293522–2.311990 | 0.009594 | 4.806807 | 44,936 |
| 512 | 2.586743 | 2.567660–2.588485 | 0.011553 | 5.389048 | 95,008 |
| 1,000 | 3.033133 | 3.020671–3.040207 | 0.009891 | 6.319027 | 158,252 |
| 1,728 | 3.401524 | 3.389463–3.409699 | 0.010180 | 7.086508 | 243,844 |
| 4,096 | 4.694764 | 4.688675–4.702762 | 0.007065 | 9.780758 | 418,781 |
| 8,000 | 7.611185 | 7.579296–7.632092 | 0.026588 | 15.856635 | 504,521 |

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
| 64 | 480 | 2.021839 | 3.57% | 1.28% | 17.67% | 54.87% | 20.09% | 2.53% | 0.000029473 |
| 216 | 480 | 2.331678 | 3.07% | 1.12% | 24.17% | 51.63% | 17.61% | 2.38% | 0.000029049 |
| 512 | 480 | 2.617352 | 2.84% | 0.97% | 26.82% | 51.37% | 15.58% | 2.42% | 0.000030090 |
| 1,000 | 480 | 3.021640 | 2.47% | 0.82% | 27.43% | 53.48% | 13.28% | 2.51% | 0.000029568 |
| 1,728 | 480 | 3.415232 | 2.27% | 0.74% | 28.56% | 53.79% | 11.81% | 2.82% | 0.000030022 |
| 4,096 | 480 | 4.709688 | 1.86% | 0.55% | 24.75% | 60.58% | 8.83% | 3.44% | 0.000034136 |
| 8,000 | 480 | 7.624718 | 1.40% | 0.38% | 19.22% | 69.35% | 6.06% | 3.58% | 0.000038412 |

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
