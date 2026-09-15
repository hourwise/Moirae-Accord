from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import rfc8785


ROOT = Path(__file__).resolve().parents[2]
R1 = ROOT / "docs" / "accord-02e4r1"
E4 = ROOT / "docs" / "accord-02e4"
BASE = ROOT / "docs" / "accord-02"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jcs_digest(value) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def ref(profile_id: str, version: str = "0.2") -> dict:
    return {"profile_type": "SETTLEMENT_PROFILE", "profile_id": profile_id, "profile_version": version}


def profile_ref(profile_id: str, version: str = "0.2") -> dict:
    return {"profile_id": profile_id, "profile_version": version}


def schema_contract(schema_id, version, record_types, path, kind, bundles, digest_policy, canonicalization=None):
    item = {
        "schema_id": schema_id,
        "schema_version": version,
        "normative_record_types": record_types,
        "schema_path": path,
        "contract_kind": kind,
        "allowed_bundle_types": bundles,
        "digest_policy": digest_policy,
    }
    if canonicalization is not None:
        item["canonicalization_profile_id"] = canonicalization
    return item


def make_package_schema():
    roles = [
        "ORCHESTRATOR", "DELEGATE_FIXTURE", "PROVIDER_FIXTURE", "OBSERVER_FIXTURE",
        "ARM-A-DURABLE", "ARM-B-PROVIDER-OBSERVATION", "ARM-C-LIGHTWEIGHT-CLASSIFIER",
        "ARM-D-ACCORD-EVIDENCE", "SCORER",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:moirae:accord-02e4r1:schema:specification-package:0.2",
        "title": "ACCORD-02E4R1 closed exact candidate package",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "package_id", "package_version", "package_path", "package_schema_id", "package_schema_version",
            "contract_policy", "base_package", "effective_inventory", "schema_contract_additions",
            "profile_contract_replacements", "profile_contract_additions", "canonicalization_profile_replacements",
            "canonicalization_profiles", "instance_contracts", "role_vocabulary", "validation_rule_contract",
            "active_profile_reference_policy", "retired_contracts", "candidate_notes",
        ],
        "properties": {
            "package_id": {"const": "urn:moirae:accord-02r5:specification-package"},
            "package_version": {"const": "0.2"},
            "package_path": {"const": "docs/accord-02e4r1/accord-02e4r1-specification-package-0.2.json"},
            "package_schema_id": {"const": "urn:moirae:accord-02e4r1:schema:specification-package:0.2"},
            "package_schema_version": {"const": "0.2"},
            "contract_policy": {"const": "CLOSED_EXACT_VERSION"},
            "base_package": {"$ref": "#/$defs/basePackage"},
            "effective_inventory": {"$ref": "#/$defs/inventory"},
            "schema_contract_additions": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/schemaContract"}},
            "profile_contract_replacements": {"type": "array", "items": {"$ref": "#/$defs/profileContract"}},
            "profile_contract_additions": {"type": "array", "items": {"$ref": "#/$defs/profileContract"}},
            "canonicalization_profile_replacements": {"type": "array", "items": {"$ref": "#/$defs/canonicalizationContract"}},
            "canonicalization_profiles": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/canonicalizationContract"}},
            "instance_contracts": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/instanceContract"}},
            "role_vocabulary": {"type": "array", "items": {"enum": roles}, "minItems": 9, "uniqueItems": True},
            "validation_rule_contract": {"$ref": "#/$defs/ruleContract"},
            "active_profile_reference_policy": {"$ref": "#/$defs/referencePolicy"},
            "retired_contracts": {"type": "array", "items": {"$ref": "#/$defs/retiredContract"}, "uniqueItems": True},
            "candidate_notes": {"$ref": "#/$defs/candidateNotes"},
            "package_digest": {"type": "string", "pattern": "^sha-256:[0-9a-f]{64}$"},
        },
        "$defs": {
            "basePackage": {
                "type": "object", "additionalProperties": False,
                "required": ["package_id", "package_version", "package_path", "package_sha256", "inheritance_policy", "schema_contract_count", "profile_contract_count", "canonicalization_profile_count", "role_count", "active_source_schema_pair_count", "active_arm_profile_reference_count", "active_rule_count"],
                "properties": {
                    "package_id": {"const": "urn:moirae:accord-02r5:specification-package"},
                    "package_version": {"const": "0.1"},
                    "package_path": {"const": "docs/accord-02/accord-02r5-specification-package.json"},
                    "package_sha256": {"const": "sha-256:fbb9c3cc97355905e7e12632706e6a982ea1187748f4d2259641f41d20be105c"},
                    "inheritance_policy": {"const": "EXACT_UNCHANGED_CONTRACTS"},
                    "schema_contract_count": {"const": 44}, "profile_contract_count": {"const": 31},
                    "canonicalization_profile_count": {"const": 1}, "role_count": {"const": 9},
                    "active_source_schema_pair_count": {"const": 13}, "active_arm_profile_reference_count": {"const": 16},
                    "active_rule_count": {"const": 82},
                },
            },
            "inventory": {
                "type": "object", "additionalProperties": False,
                "required": ["schema_contracts", "profile_contracts", "canonicalization_profiles", "roles", "active_source_schema_pairs", "active_arm_profile_references", "active_validation_rules"],
                "properties": {
                    "schema_contracts": {"const": 51}, "profile_contracts": {"const": 32},
                    "canonicalization_profiles": {"const": 1}, "roles": {"const": 9},
                    "active_source_schema_pairs": {"const": 13}, "active_arm_profile_references": {"const": 16},
                    "active_validation_rules": {"const": 97},
                },
            },
            "schemaContract": {
                "type": "object", "additionalProperties": False,
                "required": ["schema_id", "schema_version", "normative_record_types", "schema_path", "contract_kind", "allowed_bundle_types", "digest_policy"],
                "properties": {
                    "schema_id": {"type": "string", "minLength": 1}, "schema_version": {"type": "string", "minLength": 1},
                    "normative_record_types": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}, "uniqueItems": True},
                    "schema_path": {"type": "string", "pattern": "^docs/accord-02e4r1(?:/[^/]+)*\\.json$"},
                    "contract_kind": {"enum": ["INSTANCE_RECORD_SCHEMA", "BUNDLE_SCHEMA", "RUN_RECORD_SCHEMA", "SPECIFICATION_CONTRACT_SCHEMA"]},
                    "allowed_bundle_types": {"type": "array", "minItems": 1, "items": {"enum": ["VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE", "SCORER_BUNDLE", "SPECIFICATION_PACKAGE"]}, "uniqueItems": True},
                    "canonicalization_profile_id": {"type": ["string", "null"]},
                    "digest_policy": {"enum": ["OPTIONAL", "REQUIRED", "FORBIDDEN"]},
                },
            },
            "profileContract": {
                "type": "object", "additionalProperties": False,
                "required": ["profile_type", "profile_id", "profile_version", "schema_id", "schema_version", "profile_path", "record_type"],
                "properties": {
                    "profile_type": {"enum": ["VALIDATION_RULE_PROFILE", "EXPERIMENT_PROFILE", "EXTENSION_REGISTRY", "SOURCE_SCHEMA_REGISTRY", "ROLE_VISIBILITY_PROFILE", "NORMALIZATION_PROFILE", "CLASSIFIER_FEATURE_PROFILE", "PREDICATE_APPLICABILITY_PROFILE", "ARM_INPUT_PROFILE", "AUTHORITY_PROFILE", "SETTLEMENT_PROFILE", "PROJECTION_PROFILE", "TRUST_ROOT_PROFILE", "VERIFIER_PROFILE", "CANONICALIZATION_PROFILE"]},
                    "profile_id": {"type": "string", "minLength": 1}, "profile_version": {"type": "string", "minLength": 1},
                    "schema_id": {"type": "string", "minLength": 1}, "schema_version": {"type": "string", "minLength": 1},
                    "profile_path": {"type": "string", "pattern": "^docs/accord-02e4r1(?:/[^/]+)*\\.json$"},
                    "record_type": {"type": "string", "minLength": 1}, "selector": {"type": ["string", "null"]},
                    "replaces_profile_version": {"type": ["string", "null"]},
                },
            },
            "canonicalizationContract": {
                "type": "object", "additionalProperties": False,
                "required": ["profile_id", "profile_version", "schema_id", "schema_version", "profile_path", "replaces_profile_id", "replaces_profile_version"],
                "properties": {
                    "profile_id": {"type": "string", "minLength": 1}, "profile_version": {"type": "string", "minLength": 1},
                    "schema_id": {"type": "string", "minLength": 1}, "schema_version": {"type": "string", "minLength": 1},
                    "profile_path": {"type": "string", "pattern": "^docs/accord-02e4r1(?:/[^/]+)*\\.json$"},
                    "replaces_profile_id": {"type": ["string", "null"]}, "replaces_profile_version": {"type": ["string", "null"]},
                },
            },
            "instanceContract": {
                "type": "object", "additionalProperties": False,
                "required": ["contract_id", "contract_version", "path", "schema_id", "schema_version", "record_type", "required_for", "integrity_policy"],
                "properties": {
                    "contract_id": {"type": "string", "minLength": 1}, "contract_version": {"type": "string", "minLength": 1},
                    "path": {"type": "string", "pattern": "^docs/accord-02e4r1(?:/[^/]+)*\\.json$"},
                    "schema_id": {"type": "string", "minLength": 1}, "schema_version": {"type": "string", "minLength": 1},
                    "record_type": {"type": "string", "minLength": 1}, "required_for": {"type": "array", "minItems": 1, "items": {"type": "string"}, "uniqueItems": True},
                    "integrity_policy": {"enum": ["PACKAGE_MEMBER", "PACKAGE_MEMBER_DIGEST_OPTIONAL", "PACKAGE_MEMBER_DIGEST_REQUIRED"]},
                },
            },
            "ruleContract": {
                "type": "object", "additionalProperties": False,
                "required": ["base_profile_id", "base_profile_version", "overlay_profile_id", "overlay_profile_version", "overlay_path", "dependency_graph_id", "dependency_graph_version", "dependency_graph_path", "composition", "override_policy", "active_rule_count"],
                "properties": {
                    "base_profile_id": {"type": "string"}, "base_profile_version": {"type": "string"},
                    "overlay_profile_id": {"type": "string"}, "overlay_profile_version": {"type": "string"},
                    "overlay_path": {"type": "string", "pattern": "^docs/accord-02e4r1(?:/[^/]+)*\\.json$"},
                    "dependency_graph_id": {"type": "string"}, "dependency_graph_version": {"type": "string"},
                    "dependency_graph_path": {"type": "string", "pattern": "^docs/accord-02e4r1(?:/[^/]+)*\\.json$"},
                    "composition": {"const": "BASE_RULES_PLUS_EXPLICIT_OVERLAY"}, "override_policy": {"const": "R1_EXPLICIT_CANDIDATE_OVERLAY"},
                    "active_rule_count": {"const": 97},
                },
            },
            "referencePolicy": {
                "type": "object", "additionalProperties": False,
                "required": ["resolution_key", "missing_policy", "versionless_policy", "substitution_policy", "active_overrides", "vector_profile_resolution", "legacy_profile_policy"],
                "properties": {
                    "resolution_key": {"const": ["profile_type", "profile_id", "profile_version"]},
                    "missing_policy": {"const": "FAIL_VALIDATION"}, "versionless_policy": {"const": "FAIL_VALIDATION"},
                    "substitution_policy": {"const": "NO_LATEST_NO_CURRENT_NO_COMPATIBLE_SUBSTITUTION"},
                    "active_overrides": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["old_profile_id", "old_profile_version", "new_profile_id", "new_profile_version"], "properties": {"old_profile_id": {"type": "string"}, "old_profile_version": {"type": "string"}, "new_profile_id": {"type": "string"}, "new_profile_version": {"type": "string"}}}},
                    "vector_profile_resolution": {"const": "EXACT_PROFILE_TYPE_ID_VERSION"},
                    "legacy_profile_policy": {"const": "RETIRED_UNAVAILABLE_TO_ACTIVE_CANDIDATE_SCOPE"},
                },
            },
            "retiredContract": {
                "type": "object", "additionalProperties": False,
                "required": ["contract_type", "contract_id", "contract_version", "retirement_policy"],
                "properties": {"contract_type": {"type": "string"}, "contract_id": {"type": "string"}, "contract_version": {"type": "string"}, "retirement_policy": {"const": "NOT_ACTIVE_NOT_RESOLVABLE"}},
            },
            "candidateNotes": {
                "type": "object", "additionalProperties": False,
                "required": ["candidate_only", "base_is_immutable", "repository_fallback", "specification_scope", "historical_e4_preserved", "rule_inventory_policy"],
                "properties": {"candidate_only": {"const": True}, "base_is_immutable": {"const": True}, "repository_fallback": {"const": False}, "specification_scope": {"type": "string", "minLength": 1}, "historical_e4_preserved": {"const": True}, "rule_inventory_policy": {"enum": ["EXISTING_82_PLUS_VERSIONED_OVERLAY", "EXISTING_82_SUFFICIENT"]}},
            },
        },
    }


