# ACCORD-02D — Falsification Protocol & Experimental Design

Status: candidate preregistration-style research specification. This slice
freezes the claims, arms, factors, outcomes, failure rules, and preservation
requirements for a future experiment. It does not implement or authorize an
experiment harness, execute scenarios, call providers, train a classifier, or
collect scored results.

## 1. Purpose and design freeze

ACCORD-02D converts the accepted ACCORD-01 research questions and the
ACCORD-02A/B/C semantic candidates into an experimental protocol that can be
implemented later without silently changing the research claim.

The protocol is a falsification instrument. It permits the conclusions:

- a strong positive result under named conditions;
- a mixed trade-off;
- no demonstrated benefit over the strong baseline;
- a negative result;
- model falsification by a categorical failure.

It does not presume that Accord improves any metric. In particular, a system
that declares everything `UNKNOWN` is not automatically superior, and a system
that minimizes indeterminacy by making false confirmations is not acceptable.

### 1.1 Fixed before the first scored run

The following are frozen by this slice:

- primary and secondary research questions and hypotheses;
- arms and anti-straw-man fairness requirements;
- topology minimums and process-boundary requirements;
- delegate behaviour classes;
- effect surfaces and transport profiles;
- fault and idempotency condition families;
- authority and evidence condition families;
- result labels, metric formulas, denominators, and categorical failures;
- hidden-oracle and information boundaries;
- inclusion, exclusion, rerun, replication, and calibration/scored rules;
- minimum scenario catalog coverage;
- required preservation records and content-addressing boundary;
- implementation-readiness gate.

### 1.2 Calibration permitted before scoring

Only details that do not alter the research claim may be calibrated and then
recorded in a versioned configuration before scored runs. Examples are exact
timeout values, synthetic latency distributions, harmless fixture quantities,
process counts, deterministic seed ranges, and classifier hyperparameters.
Calibration may not change hypotheses, arms, result labels, categorical
failures, metric formulas, scenario inclusion, or the visibility boundary after
scored results are inspected.

## 2. Bound research questions

### 2.1 Primary question

> For external effect surfaces with differing evidence affordances and
> delegates with differing reliability or honesty, what is the achievable
> trade-off among false confirmation, indeterminacy, duplicate effects, and
> human escalation, and can a portable, externally verifiable evidence record
> that binds authority to task/effect identity materially improve that trade-off
> over durable execution plus direct provider-state observation and a
> lightweight classifier baseline?

The wording is not strengthened. The protocol must be able to report: **No
measurable improvement was demonstrated.**

### 2.2 Secondary question

> Under multi-hop delegation and sibling composition, does grant-level monotonic
> attenuation bound effective authority when parent-mediated laundering,
> composition, expiry, revocation, and resource dimensions are varied?

The protocol must be able to show monotonic attenuation under some profiles,
failure under composition, indeterminacy, or insufficiency to bound effective
authority. A positive answer is not assumed.

## 3. Falsifiable hypotheses

### H-AUTH-1 — Direct attenuation

Under a declared comparison profile, a child grant satisfying every supported
component-wise attenuation rule will not be classified as directly wider than
its parent.

Falsification occurs when a demonstrably wider child resource, action, time,
delegation-depth, audience, or other supported authority dimension is classified
as `ATTENUATED`/contained, or when an unknown authority-bearing dimension is
silently ignored.

### H-AUTH-2 — Effective authority is not implied by grant attenuation

Individually attenuated grants are insufficient by themselves to guarantee
bounded effective authority under arbitrary composition. The experiment tests
shared-budget aggregation, complementary sibling capabilities, and
parent-mediated laundering.

This is a distinction to test, not a novelty claim.

### H-AUTH-3 — Bound composition profiles

When explicit composition and accounting constraints are supplied, the model
can distinguish bounded sibling composition from potentially widening or
unresolved composition. A failure to preserve `UNKNOWN`, `UNSUPPORTED`, or
possible widening where appropriate falsifies the hypothesis.

### H-EFFECT-1 — Delegate assertion resistance

A delegate-controlled success assertion alone must not produce evidence-backed
effect settlement requiring stronger evidence. A false qualified
`VERIFIED(...)` result from delegate-only evidence is categorical failure CF-1.

### H-EFFECT-2 — Evidence-affordance trade-off

