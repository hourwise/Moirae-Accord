# ACCORD-02E3 — Target Stage & Predicate Semantics Review

Status: **CANDIDATE / ANALYSIS — NOT ACCEPTED**  
Verdict: **PARTIAL_DESIGN_ONLY**

## A. Starting state

This analysis branch was created directly from the E2 candidate:

- branch: `codex/accord-02e3-target-stage-semantics-review`;
- parent/base: `8128941a17ff9f0b24ac4531a7262539570879da`;
- E2 tree: `c7dcd93b59b70502c86bfde165396c78f0278b30`;
- accepted ACCORD-02: `5a8bf1e577f71132665ece271e70e30e87df5676`;
- `main` and `origin/main`: `5a8bf1e577f71132665ece271e70e30e87df5676`;
- `accord-02-accepted-v1^{}`: `5a8bf1e577f71132665ece271e70e30e87df5676`;
- frozen R2: `99da6ad0b5d6f535843b4c240a837b2b9f861b12`;
- starting worktree: clean.

The sealed ACCORD-02 package, E1 analysis, E2 candidate, and ACCORD-03 implementation were treated as read-only inputs.

## B. E2 facts carried forward

The accepted C fixture contains 23 vectors. Independent inspection found:

| Fact | Count |
|---|---:|
| Vectors | 23 |
| Explicit `target.stage` values | 0 |
| Non-empty `input.stages` arrays | 1 |
| Selected target stages | 0 |
| Exact predicate resolutions in accepted package | 0 |
| Lexical fallbacks | 0 |

V014 is the single vector with `input.stages`; it lists `provider_acceptance` and `recipient_acknowledgement` but does not identify which is the requested target stage. Evidence records do not supply an explicit evidence-stage field.

## C. Accepted normative intent

The C specification is clear that the settled object is a predicate, not a lifecycle label. It names stage-sensitive predicates including `provider_acceptance`, `processing_started`, `resource_created`, `resource_visible`, and `recipient_acknowledgement`. It also states that predicates are not aliases and that the intended predicate and stage are carried in the target and bound in evidence.

The same specification defines staged effects as distinct predicates with an explicit order or dependency graph. A result must identify the stage predicate being assessed, each stage's state, and the evidence/bindings for that stage. This supports exact stage-bound settlement and rules out silently treating provider acceptance as recipient acknowledgement.

Negative evidence is separately bounded: a complete ledger query may support scoped non-occurrence only when completeness, state-space coverage, interval, identity, retention, freshness, and consistency assumptions are satisfied. The accepted text does not define complete-negative as a positive lifecycle stage.

## D. Vector-by-vector result

The complete machine-readable inventory is in [`accord-02e3-vector-semantic-decision-table.json`](./accord-02e3-vector-semantic-decision-table.json).

The inventory records absent values as absent/null. It does not infer stages from evidence class, observed state, vector identifier, attempt outcome, or human-readable predicate spelling.

The four strongest intent signals are:

- V014: the expected `PARTIAL_EFFECT` strongly indicates provider acceptance supported while recipient acknowledgement remains unresolved; the requested later stage is not selected in the input.
- V021: `ACCEPTANCE_NOT_DELIVERY` and recipient mismatch strongly indicate a recipient-acknowledgement question; the target stage is still absent.
- V017/V022: the `resource-created` identifier and accepted C definition strongly indicate `resource_created`; the profile-local identity bridge and explicit stage field are absent.

The other 18 `external-effect` vectors vary across dispatch-only, transport acknowledgement, strong occurrence, stale evidence, retry ambiguity, conflict, invalid authority, incompatible profiles, extension uncertainty, and reopening. Their expected outcomes are preserved, but no exact target stage is supplied by the accepted records.

## E. Stage vocabulary and consistency

The vocabulary inventory is in [`accord-02e3-stage-vocabulary-inventory.json`](./accord-02e3-stage-vocabulary-inventory.json).

There are spelling and category differences that the accepted package does not declare equivalent:

| Source | Value | Finding |
|---|---|---|
| C prose/vector | `recipient_acknowledgement` | Predicate/stage wording used in C and V014 |
| R3 applicability profile | `recipient_acknowledged` | Profile stage; no accepted alias is declared |
| R3 applicability profile | `deliver_item` | Profile predicate; no accepted alias to `recipient-ack` is declared |
| C prose/profile | `provider_acceptance` / `provider_accepted` | Predicate and profile stage are distinct fields |
| C prose/profile | `resource_created` | C/profile stage; URN vector identifier is not bridged |
| C prose | `resource_visible` | No active applicability row or evidence capability |
| C/Evidence and Trust | `complete-negative` / `COMPLETE_NEGATIVE_LEDGER_QUERY` | Negative query/predicate family, not a positive stage row |

