Verifying frozen identity before anything else.

All identity verified. Now the high-priority §2 package-lineage question.

Significant lineage finding. Let me check whether an acceptance target is declared anywhere in the candidate.

The contract now declares explicit pointer operators. Let me independently implement it — no hard-coding — and verify all 24 records.

The catalog carries no `schema_id`/`record_type` — it cannot self-identify its mapping. Let me verify the digest anyway and quantify.

24/24 verified from the contract alone, and no hard-coded deletion in the checker. Now my MAJOR-003 retest plus the reference audit.

0 unresolved refs out of 221. Now the binding-authority retest, negative scope, rules, and stability.

Full 104-node graph confirmed. Now the mutation battery — my MAJOR-003 counterexample, the V013 matrix, and fresh attacks.

My MAJOR-003 counterexample now fails correctly. Let me fix a key name and complete the battery.

Substantial detection gaps. Let me verify the most serious ones before writing them up.

My V013 mutations used E4R1 field names — that was my error. Let me redo with the actual R2 fields.

V013 is now 13/13. Let me verify the checker's measurement basis and finish the remaining sections.

Two quick confirmations before I conclude.

Cleanup and final integrity verification.

Final reassessment complete. Repository state identical to start.

---

# ACCORD-02E4R2 — FINAL INDEPENDENT REMEDIATION REASSESSMENT

## 1. Starting state

| Item | Verified |
|---|---|
| HEAD / tree / parent | `3efed8ac…` / `d70b70d2…` / `31231b01…` ✓ exact |
| Branch | `codex/accord-02e4r2-three-assessor-closure-remediation` ✓ |
| Worktree | clean ✓ |
| `main` / `origin/main` / `accord-02-accepted-v1^{}` | all `5a8bf1e5…` ✓ |
| `accord-00` / `accord-01` tags | `ddad3092…` / `e748028d…` unchanged ✓ |
| ACCORD-03R2 | `99da6ad0…`, tree `a7aef76b…` ✓ |
| Tags | three accepted tags only — **no package-0.2 acceptance tag** ✓ |
| Accepted 0.1 | unchanged ✓ |
| E1/E2/E3/E4/E4R1 | unchanged ✓ |
| Change set | 41 files, **all additions** under `docs/accord-02e4r2/` ✓ |

## 2. Package lineage — **BLOCKING**

E4 and E4R1 both carried `package_id: urn:moirae:accord-02r5:specification-package`, `package_version: 0.2` — a clean 0.1 → 0.2 amendment inside the accepted family. **E4R2 changed it** to `urn:moirae:accord-02e4r2:specification-package`, version `0.2`.

Independently established:

- The only occurrence of `urn:moirae:accord-02r5:specification-package` anywhere in `docs/accord-02e4r2/` is the single `base_package` back-reference.
- `base_package` declares an **inheritance** relation (`EXACT_UNCHANGED_CONTRACTS`), not supersession.
- `replaces_candidate_package` points at the **E4R1 candidate**, not at the accepted package.
- Searched the package for `supersed`, `amend`, `lineage`, `becomes`, `on_acceptance`, `target_package`, `accepted_package_id` — **all absent**. The only `supersed` hits in the candidate are inside settlement-profile *reopening* semantics, unrelated to package identity.
- There is no `urn:moirae:accord-02e4r2:specification-package` version `0.1`, so "0.2" carries no lineage meaning in its own family.

A consumer resolving `urn:moirae:accord-02r5:specification-package` at version `0.2` under `CLOSED_EXACT_VERSION` with the candidate's own `fallback: FORBIDDEN` finds nothing; the accepted family still ends at 0.1. Whether this is candidate-carriage (A) or a new family (B) **is not determinable from the package**. Per the brief's instruction, ambiguity here is BLOCKING. Note also that "change package_id to the accepted family" is detected as an error by the candidate's own checker — so the new family is actively enforced, not incidental.

## 3. Full effective-package validation

Effective inventory is flattened, not overlay-based: 52 schema contracts, 32 profile contracts, 1 canonicalization profile, 9 roles, 13 source-schema pairs, 104 rules — each count independently confirmed as `len()` over the parsed artifact (checker line 399), not a literal.

**Path-base defect found.** The single flat inventory mixes two path bases with no declared root:

