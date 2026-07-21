# S048 — NVIDIA (2026)

## Full reference:

NVIDIA (2026) *CUDA Installation Guide for Linux*. Version 13.3. Santa Clara, CA: NVIDIA.

#### https://docs.nvidia.com/cuda/cuda-installation-guide-linux/

## Relevance:

Supports the documented CUDA Toolkit installation paths, `/usr/local/cuda` symbolic link and environment configuration used to select one active toolkit version.

## Reliability:

This is NVIDIA's official CUDA installation guide for Linux and is authoritative for the CUDA 13.3 installation layout and post-installation environment setup.

## Tags

`cuda`, `linux`, `installation`, `toolkit-path`

## Reading notes

- Versioned CUDA Toolkits are normally installed beneath `/usr/local`.
- `/usr/local/cuda` can point to the selected Toolkit installation.
- Executable and library paths must expose the selected Toolkit to development tools.

#### Date added

21/07/26
