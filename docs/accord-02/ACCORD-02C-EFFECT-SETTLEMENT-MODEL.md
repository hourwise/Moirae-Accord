# ACCORD-02C — Evidenced External-Effect Settlement Under Uncertainty

Status: candidate research/specification slice. This document defines a
portable semantic model and conformance boundary. It does not implement a
runtime, verifier executable, authority engine, reconciliation worker, provider
adapter, experiment harness, or control plane.

## 1. Purpose and question

ACCORD-02C answers a bounded question:

> Given portable linked records, authority analysis, attempts, observations,
> and evidence artifacts, what may an independent verifier conclude about one
> named external-effect predicate under a named settlement profile?

The answer is the strongest bounded conclusion justified by admissible evidence
under that profile. It is not an oracle, a statement of metaphysical truth, or
an assertion about paths and state that the supplied evidence cannot cover.

The model is intentionally conservative:

- dispatch is evidence that an attempt was issued, not that an effect occurred;
- transport or provider acceptance is not silently promoted to downstream
  completion;
- an observation is not automatically a settlement;
- authority validity and factual occurrence are independent axes;
- silence is not non-occurrence unless a justified completeness assumption is
  explicitly accepted;
- causal attribution is weaker than observing a matching external state when
  another actor could have produced that state;
- uncertainty, conflict, staleness, and profile incompatibility remain visible.

## 2. Architectural boundary and ownership

ACCORD-02C preserves the accepted ACCORD-01 pivot: Accord is a
research/specification/conformance instrument, not a second production control
plane.

| Concern | Owner | ACCORD-02C treatment |
| --- | --- | --- |
| Portable representation and linked records | Adrasteia | Reuses the ACCORD-02A record identities and links. |
| Authority, grants, delegation derivation, and authority decisions | Ananke | Accepts an authority analysis as an input; does not re-derive or enforce it. |
| Attempt, effect, retry, and reconciliation lifecycle state | Horae | References lifecycle records and observations; does not create a state store or worker. |
| Governed memory/provenance | Mnemosyne | No source or runtime change in this slice. |
| Conformance evidence and test fixtures | Fates Integration | Offline vectors only; no provider or repository calls. |
| Portable settlement semantics | Accord | Defines profiles, result axes, invariants, and falsification questions. |
| Transports and external systems | A2A, MCP, providers, transports | Conformance targets and evidence sources, never semantic authorities. |

This slice does not mutate ACCORD-02A or ACCORD-02B. ACCORD-02A supplies the
portable linked-record contract and verifier-facing identities. ACCORD-02B
supplies authority attenuation/composition analysis, time-aware validity, and
revocation observations. ACCORD-02C supplies evidenced effect-settlement
semantics layered over those inputs.

## 3. The settled object is a predicate, not a lifecycle label

An effect is a logical intended effect identified by `effect_id`. Its target is
an explicit predicate with a profile-qualified `predicate_id`, action, resource,
target/counterparty, and any relevant external identifier. Examples include:

- `provider_acceptance` — a provider accepted a request;
- `processing_started` — processing began;
- `resource_created` — an external resource was created;
- `resource_visible` — a resource was visible to a named reader;
- `recipient_acknowledgement` — a recipient acknowledged receipt;
- `payment_authorized` — an authorization was recorded;
- `payment_settled` — settlement completed;
- `publication_created` or `publication_visible` — distinct publication stages.

Predicates in one workflow are not aliases. A provider acceptance receipt may
settle `provider_acceptance` while leaving `recipient_acknowledgement`
unresolved. A `resource_created` observation does not settle
`resource_visible`. The intended predicate and its stage are always carried in
the target and bound in the evidence.

### 3.1 Logical effect and concrete attempts

The existing ACCORD-02A meanings remain normative for this slice:

- `effect_id` names one logical intended effect. It remains stable across
  retries and does not itself prove occurrence.
- `attempt_id` names one concrete dispatch or execution attempt. Every retry
  gets a distinct attempt ID.
- Multiple attempt IDs may refer to one `effect_id`; attempt count is not
  logical-effect count.
- A provider operation ID, transport ID, or idempotency key is a provider or
  transport reference. It cannot replace the Accord identities.

The model can represent one attempt causing one occurrence, one of several
attempts causing the occurrence, an occurrence with unknown causation, and
multiple external occurrences caused by retries. It does not infer exactly-once
behaviour from a single logical effect or from an idempotency key.

