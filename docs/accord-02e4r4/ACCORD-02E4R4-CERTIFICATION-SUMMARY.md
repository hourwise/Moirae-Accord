# ACCORD-02E4R4 certification summary

Status: `0.2 CANDIDATE_UNACCEPTED`.

## Diagnosis and schema repair

Pinned `jsonschema==4.26.0` reproduced 221 E4R3 validation errors across 45 active effective instances, including 16 schema locations with duplicate `oneOf` branches and 1,965 single-value enums. E4R4 replaces instance-transcription schemas with reusable semantic domains, uses `const` only for frozen identities, and raw SHA-256 bindings for fixture integrity. A deterministic recursive check rejects structurally duplicate `oneOf` branches.

All 17 E4R4 active package artifacts and 32 active profiles validate with Draft 2020-12 plus format checking: 49 effective instances, zero errors. Equivalent complete-negative evidence with different identities, scope, stage, timestamps, consistency level, and evidence class is accepted by the domain schema.

## Identity and provenance

`provenance_only` means `MUST_NOT_SUPPLY_ACTIVE_NORMATIVE_CONTRACTS`. The four formerly active E4R2/R3 profile authorities are adopted into R4-owned paths and identities with source paths and source-byte hashes retained only as provenance. Predicate registry `registry_id` and `profile_id` resolve to one R4 object. No active package or profile path points into E4R2 or E4R3.

The accepted source vector catalog is not modified. A package-level external-member binding assigns ID/version to its exact repository-root path and raw SHA-256; the identity is explicitly not represented as a historical self-assertion.

## Executable semantics

The operator registry defines 11 bounded operators with closed typed operand schemas, named operand sources, machine check dispatch, boolean result types, failure codes, and fail-closed behavior. One hundred distinct assertion tokens resolve to structured `ALL` expressions over named executable checks. The primary certifier dispatches every rule through its declared operator implementation, validates operands, resolves its assertion, reads actual artifacts, and records the result.

Results: 104 active rules, 104 executed, 104 PASS, 0 FAIL, 0 unevaluable, 0 ambiguous. Derived and materialized graph sets agree at 104 nodes and 127 edges with no duplicates, dangling dependencies, or cycles.

## V013

The synthetic 0.2 fixture binds evidence effect, predicate, stage, and four-dimensional scope to the target, including deterministic `NOT_APPLICABLE` handling. The interval must cover the target interval. Retention must be at least both the interval duration and profile minimum. Freshness is non-negative age bounded by `freshness_max_age_seconds`. Contradictions are admissible positive artifacts matching the target—not the evidence record—on effect, predicate, stage, and scope, deduplicated by `evidence_id`.

## Vectors and preservation

Accepted 0.1 defines all 23 vectors as offline declarative fixtures for later verifier comparison, not as an implementation. E4R4 therefore classifies all 23 as `DECLARATIVE_EXPECTATION_VECTOR`; V013 additionally has an explicitly synthetic, candidate-owned executable evidence fixture. Expected objects are preserved exactly: 23/23 vectors, 13/13 common axes, all reason codes, and 31/31 prohibitions. No historical evidence is fabricated.

Canonicalization remains RFC8785/JCS with SHA-256 and the registered include/exclude pointer operators. All 24 stored digests reproduce. Schema-annotation discovery derives 77 current non-null references with zero unresolved references; no hard-coded reference-kind allowlist is used.

## Independent evaluation and falsification

The non-normative reference evaluator imports neither builder nor primary certifier nor a shared semantic helper. It independently loads normative artifacts, performs standards validation, implements V013 checks, executes declared operators, and agrees at 104 PASS / 0 FAIL / 0 unevaluable.

The fresh mutation battery passes every required class: real duplicate-`oneOf`; alternate valid evidence; invalid/missing fields; identity collision; unregistered identity; rejected-candidate reference; unknown operator; malformed/missing/extra/wrong operands; undefined assertion; rule/operator/dependency/graph mutations; all target/scope/retention/freshness/source/contradiction cases; source catalog digest/vector mutation; and canonicalization digest mutation.
