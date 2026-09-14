# ACCORD-02E-R4 — Contract Closure Review

This document records the focused review of the R4 self-contained package, schema, profile, role, and canonicalization contracts. It is review evidence, not a remediation.

## Scope model

R4 chooses **Model B: a closed versioned specification package**. The instance bundle is intended to carry run-specific records; the exact `accord-02r4` package is intended to supply immutable schemas, profiles, registries, rule definitions, role vocabulary, and canonicalization contracts. The package uses `CLOSED_EXACT_VERSION`, so “latest”, “compatible”, repository discovery, and local fallback are not permitted.

That model is the right bounded architecture, but the current package is not complete enough to support the whole declared stack.

## Package inventory

Static inspection found:

- package ID `urn:moirae:accord-02r4:specification-package`;
- package version `0.1`;
- 30 schema contracts;
- 28 profile contracts;
- one canonicalization profile;
- nine declared roles;
- unique schema and profile ID/version pairs;
- package paths that exist in the repository.

The following acceptance-critical gaps remain:

1. active experiment and verifier run paths require profile types that are not represented as package profile contracts (`EXPERIMENT_PROFILE`, `VERIFIER_PROFILE`, and the required trust-root profile path);
2. several active arm profile references omit the exact `profile_version` required by `PROF-002`;
3. the active source-schema registry declares ten schema ID/version pairs absent from the package schema-contract inventory;
4. canonicalization applicability uses generic bundle-entry record types that do not match all concrete digest-bearing entries.

The package is therefore finite but not closed for the current use graph.

## Profile resolution

The intended resolver is exact over `(profile_type, profile_id, version, specification_scope)`, with outcomes `RESOLVED`, `MISSING`, `DUPLICATE`, `WRONG_PROFILE_TYPE`, `UNSUPPORTED_VERSION`, and `STRUCTURALLY_INVALID`. No default/latest substitution is allowed.

The resolver is deterministic when the package contains the referenced contract. It cannot produce a valid complete scope for the current experiment/verifier run schemas because required profile categories are missing from the package and some active references have no version. This is the basis of `E2E-R4-BLOCK-001`.

## Schema-contract resolution

The intended structural pipeline is:

1. resolve the normative record type and schema ID/version in the package;
2. reject an unknown or unsupported schema contract;
3. validate the record content against the resolved schema;
4. only then allow profile, lineage, proposition, or digest rules to consume the record.

This prevents a self-declared `schema_id` from becoming authority by assertion and prevents generic bundle `content` from becoming a normative record without a contract.

The pipeline remains incomplete because the active source-schema registry is not fully represented in the package. A source file existing elsewhere in the repository cannot be used under exact package semantics. This is `E2E-R4-BLOCK-002`.

## Role closure

The main role-visibility profile is closed to the nine declared roles and rejects unknown producers/consumers. That closes the direct `MAGIC_ADMIN` attack against that profile.

The source-schema registry is a separate role-bearing artifact whose `roles` values are arbitrary strings. Because source membership does not require package-role resolution, the same unknown role can still enter a source membership path. This is `E2E-R4-MAJOR-002`; it is not enough that one profile uses an enum if another active role-bearing registry does not.

## Canonicalization

The declared canonicalization method is RFC 8785 JSON Canonicalization Scheme, UTF-8, SHA-256, version `0.1`. This is sufficient in principle for independent implementations when the exact record form and covered content are identified.

The current applicability mapping is not sufficient in practice. The profile identifies generic `BUNDLE_RECORD_CONTENT`/`SCORER_RECORD_CONTENT`, while verifier and experiment bundle entries use concrete record types. Scorer entries do not carry schema ID/version fields that would let the verifier or scorer determine the applicable contract. Thus a supplied digest can be present without a deterministic match to the canonicalization profile for the actual record. This is `E2E-R4-MAJOR-001`.

No package-integrity bootstrap cycle was found. The package does not require validating its own digest before its contracts can be loaded.

## BND-004 and BND-005

### BND-004

Independent classification: `DETERMINISTIC_WITH_PROFILE` as a rule algorithm, but not closed for the current package. Inputs are the bundle scope, package schema-contract registry, source-schema registry, record type/ID, and structural validation facts. The missing source contract inventory prevents a complete valid result.

### BND-005

Independent classification: `DETERMINISTIC_WITH_PROFILE` as a rule algorithm, but not closed for the current package. Inputs are the bundle scope, exact package profile inventory, typed profile reference, and profile structure. Missing profile categories and missing active versions prevent a complete valid result.

Neither rule is syntactically ambiguous; both remain acceptance-blocked by unavailable required package members.

## Scenario identifiers

The R4 scenario-ID policy is correctly bounded:

- correlation, join, and audit only;
- non-authoritative and non-evidentiary;
- forbidden as baseline, classifier, or verifier semantic evidence;
- generated without encoding expected outcome classifications where controlled tooling is used;
- no claim that identifier syntax proves cryptographic non-correlation.

This is a sound experimental design constraint and is not itself a package-closure defect.

## External verification conclusion

The intended statement—instance bundle plus exact package, without private Accord state—is **not supported for the current R4 stack**. The package model is suitable, but the actual active package inventory must first be made complete and canonicalization applicability must be made concrete.

## Review conclusion

The R4 architecture is directionally correct and bounded. It has not yet reached specification freeze because “closed exact package” currently describes the policy more completely than it describes the active contract inventory.
