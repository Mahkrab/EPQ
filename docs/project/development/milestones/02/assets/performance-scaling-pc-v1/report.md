# CPU worker scaling on the primary PC

CPU: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS.
Maelstrom: `60b9a767636428a26f39a1901e2cac4276c75c83`; binary SHA-256: `1f737d1dfd2c0d6bfe58ef2f39873287b2722f1737dbcdd75ba41fafc7320c29`.
Available parallelism selected by Rust: 24; inherited affinity: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23].
Collection order: serial-grid, workers-1, workers-2, workers-4, workers-8, workers-12, workers-24. Each series uses ascending sizes and the unchanged `serial-baseline-v1` policy.

All clean complete attempts must equal the same-size serial-grid warm-up exactly, including sign-sensitive
snapshot hashes, physical identities, checkpoints, density audits, CFL diagnostics and completion.
Each full 64-particle correctness result is also checked against its frozen golden.
An unequal hash rejects acceptance; no tolerance is inferred from compact data.

| Particles | Series | Median solver s | Min–max s | SD s | Updates/s | Median invocation s | vs serial grid | vs one worker | Efficiency | Exact attempts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | serial-grid | 0.327190 | 0.326972–0.328425 | 0.000784 | 93,890 | 0.331241 | 1.000 | unavailable | unavailable | 5 |
| 64 | workers-1 | 0.625012 | 0.618184–0.629566 | 0.005729 | 49,151 | 0.629164 | 0.523 | 1.000 | 1.000 | 5 |
| 64 | workers-2 | 0.561333 | 0.552165–0.568404 | 0.008142 | 54,727 | 0.565550 | 0.583 | 1.113 | 0.557 | 5 |
| 64 | workers-4 | 0.985097 | 0.949804–1.009898 | 0.030199 | 31,185 | 0.989979 | 0.332 | 0.634 | 0.159 | 5 |
| 64 | workers-8 | 4.837695 | 4.807344–4.863606 | 0.028160 | 6,350 | 4.843278 | 0.068 | 0.129 | 0.016 | 5 |
| 64 | workers-12 | 8.376671 | 8.315117–8.404229 | 0.045624 | 3,667 | 8.382411 | 0.039 | 0.075 | 0.006 | 5 |
| 64 | workers-24 | 15.896396 | 15.893162–16.289763 | 0.228050 | 1,933 | 15.903212 | 0.021 | 0.039 | 0.002 | 5 |
| 216 | serial-grid | 1.263188 | 1.252578–1.287661 | 0.017992 | 82,078 | 1.270859 | 1.000 | unavailable | unavailable | 5 |
| 216 | workers-1 | 1.637440 | 1.633477–1.639652 | 0.003128 | 63,318 | 1.644955 | 0.771 | 1.000 | 1.000 | 5 |
| 216 | workers-2 | 1.224147 | 1.221276–1.272572 | 0.028823 | 84,696 | 1.231961 | 1.032 | 1.338 | 0.669 | 5 |
| 216 | workers-4 | 1.461917 | 1.453903–1.500685 | 0.025019 | 70,921 | 1.470375 | 0.864 | 1.120 | 0.280 | 5 |
| 216 | workers-8 | 4.378485 | 4.342946–4.468238 | 0.064571 | 23,679 | 4.387531 | 0.288 | 0.374 | 0.047 | 5 |
| 216 | workers-12 | 8.316038 | 8.308469–8.342033 | 0.017605 | 12,467 | 8.325380 | 0.152 | 0.197 | 0.016 | 5 |
| 216 | workers-24 | 16.558731 | 16.501569–16.662565 | 0.081618 | 6,261 | 16.569179 | 0.076 | 0.099 | 0.004 | 5 |
| 512 | serial-grid | 3.281100 | 3.176648–3.299343 | 0.066203 | 74,902 | 3.296206 | 1.000 | unavailable | unavailable | 5 |
| 512 | workers-1 | 3.792018 | 3.787971–3.795850 | 0.003940 | 64,810 | 3.811739 | 0.865 | 1.000 | 1.000 | 5 |
| 512 | workers-2 | 2.486010 | 2.456353–2.498533 | 0.021662 | 98,857 | 2.502349 | 1.320 | 1.525 | 0.763 | 5 |
| 512 | workers-4 | 2.314932 | 2.313084–2.336095 | 0.012786 | 106,163 | 2.330967 | 1.417 | 1.638 | 0.410 | 5 |
| 512 | workers-8 | 4.191353 | 4.187075–4.193091 | 0.003097 | 58,635 | 4.210523 | 0.783 | 0.905 | 0.113 | 5 |
| 512 | workers-12 | 7.303769 | 7.225485–7.311355 | 0.047539 | 33,648 | 7.321164 | 0.449 | 0.519 | 0.043 | 5 |
| 512 | workers-24 | 13.446401 | 13.274090–13.620330 | 0.173121 | 18,277 | 13.467987 | 0.244 | 0.282 | 0.012 | 5 |
| 1,000 | serial-grid | 6.842994 | 6.733264–6.864893 | 0.070529 | 70,145 | 6.874749 | 1.000 | unavailable | unavailable | 5 |
| 1,000 | workers-1 | 7.710107 | 7.690247–7.721428 | 0.015784 | 62,256 | 7.744033 | 0.888 | 1.000 | 1.000 | 5 |
| 1,000 | workers-2 | 4.742361 | 4.727722–4.782998 | 0.028639 | 101,215 | 4.776335 | 1.443 | 1.626 | 0.813 | 5 |
| 1,000 | workers-4 | 3.830030 | 3.799476–3.842606 | 0.022181 | 125,325 | 3.862741 | 1.787 | 2.013 | 0.503 | 5 |
| 1,000 | workers-8 | 5.132384 | 5.101920–5.164133 | 0.031109 | 93,524 | 5.168629 | 1.333 | 1.502 | 0.188 | 5 |
| 1,000 | workers-12 | 6.865027 | 6.839273–6.877721 | 0.019590 | 69,920 | 6.900729 | 0.997 | 1.123 | 0.094 | 5 |
| 1,000 | workers-24 | 12.057045 | 11.882381–12.064994 | 0.103214 | 39,811 | 12.094228 | 0.568 | 0.639 | 0.027 | 5 |
| 1,728 | serial-grid | 12.508839 | 12.436995–12.867378 | 0.230558 | 66,308 | 12.575463 | 1.000 | unavailable | unavailable | 5 |
| 1,728 | workers-1 | 13.670132 | 13.603502–13.900543 | 0.155864 | 60,675 | 13.736614 | 0.915 | 1.000 | 1.000 | 5 |
| 1,728 | workers-2 | 8.370698 | 8.356692–8.437084 | 0.042946 | 99,089 | 8.439555 | 1.494 | 1.633 | 0.817 | 5 |
| 1,728 | workers-4 | 6.156865 | 6.139331–6.172918 | 0.016799 | 134,718 | 6.225454 | 2.032 | 2.220 | 0.555 | 5 |
| 1,728 | workers-8 | 6.821368 | 6.812556–6.862763 | 0.026808 | 121,594 | 6.893441 | 1.834 | 2.004 | 0.251 | 5 |
| 1,728 | workers-12 | 7.906639 | 7.872166–7.910976 | 0.021266 | 104,904 | 7.977473 | 1.582 | 1.729 | 0.144 | 5 |
| 1,728 | workers-24 | 12.530067 | 12.518484–12.957187 | 0.250009 | 66,196 | 12.603521 | 0.998 | 1.091 | 0.045 | 5 |
| 4,096 | serial-grid | 30.966757 | 30.786611–31.620976 | 0.439056 | 63,490 | 31.222284 | 1.000 | unavailable | unavailable | 5 |
| 4,096 | workers-1 | 32.793518 | 32.747059–32.811241 | 0.033146 | 59,953 | 33.048435 | 0.944 | 1.000 | 1.000 | 5 |
| 4,096 | workers-2 | 19.833324 | 19.660760–19.878105 | 0.114763 | 99,130 | 20.090063 | 1.561 | 1.653 | 0.827 | 5 |
| 4,096 | workers-4 | 13.579018 | 13.576543–13.624287 | 0.026879 | 144,788 | 13.836703 | 2.280 | 2.415 | 0.604 | 5 |
| 4,096 | workers-8 | 12.897303 | 12.641621–12.901488 | 0.148841 | 152,441 | 13.161762 | 2.401 | 2.543 | 0.318 | 5 |
| 4,096 | workers-12 | 12.634991 | 12.609318–12.670814 | 0.030887 | 155,606 | 12.899566 | 2.451 | 2.595 | 0.216 | 5 |
| 4,096 | workers-24 | 16.583034 | 16.434477–16.591471 | 0.088306 | 118,560 | 16.849782 | 1.867 | 1.978 | 0.082 | 5 |
| 8,000 | serial-grid | 64.527357 | 62.904964–64.913885 | 1.065937 | 59,510 | 65.333919 | 1.000 | unavailable | unavailable | 5 |
| 8,000 | workers-1 | 65.606625 | 65.593613–65.646354 | 0.027475 | 58,531 | 66.434382 | 0.984 | 1.000 | 1.000 | 5 |
| 8,000 | workers-2 | 39.021825 | 39.011792–39.026205 | 0.007389 | 98,406 | 39.861267 | 1.654 | 1.681 | 0.841 | 5 |
| 8,000 | workers-4 | 26.301695 | 26.241072–26.453071 | 0.109189 | 145,998 | 27.143067 | 2.453 | 2.494 | 0.624 | 5 |
| 8,000 | workers-8 | 23.242135 | 23.127404–23.251506 | 0.069104 | 165,217 | 24.090733 | 2.776 | 2.823 | 0.353 | 5 |
| 8,000 | workers-12 | 21.592798 | 21.564121–21.594882 | 0.017190 | 177,837 | 22.446165 | 2.988 | 3.038 | 0.253 | 5 |
| 8,000 | workers-24 | 27.019083 | 26.982083–27.100183 | 0.060407 | 142,122 | 27.885199 | 2.388 | 2.428 | 0.101 | 5 |

Speedup divides the fresh serial-grid median by the selected median. Scaling divides the threaded
one-worker median by that median; efficiency divides scaling by requested workers, not physical cores.
Effective pool size equals the explicit request after successful construction; this does not guarantee simultaneous CPU service.
The serial row's speedup is 1. Profiles, stage seconds/proportions/residuals and all partial attempts are retained
in each series report and dataset. Profiles do not enter primary ratios. Invocation time includes setup, audits and output.
One-time pool setup/teardown is outside solver timing; dispatch, barriers, validation and repeated allocation are inside.
No fresh brute-force series was collected, so these results support no overall gain ratio against brute force.
Fixed order, host load, scheduling and thermals remain confounders. Three samples do not establish significance.
No memory measurement, larger-size campaign, physical-accuracy or universal scaling claim is made.
