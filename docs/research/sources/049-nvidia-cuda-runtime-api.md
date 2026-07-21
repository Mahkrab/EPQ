# S049 — NVIDIA (2026)

## Full reference:

NVIDIA (2026) *CUDA Runtime API*. Version 13.3.1. Santa Clara, CA: NVIDIA.

#### https://docs.nvidia.com/cuda/cuda-runtime-api/

## Relevance:

Defines the runtime functions used by the verification program for device discovery, GPU allocation, host-device copies, synchronisation, error handling and memory release.

## Reliability:

This is NVIDIA's official API reference for CUDA 13.3.1 and is authoritative for the documented runtime functions and their behaviour.

## Tags

`cuda`, `runtime-api`, `gpu-memory`, `kernel`

## Reading notes

- The Runtime API provides device-management, execution-control and memory-management functions.
- The test uses this API to allocate memory, copy values between host and device, synchronise execution and free the allocation.

#### Date added

21/07/26
