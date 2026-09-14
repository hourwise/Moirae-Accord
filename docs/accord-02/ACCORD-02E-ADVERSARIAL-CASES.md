# ACCORD-02E — Review-Only Adversarial Cases

These cases are review constructions only. They are not executions, benchmarks,
conformance vectors, or experiment results. They test the stated A/B/C/D rules and
record where the current specification is safe, profile-dependent, or blocked
by an integrated ambiguity.

## ADV-01 — Honest but stale provider read

The effect occurred, but a provider-state reread returns an older absence.

Expected handling: `STALE_EVIDENCE`, `UNKNOWN`, or an equivalent bounded result;
no current non-occurrence. The C freshness and negative-evidence rules handle the
case. **Outcome: bounded; no finding.**

## ADV-02 — Lying child plus legitimate signed provider acceptance

The child claims recipient delivery. A signed provider artifact proves only
`provider_acceptance`.

Expected handling: the acceptance predicate may be supported, while delivery or
recipient acknowledgement remains unresolved. A delegate claim cannot upgrade
the predicate. **Outcome: intended; result-label translation remains covered by
`E2E-MAJOR-001`.**

## ADV-03 — Correct effect, wrong attempt

The external effect occurred, but the evidence names retry A2 while the selected
target asks whether A1 caused it.

Expected handling: occurrence may be supported at effect level; A1 attribution
and causality remain unknown or mismatched. Wrong-attempt evidence is excluded
from the selected target. **Outcome: intended in prose; D's optional attempt
binding contributes to `E2E-MAJOR-003` and `E2E-MAJOR-004`.**

## ADV-04 — Correct resource, wrong recipient

The receipt identifies the correct resource and operation but a different
recipient.

Expected handling: recipient-bound predicate does not settle. The resource fact
may remain diagnostically useful, but recipient delivery is not supported.
**Outcome: bounded; stage/predicate binding remains part of `E2E-MAJOR-004`.**

## ADV-05 — Two attenuated siblings exceed a shared budget

The parent pool is £100 and two individually attenuated children each claim £80.
No reservation or accounting snapshot is supplied.

Expected handling: `POSSIBLE_WIDENING`, `UNKNOWN`, or non-composition according to
the declared B profile; never automatic containment. **Outcome: intended; no
finding.**

## ADV-06 — Parent performs a forbidden child action

The child grant is narrow, but a parent-mediated path performs an action outside
the child grant.

Expected handling: the direct child grant remains narrow; the mediated path is
reported as possible widening, unsupported, or unbound. Child authorship is not
invented. **Outcome: intended; no finding.**

## ADV-07 — Revocation races dispatch

Revocation and dispatch occur within an interval whose cross-process ordering is
not established.

Expected handling: derivation, admission, dispatch, and verification remain
separate times; the authority result is `UNKNOWN` or profile-bounded rather than
an invented order. **Outcome: intended; no finding.**

## ADV-08 — Revocation after real occurrence

The grant is revoked after the provider records the external effect.

Expected handling: authority may be invalid at later evaluation while historical
dispatch and occurrence remain supported. **Outcome: intended; no finding.**

## ADV-09 — Complete negative query with insufficient retention

The source claims a complete ledger query, but its retention window begins after
the effect's relevant interval.

Expected handling: completeness or interval binding fails; the result is stale,
unknown, or insufficient, not supported non-occurrence. **Outcome: intended; no
finding.**

## ADV-10 — Idempotency window expires before retry

The response is lost and a retry arrives after the provider's idempotency window.

Expected handling: a possible or confirmed duplicate may be represented only with
appropriate evidence; a single key cannot produce an exactly-once claim.
**Outcome: intended; provider-operation reuse policy remains a minor profile
gap in `E2E-MINOR-001`.**

## ADV-11 — Transport task says completed while effect remains unknown

An A2A-shaped task or MCP-shaped call reports completion, but the intended
external predicate has no admissible downstream evidence.

