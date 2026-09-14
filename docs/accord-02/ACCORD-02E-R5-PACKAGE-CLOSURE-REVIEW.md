# ACCORD-02E-R5 — Package Closure Review

## Scope

This focused review independently checked the active R5 package against the four R4 acceptance-critical findings. The source package is [accord-02r5-specification-package.json](accord-02r5-specification-package.json), its structural contract is [schema/accord-02r5-specification-package.schema.json](schema/accord-02r5-specification-package.schema.json), and the package's own coverage audit is [accord-02r5-package-coverage-audit.json](accord-02r5-package-coverage-audit.json).

## Exact package

| Property | Result |
| --- | --- |
| Package ID | `urn:moirae:accord-02r5:specification-package` |
| Version | `0.1` |
| Policy | `CLOSED_EXACT_VERSION` |
| Schema contracts | 44 |
| Profile contracts | 31 |
| Canonicalization profiles | 1 |
| Role vocabulary | 9 |
| Active rules | 82 |
| Active source-schema pairs | 13 |
| Active arm profile references | 16 |
| Canonicalization mappings | 49 entries / 70 expanded concrete container-schema-record combinations |

The R4 package remains present historically and is not treated as the active package. The R5 package is distinct, so no immutable package ID/version is claimed by two different package contents.

## Profile resolution

All 31 package profile keys `(profile_type, profile_id, profile_version)` were unique and their declared paths existed. The active profile classes were checked for exact version binding:

- validation-rule profiles: R3 base and R5 overlay;
- experiment profile contract;
- verifier profile contract;
- trust-root profile contract;
- authority profiles: 9;
- settlement profiles: 2;
- projection profile;
- extension registry;
- source-schema registry;
- role-visibility profile;
- normalization profiles: A, B, C, and D;
- classifier-feature profile;
- predicate-applicability profile;
- arm-input profiles: A, B, C, and D;
- canonicalization profile.

The 16 active arm-profile references all contained profile IDs, exact profile versions, schema IDs, and schema versions. The package has zero missing, versionless, or duplicate active references in the current arm catalog. A wrong profile type or version cannot be silently substituted: resolution is exact and field-context constrained.

## Source schema package coverage

The source registry contains 13 active pairs. Independently comparing `(schema_id, schema_version)` against the R5 schema-contract inventory produced:

| Check | Result |
| --- | ---: |
| Registry entries | 13 |
| Unique active pairs | 13 |
| Package-covered pairs | 13 |
| Missing pairs | 0 |
| Invalid role values | 0 |

The ten source forms added by R5 use the typed R5 source-record contract; the three previously covered forms remain covered. Reverse package-to-registry bijection is not required and is not inferred.

## Role vocabulary

The single authoritative vocabulary is:

```text
ORCHESTRATOR
DELEGATE_FIXTURE
PROVIDER_FIXTURE
OBSERVER_FIXTURE
ARM-A-DURABLE
ARM-B-PROVIDER-OBSERVATION
ARM-C-LIGHTWEIGHT-CLASSIFIER
ARM-D-ACCORD-EVIDENCE
SCORER
```

The source registry's `roles` values were compared against this exact set. There were no unknown values. `MAGIC_ADMIN`, spelling variants, and undeclared future roles have no valid current-package path.

## Canonicalization applicability

The active profile [examples/accord-02r5-canonicalization-profile.json](examples/accord-02r5-canonicalization-profile.json) specifies RFC 8785 JCS, UTF-8, and SHA-256 with `content` as the covered target. It contains 49 entries:

- 11 verifier-record-entry entries;
- 33 experiment-record-entry entries;
- 5 scorer-entry entries.

The entries expand to 70 concrete container/schema/version/record-type combinations. Every mapping schema pair exists in the R5 package and no duplicate concrete key has conflicting content target or profile. Scorer entries carry schema ID/version, so scorer-side digest applicability is no longer inferred from a generic scorer label.

Digest behavior is limited correctly: a supplied digest with no applicable mapping fails or is unverifiable; a wrong digest fails validation; an absent optional digest permits ordinary typed resolution. None of these failures imply no external effect, invalid authority, or delegate dishonesty.

## BND-004, BND-005, and DIGEST-001

`BND-004` is independently classified `DETERMINISTIC_WITH_PROFILE`: the record's type/schema ID/version is resolved against the exact R5 package contract inventory, and structural validation is then performed against the resolved contract. Missing, duplicate, wrong-type, unsupported-version, or structurally invalid targets have distinct failure paths.

`BND-005` is independently classified `DETERMINISTIC_WITH_PROFILE`: every active profile reference is resolved against the exact R5 profile inventory using its field-declared profile role, profile ID, and exact profile version. Latest/default/compatible substitution is prohibited.

`DIGEST-001` is independently classified `DETERMINISTIC_WITH_PROFILE`: a supplied digest is evaluated only after the typed record, schema contract, concrete canonicalization mapping, algorithm, and content target resolve. The active R5 package supplies all of these inputs for the current concrete forms.

## Scope boundary

The exact package is a closed contract inventory, not an ambient repository. Its relative paths are package members. A local file that is not in the package does not participate in resolution merely because it exists. An implementation that falls back to such a file is non-conformant under the R5 contract.