def make_positive_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:moirae:accord-02e4r1:schema:positive-effect-proposition:0.2",
        "title": "ACCORD-02E4R1 positive/stage proposition",
        "type": "object", "additionalProperties": False,
        "required": ["schema_id", "schema_version", "record_type", "proposition_id", "proposition_kind", "effect_id", "predicate_id", "stage", "integrity"],
        "properties": {
            "schema_id": {"const": "urn:moirae:accord-02e4r1:schema:positive-effect-proposition:0.2"}, "schema_version": {"const": "0.2"}, "record_type": {"const": "effect_proposition"},
            "proposition_id": {"type": "string", "minLength": 1}, "proposition_kind": {"enum": ["POSITIVE_STAGE", "GENERIC_OCCURRENCE"]},
            "effect_id": {"type": "string", "minLength": 1}, "predicate_id": {"type": "string", "minLength": 1}, "stage": {"type": "string", "minLength": 1},
            "action": {"type": ["string", "null"]}, "resource": {"type": ["string", "null"]}, "recipient_or_counterparty": {"type": ["string", "null"]},
            "provider": {"type": ["string", "null"]}, "external_identifier": {"type": ["string", "null"]}, "attempt_id": {"type": ["string", "null"]},
            "binding_status": {"type": "object", "additionalProperties": False, "properties": {name: {"enum": ["BOUND", "OPTIONAL", "UNKNOWN", "NOT_APPLICABLE"]} for name in ["action", "resource", "recipient_or_counterparty", "provider", "attempt_id"]}},
            "integrity": {"type": "object", "additionalProperties": False, "required": ["canonicalization", "digest_algorithm", "content_digest"], "properties": {"canonicalization": {"const": "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2"}, "digest_algorithm": {"const": "SHA-256"}, "content_digest": {"type": "string", "pattern": "^sha-256:[0-9a-f]{64}$"}}},
        },
    }


def make_negative_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:moirae:accord-02e4r1:schema:negative-scope-proposition:0.2",
        "title": "ACCORD-02E4R1 bounded negative-scope proposition",
        "type": "object", "additionalProperties": False,
        "required": ["schema_id", "schema_version", "record_type", "proposition_id", "proposition_kind", "predicate_id", "stage", "effect_id", "negated_predicate_id", "negated_stage", "scope", "evidence_profile_id", "evidence_profile_version", "integrity"],
        "properties": {
            "schema_id": {"const": "urn:moirae:accord-02e4r1:schema:negative-scope-proposition:0.2"}, "schema_version": {"const": "0.2"}, "record_type": {"const": "negative_scope_proposition"},
            "proposition_id": {"type": "string", "minLength": 1}, "proposition_kind": {"const": "NEGATIVE_SCOPE"}, "predicate_id": {"const": "urn:accord:02c:predicate:complete-negative"}, "stage": {"type": "null"}, "effect_id": {"type": "string", "minLength": 1},
            "negated_predicate_id": {"type": "string", "minLength": 1}, "negated_stage": {"type": "string", "minLength": 1},
            "action": {"type": ["string", "null"]}, "resource": {"type": ["string", "null"]}, "recipient_or_counterparty": {"type": ["string", "null"]}, "provider": {"type": ["string", "null"]}, "external_identifier": {"type": ["string", "null"]},
            "scope": {"type": "object", "additionalProperties": False, "required": ["state_space", "interval", "retention_reference", "read_semantics", "consistency"], "properties": {"state_space": {"const": "COMPLETE"}, "interval": {"const": "BOUND_BY_EFFECT_INTERVAL"}, "retention_reference": {"const": "DECLARED_BY_EVIDENCE"}, "read_semantics": {"const": "COMPLETE_LEDGER_QUERY"}, "consistency": {"const": "DECLARED_BY_EVIDENCE"}}},
            "evidence_profile_id": {"type": "string", "minLength": 1}, "evidence_profile_version": {"type": "string", "minLength": 1},
            "integrity": {"type": "object", "additionalProperties": False, "required": ["canonicalization", "digest_algorithm", "content_digest"], "properties": {"canonicalization": {"const": "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2"}, "digest_algorithm": {"const": "SHA-256"}, "content_digest": {"type": "string", "pattern": "^sha-256:[0-9a-f]{64}$"}}},
        },
    }


def make_registry_schema():
    binding_names = ["principal_id", "grant_id", "intent_id", "task_id", "delegation_id", "effect_id", "attempt_id", "observer_principal_id", "issuer_principal_id", "resource", "action", "recipient_or_counterparty", "provider", "external_identifier", "predicate_id", "stage"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:moirae:accord-02e4r1:schema:predicate-registry:0.2", "title": "ACCORD-02E4R1 canonical predicate applicability registry", "type": "object", "additionalProperties": False,
        "required": ["profile_id", "profile_version", "schema_id", "schema_version", "record_type", "registry_id", "registry_version", "resolution_key", "canonical_vocabulary", "binding_vocabulary", "stage_ordering_policy", "stage_ordering_scope", "global_total_order", "exact_identifier_policy", "fail_closed_policy", "binding_authority_policy", "predecessor_policy", "entailment_policy", "closure_contract_ref", "entries"],
        "properties": {
            "profile_id": {"const": "urn:moirae:accord-02e4:predicate-applicability:0.2"}, "profile_version": {"const": "0.2"}, "schema_id": {"const": "urn:moirae:accord-02e4r1:schema:predicate-registry:0.2"}, "schema_version": {"const": "0.2"}, "record_type": {"const": "PREDICATE_APPLICABILITY_PROFILE"}, "registry_id": {"const": "urn:moirae:accord-02e4r1:registry:predicate-applicability"}, "registry_version": {"const": "0.2"}, "resolution_key": {"const": ["predicate_id", "stage"]}, "canonical_vocabulary": {"const": "CANONICAL_C_VECTOR_URNS"}, "binding_vocabulary": {"const": "urn:moirae:accord-02c:schema:settlement-profile:0.1#/$defs/bindingName"},
            "stage_ordering_policy": {"const": "EXPLICIT_PREDECESSOR_EDGES_ONLY"}, "stage_ordering_scope": {"const": "PROFILE_AND_PREDICATE_FAMILY"}, "global_total_order": {"const": False},
            "exact_identifier_policy": {"type": "object", "additionalProperties": False, "required": ["encoding", "equality", "case_sensitive", "unicode_normalization", "trim", "case_folding", "punctuation_normalization", "prefix_suffix_matching", "lexical_similarity", "namespace_fallback"], "properties": {"encoding": {"const": "UTF-8"}, "equality": {"const": "CODE_POINT_STRING_EQUALITY"}, "case_sensitive": {"const": True}, "unicode_normalization": {"const": "NONE"}, "trim": {"const": False}, "case_folding": {"const": False}, "punctuation_normalization": {"const": False}, "prefix_suffix_matching": {"const": False}, "lexical_similarity": {"const": False}, "namespace_fallback": {"const": False}}},
            "fail_closed_policy": {"type": "object", "additionalProperties": False, "required": ["unknown_predicate", "wrong_stage", "undeclared_tuple", "unsupported_predicate", "missing_required_binding", "unsupported_proposition_kind", "profile_not_resolvable"], "properties": {name: {"type": "object", "additionalProperties": False, "required": ["result", "reason_code"], "properties": {"result": {"enum": ["UNKNOWN", "INADMISSIBLE_EVIDENCE", "PROFILE_INCOMPATIBLE", "STRUCTURAL_PROFILE_INCOMPATIBLE"]}, "reason_code": {"type": "string", "minLength": 1}}} for name in ["unknown_predicate", "wrong_stage", "undeclared_tuple", "unsupported_predicate", "missing_required_binding", "unsupported_proposition_kind", "profile_not_resolvable"]}},
            "binding_authority_policy": {"type": "object", "additionalProperties": False, "required": ["required_sets_authority", "profile_requirements", "proposition_status", "contradiction_policy"], "properties": {"required_sets_authority": {"const": "REGISTRY_BY_EXACT_TUPLE"}, "profile_requirements": {"const": "ADDITIVE_EVIDENCE_REQUIREMENTS_ONLY"}, "proposition_status": {"const": "OBSERVATIONAL_NOT_PERMISSIVE"}, "contradiction_policy": {"const": "FAIL_VALIDATION"}}},
            "predecessor_policy": {"type": "object", "additionalProperties": False, "required": ["edges_are_explicit", "transitivity", "same_effect_required", "duplicate_tuple_policy", "self_edge_policy", "dangling_edge_policy", "cycle_policy"], "properties": {"edges_are_explicit": {"const": True}, "transitivity": {"const": "NO_IMPLICIT_TRANSITIVITY"}, "same_effect_required": {"const": True}, "duplicate_tuple_policy": {"const": "FAIL_VALIDATION"}, "self_edge_policy": {"const": "FAIL_VALIDATION"}, "dangling_edge_policy": {"const": "FAIL_VALIDATION"}, "cycle_policy": {"const": "FAIL_VALIDATION"}}},
            "entailment_policy": {"type": "object", "additionalProperties": False, "required": ["generic_occurrence_entails_positive_stage", "positive_stage_entails_generic_occurrence", "effect_settlement_entails_authority", "authority_entails_effect"], "properties": {"generic_occurrence_entails_positive_stage": {"const": False}, "positive_stage_entails_generic_occurrence": {"const": False}, "effect_settlement_entails_authority": {"const": False}, "authority_entails_effect": {"const": False}}},
            "closure_contract_ref": {"type": "string", "minLength": 1},
            "entries": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/entry"}},
        },
        "$defs": {
            "bindingName": {"enum": binding_names},
            "entry": {"type": "object", "additionalProperties": False, "required": ["predicate_id", "stage", "kind", "support_status", "required_bindings", "optional_bindings", "not_applicable_bindings", "predecessor_edges", "stage_settlement", "later_stage_policy", "evidence_capability_ref", "proposition_schema_id", "negative_scope_contract_ref"], "properties": {"predicate_id": {"type": "string", "minLength": 1}, "stage": {"type": ["string", "null"]}, "kind": {"enum": ["POSITIVE_STAGE", "GENERIC_OCCURRENCE", "NEGATIVE_SCOPE"]}, "support_status": {"enum": ["SUPPORTED", "UNSUPPORTED"]}, "required_bindings": {"type": "array", "items": {"$ref": "#/$defs/bindingName"}, "uniqueItems": True}, "optional_bindings": {"type": "array", "items": {"$ref": "#/$defs/bindingName"}, "uniqueItems": True}, "not_applicable_bindings": {"type": "array", "items": {"$ref": "#/$defs/bindingName"}, "uniqueItems": True}, "predecessor_edges": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["predicate_id", "stage"], "properties": {"predicate_id": {"type": "string"}, "stage": {"type": "string"}}}, "uniqueItems": True}, "stage_settlement": {"enum": ["INDEPENDENT_WHEN_BOUND", "PREREQUISITE_CHAIN", "ATOMIC_ONLY", "NOT_APPLICABLE"]}, "later_stage_policy": {"enum": ["NEW_EVIDENCE_REQUIRED", "NO_IMPLICIT_SUCCESSOR", "NOT_APPLICABLE"]}, "evidence_capability_ref": {"type": ["string", "null"]}, "proposition_schema_id": {"type": "string", "minLength": 1}, "negative_scope_contract_ref": {"type": ["string", "null"]}, "unsupported_reason": {"type": "string", "minLength": 1}}},
        },
    }


