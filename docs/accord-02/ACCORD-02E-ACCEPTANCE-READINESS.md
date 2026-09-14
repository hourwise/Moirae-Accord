# ACCORD-02E — Acceptance Readiness

## 1. Readiness verdict

**AMEND**

ACCORD-02A/B/C/D is not ready for a separate ACCORD-02 acceptance or seal task.
The core direction is sound, but one oracle-boundary issue is BLOCKING and five
cross-slice issues are MAJOR.

## 2. Readiness criteria

| Criterion | Result | Reason |
| --- | --- | --- |
| No BLOCKING findings unresolved | **FAIL** | `E2E-BLOCK-001` leaves expected oracle state in the public design catalog without a required sanitized run manifest. |
| No schema incompatibility requiring undocumented translation | **FAIL** | A/C/D result labels, result identities, authority states, and predicate stages need explicit translation. |
| Identity semantics coherent across A–D | **PARTIAL** | Core linked-record IDs are coherent; verifier/result lineage remains ambiguous. |
| Authority and effect orthogonal | **PASS in prose; AMEND machine linkage** | Required combinations are representable, but B analysis versus C/D validity needs a typed boundary. |
| Retry/attempt identity preserved | **PASS in prose and core schemas** | A and C require distinct attempts; D preserves attempt records, with optional evidence attempt binding requiring tightening. |
| Unknown and uncertain cases expressible | **PASS** | A/C/D have unknown, stale, conflict, insufficient, profile-incompatible, and pending states. |
| Negative evidence conservative | **PASS** | Completeness, interval, identity, retention, freshness, and contradiction requirements exist. |
| External verification avoids hidden Accord state | **FAIL pending amendment** | The verifier contract says no private state, but the D catalog can expose expected truth if used as a run manifest. |
| Hidden oracle cannot leak by design | **FAIL** | D separates scorer material conceptually but does not structurally separate oracle-bearing catalog fields. |
| Baselines credible | **PASS in stated design; AMEND enforcement boundary** | ARM-A/B/C are fair in prose, but input allowlists are not machine-readable. |
| Metrics unambiguous | **PASS with profile translation note** | D formulas define numerators/denominators and do not reward universal UNKNOWN. |
| Categorical failures objectively testable | **PASS in principle** | CF-1 through CF-13 have observable triggers; CF-3/CF-9 overlap is codable. |
| Experiment can produce a negative result | **PASS** | D explicitly permits no demonstrated benefit, negative result, and model falsification. |
| No research result claimed in advance | **PASS** | A–D remain hypotheses/specifications only. |
| Runtime ownership unchanged | **PASS** | No runtime or control-plane responsibility is added. |

## 3. Required bounded amendments

These amendments are required before acceptance review; they are not performed in
ACCORD-02E:

### A. Oracle-safe scenario manifests

Create a public/run-facing manifest containing scenario identity, assigned
condition, arm-allowed inputs, and fixture parameters, but excluding:

- `oracle_state`;
- expected effect occurrence;
- expected duplicate count;
- expected conformance outcomes;
- categorical-failure predictions;
- any encoded result label.

Keep expected oracle and expected conformance material scorer-only and separately
addressed. Require scenario IDs and fixture IDs to be outcome-independent.

### B. Result-vocabulary map

Define a machine-readable, normative mapping for:

- A `VERIFIED`/`CORROBORATED`;
- A `NO_EFFECT_OBSERVED`;
- A `UNKNOWN_PENDING`/`UNKNOWN_TERMINAL`;
- C occurrence, attribution, causality, freshness, duplication, completeness,
  sufficiency, and overall conclusion;
- D settlement fields.

The mapping must preserve non-equivalence and must not create a universal success
label.

### C. Authority-axis map

Separate and type:

- B direct grant relation;
- B effective-authority composition state;
- event-time authority validity from Ananke or the declared authority input;
- C/D factual effect axes.

Do not use one overloaded `relation_or_state` field for all of these meanings.

### D. Identity lineage

Require explicit references among:

- experiment `run_id`;
- D `result_record_id`;
- verifier `verifier_run_id`;
- verifier `result_id`;
- C settlement `result_id`;
- A portable bundle and result references.

The references must be typed or schema-identified, not arbitrary strings only.

### E. Predicate and stage closure

Require every effect/evidence/attempt path that can affect settlement to carry or
reference:

- `effect_id`;
- `predicate_id`;
- stage identity where applicable;
- target/resource/recipient bindings;
- attempt binding or an explicit no-attempt declaration.

An earlier stage must never satisfy a later-stage predicate through an implicit
translation.

### F. Arm input allowlists

Freeze per-arm fields and artifacts visible to delegates, ARM-A/B/C, ARM-D, and
the scorer. In particular, baseline inputs must exclude Accord-only evidence
classes, settlement labels, expected bounds, and hidden oracle fields.

## 4. Acceptance decision boundary

ACCORD-02 may proceed to a separate acceptance/seal task only after the above
amendments are made, reviewed, and revalidated. This review does not authorize a
harness, acceptance tag, promotion, merge, or seal.

## 5. Review questions

1. Valid authority plus unknown effect: **Yes.**
2. Invalid authority plus observed effect: **Yes.**
3. Individually attenuated siblings with unsafe aggregate authority: **Yes.**
4. Provider acceptance without final effect occurrence: **Yes.**
5. Complete negative evidence distinct from silence: **Yes.**
6. One logical effect versus multiple attempts: **Yes.**
7. Duplicate attempts versus duplicate external effects: **Yes.**
8. Later evidence reopening earlier results: **Yes.**
9. Third-party verification without private Accord state: **Intended yes; currently blocked by the D catalog boundary.**
10. Transport metadata becoming authority: **No.**
11. A2A task completion automatically becoming settlement: **No.**
12. Negative result for Accord: **Yes.**
13. Strong baseline outperforming Accord: **Yes.**
14. Universal UNKNOWN as automatic victory: **No.**
15. Hidden oracle unavailable to verifier: **Intended yes; current catalog path is not sufficiently closed.**
16. Existing empirical result claims: **No.**
17. Runtime design rejected by ACCORD-01 required: **No.**
18. BLOCKING issues present: **Yes — `E2E-BLOCK-001`.**
