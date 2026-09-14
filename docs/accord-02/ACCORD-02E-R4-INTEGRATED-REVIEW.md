# ACCORD-02E-R4 — Acceptance-Readiness Closure Review

## A. Starting state

Repository: `D:\Users\fleur\Moirae Accord`
Review branch: `codex/accord-02e-r4-acceptance-readiness-review`
Starting branch: `codex/accord-02r4-self-contained-profile-schema-closure`
Starting HEAD: `f027ba7ad39c1952414263ee18f2118db2364be7`
Starting tree: `d6b8cb0aaafc94cf7dda0860c0c6d534a020acd6`
Starting parent: `40424f36037d803820c10119677ee23701f39684`
Starting worktree: clean.

Protected refs were verified before branching:

- `main` = `e748028d3ac05112163765afc65ef4224933f6a1`.
- `origin/main` = `e748028d3ac05112163765afc65ef4224933f6a1`.
- `accord-01-accepted-v1` = `e748028d3ac05112163765afc65ef4224933f6a1`.
- `accord-00-accepted-v1` = `ddad3092b8b1d1d4ac5ab496143263ddd6afc587`.
- No `accord-02-accepted-v1` tag exists.

The candidate ancestry is intact:

`ACCORD-01 → 02A → 02B → 02C → 02D → 02E → 02R1 → 02E-R1 → 02R2 → 02E-R2 → 02R3 → 02E-R3 → 02R4`.

The historical reviews, prior remediation evidence, protected ACCORD-00/01 artifacts, and eight protected source snapshots were not modified.

## B. Integrated verdict

**AMEND**

R4 materially improves self-contained contract resolution, but three acceptance-critical defects remain: the active package/profile inventory is incomplete, the source-schema registry names schemas absent from the package, and digest canonicalization is not matchable to all concrete digest-bearing bundle records. A fourth major defect remains in source-registry role closure. These are specification defects, not merely missing implementation evidence.

## C. R3 finding re-evaluation

| R3 finding | Current status | Evidence |
|---|---|---|
| `E2E-R3-BLOCK-001` | PARTIALLY_CLOSED | R4 adds a closed exact-version package, but required active profiles and source contracts are still missing from that package. |
| `E2E-R3-BLOCK-002` | PARTIALLY_CLOSED | Package and schema registries exist, but active source schema IDs are not all package members. |
| `E2E-R3-MAJOR-001` | PARTIALLY_CLOSED | The role vocabulary is closed in the primary visibility profile, but source-registry role fields remain unconstrained. |
| `E2E-R3-MAJOR-002` | CLOSED | Scenario IDs are explicitly correlation-only, non-authoritative, non-evidentiary, and forbidden as classifier/verifier signals; the limitation that this is not cryptographic opacity is stated. |
| `E2E-R3-MAJOR-003` | PARTIALLY_CLOSED | JCS/SHA-256 is declared, but concrete bundle/scorer record forms do not align with the applicability keys. |
| `E2E-R3-MAJOR-004` | CLOSED | The active rule set is enumerated and its declared dependency graph has no cycles or missing references. |
| `E2E-R3-MAJOR-005` | PARTIALLY_CLOSED | Rule syntax is deterministic, but a complete self-contained schema/profile scope cannot be assembled from the current package. |

The exact fresh findings are recorded in [`accord-02e-r4-review-findings.json`](accord-02e-r4-review-findings.json).

## D. Historical closure impact

The direct oracle-locator defect is closed: the public scenario catalog does not reference the scorer expectation catalog. The remaining side-channel rule is a bounded experimental design constraint, not a claim of cryptographic opacity. Typed lineage, canonical proposition binding, settlement projection non-strengthening, authority/effect orthogonality, and truth-independent normalization show no R4 regression.

The following historical closure claims remain dependent on the open package defects: `E2E-BLOCK-001` (complete system-level isolation), `E2E-MAJOR-003` (complete lineage), `E2E-MAJOR-004` (fully evaluable proposition/profile binding), and `E2E-MAJOR-005` (complete arm/profile enforcement).

## E. Specification package

