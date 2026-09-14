# ACCORD-02E-R4 — Adversarial Cases

These are specification-level checks only. No experiment, provider call, validator, or runtime was executed.

## Historical cases rechecked

| Case | Result | Review conclusion |
|---|---|---|
| ADV-18 — scenario catalog leaks expected oracle | RESISTED | Public catalog has no scorer expectation locator; the remaining scenario-ID requirement is correlation-only and non-evidentiary. |
| ADV-19 — classifier receives Accord-only evidence | RESISTED | ARM-C feature restrictions exclude Accord settlement/verifier semantics. |
| ADV-R1-01 — scorer-extension smuggling | RESISTED | Arm-facing profiles close semantic extensions and scorer material is not an arm input. |
| ADV-R1-07 — foreign verifier result | RESISTED | Typed lineage and run-binding rules reject a result outside the supplied run scope. |
| ADV-R2-01 — missing native settlement result | RESISTED | Projection requires native C lineage. |
| ADV-R2-04 — proposition mutation | PARTIALLY_RESISTED | Proposition identity rules reject duplicate/conflicting IDs, but full package/schema closure is affected by the open package findings. |
| ADV-R2-05 — digest mismatch | PARTIALLY_RESISTED | Mismatch is a validation failure, but concrete canonicalization applicability is incomplete for all bundle forms. |
| ADV-R2-06 — truth-dependent normalization | RESISTED | Normalization consumes raw output and profile, not scorer truth. |
| ADV-R2-07 — orchestrator condition leakage | RESISTED | Visibility rules prohibit fixture-private condition labels from arm manifests where the profile marks them private. |
| ADV-R3-01 — missing extension registry | RESISTED | Positive settlement requires the declared extension registry/profile. |
| ADV-R3-03 — source schema spoof | PARTIALLY_RESISTED | Source membership is checked by schema ID/version, but the active source contracts are not all package members. |
| ADV-R3-05 — truth-dependent normalization | RESISTED | A normalizer cannot consult expected outcome material. |
| ADV-R3-07 — predicate profile missing | RESISTED | Missing required profile cannot produce a positive settlement. |
| ADV-R3-10 — hidden filesystem lookup | RESISTED | Exact package semantics prohibit ambient lookup. |
| ADV-R3-12 — scorer bundle as verifier bundle | RESISTED | Bundle classes and forbidden scorer-only material are distinct. |

## R4 package and contract cases

| ID | Construction | Expected rule | Observed specification result | Finding |
|---|---|---|---|---|
| ADV-R4-01 | Profile exists as a repository file but is absent from the package | Unavailable | Resisted by `CLOSED_EXACT_VERSION`; a valid complete run still cannot be formed when the required profile itself is missing | E2E-R4-BLOCK-001 |
| ADV-R4-02 | Validator substitutes a newer local profile | No latest/compatible substitution | Resisted; exact package/version is required | — |
| ADV-R4-03 | Record declares an unknown schema ID | Schema-contract failure | Resisted; self-declared IDs are not sufficient | — |
| ADV-R4-04 | Unknown role enters a role-bearing source registry | Closed vocabulary | Not resisted in the source-schema registry, whose role array accepts arbitrary strings | E2E-R4-MAJOR-002 |
| ADV-R4-05 | Digest uses a wrong canonicalization profile | Digest failure/unverifiable | Profile identity is checked, but concrete applicability is not fully matchable for bundle/scorer entries | E2E-R4-MAJOR-001 |
| ADV-R4-06 | Package contains duplicate profile ID/type/version | Invalid package | Resisted by uniqueness/package rules | — |
| ADV-R4-07 | Bundle declares a different package version than the verifier loads | Bundle/package mismatch | Resisted; exact package identity is a required contract input | — |
| ADV-R4-08 | ARM-C registers scenario ID as a feature | Scenario IDs are not semantic features | Resisted by `SCENARIO-ID-001` and classifier feature restrictions | — |
| ADV-R4-09 | Required contract exists only outside the package | Not available | Resisted; filesystem/repository discovery is forbidden | E2E-R4-BLOCK-001/E2E-R4-BLOCK-002 |
| ADV-R4-10 | Verifier falls back to private database after MISSING | Self-contained scope | Non-conformant | — |

## Profile, schema, and role attacks

- Correct profile ID with wrong version: rejected as unsupported/mismatch.
- Correct version with wrong profile type: rejected as wrong profile type.
- Generic bundle content without a schema contract: not admitted as a normative record.
- Known schema contract with invalid content: structurally invalid.
- `consumer_roles = ["MAGIC_ADMIN"]`: rejected by the primary role-visibility profile, but the source registry gap means the role closure is not global.
- Unknown producing role: rejected by the primary role profile.
- ARM-C receiving fixture-private delegate honesty: rejected by visibility rules.
- Scorer receiving scorer truth: permitted only on the scorer side.

## Canonicalization attacks

- Missing canonicalization profile: digest is unverifiable/fails; it does not imply an external-effect fact.
- Wrong canonicalization profile: fails profile/applicability validation.
- Unsupported digest algorithm: unverifiable/fails under the declared contract.
- Altered content with original digest: mismatch when the applicable profile is resolvable.
- Digest absent where optional: ordinary typed resolution may continue under the active profile.

The open issue is not the JCS/SHA-256 method itself. It is the inability to deterministically map that method to every concrete digest-bearing bundle record form.

## Interpretation

The cases demonstrate that direct oracle access, latest-profile substitution, self-declared-schema admission, and scenario-ID semantic use are resisted. They also demonstrate why package membership and concrete canonicalization applicability are acceptance-critical: an attack can be rejected only after the relevant contract is actually resolvable in the declared scope.
