# ACCORD-02B — Effective-Authority Composition

Status: candidate analysis and composition contract. This document defines no
enforcement engine, ledger, policy decision, or execution mediator.

## 1. Purpose

Grant-level attenuation asks whether one represented child grant is no wider
than one represented parent grant. Effective-authority analysis asks what a
principal can exercise through all active grants, sibling combinations, parent-
mediated paths, and contextual rules. The second claim is strictly stronger.

```text
GrantAuthority(G)
  = authority explicitly represented by grant G

EffectiveAuthority(P, C, T, G, R)
  = authority principal P may exercise in context C at time T
    through graph G under composition profile R
```

The model must not infer `EffectiveAuthority ⊑ ParentAuthority` merely because
every individual child grant compared so far is `ATTENUATED`.

## 2. Inputs and outputs

### 2.1 Inputs

The conceptual operator is:

```text
EffectiveAuthority(principal, context, time, graph, composition_profile)
  -> EffectiveAuthorityResult
```

Inputs are:

- principal and role records;
- active authority-grant IDs and parent/delegation links;
- task, intent, effect, and mediation links from ACCORD-02A;
- per-grant dimension values and profile IDs;
- sibling sets and composition mode;
- supplied expiry and revocation observations;
- supplied quantitative reservation/consumption evidence;
- contextual request, approval, audience, and channel values;
- the comparison and composition profile.

The operator MUST NOT consult hidden Accord state or invent missing revocation,
budget, provider, or policy facts.

### 2.2 Output

The result contains:

- `principal_id` and evaluation context;
- active grant IDs considered;
- direct exercise capabilities;
- mediated/induced exercise paths;
- composition profile;
- a capability summary with source grant/path references;
- per-dimension and aggregate containment outcomes;
- unresolved dimensions and reason codes;
- conflicts;
- `possible_widening_paths`;
- whether effective-authority containment is conclusive.

The result is an analysis artifact. It does not authorize dispatch and does not
replace Ananke's production authorization decision.

## 3. Composition profiles

Composition policy is explicit. A profile includes:

```text
CompositionProfile = {
  profile_id,
  sibling_mode,
  overlap_mode,
  action_combination_mode,
  quantitative_mode,
  mediation_mode,
  revocation_mode,
  expiry_mode,
  unknown_policy,
  transitivity_policy
}
```

Candidate modes are:

| Dimension | Candidate modes | Conservative default |
| --- | --- | --- |
| Siblings | `DISJOINT_SCOPES`, `OVERLAP_RETAINED`, `MUTUALLY_EXCLUSIVE`, `SHARED_POOL`, `RESERVED_SUBALLOCATION`, `CONTEXTUAL`, `NO_COMPOSITION` | `NO_COMPOSITION` |
| Overlap | `UNION_IF_PROVEN`, `RETAIN_SEPARATE`, `CONFLICT` | `RETAIN_SEPARATE` |
| Actions | `INDEPENDENT`, `COMPLEMENTARY_WORKFLOW`, `CLOSED_ACTION_ALGEBRA`, `UNKNOWN` | `UNKNOWN` |
| Quantities | `INDEPENDENT_CAP`, `SHARED_POOL`, `RESERVED_SUBALLOCATION`, `NON_COMPOSABLE` | `NON_COMPOSABLE` |
| Mediation | `DENY_UNBOUND`, `PARENT_INTENT_BOUND`, `PARENT_MAY_ACT_FOR_CHILD`, `UNMODELLED` | `DENY_UNBOUND` |
| Revocation | `CHECK_AT_EACH_EVENT`, `ISSUER_STATUS`, `UNAVAILABLE` | `CHECK_AT_EACH_EVENT` |
| Unknowns | `FAIL_CLOSED`, `SURFACE_UNKNOWN` | `SURFACE_UNKNOWN` |

The profile is part of the result. Two effective-authority results from
different profiles are not silently comparable.

## 4. Sibling cases

### 4.1 Disjoint resource siblings

