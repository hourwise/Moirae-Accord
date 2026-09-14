# ACCORD-02A — Trust and Evidence Profile

Status: candidate profile for later conformance work. It is a design aid, not a
universal evidence hierarchy and not an implementation.

## 1. Profile intent

This profile makes evidence affordances explicit so that a verifier never turns
a delegate assertion, provider response, or transport lifecycle state into a
stronger conclusion than its trust root supports.

The profile uses the canonical terms:

- `evidence-backed effect settlement`;
- `VERIFIED(evidence_class, observer, trust_root)`;
- `UNKNOWN_PENDING`;
- `UNKNOWN_TERMINAL`;
- `NO_EFFECT_OBSERVED(as_of, read_semantics)`.

It rejects bare `verified`, `truth`, `independent`, `completion truth`, and
`exactly once` as technical result labels.

## 2. Evidence is multidimensional

An evidence class is a declared vector of properties, not a total order. In
particular, a provider-signed receipt may be stronger for provider attribution
than a third-party log, while the third-party log may be stronger for offline
availability. The verifier MUST evaluate the declared properties relevant to
the requested conclusion.

Each class declaration includes:

| Property | Values / meaning |
| --- | --- |
| `issuer_principal_id` | Party that produced the artifact. |
| `observer_principal_id` | Party that observed or attested the state. |
| `trust_root_id` | Root that authenticates the issuer or observer. |
| `freshness` | Capture time, validity interval, and permitted age/skew. |
| `read_semantics` | What state boundary was read and with what consistency. |
| `replay_resistance` | Nonce, sequence, idempotency binding, or explicit absence. |
| `identity_binding` | Which principal/task/effect/attempt identities are covered. |
| `effect_binding` | How occurrence is bound to the logical effect. |
| `authority_binding` | How the authority grant/decision is covered. |
| `provider_binding` | Whether the named provider produced or authenticated the claim. |
| `delegate_controlled` | Whether the delegate can create or alter the evidence. |
| `process_distinct` | Whether the observer is declared outside the delegate process. |
| `external_verifiability` | Whether a verifier can check it without private plane state. |
| `permitted_outcomes` | Settlement forms allowed by the profile. |

Unknown property values are not positive evidence.

## 3. Candidate class catalog

The compact labels are profile-local shorthand only. They do not establish a
universal strength ranking.

### E0_DELEGATE_ASSERTION

The delegate claims that it completed or achieved a goal.

- **Known:** a named delegate issued a claim, if the delegate identity and
  integrity are valid.
- **Observer:** the delegate or its same-process reporter.
- **Trust root:** delegate identity/profile, if any.
- **Attribution:** none beyond the delegate's own statement.
- **Defensible verdict:** record the claim; `UNKNOWN_PENDING` or
  `UNKNOWN_TERMINAL` for effect settlement according to available follow-up.
- **Not defensible:** `VERIFIED` effect occurrence, attributed effect, or goal
  satisfaction.
- **Failure modes:** lying child, partial truth, process compromise, replay,
  and success-language ambiguity.

### E1_EXECUTOR_STATE

A durable executor reports dispatch, lifecycle, or journal state.

- **Known:** the executor recorded an attempt or lifecycle event under its own
  trust root.
- **Observer:** executor/mediator; relationship to delegate MUST be declared.
- **Trust root:** executor key or conformance fixture.
- **Attribution:** may bind the attempt to the executor's dispatch, not to an
  external provider effect.
- **Defensible verdict:** attempt recorded; possibly `CORROBORATED` for
  executor state.
- **Not defensible:** provider occurrence or universal external completion.
- **Failure modes:** crash after effect before journal, stale replay, executor
  corruption, and provider acceptance without occurrence.

### E2_PROVIDER_RESPONSE

A provider response is returned through the mediated channel.

- **Known:** the named receiver observed a response claiming a provider result.
- **Observer:** receiver/mediator, with provider binding as declared.
- **Trust root:** receiver and/or provider profile.
- **Attribution:** only if the response binds effect identity, attempt identity,
  or provider operation/idempotency identity under the profile.
- **Defensible verdict:** provider response observed; sometimes
  `CORROBORATED` for acceptance.
- **Not defensible:** later occurrence if the response only acknowledges
  acceptance.
