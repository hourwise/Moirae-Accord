# ACCORD-02E4R5 per-rule semantic closure

Status: `CANDIDATE_UNACCEPTED`

## Pre-change diagnosis

The prior evaluator projected cached package-wide booleans across these multi-rule equivalence classes: `CANONICALIZATION_VALIDATE` (5), `IDENTITY_INVENTORY_VALIDATE` (5), `JSON_SCHEMA_VALIDATE` (4), `NEGATIVE_SCOPE_EVALUATE` (3), `PARTIAL_EFFECT_POLICY_VALIDATE` (4), `PREDICATE_REGISTRY_VALIDATE` (10), `PROFILE_DOMAIN_VALIDATE` (4), `PROPOSITION_VALIDATE` (2), `RFC8785_DIGEST_EQUALITY` (4), `SOURCE_REGISTRY_VALIDATE` (3), and `TYPED_REFERENCE_CLOSURE` (7). Single-rule classes were also package-global computations.

## Closed execution contract

Every executable rule now contains a normative `JSON_POINTER_COMPARE` check with four complete operands:

1. `subject`: an exact typed object reference;
2. `pointer`: an RFC 6901 JSON Pointer;
3. `comparison`: `EXACT_EQUAL`;
4. `expected`: a typed JSON value.

The procedure registry normatively defines exact-one subject resolution, RFC 6901 extraction, no value normalization, JSON type-and-value equality, missing and ambiguous behavior, result type, and failure codes. Evaluators derive a verdict solely from these operands. Neither evaluator has a package-global rule-result dictionary, semantic-name cache, or rule-ID expected-answer map.

## Divergence evidence

Both evaluator entry points independently produced the following results in temporary no-Git exports:

| Pair | Mutation | Dependent rule | Other rule |
|---|---|---|---|
| `PRED-001` / `PRED-002` | `/global_stage_order := MUTATED` | `PRED-001 = FAIL` | `PRED-002 = PASS` |
| `PRED-001` / `PRED-002` | `/implicit_transitivity := MUTATED` | `PRED-002 = FAIL` | `PRED-001 = PASS` |
| `E4R1-PART-001` / `E4R1-PART-002` | `/same_effect_required := false` | `E4R1-PART-001 = FAIL` | `E4R1-PART-002 = PASS` |
| `E4R1-PART-001` / `E4R1-PART-002` | `/direct_predecessor_required := false` | `E4R1-PART-002 = FAIL` | `E4R1-PART-001 = PASS` |

Swapped operands followed the operands rather than rule IDs. A consistently renamed rule retained its operand-derived result. A missing required comparison parameter produced `UNEVALUABLE` while an adjacent rule remained `PASS`.

## Trace contract

For each executable rule, both evaluators emit the rule ID, scope, procedure ID, canonicalized operands, resolved object ID, resolved repository path, JSON Pointer, extracted input value, result, and failure code. Deferred rules emit only their rule ID, deferred scope, missing subject roles, lifecycle stage, and deferred status.

## Final counts

- `TOTAL_DECLARED_RULES = 104`
- `EXECUTABLE_IN_PACKAGE_0_2 = 54`
- `DEFERRED_NO_SUBJECT_ARTIFACT = 50`
- `EXECUTED = 54`
- `PASS = 54`
- `FAIL = 0`
- `UNEVALUABLE_EXECUTABLE = 0`
- `AMBIGUOUS_EXECUTABLE = 0`

The independent evaluator imports neither the builder nor the primary evaluator. LF, CRLF, and exported no-Git representations produce identical results without writing to the source tree.
