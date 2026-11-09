# Post-resume hardware check

This separate campaign tests the new hypothesis that the retained renderer still improves end-to-end throughput after machine-state variation. It does not replace the original alternating campaign. The final executable hash is unchanged (`967a6b53d1ed055f1d01d5ba36f35047a893064e3a09f312b5e334a3ae3ecacd`). Three large-scene pairs alternate AB/BA/AB; one diagnostic pair covers each smaller count. No clock, power, driver or system setting was changed.

| Particles | Variant | Sim s/wall s | Solver ms/step | Presents/s | Mean interval ms | p95 ms | p99 ms | CPU cores | GPU utilisation % | GPU MiB |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8,000 | indexed | 1.7256 | 2.445 | 62.062 | 16.113 | 18.023 | 18.825 | 1.166 | 47.80 | 2776.9 |
| 8,000 | impostor | 1.7792 | 2.379 | 62.095 | 16.104 | 19.462 | 22.047 | 1.157 | 44.93 | 2702.1 |
| 32,000 | indexed | 0.9348 | 4.459 | 61.969 | 16.137 | 17.705 | 18.290 | 1.159 | 60.11 | 2680.9 |
| 32,000 | impostor | 1.0611 | 3.919 | 61.978 | 16.135 | 17.649 | 18.573 | 1.174 | 57.04 | 2602.8 |
| 110,592 | indexed | 0.2423 | 17.053 | 61.895 | 16.156 | 18.142 | 19.204 | 1.196 | 84.55 | 2611.2 |
| 110,592 | impostor | 0.3842 | 10.758 | 61.919 | 16.150 | 17.525 | 18.111 | 1.212 | 74.76 | 2655.6 |

The large-scene median is 0.2423 → 0.3842 simulated s/wall s, a 58.6% improvement; individual ratios are 1.580×, 1.684× and 1.537×. Both renderers are slower than the original campaign. Thus the renderer benefit replicates, while the absolute rate is machine-state dependent. At 110,592, current-session throughput still needs approximately 2.60× improvement to reach real time.

The exact executable and native PTX match; graphics logs still identify hardware D3D12 on the RTX 4070, with similar GPU clocks. A short read-only clock diagnostic found monotonic and realtime deltas agreeing during five two-second intervals, while raw-clock deltas differed. It does not identify the cause or independently calibrate physical wall time. Host/virtualisation/load changes remain unresolved. No observation has been discarded and no numerical, scheduling or system change was made to recover a better number.

The strict capacity traces below use the same bounded accepted-step instrument and independent every-window reader as the original qualification. A failed second disqualifies the count even when its average exceeds one.

## Current-session capacity

| Particles | Repeat | Average sim s/wall s | Minimum steps in any second | Minimum sim s in any second | Pass |
| ---: | ---: | ---: | ---: | ---: | --- |
| 35,200 | 1 | 0.9929 | 201 | 0.837500 | False |
| 35,200 | 2 | 0.9773 | 219 | 0.912500 | False |
| 35,200 | 3 | 0.9887 | 214 | 0.891667 | False |
| 32,000 | 1 | 1.1166 | 255 | 1.062500 | True |
| 32,000 | 2 | 1.0493 | 218 | 0.908333 | False |
| 32,000 | 3 | 1.1362 | 260 | 1.083333 | True |
| 30,400 | 1 | 1.0702 | 238 | 0.991667 | False |
| 30,400 | 2 | 1.1361 | 240 | 1.000000 | True |
| 30,400 | 3 | 1.1099 | 248 | 1.033333 | True |
| 28,800 | 1 | 1.2024 | 268 | 1.116667 | True |
| 28,800 | 2 | 1.2158 | 273 | 1.137500 | True |
| 28,800 | 3 | 1.1921 | 266 | 1.108333 | True |

**28,800 is the highest count verified in this resumed session**, with all three complete 20-simulated-second runs passing every sliding one-second window. The next tested layer, 30,400, fails once (238 steps), despite averages above real time. At 32,000 one run also fails (218 steps); 35,200 fails in all three runs. These slower conditions do not support the earlier 38,400 qualification as a current guaranteed capacity. The original qualification remains valid evidence of that earlier measured machine state, not a substituted promise.

The whole-device GPU-memory level also changed from roughly 1.2 GiB in the initial campaign to roughly 2.6 GiB here. This confirms a different resource state, without identifying the cause of the slower execution. No system changes were made to pursue the earlier numbers.
