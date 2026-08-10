# Development evidence and checkpoints

This directory contains the implementation evidence for the
[Maelstrom development roadmap](/docs/project/plan.md). The roadmap owns the complete milestone and phase
sequence. Each milestone record owns its numerical and behavioural contract, while this page owns the
project-wide checkpoint process.

Current milestone evidence:

- Milestone 00: [normative contract and implementation record](/docs/project/development/milestones/00/serial-brute-force.md)
- Milestone 00: [accessible mathematical explanation](/docs/project/development/milestones/00/explation.md)

## Primary evidence model

EPQ and Maelstrom are separate Git repositories. A phase boundary is represented by full commits and
annotated tags in both repositories, joined by the Maelstrom gitlink recorded in EPQ. The prose milestone
record explains what was implemented, how it was assessed, the gate decision and any limitations.

```text
Maelstrom start tag
  -> temporary phase branch
  -> committed implementation and tests
  -> verification of that exact commit
  -> milestone branch and Maelstrom completion tag
  -> EPQ gitlink and phase evidence record
  -> verification of the exact EPQ commit
  -> EPQ completion tag
```

Branches are movable integration and review surfaces, not historical evidence. A tag gives a readable name
to a commit, but does not prove that tests ran. Verification results therefore remain explicit evidence
alongside the tagged commits.

## Repository responsibilities

Maelstrom owns simulator source, tests and simulator verification. Its completion checkpoint must contain
the implementation and every test needed to support the phase decision in the same durable commit. A dirty
worktree, untracked test or source-only commit is not a completion checkpoint.

EPQ owns the roadmap, milestone contract, implementation record, gate decision and evidence summary. It
records the exact assessed Maelstrom commit through its gitlink. A recursive checkout of the EPQ completion
tag must therefore reproduce the Maelstrom source and tests that were assessed.

The EPQ phase record identifies the full Maelstrom commit and the intended annotated tags in both
repositories. It does not include the hash of the EPQ commit containing that record: the EPQ completion tag
identifies that parent commit without creating a circular claim.

## Checkpoint names

Milestone integration branches use `milestone/<NN>-<slug>`. Temporary phase branches use
`phase/<MM>-<PP>-<slug>`, with zero-padded milestone and phase numbers.

Annotated checkpoint tags use:

- `milestone-<NN>/start`
- `milestone-<NN>/phase-<PP>/start`
- `milestone-<NN>/phase-<PP>/complete`
- `milestone-<NN>/complete`

A start tag names the clean committed base before the corresponding work. A completion tag names the
reviewed commit that satisfies the recorded gate. Published checkpoint tags are not moved or reused. When a
boundary has to be reconstructed retrospectively, its record states the nearest defensible committed state
and the limitation instead of implying that the original uncaptured state is recoverable.

## Phase lifecycle

1. Establish a clean milestone integration point in each repository and record the applicable start
   checkpoints.
2. Create a temporary phase branch from the milestone branch. Worktrees may provide convenient parallel
   checkouts, but are not evidence themselves.
3. Commit the Maelstrom implementation and tests coherently, then verify the exact committed tree rather
   than an uncommitted working copy.
4. Review the change directly or through a pull request, merge it into the Maelstrom milestone branch and
   create the Maelstrom completion tag only when the current gate is supported.
5. Record that full Maelstrom commit in the EPQ phase record and deliberately advance the parent gitlink to
   the same revision.
6. Verify the exact EPQ commit, including a recursive submodule checkout, then merge it into the EPQ
   milestone branch and create the EPQ completion tag.
7. Record local and hosted verification separately. Begin the next phase from the completed milestone state.

Once a phase is merged and its annotated tags are available, its temporary branches may be deleted. The
commits and tags retain the boundary without accumulating permanent phase branches. A milestone branch may
likewise be retired after the completed milestone is integrated into its long-lived repository branch.

## Links and verification records

Repository-root links such as `/Maelstrom/src/lib.rs` are convenient views of the current parent checkout;
they are not immutable historical evidence. A phase record uses full-commit Maelstrom permalinks for the
assessed source and tests. An annotated-tag link may be offered as a readable checkpoint name, while the full
commit remains explicit.

Verification evidence states the assessed commit, environment, checks performed, observed outcomes and
limitations. Local results are labelled as local. Hosted continuous-integration or pull-request results are
linked when they exist and are not inferred from local runs. Neither a branch name nor a tag alone proves
origin, correctness, review or successful verification.

## Milestone assets

An `assets/` directory is for genuine supporting artefacts such as plots, diagrams, screenshots, small
golden outputs, selected machine-readable results and configuration needed to reproduce an experiment. It
does not contain copied repositories, source or test trees, `.git` metadata, dependency caches, generated
documentation or build output.

Large generated results normally belong in an external release or archival store. The milestone record
keeps their producing commit, configuration, tool version, location, integrity digest and interpretation so
the evidence can be checked without committing a generated tree to `docs/`.

## Reproducing a checkpoint

An assessor starts from the EPQ completion tag and performs a recursive checkout. This supplies the exact
parent record and the Maelstrom revision stored by its gitlink. The phase record then leads to the immutable
source and test evidence and to any local or hosted verification results. The starting state is available
through the corresponding start tags in both repositories.

For final-submission resilience, a separately published source archive may supplement the Git remotes. It
is derived from named commits, excludes repository metadata and generated output, and includes a manifest
and integrity digest. It does not replace the ordinary commit, tag and gitlink model or become a copied
source tree under milestone documentation.
