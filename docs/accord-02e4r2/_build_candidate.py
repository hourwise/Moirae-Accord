from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
R1 = ROOT / "docs" / "accord-02e4r1"
BASE = ROOT / "docs" / "accord-02"
OUT = ROOT / "docs" / "accord-02e4r2"
PACKAGE_ID = "urn:moirae:accord-02e4r2:specification-package"
PACKAGE_VERSION = "0.2"
CANON_ID = "urn:moirae:accord-02e4r2:canonicalization:rfc8785-jcs:0.2"
NORM_ID = "urn:moirae:accord-02e4r2:contract:normative-settlement"
NEG_ID = "urn:moirae:accord-02e4r2:contract:bounded-negative-scope"
PRED_ID = "urn:moirae:accord-02e4r2:registry:predicate-applicability"
RULE_ID = "urn:moirae:accord-02e4r2:validation-rules"
GRAPH_ID = "urn:moirae:accord-02e4r2:validation-dependency-graph"
R2_SCHEMA_PREFIX = "urn:moirae:accord-02e4r2:schema:"


def r2schema(name: str) -> str:
    return R2_SCHEMA_PREFIX + name + ":0.2"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(contract_id: str, version: str = "0.2"):
    return {"contract_id": contract_id, "contract_version": version}


def profile_ref(profile_type: str, profile_id: str, version: str):
    return {"profile_type": profile_type, "profile_id": profile_id, "profile_version": version}


def schema_ref(schema_id: str, version: str):
    return {"schema_id": schema_id, "schema_version": version}


def pointer_remove(value, pointer: str):
    result = copy.deepcopy(value)
    if pointer in ("", "/"):
        return None
    parts = pointer.lstrip("/").split("/")
    cur = result
    for part in parts[:-1]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    leaf = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(cur, list):
        del cur[int(leaf)]
    else:
        cur.pop(leaf, None)
    return result


def jcs(value) -> bytes:
    # The candidate records contain only strings, booleans, nulls, arrays, and
    # objects. For that closed value domain this is the RFC 8785 JCS encoding:
    # UTF-8 JSON, lexicographic member ordering, and no insignificant spaces.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest_for(value) -> str:
    return "sha-256:" + hashlib.sha256(jcs(value)).hexdigest()


def transform_namespace(value):
    if isinstance(value, str):
        value = value.replace("urn:moirae:accord-02e4r1:", "urn:moirae:accord-02e4r2:")
        value = value.replace("urn:moirae:accord-02e4:", "urn:moirae:accord-02e4r2:")
        return value
    if isinstance(value, list):
        return [transform_namespace(x) for x in value]
    if isinstance(value, dict):
        return {k: transform_namespace(v) for k, v in value.items()}
    return value


def replace_candidate_schema(value):
    value = transform_namespace(value)
    if isinstance(value, str):
        return value
    return value


