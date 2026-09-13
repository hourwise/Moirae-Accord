# ACCORD-00 Acceptance

## Scope

ACCORD-00 was a static, read-only ecosystem audit of exactly eight named Moirae/Fates repositories. The audit used isolated source snapshots created before substantive analysis:

`D:\Users\fleur\Moirae Accord - Source Snapshots\ACCORD-00-20260913-215700`

The audit did not:

- implement Moirae Accord runtime code;
- modify any source repository, source branch, tag, commit, release, worktree, or remote;
- modify any hackathon or accepted Fates reference;
- perform cloud, provider, model, or other external API calls;
- run Firecracker or any other sandbox executor;
- install dependencies or run npm installation commands;
- perform external side effects.

The only Accord-side material created before this acceptance record was the ACCORD-00 research/evidence set. The source snapshots were rechecked during sealing and remained clean, with their original fetch URLs and disabled copy-only push URLs intact.

## Accepted findings

1. Accord should extend existing Fates rather than create private copies of Fates behavior.

2. The recommended reusable baselines are:

   - Adrasteia: `a1c01bf9e6f9d6a126cfdcc1acfacd488b214210`, ref `release/webmcp-runtime-v0.6.2`.
   - Ananke: `b888d61adf180d33e2ae2e61d276cb9b0f13bd12`, accepted FATES-008 terminal lineage.
   - Horae: `aa296b420fbcf578089ca66dc03f6d09d9b06f00`, accepted FATES-007A terminal lineage.

3. Accord v0.1 defers:

   - Mnemosyne runtime integration;
   - Console UI integration;
   - Firecracker/microVM execution;
   - multi-host consensus;
   - distributed exactly-once claims;
   - production external-provider effects.

4. The core research invariants remain:

   - `CHILD_AUTHORITY <= PARENT_AUTHORITY`
   - `REMOTE_COMPLETED != VERIFIED_SUCCESS`
   - `UNKNOWN != SUCCESS`
   - `UNKNOWN != FAILURE`
   - `NO_VALID_AUTHORITY -> NO_EFFECT`
   - `NO_ACCEPTABLE_EFFECT_EVIDENCE -> NO_VERIFIED_SUCCESS`

5. Project-Fates-Integration remains outside the runtime path and retains an evidence/conformance role only.

6. Existing hackathon consumers and accepted Fates consumers remain pinned. No consumer is silently upgraded by this acceptance.

## V0.1 narrowing

The initial Accord implementation boundary is intentionally narrow:

- one parent;
- one child;
- maximum delegation depth 1;
- maximum children 1;
- model future multi-hop fields where appropriate, but do not implement arbitrary recursion yet;
- defer provider-specific token and cost budgets;
- support deterministic capability, resource, deadline, and approval attenuation.

This is an Accord v0.1 boundary decision. It is not a claim that the underlying Fates already implement all of these child-delegation semantics.

## Accepted open questions

The following remain unresolved and are preserved for later human-approved work:

- exact canonical child-authority subset semantics;
- exact delegation-chain digest;
- parent/child revocation semantics;
- remote task lifecycle mapping;
- independent remote effect receipt authority;
- provider idempotency semantics;
- exact A2A version and SDK pin;
- eventual arbitrary multi-hop semantics.

## Corrections made during sealing

NONE

## No-mutation attestation

```text
SOURCE_REPOSITORIES_MUTATED: NO
SOURCE_BRANCHES_CREATED: NO
SOURCE_TAGS_CREATED: NO
SOURCE_COMMITS_CREATED: NO
SOURCE_PUSHES_PERFORMED: NO
SOURCE_SNAPSHOTS_MUTATED: NO
HACKATHON_REFS_CHANGED: NO
ACCORD_RUNTIME_CODE_WRITTEN: NO
```
