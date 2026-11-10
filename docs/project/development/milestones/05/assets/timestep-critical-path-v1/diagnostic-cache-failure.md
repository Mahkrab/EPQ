# Rejected diagnostic control captures

The first NVTX control build reused the final ordinary executable from a shared
Cargo target cache. Its binary digest was c4b70554d3cacb4d6abbb434fcb96269a44afa7490196558cacaae4ca429583e,
whereas the diagnostic source required embedded source digest
15edfe811e2c222414bbad2b24d8bcdc7d17cf47ee4108e7d2634476a09cc086.
The build completed in 0.10 s and did not compile the requested source. This was
caught by checking the expected source digest directly inside every executable.
The ordinary control, row-eight, tiled and final measurement binaries all passed
that independent check; their samples remain admitted.

Exclude `nvtx-*-control` from source/component comparisons. Retain their original
command, summaries and logs as failed diagnostic attempts. Rebuilding after touching
build.rs forces the source/build identity and PTX pipeline to run. A byte search
asserts the expected source digest before `nvtx-rebuilt-*-control` collection.
The correctly identified diagnostic final build is separate. Never infer source
identity merely from Cargo success or a copied executable's filename.
