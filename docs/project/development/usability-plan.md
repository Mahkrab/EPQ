# Maelstrom usability revision plan

## Outcome and boundary

Make Maelstrom understandable as an installed application: discover a scene, choose execution,
run or view it, save output and watch it again. Rewrite its README and maintained documentation,
including fixture instructions, and bring the CLI and execution defaults into agreement. Start from
the [reviewed issues](/docs/project/development/pre-evaluation-review.md), not an assumed new interface.

This is a pre-evaluation revision, not a completed evaluation phase. Solver optimisation, numerical
retuning, new rendering features and final benchmark collection are excluded. Follow the applicable
`AGENTS.md`; this plan adds task-specific outcomes rather than repeating those rules. Internal
structure and documentation layout remain implementation decisions. The
[CLI and storage direction](/docs/project/development/cli-design.md) records the user's command
requirements and the proposed supporting commands and flags. Implement that interface rather than
inventing a competing vocabulary; resolve the identified compatibility details before changing code.

## Work and acceptance criteria

The [implementation record](/docs/project/development/usability-revision.md) describes the local
implementation, verification and remaining checkpoint/device limitations. The criteria below
remain the review basis; they do not imply final performance qualification.

1. **Decide the public interface.** Audit all commands and maintained guides, then record one concise
   decision covering terminology, execution selection, defaults, feature discovery and compatibility.
   **Done when:** compile, run and view share a coherent execution vocabulary and resolution
   policy; scene/run storage, installation, example-free help, errors, stdout/stderr, output safety
   and numerical rerun behaviour are specified.
   Identify existing commands or records that need compatibility handling before changing them.

2. **Implement consistent CLI behaviour and defaults.** Prefer practical execution for normal use;
   retain explicit brute force, serial grid, threaded grid and CUDA for comparison and demonstration.
   If automatic selection is introduced, resolve before execution, explain and record the selected
   resources, and distinguish unavailable capabilities from runtime failures. Use an honest,
   documented policy, not an unmeasured promise of optimal performance. Hardware-tuned thresholds can
   be revisited after the performance investigation.
   **Done when:** equivalent requests resolve consistently across commands, explicit selections are
   honoured, unavailable explicit CUDA fails visibly, and replay restores recorded execution rather
   than silently reselecting it. Tests cover selection, precedence, resource errors and old records;
   unchanged explicit requests retain their numerical results and output guarantees.

3. **Rewrite the documentation around user journeys.** Lead with supported installation and an
   installed `maelstrom` quick start. Cover scene editing, execution selection, viewing, result saving,
   export, playback and troubleshooting; keep detailed configuration/API material accessible without
   crowding the introduction. Explain which operations compute again and which read saved data.
   **Done when:** every maintained page has been reviewed or rewritten, examples agree with the new
   help, feature/build requirements and optimised installation are explicit, and development Cargo
   commands are separate from everyday use. Preserve technical facts, useful links and necessary compatibility guidance; do not
   rewrite historical EPQ records or churn correct Rustdoc merely to satisfy a rewrite count.

4. **Verify the complete journeys and record the outcome.** Exercise the documented installation,
   discovery, named user-scene resolution, small headless run, explicit execution selection, scene
   override, live viewing, compilation and saved-playback paths. Include invalid input and
   missing-capability failures, and verify that playing
   a compiled run performs no simulation, particle rendering or output rewrite. Test storage
   precedence, name collisions, bundle relocation, pacing and example-free help as public contracts.
   **Done when:** deterministic CLI tests and relevant regressions pass; documented examples are
   exercised on supported available configurations; device/display checks identify their environment
   and any unavailable path remains explicitly unverified. Keep a concise before/after decision and
   verification record pinned to the assessed source. Do not claim readiness for final evaluation
   until the separate performance concerns have been addressed or explicitly dispositioned.

## Using this plan with an agent

Give an agent the current task, this plan and the issue record. Let it choose the necessary source
and tests, complete the task through verification, and stop at its stated boundary. Ask only about
material choices that cannot be resolved from project evidence. Git operations still require the
authority specified by `AGENTS.md`.

This outcome-led format applies OpenAI's guidance to avoid elaborate recipes and redundant context,
while defining completion and decision boundaries. It is a project choice, not proof of a universally
optimal prompt length or model configuration.<sup><a href="#ref-s057">S057</a></sup>

## References used

<a name="ref-s057"></a> **S057** — OpenAI (2026), *Rethinking skills and prompts for GPT-6 Astra*.
[Source record](/docs/research/sources/057-openai-agent-instruction-design.md).
