# ACCORD-02C — Settlement Conformance Vectors

Status: offline candidate vectors. These cases are machine-readable fixtures,
not provider calls, runtime tests, or claims about external ground truth.

The companion fixture is
[accord-02c-settlement-test-vectors.json](./examples/accord-02c-settlement-test-vectors.json).
Every vector has a unique `vector_id`, a target `effect_id`, explicit
`attempt_id` values where relevant, a named settlement profile, portable record
references, and expected result axes. The fixture's `record_catalog` resolves
all `portable_record_ids`, `source_record_ids`, evidence references, and
conflict references used by the vectors.

## 1. Expected profile

The default fixture profile is
`urn:accord:02c:profile:conservative-v1`. It assumes:

- `effect_id` is stable across retries and `attempt_id` is unique per attempt;
- transport acknowledgement and provider acceptance settle only their own
  predicates;
- occurrence requires an effect/predicate binding and an admissible observation
  or receipt;
- causal attribution to a specific attempt requires a specific binding, not
  merely a matching external state;
- no completeness is assumed for silence, timeout, or an ordinary state read;
- a complete negative ledger may support scoped non-occurrence when its identity,
  time, consistency, retention, and completeness assumptions are satisfied;
- stale, corrupted, replayed, wrong-effect, wrong-attempt, and incompatible
  evidence cannot upgrade a settlement;
- conflicts remain visible unless an explicit profile precedence applies;
- results remain reopenable unless a finality boundary is explicitly justified.

## 2. Required vectors

| ID | Case | Expected bounded conclusion |
| --- | --- | --- |
| `ACCORD-02C-V001-DISPATCH-ONLY` | Local attempt/dispatch record only. | `occurrence=INSUFFICIENT_EVIDENCE`, `attribution=ATTRIBUTION_UNKNOWN`, overall `UNRESOLVED`. |
| `ACCORD-02C-V002-TRANSPORT-ACK-ONLY` | Transport accepted a request. | Acceptance is recorded; intended downstream effect remains `UNKNOWN`/unresolved. |
| `ACCORD-02C-V003-STRONG-BOUND-RECEIPT` | Signed provider effect receipt binds predicate, target, time, effect, and attempt. | `OCCURRENCE_SUPPORTED`, `ATTRIBUTED_TO_SPECIFIC_ATTEMPT`, `CAUSED_BY_ONE_OR_MORE_ATTEMPTS` or specific attempt per receipt, overall `EFFECT_SUPPORTED`. |
| `ACCORD-02C-V004-INDEPENDENT-CORROBORATION` | Provider receipt plus observer-distinct corroboration. | Occurrence supported; corroboration recorded with distinct observer/root assumptions. |
| `ACCORD-02C-V005-CONFLICTING-ADMISSIBLE-EVIDENCE` | Two admissible bound observations disagree. | `CONFLICTING_EVIDENCE`, conflict retained, no latest/majority shortcut. |
| `ACCORD-02C-V006-STALE-OBSERVATION` | Correct observation is outside freshness. | `STALE_EVIDENCE`/`UNKNOWN`, no current-state settlement. |
| `ACCORD-02C-V007-WRONG-EFFECT-IDENTITY` | Valid-looking receipt belongs to another `effect_id`. | Evidence excluded for the target; `INADMISSIBLE_EVIDENCE` or `INSUFFICIENT_EVIDENCE`. |
| `ACCORD-02C-V008-WRONG-ATTEMPT-BINDING` | Attempt-specific assertion names a different attempt. | No silent reassignment; attribution remains unresolved. |
| `ACCORD-02C-V009-REPLAYED-EVIDENCE` | A receipt from another logical effect is replayed for this target. | Replay/wrong-effect diagnostic; no settlement upgrade. |
| `ACCORD-02C-V010-RETRY-FAILURE-THEN-SUCCESS` | A1 fails before dispatch, A2 is uncertain, A3 has a bound success receipt. | One logical `effect_id`, three distinct attempts, occurrence supported. |
| `ACCORD-02C-V011-RETRY-POSSIBLE-DUPLICATE` | Lost acknowledgement followed by a retry with evidence of two possible external occurrences. | Occurrence supported plus `POSSIBLE_DUPLICATE`, not exactly-once. |
| `ACCORD-02C-V012-TIMEOUT-NO-EVIDENCE` | Timeout and silence only. | `UNKNOWN`/`INSUFFICIENT_EVIDENCE`; never `NON_OCCURRENCE_SUPPORTED`. |
| `ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE` | Complete trusted ledger covers matching scope and interval and finds no event. | Scoped `NON_OCCURRENCE_SUPPORTED`, with completeness assumptions visible. |
| `ACCORD-02C-V014-PARTIAL-STAGED-EFFECT` | Acceptance stage is evidenced; later recipient delivery stage is not. | Early stage supported; later stage unresolved; overall `PARTIAL_EFFECT`. |
| `ACCORD-02C-V015-INVALID-AUTHORITY-EFFECT-OCCURRED` | Authority is invalid/widened, but a bound external receipt supports occurrence. | `authority=INVALID_AUTHORITY` and `occurrence=OCCURRENCE_SUPPORTED`. |
| `ACCORD-02C-V016-REVOCATION-AFTER-DISPATCH-EFFECT` | Revocation occurs after historical dispatch/effect. | Historical effect retained; authority-at-dispatch and current validity are separate. |
| `ACCORD-02C-V017-OBSERVED-STATE-NO-CAUSAL-ATTRIBUTION` | Target state exists, but another actor could have created it. | `OCCURRENCE_SUPPORTED` or `EXTERNAL_STATE_ONLY` with `CAUSATION_UNKNOWN`. |
| `ACCORD-02C-V018-INCOMPATIBLE-PROFILES` | Evidence and requested settlement profiles have no declared common semantics. | `PROFILE_INCOMPATIBLE`/`UNKNOWN`; no fabricated common conclusion. |
| `ACCORD-02C-V019-CLOCK-AMBIGUITY` | Event and observation clocks cannot establish required order. | Relevant order/causality remains `UNKNOWN`; no invented sequence. |
| `ACCORD-02C-V020-UNKNOWN-SETTLEMENT-EXTENSION` | Unknown extension changes settlement-bearing semantics. | `UNSUPPORTED`/`UNKNOWN` with extension preserved in diagnostics. |
| `ACCORD-02C-V021-RECIPIENT-MISMATCH` | Provider acceptance names one recipient; delivery evidence names another. | Acceptance stage may stand; target delivery predicate is inadmissible/unresolved. |
| `ACCORD-02C-V022-PARTIAL-CORRUPTION` | One corroborating artifact has digest corruption; another remains valid. | Corrupt artifact excluded; result reflects the remaining evidence and diagnostic. |
| `ACCORD-02C-V023-REOPENED-BY-LATER-EVIDENCE` | Earlier provisional settlement is contradicted by later admissible evidence. | Result becomes `REOPENED`/`CONFLICTING_EVIDENCE`; prior result is retained. |

