# ACCORD-01 Acceptance

## Scope

ACCORD-01 evaluated a deliberately blinded external adversarial review of the
Moirae Accord research question, methodology, terminology, prior-art framing,
and proposed architecture. Phase 1 was a blind review of the brief; Phase 2
was an architecture red-team review after the blind analysis was frozen.

This acceptance records a pivot. It does not authorize implementation, modify
the ACCORD-00 seal, modify the protected snapshots or source repositories, or
begin ACCORD-02.

## Accepted ancestry and protected evidence

| Item | Value |
|---|---|
| ACCORD-00 accepted parent | `ddad3092b8b1d1d4ac5ab496143263ddd6afc587` |
| ACCORD-00 accepted tag | `accord-00-accepted-v1` resolving to the parent above |
| ACCORD-01A review-pack commit | `7494da26e43248e6bc5df5f081e3dc9d5aa831c4` |
| Accord branch | `main` |
| Protected snapshot root | `D:\Users\fleur\Moirae Accord - Source Snapshots\ACCORD-00-20260913-215700` |

All ACCORD-00 artifact hashes remained unchanged. All eight protected snapshots
remained clean, at their recorded heads, with the expected source fetch URLs
and disabled `example.invalid` push URLs. No protected source repository,
hackathon ref, accepted tag, or snapshot was changed.

## External review provenance

The two reviewer outputs were located inside the Accord repository and copied
byte-for-byte to canonical preserved paths. The original input files were also
retained as provenance files. The review index is only an index and does not
duplicate or rewrite the review bodies.

| Phase | Original input | Preserved file | SHA-256 |
|---|---|---|---|
| Phase 1 | `docs/reviews/Phase 1 — Independent Adversarial Review.md` | `docs/reviews/ACCORD-01-EXTERNAL-REVIEW-PHASE1-VERBATIM.md` | `CD94372836C8A2CCCA8E0292AC84548B830B1C11E0176D0FAD13760EAF6E3FB6` |
| Phase 2 | `docs/reviews/ACCORD-01 External Review — Phase 2.md` | `docs/reviews/ACCORD-01-EXTERNAL-REVIEW-PHASE2-VERBATIM.md` | `05B5B47F3E572F41D6118581D6AE328270E28E327B8D6F5549928019082F9508` |

Both frozen phases returned primary verdict `PIVOT`.

## Independent verification result

The bounded current public-web check confirmed substantial prior art for
attenuating authorization, in-doubt uncertainty, durable execution, retries,
idempotency, receiver/provider receipts, proof-carrying actions, payment
mandates, and agent task protocols. It also confirmed that active drafts and
adjacent systems must not be described as a finished general solution. The
review’s central criticism was accepted, while claims that treated an active
Internet-Draft, A2A task-state semantics, or adjacent receipt work as exact
equivalents were qualified or rejected with evidence.

The principal sources are recorded in
`docs/reviews/ACCORD-01-PRIOR-ART-VERIFICATION.md`, including the current A2A
specification, the OAuth attenuating-agent-token Internet-Draft, the False
Success benchmark paper, Notarized Agents, Proof-Carrying Agent Actions, RAILS,
AP2, Temporal, Restate, DBOS, AWS durable-execution guidance, and primary
in-doubt transaction documentation.

## Final project decision

The binding verdict is `PIVOT`.

The Moirae Accord project continues only as a research/specification,
portable-record, verifier, and conformance/test-profile effort. The proposed
new Accord runtime is rejected. Ananke remains the authority and admission
owner; Horae remains the durable execution, reconciliation, and effect-state
owner; Adrasteia owns the portable linked record contracts; Mnemosyne remains
deferred; Fates Integration remains evidence/conformance only; A2A and MCP are
transport/conformance targets rather than the research foundation; Firecracker
remains deferred for stronger whole-process mediation claims.

The primary research question now concerns the measurable trade-off among false
confirmation, indeterminacy, duplicate effects, and human escalation across
effect surfaces and delegate honesty models, compared with durable execution
plus provider-state observation and a lightweight classifier. The secondary
question concerns whether monotonic grant attenuation bounds effective authority
under multi-hop and sibling composition. Both questions are explicitly
falsifiable and require an externally runnable verifier.

## Material pivot from the pre-review architecture

The pre-review appendix depicted a new Accord synthesis/control-plane runtime
above “The Fates.” The accepted post-review direction removes that runtime box.
Accord must not mint authority, become a second policy engine, become a second
effect-state store, or claim whole-process escalation prevention without
complete mediation. The portable record and verifier are design instruments
whose trust roots and limits must be explicit.

## No implementation

No runtime code, schemas, tests, A2A adapter, MCP adapter, Fates branch, source
change, package installation, provider call, Firecracker run, deployment, or
experiment harness was created by ACCORD-01C. ACCORD-02 was not started.

## No-mutation attestation

SOURCE_REPOSITORIES_MUTATED: NO
SOURCE_BRANCHES_CREATED: NO
SOURCE_TAGS_CREATED: NO
SOURCE_COMMITS_CREATED: NO
SOURCE_PUSHES_PERFORMED: NO
SOURCE_SNAPSHOTS_MUTATED: NO
HACKATHON_REFS_CHANGED: NO
ACCORD00_SEAL_MODIFIED: NO
ACCORD_RUNTIME_CODE_WRITTEN: NO
FATES_RUNTIME_CODE_WRITTEN: NO
ACCORD02_STARTED: NO