`accord-02r4-specification-package.json` is a finite, versioned package manifest with `CLOSED_EXACT_VERSION` semantics. Its inventory is internally unique and its listed paths exist. It contains 30 schema contracts, 28 profile contracts, one canonicalization contract, and a nine-role vocabulary.

That closure is incomplete for the current stack. The package does not provide entries for active `EXPERIMENT_PROFILE`, `VERIFIER_PROFILE`, or `TRUST_ROOT_PROFILE` references, although run schemas and bundle usage require some of these categories. A package enum also does not include `EXPERIMENT_PROFILE`. Therefore a conforming implementation cannot construct a complete valid experiment/verifier scope without inventing a contract source.

## F. Profile resolution

The R4 profile resolution algorithm is clear in isolation: exact type, ID, and version; outcomes are resolved, missing, duplicate, wrong type, unsupported version, or structurally invalid. The package membership requirement is also clear.

The active inventory does not satisfy that contract. In addition, several arm-facing profile references in the active example profile catalog omit `profile_version`, while `PROF-002` requires exact version binding. This is an acceptance-critical dangling/under-specified reference path, not a latest-version implementation detail.

## G. Schema contracts

The package has a schema-contract registry and the listed schema files exist. Structural validation correctly requires resolving a normative schema contract before treating generic content as a record.

However, the active source-schema registry declares ten source schema ID/version pairs that do not appear in the package schema-contract inventory. This makes provider/task/attempt/source membership validation incomplete under the very package that is supposed to close it. A file existing elsewhere in the repository is not enough under `CLOSED_EXACT_VERSION`.

The generic-content rule is otherwise conservative: untyped content cannot become normative merely because it is present in a bundle entry.

## H. BND-004 and BND-005

The declared rule algorithms are structurally deterministic with profile/package inputs and the independent rule review classifies both as `DETERMINISTIC_WITH_PROFILE`. That classification does not make the current package complete:

- `BND-004` cannot establish complete structural/source resolution while required source schema contracts are outside package scope.
- `BND-005` cannot establish complete active-profile resolution while required profile types are missing and some active references are not version-pinned.

Thus the rule graph has no syntactic ambiguity, but the acceptance-critical contract is not satisfiable from a valid current R4 bundle.

## I. Role closure

The primary role-visibility profile uses a closed vocabulary: `ORCHESTRATOR`, `DELEGATE_FIXTURE`, `PROVIDER_FIXTURE`, `OBSERVER_FIXTURE`, `ARM-A-DURABLE`, `ARM-B-PROVIDER-OBSERVATION`, `ARM-C-LIGHTWEIGHT-CLASSIFIER`, `ARM-D-ACCORD-EVIDENCE`, and `SCORER`. Unknown roles are rejected there.

The source-schema registry separately permits arbitrary role strings in its `roles` arrays, and source membership rules do not force those values through the package vocabulary. Therefore `MAGIC_ADMIN` is rejected by one path but can enter another role-bearing path. This is `E2E-R4-MAJOR-002`.

## J. Canonicalization and digests

The package identifies RFC 8785 JCS, UTF-8, and SHA-256 in a versioned canonicalization profile. No circular package-integrity dependency was found: the package does not require its own digest to bootstrap resolution.

The applicability contract is not complete. The canonicalization profile is keyed to generic `BUNDLE_RECORD_CONTENT`/`SCORER_RECORD_CONTENT` forms, while verifier and experiment entries use concrete record types such as observations and settlement results. Scorer entries also lack schema ID/version fields needed to determine profile applicability. Consequently two implementations cannot always decide whether the same supplied digest is being checked under the same admitted record form. This is `E2E-R4-MAJOR-001`.

## K. Scenario-ID semantics

The R4 scenario-ID correction is adequate as a specification constraint. IDs are correlation-only, non-authoritative, non-evidentiary, and prohibited as baseline/classifier/verifier semantic inputs. The catalog explicitly states that controlled generation must avoid encoding expected outcome classifications and that the rule does not prove cryptographic non-correlation.

