# ACCORD-02E-R1 — Adversarial Re-Review Cases

This is a review artifact, not an experiment execution record. No case below
was run against a harness, provider, verifier executable, or distributed
system. Outcomes describe what the remediated schemas and normative text
permit or prevent by inspection.

## Original ADV-01 through ADV-20

| Case | Construction | Re-review outcome | Finding / consequence |
| --- | --- | --- | --- |
| ADV-01 | Honest delegate with a stale provider read says the effect is absent. | RESISTED | C freshness and occurrence axes preserve stale/unknown; no current non-occurrence claim. |
| ADV-02 | Lying child claims delivery while the provider proves only acceptance. | PARTIALLY_RESISTED | C/A prose prevents downstream promotion; standalone A schema does not require the native map reference. `E2E-MAJOR-001`. |
| ADV-03 | Real occurrence is bound to another retry attempt. | PARTIALLY_RESISTED | C wrong-attempt policy is conservative, but D cross-record/binding equality is not schema-enforced. `E2E-MAJOR-003`, `E2E-MAJOR-004`. |
| ADV-04 | Correct resource, wrong recipient. | PARTIALLY_RESISTED | Recipient binding exists, but a schema-valid inconsistent descriptor can be constructed without a cross-field resolver. `E2E-MAJOR-004`. |
| ADV-05 | Two attenuated siblings exceed a shared budget. | RESISTED | B effective-authority state can be `POSSIBLE_WIDENING`; it is separate from grant relation. |
| ADV-06 | Parent performs an action outside direct child authority. | RESISTED | B mediation and composition distinctions preserve parent-mediated possibility versus direct child authority. |
| ADV-07 | Revocation races dispatch. | RESISTED | D carries event-time validity at dispatch independently of derivation/admission. |
| ADV-08 | Revocation occurs after a real external effect. | RESISTED | Historical occurrence and later validity remain separate. |
| ADV-09 | Complete negative query retention does not cover the dispatch interval. | RESISTED | C complete-negative requirements include interval and retention; ordinary negative evidence cannot settle non-occurrence. |
| ADV-10 | Idempotency window expires before retry. | RESISTED | C duplicate axis and reopening/finality semantics preserve duplicate risk and do not imply exactly-once. |
| ADV-11 | Transport task says completed while the intended effect remains unknown. | RESISTED | Transport metadata is non-authoritative and C/A effect settlement remains distinct. |
| ADV-12 | Provider and observer evidence conflict. | RESISTED | Conflict, sufficiency, and reopening axes preserve unresolved conflict. |
| ADV-13 | Later strong evidence follows an earlier unknown-terminal result. | RESISTED_WITH_PROFILE_SCOPE | Reopening is expressible where the active profile permits it; `UNKNOWN_TERMINAL` is not universal finality. |
| ADV-14 | Evidence class is valid but its trust root is missing. | RESISTED | A/C profiles permit inadmissible, unverifiable, or incompatible outcomes rather than a stronger settlement. |
| ADV-15 | Authority chain has an unknown authority-bearing extension. | RESISTED | B unknown-dimension policies and D separate authority axes prevent silent attenuation. |
| ADV-16 | Provider operation ID is reused across logical effects. | PARTIALLY_RESISTED | A prose forbids identity substitution, but arbitrary ID values and absent referential checks leave a machine-level aliasing gap. `E2E-MAJOR-003`, `E2E-MINOR-001`. |
| ADV-17 | Same effect ID is reused for semantically different predicates/stages. | PARTIALLY_RESISTED | Predicate/stage descriptors exist, but equality and target-to-evidence checks are not schema-enforced. `E2E-MAJOR-004`. |
| ADV-18 | Scenario catalog or its referenced scorer catalog is exposed to an arm. | OPEN_BYPASS | Public catalog directly contains `scorer_expectation_catalog_ref`; the attack can traverse the protected expectation path. `E2E-BLOCK-001`, `E2E-R1-BLOCK-001`. |
| ADV-19 | Classifier receives an Accord-only evidence property. | OPEN_BYPASS | ARM-C has a forbidden-field list, but generic field values and absent selected-profile membership enforcement allow a schema-valid smuggling path. `E2E-BLOCK-001`, `E2E-MAJOR-005`. |
| ADV-20 | Every case is reported as UNKNOWN. | RESISTED | D metrics and research framing do not treat universal UNKNOWN as an automatic win; excessive indeterminacy remains scoreable. |

## Post-remediation ADV-R1-01 through ADV-R1-10

| Case | Construction | Re-review outcome | Finding / consequence |
| --- | --- | --- | --- |
| ADV-R1-01 | Put expected outcome inside a generic extension or nested field value. | OPEN_BYPASS | Manifest `value` is unconstrained and the finite forbidden path list does not reject nested oracle members. `E2E-BLOCK-001`. |
| ADV-R1-02 | Use an ARM-D manifest as ARM-C input. | OPEN_BYPASS | `arm_id` and `input_profile_ref` are not cross-bound, and allowlist membership is deferred to a future harness. `E2E-MAJOR-005`. |
| ADV-R1-03 | Supply a valid receipt for another predicate. | PARTIALLY_RESISTED | C profile rules can exclude the evidence, but D/A schemas do not enforce descriptor equality. `E2E-MAJOR-004`. |
| ADV-R1-04 | Supply an earlier-stage receipt for a later-stage claim. | PARTIALLY_RESISTED | Stage is represented and documented, but the A schema and D projection do not impose the native C stage condition structurally. `E2E-MAJOR-001`, `E2E-MAJOR-004`. |
| ADV-R1-05 | Use `ATTENUATED` grant relation with `INVALID_AUTHORITY` at dispatch. | RESISTED | Three independent authority axes represent the combination. |
| ADV-R1-06 | Use UNKNOWN predicate binding together with a strong receipt. | PARTIALLY_RESISTED | The map requires exact binding for VERIFIED, but a standalone A schema can carry a stronger-looking result without a native/map reference. `E2E-MAJOR-001`, `E2E-MAJOR-004`. |
| ADV-R1-07 | Insert a valid verifier result from another experiment run. | OPEN_LINEAGE_GAP | Typed record categories are present, but run/result/effect equality and reference resolution are not schema-enforced. `E2E-MAJOR-003`. |
| ADV-R1-08 | Project `VERIFIED` beyond what native C supports. | PARTIALLY_RESISTED | The named map rejects the projection normatively; the standalone A result schema does not require proof of map application. `E2E-MAJOR-001`. |
| ADV-R1-09 | Use complete-negative evidence with the wrong recipient scope. | PARTIALLY_RESISTED | C completeness requires recipient binding where applicable, but D duplicated bindings can be inconsistent without a cross-field check. `E2E-MAJOR-004`. |
| ADV-R1-10 | Put scorer truth inside a system-visible raw output field and rely on later scoring separation. | OPEN_BYPASS | Raw field values are unconstrained and the result schema records an allowlist reference without proving membership or sanitization. `E2E-BLOCK-001`, `E2E-MAJOR-005`. |

## Interpretation

The semantic model resists many attacks when a future implementation follows
the prose and active profiles. The remaining open attacks are not empirical
failures; they are specification-boundary failures. They prevent a fresh
`READY` verdict because a schema-valid arm input or standalone A result can
still bypass the intended normative separation.
