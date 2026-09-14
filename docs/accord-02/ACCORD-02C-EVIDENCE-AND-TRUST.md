# ACCORD-02C — Evidence and Trust

Status: candidate research/specification slice. This document defines an
implementation-neutral evidence taxonomy and explicit trust assumptions for
the ACCORD-02C settlement model. It does not declare any source universally
authoritative and does not implement trust, signatures, reconciliation, or
provider access.

## 1. Evidence is a bounded proposition

An evidence artifact supports only the proposition stated in its coverage and
only under the bindings, integrity mechanism, observer relationship, temporal
scope, and settlement profile that the artifact declares. The fact that an
artifact is signed, recent, local, or produced by a provider does not enlarge
its proposition.

The verifier therefore asks, separately:

1. Is the artifact structurally and cryptographically usable?
2. Who issued, observed, or attested to it?
3. What exact effect predicate and stage does it cover?
4. Which `effect_id`, `attempt_id`, and other identities does it bind?
5. What resource, action, recipient/counterparty, and provider does it cover?
6. Which event time, observation time, issuance time, and validity interval does
   it cover?
7. What trust, completeness, freshness, independence, and causal assumptions
   does the active profile accept?
8. Does it agree or conflict with other admissible evidence?

Unknown answers remain unknown. They are not filled by transport metadata,
human labels, proximity in a record bundle, or the most convenient provider
interpretation.

## 2. Evidence taxonomy

The following classes are a useful implementation-neutral vocabulary. They are
profile inputs, not a universal ranking. The same class can support different
conclusions for different predicates and profiles.

| Class | What it can directly establish | What it does not establish by itself |
| --- | --- | --- |
| `LOCAL_ATTEMPT_DISPATCH_RECORD` | A dispatcher or executor recorded an attempt with an `attempt_id` and target `effect_id`. | Provider acceptance, external occurrence, recipient delivery, or causation. |
| `TRANSPORT_ACKNOWLEDGEMENT` | A transport layer accepted or delivered a message/call according to its own semantics. | The intended business effect or a downstream provider/recipient state. |
| `PROVIDER_ACCEPTANCE_RECEIPT` | A named provider accepted a request or queued work under the receipt's scope. | Processing, creation, publication, settlement, or recipient delivery unless separately covered. |
| `PROVIDER_EFFECT_RECEIPT` | A provider asserts that the named effect predicate occurred, when identity, predicate, target, time, and integrity bindings pass. | Universal truth, an unmediated path, or a later stage not covered by the receipt. |
| `TARGET_ACKNOWLEDGEMENT` | A named target/counterparty acknowledged a specified predicate or artifact. | A provider-side action or any stage not acknowledged. |
| `FIRST_PARTY_OBSERVATION` | The named first party reports a state or event under stated read semantics. | Independence from that party, universal completeness, or causal attribution without bindings. |
| `INDEPENDENT_OBSERVATION` | An observer-distinct party reports a state under an explicitly declared relationship. | Independence in the strong sense unless operator/root/process boundaries support it. |
| `SIGNED_ATTESTED_ARTIFACT` | A trusted issuer attested to the covered bytes/proposition under a declared root. | Truth beyond the issuer's scope, freshness beyond the validity rule, or effect causation. |
| `EXTERNAL_STATE_SNAPSHOT` | A snapshot describes a resource/state at an `as_of` boundary. | That the linked attempt created the state or that the state persists later. |
| `RECONCILIATION_RESULT` | A named reconciliation process produced a result under its declared inputs and profile. | The correctness of the reconciliation process or hidden state not included in the evidence. |
| `COMPLETE_NEGATIVE_LEDGER_QUERY` | A complete, bound query found no matching event in a declared scope and interval. | Non-occurrence outside the covered state space, interval, retention, or completeness assumption. |
| `HUMAN_ASSERTION` | A named human made a statement, with its provenance if available. | Independent factual settlement without a profile explicitly accepting that risk. |
| `DERIVED_EVIDENCE` | A declared derivation produced a conclusion from named source artifacts. | Any source proposition or trust property omitted by the derivation. |

For example, HTTP 200 normally belongs to a transport or provider response
class. It may support request acceptance if the profile says so; it does not
inherently prove that an email reached a recipient or that a payment settled.

## 3. Evidence property vector

An accepted evidence class is evaluated as a vector, not a total order. A
profile should declare at least:

| Property | Required question |
| --- | --- |
| `evidence_class` | Which class and profile-local subtype is this? |
| `issuer_principal_id` | Who created or issued the artifact? |
| `observer_principal_id` | Who observed or attested to the proposition? |
| `trust_root_id` | Which root authenticates the issuer or observer? |
| `observer_role` | Is the party a provider, receiver, executor, target, witness, or other role? |
| `observer_relationship` | Same process, same operator, separate service, provider-originated, third party, or synthetic fixture? |
| `operator_boundary` | Which operator controls the observer and issuer? |
| `process_boundary` | Is the observer process distinct from the dispatcher/delegate? |
| `external_verifiability` | Can a third party check the claim with supplied material? |
| `identity_binding` | Which principal/grant/intent/task/delegation/effect/attempt identities are covered? |
| `predicate_binding` | Which stage, action, resource, recipient, and external identifier are covered? |
| `temporal_binding` | Which event/observation/issuance times or intervals are covered? |
| `read_semantics` | What was actually read or measured, with what consistency? |
| `integrity_mechanism` | Digest, signature, attestation, log proof, hash chain, or none? |
| `replay_resistance` | Nonce, sequence, idempotency binding, unique artifact version, or explicit absence? |
| `freshness` | What age, skew, validity, or retention rule applies? |
| `completeness` | Does the source cover the entire proposition scope and interval? |
| `causal_strength` | State only, effect-bound, one-or-more attempt, or specific-attempt cause? |
| `profile_compatibility` | Can the active settlement profile interpret the artifact? |

An unknown property is not positive evidence. A profile may accept an unknown
property only by returning a bounded or unresolved result and exposing the
assumption.

## 4. Observer and trust-root relationships

The term `independent` is never used without a boundary. The preferred
relationship vocabulary is:

| Relationship | Interpretation |
| --- | --- |
| `SAME_PROCESS` | Observer and delegate share a process boundary. Evidence is delegate-controlled. |
| `SAME_OPERATOR_DISTINCT_PROCESS` | Different process, same declared operator. Process distinction does not imply operator independence. |
| `SEPARATE_SERVICE_SAME_OPERATOR` | Service boundary is distinct; the trust/operator relationship remains shared. |
| `PROVIDER_ORIGINATED` | Provider created or signed the observation. It is provider-attested, not provider-independent. |
| `THIRD_PARTY` | Observer has a declared separate operator/trust context, subject to the named root and assumptions. |
| `SYNTHETIC_FIXTURE` | Offline fixture role. It proves only what the fixture profile defines. |
| `UNKNOWN_RELATIONSHIP` | The profile cannot assess the relationship; no corroboration upgrade is permitted. |

A trust root authenticates only its declared scope. A provider key may
authenticate a provider statement; it does not authenticate an Ananke grant or
an external universal fact unless a profile explicitly binds those claims.
Root declarations should identify:

- root ID and kind (`PUBLIC_KEY`, `PINNED_ISSUER`, `PROVIDER_PROFILE`,
  `FIXTURE_KEY`, or `TRANSPARENCY_LOG`);
- verification-material reference and algorithm profile;
- subject/operator scope;
- validity and replacement/revocation rule;
- authenticated claim types;
- independent operator/process boundary assumptions.

## 5. Identity, predicate, and provenance binding

Evidence coverage must be explicit. A useful coverage object can bind any of
the following, with `status` and `binding_method` for each:

- `principal_id`, `grant_id`, `intent_id`, `task_id`, `delegation_id`;
- `effect_id` and the exact `predicate_id`/stage;
- one `attempt_id`, a declared attempt set, or no attempt;
- observer, issuer, and trust root;
- action descriptor digest, resource, recipient/counterparty, provider;
- provider operation ID, resource ID, ledger ID, or idempotency-key digest;
- event time or interval, observation time, evidence issuance time, and
  verification-time applicability.

The exact `effect_id` is mandatory for an attributed settlement. An artifact
for another effect is not reusable merely because its action, payload, resource,
or human label is similar. An attempt-specific artifact cannot prove a different
attempt without a profile-approved multi-attempt binding that preserves the
ambiguity.

The following binding methods are illustrative and profile-controlled:

`EXPLICIT_FIELD`, `SIGNED_COVERAGE`, `ECHOED_PROVIDER_OPERATION_ID`,
`ECHOED_IDEMPOTENCY_KEY`, `ACTION_DIGEST`, `RESOURCE_IDENTIFIER`,
`TARGET_ACKNOWLEDGEMENT`, `LOG_SEQUENCE`, `DERIVED_FROM_BOUND_ARTIFACT`, and
`UNBOUND`.

`UNBOUND` is diagnostic. It cannot upgrade attribution or causal strength.

## 6. Integrity and replay

Integrity mechanisms answer whether supplied material is the material that the
issuer covered. They do not decide whether the issuer's proposition is true.
Profiles may accept content digests, detached signatures, signed attestations,
transparency-log proofs, and hash-chain links. They must specify canonicalization
and algorithm handling.

Replay handling is separate from integrity. A valid old receipt can be replayed
without being corrupted. The profile should use artifact IDs, content digests,
nonces, sequence numbers, validity intervals, provider operation IDs, or
idempotency bindings to classify replays. The same valid artifact repeated is an
idempotent duplicate, not a second observation. Changed bytes under the same
artifact identity are a corruption or conflict finding.

## 7. Freshness, event time, and late observations

Evidence records at least:

- `event_time` or event interval when the external event is claimed;
- `observed_at` for when the observer saw or measured it;
- `issued_at`/`evidence_issued_at` for artifact creation;
- `valid_from`/`valid_until` where a profile defines them;
- `as_of` for a state snapshot or negative query;
- `verified_at`/`current_time` for the settlement decision.