def make_catalog_schema():
    expected_keys = ["authority_status", "profile_compatibility", "overall", "occurrence", "attribution", "causality", "completeness", "sufficiency", "freshness", "duplication", "finality", "reason_codes", "must_not_conclude"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:moirae:accord-02e4r1:schema:settlement-vector-catalog:0.2", "title": "ACCORD-02E4R1 complete typed settlement-vector catalog", "type": "object", "additionalProperties": False,
        "required": ["catalog_id", "catalog_version", "source_catalog", "integrity", "vectors"],
        "properties": {"catalog_id": {"const": "urn:moirae:accord-02e4r1:catalog:settlement-vectors"}, "catalog_version": {"const": "0.2"}, "source_catalog": {"const": "docs/accord-02/examples/accord-02c-settlement-test-vectors.json"}, "integrity": {"type": "object", "additionalProperties": False, "required": ["canonicalization", "digest_algorithm", "content_digest"], "properties": {"canonicalization": {"const": "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2"}, "digest_algorithm": {"const": "SHA-256"}, "content_digest": {"type": "string", "pattern": "^sha-256:[0-9a-f]{64}$"}}}, "vectors": {"type": "array", "minItems": 23, "items": {"$ref": "#/$defs/vector"}}},
        "$defs": {
            "profileRef": {"type": "object", "additionalProperties": False, "required": ["profile_type", "profile_id", "profile_version"], "properties": {"profile_type": {"const": "SETTLEMENT_PROFILE"}, "profile_id": {"type": "string"}, "profile_version": {"type": "string"}}},
            "tuple": {"type": "object", "additionalProperties": False, "required": ["predicate_id", "stage"], "properties": {"predicate_id": {"type": "string"}, "stage": {"type": ["string", "null"]}}},
            "expected": {"type": "object", "additionalProperties": False, "required": expected_keys, "properties": {"authority_status": {"type": "string"}, "profile_compatibility": {"type": "string"}, "overall": {"type": "string"}, "occurrence": {"type": "string"}, "attribution": {"type": "string"}, "causality": {"type": "string"}, "completeness": {"type": "string"}, "sufficiency": {"type": "string"}, "freshness": {"type": "string"}, "duplication": {"type": "string"}, "finality": {"type": "string"}, "reason_codes": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}, "must_not_conclude": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}}},
            "vector": {"type": "object", "additionalProperties": False, "required": ["vector_id", "source_vector_ref", "settlement_profile_ref", "evidence_profile_ref", "effect_id", "target", "expected", "semantic_status"], "properties": {"vector_id": {"type": "string"}, "source_vector_ref": {"type": "string"}, "settlement_profile_ref": {"$ref": "#/$defs/profileRef"}, "evidence_profile_ref": {"$ref": "#/$defs/profileRef"}, "effect_id": {"type": "string"}, "target": {"$ref": "#/$defs/target"}, "expected": {"$ref": "#/$defs/expected"}, "semantic_status": {"enum": ["SEMANTICS_PRESERVED", "SEMANTICS_AMENDED"]}}},
            "target": {
                "type": "object", "additionalProperties": False,
                "required": ["proposition", "applicability", "target_resolution"],
                "properties": {
                    "proposition": {"type": "object", "required": ["schema_id", "schema_version", "record_type", "proposition_id", "proposition_kind"]},
                    "applicability": {"$ref": "#/$defs/tuple"},
                    "target_resolution": {
                        "type": "object", "additionalProperties": False,
                        "required": ["kind", "proposition_schema_id", "predecessor_edges", "binding_policy", "same_effect_policy"],
                        "properties": {
                            "kind": {"enum": ["POSITIVE_STAGE", "GENERIC_OCCURRENCE", "NEGATIVE_SCOPE"]},
                            "proposition_schema_id": {"type": "string"},
                            "predecessor_edges": {"type": "array", "items": {"$ref": "#/$defs/tuple"}, "uniqueItems": True},
                            "binding_policy": {"const": "REGISTRY_EXACT_TUPLE"},
                            "same_effect_policy": {"const": "REQUIRED_FOR_PREDECESSOR_SUPPORT"},
                            "negative_scope_contract_ref": {"type": ["string", "null"]},
                            "recipient_mismatch_policy": {"enum": ["RETURN_PARTIAL_EFFECT_WITH_ATTRIBUTION_CONFLICT", "RETURN_INADMISSIBLE"]},
                        },
                    },
                },
            },
        },
    }


def make_normative_contract_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:moirae:accord-02e4r1:schema:normative-contracts:0.2", "title": "ACCORD-02E4R1 normative closure contracts", "type": "object", "additionalProperties": False,
        "required": ["contract_id", "contract_version", "record_type", "exact_identifier_policy", "fail_closed_policy", "binding_authority_policy", "predecessor_policy", "partial_effect_policy", "negative_scope_contracts", "entailment_policy", "predicate_authority_policy", "closure_checks", "invariants", "evidence_capability_contracts"],
        "properties": {
            "contract_id": {"const": "urn:moirae:accord-02e4r1:contract:normative-settlement"},
            "contract_version": {"const": "0.2"}, "record_type": {"const": "NORMATIVE_SETTLEMENT_CONTRACTS"},
            "exact_identifier_policy": {"type": "object"}, "fail_closed_policy": {"type": "object"}, "binding_authority_policy": {"type": "object"}, "predecessor_policy": {"type": "object"}, "partial_effect_policy": {"type": "object"}, "negative_scope_contracts": {"type": "array", "minItems": 1}, "entailment_policy": {"type": "object"}, "predicate_authority_policy": {"type": "object"},
            "closure_checks": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "object", "required": ["check_id", "rule", "failure_code"], "additionalProperties": False, "properties": {"check_id": {"type": "string"}, "rule": {"type": "string"}, "failure_code": {"type": "string"}}}},
            "invariants": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "object", "required": ["invariant_id", "statement", "normative_reference"], "additionalProperties": False, "properties": {"invariant_id": {"type": "string"}, "statement": {"type": "string"}, "normative_reference": {"type": "string"}}}},
            "evidence_capability_contracts": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["capability_id", "capability_version", "predicate_id", "stage", "kind", "supported_evidence_classes", "required_bindings", "does_not_prove"], "additionalProperties": False, "properties": {"capability_id": {"type": "string"}, "capability_version": {"type": "string"}, "predicate_id": {"type": "string"}, "stage": {"type": ["string", "null"]}, "kind": {"type": "string"}, "supported_evidence_classes": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}, "required_bindings": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}, "does_not_prove": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}}}},
        },
    }


def build_registry():
    registry = read_json(E4 / "accord-02e4-predicate-applicability-registry.json")
    registry["schema_id"] = "urn:moirae:accord-02e4r1:schema:predicate-registry:0.2"
    registry["registry_id"] = "urn:moirae:accord-02e4r1:registry:predicate-applicability"
    registry["binding_vocabulary"] = "urn:moirae:accord-02c:schema:settlement-profile:0.1#/$defs/bindingName"
    registry["exact_identifier_policy"] = {"encoding": "UTF-8", "equality": "CODE_POINT_STRING_EQUALITY", "case_sensitive": True, "unicode_normalization": "NONE", "trim": False, "case_folding": False, "punctuation_normalization": False, "prefix_suffix_matching": False, "lexical_similarity": False, "namespace_fallback": False}
    registry["fail_closed_policy"] = {name: {"result": result, "reason_code": code} for name, result, code in [
        ("unknown_predicate", "UNKNOWN", "PREDICATE_UNKNOWN"), ("wrong_stage", "UNKNOWN", "PREDICATE_STAGE_MISMATCH"), ("undeclared_tuple", "UNKNOWN", "PREDICATE_STAGE_TUPLE_UNDECLARED"),
        ("unsupported_predicate", "UNKNOWN", "PREDICATE_UNSUPPORTED"), ("missing_required_binding", "INADMISSIBLE_EVIDENCE", "REQUIRED_BINDING_MISSING"),
        ("unsupported_proposition_kind", "STRUCTURAL_PROFILE_INCOMPATIBLE", "PROPOSITION_KIND_UNSUPPORTED"), ("profile_not_resolvable", "PROFILE_INCOMPATIBLE", "PROFILE_UNRESOLVABLE"),
    ]}
    registry["binding_authority_policy"] = {"required_sets_authority": "REGISTRY_BY_EXACT_TUPLE", "profile_requirements": "ADDITIVE_EVIDENCE_REQUIREMENTS_ONLY", "proposition_status": "OBSERVATIONAL_NOT_PERMISSIVE", "contradiction_policy": "FAIL_VALIDATION"}
    registry["predecessor_policy"] = {"edges_are_explicit": True, "transitivity": "NO_IMPLICIT_TRANSITIVITY", "same_effect_required": True, "duplicate_tuple_policy": "FAIL_VALIDATION", "self_edge_policy": "FAIL_VALIDATION", "dangling_edge_policy": "FAIL_VALIDATION", "cycle_policy": "FAIL_VALIDATION"}
    registry["entailment_policy"] = {"generic_occurrence_entails_positive_stage": False, "positive_stage_entails_generic_occurrence": False, "effect_settlement_entails_authority": False, "authority_entails_effect": False}
    registry["closure_contract_ref"] = "urn:moirae:accord-02e4r1:contract:normative-settlement@0.2"
    for entry in registry["entries"]:
        entry["later_stage_policy"] = "NO_IMPLICIT_SUCCESSOR" if entry["later_stage_policy"] == "NO_SUCCESSOR_DECLARED" else entry["later_stage_policy"]
        if entry["evidence_capability_ref"]:
            entry["evidence_capability_ref"] = entry["evidence_capability_ref"].replace("urn:moirae:accord-02e4:evidence-capability:", "urn:moirae:accord-02e4r1:evidence-capability:")
    return registry


