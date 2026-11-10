# S085 — OpenVDB contributors (n.d.)

## Full reference:

OpenVDB contributors (n.d.) *OpenVDB Overview*. Online API documentation displaying version 14.0.0.
Accessed 10 November 2026.

#### https://www.openvdb.org/documentation/doxygen/overview.html

## Relevance:

Assesses sparse-volume storage against the current workload of exact particle positions and velocities.

## Reliability:

Official library documentation. This overview concerns sparse grids; it does not establish that
OpenVDB cannot store points. No OpenVDB point-format or compression benchmark was performed.

## Tags

`openvdb`, `sparse-volumes`, `cache-formats`

## Reading notes

- The core grid model combines a sparse tree, a transform and metadata, with integer index
  space separated from physical space. That machinery is useful for volume products, but is
  unnecessary for Maelstrom's current fixed particle arrays; this last judgement is a project decision.

#### Date added

10/11/26