| Member class | Declared `schema_path` |
|---|---|
| Inherited 0.1 (44) | `schema/accord-02a-portable-record.schema.json` — relative to `docs/accord-02/` |
| R2-owned (8) | `docs/accord-02e4r2/schema/…` — relative to repo root |

`path_base`, `path_policy`, `base_path`, `package_root`, `resolution_root` are all **absent**. `reference_resolution_policy` governs *identifier* resolution only. An implementer given the package alone cannot resolve 44 of 52 schema paths. Consequently I could validate only the 8 R2-owned schemas and 4 R2-owned profiles directly; the 44 inherited members are accepted-by-inheritance and were not revalidated under R2 constraints.

## 4. Exact-reference audit

I enumerated references independently rather than trusting the claimed 228: **221 non-null normative references** across 16 reference classes (`proposition_schema_ref` 29, `canonicalization_profile_ref` 55, `settlement_profile_ref` 23, `evidence_profile_ref` 23, `canonicalization` 24, `canonicalization_ref` 23, `package_contract_ref` 13, `schema_ref` 17, `evidence_capability_ref` 5, `negative_scope_contract_ref` 2, plus singletons).

**0 unresolved.** My E4R1-MAJOR-002 is closed — both `negative_scope_contract_ref` instances now resolve. Stale-namespace scan found exactly two `accord-02e4r1` occurrences, both legitimate (`replaces_candidate_package` and the base rule-registry back-reference). 196 refs use the `{id, version}` object form. `reference_resolution_policy` declares `CODE_POINT_EXACT`, `normalization: NONE`, `fallback: FORBIDDEN`, and treats nullable slots as `NOT_DANGLING_WHEN_NULL_AND_SCHEMA_PERMITS_NULL` — semantically nullable, not merely ignored.

## 5. Canonicalization — **my E4R1-MAJOR-001 is CLOSED**

The contract now declares a `content_target_registry` with three named operators and explicit JSON Pointer semantics:

| Operator | Mode | Pointers |
|---|---|---|
| `RECORD_EXCLUDING_INTEGRITY_CONTENT_DIGEST` | EXCLUDE | `/integrity/content_digest` |
| `RECORD_EXCLUDING_INTEGRITY` | EXCLUDE | `/integrity` |
| `ENTRY_CONTENT` | INCLUDE | `/content` |

I wrote an independent implementation that derives the canonical value **only** from the mapping, with no record-type branches, then hashed with RFC 8785 + SHA-256:

- **24/24 digest-bearing records verified** (23 propositions + catalog)
- Every mapping's `content_target_id` is in the registry; every inline `content_target` matches its registry entry
- Key-reorder invariant ✓ · semantic mutation changes digest ✓ · tampered digest rejected ✓ · unknown target operator rejected ✓ · changed mapping changes result ✓

**No hidden convention:** the R2 checker reads `excluded_json_pointers` from the mapping (lines 210, 220); it does not hard-code field deletion.

One gap: the catalog record carries no `schema_id`, `schema_version` or `record_type`, so it cannot self-identify its mapping — I had to supply the schema identity out of band. The propositions self-identify correctly.

## 6. Closure-checker measurement

Counts are genuinely derived (`len(package["schema_contracts"])`, `len(rules["active_rule_ids"])`, `len(graph["node_inventory"])` …), and `active_source_schema_pairs` is cross-checked against the derived length. Binding, negative-scope, canonicalization and graph error sets are computed by real functions over parsed artifacts, not constants.

But the adversarial suite is a **fixed list of hard-coded mutations** (lines 318–347). Mutations outside that list are not covered — which is how the gaps in §7/§9/§17 below survive.

## 7. Binding authority — **my E4R1-MAJOR-003 is CLOSED**

`binding_authority_policy` now distinguishes three classes machine-readably: `proposition_bindings: REGISTRY_EXACT_TUPLE_AUTHORITATIVE`, `evidence_capability_bindings: ADDITIVE_EVIDENCE_REQUIREMENTS_ONLY`, `evidence_provenance_bindings: SEPARATE_FROM_PROPOSITION_IDENTITY` with named `provenance_fields`. Capability contracts carry separate `required_proposition_bindings` and `required_evidence_provenance_bindings` plus `does_not_prove`.