def build_normative_contracts():
    capability_data = [
        ("generic-occurrence", "urn:accord:02c:predicate:external-effect", "effect", "GENERIC_OCCURRENCE", ["PROVIDER_EFFECT_RECEIPT", "TARGET_ACKNOWLEDGEMENT", "INDEPENDENT_OBSERVATION", "SIGNED_ATTESTED_ARTIFACT", "EXTERNAL_STATE_SNAPSHOT"], ["effect_id", "predicate_id", "stage"], ["NON_OCCURRENCE", "CAUSALITY", "SPECIFIC_ATTEMPT_CAUSED"]),
        ("resource-created", "urn:accord:02c:predicate:resource-created", "resource_created", "POSITIVE_STAGE", ["INDEPENDENT_OBSERVATION", "SIGNED_ATTESTED_ARTIFACT", "EXTERNAL_STATE_SNAPSHOT"], ["effect_id", "predicate_id", "stage", "resource"], ["CAUSALITY", "SPECIFIC_ATTEMPT_CAUSED"]),
        ("recipient-ack", "urn:accord:02c:predicate:recipient-ack", "recipient_acknowledged", "POSITIVE_STAGE", ["TARGET_ACKNOWLEDGEMENT", "INDEPENDENT_OBSERVATION", "SIGNED_ATTESTED_ARTIFACT"], ["effect_id", "predicate_id", "stage", "recipient_or_counterparty"], ["CAUSALITY", "SPECIFIC_ATTEMPT_CAUSED"]),
        ("provider-acceptance", "urn:accord:02c:predicate:provider-acceptance", "provider_accepted", "POSITIVE_STAGE", ["PROVIDER_ACCEPTANCE_RECEIPT"], ["effect_id", "predicate_id", "stage", "provider"], ["OCCURRENCE", "CAUSALITY"]),
        ("complete-negative", "urn:accord:02c:predicate:complete-negative", None, "NEGATIVE_SCOPE", ["COMPLETE_NEGATIVE_LEDGER_QUERY"], ["effect_id", "predicate_id"], ["OCCURRENCE", "CAUSALITY"]),
    ]
    capabilities = []
    for name, predicate, stage, kind, classes, bindings, not_prove in capability_data:
        capabilities.append({"capability_id": f"urn:moirae:accord-02e4r1:evidence-capability:{name}:0.2", "capability_version": "0.2", "predicate_id": predicate, "stage": stage, "kind": kind, "supported_evidence_classes": classes, "required_bindings": bindings, "does_not_prove": not_prove})
    return {
        "contract_id": "urn:moirae:accord-02e4r1:contract:normative-settlement", "contract_version": "0.2", "record_type": "NORMATIVE_SETTLEMENT_CONTRACTS",
        "exact_identifier_policy": {"encoding": "UTF-8", "equality": "CODE_POINT_STRING_EQUALITY", "case_sensitive": True, "unicode_normalization": "NONE", "trim": False, "case_folding": False, "punctuation_normalization": False, "prefix_suffix_matching": False, "lexical_similarity": False, "namespace_fallback": False},
        "fail_closed_policy": {"unknown_predicate": {"result": "UNKNOWN", "reason_code": "PREDICATE_UNKNOWN"}, "wrong_stage": {"result": "UNKNOWN", "reason_code": "PREDICATE_STAGE_MISMATCH"}, "undeclared_tuple": {"result": "UNKNOWN", "reason_code": "PREDICATE_STAGE_TUPLE_UNDECLARED"}, "unsupported_predicate": {"result": "UNKNOWN", "reason_code": "PREDICATE_UNSUPPORTED"}, "missing_required_binding": {"result": "INADMISSIBLE_EVIDENCE", "reason_code": "REQUIRED_BINDING_MISSING"}, "unsupported_proposition_kind": {"result": "STRUCTURAL_PROFILE_INCOMPATIBLE", "reason_code": "PROPOSITION_KIND_UNSUPPORTED"}, "profile_not_resolvable": {"result": "PROFILE_INCOMPATIBLE", "reason_code": "PROFILE_UNRESOLVABLE"}},
        "binding_authority_policy": {"required_sets_authority": "REGISTRY_BY_EXACT_TUPLE", "profile_requirements": "ADDITIVE_EVIDENCE_REQUIREMENTS_ONLY", "proposition_status": "OBSERVATIONAL_NOT_PERMISSIVE", "contradiction_policy": "FAIL_VALIDATION"},
        "predecessor_policy": {"edges_are_explicit": True, "transitivity": "NO_IMPLICIT_TRANSITIVITY", "same_effect_required": True, "duplicate_tuple_policy": "FAIL_VALIDATION", "self_edge_policy": "FAIL_VALIDATION", "dangling_edge_policy": "FAIL_VALIDATION", "cycle_policy": "FAIL_VALIDATION", "direct_edges_only": True},
        "partial_effect_policy": {"supported_predecessor": "POTENTIAL_PARTIAL_EFFECT", "no_supported_predecessor": "NOT_PARTIAL_EFFECT", "atomic_only": "NOT_PARTIAL_EFFECT", "empty_predecessors": "NOT_PARTIAL_EFFECT", "incompatible_or_inadmissible": "INADMISSIBLE_OR_UNKNOWN", "same_effect_required": True, "later_stage_requires_new_evidence": True},
        "negative_scope_contracts": [{"contract_id": "urn:moirae:accord-02e4r1:contract:bounded-negative-scope", "contract_version": "0.2", "state_space": "COMPLETE", "predicate_binding": "EXACT_NEGATED_PREDICATE_ID_AND_STAGE", "resource_action_recipient_provider_scope": "BOUND_WHERE_APPLICABLE", "interval": "BOUND_BY_EFFECT_INTERVAL", "retention": "DECLARED_BY_EVIDENCE", "consistency": "DECLARED_BY_EVIDENCE", "freshness": "FRESH_AT_VERIFICATION", "contradictory_evidence": "FAIL_VALIDATION", "accepted_source_class": "COMPLETE_NEGATIVE_LEDGER_QUERY", "silence_timeout_stale_or_incomplete": "NOT_SUFFICIENT"}],
        "entailment_policy": {"generic_occurrence_entails_positive_stage": False, "positive_stage_entails_generic_occurrence": False, "effect_settlement_entails_authority": False, "authority_entails_effect": False, "earlier_stage_entails_later_stage": False, "occurrence_entails_attempt_attribution": False},
        "predicate_authority_policy": {"active_authority": "urn:moirae:accord-02e4r1:registry:predicate-applicability@0.2", "retired_authorities": ["urn:moirae:accord-02r3:predicate-applicability:fixture-v1@1.0"], "retired_policy": "NOT_ACTIVE_NOT_RESOLVABLE", "lexical_resolution": "FORBIDDEN"},
        "closure_checks": [
            {"check_id": "CLOSE-001", "rule": "schema ids and versions unique", "failure_code": "DUPLICATE_SCHEMA_CONTRACT"},
            {"check_id": "CLOSE-002", "rule": "profile type/id/version unique", "failure_code": "DUPLICATE_PROFILE_CONTRACT"},
            {"check_id": "CLOSE-003", "rule": "all declared package paths exist and are package-relative", "failure_code": "PACKAGE_PATH_INVALID"},
            {"check_id": "CLOSE-004", "rule": "all declared contract references resolve", "failure_code": "DANGLING_CONTRACT_REFERENCE"},
            {"check_id": "CLOSE-005", "rule": "predicate tuple unique", "failure_code": "DUPLICATE_PREDICATE_STAGE_TUPLE"},
            {"check_id": "CLOSE-006", "rule": "predecessor edges resolve", "failure_code": "DANGLING_PREDECESSOR"},
            {"check_id": "CLOSE-007", "rule": "predecessor graph has no self-edge or cycle", "failure_code": "PREDECESSOR_GRAPH_INVALID"},
            {"check_id": "CLOSE-008", "rule": "unsupported rows cannot carry active capabilities", "failure_code": "UNSUPPORTED_CAPABILITY_CONTRADICTION"},
            {"check_id": "CLOSE-009", "rule": "canonicalization mapping concrete and unique", "failure_code": "CANONICALIZATION_MAPPING_INVALID"},
            {"check_id": "CLOSE-010", "rule": "registry required bindings and profile requirements do not contradict", "failure_code": "BINDING_AUTHORITY_CONTRADICTION"},
            {"check_id": "CLOSE-011", "rule": "all vector profiles exact-version resolve", "failure_code": "VECTOR_PROFILE_UNRESOLVABLE"},
            {"check_id": "CLOSE-012", "rule": "all vector target propositions validate", "failure_code": "VECTOR_TARGET_INVALID"},
            {"check_id": "CLOSE-013", "rule": "full expected axes and prohibitions are present", "failure_code": "EXPECTATION_CONTRACT_INCOMPLETE"},
            {"check_id": "CLOSE-014", "rule": "legacy lexical predicate authority is retired", "failure_code": "COMPETING_PREDICATE_AUTHORITY"},
            {"check_id": "CLOSE-015", "rule": "active candidate rule inventory and dependencies are closed", "failure_code": "RULE_INVENTORY_INVALID"},
        ],
        "invariants": [
            {"invariant_id": "INV-001", "statement": "Adding inadmissible evidence cannot strengthen a settlement result.", "normative_reference": "E4R1-ENT-001"},
            {"invariant_id": "INV-002", "statement": "Removing evidence cannot strengthen a settlement result.", "normative_reference": "E4R1-ENT-001"},
            {"invariant_id": "INV-003", "statement": "Permutation of evidence in a non-ordered collection cannot change the normative result.", "normative_reference": "E4R1-CLOSE-015"},
            {"invariant_id": "INV-004", "statement": "Replay of the same artifact cannot increase corroboration.", "normative_reference": "E4R1-ENT-001"},
            {"invariant_id": "INV-005", "statement": "Lexical variation cannot grant predicate semantics.", "normative_reference": "E4R1-PRED-003"},
            {"invariant_id": "INV-006", "statement": "Earlier stage evidence cannot settle a later stage.", "normative_reference": "E4R1-ENT-001"},
            {"invariant_id": "INV-007", "statement": "An unknown tuple cannot become positive.", "normative_reference": "E4R1-PRED-002"},
            {"invariant_id": "INV-008", "statement": "Sufficient exact evidence remains capable of a positive result when all profile requirements are met.", "normative_reference": "E4R1-BIND-001"},
            {"invariant_id": "INV-009", "statement": "Generic occurrence and positive stage are non-entailing in both directions.", "normative_reference": "E4R1-ENT-001"},
        ],
        "evidence_capability_contracts": capabilities,
    }


