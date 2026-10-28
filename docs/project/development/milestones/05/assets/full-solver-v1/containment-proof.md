# Deferred final-containment certificate

The host predicate first checks that the point is finite, evaluates
`(nx*x + ny*y) + nz*z` in binary32, checks that result, subtracts the plane
offset, checks that result, then compares with zero. The certificate uses the
same dot product, subtraction, finite tests and sign predicate. CUDA retains
`--fmad=false --ftz=false --prec-div=true --prec-sqrt=true`; no expression in
integration, PBF, projection, velocity reconstruction or effects is changed.
Signed zero satisfies both predicates. NaN and infinity fail both predicates.
The host still checks all final particle components and identities independently.

Projection is the last writer of positions. Every projection launch resets the
private marker in lane zero. Its entire launch completes before reconstruction
on the same stream, so there is no race with later marker readers/atomics.
Reconstruction tests the final positions and writes only the velocity prefix.
For each failed point, unsigned atomic minimum records the earliest row/plane;
it changes no numerical state. Later effects leave positions and the marker
unchanged. Their errors and cancellation polls still occur before host output
validation and containment acceptance. A failure certificate reruns the original
ordered host loop, so the exact original error and its priority are retained.
Even if later checks reject the attempt, no accepted allocation is promoted.
A retry resets diagnostics and projection resets its working marker again.

A vector occupies 12 bytes. With CUDA allocation alignment, `12*N` is aligned to
eight bytes for even N; for odd N the marker starts four bytes later. Four u32
trailer words cover both alignments and are all initialized before download.
Both velocity allocations have the same 16-byte trailer and their capacities
are swapped together with their pointers. The bridge checks both capacities
before submission. The empty case reads or writes no trailer.

The final copy downloads `3*N + 4` u32 words for non-empty state. Prefix words
become f32 through `from_bits`, preserving every bit; the marker never enters
numerical arithmetic. The marker is a private certificate consumed only at the
original host validation boundary. There is no new launch, copy, wait, host
pointer retained by CUDA, shared context, thread or cancellation boundary.
Requested device capacity increases by 32 bytes per non-empty solver, and steady
DtoH traffic by 16 bytes per accepted step. Allocation granularity may exceed
these requested sizes.
