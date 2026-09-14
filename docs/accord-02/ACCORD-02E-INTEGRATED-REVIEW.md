# ACCORD-02E — Integrated Consistency, Adversarial Review & Acceptance Readiness

Status: review-only candidate. This document does not accept, promote, execute,
or amend ACCORD-02A, ACCORD-02B, ACCORD-02C, or ACCORD-02D.

## 1. Review scope and decision posture

This review treats ACCORD-02A/B/C/D as one proposed research specification. It
checks semantic compatibility, machine-readable linkage, adversarial behaviour,
experimental validity, and acceptance readiness. It does not treat passing an
offline vector as evidence that Accord improves a baseline.

The reviewed candidate commits are:

| Slice | Commit |
| --- | --- |
| ACCORD-01 baseline | `e748028d3ac05112163765afc65ef4224933f6a1` |
| ACCORD-02A | `2e2c036539dcc32f7411b5180e16ba46a7209d1a` |
| ACCORD-02B | `90c80c77ed0d312c7d5c4e72d7b92b55d4ed1e6f` |
| ACCORD-02C | `b94f3783c7bf3a65f7698c37ae89bef6e088a5ad` |
| ACCORD-02D | `9adf15d6005c72e5fbf49d2f3f7f62ca8f7e6354` |

## 2. Integrated verdict

**AMEND**

The research direction and architectural boundaries are coherent, but the stack
is not ready for a separate ACCORD-02 acceptance/seal task. One BLOCKING oracle
boundary defect and several MAJOR schema/translation ambiguities must be resolved
before an experiment harness or acceptance decision is authorized.

The required amendments are bounded and do not require a runtime architecture:

1. Split the public scenario-design catalog from the private expected-oracle and
   scoring material. A run-facing manifest must not expose `oracle_state`,
   expected truth, or expected conformance outcomes to any system under test.
2. Define a normative translation between the ACCORD-02A verifier labels and the
   ACCORD-02C/D multidimensional settlement labels.
3. Separate ACCORD-02B grant-relation/effective-authority analysis from an
   authority-validity decision used by ACCORD-02C/D.
4. Close verifier/result identity lineage across `result_id`,
   `verifier_run_id`, `result_record_id`, and experiment `run_id`.
5. Make predicate/stage and attempt binding explicit enough that an
   implementation cannot settle a later stage from an earlier-stage artifact by
   undocumented translation.
6. Freeze per-arm input manifests or allowlists so baseline and classifier
   inputs are auditable and cannot receive Accord-only labels or oracle-bearing
   metadata.

## 3. Finding summary

| Severity | Count |
| --- | ---: |
| BLOCKING | 1 |
| MAJOR | 5 |
| MINOR | 2 |
| NOTE | 2 |

| Disposition class | Count |
| --- | ---: |
| `SPEC_AMBIGUITY` | 6 |
| `EXPERIMENT_RISK` | 2 |
| `DOCUMENTATION_GAP` | 1 |
| `NON_ISSUE` | 2 |

The complete machine-readable findings are in
[accord-02e-review-findings.json](./accord-02e-review-findings.json).

## 4. What is coherent

The following integrated properties survived adversarial review:

- A logical `effect_id` remains distinct from per-dispatch `attempt_id`.
- Authority validity and factual occurrence are represented on separate axes.
- ACCORD-02B explicitly distinguishes grant attenuation from effective-authority
  containment.
- Shared-pool, reserved-suballocation, complementary-sibling, and
  parent-mediated cases are represented as profile-dependent rather than
  universally decidable.
- ACCORD-02C distinguishes provider acceptance, external occurrence, attribution,
  causality, staged effects, freshness, completeness, and duplicate risk.
- Ordinary silence, timeout, missing receipts, stale reads, and incomplete reads
  remain unresolved or insufficient rather than becoming non-occurrence.
- Later evidence can strengthen, weaken, supersede, contradict, or reopen a
  prior result under an explicit profile.
- Transport metadata is normatively denied authority and effect-settlement power.
- ACCORD-02D permits negative results, strong-baseline outperformance, and
  excessive `UNKNOWN` as an empirical cost.
- The baseline arms are conceptually credible and are not deliberately denied
  ordinary durable execution or provider-state observation.

## 5. Integrated identity findings

The identity meanings are mostly compatible:

| Identity | Integrated result |
| --- | --- |
| `principal_id` | Stable principal identity across A/B/C/D. |
| `grant_id` | Logical grant identity reused by authority analysis and effect linkage. |
| `intent_id` | Logical requested goal identity. |
| `task_id` | Logical task identity; retries do not create a new task. |
| `delegation_id` | Delegation-edge identity; task and authority delegation remain distinct kinds. |
| `effect_id` | Logical intended effect identity; stable across retries. |
| `attempt_id` | Per-dispatch identity; must be distinct for every retry. |
| `observation_id` | Observer-issued observation identity. |
| `evidence_id` | Evidence-artifact identity/version. |
| `verifier_run_id` | Verifier invocation identity in A and C. |
| `result_id` | Verification-result identity in A and C. |
| `provider_operation_id` | External/provider correlation identity, not an Accord semantic identity. |
| transport message/call ID | Transport correlation only. |
| experiment `scenario_id` | Design/scenario identity, not an effect or oracle identity. |
| experiment `run_id` | One experimental execution, distinct from a verifier invocation. |
| D `result_record_id` | Experimental result-record identity, currently not normatively linked to C `result_id` or A `verifier_run_id`. |

The last three result identities are the subject of finding
`E2E-MAJOR-003`. No transport identifier may substitute for any semantic
identity.

## 6. Authority/effect orthogonality result

The stack can represent the required combinations:

| Authority | Effect | Review result |
| --- | --- | --- |
| Valid | No effect | Representable. |
| Valid | Unknown effect | Representable. |
| Valid | Supported effect | Representable. |
| Invalid | Supported effect | Required and representable. |
| Unknown | Supported effect | Representable. |
| Invalid | No effect | Representable. |
| Revoked after dispatch | Later occurrence | Historical occurrence remains possible and supported. |
| Widened authority | Apparent successful effect | Separate authority and effect results remain possible. |

No normative path was found in the prose that turns invalid authority into
`NO_EFFECT`, or factual occurrence into valid authority. The machine-readable
authority-result translation remains ambiguous because ACCORD-02B returns a
relation/effective-authority analysis while ACCORD-02C/D also use validity labels
such as `AUTHORIZED` and `INVALID_AUTHORITY`. This is finding
`E2E-MAJOR-002`.

## 7. Authority composition result

The review confirms that ACCORD-02B can express:

- direct widening in action, resource, time, or another authoritative dimension;
- unknown authority-bearing extensions without silent attenuation;
- depth-2 monotonic delegation;
- shared-pool cases such as child caps of £80 + £80 against a £100 parent pool;
- explicit reserved allocations such as £40 + £60;
- complementary siblings that may form a wider workflow capability;
- parent-mediated action without silently assigning parent action to the child;
- revocation and expiry at derivation, admission, dispatch, occurrence, and
  verification times.

The remaining issue is not lack of conceptual coverage. It is that B's
`aggregate_relation` and `effective_authority.state` are merged by D into one
`relation_or_state` field, while C/D also use `authority.status` for validity.
That field can carry `ATTENUATED`, `CONTAINED`, or `AUTHORIZED` without a
machine-readable distinction between grant relation, effective-authority state,
and event-time authorization. This is an acceptance-blocking ambiguity, not a
claim that the B model itself is unsound.

## 8. Effect settlement result

ACCORD-02C remains conservative for:

- dispatch-only and transport-ACK-only cases;
- provider acceptance versus downstream completion;
- strong bound receipts;
- independent corroboration;
- conflicting admissible evidence;
- stale and late evidence;
- wrong effect, attempt, recipient, and resource bindings;
- complete negative queries versus incomplete empty reads;
- lost-response retries and duplicate external occurrences;
- partial and staged effects;
- invalid authority with supported occurrence.

The review did not construct a conforming C-profile path that turns ordinary
silence into definitive non-occurrence or a provider acceptance into recipient
acknowledgement. However, the A/C settlement labels are not normatively mapped,
and the A/D schema linkage does not require a predicate/stage-preserving result
translation. Those gaps are findings `E2E-MAJOR-001` and `E2E-MAJOR-004`.

## 9. Negative evidence

The C settlement profile is sufficient in concept to require:

- complete state-space coverage;
- identity, predicate, resource, recipient, and interval binding;
- retention and consistency declarations;
- freshness at verification;
- absence of contradictory evidence;
- explicit stale and partial-source outcomes.

The adversarial complete-negative case whose retention window excludes the target
interval remains unresolved rather than negative. No ordinary timeout, empty
eventually-consistent read, or failed local task is a valid negative conclusion.

## 10. Retry, duplicate, and staged-effect result

The logical/retry distinction is coherent:

- one `effect_id` may have A1, A2, and A3 attempts;
- every attempt has a distinct `attempt_id`;
- duplicate attempts do not imply duplicate effects;
- duplicate effects require evidence or the hidden experimental oracle;
- an idempotency key never proves exactly-once occurrence;
- provider operation IDs remain external references;
- staged predicates cannot be collapsed in the prose model.

The remaining schema-level risk is that A does not define a first-class logical
effect/predicate record, while D permits `attempt_ids` and event-time fields to
be optional in system-visible evidence. A conforming profile can reject or mark
such material unresolved, but the cross-slice translation is not explicit
enough for acceptance. This is included in `E2E-MAJOR-004`.

## 11. External verification

The intended contract is externally verifiable from a portable bundle, declared
profiles, trust roots, detached material, and evidence. A/B/C explicitly reject
hidden Accord-private state, and D's reproducibility schema requires
`private_state_used=false`.

The review found no required local database, executor memory, runtime cache,
provider session, or environment variable in the normative verifier inputs.
However, D's public scenario catalog contains expected oracle state and expected
conformance bounds. If that catalog is used as or referenced by a run-facing
manifest, it becomes hidden-oracle leakage or circular scoring. The separation
must be made structural before external-verification claims can be accepted.

## 12. Transport neutrality

The local, MCP-shaped, and A2A-shaped profiles remain carriage profiles only.
The reviewed prose correctly states that:

- tool names and method names are not authority;
- transport message IDs and sessions are correlation only;
- transport acceptance is not downstream effect occurrence;
- A2A task lifecycle state is not external-effect settlement;
- `TASK_STATE_UNSPECIFIED` remains indeterminate;
- A2A SEP #1404 is not used normatively.

The minimum experiment uses local and MCP-shaped transports. The A2A-shaped
profile is defined but not required in the first scored matrix, which is a
non-blocking scope choice.

## 13. Baseline and classifier result

ARM-A, ARM-B, and ARM-C are credible in principle:

- ARM-B is explicitly entitled to ordinary provider-state rereads and
  reconciliation.
- ARM-C may use ARM-B signals plus a simple reproducible classifier.
- No baseline is intentionally deprived of ordinary task, attempt, timing,
  provider, or retry signals.
- Accord's proposed advantage is identity binding, evidence semantics, trust-root
  declaration, settlement discipline, and external reproduction.

The risk is enforcement rather than stated intent. The machine-readable D result
schema leaves `baseline_or_system_output` open-ended, and the scenario catalog
contains oracle-bearing metadata. D does not define a sanitized per-arm input
manifest or field-level allowlist. A future harness could therefore violate the
declared fairness boundary without violating a JSON schema. This is finding
`E2E-MAJOR-005`.

## 14. Metrics and categorical failures

The D metrics have usable numerators and denominators for false confirmation,
indeterminacy, duplicate effects, escalation, external verifiability,
attribution, and authority composition. They explicitly avoid rewarding
universal `UNKNOWN` or unsafe overconfidence.

CF-1 through CF-13 are objectively scoreable in principle, with evidence,
scenario, run, and oracle references preserved. CF-3 and CF-9 overlap when a
verifier reads private oracle state; the distinction is still usable:

- CF-3 is a result-level private-state dependency;
- CF-9 is an information-flow leak into the system under test.

The overlap should be retained as dual coding rather than treated as a reason to
discard either failure.

## 15. Preregistration and conformance boundary

The D documents freeze hypotheses, arms, matrix families, metrics, categorical
failures, calibration/scored separation, exclusions, reruns, and replication
requirements. The design permits a negative result and does not claim any scored
outcome.

The stack also distinguishes:

- deterministic conformance: whether an implementation follows A/B/C semantics;
- empirical research: whether the approach changes the trade-off against credible
  baselines.

Conformance cannot establish a research benefit, and a negative comparison does
not by itself prove schema non-conformance.

## 16. Acceptance boundary

ACCORD-02 is **not ready** for a separate acceptance/seal task because the
BLOCKING oracle-boundary finding remains unresolved and the MAJOR translation
ambiguities violate the readiness criteria concerning schema compatibility,
identity coherence, and auditable information boundaries.

No amendment is performed here. ACCORD-02A/B/C/D remain exactly as reviewed.

The adversarial case details are in
[ACCORD-02E-ADVERSARIAL-CASES.md](./ACCORD-02E-ADVERSARIAL-CASES.md), the
claim classification is in [ACCORD-02E-CLAIM-AUDIT.md](./ACCORD-02E-CLAIM-AUDIT.md),
and the bounded amendment/readiness reasoning is in
[ACCORD-02E-ACCEPTANCE-READINESS.md](./ACCORD-02E-ACCEPTANCE-READINESS.md).