def make_target(source_vector, vector_id):
    src = source_vector["input"]["target"]
    predicate = src["predicate_id"]
    if predicate == "urn:accord:02c:predicate:complete-negative":
        proposition = {"schema_id": "urn:moirae:accord-02e4r1:schema:negative-scope-proposition:0.2", "schema_version": "0.2", "record_type": "negative_scope_proposition", "proposition_id": f"urn:moirae:accord-02e4r1:proposition:{vector_id}", "proposition_kind": "NEGATIVE_SCOPE", "predicate_id": predicate, "stage": None, "effect_id": source_vector["input"]["target"]["effect_id"], "negated_predicate_id": "urn:accord:02c:predicate:external-effect", "negated_stage": "effect", "scope": {"state_space": "COMPLETE", "interval": "BOUND_BY_EFFECT_INTERVAL", "retention_reference": "DECLARED_BY_EVIDENCE", "read_semantics": "COMPLETE_LEDGER_QUERY", "consistency": "DECLARED_BY_EVIDENCE"}, "evidence_profile_id": "urn:accord:02c:profile:conservative-v1", "evidence_profile_version": "0.2"}
        kind = "NEGATIVE_SCOPE"
        scope_ref = "urn:moirae:accord-02e4r1:contract:bounded-negative-scope@0.2"
    else:
        kind = "GENERIC_OCCURRENCE" if predicate == "urn:accord:02c:predicate:external-effect" else "POSITIVE_STAGE"
        stage = "effect" if kind == "GENERIC_OCCURRENCE" else ("recipient_acknowledged" if predicate == "urn:accord:02c:predicate:recipient-ack" else "resource_created")
        proposition = {"schema_id": "urn:moirae:accord-02e4r1:schema:positive-effect-proposition:0.2", "schema_version": "0.2", "record_type": "effect_proposition", "proposition_id": f"urn:accord:02e4r1:proposition:{vector_id}", "proposition_kind": kind, "effect_id": source_vector["input"]["target"]["effect_id"], "predicate_id": predicate, "stage": stage}
        if predicate == "urn:accord:02c:predicate:resource-created":
            effect_id = source_vector["input"]["target"]["effect_id"]
            proposition["resource"] = f"urn:accord:02c:resource:{effect_id[effect_id.rfind(':') + 1:]}"
        if predicate == "urn:accord:02c:predicate:recipient-ack":
            proposition["recipient_or_counterparty"] = source_vector["input"]["target"].get("recipient_or_counterparty", "urn:accord:02c:principal:recipient")
        scope_ref = None
    proposition["integrity"] = {"canonicalization": "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2", "digest_algorithm": "SHA-256"}
    no_digest = copy.deepcopy(proposition)
    if "content_digest" in no_digest["integrity"]:
        del no_digest["integrity"]["content_digest"]
    proposition["integrity"]["content_digest"] = "sha-256:" + jcs_digest(no_digest)
    predecessor_edges = []
    if predicate == "urn:accord:02c:predicate:recipient-ack":
        predecessor_edges = [{"predicate_id": "urn:accord:02c:predicate:provider-acceptance", "stage": "provider_accepted"}]
    target_resolution = {"kind": kind, "proposition_schema_id": proposition["schema_id"], "predecessor_edges": predecessor_edges, "binding_policy": "REGISTRY_EXACT_TUPLE", "same_effect_policy": "REQUIRED_FOR_PREDECESSOR_SUPPORT"}
    if vector_id.endswith("RECIPIENT-MISMATCH"):
        target_resolution["recipient_mismatch_policy"] = "RETURN_PARTIAL_EFFECT_WITH_ATTRIBUTION_CONFLICT"
    if scope_ref:
        target_resolution["negative_scope_contract_ref"] = scope_ref
    return {"proposition": proposition, "applicability": {"predicate_id": predicate, "stage": None if kind == "NEGATIVE_SCOPE" else proposition["stage"]}, "target_resolution": target_resolution}


def build_catalog():
    source = read_json(BASE / "examples" / "accord-02c-settlement-test-vectors.json")
    vectors = []
    for item in source["vectors"]:
        vid = item["vector_id"]
        target = make_target(item, vid)
        evidence_profile_id = "urn:accord:02c:profile:incompatible-v1" if "V018" in vid else "urn:accord:02c:profile:conservative-v1"
        expected = copy.deepcopy(item["expected"])
        if "authority" in expected:
            expected["authority_status"] = expected.pop("authority")
        vectors.append({"vector_id": vid, "source_vector_ref": vid, "settlement_profile_ref": ref("urn:accord:02c:profile:conservative-v1"), "evidence_profile_ref": ref(evidence_profile_id), "effect_id": item["input"]["target"]["effect_id"], "target": target, "expected": expected, "semantic_status": "SEMANTICS_PRESERVED"})
    catalog = {"catalog_id": "urn:moirae:accord-02e4r1:catalog:settlement-vectors", "catalog_version": "0.2", "source_catalog": "docs/accord-02/examples/accord-02c-settlement-test-vectors.json", "vectors": vectors}
    no_integrity = copy.deepcopy(catalog)
    catalog["integrity"] = {"canonicalization": "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2", "digest_algorithm": "SHA-256", "content_digest": "sha-256:" + jcs_digest(no_integrity)}
    return catalog


def build_rules():
    base = read_json(BASE / "accord-02r5-validation-rules.json")
    additions = []
    specs = [
        ("E4R1-PRED-001", "PREDICATE_APPLICABILITY", "exact UTF-8 predicate/stage tuple resolves to one row", ["PRED-004", "PKG-002"], "PREDICATE_TUPLE_RESOLUTION_FAILURE"),
        ("E4R1-PRED-002", "FAIL_CLOSED", "unknown, wrong-stage, unsupported, or undeclared tuples cannot produce a positive result", ["E4R1-PRED-001"], "PREDICATE_FAIL_CLOSED"),
        ("E4R1-PRED-003", "EXACT_IDENTIFIER", "identifier comparison is case-sensitive code-point equality with no normalization or lexical fallback", ["E4R1-PRED-001"], "PREDICATE_IDENTIFIER_NOT_EXACT"),
        ("E4R1-AUTH-001", "PREDICATE_AUTHORITY", "only the active R1 predicate registry is normative; retired lexical profiles are unavailable", ["PKG-002", "E4R1-PRED-003"], "COMPETING_PREDICATE_AUTHORITY"),
        ("E4R1-BIND-001", "BINDING_AUTHORITY", "registry required bindings are authoritative and profile requirements are additive", ["PRED-001", "PRED-002", "E4R1-PRED-001"], "BINDING_AUTHORITY_CONTRADICTION"),
        ("E4R1-PROP-001", "PROPOSITION_KIND", "proposition kind and schema must match the resolved tuple kind", ["SCHEMA-002", "E4R1-PRED-001"], "PROPOSITION_KIND_MISMATCH"),
        ("E4R1-PART-001", "PARTIAL_EFFECT", "partial effect requires a supported direct predecessor and later-stage evidence requirement", ["E4R1-BIND-001", "E4R1-PRED-001"], "PARTIAL_EFFECT_PREREQUISITE_UNSATISFIED"),
        ("E4R1-PART-002", "PREDECESSOR_IDENTITY", "predecessor support must bind to the same logical effect and exact predecessor tuple", ["E4R1-PART-001", "E4R1-PRED-001"], "PREDECESSOR_EFFECT_MISMATCH"),
        ("E4R1-PART-003", "PREDECESSOR_GRAPH", "predecessor edges are direct, unique, non-self, non-dangling, and acyclic", ["E4R1-PRED-001", "PKG-002"], "PREDECESSOR_GRAPH_INVALID"),
        ("E4R1-NEG-001", "NEGATIVE_SCOPE", "negative settlement is bounded by exact negated predicate/stage and complete scope requirements", ["E4R1-PRED-001", "E4R1-BIND-001"], "NEGATIVE_SCOPE_INCOMPLETE"),
        ("E4R1-NEG-002", "NEGATIVE_SCOPE", "silence, timeout, stale, incomplete, or contradictory reads cannot support non-occurrence", ["E4R1-NEG-001"], "NEGATIVE_SCOPE_NOT_SUFFICIENT"),
        ("E4R1-ENT-001", "NON_ENTAILMENT", "generic occurrence, positive stage, authority, and effect remain orthogonal", ["E4R1-PRED-001", "E4R1-AUTH-001"], "FORBIDDEN_ENTAILMENT"),
        ("E4R1-CANON-001", "CANONICALIZATION", "each concrete candidate digest form resolves one canonicalization mapping and target", ["DIGEST-CANON-001", "DIGEST-CANON-002"], "CANONICALIZATION_MAPPING_INVALID"),
        ("E4R1-EXPECT-001", "EXPECTATION_CONTRACT", "all accepted expected axes, reason codes, and prohibitions remain present and comparable", ["PKG-002"], "EXPECTATION_CONTRACT_INCOMPLETE"),
        ("E4R1-CLOSE-001", "CANDIDATE_CLOSURE", "candidate package closure checks detect duplicate, dangling, unsafe, contradictory, and unresolved contracts", ["PKG-002", "E4R1-PRED-001", "E4R1-PART-003", "E4R1-CANON-001"], "CANDIDATE_CLOSURE_FAILURE"),
    ]
    for rid, category, description, deps, failure in specs:
        additions.append({"rule_id": rid, "category": category, "classification": "DETERMINISTIC_WITH_PROFILE", "inputs": ["R1 exact candidate package", "declared validation scope", "resolved candidate contract"], "condition": {"operator": description}, "failure_code": failure, "severity": "BLOCKING", "required_for": ["candidate closure", "settlement amendment conformance"], "depends_on": deps, "produces": [rid + "_SATISFIED"]})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:moirae:accord-02e4r1:schema:validation-rules:0.2", "rule_profile_id": "urn:moirae:accord-02e4r1:validation-rules:0.2", "rule_profile_version": "0.2", "record_type": "VALIDATION_RULE_PROFILE", "base_rule_registry": {"path": "docs/accord-02/accord-02r5-validation-rules.json", "profile_id": base["rule_profile_id"], "profile_version": base["rule_profile_version"]}, "overlay_semantics": "The active R1 candidate rule set is the accepted R5 active set plus this explicit versioned overlay. Candidate obligations are not silently assigned to historical rules.", "overrides": base["overrides"], "candidate_additions": additions, "active_rule_count": 82 + len(additions), "classification_gate": {"acceptance_critical_ambiguous": 0, "acceptance_critical_unevaluable": 0, "acceptance_critical_contradictory": 0}}


