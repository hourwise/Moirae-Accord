# ACCORD-02E-R5 — Adversarial Cases

These are static specification and inventory checks. No executable validator, verifier, harness, experiment, classifier training, provider call, or dependency installation was used.

## Profile attacks

| Case | Construction | Result |
| --- | --- | --- |
| PROF-R5-01 | Correct profile ID with wrong version | **RESISTED** — exact tuple does not resolve. |
| PROF-R5-02 | Correct version with wrong profile type | **RESISTED** — field-context/profile-type mismatch fails. |
| PROF-R5-03 | Profile exists locally but is absent from package | **RESISTED** — repository-local fallback is prohibited. |
| PROF-R5-04 | Versionless active profile reference | **RESISTED** — active reference schema/rule requires exact version. |
| PROF-R5-05 | Duplicate type/ID/version profile contract | **RESISTED** — package uniqueness check fails. |
| PROF-R5-06 | Required trust-root profile omitted | **RESISTED** — required profile resolution fails. |

## Source-schema attacks

| Case | Construction | Result |
| --- | --- | --- |
| SRC-R5-01 | Unknown source schema ID | **RESISTED** — no package contract. |
| SRC-R5-02 | Known source schema ID with wrong version | **RESISTED** — exact version mismatch. |
| SRC-R5-03 | Correct payload presented under wrong source type | **RESISTED** — source membership and record type disagree. |
| SRC-R5-04 | Schema file exists but is not in active package | **RESISTED** — file existence has no membership effect. |
| SRC-R5-05 | Filename/path spoof | **RESISTED** — membership uses supplied schema ID/version and registry, not filenames. |

## Role attacks

| Case | Construction | Result |
| --- | --- | --- |
| ROLE-R5-01 | Source role `MAGIC_ADMIN` | **RESISTED** — outside the nine-value vocabulary. |
| ROLE-R5-02 | Typographical ARM-C role | **RESISTED** — exact enum membership required. |
| ROLE-R5-03 | Valid ARM-C role on legitimate classifier source | **ADMITTED** — permitted by source registry/profile. |
| ROLE-R5-04 | SCORER-only source exposed to ARM-D | **RESISTED** — source/visibility profile forbids it. |
| ROLE-R5-05 | Undeclared future role | **RESISTED** — no current-package default visibility. |

## Canonicalization attacks

| Case | Construction | Result |
| --- | --- | --- |
| CANON-R5-01 | Concrete verifier record with valid digest | **RESISTED TO AMBIGUITY** — applicability resolves to one mapping. |
| CANON-R5-02 | Concrete experiment record | **RESISTED TO AMBIGUITY** — applicability resolves to one mapping. |
| CANON-R5-03 | Concrete scorer record | **RESISTED TO AMBIGUITY** — scorer schema identity and mapping are present. |
| CANON-R5-04 | Digest-bearing form absent from mapping | **RESISTED** — unverifiable/failure; no silent fallback. |
| CANON-R5-05 | Wrong digest | **RESISTED** — digest mismatch only. |
| CANON-R5-06 | Optional digest absent | **ADMITTED FOR TYPED RESOLUTION** where the active contract makes it optional. |
| CANON-R5-07 | Conflicting mappings for one concrete key | **RESISTED** — package/mapping uniqueness condition fails. |

## Historical problematic cases and regressions

The following previously problematic cases were rechecked against the R5 changes. R5 is package-inventory-only, so the semantic closure from earlier reviews remains intact.

| Cases | Outcome |
| --- | --- |
| `ADV-18`, `ADV-19` | **RESISTED** — no public scorer locator; ARM-C profile excludes Accord-only outcome semantics. |
| `ADV-R1-01`, `ADV-R1-07` | **RESISTED** — extension smuggling and foreign verifier result remain rejected. |
| `ADV-R2-01`, `ADV-R2-04`, `ADV-R2-05`, `ADV-R2-06`, `ADV-R2-07` | **RESISTED** — missing bundle member, proposition mutation, digest mismatch, truth-dependent normalization, and role/condition leakage remain invalid. |
| `ADV-R3-01`, `ADV-R3-03`, `ADV-R3-05`, `ADV-R3-07`, `ADV-R3-10`, `ADV-R3-12` | **RESISTED** — missing registry, source spoof, truth-dependent normalizer, missing predicate profile, ambient lookup, and scorer-bundle-as-verifier attacks fail. |
| `ADV-R4-01`, `ADV-R4-03`, `ADV-R4-04`, `ADV-R4-05`, `ADV-R4-09`, `ADV-R4-10` | **RESISTED** — local undeclared profile, unknown schema, unknown role, wrong canonicalization, outside-package contract, and private fallback fail. |
| `ADV-01` through `ADV-17`, `ADV-20`, `ADV-R1-02` through `ADV-R1-10`, and remaining R2 cases | **NO REGRESSION OBSERVED** — existing protections remain represented by the unchanged A/B/C/D/R1/R2/R3/R4 contracts. |

## Implementation deferral case

| Case | Outcome |
| --- | --- |
| ADV-R5-10 — missing validator executable | **DEFERRED_TO_CONFORMANCE_IMPLEMENTATION**; absence of an executable is not a specification failure when the normative contract is complete. |
