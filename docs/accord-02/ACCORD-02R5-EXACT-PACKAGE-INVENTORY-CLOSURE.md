# ACCORD-02R5 — Exact Package Inventory Closure

Status: bounded remediation only. ACCORD-02 remains unaccepted, unpromoted, unmerged, untagged, and unpushed.

## Scope

R5 addresses only the four open findings recorded by the independent ACCORD-02E-R4 review:

| Finding | Severity | R4 defect | R5 disposition |
| --- | --- | --- | --- |
| E2E-R4-BLOCK-001 | BLOCKING | The exact package omitted required experiment, verifier, and trust-root profile contracts; active arm profile references were not all version pinned. | CLOSED by the R5 exact package inventory, three required profile contracts, and exact profile versions. |
| E2E-R4-BLOCK-002 | BLOCKING | Ten active source-schema ID/version pairs in the source registry were absent from the closed package inventory. | CLOSED by packaging all 13 active source-schema pairs. |
| E2E-R4-MAJOR-001 | MAJOR | Digest applicability named generic bundle forms and scorer entries lacked sufficient concrete schema identity. | CLOSED by concrete schema/version/record-type mappings and scorer-entry structural identity. |
| E2E-R4-MAJOR-002 | MAJOR | Source-schema registry roles were unrestricted strings although the role-visibility profile used a closed vocabulary. | CLOSED by applying the single nine-value role vocabulary to source-registry roles. |

No authority, settlement, oracle, normalization, experiment-hypothesis, metric, baseline, transport, or runtime model was added or redesigned.

## Immutable package boundary

The R4 package remains historical and unchanged:

`urn:moirae:accord-02r4:specification-package / 0.1`

R5 introduces the current candidate package:

`urn:moirae:accord-02r5:specification-package / 0.1`

The package is `CLOSED_EXACT_VERSION`. A bundle binds the exact package ID, package version, and package schema ID/version. A validator may resolve contracts only from that package inventory; it may not use latest, compatible, default, repository-local, filesystem, network, cache, or private-runtime fallback.

The R5 package contains 44 schema contracts, 31 profile contracts, one canonicalization profile reference, one closed role vocabulary, and the R5 validation-rule overlay. The R3 validation registry remains the explicit base of the R5 overlay; the R5 overlay is authoritative for the current package and preserves the historical BND-004, BND-005, and DIGEST-001 rule IDs with package-specific inputs and failure codes.

## Profile closure

Every active typed profile reference is resolved by `(profile_type, profile_id, profile_version)` exactly once. The package includes the existing authority, settlement, projection, extension, source-schema, role-visibility, normalization, classifier-feature, predicate-applicability, arm-input, and base validation profiles, plus the required R5 package members:

- `EXPERIMENT_PROFILE` → `urn:moirae:accord-02d:experiment-profile / 0.2` → `schema/accord-02d-experiment-profile.schema.json`.
- `VERIFIER_PROFILE` → `urn:moirae:accord-02r5:verifier:default:0.1 / 0.1` → `schema/accord-02r5-verifier-profile.schema.json`.
- `TRUST_ROOT_PROFILE` → `urn:moirae:accord-02a:trust-root:fixture-v1 / 0.1` → `schema/accord-02r5-trust-root-profile.schema.json`.
- Current validation overlay → `urn:moirae:accord-02r5:validation-rules:0.1 / 0.1` → `accord-02r5-validation-rules.json`.
- Current canonicalization profile → `urn:moirae:accord-02r5:canonicalization:rfc8785-jcs:0.1 / 0.1` → `examples/accord-02r5-canonicalization-profile.json`.

The arm-input catalog now carries `profile_version` on its top-level and per-arm source-schema, role-visibility, validation-rule, and ARM-C classifier-feature references. No active arm profile reference is versionless or duplicated.

## Source-schema closure

The source registry has 13 active schema ID/version pairs. The ten pairs missing from R4 are now package members, all using the closed R5 typed source-record contract where appropriate:

`task-state`, `attempt`, `executor-state`, `admission-state`, `delegate-report`, `provider-state-read`, `reconciliation-result`, `classifier-feature`, `trust-root-profile`, and `detached-evidence`.

The three previously covered forms remain covered: portable record bundle, authority profile, and settlement profile. Registry-to-package coverage is 13/13; reverse package-to-registry coverage is intentionally not required because the package also contains non-arm schemas and profiles.

`schema/accord-02r3-source-schema-registry.schema.json` now constrains every `roles` entry to the same authoritative nine-value vocabulary used by the package and role-visibility profile. Filename or path similarity cannot establish source membership.

## Concrete digest applicability

The R5 canonicalization profile fixes the existing method without changing it: RFC 8785 JCS, UTF-8, SHA-256, canonicalized `content` only. It maps concrete schema ID, schema version, container type, and record type rather than generic bundle labels. The profile has 49 mappings:

- 11 verifier-record-entry mappings;
- 33 experiment-record-entry mappings;
- 5 scorer-entry mappings.

Scorer entries now carry the R5 scorer-entry schema ID/version. When a digest is supplied, the exact schema contract, concrete record form, canonicalization profile, content target, encoding, method, and algorithm are all resolvable. A missing/unsupported mapping or digest mismatch is a validation failure only; it does not imply no effect, invalid authority, or delegate dishonesty.

## Validation consequences

- `BND-004` is `DETERMINISTIC_WITH_PROFILE`: schema-contract resolution uses the supplied instance scope plus the exact R5 package inventory and the record's declared type/schema ID/version.
- `BND-005` is `DETERMINISTIC_WITH_PROFILE`: profile resolution uses exact type/ID/version against the R5 package inventory, with no latest/default substitution.
- `DIGEST-001` is `DETERMINISTIC_WITH_PROFILE`: supplied digests use the resolved concrete schema contract and R5 canonicalization mapping; optional absent digests follow the active record policy.
- Unknown schema, profile, role, or canonicalization contract values are rejected or unavailable; they are never admitted by ambient lookup.

Scenario IDs retain their prior correlation-only, non-authoritative, non-evidentiary treatment. R5 does not claim that arbitrary identifier strings are cryptographically non-correlated with outcomes; it preserves the existing design requirement that scenario IDs cannot be classifier features or verifier evidence.

## Static closure checks

The bounded R5 checks performed on the candidate report:

- all JSON documents parse;
- all 44 package schema paths and 31 profile paths resolve;
- schema ID/version pairs and profile type/ID/version pairs are unique;
- all 13 source-registry schema pairs resolve in the R5 package;
- all source-registry roles are in the single nine-value vocabulary;
- all 49 canonicalization mappings are concrete and covered by package digest-bearing contracts;
- all current arm profile references carry exact versions;
- current active bundle/run schemas are pinned to the R5 package;
- R5 validation rules preserve 82 active rules, three explicit overrides, and an acyclic 13-edge overlay dependency graph;
- no public scorer locator or scorer material was added to arm/verifier inputs;
- no runtime, validator, verifier, harness, experiment, training, dependency, provider, or external-repository change was made.

These are specification-level static checks. No standards-complete JSON Schema engine, independent validator implementation, or experiment execution was added or run here.

## Historical traceability

R5 materially closes the package-inventory portions of `E2E-BLOCK-001`, `E2E-MAJOR-003`, `E2E-MAJOR-004`, and `E2E-MAJOR-005`, and the R4 descendants listed above. The historical reviews and all previous remediation evidence remain unchanged. A fresh post-R5 acceptance-readiness review is required; this remediation does not declare ACCORD-02 accepted.
