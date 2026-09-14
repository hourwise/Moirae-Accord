# ACCORD-02D — Experiment Matrix

Status: frozen scenario-family plan for a future design-only implementation.
No matrix cell has been executed or scored.

The machine-readable catalog is
[accord-02d-scenario-catalog.json](./examples/accord-02d-scenario-catalog.json).
This document explains the intended coverage without turning the catalog into
an executable harness manifest.

## 1. Matrix axes

| Axis | Fixed levels or condition families |
| --- | --- |
| Arm | `ARM-A-DURABLE`, `ARM-B-PROVIDER-OBSERVATION`, `ARM-C-LIGHTWEIGHT-CLASSIFIER`, `ARM-D-ACCORD-EVIDENCE` |
| Surface | `S1_STRONG_RECEIPT`, `S2_WEAK_AMBIGUOUS` |
| Transport | `T1_LOCAL_NATIVE`, `T2_MCP_SHAPED`, optional `T3_A2A_SHAPED` |
| Topology | direct control, depth-2 chain, two siblings, nested sibling branches, multi-process roles |
| Delegate | honest, lying success, lying failure, partially lying, faulty/non-malicious |
| Authority | valid, attenuated, widened, expired, revoked, unknown extension, composition, laundering |
| Evidence | dispatch, transport ack, acceptance, state read, effect receipt, corroboration, negative query, stale/conflict/mismatch |
| Fault | `F01`–`F24` from the experimental design |
| Idempotency | none, stable, known/queryable, wrong reuse, expired, duplicate inside/outside window |
| Replication | deterministic adversarial vector or seeded stochastic/timing replicate |

The full Cartesian product is intentionally not required. A core subset covers
the principal factors; targeted adversarial and boundary families cover the
failure modes that a broad average could hide.

## 2. Core matrix

The future scored set must contain matched tasks across all four arms for a
representative subset of the following rows:

| Core row | Surface | Transport | Delegate | Authority | Evidence/fault focus |
| --- | --- | --- | --- | --- | --- |
| `CORE-01` | S1 | T1 | Honest | Valid direct | Strong receipt, no fault |
| `CORE-02` | S1 | T2 | Honest | Attenuated depth-2 | Provider observation and transport metadata |
| `CORE-03` | S2 | T1 | Honest | Valid direct | Acceptance only, delayed final state |
| `CORE-04` | S2 | T2 | Faulty | Valid direct | Lost response, stale read |
| `CORE-05` | S1 | T1 | Lying success | Valid direct | Delegate assertion only |
| `CORE-06` | S2 | T2 | Lying failure | Valid direct | Actual occurrence, false non-occurrence claim |
| `CORE-07` | S1 | T1 | Partially lying | Widened action | Wrong attempt/effect attribution |
| `CORE-08` | S2 | T2 | Honest | Revoked after dispatch | Delayed observation and historical effect |
| `CORE-09` | S1 | T1 | Faulty | Shared-budget siblings | Duplicate/possible widening |
| `CORE-10` | S2 | T2 | Honest | Unknown authority extension | Profile unknown/unsupported |

ARM-A/B/C/D receive the same logical scenario, seed, fault schedule, and
ordinary provider observations that their arm definition permits.

## 3. Authority sub-experiment families

These families correspond to the required A1–A12 cases. Each family appears in
the catalog as `ACCORD-02D-A01` through `ACCORD-02D-A12`.

| ID | Authority case | Main question | Failure focus |
| --- | --- | --- | --- |
| A1 | Simple two-level attenuation | Does a supported child remain no wider? | CF-2 |
| A2 | Depth-2 monotonic chain | Does component-wise attenuation survive one more explicit hop? | CF-2, unknown handling |
| A3 | Widened dimension | Is wider action/resource/time detected? | CF-2 |
| A4 | Unknown authority-bearing extension | Is conclusion withheld? | CF-2, unknown extension |
| A5 | Shared-budget siblings | Can individually narrow grants widen effective authority? | CF-2, composition |
| A6 | Reserved-budget siblings | Does explicit accounting support bounded composition? | false containment/widening |
| A7 | Complementary sibling capabilities | Does composition remain profile-dependent? | CF-2, CF-4 where transport involved |
| A8 | Parent-mediated possible laundering | Is mediated possible widening distinct from direct child widening? | CF-2 |
| A9 | Revocation before dispatch | Is dispatch authority invalid at the event? | temporal authority |
| A10 | Revocation after dispatch | Is history retained while current validity changes? | CF-8 |
| A11 | Expiry boundary | Is time ordering and boundary handling explicit? | unknown-order failures |
| A12 | Resource/action composition | Are dimensions compared independently and preserved? | CF-2 |

