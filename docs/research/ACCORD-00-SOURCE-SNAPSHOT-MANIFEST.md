# ACCORD-00 Source Snapshot Manifest

Status: read-only static audit. Snapshot root: `D:\Users\fleur\Moirae Accord - Source Snapshots\ACCORD-00-20260913-215700`.

Audit timestamp: `2026-09-13T22:40:45.5598558+01:00`.

All eight repositories were cloned before substantive analysis. Each copy fetched ordinary remote branches and tags. The fetch URL remains the original GitHub URL; the copy-only push URL was replaced with an unusable `example.invalid` destination. No push was attempted.

## Accord starting state

| Item | Observation |
|---|---|
| Local root | `D:\Users\fleur\Moirae Accord` |
| Expected remote | `https://github.com/hourwise/Moirae-Accord` |
| Initial branch/status | `main...origin/main`, clean |
| Initial HEAD | `fd336a80f3e98f5d19f4dd18214977f243514357` |
| Initial files | `.git`, `README.md` only |
| Snapshot writes | outside the Accord repository |
| Accord writes during ACCORD-00 | research/audit documents only |

## Repository snapshots

| Repository | Source URL / fetch URL | Checked-out ref | HEAD | Status | Snapshot path | Push URL |
|---|---|---|---|---|---|---|
| Moirae-Protocol | `https://github.com/hourwise/Moirae-Protocol.git` | `main` | `f179104697d5ce126fdc19306e707e100cad05ff` | clean | `...\Moirae-Protocol` | `https://example.invalid/accord-00/Moirae-Protocol.git` |
| Project-Ananke | `https://github.com/hourwise/Project-Ananke.git` | `main` | `3d76adb162a0ff07b5630700ae30a823f1419cb4` | clean | `...\Project-Ananke` | `https://example.invalid/accord-00/Project-Ananke.git` |
| Project-Fates-Integration | `https://github.com/hourwise/Project-Fates-Integration.git` | `main` | `b4ae41185bafa6b6dd80ff7e41b1de7a2915873f` | clean | `...\Project-Fates-Integration` | `https://example.invalid/accord-00/Project-Fates-Integration.git` |
| Project-Horae | `https://github.com/hourwise/Project-Horae.git` | `main` | `3f531d4f5558a10a36aeae20c3458080eb4468b9` | clean | `...\Project-Horae` | `https://example.invalid/accord-00/Project-Horae.git` |
| Moirae-Console | `https://github.com/hourwise/Moirae-Console.git` | `main` | `893ef94fa0dfad3606bd83e8b46351210cfc0d51` | clean | `...\Moirae-Console` | `https://example.invalid/accord-00/Moirae-Console.git` |
| Project-Moirae-Code | `https://github.com/hourwise/Project-Moirae-Code.git` | `main` | `9a5de8461b96db2cdb7bb85343cb48a60b5e4eb0` | clean | `...\Project-Moirae-Code` | `https://example.invalid/accord-00/Project-Moirae-Code.git` |
| Project-Mnemosyne | `https://github.com/hourwise/Project-Mnemosyne.git` | `main` | `f4ab76a9760f856d78908d35facceb068d78c8e5` | clean | `...\Project-Mnemosyne` | `https://example.invalid/accord-00/Project-Mnemosyne.git` |
| Project-Adrasteia | `https://github.com/hourwise/Project-Adrasteia.git` | `main` | `f9eeb25076e0a590f13c7bed6c8de8c9a363ce1b` | clean | `...\Project-Adrasteia` | `https://example.invalid/accord-00/Project-Adrasteia.git` |

The abbreviated `...` path above is only for table readability; the complete root is the snapshot root stated at the top of this document.

## Visible remote branches

The following branch names were visible in the fetched copies. The full ref objects remain available in the snapshot Git databases; the SHA of every checked-out `main` is recorded above and relevant non-main SHAs are recorded in the pin matrix.

