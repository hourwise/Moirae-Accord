# ACCORD-02A — Portable Linked Record Specification

Status: candidate design specification. This document is not an Accord runtime,
implementation, policy engine, workflow engine, transport broker, or effect-state
store.

## 1. Scope and design boundary

ACCORD-02A defines a transport-neutral linked record graph and the semantic
rules needed to verify that graph outside any private Accord database. It defines
portable representations for authority evidence, intent, task delegation,
effect attempts, observations, evidence artifacts, and verifier results.

It does not derive authority, admit dispatch, execute work, retry work, reconcile
provider state, or decide real-world policy. Those responsibilities remain with
Ananke, Horae, providers, and the declaring application as described by
ACCORD-01.

The normative trust boundary is:

> The system can verify only that a declared authority, task/effect identity,
> observation, and evidence artifact are consistent with named trust roots and
> the declared mediated channel; it cannot verify an unobserved external fact or
> prevent effects through paths it does not mediate.

The phrase “evidence-backed effect settlement” means a bounded verifier result
about the supplied record and its named evidence. It is not a claim of universal
truth, universal observation, or prevention outside the mediated channel.

### 1.1 Normative language

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
MAY, and OPTIONAL are to be interpreted as normative requirements for a profile
claiming conformance to this specification.

### 1.2 Explicit non-goals

This slice does not:

- create an Accord runtime, worker, queue, database, or second effect-state
  store;
- mint authority, own policy, or reproduce Ananke's authority decision logic;
- replace Horae's attempt, retry, reconciliation, or effect-state ownership;
- change Adrasteia, Ananke, Horae, Mnemosyne, Fates, MCP, or A2A source;
- install dependencies, call a provider, deploy infrastructure, or run
  Firecracker;
- claim exactly-once external effects, complete mediation, or external truth;
- select a new cryptographic primitive or define privacy cryptography;
- define arbitrary multi-hop authority algebra or a resource-budget algebra.

## 2. Conceptual graph

The portable bundle is a directed graph of immutable or append-only records.
Each edge is explicit; there is no overloaded correlation identifier.

```text
Principal ──issues/holds──> AuthorityGrant
AuthorityGrant ──authorizes-reference-for──> Intent
Intent ──instantiates──> Task
Task ──delegates-work-through──> Delegation
Delegation ──references──> child Task and child AuthorityGrant
Task ──dispatches──> EffectAttempt ──represents──> logical effect_id
EffectAttempt ──is-observed-by──> EffectObservation
EffectObservation ──is-supported-by──> EvidenceArtifact
AuthorityGrant ──is-bound-to──> EffectAttempt
all linked records ──are evaluated by──> VerifierRun / SettlementResult
```

The graph distinguishes:

1. an authority grant from the effective authority used at a mediated decision;
2. task delegation from authority delegation;
3. an effect attempt from an effect occurrence;
4. an observation from the evidence supporting that observation;
5. effect attribution from goal satisfaction;
6. task lifecycle completion from evidence-backed effect settlement.

No transport envelope can add an edge that is absent from the semantic graph.

## 3. Common record envelope

Every record MUST contain the following fields:

| Field | Meaning |
| --- | --- |
| `record_type` | Stable type name, such as `principal` or `effect_attempt`. |
| `record_id` | Opaque, profile-qualified, immutable identity. It MUST NOT be reused. |
| `record_version` | Version of the record shape, not the business state. |
| `profile` | Profile identifier governing semantics and allowed extensions. |
| `issued_at` | Time at which the issuer claims to have created the record. It is not automatically provider time. |
| `issuer_principal_id` | Principal that issued or published the record. |
| `integrity` | Content digest and optional detached attestations. |
| `extensions` | Namespaced, non-authoritative extensions. |

The following are common OPTIONAL fields:

- `observed_at`, `valid_from`, `valid_until`, or `as_of`, only when their
  record-specific meaning is defined;
