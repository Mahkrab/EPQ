# S032 — Lahey (2000)

## Full reference:

Lahey, K. (2000) *TCP Problems with Path MTU Discovery*. RFC 2923. RFC Editor.

#### https://www.rfc-editor.org/info/rfc2923/

## Relevance:

Explains path maximum transmission unit discovery failures, including the black-hole behaviour in which a TCP connection is established but later hangs when larger packets are lost. This supports the diagnosis of the stalled SSH and VS Code sessions.

## Reliability:

This is an RFC published by the RFC Editor as an IETF Network Working Group informational document. It is an authoritative description of this established TCP interoperability problem, although newer standards provide updated methods for detecting it.

## Tags

`networking`, `tcp`, `mtu`, `path-mtu-discovery`

## Reading notes

- A path MTU black hole can allow a TCP connection to begin and then hang when larger packets are sent.
- Reducing the packet size can work around a path that does not return the messages needed for normal Path MTU Discovery.

#### Date added

15/07/26
