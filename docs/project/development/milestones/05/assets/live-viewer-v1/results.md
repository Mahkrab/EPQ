# Matched live client-window results

One warm-up and three alternating pairs per size. Values are medians across the three measured invocations; raw ranges and every pair are in `comparison.json`. The GPU draw row comes from separate synchronising timestamp profiles and is not an additive part of the CPU frame intervals. Desktop scan-out FPS was not established.

## 8,000 particles

| Measurement | Before | After | Change |
| --- | ---: | ---: | ---: |
| Verified desktop FPS | unavailable | unavailable | — |
| Surface presentations/s | 62.74 | 62.74 | +0.00% |
| Mean inter-presentation time, ms | 15.939 | 15.939 | -0.00% |
| p95 inter-presentation time, ms | 16.481 | 16.682 | +1.22% |
| p99 inter-presentation time, ms | 16.586 | 17.070 | +2.92% |
| Simulated seconds / wall second | 2.2759 | 2.2703 | -0.25% |
| Accepted timesteps/s | 546.21 | 544.86 | -0.25% |
| Complete CUDA solver call, ms/step | 1.854 | 1.860 | +0.32% |
| Host snapshot copy, ms/step | 0.0039 | 0.0039 | -0.42% |
| CPU preparation, ms/frame | 0.102 | 0.081 | -20.21% |
| Vertex buffer creation/upload calls, CPU ms/frame | 0.367 | 0.369 | +0.47% |
| Render encoding/submission/polling, CPU ms/frame | 0.670 | 0.692 | +3.18% |
| Surface acquisition, CPU ms/frame | 0.003 | 0.003 | +5.63% |
| Presentation call, CPU ms/frame | 2.890 | 3.054 | +5.67% |
| Complete redraw, CPU ms/frame | 4.434 | 4.605 | +3.85% |
| GPU draw interval, ms/frame (separate profile) | 0.393 | 0.355 | -9.73% |
| CPU logical-core equivalents | 1.136 | 1.137 | +0.16% |
| Peak host RSS, MiB | 283.8 | 283.5 | -0.11% |
| Whole-device GPU utilisation, % | 47.2 | 47.1 | -0.2 |
| Whole-device VRAM used, MiB | 1200.0 | 1199.8 | -0.2 |
| Mean SM clock, MHz | 2805.0 | 2805.0 | +0.0 |
| Mean device power, W | 65.2 | 64.7 | -0.5 |
| Intervals over 33.3 ms, all three samples | 0 | 0 | — |

Vertex upload clocks include allocation, packing to bytes and driver calls; actual wgpu DMA duration was not independently measured. Device telemetry uses 200 ms whole-device readings across each invocation, including setup; the displayed value is the median of invocation means. CPU utilisation covers the observed running process interval and excludes most setup. Lower utilisation alone is not a speedup. GPU memory utilisation remained about 0%, 0.1% and 3% at the three sizes; memory clocks remained 10,251 MHz.

## 32,000 particles

| Measurement | Before | After | Change |
| --- | ---: | ---: | ---: |
| Verified desktop FPS | unavailable | unavailable | — |
| Surface presentations/s | 62.55 | 62.56 | +0.01% |
| Mean inter-presentation time, ms | 15.986 | 15.984 | -0.01% |
| p95 inter-presentation time, ms | 16.520 | 16.694 | +1.05% |
| p99 inter-presentation time, ms | 16.888 | 16.970 | +0.48% |
| Simulated seconds / wall second | 1.2367 | 1.2597 | +1.87% |
| Accepted timesteps/s | 296.80 | 302.34 | +1.87% |
| Complete CUDA solver call, ms/step | 3.375 | 3.318 | -1.70% |
| Host snapshot copy, ms/step | 0.0241 | 0.0188 | -21.92% |
| CPU preparation, ms/frame | 0.327 | 0.220 | -32.72% |
| Vertex buffer creation/upload calls, CPU ms/frame | 0.363 | 0.369 | +1.67% |
| Render encoding/submission/polling, CPU ms/frame | 0.630 | 0.622 | -1.33% |
| Surface acquisition, CPU ms/frame | 0.003 | 0.004 | +7.09% |
| Presentation call, CPU ms/frame | 3.063 | 2.980 | -2.71% |
| Complete redraw, CPU ms/frame | 4.795 | 4.591 | -4.26% |
| GPU draw interval, ms/frame (separate profile) | 1.718 | 1.583 | -7.89% |
| CPU logical-core equivalents | 1.144 | 1.134 | -0.82% |
| Peak host RSS, MiB | 290.5 | 289.4 | -0.39% |
| Whole-device GPU utilisation, % | 63.3 | 62.5 | -0.8 |
| Whole-device VRAM used, MiB | 1210.1 | 1210.6 | +0.5 |
| Mean SM clock, MHz | 2790.0 | 2790.0 | +0.0 |
| Mean device power, W | 112.1 | 109.5 | -2.6 |
| Intervals over 33.3 ms, all three samples | 0 | 0 | — |