- **Failure modes:** lost response, response replay, ambiguous asynchronous
  acceptance, and provider/operator collusion.

### E2R_PROVIDER_STATE_READ

A named observer reads provider state at a stated boundary.

- **Known:** the observer saw the specified state under the specified read
  semantics at `as_of`.
- **Observer:** provider, receiver, or separate service as explicitly declared.
- **Trust root:** observer/provider profile.
- **Attribution:** depends on echoed idempotency key, operation ID, resource
  binding, or another declared relation.
- **Defensible verdict:** observed occurrence, observed non-occurrence at a
  boundary, or `NO_EFFECT_OBSERVED(as_of, read_semantics)`.
- **Not defensible:** eternal absence unless the profile defines exhaustive
  semantics and a fence.
- **Failure modes:** stale read, delayed write, retention expiry, semantic
  duplicate, and an observer that cannot distinguish attempts.

### E3_RECEIVER_ATTESTED

A provider or receiver signs/attests to a receipt with explicit coverage.

- **Known:** the trusted issuer attested to the covered facts.
- **Observer:** provider/receiver, with process and operator boundaries named.
- **Trust root:** provider or receiver public key/profile.
- **Attribution:** potentially strong when an echoed idempotency key,
  operation ID, action digest, and effect ID are covered.
- **Defensible verdict:** `VERIFIED(E3_RECEIVER_ATTESTED, observer, trust_root)`
  only when the profile's bindings and freshness rules all pass.
- **Not defensible:** provider-independent truth, goal satisfaction, or
  unmediated-path prevention.
- **Failure modes:** forged key, stale signature, receipt suppression, provider
  bug, semantic duplicate under another key, and collusion.

### E4_CORROBORATED_EXTERNAL

An E3-style artifact is additionally bound to an observer-distinct witness,
transparency log, or equivalent externally reproducible material.

- **Known:** two or more named evidence sources corroborate the covered claim
  under their roots.
- **Observer:** provider/receiver plus observer-distinct witness or log.
- **Trust root:** each root is named; the roots are not assumed independent.
- **Attribution:** strong only if both sources cover the same effect and attempt
  identity.
- **Defensible verdict:** `VERIFIED(E4_CORROBORATED_EXTERNAL, observer, trust_root)`
  or `CORROBORATED`, according to the profile.
- **Not defensible:** universal truth, absence of collusion, or assurance about
  unmediated paths.
- **Failure modes:** shared operator/root, witness omission, split views,
  delayed publication, and a provider issuing a false but consistently signed
  statement.

## 4. Role and observer model

The same system may occupy several roles, but each record declares the role used
for that assertion. The minimum role vocabulary is:

- `principal` — identity holder;
- `delegate` — performs delegated work or issues a task claim;
- `mediator` — admits or mediates a dispatch;
- `executor` — performs durable dispatch/retry/reconciliation;
- `provider` — controls or reports an external effect surface;
- `observer` — records an observation or attestation;
- `verifier` — evaluates supplied material;
- `trust_root` — authenticates a key/issuer/profile.

The verifier MUST represent these as role assignments, not infer them solely
from a transport name.

An observation relationship is one of:

| Relationship | Meaning | Terminology allowed |
| --- | --- | --- |
| `same_process` | Observer and delegate share a process boundary. | `delegate_controlled`; no independence claim. |
| `same_operator_distinct_process` | Different process, same declared operator. | `process_distinct` may be true; `operator_distinct` false. |
| `separate_service_same_operator` | Separate service boundary, same operator. | Service-distinct; trust root relationship remains explicit. |
| `provider_originated` | Provider created or signed the observation. | Provider-attested; not provider-independent. |
| `third_party` | Observer has a declared separate operator/trust context. | Observer-distinct, subject to trust assumptions. |
| `synthetic_fixture` | Offline test fixture role. | Fixture-observed; claims are limited to the fixture profile. |

The profile MUST NOT label an observation simply `independent`.

## 5. Trust-root declarations

A trust-root profile entry MUST include:

```text
trust_root_id
root_kind
subject_scope
verification_material_reference
algorithm_profile
validity_interval
revocation_or_replacement_rule
authenticated_claim_types
operator_boundary_declaration
```

