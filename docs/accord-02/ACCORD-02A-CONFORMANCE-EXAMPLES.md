# ACCORD-02A — Offline Conformance Examples

These examples are synthetic, offline, and non-secret. They demonstrate the
semantic contract only. They do not call a provider, exercise a runtime, or
claim that any effect happened outside the fixture.

The machine-readable bundle is
[examples/accord-02a-example-record-graphs.json](examples/accord-02a-example-record-graphs.json).
Its `expected_result` values are profile expectations, not verifier output from
an implementation. The structural schemas are
[accord-02a-portable-record.schema.json](schema/accord-02a-portable-record.schema.json)
and [accord-02a-verifier-result.schema.json](schema/accord-02a-verifier-result.schema.json).

## 1. Common fixture assumptions

The examples use these synthetic principals and trust roots:

- `principal-parent-001` — parent agent;
- `principal-child-001` — delegated child;
- `principal-ananke-001` — named authority decision issuer;
- `principal-horae-001` — durable executor/mediator;
- `principal-provider-001` — provider and observer;
- `principal-verifier-001` — verifier;
- `root-fixture-001` — synthetic public fixture root.

The fixture profile treats the provider key as authenticating provider statements
only. It does not make the provider independent from itself and does not imply
universal truth.

## 2. Example 1 — verified evidence-backed effect

Graph:

```text
parent principal
  -> authority grant issued by named authority owner
  -> intent
  -> task
  -> effect_id=effect-001
  -> attempt_id=attempt-001
  -> provider receipt bound to effect_id, attempt_id, action hash, and echoed key
  -> provider observer + fixture trust root
```

Expected result:

```text
authority_evidence=CONSISTENT
effect_evidence=EVIDENCED
attribution=ATTRIBUTED
settlement=VERIFIED(E3_RECEIVER_ATTESTED, principal-provider-001, root-fixture-001)
```

This does not prove the requested goal was semantically satisfied beyond the
receipt coverage, and it does not say anything about unmediated paths.

## 3. Example 2 — UNKNOWN_PENDING

Graph:

```text
grant -> task -> attempt-002 -> provider accepted response
                              -> no occurrence evidence yet
```

Expected result:

```text
effect_evidence=UNKNOWN
settlement=UNKNOWN_PENDING
reason=provider accepted the request but occurrence/attribution evidence is absent
retry_until=fixture-defined deadline before idempotency retention expiry
```

The caller must not blindly dispatch another attempt. A later state read or
receipt may resolve the record; if the retention window expires, the result may
become `UNKNOWN_TERMINAL`.

## 4. Example 3 — NO_EFFECT_OBSERVED

Graph:

```text
attempt-003 -> provider state read at 2026-09-14T12:05:00Z
              read_semantics=linearizable lookup by echoed idempotency key
              observed_state=not_found
```

Expected result:

```text
settlement=NO_EFFECT_OBSERVED(
  as_of=2026-09-14T12:05:00Z,
  read_semantics=linearizable lookup by echoed idempotency key
)
```

This is not `VERIFIED_NO_EFFECT`. It does not rule out a later delayed write,
another semantic key, or an unmediated effect path.

## 5. Example 4 — lying child

Graph:

```text
child -> task lifecycle completed
child -> E0_DELEGATE_ASSERTION claiming success
no provider observation, receipt, or observer-distinct evidence
```

Expected result:

```text
task_lifecycle_state=observed
effect_evidence=UNKNOWN
attribution=UNKNOWN
settlement=UNKNOWN_PENDING or UNKNOWN_TERMINAL
```

The child assertion cannot produce a stronger result. If the child later
provides a forged receipt, a digest/signature/trust-root failure produces an
invalid or unverifiable result rather than `VERIFIED`.

## 6. Example 5 — retry and duplicate-attempt distinction

Graph:

```text
effect_id=effect-005
  ├─ attempt_id=attempt-005a, idempotency_key_digest=key-005
  └─ attempt_id=attempt-005b, idempotency_key_digest=key-005
```

The two attempt records have distinct dispatch times, retry ordinals, and
attempt identities. A provider may report one occurrence, two occurrences, or
neither. The record graph preserves all three possibilities:

- one occurrence bound to both attempts through a provider idempotency echo;
- two occurrences, indicating a duplicate-effect candidate;
- no decisive observation, yielding `UNKNOWN_PENDING` or `UNKNOWN_TERMINAL`.

The verifier MUST NOT merge the attempts merely because their logical effect or
idempotency-key digest is equal.

## 7. Transport-carriage shapes

The same semantic bundle can be placed in three envelopes:

```json
{
  "transport": {
    "kind": "local_fixture",
    "message_id": "local-message-001"
  },
  "semantic_bundle_ref": "urn:accord:example:bundle-001"
}
```

```json
{
  "transport": {
    "kind": "mcp_shaped",
    "tool_name": "synthetic.effect",
    "call_id": "mcp-call-001",
    "session_id": "mcp-session-001"
  },
  "semantic_bundle_ref": "urn:accord:example:bundle-001"
}
```

```json
{
  "transport": {
    "kind": "a2a_shaped",
    "context_id": "a2a-context-001",
    "task_id": "a2a-task-001",
    "message_id": "a2a-message-001",
    "task_state": "TASK_STATE_UNSPECIFIED"
  },
  "semantic_bundle_ref": "urn:accord:example:bundle-001"
}
```

The `semantic_bundle_ref` and its linked records carry the authority/effect
meaning. The transport IDs are correlation hints. They cannot widen authority,
replace `effect_id`/`attempt_id`, or settle an effect. In particular,
`TASK_STATE_UNSPECIFIED` is not automatically `UNKNOWN_PENDING` for an effect;
an effect observation and evidence profile are still required.

## 8. Conformance assertions

A later implementation can run these assertions without external services:

1. Example 1 can emit `VERIFIED` only with evidence class, observer, and trust
   root in the result.
2. Example 2 cannot emit `VERIFIED` from a provider acceptance response alone.
3. Example 3 emits qualified `NO_EFFECT_OBSERVED`, never bare no-effect truth.
4. Example 4 cannot emit `VERIFIED` from the child's assertion.
5. Example 5 retains two distinct attempt IDs and never treats a retry as the
   same attempt.
6. Replacing a semantic record's transport envelope does not change the result.
7. Removing a detached evidence artifact degrades to `INSUFFICIENT`,
   `UNVERIFIABLE`, or an UNKNOWN outcome; it does not consult hidden state.
8. Changing an evidence digest or effect ID causes invalidity or a linkage
   failure.

## 9. Schema boundary

The schemas in `schema/` validate the conservative shape of a bundle and result.
They do not prove signatures, run the authority relation, evaluate provider
state, or decide goal satisfaction. Those are verifier-profile semantics.
