ACCORD-02E4 — BLIND INDEPENDENT PACKAGE FALSIFICATION REVIEW
Scope discipline. Phase I inspected only the machine-readable candidate package, its schemas, the two candidate profiles, the candidate vector catalog and its schema, and the inherited accepted 0.1 contracts. No ACCORD-03 implementation behaviour was treated as intended semantics. Two candidate analysis JSONs (…-normative-settlement-invariants.json, …-expected-outcome-stability.json, …-spec-consistency.json) were read as candidate artifacts during Phase I; the amendment prose, decision provenance and profile audit were read only after the finding list was frozen. Validation used a real Draft 2020-12 engine: jsonschema 4.26.0 + rfc3339-validator 0.1.4 + rfc3987-syntax 1.1.0 + rfc8785 0.1.4 in a throwaway venv outside the repository.

A. Starting state
Item	Expected	Observed
Branch	codex/accord-02e4-normative-settlement-amendment	✓
HEAD	27670a6733b86c6061a8bb5c6188a266b7b3cb85	✓
Tree	684c0d44aa923947381c2724e2339c08aad5522b	✓
Parent	f8bdc730d1c3258cb687d838d94c2faa545ba438	✓
Worktree	clean	✓ (git status --porcelain -uall empty)
main / origin/main / accord-02-accepted-v1^{}	5a8bf1e5…	✓ all three
0.2 acceptance tag	none	✓ none (accord-00/01/02-accepted-v1 only)
git diff --name-status accord-02-accepted-v1 HEAD -- docs/accord-02	empty	✓ empty
B. Final verdict
REMEDIATE_AMENDMENT_CANDIDATE
Six blocking and eleven major candidate defects. The Option D direction itself survives — all 23 targets resolve exactly at the (predicate_id, stage) level — but the package as frozen is not internally consistent: the catalog fails its own schema, both profiles fail the schema they declare, the new digest mappings do not resolve, no vector can resolve a settlement profile, and two predicate authorities remain active with disjoint vocabularies.

C. Phase-I blindness attestation
My Phase-I finding list was written to session memory before reading ACCORD-02E4-NORMATIVE-SETTLEMENT-AMENDMENT-DRAFT.md, accord-02e4-decision-provenance.json and accord-02e4-profile-contract-audit.json. Findings were derived by direct inspection and by a real validator, not from the candidate's self-reports. A keyword scan afterwards confirmed that none of my six blocking findings' core concepts (must_not_conclude, versionless, digest_policy, SCORER_BUNDLE, semantic_status, compatible_profile_ids, validator) appear anywhere in E1/E2/E3.

Disclosure. In the previous session I read the E3 review and the E2 candidate registry as part of a different task. I therefore began this review with prior knowledge of the E3 option analysis and E2's registry draft. My Phase-I findings are re-derived from package 0.2 itself and are reproducible without reference to those documents; I did not carry any E3 conclusion into my verdict (indeed I disagree with E3's "stop before drafting" gate). No E4 prose was read before the freeze.

D. Accepted-0.1 integrity
accord-02 is byte-identical to accord-02-accepted-v1 (diff empty). The sealed 0.1 package's SHA-256 is sha-256:fbb9c3cc…be105c and the candidate's base_package.package_sha256 matches it exactly — verified by hashing the file. The 0.1 vector catalog's SHA-256 is sha-256:9f58e7dc…18afe and the candidate's stability record pins the same value — verified.