- `disclosure`, describing whether content is full, redacted, digest-only, or
  detached;
- `source_ref`, `parent_record_ids`, and `evidence_ref_ids`;
- `human_readable_label`, which is descriptive only.

An issuer MUST NOT use an unknown extension to silently change authority,
identity, evidence class, or settlement semantics. A verifier MUST reject a
record when an extension declared as semantically required by the selected
profile is unknown or cannot be evaluated.

### 3.1 Identifier rules

Record identifiers are opaque strings in a profile-qualified namespace. A
profile MAY use UUID, URN, or another collision-resistant format, but the core
specification does not require a particular generator. The examples use
synthetic `urn:accord:example:*` identifiers.

Identifiers MUST be:

- stable for the logical object they name;
- unique within the declaring profile's collision domain;
- safe to compare byte-for-byte after canonical serialization;
- distinct from provider IDs, transport IDs, and human labels.

An identifier is not proof of the object it names. Integrity, linkage, and trust
root checks supply that evidence.

### 3.3 Identity and correlation matrix

The following identities are deliberately separate. `correlation_id` is not a
core semantic identity; transport correlation is carried in an explicitly
non-authoritative reference.

| Identity | Semantic scope | Nature | Can repeat? | Provider/observer origin |
| --- | --- | --- | --- | --- |
| `grant_id` | One logical authority grant | Immutable logical identity | No; a reissued grant has a new ID | Issued by declared authority owner |
| `intent_id` | One requested goal | Immutable logical identity | No; a new request has a new ID | Requestor or mediator |
| `task_id` | One logical task lifecycle | Immutable logical identity | No; retries do not create a new logical task | Task owner/mediator |
| `delegation_id` | One delegation edge | Immutable edge identity | No; a changed edge is a new edge | Grant/task delegator or authority owner |
| `effect_id` | One logical external effect | Immutable logical identity | No; retries share it | Declared by the mediated request/profile |
| `attempt_id` | One dispatch/attempt | Per-attempt immutable identity | Yes across a logical effect; each value remains unique | Dispatcher/executor |
| `observation_id` | One observation event or statement | Observer-derived immutable identity | Yes for repeated observations; each value remains unique | Observer |
| `evidence_id` | One evidence artifact/version | Immutable artifact identity | Yes for later artifacts; changed content requires a new ID | Artifact issuer/observer |
| `verifier_run_id` | One verifier invocation | Per-run immutable identity | Yes across invocations; each run gets a new ID | Verifier |
| `result_id` | One emitted verification result | Immutable result identity | Yes across runs; a changed result gets a new ID | Verifier |
| provider operation ID | Provider-side operation | Provider-derived reference | Provider-defined | Provider |
| transport message/call ID | Delivery/message envelope | Transport-derived reference | Transport-defined | Transport |

Provider and transport identifiers MAY be linked, but they MUST NOT replace the
logical Accord identities or become authoritative solely by being present. An
observation MAY refer to several candidate attempts when the provider's own
semantics make that unavoidable; the verifier then reports attribution as
ambiguous rather than silently choosing one.

Provider operation IDs are external correlation references. A profile MAY
declare one provider operation ID unique within a provider ledger, but the
portable model makes no universal uniqueness assumption: a reused or collided
provider operation ID MUST remain a diagnostic and MUST NOT merge logical
effects or substitute for `attempt_id`. Only an explicit effect/attempt binding
under the selected profile can support attribution.

### 3.4 Time rules

Times MUST be RFC 3339 timestamps with an explicit UTC offset in a conforming
JSON profile. `issued_at` is issuer-declared creation time. `observed_at` is the
observer's observation time. `as_of` is the state boundary claimed by an
observation. `valid_until` is a validity limit for the record or grant and MUST
NOT be treated as proof that a provider state ceased to exist after that time.

Clock values are descriptive unless the selected trust-root/profile explicitly
defines clock authority, skew, and freshness checking.