| Test | Result |
|---|---|
| **remove `recipient_or_counterparty` from recipient-ack** (my counterexample) | **DETECTED** ✓ |
| recipient marked N/A while capability needs it | DETECTED ✓ |
| generic external-effect demands recipient | DETECTED ✓ |
| generic occurrence advertises `TARGET_ACKNOWLEDGEMENT` | **NOT DETECTED** |
| `provenance_fields` corrupted to an identity binding | **NOT DETECTED** |

`E4R2-BIND-001` claims capability/registry composition "without forbidden intersection"; the last two show it is not enforced for capability-side corruption.

## 8–9. NEGATIVE_SCOPE and the V013 matrix — **fully sound**

The negative-scope schema requires 11 scope fields with `additionalProperties: false`, and V013 carries **concrete values, not enum tokens**: `not_before: 2024-01-01T00:00:00Z`, `as_of: 2024-01-01T00:00:01Z`, `retention_window_seconds: 86400`, `consistency_level: SNAPSHOT_COMPLETE`, `read_semantics: COMPLETE_LEDGER_QUERY`, `freshness_max_age_seconds: 300`, plus four explicit binding scopes and explicit `negated_predicate_id` + `negated_stage`.

**13/13 mutations detected:**

| Mutation | Detected |
|---|---|
| each of 7 scope fields removed | ✓ ×7 |
| `state_space` COMPLETE → PARTIAL | ✓ |
| `read_semantics` → PARTIAL_SCAN | ✓ |
| `consistency_level` → EVENTUAL | ✓ |
| freshness 300 → 0 | ✓ |
| `as_of` before `not_before` (unbounded) | ✓ |
| retention 86400 → 0 | ✓ |
| negated predicate / stage changed | ✓ ✓ |

*Correction to my own working:* my first V013 pass used E4R1 field names (`interval`, `retention_reference`, `consistency`) which no longer exist, so those pops were no-ops. Re-run with the real R2 names, every case fails correctly. **Two independent implementations could not disagree on V013.**

## 10–11. Rule inventory and executability

**82 base + 15 E4R1 + 7 E4R2 = 104 confirmed** — no duplicates, no collisions with base, declared count matches, no missing dependency targets. `node_inventory` is a list of exactly the 104 active rule IDs: set equality with the rule inventory in both directions, 0 edges with unresolved endpoints. **Full 104-node graph, not partial.**

The 7 new E4R2 rules each carry a real operator, failure code and dependency set, and each maps to a three-assessor finding (`REF`, `CANON`, `BIND`, `NEG`, `GRAPH`, `PROFILE`, `CLOSE`). Not metadata rows.

**Executability gap:** several rules state obligations the certifier does not evaluate — see §17. `E4R2-GRAPH-001`, `E4R2-CANON-001` and `E4R2-BIND-001` each have a stated condition that a fresh implementation would check and the certifier does not.

## 12. `evidence_profile_ref` — **MAJOR**

It is normatively load-bearing in exactly one place: **V018** has `settlement_profile_ref = conservative-v1` and `evidence_profile_ref = incompatible-v1`, and its expected result is `profile_compatibility: INCOMPATIBLE` / `overall: PROFILE_INCOMPATIBLE`. The other 22 vectors have identical refs.

Yet the package defines no policy for what each ref controls — no `evidence_profile_policy`, no "validation view" definition anywhere in the candidate. Worse, the only role vocabulary token present is `evidence_profile_role: "SAME_PROFILE_EVIDENCE_VIEW"`, asserted on **all 23 vectors including V018**, where the two profiles demonstrably differ. The declared role contradicts the one vector where the field matters.

## 13. Profile digest scope

Coherent. Profile `integrity` governs **evidence-artifact** mechanisms (`accepted_mechanisms`, `unsupported_mechanism_policy`, `signature_scope`), which is a different axis from record-schema digest requirements. `E4R2-PROFILE-001` states the scoping explicitly: *"digest optionality is scoped to evidence artifacts and never weakens required schema digest policy."* No genuine conflict.

## 14. PARTIAL_EFFECT

