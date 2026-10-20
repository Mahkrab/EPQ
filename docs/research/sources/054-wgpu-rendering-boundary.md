# S054 — gfx-rs developers (n.d.)

## Full reference:

gfx-rs developers (n.d.) *wgpu: repository documentation, feature metadata and licences*.
README on `trunk` and `wgpu/Cargo.toml` at v30.0.0, accessed 20 October 2026.

#### https://github.com/gfx-rs/wgpu

## Relevance:

Informs the intended optional renderer boundary and native graphics target. It does not qualify
Maelstrom's display environment or establish image reproducibility.

## Reliability:

Official upstream documentation and feature metadata describe the library's intended capabilities.
The README is moving documentation; the reviewed v30.0.0 feature manifest is versioned. Upstream
support is distinct from tested application/device support. No performance claim is adopted.

## Tags

`graphics`, `wgpu`, `features`, `licensing`, `portability`

## Reading notes

- Read README platform/support and maintenance sections, v30.0.0 `wgpu/Cargo.toml`, and
  `LICENSE.MIT` / `LICENSE.APACHE` on 20 October 2026.
- The README describes a Rust graphics API with native backends including Vulkan. The manifest
  exposes backend and shader-language features, informing selective optional compilation.
- The repository supplies MIT and Apache-2.0 licences. Actual transitive notices still require
  review at dependency integration; no graphics dependency was installed by this reading.
- Maelstrom's Vulkan-first target, separate render/viewer features and deferred graphics qualification
  are project decisions, not guarantees from this source.

#### Date added

20/10/26
