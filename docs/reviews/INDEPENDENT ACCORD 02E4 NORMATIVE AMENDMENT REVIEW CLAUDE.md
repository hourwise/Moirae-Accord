Review complete. Repository state identical to start.

---

# ACCORD-02E4 — INDEPENDENT NORMATIVE AMENDMENT REVIEW

## A. Starting state

| Item | Verified |
|---|---|
| HEAD / tree / parent | `27670a67…` / `684c0d44…` / `f8bdc730…` ✓ all exact |
| Branch | `codex/accord-02e4-normative-settlement-amendment` ✓ |
| Worktree at start | clean ✓ |
| `main` / `origin/main` | both `5a8bf1e5…` ✓ |
| Tags present | `accord-00/01/02-accepted-v1` only — **no package-0.2 acceptance tag** ✓ |
| ACCORD-03R2 | `99da6ad0…` unchanged ✓ |
| First-parent chain | `5a8bf1e5 → 430c7e72 → 8128941a → f8bdc730 → 27670a67` ✓ exact, no rewrite |
| Change set | 17 files, **all additions**, all under `docs/accord-02e4/` ✓ |

## B. Verdict

**`AMENDMENT_REQUIRES_REMEDIATION`**

The semantic design is faithfully and — in several places — better-than-specified implemented. The defects are all in the package/artifact layer: one blocking gap (no declared fail-closed behaviour), two real schema failures, and a closure consequence that silently removes the accepted conformance expectations from the package.

## C. Accepted-0.1 integrity

`git diff --name-status accord-02-accepted-v1 HEAD -- docs/accord-02` is empty. Package 0.1 is byte-identical and remains authoritative. E1/E2/E3 trees unchanged (`90bbb503`, `c7dcd93b`, `ae63c72e`). E4 is strictly additive.

## D. Candidate-package integrity

`base_package.package_sha256` = `sha-256:fbb9c3cc…be105c` — **independently recomputed and matches**. Declared base counts (44 schemas, 31 profiles) match the actual accepted package. `inheritance_policy: EXACT_UNCHANGED_CONTRACTS`, `contract_policy: CLOSED_EXACT_VERSION`, `no_fallback` declared. Effective inventory 49/32 is arithmetically consistent (44+5, 31+1 with 2 in-place replacements).

## E. Canonical predicate/stage review

**One identity system, cleanly.** `resolution_key: ["predicate_id","stage"]`; `canonical_vocabulary: CANONICAL_C_VECTOR_URNS`; invariants declare `dual_profile_predicate_id: false` and `lexical_fallback: false`. I found **no** `profile_predicate_id`, display alias, local name, or normalized identifier anywhere in the candidate. The 0.1 applicability profile's disjoint vocabulary (`create_resource`/`deliver_item`/`provider_acceptance`) is superseded by a declared replacement rather than aliased.

**Binding vocabulary is consistent** (§22). All nine candidate binding names — `effect_id, predicate_id, stage, action, resource, recipient_or_counterparty, provider, external_identifier, attempt_id` — are a strict subset of the accepted `accord-02c-settlement-profile.schema.json` `$defs.bindingName` enum. The candidate correctly aligned to the settlement-profile vocabulary rather than the R3 `dimensions` list. One citation defect — see `E4-CLAUDE-MINOR-001`.

**Exact resolution (§8):** the registry data admits only exact tuple match, and the package declares `substitution_policy: NO_LATEST_NO_CURRENT_NO_COMPATIBLE_SUBSTITUTION`. But neither the registry schema nor the draft states case-sensitivity or forbids normalization — `case`, `normali`, `fold`, `trim` appear nowhere. See `E4-CLAUDE-MAJOR-001`.

## F. 23-vector resolution

**23 / 23 resolve exactly once. 0 unresolved. 0 ambiguous.** Every `target.proposition_kind` matches its registry row's `kind`.