Evidence surfaces with stronger identity binding, completeness, and observer
distinction should permit stronger settlements in appropriate conditions, while
weaker surfaces should produce greater indeterminacy rather than false
confidence. This is empirical and must not be assumed true.

### H-EFFECT-3 — Retry ambiguity

When the evidence surface cannot determine whether a lost response preceded an
effect occurrence, the result should preserve duplicate risk or `UNKNOWN`
semantics rather than infer exactly-once behaviour.

### H-EFFECT-4 — Negative evidence

Timeout, silence, missing receipt, or incomplete provider-state read must not
produce definitive non-occurrence without a profile-accepted completeness
assumption.

### H-LINK-1 — Authority/effect identity binding

Mismatched grant, effect, attempt, recipient, resource, or observer records must
not be accepted merely because each record is individually valid.

### H-EXT-1 — External verification

A verifier operating solely on the portable bundle, declared profile, trust
roots, and supplied evidence must reproduce the expected conformance conclusion
without hidden Accord-private state.

### H-BASELINE-1 — Comparative question

Accord may only be claimed to improve the trade-off if it outperforms or
materially changes one or more preregistered outcome dimensions compared with
the specified credible baseline without categorical failure. The report must
show empirical effect sizes and uncertainty rather than invent a numerical
materiality threshold in this slice.

## 4. Experimental arms

All arms receive matched logical tasks, effect surfaces, faults, timing
conditions, delegate behaviour, retry opportunities, and equivalent resource
limits. The arms differ only in the information and semantic machinery they
are entitled to use.

### ARM-A — Durable baseline

Durable execution with stable task identity, attempt tracking, retry behaviour,
and durable result storage. It does not receive Accord-specific portable
settlement semantics.

### ARM-B — Durable plus provider observation

ARM-A plus direct provider-state re-read or equivalent effect-surface
observation where available, with ordinary reconciliation. This is a strong
engineering baseline and must not be deliberately crippled.

### ARM-C — Durable plus observation plus lightweight classifier

ARM-B plus a deliberately simple deterministic classifier or heuristic using
only ordinary baseline information: durable task result, attempt count, error
type, provider acceptance, provider-state read, timing, and retry state. It may
not consume hidden oracle labels, Accord settlement labels, or privileged
authority/evidence labels unavailable to the baseline. Any learned classifier
requires isolated calibration and scored sets.

### ARM-D — Accord-profiled evidence verification

Durable execution plus the portable linked-record, authority-linkage, and
effect-evidence semantics in ACCORD-02A/B/C. It uses the same external-effect
scenario as the other arms and is scored on both factual and normative axes.

Accord's advantage, if any, must arise from explicit identity binding,
evidence semantics, trust-root declaration, settlement discipline, and
externally reproducible verification—not from withholding ordinary engineering
controls from ARM-A/B/C.

## 5. Anti-straw-man and information fairness rules

The implementation protocol must document for every arm:

- logical task and effect identity available;
- provider observations available;
- authority information available;
- delegate claims available;
- retry opportunities and fault visibility;
- process/resource limits;
- information intentionally unavailable because it belongs to another arm;
- any arm-specific output that cannot be compared directly.

ARM-B receives ordinary provider-state observation wherever the effect surface
offers it. ARM-C receives that same observation before classification. ARM-D
does not receive the hidden oracle; it receives only declared portable records,
profiles, trust roots, and supplied evidence. The experimental scorer is not the
portable verifier.

## 6. Categorical falsification rules

The following failures are frozen and override aggregate performance:

| ID | Categorical failure trigger |
| --- | --- |
| `CF-1` | A qualified `VERIFIED(...)`/equivalent positive settlement contradicts the experimental oracle for the declared predicate/profile. |
| `CF-2` | A demonstrably wider authority grant is classified as safely attenuated or contained. |
| `CF-3` | External verification requires hidden Accord-private state not in the declared verifier inputs. |
| `CF-4` | MCP, A2A, local, or other transport metadata creates or widens authority. |
| `CF-5` | Distinct retries cannot be distinguished because `attempt_id` was lost or reused. |
| `CF-6` | The system claims prevention of effects through paths it does not mediate. |
| `CF-7` | Timeout, silence, or incomplete read becomes definitive non-occurrence without complete negative evidence. |
| `CF-8` | Invalid authority is treated as proof of no effect, or occurrence creates valid authority retroactively. |
| `CF-9` | The system under test receives hidden truth-oracle information outside the declared condition. |
| `CF-10` | A baseline is materially denied ordinary provider observation or durable execution that its arm definition requires. |
| `CF-11` | Scored results are silently excluded, replaced, or retuned after their outcome is known. |
| `CF-12` | A result collapses a partial/staged predicate into later-stage success without later-stage evidence. |
| `CF-13` | A wrong effect, attempt, recipient, resource, or observer binding is accepted as the target claim. |

