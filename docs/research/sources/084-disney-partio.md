# S084 — Walt Disney Animation Studios (n.d.)

## Full reference:

Walt Disney Animation Studios (n.d.) *Partio*. Official project overview and documentation.
Accessed 10 November 2026. Bundled BGEO implementation inspected separately under S060.

#### https://www.disneyanimation.com/open-source/partio/

## Relevance:

Interoperable particle-file conversion as an optional boundary around Maelstrom's internal cache.

## Reliability:

Primary publisher/project documentation. It establishes the library's purpose and supported
format families, not compatibility between every BGEO generation or preservation of u64 IDs.

## Tags

`partio`, `particle-formats`, `interoperability`

## Reading notes

- Partio is a C++ particle I/O and manipulation library supporting several formats, including
  GEO/BGEO, PTC and PDB. It is not the name of one universal binary format.
- The [project documentation](https://partio.us/documentation.html) describes particle attributes
  and conversion tools. Any future Maelstrom adapter needs explicit coordinate, precision and
  identity checks, particularly for integer ranges.

#### Date added

10/11/26