| Tuple | n |
|---|---|
| `external-effect` / `effect` / GENERIC_OCCURRENCE | 18 |
| `recipient-ack` / `recipient_acknowledged` / POSITIVE_STAGE | 2 |
| `resource-created` / `resource_created` / POSITIVE_STAGE | 2 |
| `complete-negative` / `null` / NEGATIVE_SCOPE | 1 |

`target_selection_rule` explicitly forbids inference from evidence class, vector identifier, input order, lexical similarity, or observed state. This is the core of the amendment and it is correct.

## G. Expected-outcome stability

The two carried axes match **23/23 with zero divergence**. But the candidate catalog carries only 2 of the accepted 13 expected axes:

| Axis | Carried |
|---|---|
| `overall`, `occurrence` | 23/23 |
| `attribution`, `causality`, `completeness`, `sufficiency`, `freshness`, `duplication`, `finality`, `authority_status`, `profile_compatibility`, `reason_codes`, **`must_not_conclude`** | **0/23** |

`accord-02e4-expected-outcome-stability.json` asserts `semantics_preserved: 23`, `changed_expected_outcomes: 0`, and check `E4-CONS-010` claims *"Candidate outcome summaries preserve all 23 accepted expected outcome categories: PASS"* — without disclosing anywhere which axes were compared. §10's required verification (attribution, sufficiency, completeness, duplication, `must_not_conclude`, staged conclusions) **cannot be performed from the candidate artifacts.** Not falsified — unverifiable. See `E4-CLAUDE-MAJOR-002`.

## H. Generic occurrence

Adversarially tested and **sound**:

- `kind: GENERIC_OCCURRENCE`, `stage: "effect"` — a non-empty string, coherent with the accepted `$defs.predicate.stage` requirement
- `predecessor_edges: []`, `stage_settlement: ATOMIC_ONLY`, `later_stage_policy: NO_SUCCESSOR_DECLARED` ⇒ `PARTIAL_EFFECT` structurally unreachable
- meaning declared as *"Only the named logical external effect occurred"*; `successors: []`

**Binding set is sufficient and not over-demanding.** Tested all 18 accepted vectors against `required: [effect_id, predicate_id, stage]` / `not_applicable: [recipient_or_counterparty]`: **zero** accepted vectors supply a recipient (no NOT_APPLICABLE conflict), and **zero** lack a required binding. Confirmed none of the 18 ever expects `PARTIAL_EFFECT`, so atomic treatment is correct. This was the genuinely new normative choice and it survives scrutiny.

## I. Positive-stage predicates

| Predicate | Stage | Bindings | Predecessors | Assessment |
|---|---|---|---|---|
| `resource-created` | `resource_created` | resource REQUIRED, recipient NOT_APPLICABLE | none | coherent; V017/V022 `OCCURRENCE_SUPPORTED` preserved ✓ |
| `recipient-ack` | `recipient_acknowledged` | **recipient REQUIRED** | `provider-acceptance/provider_accepted` ✓ | correct — see M |
| `provider-acceptance` | `provider_accepted` | provider REQUIRED | none | coherent; cannot prove later stages (no successor edge exists; `later_stage_policy: NO_SUCCESSOR_DECLARED`) |

**§15 honesty check:** `provider-acceptance` has no directly-targeted accepted vector. The candidate does **not** claim conformance coverage for it — `E4-CONS-002` counts 22 positive targets, correctly excluding it. No false coverage claim found.

## J. PARTIAL_EFFECT

Truth conditions in `accord-02e4-normative-settlement-invariants.json` are **equivalent to the reviewed design**: `selected_target_stage_not_supported`, `declared_predecessor_supported`, `predecessor_policy_satisfied`, `later_stage_evidence_required`, `evidence_admissible_and_compatible`; `forbidden_without: [DECLARED_PREDECESSOR, SUPPORTED_PREDECESSOR, LATER_STAGE_QUERY]`; `atomic_only: UNREACHABLE`.

