# ACCORD-02E-R3 — Acceptance Readiness

## Result

**AMEND**

ACCORD-02 MUST NOT proceed to acceptance/seal.

## Acceptance blockers

1. Make active profile references resolvable from the declared verifier and
   experiment bundles. The current `PROFILE` reference variant is not an
   admitted inventory record and carries no inline definition.
2. Define the structural-contract source for generic bundle `content`,
   including deterministic schema/version resolution and canonical digest
   input.

## Major residuals

1. Close producer/consumer role membership in the visibility profile.
2. Replace the scenario-ID opacity assertion with a deterministic profile or
   a reviewable construction that prevents expected-result side channels.
3. Define canonicalization for every digestable generic bundle entry.

## Readiness criteria not met

- not all 71 acceptance-critical rules are evaluable from the declared
  self-contained scope;
- the external-verification statement is not supported as written;
- historical R2 blocker `E2E-R2-BLOCK-002` remains open;
- new R3 blockers remain open;
- the review cannot certify that two independent implementations will make
  the same decision from a valid bundle.

## What is not required

No new authority model, settlement model, research hypothesis, transport,
runtime, verifier, validator, harness, provider, classifier implementation, or
acceptance artifact is required by this review. The appropriate next step is a
bounded amendment followed by a fresh integrated closure review.
