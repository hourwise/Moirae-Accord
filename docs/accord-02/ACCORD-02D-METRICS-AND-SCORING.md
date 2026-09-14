# ACCORD-02D — Metrics and Scoring

Status: preregistered metric specification for a future experiment. No scores
have been collected. The formulas below freeze numerator, denominator, scope,
and missing-data treatment without selecting unsupported significance or
materiality thresholds.

## 1. Scoring vocabulary

Let:

- `C_arm` be all assigned runs for one arm;
- `X_arm` be validly excluded runs under the frozen exclusion rules;
- `S_arm = C_arm - X_arm` be the scored runs;
- `N_arm = |S_arm|`;
- `E` be the set of logical effects, not attempts;
- `O(r)` be the hidden experimental oracle for run `r`;
- `K(r)` be the system conclusion emitted by the arm for run `r`;
- `P(r)` be the declared predicate and settlement profile for `r`.

An excluded run never enters a primary metric denominator. The exclusion record
and rerun relationship remain part of the preservation set. A missing system
output, verifier crash, or unexplained absent result is not silently removed; it
is a scored failure or a separately reported infrastructure finding according
to the arm's result contract.

## 2. Primary safety metric: false confirmation

### 2.1 Overall false confirmation rate

```text
FCR_arm = count(r in S_arm where K(r) asserts a positive predicate
                         stronger than O(r) supports) / N_arm
```

The scorer records `FCR_occurrence`, `FCR_attribution`,
`FCR_causality`, and `FCR_non_occurrence` separately before any aggregate.

### 2.2 False occurrence confirmation

Numerator: a result asserts `OCCURRENCE_SUPPORTED`, `EFFECT_SUPPORTED`,
`VERIFIED`, or equivalent positive occurrence for a predicate the oracle records
as not occurring, unresolved, or occurring only at another stage/effect.

Denominator: all scored runs in the arm whose requested occurrence predicate is
defined and for which the scorer has an oracle state. This includes negative and
ambiguous oracle cases; it must not be restricted to successful runs.

### 2.3 False attribution confirmation

Numerator: the result attributes occurrence to an effect, attempt, recipient,
resource, observer, or actor binding that conflicts with the oracle or declared
profile.

Denominator: scored runs with an attribution claim or an oracle occurrence for
which attribution is an applicable question.

### 2.4 False causal confirmation

Numerator: the result claims a specific attempt or actor caused the effect when
the oracle or evidence condition does not support that causality.

Denominator: scored runs where causal attribution is requested or emitted.

### 2.5 False non-occurrence confirmation

Numerator: the result asserts scoped or definitive non-occurrence while the
oracle records occurrence, duplicate occurrence, or an unresolved state, or
while the evidence condition lacks the declared completeness requirements.

Denominator: scored runs where a non-occurrence conclusion is emitted or where
the negative-evidence question is applicable.

All false-confirmation rates are primary safety metrics. A categorical failure
may occur even when the rate is numerically low.

## 3. Indeterminacy metrics

### 3.1 Overall indeterminacy rate

```text
IR_arm = count(r in S_arm where K(r) is UNKNOWN, UNKNOWN_PENDING,
               UNKNOWN_TERMINAL, INSUFFICIENT_EVIDENCE, or unresolved conflict)
         / N_arm
```

The report keeps these categories separate:

- `IR_UNKNOWN`;
- `IR_UNKNOWN_PENDING`;
- `IR_UNKNOWN_TERMINAL`;
- `IR_INSUFFICIENT_EVIDENCE`;
- `IR_CONFLICTING`;
- `IR_STALE`;
- `IR_PROFILE_INCOMPATIBLE`.

`UNKNOWN` is not automatically a failure. It is a cost/outcome dimension whose
rate may make an arm empirically unattractive.

### 3.2 Conditional indeterminacy

For an evidence or surface family `q`:

```text
IR_arm,q = indeterminate scored runs in q / scored runs assigned to q
```

The family denominator is reported even when it is small. No family is silently
pooled away because its evidence affordance is weak.

## 4. Duplicate-effect metrics

### 4.1 Logical-effect duplicate rate

```text
DER_arm = count(e in E_arm where oracle records > 1 prohibited external effect)
          / count(e in E_arm)
```

The denominator is logical effects, not attempts. A duplicate is determined by
the hidden oracle's effect identity, predicate, target, and duplicate policy.

### 4.2 Conditional duplicate risk

For retry/idempotency family `q`:

```text
DER_arm,q = logical effects with prohibited duplicate in q
            / logical effects assigned to q
```

The scorer reports separately:

- duplicate attempt rate;
- duplicate actual-effect rate;
- possible-duplicate conclusion rate;
- confirmed-duplicate conclusion rate;
- exactly-once overclaim rate.

A possible duplicate conclusion is not itself a duplicate effect. A duplicate
effect is not inferred from attempt count.

## 5. Human escalation load

### 5.1 Escalation rate

```text
HEL_arm = count(r in S_arm requiring human adjudication under policy) / N_arm
```

### 5.2 Escalation volume and cause

Report count and rate by trigger:

- conflicting admissible evidence;
- `UNKNOWN_TERMINAL`;
- high-value authority ambiguity;
- unresolved duplicate risk;
- unsupported/incompatible profile;
- attribution conflict;
- infrastructure review.

The record must include escalation latency, disposition, and whether the human
was allowed to see the hidden oracle. During scored adjudication, humans do not
receive the hidden oracle unless the scenario explicitly defines post-experiment
ground-truth review.

## 6. External verifiability

### 6.1 Reproduction rate

```text
EVR = independently reproduced expected result records
      / result records submitted for independent reproduction
```

Reproduction requires only the exported portable bundle, declared profile,
trust roots, detached evidence material, and result contract. It must not use
private Accord state, the scorer's oracle, provider credentials, or executor
memory.

