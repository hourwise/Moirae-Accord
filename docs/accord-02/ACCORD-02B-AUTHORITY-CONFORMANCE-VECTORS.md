# ACCORD-02B — Authority Conformance Vectors

Status: offline specification vectors. The vectors are not executable authority
enforcement tests and do not authorize any action.

The machine-readable vectors are in
[accord-02b-authority-test-vectors.json](examples/accord-02b-authority-test-vectors.json).
The structural profile and result schemas are
[accord-02b-authority-profile.schema.json](schema/accord-02b-authority-profile.schema.json)
and
[accord-02b-authority-relation-result.schema.json](schema/accord-02b-authority-relation-result.schema.json).

## 1. Vector conventions

Every vector names its profile, parent/child grant IDs, dimensions, expected
direct relation, and—where relevant—expected effective-authority composition.
The expected result is evaluated over synthetic data only.

The direct relation is not a production authorization decision. `ATTENUATED`
means only that every authoritative dimension represented by the active profile
is comparable and no wider. It does not prove effective-authority containment,
effect occurrence, or safe use through unmediated paths.

## 2. Required vector summary

| ID | Scenario | Expected result |
| --- | --- | --- |
| `vector-01-simple-attenuation` | Parent resources `{A,B}`, actions `{read,update}`; child `{A}`, `{read}`. | `ATTENUATED` |
| `vector-02-action-widening` | Parent permits `read`; child requests `delete`. | `WIDENED` |
| `vector-03-expiry-widening` | Child expiry is later than parent expiry. | `WIDENED` |
| `vector-04-multi-hop-valid` | `G0 → G1 → G2`, all dimensions narrow. | Adjacent and ancestor comparisons valid; `G2 ⊑ G0`. |
| `vector-05-unknown-authority-extension` | Child contains a profile-unknown authority-bearing extension. | `UNKNOWN` or `UNSUPPORTED`, never `ATTENUATED` |
| `vector-06-sibling-resource-separation` | Siblings cover disjoint resources. | Individual `ATTENUATED`; composition only contained under explicit disjoint-union profile. |
| `vector-07-sibling-shared-budget-failure` | Parent aggregate 100; children each claim 80 under shared-pool semantics. | `UNKNOWN`, possible widening; no safe aggregate conclusion. |
| `vector-08-sibling-reserved-budgets` | Parent 100; reservations 40 and 60. | Contained under valid reserved-allocation evidence. |
| `vector-09-parent-mediated-laundering` | Child lacks `publish`; loosely bound request causes parent to publish. | Child direct relation `ATTENUATED`; effective authority `POSSIBLE_WIDENING`. |
| `vector-10-bound-parent-mediation` | Parent action is bound to its own approved intent/effect. | No false direct child widening; safe mediation state. |
| `vector-11-revocation-before-dispatch` | Valid derivation later revoked before dispatch. | Derivation history valid; dispatch validity `REVOKED`. |
| `vector-12-revocation-after-dispatch` | Dispatch precedes revocation. | Historical dispatch preserved; effect not retroactively erased. |
| `vector-13-task-only-delegation` | Task edge exists with no authority edge/grant. | No authority transfer inferred. |
| `vector-14-transport-metadata-spoofing` | Transport claims broader scope than grant. | Transport ignored; direct relation remains grant-derived. |
| `vector-15-complementary-siblings` | One sibling prepares; another approves/executes. | Individual attenuation; composed workflow `UNKNOWN`/possible widening unless declared. |
| `vector-16-approval-omission` | Parent requires approval A; child omits the binding. | `WIDENED` under explicit-inheritance profile. |
| `vector-17-resource-wildcard` | Parent finite resource set; child provider wildcard. | `UNSUPPORTED` or `INCOMPARABLE`, never assumed narrower. |
| `vector-18-profile-mismatch` | Parent and child use incompatible authority profiles. | `UNSUPPORTED` or `UNKNOWN`; no transitive conclusion. |

## 3. Interpretation of selected vectors

### Vector 1 — simple attenuation

This is the closed-world baseline. Resource and action sets are finite, all
identities and profiles match, and time/depth/context are either equal or
explicitly bounded. The expected direct relation is `ATTENUATED`.

### Vector 2 — action widening

The resource is unchanged, but `delete` is not in the parent's action set. The
single widened action is sufficient for aggregate `WIDENED`.

### Vector 3 — expiry widening

The child remains otherwise narrow but expires after the parent. A single time
dimension is sufficient for `WIDENED`.

### Vector 4 — multi-hop valid attenuation

The vector requires direct comparisons for `G1/G0` and `G2/G1`, then permits the
ancestor conclusion only because the profile declares the dimensions transitive
and stateless. It is not a universal transitivity test for budgets, revocation,
or arbitrary predicates.

### Vectors 5, 17, and 18 — non-comparability

The model surfaces uncertainty rather than interpreting unknown extensions,
wildcards, or incompatible profiles as narrowing. The expected outcome is not
necessarily one fixed status because a deployment profile may distinguish
`UNKNOWN` from `UNSUPPORTED`; both block `ATTENUATED`.

### Vectors 6–8 — sibling composition

Each child can pass direct attenuation while the composition requires a declared
policy. Vector 7 deliberately has two 80-unit claims against a 100-unit shared
pool with no allocation evidence. It cannot be declared contained. Vector 8
supplies reservations that sum to the parent cap and can be contained under the
reserved-allocation profile.

### Vectors 9–10 — mediated authority

Vector 9 does not rewrite the child grant as widened. It records a possible
effective-authority laundering path. Vector 10 shows why parent mediation is
not automatically laundering when parent intent, approval, recipient, effect,
and authority bindings are explicit.

### Vectors 11–12 — revocation timing

Revocation is evaluated separately at derivation, admission, dispatch, and
verification. A later revocation cannot erase a historical dispatch or prove
that an already occurring external effect did not happen.

### Vectors 13–15 — missing authority and workflow composition

Task delegation alone produces no authority transfer. Transport metadata cannot
broaden a grant. Complementary siblings may form a workflow capability even when
each grant is individually narrow; absent a declared action-composition profile,
the model surfaces the uncertainty.

## 4. Later test obligations

These vectors are intended to seed later property-based or model-based testing:

- generate finite set restrictions and check subset transitivity;
- generate depth and time intervals and check boundary conditions;
- mutate or add authority-bearing extensions and require fail-closed results;
- generate overlapping and complementary sibling graphs;
- vary budget allocation evidence and retention windows;
- inject revocation between lifecycle events;
- compare direct and mediated exercise paths;
- substitute local, MCP-shaped, and A2A-shaped transport envelopes;
- verify that no result itself authorizes execution.

No test runner, property generator, ledger, or policy engine is created in this
slice.
