# ACCORD-02A — Externally Runnable Verifier Contract

Status: candidate design specification. The verifier described here is a
portable contract, not a runtime implementation.

## 1. Purpose

The verifier evaluates a supplied portable linked-record bundle under explicitly
named trust roots and a conformance profile. It can report whether the supplied
records are structurally and cryptographically coherent, whether their links are
consistent, what their authority evidence supports, and what effect-evidence
settlement is defensible.

It cannot discover an unlisted provider fact, recreate hidden Accord state, run
Ananke policy, query Horae's database, or prevent an unmediated effect.

The governing limitation is:

> The system can verify only that a declared authority, task/effect identity,
> observation, and evidence artifact are consistent with named trust roots and
> the declared mediated channel; it cannot verify an unobserved external fact or
> prevent effects through paths it does not mediate.

## 2. External-runnability requirement

A conforming verifier MUST be runnable by a third party with no private Accord
database, hidden Accord runtime state, provider credentials, or access to the
executor's process memory.

It MUST accept all material inputs explicitly. If a required item is missing or
detached, the verifier MUST return an insufficient or unverifiable status rather
than consulting an implicit store.

The verifier MAY be embedded in a future library or command-line tool, but this
slice defines no implementation language, package, binary, service, or network
call.

## 3. Inputs

The contract has three required logical inputs and one optional input group.

### 3.1 Portable linked-record bundle

The bundle contains:

- `bundle_id` and `bundle_schema_version`;
- an array of Principal, Authority Grant, Intent, Task, Delegation, Effect
  Attempt, Effect Observation, and Evidence Artifact records;
- optional prior Verifier Results, which are treated as claims to be checked,
  not as privileged inputs;
- `bundle_digest` over canonical bundle bytes.

The bundle MUST be self-describing enough for the verifier to identify every
record referenced by a link. Detached content is represented by its digest and
an explicit disclosure status.

### 3.2 Trust-root profile

The profile maps `trust_root_id` to a public verification key, pinned issuer,
provider profile, fixture key, or other declared root. It MUST define:

- permitted signature/attestation formats;
- key or issuer scope;
- validity/revocation and freshness rules;
- observer relationship semantics;
- what the root authenticates;
- supported evidence classes and their permitted settlement outcomes.

No private key or credential is an input to verification.

### 3.3 Verifier/conformance profile

The profile declares:

- record/profile versions;
- required fields and extension rules;
- canonicalization and digest method;
- authority-linkage checks;
- effect-linkage and attribution checks;
- conflict precedence;
- evidence-class property vectors;
- settlement rules.

Structural JSON Schema validation is necessary but not sufficient for profile
conformance.

### 3.4 Optional external evidence material

The caller MAY provide detached evidence bytes, public keys, transparency-log
proofs, or fixture material explicitly referenced by the bundle. The verifier
MUST bind each supplied item to the expected digest and coverage before using
it. Unbound material is ignored or reported as an input error; it cannot improve
the result.

## 4. Verification stages

The stages are deterministic for the same canonical inputs and profile.

### Stage 0 — Input and canonical form

1. Parse JSON without accepting duplicate object keys.
2. Validate required profile/version fields.
3. Canonicalize according to the profile's JCS requirement.
4. Check bundle and record content digests.
5. Reject malformed records and report their IDs.

### Stage 1 — Identity and linkage

1. Build an index by immutable record ID.
2. Require every mandatory reference to resolve exactly once.
3. Confirm that type constraints on links hold.
4. Confirm that `effect_id` remains stable across attempts and that each
   `attempt_id` is unique.
5. Confirm that observations and evidence cover the IDs they claim to cover.
6. Preserve conflicting records; do not silently select one.

### Stage 2 — Integrity and trust roots

1. Recompute content digests.
2. Resolve the named trust root.
3. Verify supported signatures or attestations over the declared coverage.
4. Apply validity, expiry, replay, and freshness rules.
5. Return `UNVERIFIABLE` for unsupported but well-formed algorithms; return
   `INVALID` for bad signatures or digest mismatch.

### Stage 3 — Authority evidence

The verifier checks only declared evidence:

- issuer and subject identity links;
- parent/child grant and delegation links;
- constraint and derivation digests;
- authority decision references;
- validity and declared relation/profile;
- absence of link-level widening contradictions detectable by the selected
  profile.

It MUST NOT become Ananke's policy engine. A result of
`authority_evidence_status=CONSISTENT` means “the portable evidence is coherent
under this profile,” not “all external policy was obeyed.” A result of
`INSUFFICIENT` means the bundle cannot support the claimed authority relation;
it is not necessarily a denial by Ananke.

