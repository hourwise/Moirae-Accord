# ACCORD-02E-R2 — Adversarial Case Re-Review

These are specification-level checks only. No scenario, provider, benchmark,
classifier, verifier, or experiment was executed.

## Original ADV-01 through ADV-20

| Case | Result | Review outcome |
| --- | --- | --- |
| ADV-01 Honest but stale provider read | RESISTED | Stale evidence cannot settle current state. |
| ADV-02 Lying child plus provider acceptance | RESISTED | Acceptance is not downstream delivery. |
| ADV-03 Correct effect, wrong attempt | RESISTED | Proposition and attempt binding remain separate. |
| ADV-04 Correct resource, wrong recipient | RESISTED | Recipient binding is part of the proposition. |
| ADV-05 Two attenuated siblings exceed shared budget | RESISTED | B composition can remain possible widening/unknown. |
| ADV-06 Parent performs forbidden child action | RESISTED | Direct child authority is not invented from mediation. |
| ADV-07 Revocation races dispatch | RESISTED | Event-time validity is separate from history. |
| ADV-08 Revocation after occurrence | RESISTED | Revocation does not erase factual occurrence. |
| ADV-09 Negative query outside retention window | RESISTED | Completeness/retention is required for negative settlement. |
| ADV-10 Idempotency window expires | RESISTED | Duplicate risk remains representable. |
| ADV-11 Transport task completed, effect unknown | RESISTED | Transport lifecycle is not effect settlement. |
| ADV-12 Conflicting provider and observer evidence | RESISTED | Conflict is preserved or profile-resolved explicitly. |
| ADV-13 Late strong evidence reopens prior unknown | RESISTED | Reopening is profile-scoped and representable. |
| ADV-14 Evidence class valid, trust root missing | RESISTED | Trust context is required for admissibility. |
| ADV-15 Unknown settlement-bearing extension | PARTIALLY_RESISTED | Intended unknown-extension handling exists, but extension classification is not machine-evaluable; see E2E-R2-BLOCK-001. |
| ADV-16 Provider operation ID reused | RESISTED | External correlation does not replace semantic IDs. |
| ADV-17 Same effect ID for semantically different effects | RESISTED | Canonical proposition prevents silent cross-proposition settlement when resolved. |
| ADV-18 Scenario ID leaks expected result | RESISTED | Reviewed IDs are opaque and the catalog declares opacity; future generation must preserve this. |
| ADV-19 Baseline classifier gets Accord-only property | PARTIALLY_RESISTED | ARM-C forbids named Accord labels, but the feature profile is not supplied; see E2E-R2-MAJOR-002. |
| ADV-20 Universal UNKNOWN strategy | RESISTED | Metrics and the preregistration permit high uncertainty to be unattractive. |

`ADV-18` is resisted for the current catalog. `ADV-19` is resisted at the
named-field level but not fully closed for arbitrary feature-source semantics.

## ADV-R1-01 through ADV-R1-10

| Case | Result | Review outcome |
| --- | --- | --- |
| ADV-R1-01 Scorer-extension smuggling | OPEN | Portable extensions remain arbitrary; no namespace/classification registry. |
| ADV-R1-02 Cross-arm manifest substitution | RESISTED | Arm/profile constants and oneOf variants reject ARM-D under ARM-C. |
| ADV-R1-03 Correct effect, wrong predicate | RESISTED | Canonical proposition reference is required. |
| ADV-R1-04 Correct effect, wrong stage | RESISTED | Stage is part of proposition/projection binding. |
| ADV-R1-05 ATTENUATED but invalid at dispatch | RESISTED | B relation does not imply event-time validity. |
| ADV-R1-06 UNKNOWN binding plus strong receipt | RESISTED | UNKNOWN cannot satisfy a positive projection binding. |
| ADV-R1-07 Foreign verifier result | PARTIALLY_RESISTED | Typed reference shape is good; current-run resolution lacks a complete bundle. |
| ADV-R1-08 Projection stronger than native C | RESISTED | PROJ-001 through PROJ-004 and A schema prevent the projection. |
| ADV-R1-09 Complete negative query wrong recipient scope | PARTIALLY_RESISTED | Scope requirements exist, but profile-specific applicability is not fully declared. |
| ADV-R1-10 Score truth in system output | RESISTED | Raw output is untrusted and scorer truth is not an arm source. |

