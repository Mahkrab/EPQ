# S069 — Microsoft (n.d.)

## Full reference:

Microsoft (n.d.) *WSLg: Windows Subsystem for Linux GUI*, upstream README, architecture and
OpenGL acceleration sections. Accessed 26 October 2026.

#### https://github.com/microsoft/wslg

## Relevance:

Separates Windows presentation/compositor transport from CUDA headless execution and
Maelstrom's own offline pixel readback.

## Reliability:

Primary implementation documentation. It describes both architecture and initial-release
limitations; those historical costs are not a measurement of the current PC.

## Tags

`wslg`, `graphics`, `presentation`, `interop`

## Reading notes

- WSLg connects Linux windows to Windows through Weston, FreeRDP and local integration.
- The OpenGL section describes Mesa/D3D12 acceleration and a system-memory presentation path
  explicitly associated with the first release. Its percentage example is not a current baseline.

#### Date added

26/10/26
