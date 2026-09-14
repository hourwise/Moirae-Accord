# ACCORD-02B — Authority Attenuation Model

Status: candidate specification and conformance model. This document is not an
authority enforcement implementation.

## 1. Scope and ownership boundary

ACCORD-02B defines a portable, component-wise relation for analysing claimed
authority grants and their composition. It makes the accepted secondary
research question falsifiable:

> Under multi-hop delegation and sibling composition, does grant-level
> monotonic attenuation bound effective authority when parent-mediated
> laundering, composition, expiry, revocation, and resource dimensions are
> varied?

The model is a relation/conformance profile over the ACCORD-02A portable record
model. It may describe a grant, compare a child grant with a parent grant, and
report unresolved dimensions. It does not enforce authority.

Ananke remains the owner of authority derivation, grant validation, policy,
approval binding, and mediated dispatch admission. Accord MUST NOT mint
authority, make a production authorization decision, or become an execution
mediator. `ACCORD NEVER MINTS AUTHORITY` is a boundary rule, not a relation
implementation.

The model therefore answers only questions such as:

- what authority a grant explicitly represents;
- whether the supplied child representation is component-wise narrower than the
  supplied parent under a named profile;
- whether composition has an identified possible widening path;
- which dimensions cannot be compared from the supplied records.

It does not answer whether a real-world policy allowed an action or whether an
unmediated principal exercised an external capability.

## 2. Terminology

| Term | Normative meaning |
| --- | --- |
| Principal | A named party or system role from ACCORD-02A. |
| Grant | A portable representation of declared authority, identified by `grant_id`. |
| Parent grant | A grant alleged to constrain a derived child grant. |
| Child grant | A grant derived from, or claimed to be derived from, a parent grant. |
| Grant authority | Authority explicitly represented by one particular grant. |
| Effective authority | Authority a principal may actually exercise through the declared mediated graph and composition rules. |
| Authority delegation | Transfer/derivation of a grant relationship. It requires an authority edge and authority-owner evidence. |
| Task delegation | Assignment of work. It does not transfer authority by itself. |
| Attenuation | A child representation that is no wider than its parent under every authoritative, comparable dimension. |
| Widening | A demonstrable child or composition result that permits an authority outside the parent boundary. |
| Composition | Combining active grants or mediated paths under an explicit composition profile. |
| Aggregation | A composition operation that combines scope, actions, budgets, or context. |
| Sibling | A child grant derived from the same parent grant or authority allocation. |
| Ancestor | Any earlier grant in a derivation chain. |
| Expiry | Time validity ending at a declared `expires_at`. |
| Revocation | A state change that makes a grant or decision no longer valid under a named revocation profile. |
| Resource scope | The resources a grant may address. |
| Action scope | The operations a grant may perform on those resources. |
| Quantitative constraint | A count, amount, quota, rate, or budget constraint. |
| Contextual constraint | A purpose, approval, task, effect, recipient, environment, or channel predicate. |

The model never uses “same permissions,” “less access,” or “inherits access” as
a relation. It names the relevant dimension and outcome instead.

## 3. Authority grant model

An authority grant is modelled as:

```text
Grant G = {
  grant_id,
  issuer_principal_id,
  subject_principal_id,
  audience,
  authority_profile,
  dimensions,
  parent_grant_id?,
  delegation_id?,
  approval_ref?,
  issued_at,
  not_before?,
  expires_at?,
  integrity
}
```

`dimensions` is a profile-declared map. The minimum candidate dimensions are:

1. subject/principal;
2. resource;
3. action/operation;
4. quantity/budget/usage;
5. time;
6. delegation depth;
7. audience/recipient/counterparty;
8. context/environment;
9. approval requirements;
10. task/effect identity binding.

Profiles MAY omit dimensions that do not apply, but omission is meaningful only
when the profile explicitly declares the dimension `not_applicable`. An omitted
authority-bearing restriction is not automatically a narrower value.

### 3.1 Declared dimensions and unknowns

Each profile declares:

- the dimensions it understands;
- whether each dimension is authority-bearing;
- the value language and comparator for that dimension;
- whether the comparator is closed-world and decidable;
- how missing, redacted, or unknown values are handled;
- whether the dimension participates in sibling composition.

If a grant contains an authority-bearing dimension or extension the profile does
not understand, comparison MUST return `UNSUPPORTED` or `UNKNOWN`. It MUST NOT
return `ATTENUATED` by ignoring the field.

Descriptive metadata may be ignored only when the profile explicitly marks it
non-authoritative. The extension handling is compatible with ACCORD-02A:
unknown authority-bearing extensions block a conclusive attenuation result.

## 4. Dimension-wise attenuation

The relation `child_authority ⊑ parent_authority` means:

> Under the declared authority profile, every authoritative child dimension is
> either equivalent to or narrower than the corresponding parent dimension, all
> required derivation and identity links are valid, and no unresolved
> authority-bearing dimension prevents that conclusion.

The symbol is shorthand. A conforming result MUST include prose and structured
per-dimension outcomes.

### 4.1 Subject / principal

The child subject is not compared as a simple set subset because delegation may
change the exercising principal. A profile MUST state how a parent may name
delegatees.

- Same subject with a valid derivation edge: `EQUIVALENT` for this dimension.
- Child subject explicitly permitted by the parent delegation constraint and
  supported by an authority-delegation edge: `ATTENUATED`.
- Child subject outside the parent delegatee constraint: `WIDENED` or
  `INCONSISTENT`, according to the profile.
- No comparable delegatee constraint or unresolvable principal relation:
  `UNKNOWN` or `UNSUPPORTED`.

A task-delegation edge alone cannot satisfy this dimension.

### 4.2 Resource scope

Resource comparison is profile-specific:

- exact identifiers: child set MUST be a subset of parent set;
- finite sets: child members MUST be a subset of parent members;
- namespace/path prefixes: the profile MUST define hierarchy and boundary
  escaping before subset comparison;
- hierarchical provider resources: a provider profile MUST define containment;
- wildcards and provider-specific predicates: comparison is
  `UNSUPPORTED`/`INCOMPARABLE` unless a trusted comparator is declared.

Parent `{A,B}` and child `{A}` are `ATTENUATED`. A child wildcard is not assumed
to be narrower than a parent finite set merely because it is syntactically
shorter.

### 4.3 Action / operation scope

Actions are compared independently from resources. A profile MUST declare either
an exact action set or an explicit action implication relation.

For a closed action set, the child action set MUST be a subset of the parent
action set. There is no default implication between `read`, `update`, `delete`,
`transfer`, `approve`, or `publish`.

For example, parent `{resource:A, action:read}` and child
`{resource:A, action:delete}` is `WIDENED`, even though the resource is
unchanged. Resource attenuation cannot compensate for action widening.

### 4.4 Quantity / budget / usage

Static quantity is compared component-wise when the profile defines units,
scope, and arithmetic:

- child per-action maximum MUST be no greater than parent per-action maximum;
- child count limit MUST be no greater than parent count limit;
- child static aggregate cap MUST be no greater than the parent cap.

Remaining authority is different. A parent cap of 100 and a child grant saying
“remaining 80” cannot be compared conclusively without knowing whether 80 is a
reserved allocation, an independently repeated cap, or a live remaining value.
State-dependent comparisons use the quantitative accounting profile in
`ACCORD-02B-EFFECTIVE-AUTHORITY-COMPOSITION.md`.

### 4.5 Time

Under a monotonic time profile:

- child `not_before` MUST be no earlier than parent `not_before`;
- child `expires_at` MUST be no later than parent `expires_at`;
- child validity MUST intersect the parent validity interval;
- missing or uncertain ordering returns `UNKNOWN`.

An expiry that extends beyond the parent is `WIDENED`, not “almost
attenuated.” Time is evaluated at a declared verification time; it is not
silently converted to local wall-clock truth.

### 4.6 Delegation depth

Let `remaining_depth(G)` be the maximum number of further authority-delegation
edges permitted by the profile. A child derived through one authority edge MUST
satisfy:

