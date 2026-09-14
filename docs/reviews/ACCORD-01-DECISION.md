# ACCORD-01 Decision

## Primary verdict

`PIVOT`

The project remains worth investigating, but the original joined “new control
plane prevents privilege escalation and false completion” direction is not
accepted as an implementation target. The research is narrowed to falsifiable
effect-evidence trade-offs and authority composition, with existing Fates
components retaining their natural ownership.

## Project disposition

| Decision field | Binding decision |
|---|---|
| MOIRAE ACCORD PROJECT | CONTINUE, as a research/specification, portable-record, verifier, and test-profile effort |
| NEW ACCORD RUNTIME | REJECT |
| ADRASTEIA ROLE | Natural owner of portable linked authority/intent/task/effect/evidence record contracts, principal and observer representation, and transport-neutral correlation. No policy, authority minting, or effect state. |
| ANANKE ROLE | Sole owner of authority derivation, grant validation, policy, approval binding, and mediated dispatch admission. Accord never mints authority. |
| HORAE ROLE | Sole authoritative owner of attempt identity, durable dispatch/lifecycle, reconciliation, and effect-state settlement. No second effect-state store in Accord. |
| MNEMOSYNE ROLE | Deferred provenance and governed-memory context. Not required for the current research boundary and not an authority or completion oracle. |
| FATES INTEGRATION ROLE | Evidence/conformance fixtures and compatibility locks only. It remains outside the runtime path. |
| A2A ROLE | Interoperability/conformance target and optional transport fixture. It is not the research foundation and does not define Accord authority semantics. |
| MCP ROLE | Optional transport/tool fixture that carries the same authority and evidence record. MCP discovery is not authority and must not bypass Ananke/Horae ownership. |
| FIRECRACKER ROLE | Deferred. Required only if a later claim concerns whole-process complete mediation or isolation; not required for a mediated-channel evidence experiment. |

## Accepted architecture direction

There is no Accord runtime box in the accepted direction. Accord names the
research profile and portable record/verifier boundary; it does not schedule
work, mint grants, maintain a second effect state, or claim to see external
reality.

```text
                    transport fixtures
                 local / MCP-shaped / A2A-shaped
                              |
             portable linked record and verifier profile
                 (Adrasteia contract ownership)
                              |
                 Ananke-mediated authority boundary
           grant derivation / policy / approval / admission
                              |
                 Horae durable execution boundary
           attempt identity / claims / retries / reconciliation
                              |
                provider or synthetic effect surface
                              |
       observer evidence -> attributed settlement -> verifier output
```

Project-Fates-Integration is not a box in this path. It may later hold
conformance fixtures, but it does not own runtime execution or effect state.

## Canonical research questions

### Primary

For external effect surfaces with differing evidence affordances and delegates
with differing reliability or honesty, what is the achievable trade-off among
false confirmation, indeterminacy, duplicate effects, and human escalation, and
can a portable, externally verifiable evidence record that binds authority to
task/effect identity materially improve that trade-off over durable execution
plus direct provider-state observation and a lightweight classifier baseline?

This is falsifiable. The independent verifier must operate on the portable
record, supplied evidence, and declared trust roots without Accord-private
state. The null result is that the portable record does not improve the
pre-registered trade-off or assurance boundary.

### Secondary

Under multi-hop delegation and sibling composition, does grant-level monotonic
attenuation bound effective authority when parent-mediated laundering,
composition, expiry, revocation, and resource dimensions are varied?

This is falsifiable only with depth at least 2, at least two siblings, explicit
composition rules, and an authority oracle independent of the delegate’s own
claims. A depth-1 smoke test cannot answer it.

## Canonical terminology

