# ACCORD-00 Fates Delta Audit

## Executive finding

The ecosystem already contains most of the hard single-host execution truth required by the research claim: exact action binding, dual-principal context, admission, durable authority claims, reservation, invocation-start boundaries, receipts, `CONFIRMED`/`ABSENT`/`UNKNOWN`, durable human approval, and no-blind-retry recovery. It does not yet provide portable nested agent delegation with monotonic authority attenuation, remote task supervision, cascading child revocation, or a framework-independent A2A transport adapter.

The smallest credible Accord v0.1 is therefore a new synthesis/control-plane demonstration over accepted Ananke/Horae/Adrasteia checkpoints, with one narrow A2A-shaped adapter and an MCP adapter reuse path. It should not begin by rebuilding durable execution, adding Mnemosyne, or enabling Firecracker.

## Requirement matrix

| Requirement | Status | Owner | Evidence | What exists | Exact gap | V0.1? |
|---|---|---|---|---|---|---|
| Canonical principals | ALREADY_PRESENT | Adrasteia | `a1c...`, `src/identity/Principal.ts` | human, service, agent, runtime kinds | Accord needs a stable chain-facing identifier convention | YES |
| Dual-principal identity | ALREADY_PRESENT | Adrasteia | `a1c...`, `DualPrincipalContextSchema`, `ExecutionContextSchema` | authenticated, acting, optional represented principal | Must be carried through every child task hop without substitution | YES |
| Delegation request | EXTEND | Adrasteia / Accord | `a1c...`, `DelegationRequest` | request/action/audience/capability/scope/purpose/approval/correlation fields | No parent-grant/root-grant/delegation-chain fields or attenuation proof | YES |
| Delegation grant | EXTEND | Adrasteia / Ananke | `a1c...`, `DelegationDescriptor`; Ananke FATES-007A | grant/issuer/subject/audience/scope/expiry/nonce/revocation reference | No deterministic child grant issuance and monotonic comparison | YES |
| Capability attenuation | EXTEND | Ananke | Ananke accepted admission/authority code | operation and capability binding exists | Child capability set must be subset of parent, with fail-closed comparison | YES |
| Resource-scope attenuation | EXTEND | Ananke / Adrasteia | `ResourceScope.ts`; `admission.ts` | bounded scope and exact admission matching | Recursive scope intersection/subset semantics are not implemented | YES |
| Expiry attenuation | EXTEND | Ananke | FATES-008G `b888...` | trusted dispatch-time expiry | Child deadline must be no later than parent and remain bound after handoff | YES |
| Revocation | EXTEND | Ananke / Accord | accepted approval store and `GrantReference` | approval revocation and reservation fence | Child cascade/revocation tree is absent | MAYBE; single-hop v0.1 can require parent lookup |
| Nested delegation | NEW | Accord / Ananke | no `FATES-009` matches; no chain model | single-hop authority context only | durable multi-hop grant chain, parent links, attenuation checks | YES, narrow |
| Depth limits | NEW | Accord / Ananke | no chain/depth symbols found | session budgets exist in Adrasteia profiles | explicit max depth and terminal denial | YES |
| Fan-out limits | NEW | Accord / Horae | no delegation-tree implementation | Ananke/Horae budgets/claims are local execution concepts | child count/fan-out accounting | MAYBE; fixed one-child demo first |
| Budget attenuation | EXTEND | Adrasteia / Ananke | `SessionBudget`; Ananke policy/admission | max duration/tool calls/write actions/approvals | transfer and decrement budgets across parent/child | YES, duration/action budget only |
| Agent discovery | ALREADY_PRESENT | Horae / Adrasteia | Horae registry/discovery; `RuntimeProfile` | runtime identity, capabilities, health/readiness | agent-task endpoint and protocol metadata absent | YES for runtime discovery only |
| Policy-filtered discovery | EXTEND | Horae / Ananke | Horae capability reduction; Ananke admission | descriptive discovery and policy filtering scaffolds | discovery must be derived from attenuated authority and never imply authority | YES |
| Human approval | ALREADY_PRESENT | Ananke | accepted FATES-008A/G `b888...` | durable decision, binding, CAS, revocation fence, trusted dispatch time | approval of a child delegation needs chain-bound presentation | YES, as extension |
| Durable execution identity | ALREADY_PRESENT | Ananke / Horae | FATES-007A accepted tags; `computeDurableExecutionId` | native action hash, durable execution ID, authority-instance digest | parent/child task identity composition | YES |
| Claim/lease | ALREADY_PRESENT | Horae | `fates-007a.ts`, accepted `aa296...` | owner/generation claim and cross-process arbitration | remote/multi-host lease semantics absent | YES local only |
| Cross-process arbitration | ALREADY_PRESENT | Ananke / Horae | accepted stores and locks | local SQLite/filesystem process arbitration | no multi-host consensus | YES local only |
| Retry semantics | ALREADY_PRESENT | Ananke / Horae | retry/idempotency docs; claim-aware execution | retry before effect boundary; no blind retry after unknown | child-task retry ownership and parent notification | YES |
| Idempotency | EXTEND | Ananke / Horae | provider key/receipt types and durable bindings | local durable identity and adapter fields | provider idempotency is not universal and no framework-independent contract | YES for adapter contract |
| Duplicate suppression | ALREADY_PRESENT | Ananke / Horae | accepted claims, reservation, MP-09 tests | no duplicate executor dispatch for same durable identity | needs child task duplicate identity | YES |
| Effect identity | ALREADY_PRESENT | Ananke / Horae | native action hash, durable ID, authority instance | exact effect binding | composition into parent/child tree | YES |
| Effect receipt | ALREADY_PRESENT | Ananke / Horae | `createEffectReceiptV1`, `recordEffectReceipt` | binding, provider operation/idempotency, provenance, checksum | independent remote-agent receipt adapter | YES |
| `CONFIRMED` / `ABSENT` / `UNKNOWN` | ALREADY_PRESENT | Ananke / Horae | accepted FATES-007A/MP-04 | explicit states and unknown recovery | Accord-facing CompletionVerdict mapping | YES |
| Crash-after-effect reconciliation | ALREADY_PRESENT | Horae / Ananke | accepted FATES-007A; MP-04 evidence | restart recovery and reconciliation-required state | cross-runtime/remote agent recovery | YES local |
| Remote task lifecycle | NEW | Accord / Horae | no accepted remote-task implementation | runtime lifecycle/health only | durable delegated task status, polling, timeout, handoff | YES narrow |
| Remote-completed != verified-success | EXTEND | Accord / Ananke | Ananke `Outcome` docs say success is not independent effect truth; receipts are stronger | typed outcomes and unknown | one public Accord verdict must never map agent claim to success | YES |
| Cancellation propagation | NEW | Accord / Horae | no nested task cancellation tree | local cancellation concepts only | parent cancellation, child stop/settlement, effect-boundary rules | NO for first proof; document boundary |
| CompletionVerdict | EXTEND | Accord | existing `Outcome` + FATES receipts | outcome states and effect truth are split across runtimes | stable cross-transport verdict: verified success/no-effect/failure/rejected/cancelled/unknown | YES |
| Audit provenance | EXTEND | Ananke / Accord | audit event types and approval evidence | runtime audit events and correlation | one joined parent/child audit explanation | YES |
| Evidence provenance | EXTEND | Ananke / Horae | receipt provenance/checksum and Protocol MP-09 evidence | local evidence lineage | independently verifiable agent-origin/effect evidence envelope | YES |
| MCP adapter | ALREADY_PRESENT / EXTEND | Ananke | `packages/mcp-adapter/src/mcp-adapter.ts` | stdio discovery and tool execution adapter | must route through Accord delegation context; no direct bypass | YES reuse |
| WebMCP host surface | OUT_OF_SCOPE | Console | Console WebMCP boundary and fixed publication host | useful approval/evidence UX | no Accord UI in ACCORD-00 | NO |
| A2A adapter | NEW | Accord | no implementation; no `FATES-009` namespace | only conceptual/lockfile evidence | transport-neutral agent task request/status/evidence bridge | YES, narrow fixture adapter |
| Firecracker isolation | OUT_OF_SCOPE_FOR_ACCORD_V0_1 | Moirae Code / host | sandbox `MicroVM` enum and future roadmap; no executor | declared mode and risk mapping | verified host supervisor, image, attestation, lifecycle | NO |
| Mnemosyne provenance | OUT_OF_SCOPE_FOR_ACCORD_V0_1 | Mnemosyne | governed memory/source/reliability/retrieval | qualified memory and source hashes | not needed to establish delegated effect truth | NO |
| Console human surface | OUT_OF_SCOPE_FOR_ACCORD_V0_1 | Console | protected hackathon material | approval cards and evidence display concepts | UI integration and protected consumer upgrade | NO |

