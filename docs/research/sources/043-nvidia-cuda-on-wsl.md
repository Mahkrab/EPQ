# S043 — NVIDIA (2026)

## Full reference:

NVIDIA (2026) *CUDA on WSL User Guide*. Version 13.3. Santa Clara, CA: NVIDIA.

#### https://docs.nvidia.com/cuda/wsl-user-guide/

## Relevance:

Explains how the Windows NVIDIA driver exposes CUDA to WSL 2 through `libcuda.so` and why a second Linux display driver must not be installed inside WSL. This supports the documented driver and toolkit architecture.

## Reliability:

This is NVIDIA's official product documentation for CUDA on WSL and is authoritative for the supported driver arrangement. It is version-specific and should be rechecked when CUDA or WSL is upgraded.

## Tags

`cuda`, `wsl2`, `nvidia-driver`, `libcuda`

## Reading notes

- The Windows NVIDIA driver is exposed inside WSL 2 as `libcuda.so`.
- NVIDIA instructs WSL users not to install a separate Linux display driver.
- A Linux CUDA Toolkit is still required to compile CUDA applications inside WSL.

#### Date added

21/07/26
