# ACCORD-02E-R3 — Final Specification Closure Review

## Verdict

**AMEND**

The R3 direction is sound, but the stack has not reached a genuine
specification freeze. The review found two acceptance-blocking scope defects:

1. active profile references cannot be resolved from the declared verifier or
   experiment bundle; and
2. the bundle's generic `schema_id`/`schema_version` plus unconstrained
   `content` does not itself supply a deterministic schema-contract lookup.

Those defects prevent independent evaluation of the extension, source,
visibility, normalization, classifier, predicate, digest, and projection
rules. Several earlier findings therefore remain only partially closed.

This is a review-only result. No specification file was amended and no
experiment, verifier, validator, or runtime was executed.

## Starting state

| Item | Verified value |
|---|---|
| Repository | `D:\Users\fleur\Moirae Accord` |
| Review branch | `codex/accord-02e-r3-final-closure-review` |
| Starting R3 commit | `93165ef0755b6161c58255d304b505ce5509ec62` |
| Starting tree | `edb446355c5326882b83e9f350ed8eb95628fa15` |
| Starting parent | `533126f893f149002828cd4225753e8e2a20b792` |
| `main` / `origin/main` | `e748028d3ac05112163765afc65ef4224933f6a1` |
| `accord-01-accepted-v1` | `e748028d3ac05112163765afc65ef4224933f6a1` |
| `accord-00-accepted-v1` | `ddad3092b8b1d1d4ac5ab496143263ddd6afc587` |
| Worktree at start | clean |

The exact A→R3 ancestry was present and no `accord-02-accepted-v1` tag
existed. The two sealed artifact hashes and all eight protected source
snapshots were unchanged, clean, fetch-correct, and push-disabled.

## Review method

The review reconstructed the R3 bundle and rule graph, inspected all 71
combined normative rules, and replayed the prior adversarial constructions.
The tests were specification-level/static checks only. JSON was parsed and
local references were inspected without installing a validator or executing
any experiment.

The decisive test was whether a conforming implementation can evaluate a
rule from the declared bundle scope alone. A prose statement that a profile
is “supplied by reference” does not close the rule when the reference cannot
resolve to a record or supplied definition in that scope.

## Historical finding re-evaluation

| Finding | R3 result | Reason |
|---|---|---|
| `E2E-BLOCK-001` | PARTIALLY_CLOSED | Extension registry concept exists, but active registry resolution is not self-contained. |
| `E2E-R1-BLOCK-001` | CLOSED | No public scorer locator or reverse reference was found. |
| `E2E-MAJOR-001` | CLOSED | A projection requires native C lineage, a projection profile, and a proposition reference; no regression found. |
| `E2E-MAJOR-002` | CLOSED | Grant relation, effective authority, and event-time validity remain separate. |
| `E2E-MAJOR-003` | PARTIALLY_CLOSED | Typed references and run records exist, but the declared scope cannot resolve all profile/schema targets. |
| `E2E-MAJOR-004` | PARTIALLY_CLOSED | Canonical proposition and applicability profile exist, but profile resolution and duplicate-field adjudication are not independently closed. |
| `E2E-MAJOR-005` | PARTIALLY_CLOSED | Arm/source/profile artifacts exist, but their active profile references are not resolvable inside the bundle. |
| `E2E-R2-BLOCK-001` | PARTIALLY_CLOSED | R3 adds an extension registry and conservative unknown-extension rules, but the registry cannot be obtained from the declared scope. |
| `E2E-R2-BLOCK-002` | OPEN | Bundle envelopes exist, but they do not contain resolvable active profile records or a complete structural-contract inventory. |
| `E2E-R2-MAJOR-001` | PARTIALLY_CLOSED | Source membership is described and catalogued, but active source-schema registry resolution remains unavailable. |
| `E2E-R2-MAJOR-002` | PARTIALLY_CLOSED | Normalization and classifier profiles exist, but their profile references cannot be resolved from the bundle schema. |
| `E2E-R2-MAJOR-003` | PARTIALLY_CLOSED | Visibility profile exists, but role membership and active profile resolution are not fully closed. |
| `E2E-R2-MAJOR-004` | PARTIALLY_CLOSED | Predicate applicability is expressed, but the active profile cannot be resolved and duplicate-copy handling is not fully inspectable. |
| `E2E-R2-MAJOR-005` | PARTIALLY_CLOSED | Digest rules exist, but generic record canonicalization is not fixed for every bundle entry. |
| `E2E-MINOR-001` | CLOSED | Provider operation IDs remain external correlation IDs. |
| `E2E-MINOR-002` | OPEN / non-blocking | Optional A2A-shaped coverage remains optional and does not contradict the two-transport requirement. |

## Main findings

### E2E-R3-BLOCK-001 — active profiles are not resolvable in scope

Both R3 bundle schemas define active profile references with
`record_type: PROFILE`, `profile_id`, `schema_id`, and `schema_version`.
Neither bundle's record inventory admits `PROFILE` as a record type, and the
reference contains no profile content. The inventory instead contains
concrete types such as `EXTENSION_REGISTRY`, `SOURCE_SCHEMA_REGISTRY`,
`ROLE_VISIBILITY_PROFILE`, and `NORMALIZATION_PROFILE`.

Therefore `BND-005` cannot determine whether the active profile exists,
matches its referenced identity, or is structurally valid using only the
declared scope. An implementation must either consult an unstated profile
store or reject every otherwise valid bundle. Both outcomes violate the
self-contained contract claimed by R3.

