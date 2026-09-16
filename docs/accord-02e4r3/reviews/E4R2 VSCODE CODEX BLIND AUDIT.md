## A. Starting state

- HEAD: `3efed8ac234cf1a5acf34198b49022923fc8fad8`
- Tree: `d70b70d2c09363eea092b588658cfc133555cecf`
- Parent: `31231b01f2fa560dbec714c9ce72128754e18e4f`
- `accord-02-accepted-v1^{}`: `5a8bf1e577f71132665ece271e70e30e87df5676`
- No package-0.2 acceptance tag was present.
- Worktree was clean, with no staged or untracked repository files.

## B. Blindness attestation

Phase I reviewed the candidate’s machine-readable package, schemas, registry, profiles, canonicalization contract, rule contract, graph, and vector catalog before reading the closure checker, remediation prose, prior-review register, or validation reports.

One protocol caveat: while examining the permitted NEGATIVE_SCOPE requirement map, I also opened the adjacent V013 trace before the Phase-I freeze. I excluded that self-authored trace from Phase-I evidence and did not rely on it for the frozen findings. Phase II then examined it and the certifier explicitly.

## C. Frozen candidate integrity

The frozen candidate identity matches the required commit and tree. Candidate JSON documents parsed successfully.

## D. Accepted-0.1 integrity

The accepted ACCORD-02 tag resolves to the required object. The candidate’s `base_package` digest and declared base path identify the accepted package, but that does not establish amendment succession; see Section E.

## E. Package lineage

**Finding: E4R2-VSCODE-CODEX-BLOCK-001 — package 0.2 is not a deterministically identified successor of the accepted package family.**

- File: [accord-02e4r2-specification-package-0.2.json](D:\Users\fleur\Moirae Accord - E4R2 Blind Audit\docs\accord-02e4r2\accord-02e4r2-specification-package-0.2.json)
- Pointers: `/$id`, `/package_id`, `/base_package`, `/replaces_candidate_package`, `/candidate_only`
- Observed candidate ID: `urn:moirae:accord-02e4r2:specification-package`
- Accepted package ID: `urn:moirae:accord-02r5:specification-package`
- Observed version: `0.2`; accepted version: `0.1`
- Observed replacement relation: only to `urn:moirae:accord-02e4r1:specification-package@0.2`
- Expected: an explicit machine-readable amendment/successor relation from the accepted package ID and version to `0.2`, with replacement/acceptance semantics.
- Result: the package is explicitly marked `candidate_only: true` and is a closed package that depends on an immutable base. It does not say that it is version `0.2` of the accepted package identity. A consumer cannot answer the required question without interpreting builder history.

This is a bounded package-contract defect, not necessarily a need to reopen the settlement model.

## F. Independently derived effective inventory

I derived:

| Category | Derived count |
|---|---:|
| Schema-contract entries | 52 |
| Candidate-owned schema entries | 8 |
| Profile-contract entries | 32 |
| Canonicalization mappings | 52 |
| Source-schema pairs | 13 |
| Predicate/stage registry rows | 6 |
| Active rule IDs | 104 |
| Independently derived rule dependencies | 188 |
| Declared graph dependencies | 71 |
| Settlement vectors | 23 |
| Candidate digest-bearing forms | 24 |

The active-rule total reconciles as 71 base R3 rules, 14 R5 rule IDs of which 3 are overridden, plus 22 R1/R2 additions: `82 + 22 = 104`.

## G. Effective-package schema validation

Using an isolated temporary environment with:

- `jsonschema==4.26.0`
- `rfc3339-validator==0.1.4`
- `rfc3987-syntax==1.1.0`
- `rfc8785==0.1.4`

I meta-validated all 52 declared schema-contract entries under Draft 2020-12: **52/52 passed**.

I independently instance-validated the nine candidate artifacts for which the candidate provides an explicit schema contract:

- specification package
- normative contracts
- predicate registry
- vector catalog
- two settlement profiles
- canonicalization profile
- validation rules
- dependency graph

All nine passed their declared schemas.

However, three active candidate artifacts do not have a candidate-declared schema target in the contract inventory:

- `accord-02e4r2-reference-field-registry.json`
- `accord-02e4r2-negative-scope-requirement-map.json`
- `accord-02e4r2-source-schema-registry.json`

The first two are acceptance-critical and were therefore not independently schema-validated as instance contracts. Schema validity does not cure the semantic failures below.

## H. Exact reference graph

**Finding: E4R2-VSCODE-CODEX-BLOCK-002 — the exact-reference registry is incomplete, and the vectors use nonconforming live references.**

