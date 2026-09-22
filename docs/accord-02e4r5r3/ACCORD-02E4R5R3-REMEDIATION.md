# ACCORD-02E4R5R3 remediation record

Candidate: `urn:moirae:accord-02r5:specification-package` version `0.2`,
status `CANDIDATE_UNACCEPTED`.  Additive tree: `docs/accord-02e4r5r3/`.
Parent revision on this branch: `44d0e72` (E4R5R2), working-tree base tree
`19dc935`.  Accepted tag `accord-02-accepted-v1^{}` = `5a8bf1e` and frozen
ACCORD-03R2 `99da6ad` are untouched.

## Claim surface

| Claim | Value |
| --- | --- |
| INTERNAL_PACKAGE_CONFORMANCE | PASS |
| TRUSTED_PACKAGE_IDENTITY (external anchor supplied) | PASS |
| TRUSTED_PACKAGE_IDENTITY (no external anchor) | FAIL / MISSING_EXTERNAL_TRUST_INPUT |
| TOTAL_RULES | 104 |
| CONFORMANCE_MEMBER_RULES | 42 |
| INDEPENDENT_BINDINGS | 16 |
| INTERNAL_DESIGN_INVARIANTS | 12 |
| DEFERRED_RULES | 50 |
| PACKAGE_INVARIANTS | 23 (all PASS) |
| GOVERNANCE_INVARIANTS | 16 (all PASS) |
| TRUST_INVARIANTS | 1 |
| V013_RESULT | NON_OCCURRENCE_SUPPORTED |

Candidate semantic identity (recomputed, package excluding self digest):
`b07d43d0ecbe75a5e23d090b3aceec976e030a3268272185e9809436075c421d`.
Registry semantic digest: `e5c13df5f933209ce9464d3755a7f220ccb5ff8a7c75f5a5ccc06342e753ef92`.
Registered objects: 42.  Derived reference edges: 256 (identical across the
primary evaluator, the independent evaluator and a third external scanner).

## A. Starting state
Branch `codex/accord-02e4r5r3-governance-trust-closure`, HEAD
`44d0e7240c97dcc12463b5611a7adf61399924d7`, tree
`19dc9356784d08d04945f8e2ce9b24bcd49e3683`, clean worktree, no tag/merge/rebase
performed.  All four protected refs verified before any write.

## B. Isolated worktree
All writes are confined to `docs/accord-02e4r5r3/`.  `git status --porcelain`
reports only `?? docs/accord-02e4r5r3/`.

## C. Reproduced defects
Both E4R5R2 evaluators baselined PASS at 104/42/16/12/50/21 while the following
defects were live: `MEMBERSHIP_RESOLVE` was a presence test; source binding
accepted a redirect to the accepted package with recomputed local digests;
`admissible` defaulted via `x.get('admissible', True)`; unknown integrity mode
failed in the primary but passed in the independent evaluator; `SELF` projection
was undefined; rule identity was count-only; `caller_supplied_contradiction_count`
was inert; catalog members and governance declarations were inert; projection
SELF undefined; the falsifier accepted unrelated failures and had no baseline.

## D. Trust boundary
Two layers are reported separately by both evaluators.  The candidate self
digest is always recomputed internally; the external anchor is supplied outside
the registry and is never read from the candidate.  An absent anchor is
`FAIL / MISSING_EXTERNAL_TRUST_INPUT` while internal conformance still reports
PASS (control `NO_EXTERNAL_TRUST_INPUT`).

## E. External contract
`external-verification-input.contract.json` declares `input_type`,
`registry_membership: FORBIDDEN_NOT_A_PACKAGE_OBJECT`,
`candidate_self_assertion: FORBIDDEN`, the four CLI inputs, the recomputation
rule, the trust-root kinds and the three-valued result vocabulary.

## F. Source binding
`MEMBERSHIP_RESOLVE` is replaced by procedure `SOURCE_CATALOG_BINDING_MATCH`
with typed arguments `candidate_binding`, `accepted_binding`, `object_registry`.
It mechanically checks registered identity, accepted path, registry path
resolution, candidate/accepted/recomputed semantic and raw digests, and the
declared canonicalization/integrity-class/algorithm against the explicit,
machine-readable field-vocabulary mapping.  `SRC-001`/`SRC-003` depend on it and
emit exactly `ACCORD-02R3-SOURCE-SCHEMA-NOT-PERMITTED` and
`ACCORD-02R3-SOURCE-FILENAME-NOT-AUTHORITY`.