Permitted `root_kind` examples are `public_key`, `pinned_issuer`,
`provider_profile`, `fixture_key`, and `transparency_log`. Verification material
may be a public key or digest reference. Secret material is never portable
record content.

Trust roots authenticate only their declared scope. A provider key can
authenticate a provider statement; it cannot authenticate an Ananke grant unless
the profile explicitly binds that claim.

## 6. Verdict matrix

The following is a conservative default. A profile may be stricter but MUST NOT
be more permissive without documenting the trust assumption.

| Evidence condition | Authority evidence | Attribution | Default settlement |
| --- | --- | --- | --- |
| E0 delegate assertion | Any | Unknown | `UNKNOWN_PENDING` or `UNKNOWN_TERMINAL` |
| E1 executor state only | Consistent | Executor-only | `CORROBORATED` for executor attempt; effect settlement unknown |
| E2 provider response, no occurrence binding | Consistent | Unknown/partial | `CORROBORATED` for response; effect settlement unknown |
| E2R state read, occurrence bound to effect | Consistent | Attributed or profile-accepted | `CORROBORATED` or `VERIFIED` only if profile explicitly permits |
| E3 receipt, valid root and full identity binding | Consistent | Attributed | `VERIFIED(E3..., observer, trust_root)` |
| E4 corroboration, distinct roots/bindings | Consistent | Attributed | `VERIFIED(E4..., observer, trust_root)` or `CORROBORATED` |
| Conflicting material observations | Any | Conflicting | `UNKNOWN_PENDING` or `UNKNOWN_TERMINAL` |
| Read finds no effect at boundary | Consistent/insufficient | N/A | `NO_EFFECT_OBSERVED(as_of, read_semantics)` |

This table does not make E2R universally stronger or E4 universally truthful.
The property vector and trust assumptions control the result.

## 7. Pending versus terminal unknown

`UNKNOWN_PENDING` means a named action may still resolve the evidence gap. It
MUST identify a retry/review deadline, a reason, and the obligation to avoid
blind duplicate dispatch.

`UNKNOWN_TERMINAL` means the profile does not expect the gap to resolve. Typical
causes include an expired provider idempotency retention window, permanently
missing evidence, or irreconcilable conflicting observations. It MUST identify
the reason and the caller-facing escalation/compensation policy reference, if
one exists.

Neither status is failure in the external world, and neither is success.

## 8. No-effect observation

The canonical representation is:

```json
{
  "kind": "NO_EFFECT_OBSERVED",
  "as_of": "2026-09-14T12:05:00Z",
  "read_semantics": "provider lookup by echoed idempotency key at linearizable read boundary",
  "observer_principal_id": "urn:accord:example:provider-001",
  "trust_root_id": "urn:accord:example:fixture-root-001"
}
```

This says what was not observed as of a boundary. It does not say that a delayed
provider write cannot occur, that another key did not produce a semantic
duplicate, or that an unmediated path was unused.

## 9. Authority properties and unresolved algebra

This profile may carry set-like, temporal, and consumable constraint descriptors,
but it does not define a universal `<=` relation. A future authority-composition
profile must distinguish at least:

- set-like attenuation, which may admit a subsumption preorder;
- temporal constraints, which require clock/expiry semantics;
- consumable budgets, quotas, and rates, which require accounting and cannot be
  treated as a simple static partial order;
- sibling composition, which may widen effective authority even when each grant
  is individually narrow;
- parent-mediated laundering, where a child can use an authority path not
  represented in its grant.

The record can preserve the data needed to test these claims, but it does not
resolve them in ACCORD-02A.

## 10. Profile invariants

1. A higher evidence label never overrides a missing identity or invalid digest.
2. A provider signature authenticates a provider statement, not universal truth.
3. An observer-distinct record is not automatically operator-distinct.
4. Delegate-controlled evidence cannot alone produce attributed settlement.
5. Authority binding and effect binding are independently checked.
6. A task lifecycle state is never an effect settlement.
7. `UNKNOWN_PENDING` carries an obligation; it is not a retry instruction.
8. `UNKNOWN_TERMINAL` is not a license to assume success or no effect.
9. `NO_EFFECT_OBSERVED` always carries `as_of` and `read_semantics`.
10. The verifier reports profile limitations rather than silently filling them.
