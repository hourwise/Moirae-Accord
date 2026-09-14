# ACCORD-02R1 — Bounded Integrated-Review Remediation

Status: candidate remediation from ACCORD-02E `AMEND`. This document records
only the six bounded amendments requested by the integrated review and the
naturally related provider-operation-ID clarification. It is not ACCORD-02F,
does not replace any A/B/C/D model, and does not accept or promote ACCORD-02.

## 1. Starting point and scope

ACCORD-02R1 is based directly on the ACCORD-02E candidate. The ACCORD-02E
review artifacts remain unchanged and continue to record the pre-remediation
`AMEND` verdict. No prior candidate commit is rewritten.

The targeted findings are:

| Finding | Bounded repair |
| --- | --- |
| `E2E-BLOCK-001` | Split orchestration definitions, sanitized per-arm manifests, and scorer-only expectation/oracle material. |
| `E2E-MAJOR-001` | Add a normative machine-readable A/C settlement-vocabulary projection map. |
| `E2E-MAJOR-002` | Separate B grant relation, B effective-authority state, and event-time authority validity in D results. |
| `E2E-MAJOR-003` | Add typed lineage across experiment run, result, verifier, authority, settlement, and portable-bundle references. |
| `E2E-MAJOR-004` | Add a structured effect/predicate/stage/target/resource/recipient/provider binding descriptor to settlement-relevant paths. |
| `E2E-MAJOR-005` | Freeze machine-readable per-arm allowlists, forbidden fields, classifier inputs, and closed raw-output/manifest shapes. |
| `E2E-MINOR-001` | State that provider operation IDs are correlation references and may not merge effects or replace attempt IDs. |

`E2E-MINOR-002` remains a non-blocking note: A2A-shaped transport coverage is
optional for the first experiment because T1 plus T2 remains the minimum D
design. No new arm, provider, transport implementation, or empirical claim is
introduced here.

## 2. Information classes and oracle boundary

The D catalog is now a `SCENARIO_DEFINITION_ORCHESTRATION_ONLY` catalog. It
contains fixture references and assigned conditions needed to construct a case,
but it contains no `oracle_state`, expected conformance or settlement bounds,
or categorical-failure expectation. Scenario IDs are opaque with respect to
expected outcomes; the family prefix is a selection label, not a result label.

The separate `accord-02d-scorer-expectations.json` catalog is marked
`information_class=SCORER_ONLY`, `system_under_test_visible=false`, and
`protected_from_arm_inputs=true`. It has one expectation record per public
scenario ID. It contains the hidden factual oracle, expected authority/effect
bounds, and categorical-failure relevance. The score record schema stores a
typed reference to this material rather than copying it into a run-facing
result.

The run-facing `accord-02d-result-record.schema.json` no longer contains a
`scorer_only` object. It contains system-visible records only. The separate
`accord-02d-score-record.schema.json` carries expectation references, actual
oracle facts, normalized arm interpretation, metric contributions, exclusions,
reruns, and categorical-failure adjudication.

## 3. Per-arm manifests and allowlists

`accord-02d-arm-input-profiles.json` defines one closed field-level profile for
each arm. `accord-02d-arm-input-manifest.schema.json` marks a materialized
manifest as system-visible, forbids known oracle/expected-result field paths,
and requires a future harness to have checked it against the referenced
allowlist. The full scenario catalog is never directly consumable by an arm.

The intended information boundary is:

| Arm | Permitted information | Explicitly forbidden |
| --- | --- | --- |
| ARM-A | Durable task/attempt/executor state, assigned fixture metadata, delegate claims, and ordinary admission state. | Oracle, expected results, scorer fields, Accord settlement labels, privileged authority analysis, private Accord state. |
| ARM-B | ARM-A plus ordinary provider acceptance/state reads and reconciliation. | The same hidden/scorer/Accord outcome material. |
| ARM-C | ARM-B plus the frozen classifier feature subset. | Oracle, expected results, Accord evidence/settlement labels, projections, and scorer categories. |
| ARM-D | Portable records, declared authority/evidence/settlement profiles, trust roots, and supplied evidence allowed by the case. | Oracle, expected results, scorer adjudication, and any precomputed expected authority/effect answer. |

The raw arm output is a closed field-entry structure whose field paths are
checked against the relevant allowlist. Classifier output carries its input
profile reference and an explicit assertion that Accord outcome fields are
absent. The scorer normalizes arm-specific output after the run using a frozen
adapter profile; a baseline is never required to emit an Accord label.

## 4. A/C settlement vocabulary projection

`accord-02r1-settlement-vocabulary-map.json` is the named normative projection
profile. Its schema requires a native C result reference and declares the
conditions for each A-style kind:

- `VERIFIED` requires exact effect/predicate/stage binding, admissible and
  sufficient evidence, compatible profile, supported occurrence, and the
  required evidence class/observer/trust-root fields.
