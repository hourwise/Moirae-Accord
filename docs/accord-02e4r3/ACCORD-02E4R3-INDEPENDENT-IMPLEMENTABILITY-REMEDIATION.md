# ACCORD-02E4R3 — Independent-Implementability Remediation

## A. Starting state

The branch was created directly from `3efed8ac234cf1a5acf34198b49022923fc8fad8`, tree `d70b70d2c09363eea092b588658cfc133555cecf`, parent `31231b01f2fa560dbec714c9ce72128754e18e4f`. `main`, `origin/main`, and `accord-02-accepted-v1^{}` remained at `5a8bf1e577f71132665ece271e70e30e87df5676`. ACCORD-03R2 remained at `99da6ad0b5d6f535843b4c240a837b2b9f861b12`.

## B–D. Four-assessor intake, reproductions, and adjudication

The exact four reports are preserved under `reviews/`; byte counts, original paths, and SHA-256 values are recorded in `accord-02e4r3-four-assessor-findings.json`. Findings were adjudicated by reproduction rather than voting. The package-lineage, path-base, incomplete reference model, permissive-schema, non-executable-rule, incomplete graph, canonicalization interpreter, binding, profile-role, negative-evidence, source-registry, and PARTIAL_EFFECT findings were confirmed or formalised. The claim that the existing V013 trace alone constituted an independent evidence contract was refuted: its proposition values were concrete, but its evidence-side type and contradiction derivation were absent.

## E. Design-freeze integrity

Exact predicate/stage authority, POSITIVE_STAGE, GENERIC_OCCURRENCE, NEGATIVE_SCOPE, explicit same-effect predecessors, no global stage order, non-entailment, accepted vocabulary, the complete-negative concept, and accepted outcomes remain unchanged. Direct parsed comparison reports 23/23 vectors, 13/13 expected axes, all reason codes, and 31/31 prohibitions unchanged.

## F–H. Lineage, digests, and paths

Candidate 0.2 now uses the accepted family ID `urn:moirae:accord-02r5:specification-package`. `on_acceptance.replaces` identifies version 0.1 exactly. Accepted-base and rejected-candidate provenance use raw-file-byte SHA-256; the current package uses RFC 8785-style canonical JSON with the self-digest field excluded. Every member path is repository-root-relative, with traversal, absolute paths, and repository-search fallback forbidden.

## I–K. Inventory and validation

The manifest declares `BASE + REPLACEMENTS + ADDITIONS - RETIREMENTS` derivation data and exact active members. Candidate-owned schemas are closed Draft 2020-12 schemas with required fields. Every active effective profile is validated; immutable inherited bytes are paired with candidate-owned strict validation-schema overlays instead of being skipped or rewritten.

## L–O. References, source vectors, and source registry

Reference objects carry an explicit kind and version and are discovered generically. Certification derives 234 non-null edges and resolves all 234 without normalization, fallback, latest/current substitution, or self-registration from a referencing declaration. All 23 source vectors use typed catalog/version/vector references. The source-schema registry is an active, schema-bound contract.

## P–Q. Canonicalization and digests

The target registry is the sole source of target semantics; mappings contain only `content_target_id`. The interpreter executes both INCLUDE and EXCLUDE pointer modes with explicit missing/duplicate policies. All 23 proposition digests and the catalog digest are recomputed from the registry.

## R–T. Operators, rules, and graph

The versioned operator registry defines operands, inputs, evaluation semantics, result type, and fail-closed behavior. All 104 active rules carry stable operator IDs and typed operands. The dependency graph is materialized solely from `rules[].depends_on`: 104 nodes and 127 dependency pairs, with exact node/edge equality, target resolution, and acyclicity checks.

## U–V. Bindings and evidence profiles

The verifier checks binding-set disjointness, capability-subset compatibility, N/A conflicts, provenance/identity separation, and unsupported capabilities. Settlement profiles control settlement decision policy; evidence profiles control admissibility and interpretation. Same-profile pairs are compatible; undeclared different pairs are incompatible; missing or unresolved references fail. V018 therefore deterministically produces `INCOMPATIBLE`.

## W–Y. NEGATIVE_SCOPE and V013

The complete-negative evidence contract types effect identity, tuple, scope, interval, retention, consistency, read semantics, observation/verification times, source class, and the evidence universe. Ten typed requirement operators execute actual comparisons and arithmetic. Contradictory positive evidence is derived from the admissible same-effect/predicate/stage evidence set and deduplicated by evidence ID; caller-supplied counts are forbidden. The accepted V013 booleans have an explicit mapping to candidate evidence fields and derived checks, yielding `NON_OCCURRENCE_SUPPORTED` without changing the accepted expected result.

## Z. PARTIAL_EFFECT

The policy states `target_already_supported: NOT_PARTIAL_EFFECT` and rejects unknown, unsupported, wrong-effect, self, cyclic, and dangling predecessor targets. Actual mutations cover an already-supported target and an unsupported predecessor.

## AA–AB. Independent evaluator comparison

A fresh standard-library-only evaluator was created and run outside the repository. It imported neither builder nor repository certifier. Both implementations returned PASS, the same empty material-failure set, 104 rules, 127 dependency pairs, 234/234 resolved references, and 23 vectors. See `accord-02e4r3-independent-comparison.json`.

## AC. Fresh falsification

The generic verifier detected 32/32 actual in-memory mutations across lineage, open policy, path models, typed references, INCLUDE/EXCLUDE canonicalization, pointers and target IDs, rule operators/operands/dependencies, binding authority, negative evidence, contradiction derivation, and PARTIAL_EFFECT. The report records observed failure codes; no mutation result is a mocked lambda.

## AD–AF. Expectations and usefulness

Direct reconstruction preserves all 23 expected objects and all 31 prohibitions. EFFECT_SUPPORTED, NON_OCCURRENCE_SUPPORTED, PARTIAL_EFFECT, generic occurrence, resource-created occurrence, and corroborated occurrence remain reachable; there is no all-UNKNOWN retreat.

## AG. Remaining minor/note findings

The catalog is schema-bound and self-identifying in the candidate package. Historical accepted and rejected artifacts remain immutable. The generated strict schemas deliberately describe the exact candidate instances and active effective profiles; widening future versions requires an explicit schema version change.

## AH–AI. Changed files and commit

All changes are additive under `docs/accord-02e4r3/`. Commit identifiers are recorded after the single required commit.

## AJ. Mutation attestation

```text
ACCORD02_ACCEPTED_0_1_MUTATED: NO
E1_MUTATED: NO
E2_MUTATED: NO
E3_MUTATED: NO
E4_MUTATED: NO
E4R1_MUTATED: NO
E4R2_MUTATED: NO
ACCORD03_MUTATED: NO
PACKAGE_0_2_ACCEPTED: NO
EXPERIMENT_IMPLEMENTED: NO
EXPERIMENT_EXECUTED: NO
MAIN_ADVANCED: NO
TAG_CREATED: NO
PUSH_PERFORMED: NO
```

## AK–AL. Verdict and next gate

`AMENDMENT_CANDIDATE_READY_FOR_FINAL_INDEPENDENT_REASSESSMENT`

The next gate is a fresh independent reassessment before any package-0.2 acceptance action.

ACCORD-02E4R3 COMPLETE — READY FOR FINAL INDEPENDENT REASSESSMENT BEFORE PACKAGE-0.2 ACCEPTANCE.
