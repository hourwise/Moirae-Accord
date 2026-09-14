# ACCORD-02E-R1 — Claim Audit

This audit distinguishes normative rules from empirical hypotheses and checks
whether R1 introduced language stronger than the machine-readable boundary.

| Claim | Classification | Re-review status | Finding |
| --- | --- | --- | --- |
| Native ACCORD-02C axes are the semantic source for effect settlement. | Normative definition | Supported | None |
| A-style `VERIFIED`/`CORROBORATED` values are qualified projections, not universal truth. | Normative definition | Supported in map and prose; A schema does not require proof of projection | `E2E-MAJOR-001` |
| `NO_EFFECT_OBSERVED` is not ordinary evidence of non-occurrence. | Normative definition | Supported by C/profile/map rules | None |
| `ATTENUATED` or `CONTAINED` does not mean `AUTHORIZED`. | Normative definition | Supported | None |
| Invalid authority does not imply no effect. | Normative definition | Supported | None |
| Typed references make lineage independently auditable. | Engineering contract | Overstated if read as automatic referential integrity | `E2E-MAJOR-003` |
| Sanitized arm manifests cannot carry scorer-only material. | Engineering contract | Overstated; generic nested values and profile membership are not schema-closed | `E2E-BLOCK-001`, `E2E-MAJOR-005` |
| The public scenario catalog is safe orchestration data. | Engineering contract | Overstated while it directly references scorer expectations | `E2E-R1-BLOCK-001` |
| Predicate/stage binding prevents cross-proposition strengthening. | Normative definition | Supported only after future profile/verifier checks; not independently enforced by D schema | `E2E-MAJOR-004` |
| ARM-A/B/C are credible engineering baselines. | Experimental design requirement | Supported in declared capabilities; enforcement gap remains | `E2E-MAJOR-005` |
| Stronger evidence affordances may improve the trade-off. | Empirical hypothesis | Open; no result claimed | None |
| Accord may show no measurable improvement. | Research limitation | Supported | None |
| Accord prevents effects outside complete mediation. | Prohibited claim | Not found in the remediated stack | None |
| Exactly-once external occurrence follows from a stable idempotency key. | Prohibited claim | Not found; explicitly denied | None |
| A2A task completion is external-effect settlement. | Prohibited claim | Not found; transport remains non-authoritative | None |

## Claim conclusion

The core research and architectural claims remain appropriately conditional.
The material overclaims are limited to describing the R1 boundary as
machine-closed when the schemas still delegate critical checks to a future
harness, resolver, or verifier. Those overclaims are acceptance-relevant
because the task requires the information boundary to be independently
auditable.
