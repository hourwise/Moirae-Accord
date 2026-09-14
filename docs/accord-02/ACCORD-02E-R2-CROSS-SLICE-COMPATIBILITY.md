# ACCORD-02E-R2 — Cross-Slice Compatibility

This matrix was rebuilt from the A/B/C/D/R1/R2 artifacts. It is machine-readable
in [`accord-02e-r2-compatibility-matrix.json`](./accord-02e-r2-compatibility-matrix.json).

## Status counts

The matrix contains 36 entries. The authoritative counts are kept in the
machine-readable entries and are summarized here after parsing the file:

| Status | Meaning in this review |
| --- | --- |
| EXACT | Same identifier/shape or an explicit invariant establishes the relation. |
| COMPATIBLE | No profile-specific translation is needed for the reviewed relation. |
| COMPATIBLE_WITH_PROFILE | The relation is sound only under a named supplied profile. |
| AMBIGUOUS | A required cross-slice term or membership/equality rule is not frozen. |
| INCOMPATIBLE | The slices cannot be combined without an undocumented translation. |
| NOT_APPLICABLE | The row is intentionally outside the first mandatory experiment scope. |

Current machine-readable counts are: EXACT 7; COMPATIBLE 8;
COMPATIBLE_WITH_PROFILE 9; AMBIGUOUS 11; INCOMPATIBLE 0; NOT_APPLICABLE 1.
Every ambiguous row carries a finding ID.

## Integrated conclusions

### Identity and proposition

`effect_id` remains logical and `attempt_id` remains per-dispatch. Provider and
transport IDs are explicitly non-substitutive. The R2 proposition record is a
good canonical anchor for effect, predicate, stage, action, and applicability
slots. The remaining weakness is not identity naming; it is the absence of a
complete supplied collection and deterministic applicability/digest rules.

### Authority

The B result remains compatible with D. Grant relation, effective-authority
composition, and event-time validity are independent. No compatibility row
allows `ATTENUATED`, `CONTAINED`, or an observed effect to become `AUTHORIZED`.

### Settlement and projection

The C result remains native. The A projection is profile-bound and references
the native C result and proposition. Provider acceptance cannot project to an
arbitrary later stage, and incomplete negative reads cannot project to bounded
non-occurrence.

### Experiment boundaries

The public-to-scorer reverse edge is gone. The arm manifest discriminator is
strong. However, the source schema membership, extension namespace, feature
profile, normalization profile, and orchestrator/arm role visibility are not
fully compatible as machine-enforceable artifacts.

### External verification

The intended inputs are portable, but `LIN-001`–`LIN-007` need a declared
validation bundle and scope. Until that is defined, a private store could be
used to supply the missing records without violating an explicit structural
contract. The stack therefore cannot yet claim deterministic third-party
reproduction.
