# S077 — de Goes et al. (2015)

## Full reference:

de Goes, F., Wallez, C., Huang, J., Pavlov, D. and Desbrun, M. (2015) *Power Particles:
An incompressible fluid solver based on power diagrams*. ACM Transactions on Graphics,
34(4), Article 50, pp. 1–11. DOI: 10.1145/2766901.

#### https://www.geometry.caltech.edu/pubs/dGWH%2B15.pdf

## Relevance:

An established volume-based alternative to sampled density. Distinguishes a weighted
power-diagram algorithm from treating unweighted Voronoi cells as material parcels.

## Reliability:

Primary peer-reviewed SIGGRAPH research, obtained from the authors' Caltech host. Read on
29 October 2026, particularly §§2.1–2.3 and §§3.1–3.2. The institutional bibliographic record
confirms the DOI. Published timings are not local RTX 4070 evidence. Robust geometry and
boundary clipping are substantial implementation dependencies.

## Tags

`pressure-projection`, `power-diagrams`, `volume-conservation`, `feasibility`

## Reading notes

- §2.2 controls target cell volumes through weights and Newton updates involving a
  facet-area/site-distance Laplacian. Equal weights reduce the partition to Voronoi cells.
- §2.3 derives divergence from volume variations and its negative transpose gradient,
  discusses linear-pressure consistency, momentum and the benefits of centroidal sites.
- §§3.1–3.2 make evolving weighted parcels central to the method. A counterexample for
  unweighted material-cell constraints does not reject this full algorithm.
- §2.1 states quadratic worst-case and linear average-case 3D construction complexity.
  This is the paper's analysis, not measured Maelstrom cost or a GPU guarantee.

#### Date added

29/10/26
