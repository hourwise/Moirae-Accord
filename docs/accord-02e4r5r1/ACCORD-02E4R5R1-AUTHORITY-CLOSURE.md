# ACCORD-02E4R5R1 authority-bound conformance closure

Status: `CANDIDATE_UNACCEPTED`. Package family and version remain `urn:moirae:accord-02r5:specification-package`, `0.2`.

## Diagnosis and semantic classification

Phase A reproduced the decisive R5 defect outside the repository: a subject-only mutation failed, the same subject mutation plus a matching assertion-local expected value passed, and redirecting the assertion to unrelated `/registry_version` with matching `"0.2"` passed. The complete 54-record diagnosis is preserved in the authority matrix together with inherited family, inherited failure code, original subject binding, and repaired semantic requirement.

The classification is derived from the 104 inherited rule records:

- 42 `EXECUTABLE_CONFORMANCE_RULE` records use declared deterministic invariants and contain no inline expected literal.
- 12 `INTERNAL_DESIGN_INVARIANT` records preserve useful candidate-owned consistency checks but are excluded from conformance counts.
- 50 `DEFERRED_NO_SUBJECT_ARTIFACT` records remain honestly deferred.

## Normative model

The package-specific invariant registry declares 17 active invariants over nine bounded procedures. Each procedure declares typed arguments, resolution, normalization, result, missing/ambiguity behavior, and fail-closed behavior. `RULE_EXPECTATION_AUTHORITY_COMPLETE` requires exactly one derived or authority-bound form for every conformance rule. Both the authority matrix and invariant registry are semantic-integrity bound by the candidate package.

The accepted 0.1 package and accepted vector catalog are registered as active accepted sources and carry both RFC 8785/JCS SHA-256 and raw-file-byte SHA-256. The vector catalog has one registration and two roles (`CATALOG_BINDING`, `VECTOR_SOURCE`). The accepted base is a typed package identity, not a bare path.

Normative reference discovery uses one declared exact-shape predicate. Independently implemented walkers derive the same 101-edge set and zero unresolved or ambiguous edges. Schema identity is explicit: for `SCHEMA`, document `$id` is registered `id + ':' + version`; `$schema` remains the Draft 2020-12 dialect URI.

The predicate registry is the single authority for `global_stage_order` and `implicit_transitivity`; the R1 partial-effect policy references it and carries no duplicate values. The prior unreachable `UNKNOWN_TUPLE`/`WRONG_STAGE` distinction is merged into `UNKNOWN_TUPLE_OR_WRONG_STAGE: REJECT`.

V013 now states only `CANDIDATE_FIXTURE_OF_SAME_SEMANTIC_CLASS_AS_ACCEPTED_V013`. Its relationship basis separates accepted fields from candidate-supplied interval, scope, retention, consistency, and observation-time fields. The exact-target, interval, retention, freshness, complete-read, and no-same-target-positive mechanics remain executable; an irrelevant positive item for a different effect proves target scoping.

## Independent execution and release gates

The primary and independent implementations share normative artifacts only and do not import each other or a common semantic helper. They independently derive all rule classes, invariant outcomes, reference edges, accepted-source integrity, expectation stability, and V013 result.

Expected clean result:

| Claim | Result |
|---|---:|
| Total declared | 104 |
| Conformance executed / pass / fail | 42 / 42 / 0 |
| Internal executed / pass / fail | 12 / 12 / 0 |
| Deferred | 50 |
| Unevaluable / ambiguous conformance | 0 / 0 |
| Accepted vectors | 23/23 |
| Expectation axes | 13/13 |
| Prohibitions | 31/31 |
| Accepted expected-object changes | 0 |

The real-system falsifier runs both evaluator subprocesses against disposable, no-Git exports. It covers subject-only and co-mutation attacks; authority mutation/disagreement; pointer redirection; subject/authority swap; authority removal/retarget; derivation mutation; invariant deletion; identity/reference failures; raw-byte and semantic accepted-source mutations; LF/CRLF; lineage and canonicalization mutations; V013 and partial-effect attacks; semantic-class attacks; authority omission; and clean-export execution.

Positive usefulness remains: bound resource/effect receipt, independently corroborated occurrence, `PARTIAL_EFFECT`, and `NON_OCCURRENCE_SUPPORTED` all remain represented; the vector set does not retreat to all-unknown.

## Delete-the-primary answer

YES. With the builder and primary certifier absent, the normative artifacts, accepted sources, pinned public dependencies, and independent evaluator determine standards validation, lineage, dual integrity, identities, references, invariant closure, all semantic classes and results, V013, partial effect, and expectation stability. For each conformance rule, what should be true comes from a declared deterministic derivation over normative inputs, never from the subject itself or an assertion-local copied literal.

No acceptance, experiment execution, push, tag, merge, or main advancement is performed by this candidate.
