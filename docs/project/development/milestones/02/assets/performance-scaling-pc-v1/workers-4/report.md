# Threaded uniform-grid, 4 workers performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-18T15:20:45.907242+00:00 to 2026-10-18T15:25:25.985962+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.985097 | 0.949804–1.009898 | 0.030199 | 2.052286 | 31,185 |
| 216 | 1.461917 | 1.453903–1.500685 | 0.025019 | 3.045660 | 70,921 |
| 512 | 2.314932 | 2.313084–2.336095 | 0.012786 | 4.822775 | 106,163 |
| 1,000 | 3.830030 | 3.799476–3.842606 | 0.022181 | 7.979230 | 125,325 |
| 1,728 | 6.156865 | 6.139331–6.172918 | 0.016799 | 12.826801 | 134,718 |
| 4,096 | 13.579018 | 13.576543–13.624287 | 0.026879 | 28.289621 | 144,788 |
| 8,000 | 26.301695 | 26.241072–26.453071 | 0.109189 | 54.795197 | 145,998 |

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
| 64 | 480 | 0.974314 | 0.04% | 0.03% | 2.38% | 95.74% | 1.50% | 0.23% | 0.000916185 |
| 216 | 480 | 1.508967 | 0.08% | 0.05% | 7.54% | 88.43% | 3.28% | 0.45% | 0.002519786 |
| 512 | 480 | 2.319647 | 0.11% | 0.07% | 13.70% | 80.14% | 5.07% | 0.69% | 0.004613186 |
| 1,000 | 480 | 3.861302 | 0.13% | 0.09% | 18.57% | 74.24% | 5.95% | 0.83% | 0.007716280 |
| 1,728 | 480 | 6.203302 | 0.13% | 0.10% | 22.07% | 70.14% | 6.48% | 0.89% | 0.011747908 |
| 4,096 | 480 | 13.642011 | 0.13% | 0.09% | 26.06% | 66.04% | 6.60% | 0.90% | 0.022920877 |
| 8,000 | 480 | 26.345529 | 0.13% | 0.09% | 28.70% | 63.49% | 6.52% | 0.89% | 0.046053571 |

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