Parent grants `{A,B}`. Child A has `{A}` and Child B has `{B}`. Each direct
comparison is `ATTENUATED`. The composition may be `EQUIVALENT` to the parent's
resource set only under `DISJOINT_SCOPES` plus `UNION_IF_PROVEN`, with compatible
action, context, audience, time, and quantitative dimensions.

Without those declarations, the result is `UNKNOWN` or `NO_COMPOSITION`, not an
automatic union.

### 4.2 Overlapping resource siblings

If both children address `{A}`, the graph retains two grants and two possible
paths. The overlap can produce duplicate authority, competing quantitative
consumption, or a semantic duplicate effect. The profile may retain them as
separate (`OVERLAP_RETAINED`), reject composition, or apply an explicit shared
pool. It must not discard the overlap.

### 4.3 Disjoint action siblings

Child A has `read`; Child B has `update`, each on a parent-approved resource.
They remain separate capabilities unless the profile declares a closed action
algebra. Scope containment for each grant does not prove safety of the combined
workflow.

### 4.4 Complementary action siblings

One sibling may prepare a change while another may approve or execute it. Each
may be individually contained while the pair enables a workflow unavailable to
either sibling. The result must identify the composed action path and whether
the parent explicitly authorized that combination. Otherwise it reports a
possible widening path or `UNKNOWN`.

### 4.5 Separate grants forming a new workflow

Composition can be wider in capability shape without any single grant widening.
The profile must declare whether workflow capabilities are first-class. If not,
the operator reports `workflow_composition=UNSUPPORTED` or `UNKNOWN` rather than
assuming that the union is safe.

## 5. Quantitative composition

Quantitative dimensions are not one static lattice. The model distinguishes:

### 5.1 Independent cap

Each child has its own cap, but there is no claim that their sum is bounded by a
parent aggregate cap. This can preserve per-action attenuation while failing
aggregate containment.

### 5.2 Reserved suballocation

A parent aggregate cap is partitioned into explicit reservations. For parent
100, Child A reservation 40 and Child B reservation 60, the composition may be
contained if the record includes valid allocation evidence, non-overlap, and
consumption semantics. The model does not maintain the allocation ledger.

### 5.3 Shared parent pool

For parent aggregate cap 100, two children each saying cap 80 do not prove a
shared bound. Without a supplied reservation or accounting snapshot, the result
is `UNKNOWN` with `possible_widening_paths=true`. With evidence that the pool has
only 100 remaining and admission serializes consumption, the profile may derive
a bounded residual result, subject to freshness.

### 5.4 Non-composable limits

Rates, quotas, retention windows, and provider-specific limits may not admit a
safe static comparison. The profile returns `UNSUPPORTED` or `UNKNOWN` and keeps
the dimension visible.

### 5.5 Required quantitative fields

When a profile evaluates state-dependent limits, a grant or composition record
may carry:

- `quantity_kind` and units;
- `scope_key` (resource/action/counterparty);
- `static_limit`;
- `allocation_mode`;
- `allocation_id` and `parent_allocation_id`;
- `reserved_amount`;
- `consumed_amount`;
- `remaining_amount`;
- `remaining_as_of`;
- `accounting_snapshot_ref`;
- `allocation_evidence_ref`.

Missing state is not zero remaining and is not unlimited remaining.

## 6. Parent-mediated authority and laundering

### 6.1 Direct versus induced exercise

Direct child exercise is supported by the child grant's own action/resource /
context dimensions. Induced or mediated exercise is a path in which a child
requests, causes, or benefits from a parent or other principal exercising a
capability held by that principal.

Both paths are represented without relabelling the parent grant as a child grant.

```text
child task
  -> request/effect bound to child intent
  -> parent-mediated task/effect
  -> parent grant authorizes action X
  -> provider effect X
```

The path links `intent_id`, `task_id`, `delegation_id`, `effect_id`, parent grant,
mediator, and provider/evidence records where present.

### 6.2 Possible laundering

The path is a possible authority-laundering or confused-deputy path when:

- the child lacks direct authority for X;
- the parent retains authority for X;
- the child can cause the parent to exercise X;
- the parent action is not bound to a parent-approved intent/effect, recipient,
  purpose, or approval that excludes the child's unbounded request;
