# S045 — NVIDIA (2026)

## Full reference:

NVIDIA (2026) *NVIDIA CUDA Compiler Driver NVCC*. Version 13.3. Santa Clara, CA: NVIDIA.

#### https://docs.nvidia.com/cuda/archive/13.3.0/cuda-compiler-driver-nvcc/index.html

## Relevance:

Defines the `nvcc` compiler driver used to compile the standalone CUDA C++ test and later integrate CUDA source compilation into the project build.

## Reliability:

This is NVIDIA's official compiler-driver documentation and is authoritative for CUDA 13.3 compilation phases, inputs and command-line options.

## Tags

`cuda`, `nvcc`, `compiler`, `cuda-cpp`

## Reading notes

- `nvcc` compiles CUDA C++ source through host and device compilation phases.
- The `-o` option selects the output file produced by the compilation command.
- On 24 October 2026, checked the archived 13.3 guide, §4.2.8.16:
  `--resource-usage` reports registers and memory. The project's PTX-only build
  still needs separate checks of driver-loaded kernel resources.

- On 25 October 2026, checked §§4.2.3.13–15 and 4.2.7.7–11: `-O` selects host
  optimisation; device optimisation is implicit without `-G`. Fast maths changes
  denormal handling, division/square-root precision and multiply-add contraction.

#### Date added

21/07/26
