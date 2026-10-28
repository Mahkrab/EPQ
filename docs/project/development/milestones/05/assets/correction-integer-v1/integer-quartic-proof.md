# Exact reconstruction of the retained quartic guard

This is an implementation argument for `native/power.cuh`, supported by the
exhaustive results in `reference-power/` inside `verification.tar.xz`. It does not
replace the retained approximation with the mathematical fourth power. The candidate
reproduces the old guard's intermediate rounding, acceptance set and accepted result.

A positive normal binary32 input is `x = M * 2^(e-23)`, where M has 24 bits.
The retained first binary64 square is exact: `S = M*M` needs at most 48 bits.
Its second square forms `P = S*S`, which needs at most 96 bits, before rounding
to 53 significant bits. The candidate obtains P's low and high 64-bit halves using
unsigned multiplication and `__umul64hi`. Unsigned overflow gives exactly the required
low half; no signed overflow or out-of-range conversion is used.

Because `2^92 <= P < 2^96`, its leading-bit index K is 92–95. The high half is
non-zero and fits 32 bits, so `95 - clz(high)` obtains K. Rounding P to 53 bits
discards `K-52` bits, between 40 and 43, entirely in the low half. The candidate
constructs the top 53 bits, compares the remainder with its midpoint, and applies
ties-to-even. A carry is normalised. This reproduces the retained binary64 quartic,
including its low 29 fraction bits; the first square needed no rounding.

The resulting exponent is `4*(e-23) + K`. A second ties-to-even rounding discards
the same low 29 bits to form a 24-bit binary32 significand, normalising any carry.
Normal output bits therefore equal the old binary64-to-binary32 conversion. Inputs
whose output exponent is below -126 can produce at most the minimum normal value;
the retained guard rejects that value and every subnormal. Outputs above exponent
127 are also rejected. The original endpoint tests, excluding minimum-normal and
maximum-finite values, remain unchanged.

Only input exponents -32 through 31 can pass. Smaller inputs have fourth powers
below the retained normal-output range; inputs at least `2^32` overflow binary32.
The unsigned word interval for those binades also excludes every negative value,
zero, subnormal, infinity and NaN. Early rejection therefore cannot change an accepted
input. The helper's output parameter, as before, is consumed only when it returns true.

Finally, the original guard compares the low 29 bits of the rounded binary64 result
with their binary32 midpoint. The candidate uses exactly those reconstructed bits
and the unchanged distance threshold `0x200000`, including the strict `>` comparison.
It preserves both the accepted result and the decision to fall back. Directly rounding
the exact 96-bit product to binary32 would omit a retained rounding stage; this
implementation deliberately reproduces both stages.

For exponent four, identical acceptance and accepted bits plus the unchanged fallback
imply identical `ordered_power` results. Every negative input still falls back by
construction, and every other exponent takes the unchanged branch. The exhaustive
GPU test checks all 2,147,483,648 non-negative words against both the original
approximation and an independent copy of the retained binary64 guard, at every
supported block size. It reports zero result or guard mismatches, 529,216,975 accepted
words, and the unchanged 354,191 unguarded-quartic negative-control mismatches.

No correction reduction, ratio division, pressure multiplication or checked expression
surrounding this helper changes. Identical shaped-value bits preserve finiteness and
therefore the original error priority; no state, diagnostic, cancellation, publication
or rollback boundary changes. This is exact implementation substitution, not a new
precision, approximation, accumulation order or convergence setting.
