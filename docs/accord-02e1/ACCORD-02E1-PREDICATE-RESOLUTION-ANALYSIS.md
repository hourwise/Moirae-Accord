# ACCORD-02E1 — Predicate Applicability Erratum / Amendment Analysis

Status: `NORMATIVE_AMENDMENT_REQUIRED`

## A. Starting state

The analysis branch was created directly from accepted ACCORD-02 commit
`5a8bf1e577f71132665ece271e70e30e87df5676`:

- accepted tag: `accord-02-accepted-v1`;
- `main`: `5a8bf1e577f71132665ece271e70e30e87df5676`;
- `origin/main`: `5a8bf1e577f71132665ece271e70e30e87df5676`;
- ACCORD-01 tag: `e748028d3ac05112163765afc65ef4224933f6a1`;
- ACCORD-00 tag: `ddad3092b8b1d1d4ac5ab496143263ddd6afc587`;
- worktree was clean at the gate;
- R2 branch `codex/accord-03r2-cross-assessor-remediation` was not modified.

The machine-readable inventory is
[`accord-02e1-predicate-inventory.json`](./accord-02e1-predicate-inventory.json).

## B. Accepted-spec integrity

The accepted `docs/accord-02` tree was treated as read-only. No accepted
specification, review, remediation, or acceptance artifact was changed. No
ACCORD-03 source was changed. This branch contains analysis artifacts only.

## C. Reproduction of the reported condition

The accepted predicate-applicability profile at
`docs/accord-02/examples/accord-02r3-predicate-applicability-profile.json`
declares exactly these rows:

| Profile predicate ID | Stage | Required/optional/NA bindings |
| --- | --- | --- |
| `create_resource` | `resource_created` | target REQUIRED; resource REQUIRED; recipient NOT_APPLICABLE; provider OPTIONAL; attempt attribution OPTIONAL |
| `deliver_item` | `recipient_acknowledged` | target REQUIRED; resource OPTIONAL; recipient REQUIRED; provider OPTIONAL; attempt attribution OPTIONAL |
| `provider_acceptance` | `provider_accepted` | target REQUIRED; resource OPTIONAL; recipient OPTIONAL; provider REQUIRED; attempt attribution OPTIONAL |

The accepted settlement vector fixture declares six URN predicate records and
uses four of them as vector targets:

- `urn:accord:02c:predicate:external-effect` — 18 vector targets;
- `urn:accord:02c:predicate:complete-negative` — V013;
- `urn:accord:02c:predicate:recipient-ack` — V014 and V021;
- `urn:accord:02c:predicate:resource-created` — V017 and V022.

There is no exact profile row for any of those four target identifiers. The
other two catalog URNs, `provider-acceptance` and `resource-visible`, also have
no profile row. The accepted R1 vocabulary map is a result-label projection
map; it has no predicate alias or identifier mapping.

The condition is therefore reproduced from accepted artifacts without relying
on implementation output.

## D. Existing normative bridge search

The complete accepted-stack search found no:

- predicate alias table;
- predicate registry;
- profile-local alias field;
- mapping profile from settlement URNs to applicability rows;
- rule stating that stage equality selects a predicate row;
- package inventory entry for such a bridge.

The relevant accepted rules instead make the gap visible:

1. ACCORD-02C says predicates are not aliases and the intended predicate and
   stage must be carried in the target and bound in evidence
   (`ACCORD-02C-EFFECT-SETTLEMENT-MODEL.md:70-74`).
2. The R1 map requires `predicate_binding=EXACT`, but only after a native
   settlement result has a resolved predicate; it does not resolve predicate
   vocabulary.
3. R3 `PRED-004` requires
   `predicate_stage_profile_matches_proposition`, but the accepted profile has
   no row for the vector URNs.
4. The R5 package inventories the predicate-applicability profile but no
   predicate mapping/alias contract.

The accepted material does not authorize the R2 implementation fallback that
selects a same-stage row when `predicate_id` merely starts with `urn:`. That
fallback is an implementation defect once the missing contract is recognized,
not a normative bridge.

## E. Settlement-vector inventory and resolution

There are 23 settlement vectors. All 23 have `resolution=UNRESOLVED` in the
machine-readable matrix. Counts are:

| Resolution | Count |
| --- | ---: |
| EXACT | 0 |
| EXPLICITLY_MAPPED | 0 |
| UNRESOLVED | 23 |
| AMBIGUOUS | 0 |

`AMBIGUOUS` is not used as the resolution value because the immediate failure
is that no exact mapping exists. The separate derivability analysis records
whether a row could be guessed from context:

- the 18 `external-effect` targets have multiple plausible profile rows or no
  generic row, depending on the vector's evidence/stage semantics;
- V013's `complete-negative` target has no positive applicability row and is a
  distinct negative-evidence construct;
- V014/V021 have `deliver_item` as a human-plausible candidate, but no accepted
  alias from `recipient-ack` or `recipient_acknowledgement` to that row;
- V017/V022 have `create_resource` as a human-plausible candidate, but no
  accepted alias from `resource-created` to that row.

Human-plausible candidates are not normative derivations under the explicit
no-normalization rule.

## F. V014 and V021