`partial_effect_policy` is explicit and complete: `supported_predecessor → POTENTIAL_PARTIAL_EFFECT`, `no_supported_predecessor → NOT_PARTIAL_EFFECT`, `atomic_only → NOT_PARTIAL_EFFECT`, `empty_predecessors → NOT_PARTIAL_EFFECT`, `incompatible_or_inadmissible → INADMISSIBLE_OR_UNKNOWN`, `same_effect_required: true`, `later_stage_requires_new_evidence: true`. Reachable only for `recipient-ack`; unreachable for GENERIC_OCCURRENCE, NEGATIVE_SCOPE, ATOMIC_ONLY and all zero-predecessor rows. No prose inference required.

## 15. Incompatible-profile semantics

Sound. `incompatible-v1` has `compatible_profile_ids: []` but also `self_identity_policy: SELF_IS_NOT_A_COUNTERPART` and an explicit pairwise-evaluation policy, so the empty list does not make the profile invalid — it makes it compatible with nothing, which is its purpose.

## 16. Full expectation stability

**23/23 full semantic equality across all 13 accepted axes, 0 divergences**, independently recomputed against accepted 0.1. All **31/31** `must_not_conclude` entries preserved. Vector-ID sets identical.

## 17. Fresh adversarial mutations

27 independent mutations beyond the published 20. **Detected 20, not detected 7:**

| Mutation | Detected |
|---|---|
| remove recipient binding / N/A conflict / generic demands recipient | ✓ ✓ ✓ |
| all 13 V013 scope mutations | ✓ ×13 |
| package_id changed to accepted family | ✓ |
| canonicalization registry operator deleted | ✓ |
| graph node removed | ✓ |
| `evidence_profile_ref` → incompatible profile | ✓ |
| `reason_codes` altered · `must_not_conclude` dropped | ✓ ✓ |
| proposition `schema_id` → stale E4R1 namespace | ✓ |
| vector target predicate uppercased | ✓ |
| **base_package sha256 → zeros** | **✗** |
| **rule `depends_on` → `NO-SUCH-RULE`** | **✗** |
| **dependency cycle injected in rules file** | **✗** |
| **`content_target_id` vs inline target disagree** | **✗** |
| **generic occurrence advertises TARGET_ACKNOWLEDGEMENT** | **✗** |
| **`provenance_fields` corrupted** | **✗** |
| **predecessor edge → UNSUPPORTED `resource-visible`** | **✗** |
| **registry `entries[0]` predicate uppercased** | **✗** |

Root cause for the graph pair: the checker validates `graph["edges"]`, while `candidate_additions[].depends_on` is a **second, unvalidated source of dependency truth**. The two are never reconciled.

## Findings

