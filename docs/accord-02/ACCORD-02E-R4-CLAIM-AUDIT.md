# ACCORD-02E-R4 — Claim Audit

## Normative definitions

The following are specification definitions rather than empirical results:

- the exact-version package policy `CLOSED_EXACT_VERSION`;
- typed profile and schema-contract resolution outcomes;
- the closed primary role vocabulary;
- RFC 8785 JCS, UTF-8, and SHA-256 as the declared canonicalization method;
- scenario IDs as correlation-only, non-authoritative, and non-evidentiary;
- no latest/default/private-database fallback;
- native settlement results remaining authoritative over verifier projections;
- authority/effect orthogonality and conservative unknown handling.

## Engineering hypotheses and deferred evidence

These remain future implementation/conformance questions:

- two independent validators will produce the same decisions when both conform to the contract;
- JSON Schema implementations in different languages will implement the declared structural constraints equivalently;
- the future verifier and harness will preserve the stated information boundaries;
- the experiment will measure the proposed metrics with usable reliability;
- any arm will outperform another arm.

The lack of executable implementation evidence is not itself an R4 specification defect.

## Supported limitation claims

The stack appropriately limits the following claims:

- self-contained verification is relative to supplied records, package contracts, profiles, and trust roots;
- verification does not establish arbitrary real-world truth;
- provider evidence may be false, stale, incomplete, or conflicted;
- scenario-ID requirements do not prove cryptographic non-correlation;
- no complete-mediation or universal-prevention guarantee is claimed;
- digest failure does not imply no effect or invalid authority.

## Overclaims requiring correction before freeze

The R4 remediation artifacts describe the package as if all active profile and schema contracts are already closed. That is not supported by the current inventory:

1. required profile categories are absent from the package;
2. active source schemas are outside the package;
3. digest applicability is not resolved for concrete bundle/scorer forms;
4. source registry roles are not closed to the package vocabulary.

Until those defects are repaired, “self-contained”, “all active profiles resolve”, “all schema contracts resolve”, and “acceptance-critical validation is fully deterministic from the package” must be treated as conditional design goals, not established properties of the current stack.

## No empirical claims

No experiment has run. No validator, verifier, classifier, provider, or harness has run. No empirical benefit, interoperability, accuracy, or acceptance result has been demonstrated. The review verdict is based on static and cross-artifact specification evidence only.