## G. Membership
The old presence-only check no longer exists; membership is decided by full
path/identity/digest agreement (falsifier cases `WRONG_SOURCE_PATH`,
`WRONG_SOURCE_IDENTITY`, `WRONG_SOURCE_SEMANTIC_MAPPING`,
`CORRUPT_CANDIDATE_BINDING_DIGEST`, `NONEXISTENT_SOURCE_PATH`).

## H. Admissibility
Every `evidence_universe` item requires an explicit boolean `admissible` under a
closed `additionalProperties: false` schema covering `evidence_id`, `effect_id`,
`predicate_id`, `stage`, `scope`, `polarity`, `relationship`, `admissible`,
`observed_interval`, `consistency_level` and `source_class`.  Neither evaluator
uses a default; a missing key is a hard `FAIL` (`MISSING_ADMISSIBLE`).

## I. Modes
`integrity-modes.json` is a closed vocabulary: `SEMANTIC_JSON_CONTENT`,
`RAW_FILE_BYTES`, `PACKAGE_PINNED_BOOTSTRAP`, `SELF_DIGEST`,
`DUAL_ACCEPTED_SOURCE`, each declaring input, canonicalization, algorithm,
expected-digest source, verification operation, failure code and applicability.
`DIGEST_RECOMPUTE` dispatches solely from this artifact; an unknown mode fails
closed identically in both evaluators (`UNSUPPORTED_INTEGRITY_MODE`).

## J. Role closure
`PROFILE_REFERENCE_PINNING` now takes `inputs` + `authority`;
`CURRENT_PACKAGE_IDENTITY` now takes `registry` + `package` + `authority`.
`INVARIANT_PROCEDURE_ARITY_AGREEMENT` compares invariant required input roles,
procedure required arguments and every role root used anywhere in the
derivation, requiring A = B = C with no undeclared optional arguments.

## K. Governance
A package-only governance artifact declares sixteen bounded invariants:
FAIL_CLOSED_ENFORCED, SUBJECT_ROLE_COVERAGE, DEFAULT_ARGUMENT_COVERAGE,
DERIVATION_ROLE_CLOSURE, PROCEDURE_OPERATION_SUPPORTED,
MISSING_BEHAVIOR_SUPPORTED, AMBIGUITY_BEHAVIOR_SUPPORTED,
REFERENCE_DISCOVERY_SCOPE_VALID, REFERENCE_SHAPE_PREDICATE_APPLIED,
UNIQUENESS_KEY_APPLIED, ROLE_MODEL_APPLIED, SCHEMA_IDENTITY_MATCHES_REGISTRY,
RULE_COVERAGE_EXACT, INVARIANT_SET_EXACT, GOVERNING_AUTHORITY_REFERENCE_VALID
and GOVERNING_TOKEN_SINGLETON.  Every declaration is load-bearing and each has a
dedicated falsifier case.

## L. Fail closed
Every acceptance-critical invariant declares `fail_closed: true`; a false value
is rejected by `FAIL_CLOSED_ENFORCED` (`FAIL_CLOSED_FALSE`).

## M. Missing / ambiguity
`missing_behavior` and `ambiguity_behavior` use the closed vocabulary
`["FAIL_CLOSED"]` and drive explicit behaviour: resolution failure or ambiguity
produces an invariant FAIL (`MISSING_BEHAVIOR`, `AMBIGUITY_BEHAVIOR`).

## N. Subject roles
Every `subject_roles` entry must be a declared required input role, and every
semantic subject is declared by the role model (`SUBJECT_ROLES`).

## O. Defaults
Default arguments cover every required role, contain no undeclared role, match
kind and cardinality, and resolve to exactly one registered object
(`DEFAULT_ARGUMENTS`).

## P. Reference universe
`REFERENCE_DISCOVERY_SCOPE_VALID` requires the discovery object set to equal the
non-empty set of registry objects satisfying the declared scope
(`EMPTY_DISCOVERY_UNIVERSE`).

## Q. Shape
`additional_keys` behaviour is derived from the declared field; `ALLOW` both
changes the governed edge universe and violates the closed allowed value
(`WIDENED_SHAPE_PREDICATE`).