Both target `urn:accord:02c:predicate:recipient-ack`. V014 declares stages
`provider_acceptance` and `recipient_acknowledgement`, supplies a provider
acceptance receipt, and expects `PARTIAL_EFFECT`. V021 targets the same URN and
expects partial/conflicting treatment for a recipient mismatch.

The current R2 implementation implicitly borrows the `deliver_item` row after
code-level stage normalization (`recipient_acknowledgement` to
`recipient_acknowledged`) and a URN-prefix fallback. The accepted package does
not authorize either operation. Removing that fallback leaves both vectors
without a resolvable applicability row; retaining it allows arbitrary
unregistered URNs to inherit a row.

The expected vector outcomes are not changed by this analysis.

## G. Complete-negative predicate

`urn:accord:02c:predicate:complete-negative` is a target predicate in V013,
but the vector also supplies an explicit `negative_query` with complete state
space, interval, retention, and freshness flags. The C text describes
complete-negative as a bounded negative-evidence condition, not as a synonym
for any positive lifecycle predicate. The accepted package lacks the typed
contract that connects this target identifier to the negative-evidence rules.

It must not be forced into `create_resource`, `deliver_item`, or
`provider_acceptance` merely for vocabulary symmetry.

## H. External-effect predicate

`urn:accord:02c:predicate:external-effect` is a generic-looking fixture
predicate used for 18 vectors spanning dispatch-only, transport acknowledgement,
strong occurrence, stale evidence, retry ambiguity, invalid authority,
incompatible profiles, clock ambiguity, unknown extensions, and reopening.
The accepted package supplies no generic applicability row and no
stage-specific mapping for these uses. A single alias to one of the three
profile rows would not preserve the accepted distinct evidence/binding
semantics.

## I. Predicate-specific consistency findings

1. Vector target identifiers and applicability profile identifiers are from
   different vocabularies with no bridge.
2. The C prose uses `provider_acceptance`, `resource_created`,
   `resource_visible`, and `recipient_acknowledgement`; the profile uses
   `provider_acceptance`, `resource_created`, and `recipient_acknowledged` as
   stage/predicate fields, but the URN fixture identifiers remain unmapped.
3. The profile uses `deliver_item` while the C prose and vectors describe
   recipient acknowledgement; no accepted rule makes those identifiers equal.
4. The A example uses `urn:accord:example:predicate-resource-created` with
   `kind=resource_created` and `action=create_resource`, but it is illustrative
   and does not declare a profile mapping.
5. The D scenario catalog uses `create_resource` and
   `deliver_or_publish_item` as scenario surface terms, not as a normative
   predicate registry.
6. The R1 map requires exact predicate binding but maps only result kinds and
   C axes.
7. `PRED-004` cannot be satisfied for the vector URNs from the accepted
   package alone.

## J. Verdict

`NORMATIVE_AMENDMENT_REQUIRED`

The accepted artifacts do not determine a unique mapping for the settlement
vector predicates. This is not merely an editorial omission: a future
implementation must make semantic choices about generic external effects,
recipient acknowledgement, resource creation, provider acceptance, and the
complete-negative target before it can evaluate the vectors deterministically.

## K. Recommended bounded action

Do not patch the implementation with another heuristic. Before ACCORD-03R3,
make one explicit normative decision using a small, versioned predicate
registry or exact profile extension. Each entry should contain the exact
predicate identifier, version, applicability target, stage, bindings, and
negative-evidence policy where relevant. The contract must define exact
resolution and fail closed for unknown identifiers.

The analysis does not recommend a semantic mapping as an existing fact. It
records the candidate shapes and unresolved decisions in
[`ACCORD-02E1-NORMATIVE-DECISION.md`](./ACCORD-02E1-NORMATIVE-DECISION.md).

## L. Versioning recommendation

Keep `accord-02-accepted-v1` and package version `0.1` immutable. If a mapping
is selected, issue a new exact package version—preferably the same package ID at
version `0.2` if repository package policy permits—and subject it to a
separate amendment review and acceptance decision. No tag, main advancement,
or promotion is performed by ACCORD-02E1.

## M. ACCORD-03 implementation impact

The affected implementation surfaces and the deferred Claude/DeepSeek R3
findings are recorded in
[`accord-02e1-implementation-impact.json`](./accord-02e1-implementation-impact.json).
No ACCORD-03 source was changed.

## N. Changed files

- `docs/accord-02e1/ACCORD-02E1-PREDICATE-RESOLUTION-ANALYSIS.md`
- `docs/accord-02e1/ACCORD-02E1-NORMATIVE-DECISION.md`
- `docs/accord-02e1/accord-02e1-predicate-inventory.json`
- `docs/accord-02e1/accord-02e1-implementation-impact.json`

## O. Mutation attestation

```text
ACCORD02_ACCEPTED_FILES_MUTATED: NO
ACCORD03_IMPLEMENTATION_MUTATED: NO
EXPERIMENT_IMPLEMENTED: NO
EXPERIMENT_EXECUTED: NO
MAIN_ADVANCED: NO
TAG_CREATED: NO
PUSH_PERFORMED: NO
```

## P. Next gate

`ACCORD-02E1 ANALYSIS COMPLETE — NORMATIVE PREDICATE-MAPPING DECISION REQUIRED BEFORE ACCORD-03R3.`

`ACCORD-02E1 COMPLETE — STOP BEFORE ACCORD-03R3 OR EXPERIMENT WORK.`