- Files:
  - [accord-02e4r2-reference-field-registry.json](D:\Users\fleur\Moirae Accord - E4R2 Blind Audit\docs\accord-02e4r2\accord-02e4r2-reference-field-registry.json)
  - [accord-02e4r2-settlement-vector-catalog.json](D:\Users\fleur\Moirae Accord - E4R2 Blind Audit\docs\accord-02e4r2\accord-02e4r2-settlement-vector-catalog.json)
  - [accord-02e4r2-canonicalization-profile.json](D:\Users\fleur\Moirae Accord - E4R2 Blind Audit\docs\accord-02e4r2\canonicalization\accord-02e4r2-canonicalization-profile.json)
- Governing requirement: `reference_resolution_policy` requires `OBJECT_ID_AND_EXPLICIT_VERSION`, code-point exact comparison, no normalization, and no repository fallback.
- Observed: the declared registry lists 228 non-null references, but it omits:
  - 23 `/vectors/*/source_vector_ref` fields, each an unversioned string;
  - 52 `/applies_to/*/canonicalization_profile_ref` fields;
  - 2 settlement-profile `complete_query_requirement_map_ref` fields.
- Thus there are at least **305** non-null normative reference-bearing fields, not 228.

The 23 `source_vector_ref` values are material: the candidate carries a target proposition and expected result, but not the underlying evidence inputs required to perform settlement. It relies on an unversioned identifier such as `ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE` and repository knowledge to locate the accepted vector.

Reproducible temporary-copy mutation:

```powershell
# The following was executed in memory against the Draft 2020-12 catalog schema:
vectors[0].source_vector_ref = "urn:garbage:vector:0.2"
```

Result: **0 schema errors**. No declared exact-reference registry entry governs this field, so the candidate’s stated reference machinery cannot reject it.

This alone prevents a fresh implementation from reconstructing the 23 settlement cases from declared contracts alone.

## I. Canonicalization and digest reproduction

The positive result is that canonicalization of the currently embedded digest forms is reproducible:

- 23 proposition digests checked
- 1 catalog digest checked
- **24/24 matched**
- RFC 8785 JCS and SHA-256 were applied from the candidate canonicalization contract.
- The proposition mappings exclude `/integrity/content_digest`; the catalog mapping excludes `/integrity`.

The mapping is sufficient for those 24 forms. But the general enforcement mechanism is not independently executable: uniqueness, target resolution, mapping conflict behavior, and the required reaction to malformed mappings are expressed partly as prose-only rules and are enforced by the Python checker’s bespoke code.

## J. Predicate/stage authority

The predicate registry does provide one explicit active authority keyed by exact `(predicate_id, stage)` tuples:

- 6 registry rows
- exact code-point equality
- no normalization, trimming, case-folding, prefix/suffix matching, or lexical fallback
- explicit unsupported `resource-visible/resource_visible` row
- explicit no-entailment booleans

This portion is independently understandable. Historical lexical identifiers have no declared active semantics.

## K. Binding authority/composition

The registry distinguishes required, optional, and not-applicable proposition bindings. The normative contract separately declares evidence-provenance bindings as additive and non-propositional.

The declared data correctly represents, for example:

- `recipient-ack` requires `recipient_or_counterparty`;
- generic external effect marks that binding not applicable;
- provider acceptance requires `provider`;
- the negative row has explicit null stage semantics.

But the package does not provide machine-evaluable semantics for evaluating all the composition rules. It relies on prose assertions such as `MUST_BE_SUBSET_COMPATIBLE_WITH_REGISTRY` and `MAY_NOT_INTERSECT_NOT_APPLICABLE_BINDINGS`.

## L. NEGATIVE_SCOPE / V013

**Finding: E4R2-VSCODE-CODEX-BLOCK-003 — V013 is described but not independently executable from the normative package.**

- File: [accord-02e4r2-negative-scope-requirement-map.json](D:\Users\fleur\Moirae Accord - E4R2 Blind Audit\docs\accord-02e4r2\accord-02e4r2-negative-scope-requirement-map.json)
- Pointers: `/requirements/*/validator_condition`
- Governing requirement: every completeness condition must have an executable validator condition and deterministic failure consequence.
- Observed: all twelve `validator_condition` values are prose strings, for example:
  - `RFC3339 interval is present and query covers it`
  - `evidence retention window covers query interval`
  - `evidence consistency level meets profile`
  - `validator computes admissible positive evidence count == 0`