## 7. Truth oracle and information boundary

The experiment requires a synthetic ground-truth oracle for scoring. The oracle
records factual events such as occurrence, non-occurrence, duplicate count,
recipient, resource, and actual attempt sequence. It is not part of the system
under test and must be stored separately from verifier-visible artifacts.

| Component | Hidden oracle | Authority bundle | Provider observations | Delegate claims | Accord evidence |
| --- | --- | --- | --- | --- | --- |
| Delegate | NO | Assigned subset only | Assigned subset only | Own claims | Assigned subset only |
| ARM-A/B/C baseline | NO | Ordinary authority state only where normally available | According to arm | YES | NO Accord-only labels |
| ARM-D verifier | NO | YES | Only supplied evidence | YES | YES |
| Experimental scorer | YES | YES | YES | YES | YES |

The scorer may use the hidden oracle during post-run adjudication. No arm may
read it during a scored run. A result that reproduces a conclusion only by
reading the oracle is CF-3/CF-9, not external verification.

## 8. Fixed experimental coverage

The planned catalog requires:

- depth-2 delegation `P0 → P1 → P2`;
- at least two sibling delegates under `P0`;
- a parent with two child branches where composition is relevant;
- real local process boundaries between at least some delegate, executor/
  mediator, provider fixture, observer, and verifier components;
- two effect surfaces with materially different evidence affordances;
- at least two transport profiles, including a local/native fixture and an
  MCP-shaped or A2A-shaped envelope;
- honest, lying, partially lying, and faulty/non-malicious delegates;
- all required fault families, authority families, evidence families, and
  idempotency conditions in the catalog;
- deterministic adversarial cases plus seeded replicated timing/fault cases.

Local multi-process execution is sufficient. Cloud deployment and live
providers are not required for the first harness.

## 9. Scenario selection strategy

The future harness must not execute a meaningless full Cartesian product.
Selection is frozen as three families:

1. **Core matrix:** a bounded full-factor subset covering arm, surface,
   transport, delegate reliability, authority validity, evidence strength,
   retry/idempotency, and representative faults.
2. **Targeted adversarial cases:** lying delegates, laundering, duplicate
   effects, conflicting evidence, idempotency expiry, revocation, and sibling
   composition.
3. **Boundary cases:** expiry, idempotency-window, freshness, timeout, and
   retry boundaries.

The machine-readable scenario catalog records the family, rationale, expected
oracle state, expected conformance bounds, primary metrics, and relevant
categorical failures. It is a design catalog, not an executable manifest.

## 10. Result and preservation obligations

Each future scored run must preserve content-addressed or immutable records for:

- experiment, fixture, code, and configuration versions;
- seed, scenario, arm, topology, transport, surface, delegate behaviour, and
  fault injection;
- authority bundle/profile and effect/task identities;
- attempt records, injected-fault record, provider/effect-surface events,
  observations, evidence artifacts, and verifier output;
- baseline and classifier output;
- hidden scoring-oracle record, stored separately;
- final scoring, exclusions, rerun status, escalation, and categorical failure.

The future result schema distinguishes system-visible evidence from the hidden
oracle and scorer-only material. A scored case must be reconstructable without
making the portable verifier depend on private state.

## 11. Exclusions, reruns, and replication

Valid exclusions are limited to a corrupt fixture that cannot execute, a proven
harness defect that prevents the assigned condition, oracle corruption, or
machine failure before scenario start. A case is not excluded because Accord
performs badly, a baseline performs well, the result is `UNKNOWN`, a delegate
fooled the verifier, or a duplicate occurred.

Every exclusion carries a reason code, evidence, responsible stage, and rerun
eligibility. Reruns distinguish a scenario that never started, a harness
failure, a planned replicate, and a post-outcome repeat. The last category
cannot silently replace the original scored record.

