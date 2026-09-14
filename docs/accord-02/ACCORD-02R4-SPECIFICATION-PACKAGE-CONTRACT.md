# ACCORD-02R4 Specification Package Contract

## Status and scope

This document is a bounded remediation of the open ACCORD-02E-R3 findings. It does not add a research hypothesis, authority model, settlement taxonomy, experiment arm, transport, or runtime implementation. ACCORD-02 remains an unaccepted candidate.

R4 selects Model B: a closed, exact-version ACCORD-02 specification package. Run-specific records remain instance material supplied in a validation bundle. Normative schemas, profiles, registries, role vocabulary, canonicalization contracts, and validation rules are specification contracts resolved only from the exact package identified by the bundle.

The package is identified by:

- package ID: `urn:moirae:accord-02r4:specification-package`
- package version: `0.1`
- contract policy: `CLOSED_EXACT_VERSION`

There is no ambient “latest” or “compatible” lookup. A validator may use only the package manifest and the paths/contracts listed by it. The package manifest is not an implementation dependency bundle and does not authorize filesystem, network, database, cache, or private Accord lookup.

## Scope classes

Instance records include propositions, attempts, observations, evidence, authority analysis, settlement results, verifier runs/results, experiment runs, raw outputs, and normalized claims. They must be present in the selected validation bundle when required by the active profile.

Specification contracts include schema contracts, profile contracts, the role vocabulary, canonicalization profiles, and the base-plus-overlay validation-rule contract. They are closed by `accord-02r4-specification-package.json` and selected by its exact package reference.

The three bundle classes remain distinct:

- verifier bundles contain instance records and the package reference, but no scorer material;
- experiment bundles add run, arm, normalization, and lineage records, but no scorer material;
- scorer bundles add expectations, oracle records, and score material and are never verifier or arm inputs.

## Resolution contract

Resolution is scoped to the supplied instance bundle plus the exact package contract:

```text
resolve(type, id, validation_scope)
resolve_profile(profile_type, profile_id, version, specification_scope)
resolve_schema(schema_id, schema_version, specification_scope)
```

Each returns exactly one declared result: `RESOLVED`, `MISSING`, `DUPLICATE`, `WRONG_TYPE`/`WRONG_PROFILE_TYPE`, `UNSUPPORTED_VERSION`, or `STRUCTURALLY_INVALID` as applicable. No first-match selection or default substitution is permitted. A self-declared schema ID is not sufficient: it must resolve to a package schema contract, and the content must validate against that contract before it can produce `STRUCTURE_VALID`.

The package maps profile IDs to a profile type, exact profile version, schema contract, path, and—where a catalog contains several selected profiles—a deterministic selector. The R3 validation profile remains the base registry; the R4 overlay is explicit and preserves traceability for `BND-004` and `BND-005`.

## Roles and scenario IDs

The role vocabulary is closed to the nine values in the package manifest. Producing and consumer roles in the role-visibility profile must be members of that vocabulary. Unknown roles do not default to public, private, or visible.

Scenario IDs are correlation identifiers only. They may be used for correlation, joins, and audit. They are not authoritative or evidentiary and may not be used by a baseline decision, classifier feature derivation, or Accord verifier decision as a semantic predictor. Controlled experiment tooling must generate them without encoding expected outcomes. This is a generation/use requirement, not a cryptographic proof that an arbitrary identifier is semantically opaque.

## Digest canonicalization

The R4 canonicalization profile is `urn:moirae:accord-02r4:canonicalization:rfc8785-jcs:0.1`. It binds SHA-256 over UTF-8 RFC 8785 JSON Canonicalization Scheme output for the declared `content` member of digest-bearing generic bundle entries. The profile is resolvable from the package and admits the bundle-entry schema forms listed there.

If a digest is supplied, its canonicalization profile is required and must resolve, admit the record schema/type, and use a supported algorithm/method. If no profile exists, digest verification is unavailable and cannot silently fall back to ID-only acceptance. Digest failure is a validation failure only; it does not imply effect non-occurrence, authority invalidity, or any other external fact.

## Rule closure

`accord-02r4-validation-rules.json` is an explicit overlay over the R3 rule registry. It overrides `BND-004` and `BND-005` from unevaluable to deterministic-with-profile and adds package, profile, schema, role, canonicalization, and scenario-ID rules. The R4 dependency graph adds those nodes and dependencies to the R3 graph. Acceptance-critical classification targets are zero ambiguous, zero unevaluable, and zero contradictory rules after the package is resolved.

This contract establishes deterministic specification semantics. It does not demonstrate implementation interoperability, establish external truth, or authorize an experiment harness.
