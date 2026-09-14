# ACCORD-02D — Experimental Design

Status: design-only candidate. This document specifies future controlled
conditions. It does not create a harness, fixture, process, classifier, or
provider integration.

## 1. Design unit and run boundary

The unit of analysis is one scored scenario execution for one arm, effect
surface, transport, delegate behaviour, authority condition, evidence
condition, fault schedule, and seed. A logical `effect_id` may have several
`attempt_id` values; duplicate actual effects are scored from the hidden oracle,
not inferred from attempt count.

Each run receives a stable `run_id` and records the scenario manifest,
configuration digest, code/fixture versions, seed, and all event order needed to
reconstruct the case. A run is not a production transaction and does not imply
that a provider or distributed system was contacted.

## 2. Minimum topology

### 2.1 Delegation depth

The minimum scored topology includes:

```text
P0 ──authority/task delegation──> P1 ──authority/task delegation──> P2
```

The protocol records whether each edge is a task delegation, authority
delegation, or both. Task delegation alone must not be interpreted as authority
delegation.

### 2.2 Siblings and composition

At least one family uses:

```text
       P0
      /  \
    P1    P2
```

and at least one family uses:

```text
P0 ──> P1
       /  \
     P2    P3
```

The scenarios vary disjoint resources, overlapping resources, complementary
actions, shared budgets, reserved suballocation, and parent-mediated actions.

### 2.3 Host and process diversity

Scored cases must include real local process boundaries between at least some of:

- delegate;
- executor/mediator;
- provider/effect-surface fixture;
- observer/reconciler;
- verifier/scorer.

One process may host multiple roles in control cases, but all role assignments
and process/operator boundaries are recorded. Local multi-process execution is
adequate; cloud deployment is not required.

## 3. Delegate behaviour classes

| ID | Behaviour | Required cases |
| --- | --- | --- |
| `HONEST` | Reports what it genuinely believes occurred. | Correct reports, stale state, lost response, and incomplete observation. |
| `LYING_SUCCESS` | Claims success when the oracle says the required predicate did not occur. | False-success and evidence-substitution cases. |
| `LYING_FAILURE` | Claims non-occurrence after the oracle records occurrence. | False-negative and retry/escalation cases. |
| `PARTIALLY_LYING` | Truthful attempt identity or provider response mixed with false outcome, altered attribution, omitted retry, or omitted sibling involvement. | Binding and partial-truth cases. |
| `FAULTY_NON_MALICIOUS` | Reports incorrectly due to crash, stale memory, duplication, reordering, or partial state. | Distributed-failure cases kept distinct from dishonesty. |

Dishonesty and ordinary failure are separate factors. The protocol does not
assume that honest delegates are correct or that lying delegates are the only
source of false claims.

## 4. Effect surfaces

### S1 — Strong-receipt surface

A controlled synthetic surface representing an effect with comparatively strong
evidence affordances:

- stable provider operation identifier;
- explicit provider effect receipt;
- effect/predicate/attempt binding;
- queryable provider ledger/state;
- deterministic synthetic truth oracle;
- optional complete negative query.

The representative predicate is `create_resource`. This surface is a fixture
family, not a claim that all real resource APIs behave this way.

### S2 — Weak/ambiguous surface

A controlled synthetic surface representing weaker affordances:

- acceptance acknowledgement is available;
- final occurrence may be delayed;
- state read may be incomplete or eventually consistent;
- response loss creates ambiguity;
- no universally definitive receipt is exposed.

The representative predicate is `deliver_or_publish_item`. This surface is also
a fixture family, not a universal model of messaging or publication systems.

### Optional S3 — staged surface

If calibrated without changing the research claim, a staged fixture may expose
acceptance, processing, creation, visibility, and recipient acknowledgement as
separate predicates. S3 cannot be substituted for S1/S2 or used to remove the
required weak/strong comparison.

## 5. Transport profiles

### T1 — Local/native fixture

A simple direct message/RPC or equivalent controlled carriage. Transport IDs,
delivery timestamps, and envelope status are ordinary metadata and cannot create
or widen authority.

### T2 — MCP-shaped fixture

An envelope with tool name, call ID, session/context ID, and result metadata.
These fields are deliberately available to test transport-authority injection
and must remain non-authoritative.

### T3 — A2A-shaped fixture

An envelope with context/task/message IDs, artifacts, and task state. Task state
describes lifecycle, not external-effect settlement. T3 is optional for the
first scored experiment; T1 plus either T2 or T3 is mandatory.

Transport variation must not change the semantic meaning of grant, effect,
attempt, observation, evidence, or settlement.

## 6. Reproducible fault model

The following fault IDs are fixed. Each injection is deterministic by fixture
identity or seed and records its intended and observed delivery point.

| ID | Fault |
| --- | --- |
| `F01` | Crash before dispatch. |
| `F02` | Crash after dispatch before response persistence. |
| `F03` | Crash after provider acceptance. |
| `F04` | Lost request. |
| `F05` | Lost response. |
| `F06` | Duplicated request. |
| `F07` | Delayed request. |
| `F08` | Delayed response. |
| `F09` | Reordered observations. |
| `F10` | Stale provider-state read. |
| `F11` | Provider-state read unavailable. |
| `F12` | Partial provider response. |
| `F13` | Idempotency-window expiry. |
| `F14` | Replayed evidence artifact. |
| `F15` | Wrong effect identity. |
| `F16` | Wrong attempt identity. |
| `F17` | Conflicting observations. |
| `F18` | Late observer evidence. |
| `F19` | Corrupted evidence artifact. |
| `F20` | Grant revoked before dispatch. |
| `F21` | Grant revoked after dispatch. |
| `F22` | Grant expired. |
| `F23` | Sibling composition conflict. |
| `F24` | Parent-mediated action outside direct child authority. |

