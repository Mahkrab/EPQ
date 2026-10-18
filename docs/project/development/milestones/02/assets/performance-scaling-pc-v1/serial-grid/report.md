# Serial uniform-grid performance baseline

Policy: `serial-baseline-v1`. Collection: 2026-10-18T14:53:43.945892+00:00 to 2026-10-18T15:03:48.517006+00:00.

Environment: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`; x86_64.
Standard Cargo release build; sequential processes; no affinity, priority or frequency changes.
Primary totals exclude setup, audits and output. Raw per-step samples are retained in `raw/`.

| Particles | Median total (s) | Min–max (s) | Sample SD (s) | Median step (ms) | Particle updates/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.327190 | 0.326972–0.328425 | 0.000784 | 0.681645 | 93,890 |
| 216 | 1.263188 | 1.252578–1.287661 | 0.017992 | 2.631641 | 82,078 |
| 512 | 3.281100 | 3.176648–3.299343 | 0.066203 | 6.835625 | 74,902 |
| 1,000 | 6.842994 | 6.733264–6.864893 | 0.070529 | 14.256238 | 70,145 |
| 1,728 | 12.508839 | 12.436995–12.867378 | 0.230558 | 26.060082 | 66,308 |
| 4,096 | 30.966757 | 30.786611–31.620976 | 0.439056 | 64.514077 | 63,490 |
| 8,000 | 64.527357 | 62.904964–64.913885 | 1.065937 | 134.431993 | 59,510 |

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
| 64 | 480 | 0.331346 | 0.09% | 0.06% | 6.66% | 88.39% | 4.10% | 0.57% | 0.000400422 |
| 216 | 480 | 1.303567 | 0.09% | 0.05% | 8.31% | 87.40% | 3.57% | 0.47% | 0.001335219 |
| 512 | 480 | 3.163473 | 0.07% | 0.05% | 9.01% | 87.01% | 3.33% | 0.44% | 0.002723362 |
| 1,000 | 480 | 6.694897 | 0.07% | 0.04% | 9.79% | 86.47% | 3.13% | 0.42% | 0.005028431 |
| 1,728 | 480 | 12.434431 | 0.06% | 0.04% | 10.21% | 86.28% | 2.94% | 0.40% | 0.009215765 |
| 4,096 | 480 | 30.738381 | 0.05% | 0.04% | 10.85% | 85.91% | 2.72% | 0.37% | 0.019579053 |
| 8,000 | 480 | 65.327785 | 0.05% | 0.04% | 11.13% | 85.87% | 2.51% | 0.35% | 0.040228073 |

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
