# Usability verification

This inventory supports the [implementation record](/docs/project/development/usability-revision.md).
It identifies the uncommitted working files, local checks, isolated installation and actual
window journeys. It is not a source snapshot, a Git checkpoint or hosted evidence.

`verification.json` records command outcomes and SHA-256 identities. Its native playback section
retains the original sequence-file inventory, confirming that playback did not rewrite its input.
The short three-frame compilation deliberately uses unforced input and a half-second timestep to
make playback controls observable. It is a synthetic usability fixture, not a new numerical default,
golden trajectory or benchmark. The normal numerical suite separately checks the retained goldens.

Release headless tests passed 233 checks; viewer tests passed 265 ordinary checks, with nine opt-in
software-Vulkan checks exercised separately. Parent suites passed 16 + 27 + 7 tests. Formatting,
strict Clippy and warning-denying Rustdoc passed. Installation used an isolated temporary root;
the normal installed command and system libraries were not replaced.

Native WSLg/Xwayland events addressed only the test-owned windows. Viewer checks covered controls,
resource failure, prior outcomes, surface recreation and close during work. Saved playback covered
seeking, endpoints, speed, pause/resume, resize and close, leaving input files unchanged. Selected
captures were inspected; screenshots alone are not the numerical or interaction oracle.
The live journey deliberately sets `cfl_factor=0.000001` to exercise warning presentation;
the warning capture does not show the ordinary defaults or a reference benchmark request.

Selected captures: [live completed state](viewer-completed.png) and
[resized saved playback](playback-resized.png). The low-resolution playback image was
deliberately compiled at 64 × 64 pixels to keep this control check small.

The initial window attempt selected a shared target executable left by a headless build. Its
explicit missing-feature error is retained in the inventory; the isolated installation then passed.
Earlier development failures in scene serialisation and ID presentation are explained in the
implementation record, not hidden by claiming every first attempt passed.

No CUDA hardware, hardware-Vulkan, other-platform or hosted verification ran here. No performance
claim follows from test execution or synthetic playback timing. Published source links still need
an authorised implementation-first checkpoint.
