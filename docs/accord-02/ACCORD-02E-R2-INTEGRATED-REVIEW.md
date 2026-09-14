# ACCORD-02E-R2 — Post-R2 Integrated Closure Review

## Result

**Integrated verdict: AMEND**

This is a fresh review of the remediated ACCORD-02A/B/C/D/R1/R2 stack. It
does not modify or overwrite the historical reviews or the R2 remediation.
The direct public scorer locator was removed and the A/C projection boundary
was materially improved. Acceptance is still blocked by unresolved
machine-enforceability and experiment-boundary defects described below.

## Review basis

The reviewed candidate chain is:

```text
ACCORD-01  e748028d3ac05112163765afc65ef4224933f6a1
  02A     2e2c036539dcc32f7411b5180e16ba46a7209d1a
  02B     90c80c77ed0d312c7d5c4e72d7b92b55d4ed1e6f
  02C     b94f3783c7bf3a65f7698c37ae89bef6e088a5ad
  02D     9adf15d6005c72e5fbf49d2f3f7f62ca8f7e6354
  02E     73b63daa9453fd3660c07c1c0b58bf0039302bca
  R1      e378116eed1cb540baa230471687bae628448838
  E-R1    d0aed1da5f54a638c2c357f7a5d9e77e33ad5209
  R2      c05c2b34c1d448055307044605955c80e701333c
```

The R2 rule registry contains 33 rules. This review classifies every rule in
[`accord-02e-r2-validation-rule-review.json`](./accord-02e-r2-validation-rule-review.json).
The rebuilt compatibility matrix is in
[`accord-02e-r2-compatibility-matrix.json`](./accord-02e-r2-compatibility-matrix.json).

## Historical closure assessment

| Finding | R2 claim | Independent status | Reason |
| --- | --- | --- | --- |
| E2E-BLOCK-001 | CLOSED | PARTIALLY_CLOSED | Direct locator and arbitrary manifest values are gone; portable-record extensions remain an unresolved semantic channel. |
| E2E-R1-BLOCK-001 | CLOSED | CLOSED | The public catalog contains no scorer catalog locator or reverse reference. |
| E2E-MAJOR-001 | CLOSED | CLOSED | A settlement projection requires native C result, mapping profile, and proposition references. |
| E2E-MAJOR-002 | unchanged closed | CLOSED | Grant relation, effective authority, and event-time validity remain separate. |
| E2E-MAJOR-003 | CLOSED | PARTIALLY_CLOSED | Typed references exist, but the validation bundle and run/scope record contracts are absent. |
| E2E-MAJOR-004 | CLOSED | PARTIALLY_CLOSED | A canonical proposition exists, but applicability and duplicate-summary equality are not fully defined. |
| E2E-MAJOR-005 | CLOSED | PARTIALLY_CLOSED | Arm discriminators are closed, but source-schema membership, feature definitions, normalization, and visibility remain incomplete. |
| E2E-MINOR-001 | unchanged closed | CLOSED | Provider operation IDs remain external correlation identifiers. |
| E2E-MINOR-002 | unchanged note | OPEN / non-blocking | Optional A2A coverage remains optional and must not support universal transport claims. |

## New findings

| Finding | Severity | Disposition | Acceptance impact |
| --- | --- | --- | --- |
| E2E-R2-BLOCK-001 | BLOCKING | SPEC_AMBIGUITY | Portable-record extension semantics are not deterministically closed. |
| E2E-R2-BLOCK-002 | BLOCKING | SPEC_AMBIGUITY | No complete verifier/experiment validation-bundle contract is defined. |
| E2E-R2-MAJOR-001 | MAJOR | SPEC_AMBIGUITY | ARM-004 requires source schema membership absent from the profiles. |
| E2E-R2-MAJOR-002 | MAJOR | EXPERIMENT_RISK | Normalization and classifier feature profiles are referenced but not supplied. |
| E2E-R2-MAJOR-003 | MAJOR | EXPERIMENT_RISK | Arm profiles expose orchestration condition labels without a role-specific visibility contract. |
| E2E-R2-MAJOR-004 | MAJOR | SPEC_AMBIGUITY | NOT_APPLICABLE and duplicate proposition summaries are not fully profile-bound. |
| E2E-R2-MAJOR-005 | MAJOR | DOCUMENTATION_GAP | Optional digest checks have no registered deterministic rule or failure code. |

