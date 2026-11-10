# Reviewed complete-step attribution

All tables are diagnostic, including instrumentation overhead. Kernel durations
are GPU intervals; API durations overlap them. Values must not be added across
those categories. Source and binary identities are in `checks/`.

## 8000 particles

| Component, ms/step | Control | Reviewed |
| --- | ---: | ---: |
| complete_ms_per_step | 2.432711 | 2.568282 |
| solver_gpu_ms_per_step | 0.924996 | 0.928443 |
| without_solver_gpu_ms_per_step | 1.507715 | 1.639839 |
| worker_publication_ms | 0.007455 | 0.007780 |
| GPU acceleration summary | 0.001853 | 0.001878 |
| GPU candidate | 0.011493 | 0.011445 |
| GPU cell keys | 0.003239 | 0.003293 |
| GPU correction | 0.295506 | 0.295411 |
| GPU density and lambda | 0.270740 | 0.271688 |
| GPU lambda publication | 0.011638 | 0.011509 |
| GPU neighbour count | 0.109742 | 0.109484 |
| GPU neighbour fill | 0.118876 | 0.122025 |
| GPU physical density check | 0.012320 | 0.012248 |
| GPU plane projection | 0.018766 | 0.018535 |
| GPU prediction summary | 0.002132 | 0.002121 |
| GPU row prefix | 0.004726 | 0.004725 |
| GPU row sort | 0.006373 | 0.006779 |
| GPU spatial sort | 0.042929 | 0.042693 |
| GPU velocity and containment | 0.002222 | 0.002192 |

| API | Control inclusive / without GPU ms | Reviewed inclusive / without GPU ms |
| --- | ---: | ---: |
| api:cuLaunchKernel | 0.201152 / 0.147710 | 0.204155 / 0.160199 |
| api:cuStreamSynchronize | 1.895656 / 1.064423 | 2.002328 / 1.157716 |
| api:cuMemcpyDtoH_v2 | 0.219610 / 0.202681 | 0.243768 / 0.227893 |

| Steps | Control density / correction / neighbour count+fill ms | Reviewed density / correction / neighbour count+fill ms |
| --- | --- | --- |
| 1-240 | 0.276893 / 0.314373 / 0.287132 | 0.276252 / 0.313133 / 0.289274 |
| 241-480 | 0.271260 / 0.293613 / 0.219901 | 0.272571 / 0.293885 / 0.222970 |
| 481-1200 | 0.268515 / 0.289849 / 0.212019 | 0.269872 / 0.290012 / 0.215101 |

## 32000 particles

| Component, ms/step | Control | Reviewed |
| --- | ---: | ---: |
| complete_ms_per_step | 3.899676 | 3.629800 |
| solver_gpu_ms_per_step | 1.971150 | 1.765218 |
| without_solver_gpu_ms_per_step | 1.928525 | 1.864583 |
| worker_publication_ms | 0.044078 | 0.042781 |
| GPU acceleration summary | 0.002259 | 0.002265 |
| GPU candidate | 0.015577 | 0.015623 |
| GPU cell keys | 0.008030 | 0.008059 |
| GPU correction | 0.637282 | 0.530662 |
| GPU density and lambda | 0.629756 | 0.456019 |
| GPU lambda publication | 0.014635 | 0.014618 |
| GPU neighbour count | 0.218422 | 0.218169 |
| GPU neighbour fill | 0.240154 | 0.272027 |
| GPU physical density check | 0.013784 | 0.013744 |
| GPU plane projection | 0.022723 | 0.022815 |
| GPU prediction summary | 0.003053 | 0.003043 |
| GPU row prefix | 0.005308 | 0.005327 |
| GPU row sort | 0.044193 | 0.070257 |
| GPU spatial sort | 0.076859 | 0.076621 |
| GPU tile prefix | 0.000000 | 0.016906 |
| GPU velocity and containment | 0.002653 | 0.002650 |

| API | Control inclusive / without GPU ms | Reviewed inclusive / without GPU ms |
| --- | ---: | ---: |
| api:cuLaunchKernel | 0.233930 / 0.145475 | 0.236036 / 0.180140 |
| api:cuStreamSynchronize | 3.077792 / 1.273909 | 2.805170 / 1.171198 |
| api:cuMemcpyDtoH_v2 | 0.301672 / 0.256790 | 0.299026 / 0.257999 |

| Steps | Control density / correction / neighbour count+fill ms | Reviewed density / correction / neighbour count+fill ms |
| --- | --- | --- |
| 1-240 | 0.480545 / 0.549468 / 0.423435 | 0.441470 / 0.541930 / 0.434989 |
| 241-480 | 0.590103 / 0.592778 / 0.430680 | 0.447442 / 0.516344 / 0.450185 |
| 481-1200 | 0.692711 / 0.681388 / 0.479588 | 0.463727 / 0.531679 / 0.521936 |

## 110592 particles

| Component, ms/step | Control | Reviewed |
| --- | ---: | ---: |
| complete_ms_per_step | 11.085136 | 9.023204 |
| solver_gpu_ms_per_step | 7.517603 | 5.814602 |
| without_solver_gpu_ms_per_step | 3.567533 | 3.208602 |
| worker_publication_ms | 0.534885 | 0.368211 |
| GPU acceleration summary | 0.004443 | 0.004452 |
| GPU candidate | 0.027417 | 0.028102 |
| GPU cell keys | 0.020805 | 0.020908 |
| GPU correction | 2.483659 | 1.880772 |
| GPU density and lambda | 2.857377 | 1.377107 |
| GPU lambda publication | 0.026116 | 0.025179 |
| GPU neighbour count | 0.701574 | 0.752421 |
| GPU neighbour fill | 0.846011 | 0.924909 |
| GPU physical density check | 0.023475 | 0.024565 |
| GPU plane projection | 0.047063 | 0.047296 |
| GPU prediction summary | 0.007064 | 0.007040 |
| GPU row prefix | 0.008497 | 0.008413 |
| GPU row sort | 0.100204 | 0.281889 |
| GPU spatial sort | 0.236574 | 0.237363 |
| GPU tile prefix | 0.000000 | 0.066089 |
| GPU velocity and containment | 0.006366 | 0.006924 |

| API | Control inclusive / without GPU ms | Reviewed inclusive / without GPU ms |
| --- | ---: | ---: |
| api:cuLaunchKernel | 0.281810 / 0.231817 | 0.289811 / 0.205128 |
| api:cuStreamSynchronize | 8.707769 / 1.418456 | 6.941051 / 1.403018 |
| api:cuMemcpyDtoH_v2 | 0.563359 / 0.438861 | 0.527251 / 0.397953 |

| Steps | Control density / correction / neighbour count+fill ms | Reviewed density / correction / neighbour count+fill ms |
| --- | --- | --- |
| 1-240 | 2.050283 / 1.860778 / 1.230978 | 1.165830 / 1.702443 / 1.362432 |
| 241-480 | 2.866019 / 2.446328 / 1.487846 | 1.358361 / 1.877381 / 1.652542 |
| 481-1200 | 3.123528 / 2.703729 / 1.673034 | 1.453781 / 1.941345 / 1.790558 |