## 4. Record types

The following sections define the minimum semantic contract. The machine-readable
schema is deliberately narrower than these prose semantics: schema validation is
structural and does not implement Ananke's authority lattice or provider truth.

### 4.1 Principal

**Purpose.** Names a party or system role participating in issuance,
delegation, execution, observation, verification, or trust-root resolution.

**Required fields.** `record_type=principal`, `principal_id`/`record_id`,
`principal_kind`, `roles`, `issuer_principal_id`, `issued_at`, `profile`, and
`integrity`.

`principal_kind` MAY be `human`, `agent`, `service`, `provider`, `mediator`,
`executor`, `observer`, `verifier`, `fixture`, or `composite`. `roles` is a
declared role set, not an authority grant.

**Optional fields.** Display name, public-key references, operator boundary
declaration, process/host boundary declaration, provider profile, and
conformance metadata. Credentials and bearer tokens MUST NOT appear.

**Links.** Other records refer to a principal by explicit `*_principal_id`.

**Issuer and non-proof.** A trusted registry, profile, or the principal's
declared issuer MAY issue it. It does not prove that the principal behaved,
holds a grant, observed a provider, or is independent from another principal.

**Nature.** Descriptive identity; role declarations become normative only when
the selected profile names a trust root and checks them.

### 4.2 Authority Grant

**Purpose.** Carries a portable representation of a grant and its claimed
derivation context. It does not mint or derive authority.

**Required fields.** `grant_id`, `record_type=authority_grant`,
`issuer_principal_id`, `subject_principal_id`, `audience`, `authority_profile`,
`constraint_set`, `issued_at`, `valid_until` or an explicit non-expiring
profile declaration, `integrity`, and `profile`.

**Optional fields.** `parent_grant_id`, `delegation_id`,
`parent_constraint_digest`, `derivation_ref`, `authority_decision_ref`,
`approval_ref`, `revocation_ref`, `resource_scope`, and a
`monotonicity_claim`.

`constraint_set` is a profile-defined, canonical description. The core record
does not prescribe a universal lattice. Set-like, temporal, and consumable
dimensions MUST NOT be assumed to share one attenuation algebra.

**Links.** Parent grant, authority-delegation edge, subject principal, approval,
resource identifiers, and an Ananke decision reference MAY be linked by digest
or record ID.

**Issuer and non-proof.** The declared authority owner or its mediated authority
service issues it. A grant record proves only that the declared issuer produced
the represented data under the selected trust profile. It does not prove that
all real-world policy was satisfied, that a child grant is actually narrower,
or that an effect was authorized. A verifier may report `CONSISTENT` for
structural/cryptographic evidence without claiming policy validity.

**Normative ownership.** Ananke remains the authority owner. Accord MUST NOT
mint a grant or substitute a policy decision. The rule is:

> ACCORD NEVER MINTS AUTHORITY.

### 4.3 Intent

**Purpose.** Describes the requested goal or desired effect before task
execution.

**Required fields.** `intent_id`, `requestor_principal_id`, `intent_kind`,
`goal_descriptor`, `created_at`, and `integrity`.

**Optional fields.** Resource scope, requested capability, approval reference,
parent intent, expiry, desired effect descriptor, disclosure policy, and
authority grant reference.

**Links.** An intent links to the task it instantiates and to the authority
reference under which the request was admitted.

**Issuer and non-proof.** The requestor or authorized mediator issues it. It
does not prove dispatch, execution, effect occurrence, attribution, or goal
satisfaction.

**Nature.** Descriptive request; a profile may make selected fields normative
for a later admission check.

### 4.4 Task

**Purpose.** Names a logical unit of delegated work and its lifecycle. A task is
not an effect and is not a settlement.

**Required fields.** `task_id`, `intent_id`, `task_owner_principal_id`,
`task_kind`, `created_at`, and `integrity`.

