# ACCORD-02E-R4 — Cross-Slice Compatibility

This matrix is rebuilt for R4 rather than inherited from earlier reviews. Machine-readable rows are in [`accord-02e-r4-compatibility-matrix.json`](accord-02e-r4-compatibility-matrix.json).

## Status counts

| Status | Count |
|---|---:|
| EXACT | 7 |
| COMPATIBLE | 0 |
| COMPATIBLE_WITH_PROFILE | 7 |
| AMBIGUOUS | 1 |
| INCOMPATIBLE | 5 |
| NOT_APPLICABLE | 0 |

## Material compatibility findings

| Area | Result | Reason |
|---|---|---|
| Package ↔ schemas | INCOMPATIBLE | Active source schema IDs are absent from the package schema-contract inventory. |
| Package ↔ profiles | INCOMPATIBLE | Required run/profile categories are not all package members; some active references lack versions. |
| Bundles ↔ package | INCOMPATIBLE | A complete experiment/verifier scope cannot resolve every declared active contract from the exact package. |
| Records ↔ schema contracts | COMPATIBLE_WITH_PROFILE | The structural pipeline is clear where a package contract exists. |
| Profile refs ↔ contracts | INCOMPATIBLE | Exact resolution fails for missing/unversioned active refs. |
| Roles ↔ visibility | AMBIGUOUS | Primary visibility roles are closed, but source-registry role-bearing fields are open strings. |
| Digest refs ↔ canonicalization | INCOMPATIBLE | Canonicalization applicability keys do not match every concrete digest-bearing record form. |
| Rules ↔ package | COMPATIBLE_WITH_PROFILE | The 82-rule set is explicit and acyclic, but several required inputs are absent from package scope. |
| Scenario ID ↔ classifier/verifier | EXACT | Correlation-only and forbidden semantic use are explicit. |
| External verifier ↔ supplied scope | INCOMPATIBLE | Current package gaps require a contract outside the declared exact scope for some paths. |

## Cross-slice conclusions

The A/B/C semantic separation remains compatible: authority relation, effective authority, and temporal validity remain separate; native C settlement remains authoritative over A projections; canonical proposition and typed lineage remain the binding path.

The remaining incompatibilities are contract-materialization defects in the A/D/package boundary, not a need to alter the research questions or authority/effect model. The ambiguous role row is an acceptance-critical defect because it permits two profile paths to disagree about the role vocabulary.

## Matrix policy

Every `AMBIGUOUS` or `INCOMPATIBLE` row is linked to a finding in the JSON matrix. `COMPATIBLE_WITH_PROFILE` is used only where the active profile is named and the remaining qualification is intentional; it is not used to conceal a missing required package member.