## Completion truth assessment

The ecosystem is close to an Accord completion verdict on one host, but the pieces must be joined carefully:

1. An Ananke `COMPLETED` outcome is a runtime/tool outcome and is explicitly not by itself an independently verified external effect.
2. Horae's accepted FATES-007A lifecycle can record an effect receipt as `CONFIRMED`, `ABSENT`, or `UNKNOWN`; `UNKNOWN` is not retryable and does not reopen dispatch.
3. Protocol MP-04 and MP-09 demonstrate the intended separation: an executor return or provider success observation cannot elevate an uncorrelated external effect to confirmed truth.
4. Accord should define only a synthesis mapping over those existing states, with `VERIFIED_SUCCESS` requiring a valid receipt/reconciliation, `VERIFIED_NO_EFFECT` requiring authoritative absence, and `UNKNOWN` remaining terminal-for-redispatch but non-success.

## Documentation/code contradictions

- Ananke's accepted FATES-008 annotated tag accepts the durable approval decision boundary, while some `docs/evidence/fates-008*.json` files still say `implementation-candidate`; the accepted tag and terminal source outrank stale evidence labels.
- Horae's current `main` omits/reverts the accepted FATES-007A implementation; the accepted tag is the baseline for this audit.
- Protocol MP-05 and MP-06 documents describe candidate/readiness states even though accepted tags exist in the snapshot. They are not treated as new runtime guarantees without matching accepted source and evidence.
- Console's manifest names reviewed SHA `8c5109c...`, but that object/ref was not present in the fetched copy. It remains a protected documented pin, not a verifiable Accord dependency.
- Integration's `fates-lock.json` is explicitly provisional/inspection-only; it is conformance evidence, not an authoritative runtime composition.