| Term | Decision |
|---|---|
| completion truth | REJECT. It conflates lifecycle and epistemic claims. |
| truth | REJECT when unqualified. State the claim, observer, evidence, and trust root. |
| verified | ACCEPT only in qualified form: `VERIFIED(evidence_class, observer, trust_root)`. |
| independent | REJECT when unqualified. Use `delegate-independent`, `process-independent`, `observer-distinct`, or `externally verifiable`. |
| completion | Reserve for task/agent lifecycle status. It does not settle an external effect. |
| effect | Split into attempted operation, observed state, effect occurrence, attribution, and goal satisfaction. |
| exactly-once | REJECT when unqualified. Use at-most-once dispatch, at-least-once retry, duplicate-recognizable, or settled effect semantics. |
| authority | Distinguish grant authority from effective authority after composition, policy, mediation, and execution context. |
| delegation | Distinguish authority delegation from task/work delegation. |
| UNKNOWN | Use `UNKNOWN_PENDING` when a reconciliation obligation remains and `UNKNOWN_TERMINAL` when the declared evidence contract cannot improve the result. Neither means success or failure. |
| VERIFIED_NO_EFFECT | REPLACE in ordinary use with `NO_EFFECT_OBSERVED(as_of, read_semantics)`. A stronger no-effect result requires an authoritative absence assertion or suitable fence. |
| evidence-backed effect settlement | ACCEPT as the primary replacement for “completion truth.” |
| CORROBORATED | ACCEPT for evidence that supports a claim but does not meet the declared verification threshold. |
| EVIDENCED EFFECT | ACCEPT as a descriptive noun phrase, not as an unqualified success verdict. |

## Provisional evidence-class model — design only

The reviewer’s E0–E4 taxonomy is retained as a useful starting vocabulary, but
the classes are not a universal total order. Evidence must also record freshness,
scope, goal coverage, observer identity, attribution method, and trust root.

| Class | What is actually known | Observer and trust root | Attribution strength | Success statement | Defensible verdict | Main ambiguity/failure modes |
|---|---|---|---|---|---|---|
| E0 — no observable state | A dispatch or agent report may exist; external state is not observable under the contract. | Delegate, transport, or local logger; trust is limited to that source. | None unless a separate binding exists. | No effect success. | `UNKNOWN_PENDING` if reconciliation is possible; otherwise `UNKNOWN_TERMINAL`. | Fire-and-forget, lost response, hidden effect, duplicate effect, unverifiable absence. |
| E1 — observable but unattributable | A provider or system state can be read, but the observation cannot be tied to this attempt. | Named observer and read semantics; trust is relative to that observer. | Weak or none. | Do not state attributed success. | `OBSERVED_CONSISTENT` or `UNKNOWN`, depending on goal and freshness. | Pre-existing state, concurrent actor, stale read, wrong resource, coincidental match. |
| E2 — attributable provider observation | Provider state echoes or honors a client idempotency key or equivalent correlation. | Provider/client observer and its declared consistency/trust semantics. | Stronger, but still conditional on provider retention, uniqueness, and key scope. | `CORROBORATED` or qualified `VERIFIED` only if the policy explicitly accepts this trust root. | `ATTRIBUTED_OBSERVATION`; may settle success under a declared provider-trust policy. | Key expiry, provider bug, key collision, non-linearizable read, partial execution, goal mismatch. |
| E3 — provider-signed receipt | A provider or receiving service signs a receipt bound to the operation and relevant identifiers. | Provider signing key, key-distribution policy, and observer distinct from the delegate where required. | Strong cryptographic attribution to the signer’s observation. | Qualified `VERIFIED(evidence_class=E3, observer, trust_root)`, never provider-independent truth. | `EVIDENCED_EFFECT` or `CORROBORATED` according to goal coverage. | Key compromise, signer/agent collusion, omitted fields, suppression, receipt for acceptance rather than completion, goal mismatch. |
| E4 — receipt plus witness/transparency evidence | A signed receipt is committed to a third-party witness or transparency log with verifiable inclusion. | Provider key plus witness/log trust roots and inclusion semantics. | Strongest in this provisional model for provenance and non-equivocation, not necessarily for effect reality. | Qualified `VERIFIED` relative to both roots and the declared effect predicate. | `EVIDENCED_EFFECT` with stronger external verifiability. | Provider/witness collusion, unavailable witness, delayed inclusion, receipt suppression before logging, goal mismatch, trust-root governance. |

