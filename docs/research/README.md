# Maelstrom EPQ Research Sources

Research record.

- [source-register.md](/docs/research/source-register.md) is the readable overview.
- [references.bib](/docs/research/references.bib) is the citation database for the report.
- [sources/](/docs/research/sources/) contains one focused evaluation record per source.
- [sources/TEMPLATE.md](/docs/research/sources/TEMPLATE.md) is the format for new source records.

## How artefact pages cite these sources

Artefact pages use quick-definition links and evidence citations for different purposes. The first
useful mention of an unfamiliar concept may link to Wikipedia or a clear authoritative overview for
the reader. A registered source is cited after the punctuation of the claim it supports

### Example

 
<div style="padding: 5px; border: 1px solid #575757">

The [Compute Unified Device Architecture (CUDA)](https://en.wikipedia.org/wiki/CUDA)
toolchain compiles kernels for execution on NVIDIA GPUs.<sup><a href="#ref-s012">S012</a></sup>

</div>

Only the first useful occurrence of that concept receives the quick link. Later mentions remain
plain text, while `S012` is repeated only where another claim needs clear attribution. Multiple
sources supporting one claim share one superscript.

A page that uses registered sources ends with one compact, numerically ordered entry per cited ID:

<div style="padding: 5px; border: 1px solid #575757">

### References used
 <a name="ref-s012"></a> **S012 — NVIDIA Corporation (2026).** *CUDA Programming Guide*, Release 13.2. [Source record](/docs/research/sources/012-nvidia-cuda-programming-guide-release-13-2.md).

</div>

The linked appraisal record contains the fuller reference, relevance, reliability and reading notes; `references.bib` remains the structured bibliography for the formal report. Source catalogue files do not cite themselves.