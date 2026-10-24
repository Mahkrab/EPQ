# S066 — Rust Project Developers (n.d.)

## Full reference:

Rust Project Developers (n.d.) *The Cargo Book: Profiles*. Live documentation, accessed 25 October 2026.

#### https://doc.rust-lang.org/cargo/reference/profiles.html

## Relevance:

Defines the release settings and optional link-time optimisation used to assess Maelstrom's
Rust build. It distinguishes compiler options from measured application improvements.

## Reliability:

Official Cargo documentation, authoritative for documented profile behaviour. The page is
unversioned; the actual compiler and command environment must accompany measurements.
It does not establish which profile is fastest for Maelstrom.

## Tags

`rust`, `cargo`, `compiler`, `optimisation`

## Reading notes

- Read on 25 October 2026: release defaults, `lto`, `codegen-units`, `panic` and profile overrides.
- Release uses optimisation level 3 and 16 code-generation units by default. `lto = false`
  permits local ThinLTO; it does not mean all link-time optimisation is disabled.
- Cross-crate ThinLTO and fewer code-generation units may improve generated code but cost
  compilation time. Cargo recommends experiments rather than assuming larger settings win.
- Maelstrom's separate C++ and embedded PTX builds do not gain cross-language optimisation
  merely by selecting Rust ThinLTO.

#### Date added

25/10/26
