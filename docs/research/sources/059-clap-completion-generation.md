# S059 — clap contributors (n.d.)

## Full reference:

clap contributors (n.d.) *clap_complete: Shell completion generation for clap*.
Version 4.6.11 API documentation. Accessed 21 October 2026.

#### https://docs.rs/clap_complete/4.6.11/clap_complete/

## Relevance:

Supports generating shell completions from Maelstrom's actual command declarations
instead of maintaining separate shell-specific copies of its commands and flags.

## Reliability:

Primary crate documentation published from the upstream Rust package, version 4.6.11.
It documents the generator API, not the correctness of Maelstrom's command definitions
or every installed shell environment. The package remains a supply-chain dependency.

## Tags

`cli`, `completions`, `rust`, `dependencies`

## Reading notes

- Read the quick start, runtime generation example and licence statement on 21 October 2026.
- The generator accepts a clap command and writes completion definitions to a chosen writer.
- Maelstrom uses the stable generation API without unstable dynamic completion or automatic
  shell configuration changes. Local tests must check its own generated output.

#### Date added

21/10/26