- Expected: a defined operator vocabulary with structured operands, input population rules, comparison semantics, and fail-closed behavior.

The requirement map identifies useful fields, but does not specify:

- what evidence set is searched for contradictory admissible positives;
- how evidence admissibility is established;
- what “query covers” means for interval endpoints;
- the retention arithmetic;
- the ordering/comparison semantics for consistency levels;
- how “where applicable” scope dimensions are determined;
- the source of `verification_time`.

Therefore, two competent independent implementations can disagree on whether V013 satisfies the completeness contract while both obeying the package’s text. The answer to the required determinism question is **yes**.

The V013 self-trace does not cure this. In Phase II, the closure checker was found to treat trace entries marked `result: "PASS"` as satisfaction rather than evaluating candidate evidence.

## M. PARTIAL_EFFECT

The registry and normative contract express the intended policy:

- explicit predecessor edges only;
- same effect required;
- no implicit transitivity;
- `ATOMIC_ONLY` cannot yield partial effect;
- valid predecessor support can yield `PARTIAL_EFFECT`;
- absent, wrong-tuple, wrong-effect, or inadmissible predecessor support cannot.

The policy is readable, but the package lacks a formal evaluator for “supported,” “valid predecessor,” and “incompatible or inadmissible.” Consequently the intended cases cannot be implemented without supplying semantics not declared in the package.

## N. Generic/stage non-entailment

Both directions are explicitly represented as false:

- `GENERIC_OCCURRENCE` does not entail `POSITIVE_STAGE`;
- `POSITIVE_STAGE` does not entail `GENERIC_OCCURRENCE`.

I found no declared direct alternate entailment route. This part is clear at the policy level, although enforcement again depends on opaque rule conditions.

## O. Rule inventory

The independently reconstructed active inventory is 104 unique IDs with no missing dependency targets and no detected cycle in the full derived graph.

The candidate’s claimed rule count is therefore numerically correct, but the supplied dependency graph is incomplete.

## P. Rule executability

**Finding: E4R2-VSCODE-CODEX-BLOCK-004 — acceptance-critical R1/R2 rule conditions are prose, not machine-evaluable contracts.**

- File: [accord-02e4r2-validation-rules.json](D:\Users\fleur\Moirae Accord - E4R2 Blind Audit\docs\accord-02e4r2\accord-02e4r2-validation-rules.json)
- Pointers: `/candidate_additions/0..21/condition/operator`
- Governing requirement: a rule must have structured inputs, defined condition semantics, a failure result, and independently executable semantics.
- Observed: the `operator` field contains natural-language sentences, including:
  - `all non-null reference fields use one exact object ID/version representation and resolve`
  - `registry bindings and evidence capabilities compose without forbidden intersections`
  - `all complete-negative requirements map to observed proposition/profile/evidence fields`
- Expected: stable operator IDs plus parameter schemas and declarative semantics.

All 22 candidate additions are labelled `DETERMINISTIC_WITH_PROFILE`, but their condition language is undefined anywhere in the package. A fresh implementation cannot execute them without knowing the builder’s Python behavior.

## Q. Full dependency graph

**Finding: E4R2-VSCODE-CODEX-MAJOR-001 — the declared dependency graph is not the full effective rule graph.**

- File: [accord-02e4r2-validation-dependency-graph.json](D:\Users\fleur\Moirae Accord - E4R2 Blind Audit\docs\accord-02e4r2\accord-02e4r2-validation-dependency-graph.json)
- Pointers: `/node_inventory`, `/edges`
- Observed: 104 nodes and 71 declared dependency arcs.
- Independently derived from the active R3, R5, R1, and R2 rule records: 104 nodes and **188** arcs.
- Result: **117 active dependencies are omitted** from the supplied graph.

For example, inherited dependencies such as `ORC-001 → BND-001`, `ORC-001 → EXT-001`, `ARM-002 → ARM-001`, and `PROJ-001 → PROP-001` exist in active rule records but not in the candidate graph.

The graph checker verifies that listed nodes exist and listed edges are acyclic; it does not establish that all active dependencies were included.

## R. Evidence-profile semantics

The candidate supplies both `settlement_profile_ref` and `evidence_profile_ref` for every vector. Twenty-two vectors use the same profile; V018 uses the incompatible evidence profile.

The intended division is inferable from field names and prose-like role labels, but the contract does not provide a formal policy partition saying which decision functions each profile exclusively controls. This is a supporting ambiguity, not the primary blocking reason.

## S. Profile digest scope

The settlement profiles state that evidence artifact digests may be optional, while the candidate proposition schemas require their integrity digests. The current fixtures do not directly contradict that distinction.

