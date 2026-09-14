# ACCORD-02R3 — Validation Closure & Profile Registry Remediation

ACCORD-02R3 materializes the finite validation scope, profile registries, and
dependency facts that ACCORD-02R2 had named but not supplied. It is a bounded
remediation, not a new research model and not an executable validator.

## Closure rule

Every acceptance-critical statement is now evaluated by one of three declared
mechanisms:

1. JSON Schema structural admission;
2. a supplied, versioned registry/profile;
3. a deterministic cross-record rule evaluated over the supplied validation
   scope.

There is no ambient repository, database, network, cache, provider session, or
private Accord store in the initial self-contained profile. The active R3 rule
overlay is [`accord-02r3-validation-rules.json`](./accord-02r3-validation-rules.json);
the R2 rules remain preserved and traceable through its `base_registry` and
`base_rule_closures`.

## Explicit bundles and scopes

- [`accord-02r3-verifier-validation-bundle.schema.json`](./schema/accord-02r3-verifier-validation-bundle.schema.json)
  supplies the portable records, canonical proposition, evidence, results,
  profiles, and trust material needed for one verifier conclusion.
- [`accord-02r3-experiment-validation-bundle.schema.json`](./schema/accord-02r3-experiment-validation-bundle.schema.json)
  adds scenario/run/arm/normalization lineage without scorer truth.
- [`accord-02r3-scorer-bundle.schema.json`](./schema/accord-02r3-scorer-bundle.schema.json)
  is explicitly `SCORER_ONLY` and cannot be an arm or verifier input.

Resolution is `RESOLVED`, `MISSING`, `DUPLICATE`, `WRONG_TYPE`, or
`STRUCTURALLY_INVALID`. A digest, when supplied, is checked after typed
resolution. No implementation may silently select a first match.

## Registries

The supplied catalogs define:

- extension classification and the non-strengthening behavior of unknown
  extensions;
- source-type to record-type/schema membership for all four arms;
- orchestrator, fixture, provider, observer, arm, and scorer visibility;
- deterministic arm-output normalization;
- the closed ARM-C classifier feature set;
- predicate/stage binding applicability.

Their schemas are closed. Registry IDs and versions are part of the active
bundle profile references, so a future implementation does not infer them from
filenames or local configuration.

## Required separation

The public scenario catalog remains orchestration material. It may describe the
condition being enacted, but a sanitized arm manifest contains only typed source
references authorized by the selected arm and role-visibility profile. Scorer
expectations join to `scenario_id` only on the scorer side. The public catalog
does not locate the scorer catalog.

The scoring sequence remains:

```text
raw arm output -> frozen normalization profile -> normalized claim
               -> compare with scorer truth -> score
```

Normalization cannot consult oracle truth. A raw claim remains untrusted output
and is never forwarded automatically as another arm's input.

## Proposition and digest limits

The R2 canonical proposition remains the single semantic descriptor for the
settlement proposition. The predicate applicability profile determines whether a
binding is `REQUIRED`, `OPTIONAL`, or `NOT_APPLICABLE`; `UNKNOWN` cannot satisfy a
positive projection. A proposition ID resolves to one descriptor in the supplied
scope. A digest mismatch fails reference validation and does not imply anything
about external occurrence.

## Non-goals

This remediation does not execute validation, prove source trust, establish
external ground truth, add runtime ownership, alter Ananke/Horae/Adrasteia, or
authorize an experiment harness. A fresh post-R3 integrated closure review is
required before any ACCORD-02 acceptance decision.
