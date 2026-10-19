# Serial uniform-grid performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-19T09:49:53.545925+00:00 to 2026-10-19T09:59:42.763321+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.328366 | 0.327064–0.328872 | 0.000933 | 0.684096 | 93,554 |
| 216 | 1.255364 | 1.254682–1.264304 | 0.005369 | 2.615342 | 82,590 |
| 512 | 3.181563 | 3.177425–3.185851 | 0.004213 | 6.628257 | 77,245 |
| 1,000 | 6.815932 | 6.598518–6.832208 | 0.130477 | 14.199858 | 70,423 |
| 1,728 | 12.484920 | 12.469283–12.555184 | 0.045754 | 26.010249 | 66,435 |
| 4,096 | 31.378775 | 31.315133–31.459459 | 0.072331 | 65.372448 | 62,656 |
| 8,000 | 63.791997 | 63.777887–63.808944 | 0.015550 | 132.899995 | 60,196 |

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
| 64 | 480 | 0.329218 | 0.09% | 0.07% | 6.65% | 88.36% | 4.12% | 0.59% | 0.000395353 |
| 216 | 480 | 1.261978 | 0.09% | 0.06% | 8.54% | 86.95% | 3.74% | 0.50% | 0.001429486 |
| 512 | 480 | 3.191540 | 0.08% | 0.05% | 9.37% | 86.47% | 3.47% | 0.46% | 0.002862537 |
| 1,000 | 480 | 6.813158 | 0.07% | 0.05% | 9.80% | 86.43% | 3.17% | 0.42% | 0.005193649 |
| 1,728 | 480 | 12.506971 | 0.06% | 0.04% | 10.08% | 86.37% | 2.97% | 0.41% | 0.008971797 |
| 4,096 | 480 | 31.283609 | 0.05% | 0.04% | 11.01% | 85.72% | 2.74% | 0.37% | 0.020021614 |
| 8,000 | 480 | 64.153235 | 0.05% | 0.04% | 11.48% | 85.38% | 2.62% | 0.36% | 0.042122662 |

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
