# Threaded uniform-grid, 2 workers performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-18T15:14:20.132481+00:00 to 2026-10-18T15:20:45.803781+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.561333 | 0.552165–0.568404 | 0.008142 | 1.169443 | 54,727 |
| 216 | 1.224147 | 1.221276–1.272572 | 0.028823 | 2.550305 | 84,696 |
| 512 | 2.486010 | 2.456353–2.498533 | 0.021662 | 5.179188 | 98,857 |
| 1,000 | 4.742361 | 4.727722–4.782998 | 0.028639 | 9.879919 | 101,215 |
| 1,728 | 8.370698 | 8.356692–8.437084 | 0.042946 | 17.438954 | 99,089 |
| 4,096 | 19.833324 | 19.660760–19.878105 | 0.114763 | 41.319425 | 99,130 |
| 8,000 | 39.021825 | 39.011792–39.026205 | 0.007389 | 81.295468 | 98,406 |

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
| 64 | 480 | 0.575162 | 0.06% | 0.04% | 3.98% | 92.89% | 2.50% | 0.37% | 0.000872376 |
| 216 | 480 | 1.321225 | 0.09% | 0.06% | 8.58% | 86.78% | 3.79% | 0.51% | 0.002457924 |
| 512 | 480 | 2.484210 | 0.10% | 0.07% | 12.31% | 82.18% | 4.55% | 0.62% | 0.004311505 |
| 1,000 | 480 | 4.820024 | 0.10% | 0.07% | 15.26% | 78.85% | 4.90% | 0.66% | 0.007689302 |
| 1,728 | 480 | 8.376500 | 0.10% | 0.07% | 17.10% | 76.91% | 4.98% | 0.69% | 0.011974665 |
| 4,096 | 480 | 19.894452 | 0.10% | 0.07% | 18.19% | 75.54% | 5.26% | 0.71% | 0.024898682 |
| 8,000 | 480 | 39.115917 | 0.10% | 0.07% | 19.29% | 74.72% | 4.99% | 0.70% | 0.055687308 |

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