def build_graph(rules):
    base = read_json(BASE / "accord-02r5-validation-dependency-graph.json")
    additions = rules["candidate_additions"]
    edges = copy.deepcopy(base["edges"])
    for rule in additions:
        edges.append({"from": rule["rule_id"], "depends_on": rule["depends_on"]})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:moirae:accord-02e4r1:schema:validation-dependency-graph:0.2", "graph_id": "urn:moirae:accord-02e4r1:validation-dependency-graph:0.2", "version": "0.2", "base_graph": {"graph_id": base["graph_id"], "path": "docs/accord-02/accord-02r5-validation-dependency-graph.json"}, "overlay_rule_registry": {"path": "docs/accord-02e4r1/accord-02e4r1-validation-rules.json", "profile_id": rules["rule_profile_id"], "profile_version": rules["rule_profile_version"]}, "added_nodes": base["added_nodes"] + [x["rule_id"] for x in additions], "edges": edges, "validation_facts": base["validation_facts"] + [x["rule_id"] + "_SATISFIED" for x in additions], "acyclicity": {"acceptance_critical": True, "result": "ACYCLIC_BY_DECLARED_DEPENDENCIES", "cycles": []}}


def build_findings():
    claude = [
        ("E4-CLAUDE-BLOCK-001", "BLOCKING", "No explicit fail-closed outcome vocabulary for unknown predicate, stage, tuple, required binding, proposition kind, or profile resolution.", "fail-closed registry and normative contract", "CLOSED_BY_R1_CANDIDATE", "R1-ADV-15; R1-ADV-18", "Explicit fail-closed policy and reason codes are present and exercised."),
        ("E4-CLAUDE-MAJOR-001", "MAJOR", "Exact identifier matching did not define case, normalization, trimming, folding, or lexical fallback semantics.", "predicate registry exact_identifier_policy", "CLOSED_BY_R1_CANDIDATE", "R1-ADV-18", "Exact UTF-8 code-point equality and no-normalization policy is explicit."),
        ("E4-CLAUDE-MAJOR-002", "MAJOR", "The candidate omitted the complete expectation axes and prohibitions and did not package the replacement catalog instance.", "settlement vector catalog and package instance_contracts", "CLOSED_BY_R1_CANDIDATE", "R1-ADV-16; full expectation stability", "All accepted axes and prohibitions are carried forward and the catalog is package-inventoried."),
        ("E4-CLAUDE-MAJOR-003", "MAJOR", "Both replacement settlement profiles used CORROBORATION outside the accepted required_for vocabulary.", "replacement settlement profiles", "CLOSED_BY_R1_CANDIDATE", "Draft 2020-12 profile validation", "Profile values are mapped to the accepted OCCURRENCE vocabulary and duplicate values are removed."),
        ("E4-CLAUDE-MAJOR-004", "MAJOR", "Evidence-capability and negative-scope references dangled under closed exact resolution.", "predicate registry and normative contracts", "CLOSED_BY_R1_CANDIDATE", "registry capability closure", "All supported rows resolve to explicit capability contracts and the negative-scope contract is declared."),
        ("E4-CLAUDE-MAJOR-005", "MAJOR", "The candidate settlement vector catalog failed its own additionalProperties-false schema.", "settlement vector catalog schema and targets", "CLOSED_BY_R1_CANDIDATE", "23 target proposition validations", "The catalog schema explicitly admits the typed target structure and all 23 targets validate."),
        ("E4-CLAUDE-MINOR-001", "MINOR", "The binding vocabulary citation was not resolvable.", "predicate registry binding_vocabulary", "CLOSED_BY_R1_CANDIDATE", "registry schema validation", "The registry points to the accepted bindingName vocabulary."),
        ("E4-CLAUDE-MINOR-002", "MINOR", "Generic/stage non-entailment was asymmetric in the candidate representation.", "normative entailment policy", "CLOSED_BY_R1_CANDIDATE", "normative contract validation", "Both non-entailment directions are explicit."),
        ("E4-CLAUDE-MINOR-003", "MINOR", "One expectation used authority instead of authority_status.", "vector expectation contract", "CLOSED_BY_R1_CANDIDATE", "full expectation stability", "The candidate expectation schema and vectors use the complete accepted axis names."),
        ("E4-CLAUDE-MINOR-004", "MINOR", "Four accepted invariants were absent from the candidate invariants artifact.", "normative contract invariants", "CLOSED_BY_R1_CANDIDATE", "normative contract validation", "The missing strengthening/replay/permutation invariants are present."),
        ("E4-CLAUDE-MINOR-005", "MINOR", "The prior consistency check tested section presence rather than schema validity.", "R1 schema-validation report", "CLOSED_BY_R1_CANDIDATE", "Draft 2020-12 validation report", "The R1 closure checker validates schemas and all candidate instances."),
        ("E4-CLAUDE-NOTE-001", "NOTE", "Identity, ancestry, protected refs, and base immutability were independently verified.", "historical review record", "CARRIED_FORWARD", "starting-gate evidence", "Preserved as historical evidence; no historical file is modified."),
        ("E4-CLAUDE-NOTE-002", "NOTE", "All candidate targets resolved exactly once.", "vector catalog", "CARRIED_FORWARD", "target closure", "Preserved and strengthened by schema validation of all 23 targets."),
        ("E4-CLAUDE-NOTE-003", "NOTE", "Predecessor graph was acyclic with no dangling targets.", "predicate registry", "CARRIED_FORWARD", "predecessor closure", "Preserved with explicit edge, self-edge, cycle, and dangling-edge checks."),
        ("E4-CLAUDE-NOTE-004", "NOTE", "PARTIAL_EFFECT was reachable only for the recipient acknowledgement path.", "partial-effect contract", "CARRIED_FORWARD", "partial-effect policy", "Preserved and referenced by the normative contract."),
        ("E4-CLAUDE-NOTE-005", "NOTE", "External-effect binding coverage was adversarially tested.", "binding registry", "CARRIED_FORWARD", "binding closure", "Preserved with exact tuple and required-binding checks."),
        ("E4-CLAUDE-NOTE-006", "NOTE", "Request-level completeness laundering was structurally absent.", "negative-scope model", "CARRIED_FORWARD", "negative-scope closure", "Preserved with bounded negative-scope schema and contract."),
        ("E4-CLAUDE-NOTE-007", "NOTE", "No-rule-change claim had support in the pre-R1 predicate rule.", "historical rule trace", "CARRIED_FORWARD", "versioned rule overlay", "Superseded by an explicit R1 overlay rather than relying on an unchanged-count claim."),
        ("E4-CLAUDE-NOTE-008", "NOTE", "Decision provenance was reported honestly.", "historical review provenance", "CARRIED_FORWARD", "assessment manifest", "Preserved with source hashes and no normalization claim."),
        ("E4-CLAUDE-NOTE-009", "NOTE", "Profiles were substantive rather than tautological.", "settlement profiles", "CARRIED_FORWARD", "profile validation", "Preserved; both profiles pass the accepted schema."),
    ]
    deepseek_specs = [
        ("E4-DEEPSEEK-BLOCK-01", "BLOCKING", "The candidate catalog instance failed its own schema through an undeclared target_selection_rule field.", "settlement vector catalog schema", "CLOSED_BY_R1_CANDIDATE", "23 target proposition validations", "The R1 catalog schema and typed targets are mutually valid."),
        ("E4-DEEPSEEK-BLOCK-02", "BLOCKING", "Both replacement settlement profiles failed the accepted profile schema on CORROBORATION.", "replacement settlement profiles", "CLOSED_BY_R1_CANDIDATE", "Draft 2020-12 profile validation", "The replacement profiles use only accepted required_for values."),
        ("E4-DEEPSEEK-BLOCK-03", "BLOCKING", "The candidate dropped eleven expectation axes and all must_not_conclude prohibitions.", "vector expectation contract", "CLOSED_BY_R1_CANDIDATE", "R1-ADV-16; full expectation stability", "The full expectation contract is carried forward and mutation-tested."),
        ("E4-DEEPSEEK-BLOCK-04", "BLOCKING", "Digest mappings and the referenced canonicalization profile were not resolvable.", "canonicalization profile and package mappings", "CLOSED_BY_R1_CANDIDATE", "candidate canonicalization mapping checks", "The exact R1 canonicalization profile and three concrete mappings resolve."),
        ("E4-DEEPSEEK-BLOCK-05", "BLOCKING", "Versionless inherited vector references could not resolve under exact version policy.", "settlement vector profile references", "CLOSED_BY_R1_CANDIDATE", "23 exact profile references", "Every vector binds exact settlement/evidence profile type, ID, and version."),
        ("E4-DEEPSEEK-BLOCK-06", "BLOCKING", "The inherited lexical applicability authority remained alongside the candidate registry.", "package profile inventory and predicate authority policy", "CLOSED_BY_R1_CANDIDATE", "retired-authority and lexical-resolution checks", "The R1 package retires the legacy authority and forbids lexical resolution."),
        ("E4-DEEPSEEK-MAJOR-01", "MAJOR", "Partial-effect semantics existed only as an orphan invariant rather than an active contract.", "partial-effect normative contract", "CLOSED_BY_R1_CANDIDATE", "normative contract validation", "Partial-effect policy is a declared normative contract and active rule overlay input."),
        ("E4-DEEPSEEK-MAJOR-02", "MAJOR", "Capability, negative-scope, and binding references dangled.", "registry contract references", "CLOSED_BY_R1_CANDIDATE", "registry capability closure", "All referenced contracts are explicitly declared and resolvable."),
        ("E4-DEEPSEEK-MAJOR-03", "MAJOR", "Binding authority was triplicated across registry, profile, and proposition without precedence.", "binding authority policy", "CLOSED_BY_R1_CANDIDATE", "binding authority and contradiction checks", "Registry requirements are authoritative; profile requirements are additive and proposition fields are observations."),
        ("E4-DEEPSEEK-MAJOR-04", "MAJOR", "Stage settlement vocabulary diverged from accepted enums.", "predicate registry schema", "CLOSED_BY_R1_CANDIDATE", "Draft 2020-12 registry validation", "Candidate stage-policy values are closed to the versioned registry schema."),
        ("E4-DEEPSEEK-MAJOR-05", "MAJOR", "The predecessor policy conflicted with the profile-level stage policy and successor relation.", "predecessor and partial-effect policies", "CLOSED_BY_R1_CANDIDATE", "predecessor closure and later-stage policy", "NO_IMPLICIT_SUCCESSOR is used and explicit predecessor edges are separately authoritative."),
        ("E4-DEEPSEEK-MAJOR-06", "MAJOR", "Four vector targets were not expressible as valid proposition records.", "V013, V014, V017, V021 targets", "CLOSED_BY_R1_CANDIDATE", "23 target proposition validations", "Control/expectation data is outside typed propositions and V013 uses the negative-scope schema."),
        ("E4-DEEPSEEK-MAJOR-07", "MAJOR", "Negative-scope semantics used unconstrained strings without a deterministic mapping.", "negative-scope proposition and contract", "CLOSED_BY_R1_CANDIDATE", "negative-scope contract validation", "State space, interval, retention, read semantics, consistency, and source class are closed."),
        ("E4-DEEPSEEK-MAJOR-08", "MAJOR", "The unchanged 82-rule inventory could not express the candidate obligations.", "validation rule registry", "CLOSED_BY_R1_CANDIDATE", "97-rule overlay and dependency closure", "R1 adds an explicit versioned overlay and reports 97 active rules."),
        ("E4-DEEPSEEK-MAJOR-09", "MAJOR", "The candidate lacked fail-closed outcome vocabulary.", "fail-closed policy", "CLOSED_BY_R1_CANDIDATE", "R1-ADV-15", "The registry and normative contract define deterministic fail-closed statuses and reason codes."),
        ("E4-DEEPSEEK-MAJOR-10", "MAJOR", "Duplicate registry tuples were not deterministically rejected.", "registry resolution key and closure checks", "CLOSED_BY_R1_CANDIDATE", "R1-ADV-01; R1-ADV-02", "Exact tuple uniqueness and contradiction policy are explicit and mutation-tested."),
        ("E4-DEEPSEEK-MAJOR-11", "MAJOR", "Predecessor support lacked same-effect coupling.", "predecessor policy and target resolution", "CLOSED_BY_R1_CANDIDATE", "predecessor closure", "Same-effect requirement and explicit predecessor target resolution are normative."),
        ("E4-DEEPSEEK-MINOR-01", "MINOR", "The incompatible profile was weakly distinguished from the conservative profile.", "settlement profile compatibility", "CARRIED_FORWARD", "profile validation", "The profile remains a declared candidate distinction; conformance of semantics remains a later implementation concern."),
        ("E4-DEEPSEEK-MINOR-02", "MINOR", "Profile digest optionality conflicted with candidate schema/package digest requirements.", "profile integrity and schema contracts", "CLOSED_BY_R1_CANDIDATE", "canonicalization and package mapping checks", "Candidate proposition/catalog integrity contracts are explicit and mapped."),
        ("E4-DEEPSEEK-MINOR-03", "MINOR", "Digest policy and bundle admissibility changes were not explicit.", "schema contract additions", "CLOSED_BY_R1_CANDIDATE", "package schema validation", "Candidate schemas explicitly restrict bundle classes and digest policy."),
        ("E4-DEEPSEEK-MINOR-04", "MINOR", "Stage relation appeared in multiple encodings.", "registry, profile, catalog target resolution", "CARRIED_FORWARD", "stage policy closure", "R1 identifies the registry exact tuple as binding authority and keeps target resolution metadata non-authoritative."),
        ("E4-DEEPSEEK-MINOR-05", "MINOR", "Package path patterns permitted traversal-shaped values.", "package schema and closure checks", "CLOSED_BY_R1_CANDIDATE", "R1-ADV-06; R1-ADV-07", "Package-relative path closure rejects traversal and missing paths."),
        ("E4-DEEPSEEK-MINOR-06", "MINOR", "Override and no-substitution policies were not clearly coordinated.", "active profile reference policy", "CLOSED_BY_R1_CANDIDATE", "exact profile resolution checks", "Explicit versioned replacements coexist with no latest/current/compatible substitution."),
        ("E4-DEEPSEEK-MINOR-07", "MINOR", "Kind agreement was convention rather than a closed contract.", "typed proposition and registry target resolution", "CLOSED_BY_R1_CANDIDATE", "23 target proposition validations", "Kind is explicitly typed in candidate proposition/catalog schemas."),
        ("E4-DEEPSEEK-MINOR-08", "MINOR", "V015 used an undeclared authority expectation key/value.", "expectation schema", "CLOSED_BY_R1_CANDIDATE", "full expectation stability", "The accepted authority_status axis is retained."),
        ("E4-DEEPSEEK-NOTE-01", "NOTE", "Negative proposition scope is intentionally closed to a complete state space and bounded interval.", "negative-scope contract", "CARRIED_FORWARD", "negative-scope validation", "Preserved as explicit R1 contract semantics."),
        ("E4-DEEPSEEK-NOTE-02", "NOTE", "Proposition identity uniqueness was not separately declared.", "candidate vector/proposition inventory", "CARRIED_FORWARD", "target identity closure", "Candidate catalog and typed proposition IDs are validated within the declared scope."),
        ("E4-DEEPSEEK-NOTE-03", "NOTE", "Target effect identity had limited binding constraints in the prior candidate.", "positive proposition schema", "CARRIED_FORWARD", "proposition schema validation", "The R1 schema preserves explicit effect identity and target resolution fields."),
        ("E4-DEEPSEEK-NOTE-04", "NOTE", "The prior candidate reported PASS without a standards-complete validator.", "historical E4 consistency evidence", "CARRIED_FORWARD", "R1 schema validation report", "R1 uses jsonschema 4.26.0 for Draft 2020-12 validation; no interoperability claim is made."),
        ("E4-DEEPSEEK-NOTE-05", "NOTE", "Base inventory and protected counts were independently reproduced.", "package inheritance", "CARRIED_FORWARD", "base package digest and inventory", "The R1 package pins the immutable base package and preserves its counts."),
        ("E4-DEEPSEEK-NOTE-06", "NOTE", "Active arm profile count and raw reference occurrence count differ by definition.", "package inventory", "CARRIED_FORWARD", "package inventory audit", "The R1 inventory retains the declared active reference count without changing experiment scope."),
    ]
    findings = []
    for assessor, specs in (("CLAUDE", claude), ("DEEPSEEK", deepseek_specs)):
        for finding_id, severity, exact_defect, artifact, status, test_id, adjudication in specs:
            findings.append({
                "assessor": assessor,
                "original_finding_id": finding_id,
                "severity": severity,
                "normative_source": "ACCORD-02E4 independent assessment",
                "affected_artifact": artifact,
                "overlap_group": finding_id.split("-", 3)[-1],
                "exact_defect": exact_defect,
                "remediation_status": status,
                "test_reproducer": test_id,
                "final_adjudication": adjudication,
            })
    return {
        "candidate": "ACCORD-02E4R1",
        "ingestion_policy": "EVERY_ASSESSOR_FINDING_ONCE; DISAGREEMENTS_RETAINED",
        "findings_count": len(findings),
        "findings": findings,
    }


