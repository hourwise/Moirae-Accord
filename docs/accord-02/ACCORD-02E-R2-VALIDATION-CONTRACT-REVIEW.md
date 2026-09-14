# ACCORD-02E-R2 — Validation Contract Review

## Standard

The R2 registry has 33 named rules. A rule ID is not itself evidence of
determinism. This review asks whether the declared inputs, profiles, records,
terms, and failure behavior are sufficient for two independent future
implementations to reach the same result without hidden Accord state.

The complete per-rule assessment is in
[`accord-02e-r2-validation-rule-review.json`](./accord-02e-r2-validation-rule-review.json).

## Classification summary

| Classification | Count | Interpretation |
| --- | ---: | --- |
| DETERMINISTIC | 9 | Structural or lexical rule can be evaluated from the named artifact. |
| DETERMINISTIC_WITH_PROFILE | 6 | Decision is reproducible once a named, supplied profile is available. |
| AMBIGUOUS | 7 | Terms or membership/equality semantics are not fully frozen. |
| UNEVALUABLE | 11 | A required record/profile collection is not defined as a supplied artifact. |
| CONTRADICTORY | 0 | No acceptance-critical direct rule cycle or contradictory enum was found. |
| NOT_APPLICABLE | 0 | All 33 registry rules are applicable to at least one declared boundary. |

There are 17 unresolved rules in the last two categories. This is why the
review verdict is AMEND even though the schema-level boundary has improved.

## Rule-family findings

### ORACLE_BOUNDARY

`ORC-001` is deterministic for explicit forbidden fields and references.
`ORC-002` is deterministic for the one-way scorer-to-scenario join.
`ORC-003` is deterministic only with the declared opaque-identifier policy;
the checked catalog values do not encode an expected outcome, but opacity is a
semantic property rather than a JSON Schema property.

The direct public reverse reference is gone. It is not safe, however, to treat
the absence of that field as closure of all possible semantic channels.

### ARM_ISOLATION

`ARM-001` and `ARM-002` are structurally strong: the manifest discriminator
selects one arm and its profile. `ARM-003` is profile-dependent but has a clear
source-type set.

`ARM-004` is ambiguous because it requires `schema_id` membership and version
matching, while the profile catalog contains no per-source schema map. The
manifest accepts non-empty arbitrary schema IDs and versions.

`ARM-005` is ambiguous for source projections and portable records. The
manifest itself is closed, but the projection field paths and source payload
semantics are not bound to a declared source schema/profile set.

`ARM-006` is ambiguous because `CLASSIFIER_FEATURE` is permitted without a
supplied feature profile or declared derived-feature registry.

`ARM-007` is unevaluable. The A portable base permits an arbitrary
`extensions` object; C has extension policies but no extension namespace,
classification, or active-profile lookup artifact. This is
`E2E-R2-BLOCK-001`.

### RAW_OUTPUT

`RAW-001` and `RAW-002` are deterministic schema checks. They successfully
separate an arm's untrusted output from the arm input boundary.
`RAW-003` is a clear prohibition, but its detection is a run-graph/process
property and therefore profile-dependent rather than a property of the raw
output object alone.

### PROJECTION

`PROJ-001`–`PROJ-004` are deterministic with the named R1 mapping profile and
supplied native C result. They correctly prevent standalone `VERIFIED`,
incomplete-negative projection, and history-rewriting interpretations.
Their evaluation still depends on reference resolution, which is covered by
the separate bundle finding rather than weakening the projection rule itself.

### LINEAGE

`LIN-001`–`LIN-006` are logically clear but unevaluable as a complete contract
because no validation-bundle schema or record inventory defines the collection
to search. `LIN-007` is additionally ambiguous: “current run/effect/proposition
scope” has no canonical scope record or equality operation. `LIN-008` is
deterministic and preserves semantic namespaces even when strings match.

This is `E2E-R2-BLOCK-002` and leaves the historical E2E-MAJOR-003 only
partially closed.

### PROPOSITION

`PROP-001` and `PROP-002` need the missing bundle and are therefore
unevaluable. `PROP-003` says duplicate summaries must match or be omitted, but
does not enumerate the duplicate field set or the canonical comparison
procedure. `PROP-004` protects UNKNOWN but cannot decide whether
`NOT_APPLICABLE` is legitimate because predicate-specific applicability is not
declared in the active profile. `PROP-005` is semantically appropriate but
requires the missing attempt/proposition record collection.

These issues comprise `E2E-R2-MAJOR-004`; the canonical proposition itself is
a genuine improvement and is retained as the right direction.

### SCORE_SEPARATION

`SCORE-001` is structurally deterministic: the score record is scorer-only.
`SCORE-002` is ambiguous and `SCORE-003` is unevaluable because
`NORMALIZATION_PROFILE` and the classifier feature profile are only arbitrary
typed references. The prose fixes an order but does not freeze the adapter
rules that give normalization a reproducible meaning. This is
`E2E-R2-MAJOR-002`.

## Validation-bundle audit

The reviewed stack names, but does not define, the following collections:

### Verifier bundle

The intended verifier inputs are the A portable-record bundle, canonical
proposition, active B/C profiles and results, trust roots, detached evidence,
observations, attempts, and the typed records needed by the selected A/C
projection. A bundle schema or explicit record inventory is absent. A
`PORTABLE_BUNDLE` schema is not equivalent to a complete cross-slice verifier
bundle.

### Experiment validation bundle

The intended experiment-side inputs additionally include experiment run,
result, verifier run/result, authority analysis result, settlement result,
arm-input manifest/profile, raw output, normalization profile, and their
lineage. No experiment-run or verifier-run schema exists, and no envelope says
which records are complete for an admission decision.

### Scorer-only material

The scorer expectation catalog, hidden oracle, normalized claim, metric
adjudication, and categorical-failure scoring belong only to the scorer. They
must not be required by the external verifier or any arm. The current score
schema expresses that role, but the missing bundle contract must not be filled
from scorer-only state.

## Evaluation order

The natural dependency order is structural validation, identity uniqueness,
typed resolution, proposition resolution, profile resolution, lineage/scope,
projection, arm isolation, then scoring. The R2 contract does not publish this
as a machine-readable dependency graph. A family-level review found no direct
cycle, but the missing bundle and profile artifacts mean that “resolved” and
“active” are not independently defined outputs. This remains part of
`E2E-R2-BLOCK-002`, not a claim that a harmful cycle was found.

## Failure-code audit

The registered rule failures are stable and conservatively named. One gap was
found: the R2 prose says supplied content digests are checked, but the rule
registry has no digest-equality rule or failure code. A modified proposition
with an optional mismatching digest is therefore not handled by a named
normative rule. This is `E2E-R2-MAJOR-005`.

## Conclusion

R2 successfully created the beginnings of a two-layer enforcement model, but
the cross-document layer remains incomplete as a portable contract. The next
repair must define supplied record collections and profile membership without
introducing runtime code. This review does not perform that repair.