## 3. Cross-vector invariants

The vectors test these invariants in addition to their individual expectations:

1. Every `effect_id` is stable across all of its retry attempts.
2. Every `attempt_id` is unique, and retry count never creates logical effect
   multiplicity.
3. A dispatch record alone cannot settle occurrence.
4. Provider acceptance is not recipient delivery or downstream completion.
5. A wrong effect or attempt binding cannot be repaired by a transport ID,
   payload similarity, timestamp, or human label.
6. A valid authority analysis cannot upgrade weak factual evidence.
7. Invalid or unknown authority cannot erase a supported factual occurrence.
8. Timeout and silence do not support non-occurrence.
9. Complete negative evidence is scoped by its query, interval, completeness,
   freshness, and trust assumptions.
10. A partial stage never settles a later stage implicitly.
11. A state observation can support occurrence while leaving causal attribution
    unknown.
12. Conflicts, duplicate diagnostics, stale findings, and unsupported
    extensions remain machine-readable.
13. An incompatible profile produces no fabricated common interpretation.
14. Later evidence can reopen a prior result when the profile permits reopening.

## 4. Portable-record coverage

The fixture deliberately reuses the ACCORD-02A identities and records the
cross-system authority input separately:

`principal_id`, `grant_id`, `intent_id`, `task_id`, `delegation_id`, `effect_id`,
`attempt_id`, `observation_id`, and `evidence_id` are explicit. Authority
analysis is represented as a supplied 02B-shaped input with an independent
status; it is not recomputed by these vectors.

No vector contains a provider endpoint, credential, network URL, runtime
instruction, or hidden database reference. All assertions are offline fixture
claims under the named profile.

## 5. Falsification use

These vectors do not demonstrate that the conclusions are correct in the real
world. They make disagreements executable later: a future verifier can compare
its result axes, admissibility diagnostics, bindings, profile compatibility,
and reopening metadata with the expected fixture result without consulting
private Accord state.
