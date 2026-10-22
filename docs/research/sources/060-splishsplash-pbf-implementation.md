# S060 — Bender and contributors (n.d.)

## Full reference:

Bender, J. and contributors (n.d.) *SPlisHSPlasH*. Upstream README and
`SPlisHSPlasH/PBF/TimeStepPBF.cpp`, revision `7586ffa25948c6ce3bc6c238cda30ad8d35f60a0`.
Accessed 22 October 2026.

#### https://github.com/InteractiveComputerGraphics/SPlisHSPlasH/tree/7586ffa25948c6ce3bc6c238cda30ad8d35f60a0

## Relevance:

Runnable PBF comparator and implementation reference for the performance investigation.

## Reliability:

Primary upstream code, pinned for reproducibility. Source inspection establishes behaviour,
not independently measured performance or numerical equivalence with Maelstrom.

## Tags

`pbf`, `performance`, `comparison`, `open-source`

## Reading notes

- Read the pinned [README](https://github.com/InteractiveComputerGraphics/SPlisHSPlasH/blob/7586ffa25948c6ce3bc6c238cda30ad8d35f60a0/README.md)
  and [PBF implementation](https://github.com/InteractiveComputerGraphics/SPlisHSPlasH/blob/7586ffa25948c6ce3bc6c238cda30ad8d35f60a0/SPlisHSPlasH/PBF/TimeStepPBF.cpp).
- The PBF path uses OpenMP loops, minimum/maximum iterations and a density-error stopping condition.
  Its non-negative density constraint and boundary handling differ from Maelstrom.
- The README identifies several solver methods and separate CPU/GPU neighbourhood-search libraries.
  Selecting GPU search does not by itself establish a GPU-resident PBF solver.
- For the diagnosis on 22 October, also read pinned `Simulation.cpp`, `Simulator/SimulatorBase.cpp`,
  `CMakeLists.txt`, `CMake/Common.cmake`, `CMake/SetUpExternalProjects.cmake` and the double-dam-break scene.
  Method registration selects PBF at index 2; the sample scene instead selects DFSPH. Headless
  stopping and `SimStep` timing need explicit alignment before external comparison.
- Also inspected `FluidModel.cpp` and the bundled Partio `PTS.cpp` for the same-PC comparison.
  The pinned fluid mass is rest density times particle diameter cubed; Partio swaps Y/Z in PTS
  input. The diagnostic importer compensates for that swap and verifies actual readback coordinates.
  The simulator's printed iteration totals allow the eight-iteration workload to be counted;
  its `SimStep` timer excludes the separately invoked boundary simulator.

#### Date added

22/10/26
