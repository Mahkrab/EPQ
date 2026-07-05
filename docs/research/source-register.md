# Source Register

## Fluid simulation and graphics

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S001](sources/001-bridson-fluid-simulation-for-computer-graphics.md) | Bridson (2015) | Textbook | Primary practical reference for the continuum-fluid background, grid-based methods, pressure projection, advection, incompressibility and numerical trade-offs in graphics-oriented simulation. | [Official / DOI](https://doi.org/10.1201/9781315266008) |
| [S002](sources/002-stam-stable-fluids.md) | Stam (1999) | Peer-reviewed conference paper | Background comparison source for stable Eulerian, grid-based fluid simulation and the relationship between numerical stability, timestep selection and interactive performance. | [Official / DOI](https://doi.org/10.1145/311535.311548) |
| [S003](sources/003-muller-charypar-gross-particle-based-fluid-simulation.md) | Müller, Charypar and Gross (2003) | Peer-reviewed conference paper | Foundational source for particle-based, Smoothed Particle Hydrodynamics-style fluid simulation and neighbour interactions. | [Official / DOI](https://doi.org/10.5555/846276.846298) |
| [S004](sources/004-macklin-muller-position-based-fluids.md) | Macklin and Müller (2013) | Peer-reviewed journal paper | Core design reference for a position-based fluid constraint solver, density correction, solver iteration count and the trade-off between visual plausibility, stability and speed. | [Official / DOI](https://doi.org/10.1145/2461912.2461984) |

## Computational fluid dynamics

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S005](sources/005-ferziger-peric-street-computational-methods-for-fluid-dynamics.md) | Ferziger, Perić and Street (2020) | Advanced textbook | Theoretical reference for numerical discretisation, error, stability, convergence, boundary conditions and validation language in the report. | [Official / DOI](https://doi.org/10.1007/978-3-319-99693-6) |
| [S006](sources/006-versteeg-malalasekera-introduction-to-cfd.md) | Versteeg and Malalasekera (2007) | Textbook | Supporting background source for continuum governing equations, finite-volume concepts and the distinction between grid-based engineering CFD and Maelstrom’s particle-focused simulation. | [Official / DOI](https://books.google.com/books?id=RvBZ-UMpGzIC) |
| [S007](sources/007-nasa-glenn-navier-stokes-equation.md) | NASA Glenn Research Center (2024) | Official educational web resource | Plain-language introductory explanation of the variables represented in the three-dimensional unsteady Navier–Stokes equations. | [Official / DOI](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/navier-strokes-equation/) |

## Collisions and physics simulation

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S008](sources/008-ericson-real-time-collision-detection.md) | Ericson (2005) | Professional technical textbook | Practical reference for broad-phase versus narrow-phase collision detection, bounding volumes, robustness and real-time algorithm choices. | [Official / DOI](https://realtimecollisiondetection.net/) |
| [S009](sources/009-gilbert-johnson-keerthi-gjk.md) | Gilbert, Johnson and Keerthi (1988) | Peer-reviewed journal paper | Theoretical source for GJK distance and intersection queries between convex objects; useful as future collision-system context. | [Official / DOI](https://doi.org/10.1109/56.2083) |
| [S010](sources/010-baraff-non-penetrating-rigid-bodies.md) | Baraff (1989) | Peer-reviewed conference paper | Theoretical background for non-penetration constraints, rigid-body contact and the limitations of simple collision responses. | [Official / DOI](https://doi.org/10.1145/74334.74356) |

## Implementations and tools

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S011](sources/011-openfoam-v2606-user-guide.md) | OpenCFD (2026) | Official software documentation | Industry context and comparison point for case setup, mesh-based CFD workflows, parallel execution and validation expectations. | [Official / DOI](https://www.openfoam.com/documentation/user-guide) |
| [S012](sources/012-nvidia-cuda-programming-guide-release-13-2.md) | NVIDIA (2026) | Official technical documentation | Primary implementation reference for CUDA’s execution model, memory hierarchy, kernel launches, synchronisation and host–device data management. | [Official / DOI](https://docs.nvidia.com/cuda/archive/13.2.0/pdf/CUDA_C_Programming_Guide.pdf) |
| [S013](sources/013-macklin-muller-chentanez-kim-unified-particle-physics.md) | Macklin et al. (2014) | Peer-reviewed journal paper | Design and industry-context source for unified particle representations, position-based constraints, collisions and GPU-parallel real-time simulation. | [Official / DOI](https://doi.org/10.1145/2601097.2601152) |