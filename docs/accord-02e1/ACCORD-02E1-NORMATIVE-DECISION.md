# ACCORD-02E1 — Normative Predicate-Mapping Decision Required

Status: `NORMATIVE_AMENDMENT_REQUIRED`

This document is an amendment candidate analysis. It is not part of the
accepted ACCORD-02 package and does not modify the accepted tag.

## Finding

The accepted ACCORD-02C settlement vectors use predicate identifiers such as:

- `urn:accord:02c:predicate:external-effect`
- `urn:accord:02c:predicate:complete-negative`
- `urn:accord:02c:predicate:recipient-ack`
- `urn:accord:02c:predicate:resource-created`

The accepted R3 predicate-applicability profile declares only:

- `create_resource` at `resource_created`;
- `deliver_item` at `recipient_acknowledged`;
- `provider_acceptance` at `provider_accepted`.

The accepted package contains no predicate alias registry, predicate mapping
profile, or rule that makes these vocabularies equivalent. The R1 settlement
vocabulary map maps native C result axes to A-style result kinds; it does not
map predicate identifiers. The C specification also says that predicates are
not aliases and that the intended predicate and stage must be carried and
bound explicitly.

Consequently, the accepted artifacts do not determine a unique applicability
row for all vector targets. A same-stage or `urn:` fallback is an
implementation interpretation, not an accepted normative rule.

## V014 and V021

Both vectors target:

`urn:accord:02c:predicate:recipient-ack`

The only plausible profile-local candidate is `deliver_item`, because it
requires a recipient and names the `recipient_acknowledged` stage. That is not
an accepted mapping: the vector uses `recipient-ack`, the C vocabulary uses
`recipient_acknowledgement`, and the profile uses `deliver_item` /
`recipient_acknowledged`. No rule authorizes normalization among those names.

V014 additionally declares `provider_acceptance` followed by
`recipient_acknowledgement` and expects a partial staged result. The accepted
records therefore identify a meaningful staged intent, but not a
machine-resolvable profile row. V021 has the same unresolved target predicate
and adds recipient mismatch evidence. Its expected partial result must not be
changed; the missing predicate mapping must be resolved first.

## Complete-negative predicate

`urn:accord:02c:predicate:complete-negative` is used as the target of V013,
which supplies a complete-negative query and expects scoped
`NON_OCCURRENCE_SUPPORTED`. The C model treats complete negative evidence as a
profile-bounded negative-evidence condition with scope, interval, retention,
freshness, and read-semantics requirements. It is not one of the three
positive applicability rows. An amendment must either give it an explicit
negative predicate/applicability entry or define a separate typed negative
query contract and its binding to the target proposition.

## External-effect predicate

`urn:accord:02c:predicate:external-effect` is used by 18 vectors with
different evidence situations: dispatch only, transport acknowledgement,
strong occurrence, stale evidence, retry ambiguity, invalid authority,
incompatible profiles, clock ambiguity, extension uncertainty, and reopening.
The accepted material does not provide a generic applicability row or a
stage-specific identity for this URI. Mapping it to one of the three existing
rows would either be under-specified or would silently collapse distinct
stages and binding requirements.

## Candidate amendment shapes

These are options for a future normative decision, not facts already present in
ACCORD-02.

### Option A — exact predicate registry / alias map

Add a closed, versioned registry containing exact source predicate IDs,
profile-local IDs, stage, binding requirements, and negative-evidence policy.
The registry could explicitly decide whether the plausible pairs are:

| Source identifier | Possible target | Current status |
| --- | --- | --- |
| `urn:accord:02c:predicate:resource-created` | `create_resource` | plausible only; not accepted |
| `urn:accord:02c:predicate:recipient-ack` | `deliver_item` | plausible only; not accepted |
| `urn:accord:02c:predicate:provider-acceptance` | `provider_acceptance` | plausible only; not accepted |

It would still need an explicit decision for `external-effect` and
`complete-negative`. A generic prefix/suffix rule would not satisfy the
contract.

### Option B — extend the applicability profile with exact URN rows

Add versioned rows for each accepted URN predicate, including exact stage and
bindings. This avoids aliases but requires a normative decision for the
generic `external-effect` uses and for the negative predicate.

### Option C — revise the vectors to use profile-local identifiers

Replace vector target identifiers with the existing profile-local vocabulary
and define a separate typed negative-query target for V013. This would alter
accepted fixture bytes and expected package content, so it is not an editorial
change to the sealed package.

## Recommended bounded shape

No semantic mapping option is recommended as an existing normative fact. The
next decision should use a small exact registry or exact profile extension,
with no lexical normalization and with explicit treatment of
`external-effect`, `recipient-ack`, `resource-created`,
`provider-acceptance`, and `complete-negative`. The authors must choose the
semantic target before ACCORD-03R3 changes the implementation.

## Versioning

The accepted `accord-02-accepted-v1` tag and its package
`urn:moirae:accord-02r5:specification-package` version `0.1` must remain
immutable. If the semantic mapping is amended, the cleanest bounded approach
is a new exact package version (for example, the same package ID at version
`0.2`, subject to the repository's package-version policy) and a separate
amendment acceptance decision. No new tag is created by ACCORD-02E1.

## Scope boundary

This analysis does not modify ACCORD-02, the R2 implementation branch, or any
ACCORD-03 implementation. The external Claude and DeepSeek implementation
findings remain deferred to the later ACCORD-03R3 remediation as listed in
`accord-02e1-implementation-impact.json`.
