# Compiler optimisation assessment

Reviewed on 25 October 2026 after the neighbour attribution and large-playback repair.
The [retained PC experiment](/docs/project/development/assets/compiler-assessment-v1/README.md)
compares optional Rust settings without altering production defaults or numerical flags.

## Are optimisations already enabled?

Yes. Maelstrom has no release-profile override, so ordinary release builds use Rust
optimisation level 3, 16 code-generation units and local ThinLTO. The default `lto = false`
does not disable every form of link-time optimisation. Cross-crate ThinLTO is an additional
option, with a linking-time cost.<sup><a href="#ref-s066">S066</a></sup>

`build.rs` compiles the C++ bridge with `-O2` and emits PTX for `compute_89` by default.
NVCC's `-O3` selects host optimisation; device optimisation is already implicit without
device debug mode. The build does not enable `-G` or fast-compile shortcuts.<sup><a href="#ref-s045">S045</a></sup>
The bridge loads PTX with `cuModuleLoadData`, without lowering the driver compiler's
default optimisation level of 4, its highest documented level.<sup><a href="#ref-s053">S053</a></sup>
There is no evidence that our CUDA results came from accidentally unoptimised device code.

The [generated-code inspection](/docs/project/development/performance-neighbour-attribution.md)
also shows common distance expressions already shared within individual loops. Optimising
source expressions that have disappeared from generated code would not establish a speedup.

## Measured optional Rust profile

I built the same exported solver with `CARGO_PROFILE_RELEASE_LTO=thin` and
`CARGO_PROFILE_RELEASE_CODEGEN_UNITS=1`, keeping native flags unchanged. These two
settings were tested together, so the results cannot isolate their individual effects.
Both binaries ran CUDA device 0, 128 lanes, 480 steps, timestep refinement 4 and eight
iterations, without checkpoint audits. Each size had one warm-up per variant and five
alternating matched pairs on the primary Ryzen 9 7900X/RTX 4070 PC.

| Particles | Ordinary release median | ThinLTO / one-unit median | Observation |
| --- | ---: | ---: | --- |
| 8,000 | 1.660 s | 1.677 s | About 1.0% slower; four of five pairs slower |
| 110,592 | 10.084 s | 10.039 s | About 0.45% faster; three pairs faster, two slower |

The first small campaign overlapped my playback-window check. It is retained as exploratory
evidence; the table uses a fresh small campaign collected after display testing ended.
The large campaign began after the window closed. Campaigns were not pooled, and all raw
samples, including slower ones, remain available. Machine readings describe Linux and
available GPU state, not a complete view of other Windows activity.

All compared runs agreed exactly on physical results and ordered diagnostics; all 18
explicit CUDA library tests passed for the optional profile. The large trajectory retains
known CFL warnings. The headless executable shrank from 3,692,912 to 3,026,000 bytes,
about 18%. Its build took 16.75 s, but the release control used cached dependencies, so
these are not matched cold-build costs. No CPU-backend, viewer or compilation-throughput
performance comparison was made for this profile.

## Decision and risks

Keep ordinary release defaults for now. The CUDA device programme is unchanged by these
Rust options; the small workload became slower and the large pairs show little consistent
runtime benefit. The smaller binary is a real benefit worth considering for distribution,
but this trial does not establish a broadly faster default. This is an assessment of the
combined settings on these workloads, not a rejection threshold or a claim that ThinLTO
cannot help CPU execution. A separate CPU/CLI study could change the decision.

The main remaining compiler choices have different consequences:

- Cross-crate LTO and fewer code-generation units can trade build time for different
  optimisation opportunities; they still require application tests and measurements.
  Profile-guided optimisation needs representative training and independent evaluation.<sup><a href="#ref-s066">S066</a></sup>
- `target-cpu=native` permits instructions for the build machine. Keep it an explicit
  local experiment; copying that binary to another processor can lose compatibility.<sup><a href="#ref-s067">S067</a></sup>
- CUDA fast maths enables denormal flushing, approximate division/square root and
  multiply-add contraction. The current flags deliberately preserve the numerical contract;
  changing them is a separately qualified arithmetic variant.<sup><a href="#ref-s045">S045</a></sup>
- `panic=abort` changes failure behaviour, while stripping symbols mainly changes artefact
  size and diagnosability. Neither is a substitute for measuring solver bottlenecks.<sup><a href="#ref-s066">S066</a></sup>

Dedicated operation entry points, ordered arithmetic reuse and identity sorting remain
implementation candidates. More aggressive flags do not remove their algorithmic costs.

## References used

<a name="ref-s045"></a> **S045** — NVIDIA, *NVCC*, CUDA 13.3, §§4.2.3.13–15 and 4.2.7.7–11.
[Source record](/docs/research/sources/045-nvidia-nvcc.md).

<a name="ref-s053"></a> **S053** — NVIDIA, *CUDA Driver API*, CUDA 13.3, `CUjit_option`.
[Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).

<a name="ref-s066"></a> **S066** — Rust Project Developers, *The Cargo Book: Profiles*.
[Source record](/docs/research/sources/066-cargo-profiles.md).

<a name="ref-s067"></a> **S067** — Rust Project Developers, *The rustc book: Codegen Options*.
[Source record](/docs/research/sources/067-rustc-codegen-options.md).