**Optional fields.** Parent task, child task refs, lifecycle observations,
declared deadline, transport correlation refs, execution owner, completion
claim, and delegation ref.

**Links.** Intent, parent task, delegation, authority grant, effect attempts,
and transport correlation records.

**Issuer and non-proof.** A task owner or mediator issues it. A task lifecycle
state such as `completed` proves only that the declared task lifecycle reached
that state under the named task issuer. It does not prove effect occurrence,
attribution, goal satisfaction, or evidence-backed effect settlement.

### 4.5 Delegation edge

**Purpose.** Separately records delegation of work and its relation to a child
grant. It prevents a task relationship from being mistaken for authority
derivation.

**Required fields.** `delegation_id`, `delegation_kind` (`task_delegation` or
`authority_delegation`), `parent_task_id` or `parent_grant_id` as applicable,
`child_task_id` or `child_grant_id` as applicable, `issuer_principal_id`,
`issued_at`, and `integrity`.

**Optional fields.** Parent/child edge digest, hop number, derivation reference,
attenuation claim, delegation deadline, revocation reference, and sibling set
reference.

**Links.** The edge MUST link the exact records on both sides. A task-delegation
edge MUST NOT create a grant. An authority-delegation edge MUST reference the
authority owner/decision that issued or accepted the child grant.

**Issuer and non-proof.** The parent task owner, authority owner, or mediator
issues the edge according to its kind. It does not prove that the child was
admitted, that the child obeyed its constraints, or that effective authority
was bounded under an unresolved multi-hop algebra.

### 4.6 Effect Attempt

**Purpose.** Records an attempted dispatch of a logical effect without claiming
that an external effect occurred.

**Required fields.** `attempt_id`, `effect_id`, `task_id`, `authority_grant_id`,
`action_descriptor_hash`, `attempted_at`, `dispatcher_principal_id`, and
`integrity`.

`effect_id` is the logical effect identity. `attempt_id` is unique per dispatch
attempt and MUST change on every retry, even when the logical effect and
idempotency key are reused.

**Optional fields.** `delegation_id`, provider target/profile, client-chosen
idempotency-key digest, provider operation ID, transport refs, admission
decision ref, attempt deadline, retry ordinal, response digest, and an
`effect_binding` descriptor. The descriptor binds this attempt to the exact
`predicate_id`, stage, action, target, resource, recipient/counterparty,
provider, and external identifier when the selected settlement profile requires
those dimensions. A settlement-relevant profile MUST reject or leave unresolved
an attempt whose required binding slot is absent or unknown; it MUST NOT fill a
slot with a transport ID or provider operation ID merely because that value is
available.

**Links.** Task, grant, authority decision, delegation edge, observations,
evidence artifacts, and retry siblings.

**Issuer and non-proof.** Horae or the mediated dispatcher issues it. It proves
only that a declared attempt record exists and is internally linked. It does not
prove acceptance, occurrence, attribution, or goal satisfaction.

### 4.7 Effect Observation

**Purpose.** Records what an observer reported about a logical effect or attempt
at a stated time and under stated read semantics.

**Required fields.** `observation_id`, `effect_id`, `observer_principal_id`,
`observation_kind`, `observed_at`, `read_semantics`, `observed_state`, and
`integrity`.

`observation_kind` MAY be `provider_response`, `provider_state_read`,
`executor_state`, `receiver_receipt`, `third_party_witness`, or
`synthetic_fixture`. `observed_state` is profile-defined and MUST NOT be
interpreted without the named read semantics.

**Optional fields.** `attempt_id`, provider operation ID, provider resource ID,
as-of time, freshness limit, attribution assertion, source evidence ref,
conflict set, transport refs, and an `effect_binding` descriptor. When an
observation is offered to settle a predicate, its binding MUST identify the
exact logical `effect_id`, predicate and stage, plus the profile-applicable
action, target, resource, recipient/counterparty, provider, and external
identifier slots. Each slot is explicitly `BOUND`, `NOT_APPLICABLE`, or
`UNKNOWN`; a missing or `UNKNOWN` required slot prevents a stronger settlement.

