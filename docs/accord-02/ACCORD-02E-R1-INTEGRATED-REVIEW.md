# ACCORD-02E-R1 — Post-Remediation Integrated Re-Review

## Verdict

**AMEND**

The remediation improved the semantic model, but the stack is not ready for
acceptance/seal. The original oracle-isolation blocker remains open in a
machine-readable path, and four original major findings are only partially
closed at the schema boundary. No experiment has been executed and no
research benefit is claimed.

## A. Starting state

Repository: `D:\Users\fleur\Moirae Accord`

Starting branch: `codex/accord-02r1-integrated-review-remediation`

Starting commit:

```text
HEAD:   e378116eed1cb540baa230471687bae628448838
TREE:   e6f61f3e88e627d6b3c9d051e8b886809d6a2b6a
PARENT: 73b63daa9453fd3660c07c1c0b58bf0039302bca
```

The worktree was clean. Protected refs were:

```text
main                         e748028d3ac05112163765afc65ef4224933f6a1
origin/main                  e748028d3ac05112163765afc65ef4224933f6a1
accord-01-accepted-v1        e748028d3ac05112163765afc65ef4224933f6a1
accord-00-accepted-v1        ddad3092b8b1d1d4ac5ab496143263ddd6afc587
```

The exact candidate chain was verified as ACCORD-01 → 02A → 02B → 02C →
02D → original 02E → R1. No earlier candidate commit was rewritten. The
historical 02E artifacts and R1 remediation artifacts were unchanged at the
review starting point. No acceptance tag or previous 02E-R1 review branch or
file existed.

The sealed ACCORD-00/01 artifact hashes and all eight protected source
snapshots remained intact, pinned, clean, and configured with the recorded
fetch URLs and disabled `example.invalid` push URLs.

## B. Review method

The R1 closure record was treated as an assertion set only. Each inherited
BLOCKING and MAJOR finding was reconstructed against both prose and
machine-readable artifacts. The review repeated the original adversarial
constructions and added the ten `ADV-R1-*` cases in
[ACCORD-02E-R1-ADVERSARIAL-CASES.md](./ACCORD-02E-R1-ADVERSARIAL-CASES.md).

This was an offline specification review. No runtime, verifier executable,
harness, provider, classifier, or experiment was used.

## C. Original finding re-evaluation

| Finding | Original severity | R1 claim | Independent status | Reason |
| --- | --- | --- | --- | --- |
| `E2E-BLOCK-001` | BLOCKING | CLOSED | **OPEN** | Scorer split exists, but the public catalog points to scorer truth and manifest values/profile membership are not structurally closed. |
| `E2E-MAJOR-001` | MAJOR | CLOSED | **PARTIALLY_CLOSED** | The normative map is conservative, but A’s standalone result schema does not require a native C result or map reference. |
| `E2E-MAJOR-002` | MAJOR | CLOSED | **CLOSED** | Grant relation, effective authority, and event-time validity are distinct and composable. |
| `E2E-MAJOR-003` | MAJOR | CLOSED | **PARTIALLY_CLOSED** | Typed references exist, but reference existence, equality, and semantic ID namespaces remain external checks. |
| `E2E-MAJOR-004` | MAJOR | CLOSED | **PARTIALLY_CLOSED** | Predicate/stage binding is expressible and required in D, but duplicated bindings and A optionality are not equality-enforced. |
| `E2E-MAJOR-005` | MAJOR | CLOSED | **PARTIALLY_CLOSED** | Per-arm profiles exist, but profile selection, field membership, nested values, and raw-output sanitization rely on a future harness assertion. |
| `E2E-MINOR-001` | MINOR | CLOSED | **CLOSED** | Provider operation IDs remain documented as external correlation only. |
| `E2E-MINOR-002` | MINOR | NON_BLOCKING_NOTE | **OPEN / NON-BLOCKING** | A2A remains optional; the minimum T1/T2 design is internally consistent if claims stay scoped. |

The new `E2E-R1-BLOCK-001` records the direct scorer-catalog reference
introduced in the public scenario catalog. It is a regression in the repaired
boundary and independently blocks readiness.

## D. Oracle isolation

The scorer-only expectation catalog is correctly marked and has a one-to-one
scenario linkage. The public scenario records no longer contain the original
oracle fields. Those are positive repairs.

They are not sufficient for closure:

