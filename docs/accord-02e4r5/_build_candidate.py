#!/usr/bin/env python3
"""Build the additive ACCORD-02E4R5 portable executable-contract candidate."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import rfc8785

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "accord-02e4r5"
SCHEMA = OUT / "schema"
NS = "urn:moirae:accord-02r5"
VERSION = "0.2"
PKG_ID = f"{NS}:specification-package"
CATALOG_ID = f"{NS}:source-vector-catalog"
CANON_ID = f"{NS}:canonicalization:rfc8785-jcs"


def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def emit(rel, value):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def jcs_digest(value):
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def ref(kind, object_id, version=VERSION, member_id=None):
    result = {"kind": kind, "id": object_id, "version": version}
    if member_id is not None:
        result["member_id"] = member_id
    return result


def identity(object_id, schema_name):
    return {"$schema": f"{NS}:schema:{schema_name}:{VERSION}", "$id": f"{object_id}:{VERSION}", "object_id": object_id, "object_version": VERSION}


def remove_pointer(value, pointer):
    result = copy.deepcopy(value)
    parts = pointer.split("/")[1:]
    cur = result
    for raw in parts[:-1]:
        token = raw.replace("~1", "/").replace("~0", "~")
        cur = cur[int(token)] if isinstance(cur, list) else cur[token]
    token = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(cur, list): del cur[int(token)]
    else: del cur[token]
    return result


def projected_digest(value, pointers):
    projected = copy.deepcopy(value)
    for pointer in pointers: projected = remove_pointer(projected, pointer)
    return jcs_digest(projected)


def object_ref_schema():
    return {"type": "object", "x-normative-reference": True, "required": ["kind", "id", "version"], "properties": {"kind": {"enum": ["CONTRACT", "SCHEMA", "PROFILE", "SOURCE_VECTOR", "CANONICALIZATION", "POLICY", "REQUIREMENT_MAP", "PACKAGE", "REGISTRY"]}, "id": {"type": "string", "minLength": 1}, "version": {"type": "string", "minLength": 1}, "member_id": {"type": "string", "minLength": 1}}, "additionalProperties": False}


def base_schema(name, required, properties, defs=None, object_id=None):
    oid = object_id or f"{NS}:{name}"
    result = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:schema:{name}:{VERSION}", "type": "object", "required": ["$schema", "$id", "object_id", "object_version", *required], "properties": {"$schema": {"const": f"{NS}:schema:{name}:{VERSION}"}, "$id": {"const": f"{oid}:{VERSION}"}, "object_id": {"const": oid}, "object_version": {"const": VERSION}, **properties}, "additionalProperties": False}
    result["$defs"] = {"objectRef": object_ref_schema(), **(defs or {})}
    return result


EXECUTABLE = {
    "BND-001", "BND-002", "BND-004", "BND-005", "LIN-001", "LIN-002", "LIN-007", "PROP-001", "EXT-001",
    "SRC-001", "SRC-002", "SRC-003", "PRED-001", "PRED-002", "PRED-003", "PRED-004", "DIGEST-001", "DIGEST-002", "DIGEST-003", "LIN-009", "PROP-006",
    "PKG-001", "PKG-002", "PROF-001", "PROF-002", "SCHEMA-001", "SCHEMA-002", "ROLE-001", "DIGEST-CANON-001", "DIGEST-CANON-002", "DIGEST-CANON-003", "SCENARIO-ID-001",
    "E4R1-PRED-001", "E4R1-PRED-002", "E4R1-PRED-003", "E4R1-AUTH-001", "E4R1-BIND-001", "E4R1-PROP-001", "E4R1-PART-001", "E4R1-PART-002", "E4R1-PART-003", "E4R1-NEG-001", "E4R1-NEG-002", "E4R1-ENT-001", "E4R1-CANON-001", "E4R1-EXPECT-001", "E4R1-CLOSE-001",
    "E4R2-REF-001", "E4R2-CANON-001", "E4R2-BIND-001", "E4R2-NEG-001", "E4R2-GRAPH-001", "E4R2-PROFILE-001", "E4R2-CLOSE-001",
}

DEFERRED_STAGE = {"ORACLE_BOUNDARY": "EXPERIMENT_ASSEMBLY", "ARM_ISOLATION": "EXPERIMENT_INPUT_ASSEMBLY", "RAW_OUTPUT": "PROVIDER_EXECUTION_CAPTURE", "PROJECTION": "VERIFIER_EXECUTION", "SCORE_SEPARATION": "SCORING", "RUN_CONTRACT": "EXPERIMENT_EXECUTION", "ROLE_VISIBILITY": "EXPERIMENT_INPUT_ASSEMBLY", "NORMALIZATION": "NORMALIZATION_EXECUTION", "CLASSIFIER_FEATURE": "CLASSIFICATION_EXECUTION"}


def deferred_role(rule):
    category = rule.get("category") or "BUNDLE"
    if category in DEFERRED_STAGE: return DEFERRED_STAGE[category]
    if rule["rule_id"] == "BND-003": return "BUNDLE_ASSEMBLY"
    if rule["rule_id"].startswith("LIN-"): return "EXPERIMENT_OR_SCORING_EXECUTION"
    if rule["rule_id"].startswith("PROP-"): return "VERIFIER_EXECUTION"
    if rule["rule_id"].startswith("EXT-"): return "BUNDLE_OR_VERIFIER_EXECUTION"
    if rule["rule_id"] == "SRC-004": return "PROVIDER_EXECUTION_CAPTURE"
    return "LATER_CONFORMANCE_LIFECYCLE"


def primitive_for(rule_id):
    if "NEG" in rule_id: return "NEGATIVE_SCOPE_EVALUATE"
    if "PART" in rule_id or rule_id == "E4R1-ENT-001": return "PARTIAL_EFFECT_POLICY_VALIDATE"
    if "PRED" in rule_id or rule_id in {"E4R1-AUTH-001", "E4R1-BIND-001", "E4R2-BIND-001"}: return "PREDICATE_REGISTRY_VALIDATE"
    if "CANON" in rule_id: return "CANONICALIZATION_VALIDATE"
    if "EXPECT" in rule_id: return "EXPECTATION_STABILITY"
    if "GRAPH" in rule_id: return "GRAPH_SET_EQUALITY"
    if rule_id.startswith("SCHEMA") or rule_id in {"LIN-009", "E4R1-PROP-001"}: return "JSON_SCHEMA_VALIDATE"
    if rule_id.startswith("PROF") or rule_id in {"BND-005", "SCENARIO-ID-001"}: return "PROFILE_DOMAIN_VALIDATE"
    if rule_id.startswith("SRC"): return "SOURCE_REGISTRY_VALIDATE"
    if rule_id.startswith("PROP"): return "PROPOSITION_VALIDATE"
    if rule_id.startswith("DIGEST") or rule_id == "E4R2-PROFILE-001": return "RFC8785_DIGEST_EQUALITY"
    if rule_id in {"LIN-002", "PKG-002", "BND-002", "ROLE-001", "E4R2-CLOSE-001"}: return "IDENTITY_INVENTORY_VALIDATE"
    if rule_id.startswith("LIN") or rule_id.startswith("PKG") or rule_id in {"BND-004", "EXT-001", "E4R1-CLOSE-001", "E4R2-REF-001"}: return "TYPED_REFERENCE_CLOSURE"
    return "JSON_POINTER_CONSTRAINT"


SUBJECT_BY_PRIMITIVE = {
    "NEGATIVE_SCOPE_EVALUATE": ["V013_TARGET", "V013_EVIDENCE", "SETTLEMENT_PROFILE", "NEGATIVE_REQUIREMENT_MAP"],
    "PARTIAL_EFFECT_POLICY_VALIDATE": ["PARTIAL_EFFECT_POLICY", "PREDICATE_REGISTRY"], "PREDICATE_REGISTRY_VALIDATE": ["PREDICATE_REGISTRY"],
    "CANONICALIZATION_VALIDATE": ["CANONICALIZATION_PROFILE", "VECTOR_CATALOG"], "EXPECTATION_STABILITY": ["VECTOR_CATALOG", "SOURCE_CATALOG_BINDING"],
    "GRAPH_SET_EQUALITY": ["VALIDATION_RULES", "DEPENDENCY_GRAPH"], "JSON_SCHEMA_VALIDATE": ["VECTOR_CATALOG", "POSITIVE_PROPOSITION_SCHEMA", "NEGATIVE_PROPOSITION_SCHEMA"],
    "PROFILE_DOMAIN_VALIDATE": ["SETTLEMENT_PROFILE", "CANONICALIZATION_PROFILE", "PREDICATE_REGISTRY"], "SOURCE_REGISTRY_VALIDATE": ["SOURCE_CATALOG_BINDING", "VECTOR_CATALOG"],
    "PROPOSITION_VALIDATE": ["VECTOR_CATALOG", "POSITIVE_PROPOSITION_SCHEMA", "NEGATIVE_PROPOSITION_SCHEMA"], "RFC8785_DIGEST_EQUALITY": ["OBJECT_REGISTRY"],
    "IDENTITY_INVENTORY_VALIDATE": ["OBJECT_REGISTRY"], "TYPED_REFERENCE_CLOSURE": ["OBJECT_REGISTRY"], "JSON_POINTER_CONSTRAINT": ["SPECIFICATION_PACKAGE"],
}


def main():
    OUT.mkdir(parents=True, exist_ok=True); SCHEMA.mkdir(parents=True, exist_ok=True)
    draft_manifest = {**identity(f"{NS}:deepseek-draft-evidence", "deepseek-draft-evidence"), "role": "BYTE_PRESERVED_EVIDENCE_METADATA_ONLY", "source_worktree": r"D:\Users\fleur\Moirae Accord", "drafts": [
        {"path": r"D:\Users\fleur\Moirae Accord\docs\accord-02e4r5\ACCORD-02E4R5-REMEDIATION-DESIGN.md", "bytes": 8694, "algorithm": "RAW_FILE_BYTES_SHA256", "sha256": "7a2a437bada75f9faaa76934e4c697898ace2af26e2444766030f7199d0e237d", "disposition": "REWRITE"},
        {"path": r"D:\Users\fleur\Moirae Accord\docs\accord-02e4r5\accord-02e4r5-metacontract-rules.json", "bytes": 13890, "algorithm": "RAW_FILE_BYTES_SHA256", "sha256": "af8a0e430abfe4dc443e955db6dfc48cdb732a80b19f95c327f93477903080e7", "disposition": "DISCARD"},
        {"path": r"D:\Users\fleur\Moirae Accord\docs\accord-02e4r5\accord-02e4r5-primitive-registry.json", "bytes": 49015, "algorithm": "RAW_FILE_BYTES_SHA256", "sha256": "3d77d2a5c0d05cbe758003bc484061fcaa4222974d545588628e7df464a91745", "disposition": "REWRITE"},
        {"path": r"D:\Users\fleur\Moirae Accord\docs\accord-02e4r5\schema\accord-02e4r5-assertion-registry.schema.json", "bytes": 3844, "algorithm": "RAW_FILE_BYTES_SHA256", "sha256": "73cf700d6964763fee07b750572865bb07eea41894c8c4fee1d9b7783b0908a8", "disposition": "REWRITE"},
        {"path": r"D:\Users\fleur\Moirae Accord\docs\accord-02e4r5\schema\accord-02e4r5-metacontract-rules.schema.json", "bytes": 4336, "algorithm": "RAW_FILE_BYTES_SHA256", "sha256": "8e770e02c233bfbedfe4999ba2c4a8e59bcf9e959c09e0c6d4e4f3254cb7418e", "disposition": "DISCARD"},
        {"path": r"D:\Users\fleur\Moirae Accord\docs\accord-02e4r5\schema\accord-02e4r5-primitive-registry.schema.json", "bytes": 9638, "algorithm": "RAW_FILE_BYTES_SHA256", "sha256": "25720045f9899c6fd7d9a05303721d2db94b9914853f57653c7325cb998ec635", "disposition": "REWRITE"}],
        "reconciliation": {"typed_procedure_kinds": "REUSE_CONCEPT_REWRITE_CONTRACT", "package_artifact_rule_scopes": "REUSE_CONCEPT_REWRITE_AS_PACKAGE_INVARIANTS_AND_RULE_SCOPE", "mc_001_to_009": "DISCARD_WHOLESALE_METACONTRACT_RETAIN_DIRECT_INVARIANTS", "version_0_3": "DISCARD_NO_EXISTING_RULE_REQUIRES_BUMP"}}
    emit("accord-02e4r5-deepseek-draft-evidence.json", draft_manifest)

    procedure = {"procedure_id":"JSON_POINTER_COMPARE","version":"1.0","required_arguments":["subject","pointer","comparison","expected"],"argument_types":{"subject":"OBJECT_REFERENCE","pointer":"RFC6901_JSON_POINTER","comparison":{"enum":["EXACT_EQUAL"]},"expected":"JSON_VALUE"},"resolution":{"subject":"RESOLVE_EXACTLY_ONE_BY_KIND_ID_VERSION","member":"MEMBER_ID_IF_PRESENT","zero_matches":"FAIL_CLOSED","multiple_matches":"FAIL_CLOSED"},"normalization":{"subject_json":"PARSE_JSON","pointer":"RFC6901_UNESCAPE","actual_value":"NONE","expected_value":"NONE"},"extraction":{"operation":"RFC6901_RESOLVE","quantification":"EXACTLY_ONE_VALUE","missing":"FAIL_CLOSED","ambiguous":"FAIL_CLOSED"},"evaluation":{"EXACT_EQUAL":{"operation":"JSON_TYPE_AND_VALUE_EQUAL","object_member_order":"INSIGNIFICANT","array_order":"SIGNIFICANT","number_model":"RFC8785_IEEE754"}},"result_type":"BOOLEAN","failure_codes":{"resolution":"SUBJECT_RESOLUTION_FAILED","pointer":"POINTER_RESOLUTION_FAILED","comparison":"VALUE_NOT_EQUAL","argument":"INVALID_ARGUMENT"},"missing_behavior":"FAIL_CLOSED","ambiguous_behavior":"FAIL_CLOSED","fail_closed":True}
    primitive_registry = {**identity(f"{NS}:primitive-registry", "primitive-registry"), "retired_primitive_ids": ["ASSERTION_EXPRESSION"], "composition_operators": ["ALL", "ANY"],"procedure_kinds":[procedure],"primitives":[{"primitive_id":"JSON_POINTER_COMPARE","primitive_version":"1.0","scope":"RULE","procedure_kind":"JSON_POINTER_COMPARE","argument_schema":{"type":"object","required":["subject","pointer","comparison","expected"],"properties":{"subject":{"$ref":"#/$defs/objectRef"},"pointer":{"type":"string","pattern":"^(|/.*)$"},"comparison":{"const":"EXACT_EQUAL"},"expected":{}},"additionalProperties":False},"failure_codes":["SUBJECT_RESOLUTION_FAILED","POINTER_RESOLUTION_FAILED","VALUE_NOT_EQUAL","INVALID_ARGUMENT"],"error_behavior":"FAIL_CLOSED"}]}
    emit("accord-02e4r5-primitive-registry.json", primitive_registry)

    canon = {**identity(CANON_ID, "canonicalization-profile"), "profile_id": CANON_ID, "profile_version": VERSION, "algorithm": "SHA-256", "method": "RFC8785_JCS", "encoding": "UTF-8", "pointer_semantics": "RFC6901", "missing_pointer_policy": "FAIL", "duplicate_pointer_policy": "FAIL", "content_targets": [
        {"target_id": "RECORD_EXCLUDING_INTEGRITY_CONTENT_DIGEST", "mode": "EXCLUDE_JSON_POINTERS", "json_pointers": ["/integrity/content_digest"]},
        {"target_id": "RECORD_EXCLUDING_INTEGRITY", "mode": "EXCLUDE_JSON_POINTERS", "json_pointers": ["/integrity"]},
        {"target_id": "ENTRY_CONTENT", "mode": "INCLUDE_JSON_POINTERS", "json_pointers": ["/content"]}]}
    emit("accord-02e4r5-canonicalization-profile.json", canon)

    old_pred = read("docs/accord-02e4r4/accord-02e4r4-predicate-registry.json"); entries=[]
    for old in old_pred["entries"]:
        row={k:copy.deepcopy(old[k]) for k in ["predicate_id","stage","kind","support_status","required_bindings","optional_bindings","not_applicable_bindings","predecessor_edges","stage_settlement","later_stage_policy"]}
        row["proposition_schema_ref"]=ref("SCHEMA",f"{NS}:schema:"+("negative-scope-proposition" if old["kind"]=="NEGATIVE_SCOPE" else "positive-effect-proposition"))
        if old["kind"]=="NEGATIVE_SCOPE": row["negative_requirement_map_ref"]=ref("REQUIREMENT_MAP",f"{NS}:negative-requirement-map")
        entries.append(row)
    predicate_registry={**identity(f"{NS}:predicate-registry","predicate-registry"),"registry_id":f"{NS}:predicate-registry","registry_version":VERSION,"resolution_key":["predicate_id","stage"],"comparison":"UNICODE_CODE_POINT_EXACT_CASE_SENSITIVE_NO_NORMALIZATION","global_stage_order":"FORBIDDEN","implicit_transitivity":"FORBIDDEN","entries":entries,"fail_closed_policy":copy.deepcopy(old_pred["fail_closed_policy"])}
    emit("accord-02e4r5-predicate-registry.json",predicate_registry)

    settlement_profile={**identity(f"{NS}:settlement-profile:conservative","settlement-profile"),"profile_id":"urn:accord:02c:profile:conservative-v1","profile_version":VERSION,"predicate_registry_ref":ref("REGISTRY",f"{NS}:predicate-registry"),"negative_policy":{"requirement_map_ref":ref("REQUIREMENT_MAP",f"{NS}:negative-requirement-map"),"allowed_consistency_levels":["SNAPSHOT_COMPLETE","LINEARIZABLE_COMPLETE"],"allowed_source_classes":["COMPLETE_NEGATIVE_LEDGER_QUERY","COMPLETE_NEGATIVE_AUTHORITATIVE_SNAPSHOT"],"freshness_max_age_seconds":300,"minimum_retention_seconds":86400,"future_observation_result":"UNKNOWN","stale_result":"STALE_EVIDENCE"},"scope_vocabulary":{"canonical_dimensions":["resource","action","recipient_or_counterparty","provider"],"accepted_mapping":{"resource_binding":"resource","action_binding":"action","recipient_binding":"recipient_or_counterparty","provider_binding":"provider"},"not_applicable_token":"NOT_APPLICABLE"}}
    emit("accord-02e4r5-settlement-profile-conservative.json",settlement_profile)

    reqs=[("TARGET_EFFECT_EQUAL",["target.effect_id","evidence.effect_id"],"EXACT_EQUAL","NEGATIVE_EFFECT_MISMATCH"),("TARGET_PREDICATE_EQUAL",["target.negated_predicate_id","evidence.predicate_id"],"EXACT_EQUAL","NEGATIVE_PREDICATE_MISMATCH"),("TARGET_STAGE_EQUAL",["target.negated_stage","evidence.stage"],"EXACT_EQUAL","NEGATIVE_STAGE_MISMATCH"),("TARGET_SCOPE_EQUAL",["target.scope","evidence.scope"],"TUPLE_EQUAL","NEGATIVE_SCOPE_MISMATCH"),("INTERVAL_VALID",["evidence.observed_interval.not_before","evidence.observed_interval.as_of"],"RFC3339_ORDER_INCLUSIVE","NEGATIVE_INTERVAL_INVALID"),("INTERVAL_COVERS_TARGET",["target.required_interval","evidence.observed_interval"],"INTERVAL_COVERAGE_INCLUSIVE_BOTH_ENDS","NEGATIVE_INTERVAL_INSUFFICIENT"),("RETENTION_MEETS_BOUND",["evidence.retention_window_seconds","target.required_interval","profile.negative_policy.minimum_retention_seconds"],"GTE_MAX_INTERVAL_AND_PROFILE_MINIMUM","NEGATIVE_RETENTION_INSUFFICIENT"),("CONSISTENCY_ALLOWED",["evidence.consistency_level","profile.negative_policy.allowed_consistency_levels"],"MEMBERSHIP","NEGATIVE_CONSISTENCY_DISALLOWED"),("SOURCE_CLASS_ALLOWED",["evidence.evidence_class","profile.negative_policy.allowed_source_classes"],"MEMBERSHIP","NEGATIVE_SOURCE_CLASS_DISALLOWED"),("FRESHNESS_BOUND",["evidence.observed_at","evidence.verification_time","profile.negative_policy.freshness_max_age_seconds"],"ZERO_LE_AGE_LE_PROFILE_MAX","NEGATIVE_FRESHNESS_FAILED"),("READ_COMPLETE",["evidence.read_scope_complete","evidence.read_semantics"],"TRUE_AND_COMPLETE_LEDGER_QUERY","NEGATIVE_READ_INCOMPLETE"),("NO_SAME_TARGET_POSITIVE",["evidence.evidence_universe","target.effect_id","target.negated_predicate_id","target.negated_stage","target.scope"],"FILTER_ADMISSIBLE_POSITIVE_MATCH_TARGET_DEDUP_EVIDENCE_ID_COUNT_EQ_ZERO","NEGATIVE_CONTRADICTION")]
    negative_map={**identity(f"{NS}:negative-requirement-map","negative-requirement-map"),"governing_profile_ref":ref("PROFILE",f"{NS}:settlement-profile:conservative"),"requirements":[{"requirement_id":rid,"source_fields":fields,"governing_authority":"SETTLEMENT_PROFILE","procedure":proc,"failure_code":code} for rid,fields,proc,code in reqs],"evaluation_order":[x[0] for x in reqs],"caller_supplied_contradiction_count":"FORBIDDEN"}
    emit("accord-02e4r5-negative-requirement-map.json",negative_map)
    partial={**identity(f"{NS}:partial-effect-policy","partial-effect-policy"),"predicate_registry_ref":ref("REGISTRY",f"{NS}:predicate-registry"),"same_effect_required":True,"direct_predecessor_required":True,"implicit_transitivity":"FORBIDDEN","global_stage_order":"FORBIDDEN","decisions":{"VALID_SUPPORTED_DIRECT_PREDECESSOR":"PARTIAL_EFFECT","TARGET_ALREADY_SUPPORTED":"NOT_PARTIAL_EFFECT","NO_PREDECESSOR":"UNKNOWN","WRONG_EFFECT":"REJECT","UNSUPPORTED_TUPLE":"REJECT","UNKNOWN_TUPLE":"REJECT","WRONG_STAGE":"REJECT","SELF_EDGE":"REJECT","CYCLE":"REJECT","DANGLING_TARGET":"REJECT","INCOMPATIBLE_EVIDENCE":"UNKNOWN","INADMISSIBLE_EVIDENCE":"UNKNOWN"}}
    emit("accord-02e4r5-partial-effect-policy.json",partial)

    r4_catalog=read("docs/accord-02e4r4/accord-02e4r4-settlement-vector-catalog.json"); catalog=copy.deepcopy(r4_catalog)
    catalog.update(identity(f"{NS}:vector-catalog","vector-catalog")); catalog["catalog_id"]=f"{NS}:vector-catalog"; catalog["catalog_version"]=VERSION; catalog["source_catalog_ref"]=ref("CONTRACT",f"{NS}:source-catalog-binding"); catalog.pop("source_catalog_binding_id",None)
    for vector in catalog["vectors"]:
        vector["source_vector_ref"]=ref("SOURCE_VECTOR",CATALOG_ID,"0.1",vector["vector_id"]); vector["settlement_profile_ref"]=ref("PROFILE",f"{NS}:settlement-profile:conservative"); vector["evidence_profile_ref"]=ref("PROFILE",f"{NS}:settlement-profile:conservative")
        prop=vector["target"]["proposition"]; negative=prop["proposition_kind"]=="NEGATIVE_SCOPE"; prop["schema_ref"]=ref("SCHEMA",f"{NS}:schema:"+("negative-scope-proposition" if negative else "positive-effect-proposition")); prop.pop("schema_id",None); prop.pop("schema_version",None); prop["proposition_id"]=prop["proposition_id"].replace("accord-02e4r4","accord-02r5"); prop["evidence_profile_id"]="urn:accord:02c:profile:conservative-v1"
        prop["integrity"]["canonicalization_ref"]=ref("CANONICALIZATION",CANON_ID); prop["integrity"].pop("canonicalization",None)
        vector["target"]["target_resolution"]["proposition_schema_ref"]=prop["schema_ref"]; vector["target"]["target_resolution"].pop("negative_scope_contract_ref",None)
        if negative: vector["target"]["target_resolution"]["negative_requirement_map_ref"]=ref("REQUIREMENT_MAP",f"{NS}:negative-requirement-map")
        vector["target"]["canonicalization_ref"]=ref("CANONICALIZATION",CANON_ID); prop["integrity"]["content_digest"]="sha-256:"+projected_digest(prop,["/integrity/content_digest"]); vector["classification"]="DECLARATIVE_EXPECTATION_VECTOR"
    catalog["integrity"]["canonicalization_ref"]=ref("CANONICALIZATION",CANON_ID); catalog["integrity"].pop("canonicalization",None); catalog["integrity"]["content_digest"]="sha-256:"+projected_digest(catalog,["/integrity/content_digest"])
    emit("accord-02e4r5-vector-catalog.json",catalog)

    accepted_catalog_path="docs/accord-02/examples/accord-02c-settlement-test-vectors.json"
    source_binding={**identity(f"{NS}:source-catalog-binding","source-catalog-binding"),"assigned_catalog_ref":ref("CONTRACT",CATALOG_ID,"0.1"),"identity_assignment":"PACKAGE_BINDING_NOT_HISTORICAL_SELF_ASSERTION","repository_root_path":accepted_catalog_path,"integrity":{"class":"SEMANTIC_JSON_CONTENT","canonicalization":"RFC8785_JCS","algorithm":"SHA-256","digest":jcs_digest(read(accepted_catalog_path))}}
    emit("accord-02e4r5-source-catalog-binding.json",source_binding)

    v013=next(v for v in catalog["vectors"] if v["vector_id"]=="ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE"); p=v013["target"]["proposition"]
    scope={"resource":p["scope"]["resource_binding"],"action":p["scope"]["action_binding"],"recipient_or_counterparty":p["scope"]["recipient_binding"],"provider":p["scope"]["provider_binding"]}
    target={**identity(f"{NS}:v013-target","v013-target"),"relationship":"EXECUTABLE_REALIZATION_OF_EXACT_ACCEPTED_DECLARATIVE_V013","source_vector_ref":ref("SOURCE_VECTOR",CATALOG_ID,"0.1",v013["vector_id"]),"candidate_proposition_id":p["proposition_id"],"effect_id":p["effect_id"],"negated_predicate_id":p["negated_predicate_id"],"negated_stage":p["negated_stage"],"scope":scope,"required_interval":{"not_before":p["scope"]["not_before"],"as_of":p["scope"]["as_of"]},"settlement_profile_ref":ref("PROFILE",f"{NS}:settlement-profile:conservative")}
    emit("accord-02e4r5-v013-target.json",target)
    evidence={**identity(f"{NS}:v013-synthetic-evidence","complete-negative-evidence"),"fixture_status":"SYNTHETIC_CANDIDATE_0_2_NOT_ACCEPTED_HISTORY","source_accepted_evidence_id":"urn:accord:02c:evidence:EV13","evidence_id":f"{NS}:synthetic-evidence:v013","effect_id":target["effect_id"],"predicate_id":target["negated_predicate_id"],"stage":target["negated_stage"],"scope":scope,"observed_interval":copy.deepcopy(target["required_interval"]),"retention_window_seconds":86400,"consistency_level":"SNAPSHOT_COMPLETE","read_semantics":"COMPLETE_LEDGER_QUERY","read_scope_complete":True,"observed_at":p["scope"]["as_of"],"verification_time":"2024-01-01T00:01:01Z","evidence_class":"COMPLETE_NEGATIVE_LEDGER_QUERY","evidence_universe":[],"requirement_map_ref":ref("REQUIREMENT_MAP",f"{NS}:negative-requirement-map")}
    emit("accord-02e4r5-v013-synthetic-evidence.json",evidence)

    old_rules=read("docs/accord-02e4r4/accord-02e4r4-validation-rules.json")["rules"]
    object_ids={"SPECIFICATION_PACKAGE":PKG_ID,"OBJECT_REGISTRY":f"{NS}:object-registry","VALIDATION_RULES":f"{NS}:validation-rules","DEPENDENCY_GRAPH":f"{NS}:dependency-graph","VECTOR_CATALOG":f"{NS}:vector-catalog","SOURCE_CATALOG_BINDING":f"{NS}:source-catalog-binding","PREDICATE_REGISTRY":f"{NS}:predicate-registry","CANONICALIZATION_PROFILE":CANON_ID,"SETTLEMENT_PROFILE":f"{NS}:settlement-profile:conservative","NEGATIVE_REQUIREMENT_MAP":f"{NS}:negative-requirement-map","PARTIAL_EFFECT_POLICY":f"{NS}:partial-effect-policy","V013_TARGET":f"{NS}:v013-target","V013_EVIDENCE":f"{NS}:v013-synthetic-evidence","POSITIVE_PROPOSITION_SCHEMA":f"{NS}:schema:positive-effect-proposition","NEGATIVE_PROPOSITION_SCHEMA":f"{NS}:schema:negative-scope-proposition"}
    package_ref=ref("PACKAGE",PKG_ID); registry_ref=ref("REGISTRY",f"{NS}:object-registry"); predicate_ref=ref("REGISTRY",f"{NS}:predicate-registry"); canon_ref=ref("CANONICALIZATION",CANON_ID); profile_ref=ref("PROFILE",f"{NS}:settlement-profile:conservative"); partial_ref=ref("POLICY",f"{NS}:partial-effect-policy"); target_ref=ref("CONTRACT",f"{NS}:v013-target"); evidence_ref=ref("CONTRACT",f"{NS}:v013-synthetic-evidence"); negative_ref=ref("REQUIREMENT_MAP",f"{NS}:negative-requirement-map"); source_ref=ref("CONTRACT",f"{NS}:source-catalog-binding"); vector_ref=ref("CONTRACT",f"{NS}:vector-catalog"); validation_ref=ref("CONTRACT",f"{NS}:validation-rules"); graph_ref=ref("CONTRACT",f"{NS}:dependency-graph")
    operand_pools={
      "JSON_POINTER_CONSTRAINT":[(package_ref,"/status","CANDIDATE_UNACCEPTED")],
      "PREDICATE_REGISTRY_VALIDATE":[(predicate_ref,"/global_stage_order","FORBIDDEN"),(predicate_ref,"/implicit_transitivity","FORBIDDEN"),(predicate_ref,"/resolution_key",["predicate_id","stage"]),(predicate_ref,"/comparison","UNICODE_CODE_POINT_EXACT_CASE_SENSITIVE_NO_NORMALIZATION"),(predicate_ref,"/registry_version",VERSION),(predicate_ref,"/entries/0/kind",entries[0]["kind"]),(predicate_ref,"/entries/1/kind",entries[1]["kind"]),(predicate_ref,"/entries/2/kind",entries[2]["kind"]),(predicate_ref,"/entries/3/kind",entries[3]["kind"]),(predicate_ref,"/entries/4/kind",entries[4]["kind"])],
      "CANONICALIZATION_VALIDATE":[(canon_ref,"/algorithm","SHA-256"),(canon_ref,"/method","RFC8785_JCS"),(canon_ref,"/encoding","UTF-8"),(canon_ref,"/missing_pointer_policy","FAIL"),(canon_ref,"/duplicate_pointer_policy","FAIL")],
      "PARTIAL_EFFECT_POLICY_VALIDATE":[(partial_ref,"/same_effect_required",True),(partial_ref,"/direct_predecessor_required",True),(partial_ref,"/implicit_transitivity","FORBIDDEN"),(partial_ref,"/global_stage_order","FORBIDDEN")],
      "NEGATIVE_SCOPE_EVALUATE":[(target_ref,"/relationship","EXECUTABLE_REALIZATION_OF_EXACT_ACCEPTED_DECLARATIVE_V013"),(evidence_ref,"/fixture_status","SYNTHETIC_CANDIDATE_0_2_NOT_ACCEPTED_HISTORY"),(negative_ref,"/caller_supplied_contradiction_count","FORBIDDEN")],
      "PROFILE_DOMAIN_VALIDATE":[(profile_ref,"/profile_version",VERSION),(profile_ref,"/negative_policy/future_observation_result","UNKNOWN"),(profile_ref,"/negative_policy/stale_result","STALE_EVIDENCE"),(profile_ref,"/scope_vocabulary/not_applicable_token","NOT_APPLICABLE")],
      "SOURCE_REGISTRY_VALIDATE":[(source_ref,"/identity_assignment","PACKAGE_BINDING_NOT_HISTORICAL_SELF_ASSERTION"),(source_ref,"/integrity/class","SEMANTIC_JSON_CONTENT"),(source_ref,"/integrity/algorithm","SHA-256")],
      "JSON_SCHEMA_VALIDATE":[(vector_ref,"/vectors/0/classification","DECLARATIVE_EXPECTATION_VECTOR"),(vector_ref,"/vectors/1/classification","DECLARATIVE_EXPECTATION_VECTOR"),(vector_ref,"/vectors/2/classification","DECLARATIVE_EXPECTATION_VECTOR"),(vector_ref,"/vectors/3/classification","DECLARATIVE_EXPECTATION_VECTOR")],
      "PROPOSITION_VALIDATE":[(vector_ref,"/vectors/4/classification","DECLARATIVE_EXPECTATION_VECTOR"),(vector_ref,"/vectors/5/classification","DECLARATIVE_EXPECTATION_VECTOR")],
      "RFC8785_DIGEST_EQUALITY":[(canon_ref,"/content_targets/0/mode","EXCLUDE_JSON_POINTERS"),(canon_ref,"/content_targets/1/mode","EXCLUDE_JSON_POINTERS"),(canon_ref,"/content_targets/2/mode","INCLUDE_JSON_POINTERS"),(canon_ref,"/pointer_semantics","RFC6901")],
      "IDENTITY_INVENTORY_VALIDATE":[(registry_ref,"/uniqueness_key/0","kind"),(registry_ref,"/uniqueness_key/1","id"),(registry_ref,"/uniqueness_key/2","version"),(registry_ref,"/object_version",VERSION),(registry_ref,"/uniqueness_key",["kind","id","version"])],
      "TYPED_REFERENCE_CLOSURE":[(validation_ref,"/classification_policy","SUBJECT_ARTIFACT_MUST_EXIST"),(validation_ref,"/object_version",VERSION),(validation_ref,"/rules/0/scope","DEFERRED_NO_SUBJECT_ARTIFACT"),(validation_ref,"/rules/1/scope","DEFERRED_NO_SUBJECT_ARTIFACT"),(validation_ref,"/rules/2/scope","DEFERRED_NO_SUBJECT_ARTIFACT"),(validation_ref,"/rules/3/scope","DEFERRED_NO_SUBJECT_ARTIFACT"),(validation_ref,"/rules/4/scope","DEFERRED_NO_SUBJECT_ARTIFACT")],
      "EXPECTATION_STABILITY":[(vector_ref,"/vectors/6/classification","DECLARATIVE_EXPECTATION_VECTOR")],
      "GRAPH_SET_EQUALITY":[(graph_ref,"/object_version",VERSION)]}
    pool_index={k:0 for k in operand_pools}
    rules=[]; assertions=[]; classifications=[]
    for old in old_rules:
        rid=old["rule_id"]; executable=rid in EXECUTABLE; row={"rule_id":rid,"family":old.get("category") or "PACKAGE_CONTRACT","failure_code":old["failure_code"],"severity":old["severity"],"depends_on":old.get("depends_on",[])}
        if executable:
            semantic_family=primitive_for(rid); pool=operand_pools[semantic_family]; subject,pointer,expected=pool[pool_index[semantic_family] % len(pool)]; pool_index[semantic_family]+=1
            arguments={"subject":subject,"pointer":pointer,"comparison":"EXACT_EQUAL","expected":copy.deepcopy(expected)}
            aid=f"{NS}:assertion:{rid}"; row.update({"scope":"EXECUTABLE_IN_PACKAGE_0_2","subject_bindings":[subject],"assertion_ref":ref("REGISTRY",f"{NS}:assertion-registry",VERSION,aid)})
            assertions.append({"assertion_id":aid,"expression":{"operator":"ALL","checks":[{"primitive_ref":ref("REGISTRY",f"{NS}:primitive-registry",VERSION,"JSON_POINTER_COMPARE"),"arguments":arguments}]}})
            classifications.append({"rule_id":rid,"rule_family":row["family"],"classification":"EXECUTABLE_IN_PACKAGE_0_2","subject_roles":[subject["id"]],"reason":"The rule resolves its declared subject and compares its own RFC6901-selected value using its normative operands."})
        else:
            stage=deferred_role(old); missing=old.get("inputs",["runtime subject artifact"]); reason="The package defines the contract but contains no concrete lifecycle subject artifact; inventing bytes would be non-conformant."
            row.update({"scope":"DEFERRED_NO_SUBJECT_ARTIFACT","missing_subject_roles":missing,"later_lifecycle_stage":stage,"deferred_reason":reason}); classifications.append({"rule_id":rid,"rule_family":row["family"],"classification":"DEFERRED_NO_SUBJECT_ARTIFACT","missing_subject_roles":missing,"reason":reason,"later_lifecycle_stage":stage})
        rules.append(row)
    assert len(rules)==104 and len(EXECUTABLE)==54 and sum(x["scope"]=="DEFERRED_NO_SUBJECT_ARTIFACT" for x in rules)==50
    rules_doc={**identity(f"{NS}:validation-rules","validation-rules"),"classification_policy":"SUBJECT_ARTIFACT_MUST_EXIST","rules":rules}
    assertions_doc={**identity(f"{NS}:assertion-registry","assertion-registry"),"retired_primitive_ids":["ASSERTION_EXPRESSION"],"assertions":assertions}
    classification_doc={**identity(f"{NS}:rule-classification","rule-classification"),"total_declared_rules":len(rules),"executable_in_package_0_2":len(EXECUTABLE),"deferred_no_subject_artifact":len(rules)-len(EXECUTABLE),"classifications":classifications}
    graph={**identity(f"{NS}:dependency-graph","dependency-graph"),"nodes":[r["rule_id"] for r in rules],"edges":[{"from":r["rule_id"],"to":dep} for r in rules for dep in r["depends_on"]]}
    emit("accord-02e4r5-validation-rules.json",rules_doc); emit("accord-02e4r5-assertion-registry.json",assertions_doc); emit("accord-02e4r5-rule-classification.json",classification_doc); emit("accord-02e4r5-dependency-graph.json",graph)

    # Acceptance-critical schemas are family domains, not fixture transcripts.
    ref_prop={"$ref":"#/$defs/objectRef"}; str_prop={"type":"string","minLength":1}
    schemas={}
    schemas["primitive-registry"]=base_schema("primitive-registry",["retired_primitive_ids","composition_operators","procedure_kinds","primitives"],{"retired_primitive_ids":{"type":"array","contains":{"const":"ASSERTION_EXPRESSION"}},"composition_operators":{"const":["ALL","ANY"]},"procedure_kinds":{"type":"array","minItems":1,"maxItems":1,"items":{"type":"object","required":["procedure_id","version","required_arguments","argument_types","resolution","normalization","extraction","evaluation","result_type","failure_codes","missing_behavior","ambiguous_behavior","fail_closed"],"properties":{"procedure_id":{"const":"JSON_POINTER_COMPARE"},"version":{"const":"1.0"},"required_arguments":{"const":["subject","pointer","comparison","expected"]},"argument_types":{"type":"object"},"resolution":{"type":"object"},"normalization":{"type":"object"},"extraction":{"type":"object"},"evaluation":{"type":"object"},"result_type":{"const":"BOOLEAN"},"failure_codes":{"type":"object"},"missing_behavior":{"const":"FAIL_CLOSED"},"ambiguous_behavior":{"const":"FAIL_CLOSED"},"fail_closed":{"const":True}},"additionalProperties":False}},"primitives":{"type":"array","minItems":1,"maxItems":1,"items":{"type":"object","required":["primitive_id","primitive_version","scope","procedure_kind","argument_schema","failure_codes","error_behavior"],"properties":{"primitive_id":{"const":"JSON_POINTER_COMPARE"},"primitive_version":{"const":"1.0"},"scope":{"const":"RULE"},"procedure_kind":{"const":"JSON_POINTER_COMPARE"},"argument_schema":{"type":"object"},"failure_codes":{"type":"array","minItems":1,"items":str_prop},"error_behavior":{"const":"FAIL_CLOSED"}},"additionalProperties":False}}})
    schemas["canonicalization-profile"]=base_schema("canonicalization-profile",["profile_id","profile_version","algorithm","method","encoding","pointer_semantics","missing_pointer_policy","duplicate_pointer_policy","content_targets"],{"profile_id":{"const":CANON_ID},"profile_version":{"const":VERSION},"algorithm":{"const":"SHA-256"},"method":{"const":"RFC8785_JCS"},"encoding":{"const":"UTF-8"},"pointer_semantics":{"const":"RFC6901"},"missing_pointer_policy":{"const":"FAIL"},"duplicate_pointer_policy":{"const":"FAIL"},"content_targets":{"type":"array","minItems":1,"items":{"type":"object","required":["target_id","mode","json_pointers"],"properties":{"target_id":str_prop,"mode":{"enum":["INCLUDE_JSON_POINTERS","EXCLUDE_JSON_POINTERS"]},"json_pointers":{"type":"array","minItems":1,"items":{"type":"string","pattern":"^/"},"uniqueItems":True}},"additionalProperties":False}}},object_id=CANON_ID)
    schemas["predicate-registry"]=base_schema("predicate-registry",["registry_id","registry_version","resolution_key","comparison","global_stage_order","implicit_transitivity","entries","fail_closed_policy"],{"registry_id":{"const":f"{NS}:predicate-registry"},"registry_version":{"const":VERSION},"resolution_key":{"const":["predicate_id","stage"]},"comparison":{"const":"UNICODE_CODE_POINT_EXACT_CASE_SENSITIVE_NO_NORMALIZATION"},"global_stage_order":{"const":"FORBIDDEN"},"implicit_transitivity":{"const":"FORBIDDEN"},"entries":{"type":"array","minItems":1,"items":{"type":"object","required":["predicate_id","stage","kind","support_status","required_bindings","optional_bindings","not_applicable_bindings","predecessor_edges","stage_settlement","later_stage_policy","proposition_schema_ref"],"properties":{"predicate_id":str_prop,"stage":{"type":["string","null"]},"kind":{"enum":["POSITIVE_STAGE","GENERIC_OCCURRENCE","NEGATIVE_SCOPE"]},"support_status":str_prop,"required_bindings":{"type":"array","items":str_prop},"optional_bindings":{"type":"array","items":str_prop},"not_applicable_bindings":{"type":"array","items":str_prop},"predecessor_edges":{"type":"array"},"stage_settlement":{},"later_stage_policy":{},"proposition_schema_ref":ref_prop,"negative_requirement_map_ref":ref_prop},"additionalProperties":False}},"fail_closed_policy":{"type":"object","minProperties":1}})
    schemas["settlement-profile"]=base_schema("settlement-profile",["profile_id","profile_version","predicate_registry_ref","negative_policy","scope_vocabulary"],{"profile_id":str_prop,"profile_version":{"const":VERSION},"predicate_registry_ref":ref_prop,"negative_policy":{"type":"object","required":["requirement_map_ref","allowed_consistency_levels","allowed_source_classes","freshness_max_age_seconds","minimum_retention_seconds","future_observation_result","stale_result"],"properties":{"requirement_map_ref":ref_prop,"allowed_consistency_levels":{"type":"array","minItems":1,"items":str_prop},"allowed_source_classes":{"type":"array","minItems":1,"items":str_prop},"freshness_max_age_seconds":{"type":"integer","minimum":0},"minimum_retention_seconds":{"type":"integer","minimum":0},"future_observation_result":{"const":"UNKNOWN"},"stale_result":{"const":"STALE_EVIDENCE"}},"additionalProperties":False},"scope_vocabulary":{"type":"object","required":["canonical_dimensions","accepted_mapping","not_applicable_token"],"properties":{"canonical_dimensions":{"const":["resource","action","recipient_or_counterparty","provider"]},"accepted_mapping":{"type":"object","required":["resource_binding","action_binding","recipient_binding","provider_binding"],"additionalProperties":{"type":"string"}},"not_applicable_token":{"const":"NOT_APPLICABLE"}},"additionalProperties":False}},object_id=f"{NS}:settlement-profile:conservative")
    schemas["negative-requirement-map"]=base_schema("negative-requirement-map",["governing_profile_ref","requirements","evaluation_order","caller_supplied_contradiction_count"],{"governing_profile_ref":ref_prop,"requirements":{"type":"array","minItems":1,"items":{"type":"object","required":["requirement_id","source_fields","governing_authority","procedure","failure_code"],"properties":{"requirement_id":str_prop,"source_fields":{"type":"array","minItems":1,"items":str_prop},"governing_authority":{"const":"SETTLEMENT_PROFILE"},"procedure":str_prop,"failure_code":str_prop},"additionalProperties":False}},"evaluation_order":{"type":"array","minItems":1,"items":str_prop,"uniqueItems":True},"caller_supplied_contradiction_count":{"const":"FORBIDDEN"}})
    schemas["partial-effect-policy"]=base_schema("partial-effect-policy",["predicate_registry_ref","same_effect_required","direct_predecessor_required","implicit_transitivity","global_stage_order","decisions"],{"predicate_registry_ref":ref_prop,"same_effect_required":{"const":True},"direct_predecessor_required":{"const":True},"implicit_transitivity":{"const":"FORBIDDEN"},"global_stage_order":{"const":"FORBIDDEN"},"decisions":{"type":"object","required":list(partial["decisions"]),"properties":{k:{"const":v} for k,v in partial["decisions"].items()},"additionalProperties":False}})
    schemas["source-catalog-binding"]=base_schema("source-catalog-binding",["assigned_catalog_ref","identity_assignment","repository_root_path","integrity"],{"assigned_catalog_ref":ref_prop,"identity_assignment":{"const":"PACKAGE_BINDING_NOT_HISTORICAL_SELF_ASSERTION"},"repository_root_path":str_prop,"integrity":{"type":"object","required":["class","canonicalization","algorithm","digest"],"properties":{"class":{"const":"SEMANTIC_JSON_CONTENT"},"canonicalization":{"const":"RFC8785_JCS"},"algorithm":{"const":"SHA-256"},"digest":{"type":"string","pattern":"^[0-9a-f]{64}$"}},"additionalProperties":False}})
    schemas["v013-target"]=base_schema("v013-target",["relationship","source_vector_ref","candidate_proposition_id","effect_id","negated_predicate_id","negated_stage","scope","required_interval","settlement_profile_ref"],{"relationship":{"const":"EXECUTABLE_REALIZATION_OF_EXACT_ACCEPTED_DECLARATIVE_V013"},"source_vector_ref":ref_prop,"candidate_proposition_id":str_prop,"effect_id":str_prop,"negated_predicate_id":str_prop,"negated_stage":str_prop,"scope":{"$ref":"#/$defs/scope"},"required_interval":{"$ref":"#/$defs/interval"},"settlement_profile_ref":ref_prop},defs={"scope":{"type":"object","required":["resource","action","recipient_or_counterparty","provider"],"properties":{k:{} for k in ["resource","action","recipient_or_counterparty","provider"]},"additionalProperties":False},"interval":{"type":"object","required":["not_before","as_of"],"properties":{"not_before":{"type":"string","format":"date-time"},"as_of":{"type":"string","format":"date-time"}},"additionalProperties":False}})
    schemas["complete-negative-evidence"]=base_schema("complete-negative-evidence",["fixture_status","source_accepted_evidence_id","evidence_id","effect_id","predicate_id","stage","scope","observed_interval","retention_window_seconds","consistency_level","read_semantics","read_scope_complete","observed_at","verification_time","evidence_class","evidence_universe","requirement_map_ref"],{"fixture_status":{"const":"SYNTHETIC_CANDIDATE_0_2_NOT_ACCEPTED_HISTORY"},"source_accepted_evidence_id":str_prop,"evidence_id":str_prop,"effect_id":str_prop,"predicate_id":str_prop,"stage":str_prop,"scope":{"type":"object"},"observed_interval":{"type":"object"},"retention_window_seconds":{"type":"integer","minimum":0},"consistency_level":str_prop,"read_semantics":{"const":"COMPLETE_LEDGER_QUERY"},"read_scope_complete":{"type":"boolean"},"observed_at":{"type":"string","format":"date-time"},"verification_time":{"type":"string","format":"date-time"},"evidence_class":str_prop,"evidence_universe":{"type":"array","items":{"type":"object"}},"requirement_map_ref":ref_prop},object_id=f"{NS}:v013-synthetic-evidence")
    schemas["validation-rules"]=base_schema("validation-rules",["classification_policy","rules"],{"classification_policy":{"const":"SUBJECT_ARTIFACT_MUST_EXIST"},"rules":{"type":"array","minItems":1,"items":{"type":"object","required":["rule_id","family","failure_code","severity","depends_on","scope"],"properties":{"rule_id":str_prop,"family":str_prop,"failure_code":str_prop,"severity":str_prop,"depends_on":{"type":"array","items":str_prop},"scope":{"enum":["EXECUTABLE_IN_PACKAGE_0_2","DEFERRED_NO_SUBJECT_ARTIFACT"]},"subject_bindings":{"type":"array","minItems":1,"items":ref_prop},"assertion_ref":ref_prop,"missing_subject_roles":{"type":"array","minItems":1},"later_lifecycle_stage":str_prop,"deferred_reason":str_prop},"allOf":[{"if":{"properties":{"scope":{"const":"EXECUTABLE_IN_PACKAGE_0_2"}}},"then":{"required":["subject_bindings","assertion_ref"]}},{"if":{"properties":{"scope":{"const":"DEFERRED_NO_SUBJECT_ARTIFACT"}}},"then":{"required":["missing_subject_roles","later_lifecycle_stage","deferred_reason"]}}],"additionalProperties":False}}})
    schemas["assertion-registry"]=base_schema("assertion-registry",["retired_primitive_ids","assertions"],{"retired_primitive_ids":{"type":"array","contains":{"const":"ASSERTION_EXPRESSION"}},"assertions":{"type":"array","minItems":1,"items":{"type":"object","required":["assertion_id","expression"],"properties":{"assertion_id":str_prop,"expression":{"type":"object","required":["operator","checks"],"properties":{"operator":{"enum":["ALL","ANY"]},"checks":{"type":"array","minItems":1,"items":{"type":"object","required":["primitive_ref","arguments"],"properties":{"primitive_ref":ref_prop,"arguments":{"type":"object"}},"additionalProperties":False}}},"additionalProperties":False}},"additionalProperties":False}}})
    schemas["rule-classification"]=base_schema("rule-classification",["total_declared_rules","executable_in_package_0_2","deferred_no_subject_artifact","classifications"],{"total_declared_rules":{"type":"integer","minimum":1},"executable_in_package_0_2":{"type":"integer","minimum":1},"deferred_no_subject_artifact":{"type":"integer","minimum":0},"classifications":{"type":"array","minItems":1,"items":{"type":"object"}}})
    schemas["dependency-graph"]=base_schema("dependency-graph",["nodes","edges"],{"nodes":{"type":"array","items":str_prop,"uniqueItems":True},"edges":{"type":"array","items":{"type":"object","required":["from","to"],"properties":{"from":str_prop,"to":str_prop},"additionalProperties":False}}})
    schemas["vector-catalog"]={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":f"{NS}:schema:vector-catalog:{VERSION}","type":"object","required":["$schema","$id","object_id","object_version","catalog_id","catalog_version","source_catalog_ref","vectors","integrity"],"properties":{"$schema":{"const":f"{NS}:schema:vector-catalog:{VERSION}"},"$id":{"const":f"{NS}:vector-catalog:{VERSION}"},"object_id":{"const":f"{NS}:vector-catalog"},"object_version":{"const":VERSION},"catalog_id":{"const":f"{NS}:vector-catalog"},"catalog_version":{"const":VERSION},"source_catalog_ref":ref_prop,"vectors":{"type":"array","minItems":1,"items":{"type":"object","required":["vector_id","source_vector_ref","settlement_profile_ref","evidence_profile_ref","target","expected","classification"],"properties":{"vector_id":str_prop,"source_vector_ref":ref_prop,"settlement_profile_ref":ref_prop,"evidence_profile_ref":ref_prop,"target":{"type":"object","required":["proposition","target_resolution","canonicalization_ref"],"properties":{"proposition":{"type":"object"},"target_resolution":{"type":"object"},"canonicalization_ref":ref_prop},"additionalProperties":True},"expected":{"type":"object"},"classification":{"const":"DECLARATIVE_EXPECTATION_VECTOR"}},"additionalProperties":True}},"integrity":{"type":"object"}},"additionalProperties":True,"$defs":{"objectRef":object_ref_schema()}}
    schemas["object-registry"]=base_schema("object-registry",["uniqueness_key","entries"],{"uniqueness_key":{"const":["kind","id","version"]},"entries":{"type":"array","minItems":1,"items":{"type":"object","required":["kind","id","version","path","integrity","status","role"],"properties":{"kind":str_prop,"id":str_prop,"version":str_prop,"path":str_prop,"integrity":{"type":"object","required":["class","method","algorithm","digest"],"properties":{"class":{"enum":["SEMANTIC_JSON_CONTENT","SELF_EXCLUDING_SEMANTIC_JSON_CONTENT"]},"method":{"const":"RFC8785_JCS"},"algorithm":{"const":"SHA-256"},"digest":{"type":"string","pattern":"^[0-9a-f]{64}$"},"exclusion_pointers":{"type":"array","items":{"type":"string","pattern":"^/"}}},"additionalProperties":False},"status":str_prop,"role":str_prop,"members":{"type":"array","items":str_prop,"uniqueItems":True}},"additionalProperties":False}}})
    schemas["build-manifest"]=base_schema("build-manifest",["mode","verify_default","dependencies","generated_files","phase_a"],{"mode":{"const":"CONTROLLED_BUILD_ONLY"},"verify_default":{"const":"READ_ONLY"},"dependencies":{"type":"object","required":["python","jsonschema","rfc8785"]},"generated_files":{"type":"array","items":str_prop,"uniqueItems":True},"phase_a":{"type":"object","required":["total_rules","executable","deferred","version","broader_model_revision_required"]}})
    schemas["deepseek-draft-evidence"]=base_schema("deepseek-draft-evidence",["role","source_worktree","drafts","reconciliation"],{"role":{"const":"BYTE_PRESERVED_EVIDENCE_METADATA_ONLY"},"source_worktree":str_prop,"drafts":{"type":"array","minItems":6,"maxItems":6,"items":{"type":"object","required":["path","bytes","algorithm","sha256","disposition"],"properties":{"path":str_prop,"bytes":{"type":"integer","minimum":1},"algorithm":{"const":"RAW_FILE_BYTES_SHA256"},"sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"disposition":{"enum":["REUSE","REWRITE","DISCARD"]}},"additionalProperties":False}},"reconciliation":{"type":"object","minProperties":1}})
    # Candidate proposition schemas explicitly bind the frozen predicate vocabulary.
    stages=sorted({e["stage"] for e in entries},key=lambda x:(x is not None,str(x))); predicates=sorted({e["predicate_id"] for e in entries})
    common_prop={"record_type":str_prop,"proposition_id":str_prop,"proposition_kind":str_prop,"effect_id":str_prop,"evidence_profile_id":str_prop,"evidence_profile_version":str_prop,"resource":{},"recipient_or_counterparty":{},"scope":{"type":"object","minProperties":1},"integrity":{"type":"object","required":["canonicalization_ref","content_digest"],"properties":{"canonicalization_ref":ref_prop,"content_digest":{"type":"string","pattern":"^sha-256:[0-9a-f]{64}$"},"digest_algorithm":str_prop},"additionalProperties":False},"schema_ref":ref_prop}
    schemas["positive-effect-proposition"]={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":f"{NS}:schema:positive-effect-proposition:{VERSION}","type":"object","required":["proposition_id","proposition_kind","effect_id","predicate_id","stage","evidence_profile_id","integrity","schema_ref"],"properties":{**common_prop,"proposition_kind":{"enum":["POSITIVE_STAGE","GENERIC_OCCURRENCE"]},"predicate_id":{"enum":predicates},"stage":{"enum":stages}},"additionalProperties":False,"$defs":{"objectRef":object_ref_schema()}}
    schemas["negative-scope-proposition"]={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":f"{NS}:schema:negative-scope-proposition:{VERSION}","type":"object","required":["proposition_id","proposition_kind","effect_id","negated_predicate_id","negated_stage","evidence_profile_id","scope","integrity","schema_ref"],"properties":{**common_prop,"predicate_id":str_prop,"stage":{},"proposition_kind":{"const":"NEGATIVE_SCOPE"},"negated_predicate_id":{"enum":predicates},"negated_stage":{"enum":stages}},"additionalProperties":False,"$defs":{"objectRef":object_ref_schema()}}
    for name,schema in schemas.items(): emit(f"schema/accord-02e4r5-{name}.schema.json",schema)

    accepted_path="docs/accord-02/accord-02r5-specification-package.json"; accepted_digest=jcs_digest(read(accepted_path))
    package={**identity(PKG_ID,"specification-package"),"package_id":PKG_ID,"package_version":VERSION,"status":"CANDIDATE_UNACCEPTED","accepted_base":{"package_id":PKG_ID,"package_version":"0.1","path":accepted_path,"integrity":{"class":"SEMANTIC_JSON_CONTENT","method":"RFC8785_JCS","algorithm":"SHA-256","digest":accepted_digest}},"amendment_relation":"UNACCEPTED_AMENDMENT_OF_ACCEPTED_0_1","rejected_candidate_lineage":[{"revision":"E4R2","status":"REJECTED_PROVENANCE_ONLY"},{"revision":"E4R3","status":"REJECTED_PROVENANCE_ONLY"},{"revision":"E4R4","status":"REJECTED_PROVENANCE_ONLY","commit":"e360ce6c38f044e446ae8ba7e850b35840f2c8f8"}],"object_registry_ref":ref("REGISTRY",f"{NS}:object-registry"),"validation_rules_ref":ref("CONTRACT",f"{NS}:validation-rules"),"assertion_registry_ref":ref("REGISTRY",f"{NS}:assertion-registry"),"primitive_registry_ref":ref("REGISTRY",f"{NS}:primitive-registry"),"rule_classification_ref":ref("CONTRACT",f"{NS}:rule-classification"),"current_candidate_integrity":{"class":"SEMANTIC_JSON_CONTENT","method":"RFC8785_JCS","algorithm":"SHA-256","exclusion_pointers":["/current_candidate_integrity/digest"],"digest":""}}
    package["current_candidate_integrity"]["digest"]=projected_digest(package,["/current_candidate_integrity/digest"])
    schemas["specification-package"]=base_schema("specification-package",["package_id","package_version","status","accepted_base","amendment_relation","rejected_candidate_lineage","object_registry_ref","validation_rules_ref","assertion_registry_ref","primitive_registry_ref","rule_classification_ref","current_candidate_integrity"],{"package_id":{"const":PKG_ID},"package_version":{"const":VERSION},"status":{"const":"CANDIDATE_UNACCEPTED"},"accepted_base":{"type":"object","required":["package_id","package_version","path","integrity"],"properties":{"package_id":{"const":PKG_ID},"package_version":{"const":"0.1"},"path":{"const":accepted_path},"integrity":{"type":"object","required":["class","method","algorithm","digest"],"properties":{"class":{"const":"SEMANTIC_JSON_CONTENT"},"method":{"const":"RFC8785_JCS"},"algorithm":{"const":"SHA-256"},"digest":{"const":accepted_digest}},"additionalProperties":False}},"additionalProperties":False},"amendment_relation":{"const":"UNACCEPTED_AMENDMENT_OF_ACCEPTED_0_1"},"rejected_candidate_lineage":{"type":"array","minItems":3},"object_registry_ref":ref_prop,"validation_rules_ref":ref_prop,"assertion_registry_ref":ref_prop,"primitive_registry_ref":ref_prop,"rule_classification_ref":ref_prop,"current_candidate_integrity":{"type":"object","required":["class","method","algorithm","exclusion_pointers","digest"],"properties":{"class":{"const":"SEMANTIC_JSON_CONTENT"},"method":{"const":"RFC8785_JCS"},"algorithm":{"const":"SHA-256"},"exclusion_pointers":{"const":["/current_candidate_integrity/digest"]},"digest":{"type":"string","pattern":"^[0-9a-f]{64}$"}},"additionalProperties":False}})
    emit("schema/accord-02e4r5-specification-package.schema.json",schemas["specification-package"]); emit("accord-02e4r5-specification-package-0.2.json",package)

    build={**identity(f"{NS}:build-manifest","build-manifest"),"mode":"CONTROLLED_BUILD_ONLY","verify_default":"READ_ONLY","dependencies":{"python":"3.12+","jsonschema":"4.26.0","rfc8785":"0.1.4"},"generated_files":[],"phase_a":{"total_rules":104,"executable":54,"deferred":50,"version":"0.2","broader_model_revision_required":False}}
    emit("accord-02e4r5-build-manifest.json",build)
    build["generated_files"]=sorted(set([p.relative_to(ROOT).as_posix() for p in OUT.rglob("*.json")]+["docs/accord-02e4r5/accord-02e4r5-object-registry.json"]))
    emit("accord-02e4r5-build-manifest.json",build)
    paths=[]
    for path in sorted(OUT.glob("*.json")):
        if path.name in {"accord-02e4r5-object-registry.json"}: continue
        value=json.loads(path.read_text(encoding="utf-8")); oid=value.get("object_id")
        if oid: paths.append(("PACKAGE" if oid==PKG_ID else "REGISTRY" if "registry" in oid else "CANONICALIZATION" if oid==CANON_ID else "PROFILE" if "profile" in oid else "POLICY" if "policy" in oid else "REQUIREMENT_MAP" if "requirement-map" in oid else "CONTRACT",oid,value.get("object_version",VERSION),path,value))
    for path in sorted(SCHEMA.glob("*.json")):
        value=json.loads(path.read_text(encoding="utf-8")); full=value["$id"]; oid=full.rsplit(":",1)[0]; paths.append(("SCHEMA",oid,VERSION,path,value))
    inventory=[]
    for kind,oid,ver,path,value in paths:
        item={"kind":kind,"id":oid,"version":ver,"path":path.relative_to(ROOT).as_posix(),"integrity":{"class":"SEMANTIC_JSON_CONTENT","method":"RFC8785_JCS","algorithm":"SHA-256","digest":jcs_digest(value)},"status":"ACTIVE_CANDIDATE" if "deepseek-draft-evidence" not in oid else "PROVENANCE_EVIDENCE_ONLY","role":"NORMATIVE" if "deepseek-draft-evidence" not in oid else "NON_NORMATIVE_EVIDENCE"}
        if oid==f"{NS}:primitive-registry": item["members"]=[x["primitive_id"] for x in value["primitives"]]
        if oid==f"{NS}:assertion-registry": item["members"]=[x["assertion_id"] for x in value["assertions"]]
        inventory.append(item)
    # The accepted source catalog is an externally bound member collection.
    inventory.append({"kind":"CONTRACT","id":CATALOG_ID,"version":"0.1","path":accepted_path.replace("accord-02r5-specification-package.json","examples/accord-02c-settlement-test-vectors.json"),"integrity":{"class":"SEMANTIC_JSON_CONTENT","method":"RFC8785_JCS","algorithm":"SHA-256","digest":source_binding["integrity"]["digest"]},"status":"ACTIVE_ACCEPTED_SOURCE","role":"NORMATIVE_BOUND_SOURCE","members":[v["vector_id"] for v in read(accepted_catalog_path)["vectors"]]})
    inventory.append({"kind":"SOURCE_VECTOR","id":CATALOG_ID,"version":"0.1","path":accepted_catalog_path,"integrity":{"class":"SEMANTIC_JSON_CONTENT","method":"RFC8785_JCS","algorithm":"SHA-256","digest":source_binding["integrity"]["digest"]},"status":"ACTIVE_ACCEPTED_SOURCE","role":"NORMATIVE_BOUND_SOURCE","members":[v["vector_id"] for v in read(accepted_catalog_path)["vectors"]]})
    registry={**identity(f"{NS}:object-registry","object-registry"),"uniqueness_key":["kind","id","version"],"entries":inventory}
    registry["entries"].append({"kind":"REGISTRY","id":f"{NS}:object-registry","version":VERSION,"path":"docs/accord-02e4r5/accord-02e4r5-object-registry.json","integrity":{"class":"SELF_EXCLUDING_SEMANTIC_JSON_CONTENT","method":"RFC8785_JCS","algorithm":"SHA-256","exclusion_pointers":["/entries/-1/integrity/digest"],"digest":""},"status":"ACTIVE_CANDIDATE","role":"NORMATIVE"})
    registry["entries"][-1]["integrity"]["digest"]=projected_digest(registry,["/entries/"+str(len(registry["entries"])-1)+"/integrity/digest"])
    emit("accord-02e4r5-object-registry.json",registry)



if __name__ == "__main__":
    main()
