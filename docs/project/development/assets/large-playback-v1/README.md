# Large saved-run playback repair

Verified on the primary PC on 25 October 2026. The existing user compilation contains
800,000 particles, 360 accepted steps and 361 images. Its 271,654,072-byte manifest
was rejected by the old player's 64 MiB aggregate limit. No source scene or simulation
rerun was required to repair playback.

- `installed-before/` records the original command's explicit size-limit rejection.
- `build/` and `validate-existing/` record the first fixed release build and successful
  validation of all saved images, including numerical-input consistency.
- `final-build/`, `final-validate/` and `final-window/` repeat verification after the shared
  record parser was factored without changing its numerical validation.
- `large-window-checks.json` records a mapped 1280×720 X11 WSLg window, varied sampled
  image pixels and clean `WM_DELETE_WINDOW` exit, without software drawing.
- `final-verification.json` identifies source/binary hashes and verifies that every original
  bundle file was unchanged. Manifest and image bodies are private user data and are excluded.

The final validation took 3.99 s and 162.9 MiB peak resident memory, including numerical-input
validation and every PNG. This is not a solver benchmark. The saved simulation's original
warnings remain; image integrity does not qualify its physical behaviour.

The tested executable is the release build in the PC repository's `target/release/` directory,
built from the disposable source export. The installed `~/.cargo/bin/maelstrom` was not replaced.
Source checkout, Git history and existing bundles were not changed on the PC. `privacy.json`
records home-path replacement; originals remain there. `files.json` hashes the shareable record.

The [development record](/docs/project/development/performance-compilation.md) explains the fix.
