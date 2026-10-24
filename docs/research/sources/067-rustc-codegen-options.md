# S067 — Rust Project Developers (n.d.)

## Full reference:

Rust Project Developers (n.d.) *The rustc book: Codegen Options*. Live documentation, accessed 25 October 2026.

#### https://doc.rust-lang.org/rustc/codegen-options/index.html

## Relevance:

Explains processor targeting and code-generation choices considered in the compiler review.

## Reliability:

Official compiler documentation. Options are compiler- and target-dependent; the actual
toolchain and application tests remain necessary. No Maelstrom performance result follows
from an option being available.

## Tags

`rust`, `compiler`, `portability`, `optimisation`

## Reading notes

- Read `codegen-units`, `target-cpu` and `target-feature` on 25 October 2026.
- `target-cpu=native` targets the build machine. It is a candidate for explicitly local
  builds, not an appropriate implicit portability promise for distributed binaries.
- Code-generation units affect optimisation opportunities and parallel compilation.

#### Date added

25/10/26
