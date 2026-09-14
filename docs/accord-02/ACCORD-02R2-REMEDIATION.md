# ACCORD-02R2 — Machine-Enforceable Boundary, Lineage & Proposition Remediation

ACCORD-02R2 is a bounded remediation of the independent ACCORD-02E-R1
findings. It does not introduce a new authority or settlement model and does
not alter ACCORD-02B. The prior review and R1 evidence remain historical
artifacts.

## Target findings

R2 addresses:

- `E2E-BLOCK-001`
- `E2E-R1-BLOCK-001`
- `E2E-MAJOR-001`
- `E2E-MAJOR-003`
- `E2E-MAJOR-004`
- `E2E-MAJOR-005`

`E2E-MAJOR-002` remains closed and is not reopened. Optional A2A coverage
remains a non-blocking `E2E-MINOR-002` note.

The machine-readable closure record is
[`accord-02r2-remediation-evidence.json`](./accord-02r2-remediation-evidence.json).

## 1. One-way scorer boundary

The public scenario catalog no longer contains a scorer expectation locator.
The scorer expectation catalog retains its opaque `scenario_id` values, but
the join is one-way:

```text
SCORER CONFIGURATION
  ├── public run/result artifacts
  └── scorer-only expectation catalog
```

The scorer configuration is never an arm input, is not embedded in the public
catalog, and is not referenced from an arm manifest. A scenario condition such
as a lost response or lying delegate is orchestration/fixture configuration;
it is not an expected outcome.

## 2. Typed arm input boundary

`accord-02d-arm-input-manifest.schema.json` is now a discriminated `oneOf`
schema. Each manifest variant fixes both `arm_id` and the corresponding
`input_profile_id`. Manifest entries contain only:

- `source_type`;
- a typed `source_record_ref`;
- a declared projection/view;
- optional content digest on the source reference.

There is no arbitrary `field_name: value` transport for experiment-controlled
inputs. Scorer expectations, oracle records, score records, native settlement
results, projected verifier results, and private Accord state are not members
of any arm source variant.

The profile catalog now declares allowed and forbidden source types and is
structurally required to contain exactly one profile for each arm. The
previous self-attestation field `field_allowlist_checked` is no longer part of
the manifest schema. Admission is derived from the discriminated shape and
the normative `ARM-*` rules. Portable-record extensions remain profile-governed
data, not a bypass: `ARM-007` requires every arm-visible extension to be
classified as opaque, profile-declared, or evidence-bearing and forbids scorer,
oracle, expected-outcome, and post-run adjudication semantics.

## 3. Raw output and classifier separation

Raw baseline output is a closed envelope containing run/arm identity, output
type, payload schema, digest, capture time, and an explicitly untrusted
payload or payload reference. It is output, not a future arm input, and it is
never treated as scorer truth.

Classifier features are typed references under the declared classifier feature
profile. They may derive only from ARM-B-permitted information and may not carry
Accord settlement labels, verifier projections, authority answers, scorer
truth, or expected categorical failures.

## 4. Native C result and A projection

The A verifier-result schema now distinguishes effect-settlement projections
from rejection dispositions. Any claimed settlement projection requires:

- native C settlement-result reference;
- named R1 mapping-profile reference;
- canonical proposition reference;
- effect, predicate, and stage identity.

`REJECTED` may terminate before settlement analysis and therefore does not
require a native C result. It remains non-factual and does not imply
non-occurrence or invalid external history.

The native C result remains authoritative. A projection cannot add attribution,
causality, exactly-once semantics, authority validity, later-stage completion,
or universal truth.

## 5. Typed lineage

D result and score schemas now use discriminated typed-reference variants such
as `EXPERIMENT_RUN`, `VERIFIER_RESULT`, `SETTLEMENT_RESULT`,
`AUTHORITY_ANALYSIS_RESULT`, `ARM_INPUT_MANIFEST`, and
`EFFECT_PROPOSITION`. Variants carry type-specific ID fields rather than an
unconstrained universal `record_id`.

The normative validation contract supplies the cross-document rules that JSON
Schema cannot prove: exact reference resolution, no duplicate normative IDs,
same-run binding, scenario/arm agreement, proposition agreement, and rejection
of foreign results. Provider operation IDs and transport IDs remain external
correlation values.

## 6. Canonical proposition binding

[`accord-02r2-proposition.schema.json`](./schema/accord-02r2-proposition.schema.json)
defines one immutable binding descriptor for an existing logical effect claim.
It identifies effect, predicate, stage, action, and the applicable
target/resource/recipient/provider dimensions. It makes no factual or
normative conclusion.

Settlement-relevant observations, evidence, native C settlement results, A
projections, and D result records reference this proposition. Duplicate
summary fields are not authoritative and must either be omitted or match the
resolved proposition under `PROP-003`.

Attempt attribution remains separate. A result may support occurrence without
supporting a particular attempt. A specific-attempt claim requires a resolved
attempt record in the same proposition context and native C attribution
support.

## 7. UNKNOWN and NOT_APPLICABLE

`UNKNOWN` cannot satisfy a positive proposition-binding or projection
requirement. `NOT_APPLICABLE` is admitted only when the proposition and active
profile declare the dimension genuinely inapplicable; for example, recipient
may be inapplicable to a resource-creation proposition but not to recipient
delivery.

## 8. Closure position

The remediation evidence marks all six targeted findings `CLOSED` based on the
structural changes and named normative rules. This is a remediation claim, not
an acceptance decision. A fresh independent post-R2 integrated review is
required before ACCORD-02 can be considered for acceptance.

No runtime, verifier executable, validator executable, experiment harness,
classifier, provider fixture, or experiment was created or used.