- the resulting benefit or effect is attributable to the child's request or
  context.

The result is `child_grant_relation=ATTENUATED` together with
`effective_authority=MEDIATED_POSSIBLE_WIDENING`. It is not `WIDENED` direct
child grant authority unless the child grant itself contains X.

### 6.3 Properly bound parent mediation

Parent assistance is not automatically laundering. If the parent action is
explicitly bound to the parent's own approved intent/effect, recipient, purpose,
and authority decision, and the profile prohibits the child from substituting
those bindings, the result may be `SAFE_PARENT_MEDIATION` for this model. That
does not prove the external effect occurred.

### 6.4 Confused deputy distinction

Authority laundering describes an effective-authority path. Confused-deputy
behaviour describes a principal using its authority on behalf of another without
the intended restriction or identity binding. The concepts overlap but are not
identical. A legitimate parent-mediated action may be neither laundering nor a
confused deputy when its intent/effect/approval bindings are explicit.

## 7. Expiry and revocation

The result keeps these predicates separate:

```text
valid_at_derivation
valid_at_admission
valid_at_dispatch
valid_at_observation
valid_at_verification
currently_valid
```

Each predicate has a state (`VALID`, `REVOKED`, `EXPIRED`, `UNKNOWN`, or
`NOT_EVALUATED`), an evaluation time, and an evidence reference.

### 7.1 Revocation cases

| Case | Required interpretation |
| --- | --- |
| Revoked before derivation | No valid child derivation under the profile. |
| Revoked after child derivation, before dispatch | Historical derivation may remain recorded; admission/dispatch is revoked or unknown and must not be treated as valid. |
| Revoked after dispatch | Dispatch history is not erased; subsequent retries/admissions require fresh authority. |
| Revoked after occurrence | The occurrence is not retroactively undone; settlement reports authority-at-dispatch separately from current validity. |
| Revocation unavailable | Current validity is `UNKNOWN`; no invented revocation state. |
| Stale revocation view | The result is bounded by its `as_of` and freshness; it cannot claim current validity. |

Revocation is not compensation, cancellation, or erasure. Those semantics are
deferred and a portable record may reference a later compensation/saga decision
without defining one here.

### 7.2 Expiry and ordering

The model distinguishes:

- `issued_at` — issuer creation time;
- `not_before` — earliest valid use;
- `expires_at` — latest valid use under the grant profile;
- derivation time;
- admission time;
- dispatch time;
- observation time;
- verification time.

A child `not_before` earlier than the parent is widening. A child `expires_at`
later than the parent is widening. If timestamps cannot be ordered under the
clock profile, the comparison is `UNKNOWN` rather than fabricated precision.

## 8. Composition result states

The effective-authority result uses these states:

| State | Meaning |
| --- | --- |
| `CONTAINED` | All considered direct and mediated paths are bounded under a compatible profile with no unresolved authoritative dimensions. |
| `POSSIBLE_WIDENING` | At least one path may exceed the intended parent boundary, but the evidence does not establish an actual widened grant. |
| `WIDENED` | A direct grant or fully evaluated composition demonstrably exceeds the boundary. |
| `UNKNOWN` | Required state, accounting, revocation, context, or profile evidence is unresolved. |
| `UNSUPPORTED` | The selected profile cannot evaluate a required dimension or composition operator. |
| `CONFLICTING` | Supplied authority or composition evidence is mutually inconsistent. |

`POSSIBLE_WIDENING` is deliberately not `WIDENED`. It is a research signal and
may become a categorical failure under a later experimental profile.

## 9. No universal composition theorem

Grant-level attenuation may be transitive for closed, set-like, stateless
dimensions. It does not automatically imply effective-authority containment in
the presence of:

- sibling aggregation;
- parent-mediated laundering;
- context-dependent action combinations;
- stateful budgets or rates;
- expiry/revocation changes;
- incompatible profiles;
- resource expressions without a common containment algebra.

Any future claim must name its graph scope, composition profile, time/evidence
assumptions, and mediation boundary.