Each authority scenario records ground-truth relation, expected 02B relation,
effective-authority question, and applicable categorical failures. It does not
invoke Ananke or a production policy engine.

## 4. Effect sub-experiment families

These families correspond to E1–E20 and appear as `ACCORD-02D-E01` through
`ACCORD-02D-E20`.

| ID | Effect case | Main question | Primary metrics |
| --- | --- | --- | --- |
| E1 | Dispatch only | Is attempt history kept separate from effect occurrence? | FCR, IR |
| E2 | Transport acknowledgement only | Does transport acceptance avoid downstream overclaim? | FCR |
| E3 | Provider accepted, final effect unknown | Is staged acceptance preserved? | FCR, IR |
| E4 | Strong effect receipt | Can bound evidence support occurrence and attribution? | FCR, EVR, EAQ |
| E5 | Observer-distinct corroboration | Does corroboration remain explicit and bounded? | EVR, FCR |
| E6 | Lying child claims success | Is delegate-only evidence rejected? | FCR, CF-1 |
| E7 | Lying child claims failure after occurrence | Is false non-occurrence resisted? | FCR, escalation |
| E8 | Lost response then retry | Is uncertainty and retry identity preserved? | IR, DER |
| E9 | Duplicate external occurrence | Is duplicate fact distinguished from duplicate attempts? | DER, FCR |
| E10 | Complete negative query | Can scoped non-occurrence be supported? | FCR_non-occurrence, EVR |
| E11 | Incomplete empty read | Is silence kept unresolved? | FCR_non-occurrence, IR, CF-7 |
| E12 | Conflicting observations | Is conflict preserved? | IR_conflict, escalation |
| E13 | Stale evidence | Is current state withheld? | FCR, IR_stale |
| E14 | Wrong attempt binding | Is evidence prevented from proving another attempt? | EAQ, CF-5/13 |
| E15 | Wrong logical effect binding | Are valid other-effect records excluded? | EAQ, CF-13 |
| E16 | Partial/staged effect | Is early settlement prevented from settling later stages? | FCR, IR |
| E17 | Effect under invalid authority | Are normative and factual axes independent? | CF-8, FCR |
| E18 | Valid authority but no effect | Does authority avoid creating occurrence? | FCR |
| E19 | Late evidence reopens prior unknown | Is reopening preserved? | reopening, escalation |
| E20 | Idempotency window expiry | Is exactly-once avoided after retention expiry? | DER, FCR, IR |

## 5. Cross-layer families

The catalog includes six combined cases `ACCORD-02D-X01` through
`ACCORD-02D-X06`:

| ID | Combination | Expected separation |
| --- | --- | --- |
| X1 | Valid attenuated grant + lying success assertion + no provider evidence | Authority may be valid; effect remains unresolved. |
| X2 | Invalid/widened grant + actual external effect | Authority invalid; occurrence may be supported. |
| X3 | Revocation after dispatch + delayed occurrence | Historical dispatch/effect retained; current authority changes. |
| X4 | Sibling possible widening + bound effect receipt | Effective authority may be unresolved/widened while factual occurrence is supported. |
| X5 | Parent-mediated laundering + child claims direct authorship | Mediation and causal attribution remain distinct. |
| X6 | Transport metadata claims authorization absent from grant | Transport cannot inject authority. |

## 6. Boundary and replication plan

Boundary cases are placed just before, at, and just after:

- grant expiry;
- revocation;
- provider idempotency retention;
- evidence freshness;
- timeout/retry deadline;
- delayed provider event visibility.

The exact duration may be calibrated, but the boundary relation and expected
conformance bound are fixed. Deterministic cases run at least once. Stochastic
timing/fault cases use predeclared seeded replicates and matched seeds across
arms where meaningful.

## 7. Scenario catalog contract

Every catalog scenario declares:

- unique `scenario_id` and research-question family;
- applicable arms, topology, depth, sibling count, and process-boundary mode;
- delegate behaviour, authority condition, surface, evidence condition,
  transport, fault, idempotency condition;
- planned oracle state and expected conformance bounds;
- primary metrics and categorical failure relevance.

The catalog is not a claim that any row has run. Passing a deterministic catalog
case later will be conformance evidence, not evidence that a research hypothesis
is empirically true.

## 8. Conformance versus research experiment

Deterministic conformance cases ask whether an implementation obeys the frozen
02A/B/C/D contract. The empirical matrix asks whether the approach changes the
trade-off over credible baselines. The two result classes must be reported
separately and must not be used as substitutes for one another.
