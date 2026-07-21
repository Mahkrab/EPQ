# S047 — Microsoft (n.d.)

## Full reference:

Microsoft (n.d.) ‘Configure C/C++ IntelliSense’, *Visual Studio Code Documentation*.

#### https://code.visualstudio.com/docs/cpp/configure-intellisense

## Relevance:

Explains how VS Code discovers C and C++ headers through compiler and include-path configuration, supporting the requirement to avoid false missing-header diagnostics for CUDA development.

## Reliability:

This is official Microsoft documentation for the Visual Studio Code C/C++ extension. It is authoritative for current IntelliSense configuration but may change with extension releases.

## Tags

`vscode`, `cpp`, `intellisense`, `headers`

## Reading notes

- VS Code can query the selected compiler for system include paths.
- Additional include paths can be configured for headers outside the workspace or standard-library paths.

#### Date added

21/07/26
