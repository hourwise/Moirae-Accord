# ACCORD-00 Reuse Matrix

The matrix separates safe reuse of accepted runtime behavior from conceptual reuse of candidates and proposals. “Reuse unchanged” means the behavior can remain owned by its existing runtime behind an explicit adapter; it does not mean copying source or silently changing a consumer pin.

| Area | Reuse unchanged | Extend | Conceptual only / defer | Owner boundary |
|---|---|---|---|---|
| Principal and runtime identity | Adrasteia `Principal`, `ExecutionContext`, runtime identity and correlation contracts at `a1c...` | Add chain/parent/root grant references | None | Adrasteia contracts; Accord chain semantics |
| Resource scope | Adrasteia bounded/unscoped `ResourceScope` validation shape | Define scope subset/intersection and attenuation proof | Policy prose without enforcement | Ananke |
| Delegation | Adrasteia request/descriptor shapes | Multi-hop chain, parent grant, depth, fan-out, deadline/budget attenuation | Existing descriptor alone is not a delegation engine | Accord + Ananke |
| Admission | Ananke accepted admission and exact registered-operation binding | Admit child requests only under parent grant and attenuated scope | Proposed ADRs without runtime | Ananke |
| Durable authority | Ananke accepted FATES-007A authority/receipt and FATES-008 reservation fence | Bind parent/child task identity to native authority hash | Candidate branches not promoted | Ananke |
| Durable execution | Horae accepted FATES-007A claim store and lifecycle | Add delegated remote-task envelope and parent wait/recovery | Multi-host exactly-once | Horae + Accord |
| Completion truth | `CONFIRMED`/`ABSENT`/`UNKNOWN`, checksums, receipt provenance | Stable Accord `CompletionVerdict` mapping and joined evidence | Agent-reported “done” | Accord synthesis over Ananke/Horae |
| Human approval | Ananke durable approval store, binding, trusted dispatch time, revocation | Bind approval presentation to delegation chain and child action | Console UI integration | Ananke; future Console |
| MCP | Ananke stdio MCP adapter and tool metadata | Carry Accord context and enforce the same authority path | MCP itself is not authority | Ananke adapter + Accord |
| A2A | No accepted code | New transport adapter with deterministic request/status/evidence mapping | No namespace or protocol commitment exists | Accord |
| Discovery | Horae/Adrasteia capability and health/readiness contracts | Policy-filtered child-visible capabilities | Discovery as authority | Horae + Ananke |
| Host/sandbox | Moirae Code sandbox schemas, risk mapping, approval preview | Only later connect to a verified executor | Firecracker/microVM, actual spawning, supervisor launch | Moirae Code / host; v0.1 defer |
| Memory | Mnemosyne source maps, reliability, classification, qualified retrieval | Later attach provenance context to tasks | Memory as authority or completion proof | Mnemosyne; v0.1 defer |
| Integration control | Fates Integration locks/checkpoint policy/evidence conventions | Add Accord conformance fixtures without entering runtime | Integration as runtime | Integration remains evidence-only |
| Human surface | Console allow/approval/deny/evidence concepts and host-bound publication model | Later build Accord UI | Modifying sealed Console or Protocol artifacts | Console later |

## Licensing and provenance

| Repository/package | Observed license metadata | Reuse posture |
|---|---|---|
| Project-Ananke | root/package metadata indicates MIT | Package/source reuse may be considered after pin review and independent acceptance; do not install or modify during ACCORD-00. |
| Project-Adrasteia | root/package metadata indicates MIT | Safe contract dependency candidate at exact `a1c...`; keep source pin explicit. |
| Moirae-Protocol | repository/package metadata inspected; accepted artifact lineage | Use as evidence/test oracle unless a separate dependency decision is made. |
| Moirae-Console | Apache-2.0 in sealed release manifest | Concepts and UI evidence only in v0.1; no silent upgrade. |
| Project-Moirae-Code | root `package.json` MIT; `docs/THIRD_PARTY.md` records MIT/Apache/EPL/Public Domain dependencies and restrictions | Conceptual/host design reuse; dependency adoption requires a separate supply-chain and license review. |
| Project-Mnemosyne | package metadata inspected; dependency includes MIT/Apache-compatible runtime contracts and better-sqlite3/zod | Defer runtime reuse; later review package-level license inventory and source provenance. |
| Project-Horae | source snapshot and package metadata inspected | Use accepted behavior by exact ref; do not infer a license grant beyond repository metadata. |
| Project-Fates-Integration | control/evidence repository; package metadata inspected | Evidence/fixtures only; not a runtime dependency. |

No source license, package manifest, or third-party dependency was changed. No dependency was installed.
