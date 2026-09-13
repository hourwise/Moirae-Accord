# ACCORD-01 Independent Review Method

## Purpose

This process is designed to reduce confirmation bias and prevent the authors’ preferred architecture from becoming an unstated premise. The reviewer may return `CONTINUE`, `CONTINUE_WITH_CHANGES`, `PIVOT`, or `REJECT`.

## PHASE 1 — BLIND REVIEW

The reviewer receives only:

`docs/reviews/ACCORD-01-BLIND-BRIEF.md`

The reviewer must:

- investigate current prior art independently;
- challenge the novelty and usefulness of the research question;
- challenge the terminology and identify better alternatives;
- propose an architecture independently;
- propose falsification criteria and a minimum experiment;
- identify missing threat classes and hidden trust assumptions;
- distinguish authorization from effect verification;
- decide whether the project should continue at all.

The reviewer should freeze or return the Phase 1 analysis before receiving the architecture appendix.

## PHASE 2 — ARCHITECTURE RED TEAM

Only after Phase 1 is frozen, provide:

`docs/reviews/ACCORD-01-ARCHITECTURE-APPENDIX.md`

The reviewer then attacks:

- component boundaries;
- trust assumptions and bypass paths;
- authority semantics and attenuation;
- receipt authority and evidence independence;
- failure, retry, idempotency, and reconciliation semantics;
- task identity versus effect identity;
- A2A/MCP placement;
- methodology and falsifiability;
- testability and formalization needs;
- strength and scope of the claims.

The reviewer should explicitly identify where the independent design is better, where the appendix is better, and where both are inadequate.

## PHASE 3 — FINAL VERDICT

The reviewer returns exactly one primary verdict:

```text
CONTINUE
CONTINUE_WITH_CHANGES
PIVOT
REJECT
```

The reviewer must state why, list blockers before implementation, separate mandatory changes from optional improvements, and rewrite the research question if the original formulation is not defensible.

## Evidence and preservation rules

- Preserve the external review verbatim in `ACCORD-01-EXTERNAL-REVIEW-VERBATIM.md`.
- Do not edit criticism to make it more favourable.
- Record the authors’ response separately in `ACCORD-01-RESPONSE.md`.
- Record the final research decision separately in `ACCORD-01-DECISION.md`.
- Classify each material criticism as `ACCEPTED`, `PARTIALLY_ACCEPTED`, `REJECTED_WITH_EVIDENCE`, or `DEFERRED_FOR_TEST`.
- No implementation, dependency installation, source-repository change, Fates change, or ACCORD-01 acceptance tag is part of this preparation task.
