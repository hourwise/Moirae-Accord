# ACCORD-02E-R3 — Cross-Slice Compatibility

The full machine-readable matrix is [`accord-02e-r3-compatibility-matrix.json`](./accord-02e-r3-compatibility-matrix.json).

## Summary

| Status | Count |
|---|---:|
| EXACT | 5 |
| COMPATIBLE | 3 |
| COMPATIBLE_WITH_PROFILE | 11 |
| AMBIGUOUS | 4 |
| INCOMPATIBLE | 1 |
| NOT_APPLICABLE | 2 |

The incompatible row is active profile references versus the bundle inventory:
the reference is typed `PROFILE`, while concrete profile/registry records use
other record types and are not admissible as `PROFILE` inventory entries. The
ambiguous rows all have corresponding R3 finding IDs.

## Compatibility observations

- A/B authority axes remain compatible with D result records and are not
  collapsed by R3.
- C native settlement remains the source for A projections.
- Canonical proposition references are present, but the proposition profile
  and referenced record must be resolvable inside scope.
- Transport IDs and provider operation IDs remain correlation-only.
- Arm manifests are structurally discriminated by arm and profile ID.
- The scorer graph is one-way: expectation joins to the shared opaque
  `scenario_id`; public artifacts do not locate the scorer catalog.
- The cross-slice compatibility is therefore conditional on repairing the
  bundle/profile and schema-contract scope.
