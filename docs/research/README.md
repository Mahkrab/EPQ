# Maelstrom EPQ research and citation standard

This directory is the research base for the EPQ artefact. It records which external works were used, how trustworthy and relevant they are, and where their ideas support the project. The system has four coordinated parts:

- [source-register.md](/docs/research/source-register.md) is the readable catalogue
  overview
- [references.bib](/docs/research/references.bib) is the structured bibliography used for formal report citations
- [sources/](/docs/research/sources/) contains one source and reading record per source
- [sources/TEMPLATE.md](/docs/research/sources/TEMPLATE.md) is the starting format for a new source record.

## Stable source identity

Every registered source has one permanent identifier in the form `S###`. The number identifies one specific source and, where distinction matters, the version or edition. 

Source records are nveer chnaged, renamed or moved. 

The source record, register row, BibTeX entry and reference must agree on the author or responsible organisation, title, year, edition or release, and stable destination. 

## Evidence citations and reader links

Reader links and evidence citations serve different purposes:

- A reader link provides a quick link to a definition, explanation or exmaple of the term highlighted. 
- An `S###` citation identifies the registered source which supports the tagged information. It links to the page footer, which in turn links to the source record and its BibTeX entry.
- A project-evidence link points to Maelstrom source, tests, results, logs, decisions or Git checkpoints that demonstrate something about the project. 

## Citation placement and syntax

The citation will be after the punctuation of the smallest sentence, clause or cell that it supports.
It will be superscript, using html escapes on github.  

Every page that uses registered citations, ends with one `References used` section, which will hold each link to the sources. 

## Presentation example

The [CUDA infrastructure record](/docs/project/infastructure/CUDA/README.md) is the current exemplar
for citation placement, combined markers and a page-level `References used` footer.