### Stage 4 — Effect evidence

The verifier evaluates observation, attribution, and evidence-class properties
independently:

- Was an observation made, and by which observer?
- What did its read semantics actually cover?
- Is the observation bound to the logical effect and, if claimed, an attempt?
- Is attribution supported by a provider operation ID, echoed idempotency key,
  signed receipt, or other profile-approved binding?
- Is the observer relationship distinct from the delegate in the way the
  profile requires?
- Is the evidence fresh, replay-resistant, and externally checkable?

An observation of occurrence without attribution is not attributed evidence. An
attributed occurrence without goal evaluation is not goal satisfaction.

### Stage 5 — Settlement

Settlement combines the authority and effect axes under profile rules. It does
not create a new fact. The result MUST include evidence class, observer, and
trust root whenever the settlement is `VERIFIED` or `CORROBORATED`.

## 5. Machine-readable result contract

The result has the following logical shape; the companion schema constrains the
required structure.

```json
{
  "schema_id": "urn:moirae:accord-02a:verifier-result",
  "schema_version": "0.1",
  "verifier_run_id": "urn:accord:example:verifier-run-001",
  "target": {
    "effect_id": "urn:accord:example:effect-001",
    "attempt_ids": ["urn:accord:example:attempt-001"],
    "bundle_digest": "sha-256:0000000000000000000000000000000000000000000000000000000000000000"
  },
  "statuses": {
    "structural": "VALID",
    "cryptographic": "VALID",
    "linkage": "VALID",
    "authority_evidence": "CONSISTENT",
    "effect_evidence": "EVIDENCED",
    "attribution": "ATTRIBUTED"
  },
  "settlement": {
    "kind": "VERIFIED",
    "evidence_class": "E3_RECEIVER_ATTESTED",
    "observer_principal_id": "urn:accord:example:provider-001",
    "trust_root_id": "urn:accord:example:fixture-root-001",
    "reason": "provider-attested receipt covers effect and attempt identities"
  },
  "findings": [],
  "generated_at": "2026-09-14T12:00:00Z"
}
```

### 5.1 Status values

The core statuses are:

| Status | Meaning |
| --- | --- |
| `VALID` | The selected structural or cryptographic check passed. |
| `INVALID` | A required shape, digest, signature, or linkage check failed. |
| `UNVERIFIABLE` | Input is well-formed but the required trust root, algorithm, or detached content is unavailable or unsupported. |
| `INSUFFICIENT` | The supplied evidence does not support the requested conclusion. |
| `CONSISTENT` | Authority evidence is internally coherent under the declared profile. |
| `INCONSISTENT` | Authority or evidence claims conflict or violate a profile rule. |
| `EVIDENCED` | The effect axis has qualifying evidence, subject to settlement rules. |
| `UNATTRIBUTED` | Occurrence may be observed, but binding to this effect/attempt is absent. |
| `CONFLICTING` | Material observations disagree and no profile rule resolves them. |
| `UNKNOWN` | A stronger outcome is not defensible from the available material. |

### 5.2 Settlement kinds

`settlement.kind` MUST be exactly one of:

- `VERIFIED` — only with `evidence_class`, `observer_principal_id`, and
  `trust_root_id` and only when the selected evidence profile permits it;
- `CORROBORATED` — evidence is materially supportive but does not meet the
  profile's `VERIFIED` conditions;
- `NO_EFFECT_OBSERVED` — a qualified observation with required `as_of` and
  `read_semantics`; it does not prove eternal absence;
- `UNKNOWN_PENDING` — stronger evidence may still be obtained before a named
  `retry_until` or review deadline;
- `UNKNOWN_TERMINAL` — the evidence gap is not expected to resolve under the
  declared profile, such as an expired idempotency window;
- `REJECTED` — the record or claim violates an integrity/linkage/profile rule.

`UNKNOWN_PENDING` and `UNKNOWN_TERMINAL` MUST include `reason` and an explicit
obligation or next decision where the profile defines one. A caller MUST NOT
interpret either as permission to retry blindly.

`NO_EFFECT_OBSERVED` MUST include:

```json
{
  "kind": "NO_EFFECT_OBSERVED",
  "as_of": "2026-09-14T12:05:00Z",
  "read_semantics": "linearizable provider lookup for the echoed idempotency key"
}
```

