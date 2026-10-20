# S055 — winit contributors (n.d.)

## Full reference:

winit contributors (n.d.) *winit: cross-platform window creation and management in Rust*.
v0.30.12 README and Cargo manifest; repository licence, accessed 20 October 2026.

#### https://github.com/rust-windowing/winit/tree/v0.30.12

## Relevance:

Supports separating window creation and events from drawing and headless solver execution.
Informs the intended optional interactive dependency.

## Reliability:

The official versioned repository describes that release's responsibility and features. Its platform
metadata does not prove a Maelstrom window works on WSLg. The moving master README was also checked
and advertises a beta family; the design instead starts with the reviewed stable family.

## Tags

`windowing`, `events`, `features`, `licensing`

## Reading notes

- Read v0.30.12 README and Cargo manifest, current master README and repository `LICENSE` on
  20 October 2026. The licence is Apache-2.0.
- winit creates windows and delivers events such as resize and input; drawing requires another
  library. Its manifest exposes X11, Wayland and raw-window-handle support.
- The intended main-thread window, worker-owned solver and optional viewer feature are Maelstrom
  decisions. No window lifecycle or dependency compatibility was tested during this reading.

#### Date added

20/10/26
