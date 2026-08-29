# Phase 2 implementation and verification record

## Starting point

Phase 1 left Maelstrom with tht numerical building blocks for the solver implmemntation, but values
and testing states still need to be assambled in the source. 

This phase started from the [Phase 1 completion commit](https://github.com/Mahkrab/Maelstrom/tree/89393707d5f3e035150e33a67c14faf926d0c877)

## Scope and outcome

Phase 2 turned the fixed numerical decisions from Phase 0/1, into explicit, repeatable, inputs. Maelstrom
can now load and inspect strict configurations, then construct ordinary external scenes in a stable order.
EPQ has selected which of those inputs form the permanent comparison family before any golden result or
performance baseline is produced.

This phase stil does not discover neighbours, run a complete timestep, produce result, or benchmark.

## Decisions and implementation

Maelstrom owns the technical input contract, not the investigation's classification. Its
[configuration resolver](/Maelstrom/src/config/resolved.rs) starts from neutral built-in defaults and applies
configuration-file, scene and eventual command-line values in that order. Each field retains its source for
inspection. Unknown, contradictory, unsupported, invalid and non-finite values are rejected, but a different
supported value does not require a research label. Primary values remain separate from the authoritative
[derived calculations](/Maelstrom/src/config/validation.rs); supplied derived values are exact assertions, not
independent tuning inputs.

Technical configuration equivalence is represented from every resolved policy, primary value and derived
binary32 value. Scene equivalence adds the randomness policy, ordered planes and every ordered particle
identity, position and velocity. Names, descriptions, provenance and EPQ workload roles do not decide this
equivalence, although deterministic inspection still records the display metadata and field provenance.

The selected numerical values are ordinary external data in
[defaults-v1.toml](/Maelstrom/config/defaults-v1.toml). Each selected
[falling-block scene](/Maelstrom/scenes/) refers to that file through the public relative-path loader; none
uses a special reference-scene path. The files fix a half-open lattice at `[0.20, 0.40, 0.20] m`, `0.05 m`
spacing, zero initial velocity, identities beginning at zero, x-then-y-then-z construction with z fastest,
and the ordered minimum/maximum X, Y and Z planes. Their count-specific box dimensions and exact binary32
plane offsets are stored in the scene data and independently asserted by
[external-scene tests](/Maelstrom/tests/external_scenes.rs).

EPQ assigns the research use of those neutral files as follows:

| EPQ use | Ordinary scene input | Run length and checkpoints |
| --- | --- | --- |
| Frequent correctness check | [falling-block-06.toml](/Maelstrom/scenes/falling-block-06.toml), 216 particles | 240 timesteps; `0, 1, 60, 120, 240` |
| Eventual golden result | [falling-block-10.toml](/Maelstrom/scenes/falling-block-10.toml), 1,000 particles | 240 timesteps; `0, 1, 60, 120, 240` |
| Scalability sequence | [04](/Maelstrom/scenes/falling-block-04.toml), [06](/Maelstrom/scenes/falling-block-06.toml), [08](/Maelstrom/scenes/falling-block-08.toml), [10](/Maelstrom/scenes/falling-block-10.toml), [12](/Maelstrom/scenes/falling-block-12.toml), [16](/Maelstrom/scenes/falling-block-16.toml), [20](/Maelstrom/scenes/falling-block-20.toml): 64 to 8,000 particles | 20 timesteps each; `0, 1, 20` |

Changing a selected file creates a separately recorded EPQ experiment with new evidence; it does not alter
the meaning of an earlier result. That is a documented investigation rule rather than a general Rust input
classification. Focused empty, single-particle, interaction, support-boundary, coincidence and plane cases now
remain at the [test boundary](/Maelstrom/tests/scene_contract.rs), rather than appearing as simulator domain
types.

## Verification

The new behaviour is covered by:

- [configuration](/Maelstrom/tests/configuration_contract.rs)
- [scene](/Maelstrom/tests/scene_contract.rs)
- [external inputs](/Maelstrom/tests/external_scenes.rs)

| Local check | Observed outcome |
| --- | --- |
| `cargo fmt --all -- --check` and `cargo check --all-targets --all-features` | Passed |
| `cargo clippy --all-targets --all-features -- -D warnings` | Passed with warnings denied |
| `RUSTDOCFLAGS='-D warnings' cargo doc --no-deps --all-features` | Passed with warnings denied |
| `cargo test --all-targets --all-features` and the equivalent release test | Passed all 63 integration tests in each profile |