The accepted materials define profile-scoped ordering or dependency, not a universal total order. The V014 two-element array is local vector input, not a complete package-level ordering contract.

## F. `external-effect` analysis

The 18 vectors do not behave as one unqualified stage:

- V001/V002 concern dispatch and transport boundaries and explicitly do not establish external occurrence.
- V003/V004/V010/V015/V016/V023 concern occurrence, corroboration, authority orthogonality, retry success, or reopening.
- V005/V019 concern conflict or unresolved temporal ordering.
- V006 concerns stale evidence.
- V007/V008/V009 concern effect/attempt identity and replay binding.
- V011 concerns possible duplicate occurrence.
- V012 concerns timeout without evidence.
- V018 concerns incompatible profiles.
- V020 concerns an unknown settlement-bearing extension.

The accepted material therefore does not establish whether `external-effect` is:

1. one intentionally stage-less predicate;
2. shorthand for multiple stage-specific predicates; or
3. a generic predicate with an explicit requested minimum stage.

The stage-less interpretation is not presently viable as a complete normative model. It cannot determine whether provider acceptance satisfies the requested claim, cannot explain V014's earlier-supported/later-unresolved result without a requested later stage, and cannot define exact projection behavior for a generic predicate without adding new rules.

## G. V014 and V021

V014's expected `PARTIAL_EFFECT`, description, and two-stage input make the intended later-stage question highly likely to be recipient acknowledgement. The accepted C partial-effect rule says an earlier stage may be settled while a later stage remains unresolved, and requires the result to identify the stage being assessed. That is strong intent evidence, but it is not an explicit selected target stage.

V021's provider acceptance plus acknowledgement from another recipient makes the recipient-acknowledgement interpretation highly likely. It is still not a machine-level binding because the target has no stage and the accepted package has no alias from `recipient-ack` to `deliver_item` / `recipient_acknowledged`.

Neither vector permits an implementation to choose a stage by intuition. Both require an explicit amendment or a new typed target contract.

## H. V017 and V022

Both vectors use `urn:accord:02c:predicate:resource-created`. C explicitly defines `resource_created` as an external resource being created, and V022's valid observation reports `RESOURCE_CREATED`. This is normative support for the intended semantic concept, not merely an arbitrary lexical coincidence.

It does not, however, supply the missing exact machine bridge from the URN identifier to the R3 profile row `create_resource` at `resource_created`, nor does it populate `target.stage`. The intended stage is therefore strongly supported but not currently resolvable under the exact accepted contract.

## I. Provider acceptance and resource visibility

`provider_acceptance` is the clearest control case: C defines it as provider acceptance, and the profile has `provider_acceptance` at `provider_accepted`. No current vector uses the URN `provider-acceptance` as a target, but a future explicit registry row could be bounded without changing the settlement model.

`resource-visible` is not resolvable from the accepted active profile. C names the concept and explicitly distinguishes it from resource creation, but no accepted applicability row, stage mapping, or evidence capability makes it executable. It must remain unsupported or receive an explicit future contract.

## J. Complete-negative analysis

V013 is best treated as a distinct negative proposition/query applicability contract, not as an ordinary positive lifecycle stage and not as a meta-alias for `external-effect`.

The accepted intent supports binding the negative query to the named effect/proposition and its relevant identity, scope, interval, retention, freshness, and read/completeness assumptions. The exact minimal field set and whether an underlying positive predicate/stage is mandatory remain design decisions because the accepted vector does not provide a target stage or typed negative-applicability record.

The candidate must not manufacture a stage such as `negative_query` and must not force V013 into `resource_created`, `provider_accepted`, or `recipient_acknowledged`.

## K. Partial, occurrence, and non-occurrence semantics

`PARTIAL_EFFECT` is not a free-standing success label. Accepted C semantics require an early stage, a later or terminal stage, and an explicit ordering/dependency relation. Consequently, every partial-effect vector needs a requested target stage or an equivalent typed target contract.

`OCCURRENCE_SUPPORTED` is support for the named predicate under the active profile; it is not automatically stage-independent. The accepted C text repeatedly binds evidence to the named predicate and stage and disallows later-stage strengthening.

`NON_OCCURRENCE_SUPPORTED` is scoped to a complete, bound query over a declared state space and interval. It is not universal absence and is not implied by silence, timeout, stale reads, or a missing response. This is consistent with a separate negative proposition type.

## L. Candidate option evaluation

The full scoring table is in [`accord-02e3-design-options.json`](./accord-02e3-design-options.json).