## R. Registry
Role model, uniqueness key, identity fields, status and classification
vocabularies are enforced (`ROLE_MODEL`, `WEAKENED_UNIQUENESS_KEY`).

## S. Schema identity
Each `schema_ref` must resolve to a registered schema whose `$id` equals the
deterministic registered schema identity (`SCHEMA_ID_MISMATCH`).

## T. Exact rules
The rule registry materialises the exact inherited 104-rule ID set with
provenance (`source_revision`, `source_commit`, `source_tree`,
`source_rule_registry_semantic_sha256`, `required_rule_ids`).  Actual IDs must
equal required IDs exactly; deleting `LIN-001` or adding/duplicating an
undeclared rule fails (`DELETED_RULE`, `EXTRA_RULE`).

## U. Governing tokens
`semantic-key-authority.json` declares exactly one authority path for each
semantic key (`global_stage_order`, `implicit_transitivity`,
`same_effect_required`, `direct_predecessor_required`, the negative-policy
fields, `additional_keys`, `uniqueness_key`, `role_model`), with declared
governed mirrors and permitted provenance/test-fixture roles.
`GOVERNING_TOKEN_SINGLETON` operates on this metadata and rejects duplicate
independent authorities (`DUPLICATE_GOVERNING_POLICY_DECLARATION`).

## V. Rewrite tests
A coherent rewrite that recomputes candidate-local digests keeps
INTERNAL_PACKAGE_CONFORMANCE PASS but fails TRUSTED_PACKAGE_IDENTITY against the
original external anchor; supplying a deliberately replaced root records
`DIFFERENT_PACKAGE_VERIFIED / OUT_OF_SCOPE_TRUST_ROOT_REPLACEMENT` instead of an
anti-tautology success.

## W. V013 relationship
`relationship` is drawn from a closed vocabulary; `relationship_basis.accepted`
entries are pointer bindings whose values are read from the actual accepted
V013 member, and `relationship_basis.candidate_supplied` entries must declare
`CANDIDATE_LOCAL_NOT_HISTORY`.  Accepted and candidate field sets must be
disjoint; a forged accepted value fails (`FORGED_V013_BASIS`).

## X. Map closure
The requirement map declares exact required IDs, uniqueness, an evaluation order
covering each requirement exactly once, and per-requirement `source_fields`,
`governing_authority`, `procedure` and `failure_code`.  Evaluation runs over the
full declared map in declared order.  Missing requirements, duplicate IDs and
order omissions fail (`MISSING_V013_REQUIREMENT`, `DUPLICATE_REQUIREMENT_ID`,
`EVALUATION_ORDER_OMISSION`).

## Y. Policy
Eight negative-policy fields are each bound to a computing requirement and
checked against them: `minimum_retention_seconds`, `freshness_max_age_seconds`,
`future_observation_result`, `stale_result`, `contradiction_rule`,
`allowed_consistency_levels`, `allowed_source_classes`,
`complete_read_requirement`.  `caller_supplied_contradiction_count` remains
FORBIDDEN.  Cases: `FUTURE_OBSERVATION_MUTATION`,
`CONTRADICTION_RULE_MUTATION`, `CONTRADICTION_COUNT_RELAXATION`.

## Z. Propositions
`SELF` projection is replaced by an explicit collection proposition, a
projection proposition referencing it, and one member proposition per accepted
vector.  Duplicate or missing required proposition IDs fail
(`DUPLICATE_PROPOSITION_ID`, `MISSING_PROPOSITION_ID`).

## AA. Reason oracle
Each negative case records the expected failing invariant/binding, the expected
allowed failure codes, the actual failing invariants and the actual emitted
codes.  A case PASSes only when both evaluators reject it, the intended
invariant/binding fails, and its emitted codes intersect the expected set.

## AB. Baseline
An exact-environment baseline for both evaluators runs before any mutation.  A
case whose baseline does not pass is reported `INVALID_TEST_ENVIRONMENT`
(observed: baseline PASS, so no case was invalidated).

## AC. Primary
`audit/certify_e4r5r3.py` reports INTERNAL_PACKAGE_CONFORMANCE PASS,
GOVERNANCE PASS, TRUSTED_PACKAGE_IDENTITY PASS and `overall_pass: true` with the
external anchor supplied.

