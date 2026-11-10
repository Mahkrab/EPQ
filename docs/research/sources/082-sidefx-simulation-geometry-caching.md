# S082 — SideFX (n.d.)

## Full reference:

SideFX (n.d.) *File Cache 2.0; Caching simulations; USD Render*. Houdini online documentation,
displaying Houdini 22.0 when accessed on 10 November 2026.

#### https://www.sidefx.com/docs/houdini/nodes/sop/filecache.html

## Relevance:

Separates dependent simulation sequences, reusable geometry and independent rendering in the
Maelstrom cache review. These are documented product behaviours; Houdini's proprietary solver
and cache implementation were not inspected or benchmarked.

## Reliability:

Official vendor documentation. It establishes supported workflows and parameters, not the
internal scheduler, filesystem durability or performance on Maelstrom's PC. Online pages can change.

## Tags

`cache`, `houdini`, `checkpoints`, `rendering`

## Reading notes

- File Cache writes geometry and subsequently loads it from disk. Its Simulation option preserves
  frame dependencies; independent frames can cook in parallel. Frame increments and subframes
  are distinct from simulation substeps. Versioned `.bgeo.sc` paths are the documented default.
- [Caching simulations](https://www.sidefx.com/docs/houdini/dyno/cache.html) distinguishes geometry
  caching from `.sim` state/checkpoint files, checkpoint intervals and bounded checkpoint trails.
- [USD Render](https://www.sidefx.com/docs/houdini/nodes/out/usdrender.html) writes USD and launches
  an external renderer, with per-frame or persistent-process options. Maelstrom does not need USD
  or a render farm to adopt the separation of simulation and presentation.

#### Date added

10/11/26