- Option A, explicit stage per vector, is faithful and implementable after the missing stage choices are made. It is not itself a complete choice for the 18 generic vectors or V013.
- Option B, generic stage-less `external-effect`, fails the partial-stage and non-strengthening requirements unless substantial new semantics are added.
- Option C, generic predicate plus requested minimum stage, is bounded and potentially workable but requires a new target field, stage ordering/comparison semantics, and values for the affected vectors.
- Option D, typed hybrid, best preserves accepted positive-stage semantics while giving `external-effect` and `complete-negative` separate typed treatment. It remains a direction only until those two contracts are explicitly defined.

## M. Falsification and minimum novelty

Option B is falsified by V014: without a requested later stage, `PARTIAL_EFFECT` cannot say what remains unresolved. It is also unable to distinguish a provider acceptance from a downstream recipient acknowledgement while preserving exact predicate binding.

Option A alone is a data-shape repair, not a semantic answer: it still requires normative choices for the 18 `external-effect` vectors and the negative vector.

Option C preserves the generic term only by introducing a new minimum-stage relation and therefore is not already present in the accepted design.

Option D is the smallest coherent direction because it keeps existing stage-specific meanings and separates positive effects from complete-negative. It still requires genuinely new normative decisions, so selecting it now would exceed analysis authority.

## N. Independent implementability and usefulness

The accepted stage-specific portions are independently implementable after exact registry rows and target fields are supplied. The current full corpus is not: an implementation must either invent a stage, choose a default, or return unresolved for vectors whose expected outcome assumes a settled proposition.

The intended vector suite can distinguish positive occurrence, partial effect, scoped negative occurrence, conflict, duplicate uncertainty, and insufficient evidence once target proposition types/stages are bound. The present ambiguity prevents deterministic execution but does not require changing the research question.

## O. Capture-side notes

An explicit target stage is realistically capturable by an evidence producer when the requested business condition is known at dispatch or experiment assignment. The producer can bind a stage-specific proposition and evidence coverage.

For generic external effects, the capture side cannot safely infer the requested stage from a provider response. For complete-negative, the producer can bind scope, interval, retention, completeness, freshness, and read semantics, but those must be specified as a typed contract.

These are design-practicality observations, not empirical evidence.

## P. ACCORD-03 impact

No ACCORD-03 implementation was modified. The impact analysis is in [`accord-02e3-implementation-impact.json`](./accord-02e3-implementation-impact.json).

Until an amendment is accepted, ACCORD-03 must treat unresolved predicate/stage identity as unresolved or invalid according to its existing accepted boundary. It must not adopt any candidate mapping from this branch.

## Q. Deferred external implementation backlog

The E1/E2 backlog remains unchanged and is not resolved by E3:

- evidence binding completeness;
- request mutation;
- duplicate JSON verify path;
- shared-pool proof;
- evidence digest verification;
- observed-state lexical semantics;
- subject/delegatee authority;
- minimal-result crash;
- projection provenance order;
- rule trace;
- historical mapping;
- authority unknown-field handling.

## R. Verdict

**PARTIAL_DESIGN_ONLY**

Accepted material provides strong intended meanings for resource creation, recipient acknowledgement, and provider acceptance, and it clearly requires stage-specific settlement plus separate bounded negative evidence. It does not determine the requested stage for the 18 `external-effect` vectors, does not select V014's target stage, does not provide a complete negative-applicability contract, and does not define active semantics for `resource-visible`.

This is not evidence that the entire settlement model must be redesigned. It is evidence that a further explicit normative decision is required before package 0.2 or ACCORD-03R3 can claim deterministic vector closure.

## S. Changed files

- `docs/accord-02e3/ACCORD-02E3-TARGET-STAGE-SEMANTICS-REVIEW.md`
- `docs/accord-02e3/accord-02e3-stage-vocabulary-inventory.json`
- `docs/accord-02e3/accord-02e3-vector-semantic-decision-table.json`
- `docs/accord-02e3/accord-02e3-design-options.json`
- `docs/accord-02e3/accord-02e3-spec-consistency.json`
- `docs/accord-02e3/accord-02e3-implementation-impact.json`

## T. Mutation attestation

```text
ACCORD02_ACCEPTED_FILES_MUTATED: NO
ACCORD02_E2_CANDIDATE_MUTATED: NO
ACCORD03_IMPLEMENTATION_MUTATED: NO
EXPERIMENT_IMPLEMENTED: NO
EXPERIMENT_EXECUTED: NO
MAIN_ADVANCED: NO
TAG_CREATED: NO
PUSH_PERFORMED: NO
```

## U. Next gate

`ACCORD-02E3 COMPLETE — HUMAN/EXTERNAL SETTLEMENT-SEMANTICS DECISION REQUIRED.`

`ACCORD-02E3 COMPLETE — STOP BEFORE PACKAGE-0.2 ACCEPTANCE, ACCORD-03R3, OR EXPERIMENT WORK.`