**Links.** The observation MUST identify the effect and MAY identify one or
more attempts. It MUST link to the evidence artifact(s) that carry it.

**Issuer and non-proof.** The named observer issues it. Observation is not
attribution, and attribution is not goal satisfaction. `NO_EFFECT_OBSERVED` is
always qualified by `as_of` and `read_semantics`; it is not proof of eternal
absence.

### 4.8 Evidence Artifact

**Purpose.** Carries or references material supporting an observation, authority
claim, identity claim, or linkage claim.

**Required fields.** `evidence_id`, `evidence_class`, `issuer_principal_id`,
`observer_principal_id` or an explicit `observer_not_applicable`,
`trust_root_id`, `coverage`, `captured_at`, `content_digest`, and `integrity`.

**Optional fields.** Detached content URI, inline content for synthetic
fixtures, signature/attestation metadata, replay nonce, valid interval,
freshness, authority/effect/attempt bindings, `effect_binding`, disclosure
mode, and redaction descriptor. For settlement-relevant evidence,
`effect_binding` is the machine-readable proposition descriptor rather than a
free-form coverage label. It does not make the evidence true; it tells the
verifier exactly which proposition the evidence claims to cover.

**Links.** Evidence links explicitly to the record IDs and hashes it covers. A
signature over an evidence artifact is not automatically a signature over the
entire graph.

**Issuer and non-proof.** The artifact issuer or observer issues it. It proves
only the claims included in its coverage under its declared trust root. A
provider signature creates provider-attested evidence; it does not create
provider-independent truth.

### 4.9 Settlement / Verification Result

**Purpose.** Records the deterministic output of a verifier run over an input
bundle and named trust/profile inputs.

**Required fields.** `result_id`, `verifier_run_id`, `target_refs`,
`verifier_profile`, structural/cryptographic/linkage/authority/effect/
attribution statuses, `settlement`, `input_bundle_digest`, `generated_at`, and
`integrity`.

**Optional fields.** Diagnostic findings, discharged trust assumptions,
unsupported profile features, redacted input refs, and external evidence
material digests.

**Links.** The result MUST identify the exact input bundle digest and every
record/evidence ref that materially affected the result.

**Issuer and non-proof.** The verifier issues it. The result is an assertion
about the supplied records under the supplied profile; it is not a claim that
the verifier has universal access to external reality.

The canonical settlement forms are:

```text
VERIFIED(evidence_class, observer, trust_root)
CORROBORATED(evidence_class, observer, trust_root)
NO_EFFECT_OBSERVED(as_of, read_semantics)
UNKNOWN_PENDING(retry_until, reason)
UNKNOWN_TERMINAL(reason)
REJECTED(reason)
```

`VERIFIED` MUST always carry the evidence class, observer, and trust root in the
machine-readable result. Bare `verified` is not a conforming settlement.

## 5. Authority linkage and separation

An effect attempt MUST include or reference:

1. the grant alleged to authorize it;
2. the principal that issued the grant;
3. the parent grant and delegation edges, when derived;
4. restrictions and constraint digests declared at each edge;
5. the mediated authority decision/admission reference, if one exists;
6. the selected authority relation/profile.

The verifier checks graph integrity, identity equality, hash coverage, signature
validity where supported, expiry/freshness rules, and profile-specific
consistency. It MAY conclude that authority evidence is
`CONSISTENT`, `INCONSISTENT`, `INSUFFICIENT`, or `UNVERIFIABLE`.

It MUST NOT silently run Ananke policy or infer a real-world policy result from
descriptive constraints. `authority_evidence_status=CONSISTENT` means the
declared evidence is structurally/cryptographically coherent under its named
profile. It does not mean the external action was authorized under every
real-world policy.