Faults may be combined only when the scenario catalog names the combination and
the combination remains interpretable. An observed failure to inject a planned
fault is a harness/fixture finding, not silently treated as the planned case.

## 7. Idempotency conditions

The future design must include:

1. no idempotency support;
2. a stable idempotency key;
3. a known, queryable key-to-effect binding;
4. incorrect key reuse across logical effects;
5. expiry of the provider idempotency window;
6. duplicate request inside the window;
7. duplicate request after the window.

The oracle records whether one, zero, or multiple external occurrences happened.
The result must distinguish duplicate attempts from duplicate actual effects. No
condition may infer exactly-once from the key alone.

## 8. Evidence conditions

The evidence factor includes, in matched scenarios where relevant:

- E0 delegate assertion;
- executor state;
- transport acknowledgement;
- provider acceptance;
- provider-state re-read;
- provider effect receipt;
- target/recipient acknowledgement;
- observer-distinct corroboration;
- complete negative query;
- stale evidence;
- conflicting evidence.

The experiment records the ACCORD-02C property vector rather than treating E0–E4
as a scalar strength ladder. Integrity, binding, provenance, completeness,
freshness, causal strength, and profile compatibility are scored separately.

## 9. Authority conditions

The authority sub-experiment includes:

1. valid direct authority;
2. valid attenuated child authority;
3. widened child action;
4. widened resource scope;
5. expired authority;
6. revoked-before-dispatch authority;
7. revoked-after-dispatch authority;
8. unknown authority-bearing extension;
9. shared-budget siblings;
10. reserved-budget siblings;
11. parent-mediated possible laundering;
12. task delegation without authority delegation.

For every case the catalog specifies the declared profile, ground-truth
authority relation for the fixture, expected 02B relation, effective-authority
question, and categorical failure relevance.

Authority status and effect occurrence are scored independently. An invalid
authority case may still have a factual occurrence, and a valid authority case
may have no occurrence.

## 10. Core, targeted, and boundary selection

### Core matrix

The core matrix covers every arm, S1/S2, T1 plus one protocol envelope,
honest/lying/faulty behaviour, valid/invalid/unknown authority, weak/strong
evidence, retry/no-retry, and representative faults. Matched seeds and logical
tasks are used across arms.

### Targeted adversarial cases

Targeted cases exercise lying success/failure, partial lies, wrong bindings,
parent-mediated laundering, sibling composition, duplicate effects, conflicting
evidence, idempotency expiry, and revocation timing.

### Boundary cases

Boundary cases place event or observation at either side of authority expiry,
idempotency retention, evidence freshness, timeout, and retry windows. Exact
durations may be calibrated, but the boundary relation and expected semantic
distinction are fixed.

## 11. Randomization and reproducibility

Every run records:

- experiment, fixture, code, and configuration versions;
- configuration digest;
- random seed and deterministic scenario ID;
- arm, effect surface, transport, topology, delegate behaviour;
- authority/evidence profiles;
- fault and timing parameters;
- event ordering and process/observer IDs.

Deterministic adversarial scenarios should replay exactly. Concurrent schedules
need not reproduce bit-for-bit if technically unrealistic; the preserved event
order, evidence, and seed must permit reconstruction of the scored condition.

## 12. Calibration and scored separation

Calibration may tune non-research-critical timeouts, synthetic latency shapes,
fixture quantities, process counts, seed ranges, and classifier parameters.
Calibration may not inspect scored outcomes and then change hypotheses,
definitions, categorical failures, or metric formulas.

The scored set is isolated from classifier fitting and manual rule tweaking. If
a learned classifier is later used, training, calibration, validation, and
scored data are identified by immutable set/version identifiers, with no oracle
labels in baseline features.

## 13. Blinding and information boundaries

The hidden oracle is unavailable to every system-under-test component, including
the Accord verifier, baseline, delegate, provider fixture, and classifier. The
scorer may see it only during adjudication.

Provider-visible evidence may be exposed to an arm only where that arm's
definition permits it. Accord evidence labels are not baseline features. The
authority bundle supplied to ARM-D is portable evidence, not a private policy
database.

## 14. Exclusions, reruns, and replication

### Exclusions

Only predeclared infrastructure reasons qualify: fixture corruption,
oracle corruption, a proven harness defect preventing the assigned condition,
or machine failure before scenario start. The outcome being surprising,
`UNKNOWN`, a duplicate, poor Accord performance, or strong baseline performance
is not an exclusion.

### Reruns

The result record distinguishes non-start, harness-failure rerun, planned
replicate, and post-outcome repeat. A post-outcome repeat is appended and never
replaces the original.

### Replication

Deterministic adversarial vectors receive one exact execution at minimum.
Stochastic timing/fault cases receive multiple seeded replicates under a
predeclared calibration or replication plan. Matched arms share seeds and
conditions where meaningful. No unsupported significance threshold is selected
in this slice.

## 15. Future implementation boundary

The first harness may be local and synthetic. It must not require live
providers, cloud services, production credentials, or changes to Ananke,
Horae, Adrasteia, Mnemosyne, or Fates. The harness must export the future
result records and preserve the hidden oracle separately; it must not become a
new Accord runtime or control plane.

For the frozen claims and readiness gate, see
[ACCORD-02D-FALSIFICATION-PROTOCOL.md](./ACCORD-02D-FALSIFICATION-PROTOCOL.md).