```text
remaining_depth(child) <= remaining_depth(parent) - 1
```

An omitted parent bound, a negative result, or an unbounded child where the
parent is bounded is `WIDENED` or `UNKNOWN` according to whether the widening is
demonstrable. An authority profile that does not model depth returns
`UNSUPPORTED`; it does not infer arbitrary recursion.

### 4.7 Audience / recipient / counterparty

Child audience and recipient sets MUST be subsets of the parent's allowed
audience/counterparty set under a declared identity comparator. A provider or
recipient wildcard is not automatically safe. If audience semantics are
provider-specific and no comparator is supplied, return `UNSUPPORTED`.

### 4.8 Context and environmental predicates

Context comparison requires a profile-defined implication checker. A child may
add a purpose, task, effect, approval, environment, or channel restriction, but
it MUST NOT discard a parent predicate.

If the parent requires `approval=A` and the child omits it, the child is
`WIDENED` under the explicit-inheritance profile. A profile that uses lossless
implicit inheritance MAY classify it `ATTENUATED`, but the inheritance rule must
be present in the profile and evidence. Arbitrary predicate implication is not
assumed decidable; unsupported implication returns `UNSUPPORTED` or `UNKNOWN`.

### 4.9 Approval requirements

Approval is an authority-bearing contextual dimension when the parent grant
requires it. A child MUST preserve the approval reference and its binding, or
introduce a stricter requirement. The record may reference Ananke's approval
decision; this model does not recreate approval policy.

### 4.10 Task/effect binding

When the parent binds authority to `intent_id`, `task_id`, `effect_id`, or a
declared channel, a child MUST preserve or narrow that binding. A child grant
that drops a required effect or task binding is not attenuated under the
profile. The binding itself does not prove that an effect occurred.

## 5. Relation outcomes

The comparison result is not Boolean. It has one aggregate outcome and one
outcome for every declared authoritative dimension.

| Outcome | Exact meaning |
| --- | --- |
| `ATTENUATED` | Every required dimension is comparable and child-narrower; at least one dimension is narrower. |
| `EQUIVALENT` | Every required dimension is comparable and semantically equivalent. |
| `WIDENED` | At least one authoritative dimension demonstrably permits more than the parent. |
| `INCOMPARABLE` | Both values are understood but the profile cannot establish a subset/equivalence relation. |
| `UNSUPPORTED` | The active profile has no comparator for a required dimension or extension. |
| `UNKNOWN` | A required value, state, time ordering, or evidence is unavailable or unresolved. |

Aggregate precedence is deterministic:

1. `WIDENED` if any authoritative dimension is demonstrably widened;
2. `UNSUPPORTED` if no widening is demonstrated but a required comparator is
   unsupported;
3. `INCOMPARABLE` if values are understood but neither relation is established;
4. `UNKNOWN` if state/evidence is missing or time-dependent uncertainty remains;
5. `EQUIVALENT` if all dimensions are equivalent;
6. `ATTENUATED` if all dimensions are comparable and every non-equivalent one
   is narrower.

An implementation MAY report several diagnostic statuses, but it MUST NOT
emit `ATTENUATED` when any authoritative dimension remains unresolved.

## 6. Multi-hop delegation

The model supports any finite chain represented by explicit authority edges:

```text
P0 --G0--> P1 --G1--> P2 --G2--> P3
```

For adjacent grants:

```text
G1 ⊑ G0
G2 ⊑ G1
G3 ⊑ G2
```

An ancestor comparison MAY conclude `G3 ⊑ G0` only when:

- every adjacent comparison is `ATTENUATED` or `EQUIVALENT`;
- all links are integrity-valid and profile-compatible;
- the profile declares the compared dimensions transitive;
- no stateful budget, revocation, expiry, or contextual value changed the
  comparison without being included in the evaluation context;
- unknown authority-bearing extensions are absent or understood.

If any condition fails, the ancestor relation is `UNKNOWN`, `UNSUPPORTED`, or
`INCOMPARABLE`; it is not inferred from the chain shape.