## R2-ADV-01 through R2-ADV-15

| Case | Result | Review outcome |
| --- | --- | --- |
| R2-ADV-01 Public scorer traversal | RESISTED | No public scorer locator found. |
| R2-ADV-02 ARM-C selects ARM-D profile | RESISTED | Manifest profile const does not match ARM-C. |
| R2-ADV-03 Oracle nested in metadata | PARTIALLY_RESISTED | Closed manifest metadata is safe, but a portable bundle extension can still carry it. |
| R2-ADV-04 Accord result as classifier feature | PARTIALLY_RESISTED | Named forbidden source is rejected; undefined feature profile leaves a residual channel. |
| R2-ADV-05 Generic arbitrary arm value | RESISTED | No arbitrary experiment-controlled value member exists in the manifest schema. |
| R2-ADV-06 Standalone VERIFIED | RESISTED | Native C, map, and proposition references are required. |
| R2-ADV-07 Wrong projection profile | RESISTED | Mapping profile reference is discriminated and profile compatibility is normative. |
| R2-ADV-08 Foreign verifier result | PARTIALLY_RESISTED | LIN rules name rejection, but no complete bundle/scope contract exists. |
| R2-ADV-09 Nonexistent typed reference | PARTIALLY_RESISTED | LIN-001 names failure, but the searched collection is undefined. |
| R2-ADV-10 Provider ID as attempt | PARTIALLY_RESISTED | LIN-008 forbids substitution; resolution still needs a defined bundle. |
| R2-ADV-11 Wrong proposition | PARTIALLY_RESISTED | Canonical proposition rule exists; cross-record resolution is incomplete. |
| R2-ADV-12 UNKNOWN required binding | RESISTED | PROP-004 blocks positive strengthening. |
| R2-ADV-13 NOT_APPLICABLE abuse | OPEN | Predicate-specific applicability is not machine-declared. |
| R2-ADV-14 ARM-B fairness regression | RESISTED | ARM-B includes provider-state and reconciliation source types. |
| R2-ADV-15 Raw output oracle injection | RESISTED | Output remains untrusted and cannot become scorer truth. |

## New ADV-R2 cases

| Case | Result | Finding |
| --- | --- | --- |
| ADV-R2-01 Missing validation-bundle member | OPEN | E2E-R2-BLOCK-002: no complete bundle contract defines missing resolution. |
| ADV-R2-02 Normative rule cycle | RESISTED | No acceptance-critical cycle was found in the declared family dependencies; no executable dependency graph exists. |
| ADV-R2-03 Referenced record structurally invalid | PARTIALLY_RESISTED | Structural-first intent is clear, but invalid-record handling is not a registered cross-record rule. |
| ADV-R2-04 Proposition mutation | OPEN | Optional digest is not backed by a named mismatch rule; see E2E-R2-MAJOR-005. |
| ADV-R2-05 Optional digest mismatch | OPEN | No deterministic digest failure code is registered; see E2E-R2-MAJOR-005. |
| ADV-R2-06 Truth-dependent normalization | OPEN | No supplied normalization/adapter profile makes independence reproducible; see E2E-R2-MAJOR-002. |
| ADV-R2-07 Orchestrator condition leakage | OPEN | Arm profiles list condition labels as allowed; see E2E-R2-MAJOR-003. |
| ADV-R2-08 Occurrence with unknown attempt attribution | RESISTED | C supports occurrence with attribution unknown. |
| ADV-R2-09 Equivalent content under different proposition IDs | ALLOWED_WITH_DISTINCT_IDENTITY | IDs denote record identity; semantic equivalence is not inferred merely from equal fields. |
| ADV-R2-10 Score record fed to arm | RESISTED | Score record is scorer-only and not an allowed source type. |

The OPEN and PARTIALLY_RESISTED cases are specification gaps, not experimental
results. They are sufficient to prevent a READY verdict.
