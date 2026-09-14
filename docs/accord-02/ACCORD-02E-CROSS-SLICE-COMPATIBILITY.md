# ACCORD-02E — Cross-Slice Compatibility Matrix

This matrix reviews the frozen ACCORD-02A/B/C/D artifacts without changing
them. `EXACT` means the same machine-readable meaning and binding are used.
`COMPATIBLE` means the linkage is direct but may use a wrapper or reference.
`COMPATIBLE_WITH_PROFILE` means the linkage is safe only when the named profile
or an explicit external contract supplies the missing semantics. `AMBIGUOUS`
means a future implementation would need undocumented translation. There are no
confirmed hard `INCOMPATIBLE` pairs in the reviewed stack, but the ambiguous
rows are acceptance-blocking until amended.

## 1. Summary

| Status | Count |
| --- | ---: |
| `EXACT` | 16 |
| `COMPATIBLE` | 6 |
| `COMPATIBLE_WITH_PROFILE` | 11 |
| `AMBIGUOUS` | 12 |
| `INCOMPATIBLE` | 0 |
| `NOT_APPLICABLE` | 2 |

Every `AMBIGUOUS` row has one or more finding IDs in the machine-readable
matrix. The full entries are in
[accord-02e-compatibility-matrix.json](./accord-02e-compatibility-matrix.json).

## 2. Identity compatibility

| Linkage | Status | Finding |
| --- | --- | --- |
| `principal_id` across A/B/C/D | `EXACT` | — |
| `grant_id` across A/B/C/D | `EXACT` | — |
| `intent_id` across A/B/C/D | `EXACT` | — |
| `task_id` across A/B/C/D | `EXACT` | — |
| `delegation_id` across A/B/C/D | `EXACT` | — |
| `effect_id` as logical effect across A/B/C/D | `EXACT` | — |
| `attempt_id` as per-dispatch identity | `EXACT` | — |
| `observation_id` into C evidence assessment | `COMPATIBLE_WITH_PROFILE` | — |
| `evidence_id` into C/D evidence references | `COMPATIBLE` | — |
| `provider_operation_id` versus Accord IDs | `COMPATIBLE_WITH_PROFILE` | `E2E-MINOR-001` |
| A/C `verifier_run_id` to D `run_id` | `AMBIGUOUS` | `E2E-MAJOR-003` |
| A/C `result_id` to D `result_record_id` | `AMBIGUOUS` | `E2E-MAJOR-003` |
| C `predicate_id` and stage to A portable records | `AMBIGUOUS` | `E2E-MAJOR-004` |

The core linked-record identities are sound. The result and predicate identity
gaps concern lineage and machine-readable cross-slice references rather than the
meaning of the core IDs themselves.

## 3. Authority-result compatibility

| Linkage | Status | Finding |
| --- | --- | --- |
| A grant/delegation records into B relation analysis | `COMPATIBLE` | — |
| B `aggregate_relation` into C/D authority axis | `AMBIGUOUS` | `E2E-MAJOR-002` |
| B `effective_authority.state` into C/D authority axis | `AMBIGUOUS` | `E2E-MAJOR-002` |
| B relation analysis into `AUTHORIZED`/`INVALID_AUTHORITY` | `AMBIGUOUS` | `E2E-MAJOR-002` |
| B comparison profile and C settlement profile | `COMPATIBLE_WITH_PROFILE` | — |
| B revocation/expiry observations into C event-time authority | `COMPATIBLE_WITH_PROFILE` | — |
| B transport non-authority invariant into D transports | `EXACT` | — |

`ATTENUATED`, `CONTAINED`, `POSSIBLE_WIDENING`, and `AUTHORIZED` are not
synonyms. The stack currently allows them to be carried through a common
`relation_or_state`/status area without a required semantic discriminator.

## 4. Settlement-result compatibility

| Linkage | Status | Finding |
| --- | --- | --- |
| C occurrence axis into D `occurrence` | `EXACT` | — |
| C attribution axis into D `attribution` | `EXACT` | — |
| C causality axis into D `causality` | `EXACT` | — |
| C freshness axis into D `freshness` | `EXACT` | — |
| C duplication axis into D `duplication` | `EXACT` | — |
| C profile compatibility into D `profile_compatibility` | `EXACT` | — |
| C `result_id` referenced by D `result_ref` | `COMPATIBLE` | `E2E-MAJOR-003` |
| A `VERIFIED`/`CORROBORATED` into C `EFFECT_SUPPORTED` | `AMBIGUOUS` | `E2E-MAJOR-001` |
| A `NO_EFFECT_OBSERVED` into C `NON_OCCURRENCE_SUPPORTED` | `AMBIGUOUS` | `E2E-MAJOR-001` |
| A `UNKNOWN_PENDING`/`UNKNOWN_TERMINAL` into C `UNKNOWN`/`UNRESOLVED` | `AMBIGUOUS` | `E2E-MAJOR-001` |
| C staged predicate into D experiment settlement | `AMBIGUOUS` | `E2E-MAJOR-004` |

The C axis values are conservative and machine-readable. The ambiguity is the
missing normative mapping from the older A result wrapper to the newer C
multidimensional result, not an endorsement of the older labels as universal
truth.

## 5. Time and evidence compatibility

| Linkage | Status | Finding |
| --- | --- | --- |
| A issued/attempted/observed times into C temporal profile | `COMPATIBLE_WITH_PROFILE` | — |
| C event time versus observation time distinction | `EXACT` | — |
| D run/dispatch/provider/observation/verification timestamps | `COMPATIBLE` | — |
| C freshness and complete-negative requirements into D metrics | `COMPATIBLE` | — |
| A evidence artifact trust root into C trust assumptions | `COMPATIBLE_WITH_PROFILE` | — |
| C provenance/binding assessments into D observed evidence | `COMPATIBLE_WITH_PROFILE` | `E2E-MAJOR-004` |
| Unknown settlement-bearing extensions | `COMPATIBLE_WITH_PROFILE` | — |

The profile-dependent rows are acceptable as research design inputs, provided
the future harness freezes the selected profiles before scoring.

## 6. Transport, verifier, and experiment compatibility

| Linkage | Status | Finding |
| --- | --- | --- |
| Transport ID as correlation only | `EXACT` | — |
| Local/native and MCP-shaped profiles | `COMPATIBLE` | — |
| A2A-shaped carriage profile | `COMPATIBLE_WITH_PROFILE` | — |
| A verifier input bundle plus C profile/evidence | `COMPATIBLE_WITH_PROFILE` | `E2E-MAJOR-003` |
| D scenario/run records linked to portable records | `COMPATIBLE` | — |
| Public scenario catalog versus hidden oracle | `AMBIGUOUS` | `E2E-BLOCK-001` |
| Public scenario metadata versus baseline input boundary | `AMBIGUOUS` | `E2E-MAJOR-005` |
| Scorer-only material versus portable verifier | `COMPATIBLE_WITH_PROFILE` | `E2E-BLOCK-001` |

## 7. Compatibility conclusion

The A/B/C/D stack has a compatible conceptual architecture, but it is not yet a
fully closed machine-readable contract. Formal acceptance requires resolving the
six ambiguous rows, especially the oracle separation and result-label/identity
translation rows. No prior slice is amended by this review.