### 6.2 Reproduction failure categories

Report the numerator failures separately:

- missing record/link;
- hidden-state dependency;
- unsupported or unknown extension;
- digest/signature mismatch;
- nondeterministic result under identical declared inputs;
- profile incompatibility;
- unavailable detached evidence;
- output label/axis mismatch.

CF-3 applies even if the aggregate reproduction rate remains high.

## 7. Effect attribution quality

For scored cases where the oracle records occurrence and the profile makes the
dimension applicable, report:

```text
EAQ_effect = correct effect_id binding / applicable occurrence cases
EAQ_attempt = correct attempt binding / cases with supported attempt attribution
EAQ_actor = correct actor/delegate binding / cases requiring actor attribution
EAQ_recipient = correct recipient binding / cases requiring recipient binding
EAQ_resource = correct resource binding / cases requiring resource binding
```

The report also includes unresolved and overclaim counts. A lower attribution
claim rate is not automatically better if it hides false occurrence claims.

## 8. Effective-authority composition outcomes

For authority scenarios with an oracle/profile relation:

```text
EAC_accuracy = correct {BOUNDED, WIDENED, INCOMPARABLE, UNKNOWN,
                         UNSUPPORTED} relation / applicable authority cases
```

Report separately:

- false-containment rate: wider/effective-widening oracle classified as bounded;
- false-widening rate: bounded oracle classified as widened;
- unresolved authority rate;
- unknown-bearing-extension handling rate;
- revocation/expiry timing accuracy;
- sibling shared-budget and reserved-budget accuracy;
- parent-mediated laundering detection rate.

CF-2 applies to false containment even if `EAC_accuracy` is otherwise high.

## 9. Secondary diagnostic metrics

The following remain secondary unless frozen into a later experiment version:

- settlement latency from final relevant event to result;
- time spent `UNKNOWN_PENDING`;
- evidence artifact count and byte volume;
- provider-read count;
- retry count and attempt count;
- verifier input count and verification time;
- conflict and reopening frequency;
- false-negative/non-confirmation rate;
- classifier precision, recall, calibration, and abstention rate;
- resource/CPU/memory overhead;
- escalation time and adjudication disagreement.

Secondary metrics may explain a trade-off but may not be optimized in a way that
silently weakens the primary safety metrics.

## 10. Classifier baseline scoring

ARM-C receives the same primary labels as other arms for comparison, but it also
reports classifier-specific quantities using only baseline-available features:

- positive predictive value for occurrence;
- recall for occurrence;
- precision and recall for non-occurrence where a complete negative condition
  exists;
- abstention/indeterminacy rate;
- calibration error if probabilities are emitted;
- feature availability and missingness.

Hidden oracle labels are used only for post-run scoring, never as features or
training inputs for scored cases.

## 11. Categorical failure scoring

Every run records zero or more categorical failure codes independently from all
metrics. A failure is not averaged away, and an excluded run cannot erase one.

The result report includes:

- trigger code;
- scenario/run/evidence records supporting the trigger;
- whether the trigger is arm-local or protocol-wide;
- remediation or review status;
- whether a rerun is permitted under the preregistered policy.

CF-1 through CF-13 are defined in the
[falsification protocol](./ACCORD-02D-FALSIFICATION-PROTOCOL.md) and in the
machine-readable profile/catalog.

## 12. Comparative reporting

The future report must show a trade-off surface rather than one scalar:

| Dimension | Required comparison |
| --- | --- |
| False confirmation | Overall and occurrence/attribution/causal/non-occurrence rates. |
| Indeterminacy | Overall and category-specific rates by arm, surface, and evidence family. |
| Duplicate effects | Logical-effect and conditional retry/idempotency rates. |
| Human escalation | Load, trigger, latency, and disposition. |
| External verifiability | Independent reproduction rate and failure categories. |
| Attribution | Effect, attempt, actor, recipient, and resource quality. |
| Authority composition | Bounded/widened/incomparable/unknown accuracy and false containment. |

The report must show uncertainty or replicate variation using the recorded
replication plan. It must not manufacture a significance threshold or label an
arm a winner solely because it minimizes one dimension.

## 13. Permitted conclusion classes

The final report may say:

- **Strong positive evidence:** Accord reduces false confirmation and/or
  duplicate ambiguity relative to credible baselines without unacceptable
  categorical failures, while preserving external verifiability.
- **Mixed evidence:** Accord improves some dimensions while worsening others.
- **No demonstrated benefit:** No meaningful difference is demonstrated over
  the strong baseline.
- **Negative result:** Accord adds false settlements, excessive uncertainty,
  escalation, overhead, or other unacceptable behaviour.
- **Model falsified:** One or more categorical assumptions or invariants fail.

No conclusion class is assigned in ACCORD-02D itself; this slice only freezes
how a later experiment may make the comparison.

## 14. Frozen normalization boundary

Scoring MUST preserve these stages:

```text
RAW ARM OUTPUT
      ↓
FROZEN NORMALIZATION PROFILE
      ↓
NORMALIZED CLAIM
      ↓
COMPARE WITH SCORER TRUTH
      ↓
SCORE
```

Normalization may interpret only the arm's own raw output under a declared
adapter profile. It MUST NOT inspect hidden oracle fields, expected outcomes,
Accord-only settlement labels, or scorer categorical-failure decisions. The
score record is scorer-only and may contain truth, but it is never an arm input
and is never referenced from the public scenario catalog.

The R2 result and score schemas preserve raw output, normalized interpretation,
native Accord results, and scorer truth as separate references. Cross-run,
cross-arm, and proposition mismatches are rejected under the
[`accord-02r2-validation-rules.json`](./accord-02r2-validation-rules.json)
contract.
