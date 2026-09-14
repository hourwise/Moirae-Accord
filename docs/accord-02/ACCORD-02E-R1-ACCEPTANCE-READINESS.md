# ACCORD-02E-R1 — Acceptance Readiness

## Verdict

**AMEND**

`ACCORD-02 MUST NOT PROCEED TO ACCEPTANCE.`

## Criteria review

| Criterion | Result | Basis |
| --- | --- | --- |
| Original BLOCKING finding independently closed | **FAIL** | Public scorer reference and schema-valid nested-value/profile bypass remain. |
| All original MAJOR findings independently closed | **FAIL** | 02A/02C/02D projection, lineage, binding, and arm-boundary gaps remain partially closed. |
| No new BLOCKING finding | **FAIL** | `E2E-R1-BLOCK-001` records the direct public-to-scorer reference introduced by R1. |
| No unresolved MAJOR finding | **FAIL** | Four original MAJOR findings remain partial. |
| Native settlement and A projection unambiguous | **FAIL** | Normative map is clear, but A schema does not require it or a native C reference. |
| Authority axes remain separate | **PASS** | Relation, effective composition, and event-time validity are distinct. |
| Retry and attempt identity preserved | **PASS_WITH_EXTERNAL_CHECK** | Semantics are clear; ID namespace and foreign-reference checks remain external. |
| Predicate/stage binding prevents strengthening | **FAIL** | Binding is represented but duplicated-field equality is not schema-enforced. |
| External verification avoids private state | **PASS_WITH_INPUT_REQUIREMENT** | Portable verification is intended, but referenced records must be supplied and resolved. |
| Baselines remain credible | **PASS_IN_DECLARED_CAPABILITY** | ARM-B/C retain ordinary provider reads; enforcement of the allowlist is incomplete. |
| Metrics remain scoreable | **PASS_WITH_PROFILE** | Separate score record can hold required values; lineage/normalization checks remain future work. |
| Experiment can produce a negative result | **PASS** | Unknown, escalation, categorical failure, and baseline superiority remain possible. |
| No empirical result claimed | **PASS** | No experiment was executed and no benefit is claimed. |
| Runtime ownership boundaries unchanged | **PASS** | Review-only artifacts were added; no runtime or provider source changed. |

## Required bounded next remediation

This review does not perform these changes. A future remediation would need to
address at minimum:

1. Remove scorer-catalog references from arm-visible orchestration data.
2. Bind each materialized arm manifest to one selected profile and make field
   membership machine-checkable rather than an asserted boolean.
3. Close nested manifest/raw-output values or classify and schema-bind safe
   substructures.
4. Require the native C result and named mapping profile for A-style
   projections, or define a conditional schema/profile contract that makes
   the requirement enforceable.
5. Add supplied-record resolution/equality requirements for typed lineage.
6. Add cross-field effect/predicate/stage/target/resource/recipient/attempt
   consistency requirements, with profile-controlled NOT_APPLICABLE handling.

After those changes, another fresh integrated review is required. This review
does not accept, seal, tag, merge, or promote ACCORD-02.
