# ACCORD-02E4 — Normative Settlement Amendment Draft

Status: **AMENDMENT CANDIDATE — NOT ACCEPTED**
Verdict: **AMENDMENT_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW**

## A. Scope and immutability

This candidate is based on the E3 analysis branch at `f8bdc730d1c3258cb687d838d94c2faa545ba438`. The sealed ACCORD-02 package remains immutable. Candidate package version `0.2` is a distinct, exact version and does not rewrite package `0.1`, accepted examples, historical reviews, remediation evidence, ACCORD-03, or `main`.

The candidate uses the human-authorized **MODIFIED OPTION D — TYPED HYBRID**. It resolves the remaining C-stage ambiguity without introducing a new research question or changing the authority/effect, evidence, oracle, or experiment architecture.

## B. Candidate package

The machine-readable candidate package is [`accord-02e4-specification-package-0.2.json`](./accord-02e4-specification-package-0.2.json). It retains the package ID `urn:moirae:accord-02r5:specification-package`, binds the sealed 0.1 package by exact SHA-256, and uses `CLOSED_EXACT_VERSION` with candidate version `0.2`.

The candidate composition is finite:

| Contract class | Sealed base | Candidate change | Effective |
|---|---:|---:|---:|
| Schema contracts | 44 | +5 | 49 |
| Profile contracts | 31 | replace 2, +1 | 32 |
| Canonicalization profiles | 1 | 0 | 1 |
| Roles | 9 | 0 | 9 |
| Active source-schema pairs | 13 | 0 | 13 |
| Active arm profile references | 16 | explicit exact-version rewrites | 16 |
| Active validation rules | 82 | 0 | 82 |

No undeclared filesystem, repository, package, profile, registry, or implementation catalog is in scope.

## C. Canonical predicate identity

The canonical resolution key is exactly `(predicate_id, stage)`. The canonical identifiers are the accepted C-vector predicate URNs. There is no second `profile_predicate_id` namespace and no lexical fallback.

The authoritative binding vocabulary is the existing C `bindingName` vocabulary: `principal_id`, `grant_id`, `intent_id`, `task_id`, `delegation_id`, `effect_id`, `attempt_id`, `observer_principal_id`, `issuer_principal_id`, `resource`, `action`, `recipient_or_counterparty`, `provider`, `external_identifier`, `predicate_id`, and `stage`.

The registry is [`accord-02e4-predicate-applicability-registry.json`](./accord-02e4-predicate-applicability-registry.json). Its schema is [`accord-02e4-predicate-registry.schema.json`](./schema/accord-02e4-predicate-registry.schema.json).

## D. Typed hybrid semantics

### Positive stage predicates

The candidate declares the following positive rows:

| Predicate | Stage | Kind | Required semantic point |
|---|---|---|---|
| `urn:accord:02c:predicate:provider-acceptance` | `provider_accepted` | `POSITIVE_STAGE` | Provider acceptance only; it is not recipient delivery. |
| `urn:accord:02c:predicate:resource-created` | `resource_created` | `POSITIVE_STAGE` | Resource creation only; visibility is not inferred. |
| `urn:accord:02c:predicate:recipient-ack` | `recipient_acknowledged` | `POSITIVE_STAGE` | Recipient binding is required. |

`recipient_acknowledged` has one explicit predecessor edge: `provider-acceptance/provider_accepted`. It is not a global stage order. A `PARTIAL_EFFECT` result is reachable only when the selected later target is unresolved, a declared predecessor is supported, the predecessor policy is satisfied, later-stage evidence is required, and the evidence is admissible and compatible. Empty predecessor sets and `ATOMIC_ONLY` rows cannot produce `PARTIAL_EFFECT`.

### Generic occurrence

`urn:accord:02c:predicate:external-effect` is explicitly typed as `GENERIC_OCCURRENCE` at stage `effect`. It has no predecessor and no successor. It asserts only that the named logical external effect occurred under the active profile. It does not entail a positive lifecycle stage, attribution, causality, authority, or exactly-once behavior. Positive-stage and generic-occurrence rows do not entail one another unless a future explicit registry mapping is added; candidate 0.2 declares none.

### Negative scope

`urn:accord:02c:predicate:complete-negative` is not a positive lifecycle stage. Its registry tuple is `(complete-negative, null)`, where `null` is an explicit not-applicable stage marker. A negative proposition must carry the actual `negated_predicate_id` and `negated_stage`, effect identity, bounded state-space/scope, interval, retention, read semantics, consistency, freshness, and complete evidence class. The negative contract is [`accord-02e4-negative-scope-proposition.schema.json`](./schema/accord-02e4-negative-scope-proposition.schema.json).