1. `accord-02d-scenario-catalog.json` contains
   `scorer_expectation_catalog_ref`, giving an arm-visible catalog a direct
   path to scorer-only material if the catalog is exposed.
2. `arm-input-manifest.schema.json` accepts arbitrary JSON in each field’s
   `value`.
3. `notScorerField` rejects only a finite set of exact field paths, not nested
   scorer members under an otherwise permitted object.
4. `input_profile_ref` is an unconstrained string and is not schema-bound to
   `arm_id`.
5. `field_allowlist_checked=true` is an assertion; it is not derived from the
   selected profile.
6. The D result’s raw arm fields similarly carry unconstrained values and an
   allowlist reference without proving membership.

Therefore OL-01 and the catalog portion of OL-02 are not safely closed, and
OL-03/OL-04 remain viable schema-level bypasses. OL-05 and OL-07 pass by
inspection: scenario identifiers and declared timing metadata do not encode
the expected scientific answer. OL-06 fails through the direct scorer-catalog
reference. OL-08 is deferred to future implementation because no error-channel
schema is defined, but it does not repair the blocking input boundary.

## E. Per-arm information boundary and fairness

The declared arm capabilities are credible in substance:

- ARM-A has ordinary durable task/attempt/executor state.
- ARM-B adds ordinary provider acceptance/state/reconciliation.
- ARM-C adds classifier features derived from ARM-B-visible information.
- ARM-D adds portable records, declared profiles, trust roots, and supplied
  evidence.

The profiles do not deliberately withhold the ordinary provider read promised
to ARM-B or ARM-C. They also forbid Accord outcome labels in baseline arms.

The problem is enforceability rather than the intended arm comparison. The
manifest has no selected-profile foreign-key or field-membership constraint,
and generic object values can carry fields not declared by the profile. The
fairness prose is credible, but its machine boundary is not closed.

## F. Settlement vocabulary re-review

The R1 map is a meaningful improvement. It explicitly keeps native C axes,
requires exact predicate/stage binding for strong occurrence projections,
distinguishes observation-only absence from complete negative evidence, and
keeps rejected input separate from factual non-occurrence.

The following semantic conclusions are supported by the map and C model:

- provider acceptance alone cannot settle a downstream effect;
- incomplete empty reads cannot establish non-occurrence;
- complete negative evidence may establish only profile-bounded
  non-occurrence;
- unknown-terminal results are profile-scoped rather than metaphysically
  final;
- rejected evidence does not erase or negate external history;
- causality and exactly-once are not implied.

The remaining defect is at the A schema boundary. A `VERIFIED` result can be
structurally valid without carrying a native C result reference or the named
mapping profile. The normative map rejects such a projection, but the A schema
does not independently require the evidence needed to demonstrate that the
map was applied. This is why `E2E-MAJOR-001` is partially rather than fully
closed.

## G. Authority axes and temporal validity

`E2E-MAJOR-002` is independently closed.

The D schema requires separate objects for:

- B grant relation;
- B effective-authority composition state;
- event-time validity at derivation, admission, dispatch, occurrence, and
  verification.

The combination `ATTENUATED` + `POSSIBLE_WIDENING` + invalid dispatch-time
authority + supported factual occurrence remains representable. No residual
`relation_or_state` field or prose implication from attenuation to
authorization was found.

Revocation and expiry do not rewrite historical dispatch or occurrence.

## H. Typed lineage

The R1 typed-reference shape is a real improvement and distinguishes
experiment, result, verifier, authority, settlement, bundle, manifest, and
mapping record categories.

It does not provide referential integrity by itself:

- `record_id` is an arbitrary non-empty string;
- top-level `experiment_run_id` is not constrained equal to the lineage run
  reference;
- result, verifier, authority, and settlement references need not resolve to
  supplied records;
- the schemas do not bind referenced records to the current effect, scenario,
  arm, or run;
- an arbitrary provider operation ID can still be copied into an untyped
  `attempt_id` string.

A future resolver can detect these conditions if it is implemented and given
all referenced records. The portable schemas do not yet make the wrong-run or
foreign-result attack invalid at the boundary.

## I. Predicate, stage, and identity binding

R1 correctly added structured binding descriptors and D requires them for
task/effect identities, attempts, and observed evidence. The C profile also
supports profile-controlled binding requirements and conservative wrong-binding
policies.