## AD. Independent
`audit/independent_evaluate_e4r5r3.py` reimplements the pointer walker, dispatch
table, integrity dispatch and V013 engine; it independently reproduces every
reported surface.

## AE. Release
`audit/verify_release_e4r5r3.py` compares 17 exact surfaces (active object set,
schema result set, reference edges, governance map, package map, binding map,
member-rule map, internal map, class map, rule set, procedure-role closure, V013
requirement-map result, V013 result, expectation stability, trusted identity,
internal status, governance status): all true; `overall_pass: true`.

## AF. Exports
Clean export (no `.git`, no predecessor live trees): both evaluators PASS.
Windows-like CRLF checkout: PASS.  Linux-like LF pinned sources: preserved.

## AG. Delete-Python
With the builder and primary evaluator deleted, the independent evaluator still
derives 104/42/16/12/50, 23 package invariants, 16 governance invariants,
V013_RESULT `NON_OCCURRENCE_SUPPORTED` and TRUST PASS from the normative
artifacts, public standards and the external trust anchor alone.

## AH. Expectations
23/23 accepted vector IDs and 13/13 expected axes preserved; accepted
reason-code surface (29 distinct codes) and must-not-conclude surface (21
distinct codes) preserved exactly; zero accepted `expected` objects changed.

## AI. Positive usefulness
The build is positive-useful: the authentic package converges to PASS, every
adversarial mutation is rejected for its intended mechanism, and a legitimately
replaced trust root is recorded as out-of-scope rather than as a failure or a
self-asserted success.

## AJ. Counts
104 rules (42 executable conformance, 12 internal design, 50 deferred);
16 independent bindings; 40 active invariants (23 package, 16 governance,
1 trust); 42 registered objects; 256 reference edges; 23 vectors; 13 axes.

## AK. Changed files
Only `docs/accord-02e4r5r3/**` is added.  No E1–E4R5R2 file, no accepted
`docs/accord-02/**` file, no `.gitattributes` and no root file is modified.

## AL. Commit identity
BLOCKED.  Every technical gate passes, but the commit could not be created in
the worker sandbox: this directory is a linked worktree whose git directory is
`D:/Users/fleur/Moirae Accord/.git/worktrees/Moirae-Accord---E4R5R3-Sol`, outside
the worker's writable root.  `git add -A` fails with
`Unable to create '.../index.lock': Permission denied` (confirmed independently
by a direct file-creation probe against the same directory, which is denied).
The additive tree is therefore present but untracked; the supervisor must run
`git add -A && git commit -m "ACCORD-02E4R5R3: close governance semantics and trust-root boundary"`
on `codex/accord-02e4r5r3-governance-trust-closure`, or grant the worker write
access to the worktree git directory.  No tag/push/merge/rebase/stash was
performed, and `HEAD` remains `44d0e72`.

## AM. Mutation attestation

```
ACCORD02_ACCEPTED_0_1_MUTATED: NO
E1_MUTATED: NO
E2_MUTATED: NO
E3_MUTATED: NO
E4_MUTATED: NO
E4R1_MUTATED: NO
E4R2_MUTATED: NO
E4R3_MUTATED: NO
E4R4_MUTATED: NO
E4R5_MUTATED: NO
E4R5R1_MUTATED: NO
E4R5R2_MUTATED: NO
DEEPSEEK_DRAFT_WORKTREE_MUTATED: NO
ACCORD03_MUTATED: NO
PACKAGE_0_2_ACCEPTED: NO
EXPERIMENT_IMPLEMENTED: NO
EXPERIMENT_EXECUTED: NO
MAIN_ADVANCED: NO
TAG_CREATED: NO
PUSH_PERFORMED: NO
MERGE_PERFORMED: NO
REBASE_PERFORMED: NO
STASH_PERFORMED: NO
```

## AN. Verdict
`AMENDMENT_CANDIDATE_REMEDIATION_INCOMPLETE` — the single blocker is the commit
gate (AL): the worker sandbox cannot write the linked worktree's git directory,
so `git add`/`git commit` cannot run.  All semantic, trust, falsifier, release
and export gates PASS; the supervisor retains final acceptance authority and
must create the commit (or grant write access).

## AO. Next gate
Supervisor review of the diff, then acceptance or rejection of candidate 0.2.
