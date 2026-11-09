# Visual difference measurements

Medians of twelve matched stills per count, compared with indexed spheres. RGB RMSE uses 8-bit channel units. Foreground is the union of non-background pixels, including boundary outlines; full-frame errors can be diluted by sparse backgrounds. An identical image has infinite PSNR. Individual edge changes can reach 255 in a channel.

| Particles | Candidate | Image pixels changed, % | Foreground pixels changed, % | Foreground RGB RMSE / 255 | Full-frame PSNR, dB |
| ---: | --- | ---: | ---: | ---: | ---: |
| 8,000 | low | 3.73 | 53.10 | 10.54 | 38.59 |
| 8,000 | impostor | 2.15 | 30.75 | 5.88 | 43.76 |
| 8,000 | adaptive | 1.01 | 27.31 | 5.90 | 45.17 |
| 32,000 | low | 6.46 | 55.56 | 9.97 | 37.06 |
| 32,000 | impostor | 4.02 | 33.69 | 5.74 | 41.71 |
| 32,000 | adaptive | 1.78 | 27.67 | 5.73 | 44.49 |
| 110,592 | low | 10.47 | 55.61 | 9.96 | 34.81 |
| 110,592 | impostor | 6.30 | 33.67 | 5.68 | 39.55 |
| 110,592 | adaptive | 3.47 | 26.81 | 5.77 | 41.71 |
