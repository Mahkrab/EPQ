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

- On 10 November 2026, separately inspected release 2.19.1 at
  [`dba6b26b9387ab6bdd187d6df0a7c9d490d03500`](https://github.com/InteractiveComputerGraphics/SPlisHSPlasH/tree/dba6b26b9387ab6bdd187d6df0a7c9d490d03500)
  for the simulation-cache review. This does not replace the older comparator revision below.
  Read `Simulator/SimulatorBase.cpp`, particle Partio/VTK exporters, `Utilities/PartioReaderWriter.cpp`,
  `Tools/PartioViewer/PartioViewer.cpp`, bundled Partio `BGEO.cpp`, and the exporter, getting-started,
  replicability and PartioViewer documentation. `SimulatorBase::step` schedules particle and state
  exports independently by time; Partio copies position, ID and selected fields before optionally
  launching one asynchronous write. The bundled writer emits gzip-capable, big-endian BGEO v5.
  VTK output is a binary legacy unstructured grid with vertex cells and attributes.
  `saveState` adds scheduling, parameters, time-manager and simulation state to particle files;
  `loadState` checks a scene-file MD5 and warns on disagreement. This is not a portable checkpoint guarantee.
  PartioViewer reads the saved sequence and generates JPEGs or pipes RGB frames to ffmpeg;
  its inspected generation loops are sequential. No upstream throughput benchmark was run.
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
