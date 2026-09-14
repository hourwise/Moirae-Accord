# ACCORD-02E-R1 — Cross-Slice Compatibility Review

This matrix is a fresh re-evaluation of the remediated A/B/C/D stack. The
machine-readable form is
[accord-02e-r1-compatibility-matrix.json](./accord-02e-r1-compatibility-matrix.json).

## Status counts

| Status | Count |
| --- | ---: |
| EXACT | 14 |
| COMPATIBLE | 3 |
| COMPATIBLE_WITH_PROFILE | 13 |
| AMBIGUOUS | 12 |
| INCOMPATIBLE | 2 |
| NOT_APPLICABLE | 0 |

Every AMBIGUOUS or INCOMPATIBLE row has one or more linked findings in the
machine-readable matrix.

## Identity and lineage

The logical identities remain coherent: principal, grant, intent, task,
delegation, effect, attempt, observation, and evidence identifiers retain
their intended meanings. Provider and transport identifiers remain separate
correlation values.

The experiment-facing lineage is only profile-compatible. Typed references
identify record categories, but they do not by themselves resolve the record,
prove that it belongs to the current run, or equate duplicated IDs across the
record graph. This leaves `E2E-MAJOR-003` partially closed.

## Authority and effect

B relation values, B effective-authority states, C authority statuses, and D
event-time validity are exact or profile-compatible. They can represent
invalid authority with supported occurrence and do not rewrite factual history.

The C native axes also map cleanly into D’s native axes. The A projection is
only profile-compatible because the standalone A schema does not require the
R1 map and native C reference that the projection rules require.

## Input and oracle boundary

This is the principal incompatibility:

- the public catalog directly names the scorer-only catalog;
- a manifest references a profile with an unconstrained string;
- field membership is asserted rather than checked by the schema;
- arbitrary nested objects may be carried in manifest and raw-output values;
- A portable-record extensions remain open and can enter ARM-D through a
  broadly typed portable bundle field.

The intended boundary is clear in prose, but the machine-readable object graph
does not make every invalid path rejectable.

## Predicate, stage, and evidence

Predicate/stage/action/target/resource/recipient/provider binding is available
and C profile rules are conservative. The D schema requires descriptors in
important paths. However, cross-field equality and profile applicability are
not expressed as constraints, so a future verifier/scorer must perform checks
outside the schemas. These rows remain AMBIGUOUS for acceptance purposes.

## Transport and trust roots

Transport metadata remains non-authoritative. T1 and T2 satisfy the minimum
first-experiment transport requirement; T3 A2A remains optional. Trust roots,
evidence profiles, and provider operation identifiers remain distinct from
authority and effect semantics.

## Matrix conclusion

The stack has a coherent conceptual core, but it is not yet a closed,
machine-auditable contract at the arm-input, A-projection, lineage, and
cross-binding boundaries. The integrated verdict is AMEND.