Effect evidence is a separate axis. A strong authority result cannot upgrade a
weak effect result, and a strong effect observation cannot retroactively create
authority. Settlement requires both axes to satisfy the selected profile.

## 6. Evidence classes and trust roots

Evidence classes are capability descriptions, not a universal strength ladder.
Profiles MUST declare properties rather than assume that `E4 > E3` in every
decision.

The ACCORD-02A example profile uses these labels:

| Profile label | Typical evidence | It can support | It cannot support by itself |
| --- | --- | --- | --- |
| `E0_DELEGATE_ASSERTION` | Child/delegate says the goal succeeded. | A recorded claim and a diagnostic input. | Effect occurrence, attribution, or settlement. |
| `E1_EXECUTOR_STATE` | Durable executor journal/state. | Attempt/lifecycle facts under executor trust. | Provider occurrence or provider attribution. |
| `E2_PROVIDER_RESPONSE` | Response returned by the provider through the dispatcher. | Provider response observed by the receiving process. | Durable occurrence after a lost response, or observer-distinct corroboration. |
| `E2R_PROVIDER_STATE_READ` | Named provider-state read at an `as_of` boundary. | Qualified observation, possibly `NO_EFFECT_OBSERVED(as_of, read_semantics)`. | Eternal absence, unless the read profile explicitly has exhaustive semantics. |
| `E3_RECEIVER_ATTESTED` | Provider/receiver attestation bound to operation/effect data. | `VERIFIED(...)` only when profile-required bindings and trust root checks pass. | Provider-independent truth or goal satisfaction. |
| `E4_CORROBORATED_EXTERNAL` | E3-style evidence plus observer-distinct witness/log or equivalent. | Stronger corroboration and offline verification under the profile. | Universal truth, collusion resistance beyond declared assumptions, or unmediated paths. |

The labels are shorthand for a property vector. A conforming profile MUST
declare, for each class:

- issuer and observer role;
- trust root and key/issuer binding;
- freshness and read semantics;
- replay resistance;
- identity binding and effect binding;
- authority binding and provider binding;
- whether the delegate controls the evidence;
- whether the process/observer is distinct from the delegate;
- whether evidence is externally reproducible or offline verifiable;
- permitted settlement outcomes and required escalation obligations.

No class is automatically sufficient merely because it has a higher label.

### 6.1 Observer relationships

The record MUST describe the relationship between observer and delegate using
explicit declarations such as:

- `same_process`;
- `same_operator_distinct_process`;
- `separate_service_same_operator`;
- `provider_originated`;
- `third_party`;
- `synthetic_fixture`.

The terms `independent` and `independently verified` MUST NOT appear as bare
claims. A verifier MAY report `delegate_independent` or
`process_independent` only when the profile defines the boundary and the
declared roles satisfy it. A provider-originated observation is provider-
attested, not provider-independent.

### 6.2 Trust roots

A `trust_root_id` refers to a named profile entry. The entry MAY designate a
public key, pinned issuer identity, provider credential/profile, conformance
fixture key, or test trust root. Examples MUST use synthetic keys or key
digests, never secrets.

Trust roots MUST state scope, expiry/revocation semantics, algorithm profile,
and the records/claims they are allowed to authenticate. Trust-root recognition
does not authenticate unrelated records or expand authority.

## 7. Canonicalization and integrity

The JSON profile uses these requirements:

1. Records are encoded as UTF-8 JSON.
2. Canonical bytes use the JSON Canonicalization Scheme (JCS, RFC 8785) for
   the profile's signed content. Duplicate object member names are invalid.
3. Timestamps use RFC 3339 UTC form; profile-controlled numeric fields SHOULD
   avoid floating-point ambiguity.
4. A record content digest is SHA-256 over the canonical bytes of the record
   with its `integrity` value omitted. The digest is represented as
   `sha-256:<lowercase-hex>`.