### 3.2 Five distinct claims

The following claims must not be collapsed:

1. `attempt_recorded`: a mediated dispatch record exists;
2. `external_state_observed`: an observer reported a state or event;
3. `effect_occurrence_supported`: evidence supports the named predicate for
   the target effect;
4. `attribution_supported`: the occurrence is bound to the Accord effect and,
   where claimed, to one or more attempts;
5. `causal_attribution_supported`: the evidence supports that a particular
   attempt caused the occurrence.

`goal_satisfaction` is another separate claim. Even an attributed occurrence
may not satisfy the requested goal if the effect predicate or target is wrong.

## 4. Settlement is multidimensional

The result is a structured assessment, not a single `SUCCESS` boolean. At
minimum it carries these independent dimensions:

| Dimension | Conservative values | Question |
| --- | --- | --- |
| Authority | `AUTHORIZED`, `INVALID_AUTHORITY`, `UNKNOWN_AUTHORITY`, `UNSUPPORTED_AUTHORITY`, `CONFLICTING_AUTHORITY`, `NOT_EVALUATED` | Was the relevant authority analysis valid at the relevant event? |
| Occurrence | `OCCURRENCE_SUPPORTED`, `NON_OCCURRENCE_SUPPORTED`, `PARTIAL_EFFECT`, `CONFLICTING_EVIDENCE`, `INSUFFICIENT_EVIDENCE`, `INADMISSIBLE_EVIDENCE`, `STALE_EVIDENCE`, `UNKNOWN` | What does admissible evidence support about the named predicate? |
| Attribution | `ATTRIBUTED_TO_SPECIFIC_ATTEMPT`, `ATTRIBUTED_TO_ONE_OR_MORE_ATTEMPTS`, `ATTRIBUTION_UNKNOWN`, `ATTRIBUTION_CONFLICTING`, `INADMISSIBLE`, `NOT_APPLICABLE` | To which Accord effect or attempt can it be bound? |
| Causality | `SPECIFIC_ATTEMPT_SUPPORTED`, `CAUSED_BY_ONE_OR_MORE_ATTEMPTS`, `EFFECT_BOUND`, `EXTERNAL_STATE_ONLY`, `CAUSATION_UNKNOWN`, `CAUSATION_CONFLICTING`, `NOT_ASSESSED` | Does the evidence support a cause, not merely a matching state? |
| Completeness | `COMPLETE`, `PARTIAL`, `UNKNOWN`, `NOT_APPLICABLE` | Does the evidence cover the predicate's relevant scope and interval? |
| Sufficiency | `SUFFICIENT`, `INSUFFICIENT`, `INADMISSIBLE`, `STALE`, `CONFLICTING`, `PROFILE_INCOMPATIBLE`, `UNKNOWN` | Is the evidence adequate under this profile? |
| Freshness | `CURRENT`, `STALE`, `UNKNOWN`, `NOT_APPLICABLE` | Is the evidence usable at verification time? |
| Duplication | `NONE_SUPPORTED`, `POSSIBLE_DUPLICATE`, `DUPLICATE_SUPPORTED`, `DISTINCT_OCCURRENCES_SUPPORTED`, `UNKNOWN`, `NOT_APPLICABLE` | What, if anything, is justified about multiplicity? |
| Finality | `PROVISIONAL`, `REOPENABLE`, `FINAL_UNDER_PROFILE`, `REOPENED`, `NOT_FINAL` | Can later admissible evidence change this conclusion? |
| Profile compatibility | `COMPATIBLE`, `INCOMPATIBLE`, `UNKNOWN`, `NOT_EVALUATED` | Can the supplied evidence and requested conclusion be interpreted together? |

An overall result is only a conservative summary of these axes. It must not
erase the axes or convert `INVALID_AUTHORITY + OCCURRENCE_SUPPORTED` into a
failure of factual occurrence.

The result schema is [the ACCORD-02C settlement result schema](./schema/accord-02c-settlement-result.schema.json).

The native C result is the semantic source of truth for the effect-settlement
axes. When an implementation also emits an ACCORD-02A verifier-facing
`settlement.kind`, it MUST retain this native result and apply the named
[ACCORD-02R1 A/C projection map](./examples/accord-02r1-settlement-vocabulary-map.json);
it MUST NOT replace the C axes with the
projection or infer a stronger A kind from a single C status string.

