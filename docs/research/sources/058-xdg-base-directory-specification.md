# S058 — Bastian et al. (2021)

## Full reference:

Bastian, W., Karlitskaya, A., Poettering, L. and Löthberg, J. (2021) *XDG Base Directory
Specification*. Version 0.8, 8 May. Freedesktop.org. Accessed 21 October 2026.

#### https://specifications.freedesktop.org/basedir/latest/

## Relevance:

Provides the user data and configuration roots underlying the proposed Maelstrom scene library,
compiled-run storage and application preferences on Linux/WSL.

## Reliability:

The official specification is the primary reference for these variables and their default paths.
It does not prescribe Maelstrom's commands, scene packages, run bundles or application-specific
environment overrides. Those remain project decisions. The latest URL may change; version 0.8
was the document read.

## Tags

`cli`, `storage`, `configuration`, `linux`

## Reading notes

- Read the introduction, basics and environment-variable rules on 21 October 2026.
- User data defaults to `~/.local/share`; configuration defaults to `~/.config` when the
  corresponding XDG variable is unset or empty. XDG environment paths must be absolute.
- Scene names, lookup collisions, portable run manifests and the distinction between durable
  outputs and disposable caches require separate Maelstrom rules.

#### Date added

21/10/26