- `CORROBORATED` additionally requires profile-declared observer-distinct
  corroboration; it is not a universal evidence ranking.
- `NO_EFFECT_OBSERVED` is an observation projection with `as_of` and
  `read_semantics`. A separate rule permits bounded non-occurrence only when
  the native C result says `NON_OCCURRENCE_SUPPORTED` and the complete-negative
  profile requirements are satisfied. There is no unconditional absence map.
- `UNKNOWN_PENDING` represents unresolved, reopenable C results.
- `UNKNOWN_TERMINAL` is final only within the declared profile scope; it is not
  metaphysical finality and may be reopened where the profile permits later
  evidence.
- `REJECTED` represents inadmissible, invalid, or incompatible input. It is
  not evidence of non-occurrence.

The D result retains the native C multidimensional axes and the optional A
projection separately. No projection implies exactly-once occurrence,
universal external truth, later-stage completion, causal attribution unless
explicitly supported, or authority validity.

## 5. Authority axes

D’s `authority_result` now contains three independent structures:

1. `grant_relation` uses the actual ACCORD-02B relation vocabulary.
2. `effective_authority` uses the actual ACCORD-02B composition-state
   vocabulary.
3. `event_time_validity` records status independently at derivation, admission,
   dispatch, occurrence, and verification.

Consequently, a future result can carry `ATTENUATED` grant relation,
`POSSIBLE_WIDENING` effective composition, `INVALID_AUTHORITY` at dispatch,
and a supported factual occurrence without contradiction. `ATTENUATED` and
`CONTAINED` never mean `AUTHORIZED`.

## 6. Typed lineage

The D result’s `lineage` object uses typed references with record type, record
ID, schema ID, schema version, and optional digest. The chain is:

```text
EXPERIMENT_RUN
  -> EXPERIMENT_RESULT_RECORD
  -> VERIFIER_RUN -> VERIFIER_RESULT
  -> AUTHORITY_ANALYSIS_RESULT
  -> SETTLEMENT_RESULT
  -> PORTABLE_BUNDLE (when supplied)
```

Verifier and Accord references are nullable for baseline arms only; they are
not replaced with arbitrary baseline strings. Provider operation IDs and
transport IDs remain external correlation references and cannot substitute for
this lineage or for `effect_id`/`attempt_id`.

## 7. Predicate and stage binding

ACCORD-02A now exposes a structured optional `effect_binding` descriptor on
attempts, observations, and evidence artifacts. The descriptor carries the
logical effect, `predicate_id`, stage, action, and explicit binding slots for
target, resource, recipient/counterparty, provider, and external identifier.
Each slot is `BOUND`, `NOT_APPLICABLE`, or `UNKNOWN`.

The C target already identifies a predicate and stage; the C profile now also
recognizes `stage` as a binding name. The D run-facing result requires the same
descriptor for the task/effect identity, every attempt, and every observed
evidence record. A receipt for an earlier stage, a different resource,
recipient, predicate, effect, or attempt cannot strengthen the selected target.

Provider operation ID reuse remains a correlation diagnostic. It never merges
two logical effects and never converts one attempt’s evidence into another
attempt’s evidence.

## 8. Closure answers

These are schema/specification closure checks, not experimental results:

| Finding | Closure answer | Inspectable evidence |
| --- | --- | --- |
| `E2E-BLOCK-001` | **NO** — no system-under-test arm receives scorer-only oracle or expected-result material through the specified run manifest. | Sanitized catalog, scorer-only catalog/schema, arm profile, manifest schema, and closed D result schema. |
| `E2E-MAJOR-001` | **YES** — A projections and native C settlement semantics have an explicit normative map. | R1 mapping schema/instance and A/C cross-references. |
| `E2E-MAJOR-002` | **YES** — grant relation, effective composition, and event-time validity are separate machine-readable axes. | D result schema `authorityResult`. |
| `E2E-MAJOR-003` | **YES** — result lineage is typed. | D result schema `lineage`, typed references, and score-record references. |
| `E2E-MAJOR-004` | **YES** — settlement claims bind predicate/stage/target/resource/recipient and relevant attempt. | A `effect_binding`, C target/profile, and D `effectBinding`. |
| `E2E-MAJOR-005` | **YES** — arm inputs and classifier inputs are governed by explicit allowlists and forbidden fields. | Arm profile catalog/schema, manifest schema, raw-output schema, and D profile amendments. |

## 9. Boundaries retained

This remediation does not build a verifier, runtime, provider fixture,
reconciliation worker, experiment harness, classifier, adapter, or acceptance
seal. It does not run the experiment, alter the hypotheses or primary metric
formulas, make A2A mandatory, or claim that any research question has a positive
answer. A fresh integrated review remains required before an ACCORD-02
acceptance decision.
