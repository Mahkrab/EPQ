# Completed CUDA and CPU solver comparison

Fixed settings: serial grid, twelve CPU workers, CUDA device 0 / 128 lanes. Same release binary.
Ratios divide each fresh CPU median by the CUDA median. Values below one mean CUDA is slower.
Exact component checks qualify all admitted observations. No fresh brute-force ratio is available.

| Particles | Series | Solver median (s) | Min–max (s) | Invocation median (s) | Construction median (s) | Teardown median (s) | CPU/CUDA |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | serial-grid | 0.328366 | 0.327064–0.328872 | 0.332918 | 0.000003 | 0.000001 | 0.164722 |
| 64 | threaded-grid | 8.426217 | 8.414887–8.454735 | 8.432605 | 0.000743 | 0.000296 | 4.226940 |
| 64 | cuda-grid | 1.993456 | 1.987259–1.995058 | 2.192050 | 0.149669 | 0.037092 | 1.000000 |
| 216 | serial-grid | 1.255364 | 1.254682–1.264304 | 1.263483 | 0.000003 | 0.000001 | 0.544091 |
| 216 | threaded-grid | 8.417105 | 8.405137–8.545483 | 8.427107 | 0.000764 | 0.000306 | 3.648084 |
| 216 | cuda-grid | 2.307267 | 2.293522–2.311990 | 2.514276 | 0.153766 | 0.037491 | 1.000000 |
| 512 | serial-grid | 3.181563 | 3.177425–3.185851 | 3.197286 | 0.000004 | 0.000001 | 1.229949 |
| 512 | threaded-grid | 7.330407 | 7.270381–7.359987 | 7.347805 | 0.000837 | 0.000276 | 2.833836 |
| 512 | cuda-grid | 2.586743 | 2.567660–2.588485 | 2.795865 | 0.151500 | 0.037689 | 1.000000 |
| 1,000 | serial-grid | 6.815932 | 6.598518–6.832208 | 6.850313 | 0.000023 | 0.000001 | 2.247159 |
| 1,000 | threaded-grid | 6.948293 | 6.940534–6.971709 | 6.983224 | 0.000946 | 0.000310 | 2.290797 |
| 1,000 | cuda-grid | 3.033133 | 3.020671–3.040207 | 3.267609 | 0.153056 | 0.037387 | 1.000000 |
| 1,728 | serial-grid | 12.484920 | 12.469283–12.555184 | 12.552166 | 0.000037 | 0.000001 | 3.670390 |
| 1,728 | threaded-grid | 7.997439 | 7.965664–8.014916 | 8.066243 | 0.000787 | 0.000340 | 2.351134 |
| 1,728 | cuda-grid | 3.401524 | 3.389463–3.409699 | 3.671185 | 0.149680 | 0.037728 | 1.000000 |
| 4,096 | serial-grid | 31.378775 | 31.315133–31.459459 | 31.623307 | 0.000081 | 0.000001 | 6.683782 |
| 4,096 | threaded-grid | 12.681015 | 12.670127–12.692886 | 12.935936 | 0.000923 | 0.000357 | 2.701098 |
| 4,096 | cuda-grid | 4.694764 | 4.688675–4.702762 | 5.152416 | 0.157309 | 0.038158 | 1.000000 |
| 8,000 | serial-grid | 63.791997 | 63.777887–63.808944 | 64.567721 | 0.000153 | 0.000002 | 8.381349 |
| 8,000 | threaded-grid | 21.519382 | 21.515115–21.579094 | 22.332216 | 0.000989 | 0.000379 | 2.827337 |
| 8,000 | cuda-grid | 7.611185 | 7.579296–7.632092 | 8.623839 | 0.152743 | 0.038824 | 1.000000 |

Per-series reports retain throughput, spread, synchronised host stage profiles and residuals.
Setup and teardown remain outside completed-step totals; first-step buffer allocations remain inside.
Invocation includes audits, output and process costs. Profiles are not isolated device timings.
Fixed order, shared host load, thermals and scheduling remain uncontrolled; three samples show observed spread.
Memory use, bandwidth and utilisation were not measured. No tuning or numerical changes were made.