The core contract deliberately has no ordinary `VERIFIED_NO_EFFECT` result.
Such a result would require an exhaustive evidence profile with explicit limits;
otherwise absence at one read boundary can be followed by a delayed write.

## 6. Deterministic uncertainty and conflict rules

The following rules apply unless a stricter profile rule is declared:

| Input condition | Required outcome effect |
| --- | --- |
| Missing required record | `structural=INVALID`; settlement `REJECTED`. |
| Malformed or duplicate-key JSON | `structural=INVALID`; settlement `REJECTED`. |
| Digest mismatch or invalid signature | `cryptographic=INVALID`; affected evidence cannot support settlement. |
| Unsupported signature algorithm or missing detached bytes | `cryptographic=UNVERIFIABLE`; no upgrade from that evidence. |
| Broken or type-incompatible link | `linkage=INVALID`; settlement `REJECTED` for the affected target. |
| Expired evidence or stale read | Evidence is insufficient for a fresh settlement; use `UNKNOWN_PENDING` or `UNKNOWN_TERMINAL` according to retry/retention rules. |
| Conflicting observations | `effect_evidence=CONFLICTING`; use `UNKNOWN_PENDING` if reconciliation remains possible, otherwise `UNKNOWN_TERMINAL`. |
| Mismatched effect IDs | Do not merge; `linkage=INVALID` for the claim. |
| Mismatched attempt IDs | Do not attribute one attempt's evidence to another. |
| Replayed evidence with the same valid evidence ID/digest | Idempotent duplicate; do not count as a new observation. |
| Replayed evidence with changed bytes | `cryptographic=INVALID`; treat as tampering or conflicting evidence. |
| Provider response says accepted but no occurrence evidence exists | At most `CORROBORATED` for acceptance; effect settlement remains unknown. |
| Occurrence evidence lacks attribution | `effect_evidence=EVIDENCED`, `attribution=UNATTRIBUTED`; no attributed `VERIFIED`. |
| Attribution exists but goal is not evaluated | No goal-satisfaction claim; settlement remains evidence-limited. |
| Delegate alone asserts success | E0 only; no evidence-backed settlement. |
| Observation finds no effect at a stated boundary | `NO_EFFECT_OBSERVED(as_of, read_semantics)`, never eternal absence. |
| Idempotency retention window expired | `UNKNOWN_TERMINAL` unless a stronger provider assertion exists. |

The verifier MUST retain all conflicting record IDs and reason codes in
`findings` so a later reconciliation process can inspect them.

## 7. Authority/effect and lifecycle distinctions

The verifier uses these separate predicates:

```text
grant_authority_consistent
effective_authority_claim_consistent
task_lifecycle_state_observed
effect_attempt_recorded
effect_occurrence_observed
effect_attribution_supported
goal_satisfaction_evaluated
evidence_backed_effect_settled
```

None is an alias for another. In particular:

- a task state of `completed` does not settle an effect;
- an authority grant does not prove an effect;
- an effect observation does not create authority;
- a provider receipt does not prove the requested goal was semantically
  satisfied;
- a verifier result does not become a second authoritative Horae state.

## 8. Trust assumptions in output

Every result SHOULD include a `trust_assumptions` array with explicit entries,
for example:

- `fixture-root-001 authenticates the synthetic provider key`;
- `provider-state-read-001 is treated as linearizable only within the declared
  fixture profile`;
- `the verifier has no evidence about unmediated calls`;
- `provider signatures authenticate provider statements, not universal truth`.

If a result depends on same-operator or same-process observation, that fact MUST
be visible. The verifier MUST NOT use the word `independent` without a qualified
boundary.

## 9. Verifier failure obligations

The verifier implementation, when later built, MUST fail closed for:

- missing authority/effect linkage;
- unknown authority-affecting extensions;
- invalid signatures or digest coverage;
- an untrusted observer claiming E3/E4 evidence;
- an attempt/effect identity mismatch;
- a transport identifier presented as the only authority binding;
- a bare delegate success assertion presented as settlement.

Fail closed here means “do not emit a stronger settlement,” not “prove that no
external effect occurred.”

## 10. Later conformance and testing boundary

ACCORD-02A enables, but does not perform:

- property-based authority-linkage tests;
- model-based conflict and retry tests;
- adversarial lying and partially lying delegate tests;
- crash-after-effect and delayed-observation experiments;
- comparison against provider-state re-read plus a lightweight classifier;
- comparison across at least two transports and evidence profiles;
- offline third-party verification.

The verifier contract is therefore a falsifiability instrument, not a result of
those experiments.
