# Paired serial brute-force and uniform-grid measurements

Policy: `serial-baseline-v1`; exact serial acceptance: `reference-comparison-v1`.
CPU: AMD Ryzen 9 7900X 12-Core Processor; Ubuntu 24.04.5 LTS.
Source: `b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1`; tree SHA-256: `0709e7886673749eb9d4986b732479eedbc09127a3fb618a43526210e050dbd6`.
Collection: 2026-10-17T16:18:26.981628+00:00 to 2026-10-17T16:39:12.438593+00:00.

Brute force was collected first, then the grid, using one binary and unchanged inputs.
Each series retains one warm-up, three total-only samples and a separate profile per size.
Every clean full attempt is checked against the brute-force warm-up at that size, including
sign-sensitive hashes of all particle snapshots, physical inputs, audits, CFL and completion.
A missing clean primary set or reference prevents a speedup ratio.

| Particles | Brute force median (s) | Grid median (s) | Speedup | Exact complete attempts |
| ---: | ---: | ---: | ---: | ---: |
| 64 | 0.256858 | 0.268774 | 0.956× | 10 |
| 216 | 1.040863 | 1.097272 | 0.949× | 10 |
| 512 | 2.659407 | 2.673178 | 0.995× | 10 |
| 1,000 | 5.905200 | 5.921604 | 0.997× | 10 |
| 1,728 | 11.568858 | 10.851780 | 1.066× | 10 |
| 4,096 | 34.933192 | 26.231439 | 1.332× | 10 |
| 8,000 | 90.021109 | 55.621480 | 1.618× | 10 |

Raw totals, min–max ranges, sample standard deviations, throughput, profiles and every
failed/partial attempt remain in the two backend reports and their hashed raw indexes.
Profiles contain extra clocks and do not supply the primary speedup. Memory was not measured.
The fixed collection order, shared host load, scheduling and thermal state remain confounders;
three samples show observed variability, not statistical significance or a universal crossover.