Reachability computed per registry row:

| Row | PARTIAL reachable |
|---|---|
| `recipient-ack` / `recipient_acknowledged` (PREREQUISITE_CHAIN, 1 predecessor) | **yes** |
| `external-effect` (GENERIC_OCCURRENCE, ATOMIC_ONLY) | no |
| `resource-created`, `provider-acceptance` (0 predecessors) | no |
| `complete-negative` (NEGATIVE_SCOPE, NOT_APPLICABLE) | no |
| `resource-visible` (ATOMIC_ONLY, UNSUPPORTED) | no |

All five §17 negative conditions hold. I could not construct a configuration where `PARTIAL_EFFECT` is emitted incorrectly.

## K. NEGATIVE_SCOPE

The highest-risk construct, and it is well-built. The schema requires `negated_predicate_id` **and** `negated_stage` — the negation target is explicit, not inferred. Also required: `effect_id`, `proposition_kind` const-pinned, `predicate_id` const-pinned, `stage: null` (consistent with the registry marker, explained in `candidate_notes.negative_stage_marker`), `evidence_profile_id`, `integrity`, and `scope` with required `state_space`, `interval`, `retention_reference`, `read_semantics`, `consistency`.

Freshness and source-class are carried by the profile's `complete_query_requirements` (10 entries including `FRESH_AT_VERIFICATION`, `CONSISTENCY_DECLARED`, `NO_CONTRADICTORY_EVIDENCE`) and `allowed_complete_source_classes`. That placement is correct — completeness belongs to the read artifact. No field is missing; no field is invented.

## L. V013

Candidate V013 binds to `complete-negative` / `null` / NEGATIVE_SCOPE with an explicit negated predicate/stage. Provenance records this honestly: *"E13 is corrected by binding its negative proposition to external-effect/effect without modifying accepted 0.1"* — a **new normative decision**, correctly classified, and confined to 0.2. Profile declares `non_occurrence_scope: PROFILE_BOUND_SCOPE_ONLY` and `timeout_is_non_occurrence: false`; invariants declare `silence_timeout_stale_or_incomplete_read: NOT_SUFFICIENT`. Universal absence remains excluded by construction.

## M. V014 / V021

**Derivable from the candidate package alone, without naming intuition.** The chain is fully mechanical: target tuple `(recipient-ack, recipient_acknowledged)` → registry row → `kind: POSITIVE_STAGE`, `stage_settlement: PREREQUISITE_CHAIN`, `predecessor_edges: [(provider-acceptance, provider_accepted)]`, `later_stage_policy: NEW_EVIDENCE_REQUIRED`, `required_bindings` include `recipient_or_counterparty` → acceptance evidence supports the predecessor but not the target → `PARTIAL_EFFECT`. V021's recipient mismatch is caught by the REQUIRED recipient binding. No spelling is consulted at any step.

**V014's `input.stages` is now redundant**, as recommended — the predecessor edge carries the ordering.

## N. Stage predecessor semantics

Independently computed: **no dangling predecessor targets, no cycles**, one edge total. `stage_ordering_policy: EXPLICIT_PREDECESSOR_EDGES_ONLY`, `stage_ordering_scope: PROFILE_AND_PREDICATE_FAMILY`, `global_total_order: false`, `empty_predecessors: NO_PARTIAL_EFFECT`. No stage-number comparison, no lexical ordering, no implicit transitivity. Deterministic and acyclic. Exactly the reviewed design.

## O. Binding authority

One source of truth, no contradiction found. The registry supplies required/optional/not-applicable per tuple; the settlement profiles supply policy (`accepted_evidence_classes[].required_bindings`) using the same accepted `bindingName` vocabulary. Spot-checked `external-effect`, `resource-created`, `recipient-ack` — registry and profile agree.

## P. Settlement profiles