5. `integrity` MAY contain a digest, a detached signature, an attestation, or
   several of these. Signature coverage MUST state the covered record digest
   and profile/version.
6. Signature algorithms and key formats MUST come from an approved profile
   using an existing standard. ACCORD-02A does not invent an algorithm or
   require a crypto library. An unsupported but well-formed signature yields
   `cryptographic_status=UNVERIFIABLE`, not success.
7. Record linkage MAY use stable IDs, content digests, or both. A stable ID
   without matching digest/link evidence is not enough for a cryptographic
   linkage claim.

The future conformance profile may select a COSE, JOSE, or other established
signature envelope. That implementation choice is deferred until an approved
profile and dependency review exist.

## 8. Disclosure and privacy boundary

Portable bundles SHOULD support `disclosure` values:

- `full` — content is present;
- `digest_only` — content is withheld but its digest is supplied;
- `detached` — content is supplied by an explicitly named external channel;
- `redacted` — selected fields are removed under a profile-controlled rule.

Redaction MUST NOT make a record appear to prove a claim whose covered bytes are
missing. A verifier reports `INSUFFICIENT` or `UNVERIFIABLE` when required
content is detached, redacted, or unavailable. Full credentials, bearer tokens,
API keys, session cookies, and secrets MUST never be embedded in records,
schemas, or fixtures.

## 9. Deterministic semantic invariants

1. A task lifecycle completion does not prove effect occurrence.
2. A delegate success assertion does not by itself produce evidence-backed
   effect settlement.
3. Transport metadata cannot create or widen authority.
4. Retrying a logical effect does not reuse an effect-attempt identity.
5. Distinct attempts remain distinguishable even when they share an idempotency
   key or provider operation ID.
6. Authority evidence and effect evidence are separate axes.
7. Observation and attribution are separate.
8. Effect occurrence and goal satisfaction are separate.
9. `UNKNOWN_PENDING` and `UNKNOWN_TERMINAL` are not success.
10. Absence of observed evidence is not automatically proof of no effect.
11. Verifier output strength cannot exceed the declared evidence class and trust
    root.
12. External verification MUST NOT require hidden Accord-private state.
13. Accord records do not supersede Ananke policy ownership.
14. Accord records do not supersede Horae authoritative effect-state ownership.
15. Unmediated paths remain outside prevention claims.
16. A provider response proving request acceptance does not by itself prove
    later effect occurrence.
17. Evidence proving occurrence without binding it to the logical effect is
    not attributed evidence.
18. Evidence proving attribution does not prove the requested goal was
    satisfied.
19. Conflicting evidence is retained and surfaced; it is not silently merged.
20. A transport correlation ID is a hint unless an explicit semantic record
    binds it under a trust profile.

## 10. Falsifiability bridge

ACCORD-02A enables later experiments without executing them. A research harness
can calculate, from the graph and verifier results:

| Later measure | Required record material |
| --- | --- |
| False confirmation rate | Settlement results marked `VERIFIED`/`CORROBORATED`, ground-truth fixture outcome, evidence class, and delegate behaviour. |
| Indeterminacy rate | `UNKNOWN_PENDING`/`UNKNOWN_TERMINAL` results, reasons, retry deadline, and provider/evidence profile. |
| Duplicate-effect rate | One `effect_id` linked to multiple attempt IDs and provider-observed occurrences. |
| Human escalation load | Explicit escalation/referral records or test-harness annotations linked to the result. |
| External verifiability | Offline verifier output using only bundle, named trust roots, and supplied detached evidence. |
| Effect attribution | Attempt/effect IDs, provider operation IDs, idempotency-key binding, and observer attribution status. |
| Effective-authority composition | Grant chains, delegation edges, constraint digests, sibling sets, and the selected authority relation profile. |

The schema and examples do not choose thresholds or claim that any measurement
improves. They make later comparisons possible.

## 11. Transport neutrality

Semantic records keep their meaning when carried by different transports.