The E13 candidate correction binds the complete-negative claim to `external-effect/effect` without rewriting E13 in the sealed package. `NON_OCCURRENCE_SUPPORTED` remains scoped to that exact negated predicate/stage and declared interval. Silence, timeout, stale evidence, and incomplete reads remain insufficient.

### Unsupported row

`resource-visible/resource_visible` is an explicit `UNSUPPORTED` registry row. Candidate 0.2 does not invent an evidence capability, stage ordering, or settlement meaning for it.

## E. Candidate schemas and profiles

The candidate adds typed positive propositions, bounded negative propositions, the predicate registry, and the typed settlement vector catalog. The vector catalog is [`accord-02e4-settlement-vector-catalog.json`](./accord-02e4-settlement-vector-catalog.json); its schema is [`accord-02e4-settlement-vector-catalog.schema.json`](./schema/accord-02e4-settlement-vector-catalog.schema.json).

The two settlement profiles are complete candidate instances at version `0.2` and use the sealed C profile schema without changing that schema. They explicitly declare evidence classes, required bindings, time handling, integrity, freshness, corroboration, completeness, negative evidence, partial effect, retries, extension behavior, compatibility, reopening, and authority/effect orthogonality:

- [`accord-02e4-settlement-profile-conservative-v2.json`](./profiles/accord-02e4-settlement-profile-conservative-v2.json)
- [`accord-02e4-settlement-profile-incompatible-v2.json`](./profiles/accord-02e4-settlement-profile-incompatible-v2.json)

The profile audit is [`accord-02e4-profile-contract-audit.json`](./accord-02e4-profile-contract-audit.json): 16 active references, 16 resolved, 0 missing, 0 versionless, and 0 duplicates.

## F. Canonicalization applicability

The candidate reuses the existing RFC 8785 JCS / UTF-8 / SHA-256 method and does not introduce a cryptographic primitive. The package carries concrete applicability mappings for the new proposition forms and the vector catalog. Each mapping names the concrete schema ID/version, record type, canonicalization profile ID/version, digest field, content target, algorithm, and optionality. There is no generic “record-declared canonicalization” escape hatch.

For candidate propositions and the optional vector-catalog digest, the digest target is `record_without_integrity_content_digest`. A missing mapping is a validation failure/unverifiable condition, not an implementation choice.

## G. Expected outcome stability

The 23 accepted C vectors are represented one-for-one in the candidate catalog. All 23 expected outcome categories remain unchanged. Candidate changes add explicit target identity and stage; they do not change the expected settlement category. V013 receives the explicitly documented negative-scope binding to `external-effect/effect`. The outcome stability record is [`accord-02e4-expected-outcome-stability.json`](./accord-02e4-expected-outcome-stability.json).

## H. Provenance and non-claims

Clarifications of accepted intent and genuinely new normative decisions are separated in [`accord-02e4-decision-provenance.json`](./accord-02e4-decision-provenance.json). This candidate does not claim cryptographic opacity of scenario IDs, empirical benefit, provider truth, universal stage ordering, or package acceptance.

## I. Static closure result

The bounded consistency record is [`accord-02e4-spec-consistency.json`](./accord-02e4-spec-consistency.json). It records 10 candidate checks passing, zero ambiguous target tuples, zero unresolved profiles, and zero unresolved candidate target decisions. This is static candidate evidence, not acceptance and not executable validation.

## J. Required independent review

Before package 0.2 can replace the sealed 0.1 package, independent reviewers must inspect the candidate package, schema/profile instances, vector catalog, exact base hash, stage registry, E13 correction, and non-entailment rules. This branch does not accept package 0.2, change `main`, create a tag, or modify ACCORD-03.

## K. Attestation

```text
ACCORD02_ACCEPTED_FILES_MUTATED: NO
ACCORD02E1_ANALYSIS_MUTATED: NO
ACCORD02E2_CANDIDATE_MUTATED: NO
ACCORD02E3_ANALYSIS_MUTATED: NO
ACCORD03_MUTATED: NO
EXPERIMENT_IMPLEMENTED: NO
EXPERIMENT_EXECUTED: NO
PACKAGE_0_2_ACCEPTED: NO
MAIN_ADVANCED: NO
TAG_CREATED: NO
PUSH_PERFORMED: NO
```
