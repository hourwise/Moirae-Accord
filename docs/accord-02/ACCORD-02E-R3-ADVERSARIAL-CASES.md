# ACCORD-02E-R3 — Adversarial Cases

The cases below are specification-level replays. None was executed against a
runtime or experiment harness.

## Historical cases

| Case family | Result | Review conclusion |
|---|---|---|
| ADV-01–ADV-17 | RESISTED / bounded | Stale evidence, wrong recipient/resource, authority/effect separation, revocation, duplicates, and staged effects remain conservatively represented. |
| ADV-18 | PARTIALLY_RESISTED | Public scorer locator is absent, but scenario-ID opacity is a declaration rather than a deterministic information-flow control. |
| ADV-19 | RESISTED_IN_PROFILE | ARM-C cannot select ARM-D semantics through the discriminated profile, but active profile resolution is not self-contained. |
| ADV-R1-01 | PARTIALLY_RESISTED | Extension registry and unknown-extension rule exist; the active registry cannot be resolved from the bundle. |
| ADV-R1-07 | PARTIALLY_RESISTED | Typed lineage rejects wrong types conceptually; foreign-result resolution still depends on the incomplete scope contract. |
| ADV-R2-01 | OPEN_AT_SCOPE | Missing native result is detectable only if the declared scope is complete; the profile/scope gap remains. |
| ADV-R2-04 | RESISTED_IN_PROFILE | Canonical proposition collision is covered by `PROP-006`; the proposition/profile target must still resolve. |
| ADV-R2-05 | PARTIALLY_RESISTED | Digest mismatch is defined, but generic canonicalization is not fixed for every entry. |
| ADV-R2-06 | RESISTED_IN_PROFILE | Normalization forbids oracle use; profile resolution remains a prerequisite. |
| ADV-R2-07 | PARTIALLY_RESISTED | Visibility profile marks fixture-private conditions, but role membership is not closed by schema. |

## New R3 cases

| Case | Expected/observed specification result |
|---|---|
| ADV-R3-01 — missing active extension registry | **BLOCKED**: active reference cannot resolve as a supplied registry record. |
| ADV-R3-02 — unknown portable extension | **NO STRENGTHENING** once the registry is supplied; current bundle cannot prove registry presence. |
| ADV-R3-03 — source-schema spoof | **REJECTED IN PROFILE** by `SRC-001`/`SRC-004`; current active source registry reference is unresolved. |
| ADV-R3-04 — fixture-private condition leak | **REJECTED IN PROFILE** by `VIS-001`; role membership gap leaves a major residual. |
| ADV-R3-05 — truth-dependent normalization | **REJECTED** by `NORM-001`/`NORM-002`/`NORM-005`; no oracle input is permitted to normalization. |
| ADV-R3-06 — unknown classifier feature | **REJECTED IN PROFILE** by `CLF-001`/`CLF-004`; feature profile must first resolve. |
| ADV-R3-07 — missing predicate profile | **BLOCKED** rather than positive settlement; `PRED-001`/`PRED-002` need the unresolved profile. |
| ADV-R3-08 — wrong digest | **FAILURE**, not an effect or authority conclusion; generic canonicalization remains a major gap. |
| ADV-R3-09 — missing experiment run | **MISSING** under a complete scope; current bundle lineage is not sufficiently declared. |
| ADV-R3-10 — hidden filesystem lookup | **NON-CONFORMANT** under the stated self-contained profile. |
| ADV-R3-11 — same raw output, different claim | **NON-CONFORMANT** under `NORM-003`; profile contents are not yet resolvable from the bundle. |
| ADV-R3-12 — scorer bundle used as verifier bundle | **SCHEMA/INFORMATION-CLASS FAILURE**. |

## Projection and authority regressions

Provider acceptance cannot project to a final effect; incomplete absence cannot
project to non-occurrence; occurrence cannot add attribution or causality; and
effect settlement cannot create authority. `ATTENUATED`, `CONTAINED`, and
`EQUIVALENT` remain distinct from event-time authorization. These attacks were
resisted by the reviewed schemas/rules, subject to the unresolved profile
scope.

## Complete historical identifier coverage

The static replay covered every prior identifier. The compact disposition is:

| IDs | Disposition |
|---|---|
| ADV-01, ADV-02, ADV-03, ADV-04, ADV-05 | RESISTED; stale reads, wrong bindings, and sibling widening remain conservative. |
| ADV-06, ADV-07, ADV-08, ADV-09, ADV-10 | RESISTED; laundering, revocation, retention, and idempotency boundaries remain explicit. |
| ADV-11, ADV-12, ADV-13, ADV-14, ADV-15 | RESISTED; transport completion, conflicts, reopening, trust roots, and unknown extensions do not strengthen claims. |
| ADV-16, ADV-17 | RESISTED; provider-operation reuse and effect-ID reuse do not merge semantic identities. |
| ADV-18 | PARTIALLY_RESISTED; no scorer locator, but semantic ID opacity is not machine-proven. |
| ADV-19 | RESISTED_IN_PROFILE; ARM-C cannot select ARM-D semantics, subject to unresolved profile scope. |
| ADV-20 | RESISTED; universal UNKNOWN is scoreable as unattractive rather than an automatic win. |
| ADV-R1-01, ADV-R1-02, ADV-R1-03, ADV-R1-04, ADV-R1-05 | RESISTED_IN_PROFILE; extension smuggling, cross-arm substitution, wrong predicate/stage, and authority/effect separation are specified. |
| ADV-R1-06, ADV-R1-07, ADV-R1-08, ADV-R1-09, ADV-R1-10 | RESISTED_IN_PROFILE; unknown binding, foreign results, projection strengthening, negative scope, and scorer contamination are specified. |
| R2-ADV-01, R2-ADV-02, R2-ADV-03, R2-ADV-04, R2-ADV-05 | RESISTED_IN_PROFILE; public reverse references, wrong profile, nested oracle, proposition, and digest attacks are addressed. |
| R2-ADV-06, R2-ADV-07, R2-ADV-08, R2-ADV-09, R2-ADV-10 | RESISTED_IN_PROFILE; classifier, visibility, raw output, nonexistent reference, and provider-ID substitution are addressed. |
| R2-ADV-11, R2-ADV-12, R2-ADV-13, R2-ADV-14, R2-ADV-15 | RESISTED_IN_PROFILE; proposition binding, unknown/N-A, fairness, and untrusted-output boundaries are addressed. |
