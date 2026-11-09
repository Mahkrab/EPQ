# Particle rendering measurements

Medians of three ordinary alternating pairs, excluding warm-ups. GPU draw intervals come from separate synchronising profiles. These are primary-PC client-window measurements, not physical desktop FPS.

## Indexed versus retained impostor

| Particles | Metric | Indexed | Impostor |
| ---: | --- | ---: | ---: |
| 8,000 | Surface presentations/s | 62.781 | 62.751 |
| 8,000 | Mean interval, ms | 15.928 | 15.936 |
| 8,000 | p95 interval, ms | 16.819 | 16.872 |
| 8,000 | p99 interval, ms | 17.072 | 17.095 |
| 8,000 | Simulated s/wall s | 2.3091 | 2.3316 |
| 8,000 | Timesteps/s | 554.196 | 559.572 |
| 8,000 | Complete CUDA solver call, ms/step | 1.828 | 1.812 |
| 8,000 | Complete launch/completion wall time, s | 2.458 | 2.450 |
| 8,000 | Process CPU, core equivalents | 1.144 | 1.142 |
| 8,000 | Peak host RSS, KiB | 291380 | 290924 |
| 8,000 | GPU utilisation, % | 45.25 | 47.67 |
| 8,000 | GPU memory, MiB | 1198.08 | 1199.92 |
| 8,000 | SM clock, MHz | 2790.00 | 2790.00 |
| 8,000 | Memory clock, MHz | 10251.00 | 10251.00 |
| 8,000 | CPU acquire, ms/frame | 0.0030 | 0.0029 |
| 8,000 | CPU prepare, ms/frame | 0.0964 | 0.1176 |
| 8,000 | CPU upload, ms/frame | 0.3317 | 0.3633 |
| 8,000 | CPU submit, ms/frame | 0.6878 | 0.7116 |
| 8,000 | CPU present, ms/frame | 3.0128 | 3.0125 |
| 8,000 | CPU redraw, ms/frame | 4.5615 | 4.6089 |
| 8,000 | GPU draw interval, ms/frame | 0.3557 | 0.0298 |
| 32,000 | Surface presentations/s | 62.554 | 62.571 |
| 32,000 | Mean interval, ms | 15.986 | 15.982 |
| 32,000 | p95 interval, ms | 16.545 | 16.589 |
| 32,000 | p99 interval, ms | 16.825 | 16.791 |
| 32,000 | Simulated s/wall s | 1.2754 | 1.3619 |
| 32,000 | Timesteps/s | 306.098 | 326.857 |
| 32,000 | Complete CUDA solver call, ms/step | 3.273 | 3.062 |
| 32,000 | Complete launch/completion wall time, s | 4.204 | 3.959 |
| 32,000 | Process CPU, core equivalents | 1.152 | 1.149 |
| 32,000 | Peak host RSS, KiB | 297044 | 297940 |
| 32,000 | GPU utilisation, % | 62.33 | 60.00 |
| 32,000 | GPU memory, MiB | 1210.62 | 1213.55 |
| 32,000 | SM clock, MHz | 2777.14 | 2777.25 |
| 32,000 | Memory clock, MHz | 10251.00 | 10251.00 |
| 32,000 | CPU acquire, ms/frame | 0.0035 | 0.0036 |
| 32,000 | CPU prepare, ms/frame | 0.3054 | 0.3635 |
| 32,000 | CPU upload, ms/frame | 0.3479 | 0.3559 |
| 32,000 | CPU submit, ms/frame | 0.6147 | 0.6720 |
| 32,000 | CPU present, ms/frame | 2.8875 | 2.7038 |
| 32,000 | CPU redraw, ms/frame | 4.5104 | 4.5371 |
| 32,000 | GPU draw interval, ms/frame | 1.5670 | 0.0607 |
| 110,592 | Surface presentations/s | 62.335 | 62.391 |
| 110,592 | Mean interval, ms | 16.042 | 16.028 |
| 110,592 | p95 interval, ms | 17.244 | 16.693 |
| 110,592 | p99 interval, ms | 17.580 | 16.965 |
| 110,592 | Simulated s/wall s | 0.3096 | 0.4729 |
| 110,592 | Timesteps/s | 74.310 | 113.505 |
| 110,592 | Complete CUDA solver call, ms/step | 13.361 | 8.732 |
| 110,592 | Complete launch/completion wall time, s | 16.136 | 10.830 |
| 110,592 | Process CPU, core equivalents | 1.199 | 1.225 |
| 110,592 | Peak host RSS, KiB | 316688 | 316204 |
| 110,592 | GPU utilisation, % | 83.81 | 76.47 |
| 110,592 | GPU memory, MiB | 1269.59 | 1262.91 |
| 110,592 | SM clock, MHz | 2775.00 | 2769.62 |
| 110,592 | Memory clock, MHz | 10251.00 | 10251.00 |
| 110,592 | CPU acquire, ms/frame | 0.0051 | 0.0049 |
| 110,592 | CPU prepare, ms/frame | 1.0078 | 1.1808 |
| 110,592 | CPU upload, ms/frame | 0.4458 | 0.4877 |
| 110,592 | CPU submit, ms/frame | 0.7065 | 0.7552 |
| 110,592 | CPU present, ms/frame | 7.6391 | 2.0511 |
| 110,592 | CPU redraw, ms/frame | 10.2244 | 4.8940 |
| 110,592 | GPU draw interval, ms/frame | 5.9775 | 0.1695 |