The relation is generally a preorder, not a mathematical partial order: two
syntactically different grants may be semantically equivalent. A future profile
may quotient by semantic equivalence if it needs a literal partial order.

## 7. Sibling composition

Two child grants may each be attenuated relative to a parent while their
composition exceeds an intended effective boundary. Sibling comparison and
effective-authority composition are therefore separate claims.

The composition profile MUST declare a sibling mode:

- `DISJOINT_SCOPES` — union only when the profile proves disjointness and the
  parent authorizes the union;
- `OVERLAP_RETAINED` — overlapping scopes remain separately visible and may
  produce a conflict or possible widening path;
- `MUTUALLY_EXCLUSIVE` — only one sibling can be active under supplied evidence;
- `SHARED_POOL` — siblings draw from one explicitly accounted parent pool;
- `RESERVED_SUBALLOCATION` — each sibling consumes a parent allocation proved by
  reservation evidence;
- `CONTEXTUAL` — composition depends on an explicit context predicate;
- `NO_COMPOSITION` — the profile refuses to infer an aggregate capability.

The default is `NO_COMPOSITION`. No universal union rule is safe.

Cases that the model records separately:

1. disjoint resources: may compose to the parent resource set only under an
   explicit union profile;
2. overlapping resources: may duplicate capability or produce conflicting
   quantitative consumption;
3. disjoint actions: may remain independently scoped;
4. complementary actions: may jointly form a workflow capability neither grant
   can exercise alone;
5. independent quantitative caps: are not a shared parent budget;
6. shared parent budget: requires allocation or accounting evidence;
7. separate grants forming an unavailable workflow: requires a contextual
   composition rule and is otherwise `UNKNOWN`/possible widening.

## 8. Unknown and authority-bearing extensions

Unknown authority-bearing dimensions are first-class unresolved results. The
verifier MUST preserve:

- extension namespace and field digest;
- declaring record ID;
- whether the extension is authority-bearing;
- comparator/profile required to evaluate it;
- whether it could widen the parent.

Unknown descriptive metadata MAY be retained without affecting the relation if
the profile declares it non-authoritative. The absence of a field from a child
does not prove attenuation.

## 9. Formal comparison contract

The conceptual comparator is:

```text
CompareGrant(parent, child, profile, context) -> RelationResult
```

It MUST:

1. resolve the two grant records and their principals;
2. verify authority-delegation linkage and profile compatibility;
3. enumerate every parent and child authoritative dimension;
4. apply the declared comparator to each dimension;
5. retain all per-dimension outcomes;
6. calculate the aggregate outcome using the precedence rules;
7. identify unknown, unsupported, incomparable, and widening dimensions;
8. include reason codes and source record references.

It MUST NOT:

- mint or alter a grant;
- infer an authority edge from a task edge;
- use transport metadata as authority;
- consult hidden Ananke or Accord state;
- treat an unresolved dimension as narrower.

The companion relation schema defines the structural result. It does not prove
the signatures, apply a provider policy, or implement arbitrary predicate
implication.

## 10. Required invariants

1. A child grant cannot be considered monotonically attenuated if any
   authoritative dimension demonstrably widens.
2. Omitted parent restrictions do not disappear because a child omits them.
3. Unknown authority-bearing dimensions prevent a conclusive attenuation result
   unless safely covered by the active profile.
4. Task delegation does not imply authority delegation.
5. Authority delegation does not imply task completion.
6. Authority evidence does not prove effect occurrence.
7. Effect evidence cannot create missing authority.
8. Child expiry cannot exceed parent expiry under a monotonic derivation.
9. Child delegation depth cannot exceed the parent's remaining depth.
10. Revocation cannot retroactively undo an external effect that already occurred.
11. Individually attenuated siblings do not automatically imply attenuated
    effective authority.
12. Quantitative grants require explicit composition/accounting semantics.
13. Transport identifiers and metadata cannot widen authority.
14. Parent-mediated execution must not be silently attributed as direct child
    authority.
15. Grant-level attenuation and effective-authority containment are separate
    claims.
16. An Accord conformance result does not replace an Ananke production
    authorization decision.
