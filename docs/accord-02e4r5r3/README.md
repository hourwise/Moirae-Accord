# ACCORD-02E4R5R3 candidate (0.2, CANDIDATE_UNACCEPTED)

Additive self-contained revision of the ACCORD-02 R5 specification package.
It closes the E4R5R2 governance and trust-root boundary defects recorded in
the phase-A reproduction, without reopening any accepted settlement semantics.

Two layers are reported by every evaluator:

* `INTERNAL_PACKAGE_CONFORMANCE` -- the selected package bytes satisfy their
  complete normative contracts (package invariants plus bounded governance).
* `TRUSTED_PACKAGE_IDENTITY` -- an external caller-supplied trust anchor equals
  the recomputed candidate identity.

## Layout

| Path | Role |
| --- | --- |
| `*.json` | Normative package artifacts (registered objects) |
| `schema/*.schema.json` | Closed JSON Schemas for every artifact |
| `audit/certify_e4r5r3.py` | Primary evaluator |
| `audit/independent_evaluate_e4r5r3.py` | Independent evaluator |
| `audit/falsify_e4r5r3.py` | Disposable negative-case falsifier with reason oracle |
| `audit/verify_release_e4r5r3.py` | Exact-surface release verifier and clean-export harness |
| `audit/fixtures/external-trust-root.json` | Non-normative external trust anchor fixture (never registered) |
| `_build_candidate.py` | Deterministic builder with `--check` drift detection |

## Running

```
python _build_candidate.py --check
python audit/certify_e4r5r3.py --root <root> --expected-package-id <id> \
    --expected-package-version 0.2 --expected-package-digest <sha256>
python audit/independent_evaluate_e4r5r3.py --root <root> <same trust arguments>
python audit/falsify_e4r5r3.py --root <root>
python audit/verify_release_e4r5r3.py --root <root>
```

The external trust anchor is supplied outside the object registry (CLI flags or
`--verification-input`).  It is never read from the candidate, and absence of
the anchor is reported as `FAIL / MISSING_EXTERNAL_TRUST_INPUT`, never as PASS.
