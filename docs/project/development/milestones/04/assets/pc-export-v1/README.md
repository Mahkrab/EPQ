# Primary-PC CUDA capture and laptop playback

On 21 October 2026 the primary PC completed a fresh 8,000-particle capture, followed
by transfer and image-only playback on the laptop. This extends the
[offline rendering record](/docs/project/development/milestones/04/phases/phase-02-offline-rendering.md)
without turning the capture into a performance benchmark or a new numerical reference.

## Request and provenance

The source was copied into an isolated PC directory before the authorised completion
commit. Its production-content hash is
`sha256:e31c765e070e47a070a424e08bae78abeddfebe6ff531e58a4fef394a7e55079`, matching
Maelstrom [`9336ee42104badb1b5e439edc1df5e8488c32987`](https://github.com/Mahkrab/Maelstrom/tree/9336ee42104badb1b5e439edc1df5e8488c32987).
The original manifest correctly retains unavailable Git metadata for that source copy;
it has not been rewritten to imply the later commit existed during capture.

The [build log](/docs/project/development/milestones/04/assets/pc-export-v1/build.log)
records the successful release build with `cuda,render`. Its temporary personal path
is replaced by `PC_CAPTURE_SOURCE`. The manifest records Rust 1.96.0, target, source,
lock, shader and encoder identities. Before capture, configuration validation reported
8,000 particles and six planes; the CUDA round-trip check passed on the RTX 4070.

From that source directory, the capture command was:

```sh
./target/release/maelstrom export direct falling-block-20 \
  --mode cuda-grid --device 0 --block-size 128 --refine-timestep 4 \
  --steps 480 --step-stride 1 --render-config render.toml \
  --software --output frames-8000
```

The [fixed camera](/docs/project/development/milestones/04/assets/pc-export-v1/render.toml)
covers the whole plane-bounded box, including particle radius. Simulation used the
RTX 4070, device 0, 128-thread blocks and compute target 89. Graphics independently
used llvmpipe software Vulkan, Mesa 25.2.8 with LLVM 20.1.2. CUDA execution does not
establish hardware Vulkan support.

## Observed outcome and retention

The capture exited 0 with status `completed`, 480 accepted steps, zero CFL warnings
and 481 PNGs at 1280 × 720. Frames cover every accepted index 0–480, spanning
approximately one simulated second. Transfer exited 0. All 481 encoded-image hashes
matched the manifest on the laptop, and the manifest hash matched the PC:
`49e565b8acdcd0f57c261c11ad3fe6080ae9ed677a84c6e1d4f0f4a8b7308526`.

The [verification report](/docs/project/development/milestones/04/assets/pc-export-v1/capture-verification.json)
retains the checks, device context and exact request. The byte-identical
[capture manifest](/docs/project/development/milestones/04/assets/pc-export-v1/capture-manifest.json)
retains resolved inputs, every frame mapping/hash and full build/render provenance.
The complete approximately 76 MB sequence remains on the PC and laptop outside Git.
This evidence directory contains only the manifest and endpoint images, not a playable
copy of all frames. Laptop playback opened with `--software --speed 0.1 --repeat`
and consumed saved images without numerical execution or particle rendering.

![Initial 8,000-particle block with the fixed camera](/docs/project/development/milestones/04/assets/pc-export-v1/initial.png)

![Final accepted image after 480 steps](/docs/project/development/milestones/04/assets/pc-export-v1/final.png)

Completion, finite accepted states and zero warnings are not an independent numerical
comparison or proof of physical accuracy. This capture adds no new reference result,
cross-driver pixel guarantee, hardware-graphics qualification or timing claim. Hosted
verification was not performed. Earlier independent export and playback checks remain
in their original evidence inventories.