Vertex upload clocks include allocation, packing to bytes and driver calls; actual wgpu DMA duration was not independently measured. Device telemetry uses 200 ms whole-device readings across each invocation, including setup; the displayed value is the median of invocation means. CPU utilisation covers the observed running process interval and excludes most setup. Lower utilisation alone is not a speedup. GPU memory utilisation remained about 0%, 0.1% and 3% at the three sizes; memory clocks remained 10,251 MHz.

## 110,592 particles

| Measurement | Before | After | Change |
| --- | ---: | ---: | ---: |
| Verified desktop FPS | unavailable | unavailable | — |
| Surface presentations/s | 62.38 | 62.37 | -0.01% |
| Mean inter-presentation time, ms | 16.032 | 16.034 | +0.01% |
| p95 inter-presentation time, ms | 17.051 | 17.189 | +0.81% |
| p99 inter-presentation time, ms | 17.529 | 17.646 | +0.67% |
| Simulated seconds / wall second | 0.2863 | 0.3131 | +9.39% |
| Accepted timesteps/s | 68.71 | 75.15 | +9.39% |
| Complete CUDA solver call, ms/step | 14.455 | 13.217 | -8.56% |
| Host snapshot copy, ms/step | 0.1107 | 0.1071 | -3.19% |
| CPU preparation, ms/frame | 1.058 | 0.733 | -30.72% |
| Vertex buffer creation/upload calls, CPU ms/frame | 0.502 | 0.451 | -10.16% |
| Render encoding/submission/polling, CPU ms/frame | 0.730 | 0.725 | -0.71% |
| Surface acquisition, CPU ms/frame | 0.005 | 0.005 | +2.45% |
| Presentation call, CPU ms/frame | 8.570 | 7.599 | -11.32% |
| Complete redraw, CPU ms/frame | 11.256 | 9.944 | -11.65% |
| GPU draw interval, ms/frame (separate profile) | 6.829 | 5.961 | -12.71% |
| CPU logical-core equivalents | 1.217 | 1.196 | -1.70% |
| Peak host RSS, MiB | 307.9 | 307.8 | -0.03% |
| Whole-device GPU utilisation, % | 84.7 | 83.9 | -0.8 |
| Whole-device VRAM used, MiB | 1273.5 | 1268.8 | -4.7 |
| Mean SM clock, MHz | 2775.3 | 2775.4 | +0.0 |
| Mean device power, W | 147.2 | 139.3 | -7.9 |
| Intervals over 33.3 ms, all three samples | 0 | 0 | — |

Vertex upload clocks include allocation, packing to bytes and driver calls; actual wgpu DMA duration was not independently measured. Device telemetry uses 200 ms whole-device readings across each invocation, including setup; the displayed value is the median of invocation means. CPU utilisation covers the observed running process interval and excludes most setup. Lower utilisation alone is not a speedup. GPU memory utilisation remained about 0%, 0.1% and 3% at the three sizes; memory clocks remained 10,251 MHz.

## Rejected persistent upload buffers

The second campaign compares indexed rendering with and without persistent upload buffers. It is separate from the indexed campaign and must not be pooled with it.

| Particles | Indexed simulation s/s | Persistent simulation s/s | Paired complete-command speedups | Decision |
| --- | ---: | ---: | --- | --- |
| 8,000 | 2.2365 | 2.1225 | 1.0157×, 0.9602×, 0.9330× | do not retain |
| 32,000 | 1.2597 | 1.2585 | 1.0092×, 0.9992×, 0.9859× | do not retain |
| 110,592 | 0.3138 | 0.3145 | 1.0009×, 0.9979×, 1.0022× | do not retain |
