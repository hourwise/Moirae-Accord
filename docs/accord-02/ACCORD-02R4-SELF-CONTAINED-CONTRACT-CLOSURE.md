# ACCORD-02R4 — Self-Contained Profile & Schema Contract Closure

## Remediation boundary

R4 addresses only the open ACCORD-02E-R3 blocker/major findings concerning profile resolution, schema-contract resolution, role membership, digest canonicalization, and scenario-ID side-channel language. Prior review artifacts and prior remediation evidence remain historical records and are not rewritten.

The selected closure model is a closed exact-version specification package. A validation bundle carries `specification_package_ref`; that reference identifies the only normative contract inventory permitted for the selected validation profile. Instance records are still supplied in the verifier or experiment validation bundle. Scorer expectations and oracle records remain scorer-only.

## Findings targeted

| Finding | R3 defect | R4 closure material |
| --- | --- | --- |
| `E2E-R3-BLOCK-001` | Active profile references were not resolvable members of bundle/specification scope. | Closed package profile inventory, typed profile contracts, `PROF-001`, `PROF-002`, amended `BND-005`. |
| `E2E-R3-BLOCK-002` | Generic bundle content had no in-scope structural schema-contract registry. | Closed schema-contract inventory, structural validation contract, `SCHEMA-001`, `SCHEMA-002`, amended `BND-004`. |
| `E2E-R3-MAJOR-001` | Producing/consumer role strings were not closed to the declared vocabulary. | Role enum in the role schema, package role vocabulary, `ROLE-001`. |
| `E2E-R3-MAJOR-002` | Scenario-ID opacity was self-attested rather than a bounded generation/use requirement. | Correlation-only scenario-ID policy and `SCENARIO-ID-001`; no claim of cryptographic opacity. |
| `E2E-R3-MAJOR-003` | Generic digest content lacked a fixed canonicalization contract. | R4 canonicalization schema/profile, package mapping, `DIGEST-CANON-001..003`. |

The historical partial closures affected by these changes are `E2E-BLOCK-001`, `E2E-MAJOR-003`, `E2E-MAJOR-004`, and `E2E-MAJOR-005`. The R4 package makes their previously profile-dependent scope explicit without changing their semantic claims.

## Required validation scope

The verifier scope is the supplied verifier bundle plus the exact package contract and any profiles/trust roots/evidence explicitly required by that package/profile. The experiment scope adds the scenario, run, arm manifest, source registry, visibility profile, normalization/classifier profiles, raw output, normalized claim, and experiment-side lineage records. The scorer scope adds scorer-only expectation/oracle/score records; it is never a verifier or arm scope.

The validator may not search an ambient filesystem or database for an omitted contract. Missing package members, profiles, schemas, canonicalization profiles, or required instance records fail deterministically. A valid record in another run is not a valid record for the current scope without the required run/scenario/arm/proposition bindings.

## Structural and normative enforcement

JSON Schema enforces the exact package reference, closed bundle/run envelopes, digest-profile reference when a digest is present, and closed role values. Cross-record rules enforce package membership, profile/schema resolution, uniqueness, structural target validation, role/profile membership, canonicalization applicability, and scenario-ID semantic-use restrictions. The rules and their dependencies are machine-readable in the R4 overlay and dependency graph.

## Non-goals and limitations

R4 does not write a validator, verifier, classifier, harness, provider fixture, or runtime adapter. JSON Schema files are normative contracts, but this task does not claim that an external standards validator was executed. The package closes the definition of the required contracts; it does not prove that future independent implementations interoperate, that evidence is true, or that an external effect occurred.