**DeepSeek's completeness finding is addressed.** Both candidate profiles carry **20/20** required sections. Content is substantive, not placeholder: `negative_evidence` declares 10 explicit complete-query requirements; `corroboration` declares `minimum_distinct_observers: 2`, `NO_AUTOMATIC_INDEPENDENCE`, `DO_NOT_COUNT_TWICE`; `accepted_evidence_classes` gives per-class `supports` / `does_not_prove` / `required_bindings` / `minimum_integrity`; `partial_effect` declares `stage_order_field: stage_predecessors`.

**But both fail the accepted schema.** `understood_evidence_dimensions[7].required_for[1] = "CORROBORATION"` is not a member of the accepted enum `["OCCURRENCE","NON_OCCURRENCE","ATTRIBUTION","CAUSALITY","PARTIAL_STAGE","DUPLICATE_D…"]`. Package 0.2 declares these profiles under `schema_id: urn:moirae:accord-02c:schema:settlement-profile:0.1`, so they must validate against it. See `E4-CLAUDE-MAJOR-003`.

**Versioning (§24) is correct:** both are `profile_version: 0.2`, distinct files under `profiles/`, declared as `profile_contract_replacements`, with `active_profile_reference_policy.active_overrides` recording old→new. No in-place mutation.

## Q. Package 0.2 closure

Base pin verified. Replacements and additions enumerated. `active_profile_reference_policy` declares `missing_policy: FAIL_VALIDATION`, `versionless_policy: FAIL_VALIDATION`, and no-substitution. Profile audit: 16/16 active references resolved, 0 missing, 0 versionless, 0 duplicate. Overlay semantics (§26) are deterministic — a second implementer can compute the effective inventory exactly.

**Two closure defects:**

1. **Six dangling contract references.** Every `evidence_capability_ref` (5) and the `negative_scope_contract_ref` (1) appears *only* in the registry that cites it. No contract defines them. Their content is recoverable from the profiles' `accepted_evidence_classes`, so semantics are determinable — but under `CLOSED_EXACT_VERSION` a declared reference that resolves to nothing is a closure violation. See `E4-CLAUDE-MAJOR-004`.

2. **The accepted vector catalog drops out of the package.** The accepted base declares both settlement profiles with `profile_path: examples/accord-02c-settlement-test-vectors.json` — the file carrying the 23 vectors, their 13 expected axes and 31 `must_not_conclude` prohibitions. Package 0.2 replaces both contracts with standalone files under `profiles/`, after which **no contract in 0.2 references that file**. The candidate catalog that would replace it has its *schema* added but its *instance* declared nowhere — so it is unreachable under closed-exact-version resolution. See `E4-CLAUDE-BLOCK-001` (combined with the fail-closed gap) and `E4-CLAUDE-MAJOR-002`.

## R. Schema validation

Environment: isolated venv, CPython 3.14.0, `jsonschema 4.26.0` with `rfc3339-validator 0.1.4` + `rfc3987-syntax 1.1.0` bound explicitly to `date-time` and `uri`. This is a **standards-complete Draft 2020-12 validation**, which the candidate's own `limitations` note says was not performed.

| Check | Result |
|---|---|
| 5 new schemas vs 2020-12 metaschema | **all VALID**, all declare the 2020-12 dialect |
| `$ref` hygiene | all local `#/`, **zero external**, **zero unresolved** |
| registry vs registry schema | **VALID** |
| package 0.2 vs package schema | **VALID** |
| **vector catalog vs its own schema** | **FAIL** — `additionalProperties`: `target_selection_rule` unexpected |
| **both profiles vs accepted 0.1 profile schema** | **FAIL** — `CORROBORATION` not in `required_for` enum |

## S. Canonicalization / digests

Three explicit mappings, each with `container_type`, `schema_id`+version, `record_types`, `canonicalization_profile_id`+version, `content_target: record_without_integrity_content_digest`, `digest_algorithm: SHA-256`, `digest_field: integrity.content_digest`, and explicit `digest_optional`. No implementation-selected serialization. Both proposition schemas require `integrity`. Complete for every new integrity-bearing object.

