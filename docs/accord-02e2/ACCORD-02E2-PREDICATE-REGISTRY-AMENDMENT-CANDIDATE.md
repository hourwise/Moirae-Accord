# ACCORD-02E2 — Explicit Predicate Registry Amendment Candidate

Status: **CANDIDATE — NOT ACCEPTED**  
Candidate branch: `codex/accord-02e2-explicit-predicate-registry`  
Base: ACCORD-02E1 commit `430c7e72766dc708bf18f19a30df0b232c336354`

## Purpose

This additive candidate supplies an explicit, versioned predicate registry and a language-neutral exact resolver. It does not alter the accepted ACCORD-02 package, schemas, profiles, settlement vectors, or verifier implementation.

The candidate uses the exact resolution key `(predicate_id, stage)`. It permits only exact tuple equality and fails closed for unknown predicates, unknown stages, missing stages, duplicate tuples, and unsupported predicate semantics.

## Explicit candidate mappings

The candidate records the smallest mappings supported by the accepted profile and C-stage vocabulary:

| Accepted predicate ID | Exact stage | Existing profile row | Candidate interpretation |
|---|---|---|---|
| `urn:accord:02c:predicate:resource-created` | `resource_created` | `create_resource` | resource creation |
| `urn:accord:02c:predicate:recipient-ack` | `recipient_acknowledged` | `deliver_item` | recipient acknowledgement |
| `urn:accord:02c:predicate:provider-acceptance` | `provider_accepted` | `provider_acceptance` | provider acceptance |

`resource-visible` is explicitly unsupported because no accepted applicability or evidence capability defines it. `complete-negative` is not assigned a synthetic positive row; its complete-scope semantics require an explicit accepted negative applicability contract.

## Closure result

The candidate cannot certify the accepted 23 settlement vectors. The accepted C vectors do not provide the required stage input:

- the 18 `external-effect` vectors omit `target.stage`;
- V014 lists two stages but does not select the requested target stage;
- V021, V017, and V022 omit a target stage;
- V013 supplies negative-query completeness flags but no accepted target stage or negative applicability contract.

Evidence class, observation kind, attempt outcome, vector ID, and observed state are not permitted to synthesize a missing stage. Doing so would create the semantic shortcut this amendment is intended to remove.

The machine-readable certification therefore records `resolved_exactly_once = 0`, `unresolved = 23`, `ambiguous = 0`, and `lexical_fallbacks = 0`. This is a deliberate failed closure gate, not an acceptance claim.

## Package candidate

`accord-02e2-specification-package-0.2.json` is an additive candidate manifest pointing to the registry contract. It leaves the immutable ACCORD-02 0.1 package unchanged and records `candidate_closure.status = INCOMPLETE`.

## Required next normative decision

An accepted specification amendment must choose one explicit path:

1. add an explicit stage to every affected target/effect vector; or
2. define a first-class non-positive/negative predicate applicability contract whose resolution does not require an inferred stage.

The amendment must also decide whether `resource-visible` is supported. No implementation may choose among these possibilities silently.

## Verdict

**BROADER_SPECIFICATION_REVIEW_REQUIRED**

The candidate is not internally complete and must not be accepted, merged into the sealed package, or used to change ACCORD-03 behavior. The R3 external implementation-assessment backlog remains preserved and is not substituted by this candidate.