E. Package-0.2 closure
Verified independently (not from the candidate's claims): schema contracts 44 + 5 = 49 ✓; profile contracts 31 + 1 (with 2 replacements, net 0) = 32 ✓; canonicalization profiles 1 ✓; roles 9 ✓; source-schema pairs 13 ✓ (13 registry entries); active rules 82 ✓ — reproduces by following the R2 → R3 base_registry → R5 overlay chain (71 base-chain rules + 11 overlay rules, 3 overrides, 82 unique). active_arm_profile_reference_count: 16 is explicable as 4 distinct *_ref keys × 4 ARM documents, but raw occurrences total 52 (NOTE‑06).

Version isolation: 0.2 is a distinct document with contract_policy: CLOSED_EXACT_VERSION, a pinned base digest, and no in-place reinterpretation of the 0.1 file. No ambient latest/current substitution is declared. However the same profile_id is reused at version 0.2 with replaces_profile_version: 0.1, and the inventory arithmetic (32 = 31 + 1) shows the 0.1 tuples are removed rather than coexisting — see BLOCK‑05 and BLOCK‑06.

F. Schema validation
Environment: Python 3.14.0, jsonschema 4.26.0, rfc3339-validator 0.1.4, rfc3987-syntax 1.1.0, rfc8785 0.1.4; Draft202012Validator.check_schema + iter_errors with a pinned format checker.

All eight schemas are syntactically valid (check_schema OK for the 5 candidate schemas plus the accepted settlement-profile, canonicalization and applicability schemas).

Instance results:

Instance	Declared schema	Errors
accord-02e4-specification-package-0.2.json	…specification-package:0.2	0
accord-02e4-predicate-applicability-registry.json	…predicate-registry:0.2	0
accord-02e4-settlement-vector-catalog.json	…settlement-vector-catalog:0.2	1 — target_selection_rule is not allowed (additionalProperties: false)
profiles/…conservative-v2.json	urn:moirae:accord-02c:schema:settlement-profile:0.1	1 — understood_evidence_dimensions/7/required_for/1: "CORROBORATION" is not one of the accepted enum
profiles/…incompatible-v2.json	same	1 — identical violation
Removing the single unexpected root key yields 0 errors for the catalog; replacing the single CORROBORATION value yields 0 errors for both profiles (so the profiles are otherwise complete and conformant — the defect is minimal and exactly localised).

Schemas that are valid but cannot constrain what E4 claims:

semantic_status is {"enum": ["SEMANTICS_PRESERVED"]} — a one-value enum, so no vector can ever be marked as changed, and the catalog structurally cannot record the semantics change it is meant to detect.
expected is {"additionalProperties": true} requiring only overall and occurrence, so no expectation axis is enforced or even enumerated.
The registry schema imposes no uniqueness on (predicate_id, stage); two recipient-ack/recipient_acknowledged rows with different required_bindings validate with 0 errors.
The catalog's target sub-schema is a fourth target vocabulary, $ref-free: it does not reference either proposition schema, and the proposition schemas have additionalProperties: false — so 4 of 23 targets are not valid proposition records (§I).
§28 closure attacks (temporary copies). Caught: wrong candidate version; wrong base SHA-256 pin; inventory count mismatch; undeclared content_target. Not caught: duplicate profile addition; duplicate schema addition; path traversal (../../../etc/passwd.json inside profile_path / schema_path, whose pattern permits ..); a non-existent candidate schema path; the same schema mapped twice with contradictory content_target; dangling predecessor edge; predecessor self-edge; a GENERIC_OCCURRENCE row with a null stage; resource-visible flipped to SUPPORTED with no evidence capability; registry required_bindings contradicting the profile. The candidate declares no closure procedure — the package schema is structural only, and the candidate's own "static closure" record is a hand-authored PASS list whose own limitation note states no standards-complete validator was used (NOTE‑04).

G. Predicate identity
resolution_key: ["predicate_id","stage"], canonical_vocabulary: CANONICAL_C_VECTOR_URNS, lexical_fallback: false, no profile_predicate_id namespace (E4 removed E2's dual-identity bridge — a verified correction). Unknown URN → no row → no semantics; alternate case → no row; prefix/suffix lookalike → no row. Good.

But two authoritative identities survive (BLOCK‑06). The inherited 0.1 PREDICATE_APPLICABILITY_PROFILE contract (urn:moirae:accord-02r3:predicate-applicability:fixture-v1, lexical rows create_resource / deliver_item / provider_acceptance) is still in the effective inventory — the candidate replaces only the two SETTLEMENT_PROFILEs and adds the registry. Validating the 0.2 registry against the inherited applicability schema yields 7 errors (its profile_id, dimensions, predicates shape are incompatible). So a lexical alternate spelling of a known predicate does resolve to semantics, and nothing in the package detects or forbids the coexistence. The invariants file asserts dual_profile_predicate_id: false, but that is an unenforced statement.

H. Stage identity
Fields capable of selecting a stage: the proposition's stage, the registry row's stage, the profile's partial_effect policy fields, and the catalog target's stage. The catalog→registry agreement is exact for all 23 (effect ×18, recipient_acknowledged ×2, resource_created ×2, null ×1) with 0 kind mismatches, and proposition_kind matches the registry kind in all 23 (by authoring, not by any machine constraint — MINOR‑07).

Mismatch handling is not determined: nothing states whether a proposition whose stage disagrees with the registry row for its predicate_id is rejected, and no binding_status/kind cross-check exists. Worse, the relation has four incompatible encodings:

Artifact	Field	Shape
Catalog target	predecessor	singular object
Registry row	predecessor_edges	array
Profile	stage_order_field: "stage_predecessors"	string naming a field no candidate record declares
Accepted result schema	stage_predecessors / prerequisite_stage_ids	arrays
and stage_settlement / later_stage_policy vocabularies diverge from the accepted schemas (MAJOR‑04).

I. 23-vector target reconstruction (package-only)
Dimension	Result
Targets with explicit predicate URN, stage and kind	23
(predicate_id, stage) tuples resolving to exactly one registry row	23 / 23
proposition_kind agreeing with the registry kind	23 / 23
Targets that are valid instances of the proposition schema they name	19 / 23
Vectors with a resolvable settlement profile	0 / 23
Unresolved targets	0
Ambiguous targets	0 at tuple level; 4 at record level
So the headline claim 23 / 0 / 0 is true at the tuple level and false end-to-end: V013, V014, V017 and V021 carry fields (negative_scope, predecessor, causal_attribution, mismatch_policy) that the proposition schemas forbid and that no contract maps onto them; and no vector can resolve the profile under which it is to be settled (BLOCK‑05).

J. Expected-outcome comparison with accepted 0.1
Accepted 0.1 axis	Present in 0.2 / absent
overall, occurrence	23 / 0
authority_status, profile_compatibility, attribution, causality, completeness, sufficiency, freshness, duplication, finality, reason_codes, must_not_conclude	0 / 23
Headline values match for all 23 (0 mismatches on overall/occurrence). But 31 must_not_conclude prohibitions and 30 reason_codes are gone, and 11 of 13 acceptance axes are absent from every vector. The prohibitions lost include UNIVERSAL_TRUTH, EXACTLY_ONCE, NON_OCCURRENCE_SUPPORTED, RECIPIENT_ACKNOWLEDGEMENT, TARGET_RECIPIENT_ACKNOWLEDGED, UNIVERSAL_ABSENCE_OUTSIDE_SCOPE, NON_OCCURRENCE_FROM_SILENCE, SPECIFIC_ATTEMPT_CAUSED, ATTRIBUTED_TO_SPECIFIC_ATTEMPT, CURRENT_STATE, IRREVERSIBLE_FINALITY, DISPATCH_DID_NOT_OCCUR. The candidate's stability record nonetheless reports changed_expected_outcomes: 0 and SEMANTICS_PRESERVED 23, and the catalog's semantic_status enum cannot express anything else (BLOCK‑03).

Additionally V015's expectation uses {"authority": "INVALID"} — an axis name and a value that exist in no declared vocabulary (the accepted token is INVALID_AUTHORITY; "authority" as an expectation key is new here). Because expected is open, it validates silently (MINOR‑08).

K. Generic occurrence
GENERIC_OCCURRENCE at stage effect, predecessors: [], stage_settlement: ATOMIC_ONLY, required_bindings: [effect_id, predicate_id, stage], not_applicable_bindings: [recipient_or_counterparty].

What is asserted is not in the registry row: the row gives a kind label and a dangling evidence_capability_ref (urn:moirae:accord-02e4:evidence-capability:generic-occurrence:0.2, which is never declared as any id — MAJOR‑02). The only semantic statement ("Only the named logical external effect occurred") is in the unreferenced invariants file.
stage: "effect" is not schema filler — it is a real stage token that evidence must bind, and all 18 generic vectors resolve to it. But nothing defines what evidence class may satisfy it: the profile's class table uses generic tokens (supports: ["OCCURRENCE"]) with no mapping to (predicate, stage).
Can weak evidence satisfy it? PROVIDER_ACCEPTANCE_RECEIPT.supports = ["PROVIDER_ACCEPTANCE"] and does_not_prove: ["OCCURRENCE", ...] in the profile, so the class table blocks acceptance → generic occurrence. This is coherent at the class level but the binding of class→predicate is unspecified.
Can specific-stage evidence satisfy it? Undetermined. The draft says no (prose); no machine-readable artifact says so (no ENTAIL/NON_ENTAIL tokens anywhere; same_effect appears only in corroboration.require_same_effect_and_predicate).
Can it become PARTIAL_EFFECT? ATOMIC_ONLY in the registry is machine-visible ⇒ no. ✓ (first case in §M that is fully determined).
Ambiguity found: in a valid candidate package, a producer may hold both a generic and a stage-specific proposition for one effect; nothing forbids an implementation from inferring one from the other, and the corpus cannot test it because no effect carries both kinds.
L. Positive-stage propositions
Row	Registry required_bindings	Profile identity_bindings.required_for_attributed_occurrence	Agreement
resource-created/resource_created	effect_id, predicate_id, stage, resource	effect_id, predicate_id, stage	✗
recipient-ack/recipient_acknowledged	effect_id, predicate_id, stage, recipient_or_counterparty	same	✗
provider-acceptance/provider_accepted	effect_id, predicate_id, stage, provider	same	✗
Three stages of the three stage-specific rows disagree with the global profile set. The proposition schemas make resource, recipient_or_counterparty, provider optional and constrain them only by type, while an optional free binding_status object offers OPTIONAL for the very dimensions the registry marks REQUIRED. A checker must combine three artifacts with no declared precedence (MAJOR‑03). resource-visible is correctly fail-closed as an explicit UNSUPPORTED row — except that flipping it to SUPPORTED with empty bindings and a null capability validates cleanly (§F).

M. PARTIAL_EFFECT — the eight cases
Derivation from machine-readable contracts only:

Case	Determined?	Basis
1. target unsupported + predecessor supported	Partly — PARTIAL_EFFECT is the profile's partial_result and the registry declares the edge, but the composition rule (row + policy ⇒ PARTIAL_EFFECT rather than NOT_SUPPORTED) is stated only in the unreferenced invariants file	MAJOR‑01
2. target unsupported + no predecessor supported	No — nothing states the outcome for a predicate that has predecessors, none supported	gap
3. target supported + predecessor supported	Yes (both axes independent)	registry INDEPENDENT_WHEN_BOUND for provider-acceptance
4. generic target	Yes — predecessors: [] + ATOMIC_ONLY	✓
5. ATOMIC_ONLY target	Yes — same	✓
6. incompatible evidence	Yes — profile incompatible_outcome: PROFILE_INCOMPATIBLE	✓
7. predecessor from another effect	No — no contract couples predecessor evidence to the same effect_id	MAJOR‑11
8. predecessor same name, wrong predicate identity	Yes — resolution is by URN tuple	✓
Only the intended case is contractually allowed to produce PARTIAL_EFFECT; the unintended cases 2 and 7 are simply undefined, and case 1 depends on an unreferenced file.

N. Predecessor graph
The single declared edge recipient-ack/recipient_acknowledged → provider-acceptance/provider_accepted resolves; there is no self-edge and no cycle. But: nothing validates edge targets (a dangling edge and a self-edge both validate with 0 errors); transitivity is neither defined nor explicitly disclaimed; the catalog expresses at most one predecessor while the registry expresses a set; and provider-acceptance's own row declares later_stage_policy: NO_SUCCESSOR_DECLARED while another row declares it as a predecessor — a direct internal contradiction (MAJOR‑05). The registry's stage_ordering_scope: PROFILE_AND_PREDICATE_FAMILY and global_total_order: false are the right shape and are the strongest part of the candidate.

O. NEGATIVE_SCOPE — under-specified
What is negated, of which effect, over which interval, with which read semantics is not deterministically interpretable. Two implementers can construct different meanings from one valid negative proposition because:

scope.state_space, interval, retention_reference, read_semantics, consistency are all {"type":"string","minLength":1} — free text, no enum, no pattern, no $ref;
evidence_profile_id is a free unresolvable string (no profile type is named);
the profile's enumerated vocabulary (COMPLETE_STATE_SPACE, PREDICATE_BOUND, RESOURCE_BOUND, INTERVAL_BOUND, RETENTION_DECLARED, CONSISTENCY_DECLARED, FRESH_AT_VERIFICATION, NO_CONTRADICTORY_EVIDENCE) is never mapped to those five fields;
the class table's COMPLETE_NEGATIVE_LEDGER_QUERY.required_bindings = [effect_id, predicate_id] binds its own predicate (complete-negative), never the negated predicate/stage that the proposition introduces.
Boundary attacks: correct predicate/wrong stage → no rule; correct stage/wrong resource → no rule; unbounded interval → allowed (free string); incomplete source → blocked by the class table only (supports: ["NON_OCCURRENCE"] + allowed_complete_source_classes); stale read → stale_negative_policy: RETURN_STALE_EVIDENCE ✓; unspecified consistency → allowed; missing retention → allowed; request claims complete but evidence does not → the profile's timeout_is_non_occurrence: false and silence_policy: RETURN_UNKNOWN block part of this, but there is no rule mapping the completeness tokens to the evidence's actual flags. "No universal non-occurrence conclusion" is stated in prose and in the unreferenced invariants file, not in a rule.

P. V013
Reconstruction from package only: target (complete-negative, null), NEGATIVE_SCOPE, negated external-effect/effect, state_space: COMPLETE, interval: BOUND_BY_EFFECT_INTERVAL, retention: DECLARED_BY_EVIDENCE, read_semantics: COMPLETE_LEDGER_QUERY, consistency: DECLARED_BY_EVIDENCE, freshness: FRESH_AT_VERIFICATION, expected NON_OCCURRENCE_SUPPORTED.

The E13 correction direction (bind the negative claim to external-effect/effect without editing 0.1) is right and resolves the 0.1 self-contradiction. But the target is not a negative proposition: the schema wants negated_predicate_id/negated_stage at the proposition's top level, scope.{state_space, interval, retention_reference, read_semantics, consistency}, and evidence_profile_id; the catalog supplies a nested negative_scope with retention (not retention_reference), an extra freshness, and no evidence_profile_id. Validating the catalog target as a negative proposition yields 5 errors. interval: "BOUND_BY_EFFECT_INTERVAL" also names an interval that no contract computes. §19's "no universal non-occurrence" is satisfied in intent, not in mechanism.

Q. V014 / V021
V014 reconstructs in outline: target recipient-ack/recipient_acknowledged, predecessor provider-acceptance/provider_accepted, PREREQUISITE_CHAIN, later_stage_requires_new_evidence: true, partial_result: PARTIAL_EFFECT → the expected PARTIAL_EFFECT is reachable in direction, and the historical input.stages list is correctly not needed (verified: 0 occurrences of settlement_profile_id in the 0.2 catalog; the catalog carries the predecessor explicitly). Two obstacles: the target's predecessor field is not permitted by the proposition schema, and the derivation (predecessor-supported ⇒ PARTIAL) is stated only in the unreferenced invariants artefact.

V021 has the same shape plus "mismatch_policy": "PARTIAL_OR_INADMISSIBLE_BY_BOUND_RECIPIENT" — a field that appears in no schema and whose value is explicitly disjunctive ("PARTIAL or INADMISSIBLE"). The expected PARTIAL_EFFECT is therefore one of two permitted readings; why wrong-recipient acknowledgement yields PARTIAL rather than UNKNOWN/INADMISSIBLE is nowhere normative. (Wrong-recipient acknowledgement cannot settle the target: the registry requires recipient_or_counterparty and the profile's wrong_binding_policy: RETURN_INADMISSIBLE — that half is sound.)

R. Binding authority
Three authorities declare bindings, none subordinate to another, and no artifact reconciles them: the registry's per-row required_bindings/optional_bindings/not_applicable_bindings (using the accepted bindingName enum — a verified E2-correction), the profile's global identity_bindings + per-class required_bindings, and the proposition's optional binding_status. Because the profile's global set is strictly weaker than three registry rows, an artifact set can satisfy one authority and violate another with no closure detection (verified: contradictory required_bindings validate with 0 errors).

S. Settlement profiles
Both instances are substantive, not boilerplate: real evidence classes with supports/does_not_prove, temporal policy, freshness modes, corroboration minimums, completeness and negative-evidence policy, causal ladder, retry/duplicate policy, extension policy, reopening, and authority/effect orthogonality. They close the E3 gap I raised (the 0.1 instances were missing 18 of 20 required sections).

Defects: (i) both fail their declared schema on one enum value (BLOCK‑02); (ii) integrity.content_digest_required: false contradicts the candidate's own record schemas and package mappings, which require the digest (MINOR‑02); (iii) partial_effect.stage_settlement: PREREQUISITE_CHAIN is a single global value that contradicts the registry's per-row INDEPENDENT_WHEN_BOUND (resource-created) and ATOMIC_ONLY (external-effect) (MAJOR‑05); (iv) the two profiles differ in only 6 paths — profile_id, purpose, description, compatible_profile_ids, one observer-trust assumption, and one allowed-combination list — so "incompatible" is carried by a single empty list plus prose.

T. Canonicalization
Blocking. All three new mappings are unresolvable: container_type: CANDIDATE_PROPOSITION_RECORD and content_target: record_without_integrity_content_digest do not exist in the package-pinned canonicalization profile document, which declares exactly three container types and content_target: "content" on all 49 mappings, with included_fields: ["content"] and excluded_fields: []. Separately, both new proposition schemas pin integrity.canonicalization to urn:moirae:accord-02r4:canonicalization:rfc8785-jcs:0.1 — a profile that appears in no effective inventory (0.1 lists only the 02r5 profile; 0.2 inherits that and adds none), while the package's own mapping declares 02r5. Consequence: digest serialization for the two new integrity-bearing record types is implementation-selected, and their required digests cannot be computed deterministically — the exact failure §27 asks about. The catalog mapping is also unresolvable: EXPERIMENT_RECORD_ENTRY exists, but no mapping carries the new schema_id/record_type tuple.

U. Rule / source compatibility
Rules (MAJOR‑08): the rule registries contain zero occurrences of negative_scope, proposition_kind, GENERIC_OCCURRENCE, PREDICATE_APPLICABILITY_PROFILE, evidence_capability, predicate-applicability or 0.2, yet the package pins active_validation_rules: 82 and E4 changes none. The new normative behaviour (unknown tuple ⇒ ?, kind mismatch ⇒ ?, negative completeness ⇒ ?, predecessor coupling ⇒ ?) has no rule that can express or enforce it. The unchanged-82 claim cannot be sustained.
Source-schema pairs: the 13 accepted pairs cover TASK_STATE, ATTEMPT, EXECUTOR_STATE, ADMISSION_STATE, DELEGATE_REPORT, PROVIDER_STATE_READ, RECONCILIATION_RESULT, CLASSIFIER_FEATURE, TRUST_ROOT_PROFILE, DETACHED_EVIDENCE, PORTABLE_BUNDLE, AUTHORITY_PROFILE, SETTLEMENT_PROFILE. None of the new records (negative_scope_proposition, SETTLEMENT_VECTOR_CATALOG, PREDICATE_APPLICABILITY_PROFILE, effect_proposition) is a source record, so 13 unchanged is coherent — the new types are specification/bundle contracts. Documented as such.
Two related changes are not listed as decisions: effect_proposition's digest_policy moves OPTIONAL → REQUIRED, and its allowed_bundle_types silently widens to include SCORER_BUNDLE (MINOR‑03).
V. Fail-closed semantics
Condition	Deterministic result derivable from package 0.2?
Unknown predicate URN	No — no row, but no declared outcome (UNKNOWN_PREDICATE occurs 0×; the registry declares no unknown-tuple policy)
Valid predicate, wrong stage	No — same gap
Undeclared pair / unsupported proposition type	No — no vocabulary
Unsupported predicate (resource-visible)	Partly — support_status: UNSUPPORTED + unsupported_reason are declared, but no result value
Absent/wrong required binding	Yes at the profile level — wrong_binding_policy: RETURN_INADMISSIBLE; but conflict with registry/profile sets (MAJOR‑03)
Versionless profile reference	Yes — FAIL_VALIDATION, and this is fatal for all 23 vectors (BLOCK‑05)
Superseded (0.1) profile reference	Yes — rejected per the candidate's own audit; also fatal for the inherited references
W. Positive usefulness
Expressible and supportable in principle: generic occurrence (§K, blocked by dangling capability), stage-specific occurrence (registry rows + profile classes), corroborated occurrence (corroboration.minimum_distinct_observers: 2, require_same_effect_and_predicate: true), partial effect (registry edge + profile policy, once the composition rule is normative), complete negative (class table + completeness policy). A package that merely made everything UNKNOWN would fail; this candidate does not do that — the 23 expected headline outcomes are all reachable in direction. The problem is not over-conservatism but unreachable derivation.

X. Normative invariants
Invariant	Machine-readable mechanism?
Renaming / no lexical fallback	Yes — registry key is the URN tuple; but the 0.1 lexical applicability profile survives (BLOCK‑06)
Evidence permutation deterministic	Not addressed by any 0.2 artifact; digest mapping unresolvable (BLOCK‑04)
Adding inadmissible evidence never strengthens	Profile does_not_prove per class — partial
Removing evidence never strengthens	Not addressed
Replaying evidence	retry_and_duplicates.same_artifact_policy: DO_NOT_COUNT_TWICE — yes
Earlier/later-stage isolation	Registry later_stage_policy + profile later_stage_requires_new_evidence — yes in direction, but the two disagree (MAJOR‑05)
Sufficient evidence ⇒ positive conclusion	Class table + registry bindings — partial (binding authority conflict)
Generic/stage non-entailment	Prose only (draft + unreferenced invariants); 0 ENTAIL tokens
PARTIAL_EFFECT preconditions	Unreferenced artifact only
Negative-scope non-universality	Prose + unreferenced artifact; no rule
Y. Phase-I new semantic decisions (vs the provenance record)
The provenance record lists 8 authorized decisions. Present in the machine-readable contracts but absent from that record: (1) replacing 11 of 13 accepted expectation axes and dropping all 31 prohibitions from the 0.2 expectation contract; (2) a new digest regime (new content-target token, 02r4 pin, OPTIONAL→REQUIRED for effect_proposition); (3) widening effect_proposition to SCORER_BUNDLE; (4) per-predicate stage_settlement/later_stage_policy with vocabularies outside the accepted enums, including a new NOT_APPLICABLE stage-settlement value; (5) support_status as a registry-level semantic; (6) a one-value semantic_status enum plus an open expected object; (7) the location of binding authority (registry vs profile vs proposition); (8) expectation-shaped fields inside targets (mismatch_policy, causal_attribution); (9) removal of compatibility_group and its replacement by compatible_profile_ids as the incompatibility derivation. Items 2, 3 and 9 are hidden new semantics with security- or integrity-relevant effect.

Z. Minimality
Could any addition be removed while keeping all 23 targets deterministic? The five schema additions are all load-bearing except the vector-catalog schema, which adds no constraint the catalog enforces (its target shape is unused by the proposition schemas and it fails on the catalogue's own extra key). The registry is essential. The two profile replacements are essential (0.1 has no stage policy) but are currently invalid. Nothing else can be dropped without losing the target model.

What is still missing, forcing an implementer to invent behaviour? (i) a versioned vector→profile binding; (ii) a fail-closed outcome vocabulary for unknown/unsupported tuples; (iii) the PARTIAL_EFFECT composition rule and the no-predecessor-supported case; (iv) predecessor↔effect coupling; (v) the class→predicate evidence-capability composition; (vi) negative-scope field semantics and completeness mapping; (vii) resolvable digest mappings for the new records; (viii) retirement of the 0.1 lexical applicability profile; (ix) a closure procedure; (x) the non-entailment rule in machine-readable form. The amendment is not yet bounded to a finite determinable behaviour set.

AA. Frozen Phase-I findings
BLOCKING — E4-DEEPSEEK-BLOCK-01 catalog instance fails its own schema (target_selection_rule). -02 both profiles fail the declared accepted profile schema (CORROBORATION not in enum). -03 11/13 axes and all 31 prohibitions dropped while semantic_status is a one-value enum and expected is open — non-strengthening claim unfalsifiable. -04 all three digest mappings unresolvable; proposition schemas pin the 02r4 canonicalization profile which exists in no inventory. -05 no vector can resolve a settlement profile (versionless policy vs versionless inherited references). -06 two active predicate authorities with disjoint vocabularies; lexical alternate spelling still resolves.

MAJOR — -01 key semantics only in an unreferenced invariants artifact. -02 dangling evidence_capability_ref×6 / negative_scope_contract_ref / binding_vocabulary. -03 binding authority triplicated and contradictory. -04 stage_settlement/later_stage_policy vocabularies outside the accepted enums. -05 registry per-row stage policy contradicts the profile's single value; NO_SUCCESSOR_DECLARED contradicts a declared successor. -06 4/23 targets not expressible as their propositions. -07 negative scope fields are free strings; no mapping from the profile's tokens. -08 82 unchanged rules cannot express the new behaviour. -09 no fail-closed outcome vocabulary. -10 duplicate registry tuples undetectable. -11 no predecessor↔effect coupling.

MINOR — -01 incompatible profile is self-incompatible and differs in 6 paths; version excluded from compatibility. -02 content_digest_required: false contradicts the schemas. -03 effect_proposition digest policy OPTIONAL→REQUIRED and bundle scope widened to SCORER_BUNDLE. -04 four encodings of the stage relation. -05 path patterns allow ... -06 active_overrides vs NO_..._SUBSTITUTION. -07 kind agreement is convention. -08 V015's "authority": "INVALID" is an undeclared axis/value.

NOTE — -01 negative schema hardcodes one predicate and stage: null. -02 no proposition_id uniqueness rule. -03 target.effect_id optional with an undeclared lift. -04 the candidate's own consistency record discloses it used no standards-complete validator; my validator found two instance failures it reports as PASS. -05 base pin and 44/31/1/9/13/82 verified. -06 arm-reference count 16 vs 52 occurrences, counting definition undeclared.

AB. Phase-II comparison
Independently rediscovered design intent: typed target proposition keyed on (predicate_id, stage); generic occurrence with no successors; negative scope as a distinct proposition family; explicit predecessor edges; resource-visible fail-closed; E13 corrected without editing 0.1; the accepted bindingName vocabulary reused.

Verified corrections against E2/E3 (credit where due): E4 removed E2's profile_predicate_id dual-identity bridge (BLOCK‑06 is now only the surviving 0.1 contract, not a new alias field); E4 replaced E2's kind: POSITIVE_EFFECT and its target/recipient/attempt_attribution binding vocabulary with POSITIVE_STAGE/GENERIC_OCCURRENCE/NEGATIVE_SCOPE and the accepted bindingName enum; E4 completed the two settlement profile instances (the E3 gap); resource-visible is explicitly unsupported rather than silently absent.

Disagreements with E4's self-assessment. The draft's verdict AMENDMENT_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW and its §I "10 checks passing, zero unresolved" cannot be sustained: the catalog fails its own schema, both profiles fail theirs, §F's canonicalization claim is contradicted by the pinned profile document, §B's "explicit exact-version rewrites" of 16 arm references appear nowhere in the package, and §D's non-entailment and PARTIAL_EFFECT rules exist only as prose plus an unreferenced file. The candidate's own limitation note (no standards-complete validator) explains why §I's PASS list did not catch the two instance failures.

Compared with E1/E2/E3: none of my six blocking findings' concepts appear in those artifacts, so all six are new. The one thing I would not fault E4 for is the retention of external-effect: my independent E3 analysis also concluded that the generic proposition must survive as an explicit typed contract, and E4's GENERIC_OCCURRENCE row is the right shape.

AC. New counterexamples
CX‑1 — the candidate catalog does not validate against the candidate catalog schema.
Input: accord-02e4-settlement-vector-catalog.json vs …/schema/accord-02e4-settlement-vector-catalog.schema.json.
Observed: 1 error — target_selection_rule is not allowed (root additionalProperties: false). Removing the key → 0 errors.

CX‑2 — the candidate profiles are rejected by the schema they declare.
Input: both profiles/…-v2.json vs urn:moirae:accord-02c:schema:settlement-profile:0.1.
Observed: 1 error each — understood_evidence_dimensions/7/required_for/1 = "CORROBORATION" ∉ [OCCURRENCE, NON_OCCURRENCE, ATTRIBUTION, CAUSALITY, PARTIAL_STAGE, DUPLICATE_DIAGNOSTIC]. Replacing that single value → 0 errors.

CX‑3 — four vectors' targets are not the propositions they name.
Input: each catalog target + the vector's effect_id, validated as the proposition record it declares.
Observed: V013 5 errors (negative_scope unexpected; negated_predicate_id, negated_stage, scope, evidence_profile_id missing); V014 1 (predecessor); V017 1 (causal_attribution); V021 2 (predecessor, mismatch_policy). 19/23 valid.

CX‑4 — a duplicate registry tuple with contradictory bindings validates.
Input: temporary copy of the registry with a second recipient-ack/recipient_acknowledged row whose required_bindings omit recipient_or_counterparty.
Observed: 0 errors. Resolution becomes row-order dependent; no closure rule exists.

CX‑5 — an unresolvable digest mapping.
Input: canonicalization_applicability[0] (container_type: CANDIDATE_PROPOSITION_RECORD, content_target: record_without_integrity_content_digest) resolved against the pinned profile document.
Observed: the document declares no such container type and only content_target: "content"; and the proposition schemas pin integrity.canonicalization to the 02r4 profile id, which no effective inventory contains. Digest serialization is implementer-selected.

CX‑6 — no vector can resolve its profile.
Input: V001–V023 (settlement_profile_id in the inherited 0.1 input, versionless) under active_profile_reference_policy.versionless_policy: FAIL_VALIDATION.
Observed: VERSIONLESS_REJECTED (the candidate's own audit confirms this is the intended behaviour); the 0.1 form is SUPERSEDED_VERSION_REJECTED. Zero vectors reach settlement; V018's incompatibility cannot be derived.

CX‑7 — a lexical alternate spelling still resolves to semantics.
Input: create_resource (the 0.1 applicability profile's lexical predicate) resolved against the effective 0.2 package.
Observed: resolves via the inherited PROFILE_APPLICABILITY_PROFILE contract, which 0.2 neither replaces nor retires; the 0.2 registry validated against that inherited schema yields 7 errors, and nothing detects the coexistence.

CX‑8 — a predecessor occurrence from another effect is unconstrained. No artifact couples a predecessor's evidence to the target's effect_id (same_effect occurs only inside corroboration.require_same_effect_and_predicate); a PARTIAL_EFFECT conclusion can therefore be derived from unrelated-effect evidence.

CX‑9 — expectation contract weakened silently. 0.1: 13 axes, 31 prohibitions, 30 reason codes. 0.2: 2 axes, 0 prohibitions, 0 reason codes, with semantic_status able to hold only SEMANTICS_PRESERVED. changed_expected_outcomes: 0 is true only for the two retained axes.

CX‑10 — undeclared expectation axis/value. V015 expected.authority = "INVALID" validates (open expected) but appears in no vocabulary (the accepted token is INVALID_AUTHORITY).

CX‑11 — closure gaps (temporary copies, 0 errors each): duplicate profile addition; duplicate schema addition; ../../../etc/passwd.json in profile_path; non-existent schema_path; dangling predecessor edge; predecessor self-edge; GENERIC_OCCURRENCE row with null stage; resource-visible marked SUPPORTED without capability; registry bindings contradicting the profile.

AD. Next gate
REMEDIATE_E4_CANDIDATE_FIRST
Minimum repair set before an ACCORD-02 amendment acceptance decision: (1) make the catalog validate against its own schema and delete the unresolvable root key; (2) fix the CORROBORATION value and re-validate both profiles; (3) make the catalog's targets be the candidate propositions (or declare and schema-bind the derivation), and remove expectation-shaped fields from targets; (4) make the digest mappings resolvable — declare the new container type and content target in the canonicalization instrument, or extend the profile reference, and settle the 02r4/02r5 identifier conflict; (5) bind every vector to an exact profile version and state the resolution rule for the inherited evidence; (6) retire or explicitly subordinate the 0.1 lexical applicability profile so one predicate authority remains; (7) make the normative artefacts that carry PARTIAL_EFFECT, non-entailment, negative-scope and evidence-capability semantics referenced from the package rather than free-standing; (8) declare fail-closed outcomes for unknown/unsupported tuples; (9) add uniqueness and edge-resolution constraints (or a declared closure procedure) for the registry; (10) restore the full accepted expectation contract, including must_not_conclude, or state normatively why a weaker contract is non-strengthening; (11) couple predecessor evidence to the same effect_id; (12) add or map the rules that can express the new behaviour, and stop pinning active_validation_rules: 82 if the behaviour is not expressible.

The Option D direction itself does not need to be reopened: READY_FOR_ACCORD02_AMENDMENT_ACCEPTANCE_DECISION is achievable by repairing the above without changing the model.

AE. Worktree integrity
git status --porcelain -uall empty; HEAD 27670a6733b86c6061a8bb5c6188a266b7b3cb85; tree 684c0d44aa923947381c2724e2339c08aad5522b; main = origin/main = accord-02-accepted-v1^{} = 5a8bf1e577f71132665ece271e70e30e87df5676; tags unchanged (no 0.2 tag); git diff --name-status accord-02-accepted-v1 HEAD -- docs/accord-02 empty. All analysis scripts, temporary mutated copies and the validator venv were created under %TEMP% and deleted (accord-e4, accord-e4-venv both absent).

AF. Mutation attestation
Item	Expected	Observed
ACCORD02_0_1_MUTATED	NO	NO
E4_MUTATED	NO	NO (mutations existed only as in-memory copies in throwaway scripts)
ACCORD03_MUTATED	NO	NO
TEMPORARY_ARTIFACTS_REMAIN	NO	NO
COMMIT_CREATED	NO	NO
TAG_CREATED	NO	NO
PUSH_PERFORMED	NO	NO
MAIN_ADVANCED	NO	NO
AG. Stop
INDEPENDENT DEEPSEEK ACCORD-02E4 REVIEW COMPLETE — CANDIDATE REMEDIATION REQUIRED.

No ACCORD-03R3 work and no experiment work was begun.