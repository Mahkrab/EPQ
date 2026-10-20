# S056 — image-rs contributors (n.d.)

## Full reference:

image-rs contributors (n.d.) *PNG Decoder/Encoder*. Repository README, master revision
accessed 20 October 2026.

#### https://github.com/image-rs/image-png

## Relevance:

Informs the choice of a single-format PNG encoder for the intended offline image sequence,
instead of a general multi-format image dependency.

## Reliability:

The upstream README is primary documentation for the project's role and offered licences. It is
moving documentation, not a pinned encoder implementation or evidence of Maelstrom pixel stability.
Compression settings, dependencies and output behaviour need verification when integrated.

## Tags

`png`, `encoding`, `licensing`, `offline-output`

## Reading notes

- Read the README's responsibility and licence sections on 20 October 2026. It describes a Rust PNG
  decoder/encoder and offers Apache-2.0 or MIT licensing.
- Maelstrom's opaque RGBA8 output, fixed filenames, provenance manifest and same-environment decoded
  pixel requirement are project decisions. No encoding, file hash or image test was run from this source.

#### Date added

20/10/26