The current unresolved summary is 2 BLOCKING, 5 MAJOR, and one retained
non-blocking MINOR note. There are no contradictory rules in the reviewed
dependency-family graph, but the missing inputs prevent several rules from
being evaluated as deterministic acceptance checks.

## What passed

- A/B/C/D/R1/R2 commit identities and ancestry remain intact.
- The public scenario catalog has no scorer expectation locator.
- The one-way scorer join is represented only on scorer-controlled material.
- The arm manifest uses a closed discriminated structure with arm/profile
  constants and typed source references.
- Standalone A `VERIFIED`/`CORROBORATED` projections are structurally blocked
  without native C and named mapping-profile lineage.
- `ATTENUATED`, effective-authority composition, and event-time validity remain
  independent axes.
- `effect_id`, `attempt_id`, provider operation IDs, and transport IDs remain
  distinct concepts.
- A canonical proposition record exists and is required by settlement paths.
- Raw arm output is explicitly untrusted and separated from scorer truth.
- The design still permits a negative empirical result and does not claim one.

## Why the stack is not ready

1. `ARM-007` says extensions must be classified by an active namespace or
   evidence binding, but no profile/catalog defines those namespaces or the
   classification lookup. The A base schema accepts an arbitrary extensions
   object. This is a viable semantic leak path for an ARM-D portable bundle.
2. `LIN-001`–`LIN-007`, `PROP-001`, `PROP-002`, and `PROP-005` assume a supplied
   validation bundle and current scope, but no first-class verifier bundle,
   experiment bundle, experiment-run record, or verifier-run record contract
   defines the complete collection and its resolution scope.
3. `ARM-004` requires source schema ID/version membership in the active profile;
   the profile schema/catalog only enumerate source types and descriptive field
   paths. A foreign schema can therefore satisfy the present shape.
4. `SCORE-002`/`SCORE-003` and ARM-C reference normalization/feature IDs without
   a frozen machine-readable adapter or feature definition. Two scorers could
   normalize the same raw output differently while satisfying the schemas.
5. All arm profiles list delegate behavior, fault, authority-condition,
   idempotency-condition, and fixture configuration fields as allowed
   orchestration data. The design does not say which role can see them or
   prevent those labels from becoming outcome proxies.
6. `PROP-004` depends on predicate-specific applicability that is not declared
   by the proposition or settlement profile. The digest statement in the R2
   contract is also not a registered rule with a failure code.

These are bounded specification defects, not a reason to redesign the
authority or settlement models. They must be resolved in a subsequent repair
before acceptance/seal review.

## Explicit review answers

1. Can the stack represent valid authority plus unknown effect? **Yes.**
2. Can it represent invalid authority plus observed effect? **Yes.**
3. Can it represent individually attenuated siblings with unbounded aggregate
   authority? **Yes.**
4. Can provider acceptance remain distinct from final effect occurrence? **Yes.**
5. Can complete negative evidence remain distinct from ordinary silence? **Yes.**
6. Can one logical effect have multiple attempts? **Yes.**
7. Can duplicate attempts remain distinct from duplicate effects? **Yes.**
8. Can later evidence reopen an earlier result? **Yes, profile-scoped.**
9. Can a third-party verifier reproduce conclusions without private state? **The
   intended inputs are portable, but the required bundle is not defined well
   enough to verify this deterministically; therefore not yet closed.**
10. Can transport metadata become authority? **No under the declared rules.**
11. Can A2A task completion become effect settlement automatically? **No.**
12. Can Accord lose the future comparison? **Yes.**
13. Can universal UNKNOWN fail empirically? **Yes.**
14. Has any experiment occurred or any empirical benefit been established?
   **No.**
15. Are BLOCKING findings open? **Yes: E2E-R2-BLOCK-001 and
   E2E-R2-BLOCK-002.**
16. Are MAJOR findings open? **Yes: E2E-R2-MAJOR-001 through -005.**
17. Is the stack ready for acceptance? **No.**

## Scope attestation

This review does not change A/B/C/D/R1/R2 specifications, historical reviews,
or remediation evidence. It does not implement a validator, verifier,
experiment harness, provider fixture, or classifier, and it does not execute
an experiment.
