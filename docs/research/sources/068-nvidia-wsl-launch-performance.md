# S068 — Boissel and Sundaram (2021)

## Full reference:

Boissel, R. and Sundaram, A. (2021) ‘Leveling up CUDA Performance on WSL2 with New Enhancements’,
*NVIDIA Technical Blog*, 10 August. Accessed 26 October 2026.

#### https://developer.nvidia.com/blog/leveling-up-cuda-performance-on-wsl2-with-new-enhancements/

## Relevance:

Explains why repeated short CUDA submissions and completion observations merit examination
in Maelstrom's WSL2 architecture.

## Reliability:

Primary vendor engineering account. Its 2021 driver measurements are historical and do not
quantify the project's 2026 hardware/software overhead or establish a Maelstrom speedup.

## Tags

`cuda`, `wsl2`, `launch-latency`, `performance`

## Reading notes

- Read the article body, including launch latency and asynchronous submission sections.
- It distinguishes submission from end-to-end launch/completion overhead and explains why
  sufficiently pipelined work can hide costs exposed by short sequential requests.
- No published percentage is transferred to Maelstrom.

#### Date added

26/10/26