### Local fixture

The fixture envelope MAY contain `transport_kind=local_fixture`, a message ID,
and delivery timestamps. The linked record bundle remains authoritative for the
declared semantics; fixture metadata is not an authority or evidence root.

### MCP-shaped carriage

An MCP-shaped envelope MAY carry tool name, call ID, session/context ID, and
result metadata. Tool names, call IDs, and session IDs are transport metadata.
They MUST NOT become grant IDs, effect IDs, or proof of settlement without an
explicit semantic record and trust-root binding.

### A2A-shaped carriage

An A2A-shaped envelope MAY carry context ID, task/message IDs, artifacts, and
task state. A2A task state describes task lifecycle, not external-effect
settlement. `TASK_STATE_UNSPECIFIED` is an unspecified/indeterminate task state;
it is not XA/in-doubt effect semantics and MUST NOT be mapped automatically to
`UNKNOWN_PENDING` or `UNKNOWN_TERMINAL` without additional effect evidence.

A2A SEP #1404 is a discussion/proposal and is not treated as a normative
feature of this profile. A2A is an interoperability/conformance target, not the
research foundation.

## 12. Versioning and extension policy

`profile` and `record_version` are mandatory. A profile MAY add fields, but it
MUST define whether the addition is backward-compatible and how it participates
in canonicalization and signatures.

Unknown optional descriptive fields MAY be preserved and ignored. Unknown
fields that could affect authority, identity, evidence class, observer role,
trust root, or settlement MUST cause `UNVERIFIABLE` or `INVALID` until the
profile is understood. Extension names SHOULD be namespaced by a stable URI or
reverse-domain identifier.

Profiles MUST NOT redefine `task_id`, `effect_id`, `attempt_id`, or settlement
terms with incompatible meanings.

## 13. Ownership summary

| Responsibility | Owner | ACCORD-02A treatment |
| --- | --- | --- |
| Portable linked contracts | Adrasteia | Defined here as a candidate contract; no source change. |
| Authority derivation/policy/approval/admission | Ananke | Referenced, never duplicated. |
| Attempt identity/durable execution/retry/reconciliation/effect state | Horae | Referenced as authoritative; no second store. |
| Provenance/governed memory | Mnemosyne | Deferred. |
| Evidence/conformance | Fates Integration | Outside runtime path. |
| Transport interoperability | A2A/MCP profiles | Carriage/conformance only. |
| Runtime/control plane | Accord | Explicitly not created. |

## 14. Canonical effect proposition binding

Records used for settlement MUST carry a `proposition_ref` to the canonical
`effect_proposition` record defined by
[`accord-02r2-proposition.schema.json`](./schema/accord-02r2-proposition.schema.json).
Records that are not used for settlement may omit it.
The proposition is supplied as that canonical descriptor in the validation
bundle (it may be a sidecar to the ordinary A portable-record bundle); it is
not redefined as a second A record variant.
The proposition descriptor binds an existing logical `effect_id` to its
predicate, stage, action, and applicable target/resource/recipient/provider
dimensions. It does not assert occurrence, authority validity, or causality.

Observations, evidence artifacts, settlement results, verifier projections, and
experiment result records used for settlement MUST resolve to the same
proposition. Repeated summary fields are non-authoritative and MUST either be
absent or match the resolved descriptor under the ACCORD-02R2 validation
contract. A transport message ID or provider operation ID cannot substitute for
the proposition reference.

For ACCORD-02R3, the portable-record `extensions` member is governed by the
supplied extension registry
[`accord-02r3-extension-registry.json`](./examples/accord-02r3-extension-registry.json).
An unregistered extension is `UNKNOWN_FORBIDDEN` for authority/effect/verifier
purposes; a non-semantic extension is opaque and cannot influence a conclusion.
Authority-, settlement-, and evidence-bearing extensions require the matching
declared profile/comparator before they can be admitted.