An accidental correlation remains an experiment-design/conformance risk, not an evidence source. No new finding is raised for this item.

## L. Active validation rules

The active composition is 71 R3/base rules plus 11 R4 overlay rules, with overrides for `BND-004`, `BND-005`, and `DIGEST-001`: 82 active rules total. Independent graph inspection found 140 dependency edges, zero cycles, zero missing dependencies, and no undefined produced or consumed facts.

The rule classification artifact records 19 `DETERMINISTIC`, 63 `DETERMINISTIC_WITH_PROFILE`, zero `AMBIGUOUS`, zero `UNEVALUABLE`, and zero `CONTRADICTORY`. This is a valid syntactic rule-graph result but not a readiness result: the package defects mean that required profile/schema inputs are not all resolvable in the declared scope.

## M. External verification

**NOT_SUPPORTED for the current R4 stack.** The bounded claim would be supportable with qualification once all required active profiles and source schema contracts are package members and digest applicability is made concrete. At present, a third-party verifier would have to discover or invent contracts outside the exact package to evaluate some acceptance-critical paths.

The review does not claim that evidence is true, that a provider is honest, or that external reality is proved. Trust roots, evidence assumptions, and absence of complete mediation remain explicit limits.

## N. Oracle and scorer isolation

No direct scorer locator is present in the public scenario catalog or arm manifests. The scorer-side join is one-way through `scenario_id`. ARM-C feature restrictions reject Accord/scorer semantics, and the score pipeline remains raw output → normalization → truth comparison → metrics.

This part of the design is substantively closed, subject to the incomplete package/profile scope preventing a fully valid arm bundle.

## O. Baseline fairness

The package does not change the declared entitlements: ARM-B retains ordinary provider-state observation/reconciliation, ARM-C retains ARM-B inputs plus registered features, and baselines are not required to emit Accord-native labels. No R4 fairness regression was found. The fairness contract is nevertheless affected by the source-schema package gap because a valid complete ARM-B source cannot currently be resolved under the exact package.

## P. Adversarial cases

The historical oracle, lineage, projection, normalization, and scenario-ID cases are resisted by the declared rules. R4 cases show:

- undeclared/latest/out-of-package profiles are rejected;
- unknown schemas and generic uncontracted content are rejected;
- the primary role profile rejects unknown roles;
- scenario-ID feature use is rejected;
- package/profile version mismatch is rejected;
- source-registry role smuggling is not resisted;
- digest profile identity is explicit but concrete record applicability is incomplete.

Full case-by-case evidence is in [`ACCORD-02E-R4-ADVERSARIAL-CASES.md`](ACCORD-02E-R4-ADVERSARIAL-CASES.md).

## Q. Implementation deferrals

The absence of an executable validator, verifier, experiment, interoperation test, provider integration, and standards-complete external JSON Schema engine run is deferred to conformance implementation. Those omissions are not themselves specification blockers. The open findings above are different: they prevent complete deterministic evaluation from the declared package.

## R. A2A note

`E2E-MINOR-002` remains an optional A2A coverage note. It does not undermine the mandatory two-transport research design and is not a blocker.

## S. Compatibility matrix

The fresh matrix contains 20 rows:

| Status | Count |
|---|---:|
| EXACT | 7 |
| COMPATIBLE | 0 |
| COMPATIBLE_WITH_PROFILE | 7 |
| AMBIGUOUS | 1 |
| INCOMPATIBLE | 5 |
| NOT_APPLICABLE | 0 |

Every ambiguous/incompatible row links to a current finding. See [`accord-02e-r4-compatibility-matrix.json`](accord-02e-r4-compatibility-matrix.json).

## T. Claim audit

The package, role, schema, and canonicalization artifacts are normative definitions. No empirical benefit, interoperability, or real-world truth claim has been established. “Self-contained” and “deterministic” are currently overclaims if applied to the entire active stack; they should be limited to the portions whose package contracts resolve. The exact overclaim list is in [`ACCORD-02E-R4-CLAIM-AUDIT.md`](ACCORD-02E-R4-CLAIM-AUDIT.md).

## U. Residual findings