## T. Rule / source compatibility

**E4's "no rule change" claim is well-founded.** The accepted PRED-* rules are generic over the applicability profile, not bound to 0.1's vocabulary — and `PRED-004`'s operator is literally `predicate_stage_profile_matches_proposition`, i.e. the exact-tuple rule the amendment formalises. `PRED-001` (`required_binding_not_unknown_or_na_for_positive_projection`), `PRED-002` (`not_applicable_profile_declared`) and `PRED-003` (`unknown_not_positive_binding`) all operate on the registry's `required_bindings` / `not_applicable_bindings` directly. The 82-rule inventory genuinely needs no change.

Schema additions carry correct `normative_record_types` and `allowed_bundle_types`, including `negative_scope_proposition` across all three bundle types. `active_source_schema_pairs` stays at 13; since source-schema pairs govern arm-input source records rather than proposition records, not adding one is coherent.

## U. Normative invariants

Present and substantive, but four of §31's eight are absent from the artifact: *inadmissible evidence cannot strengthen*, *removing evidence cannot strengthen*, *permutation cannot change result*, *replay cannot increase corroboration* (the last is covered in the profile as `DO_NOT_COUNT_TWICE`). The other four are present and correct. No contradiction with accepted rules found.

**§12 non-entailment asymmetry:** `positive_stage.non_entailments` lists `[OTHER_STAGE, ATTEMPT_ATTRIBUTION, CAUSALITY, AUTHORITY, EXACTLY_ONCE]`, which covers POSITIVE_STAGE → GENERIC_OCCURRENCE via `OTHER_STAGE`. But `generic_occurrence` has **no** `non_entailments` field — the reverse direction rests on the prose word *"Only"*. Determinable, unevenly encoded.

## V. Usefulness

No all-UNKNOWN retreat. All five conclusions remain reachable: strong generic occurrence (18-vector family, 6 expect `OCCURRENCE_SUPPORTED`), resource-created occurrence (V017, V022), corroboration (profile declares `minimum_distinct_observers: 2` with an operative independence policy), `PARTIAL_EFFECT` (V014, V021 via the predecessor edge), scoped `NON_OCCURRENCE_SUPPORTED` (V013 via the negative proposition). 23/23 candidate expectations match accepted on the axes carried.

## W. Minimality

| Change | Classification |
|---|---|
| Four canonical URN registry rows | **necessary** |
| `GENERIC_OCCURRENCE` kind | **necessary** — 18 of 23 vectors are unresolvable without it |
| `NEGATIVE_SCOPE` kind + negative proposition schema | **necessary** — V013 has no positive stage to bind |
| external-effect binding set | **necessary**, and minimal (3 required) |
| Non-entailment rules | **necessary** |
| Predecessor edge model | **necessary** |
| `resource-visible` UNSUPPORTED row | **reasonable but optional** — a bounded, honest deferral |
| Completed settlement profiles | **necessary** — the accepted profile rows were 4-field stubs |
| Positive proposition schema | **reasonable but optional** — the accepted 02R2 proposition already required predicate/stage/bindings |
| Vector-catalog schema + catalog | **reasonable but optional**, and currently the source of two defects |
| Package 0.2 + package schema | **necessary** for versioned carriage |

**No unrelated expansion found.** The amendment is genuinely bounded. It is slightly broader than strictly required (positive proposition schema, vector catalog), but nothing is gratuitous.

## X. Decision provenance

**Honest.** 6 clarifications, 8 new decisions, 5 explicit not-claimed. Every genuinely new choice — the typed hybrid, the `external-effect` row, the `stage: null` marker, the predecessor edge, the `resource-visible` deferral, the completed profiles, the E13 correction — is filed under `new_normative_decisions_authorized_by_e4`, not presented as accepted 0.1 fact. `status: CANDIDATE / NOT ACCEPTED` throughout. I found no misattribution.