Deterministic adversarial vectors receive at least one exact execution. Stochastic
timing/fault conditions receive multiple seeded replicates selected before
scoring or justified by a recorded calibration plan. Matched arms reuse seeds
and conditions where meaningful. If sample size requires pilot variance
estimates, that fact is declared rather than replaced by an invented threshold.

## 12. Implementation-readiness gate

No harness is authorized by this slice. Before implementation begins, all of
the following must be true:

1. ACCORD-02A/B/C/D are reviewed together.
2. Identity and schema compatibility is checked without modifying frozen files.
3. Arms and anti-straw-man controls are frozen.
4. Hidden-oracle and information boundaries are frozen.
5. Scenario catalog is frozen and versioned.
6. Metric formulas and categorical failures are frozen.
7. Calibration/scored separation is frozen.
8. The initial harness has no live-provider requirement.
9. Runtime ownership boundaries remain unchanged.
10. No implementation, provider fixture, classifier training, benchmark, or
    scored run begins as part of this candidate.

## 13. Compatibility with ACCORD-02A/B/C

The protocol layers over the prior candidates without editing them.

### ACCORD-02A

The existing identities are sufficient for principals, grants, intents, tasks,
delegations, effects, attempts, observations, evidence, and verifier results.
`effect_id` remains the logical effect identity and `attempt_id` remains the
per-dispatch identity.

### ACCORD-02B

The existing authority relations express attenuation, widening, incomparable,
unsupported, unknown, sibling/effective-authority analysis, revocation, expiry,
and quantitative composition. The authority sub-experiment treats those as
inputs and scored conclusions, not as an authority engine.

### ACCORD-02C

The existing settlement model expresses occurrence, non-occurrence, conflict,
uncertainty, stale/inadmissible evidence, attribution, causality, reopening,
and duplicate-risk distinctions. The effect sub-experiment and result record
preserve those axes independently from authority.

No genuine compatibility blocker was found. ACCORD-02A/B/C files remain
unchanged.

## 14. Prohibited claims and non-goals

This protocol does not claim:

- exactly-once external effects;
- universal effect truth or perfect authority containment;
- universal decidability of authority predicates;
- complete prevention without complete mediation;
- that A2A provides effect settlement or MCP metadata supplies authority;
- that Accord replaces Ananke or Horae;
- that a provider receipt proves arbitrary goal satisfaction;
- that observation proves causality without adequate binding;
- any positive research result before experiments occur.

This slice does not build a harness, runtime, verifier executable, provider
fixture, process, distributed execution, classifier, benchmark, or scored
result. It installs no dependency and makes no external call.

## 15. Pre-commit review answers

1. Can the protocol produce a negative result for Accord? **Yes.**
2. Can the strong baseline outperform Accord? **Yes.**
3. Does the verifier receive the hidden oracle? **No.**
4. Are durable execution and provider re-read credible prior engineering rather
   than straw-man baselines? **Yes.**
5. Can lying delegates produce testable false-success conditions? **Yes.**
6. Can valid authority coexist with unknown effect settlement? **Yes.**
7. Can invalid authority coexist with proven effect occurrence? **Yes.**
8. Can individual attenuation coexist with widened effective authority? **Yes.**
9. Does timeout imply non-occurrence? **No.**
10. Does one idempotency key prove exactly-once effect? **No.**
11. Is every `UNKNOWN` an experiment failure? **No.**
12. Can excessive `UNKNOWN` make Accord empirically unattractive? **Yes.**
13. Does external verification require hidden Accord state? **No.**
14. Are categorical failures preserved despite favourable aggregate metrics? **Yes.**
15. Has any scored experiment been executed? **No.**

The companion files provide the detailed design, formulas, matrix, profile
schema, scenario catalog, and future-run result schema:

- [ACCORD-02D-EXPERIMENT-DESIGN.md](./ACCORD-02D-EXPERIMENT-DESIGN.md)
- [ACCORD-02D-METRICS-AND-SCORING.md](./ACCORD-02D-METRICS-AND-SCORING.md)
- [ACCORD-02D-EXPERIMENT-MATRIX.md](./ACCORD-02D-EXPERIMENT-MATRIX.md)
- [accord-02d-experiment-profile.schema.json](./schema/accord-02d-experiment-profile.schema.json)
- [accord-02d-scenario-catalog.json](./examples/accord-02d-scenario-catalog.json)
- [accord-02d-result-record.schema.json](./schema/accord-02d-result-record.schema.json)
