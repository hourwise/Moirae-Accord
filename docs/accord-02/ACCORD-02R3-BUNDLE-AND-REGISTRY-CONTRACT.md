# ACCORD-02R3 — Bundle, Registry, and Profile Contract

## Validation scopes

`validation_scope` means the exact records and active profiles supplied inside a
named bundle. `resolve(type, id, validation_scope)` searches only that set and
returns exactly one of `RESOLVED`, `MISSING`, `DUPLICATE`, `WRONG_TYPE`, or
`STRUCTURALLY_INVALID`. Filesystem paths, databases, network requests, caches,
and private Accord state are not implicit members of the scope.

The verifier bundle is self-contained for verifier reproduction. The experiment
bundle adds scenario, run, arm manifest, raw output, normalized claim, profile,
and lineage records. The scorer bundle adds expectations, the hidden oracle, and
score records while declaring `SCORER_ONLY`, `system_under_test_visible=false`,
`arm_input_allowed=false`, and `verifier_input_allowed=false`.

## Record inventory

The verifier inventory is conditional: it contains the portable bundle and only
the Principal, Grant, Intent, Task, Delegation, Attempt, Observation, Evidence,
Proposition, authority analysis, native settlement, verifier run/result, trust,
authority, settlement, projection, extension, predicate, and detached-evidence
records required by its active profiles. The experiment inventory additionally
contains the scenario definition, experiment run, sanitized manifest, raw output,
normalization claim/profile, classifier profile where applicable, source registry,
role-visibility profile, and validation-rule profile.

Each entry carries record type, record ID, schema ID/version, content, and an
optional content digest. The inventory label is the typed envelope identity;
the supplied schema ID/version governs the native content shape, including the
lower-case native A/C record types where those schemas define them. A valid
record in another run is still foreign if it is outside the current scope or
fails the current lineage/proposition/profile bindings.

## Registries and visibility

The extension, source-schema, role-visibility, normalization, classifier, and
predicate-applicability catalogs are supplied by profile reference. Unknown
authority/effect/verifier extensions are `UNKNOWN_FORBIDDEN`; a non-semantic
extension cannot influence any conclusion. Source membership is determined by
schema ID/version in the source registry, never by a filename or payload shape.

Orchestration condition labels such as delegate behavior, injected fault, and
idempotency condition are fixture/orchestrator configuration unless the role
profile explicitly exposes an observable consequence. Scorer truth is scorer
only. A profile violation is an admission failure, not an inferred external
effect fact.

## Run lineage

An experiment run binds scenario, arm, sanitized manifest (with its own
manifest identity), experiment/profile versions, source registry, visibility
profile, validation-rule profile, and any normalization/classifier profile. A
verifier run binds the verifier bundle, authority/settlement/projection/
predicate/extension/validation profiles, its produced result, and an explicit
experiment-run reference whenever it is used in an experiment. Typed
references plus `LIN-*`, `RUN-*`, and `DIGEST-*` rules reject missing,
duplicate, foreign, wrong-type, mismatched, or structurally invalid targets.

## Normalization

The normalizer consumes only one raw arm output and its applicable frozen
profile. It emits a normalized claim such as positive, negative, partial,
provider-accepted-only, duplicate-risk, unknown, or no-claim. It cannot consult
an expectation, oracle, native settlement result unavailable to that arm, or
categorical failure result. The scorer compares the normalized claim to truth
only after normalization.

## R4 exact-contract closure

For the current candidate stack, the package and profile-resolution rules in
`ACCORD-02R4-SPECIFICATION-PACKAGE-CONTRACT.md` govern the phrase “supplied by
profile reference” above. A verifier or experiment bundle must carry the exact
`specification_package_ref`; the package manifest closes the schema/profile/
registry inventory and pins each active contract version. The R3 text is
therefore interpreted through the R4 base-plus-overlay rule contract, not
through an implementation-defined catalog or ambient lookup.
