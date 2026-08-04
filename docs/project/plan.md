# Maelstrom Development Plan

## Preparation: project and experimental design

Define the documentation stages, infastructure behind the code, and api's, tools and languages used. As well as standards and templating.

## Milestone 00: serial CPU brute-force reference

Create and verify the complete single-threaded CPU reference implementation using bruteforce neighbour search.

## Milestone 01: serial CPU uniform-grid optimisation

Replace bruteforce neighbour discovery with uniform-grid spatial partitioning while retaining the serial CPU execution and numerical reference contract.

## Milestone 02: multithreaded CPU implementation

Parallelise the uniform grid simulation on the CPU while retaining the same inputs, numerical behaviour and observable outputs.

## Milestone 03: CUDA GPU implementation

Implement the uniform grid simulation for CUDA-capable GPUs and preserve comparability with the CPU reference implementations.

## Milestone 04: application and visualisation integration

Integrate the verified simulation backends into the interactive application, renderer and reproducible offline-output workflow without coupling rendering to simulation correctness or benchmark timing.

## Milestone 05: comparative evaluation

Complete the controlled correctness, performance and scalability comparison across brute-force search, uniform-grid partitioning, CPU multithreading and CUDA acceleration, then evaluate the results against the research question.