17. Incomparable values are not equivalent values.
18. A historical derivation-valid result is not a current dispatch-valid result.
19. A grant comparison does not establish that any effect was attempted or
    occurred.

## 11. Design review answers

1. **Can every supported child grant be compared dimension-by-dimension?** Only
   when the active profile declares a comparator for every authoritative
   dimension and the required values/evidence are present. Otherwise the result
   is unresolved.
2. **What happens when a dimension cannot be compared?** It remains a
   per-dimension `INCOMPARABLE`, `UNSUPPORTED`, or `UNKNOWN` result and blocks a
   conclusive `ATTENUATED` aggregate.
3. **Can two individually attenuated grants exceed effective authority?** Yes;
   overlapping siblings, complementary actions, shared budgets, and mediated
   paths can do so.
4. **How does the model expose this?** It records sibling composition mode,
   active grants, direct and mediated paths, unresolved dimensions, and
   `possible_widening_paths` in the effective-authority result.
5. **How are stateful limits represented?** As declared accounting mode plus
   reservation/consumption evidence references. No ledger or distributed
   accounting is implemented here.
6. **Can a parent act for a child on an action the child lacks?** Yes. The model
   represents this as a mediated path, not as direct child grant authority.
7. **How is that distinguished?** Direct exercise is evaluated from the child
   grant; induced/mediated exercise is evaluated from parent intent, effect,
   delegation, and mediation bindings.
8. **How are expiry/revocation treated?** At derivation, admission, dispatch,
   observation, and verification times separately, with `UNKNOWN` for missing
   or stale state.
9. **Can an unknown extension silently widen authority?** No. An unknown
   authority-bearing extension blocks conclusive attenuation.
10. **Does an Accord result authorize execution?** No. It is descriptive
    conformance evidence only.
11. **Is the relation a total order?** Generally no. It is a profile-dependent
    preorder for comparable dimensions with incomparable, unsupported, and
    unknown outcomes.
12. **Is `ATTENUATED` sufficient for safe effective authority under arbitrary
    composition?** No. Effective-authority containment is a separate claim and
    requires explicit composition and mediation analysis.

## 12. Relation to prior art and later work

Subsumption, attenuated credentials, bounded delegation, finite lifetime, and
offline verification have substantial prior art. This slice makes no novelty
claim for them. Its narrower research instrument is the explicit separation of
grant-level comparison from effective authority under sibling composition,
mediated laundering, stateful limits, task/effect linkage, and external evidence.

Later work may use these records for property-based or model-based tests. It must
not silently convert this specification into Ananke enforcement or an Accord
runtime.

## 13. ACCORD-02A compatibility and candidate lineage

This model is compatible with the frozen ACCORD-02A candidate representation.
It reuses `principal`, `grant_id`, `intent_id`, `task_id`, `delegation_id`,
`effect_id`, and `attempt_id`. Dimension maps and composition profiles are
profile-level data associated with an ACCORD-02A Authority Grant; they do not
change the meaning of the underlying record identifiers.

- Authority Grant carries the declared dimension values, parent grant link,
  authority profile, and optional allocation/revocation references.
- Delegation records distinguish `authority_delegation` from `task_delegation`.
- Intent, Task, Effect Attempt, and Evidence Artifact records remain governed by
  ACCORD-02A and are used for contextual/effect linkage only.
- Authority comparison does not alter verifier settlement outcomes or create a
  second effect-state store.
- Revocation and accounting evidence are represented by explicit profile fields
  and ACCORD-02A evidence references; no new runtime record type is required.

No defect in ACCORD-02A blocked this model, so no 02A file was changed.

This candidate is intentionally stacked on the unaccepted ACCORD-02A candidate:

```text
ACCORD-02B branch:
  codex/accord-02b-authority-attenuation-composition
  parent commit: 2e2c036539dcc32f7411b5180e16ba46a7209d1a
  parent tree:   02b147d14f1474c9932ddc6bc5c4a13fc0e84c4c
  parent branch: codex/accord-02a-portable-record-verifier-contract
```

The ACCORD-02A candidate remains unaccepted, unpromoted, and unmodified.
