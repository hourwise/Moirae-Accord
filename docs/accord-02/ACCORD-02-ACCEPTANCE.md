# ACCORD-02 Acceptance

## Status

**ACCORD-02 = ACCEPTED** within the bounded scope recorded here: the portable research/specification package and preregistered experiment design. This record is committed on the acceptance branch, promoted to `main` by fast-forward, and identified by the annotated tag `accord-02-accepted-v1`.

The acceptance commit is the Git commit containing this acceptance record, the seal, and the machine-readable manifest. Its exact SHA, tree, parent, and tag target are verified in the final acceptance report and repository metadata; those values are intentionally not embedded as a self-hashing requirement in this file.

## Acceptance basis

The separate ACCORD-02E-R5 acceptance-readiness review concluded **READY_WITH_NONBLOCKING_NOTES** at review commit `46c62ed4ff3638659a5c70663637b3cf0df2e2cc` (tree `4cdea4c031ed7dbbd1e71eeee5f17a9d1e6c2772`). It reported zero open BLOCKING findings and zero open MAJOR findings. The review set is preserved in:

- [Integrated review](ACCORD-02E-R5-INTEGRATED-REVIEW.md)
- [Package-closure review](ACCORD-02E-R5-PACKAGE-CLOSURE-REVIEW.md)
- [Cross-slice compatibility](ACCORD-02E-R5-CROSS-SLICE-COMPATIBILITY.md)
- [Adversarial cases](ACCORD-02E-R5-ADVERSARIAL-CASES.md)
- [Claim audit](ACCORD-02E-R5-CLAIM-AUDIT.md)
- [Acceptance readiness](ACCORD-02E-R5-ACCEPTANCE-READINESS.md)
- [Machine-readable findings](accord-02e-r5-review-findings.json)
- [Compatibility matrix](accord-02e-r5-compatibility-matrix.json)
- [Validation-rule review](accord-02e-r5-validation-rule-review.json)

The accepted ACCORD-01 base is `e748028d3ac05112163765afc65ef4224933f6a1`, and the complete ordered candidate chain is recorded in `accord-02-acceptance-manifest.json`.

## Accepted scope

### ACCORD-02A — portable linked records and verifier contract

Accepted scope includes portable semantic identities, transport-neutral linked records, trust-root-aware verifier inputs, qualified verifier projections, evidence classes, and separation of effect attempts from observations.

### ACCORD-02B — authority attenuation and composition

Accepted scope includes component-wise grant relations, direct attenuation, widening, effective-authority composition, siblings, multi-hop delegation, parent-mediated laundering analysis, and revocation/expiry temporal semantics.

### ACCORD-02C — evidence-backed effect settlement

Accepted scope preserves separation among intent, dispatch, occurrence, observation, attribution, causality, partial or staged effect, and settlement.

### ACCORD-02D — preregistered falsification experiment

Accepted scope includes ARM-A durable execution, ARM-B provider observation, ARM-C lightweight classification, and ARM-D Accord; depth-2-or-greater delegation; sibling composition; honest, lying, partially lying, and faulty delegates; multiple evidence affordances; frozen faults and authority scenarios; hidden oracle; metrics; categorical failures; and falsifiable negative outcomes.

### R1–R5 remediation history

Accepted as part of the final specification history are the remediations establishing oracle/scorer isolation, settlement projection mapping, authority-axis separation, typed lineage, canonical proposition binding, machine-readable arm boundaries, validation bundles, normative validation rules, extension and source-schema registries, role visibility, normalization and classifier-feature profiles, predicate applicability, canonicalization/digest semantics, and exact package closure.

## Active accepted package

| Property | Accepted value |
| --- | --- |
| Package ID | `urn:moirae:accord-02r5:specification-package` |
| Version | `0.1` |
| Policy | `CLOSED_EXACT_VERSION` |
| Schema contracts | 44 |
| Profile contracts | 31 |
| Canonicalization profiles | 1 |
| Role values | 9 |
| Active source-schema pairs | 13 |
| Active arm profile references | 16 |
| Active validation rules | 82 |

The accepted package is resolved by exact package identity and version. No implicit latest, compatible, default, repository-local, or runtime-private contract substitution is part of the accepted scope.

## Validation status

The final review recorded zero open BLOCKING findings and zero open MAJOR findings. Its active-rule review recorded 82 active rules: 19 deterministic, 63 deterministic-with-profile, 0 ambiguous, 0 unevaluable, 0 contradictory, and 0 dependency cycles. The focused compatibility matrix recorded 12 `EXACT`, 3 `COMPATIBLE_WITH_PROFILE`, 0 `AMBIGUOUS`, and 0 `INCOMPATIBLE` rows.

These are specification-review results, not runtime implementation or empirical results.

## Nonblocking notes carried into acceptance

1. `E2E-R4-NOTE-001`: no standards-complete external JSON Schema or independent implementation interoperability run has yet been performed. This is deferred to `CONFORMANCE_IMPLEMENTATION`.
2. `E2E-MINOR-002`: A2A-shaped transport remains optional for the first scored experiment. The currently specified mandatory T1/T2 transport coverage remains in force.

## Bounded research claim

ACCORD-02 establishes a frozen portable-record, authority-composition, effect-settlement, validation-contract, and falsification-experiment specification suitable for subsequent conformance implementation and empirical testing. The accepted specification permits negative, null, or falsifying outcomes and does not preclaim improvement over ARM-A, ARM-B, or ARM-C.

## External-verification boundary

The accepted external-verification conclusion is **SUPPORTED_WITH_QUALIFICATION**:

> Under the accepted ACCORD-02 self-contained validation profile, verification depends on the supplied instance validation bundle plus the exact versioned ACCORD-02 specification-contract package identified by that bundle, including declared schemas, profiles, registries, canonicalization contracts, trust roots/evidence inputs, and normative validation rules. The specification does not require Accord-private runtime state or scorer-only material for the declared verifier decision.

This remains relative to supplied evidence and trust roots. Evidence may be incomplete or false; provider correctness is not guaranteed; implementation interoperability has not yet been demonstrated; and the specification does not establish arbitrary real-world truth, exactly-once external effects, complete mediation, universal prevention, or unobserved facts.

## Explicitly not demonstrated

Acceptance does not claim:

- empirical superiority over ARM-A, ARM-B, or ARM-C;
- measured reductions in false confirmation, indeterminacy, duplicate effects, or human escalation;
- independent-validator or JSON Schema engine interoperability;
- runtime conformance, provider integration, production readiness, exactly-once effects, or complete mediation;
- provider honesty or arbitrary real-world truth;
- completed experiment results.

No experiment has run. No classifier has been trained. No validator or verifier has been implemented.

## Review history

The preserved integrated-review sequence is:

`AMEND → AMEND → AMEND → AMEND → AMEND → READY_WITH_NONBLOCKING_NOTES`

The repeated adversarial review and remediation history is preserved as evidence of the review process; it is not rewritten by this acceptance record.

## Next-phase boundary

Future conformance-validator, portable-verifier, frozen-fixture, harness, or pre-experiment certification work requires a new separately authorized task. This acceptance does not begin ACCORD-03 or any implementation phase.