Two consistency checks overclaim relative to what I measured: `E4-CONS-008` tests section *presence*, not schema validity (both profiles fail validation); `E4-CONS-010` says *"preserve all 23 accepted expected outcome categories"* when 2 of 13 axes are carried.

## Y. Independent implementability

**Close, but not yet.** A second implementer can derive: exact tuple resolution, the three kinds, all bindings, the predecessor relation, `PARTIAL_EFFECT` truth conditions, `OCCURRENCE_SUPPORTED` scope, the negative proposition contract, and canonicalization — all from package 0.2 alone.

Three places the answer is still **no**:

1. **What happens on an unresolvable tuple.** `support_status` has only `SUPPORTED` / `UNSUPPORTED`; nothing declares the outcome for a predicate/stage pair absent from the registry, a known predicate with a wrong stage, a missing required binding, or an unsupported proposition kind. The draft contains **zero** occurrences of "UNKNOWN" and no fail-closed statement. This is precisely the hole the `urn:` heuristic grew in.
2. **What "exact" means.** No case-sensitivity or no-normalization statement anywhere in the registry schema or draft.
3. **Which expectations are authoritative**, given that the accepted catalog leaves the package and the candidate catalog is undeclared.

## Z. Findings

| ID | Severity | Finding |
|---|---|---|
| `E4-CLAUDE-BLOCK-001` | BLOCKING | No declared fail-closed behaviour. Unknown tuple / wrong stage / undeclared pair / missing required binding / unsupported proposition kind have no specified outcome; `support_status` cannot express "unknown". An implementer must invent the rule — the exact defect class the amendment exists to close |
| `E4-CLAUDE-MAJOR-001` | MAJOR | "Exact" resolution is never defined. No case-sensitivity, no-normalization, no-trim statement in the registry schema or draft |
| `E4-CLAUDE-MAJOR-002` | MAJOR | Replacing both settlement-profile contracts removes `examples/accord-02c-settlement-test-vectors.json` from package 0.2; the replacement catalog instance is never declared as a contract. The 11 dropped expected axes and all 31 `must_not_conclude` prohibitions leave the package. `E4-CONS-010`'s preservation claim is unsubstantiated (2 of 13 axes compared, undisclosed) |
| `E4-CLAUDE-MAJOR-003` | MAJOR | Both candidate settlement profiles **fail** the accepted 0.1 profile schema they are declared against: `understood_evidence_dimensions[7].required_for[1] = "CORROBORATION"` is outside the accepted enum |
| `E4-CLAUDE-MAJOR-004` | MAJOR | Six declared contract references dangle — five `evidence_capability_ref` and one `negative_scope_contract_ref` resolve to nothing under `CLOSED_EXACT_VERSION`. Semantics are recoverable from the profiles, so this is carriage not meaning |
| `E4-CLAUDE-MAJOR-005` | MAJOR | The candidate vector catalog **fails its own schema**: `target_selection_rule` violates `additionalProperties: false` |
| `E4-CLAUDE-MINOR-001` | MINOR | `binding_vocabulary: urn:moirae:accord-02c:binding-name-vocabulary:0.1` is a non-existent identifier; the real vocabulary is `accord-02c-settlement-profile.schema.json#/$defs/bindingName`. Content correct, citation unresolvable |
| `E4-CLAUDE-MINOR-002` | MINOR | Non-entailment encoded asymmetrically — `positive_stage.non_entailments` is explicit; `generic_occurrence` relies on the prose "Only" |
| `E4-CLAUDE-MINOR-003` | MINOR | One vector uses expected key `authority`; the accepted catalog uses `authority_status` |
| `E4-CLAUDE-MINOR-004` | MINOR | Four of §31's eight invariants absent from the invariants artifact (inadmissible-cannot-strengthen, removal-cannot-strengthen, permutation-invariance, replay-cannot-corroborate) |
| `E4-CLAUDE-MINOR-005` | MINOR | `E4-CONS-008` tests section presence, not schema validity, and reports PASS for profiles that fail validation |
| `E4-CLAUDE-NOTE-001` | NOTE | Identity, ancestry, protected refs, 0.1 immutability and base digest all independently verified exact |
| `E4-CLAUDE-NOTE-002` | NOTE | 23/23 targets resolve exactly once; 0 unresolved, 0 ambiguous; kinds consistent throughout |
| `E4-CLAUDE-NOTE-003` | NOTE | Predecessor graph acyclic, no dangling targets, no global order — exactly the reviewed design |
| `E4-CLAUDE-NOTE-004` | NOTE | `PARTIAL_EFFECT` reachable only for `recipient-ack`; unreachable for generic, negative, atomic and zero-predecessor rows |
| `E4-CLAUDE-NOTE-005` | NOTE | external-effect binding set adversarially tested against all 18 vectors — sufficient, not over- or under-demanding |
| `E4-CLAUDE-NOTE-006` | NOTE | Request-level completeness laundering is structurally gone: no `request`/`caller`/`negative_query` concept in the candidate profiles; scope is required on the proposition |
| `E4-CLAUDE-NOTE-007` | NOTE | "No rule change" is well-founded; `PRED-004` already encodes exact predicate/stage matching |
| `E4-CLAUDE-NOTE-008` | NOTE | Decision provenance is honest; no new decision presented as accepted fact |
| `E4-CLAUDE-NOTE-009` | NOTE | Profiles are substantive, not tautological; 20/20 required sections present, closing the DeepSeek completeness finding |

