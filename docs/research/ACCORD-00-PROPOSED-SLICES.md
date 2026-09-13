# ACCORD-00 Proposed Fates Slices

Design only. No branches, tags, schemas, runtime code, or consumer pins were created. The namespace scan found no `FATES-009` identifier in the eight snapshots, but the name remains provisional until the maintainers reserve it. These slices are deliberately described without claiming that identifier.

## Slice A — portable delegation-chain contract

| Field | Proposal |
|---|---|
| Starting accepted SHA | Adrasteia `a1c01bf9e6f9d6a126cfdcc1acfacd488b214210` |
| Reuse unchanged | Principal kinds, dual-principal context, `DelegationRequest`, `DelegationDescriptor`, `ResourceScope`, correlation and purpose fields |
| New behavior | Parent grant ID, root grant ID, chain digest, hop index, maximum depth, parent deadline, attenuated capabilities/scope/budget, child task identity, explicit issuer/subject relation |
| Invariants | child authority is a subset of parent; child expiry cannot exceed parent; child scope/capabilities/budget cannot widen; represented principal cannot be replaced by the child; chain digest changes on any hop mutation; no implicit authority from transport/session/tool discovery |
| Tests | canonicalization/tamper tests; subset and deadline property tests; principal-substitution denial; depth/fan-out/budget denial; serialization compatibility |
| Dependencies | none beyond Adrasteia contract package; Ananke comparison rules must be specified before implementation |
| Rollback boundary | additive contract package/ref; existing consumers remain on their current pins |
| Existing consumers changed? | No |

## Slice B — monotonic child-admission and revocation fence

| Field | Proposal |
|---|---|
| Starting accepted SHA | Ananke accepted FATES-008 terminal `b888d61adf180d33e2ae2e61d276cb9b0f13bd12`, with FATES-007A authority provenance |
| Reuse unchanged | admission, registered-operation binding, approval store/CAS, trusted dispatch time, reservation fence, authority/receipt validation |
| New behavior | validate chain digest and parent grant status; calculate attenuated child grant; reject widening; optionally record child revocation dependency; make approval binding include chain and child task identity |
| Invariants | revoked/expired parent cannot authorize a child; child cannot outlive parent; parent approval cannot be reused for a changed child; reservation/approval conflict behavior remains deterministic; no memory fallback for durable mode |
| Tests | nested chain acceptance/rejection; parent revoke before/after reservation; replay and alternate-child conflict; crash at reservation and invocation-start; unknown remains non-redispatchable |
| Dependencies | Slice A; accepted Horae claim/receipt API; no Console or Protocol upgrade |
| Rollback boundary | new Ananke adapter/API behind an Accord-only entry point |
| Existing consumers changed? | No |

## Slice C — delegated task supervision and completion synthesis

| Field | Proposal |
|---|---|
| Starting accepted SHA | Horae accepted terminal `aa296b420fbcf578089ca66dc03f6d09d9b06f00` |
| Reuse unchanged | durable intent, owner/generation claims, checksummed transitions, invocation-start boundary, effect receipt reconciliation, `UNKNOWN` recovery |
| New behavior | parent task record, child task record, bounded wait/poll, terminal child evidence, parent settlement that maps only receipt truth to a stable CompletionVerdict |
| Invariants | agent “completed” claims are observations, not success; no child duplicate dispatch for the same authority identity; parent cannot settle `VERIFIED_SUCCESS` without a valid child receipt/reconciliation; unknown child blocks blind redispatch; parent cancellation cannot reverse an already-started effect |
| Tests | child crash/restart; lost response with known receipt; lost response with unknown effect; duplicate status; stale/forged child receipt; parent deadline; child terminal failure |
| Dependencies | Slices A/B; one local deterministic task adapter before remote transport |
| Rollback boundary | Accord-owned orchestration wrapper around Horae; no change to Horae consumers |
| Existing consumers changed? | No |

## Slice D — MCP and A2A interoperability fixtures

| Field | Proposal |
|---|---|
| Starting accepted SHA | Ananke MCP adapter at the accepted Ananke baseline; no accepted A2A baseline |
| Reuse unchanged | MCP tool discovery/executor adapter; transport-neutral Ananke governance; strict authority path |
| New behavior | Accord adapter interface for submit/status/receipt; MCP adapter carries the same chain context; A2A-shaped fixture maps remote task claims and evidence without trusting agent text |
| Invariants | discovery is not authority; transport cannot widen scope; every request has stable task/action/authority identity; remote claim without evidence is `UNKNOWN` or non-terminal, never verified success |
| Tests | same action via MCP and A2A fixture; altered transport metadata; replay; missing receipt; delayed status; child denial |
| Dependencies | Slices A–C; protocol-specific wire format remains an implementation choice for ACCORD-01 |
| Rollback boundary | Accord adapter package only; no upstream adapter mutation |
| Existing consumers changed? | No |

## Slice E — integration conformance evidence

| Field | Proposal |
|---|---|
| Starting accepted SHA | Project-Fates-Integration `source/evidence/fates-007b-claim-aware-execution-acceptance` `3c7b1f9916833728882e71f79a7276e9a806f808` |
| Reuse unchanged | checkpoint policy, exact lock/evidence discipline, inspection-only boundary |
| New behavior | Accord fixtures that assert cross-runtime chain, completion, and transport invariants |
| Invariants | Integration records proof; it does not become a runtime or authoritative peer |
| Tests | JSON lock validation, evidence provenance, negative drift tests, consumer pin checks |
| Dependencies | only after A–D are separately accepted |
| Rollback boundary | new evidence fixture/ref only |
| Existing consumers changed? | No |

## Explicit non-slices

- No Mnemosyne slice for v0.1. Memory provenance is useful later, but not required to prove delegated effect truth.
- No Firecracker slice for v0.1. Isolation is a separate host-enforcement claim.
- No Console/Protocol consumer upgrade.
- No distributed exactly-once or multi-host consensus claim.