| Repository | Visible remote branches |
|---|---|
| Moirae-Protocol | `source/main`; `source/codex/mp04-durable-governed-execution`; `source/codex/mp04a`; `source/codex/mp04b`; `source/codex/mp05-fates008-readiness`; `source/codex/mp05-human-approval-design`; `source/codex/mp05-human-approval-runtime`; `source/codex/mp05c`; `source/codex/mp05e`; `source/codex/mp05g`; `source/codex/mp06a`; `source/codex/mp06b`; `source/codex/mp06c`; `source/codex/mp06d`; `source/codex/mp07a`; `source/codex/mp07b`; `source/codex/mp07c`; `source/codex/mp07d` |
| Project-Ananke | `source/main`; `source/codex/fates-008a-durable-human-approval`; `source/codex/fates-008c-idempotent-decision-audit`; `source/codex/fates-008e-revocation-dispatch-boundary`; `source/codex/fates-008g-fresh-dispatch-time`; `source/codex/fates-ananke-text-preflight`; `source/codex/fates-moirae-001a`; `source/codex/mc-03`; `source/codex/mc-04`; `source/codex/mc-05`; `source/codex/mc-06`; `source/codex/mc-10`; `source/codex/mc-11`; `source/codex/mc14-redteam-remediation`; `source/codex/slice-002-bounded`; `source/codex/slice-002-http` |
| Project-Fates-Integration | `source/main`; `source/codex/fates-004b`; `source/codex/fates-005a`; `source/codex/fates-005c`; `source/codex/fates-005d`; `source/codex/fates-005d-r1`; `source/codex/fates-008h-acceptance-evidence`; `source/codex/moirae-001a-integration-evidence`; `source/codex/moirae-001a-mainline`; `source/codex/mc-04`; `source/codex/mc-05`; `source/codex/mc-06`; `source/codex/restart`; `source/codex/slice-002-activation`; `source/codex/slice-002-boundary`; `source/codex/slice-002-owner-approvals`; `source/codex/slice-002-feasibility`; `source/codex/slice-002-scope`; `source/codex/slice-003a-activation`; `source/evidence/fates-007b-claim-aware-execution-acceptance` |
| Project-Horae | `source/main`; `source/codex/fates-005d`; `source/codex/fates-005d-r1`; `source/codex/fates-horae-inspection-admission`; `source/codex/slice-002-design` |
| Moirae-Console | `source/main`; `source/codex/mc-00`; `source/codex/mc-01`; `source/codex/mc-02`; `source/codex/mc-03`; `source/codex/mc-04`; `source/codex/mc-05`; `source/codex/mc-06`; `source/codex/mc-07-hackathon-release-candidate`; `source/codex/mc-09`; `source/codex/mc-11`; `source/codex/mc-12-docs`; `source/codex/mc-12-status`; `source/codex/mc14-redteam-remediation`; `source/codex/mc15` |
| Project-Moirae-Code | `source/main`; `source/codex/fates-004b-firecracker-supervisor`; `source/codex/fates-005a-moirae-implementation`; `source/codex/fates-moirae-scoped-vsock-delivery`; `source/codex/slice-002-constrained-host-design`; `source/codex/slice-003a-host-route` |
| Project-Mnemosyne | `source/main`; `source/codex/fates-005d-durable-governance`; `source/codex/fates-mnemosyne-admission-gate`; `source/codex/fates-mnemosyne-provenance-envelope` |
| Project-Adrasteia | `source/main`; `source/codex/fates-content-preflight`; `source/codex/mc-11-public-source-contracts`; `source/codex/slice-002`; `source/release/webmcp-runtime-v0.6.2` |

## Visible tags and relevant release refs

| Repository | Visible tags / release refs |
|---|---|
| Moirae-Protocol | `moirae-protocol-mp03-fates-admission-v0.1.0`; `moirae-protocol-mp04-durable-governed-execution-v0.1.0`; `mp-03-accepted-v1`; `mp-05-accepted-v1`; `mp-06-accepted-v1`; `mp-07-accepted-v1`; `mp-08b-execution-02a`; `mp-08b-final-accepted-v1`; `mp-08b-provider-02b-r4a`; `mp-08b-provider-02b-r4c`; `mp-08b-provider-02b-r6`; `mp-09-focused-accepted-v1` |
| Project-Ananke | `ananke-adrasteia-adoption-v0.1.0-protocol-1.4.0`; `ananke-fates-007a-claim-aware-execution-v0.1.0-protocol-1.4.0`; `ananke-fates-008a-durable-human-approval-v0.1.0-protocol-1.4.0`; `ananke-fates-slice-002-v0.1.0-protocol-1.4.0`; `ananke-fates-slice-002-v0.2.0-protocol-1.4.0`; `ananke-fates-slice-003a-r1-v0.1.0-protocol-1.4.0` |
| Project-Fates-Integration | `fates-slice-002-v0.1.0-protocol-1.4.0`; `fates-slice-003a-v0.1.0-protocol-1.4.0`; `fates-slice-003a-r1-v0.1.0-protocol-1.4.0`; `fates-slice-004a-v0.1.0-protocol-1.4.0` |
| Project-Horae | `horae-fates-007a-claim-aware-execution-v0.1.0-protocol-1.4.0`; `horae-fates-slice-003a-r1-v0.1.0-protocol-1.4.0` |
| Moirae-Console | no Git tags observed; protected release candidates are branch/document pins |
| Project-Moirae-Code | `moirae-fates-slice-003a-v0.1.0-protocol-1.4.0`; `moirae-fates-slice-003a-r1-v0.1.0-protocol-1.4.0` |
| Project-Mnemosyne | `mnemosyne-adrasteia-adoption-v0.1.0-protocol-1.4.0` |
| Project-Adrasteia | `adrasteia-adoption-v0.4.0`; `adrasteia-preflight-v0.5.0-protocol-1.4.0`; `adrasteia-preflight-v0.6.0-protocol-1.4.0`; `adrasteia-preflight-v0.6.1-protocol-1.4.0`; `adrasteia-preflight-v0.6.2-protocol-1.4.0`; release branch `source/release/webmcp-runtime-v0.6.2` |

## Snapshot method and safety

- Only `git clone`, ordinary branch/tag fetches, read-only Git inspection, and copy-local push-URL replacement were used against the isolated copies.
- No source copy was checked out to a new branch, merged, rebased, tagged, committed, cleaned, or pushed.
- The warnings about the sandbox user's Git ignore file were read-only environment warnings; they did not change repository state.
- This manifest is an audit artifact, not a claim that the current `main` branch is the most advanced or authoritative implementation.
