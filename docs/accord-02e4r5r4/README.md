# ACCORD-02E4R5R4 candidate (0.2, CANDIDATE_UNACCEPTED)

This directory contains the additive R4 normative package artifacts. The package preserves the accepted 0.1 expectations while expressing R4 governance through typed, closed declarative data.

## Authority and verifier inputs

A verifier receives the expected package identity, the external acceptance profile, the verifier-owned profile-schema bytes, and the caller-supplied expected SHA-256 digest of those exact raw schema bytes independently from the candidate payload. The expected schema identity arrives through --acceptance-profile-schema-id; the schema bytes arrive through --acceptance-profile-schema; the expected digest arrives through --acceptance-profile-schema-sha256; the profile JSON arrives through --verification-input. The verifier checks the caller-supplied raw SHA-256 before parsing or using the schema, then checks its fixed schema identity and Draft 2020-12 dialect before validating the profile. The candidate registry and candidate schemas cannot select, override, or replace this schema and provide no fallback.

The file sources/external-acceptance-profile.schema.json is an unregistered transport copy only. It is never loaded automatically and is not authority. A caller may supply its exact bytes together with an independently supplied expected digest. Other files under sources/ are export transport copies and are not authority; a verifier must compare them to the separately supplied pins and must not fall back to candidate copies, package fields, or generator constants.

## Layout

| Path | Role |
| --- | --- |
| Top-level JSON files | Normative package artifacts |
| schema/ | Draft 2020-12 schemas for registered package artifacts |
| sources/ | Byte-for-byte transport copies; no source copy is registered as authority |
| audit/build_r5r4_artifacts.py | Deterministic artifact generator |

## Generation

Run python docs/accord-02e4r5r4/audit/build_r5r4_artifacts.py from the repository root to regenerate the declarative artifacts. This command generates files only; it does not evaluate or certify a candidate.

The primary generic reference evaluator is included at audit/evaluate_r5r4.py. It requires explicit caller inputs for the package trust triple, external acceptance-profile bytes, verifier-owned profile-schema bytes and identity, and the externally expected raw schema SHA-256. The bundled --self-test exercises a non-normative local profile fixture and focused binding/derivation mutations; its local source copies are not authority.

No independent evaluator, negative-case falsifier, or release verifier is included in this slice. The evaluator is a primary implementation only; its output is not an acceptance result, and the package remains CANDIDATE_UNACCEPTED.
