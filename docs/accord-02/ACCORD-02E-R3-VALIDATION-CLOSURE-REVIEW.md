# ACCORD-02E-R3 — Validation Closure Review

## Rule-classification standard

The review treated a rule as closed only when its inputs, scope, profile
resolution, failure semantics, and dependencies were all explicit. The
R3-added rule text is syntactically well formed, but `BND-004` and `BND-005`
are not independently evaluable from the supplied bundle envelopes:

- `BND-004` requires a structural contract “in the supplied scope”, but the
  bundle has no schema-contract inventory and permits arbitrary `content`.
- `BND-005` requires “profile records or supplied profile definitions”, but
  active profile references are `record_type: PROFILE` and neither bundle
  inventory admits that type nor the reference contains a definition.

All downstream profile-dependent rules are deterministic only conditional on
repairing that scope contract. They are not evidence that the current bundle
is self-contained.

## Combined 71-rule result

The machine-readable companion [`accord-02e-r3-validation-rule-review.json`](./accord-02e-r3-validation-rule-review.json)
represents all 33 preserved R2 rules and all 38 R3 rules.

| Independent classification | Count | Interpretation |
|---|---:|---|
| DETERMINISTIC | 18 | Decidable from closed structure or scope facts already present. |
| DETERMINISTIC_WITH_PROFILE | 51 | Semantics are deterministic once the named profile/registry is actually supplied and resolved. |
| AMBIGUOUS | 0 | No rule was classified ambiguous as an abstract rule. |
| UNEVALUABLE | 2 | `BND-004` and `BND-005` cannot be evaluated from the current declared bundle model. |
| CONTRADICTORY | 0 | No logical contradiction was found. |
| NOT_APPLICABLE | 0 | Every listed rule is relevant to at least one declared admission/scoring path. |

The zero ambiguous count does not yield readiness: the two unevaluable bundle
rules are acceptance-critical blockers, and they make many profile-dependent
rules unavailable in an actual self-contained run.

## Rule families

### Bundle and scope

`BND-001` through `BND-003` are structurally decidable. `BND-004` and
`BND-005` are the acceptance-critical gap. The schemas declare inventory
entries and profile references, but not the records/definitions needed to
resolve the references.

### Run and lineage

Run schemas bind IDs, arm, scenario, manifest, profiles, and produced results.
`RUN-001` through `RUN-004` are deterministic with those records present, but
their admission depends on the unresolved profile and structural-contract
scope. `LIN-001`, `LIN-003`, `LIN-006`, and `LIN-007` likewise cannot be
independently executed until record targets and contracts are resolvable.

### Extensions and source membership

The registry categories and source-schema membership fields are appropriately
explicit. `EXT-001`–`EXT-006` and `SRC-001`–`SRC-004` are deterministic with
the relevant registry supplied, but the active registry references currently
cannot resolve through the bundle envelope.

### Visibility, normalization, and classifier features

The profiles provide a useful finite vocabulary and prohibit scorer truth in
the intended paths. `VIS-001`, `NORM-001`–`NORM-005`, and `CLF-001`–`CLF-004`
remain profile-dependent. In addition, role membership is not closed by the
role-visibility schema: field-rule producer/consumer values are unrestricted
strings.

### Predicate, digest, and proposition

The predicate profile expresses REQUIRED/OPTIONAL/NOT_APPLICABLE, and the
proposition record remains the semantic anchor. `PRED-001`–`PRED-004` are
profile-dependent. `DIGEST-001` is not fully self-contained for generic bundle
entries because canonicalization is not required at the entry level.
`PROP-006` correctly prevents two descriptors with one proposition ID, but it
does not by itself define equivalence between different proposition IDs.

## Dependency review

The declared R3 dependency graph is acyclic, and all listed dependency IDs
resolve to a rule. The graph is therefore structurally sound. It does not,
however, create the missing profile/schema records; an acyclic graph over an
unresolvable input remains unevaluable.

## Validation bundle review

The three envelope classes have the right information-boundary intent:

- verifier bundle: portable records and verifier profiles, no scorer truth;
- experiment bundle: verifier scope plus run, arm, source, visibility,
  normalization, classifier, and lineage records;
- scorer bundle: experiment scope plus expectations/oracle/score material,
  explicitly scorer-only.

The missing piece is a resolvable inventory contract. `active_profiles` is a
map of references, not a collection of profile records, and `record_type:
PROFILE` is not admitted by the record inventory. The schema also does not
admit structural schema contracts or a schema registry that can validate an
arbitrary `content` member selected by `schema_id`/`schema_version`.

## External-verification statement

The R3 external-verification statement is **NOT_SUPPORTED as written**. It
becomes supportable only after the bundle includes or explicitly supplies the
profile definitions and schema-contract registry needed by the rules.

The review does not claim that any evidence is true, that a provider is
trustworthy, or that an unobserved external fact is known.