Provider signatures do not create provider-independent truth. E3 and E4 state
what the declared signer/witness attests and what the verifier can check. They do
not prove that a business goal was satisfied unless the effect predicate and
evidence cover that goal.

## Trust model

The system can verify only that a declared authority, task/effect identity,
observation, and evidence artifact are consistent with named trust roots and
the declared mediated channel; it cannot verify an unobserved external fact or
prevent effects through paths it does not mediate.

## Research versus engineering boundary

### Engineering smoke test

- one parent and one child;
- maximum depth 1 and one child;
- local or synthetic effect surface;
- single host;
- deterministic admission, claim, retry, and evidence wiring;
- no production provider effect and no whole-process containment claim.

This can demonstrate record plumbing and bounded local behavior. It is not
evidence for multi-hop authority composition, sibling aggregation, provider
uncertainty, network partition, or independent external effects.

### Research experiment

The later experiment design should evaluate, without implementation in this
task:

- depth at least 2 and at least two siblings;
- honest, lying, and partially lying child delegates;
- crash, delay, lost-response, and fault injection;
- provider idempotency-window expiry;
- at least two synthetic/external test-mode effect surfaces with different
  evidence affordances;
- at least two evidence classes, including an unattributed or ambiguous case;
- at least two transports, one local/loopback and one protocol-shaped fixture;
- an offline/third-party verifier with no Accord-private state;
- the cheap baseline of durable execution plus provider-state re-read and a
  lightweight classifier;
- explicit authority-composition cases for parent laundering and sibling joins.

The pre-registered measurements are false confirmation rate, indeterminacy rate,
duplicate effect rate, human escalation load, external verifiability, effect
attribution, and effective-authority composition. A pilot must establish the
distributions and practical costs before numerical thresholds are chosen.

Categorical research failures include: a false `VERIFIED` result under the
declared adversary; authority widening; an external verifier that requires
private Accord state; transport metadata becoming authority; inability to
distinguish duplicate attempts from settled effects; or a whole-process claim
without complete mediation.

## Falsification obligations

Before any stronger claim is made, the research must demonstrate:

1. an explicit ground-truth or adjudication procedure for each synthetic/test
   effect surface;
2. a baseline comparison, including cases where the baseline is as good as or
   better than the portable record;
3. independently reproducible verifier results from exported records;
4. no authority widening under the declared authority relation and compositions;
5. correct non-success treatment of ambiguous and unobservable outcomes;
6. measured duplicate and escalation costs, not only prevented false successes;
7. a stated trust-root and complete-mediation boundary for every verdict.

No numerical abandonment percentage is accepted in advance. Thresholds must be
pre-registered after a pilot. A categorical failure cannot be rescued by a good
average score.

## Implementation gate

ACCORD-02 is not started by this decision. If separately authorized, it may
begin with one or more of the following design-only deliverables:

- a portable linked authority/task/effect/evidence record specification;
- a verifier contract and trust-root profile;
- a formal, component-wise authority relation and composition model;
- an experiment and falsification protocol;
- conformance fixtures for local, MCP-shaped, and A2A-shaped transports.

ACCORD-02 may not begin with a new Accord runtime, Fates source changes,
consumer upgrades, provider calls, Firecracker execution, dependency
installation, or an experiment harness until a separate scope and implementation
acceptance is issued.

## Material pivot

Before review, the plan treated Accord as a new synthesis/control-plane runtime
that would join authority, durable execution, delegation, transport, and effect
verdicts. After review and verification, the accepted direction removes that
runtime. The remaining question is whether a portable record/verifier and a
carefully designed comparison experiment provide measurable value over existing
Ananke/Horae-like ownership and a direct provider-state baseline.