The remaining gap is consistency enforcement:

- A settlement-relevant `effect_binding` remains optional on A portable
  attempt, observation, and evidence records;
- D duplicates effect/predicate/stage information in multiple locations;
- the D schema does not constrain those duplicated values to be equal;
- UNKNOWN or NOT_APPLICABLE slots are structurally representable alongside a
  stronger-looking D result unless the future verifier applies the map and
  active profile.

Thus the model can represent correct rejection, but a schema-valid inconsistent
record can still be constructed. `E2E-MAJOR-004` is partially closed.

## J. Regression audit

The main R1 semantic repair did not regress authority/effect orthogonality,
retry identity, negative evidence, staged effects, or transport neutrality.

The following R1 boundary regressions or residual gaps were found:

- direct public-to-scorer catalog reference;
- allowlist membership deferred to an assertion and future harness;
- unconstrained nested manifest/raw-output values;
- A projection map not required by the A result schema;
- typed references without resolver/equality requirements;
- binding descriptors without cross-field equality constraints.

These are recorded in
[accord-02e-r1-review-findings.json](./accord-02e-r1-review-findings.json).

## K. Compatibility conclusion

The fresh 44-row matrix is in
[accord-02e-r1-compatibility-matrix.json](./accord-02e-r1-compatibility-matrix.json).

The semantic axes are largely compatible, but the following rows are not
acceptance-ready:

- public catalog to scorer-only catalog path;
- arm manifest to selected profile membership;
- nested field/raw-output values to scorer exclusion;
- standalone A projection to native C result;
- typed references to actual supplied-record equality;
- duplicated predicate/stage/effect bindings to one settlement target.

## L. Experiment falsifiability and baseline fairness

The design remains falsifiable. Accord can lose to ARM-B or ARM-C, excessive
UNKNOWN can make it unattractive, categorical failures remain disqualifying,
and no expectation record forces a system result to match the scorer truth.

The primary metric definitions remain present and the separate score record can
hold oracle outcome, normalized interpretation, metric contributions,
exclusion/rerun status, and categorical failures. However, normalization and
lineage still require future resolver/adapter checks; the score schema does
not itself prove that the referenced result belongs to the current run.

## M. Acceptance readiness

The criteria for READY or READY_WITH_NONBLOCKING_NOTES are not satisfied:

- an original BLOCKING finding remains open;
- four original MAJOR findings are only partially closed;
- the public arm-visible object graph can reach scorer material;
- selected profile membership and nested value safety are not machine-closed;
- standalone A projections and cross-record lineage remain externally
  constrained rather than schema-bound.

**ACCORD-02 MUST NOT PROCEED TO ACCEPTANCE.**

The bounded next step would be a new remediation limited to these review
findings, followed by another fresh integrated review. This task performs no
remediation.

## N. Review questions

1. Is `E2E-BLOCK-001` independently closed? **No.**
2. Can scorer expectations reach an arm through a schema-valid path? **Yes.**
3. Can an extension or nested value smuggle scorer truth? **Yes.**
4. Is the A/C mapping normative and conservative? **Yes, but not schema-bound in A.**
5. Can incomplete absence become non-occurrence? **Not under the normative C/map rules; the A schema does not prove map application.**
6. Can `ATTENUATED` become `AUTHORIZED` through translation? **No.**
7. Can the three authority axes coexist independently? **Yes.**
8. Is lineage typed? **Yes.**
9. Is foreign lineage automatically rejected? **No; external resolution is still required.**
10. Can one predicate/stage settle another? **Not under the intended C rules, but the D/A schemas do not independently enforce equality.**
11. Can ARM-C consume Accord-only outcome semantics through the declared boundary? **Yes, via the unresolved generic-value/profile-membership gap.**
12. Did allowlists weaken ARM-B? **No in declared capability; the enforcement gap is the problem.**
13. Does external verification require hidden/private state? **The intended portable path does not, but lineage resolution must be supplied explicitly.**
14. Can Accord lose? **Yes.**
15. Can universal UNKNOWN fail empirically? **Yes.**
16. Has an experiment run? **No.**
17. Has empirical benefit been demonstrated? **No.**
18. Are BLOCKING findings open? **Yes.**
19. Are MAJOR findings open or partial? **Yes.**
20. Is acceptance readiness achieved? **No.**