## 5. Evidence and observation semantics

An observation reports what an observer says was seen at a stated time and read
boundary. An evidence artifact carries or references material that supports a
proposition, its bindings, provenance, integrity, and trust assumptions.

Evidence is admissible only when the active profile understands its class,
identity bindings, temporal bindings, integrity mechanism, observer role, and
freshness. A valid signature proves at most the issuer's covered statement. A
provider signature does not prove universal truth or an unmediated path.

Evidence may be:

- direct, indirect, stale, ambiguous, partial, replayed, corrupted, or
  incorrectly attributed;
- positive, negative, or silent with respect to the target predicate;
- first-party, observer-distinct, or merely process-distinct under an explicit
  trust relationship;
- derived from other artifacts, in which case the derivation and its loss of
  information remain visible.

The companion [evidence and trust specification](./ACCORD-02C-EVIDENCE-AND-TRUST.md)
defines the taxonomy, admissibility dimensions, and non-universal trust rules.

## 6. Settlement profile

A profile is part of the semantics of a result. It declares assumptions that
would otherwise be hidden, including:

- understood authority-bearing and factual-effect dimensions;
- accepted evidence classes and the conclusions each class may support;
- required identity bindings for principal, grant, intent, task, delegation,
  effect, attempt, observer, resource, action, recipient/counterparty,
  provider, and external identifiers;
- required temporal bindings and clock/order policy;
- accepted digest, signature, attestation, and transparency mechanisms;
- evidence freshness, clock skew, and late-observation rules;
- minimum observer/root/operator distinction for corroboration;
- observer trust assumptions, completeness assumptions, and negative-evidence
  rules;
- causal-attribution strength and whether effect-bound evidence is enough;
- partial-stage treatment and whether stages settle independently;
- retry, idempotency, and duplicate-effect semantics;
- unknown or incompatible extension handling;
- reopening and finality policy.

The profile schema is [accord-02c-settlement-profile.schema.json](./schema/accord-02c-settlement-profile.schema.json).
No profile declaration makes a source trustworthy by itself; it makes the
assumption explicit so that a verifier can report what it relied on.

## 7. Binding requirements

An artifact may support only the propositions and records its coverage binds.
The verifier evaluates these bindings separately:

| Binding | Minimum question |
| --- | --- |
| Principal | Which principal issued, observed, or is the subject of the claim? |
| Grant/authority | Which `grant_id`, delegation, and authority analysis are relevant? |
| Intent/task | Which requested goal and logical task are in scope? |
| Effect | Does the evidence name the exact `effect_id` and predicate identity? |
| Attempt | Does it name one `attempt_id`, a declared set, or no attempt? |
| Observer/provenance | Who observed or attested, under which role, root, operator boundary, and process relationship? |
| Resource/action | Which resource, action, representation, and action digest are covered? |
| Recipient/counterparty | Which recipient or counterparty is covered, and does it match? |
| External identifier | Which provider operation, resource, idempotency, or ledger identifier is echoed? |
| Time | Which event, observation, issuance, validity, and verification times or intervals are covered? |

Missing or mismatched bindings do not become positive evidence through a nearby
transport ID, matching human label, or timestamp. Wrong-effect and
wrong-attempt artifacts remain linkable for diagnostics but are excluded from
settling the selected target.

## 8. Partial and staged effects

Profiles represent a staged effect as a set of distinct predicates with an
explicit order or dependency graph. A result may settle an early stage while
later stages remain unresolved. The result must identify:

- the stage predicate being assessed;
- each stage's state (`SUPPORTED`, `NOT_SUPPORTED`, `UNRESOLVED`, `CONFLICTING`,
  or `NOT_EVALUATED`);
- whether the stage is independently settleable;
- the evidence and bindings for that stage;
- any prerequisite that has not been established.

`provider_acceptance`, `processing_started`, `resource_created`,
`publication_visible`, and `recipient_acknowledgement` are not a single
success state. An early-stage receipt cannot silently settle a later stage.

## 9. Negative evidence and non-occurrence

The default rule is:

> Absence of evidence is not evidence of absence.

Timeout, missing response, failed lookup, and an empty non-authoritative view
normally produce `UNKNOWN` or `INSUFFICIENT_EVIDENCE`, not
`NON_OCCURRENCE_SUPPORTED`.

A profile may permit a non-occurrence conclusion only when all of the following
are explicit and satisfied:

1. the source is accepted as complete for the named proposition and scope;
2. the queried state space covers the target resource/action/recipient and the
   entire relevant interval;
3. identity and temporal bindings match the target effect;
4. the source's completeness, retention, and consistency assumptions are
   accepted by the active profile;
5. the negative result is not stale, partial, or contradicted by admissible
   evidence.

Even then, the conclusion is profile-bounded non-occurrence for that scope and
interval. It is not a claim about an unlisted provider, delayed state, or
unmediated path. Stale or incomplete negative observations are reported on the
freshness/completeness axes and cannot be promoted to non-occurrence.

## 10. Retry, idempotency, and duplicate effects

For one logical effect `E`, attempts may be `A1`, `A2`, and `A3`:

```text
effect_id E
  ├── attempt_id A1  (failed before dispatch)
  ├── attempt_id A2  (dispatched; acknowledgement uncertain)
  └── attempt_id A3  (dispatch or provider receipt observed)
```

The verifier records, without implementing a service:

- whether a provider idempotency key is known, unknown, or explicitly absent;
- whether the key is bound to the logical effect and which attempts reused it;
- whether a provider operation ID or external resource ID is echoed;
- whether a retry is known to be a semantic duplicate, merely possible, or
  supported as distinct;
- whether evidence supports one occurrence, multiple occurrences, or neither.

Attempt count never implies logical multiplicity. Conversely, a shared
idempotency key never proves exactly-once external occurrence unless the active
profile and evidence support that claim. Lost acknowledgement followed by a
retry must be able to produce `OCCURRENCE_SUPPORTED` with
`POSSIBLE_DUPLICATE`, rather than silently treating the history as one effect
or one occurrence.

## 11. Temporal semantics

ACCORD-02C reuses ACCORD-02A time fields and ACCORD-02B time-aware authority
analysis. A result may carry:

- intent, task, derivation, admission, dispatch, provider-event,
  observation, evidence-issuance, verification, and current times;
- event times separately from observation and evidence-issuance times;
- intervals, clock uncertainty, maximum skew, and a declared clock/order model;
- late or out-of-order observations;
- freshness and retention limits;
- incomparable cross-process clocks.

An observation at `observed_at` may describe an earlier provider `event_time`.
It does not reorder events merely because it arrived later. Where the profile
cannot establish the required order, the relevant authority, freshness,
causality, or occurrence dimension is `UNKNOWN`/unresolved rather than
invented.

## 12. Authority and factual history are orthogonal

Authority analysis is an input axis, not a rewriting rule. The result must
permit all of these combinations:

| Authority axis | Effect axis | Meaning |
| --- | --- | --- |
| `AUTHORIZED` | `OCCURRENCE_SUPPORTED` | Validly analysed authority and supported occurrence. |
| `AUTHORIZED` | `UNKNOWN` | Valid dispatch analysis but no sufficient effect evidence. |
| `AUTHORIZED` | `NON_OCCURRENCE_SUPPORTED` | Valid authority but qualified evidence supports non-occurrence. |
| `INVALID_AUTHORITY` | `OCCURRENCE_SUPPORTED` | Authority was invalid, but the external effect is still evidenced. |
| `INVALID_AUTHORITY` | `UNKNOWN` | Invalid authority and unresolved factual history. |
| `UNKNOWN_AUTHORITY` | `OCCURRENCE_SUPPORTED` | Factual occurrence is supported while authority remains unresolved. |

`NO_VALID_AUTHORITY` does not imply `NO_EFFECT`. Revocation before dispatch may
make an attempt invalid. Revocation after dispatch does not erase the dispatch;
revocation after occurrence does not erase the historical occurrence. A result
may therefore say `INVALID_AUTHORITY` at dispatch and
`OCCURRENCE_SUPPORTED` for the effect.

This is required behaviour, not a contradiction. Factual history must not be
rewritten to satisfy normative policy, and factual occurrence must not create
valid authority retroactively.

## 13. Causal attribution

The following ladder is intentionally non-equivalent:

1. external state was observed;
2. a state matching the effect predicate was observed;
3. the state is bound to `effect_id`;
4. the state is bound to one or more attempts;
5. a specific attempt caused the state.