| ID | Severity | Finding |
|---|---|---|
| `E4R2-CLAUDE-BLOCK-001` | BLOCKING | Package identity moved to a new family (`accord-02e4r2`) with no supersession, amendment or acceptance-target statement. Whether 0.2 amends accepted 0.1 or merely references it is undeterminable from the package. Regression from E4/E4R1, which both used the accepted family |
| `E4R2-CLAUDE-MAJOR-001` | MAJOR | `base_package.sha256` is never verified — replacing it with zeros passes closure. The base pin is decorative |
| `E4R2-CLAUDE-MAJOR-002` | MAJOR | Two unreconciled dependency-truth sources. A `depends_on` pointing at a nonexistent rule, and an injected cycle, both pass — contradicting `E4R2-GRAPH-001` and `acyclicity.result: COMPUTED_BY_CLOSURE_CHECKER` |
| `E4R2-CLAUDE-MAJOR-003` | MAJOR | `evidence_profile_ref` is normatively load-bearing (V018 → `PROFILE_INCOMPATIBLE`) but its semantics are undefined, and `evidence_profile_role: SAME_PROFILE_EVIDENCE_VIEW` is asserted on V018 where the profiles differ |
| `E4R2-CLAUDE-MAJOR-004` | MAJOR | Flat inventory mixes two path bases (44 inherited relative to `docs/accord-02/`, 8 R2-owned relative to repo root) with no declared resolution root; 44 of 52 schema paths unresolvable from the package alone |
| `E4R2-CLAUDE-MAJOR-005` | MAJOR | `content_target_id` disagreeing with the inline `content_target` passes — contradicting `E4R2-CANON-001` |
| `E4R2-CLAUDE-MAJOR-006` | MAJOR | Capability-side binding corruption undetected: advertising `TARGET_ACKNOWLEDGEMENT` for generic occurrence, and rewriting `provenance_fields` to an identity binding — contradicting `E4R2-BIND-001` |
| `E4R2-CLAUDE-MAJOR-007` | MAJOR | Registry-side corruption undetected: uppercasing a registry tuple (orphaning 18 vectors) and repointing a predecessor edge at the UNSUPPORTED `resource-visible` row both pass |
| `E4R2-CLAUDE-MINOR-001` | MINOR | The vector catalog carries no `schema_id`/`schema_version`/`record_type`, so it cannot self-identify its canonicalization mapping; propositions do |
| `E4R2-CLAUDE-MINOR-002` | MINOR | The checker's adversarial suite is a fixed hard-coded list; mutations outside it are uncovered, which is the mechanism behind MAJOR-001..007 |
| `E4R2-CLAUDE-NOTE-001` | NOTE | Identity, ancestry, protected refs, accepted 0.1 and E1–E4R1 immutability all independently verified exact |
| `E4R2-CLAUDE-NOTE-002` | NOTE | **E4R1-MAJOR-001 CLOSED** — 24/24 digests independently reproduced from the contract alone; named operators; no hidden deletion convention |
| `E4R2-CLAUDE-NOTE-003` | NOTE | **E4R1-MAJOR-002 CLOSED** — 221 references independently enumerated, 0 unresolved |
| `E4R2-CLAUDE-NOTE-004` | NOTE | **E4R1-MAJOR-003 CLOSED** — the binding counterexample now fails correctly |
| `E4R2-CLAUDE-NOTE-005` | NOTE | 23/23 full expectation stability on all 13 axes; 31/31 prohibitions |
| `E4R2-CLAUDE-NOTE-006` | NOTE | 104-rule inventory and full 104-node graph confirmed |
| `E4R2-CLAUDE-NOTE-007` | NOTE | V013 is 13/13 mutation-guarded with concrete scope values — no implementation disagreement possible |
| `E4R2-CLAUDE-NOTE-008` | NOTE | No checker crashes across 27 mutations; the E4R1 profile-version robustness concern appears resolved, though not separately retested |

## Verdict

**`FINAL_REMEDIATION_INCOMPLETE`**

## Gate

**`REMEDIATE_E4R2_FIRST`**

## Worktree attestation

Temporary venv, two mutation workspaces and all scripts deleted; bytecode caches removed. `git status --porcelain` empty. HEAD, tree, parent, branch and all protected refs unchanged. Accepted 0.1 and E1–E4R1 unchanged. No stash. Nothing written inside the repository.

| Check | Result |
|---|---|
| `ACCORD02_ACCEPTED_MUTATED` / `E1`–`E4R1_MUTATED` / `ACCORD03R2_MUTATED` | **NO** |
| `COMMIT_CREATED` / `TAG_CREATED` / `PUSH_PERFORMED` / `MAIN_ADVANCED` | **NO** |
| `TEMPORARY_ARTIFACTS_REMAIN` | **NO** |

---

**What changed and what didn't.** All three of my E4R1 MAJORs are genuinely closed, and closed well — the canonicalization contract now names its operators and I reproduced all 24 digests from the contract with no record-type knowledge; every one of 221 references resolves; my binding counterexample fails correctly. V013 went from a construct I could not independently pin down to one that survives thirteen distinct attacks on concrete values. That is real progress.

The pattern that persists is the one I named last round, one level up. E4R1 declared obligations its checker did not enforce; E4R2 turned those obligations into seven numbered rules — and then enforced them with a hard-coded mutation list rather than from the rules themselves. So `E4R2-GRAPH-001` says every dependency target resolves while an injected cycle passes; `E4R2-CANON-001` says every digest form resolves a declared target while a self-contradictory mapping passes; `E4R2-BIND-001` says bindings compose without forbidden intersection while a corrupted capability passes. Seven rules, three unenforced.

And the new BLOCKING finding is a fresh instance of the same habit: the package now asserts closure with more machinery than ever, while quietly changing the one identifier that tells a future consumer what it is amending. The remedy for both is the same and it is small — derive the checks from the declared rules rather than from a list, and state in one field what package 0.2 becomes on acceptance.

`ACCORD-02E4R2 CLAUDE FINAL REASSESSMENT COMPLETE — FURTHER REMEDIATION REQUIRED.`