These times must not be substituted for one another. A late observation may be
admissible if it covers an earlier event and remains within the profile's
freshness and retention rules. A stale observation remains evidence of what was
reported at its old boundary; it cannot establish current state. Incomparable
clocks or excessive uncertainty produce `UNKNOWN` or an explicit stale/
unresolved result, not invented ordering.

## 8. Negative evidence

An absent receipt, timeout, empty local database, or missing provider response
is not a complete negative query. The default evidence result is unresolved.

`COMPLETE_NEGATIVE_LEDGER_QUERY` may support
`NON_OCCURRENCE_SUPPORTED` only if the profile explicitly accepts:

1. the ledger as complete for the named proposition;
2. the queried identity, resource, action, recipient, provider, and effect
   predicate;
3. the full relevant interval, including delayed/late writes;
4. the ledger's retention, consistency, and query semantics;
5. the query's freshness and integrity;
6. the absence of contradictory admissible evidence.

The result must retain the query boundary and assumptions. A stale or partial
negative observation is represented as `NON_OCCURRENCE_NOT_ESTABLISHED` or
`STALE_EVIDENCE` on the relevant axes, never as a universal no-effect claim.

## 9. Retry and duplicate evidence

Evidence may bind to one logical `effect_id` and several attempt IDs. This is
not a contradiction: retries share the logical effect by definition. A lost
acknowledgement followed by a retry creates at least these possible histories:

- first attempt did not dispatch, retry occurred once;
- first attempt occurred and the acknowledgement was lost, retry was suppressed
  by provider idempotency;
- first attempt occurred and the retry created a semantic duplicate;
- both provider records exist but the evidence cannot determine whether they
  are one idempotent operation or two external occurrences.

The result must expose `POSSIBLE_DUPLICATE`, `DUPLICATE_SUPPORTED`, or
`DISTINCT_OCCURRENCES_SUPPORTED` only when the evidence warrants it. The
profile must not infer exactly-once from attempt count, transport success, or a
client-selected key alone.

## 10. Partial and derived evidence

A provider acceptance receipt may be strong evidence for the acceptance stage
and weak or irrelevant evidence for delivery. A derived assertion must preserve
the source evidence IDs, transformation/profile, and any loss of binding or
freshness. Derived evidence cannot be stronger than the strongest proposition
and binding it faithfully preserves.

Human assertions can be recorded and may be useful for review, but they are not
silently promoted to independent or signed evidence. Reconciliation results
can be accepted only under a profile that names the reconciler, inputs,
algorithm/process boundary, freshness, and trust root.

## 11. Conflicts and supersession

Two admissible artifacts conflict when they make incompatible claims about the
same bound predicate and overlapping scope/interval. The verifier retains both
artifact IDs and the competing propositions.

Conflict handling is profile-defined. Permitted explicit relationships include:

- `SUPERSEDES` — a later version wins for the same source and covered scope;
- `STRENGTHENS` — later evidence adds binding or corroboration without changing
  the proposition;
- `WEAKENS` — later evidence exposes staleness, incompleteness, or weaker
  provenance;
- `CONTRADICTS` — later evidence makes an incompatible claim;
- `REOPENS` — later evidence invalidates a profile's prior finality boundary.

Without an explicit precedence, admissible conflict produces
`CONFLICTING_EVIDENCE`, not a majority vote, latest-timestamp rule, provider
preference, or local-record preference.

## 12. Profile incompatibility and unknown extensions

An evidence-bearing extension is not safely ignorable merely because its JSON
shape is syntactically valid. Profiles must list understood settlement-bearing
extensions and choose a policy for unknown ones:

- `RETURN_UNKNOWN` — preserve the artifact but withhold any conclusion that
  depends on the extension;
- `RETURN_UNSUPPORTED` — report the required feature as unsupported;
- `REJECT_INPUT` — treat the target evidence as inadmissible.

Unknown descriptive metadata may be preserved when the profile declares it
non-semantic. Unknown effect identity, predicate, trust, authority, temporal,
integrity, or settlement extensions must not silently disappear.

Two profiles are not automatically compatible because they use the same words.
The result names the active profile, supplied evidence profile(s), compatibility
status, and any missing common interpretation. Incompatibility yields
`PROFILE_INCOMPATIBLE`/`UNKNOWN` rather than a fabricated common conclusion.

## 13. Trust limitations

This taxonomy does not prove that a source is honest, a key is uncompromised,
a provider is complete, a third party is independent, or a snapshot is current.
It makes those assumptions portable, inspectable, and falsifiable. Future
empirical work must measure false confirmations, unresolved rates, duplicate
effects, source compromise, collusion, delayed visibility, and provider-specific
semantics under named profiles.

For the overall semantic model, see
[ACCORD-02C-EFFECT-SETTLEMENT-MODEL.md](./ACCORD-02C-EFFECT-SETTLEMENT-MODEL.md).