However, the rules that are meant to ensure the distinction are opaque and only machine-enforced by the certifier.

## T. Profile compatibility

The compatible/incompatible profile records provide pairwise compatibility data and V018 identifies an incompatible pairing. The current vector resolution is clear, including self-compatibility behavior for the declared profiles.

## U. 23-vector reconstruction

- Target proposition/schema/profile references: **23 exact**
- Full settlement input reconstruction from the candidate’s own exact contract graph: **0 exact**
- Complete independent outcome reconstruction: **0/23**

The latter failure is because every vector depends on an undeclared, unversioned `source_vector_ref` rather than an exact reference to a source vector/evidence object. The expected result is embedded as an assertion, not reproducible settlement evidence.

## V. Full 0.1→0.2 expectation comparison

Using repository lookup only after Phase I, I compared each candidate `source_vector_ref` against the accepted 0.1 vector catalog:

- candidate vectors: 23
- accepted vectors: 23
- exact `expected` object matches: **23/23**
- differences: **0**

This is useful regression evidence, but it does not repair the package: the comparison itself required the repository-specific lookup that the package fails to declare.

## W. Positive usefulness

The expected-result catalog continues to represent:

- generic occurrence;
- resource-created occurrence;
- corroborated/effect-supported occurrence;
- PARTIAL_EFFECT;
- scoped NON_OCCURRENCE_SUPPORTED.

There is no all-UNKNOWN retreat in the declared expectations.

## X. Fresh mutation campaign

I used temporary/in-memory mutation analysis; no candidate file was written. Results under the declared machine-readable machinery:

1. Change candidate package ID to accepted-family form — successor semantics are not defined.
2. Replace a `source_vector_ref` with garbage — **not detected by its catalog schema**.
3. Add whitespace to `source_vector_ref` — no declared resolver governs it.
4. Change its case — no declared resolver governs it.
5. Replace it with a stale E4 namespace — no declared resolver governs it.
6. Add `@0.2` to it — no declared resolver governs it.
7. Remove a source-vector version — there was no explicit version to remove.
8. Duplicate a canonicalization mapping — policy requires failure, but schema does not enforce it.
9. Conflict two mappings — policy requires failure, but semantics are checker-defined.
10. Remove a canonicalization mapping — current checker detects it, but only through bespoke code.
11. Change canonicalization algorithm — schema/policy shape can reject this.
12. Change a stored proposition digest — independently detected by JCS hash reproduction.
13. Change a proposition semantic field — independently changes its digest.
14. Remove recipient binding from `recipient-ack` — data mismatch is identifiable, but full enforcement is checker-defined.
15. Mark recipient binding N/A — violates declared sets, but enforcement is checker-defined.
16. Add recipient to generic external-effect requirement — contradicts registry policy, but enforcement is checker-defined.
17. Use a predecessor from another effect — policy says fail; evaluator semantics are not declared.
18. Add a missing inherited rule dependency — declared graph cannot reveal its own omission.
19. Remove an inherited graph dependency — declared graph remains structurally valid.
20. Replace V013 `FRESH_AT_VERIFICATION` semantics — requirement map has no executable operator.
21. Remove V013 retention evidence — prose identifies failure but no executable condition.
22. Add contradictory admissible positive evidence — the package does not define the evidence universe/query that computes the count.

The campaign confirms that the contract detects digest tampering, but not the principal reference, rule-semantics, V013, and graph-completeness defects as a standalone package.

## Y. Frozen Phase-I findings

The following Phase-I findings were frozen before inspecting the checker or prior-assessor materials:

- `E4R2-VSCODE-CODEX-BLOCK-001`: ambiguous/unrelated package lineage.
- `E4R2-VSCODE-CODEX-BLOCK-002`: incomplete exact-reference graph; 23 unversioned source-vector references.
- `E4R2-VSCODE-CODEX-BLOCK-003`: V013 completeness conditions are prose-only and non-executable.
- `E4R2-VSCODE-CODEX-BLOCK-004`: R1/R2 rule operators are prose-only and non-executable.
- `E4R2-VSCODE-CODEX-MAJOR-001`: dependency graph omits 117 active dependencies.

No Phase-II evidence refuted or downgraded these findings.

## Z. Phase-II certifier inspection

I did not run the closure checker because it writes reports into the repository, which the brief forbids. I inspected it read-only.

It confirms the concerns:

- `negative_errors()` checks whether the V013 trace says `PASS`; it does not evaluate evidence fields, retention, intervals, freshness, consistency, or contradictory evidence.
- `binding_errors()` hard-codes the recipient-ack predicate identifier and special-case binding behavior.
- `canonical_errors()` implements canonicalization selection and deletion logic in Python.
- `package_errors()` hard-codes the candidate package ID/version.
- the checker saves rewritten reports, including reference-resolution and mutation reports, into the candidate directory.
- graph checking consumes the already incomplete graph rather than reconstructing every rule dependency.

## AA. Comparison with previous assessor evidence

The candidate’s prior-assessor register claims earlier issue classes were reproduced and closed. My independent result differs materially:

- the current package does reproduce its 24 embedded digests;
- the candidate’s current schema documents pass their supplied schemas;
- but the core closure claims rely on the checker and self-authored trace rather than independently executable contracts;
- the package retains an incomplete exact-reference graph and an incomplete dependency graph.

Prior reports are therefore not sufficient evidence of final independent implementability.

## AB. Builder/certifier coupling assessment

The coupling is material.

The builder creates prose-valued `condition.operator` strings, and the certifier assigns them meaning in Python. The checker also hard-codes values and special cases, including package identity, recipient acknowledgement, catalog mapping selection, V013 trace success, and multiple mutation outcomes.

A separately written implementation cannot obtain those semantics from the normative package alone.

## AC. Independent-implementability conclusion

**Can an implementation written without seeing the E4R2 Python builder/checker reproduce the package’s normative behavior?**

**No.**

It can parse schemas, resolve some typed references, reproduce the currently embedded digest values, and read the intended policy. It cannot deterministically:

- identify the candidate as the accepted package’s version-0.2 successor;
- resolve all 23 vector inputs and their evidence;
- evaluate V013’s complete-negative requirements;
- execute the acceptance-critical R1/R2 rule conditions;
- construct the claimed full rule-dependency graph.

## AD. Findings register

| ID | Severity | Summary |
|---|---|---|
| E4R2-VSCODE-CODEX-BLOCK-001 | BLOCKING | Candidate package is not explicitly the accepted package family’s `0.2` successor. |
| E4R2-VSCODE-CODEX-BLOCK-002 | BLOCKING | Exact-reference inventory excludes live vector/effective-contract references; 23 vector inputs are unversioned strings. |
| E4R2-VSCODE-CODEX-BLOCK-003 | BLOCKING | V013 complete-negative semantics are prose-only; self-trace replaces evidence evaluation. |
| E4R2-VSCODE-CODEX-BLOCK-004 | BLOCKING | R1/R2 acceptance-critical rules lack formal executable operator semantics. |
| E4R2-VSCODE-CODEX-MAJOR-001 | MAJOR | Declared dependency graph has 71 edges versus 188 active-rule dependencies; 117 are omitted. |
| E4R2-VSCODE-CODEX-MAJOR-002 | MAJOR | Reference registry and negative requirement map lack independently declared instance-schema contracts. |
| E4R2-VSCODE-CODEX-NOTE-001 | NOTE | Current 24 candidate digest forms reproduce correctly with RFC 8785 JCS/SHA-256. |
| E4R2-VSCODE-CODEX-NOTE-002 | NOTE | The 23 embedded expected-result objects match accepted 0.1, but only through repository-specific source-vector lookup. |

## AE. Final verdict

## REMEDIATE_FINAL_AMENDMENT_CANDIDATE

## AF. Next gate

`REMEDIATE_E4R2_FIRST`

## AG. Worktree integrity

- HEAD remained `3efed8ac234cf1a5acf34198b49022923fc8fad8`.
- Worktree remained clean.
- No staged or untracked repository files were created.
- The temporary validator environment was removed.
- ACCORD-03 was not modified by this audit.

## AH. Mutation attestation

`REPOSITORY_MUTATED: NO`  
`TRACKED_FILE_MUTATED: NO`  
`UNTRACKED_FILE_CREATED_IN_REPO: NO`  
`BRANCH_CREATED: NO`  
`COMMIT_CREATED: NO`  
`TAG_CREATED: NO`  
`PUSH_PERFORMED: NO`  
`MAIN_ADVANCED: NO`  
`ACCORD02_ACCEPTED_MUTATED: NO`  
`ACCORD03_MUTATED: NO`  
`TEMPORARY_AUDIT_ARTIFACTS_REMAIN: NO`

## AI. Stop

`ACCORD-02E4R2 VS CODE CODEX BLIND AUDIT COMPLETE — CANDIDATE REMEDIATION REQUIRED.`