Expected handling: task lifecycle completion remains transport/task evidence;
effect settlement remains unknown. **Outcome: intended in prose; the exact A
`VERIFIED`/C mapping is part of `E2E-MAJOR-001`.**

## ADV-12 — Conflicting provider and observer evidence

Two admissible, bound sources disagree about occurrence.

Expected handling: preserve conflict unless the selected profile declares a
legitimate precedence rule. No latest-timestamp, provider-convenience, local
record, or majority shortcut is allowed. **Outcome: intended; no finding.**

## ADV-13 — Late strong evidence reopens prior UNKNOWN_TERMINAL

The earlier result is `UNKNOWN_TERMINAL`; later evidence is fresh, bound, and
admissible under a profile permitting reopening.

Expected handling: a new result may reopen or supersede the earlier result while
preserving its history. **Outcome: intended; the label mapping from A terminal
unknown to C reopening state remains `E2E-MAJOR-001`.**

## ADV-14 — Evidence class valid but trust root missing

The artifact has a structurally valid evidence class and payload but no accepted
trust root.

Expected handling: inadmissible, unsupported, or unknown according to the profile;
the class label alone cannot elevate it. **Outcome: intended; no finding.**

## ADV-15 — Structurally valid authority chain with unknown authority extension

The child grant is otherwise a subset, but it contains an unknown
authority-bearing extension.

Expected handling: the relation is unknown or unsupported, not attenuated.
**Outcome: intended; no finding.**

## ADV-16 — Provider operation ID reused across logical effects

The provider emits the same operation identifier for two different `effect_id`
values.

Expected handling: the provider identifier cannot merge the Accord effects. The
effect and predicate bindings remain authoritative for Accord correlation, and
the reuse is preserved as a diagnostic. **Outcome: intended in prose; an
explicit provider-operation uniqueness/reuse rule is recommended in
`E2E-MINOR-001`.**

## ADV-17 — Same effect ID used for semantically different predicates

Two records reuse one `effect_id` for `provider_acceptance` and
`recipient_acknowledgement` without a declared staged predicate graph.

Expected handling: the target predicate and profile must distinguish the claims;
the conflicting binding cannot be silently merged. **Outcome: intended in
prose, but the absence of a first-class effect/predicate record and required D
stage binding contributes to `E2E-MAJOR-004`.**

## ADV-18 — Experiment scenario ID leaks expected oracle result

The future run passes the D scenario catalog to the verifier or delegate. The
catalog contains `oracle_state` and expected conformance bounds alongside the
scenario ID.

Expected handling: this must be prohibited. Under the current specification the
catalog is called a design catalog, but no sanitized system-visible manifest or
field-level separation is required. A compliant implementation could therefore
read expected truth or conformance outcomes.

**Outcome: BLOCKING finding `E2E-BLOCK-001`.**

## ADV-19 — Baseline classifier gets Accord-only evidence property

ARM-C receives an Accord evidence-class, binding, settlement, or trust-root
label that ARM-B would not ordinarily have.

Expected handling: prohibited by D's prose, but not mechanically prevented by a
per-arm input manifest or the open-ended `baseline_or_system_output` field in the
D result schema. **Outcome: MAJOR experiment-risk finding
`E2E-MAJOR-005`.**

## ADV-20 — Universal UNKNOWN strategy

An arm returns `UNKNOWN` for every case and thereby avoids positive false
confirmation.

Expected handling: false confirmation may be zero, but indeterminacy, escalation,
latency, and comparative trade-off reporting make the arm empirically
unattractive. It is not an automatic victory or categorical failure.
**Outcome: intended; no finding.**

## Review conclusion

The adversarial review does not show that the core authority/effect or
settlement semantics are incoherent. It does show that the experiment-facing
catalog and cross-slice result translations are not yet sufficiently closed for
acceptance or harness authorization.