## AA. Next-gate recommendation

**`REMEDIATE_E4_CANDIDATE_FIRST`**

All six defects are bounded and repairable inside the existing design — none requires reopening the settlement model. The semantic core is sound; what fails is carriage, validation and the one missing rule that the whole exercise was meant to supply.

## AB. Worktree integrity

Temporary validation venv and all scripts deleted; bytecode caches removed. `git status --porcelain` empty. HEAD, tree, parent, branch and all protected refs unchanged. E1/E2/E3 trees unchanged. No stash entries. Nothing written inside the repository.

## AC. Mutation attestation

| Check | Result |
|---|---|
| `ACCORD02_0_1_MUTATED` | **NO** |
| `E1_MUTATED` | **NO** |
| `E2_MUTATED` | **NO** |
| `E3_MUTATED` | **NO** |
| `E4_MUTATED` | **NO** |
| `ACCORD03_MUTATED` | **NO** |
| `COMMIT_CREATED` | **NO** |
| `TAG_CREATED` | **NO** |
| `PUSH_PERFORMED` | **NO** |
| `MAIN_ADVANCED` | **NO** |

## AD. Stop

`ACCORD-02E4 INDEPENDENT CLAUDE REVIEW COMPLETE — CANDIDATE REMEDIATION REQUIRED.`

---

**The one thing worth acting on first:** E4 gets the hard part right. The typed hybrid is faithfully implemented, 23/23 targets resolve exactly, the predecessor model is minimal and acyclic, `PARTIAL_EFFECT` is reachable exactly where it should be, and the `external-effect` binding choice survives adversarial testing against all 18 vectors. The provenance is honest about what is new.

What it omits is the other half of the E3 design: the fail-closed rule. The candidate says with great precision what happens when a tuple *resolves*, and says nothing at all about what happens when it does not. That silence is the same shape as the hole that produced `endswith("incompatible-v1")`, then `endswith("recipient-ack")`, then `startswith("urn:")` — three rounds of the same defect, each time an implementer filling an unspecified resolution failure with a string test. Adding five sentences — unknown predicate, unknown stage, undeclared pair, missing binding, unsupported kind, each → a named non-positive outcome, plus one sentence defining "exact" as byte-identical — would close the class permanently. Everything else in this report is bookkeeping by comparison.