For example, a resource with the expected content may support occurrence or
effect binding while leaving causation unknown if another actor could have
created it. A result may therefore contain
`OCCURRENCE_SUPPORTED + ATTRIBUTION_UNKNOWN` or
`EFFECT_BOUND + CAUSATION_UNKNOWN`.

## 14. Conflicts, supersession, reopening, and finality

Admissible conflict is preserved. The verifier must not resolve a conflict by
latest timestamp, provider convenience, local-record preference, or majority
count unless the active profile explicitly declares a legitimate precedence or
supersession rule.

Each conflict identifies the competing evidence, propositions, bindings, and
resolution state. Later evidence may:

- strengthen an earlier result;
- weaken it by exposing stale or incomplete assumptions;
- supersede it under an explicit version/sequence rule;
- contradict it;
- reopen a result previously marked final under a profile that permits
  reopening.

`FINAL_UNDER_PROFILE` is not universal irreversibility. It is valid only when a
profile explicitly justifies the finality boundary and its reopening policy.

## 15. Deterministic verifier obligations (specification only)

A future verifier conforming to this model would, in order:

1. parse and structurally validate the profile, target, records, and evidence;
2. resolve record IDs and preserve duplicate, wrong-target, and wrong-attempt
   artifacts for diagnostics;
3. evaluate integrity, accepted evidence class, provenance, and bindings;
4. evaluate event/observation/evidence times, freshness, completeness, and
   profile compatibility;
5. evaluate occurrence, attribution, causality, stages, and duplicate
   diagnostics independently;
6. carry the supplied 02B authority analysis without converting it into an
   effect conclusion;
7. emit a bounded result with reasons, assumptions, conflicts, and reopening
   metadata.

This list is a contract for later implementation, not an implementation in
this slice.

## 16. Research and falsification boundary

ACCORD-02C does not establish:

- omniscient external ground truth;
- trustworthy evidence sources merely by naming them;
- exactly-once external effects;
- distributed consensus;
- revocation execution or propagation;
- provider reconciliation or a durable effect-state worker;
- equivalence between transport acknowledgement and business effect;
- causal attribution where evidence cannot support it;
- valid authority merely because an effect occurred;
- effect occurrence merely because authority was valid.

Future empirical work would need provider fixtures or real-provider test
profiles, controlled crash-after-effect and lost-acknowledgement experiments,
delayed/out-of-order observation tests, duplicate-effect measurements, source
compromise and collusion cases, cross-provider comparisons, and independent
offline verification. Those experiments are deliberately outside this slice.

## 17. Conformance vectors

The offline vectors are in
[ACCORD-02C-SETTLEMENT-CONFORMANCE-VECTORS.md](./ACCORD-02C-SETTLEMENT-CONFORMANCE-VECTORS.md)
and the machine-readable fixture is
[accord-02c-settlement-test-vectors.json](./examples/accord-02c-settlement-test-vectors.json).

They cover dispatch/transport boundaries, strong and corroborated evidence,
conflict, staleness, wrong bindings, replay, retries, negative evidence,
partial stages, authority/effect orthogonality, revocation, causal ambiguity,
profile incompatibility, clock ambiguity, unknown extensions, recipient
mismatch, corruption, and reopening.

## 18. Candidate lineage

This slice is additive to the candidate branch lineage:

- [ACCORD-02A portable record and verifier contract](./ACCORD-02A-PORTABLE-RECORD-SPEC.md)
  provides `principal`, `grant_id`, `intent_id`, `task_id`, `delegation_id`,
  `effect_id`, `attempt_id`, observation, evidence, and verifier-facing links.
- [ACCORD-02A verifier contract](./ACCORD-02A-VERIFIER-CONTRACT.md) provides
  the external-runnability and fail-closed framing.
- [ACCORD-02A trust/evidence profile](./ACCORD-02A-TRUST-EVIDENCE-PROFILE.md)
  provides the non-universal evidence-class and observer-relationship framing.
- [ACCORD-02B authority attenuation model](./ACCORD-02B-AUTHORITY-ATTENUATION-MODEL.md)
  provides authority relation states and the rule that unknown authority-bearing
  dimensions remain unresolved.
- [ACCORD-02B effective-authority composition](./ACCORD-02B-EFFECTIVE-AUTHORITY-COMPOSITION.md)
  provides time-specific revocation/expiry analysis and effective-authority
  uncertainty.

ACCORD-02C consumes those contracts; it does not redefine their identifiers,
authority ownership, or runtime responsibilities.
