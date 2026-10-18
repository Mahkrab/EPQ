# Threaded uniform-grid, 12 workers performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-18T15:30:42.099085+00:00 to 2026-10-18T15:36:58.566245+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 8.376671 | 8.315117–8.404229 | 0.045624 | 17.451398 | 3,667 |
| 216 | 8.316038 | 8.308469–8.342033 | 0.017605 | 17.325078 | 12,467 |
| 512 | 7.303769 | 7.225485–7.311355 | 0.047539 | 15.216185 | 33,648 |
| 1,000 | 6.865027 | 6.839273–6.877721 | 0.019590 | 14.302139 | 69,920 |
| 1,728 | 7.906639 | 7.872166–7.910976 | 0.021266 | 16.472165 | 104,904 |
| 4,096 | 12.634991 | 12.609318–12.670814 | 0.030887 | 26.322898 | 155,606 |
| 8,000 | 21.592798 | 21.564121–21.594882 | 0.017190 | 44.984996 | 177,837 |

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
| 64 | 480 | 8.398673 | 0.00% | 0.00% | 0.38% | 99.36% | 0.19% | 0.03% | 0.001899571 |
| 216 | 480 | 8.368059 | 0.02% | 0.01% | 1.53% | 97.65% | 0.63% | 0.09% | 0.005511292 |
| 512 | 480 | 7.195954 | 0.06% | 0.04% | 4.66% | 93.17% | 1.70% | 0.24% | 0.010492460 |
| 1,000 | 480 | 6.882848 | 0.11% | 0.10% | 10.69% | 84.88% | 3.45% | 0.49% | 0.019848605 |
| 1,728 | 480 | 7.995674 | 0.20% | 0.10% | 17.67% | 75.84% | 5.10% | 0.68% | 0.032742640 |
| 4,096 | 480 | 12.738451 | 0.23% | 0.12% | 29.88% | 60.68% | 7.43% | 1.07% | 0.075087590 |
| 8,000 | 480 | 21.762074 | 0.34% | 0.19% | 37.06% | 52.05% | 8.40% | 1.13% | 0.182012973 |

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
