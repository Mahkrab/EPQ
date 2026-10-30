# S070 — Barnden (n.d.)

## Full reference:

Barnden (GitHub account) (n.d.) *Position Based Fluids*. CUDA implementation,
revision `ca191d40d937a1ea44bae4032d087ac2902f9846`. Accessed 28 October 2026.

#### https://github.com/barnden/pbf/tree/ca191d40d937a1ea44bae4032d087ac2902f9846

## Relevance:

Independent CUDA PBF numerical and neighbourhood implementation for a same-device
headless comparison and inspection of execution, ordering and precision choices.

## Reliability:

Primary source code for a student implementation, rather than a peer-reviewed
accuracy or performance result. Its README says the original renderer does not
work with WSLg CUDA/OpenGL interoperation. Source inspection found missing
density self-contribution, bounded neighbour rows and previous-position search.
A separately identified adapter is necessary; running it does not establish
physical equivalence with Maelstrom. No licence file was present in the pinned
archive; the investigation retains identities and adaptation instructions rather
than importing its implementation into Maelstrom or redistributing that archive.

## Tags

`pbf`, `cuda`, `independent-comparator`, `performance`

## Reading notes

- Read the pinned README, simulation and sorting orchestration, particle storage,
  parameters, hash, Poly6/Spiky, integration, neighbour, constraint, correction,
  projection and velocity/effect kernels.
- Constraint and correction are separate launches with a complete projection
  launch between iterations. The solver is Jacobi despite the orchestration's
  Gauss-Seidel comment.
- The constraint loop starts density at zero and skips self. Neighbour finding
  reads old positions, accepts the support boundary, and caps each row at 255
  neighbours in the original configuration. It does not sort by particle identity.
- Hash buckets are filtered by distance but not by queried-cell identity; aliases
  among queried cells can therefore visit a particle more than once.
- It uses float3 arrays and native powf. Its timestep completes on the device;
  routine CPU-owned particle snapshots and Maelstrom's ordered error/cancellation
  boundaries are absent.
- The upstream constructor performs 360 damped relaxation steps. The matched
  adapter omits that preparation so it starts from the retained initial particles,
  and increases neighbour row capacity from 256 to 512 entries.
- The headless experiment supplies independent runtime allocations in place of
  the OpenGL-backed particle class. It records a grid sentinel/compile-compatibility
  repair and explicitly separates original formulas from aligned self/support/
  prediction-time membership. Further measurements belong to the experiment
  record, not to claims about upstream performance.

#### Date added

28/10/26
