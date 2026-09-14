# ACCORD-02E-R2 — Claim Audit

## Classification key

- **Normative definition:** a required semantic or validation rule.
- **Engineering hypothesis:** a claim to be tested about implementation behavior.
- **Empirical hypothesis:** a claim that requires scored future runs.
- **Prior-art statement:** a bounded statement preserved from ACCORD-01.
- **Limitation:** an explicit non-claim.

## Material claims

| Claim | Classification | Audit result |
| --- | --- | --- |
| `effect_id` is a logical intended effect identity and `attempt_id` is per dispatch | Normative definition | Supported and consistent across A/C/D. |
| Grant relation, effective authority, and event-time validity are separate | Normative definition | Supported; no authority/effect conflation found. |
| A projection is qualified and profile-bound | Normative definition | Supported after R2 schema repair. |
| Native C result remains authoritative for settlement semantics | Normative definition | Supported; projection does not overwrite native result. |
| Portable evidence can support bounded conclusions | Engineering hypothesis / limitation | Properly scoped; no universal truth claim. |
| Stronger evidence affordances may improve the trade-off | Empirical hypothesis | Properly left for ACCORD-02D; no result is claimed. |
| Accord will outperform durable/provider-state baselines | Empirical hypothesis | Not claimed. A strong baseline may win. |
| A2A/MCP metadata is authority | Prohibited claim | Not present; transport IDs remain correlation metadata. |
| Provider receipt proves arbitrary business goal satisfaction | Prohibited claim | Not present; predicate/stage binding prevents this. |
| Exactly-once effect follows from one idempotency key | Prohibited claim | Not present. |
| Complete negative evidence proves universal non-occurrence | Prohibited claim | Not present; scope and completeness are required. |
| Typed lineage proves provenance by string syntax | Prohibited claim | Not present; semantic record resolution is required. |
| A canonical proposition proves occurrence or causality | Limitation | Explicitly not claimed. |
| A scorer-only oracle is a verifier input | Prohibited claim | Not present in the public catalog or arm source types. |
| Current arm profiles fully prevent condition-label leakage | Engineering/design claim | Not established; E2E-R2-MAJOR-003 remains open. |
| Current extension policy is machine-enforceable | Engineering/design claim | Not established; E2E-R2-BLOCK-001 remains open. |
| Current validation rules are independently reproducible | Engineering/design claim | Not established because the complete bundle and profiles are absent. |

## Overclaim risks remaining

1. The R2 contract calls the checks deterministic, but `ARM-007`, LIN scope,
   digest checks, and profile membership are not fully inspectable from supplied
   artifacts.
2. The D design says a sanitized manifest is validated against profiles, but
   the profiles contain role-visible orchestration fields that are not
   separated from fixture-private configuration.
3. The existence of a typed `NORMALIZATION_PROFILE` reference could be read as
   a frozen normalization policy even though no such profile artifact exists.
4. The existence of a canonical proposition could be read as proof of semantic
   equivalence or causal attribution; it is only a binding descriptor.

No claim that Accord has improved the baseline trade-off, achieved external
ground truth, guaranteed exactly-once effects, or completed an experiment is
made by this review.