CPU JSON stage keys retain `_s`; this table converts them to milliseconds. Upload is allocation/upload API wall time, not isolated DMA time. Submit includes encoding and error polling; present includes backpressure. These overlap GPU execution and must not be added to solver/GPU timings. CPU uses one logical core as 1.0. GPU readings are whole-device 200 ms samples, including background/desktop memory; utilisation is activity, not achieved occupancy.

## All representation comparisons

Each candidate has its own adjacent indexed controls. Ranges and individual paired effects remain in `comparison.json`.

| Candidate | Particles | Indexed → candidate sim s/wall s | Paired physics ratios | GPU draw, ms/frame |
| --- | ---: | ---: | --- | ---: |
| low | 8,000 | 2.2392 → 2.3062 | 1.032×, 1.027×, 1.039× | 0.1509 |
| low | 32,000 | 1.2192 → 1.2857 | 1.061×, 1.049×, 1.085× | 0.5376 |
| low | 110,592 | 0.3102 → 0.4184 | 1.349×, 1.315×, 1.353× | 2.1366 |
| impostor | 8,000 | 2.3091 → 2.3316 | 1.036×, 1.010×, 1.008× | 0.0298 |
| impostor | 32,000 | 1.2754 → 1.3619 | 1.055×, 1.067×, 1.100× | 0.0607 |
| impostor | 110,592 | 0.3096 → 0.4729 | 1.481×, 1.548×, 1.537× | 0.1695 |
| adaptive | 8,000 | 2.2562 → 2.3034 | 1.019×, 1.021×, 1.024× | 0.1987 |
| adaptive | 32,000 | 1.2505 → 1.2923 | 1.053×, 1.033×, 1.044× | 0.7322 |
| adaptive | 110,592 | 0.3135 → 0.3927 | 1.253×, 1.257×, 1.220× | 3.2751 |

## Every-one-second capacity qualification

Each repeat computes all 4,800 timesteps (20.000001 simulated seconds). Exact acceptance timestamps cover every continuous full one-second window, including those between displayed observations. The clock starts after construction and before the first step, includes all solver calls and inter-step observation/rendering contention, and excludes construction and teardown CSV writing.

| Particles | Repeat | Average sim s/wall s | Worst one-second steps | Worst one-second sim s | Qualifies |
| ---: | ---: | ---: | ---: | ---: | --- |
| 35,200 | 1 | 1.1392 | 265 | 1.104167 | yes |
| 35,200 | 2 | 1.1432 | 266 | 1.108333 | yes |
| 35,200 | 3 | 1.1530 | 269 | 1.120833 | yes |
| 38,400 | 1 | 1.0607 | 247 | 1.029167 | yes |
| 38,400 | 2 | 1.0638 | 247 | 1.029167 | yes |
| 38,400 | 3 | 1.0587 | 248 | 1.033333 | yes |
| 40,000 | 1 | 1.0320 | 240 | 1.000000 | yes |
| 40,000 | 2 | 1.0304 | 237 | 0.987500 | no |
| 40,000 | 3 | 1.0347 | 241 | 1.004167 | yes |

The original campaign's highest verified count is **38,400**, 9.09% above 35,200. This is a measured lattice bracket with 1,600-particle layers, not an exact universal maximum. At 40,000 the overall mean passes, but repeat two contains only 237 steps in its worst second (0.9875 simulated seconds), so that count fails. The 41,600/48,000 short pilots cannot qualify capacity. At 110,592, 0.4729× real time requires approximately 2.11× further complete-viewer throughput.

**The slower resumed session qualified only 28,800.** Its separate large-scene comparison still improved physics by 58.6%, from 0.2423 to 0.3842× real time. See [post-resume evidence](/docs/project/development/milestones/05/assets/particle-rendering-v1/post-resume/README.md). Do not treat 38,400 as a current guaranteed capacity or pool the sessions.
