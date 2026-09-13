# ACCORD-00 Protected References

This is the Accord do-not-mutate registry. The listed refs are evidence, historical checkpoints, or hackathon/release material. They are not writable development bases and were not changed during this audit.

## Protected hackathon and release material

| Repository | Protected ref/SHA | Evidence | Protection reason |
|---|---|---|---|
| Moirae-Console | reviewed implementation `8c5109c52bb8065d9c1b4f4a81e0e6df9e830030` as named by `docs/CHALLENGE_RELEASE_MANIFEST.json`; preceding remediation `204e52e697ea239de7277d2052809a51826773db`; reviewed Ananke `3d76adb162a0ff07b5630700ae30a823f1419cb4`; Adrasteia `a1c01bf9e6f9d6a126cfdcc1acfacd488b214210` | `docs/CHALLENGE_RELEASE_MANIFEST.json`, `docs/PUBLIC_RUNTIME_DISTRIBUTION.md`, `docs/FATES_BOUNDARY.md` | Sealed WebMCP hackathon candidate; `deploymentAuthorized: false`; current snapshot `main` is a later/different checked-out state. The reviewed implementation object was not visible in the fetched copy and is recorded as a documented protected SHA, not silently promoted. |
| Moirae-Console | branch `source/codex/mc-07-hackathon-release-candidate` at `77eaebe4b5a27e6f8d26e108d11afb371922dcfd` | `docs/HACKATHON_SUBMISSION.md`, WebMCP boundary and publication tests | Frozen hackathon release candidate; browser and WebMCP are deliberately non-authoritative. |
| Moirae-Protocol | `mp-08b-final-accepted-v1` at `baa269a53c46e4fd8cbc3ec1640c984280d596b6` | `docs/MP09_FOCUSED_ADVERSARIAL_ACCEPTANCE.md` | Frozen submission lineage; exactly one provider invocation in the characterization, Horae `UNKNOWN`, no independent external-effect confirmation, and no resend. |
| Moirae-Protocol | `mp-09-focused-accepted-v1` at `7bf7448fc66b42724062916362f3e1a490609a2c` | MP-09 acceptance document | Focused adversarial acceptance; it specifically protects against authority injection, approval replay, duplicate execution, provider-success escalation, and `UNKNOWN` escalation. |
| Moirae-Protocol | `mp-07-accepted-v1` at `983b785bd68e06d280a5af2898d3b43533688518` | MP-07 acceptance evidence | Product surface acceptance; browser/UI does not create policy, approval, execution, retry, reconciliation, or effect truth. |

## Protected accepted Fates checkpoints

| Runtime | Accepted ref/SHA | Evidence and scope |
|---|---|---|
| Adrasteia | `source/release/webmcp-runtime-v0.6.2` and `source/codex/mc-11-public-source-contracts`, both `a1c01bf9e6f9d6a126cfdcc1acfacd488b214210` | `RuntimeProfile`, dual-principal `ExecutionContext`, `DelegationDescriptor`, `ResourceScope`, runtime identity/registration/capability contracts. Declarative contracts only; no authority minting, signing, storage, validation, revocation, or credential exchange. |
| Ananke | `ananke-fates-007a-claim-aware-execution-v0.1.0-protocol-1.4.0`, tag object `9fb9fc4d8183db64aa37f0a4e167fdf41ca856e5`, peeled terminal `114063e03332af3389fe805193e88a62111d9323` | FATES-007A claim-aware authority and effect receipt path. |
| Ananke | `ananke-fates-008a-durable-human-approval-v0.1.0-protocol-1.4.0`, annotated tag object `0fa08f78f27e2f79c895402f3f53a8aada5837b4`, accepted terminal `b888d61adf180d33e2ae2e61d276cb9b0f13bd12` | Durable approval decision boundary; SQLite single-host/cross-process/restart scope. The tag is accepted, while some evidence JSON files retain an older `implementation-candidate` label; the annotated tag and terminal source are treated as higher-priority provenance. |
| Ananke | runtime ancestor `c89b83de40ed0275969fe3931220f440bf082aa3` | Trusted-time refresh at approval dispatch; provenance for the FATES-008G family. |
| Horae | `horae-fates-007a-claim-aware-execution-v0.1.0-protocol-1.4.0`, tag object `59763d34644567c59d1041b3acef24efc5a1d072`, peeled terminal `aa296b420fbcf578089ca66dc03f6d09d9b06f00` | FATES-007B accepted Horae terminal: durable owner/generation claim, full authority binding, checksummed lifecycle, non-blind `UNKNOWN` recovery, receipt-bound `CONFIRMED`/`ABSENT`/`UNKNOWN`. |
| Horae | runtime ancestor `7b24cb0af083e505bd2dc9fa55c6c3387f849131` | Durable claims bound to Fates authority; provenance for the accepted terminal. |
| Protocol | `moirae-protocol-mp04-durable-governed-execution-v0.1.0`, tag commit `5a073ab...` | MP-04 accepted integration of Ananke/Horae durable execution; fixture-bound, synthetic/offline, local single-host/cross-process. |

## Rules for future Accord work

1. Existing consumers remain pinned to their documented SHAs. An Accord ref must never be substituted into Console, Protocol, or any existing release without an explicit consumer change and independent acceptance.
2. No historical branch, accepted tag, release ref, evidence SHA, or hackathon material may be rewritten.
3. Any future Fates evolution must branch from an accepted checkpoint, add a new ref, and record a new acceptance boundary.
4. The protected registry is evidence of provenance, not authority to modify the upstream repositories.
