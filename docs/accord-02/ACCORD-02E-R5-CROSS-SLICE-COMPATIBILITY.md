# ACCORD-02E-R5 — Focused Compatibility Matrix

Statuses are limited to `EXACT`, `COMPATIBLE`, `COMPATIBLE_WITH_PROFILE`, `AMBIGUOUS`, `INCOMPATIBLE`, and `NOT_APPLICABLE`. This matrix was rebuilt for R5 rather than copied from an earlier review.

| ID | Relation | Status | Evidence |
| --- | --- | --- | --- |
| R5-COMP-001 | active R5 package ↔ package schema | EXACT | Package ID, version, policy, and schema ID/version satisfy the R5 package contract. |
| R5-COMP-002 | package schema contracts ↔ schema paths | EXACT | 44/44 package schema paths exist and parse; schema-contract keys are unique. |
| R5-COMP-003 | package profile contracts ↔ profile paths | EXACT | 31/31 declared paths exist; profile type/ID/version keys are unique. |
| R5-COMP-004 | active profile references ↔ package profiles | EXACT | 16/16 current arm references resolve with exact versions; no versionless active reference. |
| R5-COMP-005 | source registry ↔ package schema contracts | EXACT | 13/13 active source-schema pairs are package members. |
| R5-COMP-006 | source registry roles ↔ authoritative role vocabulary | EXACT | All roles are members of the nine-value package vocabulary. |
| R5-COMP-007 | digest-bearing verifier forms ↔ canonicalization | EXACT | 11 concrete verifier mapping entries resolve to package schema pairs. |
| R5-COMP-008 | digest-bearing experiment forms ↔ canonicalization | EXACT | 33 concrete experiment mapping entries resolve to package schema pairs. |
| R5-COMP-009 | digest-bearing scorer forms ↔ canonicalization | EXACT | 5 scorer entries have concrete schema identity and mappings. |
| R5-COMP-010 | active rules ↔ R3 base and R5 overlay | EXACT | 71 base rules plus 11 R5 overlay rules, with three explicit replacements, produce 82 unique active IDs. |
| R5-COMP-011 | active rules ↔ required profiles | COMPATIBLE_WITH_PROFILE | Profile-dependent rules resolve through the exact R5 package; no missing active profile was found. |
| R5-COMP-012 | verifier bundle ↔ self-contained scope | COMPATIBLE_WITH_PROFILE | Instance records are supplied by the bundle; normative contracts are supplied by the exact package; ambient lookup is forbidden. |
| R5-COMP-013 | scorer bundle ↔ isolated scope | EXACT | Scorer bundle is marked scorer-only and is structurally forbidden as arm or verifier input. |
| R5-COMP-014 | scenario ID ↔ classifier/verifier restrictions | COMPATIBLE_WITH_PROFILE | Scenario ID is correlation-only and non-evidentiary; classifier/verifier semantic use is prohibited by the active profile/rules. |
| R5-COMP-015 | R4 package ↔ R5 package immutability | EXACT | R5 uses a distinct package ID; R4 historical package remains unchanged. |

There are zero `AMBIGUOUS` and zero `INCOMPATIBLE` rows. No compatibility row required a new finding.