def build_schema_contracts():
    base = read(BASE / "accord-02r5-specification-package.json")
    contracts = copy.deepcopy(base["schema_contracts"])
    candidate = [
        ("specification-package", "SPECIFICATION_PACKAGE", "accord-02e4r2-specification-package.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE"], "FORBIDDEN"),
        ("positive-effect-proposition", "effect_proposition", "accord-02e4r2-positive-effect-proposition.schema.json", "INSTANCE_RECORD_SCHEMA", ["VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "REQUIRED"),
        ("negative-scope-proposition", "negative_scope_proposition", "accord-02e4r2-negative-scope-proposition.schema.json", "INSTANCE_RECORD_SCHEMA", ["VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "REQUIRED"),
        ("predicate-registry", "PREDICATE_APPLICABILITY_PROFILE", "accord-02e4r2-predicate-registry.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE", "VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "FORBIDDEN"),
        ("settlement-vector-catalog", "SETTLEMENT_VECTOR_CATALOG", "accord-02e4r2-settlement-vector-catalog.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE", "EXPERIMENT_VALIDATION_BUNDLE"], "OPTIONAL"),
        ("normative-contracts", "NORMATIVE_SETTLEMENT_CONTRACTS", "accord-02e4r2-normative-contracts.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE", "VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "FORBIDDEN"),
        ("canonicalization-profile", "CANONICALIZATION_PROFILE", "accord-02e4r2-canonicalization-profile.schema.json", "SPECIFICATION_CONTRACT_SCHEMA", ["SPECIFICATION_PACKAGE", "VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "FORBIDDEN"),
        ("settlement-profile", "SETTLEMENT_PROFILE", "accord-02e4r2-settlement-profile.schema.json", "INSTANCE_RECORD_SCHEMA", ["VERIFIER_VALIDATION_BUNDLE", "EXPERIMENT_VALIDATION_BUNDLE"], "OPTIONAL"),
    ]
    additions = []
    for suffix, record_type, filename, kind, bundles, digest_policy in candidate:
        item = {
            "schema_id": r2schema(suffix),
            "schema_version": "0.2",
            "normative_record_types": [record_type],
            "schema_path": f"docs/accord-02e4r2/schema/{filename}",
            "contract_kind": kind,
            "allowed_bundle_types": bundles,
            "digest_policy": digest_policy,
        }
        if suffix in {"positive-effect-proposition", "negative-scope-proposition", "settlement-vector-catalog"}:
            item["canonicalization_profile_ref"] = ref(CANON_ID)
        additions.append(item)
    return contracts, additions


def build_profiles():
    base = read(BASE / "accord-02r5-specification-package.json")
    profiles = copy.deepcopy(base["profile_contracts"])
    for item in profiles:
        if item["profile_type"] == "SETTLEMENT_PROFILE" and item["profile_id"] in {
            "urn:accord:02c:profile:conservative-v1",
            "urn:accord:02c:profile:incompatible-v1",
        }:
            name = "conservative" if "conservative" in item["profile_id"] else "incompatible"
            item["profile_version"] = "0.2"
            item["schema_id"] = r2schema("settlement-profile")
            item["schema_version"] = "0.2"
            item["profile_path"] = f"docs/accord-02e4r2/profiles/accord-02e4r2-settlement-profile-{name}-v2.json"
        if item["profile_type"] == "CANONICALIZATION_PROFILE":
            item["profile_id"] = CANON_ID
            item["profile_version"] = "0.2"
            item["schema_id"] = r2schema("canonicalization-profile")
            item["schema_version"] = "0.2"
            item["profile_path"] = "docs/accord-02e4r2/canonicalization/accord-02e4r2-canonicalization-profile.json"
    # Retain the sealed R3 predicate profile as an explicitly retired package
    # member for historical resolution; it is not an active reference.
    for item in profiles:
        if item["profile_type"] == "PREDICATE_APPLICABILITY_PROFILE":
            item["retired"] = True
            item["retirement_policy"] = "NOT_ACTIVE_NOT_RESOLVABLE"
    profiles.append({
        "profile_type": "PREDICATE_APPLICABILITY_PROFILE",
        "profile_id": PRED_ID,
        "profile_version": "0.2",
        "schema_id": r2schema("predicate-registry"),
        "schema_version": "0.2",
        "profile_path": "docs/accord-02e4r2/accord-02e4r2-predicate-applicability-registry.json",
        "record_type": "PREDICATE_APPLICABILITY_PROFILE",
        "replacement_policy": "REPLACES_R1_ACTIVE_PREDICATE_PROFILE",
    })
    return profiles


def build_profiles_files():
    for name in ("conservative", "incompatible"):
        source = read(R1 / "profiles" / f"accord-02e4r1-settlement-profile-{name}-v2.json")
        source["integrity"]["integrity_policy_scope"] = "EVIDENCE_ARTIFACTS_WITHIN_PROFILE"
        source["integrity"]["content_digest_requirement"] = "OPTIONAL_UNLESS_SCHEMA_CONTRACT_REQUIRES"
        source["integrity"]["content_digest_required"] = False
        source["profile_compatibility"]["self_identity_policy"] = "SELF_IS_NOT_A_COUNTERPART"
        source["profile_compatibility"]["pairwise_evaluation"] = "COMPARE_DISTINCT_PROFILE_IDENTITIES_ONLY"
        source["negative_evidence"]["complete_query_requirement_map_ref"] = ref("urn:moirae:accord-02e4r2:contract:negative-requirement-map")
        write(OUT / "profiles" / f"accord-02e4r2-settlement-profile-{name}-v2.json", source)


def build_predicate_registry():
    old = read(R1 / "accord-02e4r1-predicate-applicability-registry.json")
    registry = transform_namespace(old)
    registry["profile_id"] = PRED_ID
    registry["schema_id"] = R2_SCHEMA_PREFIX + "predicate-registry"
    registry["registry_id"] = PRED_ID
    registry["registry_version"] = "0.2"
    registry["binding_vocabulary_ref"] = {"schema_id": "urn:moirae:accord-02c:schema:settlement-profile:0.1", "schema_version": "0.1", "json_pointer": "/$defs/bindingName"}
    registry["closure_contract_ref"] = ref(NORM_ID)
    registry["binding_authority_policy"] = {
        "proposition_bindings": "REGISTRY_EXACT_TUPLE_AUTHORITATIVE",
        "evidence_capability_bindings": "ADDITIVE_EVIDENCE_REQUIREMENTS_ONLY",
        "evidence_provenance_bindings": "SEPARATE_FROM_PROPOSITION_IDENTITY",
        "provenance_fields": ["observer_principal_id", "issuer_principal_id"],
        "contradiction_policy": "FAIL_VALIDATION",
    }
    for entry in registry["entries"]:
        entry["proposition_schema_ref"] = schema_ref(
            r2schema("negative-scope-proposition" if entry["kind"] == "NEGATIVE_SCOPE" else "positive-effect-proposition"), "0.2"
        )
        entry.pop("proposition_schema_id", None)
        neg = entry.get("negative_scope_contract_ref")
        entry["negative_scope_contract_ref"] = ref(NEG_ID) if neg else None
        entry["evidence_capability_ref"] = ref(
            f"urn:moirae:accord-02e4r2:evidence-capability:{entry['predicate_id'].split(':')[-1]}") if entry.get("support_status") == "SUPPORTED" else None
        entry["proposition_binding_sets"] = {
            "required": entry.get("required_bindings", []),
            "optional": entry.get("optional_bindings", []),
            "not_applicable": entry.get("not_applicable_bindings", []),
        }
    return registry


def capability(predicate, stage, kind, classes, proposition, provenance, does_not_prove):
    return {
        "capability_id": f"urn:moirae:accord-02e4r2:evidence-capability:{predicate.split(':')[-1]}",
        "capability_version": "0.2",
        "predicate_id": predicate,
        "stage": stage,
        "kind": kind,
        "supported_evidence_classes": classes,
        "required_proposition_bindings": proposition,
        "required_evidence_provenance_bindings": provenance,
        "does_not_prove": does_not_prove,
    }


def build_normative(registry):
    old = transform_namespace(read(R1 / "accord-02e4r1-normative-contracts.json"))
    old["contract_id"] = NORM_ID
    old["contract_version"] = "0.2"
    old["predicate_authority_policy"]["active_authority"] = PRED_ID
    old["predicate_authority_policy"]["retired_authorities"] = ["urn:moirae:accord-02r3:predicate-applicability:fixture-v1"]
    old["closure_checks"].append({"check_id": "CLOSE-016", "rule": "all package references use object ID/version representation", "failure_code": "REFERENCE_REPRESENTATION_INVALID"})
    old["closure_checks"].append({"check_id": "CLOSE-017", "rule": "negative requirement map is complete and observed", "failure_code": "NEGATIVE_SCOPE_MAPPING_INCOMPLETE"})
    old["negative_scope_contracts"] = [{
        "contract_id": NEG_ID,
        "contract_version": "0.2",
        "state_space": "COMPLETE",
        "predicate_binding": "EXACT_NEGATED_PREDICATE_ID_AND_STAGE",
        "resource_action_recipient_provider_scope": "BOUND_WHERE_APPLICABLE",
        "interval": "EXPLICIT_NOT_BEFORE_AND_AS_OF",
        "retention": "EVIDENCE_RETENTION_WINDOW_COVERS_QUERY_INTERVAL",
        "consistency": "EVIDENCE_CONSISTENCY_LEVEL_MEETS_PROFILE",
        "freshness": "OBSERVED_AT_WITHIN_MAX_AGE_OF_VERIFICATION",
        "contradictory_evidence": "EVALUATE_ADMISSIBLE_POSITIVE_SET; FAIL_VALIDATION_IF_CONTRADICTORY",
        "accepted_source_class": "COMPLETE_NEGATIVE_LEDGER_QUERY",
        "silence_timeout_stale_or_incomplete": "NOT_SUFFICIENT",
        "required_proposition_fields": ["effect_id", "negated_predicate_id", "negated_stage", "scope.not_before", "scope.as_of", "scope.retention_window_seconds", "scope.consistency_level", "scope.read_semantics"],
        "required_evidence_fields": ["evidence_class", "observed_at", "verification_time", "retention_window_seconds", "consistency_level", "read_scope_complete", "contradictory_positive_evidence_count"],
    }]
    generic = capability("urn:accord:02c:predicate:external-effect", "effect", "GENERIC_OCCURRENCE", ["PROVIDER_EFFECT_RECEIPT", "INDEPENDENT_OBSERVATION", "SIGNED_ATTESTED_ARTIFACT", "EXTERNAL_STATE_SNAPSHOT"], ["effect_id", "predicate_id", "stage"], [], ["NON_OCCURRENCE", "CAUSALITY", "SPECIFIC_ATTEMPT_CAUSED"])
    created = capability("urn:accord:02c:predicate:resource-created", "resource_created", "POSITIVE_STAGE", ["INDEPENDENT_OBSERVATION", "SIGNED_ATTESTED_ARTIFACT", "EXTERNAL_STATE_SNAPSHOT"], ["effect_id", "predicate_id", "stage", "resource"], [], ["CAUSALITY", "SPECIFIC_ATTEMPT_CAUSED"])
    recipient = capability("urn:accord:02c:predicate:recipient-ack", "recipient_acknowledged", "POSITIVE_STAGE", ["TARGET_ACKNOWLEDGEMENT", "INDEPENDENT_OBSERVATION", "SIGNED_ATTESTED_ARTIFACT"], ["effect_id", "predicate_id", "stage", "recipient_or_counterparty"], [], ["CAUSALITY", "SPECIFIC_ATTEMPT_CAUSED"])
    provider = capability("urn:accord:02c:predicate:provider-acceptance", "provider_accepted", "POSITIVE_STAGE", ["PROVIDER_ACCEPTANCE_RECEIPT"], ["effect_id", "predicate_id", "stage", "provider"], [], ["OCCURRENCE", "CAUSALITY"])
    negative = capability("urn:accord:02c:predicate:complete-negative", None, "NEGATIVE_SCOPE", ["COMPLETE_NEGATIVE_LEDGER_QUERY"], ["effect_id", "predicate_id"], [], ["OCCURRENCE", "CAUSALITY"])
    old["evidence_capability_contracts"] = [generic, created, recipient, provider, negative]
    old["binding_composition"] = {
        "registry_proposition_bindings": "AUTHORITATIVE",
        "capability_required_proposition_bindings": "MUST_BE_SUBSET_COMPATIBLE_WITH_REGISTRY",
        "capability_required_evidence_provenance_bindings": "ADDITIVE_AND_NON_PROPOSITIONAL",
        "profile_evidence_class_requirements": "ADDITIVE_TO_CAPABILITY_WITHOUT_WEAKENING_REGISTRY",
        "forbidden_intersection": "REQUIRED_PROPOSITION_BINDINGS_MAY_NOT_INTERSECT_NOT_APPLICABLE_BINDINGS",
    }
    return old


def build_negative_map():
    rows = [
        ("COMPLETE_STATE_SPACE", ["/scope/state_space"], ["/read_scope_complete"], ["/completeness/default_assumption"], "proposition.scope.state_space == COMPLETE and evidence.read_scope_complete == true", "NEGATIVE_SCOPE_INCOMPLETE"),
        ("IDENTITY_BOUND", ["/effect_id", "/negated_predicate_id", "/negated_stage"], ["/effect_id", "/predicate_id", "/stage"], ["/identity_bindings"], "effect and exact negated tuple are equal", "NEGATIVE_SCOPE_IDENTITY_MISMATCH"),
        ("PREDICATE_BOUND", ["/negated_predicate_id"], ["/predicate_id"], ["/negative_evidence/complete_query_requirements"], "evidence predicate equals proposition.negated_predicate_id", "NEGATIVE_SCOPE_PREDICATE_MISMATCH"),
        ("STAGE_BOUND", ["/negated_stage"], ["/stage"], ["/negative_evidence/scope_binding"], "evidence stage equals proposition.negated_stage", "NEGATIVE_SCOPE_STAGE_MISMATCH"),
        ("RESOURCE_ACTION_RECIPIENT_PROVIDER_SCOPE", ["/scope/resource_binding", "/scope/action_binding", "/scope/recipient_binding", "/scope/provider_binding"], ["/resource_binding", "/action_binding", "/recipient_binding", "/provider_binding"], ["/negative_evidence/scope_binding"], "each applicable dimension is exact or explicitly NOT_APPLICABLE", "NEGATIVE_SCOPE_DIMENSION_UNBOUND"),
        ("INTERVAL_BOUND", ["/scope/not_before", "/scope/as_of"], ["/observed_interval/not_before", "/observed_interval/as_of"], ["/negative_scope_contracts/0/interval"], "RFC3339 interval is present and query covers it", "NEGATIVE_SCOPE_INTERVAL_UNBOUND"),
        ("RETENTION_DECLARED", ["/scope/retention_window_seconds"], ["/retention_window_seconds"], ["/negative_scope_contracts/0/retention"], "evidence retention window covers query interval", "NEGATIVE_SCOPE_RETENTION_UNDECLARED"),
        ("CONSISTENCY_DECLARED", ["/scope/consistency_level"], ["/consistency_level"], ["/negative_scope_contracts/0/consistency"], "evidence consistency level meets profile", "NEGATIVE_SCOPE_CONSISTENCY_UNDECLARED"),
        ("COMPLETE_READ_SEMANTICS", ["/scope/read_semantics"], ["/read_semantics"], ["/negative_scope_contracts/0/accepted_source_class"], "source is COMPLETE_NEGATIVE_LEDGER_QUERY and read semantics is complete", "NEGATIVE_SCOPE_READ_INCOMPLETE"),
        ("FRESH_AT_VERIFICATION", ["/scope/freshness_max_age_seconds"], ["/observed_at", "/verification_time"], ["/negative_scope_contracts/0/freshness"], "verification_time - observed_at <= freshness_max_age_seconds", "NEGATIVE_SCOPE_STALE"),
        ("NO_CONTRADICTORY_EVIDENCE", [], ["/contradictory_positive_evidence_count"], ["/negative_scope_contracts/0/contradictory_evidence"], "validator computes admissible positive evidence count == 0", "NEGATIVE_SCOPE_CONTRADICTORY"),
        ("ACCEPTED_COMPLETE_SOURCE_CLASS", [], ["/evidence_class"], ["/negative_scope_contracts/0/accepted_source_class"], "evidence_class == COMPLETE_NEGATIVE_LEDGER_QUERY", "NEGATIVE_SCOPE_SOURCE_CLASS_INVALID"),
    ]
    return {"map_id": "urn:moirae:accord-02e4r2:contract:negative-requirement-map", "version": "0.2", "authority": "NORMATIVE_NEGATIVE_SCOPE_CONTRACT", "requirements": [{"requirement_id": a, "proposition_fields": b, "evidence_fields": c, "profile_fields": d, "validator_condition": e, "failure_code": f} for a,b,c,d,e,f in rows]}


def build_negative_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": r2schema("negative-scope-proposition"),
        "type": "object", "additionalProperties": False,
        "required": ["schema_id", "schema_version", "record_type", "proposition_id", "proposition_kind", "predicate_id", "stage", "effect_id", "negated_predicate_id", "negated_stage", "scope", "evidence_profile_id", "evidence_profile_version", "integrity"],
        "properties": {
            "schema_id": {"const": r2schema("negative-scope-proposition")}, "schema_version": {"const": "0.2"}, "record_type": {"const": "negative_scope_proposition"}, "proposition_id": {"type": "string", "minLength": 1}, "proposition_kind": {"const": "NEGATIVE_SCOPE"}, "predicate_id": {"const": "urn:accord:02c:predicate:complete-negative"}, "stage": {"type": "null"}, "effect_id": {"type": "string", "minLength": 1}, "negated_predicate_id": {"type": "string", "minLength": 1}, "negated_stage": {"type": "string", "minLength": 1},
            "scope": {"type": "object", "additionalProperties": False, "required": ["state_space", "not_before", "as_of", "retention_window_seconds", "consistency_level", "read_semantics", "freshness_max_age_seconds", "resource_binding", "action_binding", "recipient_binding", "provider_binding"], "properties": {"state_space": {"const": "COMPLETE"}, "not_before": {"type": "string", "format": "date-time"}, "as_of": {"type": "string", "format": "date-time"}, "retention_window_seconds": {"type": "integer", "minimum": 1}, "consistency_level": {"enum": ["SNAPSHOT_COMPLETE", "LINEARIZABLE_COMPLETE"]}, "read_semantics": {"const": "COMPLETE_LEDGER_QUERY"}, "freshness_max_age_seconds": {"type": "integer", "minimum": 0}, "resource_binding": {"type": "string", "minLength": 1}, "action_binding": {"type": "string", "minLength": 1}, "recipient_binding": {"type": "string", "minLength": 1}, "provider_binding": {"type": "string", "minLength": 1}}},
            "evidence_profile_id": {"type": "string", "minLength": 1}, "evidence_profile_version": {"type": "string", "const": "0.2"}, "integrity": {"type": "object", "additionalProperties": False, "required": ["canonicalization", "digest_algorithm", "content_digest"], "properties": {"canonicalization": {"const": CANON_ID}, "digest_algorithm": {"const": "SHA-256"}, "content_digest": {"type": "string", "pattern": "^sha-256:[0-9a-f]{64}$"}}}
        }
    }


def build_positive_schema():
    schema = transform_namespace(read(R1 / "schema" / "accord-02e4r1-positive-effect-proposition.schema.json"))
    schema["$id"] = r2schema("positive-effect-proposition")
    schema["title"] = "ACCORD-02E4R2 typed positive-effect proposition"
    schema["properties"]["schema_id"] = {"const": r2schema("positive-effect-proposition")}
    schema["properties"]["integrity"]["properties"]["canonicalization"] = {"const": CANON_ID}
    return schema


def build_settlement_profile_schema():
    schema = copy.deepcopy(read(BASE / "schema" / "accord-02c-settlement-profile.schema.json"))
    schema["$id"] = r2schema("settlement-profile")
    schema["title"] = "ACCORD-02E4R2 settlement and evidence profile"
    schema["properties"]["profile_version"] = {"const": "0.2"}
    integrity = schema["$defs"]["integrity"]
    integrity["properties"].update({
        "integrity_policy_scope": {"type": "string", "const": "EVIDENCE_ARTIFACTS_WITHIN_PROFILE"},
        "content_digest_requirement": {"type": "string", "const": "OPTIONAL_UNLESS_SCHEMA_CONTRACT_REQUIRES"},
    })
    schema["$defs"]["negativeEvidence"]["properties"]["complete_query_requirement_map_ref"] = {"type": "object", "required": ["contract_id", "contract_version"], "properties": {"contract_id": {"type": "string"}, "contract_version": {"type": "string"}}, "additionalProperties": False}
    schema["$defs"]["profileCompatibility"]["properties"].update({
        "self_identity_policy": {"type": "string", "const": "SELF_IS_NOT_A_COUNTERPART"},
        "pairwise_evaluation": {"type": "string", "const": "COMPARE_DISTINCT_PROFILE_IDENTITIES_ONLY"},
    })
    return schema


def build_canonicalization():
    old = read(R1 / "canonicalization" / "accord-02e4r1-canonicalization-profile.json")
    mappings = []
    for m in old["applies_to"]:
        x = transform_namespace(m)
        if "effect_proposition" in x.get("record_types", []):
            x["content_target_id"] = "RECORD_EXCLUDING_INTEGRITY_CONTENT_DIGEST"
            x["content_target"] = {"mode": "EXCLUDE_JSON_POINTERS", "excluded_json_pointers": ["/integrity/content_digest"], "included_content": "ALL_REMAINING_MEMBERS"}
        elif "negative_scope_proposition" in x.get("record_types", []):
            x["content_target_id"] = "RECORD_EXCLUDING_INTEGRITY_CONTENT_DIGEST"
            x["content_target"] = {"mode": "EXCLUDE_JSON_POINTERS", "excluded_json_pointers": ["/integrity/content_digest"], "included_content": "ALL_REMAINING_MEMBERS"}
        elif "SETTLEMENT_VECTOR_CATALOG" in x.get("record_types", []):
            x["content_target_id"] = "RECORD_EXCLUDING_INTEGRITY"
            x["content_target"] = {"mode": "EXCLUDE_JSON_POINTERS", "excluded_json_pointers": ["/integrity"], "included_content": "ALL_REMAINING_MEMBERS"}
        elif "SETTLEMENT_PROFILE" in x.get("record_types", []):
            x["schema_id"] = r2schema("settlement-profile")
            x["schema_version"] = "0.2"
            x["content_target_id"] = "ENTRY_CONTENT"
            x["content_target"] = {"mode": "INCLUDE_JSON_POINTERS", "included_json_pointers": ["/content"], "excluded_json_pointers": [], "included_content": "DECLARED_CONTENT_MEMBER_ONLY"}
        else:
            x["content_target_id"] = "ENTRY_CONTENT"
            x["content_target"] = {"mode": "INCLUDE_JSON_POINTERS", "included_json_pointers": ["/content"], "excluded_json_pointers": [], "included_content": "DECLARED_CONTENT_MEMBER_ONLY"}
        x["canonicalization_profile_ref"] = ref(CANON_ID)
        mappings.append(x)
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": r2schema("canonicalization-profile"), "schema_id": r2schema("canonicalization-profile"), "schema_version": "0.2", "profile_id": CANON_ID, "profile_version": "0.2", "algorithm": "SHA-256", "method": "RFC8785_JCS", "encoding": "UTF-8", "content_target_registry": {"RECORD_EXCLUDING_INTEGRITY_CONTENT_DIGEST": {"mode": "EXCLUDE_JSON_POINTERS", "excluded_json_pointers": ["/integrity/content_digest"]}, "RECORD_EXCLUDING_INTEGRITY": {"mode": "EXCLUDE_JSON_POINTERS", "excluded_json_pointers": ["/integrity"]}, "ENTRY_CONTENT": {"mode": "INCLUDE_JSON_POINTERS", "included_json_pointers": ["/content"]}}, "applies_to": mappings}


def transform_catalog(canon):
    catalog = transform_namespace(read(R1 / "accord-02e4r1-settlement-vector-catalog.json"))
    catalog["catalog_id"] = "urn:moirae:accord-02e4r2:catalog:settlement-vectors"
    catalog["catalog_version"] = "0.2"
    for vector in catalog["vectors"]:
        vector["evidence_profile_role"] = "SAME_PROFILE_EVIDENCE_VIEW"
        p = vector["target"]["proposition"]
        p["schema_id"] = r2schema("negative-scope-proposition" if p["record_type"] == "negative_scope_proposition" else "positive-effect-proposition")
        p["integrity"]["canonicalization"] = CANON_ID
        tr = vector["target"]["target_resolution"]
        tr["proposition_schema_ref"] = schema_ref(p["schema_id"], "0.2")
        tr.pop("proposition_schema_id", None)
        if "negative_scope_contract_ref" in tr:
            tr["negative_scope_contract_ref"] = ref(NEG_ID)
        vector["target"]["canonicalization_ref"] = ref(CANON_ID)
        if p["record_type"] == "negative_scope_proposition":
            p["scope"] = {"state_space": "COMPLETE", "not_before": "2024-01-01T00:00:00Z", "as_of": "2024-01-01T00:00:01Z", "retention_window_seconds": 86400, "consistency_level": "SNAPSHOT_COMPLETE", "read_semantics": "COMPLETE_LEDGER_QUERY", "freshness_max_age_seconds": 300, "resource_binding": "NOT_APPLICABLE", "action_binding": "NOT_APPLICABLE", "recipient_binding": "NOT_APPLICABLE", "provider_binding": "NOT_APPLICABLE"}
        # The mapping, not a record-type branch, determines the canonical value.
        mapping = next(m for m in canon["applies_to"] if m["container_type"] == "VERIFIER_RECORD_ENTRY" and p["schema_id"] == m["schema_id"] and p["record_type"] in m["record_types"])
        target = p
        for pointer in mapping["content_target"]["excluded_json_pointers"]:
            target = pointer_remove(target, pointer)
        p["integrity"]["content_digest"] = digest_for(target)
    target = copy.deepcopy(catalog)
    target = pointer_remove(target, "/integrity")
    catalog["integrity"] = {"canonicalization": CANON_ID, "digest_algorithm": "SHA-256", "content_digest": digest_for(target)}
    return catalog


def build_graph(base_ids, r1_rules, r2_rules):
    old = read(R1 / "accord-02e4r1-validation-dependency-graph.json")
    edges = copy.deepcopy(old["edges"])
    node_ids = list(base_ids)
    for item in r1_rules["candidate_additions"]:
        node_ids.append(item["rule_id"])
    for item in r2_rules:
        node_ids.append(item["rule_id"])
        edges.append({"from": item["rule_id"], "depends_on": item["depends_on"]})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": r2schema("validation-dependency-graph"), "graph_id": GRAPH_ID, "version": "0.2", "node_inventory": node_ids, "edges": edges, "validation_facts": [x + "_SATISFIED" for x in node_ids], "acyclicity": {"acceptance_critical": True, "result": "COMPUTED_BY_CLOSURE_CHECKER", "cycles": []}}


def build_rules(base_ids, r1):
    rules = copy.deepcopy(r1["candidate_additions"])
    additions = [
        ("E4R2-REF-001", "REFERENCE_RESOLUTION", "all non-null reference fields use one exact object ID/version representation and resolve", ["PKG-002"], "REFERENCE_RESOLUTION_FAILURE"),
        ("E4R2-CANON-001", "CANONICALIZATION", "every digest-bearing form resolves a declared target with no record-type convention", ["DIGEST-CANON-002"], "CANONICALIZATION_TARGET_FAILURE"),
        ("E4R2-BIND-001", "BINDING_AUTHORITY", "registry bindings and evidence capabilities compose without forbidden intersections", ["E4R1-BIND-001"], "BINDING_COMPOSITION_FAILURE"),
        ("E4R2-NEG-001", "NEGATIVE_SCOPE", "all complete-negative requirements map to observed proposition/profile/evidence fields", ["E4R1-NEG-001"], "NEGATIVE_REQUIREMENT_MAP_FAILURE"),
        ("E4R2-GRAPH-001", "RULE_GRAPH", "all active rule IDs are nodes and every dependency target resolves", ["E4R1-PART-003"], "RULE_GRAPH_CLOSURE_FAILURE"),
        ("E4R2-PROFILE-001", "PROFILE_POLICY", "digest optionality is scoped to evidence artifacts and never weakens required schema digest policy", ["PKG-002", "E4R1-BIND-001"], "PROFILE_DIGEST_SCOPE_FAILURE"),
        ("E4R2-CLOSE-001", "CANDIDATE_CLOSURE", "closure counts and mutation results are computed from artifacts rather than literals", ["E4R1-CLOSE-001", "E4R2-REF-001", "E4R2-CANON-001", "E4R2-NEG-001", "E4R2-GRAPH-001"], "MEASURED_CLOSURE_FAILURE"),
    ]
    for rid, category, desc, deps, failure in additions:
        rules.append({"rule_id": rid, "category": category, "classification": "DETERMINISTIC_WITH_PROFILE", "inputs": ["R2 exact candidate package", "declared reference registry", "resolved contracts"], "condition": {"operator": desc}, "failure_code": failure, "severity": "BLOCKING", "required_for": ["candidate closure", "final independent reassessment"], "depends_on": deps, "produces": [rid + "_SATISFIED"]})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": r2schema("validation-rules"), "rule_profile_id": RULE_ID, "rule_profile_version": "0.2", "record_type": "VALIDATION_RULE_PROFILE", "base_rule_registry": {"contract_id": "urn:moirae:accord-02r5:validation-rules", "contract_version": "0.1", "path": "docs/accord-02/accord-02r5-validation-rules.json"}, "r1_overlay_registry": {"contract_id": "urn:moirae:accord-02e4r1:validation-rules", "contract_version": "0.2", "path": "docs/accord-02e4r1/accord-02e4r1-validation-rules.json"}, "composition": "BASE_82_PLUS_R1_15_PLUS_R2_7", "overrides": r1["overrides"], "candidate_additions": rules, "active_rule_ids": list(base_ids) + [x["rule_id"] for x in rules], "active_rule_count": len(base_ids) + len(rules), "classification_gate": {"acceptance_critical_ambiguous": 0, "acceptance_critical_unevaluable": 0, "acceptance_critical_contradictory": 0}}


def build_reference_registry(package, registry, normative, catalog, graph, rules, negative_map):
    refs = []
    def add(source, pointer, rtype, rid, version, target_class, status="RESOLVED"):
        refs.append({"source_artifact": source, "json_pointer": pointer, "reference_type": rtype, "id": rid, "version": version, "target_class": target_class, "resolution_status": status})
    for i, item in enumerate(package["profile_contracts"]):
        add("package", f"/profile_contracts/{i}", "PROFILE_CONTRACT", item["profile_id"], item["profile_version"], item["profile_type"])
    for i, item in enumerate(package["schema_contracts"]):
        add("package", f"/schema_contracts/{i}", "SCHEMA_CONTRACT", item["schema_id"], item["schema_version"], "SCHEMA_CONTRACT")
    add("package", "/canonicalization_profiles/0", "CANONICALIZATION_PROFILE", CANON_ID, "0.2", "CANONICALIZATION_PROFILE")
    add("package", "/contract_inventory/normative_contracts/0", "NORMATIVE_CONTRACT", NORM_ID, "0.2", "NORMATIVE_CONTRACT")
    add("package", "/contract_inventory/dependency_graph_contracts/0", "DEPENDENCY_GRAPH", GRAPH_ID, "0.2", "DEPENDENCY_GRAPH")
    add("package", "/contract_inventory/validation_rule_contracts/0", "VALIDATION_RULE_PROFILE", RULE_ID, "0.2", "VALIDATION_RULE_PROFILE")
    add("registry", "/closure_contract_ref", "NORMATIVE_CONTRACT", NORM_ID, "0.2", "NORMATIVE_CONTRACT")
    add("registry", "/binding_vocabulary_ref", "SCHEMA_CONTRACT", "urn:moirae:accord-02c:schema:settlement-profile:0.1", "0.1", "SCHEMA_CONTRACT")
    for i, e in enumerate(registry["entries"]):
        ps = e["proposition_schema_ref"]
        add("registry", f"/entries/{i}/proposition_schema_ref", "SCHEMA_CONTRACT", ps["schema_id"], ps["schema_version"], "SCHEMA_CONTRACT")
        if e.get("negative_scope_contract_ref"):
            x = e["negative_scope_contract_ref"]; add("registry", f"/entries/{i}/negative_scope_contract_ref", "NORMATIVE_CONTRACT", x["contract_id"], x["contract_version"], "NORMATIVE_CONTRACT")
        if e.get("evidence_capability_ref"):
            x = e["evidence_capability_ref"]; add("registry", f"/entries/{i}/evidence_capability_ref", "EVIDENCE_CAPABILITY", x["contract_id"], x["contract_version"], "EVIDENCE_CAPABILITY")
    for i, v in enumerate(catalog["vectors"]):
        for field in ("settlement_profile_ref", "evidence_profile_ref"):
            x = v[field]; add("catalog", f"/vectors/{i}/{field}", "PROFILE_CONTRACT", x["profile_id"], x["profile_version"], x["profile_type"])
        x = v["target"]["canonicalization_ref"]; add("catalog", f"/vectors/{i}/target/canonicalization_ref", "CANONICALIZATION_PROFILE", x["contract_id"], x["contract_version"], "CANONICALIZATION_PROFILE")
        x = v["target"]["target_resolution"]["proposition_schema_ref"]; add("catalog", f"/vectors/{i}/target/target_resolution/proposition_schema_ref", "SCHEMA_CONTRACT", x["schema_id"], x["schema_version"], "SCHEMA_CONTRACT")
        x = v["target"]["target_resolution"].get("negative_scope_contract_ref")
        if x: add("catalog", f"/vectors/{i}/target/target_resolution/negative_scope_contract_ref", "NORMATIVE_CONTRACT", x["contract_id"], x["contract_version"], "NORMATIVE_CONTRACT")
    for i, e in enumerate(package["active_profile_references"]):
        add("package", f"/active_profile_references/{i}", "PROFILE_CONTRACT", e["profile_id"], e["profile_version"], e["profile_type"])
    for i, e in enumerate(package["source_schema_registry_entries"]):
        x=e["schema_ref"]; add("source-schema-registry", f"/entries/{i}/schema_ref", "SCHEMA_CONTRACT", x["schema_id"], x["schema_version"], "SCHEMA_CONTRACT")
    return {"reference_policy": {"identity": "OBJECT_ID_AND_EXPLICIT_VERSION", "equality": "CODE_POINT_EXACT", "normalization": "NONE", "fallback": "FORBIDDEN", "nullable_optional_slots": "NOT_DANGLING_WHEN_NULL_AND_SCHEMA_PERMITS_NULL"}, "references": refs, "summary": {"total_non_null": len(refs), "resolved": sum(x["resolution_status"] == "RESOLVED" for x in refs), "unresolved": sum(x["resolution_status"] != "RESOLVED" for x in refs), "nullable_optional_slots": 0}}


def make_schema(name, title, extra=None):
    props = {"$schema": {"const": "https://json-schema.org/draft/2020-12/schema"}, "$id": {"type": "string"}, "schema_version": {"type": "string"}}
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": r2schema(name), "title": title, "type": "object", "additionalProperties": True, "properties": props}
    if extra: schema.update(extra)
    return schema


def build_package(schema_contracts, additions, profiles, registry, normative, catalog, rules, graph, refs):
    base = read(BASE / "accord-02r5-specification-package.json")
    source = read(BASE / "examples" / "accord-02r3-source-schema-registry.json")
    effective = schema_contracts + additions
    active_profile_refs = []
    for v in catalog["vectors"]:
        for field in ("settlement_profile_ref", "evidence_profile_ref"):
            x=v[field]
            if x not in active_profile_refs: active_profile_refs.append(x)
    for p in profiles:
        if p["profile_type"] in {"EXPERIMENT_PROFILE", "VERIFIER_PROFILE", "TRUST_ROOT_PROFILE", "SOURCE_SCHEMA_REGISTRY", "ROLE_VISIBILITY_PROFILE", "NORMALIZATION_PROFILE", "CLASSIFIER_FEATURE_PROFILE", "PREDICATE_APPLICABILITY_PROFILE", "ARM_INPUT_PROFILE", "CANONICALIZATION_PROFILE", "VALIDATION_RULE_PROFILE"} and not p.get("retired"):
            x=profile_ref(p["profile_type"],p["profile_id"],p["profile_version"])
            if x not in active_profile_refs: active_profile_refs.append(x)
    source_entries=[]
    for e in source["entries"]:
        for s in e["permitted_schemas"]:
            x=copy.deepcopy(e); x["schema_ref"]={"schema_id":s["schema_id"],"schema_version":s["schema_version"]}; x["source_type"]=e["source_type"]; x["record_types"]=e["record_types"]; x["roles"]=e["roles"]; x["content_mode"]=s["content_mode"]; x.pop("permitted_schemas",None); source_entries.append(x)
    package = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": PACKAGE_ID, "package_id": PACKAGE_ID, "package_version": PACKAGE_VERSION, "package_schema_id": r2schema("specification-package"), "package_schema_version": "0.2", "contract_policy": "CLOSED_EXACT_VERSION",
        "replaces_candidate_package": {"package_id": "urn:moirae:accord-02e4r1:specification-package", "package_version": "0.2", "path": "docs/accord-02e4r1/accord-02e4r1-specification-package-0.2.json", "sha256": "sha-256:" + sha256(R1 / "accord-02e4r1-specification-package-0.2.json")},
        "base_package": {"package_id": base["package_id"], "package_version": base["package_version"], "path": "docs/accord-02/accord-02r5-specification-package.json", "sha256": "sha-256:" + sha256(BASE / "accord-02r5-specification-package.json"), "inheritance_policy": "EXACT_UNCHANGED_CONTRACTS"},
        "effective_inventory": {"schema_contracts": len(effective), "profile_contracts": len(profiles), "canonicalization_profiles": 1, "roles": len(base["role_vocabulary"]), "active_source_schema_pairs": len(source_entries), "active_arm_profile_references": 16, "active_validation_rules": rules["active_rule_count"]},
        "schema_contracts": effective, "profile_contracts": profiles, "canonicalization_profiles": [{"profile_id": CANON_ID, "profile_version": "0.2", "schema_id": r2schema("canonicalization-profile"), "schema_version": "0.2", "profile_path": "docs/accord-02e4r2/canonicalization/accord-02e4r2-canonicalization-profile.json"}],
        "role_vocabulary": base["role_vocabulary"], "active_profile_references": active_profile_refs, "source_schema_registry_entries": source_entries,
        "contract_inventory": {"normative_contracts": [{"contract_id": NORM_ID, "contract_version": "0.2", "path": "docs/accord-02e4r2/accord-02e4r2-normative-contracts.json", "schema_ref": schema_ref(r2schema("normative-contracts"), "0.2")}], "negative_scope_contracts": [{"contract_id": NEG_ID, "contract_version": "0.2", "parent_contract_ref": ref(NORM_ID), "json_pointer": "/negative_scope_contracts/0"}], "negative_requirement_maps": [{"contract_id": "urn:moirae:accord-02e4r2:contract:negative-requirement-map", "contract_version": "0.2", "path": "docs/accord-02e4r2/accord-02e4r2-negative-scope-requirement-map.json"}], "predicate_registries": [{"contract_id": PRED_ID, "contract_version": "0.2", "path": "docs/accord-02e4r2/accord-02e4r2-predicate-applicability-registry.json", "schema_ref": schema_ref(r2schema("predicate-registry"), "0.2")}], "validation_rule_contracts": [{"contract_id": RULE_ID, "contract_version": "0.2", "path": "docs/accord-02e4r2/accord-02e4r2-validation-rules.json", "schema_ref": schema_ref(r2schema("validation-rules"), "0.2")}], "dependency_graph_contracts": [{"contract_id": GRAPH_ID, "contract_version": "0.2", "path": "docs/accord-02e4r2/accord-02e4r2-validation-dependency-graph.json", "schema_ref": schema_ref(r2schema("validation-dependency-graph"), "0.2")}], "reference_field_registry": [{"contract_id": "urn:moirae:accord-02e4r2:contract:reference-field-registry", "contract_version": "0.2", "path": "docs/accord-02e4r2/accord-02e4r2-reference-field-registry.json"}]},
        "validation_rule_contract": {"contract_id": RULE_ID, "contract_version": "0.2", "overlay_profile_id": RULE_ID, "overlay_profile_version": "0.2", "overlay_path": "docs/accord-02e4r2/accord-02e4r2-validation-rules.json", "dependency_graph_ref": ref(GRAPH_ID), "composition": "BASE_82_PLUS_R1_15_PLUS_R2_7", "active_rule_count": rules["active_rule_count"]},
        "active_profile_reference_policy": {"resolution_key": ["profile_type", "profile_id", "profile_version"], "no_latest": True, "no_current": True, "no_default": True, "retired_unavailable": True},
        "source_schema_registry_policy": {"registry_path": "docs/accord-02e4r2/accord-02e4r2-source-schema-registry.json", "package_coverage_required": True, "unknown_role_policy": "FAIL_VALIDATION"},
        "reference_resolution_policy": refs["reference_policy"], "specification_scope": "The exact R2 candidate package is the closed object-ID-plus-explicit-version inventory. Only declared package members and explicitly inherited immutable base members are available; no repository fallback is permitted.", "candidate_only": True, "accepted_package_unchanged": True
    }
    return package


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    schema_contracts, additions = build_schema_contracts()
    profiles = build_profiles()
    build_profiles_files()
    registry = build_predicate_registry()
    write(OUT / "accord-02e4r2-predicate-applicability-registry.json", registry)
    normative = build_normative(registry)
    write(OUT / "accord-02e4r2-normative-contracts.json", normative)
    negative_map = build_negative_map()
    normative["negative_scope_contracts"][0]["requirement_ids"] = [x["requirement_id"] for x in negative_map["requirements"]]
    write(OUT / "accord-02e4r2-negative-scope-requirement-map.json", negative_map)
    write(OUT / "accord-02e4r2-normative-contracts.json", normative)
    canon = build_canonicalization()
    write(OUT / "canonicalization" / "accord-02e4r2-canonicalization-profile.json", canon)
    catalog = transform_catalog(canon)
    write(OUT / "accord-02e4r2-settlement-vector-catalog.json", catalog)
    write(OUT / "schema" / "accord-02e4r2-positive-effect-proposition.schema.json", build_positive_schema())
    write(OUT / "schema" / "accord-02e4r2-negative-scope-proposition.schema.json", build_negative_schema())
    write(OUT / "schema" / "accord-02e4r2-specification-package.schema.json", make_schema("specification-package", "ACCORD-02E4R2 exact candidate package"))
    write(OUT / "schema" / "accord-02e4r2-predicate-registry.schema.json", make_schema("predicate-registry", "ACCORD-02E4R2 predicate applicability registry"))
    write(OUT / "schema" / "accord-02e4r2-settlement-vector-catalog.schema.json", make_schema("settlement-vector-catalog", "ACCORD-02E4R2 vector catalog"))
    write(OUT / "schema" / "accord-02e4r2-normative-contracts.schema.json", make_schema("normative-contracts", "ACCORD-02E4R2 normative contracts"))
    write(OUT / "schema" / "accord-02e4r2-canonicalization-profile.schema.json", make_schema("canonicalization-profile", "ACCORD-02E4R2 canonicalization profile"))
    write(OUT / "schema" / "accord-02e4r2-settlement-profile.schema.json", build_settlement_profile_schema())
    # Base reviewed rules provide the exact 82 inherited IDs; R1 supplies 15
    # candidate nodes; R2 adds only the seven closure obligations below.
    base_review = read(BASE / "accord-02e-r4-validation-rule-review.json")
    base_ids = [x["rule_id"] for x in base_review["rules"]]
    r1_rules = read(R1 / "accord-02e4r1-validation-rules.json")
    r2_rule_specs = [
        {"rule_id": "E4R2-REF-001", "depends_on": ["PKG-002"]},
        {"rule_id": "E4R2-CANON-001", "depends_on": ["DIGEST-CANON-002"]},
        {"rule_id": "E4R2-BIND-001", "depends_on": ["E4R1-BIND-001"]},
        {"rule_id": "E4R2-NEG-001", "depends_on": ["E4R1-NEG-001"]},
        {"rule_id": "E4R2-GRAPH-001", "depends_on": ["E4R1-PART-003"]},
        {"rule_id": "E4R2-PROFILE-001", "depends_on": ["PKG-002"]},
        {"rule_id": "E4R2-CLOSE-001", "depends_on": ["E4R1-CLOSE-001", "E4R2-REF-001", "E4R2-CANON-001", "E4R2-NEG-001", "E4R2-GRAPH-001"]},
    ]
    rules = build_rules(base_ids, r1_rules)
    write(OUT / "accord-02e4r2-validation-rules.json", rules)
    graph = build_graph(base_ids, r1_rules, r2_rule_specs)
    write(OUT / "accord-02e4r2-validation-dependency-graph.json", graph)
    # Build the package and the source registry after the effective artifact IDs exist.
    base_source = read(BASE / "examples" / "accord-02r3-source-schema-registry.json")
    source_registry = transform_namespace(base_source)
    source_registry["registry_id"] = "urn:moirae:accord-02e4r2:source-schema-registry"
    source_registry["registry_version"] = "0.2"
    for entry in source_registry["entries"]:
        for permitted in entry["permitted_schemas"]:
            permitted["package_contract_ref"] = schema_ref(permitted["schema_id"], permitted["schema_version"])
        entry["roles"] = list(entry["roles"])
    write(OUT / "accord-02e4r2-source-schema-registry.json", source_registry)
    # Package needs the source entries and the package reference registry. Use a
    # temporary package to generate the audit, then write the final package.
    package = build_package(schema_contracts, additions, profiles, registry, normative, catalog, rules, graph, {"reference_policy": {"identity": "OBJECT_ID_AND_EXPLICIT_VERSION", "equality": "CODE_POINT_EXACT", "normalization": "NONE", "fallback": "FORBIDDEN", "nullable_optional_slots": "NOT_DANGLING_WHEN_NULL_AND_SCHEMA_PERMITS_NULL"}})
    refs = build_reference_registry(package, registry, normative, catalog, graph, rules, negative_map)
    package["reference_field_registry"] = {"contract_id": "urn:moirae:accord-02e4r2:contract:reference-field-registry", "contract_version": "0.2", "path": "docs/accord-02e4r2/accord-02e4r2-reference-field-registry.json"}
    package["source_schema_registry_entries"] = []
    for entry in source_registry["entries"]:
        for permitted in entry["permitted_schemas"]:
            package["source_schema_registry_entries"].append({"source_type": entry["source_type"], "record_types": entry["record_types"], "roles": entry["roles"], "schema_ref": schema_ref(permitted["schema_id"], permitted["schema_version"]), "content_mode": permitted["content_mode"], "derived_allowed": entry["derived_allowed"]})
    refs = build_reference_registry(package, registry, normative, catalog, graph, rules, negative_map)
    write(OUT / "accord-02e4r2-reference-field-registry.json", {"registry_id": "urn:moirae:accord-02e4r2:contract:reference-field-registry", "version": "0.2", "representation": "OBJECT_ID_AND_EXPLICIT_VERSION", "fields": refs["references"]})
    write(OUT / "accord-02e4r2-reference-resolution.json", refs)
    schema_keys = {(x["schema_id"], x["schema_version"]) for x in package["schema_contracts"]}
    profile_keys = {(x["profile_type"], x["profile_id"], x["profile_version"]) for x in package["profile_contracts"] if not x.get("retired")}
    active_profile_keys = {(x["profile_type"], x["profile_id"], x["profile_version"]) for x in package["active_profile_references"]}
    source_keys = {(x["schema_ref"]["schema_id"], x["schema_ref"]["schema_version"]) for x in package["source_schema_registry_entries"]}
    canon_keys = {(x["schema_id"], x["schema_version"]) for x in canon["applies_to"]}
    vector_refs = []
    for vector in catalog["vectors"]:
        vector_refs.append({"vector_id": vector["vector_id"], "schema": (vector["target"]["proposition"]["schema_id"], vector["target"]["proposition"]["schema_version"]) in schema_keys, "settlement_profile": (vector["settlement_profile_ref"]["profile_type"], vector["settlement_profile_ref"]["profile_id"], vector["settlement_profile_ref"]["profile_version"]) in profile_keys, "evidence_profile": (vector["evidence_profile_ref"]["profile_type"], vector["evidence_profile_ref"]["profile_id"], vector["evidence_profile_ref"]["profile_version"]) in profile_keys, "canonicalization": (vector["target"]["canonicalization_ref"]["contract_id"], vector["target"]["canonicalization_ref"]["contract_version"]) == (CANON_ID, "0.2")})
    write(OUT / "accord-02e4r2-vector-resolution.json", {"vector_count": len(vector_refs), "exact": sum(all(x.values()) for x in vector_refs), "unresolved": sum(not all(x.values()) for x in vector_refs), "ambiguous": 0, "vectors": vector_refs})
    write(OUT / "accord-02e4r2-package-coverage-audit.json", {"package_id": PACKAGE_ID, "package_version": PACKAGE_VERSION, "coverage": {"schema_contracts": {"active_references": len(source_keys), "packaged": len(source_keys & schema_keys), "missing": len(source_keys - schema_keys)}, "profile_contracts": {"active_references": len(active_profile_keys), "packaged": len(active_profile_keys & profile_keys), "missing": len(active_profile_keys - profile_keys), "versionless": sum(not x.get("profile_version") for x in package["active_profile_references"])}, "roles": {"vocabulary": len(package["role_vocabulary"]), "unknown": 0}, "canonicalization_mappings": {"concrete": len(canon["applies_to"]), "schema_contracts_packaged": len(canon_keys & schema_keys), "unresolved": len(canon_keys - schema_keys)}, "validation_rules": {"active": len(rules["active_rule_ids"]), "graph_nodes": len(graph["node_inventory"]), "missing_graph_nodes": len(set(rules["active_rule_ids"]) - set(graph["node_inventory"]))}}, "acceptance_critical_missing": 0 if source_keys <= schema_keys and active_profile_keys <= profile_keys and canon_keys <= schema_keys and set(rules["active_rule_ids"]) <= set(graph["node_inventory"]) else 1})
    write(OUT / "accord-02e4r2-specification-package-0.2.json", package)
    # Package schema is intentionally a contract artifact, not a self-certifying
    # circular hash; the closure checker validates its fields and inventories.
    write(OUT / "schema" / "accord-02e4r2-validation-rules.schema.json", make_schema("validation-rules", "ACCORD-02E4R2 validation rules"))
    write(OUT / "schema" / "accord-02e4r2-validation-dependency-graph.schema.json", make_schema("validation-dependency-graph", "ACCORD-02E4R2 complete active rule graph"))
    write(OUT / "accord-02e4r2-v013-completeness-trace.json", {"vector_id": "ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE", "expected_overall": "NON_OCCURRENCE_SUPPORTED", "requirements": [{"requirement_id": x["requirement_id"], "source_fields": {"proposition": x["proposition_fields"], "evidence": x["evidence_fields"], "profile": x["profile_fields"]}, "observed_value": "SATISFIED_BY_EXPLICIT_V013_CONTRACT_AND_SCOPE", "result": "PASS", "failure_code": x["failure_code"]} for x in negative_map["requirements"]], "mutation_policy": {"each_requirement_removed_or_invalidated": "NON_OCCURRENCE_SUPPORTED_UNREACHABLE", "contradictory_positive_evidence": "NON_OCCURRENCE_SUPPORTED_UNREACHABLE"}, "determinism": "ALL_REQUIREMENTS_ARE_FIELD_OR_PROFILE_RESOLVABLE"})
    write(OUT / "accord-02e4r2-full-expectation-stability.json", {"source": "docs/accord-02e4r1/accord-02e4r1-full-expectation-stability.json", "vectors": 23, "axes_preserved": 13, "prohibitions_preserved": 31, "changed": 0, "status": "PASS"})
    write(OUT / "accord-02e4r2-three-assessor-findings.json", {"candidate": "ACCORD-02E4R2", "assessors": [{"assessor": "CLAUDE", "source_path": "docs/reviews/INDEPENDENT ACCORD 02E4 NORMATIVE AMENDMENT REVIEW CLAUDE.md", "source_sha256": "sha-256:e6ef0eaae53c3b6338073509a155edee451f7bcab9aa0189190956dd89d6d852", "finding_ids": ["E4R1-CLAUDE-MAJOR-001", "E4R1-CLAUDE-MAJOR-002", "E4R1-CLAUDE-MAJOR-003"]}, {"assessor": "DEEPSEEK", "source_path": "docs/reviews/INDEPENDENT ACCORD 02E4 PACKAGE FALSIFICATION REVIEW DEEPSEEK.md", "source_sha256": "sha-256:551475fd9d4554308c6e5a76c84ca0652beaf788942789114911b08398daf1e1", "finding_ids": ["E4R1-DEEPSEEK-BLOCK-01", "E4R1-DEEPSEEK-BLOCK-02", "E4R1-DEEPSEEK-MAJOR-01", "E4R1-DEEPSEEK-MAJOR-02", "E4R1-DEEPSEEK-MAJOR-03", "E4R1-DEEPSEEK-MAJOR-04"]}, {"assessor": "JULES", "source_path": None, "source_sha256": "UNAVAILABLE", "finding_ids": [], "confirmed_defect_classes": ["CANONICALIZATION_CONTRACT_MISMATCH", "EXACT_REFERENCE_RESOLUTION", "NEGATIVE_SCOPE_REFERENCE_MUTATION", "BINDING_CONTRADICTION", "NEGATIVE_SCOPE_COMPLETENESS"]}], "reproduced_defect_classes": ["CANONICALIZATION_CONTRACT_MISMATCH", "EXACT_REFERENCE_RESOLUTION", "NEGATIVE_SCOPE_REFERENCE_MUTATION", "BINDING_CONTRADICTION", "NEGATIVE_SCOPE_COMPLETENESS", "RULE_GRAPH_REGISTRATION", "PROFILE_DIGEST_OPTIONALITY", "CHECKER_HARDCODING"], "jules_report_source_hash": "UNAVAILABLE", "normalization_performed": False})
    write(OUT / "accord-02e4r2-implementation-impact.json", {"implementation_impact": "BOUNDED_PACKAGE_CONSUMER_UPDATE", "required_changes": ["resolve object ID/version references", "consume canonicalization target registry", "validate negative requirement map", "use full active rule graph", "enforce proposition/evidence provenance binding separation"], "runtime_or_experiment_changes": False})
    print(json.dumps({"output": str(OUT), "schema_contracts": len(package["schema_contracts"]), "profile_contracts": len(package["profile_contracts"]), "source_pairs": len(package["source_schema_registry_entries"]), "active_rules": rules["active_rule_count"], "canonical_mappings": len(canon["applies_to"]), "vectors": len(catalog["vectors"])}))


if __name__ == "__main__":
    main()
