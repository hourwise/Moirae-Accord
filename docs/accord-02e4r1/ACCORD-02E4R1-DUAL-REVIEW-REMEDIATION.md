# ACCORD-02E4R1 — Dual-Review Amendment Remediation

## Candidate and boundary

This is a new, unaccepted package-0.2 candidate based directly on E4 commit `27670a6733b86c6061a8bb5c6188a266b7b3cb85`, on branch `codex/accord-02e4r1-dual-review-remediation`. The accepted ACCORD-02 package-0.1 and the E4 candidate are preserved as historical inputs. No ACCORD-03 artifact was modified.

The two supplied external review files are preserved byte-for-byte at:

* `../reviews/INDEPENDENT ACCORD 02E4 NORMATIVE AMENDMENT REVIEW CLAUDE.md`
* `../reviews/INDEPENDENT ACCORD 02E4 PACKAGE FALSIFICATION REVIEW DEEPSEEK.md`

The actual local review metadata is recorded in `accord-02e4r1-external-assessment-manifest.json`. The local files do not match the byte/hash metadata quoted in the R1 instruction; no normalization or false match claim was made.

## Finding intake and adjudication

`accord-02e4r1-dual-review-findings.json` ingests 20 Claude findings and 31 DeepSeek findings exactly once. Findings remain assessor-specific; overlap is not silently collapsed. The R1 candidate closes the 23 blocking/major findings represented by the two assessments and carries 28 minor/note observations forward.

The disagreements were adjudicated against the effective candidate package:

* Canonicalization: DeepSeek was correct about E4: the candidate mappings were not resolvable against a declared candidate profile. R1 supplies an exact replacement profile, concrete schema/container mappings, content targets, and digest policy. Claude's desired explicit mapping is now satisfied by the R1 artifacts.
* Profile resolution: DeepSeek was correct about E4: inherited versionless vector references fail exact resolution. R1 writes exact settlement and evidence profile type/ID/version references into all 23 vectors.
* Predicate authority: DeepSeek was correct about E4: the inherited lexical authority remained in the effective inventory. R1 retires that authority for the active candidate and makes lexical resolution forbidden. The R1 registry is the sole active authority.
* Rule inventory: DeepSeek was correct about E4: the unchanged 82-rule claim did not express the new obligations. R1 uses a versioned overlay, with 97 active rules and an explicit semantic trace; it does not preserve 82 as a misleading sufficiency claim.

## Frozen semantic design

R1 preserves the E4 design freeze: modified Option D; exact `(predicate_id, stage)` resolution; `POSITIVE_STAGE`, `GENERIC_OCCURRENCE`, and `NEGATIVE_SCOPE`; explicit predecessor edges; no global stage order; generic external effect as occurrence; recipient acknowledgement with an explicit provider-acceptance predecessor; resource creation; provider acceptance; fail-closed resource visibility; V013 as a bounded negative scope; no lexical fallback; and no automatic generic/stage entailment.

## Fail-closed and exact matching

The predicate registry and normative contract define deterministic outcomes for unknown predicates, wrong stages, undeclared tuples, unsupported predicates, missing required bindings, unsupported proposition kinds, and unresolvable profiles. These outcomes use named statuses and reason codes and cannot produce a positive semantic result.

Identifier equality is UTF-8 code-point equality, case-sensitive, with no Unicode normalization, trimming, case folding, punctuation normalization, prefix/suffix matching, lexical similarity, or namespace fallback.

## Profile, schema, and package closure

The candidate package remains `urn:moirae:accord-02r5:specification-package` version `0.2` with `CLOSED_EXACT_VERSION` policy. The immutable 0.1 base is pinned by its SHA-256. The candidate inventory is 51 schema contracts, 32 profile contracts, one canonicalization profile, nine role values, 13 active source-schema pairs, 16 active arm-profile references, and 97 active validation rules.

All 23 vector settlement/evidence profile references are exact and resolve. The replacement settlement profiles validate against the accepted settlement-profile schema. The candidate vector catalog instance, predicate registry, normative contracts, and canonicalization profile are package-inventoried rather than orphan files. Package closure checks reject traversal paths, missing files, duplicate contracts, conflicting tuples, unsupported capability rows, dangling predecessor edges, self-edges, cycles, and conflicting canonicalization mappings.

## Catalog and proposition repair

The candidate catalog preserves all 13 accepted expectation axes, reason codes, and `must_not_conclude` prohibitions for all 23 vectors. Its field-by-field stability check reports `23/23 FULL SEMANTICS PRESERVED`, with no changed or missing fields. V013 is represented by the typed negative-scope proposition schema. V014, V017, and V021 keep control/expectation data outside proposition content; all 23 embedded targets validate against their declared proposition schema.

## Negative scope, bindings, and stages

The bounded negative-scope contract closes state space, exact negated predicate/stage binding, applicable resource/action/recipient/provider scope, effect interval, retention, consistency, freshness, contradictory evidence, and the accepted complete query source class. Silence, timeout, stale, and incomplete reads are not sufficient.

The registry is authoritative for proposition-specific required/optional/not-applicable bindings. Settlement profile requirements are additive evidence requirements and cannot weaken registry requirements. Predecessor support requires the same logical effect and exact predecessor tuple. Direct edges are explicit; no implicit transitivity is introduced. The stage policy uses `NO_IMPLICIT_SUCCESSOR`, so a row may be referenced as a predecessor without contradiction.

Both generic-occurrence/non-stage entailment directions are explicit, as are authority/effect non-entailments. `PARTIAL_EFFECT` is a referenced normative policy, not an orphan invariant.

## Canonicalization and stability

The R1 canonicalization profile is an exact RFC 8785 JCS / UTF-8 / SHA-256 contract. It contains the inherited mappings plus three concrete candidate forms for verifier propositions, negative-scope propositions, and the candidate vector catalog. Each mapping identifies container type, schema ID/version, record type, and content target. JCS digest stability was checked under key reordering, and semantic mutation changes the digest. The closure report contains no unresolved mapping.

## Rule inventory and validation

The active rule decision is `VERSIONED_RULE_OVERLAY_REQUIRED`: 82 immutable base rules plus 15 explicit R1 candidate rules, for 97 active rules. The semantic trace maps each R1 obligation to a rule and has no unmapped obligations. The dependency graph is acyclic and has no missing dependencies.

The isolated Draft 2020-12 validation environment is recorded in the closure certificate. `jsonschema==4.26.0`, `rfc3339-validator==0.1.4`, `rfc3987-syntax==1.1.0`, and `rfc8785==0.1.4` were used. Seven R1 schema documents and all R1 instances passed; no accepted or ACCORD-03 specification was modified.

## Static adversarial closure

The bounded checker detects all 18 required package mutations: duplicate/conflicting registry tuples, dangling/self/cyclic predecessor changes, missing or unsafe paths, duplicate contracts, stale base digest, conflicting canonicalization mapping, binding contradiction, unsupported capability, wrong/versionless profile references, dropped or altered expectations, and lexical predicate lookalikes. Result: `18/18`, `PASS`.

## ACCORD-03 impact

None. ACCORD-03 remains frozen and unstarted for this remediation. No settlement engine, verifier, experiment, runtime, dependency set, or external repository was changed.

## Verdict and next gate

`AMENDMENT_CANDIDATE_READY_FOR_DUAL_REASSESSMENT`

This is not package-0.2 acceptance. A fresh dual independent reassessment must inspect the candidate and the preserved evidence before any acceptance, merge, tag, or promotion.