- `E2E-R4-BLOCK-001` — required active profiles are missing or not fully version-pinned in the exact package.
- `E2E-R4-BLOCK-002` — active source schema IDs are absent from the exact package schema-contract inventory.
- `E2E-R4-MAJOR-001` — digest canonicalization applicability does not match all concrete digest-bearing record forms.
- `E2E-R4-MAJOR-002` — source-schema registry role membership is not closed to the declared vocabulary.
- `E2E-R4-NOTE-001` — no standards-complete external JSON Schema/interoperability run; deferred.

## V. Acceptance readiness

**ACCORD-02 MUST NOT PROCEED TO ACCEPTANCE.**

The appropriate next step is a bounded remediation of the four specification defects, followed by a fresh independent closure review. This review does not remediate them and does not create an acceptance seal.

## W. Validation

- Exact starting identity, ancestry, protected refs, accepted tags, and clean worktree were verified.
- Historical review/remediation artifacts were left unchanged.
- New JSON artifacts parse and have unique IDs.
- The active rule inventory contains all 82 expected IDs; dependency recomputation found no cycle.
- Compatibility statuses are valid and every ambiguous/incompatible row has a finding.
- No acceptance tag, runtime code, verifier, validator, harness, experiment, classifier training, dependency installation, provider call, merge, or push occurred.
- No external standards-complete JSON Schema validator was installed; structural claims are limited to static parsing/reference inspection and cross-artifact review.
- `git diff --check` and post-commit cleanliness are required and are reported after commit.

## X. Changed files

Only these fresh review artifacts are added:

- `docs/accord-02/ACCORD-02E-R4-INTEGRATED-REVIEW.md`
- `docs/accord-02/ACCORD-02E-R4-CONTRACT-CLOSURE-REVIEW.md`
- `docs/accord-02/ACCORD-02E-R4-CROSS-SLICE-COMPATIBILITY.md`
- `docs/accord-02/ACCORD-02E-R4-ADVERSARIAL-CASES.md`
- `docs/accord-02/ACCORD-02E-R4-CLAIM-AUDIT.md`
- `docs/accord-02/ACCORD-02E-R4-ACCEPTANCE-READINESS.md`
- `docs/accord-02/accord-02e-r4-review-findings.json`
- `docs/accord-02/accord-02e-r4-compatibility-matrix.json`
- `docs/accord-02/accord-02e-r4-validation-rule-review.json`

## Y. Commit

To be populated after validation and commit on `codex/accord-02e-r4-acceptance-readiness-review`.

## Z. Mutation attestation

All values are `NO`:

`ACCORD02_SPECIFICATIONS_MUTATED` · `ACCORD02_HISTORICAL_REVIEWS_MUTATED` · `ACCORD02R1_REMEDIATION_MUTATED` · `ACCORD02R2_REMEDIATION_MUTATED` · `ACCORD02R3_REMEDIATION_MUTATED` · `ACCORD02R4_REMEDIATION_MUTATED` · `ACCORD_RUNTIME_CODE_WRITTEN` · `VERIFIER_EXECUTABLE_WRITTEN` · `VALIDATOR_EXECUTABLE_WRITTEN` · `EXPERIMENT_HARNESS_WRITTEN` · `EXPERIMENT_EXECUTED` · `CLASSIFIER_TRAINED` · `ANANKE_MUTATED` · `HORAE_MUTATED` · `ADRASTEIA_SOURCE_MUTATED` · `MNEMOSYNE_MUTATED` · `FATES_MUTATED` · `EXTERNAL_REPOSITORIES_MUTATED` · `DEPENDENCIES_INSTALLED` · `PROVIDER_CALLS_MADE` · `MAIN_ADVANCED` · `ACCORD02_ACCEPTANCE_TAG_CREATED` · `PUSH_PERFORMED`.

`ACCORD02E_R4_REVIEW_COMMIT_CREATED` will be `YES` only after the fresh review artifacts are committed.

ACCORD-02E-R4 REVIEW COMPLETE — ACCORD-02 NOT READY FOR ACCEPTANCE.