def build():
    for sub in ["schema", "profiles", "canonicalization"]:
        (R1 / sub).mkdir(parents=True, exist_ok=True)
    write_json(R1 / "schema" / "accord-02e4r1-specification-package.schema.json", make_package_schema())
    write_json(R1 / "schema" / "accord-02e4r1-positive-effect-proposition.schema.json", make_positive_schema())
    write_json(R1 / "schema" / "accord-02e4r1-negative-scope-proposition.schema.json", make_negative_schema())
    write_json(R1 / "schema" / "accord-02e4r1-predicate-registry.schema.json", make_registry_schema())
    write_json(R1 / "schema" / "accord-02e4r1-settlement-vector-catalog.schema.json", make_catalog_schema())
    write_json(R1 / "schema" / "accord-02e4r1-normative-contracts.schema.json", make_normative_contract_schema())
    base_canon_schema = read_json(BASE / "schema" / "accord-02r5-canonicalization-profile.schema.json")
    base_canon_schema["$id"] = "urn:moirae:accord-02e4r1:schema:canonicalization-profile:0.2"
    base_canon_schema["title"] = "ACCORD-02E4R1 candidate RFC8785 canonicalization profile"
    base_canon_schema["properties"]["schema_id"] = {"const": "urn:moirae:accord-02e4r1:schema:canonicalization-profile:0.2"}
    base_canon_schema["properties"]["schema_version"] = {"const": "0.2"}
    base_canon_schema["properties"]["profile_id"] = {"const": "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2"}
    base_canon_schema["properties"]["profile_version"] = {"const": "0.2"}
    write_json(R1 / "schema" / "accord-02e4r1-canonicalization-profile.schema.json", base_canon_schema)

    canon = read_json(BASE / "examples" / "accord-02r5-canonicalization-profile.json")
    canon["schema_id"] = "urn:moirae:accord-02e4r1:schema:canonicalization-profile:0.2"
    canon["schema_version"] = "0.2"
    canon["profile_id"] = "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2"
    canon["profile_version"] = "0.2"
    canon["applies_to"] += [
        {"container_type": "VERIFIER_RECORD_ENTRY", "schema_id": "urn:moirae:accord-02e4r1:schema:positive-effect-proposition:0.2", "schema_version": "0.2", "record_types": ["effect_proposition"], "content_target": "content"},
        {"container_type": "VERIFIER_RECORD_ENTRY", "schema_id": "urn:moirae:accord-02e4r1:schema:negative-scope-proposition:0.2", "schema_version": "0.2", "record_types": ["negative_scope_proposition"], "content_target": "content"},
        {"container_type": "EXPERIMENT_RECORD_ENTRY", "schema_id": "urn:moirae:accord-02e4r1:schema:settlement-vector-catalog:0.2", "schema_version": "0.2", "record_types": ["SETTLEMENT_VECTOR_CATALOG"], "content_target": "content"},
    ]
    write_json(R1 / "canonicalization" / "accord-02e4r1-canonicalization-profile.json", canon)

    registry = build_registry()
    write_json(R1 / "accord-02e4r1-predicate-applicability-registry.json", registry)
    contracts = build_normative_contracts()
    write_json(R1 / "accord-02e4r1-normative-contracts.json", contracts)

    for name in ["conservative", "incompatible"]:
        profile = read_json(E4 / "profiles" / f"accord-02e4-settlement-profile-{name}-v2.json")
        for dim in profile["understood_evidence_dimensions"]:
            mapped = ["OCCURRENCE" if x == "CORROBORATION" else x for x in dim["required_for"]]
            dim["required_for"] = list(dict.fromkeys(mapped))
        write_json(R1 / "profiles" / f"accord-02e4r1-settlement-profile-{name}-v2.json", profile)

    catalog = build_catalog()
    write_json(R1 / "accord-02e4r1-settlement-vector-catalog.json", catalog)
    rules = build_rules()
    write_json(R1 / "accord-02e4r1-validation-rules.json", rules)
    graph = build_graph(rules)
    write_json(R1 / "accord-02e4r1-validation-dependency-graph.json", graph)

    additions = [
        schema_contract("urn:moirae:accord-02e4r1:schema:specification-package:0.2", "0.2", ["SPECIFICATION_PACKAGE"], "docs/accord-02e4r1/schema/accord-02e4r1-specification-package.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE"], "FORBIDDEN"),
        schema_contract("urn:moirae:accord-02e4r1:schema:positive-effect-proposition:0.2", "0.2", ["effect_proposition"], "docs/accord-02e4r1/schema/accord-02e4r1-positive-effect-proposition.schema.json", "INSTANCE_RECORD_SCHEMA", ["VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "REQUIRED", "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2"),
        schema_contract("urn:moirae:accord-02e4r1:schema:negative-scope-proposition:0.2", "0.2", ["negative_scope_proposition"], "docs/accord-02e4r1/schema/accord-02e4r1-negative-scope-proposition.schema.json", "INSTANCE_RECORD_SCHEMA", ["VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "REQUIRED", "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2"),
        schema_contract("urn:moirae:accord-02e4r1:schema:predicate-registry:0.2", "0.2", ["PREDICATE_APPLICABILITY_PROFILE"], "docs/accord-02e4r1/schema/accord-02e4r1-predicate-registry.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE", "VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "FORBIDDEN"),
        schema_contract("urn:moirae:accord-02e4r1:schema:settlement-vector-catalog:0.2", "0.2", ["SETTLEMENT_VECTOR_CATALOG"], "docs/accord-02e4r1/schema/accord-02e4r1-settlement-vector-catalog.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE", "EXPERIMENT_VALIDATION_BUNDLE"], "OPTIONAL", "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2"),
        schema_contract("urn:moirae:accord-02e4r1:schema:normative-contracts:0.2", "0.2", ["NORMATIVE_SETTLEMENT_CONTRACTS"], "docs/accord-02e4r1/schema/accord-02e4r1-normative-contracts.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE", "VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "FORBIDDEN"),
        schema_contract("urn:moirae:accord-02e4r1:schema:canonicalization-profile:0.2", "0.2", ["CANONICALIZATION_PROFILE"], "docs/accord-02e4r1/schema/accord-02e4r1-canonicalization-profile.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE", "VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "FORBIDDEN"),
    ]
    package = {
        "package_id": "urn:moirae:accord-02r5:specification-package", "package_version": "0.2", "package_path": "docs/accord-02e4r1/accord-02e4r1-specification-package-0.2.json", "package_schema_id": "urn:moirae:accord-02e4r1:schema:specification-package:0.2", "package_schema_version": "0.2", "contract_policy": "CLOSED_EXACT_VERSION",
        "base_package": {"package_id": "urn:moirae:accord-02r5:specification-package", "package_version": "0.1", "package_path": "docs/accord-02/accord-02r5-specification-package.json", "package_sha256": "sha-256:fbb9c3cc97355905e7e12632706e6a982ea1187748f4d2259641f41d20be105c", "inheritance_policy": "EXACT_UNCHANGED_CONTRACTS", "schema_contract_count": 44, "profile_contract_count": 31, "canonicalization_profile_count": 1, "role_count": 9, "active_source_schema_pair_count": 13, "active_arm_profile_reference_count": 16, "active_rule_count": 82},
        "effective_inventory": {"schema_contracts": 51, "profile_contracts": 32, "canonicalization_profiles": 1, "roles": 9, "active_source_schema_pairs": 13, "active_arm_profile_references": 16, "active_validation_rules": rules["active_rule_count"]},
        "schema_contract_additions": additions,
        "profile_contract_replacements": [
            {"profile_type": "SETTLEMENT_PROFILE", "profile_id": "urn:accord:02c:profile:conservative-v1", "profile_version": "0.2", "schema_id": "urn:moirae:accord-02c:schema:settlement-profile:0.1", "schema_version": "0.1", "profile_path": "docs/accord-02e4r1/profiles/accord-02e4r1-settlement-profile-conservative-v2.json", "record_type": "SETTLEMENT_PROFILE", "selector": "urn:accord:02c:profile:conservative-v1", "replaces_profile_version": "0.1"},
            {"profile_type": "SETTLEMENT_PROFILE", "profile_id": "urn:accord:02c:profile:incompatible-v1", "profile_version": "0.2", "schema_id": "urn:moirae:accord-02c:schema:settlement-profile:0.1", "schema_version": "0.1", "profile_path": "docs/accord-02e4r1/profiles/accord-02e4r1-settlement-profile-incompatible-v2.json", "record_type": "SETTLEMENT_PROFILE", "selector": "urn:accord:02c:profile:incompatible-v1", "replaces_profile_version": "0.1"},
        ],
        "profile_contract_additions": [{"profile_type": "PREDICATE_APPLICABILITY_PROFILE", "profile_id": "urn:moirae:accord-02e4:predicate-applicability:0.2", "profile_version": "0.2", "schema_id": "urn:moirae:accord-02e4r1:schema:predicate-registry:0.2", "schema_version": "0.2", "profile_path": "docs/accord-02e4r1/accord-02e4r1-predicate-applicability-registry.json", "record_type": "PREDICATE_APPLICABILITY_PROFILE", "selector": None, "replaces_profile_version": None}],
        "canonicalization_profile_replacements": [{"profile_id": "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2", "profile_version": "0.2", "schema_id": "urn:moirae:accord-02e4r1:schema:canonicalization-profile:0.2", "schema_version": "0.2", "profile_path": "docs/accord-02e4r1/canonicalization/accord-02e4r1-canonicalization-profile.json", "replaces_profile_id": "urn:moirae:accord-02r5:canonicalization:rfc8785-jcs:0.1", "replaces_profile_version": "0.1"}],
        "canonicalization_profiles": [{"profile_id": "urn:moirae:accord-02e4r1:canonicalization:rfc8785-jcs:0.2", "profile_version": "0.2", "schema_id": "urn:moirae:accord-02e4r1:schema:canonicalization-profile:0.2", "schema_version": "0.2", "profile_path": "docs/accord-02e4r1/canonicalization/accord-02e4r1-canonicalization-profile.json", "replaces_profile_id": "urn:moirae:accord-02r5:canonicalization:rfc8785-jcs:0.1", "replaces_profile_version": "0.1"}],
        "instance_contracts": [
            {"contract_id": "urn:moirae:accord-02e4r1:contract:settlement-vector-catalog", "contract_version": "0.2", "path": "docs/accord-02e4r1/accord-02e4r1-settlement-vector-catalog.json", "schema_id": "urn:moirae:accord-02e4r1:schema:settlement-vector-catalog:0.2", "schema_version": "0.2", "record_type": "SETTLEMENT_VECTOR_CATALOG", "required_for": ["candidate_amendment_conformance", "expectation_stability"], "integrity_policy": "PACKAGE_MEMBER_DIGEST_REQUIRED"},
            {"contract_id": "urn:moirae:accord-02e4r1:contract:normative-settlement", "contract_version": "0.2", "path": "docs/accord-02e4r1/accord-02e4r1-normative-contracts.json", "schema_id": "urn:moirae:accord-02e4r1:schema:normative-contracts:0.2", "schema_version": "0.2", "record_type": "NORMATIVE_SETTLEMENT_CONTRACTS", "required_for": ["candidate_amendment_conformance", "closure_validation"], "integrity_policy": "PACKAGE_MEMBER"},
        ],
        "role_vocabulary": ["ORCHESTRATOR", "DELEGATE_FIXTURE", "PROVIDER_FIXTURE", "OBSERVER_FIXTURE", "ARM-A-DURABLE", "ARM-B-PROVIDER-OBSERVATION", "ARM-C-LIGHTWEIGHT-CLASSIFIER", "ARM-D-ACCORD-EVIDENCE", "SCORER"],
        "validation_rule_contract": {"base_profile_id": "urn:moirae:accord-02r5:validation-rules:0.1", "base_profile_version": "0.1", "overlay_profile_id": rules["rule_profile_id"], "overlay_profile_version": rules["rule_profile_version"], "overlay_path": "docs/accord-02e4r1/accord-02e4r1-validation-rules.json", "dependency_graph_id": graph["graph_id"], "dependency_graph_version": graph["version"], "dependency_graph_path": "docs/accord-02e4r1/accord-02e4r1-validation-dependency-graph.json", "composition": "BASE_RULES_PLUS_EXPLICIT_OVERLAY", "override_policy": "R1_EXPLICIT_CANDIDATE_OVERLAY", "active_rule_count": rules["active_rule_count"]},
        "active_profile_reference_policy": {"resolution_key": ["profile_type", "profile_id", "profile_version"], "missing_policy": "FAIL_VALIDATION", "versionless_policy": "FAIL_VALIDATION", "substitution_policy": "NO_LATEST_NO_CURRENT_NO_COMPATIBLE_SUBSTITUTION", "active_overrides": [{"old_profile_id": "urn:accord:02c:profile:conservative-v1", "old_profile_version": "0.1", "new_profile_id": "urn:accord:02c:profile:conservative-v1", "new_profile_version": "0.2"}, {"old_profile_id": "urn:accord:02c:profile:incompatible-v1", "old_profile_version": "0.1", "new_profile_id": "urn:accord:02c:profile:incompatible-v1", "new_profile_version": "0.2"}, {"old_profile_id": "urn:moirae:accord-02r3:predicate-applicability:fixture-v1", "old_profile_version": "1.0", "new_profile_id": "urn:moirae:accord-02e4:predicate-applicability:0.2", "new_profile_version": "0.2"}], "vector_profile_resolution": "EXACT_PROFILE_TYPE_ID_VERSION", "legacy_profile_policy": "RETIRED_UNAVAILABLE_TO_ACTIVE_CANDIDATE_SCOPE"},
        "retired_contracts": [{"contract_type": "PREDICATE_APPLICABILITY_PROFILE", "contract_id": "urn:moirae:accord-02r3:predicate-applicability:fixture-v1", "contract_version": "1.0", "retirement_policy": "NOT_ACTIVE_NOT_RESOLVABLE"}],
        "candidate_notes": {"candidate_only": True, "base_is_immutable": True, "repository_fallback": False, "specification_scope": "The R1 candidate is the exact sealed 0.1 package plus only the enumerated R1 replacements, additions, candidate instance contracts, canonicalization replacement, and versioned rule overlay.", "historical_e4_preserved": True, "rule_inventory_policy": "EXISTING_82_PLUS_VERSIONED_OVERLAY"},
    }
    write_json(R1 / "accord-02e4r1-specification-package-0.2.json", package)
    write_json(R1 / "accord-02e4r1-dual-review-findings.json", build_findings())
    print(json.dumps({"package": package["package_id"], "version": package["package_version"], "vectors": len(catalog["vectors"]), "rules": rules["active_rule_count"], "schemas": len(additions), "profile_replacements": len(package["profile_contract_replacements"])}, indent=2))


if __name__ == "__main__":
    build()
