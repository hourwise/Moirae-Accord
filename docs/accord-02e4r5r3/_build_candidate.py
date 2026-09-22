#!/usr/bin/env python3
"""Deterministic builder for the ACCORD-02E4R5R3 specification package.

The builder materialises every committed normative artifact under
``docs/accord-02e4r5r3`` from the embedded specification and the accepted
source revision, then reports drift in ``--check`` mode.  It never reads a
rejected sibling tree: the inherited rule inventory, dependency graph and
accepted-vector expectations are embedded or read from the accepted
``docs/accord-02`` sources.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import rfc8785

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SCHEMA_DIR = OUT / "schema"
AUDIT_DIR = OUT / "audit"
FIXTURE_DIR = AUDIT_DIR / "fixtures"
REL = "docs/accord-02e4r5r3"
ACCEPTED = ROOT / "docs/accord-02"

VERSION = "0.2"
DIALECT = "https://json-schema.org/draft/2020-12/schema"
NS = "urn:moirae:accord-02r5r3"
PKG_ID = "urn:moirae:accord-02r5:specification-package"
CATALOG_ID = "urn:moirae:accord-02r5:source-vector-catalog"

SOURCE_REVISION = {
    "revision": "E4R5R2",
    "commit": "44d0e7240c97dcc12463b5611a7adf61399924d7",
    "tree": "19dc9356784d08d04945f8e2ce9b24bcd49e3683",
    "rule_registry_semantic_sha256": "5a772a45538af7ea3df082050842e1881601d626fc239a549c2a5538a3ca9c86",
}
REJECTED_LINEAGE = [
    {"revision": "E4R2", "status": "REJECTED_PROVENANCE_ONLY"},
    {"revision": "E4R3", "status": "REJECTED_PROVENANCE_ONLY"},
    {"revision": "E4R4", "status": "REJECTED_PROVENANCE_ONLY", "commit": "e360ce6c38f044e446ae8ba7e850b35840f2c8f8"},
    {"revision": "E4R5", "status": "REJECTED_PROVENANCE_ONLY", "commit": "b92d5707e9966c8543111b1c448aa5c2f5b0e496"},
    {"revision": "E4R5R1", "status": "REJECTED_PROVENANCE_ONLY", "commit": "f75352c0d673d77873fb96a9975a6c37abceb519"},
    {"revision": "E4R5R2", "status": "REJECTED_PROVENANCE_ONLY", "commit": "44d0e7240c97dcc12463b5611a7adf61399924d7"},
]

OBJ = {
    "rules": f"{NS}:rule-registry",
    "invariants": f"{NS}:invariant-registry",
    "procedures": f"{NS}:procedure-registry",
    "registry": f"{NS}:object-registry",
    "references": f"{NS}:reference-model",
    "authority": f"{NS}:authority-requirements",
    "governance": f"{NS}:governance-requirements",
    "integrity_modes": f"{NS}:integrity-modes",
    "semantic_keys": f"{NS}:semantic-key-authority",
    "inputs": f"{NS}:normative-inputs",
    "bindings": f"{NS}:accepted-source-bindings",
    "canon": f"{NS}:canonicalization-profile",
    "partial": f"{NS}:partial-effect-policy",
    "target": f"{NS}:v013-target",
    "evidence": f"{NS}:v013-evidence",
    "v013_gov": f"{NS}:v013-governance",
    "propositions": f"{NS}:proposition-inventory",
    "source_binding": f"{NS}:source-catalog-binding",
    "ext_contract": f"{NS}:external-verification-input-contract",
    "package": PKG_ID,
}

SCHEMA_NAMES = [
    "authority-requirements",
    "governance-requirements",
    "integrity-modes",
    "semantic-key-authority",
    "normative-inputs",
    "partial-effect-policy",
    "v013-target",
    "v013-evidence",
    "v013-governance",
    "proposition-inventory",
    "source-catalog-binding",
    "rule-registry",
    "invariant-registry",
    "procedure-registry",
    "reference-model",
    "accepted-source-bindings",
    "canonicalization-profile",
    "external-verification-input-contract",
    "object-registry",
    "specification-package",
]
SCHEMA_IDS = {name: f"{NS}:schema:{name}" for name in SCHEMA_NAMES}

# Inherited 104-rule inventory from E4R5R2 (see SOURCE_REVISION).  Row layout:
# [rule_id, class(R|D|I), inherited_family, inherited_failure_code, extra]
#   R = EXECUTABLE_CONFORMANCE_RULE, I = INTERNAL_DESIGN_INVARIANT,
#   D = DEFERRED_NO_SUBJECT_ARTIFACT with [missing_subject_roles, later_stage].
RULE_ROWS = json.loads(
    '[["ORC-001","D","ORACLE_BOUNDARY","ACCORD-02R2-ORACLE-REFERENCE",[["public scenario catalog","system-under-test input manifests"],"EXPERIMENT_ASSEMBLY"]],'
    '["ORC-002","D","ORACLE_BOUNDARY","ACCORD-02R2-ORACLE-REVERSE-JOIN",[["scorer configuration","public scenario catalog","arm manifests"],"EXPERIMENT_ASSEMBLY"]],'
    '["ORC-003","D","ORACLE_BOUNDARY","ACCORD-02R2-OPAQUE-SCENARIO-ID",[["scenario_id","fixture identity","timing configuration"],"EXPERIMENT_ASSEMBLY"]],'
    '["ARM-001","D","ARM_ISOLATION","ACCORD-02R2-ARM-DISCRIMINATOR",[["arm input manifest"],"EXPERIMENT_INPUT_ASSEMBLY"]],'
    '["ARM-002","D","ARM_ISOLATION","ACCORD-02R2-ARM-PROFILE-MISMATCH",[["arm_id","input_profile_id","arm input profile catalog"],"EXPERIMENT_INPUT_ASSEMBLY"]],'
    '["ARM-003","D","ARM_ISOLATION","ACCORD-02R2-SOURCE-TYPE-NOT-ALLOWED",[["arm source references","arm input profile"],"EXPERIMENT_INPUT_ASSEMBLY"]],'
    '["ARM-004","D","ARM_ISOLATION","ACCORD-02R2-SOURCE-RECORD-MISMATCH",[["source_type","source_record_ref.record_type"],"EXPERIMENT_INPUT_ASSEMBLY"]],'
    '["ARM-005","D","ARM_ISOLATION","ACCORD-02R2-ARM-EXTENSION-SMUGGLING",[["arm input manifest extensions","source projections"],"EXPERIMENT_INPUT_ASSEMBLY"]],'
    '["ARM-006","D","ARM_ISOLATION","ACCORD-02R2-CLASSIFIER-SOURCE-LEAK",[["ARM-C classifier feature references","ARM-B-visible source set"],"EXPERIMENT_INPUT_ASSEMBLY"]],'
    '["ARM-007","D","ARM_ISOLATION","ACCORD-02R2-EXTENSION-SEMANTIC-LEAK",[["arm-visible portable record extensions","active record/evidence profile"],"EXPERIMENT_INPUT_ASSEMBLY"]],'
    '["RAW-001","D","RAW_OUTPUT","ACCORD-02R2-RAW-ENVELOPE",[["raw arm output"],"PROVIDER_EXECUTION_CAPTURE"]],'
    '["RAW-002","D","RAW_OUTPUT","ACCORD-02R2-RAW-PAYLOAD-MISSING",[["raw arm output"],"PROVIDER_EXECUTION_CAPTURE"]],'
    '["RAW-003","D","RAW_OUTPUT","ACCORD-02R2-RAW-CROSS-ARM-FORWARD",[["raw arm output","other arm inputs"],"PROVIDER_EXECUTION_CAPTURE"]],'
    '["PROJ-001","D","PROJECTION","ACCORD-02R2-PROJECTION-LINEAGE-MISSING",[["A verifier projection","native C settlement result","named mapping profile","canonical proposition"],"VERIFIER_EXECUTION"]],'
    '["PROJ-002","D","PROJECTION","ACCORD-02R2-NEGATIVE-PROJECTION-UNSUPPORTED",[["native C result","NO_EFFECT_OBSERVED projection"],"VERIFIER_EXECUTION"]],'
    '["PROJ-003","D","PROJECTION","ACCORD-02R2-PROJECTION-STRENGTHENING",[["native C result","A projection"],"VERIFIER_EXECUTION"]],'
    '["PROJ-004","D","PROJECTION","ACCORD-02R2-REJECTED-HISTORY-REWRITE",[["REJECTED verifier disposition"],"VERIFIER_EXECUTION"]],'
    '["LIN-001","R","LINEAGE","ACCORD-02R2-REFERENCE-MISSING-OR-AMBIGUOUS"],'
    '["LIN-002","R","LINEAGE","ACCORD-02R2-DUPLICATE-NORMATIVE-ID"],'
    '["LIN-003","D","LINEAGE","ACCORD-02R2-FOREIGN-VERIFIER-RUN",[["experiment result","experiment run","verifier result","verifier run"],"EXPERIMENT_OR_SCORING_EXECUTION"]],'
    '["LIN-004","D","LINEAGE","ACCORD-02R2-SCENARIO-MISMATCH",[["experiment run","score record","result record"],"EXPERIMENT_OR_SCORING_EXECUTION"]],'
    '["LIN-005","D","LINEAGE","ACCORD-02R2-ARM-MISMATCH",[["experiment run","score record","result record"],"EXPERIMENT_OR_SCORING_EXECUTION"]],'
    '["LIN-006","D","LINEAGE","ACCORD-02R2-PROPOSITION-MISMATCH",[["settlement result","experiment proposition","result record"],"EXPERIMENT_OR_SCORING_EXECUTION"]],'
    '["LIN-007","R","LINEAGE","ACCORD-02R2-FOREIGN-RESULT"],'
    '["LIN-008","D","LINEAGE","ACCORD-02R2-EXTERNAL-ID-SUBSTITUTION",[["provider_operation_id","transport_call_id","Accord semantic references"],"EXPERIMENT_OR_SCORING_EXECUTION"]],'
    '["PROP-001","R","PROPOSITION","ACCORD-02R2-PROPOSITION-REFERENCE"],'
    '["PROP-002","D","PROPOSITION","ACCORD-02R2-PROPOSITION-CROSS-LINK-MISMATCH",[["evidence","observation","settlement result","verifier projection"],"VERIFIER_EXECUTION"]],'
    '["PROP-003","D","PROPOSITION","ACCORD-02R2-PROPOSITION-DUPLICATE-MISMATCH",[["denormalized effect/predicate/stage fields","canonical proposition"],"VERIFIER_EXECUTION"]],'
    '["PROP-004","D","PROPOSITION","ACCORD-02R2-BINDING-STATUS-INVALID",[["binding slots","active proposition/profile"],"VERIFIER_EXECUTION"]],'
    '["PROP-005","D","PROPOSITION","ACCORD-02R2-ATTEMPT-ATTRIBUTION-MISMATCH",[["attempt attribution","attempt record","native C result"],"VERIFIER_EXECUTION"]],'
    '["SCORE-001","D","SCORE_SEPARATION","ACCORD-02R2-SCORE-ARM-CONTAMINATION",[["score record","arm inputs"],"SCORING"]],'
    '["SCORE-002","D","SCORE_SEPARATION","ACCORD-02R2-SCORE-PIPELINE-REORDERED",[["raw arm output","normalization profile","normalized claim","scorer truth"],"SCORING"]],'
    '["SCORE-003","D","SCORE_SEPARATION","ACCORD-02R2-NORMALIZATION-ORACLE-USE",[["normalization profile","arm-visible information"],"SCORING"]],'
    '["BND-001","I","BUNDLE","ACCORD-02R3-BUNDLE-SCOPE-INVALID","CANDIDATE_UNACCEPTED"],'
    '["BND-002","I","BUNDLE","ACCORD-02R3-UNDECLARED-SCOPE","id"],'
    '["BND-003","D","BUNDLE","ACCORD-02R3-SCORER-MATERIAL-IN-BUNDLE",[["bundle information class","visibility flags"],"BUNDLE_ASSEMBLY"]],'
    '["BND-004","R","PACKAGE_CONTRACT","ACCORD-02R5-SCHEMA-CONTRACT-RESOLUTION-FAILURE"],'
    '["BND-005","R","PACKAGE_CONTRACT","ACCORD-02R5-ACTIVE-PROFILE-RESOLUTION-FAILURE"],'
    '["RUN-001","D","RUN_CONTRACT","ACCORD-02R3-EXPERIMENT-RUN-INCOMPLETE",[["experiment run record"],"EXPERIMENT_EXECUTION"]],'
    '["RUN-002","D","RUN_CONTRACT","ACCORD-02R3-VERIFIER-RUN-INCOMPLETE",[["verifier run record"],"EXPERIMENT_EXECUTION"]],'
    '["RUN-003","D","RUN_CONTRACT","ACCORD-02R3-RUN-MANIFEST-MISMATCH",[["experiment run","arm manifest"],"EXPERIMENT_EXECUTION"]],'
    '["RUN-004","D","RUN_CONTRACT","ACCORD-02R3-RUN-SCORER-REFERENCE",[["experiment run","verifier run"],"EXPERIMENT_EXECUTION"]],'
    '["EXT-001","I","EXTENSION","ACCORD-02R3-EXTENSION-UNREGISTERED","DEFERRED_NO_SUBJECT_ARTIFACT"],'
    '["EXT-002","D","EXTENSION","ACCORD-02R3-NON-SEMANTIC-USED",[["extension registry","NON_SEMANTIC extensions"],"BUNDLE_OR_VERIFIER_EXECUTION"]],'
    '["EXT-003","D","EXTENSION","ACCORD-02R3-AUTHORITY-EXTENSION-NO-COMPARATOR",[["AUTHORITY_BEARING extension","authority profile"],"BUNDLE_OR_VERIFIER_EXECUTION"]],'
    '["EXT-004","D","EXTENSION","ACCORD-02R3-EVIDENCE-EXTENSION-NO-PROFILE",[["SETTLEMENT_BEARING or EVIDENCE_BEARING extension","settlement/evidence profile"],"BUNDLE_OR_VERIFIER_EXECUTION"]],'
    '["EXT-005","D","EXTENSION","ACCORD-02R3-EXTENSION-CANNOT-STRENGTHEN",[["unknown or incompatible extension"],"BUNDLE_OR_VERIFIER_EXECUTION"]],'
    '["EXT-006","D","EXTENSION","ACCORD-02R3-EXTENSION-REGISTRY-MISSING",[["arm-visible portable bundle","extension registry"],"BUNDLE_OR_VERIFIER_EXECUTION"]],'
    '["SRC-001","R","SOURCE_MEMBERSHIP","ACCORD-02R3-SOURCE-SCHEMA-NOT-PERMITTED"],'
    '["SRC-002","R","SOURCE_MEMBERSHIP","ACCORD-02R3-SOURCE-CLASS-MISMATCH"],'
    '["SRC-003","R","SOURCE_MEMBERSHIP","ACCORD-02R3-SOURCE-FILENAME-NOT-AUTHORITY"],'
    '["SRC-004","D","SOURCE_MEMBERSHIP","ACCORD-02R3-SOURCE-EVIDENCE-MASQUERADE",[["provider/transport/raw output","portable evidence"],"PROVIDER_EXECUTION_CAPTURE"]],'
    '["VIS-001","D","ROLE_VISIBILITY","ACCORD-02R3-VISIBILITY-VIOLATION",[["role-visibility profile","arm manifest fields"],"EXPERIMENT_INPUT_ASSEMBLY"]],'
    '["NORM-001","D","NORMALIZATION","ACCORD-02R3-NORMALIZATION-INPUT-INVALID",[["raw arm output","normalization profile"],"NORMALIZATION_EXECUTION"]],'
    '["NORM-002","D","NORMALIZATION","ACCORD-02R3-NORMALIZATION-ORACLE-INPUT",[["normalization process inputs"],"NORMALIZATION_EXECUTION"]],'
    '["NORM-003","D","NORMALIZATION","ACCORD-02R3-NORMALIZATION-NONDETERMINISTIC",[["raw arm output","normalization profile"],"NORMALIZATION_EXECUTION"]],'
    '["NORM-004","D","NORMALIZATION","ACCORD-02R3-NORMALIZATION-MALFORMED-UNDEFINED",[["malformed or unmapped raw output","normalization profile"],"NORMALIZATION_EXECUTION"]],'
    '["NORM-005","D","NORMALIZATION","ACCORD-02R3-NORMALIZATION-TRUTH-REINTERPRETATION",[["normalized claim","scorer truth"],"NORMALIZATION_EXECUTION"]],'
    '["CLF-001","D","CLASSIFIER_FEATURE","ACCORD-02R3-CLASSIFIER-FEATURE-UNREGISTERED",[["classifier feature","classifier feature profile"],"CLASSIFICATION_EXECUTION"]],'
    '["CLF-002","D","CLASSIFIER_FEATURE","ACCORD-02R3-CLASSIFIER-UPSTREAM-INVALID",[["derived classifier feature","ARM-C source set"],"CLASSIFICATION_EXECUTION"]],'
    '["CLF-003","D","CLASSIFIER_FEATURE","ACCORD-02R3-CLASSIFIER-PRIVILEGED-UPSTREAM",[["classifier feature derivation"],"CLASSIFICATION_EXECUTION"]],'
    '["CLF-004","D","CLASSIFIER_FEATURE","ACCORD-02R3-CLASSIFIER-FEATURE-UNKNOWN",[["classifier feature"],"CLASSIFICATION_EXECUTION"]],'
    '["PRED-001","I","PREDICATE_APPLICABILITY","ACCORD-02R3-REQUIRED-BINDING-UNRESOLVED","FORBIDDEN"],'
    '["PRED-002","I","PREDICATE_APPLICABILITY","ACCORD-02R3-NOT-APPLICABLE-UNJUSTIFIED","FORBIDDEN"],'
    '["PRED-003","I","PREDICATE_APPLICABILITY","ACCORD-02R3-UNKNOWN-BINDING-STRENGTHENING",["predicate_id","stage"]],'
    '["PRED-004","I","PREDICATE_APPLICABILITY","ACCORD-02R3-PREDICATE-PROFILE-MISMATCH","UNICODE_CODE_POINT_EXACT_CASE_SENSITIVE_NO_NORMALIZATION"],'
    '["DIGEST-001","R","PACKAGE_CONTRACT","ACCORD-02R5-DIGEST-MISMATCH"],'
    '["DIGEST-002","I","DIGEST","ACCORD-02R3-DIGEST-REQUIRED-BUT-ABSENT","EXCLUDE_JSON_POINTERS"],'
    '["DIGEST-003","I","DIGEST","ACCORD-02R3-DIGEST-FAILURE-HISTORY-SEPARATED","INCLUDE_JSON_POINTERS"],'
    '["LIN-009","R","LINEAGE_CLOSURE","ACCORD-02R3-STRUCTURALLY-INVALID-REFERENCE-TARGET"],'
    '["PROP-006","R","LINEAGE_CLOSURE","ACCORD-02R3-PROPOSITION-ID-COLLISION"],'
    '["PKG-001","R","SPECIFICATION_PACKAGE","ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH"],'
    '["PKG-002","R","SPECIFICATION_PACKAGE","ACCORD-02R5-PACKAGE-CONTRACT-DUPLICATE-OR-DANGLING"],'
    '["PROF-001","I","PROFILE_RESOLUTION","ACCORD-02R5-PROFILE-RESOLUTION-FAILURE","UNKNOWN"],'
    '["PROF-002","R","PROFILE_RESOLUTION","ACCORD-02R5-PROFILE-VERSION-UNPINNED"],'
    '["SCHEMA-001","R","SCHEMA_CONTRACT","ACCORD-02R5-SCHEMA-CONTRACT-FAILURE"],'
    '["SCHEMA-002","R","SCHEMA_CONTRACT","ACCORD-02R5-STRUCTURE-VALIDATION-FAILURE"],'
    '["ROLE-001","I","ROLE_VOCABULARY","ACCORD-02R5-UNKNOWN-ROLE","0.2"],'
    '["DIGEST-CANON-001","R","DIGEST_CANONICALIZATION","ACCORD-02R5-CANONICALIZATION-MISSING"],'
    '["DIGEST-CANON-002","R","DIGEST_CANONICALIZATION","ACCORD-02R5-CANONICALIZATION-INCOMPATIBLE"],'
    '["DIGEST-CANON-003","R","DIGEST_CANONICALIZATION","ACCORD-02R5-CANONICALIZATION-UNSUPPORTED"],'
    '["SCENARIO-ID-001","I","SCENARIO_ID_POLICY","ACCORD-02R5-SCENARIO-ID-SEMANTIC-USE","NOT_APPLICABLE"],'
    '["E4R1-PRED-001","R","PREDICATE_APPLICABILITY","PREDICATE_TUPLE_RESOLUTION_FAILURE"],'
    '["E4R1-PRED-002","R","FAIL_CLOSED","PREDICATE_FAIL_CLOSED"],'
    '["E4R1-PRED-003","R","EXACT_IDENTIFIER","PREDICATE_IDENTIFIER_NOT_EXACT"],'
    '["E4R1-AUTH-001","R","PREDICATE_AUTHORITY","COMPETING_PREDICATE_AUTHORITY"],'
    '["E4R1-BIND-001","R","BINDING_AUTHORITY","BINDING_AUTHORITY_CONTRADICTION"],'
    '["E4R1-PROP-001","R","PROPOSITION_KIND","PROPOSITION_KIND_MISMATCH"],'
    '["E4R1-PART-001","R","PARTIAL_EFFECT","PARTIAL_EFFECT_PREREQUISITE_UNSATISFIED"],'
    '["E4R1-PART-002","R","PREDECESSOR_IDENTITY","PREDECESSOR_EFFECT_MISMATCH"],'
    '["E4R1-PART-003","R","PREDECESSOR_GRAPH","PREDECESSOR_GRAPH_INVALID"],'
    '["E4R1-NEG-001","R","NEGATIVE_SCOPE","NEGATIVE_SCOPE_INCOMPLETE"],'
    '["E4R1-NEG-002","R","NEGATIVE_SCOPE","NEGATIVE_SCOPE_NOT_SUFFICIENT"],'
    '["E4R1-ENT-001","R","NON_ENTAILMENT","FORBIDDEN_ENTAILMENT"],'
    '["E4R1-CANON-001","R","CANONICALIZATION","CANONICALIZATION_MAPPING_INVALID"],'
    '["E4R1-EXPECT-001","R","EXPECTATION_CONTRACT","EXPECTATION_CONTRACT_INCOMPLETE"],'
    '["E4R1-CLOSE-001","R","CANDIDATE_CLOSURE","CANDIDATE_CLOSURE_FAILURE"],'
    '["E4R2-REF-001","R","REFERENCE_RESOLUTION","REFERENCE_RESOLUTION_FAILURE"],'
    '["E4R2-CANON-001","R","CANONICALIZATION","CANONICALIZATION_TARGET_FAILURE"],'
    '["E4R2-BIND-001","R","BINDING_AUTHORITY","BINDING_COMPOSITION_FAILURE"],'
    '["E4R2-NEG-001","R","NEGATIVE_SCOPE","NEGATIVE_REQUIREMENT_MAP_FAILURE"],'
    '["E4R2-GRAPH-001","R","RULE_GRAPH","RULE_GRAPH_CLOSURE_FAILURE"],'
    '["E4R2-PROFILE-001","R","PROFILE_POLICY","PROFILE_DIGEST_SCOPE_FAILURE"],'
    '["E4R2-CLOSE-001","R","CANDIDATE_CLOSURE","MEASURED_CLOSURE_FAILURE"]]'
)

# rule -> governing invariant for the 42 executable conformance members.
RULE_INVARIANT = {
    "LIN-001": "TYPED_REFERENCE_CLOSURE", "LIN-002": "OBJECT_IDENTITY_UNIQUE",
    "LIN-007": "PACKAGE_LINEAGE", "PROP-001": "STANDARDS_VALIDATION",
    "BND-004": "STANDARDS_VALIDATION", "BND-005": "PREDICATE_AUTHORITY_CLOSURE",
    "SRC-001": "SOURCE_CATALOG_BINDING", "SRC-002": "ACCEPTED_SOURCE_DUAL_INTEGRITY",
    "SRC-003": "SOURCE_CATALOG_BINDING", "DIGEST-001": "SEMANTIC_DIGEST_VERIFY",
    "LIN-009": "STANDARDS_VALIDATION", "PROP-006": "PROPOSITION_INVENTORY_BOUND",
    "PKG-001": "PACKAGE_LINEAGE", "PKG-002": "TYPED_REFERENCE_CLOSURE",
    "PROF-002": "PROFILE_REFERENCE_PINNING", "SCHEMA-001": "TYPED_REFERENCE_CLOSURE",
    "SCHEMA-002": "STANDARDS_VALIDATION", "DIGEST-CANON-001": "CANONICALIZATION_AUTHORITY_CLOSURE",
    "DIGEST-CANON-002": "CANONICALIZATION_AUTHORITY_CLOSURE", "DIGEST-CANON-003": "CANONICALIZATION_AUTHORITY_CLOSURE",
    "E4R1-PRED-001": "PREDICATE_AUTHORITY_CLOSURE", "E4R1-PRED-002": "PREDICATE_AUTHORITY_CLOSURE",
    "E4R1-PRED-003": "PREDICATE_AUTHORITY_CLOSURE", "E4R1-AUTH-001": "PREDICATE_AUTHORITY_CLOSURE",
    "E4R1-BIND-001": "PREDICATE_AUTHORITY_CLOSURE", "E4R1-PROP-001": "STANDARDS_VALIDATION",
    "E4R1-PART-001": "PARTIAL_EFFECT_POLICY_CLOSURE", "E4R1-PART-002": "PARTIAL_EFFECT_POLICY_CLOSURE",
    "E4R1-PART-003": "PARTIAL_EFFECT_POLICY_CLOSURE", "E4R1-NEG-001": "NEGATIVE_REQUIREMENT_MAP_CLOSURE",
    "E4R1-NEG-002": "NEGATIVE_REQUIREMENT_MAP_CLOSURE", "E4R1-ENT-001": "PREDICATE_AUTHORITY_CLOSURE",
    "E4R1-CANON-001": "CANONICALIZATION_AUTHORITY_CLOSURE", "E4R1-EXPECT-001": "EXPECTATION_STABILITY",
    "E4R1-CLOSE-001": "RULE_EXPECTATION_AUTHORITY_COMPLETE", "E4R2-REF-001": "TYPED_REFERENCE_CLOSURE",
    "E4R2-CANON-001": "CANONICALIZATION_AUTHORITY_CLOSURE", "E4R2-BIND-001": "PREDICATE_AUTHORITY_CLOSURE",
    "E4R2-NEG-001": "NEGATIVE_REQUIREMENT_MAP_CLOSURE", "E4R2-GRAPH-001": "DEPENDENCY_GRAPH_EQUAL",
    "E4R2-PROFILE-001": "SEMANTIC_DIGEST_VERIFY", "E4R2-CLOSE-001": "RULE_EXPECTATION_AUTHORITY_COMPLETE",
}

DEPENDENT_RULES = json.loads(
    '[["BND-002",["BND-001"]],["BND-003",["BND-001"]],["BND-004",["PKG-001","PKG-002","SCHEMA-001","SCHEMA-002"]],'
    '["BND-005",["PKG-001","PKG-002","PROF-001","PROF-002"]],["RUN-001",["BND-005"]],["RUN-002",["BND-005"]],'
    '["RUN-003",["RUN-001","ARM-001","ARM-002"]],["RUN-004",["RUN-001","RUN-002","BND-003"]],["EXT-001",["BND-005"]],'
    '["EXT-002",["EXT-001"]],["EXT-003",["EXT-001","BND-005"]],["EXT-004",["EXT-001","BND-005"]],["EXT-005",["EXT-001"]],'
    '["EXT-006",["BND-005","EXT-001"]],["SRC-001",["BND-005","ARM-001"]],["SRC-002",["SRC-001"]],["SRC-003",["SRC-001"]],'
    '["SRC-004",["SRC-001","EXT-001"]],["VIS-001",["BND-005","RUN-001"]],["NORM-001",["RAW-001","BND-005"]],'
    '["NORM-002",["NORM-001","BND-003"]],["NORM-003",["NORM-001"]],["NORM-004",["NORM-001"]],["NORM-005",["NORM-002","NORM-003"]],'
    '["CLF-001",["BND-005","SRC-001"]],["CLF-002",["CLF-001","SRC-001"]],["CLF-003",["CLF-001","CLF-002"]],["CLF-004",["CLF-001"]],'
    '["PRED-001",["BND-005","PROP-001"]],["PRED-002",["PRED-001"]],["PRED-003",["PRED-001"]],["PRED-004",["PRED-001","PROP-001","PROP-002"]],'
    '["DIGEST-001",["BND-004","DIGEST-CANON-001","DIGEST-CANON-002","DIGEST-CANON-003"]],["DIGEST-002",["BND-005"]],["DIGEST-003",["DIGEST-001"]],'
    '["LIN-009",["LIN-001","DIGEST-001"]],["PROP-006",["PROP-001","LIN-002"]],["PKG-002",["PKG-001"]],["PROF-001",["PKG-001","PKG-002"]],'
    '["PROF-002",["PROF-001"]],["SCHEMA-001",["PKG-001","PKG-002"]],["SCHEMA-002",["SCHEMA-001"]],["ROLE-001",["PKG-001","PKG-002","PROF-001"]],'
    '["DIGEST-CANON-001",["PKG-001","PKG-002","PROF-001","SCHEMA-001"]],["DIGEST-CANON-002",["DIGEST-CANON-001","SCHEMA-001"]],["DIGEST-CANON-003",["DIGEST-CANON-001"]],'
    '["SCENARIO-ID-001",["PROF-001","CLF-001"]],["E4R1-PRED-001",["PRED-004","PKG-002"]],["E4R1-PRED-002",["E4R1-PRED-001"]],'
    '["E4R1-PRED-003",["E4R1-PRED-001"]],["E4R1-AUTH-001",["PKG-002","E4R1-PRED-003"]],["E4R1-BIND-001",["PRED-001","PRED-002","E4R1-PRED-001"]],'
    '["E4R1-PROP-001",["SCHEMA-002","E4R1-PRED-001"]],["E4R1-PART-001",["E4R1-BIND-001","E4R1-PRED-001"]],'
    '["E4R1-PART-002",["E4R1-PART-001","E4R1-PRED-001"]],["E4R1-PART-003",["E4R1-PRED-001","PKG-002"]],'
    '["E4R1-NEG-001",["E4R1-PRED-001","E4R1-BIND-001"]],["E4R1-NEG-002",["E4R1-NEG-001"]],'
    '["E4R1-ENT-001",["E4R1-PRED-001","E4R1-AUTH-001"]],["E4R1-CANON-001",["DIGEST-CANON-001","DIGEST-CANON-002"]],'
    '["E4R1-EXPECT-001",["PKG-002"]],["E4R1-CLOSE-001",["PKG-002","E4R1-PRED-001","E4R1-PART-003","E4R1-CANON-001"]],'
    '["E4R2-REF-001",["PKG-002"]],["E4R2-CANON-001",["DIGEST-CANON-002"]],["E4R2-BIND-001",["E4R1-BIND-001"]],'
    '["E4R2-NEG-001",["E4R1-NEG-001"]],["E4R2-GRAPH-001",["E4R1-PART-003"]],["E4R2-PROFILE-001",["PKG-002","E4R1-BIND-001"]],'
    '["E4R2-CLOSE-001",["E4R1-CLOSE-001","E4R2-REF-001","E4R2-CANON-001","E4R2-NEG-001","E4R2-GRAPH-001"]]]'
)

INTERNAL_DESIGN_VALUES = {
    row[0]: row[4] for row in RULE_ROWS if row[1] == "I"
}

CONFORMANCE_RULES = [row[0] for row in RULE_ROWS if row[1] == "R"]
INTERNAL_RULES = [row[0] for row in RULE_ROWS if row[1] == "I"]
DEFERRED_RULES = [row[0] for row in RULE_ROWS if row[1] == "D"]


def load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sem(value) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def sem_file(path: Path) -> str:
    return sem(load(path))


def raw_sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tref(kind, id, version=VERSION, member_id=None):
    out = {"kind": kind, "id": id, "version": version}
    if member_id is not None:
        out["member_id"] = member_id
    return out


def envelope(object_id, schema_name):
    return {
        "$schema": DIALECT,
        "schema_ref": tref("SCHEMA", SCHEMA_IDS[schema_name]),
        "$id": f"{object_id}:{VERSION}",
        "object_id": object_id,
        "object_version": VERSION,
    }


def build() -> dict:
    """Return the complete artifact set as {relative_path: json_value}."""
    accepted_catalog = load(ACCEPTED / "examples/accord-02c-settlement-test-vectors.json")
    accepted_package = load(ACCEPTED / "accord-02r5-specification-package.json")
    artifacts: dict[str, object] = {}

    def put(name: str, value) -> None:
        artifacts[name] = value

    # ---------------------------------------------------------------- authority
    authority = envelope(OBJ["authority"], "authority-requirements")
    authority.update(
        {
            "package_requirements": {
                "family": PKG_ID,
                "version": VERSION,
                "status": "CANDIDATE_UNACCEPTED",
                "accepted_base_version": "0.1",
                "required_rejected_revision": {
                    "revision": "E4R5R2",
                    "commit": SOURCE_REVISION["commit"],
                },
            },
            "stage_policy_requirements": {
                "global_stage_order": "FORBIDDEN",
                "implicit_transitivity": "FORBIDDEN",
            },
            "stage_policy_authorization": {
                "global_stage_order": ["FORBIDDEN"],
                "implicit_transitivity": ["FORBIDDEN"],
            },
            "canonicalization_requirements": {
                "standard": "RFC8785",
                "serialization": "RFC8785_JCS",
                "encoding": "UTF-8",
                "algorithm": "SHA-256",
                "target_id": "PACKAGE_EXCLUDING_SELF_DIGEST",
                "selection": "ENTIRE_PACKAGE_DOCUMENT",
                "reduction": "REMOVE_POINTER",
                "exclusion_pointers": ["/current_candidate_integrity/digest"],
            },
            "partial_effect_requirements": {
                "same_effect_required": True,
                "direct_predecessor_required": True,
                "merged_decision_key": "UNKNOWN_TUPLE_OR_WRONG_STAGE",
                "merged_decision_value": "REJECT",
            },
            "classification_requirements": {
                "conformance": "invariant_binding exists and validates",
                "internal": "internal_check exists and no invariant_binding",
                "deferred": "missing_subject_roles and later_lifecycle_stage exist and no binding/check",
            },
            "governing_contract_refs": {
                "integrity_modes": tref("CONTRACT", OBJ["integrity_modes"]),
                "semantic_key_authority": tref("CONTRACT", OBJ["semantic_keys"]),
                "governance_requirements": tref("CONTRACT", OBJ["governance"]),
                "external_verification_contract": tref("CONTRACT", OBJ["ext_contract"]),
            },
            "trust_boundary_requirements": {
                "layers": ["INTERNAL_PACKAGE_CONFORMANCE", "TRUSTED_PACKAGE_IDENTITY"],
                "external_input_source": "CALLER_SUPPLIED_OUTSIDE_OBJECT_REGISTRY",
                "candidate_self_assertion_permitted": False,
                "missing_external_input_result": "FAIL",
                "cli": [
                    "--expected-package-id",
                    "--expected-package-version",
                    "--expected-package-digest",
                    "--verification-input",
                ],
                "trust_root_kinds": ["PINNED_ACCEPTED_TRUST_ROOT", "REPLACED_TRUST_ROOT"],
                "result_vocabulary": ["PASS", "FAIL", "DIFFERENT_PACKAGE_VERIFIED"],
                "replacement_sub_status": "OUT_OF_SCOPE_TRUST_ROOT_REPLACEMENT",
            },
        }
    )
    put("authority-requirements.json", authority)

    # --------------------------------------------------------------- governance
    governance_invariant_ids = [
        "FAIL_CLOSED_ENFORCED",
        "SUBJECT_ROLE_COVERAGE",
        "DEFAULT_ARGUMENT_COVERAGE",
        "DERIVATION_ROLE_CLOSURE",
        "PROCEDURE_OPERATION_SUPPORTED",
        "MISSING_BEHAVIOR_SUPPORTED",
        "AMBIGUITY_BEHAVIOR_SUPPORTED",
        "REFERENCE_DISCOVERY_SCOPE_VALID",
        "REFERENCE_SHAPE_PREDICATE_APPLIED",
        "UNIQUENESS_KEY_APPLIED",
        "ROLE_MODEL_APPLIED",
        "SCHEMA_IDENTITY_MATCHES_REGISTRY",
        "RULE_COVERAGE_EXACT",
        "INVARIANT_SET_EXACT",
        "GOVERNING_AUTHORITY_REFERENCE_VALID",
        "GOVERNING_TOKEN_SINGLETON",
    ]
    governance = envelope(OBJ["governance"], "governance-requirements")
    governance.update(
        {
            "scope": "BOUNDED_PACKAGE_ONLY_GOVERNANCE",
            "governance_invariants": governance_invariant_ids,
            "fail_closed_requirement": {
                "acceptance_critical_must_be_fail_closed": True,
                "reject_false": "METACONTRACT_REJECTS",
            },
            "behavior_vocabulary": {
                "missing_behavior": ["FAIL_CLOSED"],
                "ambiguity_behavior": ["FAIL_CLOSED"],
                "explicit_behavior": {
                    "FAIL_CLOSED": "resolution failure or ambiguity yields an invariant FAIL"
                },
            },
            "subject_role_requirement": {
                "every_subject_role_is_input_role": True,
                "every_semantic_subject_declared_by_role_model": True,
                "role_model": "SUBJECT_ROLES_DECLARED_SUBSET_OF_INPUT_ROLES",
            },
            "default_argument_requirement": {
                "cover_every_required_role": True,
                "no_undeclared_role": True,
                "validate_kind_and_cardinality": True,
                "resolve_exactly": True,
            },
            "derivation_role_closure_requirement": {
                "sets_must_be_equal": [
                    "invariant_required_input_roles",
                    "procedure_required_arguments",
                    "derivation_referenced_roles",
                ],
                "optional_arguments_must_be_declared": True,
            },
            "reference_discovery_scope_requirement": {
                "source": "reference_model:/discovery_scope",
                "require_non_empty_universe": True,
            },
            "shape_predicate_requirement": {
                "additional_keys_authority": "DISQUALIFY",
                "allowed_additional_keys": ["DISQUALIFY"],
                "behaviour_derived_from_declared_field": True,
            },
            "uniqueness_key_requirement": {
                "identity_fields": ["kind", "id", "version"],
                "detect_duplicates": True,
            },
            "role_model_requirement": {
                "required_role_model": "roles-array",
                "role_source": "object-registry:/role_vocabulary",
                "unknown_role_fails": True,
            },
            "schema_identity_requirement": {
                "identity_template": f"{NS}:schema:{{name}}:{VERSION}",
                "schema_id_must_equal_registered_identity": True,
            },
            "governing_authority_requirement": {
                "authority_roots_source": "v013-governance:/authority_roots",
                "reference_must_resolve": True,
            },
            "rule_coverage_requirement": {
                "required_rule_ids_ref": "rule-registry:/required_rule_ids",
                "exact": True,
            },
            "invariant_set_requirement": {
                "required_invariant_ids_ref": "package:/required_invariant_ids",
                "exact": True,
            },
            "supported_operations": [
                "VALIDATE_ACTIVE_UNIVERSE", "SECTION_ENTAILMENT", "DIGEST_RECOMPUTE",
                "UNIQUE_KEY", "REFERENCE_RESOLUTION", "SET_EQUALITY", "POLICY_AGREEMENT",
                "SOURCE_CATALOG_BINDING_MATCH", "REQUIREMENT_MAP_EVAL", "AUTHORITY_COMPLETENESS",
                "PROPOSITION_INVENTORY_BOUND", "ARITY_AGREEMENT", "SCHEMA_NON_VACUITY",
                "CURRENT_PACKAGE_IDENTITY", "SELF_DIGEST", "INTEGRITY_MODE_DISPATCH",
                "V013_BASIS_VALID", "FAIL_CLOSED_ENFORCED", "SUBJECT_ROLE_COVERAGE",
                "DEFAULT_ARGUMENT_COVERAGE", "DERIVATION_ROLE_CLOSURE",
                "PROCEDURE_OPERATION_SUPPORTED", "MISSING_BEHAVIOR_SUPPORTED",
                "AMBIGUITY_BEHAVIOR_SUPPORTED", "REFERENCE_DISCOVERY_SCOPE_VALID",
                "REFERENCE_SHAPE_PREDICATE_APPLIED", "UNIQUENESS_KEY_APPLIED",
                "ROLE_MODEL_APPLIED", "SCHEMA_IDENTITY_MATCHES_REGISTRY",
                "RULE_COVERAGE_EXACT", "INVARIANT_SET_EXACT",
                "GOVERNING_AUTHORITY_REFERENCE_VALID", "GOVERNING_TOKEN_SINGLETON",
                "TRUST_ANCHOR_COMPARE",
            ],
            "semantic_key_governance": {
                "semantic_key_authority_ref": tref("CONTRACT", OBJ["semantic_keys"]),
                "forbid_duplicate_independent_authority": True,
                "permitted_exception_roles": ["PROVENANCE", "TEST_FIXTURE"],
            },
        }
    )
    put("governance-requirements.json", governance)

    # ----------------------------------------------------------- integrity modes
    integrity_modes = envelope(OBJ["integrity_modes"], "integrity-modes")
    integrity_modes.update(
        {
            "modes": [
                {
                    "mode": "SEMANTIC_JSON_CONTENT",
                    "input": "CANONICAL_JSON_OF_OBJECT_FILE",
                    "canonicalization": "RFC8785_JCS",
                    "algorithm": "SHA-256",
                    "expected_digest_source": "OBJECT_INTEGRITY_DIGEST_FIELD",
                    "verification_operation": "REMOVE_NOT_APPLICABLE_RECOMPUTE_AND_COMPARE",
                    "failure_code": "E4R5R3-SEMANTIC-DIGEST-MISMATCH",
                    "applicability": ["NORMATIVE_PACKAGE_LOCAL_FILE"],
                },
                {
                    "mode": "RAW_FILE_BYTES",
                    "input": "RAW_FILE_BYTES",
                    "canonicalization": "NONE",
                    "algorithm": "SHA-256",
                    "expected_digest_source": "OBJECT_INTEGRITY_DIGEST_FIELD",
                    "verification_operation": "RECOMPUTE_AND_COMPARE",
                    "failure_code": "E4R5R3-RAW-FILE-DIGEST-MISMATCH",
                    "applicability": ["NORMATIVE_PACKAGE_LOCAL_FILE"],
                },
                {
                    "mode": "PACKAGE_PINNED_BOOTSTRAP",
                    "input": "CANONICAL_JSON_OF_OBJECT_FILE",
                    "canonicalization": "RFC8785_JCS",
                    "algorithm": "SHA-256",
                    "expected_digest_source": "PACKAGE_REGISTRY_SEMANTIC_SHA256",
                    "verification_operation": "RECOMPUTE_AND_COMPARE",
                    "failure_code": "E4R5R3-BOOTSTRAP-DIGEST-MISMATCH",
                    "applicability": ["OBJECT_REGISTRY"],
                },
                {
                    "mode": "SELF_DIGEST",
                    "input": "OBJECT_WITH_EXCLUSION_POINTERS_REMOVED",
                    "canonicalization": "RFC8785_JCS",
                    "algorithm": "SHA-256",
                    "expected_digest_source": "OBJECT_CURRENT_CANDIDATE_INTEGRITY_DIGEST",
                    "verification_operation": "REMOVE_POINTER_THEN_RECOMPUTE_AND_COMPARE",
                    "failure_code": "E4R5R3-SELF-DIGEST-MISMATCH",
                    "applicability": ["CURRENT_CANDIDATE_PACKAGE"],
                },
                {
                    "mode": "DUAL_ACCEPTED_SOURCE",
                    "input": "RAW_FILE_BYTES_AND_CANONICAL_JSON",
                    "canonicalization": "RFC8785_JCS",
                    "algorithm": "SHA-256",
                    "expected_digest_source": "BOUND_ACCEPTED_SOURCE_BINDING",
                    "verification_operation": "RECOMPUTE_BOTH_AND_COMPARE",
                    "failure_code": "E4R5R3-ACCEPTED-SOURCE-DIGEST-MISMATCH",
                    "applicability": ["ACCEPTED_SOURCE"],
                },
            ],
            "dispatch": {
                "procedure_operation": "INTEGRITY_MODE_DISPATCH",
                "dispatch_key": "OBJECT_INTEGRITY_MODE_FIELD",
                "unknown_mode_behavior": "FAIL_CLOSED",
                "unknown_mode_failure_code": "E4R5R3-INTEGRITY-MODE-UNKNOWN",
            },
        }
    )
    put("integrity-modes.json", integrity_modes)

    # ------------------------------------------------------- semantic key auth
    semantic_keys = envelope(OBJ["semantic_keys"], "semantic-key-authority")
    semantic_keys.update(
        {
            "semantic_keys": [
                {
                    "key": "global_stage_order",
                    "authority_path": "authority:/stage_policy_requirements/global_stage_order",
                    "governed_mirror_paths": [
                        "inputs:/predicate_policy/global_stage_order",
                        "authority:/stage_policy_authorization/global_stage_order",
                    ],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "implicit_transitivity",
                    "authority_path": "authority:/stage_policy_requirements/implicit_transitivity",
                    "governed_mirror_paths": [
                        "inputs:/predicate_policy/implicit_transitivity",
                        "authority:/stage_policy_authorization/implicit_transitivity",
                    ],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "same_effect_required",
                    "authority_path": "authority:/partial_effect_requirements/same_effect_required",
                    "governed_mirror_paths": ["partial:/same_effect_required"],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "direct_predecessor_required",
                    "authority_path": "authority:/partial_effect_requirements/direct_predecessor_required",
                    "governed_mirror_paths": ["partial:/direct_predecessor_required"],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "minimum_retention_seconds",
                    "authority_path": "inputs:/profile/negative_policy/minimum_retention_seconds",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "freshness_max_age_seconds",
                    "authority_path": "inputs:/profile/negative_policy/freshness_max_age_seconds",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "future_observation_result",
                    "authority_path": "inputs:/profile/negative_policy/future_observation_result",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "stale_result",
                    "authority_path": "inputs:/profile/negative_policy/stale_result",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "contradiction_rule",
                    "authority_path": "inputs:/profile/negative_policy/contradiction_rule",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "complete_read_requirement",
                    "authority_path": "inputs:/profile/negative_policy/complete_read_requirement",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "additional_keys",
                    "authority_path": "references:/shape_predicate/additional_keys",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "uniqueness_key",
                    "authority_path": "registry:/uniqueness_key",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
                {
                    "key": "role_model",
                    "authority_path": "registry:/role_model",
                    "governed_mirror_paths": [],
                    "permitted_provenance_roles": ["NORMATIVE", "PROVENANCE"],
                },
            ],
            "governing_token_singleton": {
                "operation": "GOVERNING_TOKEN_SINGLETON",
                "forbid": "DUPLICATE_INDEPENDENT_AUTHORITY",
                "permitted_exception_roles": ["PROVENANCE", "TEST_FIXTURE"],
                "scan": "DECLARED_SEMANTIC_KEY_METADATA",
                "scan_excludes_kinds": ["SCHEMA"],
                "scan_excluded_pointer_prefixes": [
                    "/policy_field_roles", "/requirement_map", "/relationship_basis",
                    "/evidence_universe", "/vector_expectations", "/internal_design_values",
                    "/rules", "/invariants", "/procedures", "/objects", "/sources", "/members",
                    "/reason_code_surface", "/must_not_conclude_surface", "/supported_operations",
                    "/fields", "/results", "/mode_map", "/governed_mirror_paths",
                    "/subject_role_requirement", "/role_model_requirement",
                    "/uniqueness_key_requirement", "/default_argument_requirement",
                    "/derivation_role_closure_requirement", "/fail_closed_requirement",
                    "/shape_predicate_requirement", "/reference_discovery_scope_requirement",
                    "/governing_authority_requirement", "/rule_coverage_requirement",
                    "/invariant_set_requirement", "/semantic_key_governance",
                ],
            },
        }
    )
    put("semantic-key-authority.json", semantic_keys)

    # --------------------------------------------------------- source binding
    catalog_path = "docs/accord-02/examples/accord-02c-settlement-test-vectors.json"
    package_path = "docs/accord-02/accord-02r5-specification-package.json"
    accepted_bindings = envelope(OBJ["bindings"], "accepted-source-bindings")
    accepted_bindings["sources"] = [
        {
            "ref": tref("PACKAGE", PKG_ID, "0.1"),
            "path": package_path,
            "status": "ACTIVE_ACCEPTED_SOURCE",
            "roles": ["NORMATIVE_BOUND_SOURCE"],
            "integrity": {
                "semantic_json_content_sha256": sem_file(ACCEPTED / "accord-02r5-specification-package.json"),
                "raw_file_bytes_sha256": raw_sha(ACCEPTED / "accord-02r5-specification-package.json"),
                "raw_byte_preservation": "GIT_ATTRIBUTES_MINUS_TEXT",
            },
        },
        {
            "ref": tref("SOURCE_VECTOR_CATALOG", CATALOG_ID, "0.1"),
            "path": catalog_path,
            "status": "ACTIVE_ACCEPTED_SOURCE",
            "roles": ["CATALOG_BINDING", "VECTOR_SOURCE"],
            "integrity": {
                "semantic_json_content_sha256": sem(accepted_catalog),
                "raw_file_bytes_sha256": raw_sha(ACCEPTED / "examples/accord-02c-settlement-test-vectors.json"),
                "raw_byte_preservation": "GIT_ATTRIBUTES_MINUS_TEXT",
            },
        },
    ]
    put("accepted-source-bindings.json", accepted_bindings)

    source_binding = envelope(OBJ["source_binding"], "source-catalog-binding")
    source_binding.update(
        {
            "candidate_binding": {
                "assigned_kind": "SOURCE_VECTOR_CATALOG",
                "assigned_id": CATALOG_ID,
                "assigned_version": "0.1",
                "repository_root_path": catalog_path,
                "semantic_json_content_sha256": sem(accepted_catalog),
                "raw_file_bytes_sha256": raw_sha(ACCEPTED / "examples/accord-02c-settlement-test-vectors.json"),
                "declared_integrity_class": "SEMANTIC_JSON_CONTENT",
                "declared_canonicalization": "RFC8785_JCS",
                "declared_algorithm": "SHA-256",
                "identity_assignment": "PACKAGE_BINDING_NOT_HISTORICAL_SELF_ASSERTION",
            },
            "accepted_binding_ref": tref("CONTRACT", OBJ["bindings"]),
            "object_registry_ref": tref("REGISTRY", OBJ["registry"]),
            "integrity_mode_vocabulary_ref": tref("CONTRACT", OBJ["integrity_modes"]),
            "field_vocabulary_mapping": {
                "declared_integrity_class": "mode",
                "declared_canonicalization": "canonicalization",
                "declared_algorithm": "algorithm",
            },
        }
    )
    put("source-catalog-binding.json", source_binding)

    # --------------------------------------------------------- canonicalization
    canon = envelope(OBJ["canon"], "canonicalization-profile")
    canon.update(copy.deepcopy(authority["canonicalization_requirements"]))
    put("canonicalization-profile.json", canon)

    # ------------------------------------------------------------ partial policy
    partial = envelope(OBJ["partial"], "partial-effect-policy")
    partial.update(
        {
            "stage_authority_ref": tref("AUTHORITY", OBJ["authority"]),
            "same_effect_required": True,
            "direct_predecessor_required": True,
            "decisions": {
                "VALID_SUPPORTED_DIRECT_PREDECESSOR": "PARTIAL_EFFECT",
                "TARGET_ALREADY_SUPPORTED": "NOT_PARTIAL_EFFECT",
                "NO_PREDECESSOR": "UNKNOWN",
                "WRONG_EFFECT": "REJECT",
                "UNSUPPORTED_TUPLE": "REJECT",
                "UNKNOWN_TUPLE_OR_WRONG_STAGE": "REJECT",
                "SELF_EDGE": "REJECT",
                "CYCLE": "REJECT",
                "DANGLING_TARGET": "REJECT",
                "INCOMPATIBLE_EVIDENCE": "UNKNOWN",
                "INADMISSIBLE_EVIDENCE": "UNKNOWN",
            },
        }
    )
    put("partial-effect-policy.json", partial)

    # ------------------------------------------------------ normative inputs
    negative_policy = {
        "allowed_consistency_levels": ["SNAPSHOT_COMPLETE", "LINEARIZABLE_COMPLETE"],
        "allowed_source_classes": [
            "COMPLETE_NEGATIVE_LEDGER_QUERY",
            "COMPLETE_NEGATIVE_AUTHORITATIVE_SNAPSHOT",
        ],
        "freshness_max_age_seconds": 300,
        "minimum_retention_seconds": 86400,
        "future_observation_result": "UNKNOWN",
        "stale_result": "STALE_EVIDENCE",
        "contradiction_rule": "FORBID_ADMISSIBLE_SAME_TARGET_POSITIVE",
        "complete_read_requirement": "COMPLETE_LEDGER_QUERY_REQUIRED",
    }
    reason_surface = sorted(
        {code for v in accepted_catalog["vectors"] for code in v["expected"].get("reason_codes", [])}
    )
    must_not_surface = sorted(
        {code for v in accepted_catalog["vectors"] for code in v["expected"].get("must_not_conclude", [])}
    )
    inputs = envelope(OBJ["inputs"], "normative-inputs")
    inputs.update(
        {
            "predicate_policy": {
                "global_stage_order": "FORBIDDEN",
                "implicit_transitivity": "FORBIDDEN",
            },
            "rule_dependencies": [
                {"rule_id": rule_id, "depends_on": dict(DEPENDENT_RULES).get(rule_id, [])}
                for rule_id in [row[0] for row in RULE_ROWS]
            ],
            "dependency_edges": [
                {"from": src, "to": dep} for src, deps in DEPENDENT_RULES for dep in deps
            ],
            "vector_expectations": [
                {"vector_id": v["vector_id"], "expected": v["expected"]} for v in accepted_catalog["vectors"]
            ],
            "propositions": {
                "collection_proposition_id": f"{NS}:proposition-collection:accepted-settlement-vectors",
                "projection_proposition_id": f"{NS}:proposition:vector-expectation-map",
            },
            "profile": {"negative_policy": negative_policy, "object_version": VERSION},
            "source_catalog_binding_ref": tref("CONTRACT", OBJ["source_binding"]),
            "negative_requirement_map_ref": tref("CONTRACT", OBJ["v013_gov"]),
            "proposition_inventory_ref": tref("CONTRACT", OBJ["propositions"]),
            "internal_design_values": copy.deepcopy(INTERNAL_DESIGN_VALUES),
            "reason_code_surface": reason_surface,
            "must_not_conclude_surface": must_not_surface,
            "accepted_base_package_ref": tref("PACKAGE", PKG_ID, "0.1"),
            "accepted_base_package_semantic_sha256": sem(accepted_package),
        }
    )
    put("normative-inputs.json", inputs)

    # ---------------------------------------------------------------- reference
    reference = envelope(OBJ["references"], "reference-model")
    reference.update(
        {
            "mechanism": "SHAPE_PREDICATE",
            "discovery_scope": {"registry_status": "ACTIVE", "classification": "NORMATIVE"},
            "shape_predicate": {
                "required_keys": ["kind", "id", "version"],
                "optional_keys": ["member_id"],
                "additional_keys": "DISQUALIFY",
                "all_values_type": "STRING",
            },
            "edge_identity": [
                "source_kind", "source_id", "source_version", "source_pointer",
                "target_kind", "target_id", "target_version", "member_id_or_empty",
            ],
            "deduplication": "SET_BY_EDGE_IDENTITY",
            "resolution_cardinality": "EXACTLY_ONE",
        }
    )
    put("reference-model.json", reference)

    # -------------------------------------------------------- V013 V013 target
    target = envelope(OBJ["target"], "v013-target")
    target.update(
        {
            "candidate_proposition_id": f"{NS}:proposition:v013-complete-negative-evidence",
            "effect_id": "urn:accord:02c:effect:E13",
            "negated_predicate_id": "urn:accord:02c:predicate:complete-negative",
            "negated_stage": "effect",
            "scope": {
                "resource": "NOT_APPLICABLE",
                "action": "NOT_APPLICABLE",
                "recipient_or_counterparty": "NOT_APPLICABLE",
                "provider": "NOT_APPLICABLE",
            },
            "required_interval": {
                "not_before": "2024-01-01T00:00:00Z",
                "as_of": "2024-01-01T00:00:01Z",
            },
            "settlement_profile_ref": tref("NORMATIVE_INPUTS", OBJ["inputs"]),
            "source_vector_ref": tref(
                "SOURCE_VECTOR_CATALOG", CATALOG_ID, "0.1",
                member_id="ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE",
            ),
            "relationship": "CANDIDATE_FIXTURE_OF_SAME_SEMANTIC_CLASS_AS_ACCEPTED_V013",
            "relationship_basis": {
                "accepted": [
                    {"field_id": "effect_identity", "accepted_pointer": "/input/target/effect_id",
                     "must_equal": "urn:accord:02c:effect:E13"},
                    {"field_id": "complete_negative_query_flag",
                     "accepted_pointer": "/input/negative_query/complete_state_space", "must_equal": True},
                    {"field_id": "interval_bound_flag",
                     "accepted_pointer": "/input/negative_query/interval_bound", "must_equal": True},
                    {"field_id": "retention_declared_flag",
                     "accepted_pointer": "/input/negative_query/retention_declared", "must_equal": True},
                    {"field_id": "fresh_at_verification_flag",
                     "accepted_pointer": "/input/negative_query/fresh_at_verification", "must_equal": True},
                    {"field_id": "accepted_overall_result",
                     "accepted_pointer": "/expected/overall", "must_equal": "NON_OCCURRENCE_SUPPORTED"},
                    {"field_id": "accepted_reason_code",
                     "accepted_pointer": "/expected/reason_codes/*", "must_contain":
                         "COMPLETE_NEGATIVE_LEDGER_SCOPE_ACCEPTED"},
                ],
                "candidate_supplied": [
                    {"field_id": "negated_predicate", "candidate_pointer": "/negated_predicate_id",
                     "provenance": "CANDIDATE_LOCAL_NOT_HISTORY"},
                    {"field_id": "negated_stage", "candidate_pointer": "/negated_stage",
                     "provenance": "CANDIDATE_LOCAL_NOT_HISTORY"},
                    {"field_id": "exact_interval", "candidate_pointer": "/required_interval",
                     "provenance": "CANDIDATE_LOCAL_NOT_HISTORY"},
                    {"field_id": "canonical_scope", "candidate_pointer": "/scope",
                     "provenance": "CANDIDATE_LOCAL_NOT_HISTORY"},
                ],
            },
        }
    )
    put("v013-target.json", target)

    # --------------------------------------------------------------- evidence
    evidence = envelope(OBJ["evidence"], "v013-evidence")
    scope = {
        "resource": "NOT_APPLICABLE",
        "action": "NOT_APPLICABLE",
        "recipient_or_counterparty": "NOT_APPLICABLE",
        "provider": "NOT_APPLICABLE",
    }
    evidence.update(
        {
            "fixture_status": "SYNTHETIC_CANDIDATE_0_2_NOT_ACCEPTED_HISTORY",
            "source_accepted_evidence_id": "urn:accord:02c:evidence:EV13",
            "evidence_id": "urn:moirae:accord-02r5:synthetic-evidence:v013",
            "effect_id": "urn:accord:02c:effect:E13",
            "predicate_id": "urn:accord:02c:predicate:complete-negative",
            "stage": "effect",
            "scope": copy.deepcopy(scope),
            "observed_interval": {
                "not_before": "2024-01-01T00:00:00Z",
                "as_of": "2024-01-01T00:00:01Z",
            },
            "retention_window_seconds": 86400,
            "consistency_level": "SNAPSHOT_COMPLETE",
            "read_semantics": "COMPLETE_LEDGER_QUERY",
            "read_scope_complete": True,
            "observed_at": "2024-01-01T00:00:01Z",
            "verification_time": "2024-01-01T00:01:01Z",
            "evidence_class": "COMPLETE_NEGATIVE_LEDGER_QUERY",
            "evidence_universe": [
                {
                    "evidence_id": "E-IRRELEVANT-POSITIVE-DIFFERENT-EFFECT",
                    "effect_id": "urn:accord:02c:effect:IRRELEVANT",
                    "predicate_id": "urn:accord:02c:predicate:complete-negative",
                    "stage": "effect",
                    "scope": copy.deepcopy(scope),
                    "polarity": "POSITIVE",
                    "relationship": "DIFFERENT_TARGET",
                    "admissible": True,
                    "observed_interval": {
                        "not_before": "2024-01-01T00:00:00Z",
                        "as_of": "2024-01-01T00:00:01Z",
                    },
                    "consistency_level": "SNAPSHOT_COMPLETE",
                    "source_class": "COMPLETE_NEGATIVE_LEDGER_QUERY",
                },
                {
                    "evidence_id": "E-INADMISSIBLE-POSITIVE-SAME-TARGET",
                    "effect_id": "urn:accord:02c:effect:E13",
                    "predicate_id": "urn:accord:02c:predicate:complete-negative",
                    "stage": "effect",
                    "scope": copy.deepcopy(scope),
                    "polarity": "POSITIVE",
                    "relationship": "SAME_TARGET",
                    "admissible": False,
                    "observed_interval": {
                        "not_before": "2024-01-01T00:00:00Z",
                        "as_of": "2024-01-01T00:00:01Z",
                    },
                    "consistency_level": "SNAPSHOT_COMPLETE",
                    "source_class": "COMPLETE_NEGATIVE_LEDGER_QUERY",
                },
            ],
        }
    )
    put("v013-evidence.json", evidence)

    # -------------------------------------------------------- V013 governance
    requirement_map = [
        ("TARGET_EFFECT_EQUAL", ["target.effect_id", "evidence.effect_id"], "TARGET_CONTRACT",
         "EXACT_EQUAL", "NEGATIVE_EFFECT_MISMATCH"),
        ("TARGET_PREDICATE_EQUAL", ["target.negated_predicate_id", "evidence.predicate_id"],
         "TARGET_CONTRACT", "EXACT_EQUAL", "NEGATIVE_PREDICATE_MISMATCH"),
        ("TARGET_STAGE_EQUAL", ["target.negated_stage", "evidence.stage"], "TARGET_CONTRACT",
         "EXACT_EQUAL", "NEGATIVE_STAGE_MISMATCH"),
        ("TARGET_SCOPE_EQUAL", ["target.scope", "evidence.scope"], "TARGET_CONTRACT",
         "TUPLE_EQUAL", "NEGATIVE_SCOPE_MISMATCH"),
        ("INTERVAL_VALID", ["evidence.observed_interval.not_before",
                            "evidence.observed_interval.as_of"], "EVIDENCE_CONTRACT",
         "RFC3339_ORDER_INCLUSIVE", "NEGATIVE_INTERVAL_INVALID"),
        ("INTERVAL_COVERS_TARGET", ["target.required_interval", "evidence.observed_interval"],
         "TARGET_CONTRACT", "INTERVAL_COVERAGE_INCLUSIVE_BOTH_ENDS", "NEGATIVE_INTERVAL_INSUFFICIENT"),
        ("RETENTION_MEETS_BOUND", ["evidence.retention_window_seconds",
                                   "target.required_interval",
                                   "profile.negative_policy.minimum_retention_seconds"],
         "SETTLEMENT_NEGATIVE_POLICY", "RETENTION_GTE_MAX_SPAN_AND_PROFILE_MIN",
         "NEGATIVE_RETENTION_INSUFFICIENT"),
        ("CONSISTENCY_ALLOWED", ["evidence.consistency_level",
                                 "profile.negative_policy.allowed_consistency_levels"],
         "SETTLEMENT_NEGATIVE_POLICY", "MEMBERSHIP", "NEGATIVE_CONSISTENCY_DISALLOWED"),
        ("SOURCE_CLASS_ALLOWED", ["evidence.evidence_class",
                                  "profile.negative_policy.allowed_source_classes"],
         "SETTLEMENT_NEGATIVE_POLICY", "MEMBERSHIP", "NEGATIVE_SOURCE_CLASS_DISALLOWED"),
        ("FRESHNESS_BOUND", ["evidence.observed_at", "evidence.verification_time",
                             "profile.negative_policy.freshness_max_age_seconds"],
         "SETTLEMENT_NEGATIVE_POLICY", "AGE_WITHIN_PROFILE_MAX", "NEGATIVE_FRESHNESS_FAILED"),
        ("READ_COMPLETE", ["evidence.read_scope_complete", "evidence.read_semantics",
                           "profile.negative_policy.complete_read_requirement"],
         "SETTLEMENT_NEGATIVE_POLICY", "COMPLETE_READ_REQUIRED", "NEGATIVE_READ_INCOMPLETE"),
        ("NO_SAME_TARGET_POSITIVE", ["evidence.evidence_universe", "target.effect_id",
                                     "target.negated_predicate_id", "target.negated_stage",
                                     "target.scope", "profile.negative_policy.contradiction_rule"],
         "SETTLEMENT_NEGATIVE_POLICY", "ADMISSIBLE_POSITIVE_SAME_TARGET_COUNT_ZERO",
         "NEGATIVE_CONTRADICTION"),
        ("FUTURE_OBSERVATION_BOUND", ["evidence.observed_at", "evidence.verification_time",
                                      "profile.negative_policy.future_observation_result"],
         "SETTLEMENT_NEGATIVE_POLICY", "OBSERVATION_NOT_IN_FUTURE", "NEGATIVE_FUTURE_OBSERVATION"),
        ("STALE_RESULT_BOUND", ["evidence.observed_at", "evidence.verification_time",
                                "profile.negative_policy.freshness_max_age_seconds",
                                "profile.negative_policy.stale_result"],
         "SETTLEMENT_NEGATIVE_POLICY", "OBSERVATION_NOT_STALE", "NEGATIVE_STALE_EVIDENCE"),
        ("EVIDENCE_UNIVERSE_TYPED", ["evidence.evidence_universe"], "EVIDENCE_CONTRACT",
         "UNIVERSE_ITEMS_TYPED_CLOSED", "NEGATIVE_UNIVERSE_UNTYPED"),
        ("FORBID_CALLER_SUPPLIED_CONTRADICTION_COUNT", ["target", "evidence"], "TARGET_CONTRACT",
         "CALLER_SUPPLIED_COUNT_FORBIDDEN", "NEGATIVE_CALLER_SUPPLIED_COUNT_FORBIDDEN"),
    ]
    v013_gov = envelope(OBJ["v013_gov"], "v013-governance")
    v013_gov.update(
        {
            "fixture_status": "NORMATIVE_CANDIDATE_0_2",
            "accepted_v013_locator": {
                "source_ref": tref("SOURCE_VECTOR_CATALOG", CATALOG_ID, "0.1",
                                   member_id="ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE"),
                "accepted_member_id": "ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE",
            },
            "relationship_vocabulary": [
                "CANDIDATE_FIXTURE_OF_SAME_SEMANTIC_CLASS_AS_ACCEPTED_V013"
            ],
            "relationship_basis_schema": {
                "accepted_pointer_prefix": "/",
                "candidate_pointer_prefix": "/",
                "require_accepted_value_match": True,
                "forbid_candidate_history_claim": True,
                "forbidden_overlaps": [],
                "overlap_policy": "ACCEPTED_AND_CANDIDATE_SUPPLIED_FIELD_SETS_MUST_BE_DISJOINT",
            },
            "authority_roots": {
                "SETTLEMENT_NEGATIVE_POLICY": "inputs:/profile/negative_policy",
                "TARGET_CONTRACT": "target",
                "EVIDENCE_CONTRACT": "evidence",
            },
            "result_vocabulary": ["NON_OCCURRENCE_SUPPORTED", "UNKNOWN", "STALE_EVIDENCE"],
            "requirement_map": {
                "required_requirement_ids": [row[0] for row in requirement_map],
                "requirements": [
                    {
                        "requirement_id": rid,
                        "source_fields": fields,
                        "governing_authority": authority_root,
                        "procedure": procedure,
                        "failure_code": failure,
                    }
                    for rid, fields, authority_root, procedure, failure in requirement_map
                ],
                "evaluation_order": [row[0] for row in requirement_map],
                "forbidden_requirements": ["caller_supplied_contradiction_count"],
            },
            "policy_field_roles": {
                "minimum_retention_seconds": "COMPUTED:RETENTION_MEETS_BOUND",
                "freshness_max_age_seconds": "COMPUTED:FRESHNESS_BOUND",
                "future_observation_result": "COMPUTED:FUTURE_OBSERVATION_BOUND",
                "stale_result": "COMPUTED:STALE_RESULT_BOUND",
                "contradiction_rule": "COMPUTED:NO_SAME_TARGET_POSITIVE",
                "allowed_consistency_levels": "COMPUTED:CONSISTENCY_ALLOWED",
                "allowed_source_classes": "COMPUTED:SOURCE_CLASS_ALLOWED",
                "complete_read_requirement": "COMPUTED:READ_COMPLETE",
            },
            "pass_result": "NON_OCCURRENCE_SUPPORTED",
            "fail_result": "UNKNOWN",
        }
    )
    put("v013-governance.json", v013_gov)

    # ------------------------------------------------------------ propositions
    collection_id = f"{NS}:proposition-collection:accepted-settlement-vectors"
    projection_id = f"{NS}:proposition:vector-expectation-map"
    propositions = envelope(OBJ["propositions"], "proposition-inventory")
    propositions.update(
        {
            "derived_from": {
                "vector_expectations_pointer": "inputs:/vector_expectations/*",
                "accepted_catalog_ref": tref("SOURCE_VECTOR_CATALOG", CATALOG_ID, "0.1"),
            },
            "collection_propositions": [
                {
                    "proposition_id": collection_id,
                    "kind": "COLLECTION",
                    "normative": True,
                    "member_pointer": "inputs:/vector_expectations/*/vector_id",
                    "derived_from": "inputs:/vector_expectations",
                }
            ],
            "member_propositions": [
                {
                    "proposition_id": row["vector_id"],
                    "kind": "MEMBER",
                    "normative": True,
                    "member_of": collection_id,
                    "derived_from": "inputs:/vector_expectations/*/vector_id",
                }
                for row in inputs["vector_expectations"]
            ],
            "projection_propositions": [
                {
                    "proposition_id": projection_id,
                    "kind": "PROJECTION",
                    "normative": True,
                    "collection_proposition_id": collection_id,
                    "projection": {
                        "source": "inputs:/vector_expectations/*",
                        "key": "vector_id",
                        "value": "expected",
                    },
                }
            ],
            "informational": [],
        }
    )
    put("proposition-inventory.json", propositions)

    # -------------------------------------------------- external input contract
    ext = envelope(OBJ["ext_contract"], "external-verification-input-contract")
    ext.update(
        {
            "input_type": "EXTERNAL_VERIFICATION_INPUT",
            "registry_membership": "FORBIDDEN_NOT_A_PACKAGE_OBJECT",
            "candidate_self_assertion": "FORBIDDEN",
            "fields": {
                "package_id": {"required": True, "source": "CALLER_SUPPLIED"},
                "package_version": {"required": True, "source": "CALLER_SUPPLIED"},
                "package_digest": {
                    "required": True,
                    "source": "CALLER_SUPPLIED",
                    "meaning": "RECOMPUTED_CANDIDATE_SEMANTIC_IDENTITY",
                },
                "trust_root": {
                    "required": True,
                    "fields": {
                        "root_id": {"required": True},
                        "root_kind": {
                            "required": True,
                            "allowed": ["PINNED_ACCEPTED_TRUST_ROOT", "REPLACED_TRUST_ROOT"],
                        },
                        "root_digest": {"required": False},
                    },
                },
            },
            "candidate_identity_recomputation": {
                "target": "PACKAGE_EXCLUDING_SELF_DIGEST",
                "canonicalization": "RFC8785_JCS",
                "algorithm": "SHA-256",
            },
            "results": {
                "PASS": {
                    "condition": "external identity == recomputed candidate identity AND root_kind == PINNED_ACCEPTED_TRUST_ROOT"
                },
                "FAIL": {
                    "conditions": [
                        "MISSING_EXTERNAL_TRUST_INPUT",
                        "TRUSTED_IDENTITY_MISMATCH",
                        "FOREIGN_PACKAGE_IDENTITY",
                    ]
                },
                "DIFFERENT_PACKAGE_VERIFIED": {
                    "sub_status": "OUT_OF_SCOPE_TRUST_ROOT_REPLACEMENT",
                    "condition": "root_kind == REPLACED_TRUST_ROOT",
                },
            },
            "cli": {
                "--expected-package-id": "package_id",
                "--expected-package-version": "package_version",
                "--expected-package-digest": "package_digest",
                "--verification-input": "PATH_TO_EXTERNAL_JSON_INPUT",
            },
        }
    )
    put("external-verification-input.contract.json", ext)

    # ------------------------------------------------------- procedures/invariants
    procedure_specs = build_procedure_specs()
    invariant_specs = build_invariant_specs(procedure_specs)
    required_invariant_ids = [spec["invariant_id"] for spec in invariant_specs]

    procedures = envelope(OBJ["procedures"], "procedure-registry")
    procedures["procedures"] = []
    for spec in procedure_specs:
        procedures["procedures"].append(
            {
                "procedure_id": spec["procedure_id"],
                "arguments": [
                    {"name": name, "kind": kind, "required": True, "cardinality": "ONE"}
                    for name, kind in spec["arguments"]
                ],
                "derivation": spec["derivation"],
                "result": {"type": "BOOLEAN", "status": ["PASS", "FAIL"], "witness_required": True},
                "missing_behavior": "FAIL_CLOSED",
                "ambiguity_behavior": "FAIL_CLOSED",
                "fail_closed": True,
            }
        )
    put("procedure-registry.json", procedures)

    invariants = envelope(OBJ["invariants"], "invariant-registry")
    invariants["invariants"] = invariant_specs
    put("invariant-registry.json", invariants)

    # -------------------------------------------------------------- rule registry
    rules = envelope(OBJ["rules"], "rule-registry")
    rules["provenance"] = {
        "source_revision": SOURCE_REVISION["revision"],
        "source_commit": SOURCE_REVISION["commit"],
        "source_tree": SOURCE_REVISION["tree"],
        "source_rule_registry_semantic_sha256": SOURCE_REVISION["rule_registry_semantic_sha256"],
        "required_rule_ids": [row[0] for row in RULE_ROWS],
        "required_rule_inventory_hash": sem([row[0] for row in RULE_ROWS]),
    }
    rules["rules"] = []
    for row_values in RULE_ROWS:
        rule_id, cls, family, failure_code = row_values[:4]
        extra = row_values[4] if len(row_values) > 4 else None
        row = {
            "rule_id": rule_id,
            "declared_class": {
                "R": "EXECUTABLE_CONFORMANCE_RULE",
                "D": "DEFERRED_NO_SUBJECT_ARTIFACT",
                "I": "INTERNAL_DESIGN_INVARIANT",
            }[cls],
            "inherited_family": family,
            "inherited_failure_code": failure_code,
            "provenance_source_revision": SOURCE_REVISION["revision"],
            "provenance_source_commit": SOURCE_REVISION["commit"],
        }
        if cls == "R":
            inv = RULE_INVARIANT[rule_id]
            spec = next(s for s in invariant_specs if s["invariant_id"] == inv)
            row["invariant_binding"] = {"invariant_id": inv,
                                        "arguments": copy.deepcopy(spec["default_arguments"])}
        elif cls == "I":
            row["internal_check"] = {
                "procedure": "JSON_POINTER_COMPARE",
                "subject": tref("NORMATIVE_INPUTS", OBJ["inputs"]),
                "pointer": "/internal_design_values/" + rule_id,
                "comparison": "EXACT_EQUAL",
                "expected": extra,
                "conformance_excluded": True,
            }
        else:
            row["missing_subject_roles"] = extra[0]
            row["later_lifecycle_stage"] = extra[1]
            row["deferred_reason"] = (
                "The package defines the contract but contains no concrete lifecycle "
                "subject artifact; inventing bytes would be non-conformant."
            )
        rules["rules"].append(row)
    put("rule-registry.json", rules)

    # ---------------------------------------------------------------- registry
    file_map = {
        "authority-requirements.json": ("AUTHORITY", OBJ["authority"], "authority-requirements"),
        "governance-requirements.json": ("CONTRACT", OBJ["governance"], "governance-requirements"),
        "integrity-modes.json": ("CONTRACT", OBJ["integrity_modes"], "integrity-modes"),
        "semantic-key-authority.json": ("CONTRACT", OBJ["semantic_keys"], "semantic-key-authority"),
        "normative-inputs.json": ("NORMATIVE_INPUTS", OBJ["inputs"], "normative-inputs"),
        "partial-effect-policy.json": ("POLICY", OBJ["partial"], "partial-effect-policy"),
        "v013-target.json": ("CONTRACT", OBJ["target"], "v013-target"),
        "v013-evidence.json": ("EVIDENCE", OBJ["evidence"], "v013-evidence"),
        "v013-governance.json": ("CONTRACT", OBJ["v013_gov"], "v013-governance"),
        "proposition-inventory.json": ("CONTRACT", OBJ["propositions"], "proposition-inventory"),
        "source-catalog-binding.json": ("CONTRACT", OBJ["source_binding"], "source-catalog-binding"),
        "rule-registry.json": ("REGISTRY", OBJ["rules"], "rule-registry"),
        "invariant-registry.json": ("REGISTRY", OBJ["invariants"], "invariant-registry"),
        "procedure-registry.json": ("REGISTRY", OBJ["procedures"], "procedure-registry"),
        "reference-model.json": ("CONTRACT", OBJ["references"], "reference-model"),
        "accepted-source-bindings.json": ("CONTRACT", OBJ["bindings"], "accepted-source-bindings"),
        "canonicalization-profile.json": ("CANONICALIZATION", OBJ["canon"], "canonicalization-profile"),
        "external-verification-input.contract.json": (
            "CONTRACT", OBJ["ext_contract"], "external-verification-input-contract"),
    }
    objects = []
    for filename, (kind, object_id, schema_name) in file_map.items():
        objects.append(
            {
                "kind": kind,
                "id": object_id,
                "version": VERSION,
                "path": f"{REL}/{filename}",
                "status": "ACTIVE",
                "roles": ["NORMATIVE"],
                "classification": "NORMATIVE",
                "schema_ref": tref("SCHEMA", SCHEMA_IDS[schema_name]),
                "integrity": {
                    "mode": "SEMANTIC_JSON_CONTENT",
                    "algorithm": "SHA-256",
                    "serialization": "RFC8785_JCS",
                    "digest": sem(artifacts[filename]),
                },
            }
        )
    for name in SCHEMA_NAMES:
        objects.append(
            {
                "kind": "SCHEMA",
                "id": SCHEMA_IDS[name],
                "version": VERSION,
                "path": f"{REL}/schema/{name}.schema.json",
                "status": "ACTIVE",
                "roles": ["SCHEMA_AUTHORITY"],
                "classification": "NORMATIVE",
                "integrity": {
                    "mode": "SEMANTIC_JSON_CONTENT",
                    "algorithm": "SHA-256",
                    "serialization": "RFC8785_JCS",
                    "digest": None,  # filled by the caller after schema materialisation
                },
            }
        )
    for source in accepted_bindings["sources"]:
        objects.append(
            {
                "kind": source["ref"]["kind"],
                "id": source["ref"]["id"],
                "version": source["ref"]["version"],
                "path": source["path"],
                "status": "ACTIVE_ACCEPTED_SOURCE",
                "roles": source["roles"],
                "classification": "PROVENANCE",
                "integrity": {
                    "mode": "DUAL_ACCEPTED_SOURCE",
                    "binding_ref": tref("CONTRACT", OBJ["bindings"]),
                },
                "members": (
                    [v["vector_id"] for v in accepted_catalog["vectors"]]
                    if source["ref"]["kind"] == "SOURCE_VECTOR_CATALOG"
                    else []
                ),
            }
        )
    objects.append(
        {
            "kind": "REGISTRY",
            "id": OBJ["registry"],
            "version": VERSION,
            "path": f"{REL}/object-registry.json",
            "status": "ACTIVE",
            "roles": ["NORMATIVE", "IDENTITY_AUTHORITY"],
            "classification": "NORMATIVE",
            "schema_ref": tref("SCHEMA", SCHEMA_IDS["object-registry"]),
            "integrity": {
                "mode": "PACKAGE_PINNED_BOOTSTRAP",
                "justification": "Registry digest is pinned by the current package to avoid self-reference.",
            },
        }
    )
    objects.append(
        {
            "kind": "PACKAGE",
            "id": PKG_ID,
            "version": VERSION,
            "path": f"{REL}/specification-package-0.2.json",
            "status": "ACTIVE",
            "roles": ["CURRENT_CANDIDATE_PACKAGE", "NORMATIVE"],
            "classification": "NORMATIVE",
            "schema_ref": tref("SCHEMA", SCHEMA_IDS["specification-package"]),
            "integrity": {"mode": "SELF_DIGEST",
                          "content_target_ref": "PACKAGE_EXCLUDING_SELF_DIGEST"},
        }
    )
    registry = envelope(OBJ["registry"], "object-registry")
    registry.update(
        {
            "uniqueness_key": ["kind", "id", "version"],
            "role_model": "roles-array",
            "identity_fields": ["kind", "id", "version"],
            "status_vocabulary": ["ACTIVE", "ACTIVE_ACCEPTED_SOURCE", "RETIRED"],
            "classification_vocabulary": ["NORMATIVE", "PROVENANCE", "INFORMATIONAL"],
            "role_vocabulary": [
                "NORMATIVE", "IDENTITY_AUTHORITY", "SCHEMA_AUTHORITY",
                "NORMATIVE_BOUND_SOURCE", "CATALOG_BINDING", "VECTOR_SOURCE",
                "CURRENT_CANDIDATE_PACKAGE",
            ],
            "objects": objects,
        }
    )
    put("object-registry.json", registry)

    # ----------------------------------------------------------------- package
    package = envelope(PKG_ID, "specification-package")
    package.update(
        {
            "package_id": PKG_ID,
            "package_version": VERSION,
            "status": "CANDIDATE_UNACCEPTED",
            "accepted_base_ref": tref("PACKAGE", PKG_ID, "0.1"),
            "rejected_candidate_lineage": copy.deepcopy(REJECTED_LINEAGE),
            "object_registry_ref": tref("REGISTRY", OBJ["registry"]),
            "rule_registry_ref": tref("REGISTRY", OBJ["rules"]),
            "invariant_registry_ref": tref("REGISTRY", OBJ["invariants"]),
            "procedure_registry_ref": tref("REGISTRY", OBJ["procedures"]),
            "required_invariant_ids": required_invariant_ids,
            "required_rule_ids_ref": "rule-registry:/provenance/required_rule_ids",
            "trust_anchor_requirement_ref": tref("CONTRACT", OBJ["ext_contract"]),
            "runtime": {
                "python": "~=3.14.0",
                "requirements_path": f"{REL}/requirements.txt",
            },
            "current_candidate_integrity": {
                "class": "SEMANTIC_JSON_CONTENT",
                "content_target_ref": "PACKAGE_EXCLUDING_SELF_DIGEST",
                "algorithm": "SHA-256",
                "digest": None,
            },
        }
    )
    put("specification-package-0.2.json", package)

    return artifacts


def build_procedure_specs():
    """Procedure table: id -> (typed args, derivation).  Role pointers use
    ``role:/pointer`` so derivation role closure is mechanically checkable."""

    specs = []

    def add(procedure_id, arguments, derivation):
        specs.append({"procedure_id": procedure_id, "arguments": arguments, "derivation": derivation})

    add("SCHEMA_VALIDATION", [("registry", "REGISTRY"), ("reference_model", "CONTRACT")],
        {"operation": "VALIDATE_ACTIVE_UNIVERSE",
         "meta_validate_schemas": True, "validate_declared_instances": True,
         "universe_source": "registry:/objects/*", "model_source": "reference_model:/discovery_scope"})
    add("LINEAGE_VALIDATION", [("package", "PACKAGE"), ("authority", "AUTHORITY")],
        {"operation": "SECTION_ENTAILMENT",
         "comparisons": [
             {"left": "package:/package_id", "right": "authority:/package_requirements/family"},
             {"left": "package:/package_version", "right": "authority:/package_requirements/version"},
             {"left": "package:/status", "right": "authority:/package_requirements/status"}],
         "required_lineage_entry": "authority:/package_requirements/required_rejected_revision"})
    add("DUAL_INTEGRITY", [("bindings", "CONTRACT")],
        {"operation": "DIGEST_RECOMPUTE", "source_selector": "bindings:/sources/*",
         "semantic_serialization": "RFC8785_JCS", "raw_serialization": "RAW_BYTES",
         "algorithms": ["SHA-256"]})
    add("UNIQUE_KEY", [("registry", "REGISTRY")],
        {"operation": "UNIQUE_KEY", "source": "registry:/objects/*",
         "projection": "registry:/identity_fields"})
    add("REFERENCE_RESOLUTION", [("registry", "REGISTRY"), ("reference_model", "CONTRACT")],
        {"operation": "REFERENCE_RESOLUTION", "universe": "registry:/objects/*",
         "model": "reference_model:/shape_predicate", "scope": "reference_model:/discovery_scope",
         "edge_identity": "reference_model:/edge_identity",
         "cardinality": "reference_model:/resolution_cardinality"})
    add("DIGEST_RECOMPUTE", [("registry", "REGISTRY"), ("package", "PACKAGE"),
                             ("canonicalization", "CANONICALIZATION")],
        {"operation": "DIGEST_RECOMPUTE", "objects": "registry:/objects/*",
         "self_digest_contract": "canonicalization:/reduction",
         "package_integrity": "package:/current_candidate_integrity"})
    add("SET_EQUALITY", [("inputs", "NORMATIVE_INPUTS")],
        {"operation": "SET_EQUALITY",
         "left": {"source": "inputs:/rule_dependencies/*", "projection": ["rule_id", "depends_on/*"]},
         "right": {"source": "inputs:/dependency_edges/*", "projection": ["from", "to"]},
         "comparison": "SET_EQUAL"})
    add("EXPECTATION_STABILITY", [("inputs", "NORMATIVE_INPUTS"),
                                  ("accepted_vectors", "SOURCE_VECTOR_CATALOG")],
        {"operation": "SET_EQUALITY",
         "left": {"source": "inputs:/vector_expectations/*", "key": "vector_id", "value": "expected"},
         "right": {"source": "accepted_vectors:/vectors/*", "key": "vector_id", "value": "expected"},
         "comparison": "MAP_EQUAL"})
    add("PREDICATE_POLICY_AGREEMENT", [("inputs", "NORMATIVE_INPUTS"), ("authority", "AUTHORITY")],
        {"operation": "POLICY_AGREEMENT",
         "comparisons": [
             {"left": "inputs:/predicate_policy/global_stage_order",
              "right": "authority:/stage_policy_requirements/global_stage_order",
              "authorized_by": "authority:/stage_policy_authorization/global_stage_order"},
             {"left": "inputs:/predicate_policy/implicit_transitivity",
              "right": "authority:/stage_policy_requirements/implicit_transitivity",
              "authorized_by": "authority:/stage_policy_authorization/implicit_transitivity"}]})
    add("CANONICALIZATION_PROFILE_WELLFORMED", [("profile", "CANONICALIZATION"),
                                                ("authority", "AUTHORITY")],
        {"operation": "POLICY_AGREEMENT",
         "comparisons": [
             {"left": f"profile:/{key}",
              "right": f"authority:/canonicalization_requirements/{key}"}
             for key in ["standard", "serialization", "encoding", "algorithm", "target_id",
                         "selection", "reduction", "exclusion_pointers"]]})
    add("SOURCE_CATALOG_BINDING_MATCH", [("candidate_binding", "CONTRACT"),
                                         ("accepted_binding", "CONTRACT"),
                                         ("object_registry", "REGISTRY")],
        {"operation": "SOURCE_CATALOG_BINDING_MATCH",
         "candidate": "candidate_binding:/candidate_binding",
         "accepted_sources": "accepted_binding:/sources",
         "objects": "object_registry:/objects",
         "vocabulary_ref": tref("CONTRACT", OBJ["integrity_modes"]),
         "mapping_ref": "candidate_binding:/field_vocabulary_mapping"})
    add("PARTIAL_EFFECT_POLICY_CLOSURE", [("policy", "POLICY"), ("authority", "AUTHORITY")],
        {"operation": "POLICY_AGREEMENT",
         "comparisons": [
             {"left": "policy:/same_effect_required",
              "right": "authority:/partial_effect_requirements/same_effect_required"},
             {"left": "policy:/direct_predecessor_required",
              "right": "authority:/partial_effect_requirements/direct_predecessor_required"},
             {"left_dynamic": "policy:/decisions/{authority:/partial_effect_requirements/merged_decision_key}",
              "right": "authority:/partial_effect_requirements/merged_decision_value"}]})
    add("REQUIREMENT_MAP_EVAL", [("target", "CONTRACT"), ("evidence", "EVIDENCE"),
                                 ("inputs", "NORMATIVE_INPUTS")],
        {"operation": "REQUIREMENT_MAP_EVAL",
         "relationship_basis": "target:/relationship_basis",
         "policy": "inputs:/profile/negative_policy",
         "evidence_fields": "evidence:/evidence_id",
         "requirement_ref": tref("CONTRACT", OBJ["v013_gov"]),
         "pass_result": "NON_OCCURRENCE_SUPPORTED", "fail_result": "UNKNOWN"})
    add("AUTHORITY_COMPLETENESS", [("rules", "REGISTRY"), ("invariants", "REGISTRY"),
                                   ("procedures", "REGISTRY"), ("registry", "REGISTRY")],
        {"operation": "AUTHORITY_COMPLETENESS",
         "rule_rows": "rules:/rules/*", "invariant_rows": "invariants:/invariants/*",
         "procedure_rows": "procedures:/procedures/*", "objects": "registry:/objects/*",
         "requirements": ["BINDING_ROLE_EXACT", "REFERENCE_EXACTLY_ONE", "FAILURE_COMPATIBLE",
                          "DECLARED_CLASS_EQUALS_DERIVED", "NO_CONFORMANCE_SUBJECTS",
                          "EXACT_ACTIVE_INVARIANT_SET"]})
    add("PROPOSITION_INVENTORY_BOUND", [("inputs", "NORMATIVE_INPUTS"),
                                        ("inventory", "CONTRACT")],
        {"operation": "PROPOSITION_INVENTORY_BOUND",
         "vector_expectations": "inputs:/vector_expectations/*",
         "collection": "inventory:/collection_propositions/*",
         "projection": "inventory:/projection_propositions/*",
         "informational": "inventory:/informational/*"})
    add("PROFILE_REFERENCE_PINNING", [("inputs", "NORMATIVE_INPUTS"), ("authority", "AUTHORITY")],
        {"operation": "SECTION_ENTAILMENT",
         "required_pointer": "inputs:/profile/object_version",
         "governing_pointer": "authority:/package_requirements/version"})
    add("ARITY_AGREEMENT", [("invariants", "REGISTRY"), ("procedures", "REGISTRY")],
        {"operation": "ARITY_AGREEMENT",
         "invariant_roles": "invariants:/invariants/*/input_roles/*/role",
         "procedure_arguments": "procedures:/procedures/*/arguments/*/name"})
    add("SCHEMA_NON_VACUITY", [("registry", "REGISTRY")],
        {"operation": "SCHEMA_NON_VACUITY", "objects": "registry:/objects/*",
         "probe": {"zzz": 1}, "expected": "REJECT_ALL_ACTIVE_SCHEMAS"})
    add("CURRENT_PACKAGE_IDENTITY", [("registry", "REGISTRY"), ("package", "PACKAGE"),
                                     ("authority", "AUTHORITY")],
        {"operation": "CURRENT_PACKAGE_IDENTITY",
         "identity_from": "authority:/package_requirements",
         "objects": "registry:/objects/*", "package_pointer": "package:/package_id",
         "required_resolution_count": 1})
    add("SELF_DIGEST", [("package", "PACKAGE"), ("canonicalization", "CANONICALIZATION")],
        {"operation": "SELF_DIGEST",
         "target": "package:/current_candidate_integrity",
         "reduction": "canonicalization:/reduction",
         "exclusion": "canonicalization:/exclusion_pointers"})
    add("INTEGRITY_MODE_DISPATCH", [("registry", "REGISTRY"), ("package", "PACKAGE"),
                                    ("integrity_modes", "CONTRACT")],
        {"operation": "INTEGRITY_MODE_DISPATCH",
         "objects": "registry:/objects/*", "modes": "integrity_modes:/modes",
         "bootstrap_pin": "package:/registry_semantic_sha256"})
    add("V013_BASIS_VALID", [("target", "CONTRACT"), ("evidence", "EVIDENCE"),
                             ("accepted_vectors", "SOURCE_VECTOR_CATALOG"),
                             ("v013_governance", "CONTRACT")],
        {"operation": "V013_BASIS_VALID",
         "accepted_members": "accepted_vectors:/vectors/*",
         "relationship": "target:/relationship",
         "basis": "target:/relationship_basis",
         "locator": "v013_governance:/accepted_v013_locator",
         "relationship_vocabulary": "v013_governance:/relationship_vocabulary",
         "basis_schema": "v013_governance:/relationship_basis_schema",
         "candidate_evidence": "evidence:/evidence_id"})
    add("FAIL_CLOSED_ENFORCED", [("invariants", "REGISTRY"), ("governance", "CONTRACT")],
        {"operation": "FAIL_CLOSED_ENFORCED", "invariant_rows": "invariants:/invariants/*",
         "requirement": "governance:/fail_closed_requirement"})
    add("SUBJECT_ROLE_COVERAGE", [("invariants", "REGISTRY"), ("governance", "CONTRACT")],
        {"operation": "SUBJECT_ROLE_COVERAGE", "invariant_rows": "invariants:/invariants/*",
         "requirement": "governance:/subject_role_requirement"})
    add("DEFAULT_ARGUMENT_COVERAGE", [("invariants", "REGISTRY"), ("procedures", "REGISTRY"),
                                      ("registry", "REGISTRY")],
        {"operation": "DEFAULT_ARGUMENT_COVERAGE", "invariant_rows": "invariants:/invariants/*",
         "procedure_rows": "procedures:/procedures/*", "objects": "registry:/objects/*"})
    add("DERIVATION_ROLE_CLOSURE", [("invariants", "REGISTRY"), ("procedures", "REGISTRY")],
        {"operation": "DERIVATION_ROLE_CLOSURE", "invariant_rows": "invariants:/invariants/*",
         "procedure_rows": "procedures:/procedures/*"})
    add("PROCEDURE_OPERATION_SUPPORTED", [("procedures", "REGISTRY"), ("governance", "CONTRACT")],
        {"operation": "PROCEDURE_OPERATION_SUPPORTED", "procedure_rows": "procedures:/procedures/*",
         "supported": "governance:/supported_operations"})
    add("MISSING_BEHAVIOR_SUPPORTED", [("procedures", "REGISTRY"), ("governance", "CONTRACT")],
        {"operation": "MISSING_BEHAVIOR_SUPPORTED", "procedure_rows": "procedures:/procedures/*",
         "vocabulary": "governance:/behavior_vocabulary/missing_behavior"})
    add("AMBIGUITY_BEHAVIOR_SUPPORTED", [("procedures", "REGISTRY"), ("governance", "CONTRACT")],
        {"operation": "AMBIGUITY_BEHAVIOR_SUPPORTED", "procedure_rows": "procedures:/procedures/*",
         "vocabulary": "governance:/behavior_vocabulary/ambiguity_behavior"})
    add("REFERENCE_DISCOVERY_SCOPE_VALID", [("reference_model", "CONTRACT"), ("registry", "REGISTRY")],
        {"operation": "REFERENCE_DISCOVERY_SCOPE_VALID",
         "scope": "reference_model:/discovery_scope", "objects": "registry:/objects/*"})
    add("REFERENCE_SHAPE_PREDICATE_APPLIED", [("reference_model", "CONTRACT"),
                                              ("governance", "CONTRACT")],
        {"operation": "REFERENCE_SHAPE_PREDICATE_APPLIED",
         "shape": "reference_model:/shape_predicate",
         "requirement": "governance:/shape_predicate_requirement"})
    add("UNIQUENESS_KEY_APPLIED", [("registry", "REGISTRY"), ("governance", "CONTRACT")],
        {"operation": "UNIQUENESS_KEY_APPLIED", "uniqueness_key": "registry:/uniqueness_key",
         "identity_fields": "registry:/identity_fields", "objects": "registry:/objects/*",
         "requirement": "governance:/uniqueness_key_requirement"})
    add("ROLE_MODEL_APPLIED", [("registry", "REGISTRY"), ("governance", "CONTRACT")],
        {"operation": "ROLE_MODEL_APPLIED", "role_model": "registry:/role_model",
         "role_vocabulary": "registry:/role_vocabulary", "objects": "registry:/objects/*",
         "requirement": "governance:/role_model_requirement"})
    add("SCHEMA_IDENTITY_MATCHES_REGISTRY", [("registry", "REGISTRY")],
        {"operation": "SCHEMA_IDENTITY_MATCHES_REGISTRY", "objects": "registry:/objects/*"})
    add("RULE_COVERAGE_EXACT", [("rules", "REGISTRY")],
        {"operation": "RULE_COVERAGE_EXACT", "rule_rows": "rules:/rules/*",
         "required": "rules:/provenance/required_rule_ids"})
    add("INVARIANT_SET_EXACT", [("package", "PACKAGE"), ("invariants", "REGISTRY")],
        {"operation": "INVARIANT_SET_EXACT", "required": "package:/required_invariant_ids",
         "invariant_rows": "invariants:/invariants/*"})
    add("GOVERNING_AUTHORITY_REFERENCE_VALID",
        [("v013_governance", "CONTRACT"), ("authority", "AUTHORITY"),
         ("integrity_modes", "CONTRACT")],
        {"operation": "GOVERNING_AUTHORITY_REFERENCE_VALID",
         "authority_roots": "v013_governance:/authority_roots",
         "requirements": "v013_governance:/requirement_map/requirements/*",
         "package_requirements": "authority:/package_requirements",
         "modes": "integrity_modes:/modes"})
    add("GOVERNING_TOKEN_SINGLETON", [("semantic_keys", "CONTRACT"), ("registry", "REGISTRY")],
        {"operation": "GOVERNING_TOKEN_SINGLETON", "semantic_keys": "semantic_keys:/semantic_keys/*",
         "objects": "registry:/objects/*",
         "policy": "semantic_keys:/governing_token_singleton"})
    add("TRUST_ANCHOR_COMPARE", [("package", "PACKAGE")],
        {"operation": "TRUST_ANCHOR_COMPARE", "package_identity": "package:/package_id",
         "package_integrity": "package:/current_candidate_integrity"})
    return specs


PACKAGE_INVARIANT_TABLE = [
    # invariant_id, procedure_id, usage, roles, subject_role
    ("STANDARDS_VALIDATION", "SCHEMA_VALIDATION", "CONFORMANCE_BOUND", ["registry", "reference_model"], "registry"),
    ("PACKAGE_LINEAGE", "LINEAGE_VALIDATION", "CONFORMANCE_BOUND", ["package", "authority"], "package"),
    ("ACCEPTED_BASE_DUAL_INTEGRITY", "DUAL_INTEGRITY", "PACKAGE_ONLY_REQUIRED", ["bindings"], "bindings"),
    ("OBJECT_IDENTITY_UNIQUE", "UNIQUE_KEY", "CONFORMANCE_BOUND", ["registry"], "registry"),
    ("TYPED_REFERENCE_CLOSURE", "REFERENCE_RESOLUTION", "CONFORMANCE_BOUND", ["registry", "reference_model"], "registry"),
    ("SEMANTIC_DIGEST_VERIFY", "DIGEST_RECOMPUTE", "CONFORMANCE_BOUND", ["registry", "package", "canonicalization"], "registry"),
    ("ACCEPTED_SOURCE_DUAL_INTEGRITY", "DUAL_INTEGRITY", "CONFORMANCE_BOUND", ["bindings"], "bindings"),
    ("DEPENDENCY_GRAPH_EQUAL", "SET_EQUALITY", "CONFORMANCE_BOUND", ["inputs"], "inputs"),
    ("EXPECTATION_STABILITY", "EXPECTATION_STABILITY", "CONFORMANCE_BOUND", ["inputs", "accepted_vectors"], "inputs"),
    ("PREDICATE_AUTHORITY_CLOSURE", "PREDICATE_POLICY_AGREEMENT", "CONFORMANCE_BOUND", ["inputs", "authority"], "inputs"),
    ("CANONICALIZATION_AUTHORITY_CLOSURE", "CANONICALIZATION_PROFILE_WELLFORMED", "CONFORMANCE_BOUND", ["profile", "authority"], "profile"),
    ("SOURCE_CATALOG_BINDING", "SOURCE_CATALOG_BINDING_MATCH", "CONFORMANCE_BOUND", ["candidate_binding", "accepted_binding", "object_registry"], "candidate_binding"),
    ("PARTIAL_EFFECT_POLICY_CLOSURE", "PARTIAL_EFFECT_POLICY_CLOSURE", "CONFORMANCE_BOUND", ["policy", "authority"], "policy"),
    ("NEGATIVE_REQUIREMENT_MAP_CLOSURE", "REQUIREMENT_MAP_EVAL", "CONFORMANCE_BOUND", ["target", "evidence", "inputs"], "target"),
    ("RULE_EXPECTATION_AUTHORITY_COMPLETE", "AUTHORITY_COMPLETENESS", "CONFORMANCE_BOUND", ["rules", "invariants", "procedures", "registry"], "rules"),
    ("PROPOSITION_INVENTORY_BOUND", "PROPOSITION_INVENTORY_BOUND", "CONFORMANCE_BOUND", ["inputs", "inventory"], "inventory"),
    ("PROFILE_REFERENCE_PINNING", "PROFILE_REFERENCE_PINNING", "CONFORMANCE_BOUND", ["inputs", "authority"], "inputs"),
    ("INVARIANT_PROCEDURE_ARITY_AGREEMENT", "ARITY_AGREEMENT", "PACKAGE_ONLY_REQUIRED", ["invariants", "procedures"], "invariants"),
    ("SCHEMA_NON_VACUITY", "SCHEMA_NON_VACUITY", "PACKAGE_ONLY_REQUIRED", ["registry"], "registry"),
    ("CURRENT_PACKAGE_IDENTITY", "CURRENT_PACKAGE_IDENTITY", "PACKAGE_ONLY_REQUIRED", ["registry", "package", "authority"], "registry"),
    ("PACKAGE_SELF_DIGEST", "SELF_DIGEST", "PACKAGE_ONLY_REQUIRED", ["package", "canonicalization"], "package"),
    ("INTEGRITY_MODE_DISPATCH", "INTEGRITY_MODE_DISPATCH", "PACKAGE_ONLY_REQUIRED", ["registry", "package", "integrity_modes"], "registry"),
    ("V013_BASIS_VALID", "V013_BASIS_VALID", "PACKAGE_ONLY_REQUIRED", ["target", "evidence", "accepted_vectors", "v013_governance"], "target"),
]

GOVERNANCE_INVARIANT_TABLE = [
    ("FAIL_CLOSED_ENFORCED", ["invariants", "governance"], "invariants"),
    ("SUBJECT_ROLE_COVERAGE", ["invariants", "governance"], "invariants"),
    ("DEFAULT_ARGUMENT_COVERAGE", ["invariants", "procedures", "registry"], "invariants"),
    ("DERIVATION_ROLE_CLOSURE", ["invariants", "procedures"], "invariants"),
    ("PROCEDURE_OPERATION_SUPPORTED", ["procedures", "governance"], "procedures"),
    ("MISSING_BEHAVIOR_SUPPORTED", ["procedures", "governance"], "procedures"),
    ("AMBIGUITY_BEHAVIOR_SUPPORTED", ["procedures", "governance"], "procedures"),
    ("REFERENCE_DISCOVERY_SCOPE_VALID", ["reference_model", "registry"], "reference_model"),
    ("REFERENCE_SHAPE_PREDICATE_APPLIED", ["reference_model", "governance"], "reference_model"),
    ("UNIQUENESS_KEY_APPLIED", ["registry", "governance"], "registry"),
    ("ROLE_MODEL_APPLIED", ["registry", "governance"], "registry"),
    ("SCHEMA_IDENTITY_MATCHES_REGISTRY", ["registry"], "registry"),
    ("RULE_COVERAGE_EXACT", ["rules"], "rules"),
    ("INVARIANT_SET_EXACT", ["package", "invariants"], "package"),
    ("GOVERNING_AUTHORITY_REFERENCE_VALID", ["v013_governance", "authority", "integrity_modes"], "v013_governance"),
    ("GOVERNING_TOKEN_SINGLETON", ["semantic_keys", "registry"], "semantic_keys"),
]

TRUST_INVARIANT_TABLE = [
    ("TRUSTED_PACKAGE_IDENTITY", ["package"], "package"),
]

ROLE_KIND = {
    "registry": "REGISTRY", "reference_model": "CONTRACT", "package": "PACKAGE",
    "authority": "AUTHORITY", "bindings": "CONTRACT", "inputs": "NORMATIVE_INPUTS",
    "accepted_vectors": "SOURCE_VECTOR_CATALOG", "profile": "CANONICALIZATION",
    "candidate_binding": "CONTRACT", "accepted_binding": "CONTRACT",
    "object_registry": "REGISTRY", "policy": "POLICY", "target": "CONTRACT",
    "evidence": "EVIDENCE", "rules": "REGISTRY", "invariants": "REGISTRY",
    "procedures": "REGISTRY", "inventory": "CONTRACT", "governance": "CONTRACT",
    "integrity_modes": "CONTRACT", "semantic_keys": "CONTRACT",
    "v013_governance": "CONTRACT", "canonicalization": "CANONICALIZATION",
}

ROLE_DEFAULT_TARGET = {
    "registry": tref("REGISTRY", OBJ["registry"]),
    "reference_model": tref("CONTRACT", OBJ["references"]),
    "package": tref("PACKAGE", PKG_ID),
    "authority": tref("AUTHORITY", OBJ["authority"]),
    "bindings": tref("CONTRACT", OBJ["bindings"]),
    "inputs": tref("NORMATIVE_INPUTS", OBJ["inputs"]),
    "accepted_vectors": tref("SOURCE_VECTOR_CATALOG", CATALOG_ID, "0.1"),
    "profile": tref("CANONICALIZATION", OBJ["canon"]),
    "candidate_binding": tref("CONTRACT", OBJ["source_binding"]),
    "accepted_binding": tref("CONTRACT", OBJ["bindings"]),
    "object_registry": tref("REGISTRY", OBJ["registry"]),
    "policy": tref("POLICY", OBJ["partial"]),
    "target": tref("CONTRACT", OBJ["target"]),
    "evidence": tref("EVIDENCE", OBJ["evidence"]),
    "rules": tref("REGISTRY", OBJ["rules"]),
    "invariants": tref("REGISTRY", OBJ["invariants"]),
    "procedures": tref("REGISTRY", OBJ["procedures"]),
    "inventory": tref("CONTRACT", OBJ["propositions"]),
    "governance": tref("CONTRACT", OBJ["governance"]),
    "integrity_modes": tref("CONTRACT", OBJ["integrity_modes"]),
    "semantic_keys": tref("CONTRACT", OBJ["semantic_keys"]),
    "v013_governance": tref("CONTRACT", OBJ["v013_gov"]),
    "canonicalization": tref("CANONICALIZATION", OBJ["canon"]),
}


def build_invariant_specs(procedure_specs):
    failures = {}
    for rule_id, invariant_id in RULE_INVARIANT.items():
        code = next(row[3] for row in RULE_ROWS if row[0] == rule_id)
        failures.setdefault(invariant_id, set()).add(code)

    specs = []

    def emit(invariant_id, procedure_id, usage, roles, subject, klass, extra_codes):
        codes = sorted(set(failures.get(invariant_id, set())) | set(extra_codes))
        specs.append(
            {
                "invariant_id": invariant_id,
                "status": "ACTIVE",
                "class": klass,
                "usage": usage,
                "acceptance_critical": True,
                "procedure_id": procedure_id,
                "input_roles": [
                    {"role": role, "kind": ROLE_KIND[role], "required": True, "cardinality": "ONE"}
                    for role in roles
                ],
                "subject_roles": [subject],
                "default_arguments": {role: copy.deepcopy(ROLE_DEFAULT_TARGET[role]) for role in roles},
                "compatible_failure_codes": codes,
                "fail_closed": True,
            }
        )

    for invariant_id, procedure_id, usage, roles, subject in PACKAGE_INVARIANT_TABLE:
        emit(invariant_id, procedure_id, usage, roles, subject, "PACKAGE_CONFORMANCE",
             [f"{invariant_id}_FAILURE"])
    for invariant_id, roles, subject in GOVERNANCE_INVARIANT_TABLE:
        emit(invariant_id, invariant_id, "GOVERNANCE_REQUIRED", roles, subject, "GOVERNANCE",
             [f"{invariant_id}_FAILURE"])
    for invariant_id, roles, subject in TRUST_INVARIANT_TABLE:
        emit(invariant_id, "TRUST_ANCHOR_COMPARE", "TRUST_REQUIRED", roles, subject, "TRUST",
             [f"{invariant_id}_FAILURE"])
    return specs


def reference_schema():
    return {
        "type": "object",
        "required": ["kind", "id", "version"],
        "properties": {
            "kind": {"enum": ["SCHEMA", "REGISTRY", "CONTRACT", "AUTHORITY",
                              "NORMATIVE_INPUTS", "CANONICALIZATION", "POLICY",
                              "EVIDENCE", "PACKAGE", "SOURCE_VECTOR_CATALOG"]},
            "id": {"type": "string", "minLength": 1},
            "version": {"type": "string", "minLength": 1},
            "member_id": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }


def closed_schema(name, required, properties, defs=None):
    props = {
        "$schema": {"const": DIALECT},
        "schema_ref": {"$ref": "#/$defs/ref"},
        "$id": {"type": "string", "pattern": f"^urn:moirae:accord-02r5r3:[a-z0-9-]+:{VERSION}$"},
        "object_id": {"type": "string", "minLength": 1},
        "object_version": {"const": VERSION},
    }
    props.update(properties)
    all_defs = {"ref": reference_schema()}
    all_defs.update(defs or {})
    return {
        "$schema": DIALECT,
        "$id": f"{SCHEMA_IDS[name]}:{VERSION}",
        "type": "object",
        "required": ["$schema", "$id", "schema_ref", "object_id", "object_version"] + list(required),
        "properties": props,
        "additionalProperties": False,
        "$defs": all_defs,
    }


def scope_schema():
    return {
        "type": "object",
        "required": ["resource", "action", "recipient_or_counterparty", "provider"],
        "properties": {
            "resource": {"type": "string"},
            "action": {"type": "string"},
            "recipient_or_counterparty": {"type": "string"},
            "provider": {"type": "string"},
        },
        "additionalProperties": False,
    }


def interval_schema():
    return {
        "type": "object",
        "required": ["not_before", "as_of"],
        "properties": {"not_before": {"type": "string"}, "as_of": {"type": "string"}},
        "additionalProperties": False,
    }


EXPECTED_VECTOR_SCHEMA = {
    "type": "object",
    "required": ["authority_status", "profile_compatibility", "overall", "occurrence",
                 "attribution", "causality", "completeness", "sufficiency", "freshness",
                 "duplication", "finality", "reason_codes", "must_not_conclude"],
    "properties": {
        "authority_status": {"type": "string"},
        "profile_compatibility": {"type": "string"},
        "overall": {"type": "string"},
        "occurrence": {"type": "string"},
        "attribution": {"type": "string"},
        "causality": {"type": "string"},
        "completeness": {"type": "string"},
        "sufficiency": {"type": "string"},
        "freshness": {"type": "string"},
        "duplication": {"type": "string"},
        "finality": {"type": "string"},
        "reason_codes": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "must_not_conclude": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    },
    "additionalProperties": False,
}

EVIDENCE_ITEM_SCHEMA = {
    "type": "object",
    "required": ["evidence_id", "effect_id", "predicate_id", "stage", "scope",
                 "polarity", "relationship", "admissible", "observed_interval",
                 "consistency_level", "source_class"],
    "properties": {
        "evidence_id": {"type": "string", "minLength": 1},
        "effect_id": {"type": "string", "minLength": 1},
        "predicate_id": {"type": "string", "minLength": 1},
        "stage": {"type": "string", "minLength": 1},
        "scope": scope_schema(),
        "polarity": {"enum": ["POSITIVE", "NEGATIVE"]},
        "relationship": {"enum": ["SAME_TARGET", "DIFFERENT_TARGET", "IRRELEVANT"]},
        "admissible": {"type": "boolean"},
        "observed_interval": interval_schema(),
        "consistency_level": {"type": "string", "minLength": 1},
        "source_class": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}


def build_schemas():
    schemas = {}
    ref = {"$ref": "#/$defs/ref"}

    schemas["authority-requirements"] = closed_schema(
        "authority-requirements",
        ["package_requirements", "stage_policy_requirements", "stage_policy_authorization",
         "canonicalization_requirements", "partial_effect_requirements",
         "classification_requirements", "governing_contract_refs", "trust_boundary_requirements"],
        {
            "package_requirements": {"type": "object"},
            "stage_policy_requirements": {"type": "object", "required": ["global_stage_order", "implicit_transitivity"],
                                          "additionalProperties": {"type": "string"}},
            "stage_policy_authorization": {"type": "object", "additionalProperties": {
                "type": "array", "items": {"type": "string"}}},
            "canonicalization_requirements": {"type": "object"},
            "partial_effect_requirements": {"type": "object"},
            "classification_requirements": {"type": "object"},
            "governing_contract_refs": {"type": "object", "additionalProperties": ref},
            "trust_boundary_requirements": {"type": "object"},
        },
    )
    schemas["governance-requirements"] = closed_schema(
        "governance-requirements",
        ["scope", "governance_invariants", "fail_closed_requirement", "behavior_vocabulary",
         "subject_role_requirement", "default_argument_requirement",
         "derivation_role_closure_requirement", "reference_discovery_scope_requirement",
         "shape_predicate_requirement", "uniqueness_key_requirement", "role_model_requirement",
         "schema_identity_requirement", "governing_authority_requirement",
         "rule_coverage_requirement", "invariant_set_requirement", "supported_operations",
         "semantic_key_governance"],
        {
            "scope": {"const": "BOUNDED_PACKAGE_ONLY_GOVERNANCE"},
            "governance_invariants": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "fail_closed_requirement": {"type": "object"},
            "behavior_vocabulary": {"type": "object"},
            "subject_role_requirement": {"type": "object"},
            "default_argument_requirement": {"type": "object"},
            "derivation_role_closure_requirement": {"type": "object"},
            "reference_discovery_scope_requirement": {"type": "object"},
            "shape_predicate_requirement": {"type": "object"},
            "uniqueness_key_requirement": {"type": "object"},
            "role_model_requirement": {"type": "object"},
            "schema_identity_requirement": {"type": "object"},
            "governing_authority_requirement": {"type": "object"},
            "rule_coverage_requirement": {"type": "object"},
            "invariant_set_requirement": {"type": "object"},
            "supported_operations": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "semantic_key_governance": {"type": "object"},
        },
    )
    mode = {
        "type": "object",
        "required": ["mode", "input", "canonicalization", "algorithm",
                     "expected_digest_source", "verification_operation", "failure_code",
                     "applicability"],
        "properties": {
            "mode": {"type": "string", "minLength": 1},
            "input": {"type": "string", "minLength": 1},
            "canonicalization": {"type": "string", "minLength": 1},
            "algorithm": {"type": "string", "minLength": 1},
            "expected_digest_source": {"type": "string", "minLength": 1},
            "verification_operation": {"type": "string", "minLength": 1},
            "failure_code": {"type": "string", "minLength": 1},
            "applicability": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        },
        "additionalProperties": False,
    }
    schemas["integrity-modes"] = closed_schema(
        "integrity-modes", ["modes", "dispatch"],
        {"modes": {"type": "array", "items": mode, "minItems": 1},
         "dispatch": {
             "type": "object",
             "required": ["procedure_operation", "dispatch_key", "unknown_mode_behavior",
                          "unknown_mode_failure_code"],
             "properties": {
                 "procedure_operation": {"const": "INTEGRITY_MODE_DISPATCH"},
                 "dispatch_key": {"const": "OBJECT_INTEGRITY_MODE_FIELD"},
                 "unknown_mode_behavior": {"const": "FAIL_CLOSED"},
                 "unknown_mode_failure_code": {"type": "string", "minLength": 1},
             },
             "additionalProperties": False}},
    )
    schemas["semantic-key-authority"] = closed_schema(
        "semantic-key-authority", ["semantic_keys", "governing_token_singleton"],
        {"semantic_keys": {"type": "array", "minItems": 1, "items": {
            "type": "object",
            "required": ["key", "authority_path", "governed_mirror_paths",
                         "permitted_provenance_roles"],
            "properties": {
                "key": {"type": "string", "minLength": 1},
                "authority_path": {"type": "string", "minLength": 1},
                "governed_mirror_paths": {"type": "array", "items": {"type": "string"}},
                "permitted_provenance_roles": {"type": "array", "items": {"type": "string"},
                                               "minItems": 1},
            },
            "additionalProperties": False}},
         "governing_token_singleton": {"type": "object"}},
    )
    schemas["normative-inputs"] = closed_schema(
        "normative-inputs",
        ["predicate_policy", "rule_dependencies", "dependency_edges", "vector_expectations",
         "propositions", "profile", "source_catalog_binding_ref",
         "negative_requirement_map_ref", "proposition_inventory_ref", "internal_design_values",
         "reason_code_surface", "must_not_conclude_surface", "accepted_base_package_ref",
         "accepted_base_package_semantic_sha256"],
        {
            "predicate_policy": {"type": "object", "required": ["global_stage_order", "implicit_transitivity"],
                                 "additionalProperties": False,
                                 "properties": {"global_stage_order": {"type": "string"},
                                                "implicit_transitivity": {"type": "string"}}},
            "rule_dependencies": {"type": "array", "minItems": 1, "items": {
                "type": "object", "required": ["rule_id", "depends_on"],
                "properties": {"rule_id": {"type": "string"},
                               "depends_on": {"type": "array", "items": {"type": "string"}}},
                "additionalProperties": False}},
            "dependency_edges": {"type": "array", "minItems": 1, "items": {
                "type": "object", "required": ["from", "to"],
                "properties": {"from": {"type": "string"}, "to": {"type": "string"}},
                "additionalProperties": False}},
            "vector_expectations": {"type": "array", "minItems": 23, "items": {
                "type": "object", "required": ["vector_id", "expected"],
                "properties": {"vector_id": {"type": "string"},
                               "expected": {"$ref": "#/$defs/expectedVector"}},
                "additionalProperties": False}},
            "propositions": {"type": "object", "required": ["collection_proposition_id",
                                                            "projection_proposition_id"],
                             "additionalProperties": False,
                             "properties": {"collection_proposition_id": {"type": "string"},
                                            "projection_proposition_id": {"type": "string"}}},
            "profile": {"type": "object", "required": ["negative_policy", "object_version"],
                        "additionalProperties": False,
                        "properties": {"negative_policy": {"$ref": "#/$defs/negativePolicy"},
                                       "object_version": {"const": VERSION}}},
            "source_catalog_binding_ref": ref,
            "negative_requirement_map_ref": ref,
            "proposition_inventory_ref": ref,
            "internal_design_values": {"type": "object", "minProperties": 1},
            "reason_code_surface": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "must_not_conclude_surface": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "accepted_base_package_ref": ref,
            "accepted_base_package_semantic_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
        defs={
            "expectedVector": EXPECTED_VECTOR_SCHEMA,
            "negativePolicy": {
                "type": "object",
                "required": ["allowed_consistency_levels", "allowed_source_classes",
                             "freshness_max_age_seconds", "minimum_retention_seconds",
                             "future_observation_result", "stale_result", "contradiction_rule",
                             "complete_read_requirement"],
                "properties": {
                    "allowed_consistency_levels": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "allowed_source_classes": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "freshness_max_age_seconds": {"type": "integer", "minimum": 0},
                    "minimum_retention_seconds": {"type": "integer", "minimum": 0},
                    "future_observation_result": {"type": "string", "minLength": 1},
                    "stale_result": {"type": "string", "minLength": 1},
                    "contradiction_rule": {"type": "string", "minLength": 1},
                    "complete_read_requirement": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
            },
        },
    )
    decision_map = {"type": "object", "minProperties": 1, "additionalProperties": {"type": "string"}}
    schemas["partial-effect-policy"] = closed_schema(
        "partial-effect-policy",
        ["stage_authority_ref", "same_effect_required", "direct_predecessor_required", "decisions"],
        {"stage_authority_ref": ref,
         "same_effect_required": {"type": "boolean"},
         "direct_predecessor_required": {"type": "boolean"},
         "decisions": decision_map},
    )
    basis_accepted = {"type": "object",
                      "required": ["field_id", "accepted_pointer"],
                      "properties": {"field_id": {"type": "string"},
                                     "accepted_pointer": {"type": "string"},
                                     "must_equal": {},
                                     "must_contain": {"type": "string"}},
                      "additionalProperties": False}
    basis_candidate = {"type": "object",
                       "required": ["field_id", "candidate_pointer", "provenance"],
                       "properties": {"field_id": {"type": "string"},
                                      "candidate_pointer": {"type": "string"},
                                      "provenance": {"const": "CANDIDATE_LOCAL_NOT_HISTORY"}},
                       "additionalProperties": False}
    schemas["v013-target"] = closed_schema(
        "v013-target",
        ["candidate_proposition_id", "effect_id", "negated_predicate_id", "negated_stage",
         "scope", "required_interval", "settlement_profile_ref", "source_vector_ref",
         "relationship", "relationship_basis"],
        {"candidate_proposition_id": {"type": "string"},
         "effect_id": {"type": "string"},
         "negated_predicate_id": {"type": "string"},
         "negated_stage": {"type": "string"},
         "scope": scope_schema(),
         "required_interval": interval_schema(),
         "settlement_profile_ref": ref,
         "source_vector_ref": ref,
         "relationship": {"type": "string", "minLength": 1},
         "relationship_basis": {"type": "object", "required": ["accepted", "candidate_supplied"],
                                 "additionalProperties": False,
                                 "properties": {"accepted": {"type": "array", "minItems": 1,
                                                              "items": basis_accepted},
                                                "candidate_supplied": {"type": "array", "minItems": 1,
                                                                       "items": basis_candidate}}}},
    )
    schemas["v013-evidence"] = closed_schema(
        "v013-evidence",
        ["fixture_status", "source_accepted_evidence_id", "evidence_id", "effect_id",
         "predicate_id", "stage", "scope", "observed_interval", "retention_window_seconds",
         "consistency_level", "read_semantics", "read_scope_complete", "observed_at",
         "verification_time", "evidence_class", "evidence_universe"],
        {"fixture_status": {"const": "SYNTHETIC_CANDIDATE_0_2_NOT_ACCEPTED_HISTORY"},
         "source_accepted_evidence_id": {"type": "string"},
         "evidence_id": {"type": "string"},
         "effect_id": {"type": "string"},
         "predicate_id": {"type": "string"},
         "stage": {"type": "string"},
         "scope": scope_schema(),
         "observed_interval": interval_schema(),
         "retention_window_seconds": {"type": "integer", "minimum": 0},
         "consistency_level": {"type": "string"},
         "read_semantics": {"type": "string"},
         "read_scope_complete": {"type": "boolean"},
         "observed_at": {"type": "string"},
         "verification_time": {"type": "string"},
         "evidence_class": {"type": "string"},
         "evidence_universe": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/evidenceItem"}}},
        defs={"evidenceItem": EVIDENCE_ITEM_SCHEMA},
    )
    requirement = {"type": "object",
                   "required": ["requirement_id", "source_fields", "governing_authority",
                                "procedure", "failure_code"],
                   "properties": {"requirement_id": {"type": "string", "minLength": 1},
                                  "source_fields": {"type": "array", "items": {"type": "string"},
                                                    "minItems": 1},
                                  "governing_authority": {"type": "string", "minLength": 1},
                                  "procedure": {"type": "string", "minLength": 1},
                                  "failure_code": {"type": "string", "minLength": 1}},
                   "additionalProperties": False}
    schemas["v013-governance"] = closed_schema(
        "v013-governance",
        ["fixture_status", "accepted_v013_locator", "relationship_vocabulary",
         "relationship_basis_schema", "authority_roots", "result_vocabulary",
         "requirement_map", "policy_field_roles", "pass_result", "fail_result"],
        {"fixture_status": {"const": "NORMATIVE_CANDIDATE_0_2"},
         "accepted_v013_locator": {"type": "object", "required": ["source_ref", "accepted_member_id"],
                                   "additionalProperties": False,
                                   "properties": {"source_ref": ref,
                                                  "accepted_member_id": {"type": "string"}}},
         "relationship_vocabulary": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "relationship_basis_schema": {"type": "object"},
         "authority_roots": {"type": "object", "minProperties": 1,
                             "additionalProperties": {"type": "string"}},
         "result_vocabulary": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "requirement_map": {"type": "object",
                             "required": ["required_requirement_ids", "requirements",
                                          "evaluation_order", "forbidden_requirements"],
                             "additionalProperties": False,
                             "properties": {
                                 "required_requirement_ids": {"type": "array",
                                                              "items": {"type": "string"}, "minItems": 1},
                                 "requirements": {"type": "array", "items": requirement, "minItems": 1},
                                 "evaluation_order": {"type": "array", "items": {"type": "string"},
                                                      "minItems": 1},
                                 "forbidden_requirements": {"type": "array",
                                                            "items": {"type": "string"}, "minItems": 1}}},
         "policy_field_roles": {"type": "object", "minProperties": 1,
                                "additionalProperties": {"type": "string"}},
         "pass_result": {"type": "string"},
         "fail_result": {"type": "string"}},
    )
    schemas["proposition-inventory"] = closed_schema(
        "proposition-inventory",
        ["derived_from", "collection_propositions", "member_propositions",
         "projection_propositions", "informational"],
        {"derived_from": {"type": "object"},
         "collection_propositions": {"type": "array", "minItems": 1, "items": {
             "type": "object",
             "required": ["proposition_id", "kind", "normative", "member_pointer", "derived_from"],
             "properties": {"proposition_id": {"type": "string"}, "kind": {"const": "COLLECTION"},
                            "normative": {"type": "boolean"}, "member_pointer": {"type": "string"},
                            "derived_from": {"type": "string"}},
             "additionalProperties": False}},
         "member_propositions": {"type": "array", "minItems": 1, "items": {
             "type": "object",
             "required": ["proposition_id", "kind", "normative", "member_of", "derived_from"],
             "properties": {"proposition_id": {"type": "string"}, "kind": {"const": "MEMBER"},
                            "normative": {"type": "boolean"}, "member_of": {"type": "string"},
                            "derived_from": {"type": "string"}},
             "additionalProperties": False}},
         "projection_propositions": {"type": "array", "minItems": 1, "items": {
             "type": "object",
             "required": ["proposition_id", "kind", "normative", "collection_proposition_id",
                          "projection"],
             "properties": {"proposition_id": {"type": "string"}, "kind": {"const": "PROJECTION"},
                            "normative": {"type": "boolean"},
                            "collection_proposition_id": {"type": "string"},
                            "projection": {"type": "object"}},
             "additionalProperties": False}},
         "informational": {"type": "array", "items": {"type": "object"}}},
    )
    candidate_binding = {
        "type": "object",
        "required": ["assigned_kind", "assigned_id", "assigned_version", "repository_root_path",
                     "semantic_json_content_sha256", "raw_file_bytes_sha256",
                     "declared_integrity_class", "declared_canonicalization", "declared_algorithm",
                     "identity_assignment"],
        "properties": {
            "assigned_kind": {"type": "string"},
            "assigned_id": {"type": "string"},
            "assigned_version": {"type": "string"},
            "repository_root_path": {"type": "string", "minLength": 1},
            "semantic_json_content_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "raw_file_bytes_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "declared_integrity_class": {"type": "string"},
            "declared_canonicalization": {"type": "string"},
            "declared_algorithm": {"type": "string"},
            "identity_assignment": {"const": "PACKAGE_BINDING_NOT_HISTORICAL_SELF_ASSERTION"},
        },
        "additionalProperties": False,
    }
    schemas["source-catalog-binding"] = closed_schema(
        "source-catalog-binding",
        ["candidate_binding", "accepted_binding_ref", "object_registry_ref",
         "integrity_mode_vocabulary_ref", "field_vocabulary_mapping"],
        {"candidate_binding": candidate_binding,
         "accepted_binding_ref": ref,
         "object_registry_ref": ref,
         "integrity_mode_vocabulary_ref": ref,
         "field_vocabulary_mapping": {"type": "object", "minProperties": 1,
                                      "additionalProperties": {"type": "string"}}},
    )
    rule_row = {"type": "object", "required": ["rule_id", "declared_class", "inherited_family",
                                               "inherited_failure_code",
                                               "provenance_source_revision",
                                               "provenance_source_commit"],
                "properties": {"rule_id": {"type": "string"},
                               "declared_class": {"enum": ["EXECUTABLE_CONFORMANCE_RULE",
                                                           "INTERNAL_DESIGN_INVARIANT",
                                                           "DEFERRED_NO_SUBJECT_ARTIFACT"]},
                               "inherited_family": {"type": "string"},
                               "inherited_failure_code": {"type": "string"},
                               "provenance_source_revision": {"type": "string"},
                               "provenance_source_commit": {"type": "string"},
                               "invariant_binding": {"type": "object"},
                               "internal_check": {"type": "object"},
                               "missing_subject_roles": {"type": "array", "items": {"type": "string"}},
                               "later_lifecycle_stage": {"type": "string"},
                               "deferred_reason": {"type": "string"}},
                "additionalProperties": False}
    schemas["rule-registry"] = closed_schema(
        "rule-registry", ["provenance", "rules"],
        {"provenance": {"type": "object",
                        "required": ["source_revision", "source_commit", "source_tree",
                                     "source_rule_registry_semantic_sha256",
                                     "required_rule_ids", "required_rule_inventory_hash"],
                        "additionalProperties": False,
                        "properties": {"source_revision": {"type": "string"},
                                       "source_commit": {"type": "string"},
                                       "source_tree": {"type": "string"},
                                       "source_rule_registry_semantic_sha256": {"type": "string"},
                                       "required_rule_ids": {"type": "array", "items": {"type": "string"},
                                                             "minItems": 1},
                                       "required_rule_inventory_hash": {"type": "string"}}},
         "rules": {"type": "array", "minItems": 1, "items": rule_row}},
    )
    invariants_schema = {"type": "object",
                         "required": ["invariant_id", "status", "class", "usage",
                                      "acceptance_critical", "procedure_id", "input_roles",
                                      "subject_roles", "default_arguments",
                                      "compatible_failure_codes", "fail_closed"],
                         "properties": {"invariant_id": {"type": "string"},
                                        "status": {"enum": ["ACTIVE", "RETIRED"]},
                                        "class": {"enum": ["PACKAGE_CONFORMANCE", "GOVERNANCE", "TRUST"]},
                                        "usage": {"type": "string"},
                                        "acceptance_critical": {"type": "boolean"},
                                        "procedure_id": {"type": "string"},
                                        "input_roles": {"type": "array", "minItems": 1},
                                        "subject_roles": {"type": "array", "minItems": 1,
                                                          "items": {"type": "string"}},
                                        "default_arguments": {"type": "object", "minProperties": 1},
                                        "compatible_failure_codes": {"type": "array",
                                                                     "items": {"type": "string"}},
                                        "fail_closed": {"type": "boolean"}},
                         "additionalProperties": False}
    schemas["invariant-registry"] = closed_schema(
        "invariant-registry", ["invariants"],
        {"invariants": {"type": "array", "minItems": 1, "items": invariants_schema}},
    )
    procedure_row = {"type": "object",
                     "required": ["procedure_id", "arguments", "derivation", "result",
                                  "missing_behavior", "ambiguity_behavior", "fail_closed"],
                     "properties": {"procedure_id": {"type": "string"},
                                    "arguments": {"type": "array", "minItems": 1},
                                    "derivation": {"type": "object", "minProperties": 1},
                                    "result": {"type": "object"},
                                    "missing_behavior": {"type": "string"},
                                    "ambiguity_behavior": {"type": "string"},
                                    "fail_closed": {"type": "boolean"}},
                     "additionalProperties": False}
    schemas["procedure-registry"] = closed_schema(
        "procedure-registry", ["procedures"],
        {"procedures": {"type": "array", "minItems": 1, "items": procedure_row}},
    )
    schemas["reference-model"] = closed_schema(
        "reference-model",
        ["mechanism", "discovery_scope", "shape_predicate", "edge_identity", "deduplication",
         "resolution_cardinality"],
        {"mechanism": {"const": "SHAPE_PREDICATE"},
         "discovery_scope": {"type": "object", "required": ["registry_status", "classification"],
                             "additionalProperties": False,
                             "properties": {"registry_status": {"type": "string"},
                                            "classification": {"type": "string"}}},
         "shape_predicate": {"type": "object",
                             "required": ["required_keys", "optional_keys", "additional_keys",
                                          "all_values_type"],
                             "additionalProperties": False,
                             "properties": {"required_keys": {"type": "array", "items": {"type": "string"},
                                                              "minItems": 1},
                                            "optional_keys": {"type": "array", "items": {"type": "string"}},
                                            "additional_keys": {"type": "string"},
                                            "all_values_type": {"const": "STRING"}}},
         "edge_identity": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "deduplication": {"type": "string"},
         "resolution_cardinality": {"const": "EXACTLY_ONE"}},
    )
    source = {"type": "object", "required": ["ref", "path", "status", "roles", "integrity"],
              "properties": {"ref": ref, "path": {"type": "string", "minLength": 1},
                             "status": {"const": "ACTIVE_ACCEPTED_SOURCE"},
                             "roles": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                             "integrity": {"type": "object",
                                           "required": ["semantic_json_content_sha256",
                                                        "raw_file_bytes_sha256",
                                                        "raw_byte_preservation"],
                                           "additionalProperties": False,
                                           "properties": {
                                               "semantic_json_content_sha256": {"type": "string",
                                                                                "pattern": "^[0-9a-f]{64}$"},
                                               "raw_file_bytes_sha256": {"type": "string",
                                                                         "pattern": "^[0-9a-f]{64}$"},
                                               "raw_byte_preservation": {"type": "string"}}}},
              "additionalProperties": False}
    schemas["accepted-source-bindings"] = closed_schema(
        "accepted-source-bindings", ["sources"],
        {"sources": {"type": "array", "minItems": 1, "items": source}},
    )
    schemas["canonicalization-profile"] = closed_schema(
        "canonicalization-profile",
        ["standard", "serialization", "encoding", "algorithm", "target_id", "selection",
         "reduction", "exclusion_pointers"],
        {"standard": {"type": "string"}, "serialization": {"type": "string"},
         "encoding": {"type": "string"}, "algorithm": {"type": "string"},
         "target_id": {"type": "string"}, "selection": {"type": "string"},
         "reduction": {"type": "string"},
         "exclusion_pointers": {"type": "array", "items": {"type": "string"}, "minItems": 1}},
    )
    schemas["external-verification-input-contract"] = closed_schema(
        "external-verification-input-contract",
        ["input_type", "registry_membership", "candidate_self_assertion", "fields",
         "candidate_identity_recomputation", "results", "cli"],
        {"input_type": {"const": "EXTERNAL_VERIFICATION_INPUT"},
         "registry_membership": {"const": "FORBIDDEN_NOT_A_PACKAGE_OBJECT"},
         "candidate_self_assertion": {"const": "FORBIDDEN"},
         "fields": {"type": "object", "minProperties": 1},
         "candidate_identity_recomputation": {"type": "object"},
         "results": {"type": "object", "minProperties": 1},
         "cli": {"type": "object", "minProperties": 1}},
    )
    registry_object = {"type": "object",
                       "required": ["kind", "id", "version", "path", "status", "roles",
                                    "classification", "integrity"],
                       "properties": {"kind": {"type": "string"},
                                      "id": {"type": "string"},
                                      "version": {"type": "string"},
                                      "path": {"type": "string", "minLength": 1},
                                      "status": {"type": "string"},
                                      "roles": {"type": "array", "items": {"type": "string"},
                                                "minItems": 1},
                                      "classification": {"type": "string"},
                                      "schema_ref": ref,
                                      "members": {"type": "array", "items": {"type": "string"}},
                                      "integrity": {"type": "object", "required": ["mode"],
                                                    "properties": {"mode": {"type": "string"}},
                                                    "additionalProperties": True}},
                       "additionalProperties": False}
    schemas["object-registry"] = closed_schema(
        "object-registry",
        ["uniqueness_key", "role_model", "identity_fields", "status_vocabulary",
         "classification_vocabulary", "role_vocabulary", "objects"],
        {"uniqueness_key": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "role_model": {"type": "string"},
         "identity_fields": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "status_vocabulary": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "classification_vocabulary": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "role_vocabulary": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "objects": {"type": "array", "minItems": 1, "items": registry_object}},
    )
    schemas["specification-package"] = closed_schema(
        "specification-package",
        ["package_id", "package_version", "status", "accepted_base_ref",
         "rejected_candidate_lineage", "object_registry_ref", "rule_registry_ref",
         "invariant_registry_ref", "procedure_registry_ref", "required_invariant_ids",
         "required_rule_ids_ref", "trust_anchor_requirement_ref", "registry_semantic_sha256",
         "runtime",
         "current_candidate_integrity"],
        {"package_id": {"type": "string"},
         "package_version": {"const": VERSION},
         "status": {"const": "CANDIDATE_UNACCEPTED"},
         "accepted_base_ref": ref,
         "rejected_candidate_lineage": {"type": "array", "minItems": 1,
                                        "items": {"type": "object", "required": ["revision", "status"],
                                                  "properties": {"revision": {"type": "string"},
                                                                 "status": {"type": "string"},
                                                                 "commit": {"type": "string"}},
                                                  "additionalProperties": False}},
         "object_registry_ref": ref, "rule_registry_ref": ref,
         "invariant_registry_ref": ref, "procedure_registry_ref": ref,
         "required_invariant_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
         "required_rule_ids_ref": {"type": "string"},
         "trust_anchor_requirement_ref": ref,
         "registry_semantic_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
         "runtime": {"type": "object", "required": ["python", "requirements_path"],
                     "additionalProperties": False,
                     "properties": {"python": {"type": "string"},
                                    "requirements_path": {"type": "string"}}},
         "current_candidate_integrity": {
             "type": "object",
             "required": ["class", "content_target_ref", "algorithm", "digest"],
             "additionalProperties": False,
             "properties": {
                 "class": {"type": "string"},
                 "content_target_ref": {"type": "string"},
                 "algorithm": {"type": "string"},
                 "digest": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"}}}},
    )
    # The current candidate keeps the frozen accepted family identity, which is
    # not namespaced under the revision-local schema namespace.
    schemas["specification-package"]["properties"]["$id"] = {
        "const": f"{PKG_ID}:{VERSION}"
    }
    schemas["specification-package"]["properties"]["object_id"] = {"const": PKG_ID}
    return schemas


def materialise(target: Path) -> None:
    """Write the full artifact set beneath *target* (a repository root)."""
    artifacts = build()
    schemas = build_schemas()
    base = target / REL
    schema_dir = base / "schema"
    fixture_dir = base / "audit" / "fixtures"
    schema_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir.mkdir(parents=True, exist_ok=True)

    for name, value in artifacts.items():
        dump(base / name, value)
    for name, value in schemas.items():
        dump(schema_dir / f"{name}.schema.json", value)

    # Registry schema digests are only knowable after the schemas exist.
    registry = artifacts["object-registry.json"]
    for entry in registry["objects"]:
        if entry["kind"] == "SCHEMA":
            entry["integrity"]["digest"] = sem_file(target / entry["path"])
    dump(base / "object-registry.json", registry)

    package = artifacts["specification-package-0.2.json"]
    package["registry_semantic_sha256"] = sem(registry)
    reduced = copy.deepcopy(package)
    del reduced["current_candidate_integrity"]["digest"]
    package["current_candidate_integrity"]["digest"] = sem(reduced)
    dump(base / "specification-package-0.2.json", package)

    trust_root = {
        "fixture_status": "NON_NORMATIVE_EXTERNAL_TRUST_ROOT_FIXTURE",
        "trust_root_id": f"{NS}:external-trust-root:fixture-v1",
        "package_id": PKG_ID,
        "package_version": VERSION,
        "package_digest": package["current_candidate_integrity"]["digest"],
        "root_kind_definition": {
            "PINNED_ACCEPTED_TRUST_ROOT": "caller asserts this digest is the accepted trust anchor",
            "REPLACED_TRUST_ROOT": "caller asserts the anchor has been replaced out of scope",
        },
    }
    dump(fixture_dir / "external-trust-root.json", trust_root)


def snapshot(root: Path) -> dict[str, bytes]:
    """The builder-produced artifact set (normative JSON, schemas, fixture)."""
    base = root / REL
    produced: dict[str, bytes] = {}
    for path in sorted(base.glob("*.json")):
        produced[path.name] = path.read_bytes()
    for path in sorted((base / "schema").glob("*.schema.json")):
        produced["schema/" + path.name] = path.read_bytes()
    for path in sorted((base / "audit" / "fixtures").glob("*.json")):
        produced["audit/fixtures/" + path.name] = path.read_bytes()
    return produced


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        expected = snapshot(ROOT)
        with tempfile.TemporaryDirectory(prefix="accord-e4r5r3-build-") as tmp:
            materialise(Path(tmp))
            actual = snapshot(Path(tmp))
        drift = sorted(
            set(expected) ^ set(actual)
            | {name for name in set(expected) & set(actual) if expected[name] != actual[name]}
        )
        report = {"mode": "check", "drift": drift, "drift_count": len(drift),
                  "overall_pass": not drift}
        print(json.dumps(report, indent=2))
        return 0 if not drift else 1
    materialise(root)
    print(json.dumps({"mode": "materialise", "root": str(root), "overall_pass": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
