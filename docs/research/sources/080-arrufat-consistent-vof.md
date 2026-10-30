# S080 — Arrufat et al. (2021)

## Full reference:

Arrufat, T., Crialesi-Esposito, M., Fuster, D., Ling, Y., Malan, L., Pal, S., Scardovelli, R.,
Tryggvason, G. and Zaleski, S. (2021) *A mass-momentum consistent, Volume-of-Fluid method for
incompressible flow on staggered grids*. Computers & Fluids, 215, Article 104785.
DOI: 10.1016/j.compfluid.2020.104785. Author preprint arXiv:1811.12327v2, 24 February 2021.

#### https://arxiv.org/abs/1811.12327v2

## Relevance:

Shared phase/momentum fluxes and geometric interface transport for the isolated coupled-fluid
study. The local averaged-staggered-mass prototype is not a reproduction of this full algorithm.

## Reliability:

Primary research with a linked journal publication. The 52-page v2 manuscript was read selectively
on 29 October 2026: abstract/introduction, §§3.3.4–3.3.5 and §§3.4.1–3.4.5. This supports the
transport principles, not a claim that every benchmark or implementation detail was reproduced.

## Tags

`vof`, `mass-momentum-consistency`, `staggered-grid`, `free-surface`

## Reading notes

- WY advection uses a direction-independent compression indicator, cancelling its split source
  when discrete divergence is zero. The authors discuss clipping and tiny interface fragments.
- Material-derived mass fluxes support momentum consistency. Auxiliary staggered-density
  reconstruction is a distinct part of the published method.
- Local wave, conservation and collision outcomes are project observations; the publication
  does not establish local accuracy, constants or GPU throughput.

#### Date added

29/10/26
