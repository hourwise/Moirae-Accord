# ACCORD-02R2 — Normative Validation Contract

This contract defines deterministic checks that complement JSON Schema. It is
part of the ACCORD-02 specification and is not an executable validator.

The machine-readable rule registry is
[`accord-02r2-validation-rules.json`](./accord-02r2-validation-rules.json).
Each rule has a stable identifier, structured inputs and condition, failure
code, severity, and admission scopes.

## Enforcement layers

1. JSON Schema performs structural admission: closed objects, discriminated
   arm variants, typed source records, required fields, enum membership, and
   absence of arbitrary experiment-controlled values.
2. This contract performs deterministic cross-record validation: reference
   existence, identity equality, run membership, proposition membership,
   profile membership, and projection validity.
3. Content digests are checked when supplied. A digest binds supplied material
   to a content identity; it does not establish source trust or external truth.

The second layer is not an optional future harness reminder. A verifier,
experiment-run admission process, or scorer MUST report the named failure code
when its required rule cannot be satisfied.

## Rule families

| Family | Purpose | Representative rules |
| --- | --- | --- |
| `ORACLE_BOUNDARY` | Prevent public-to-scorer traversal and outcome encoding. | `ORC-001`–`ORC-003` |
| `ARM_ISOLATION` | Tie a manifest to one arm/profile, restrict typed sources, and classify any arm-visible portable extensions. | `ARM-001`–`ARM-007` |
| `RAW_OUTPUT` | Keep system output in an untrusted closed envelope. | `RAW-001`–`RAW-003` |
| `PROJECTION` | Prevent an A-style result from strengthening native C semantics. | `PROJ-001`–`PROJ-004` |
| `LINEAGE` | Resolve and bind typed records across a run. | `LIN-001`–`LIN-008` |
| `PROPOSITION` | Use one canonical proposition for settlement-relevant claims. | `PROP-001`–`PROP-005` |
| `SCORE_SEPARATION` | Freeze raw-output normalization before truth comparison. | `SCORE-001`–`SCORE-003` |

## Admission scopes

Rules declare one or more of:

- `structural admission`: the document cannot enter the relevant bundle unless
  its shape and discriminators are valid;
- `verifier admission`: the verifier cannot use the material to produce a
  stronger effect or authority conclusion;
- `experiment-run admission`: the assigned arm cannot start with an invalid or
  contaminated input manifest;
- `scoring admission`: the scorer cannot score a record whose lineage or
  normalization boundary is invalid.

Failure at an applicable scope is not repaired by a later result label. In
particular, `UNKNOWN` is preferable to a strengthened conclusion when a
required reference or proposition binding cannot be resolved.

## Typed identity rule

Textual equality across identifier types does not establish identity
equivalence. A `provider_operation_id` or transport call ID remains external
correlation data even when its characters happen to equal an `attempt_id`.
The value must resolve to the required typed record in the supplied bundle.

## Extension closure

An arm-visible portable record may retain an `extensions` member because the
portable-record model supports profile-governed extensions. That member is not
an unrestricted input channel. Under `ARM-007`, every extension is classified
as one of `NON_SEMANTIC_OPAQUE`, `PROFILE_DECLARED`, or `EVIDENCE_BEARING`.
`PROFILE_DECLARED` extensions must resolve to a namespace declared by the
active profile; `EVIDENCE_BEARING` extensions must be bound as supplied
evidence. Scorer expectations, oracle records, score records, expected
outcomes, and post-run adjudication are forbidden extension semantics. An
unclassified or forbidden extension causes admission failure and cannot be
repaired by an outcome label.

Source type to source-record-type compatibility is the explicit machine-readable
`pair_table` in `ARM-004`; the source schema identifier and version must also
be declared by the active profile. This prevents a permitted source label from
being paired with a foreign record or scorer-owned schema.

## Proposition rule

The canonical proposition schema is
[`accord-02r2-proposition.schema.json`](./schema/accord-02r2-proposition.schema.json).
It identifies an existing logical effect claim by effect, predicate, stage,
action, and applicable target/resource/recipient/provider bindings. It does
not assert occurrence, authority validity, or causality.

Settlement-relevant evidence, observations, native settlement results, A-style
projections, and D result records reference the proposition. Repeated summary
fields are either absent or must equal the resolved proposition under
`PROP-003`.

`UNKNOWN` cannot satisfy a positive binding requirement. `NOT_APPLICABLE` is
valid only when the proposition and active settlement profile declare the
dimension inapplicable.

## Projection rule

An A-style `VERIFIED`, `CORROBORATED`, `NO_EFFECT_OBSERVED`, `UNKNOWN_PENDING`,
or `UNKNOWN_TERMINAL` settlement projection requires:

- a typed native ACCORD-02C settlement-result reference;
- the named ACCORD-02R1 projection-map reference;
- the canonical proposition reference; and
- native C axes that satisfy the selected mapping rule.

`REJECTED` is a structural, evidence, or profile disposition. It does not
imply non-occurrence, no external history, or valid authority.

## Score pipeline

The scorer-only path is:

```text
RAW ARM OUTPUT
      ↓
FROZEN NORMALIZATION PROFILE
      ↓
NORMALIZED CLAIM
      ↓
COMPARE WITH SCORER TRUTH
      ↓
SCORE RECORD
```

The scorer expectation catalog is discovered through scorer configuration. It
is never referenced by the public scenario catalog, arm manifest, or any
system-under-test input. The public side may expose an opaque `scenario_id`
because it is needed for orchestration; only the scorer joins that ID to
expectation material.

## Non-goals

This contract does not execute validation, implement a verifier, create an
experiment harness, provide cryptographic trust, or establish external ground
truth. It makes the required decisions and failure conditions explicit so a
future implementation cannot replace them with undocumented local behavior.