### E2E-R3-BLOCK-002 — structural contract selection is not self-contained

Bundle entries carry an arbitrary `content` value plus free-form
`schema_id`/`schema_version`. `BND-004` says those identifiers select a
declared structural contract in the supplied scope, but neither bundle
defines a record-schema registry or admits schema-contract records. The
schemas themselves do not cross-check that `content` conforms to the named
schema.

This leaves `RESOLVED` versus `STRUCTURALLY_INVALID` dependent on an
implementation-known registry or ambient repository. The issue is distinct
from profile identity: even after a profile reference is made resolvable, the
bundle still needs a declared, deterministic source for the contracts used to
validate its arbitrary content entries.

### E2E-R3-MAJOR-001 — role profiles are not fully closed over declared roles

The role-visibility schema constrains the top-level `roles` array to known
role enums, but `field_rules[].producing_role` and
`field_rules[].consumer_roles[]` are unrestricted strings. `VIS-001` says a
consumer is allowed but does not explicitly require every producer and
consumer to be a member of the declared role set. Two implementations can
therefore disagree about whether an undeclared role is a profile error or an
ordinary role name. This is a profile determinism defect, not an effect-truth
claim.

### E2E-R3-MAJOR-002 — scenario-ID opacity remains an assertion

The public catalog and R2 `ORC-003` preserve the requirement that scenario
identifiers be opaque to expected outcomes, but the schema cannot establish
semantic opacity. A field such as
`scenario_identifiers_opaque_to_expected_result: true` is a declaration, not
a testable information-flow rule. A future catalog may encode the expected
answer in an ID, fixture name, or condition label while remaining
schema-valid. This leaves an oracle side-channel risk in the frozen design.

### E2E-R3-MAJOR-003 — generic digest canonicalization is incomplete

`DIGEST-001` uses `record_declared_canonicalization`, but the generic bundle
record entry does not require or define that value and permits arbitrary
`content`. Existing native records have their own integrity conventions, but
R3 does not define how the digest covers every generic inventory entry. A
supplied digest is consequently not always independently verifiable from the
declared bundle and profile inputs.

## What did close

- Standalone `VERIFIED` and `CORROBORATED` projections cannot be admitted
  without native ACCORD-02C settlement lineage.
- Incomplete absence cannot project to bounded non-occurrence.
- Authority relation, effective composition, and temporal authority validity
  remain separate.
- Attempt, provider operation, transport, proposition, verifier-run, and
  result identifiers remain typed distinctions.
- The public scenario catalog does not point to scorer expectations.
- Normalization is specified as raw output plus profile before comparison to
  scorer truth; no executed normalization was performed in this review.
- Digest failure is kept separate from effect occurrence and authority facts.

These closures do not cure the missing bundle/profile resolution contract.

## Readiness decision

The stack is **not ready** for a separate acceptance/seal task. The required
next amendment is bounded: make active profiles and structural schema
contracts actual members of a self-contained validation scope (or define an
equally explicit supplied registry), then re-review role membership, ID
opacity, and digest canonicalization against that scope. No new research model
is required.

## Explicit answers

1. Every verifier-required record is not yet demonstrably contained in a
   resolvable verifier bundle: **NO**.
2. A verifier rule still has an unstated profile/schema lookup path:
   **YES**.
3. An arm-visible artifact locates scorer truth: **NO** in the inspected
   public graph.
4. Unknown extensions can strengthen a result under the intended rules:
   **NO**, but the active registry cannot currently be resolved.
5. Extension classification is deterministic once a supplied registry exists:
   **YES WITH PROFILE**, not currently admissible from the bundle schema.
6. Every arm source has a declared membership model: **YES IN PROFILE**, not
   fully resolvable from the declared bundle.
7. Fixture-private labels are prohibited from arm visibility by the intended
   visibility profile: **YES IN PROFILE**; role membership is still a major
   closure gap.
8. Normalization is intended to be raw-output-plus-profile deterministic:
   **YES IN PROFILE**; the profile reference is not self-contained.
9. ARM-C may use an unregistered feature: **NO** under the intended rule.
10. Predicate applicability is explicit in the supplied profile model:
    **YES IN PROFILE**.
11. Unknown required binding can produce qualified `VERIFIED`: **NO**.
12. Wrong supplied digest fails validation: **YES WHERE CANONICALIZATION IS
    KNOWN**.
13. Digest failure implies no external effect: **NO**.
14. Foreign verifier result passes lineage silently: **NO IN THE INTENDED
    RULES**, but scope resolution remains incomplete.
15. Structurally invalid target counts as resolved: **NO**.
16. Occurrence can coexist with unknown attempt attribution: **YES**.
17. Effect settlement creates valid authority: **NO**.
18. Authority validity proves occurrence: **NO**.
19. ARM-B/C may outperform Accord: **YES**.
20. Accord may lose through excess uncertainty or categorical failure: **YES**.
21. Experiment run: **NO**.
22. Empirical benefit established: **NO**.
23. Open blockers: **YES**, `E2E-R3-BLOCK-001` and `E2E-R3-BLOCK-002`.
24. Open majors: **YES**, `E2E-R3-MAJOR-001` through `E2E-R3-MAJOR-003`.
25. Acceptance readiness: **NO**.

## Scope and attestation

Only fresh review artifacts are committed on the review branch. No ACCORD-02
specification, historical review, remediation evidence, runtime, verifier,
validator, harness, classifier, source repository, dependency, provider, main
ref, tag, or external repository was changed.
