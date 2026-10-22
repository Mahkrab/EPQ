# S061 — Koschier and contributors (n.d.)

## Full reference:

Koschier, D. and contributors (n.d.) *CompactNSearch*. Upstream README, revision
`b40afcf47fe1963b363eba2371f04b42720fcb1d`. Accessed 22 October 2026.

#### https://github.com/InteractiveComputerGraphics/CompactNSearch/tree/b40afcf47fe1963b363eba2371f04b42720fcb1d

## Relevance:

Design reference for local neighbourhood storage, search and spatial ordering, not a proposed dependency.

## Reliability:

Primary, revision-pinned documentation by the library's developers. Its design description does
not prove a benefit in Maelstrom; query ordering and numerical compatibility require separate checks.

## Tags

`neighbours`, `spatial-hashing`, `performance`, `open-source`

## Reading notes

- Read the pinned [README](https://github.com/InteractiveComputerGraphics/CompactNSearch/blob/b40afcf47fe1963b363eba2371f04b42720fcb1d/README.md).
- Describes parallel fixed-radius search using compact hashing and optional Z-curve reordering
  for cache efficiency. Its interface exposes per-point neighbour counts and indexed neighbours.
- It is a search component, not a complete fluid solver. Internal implementation and integration
  costs remain subjects for the planned investigation.
- Further reading on 22 October checked pinned `include/PointSet.h`: its query API accesses explicit
  per-point neighbour vectors. This is evidence of local-list traversal, not a GPU layout recommendation.

#### Date added

22/10/26
