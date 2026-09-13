# ACCORD-00 Moirae Accord v0.1 Boundary

## Smallest credible public demonstration

Build one deterministic, local, framework-independent control-plane demonstration:

1. A parent agent submits a typed task/action request through an Accord adapter.
2. Accord carries an authenticated principal, acting agent, represented human (if present), bounded resource scope, purpose, deadline, parent grant, and stable correlation/task identity.
3. Ananke admits the child request only if capability, scope, purpose, principal, policy and parent-chain attenuation all match.
4. A human approval, when required, is durable and hash-bound to the exact child action and chain.
5. Horae creates the durable execution intent and claim; the executor is invoked at most once for that authority identity.
6. The child/adapter response is treated as an observation. Only a validated effect receipt or authoritative reconciliation can produce `VERIFIED_SUCCESS` or `VERIFIED_NO_EFFECT`.
7. A lost response, ambiguous provider state, or uncorrelated completion remains `UNKNOWN`; it cannot be blindly retried or reported as success.
8. The result includes a joined parent/child audit explanation and evidence references.

The public demo can use a deterministic synthetic effect adapter and local single-host durable stores. That matches the accepted FATES evidence and avoids making unsupported claims about remote exactly-once execution, Firecracker isolation, credentials, provider webhooks, or production deployment.

## Proposed Accord synthesis

Accord should own only the cross-runtime synthesis layer:

| Concern | Reuse/owner |
|---|---|
| Portable identities, context, scope, correlation | Adrasteia at `a1c...` |
| Policy, admission, approval, authority reservation, receipt validation | Ananke accepted FATES line |
| Durable execution intent, claim, invocation boundary, reconciliation | Horae accepted FATES-007A line |
| MCP transport | Ananke adapter through Accord context |
| A2A transport | New Accord adapter, initially fixture/local only |
| Parent/child chain, attenuation and CompletionVerdict | Accord-specific synthesis, with Ananke/Horae enforcement extensions |
| Memory/provenance | Mnemosyne later |
| UI/host/sandbox | Console/Moirae Code later |
| Integration proof | Fates Integration evidence-only fixtures |

## Qualitative work estimate

| Area | v0.1 new work |
|---|---|
| Adrasteia | Small-to-medium: additive chain/attenuation contract and canonical digest rules |
| Ananke | Medium: child admission, monotonic attenuation, chain-bound approval/authority, revocation lookup |
| Horae | Medium: parent/child durable task envelope and terminal evidence handoff; reuse most single-host claim machinery |
| Accord core | Medium: adapter-neutral task model, CompletionVerdict synthesis, audit join, conformance tests |
| A2A adapter | Medium: new wire/fixture boundary; keep transport narrow and do not claim a standard implementation until selected |
| MCP adapter | Small: carry Accord context through existing adapter and verify no governance bypass |
| Console later | Medium-to-large; UI/host integration is deliberately excluded |
| Mnemosyne later | Medium; useful for evidence context, not authority |
| Firecracker later | Large; requires actual host supervisor, image/runtime policy, attestation, cleanup, crash semantics and security review |

## Out of scope and non-claims

- No provider credentials, network production effects, external APIs, or browser authority.
- No multi-host consensus, distributed leases, or exactly-once claim.
- No claim that `COMPLETED` from an agent or Ananke outcome means external effect success.
- No Firecracker execution or security claim.
- No Mnemosyne-backed authorization or memory-as-truth claim.
- No Console or Protocol source modification, silent upgrade, or UI work.
- No implementation in ACCORD-00; this document is a boundary for later human-approved work.

## Open gates before ACCORD-01

1. Choose and document the exact parent/child delegation digest and subset semantics.
2. Decide whether v0.1 is one-child-only or includes bounded depth/fan-out.
3. Select the A2A wire protocol/version; the snapshot contains no existing A2A implementation.
4. Define independent effect receipt authority for the public demo and its synthetic adapter.
5. Resolve accepted-tag versus stale-evidence-document status naming in upstream Fates repositories without altering those repositories.
6. Obtain explicit approval before any runtime/schema/branch work.
