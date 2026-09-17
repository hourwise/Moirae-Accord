#!/usr/bin/env python3
"""Deterministically build the additive ACCORD-02E4R4 candidate artifacts."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "accord-02e4r4"
SCHEMA = OUT / "schema"
PROFILE = OUT / "profiles"
NS = "urn:moirae:accord-02e4r4"
VERSION = "0.2"


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def raw_sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def jcs(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def pointer_get(value, pointer):
    current = value
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def pointer_remove(value, pointer):
    result = copy.deepcopy(value)
    parts = pointer.split("/")[1:]
    current = result
    for raw in parts[:-1]:
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    token = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(current, list):
        del current[int(token)]
    else:
        del current[token]
    return result


def content_target(value, target):
    if target["mode"] == "EXCLUDE_JSON_POINTERS":
        result = copy.deepcopy(value)
        for pointer in target["json_pointers"]:
            result = pointer_remove(result, pointer)
        return result
    values = [copy.deepcopy(pointer_get(value, pointer)) for pointer in target["json_pointers"]]
    return values[0] if len(values) == 1 else values


def write(rel: str, value) -> None:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def adopt(value):
    if isinstance(value, dict):
        return {k: adopt(v) for k, v in value.items()}
    if isinstance(value, list):
        return [adopt(v) for v in value]
    if isinstance(value, str):
        return value.replace("accord-02e4r2", "accord-02e4r4").replace("accord-02e4r3", "accord-02e4r4")
    return value


def schema_doc(name: str, required: list[str], properties: dict, *, extra=True, defs=None):
    doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:schema:{name}:{VERSION}",
        "title": f"ACCORD-02E4R4 {name} semantic domain",
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": extra,
    }
    if defs:
        doc["$defs"] = defs
    return doc


def s_string(**kw):
    return {"type": "string", **kw}


def reference_annotation(kind: str):
    return {"type": "string", "minLength": 1, "x-normative-reference": {"reference_kind": kind}}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    SCHEMA.mkdir(parents=True, exist_ok=True)
    PROFILE.mkdir(parents=True, exist_ok=True)

    # Adopt the four formerly active rejected-candidate profiles and the one R3
    # canonicalization authority into candidate-owned E4R4 identities.
    adopted_sources = {
        "settlement-profile-conservative": "docs/accord-02e4r2/profiles/accord-02e4r2-settlement-profile-conservative-v2.json",
        "settlement-profile-incompatible": "docs/accord-02e4r2/profiles/accord-02e4r2-settlement-profile-incompatible-v2.json",
        "predicate-applicability-profile": "docs/accord-02e4r2/accord-02e4r2-predicate-applicability-registry.json",
        "canonicalization-profile": "docs/accord-02e4r3/canonicalization/accord-02e4r3-canonicalization-profile.json",
    }
    adopted_paths = {}
    for name, source in adopted_sources.items():
        rel = f"profiles/accord-02e4r4-{name}.json"
        value = adopt(load(source))
        value["e4r4_adoption"] = {
            "source_path": source,
            "source_raw_sha256": raw_sha(source),
            "source_role": "PROVENANCE_ONLY",
            "active_identity_owner": "ACCORD-02E4R4",
        }
        write(rel, value)
        adopted_paths[name] = f"docs/accord-02e4r4/{rel}"

    accepted_path = "docs/accord-02/examples/accord-02c-settlement-test-vectors.json"
    accepted = load(accepted_path)
    vector_classes = [
        {
            "vector_id": v["vector_id"],
            "classification": "DECLARATIVE_EXPECTATION_VECTOR",
            "basis": "Accepted 0.1 describes offline fixture claims and a future verifier; it does not supply an executable settlement implementation.",
            "expected_object_preserved": True,
        }
        for v in accepted["vectors"]
    ]
    vector_catalog = adopt(load("docs/accord-02e4r3/accord-02e4r3-settlement-vector-catalog.json"))
    vector_catalog["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    vector_catalog["$id"] = f"{NS}:settlement-vector-catalog:{VERSION}"
    vector_catalog["catalog_id"] = f"{NS}:settlement-vector-catalog"
    vector_catalog["catalog_version"] = VERSION
    vector_catalog["source_catalog_binding_id"] = f"{NS}:external-member-binding:accepted-vector-catalog"
    vector_catalog["classification_policy"] = "ACCEPTED_0_1_DECLARATIVE_EXPECTATIONS"
    vector_catalog["classification_evidence"] = vector_classes
    vector_catalog["synthetic_executable_fixtures"] = ["ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE"]
    for vector in vector_catalog["vectors"]:
        vector["classification"] = "DECLARATIVE_EXPECTATION_VECTOR"
    canon_for_digest = adopt(load("docs/accord-02e4r3/canonicalization/accord-02e4r3-canonicalization-profile.json"))
    targets_for_digest = {x["content_target_id"]: x for x in canon_for_digest["content_target_registry"]}
    for vector in vector_catalog["vectors"]:
        proposition = vector["target"]["proposition"]
        mapping = next(x for x in canon_for_digest["applies_to"] if x["container_type"] == "VERIFIER_RECORD_ENTRY" and x["schema_id"] == proposition["schema_id"] and x["schema_version"] == proposition["schema_version"] and proposition["record_type"] in x["record_types"])
        proposition["integrity"]["content_digest"] = "sha-256:" + hashlib.sha256(jcs(content_target(proposition, targets_for_digest[mapping["content_target_id"]]))).hexdigest()
    catalog_mapping = next(x for x in canon_for_digest["applies_to"] if x["container_type"] == "EXPERIMENT_RECORD_ENTRY" and "SETTLEMENT_VECTOR_CATALOG" in x["record_types"])
    vector_catalog["integrity"]["content_digest"] = "sha-256:" + hashlib.sha256(jcs(content_target(vector_catalog, targets_for_digest[catalog_mapping["content_target_id"]]))).hexdigest()
    write("accord-02e4r4-settlement-vector-catalog.json", vector_catalog)

    source_binding = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:external-member-binding:accepted-vector-catalog:{VERSION}",
        "binding_id": f"{NS}:external-member-binding:accepted-vector-catalog",
        "binding_version": VERSION,
        "assigned_object_id": "urn:moirae:accord-02:accepted:settlement-vector-catalog",
        "assigned_object_version": "0.1",
        "identity_assignment": "PACKAGE_EXTERNAL_MEMBER_BINDING_NOT_HISTORICAL_SELF_ASSERTION",
        "repository_root_path": accepted_path,
        "digest_algorithm": "SHA-256",
        "digest_scope": "RAW_BYTES",
        "raw_sha256": raw_sha(accepted_path),
    }
    write("accord-02e4r4-source-catalog-binding.json", source_binding)

    target = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:v013-target:{VERSION}",
        "target_id": f"{NS}:target:v013",
        "target_version": VERSION,
        "source_vector_id": "ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE",
        "effect_id": "urn:accord:02c:effect:E13",
        "negated_predicate_id": "urn:accord:02c:predicate:external-effect",
        "negated_stage": "effect",
        "scope": {"resource": "NOT_APPLICABLE", "action": "NOT_APPLICABLE", "recipient": "NOT_APPLICABLE", "provider": "NOT_APPLICABLE"},
        "required_interval": {"not_before": "2025-01-01T00:00:00Z", "as_of": "2025-01-02T00:00:00Z"},
        "verification_time": "2025-01-02T00:01:00Z",
        "minimum_retention_seconds": 86400,
    }
    evidence = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:complete-negative-evidence:v013:{VERSION}",
        "evidence_id": f"{NS}:evidence:v013:synthetic-complete-negative",
        "evidence_version": VERSION,
        "fixture_status": "SYNTHETIC_CANDIDATE_0_2_NOT_ACCEPTED_HISTORY",
        "effect_id": target["effect_id"],
        "predicate_id": target["negated_predicate_id"],
        "stage": target["negated_stage"],
        "scope": copy.deepcopy(target["scope"]),
        "observed_interval": copy.deepcopy(target["required_interval"]),
        "retention_window_seconds": 172800,
        "consistency_level": "SNAPSHOT_COMPLETE",
        "read_semantics": "COMPLETE_LEDGER_QUERY",
        "observed_at": "2025-01-02T00:00:00Z",
        "verification_time": target["verification_time"],
        "freshness_max_age_seconds": 300,
        "evidence_class": "COMPLETE_NEGATIVE_LEDGER_QUERY",
        "read_scope_complete": True,
        "evidence_universe": [
            {
                "evidence_id": f"{NS}:evidence:v013:synthetic-complete-negative",
                "admissible": True,
                "polarity": "NEGATIVE",
                "effect_id": target["effect_id"],
                "predicate_id": target["negated_predicate_id"],
                "stage": target["negated_stage"],
                "scope": copy.deepcopy(target["scope"]),
            }
        ],
    }
    negative_contract = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:negative-scope-contract:{VERSION}",
        "contract_id": f"{NS}:negative-scope-contract",
        "contract_version": VERSION,
        "target_path": "docs/accord-02e4r4/accord-02e4r4-v013-target.json",
        "evidence_path": "docs/accord-02e4r4/accord-02e4r4-complete-negative-evidence.json",
        "retention_semantics": "RETENTION_WINDOW_MUST_COVER_REQUIRED_INTERVAL_AND_MEET_PROFILE_MINIMUM",
        "retention_formula": "retention_window_seconds >= max(interval_seconds, minimum_retention_seconds)",
        "contradiction_filter": {
            "polarity": "POSITIVE",
            "admissible": True,
            "identity_basis": "TARGET_NOT_EVIDENCE_RECORD",
            "match": ["effect_id", "predicate_id", "stage", "scope"],
            "deduplicate_by": "evidence_id",
        },
        "requirements": [
            "TARGET_IDENTITY_EQUAL", "TARGET_SCOPE_EQUAL", "INTERVAL_COVERS_TARGET",
            "RETENTION_COVERS_INTERVAL_AND_MINIMUM", "CONSISTENCY_ALLOWED", "READ_SEMANTICS_COMPLETE",
            "FRESH_AT_VERIFICATION", "SOURCE_CLASS_ALLOWED", "READ_SCOPE_COMPLETE", "NO_SAME_TARGET_POSITIVE",
        ],
    }
    write("accord-02e4r4-v013-target.json", target)
    write("accord-02e4r4-complete-negative-evidence.json", evidence)
    write("accord-02e4r4-negative-scope-contract.json", negative_contract)

    # Preserve and adopt core candidate contracts without retaining an active E4R2/E4R3 identity.
    copies = {
        "predicate-registry": "docs/accord-02e4r3/accord-02e4r3-predicate-registry.json",
        "normative-contracts": "docs/accord-02e4r3/accord-02e4r3-normative-contracts.json",
        "profile-semantics": "docs/accord-02e4r3/accord-02e4r3-profile-semantics.json",
        "source-schema-registry": "docs/accord-02e4r3/accord-02e4r3-source-schema-registry.json",
        "reference-semantics": "docs/accord-02e4r3/accord-02e4r3-reference-semantics.json",
        "partial-effect-policy": "docs/accord-02e4r3/accord-02e4r3-partial-effect-policy.json",
    }
    for name, source in copies.items():
        obj = adopt(load(source))
        obj.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
        obj.setdefault("$id", f"{NS}:{name}:{VERSION}")
        if name == "predicate-registry":
            obj["registry_id"] = f"{NS}:predicate-registry"
            obj["profile_id"] = obj["registry_id"]
        obj["e4r4_adoption"] = {"source_path": source, "source_raw_sha256": raw_sha(source), "source_role": "PROVENANCE_ONLY"}
        write(f"accord-02e4r4-{name}.json", obj)

    operand_schema = {
        "type": "object",
        "required": ["rule_id", "source_artifact_classes", "declared_assertion_id"],
        "properties": {
            "rule_id": {"type": "string", "minLength": 1},
            "source_artifact_classes": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
            "declared_assertion_id": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }
    operator_specs = {
        "REFERENCE_GRAPH_CLOSED": ("discover schema-annotated non-null references and require exact resolution", "REFERENCES_CLOSED"),
        "DECLARED_CONTRACT_INVARIANT_VALID": ("resolve declared_assertion_id and evaluate its structured check conjunction", "ASSERTION_EXPRESSION"),
        "BINDING_COMPOSITION_VALID": ("evaluate exact identity and scope binding checks selected by the assertion", "BINDINGS_VALID"),
        "DEPENDENCY_GRAPH_EQUALS_RULES": ("derive node and edge sets from rules and compare exact sets", "GRAPH_EQUAL"),
        "DIGEST_MATCHES_DECLARED_MAPPING": ("recompute declared SHA-256 byte or canonical targets and compare", "DIGESTS_VALID"),
        "EFFECTIVE_INVENTORY_VALID": ("validate registered active object inventory and unique identities", "IDENTITY_UNIQUE"),
        "EXPECTATION_SET_EQUAL": ("compare accepted and candidate expected objects including reasons and prohibitions", "EXPECTATIONS_STABLE"),
        "NEGATIVE_SCOPE_REQUIREMENTS_PASS": ("evaluate the complete-negative target/evidence contract", "V013_VALID"),
        "PREDICATE_REGISTRY_VALID": ("validate unique predicate-stage registry keys and active identity", "PREDICATE_REGISTRY_VALID"),
        "PROFILE_PAIR_COMPATIBLE": ("validate active profile bindings and candidate-owned replacements", "PROFILES_VALID"),
        "STRICT_SCHEMA_VALID": ("validate all effective instances with Draft 2020-12 and format checking", "SCHEMAS_VALID"),
    }
    operators = []
    for operator_id, (rule_text, check_id) in operator_specs.items():
        operators.append({
            "operator_id": operator_id,
            "operator_version": "1.0",
            "operand_schema": copy.deepcopy(operand_schema),
            "operand_sources": {"rule_id": "RULE", "source_artifact_classes": "RULE", "declared_assertion_id": "RULE_AND_ASSERTION_REGISTRY"},
            "evaluation": {"kind": "NAMED_CHECK_DISPATCH", "check_id": check_id, "rule": rule_text},
            "result_schema": {"type": "boolean"},
            "failure_codes": [f"{operator_id}_FAILED", "MALFORMED_OPERANDS", "UNDEFINED_ASSERTION"],
            "error_behavior": "FAIL_CLOSED",
            "implementation_function": f"op_{operator_id.lower()}",
        })
    operator_registry = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:operator-registry:{VERSION}",
        "registry_id": f"{NS}:operator-registry",
        "registry_version": VERSION,
        "primitive_vocabulary": sorted({v[1] for v in operator_specs.values()} | {"PACKAGE_CANDIDATE", "RULES_WELL_FORMED", "OPERATORS_TYPED", "CANONICALIZATION_VALID", "SOURCE_CATALOG_BOUND"}),
        "operators": operators,
    }
    write("accord-02e4r4-operator-registry.json", operator_registry)

    old_rules_doc = load("docs/accord-02e4r3/accord-02e4r3-validation-rules.json")
    rules = adopt(old_rules_doc)
    rules["$id"] = f"{NS}:validation-rules:{VERSION}"
    rules["profile_id"] = f"{NS}:validation-rules"
    rules["profile_version"] = VERSION
    assertions = {}
    for rule in rules["rules"]:
        operands = rule["condition"]["operands"]
        aid = operands["declared_assertion_id"]
        family = operator_specs[rule["condition"]["operator_id"]][1]
        checks = [family, "PACKAGE_CANDIDATE", "RULES_WELL_FORMED", "OPERATORS_TYPED"]
        token = aid.upper()
        if "NEGATIVE" in token or "NON_OCCURRENCE" in token:
            checks.append("V013_VALID")
        if "DIGEST" in token or "CANONICAL" in token:
            checks.extend(["DIGESTS_VALID", "CANONICALIZATION_VALID"])
        if "REFERENCE" in token or "RESOLV" in token or "CLOSED" in token:
            checks.append("REFERENCES_CLOSED")
        if "PROFILE" in token:
            checks.append("PROFILES_VALID")
        if "EXPECT" in token or "VECTOR" in token:
            checks.append("EXPECTATIONS_STABLE")
        assertions.setdefault(aid, {
            "assertion_id": aid,
            "expression": {"operator": "ALL", "checks": list(dict.fromkeys(checks))},
            "result_type": "boolean",
            "error_behavior": "FAIL_CLOSED",
        })
    assertion_registry = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:assertion-registry:{VERSION}",
        "registry_id": f"{NS}:assertion-registry",
        "registry_version": VERSION,
        "assertions": sorted(assertions.values(), key=lambda x: x["assertion_id"]),
    }
    write("accord-02e4r4-assertion-registry.json", assertion_registry)
    write("accord-02e4r4-validation-rules.json", rules)

    node_ids = [r["rule_id"] for r in rules["rules"]]
    edges = []
    for r in rules["rules"]:
        for dep in r.get("depends_on", []):
            edges.append({"from": r["rule_id"], "to": dep})
    graph = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:dependency-graph:{VERSION}",
        "graph_id": f"{NS}:dependency-graph",
        "graph_version": VERSION,
        "derivation": "RULES_DEPENDS_ON_EXACT_SET",
        "nodes": node_ids,
        "edges": edges,
    }
    write("accord-02e4r4-dependency-graph.json", graph)

    # Active profiles: accepted material remains active and byte-bound; the four
    # rejected-candidate members are replaced by R4-owned adoptions.
    old_profiles = load("docs/accord-02e4r3/accord-02e4r3-specification-package-0.2.json")["profile_contracts"]
    profiles = []
    replacement = {
        "docs/accord-02e4r2/profiles/accord-02e4r2-settlement-profile-conservative-v2.json": adopted_paths["settlement-profile-conservative"],
        "docs/accord-02e4r2/profiles/accord-02e4r2-settlement-profile-incompatible-v2.json": adopted_paths["settlement-profile-incompatible"],
        "docs/accord-02e4r2/canonicalization/accord-02e4r2-canonicalization-profile.json": adopted_paths["canonicalization-profile"],
        "docs/accord-02e4r2/accord-02e4r2-predicate-applicability-registry.json": adopted_paths["predicate-applicability-profile"],
    }
    for p in old_profiles:
        q = adopt(p)
        q["profile_path"] = replacement.get(p["profile_path"], p["profile_path"])
        q["schema_id"] = f"{NS}:schema:effective-profile-domain:{VERSION}"
        q["schema_version"] = VERSION
        q["raw_sha256"] = raw_sha(q["profile_path"])
        q["integrity_scope"] = "RAW_BYTES"
        profiles.append(q)
    profile_manifest = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:effective-profile-manifest:{VERSION}",
        "manifest_id": f"{NS}:effective-profile-manifest",
        "manifest_version": VERSION,
        "classification": {
            "semantic_domain": "effective-profile-domain schema",
            "frozen_identity": ["profile_type", "profile_version", "record_type", "contract_class", "status"],
            "fixture_integrity": ["profile_path", "raw_sha256", "integrity_scope"],
        },
        "profiles": profiles,
    }
    write("accord-02e4r4-effective-profile-manifest.json", profile_manifest)

    # Schemas are hand-authored domains, not fixture transcriptions.
    id_props = {"$schema": {"const": "https://json-schema.org/draft/2020-12/schema"}, "$id": s_string(pattern="^urn:moirae:accord-02e4r4:")}
    schemas = {}
    schemas["generic-contract"] = schema_doc("generic-contract", ["$schema", "$id"], id_props)
    schemas["effective-profile-domain"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:schema:effective-profile-domain:{VERSION}",
        "title": "Reusable effective profile semantic domain", "type": "object", "minProperties": 1,
        "not": {"required": ["e4r4_forbidden_active_rejected_candidate"]},
    }
    schemas["complete-negative-evidence"] = schema_doc("complete-negative-evidence",
        ["$schema", "$id", "evidence_id", "evidence_version", "fixture_status", "effect_id", "predicate_id", "stage", "scope", "observed_interval", "retention_window_seconds", "consistency_level", "read_semantics", "observed_at", "verification_time", "freshness_max_age_seconds", "evidence_class", "read_scope_complete", "evidence_universe"],
        {**id_props, "$id": s_string(minLength=1),
         "evidence_id": s_string(minLength=1), "evidence_version": {"const": VERSION},
         "fixture_status": {"enum": ["SYNTHETIC_CANDIDATE_0_2_NOT_ACCEPTED_HISTORY", "EXTERNAL_BOUND_EVIDENCE"]},
         "effect_id": s_string(minLength=1), "predicate_id": s_string(minLength=1), "stage": {"enum": ["attempt", "dispatch", "acceptance", "processing", "effect", "delivery", "visibility", "settlement"]},
         "scope": {"type": "object", "required": ["resource", "action", "recipient", "provider"], "properties": {k: s_string(minLength=1) for k in ["resource", "action", "recipient", "provider"]}, "additionalProperties": False},
         "observed_interval": {"type": "object", "required": ["not_before", "as_of"], "properties": {"not_before": {"type": "string", "format": "date-time"}, "as_of": {"type": "string", "format": "date-time"}}, "additionalProperties": False},
         "retention_window_seconds": {"type": "integer", "minimum": 1},
         "consistency_level": {"enum": ["SNAPSHOT_COMPLETE", "LINEARIZABLE_COMPLETE"]},
         "read_semantics": {"const": "COMPLETE_LEDGER_QUERY"}, "observed_at": {"type": "string", "format": "date-time"}, "verification_time": {"type": "string", "format": "date-time"},
         "freshness_max_age_seconds": {"type": "integer", "minimum": 0}, "evidence_class": {"enum": ["COMPLETE_NEGATIVE_LEDGER_QUERY", "COMPLETE_NEGATIVE_AUTHORITATIVE_SNAPSHOT"]},
         "read_scope_complete": {"const": True},
         "evidence_universe": {"type": "array", "uniqueItems": True, "items": {"type": "object", "required": ["evidence_id", "admissible", "polarity", "effect_id", "predicate_id", "stage", "scope"], "properties": {"evidence_id": s_string(minLength=1), "admissible": {"type": "boolean"}, "polarity": {"enum": ["POSITIVE", "NEGATIVE"]}, "effect_id": s_string(minLength=1), "predicate_id": s_string(minLength=1), "stage": s_string(minLength=1), "scope": {"type": "object"}}, "additionalProperties": False}},
        }, extra=False)
    schemas["operator-registry"] = schema_doc("operator-registry", ["$schema", "$id", "registry_id", "registry_version", "primitive_vocabulary", "operators"], {**id_props, "registry_id": s_string(), "registry_version": {"const": VERSION}, "primitive_vocabulary": {"type": "array", "uniqueItems": True, "items": s_string()}, "operators": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["operator_id", "operator_version", "operand_schema", "operand_sources", "evaluation", "result_schema", "failure_codes", "error_behavior", "implementation_function"]}}})
    schemas["validation-rules"] = schema_doc("validation-rules", ["$schema", "$id", "rules"], {**id_props, "rules": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["rule_id", "condition", "failure_code", "severity"], "properties": {"rule_id": s_string(), "depends_on": {"type": "array", "uniqueItems": True, "items": s_string()}, "condition": {"type": "object", "required": ["operator_id", "operands"]}, "failure_code": s_string(), "severity": s_string()}, "additionalProperties": True}}})
    schemas["assertion-registry"] = schema_doc("assertion-registry", ["$schema", "$id", "registry_id", "registry_version", "assertions"], {**id_props, "registry_id": s_string(), "registry_version": {"const": VERSION}, "assertions": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["assertion_id", "expression", "result_type", "error_behavior"]}}})
    schemas["dependency-graph"] = schema_doc("dependency-graph", ["$schema", "$id", "graph_id", "graph_version", "nodes", "edges"], {**id_props, "graph_id": s_string(), "graph_version": {"const": VERSION}, "nodes": {"type": "array", "uniqueItems": True, "items": s_string()}, "edges": {"type": "array", "uniqueItems": True, "items": {"type": "object", "required": ["from", "to"], "properties": {"from": s_string(), "to": s_string()}, "additionalProperties": False}}})
    schemas["source-catalog-binding"] = schema_doc("source-catalog-binding", ["$schema", "$id", "binding_id", "binding_version", "assigned_object_id", "assigned_object_version", "identity_assignment", "repository_root_path", "digest_algorithm", "digest_scope", "raw_sha256"], {**id_props, "binding_id": s_string(), "binding_version": {"const": VERSION}, "assigned_object_id": s_string(), "assigned_object_version": s_string(), "identity_assignment": {"const": "PACKAGE_EXTERNAL_MEMBER_BINDING_NOT_HISTORICAL_SELF_ASSERTION"}, "repository_root_path": reference_annotation("RAW_BYTE_EXTERNAL_MEMBER"), "digest_algorithm": {"const": "SHA-256"}, "digest_scope": {"const": "RAW_BYTES"}, "raw_sha256": s_string(pattern="^[0-9a-f]{64}$")}, extra=False)
    schemas["vector-catalog"] = schema_doc("vector-catalog", ["$schema", "$id", "catalog_id", "catalog_version", "source_catalog_binding_id", "classification_policy", "vectors", "classification_evidence"], {**id_props, "catalog_id": s_string(), "catalog_version": {"const": VERSION}, "source_catalog_binding_id": s_string(), "classification_policy": {"const": "ACCEPTED_0_1_DECLARATIVE_EXPECTATIONS"}, "vectors": {"type": "array", "minItems": 23, "maxItems": 23, "uniqueItems": True, "items": {"type": "object", "required": ["vector_id", "classification", "expected"], "properties": {"vector_id": s_string(), "classification": {"const": "DECLARATIVE_EXPECTATION_VECTOR"}, "expected": {"type": "object"}}, "additionalProperties": True}}, "classification_evidence": {"type": "array", "minItems": 23, "maxItems": 23}, "synthetic_executable_fixtures": {"type": "array", "uniqueItems": True, "items": s_string()}})
    schemas["target"] = schema_doc("target", ["$schema", "$id", "target_id", "target_version", "source_vector_id", "effect_id", "negated_predicate_id", "negated_stage", "scope", "required_interval", "verification_time", "minimum_retention_seconds"], {**id_props, "target_id": s_string(), "target_version": {"const": VERSION}, "source_vector_id": s_string(), "effect_id": s_string(), "negated_predicate_id": s_string(), "negated_stage": s_string(), "scope": {"type": "object"}, "required_interval": {"type": "object"}, "verification_time": {"type": "string", "format": "date-time"}, "minimum_retention_seconds": {"type": "integer", "minimum": 1}})
    schemas["profile-manifest"] = schema_doc("profile-manifest", ["$schema", "$id", "manifest_id", "manifest_version", "classification", "profiles"], {**id_props, "manifest_id": s_string(), "manifest_version": {"const": VERSION}, "classification": {"type": "object"}, "profiles": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["profile_id", "profile_version", "profile_path", "schema_id", "schema_version", "raw_sha256", "integrity_scope", "status"], "properties": {"profile_path": reference_annotation("PROFILE"), "schema_id": s_string()}, "additionalProperties": True}}})
    schemas["negative-contract"] = schema_doc("negative-contract", ["$schema", "$id", "contract_id", "contract_version", "target_path", "evidence_path", "retention_semantics", "retention_formula", "contradiction_filter", "requirements"], {**id_props, "contract_id": s_string(), "contract_version": {"const": VERSION}, "target_path": reference_annotation("TARGET"), "evidence_path": reference_annotation("EVIDENCE"), "retention_semantics": {"const": "RETENTION_WINDOW_MUST_COVER_REQUIRED_INTERVAL_AND_MEET_PROFILE_MINIMUM"}, "retention_formula": s_string(), "contradiction_filter": {"type": "object"}, "requirements": {"type": "array", "minItems": 10, "uniqueItems": True, "items": s_string()}})
    for name, doc in schemas.items():
        write(f"schema/accord-02e4r4-{name}.schema.json", doc)

    instance_specs = [
        ("predicate-registry", "generic-contract"), ("normative-contracts", "generic-contract"),
        ("profile-semantics", "generic-contract"), ("source-schema-registry", "generic-contract"),
        ("reference-semantics", "generic-contract"), ("partial-effect-policy", "generic-contract"),
        ("operator-registry", "operator-registry"), ("assertion-registry", "assertion-registry"),
        ("validation-rules", "validation-rules"), ("dependency-graph", "dependency-graph"),
        ("settlement-vector-catalog", "vector-catalog"), ("source-catalog-binding", "source-catalog-binding"),
        ("v013-target", "target"), ("complete-negative-evidence", "complete-negative-evidence"),
        ("negative-scope-contract", "negative-contract"), ("effective-profile-manifest", "profile-manifest"),
    ]
    active_instances = []
    for artifact, schema in instance_specs:
        path = f"docs/accord-02e4r4/accord-02e4r4-{artifact}.json"
        active_instances.append({"artifact": artifact, "path": path, "schema_id": f"{NS}:schema:{schema}:{VERSION}", "schema_path": f"docs/accord-02e4r4/schema/accord-02e4r4-{schema}.schema.json", "status": "ACTIVE"})

    package = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{NS}:specification-package:{VERSION}",
        "package_id": f"{NS}:specification-package",
        "package_version": VERSION,
        "status": "CANDIDATE_UNACCEPTED",
        "lineage": {"parent_commit": "a2ea38f7788a4c829f64af72f41f32d1188d1154", "accepted_0_1": "5a8bf1e577f71132665ece271e70e30e87df5676", "rejected_candidates": ["E4R2", "E4R3"], "provenance_only_definition": "MUST_NOT_SUPPLY_ACTIVE_NORMATIVE_CONTRACTS"},
        "active_instances": active_instances,
        "active_profiles_manifest_path": "docs/accord-02e4r4/accord-02e4r4-effective-profile-manifest.json",
        "operator_registry_path": "docs/accord-02e4r4/accord-02e4r4-operator-registry.json",
        "assertion_registry_path": "docs/accord-02e4r4/accord-02e4r4-assertion-registry.json",
        "rules_path": "docs/accord-02e4r4/accord-02e4r4-validation-rules.json",
        "graph_path": "docs/accord-02e4r4/accord-02e4r4-dependency-graph.json",
        "source_catalog_binding_path": "docs/accord-02e4r4/accord-02e4r4-source-catalog-binding.json",
        "canonicalization_authority_path": adopted_paths["canonicalization-profile"],
        "predicate_registry_path": "docs/accord-02e4r4/accord-02e4r4-predicate-registry.json",
        "design_freeze": {"vectors": 23, "expectation_axes": 13, "must_not_conclude": 31, "accepted_outcome_changes": 0},
    }
    package_schema = schema_doc("specification-package", ["$schema", "$id", "package_id", "package_version", "status", "lineage", "active_instances", "active_profiles_manifest_path", "operator_registry_path", "assertion_registry_path", "rules_path", "graph_path", "source_catalog_binding_path", "canonicalization_authority_path", "predicate_registry_path", "design_freeze"], {**id_props, "package_id": s_string(), "package_version": {"const": VERSION}, "status": {"const": "CANDIDATE_UNACCEPTED"}, "lineage": {"type": "object"}, "active_instances": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "object", "required": ["artifact", "path", "schema_id", "schema_path", "status"], "properties": {"artifact": s_string(), "path": reference_annotation("ACTIVE_INSTANCE"), "schema_id": s_string(), "schema_path": reference_annotation("SCHEMA"), "status": {"const": "ACTIVE"}}, "additionalProperties": False}}, "active_profiles_manifest_path": reference_annotation("PROFILE_MANIFEST"), "operator_registry_path": reference_annotation("OPERATOR_REGISTRY"), "assertion_registry_path": reference_annotation("ASSERTION_REGISTRY"), "rules_path": reference_annotation("RULES"), "graph_path": reference_annotation("GRAPH"), "source_catalog_binding_path": reference_annotation("EXTERNAL_MEMBER_BINDING"), "canonicalization_authority_path": reference_annotation("CANONICALIZATION_PROFILE"), "predicate_registry_path": reference_annotation("PREDICATE_REGISTRY"), "design_freeze": {"type": "object", "required": ["vectors", "expectation_axes", "must_not_conclude", "accepted_outcome_changes"], "properties": {"vectors": {"const": 23}, "expectation_axes": {"const": 13}, "must_not_conclude": {"const": 31}, "accepted_outcome_changes": {"const": 0}}, "additionalProperties": False}})
    # A deliberately valid, structurally disjoint oneOf exercises the real keyword.
    package_schema["allOf"] = [{"anyOf": [{"required": ["status"]}, {"required": ["package_version"]}]}, {"oneOf": [{"properties": {"status": {"const": "CANDIDATE_UNACCEPTED"}}}, {"required": ["accepted_at"]}]}]
    write("schema/accord-02e4r4-specification-package.schema.json", package_schema)
    package["active_instances"].insert(0, {"artifact": "specification-package", "path": "docs/accord-02e4r4/accord-02e4r4-specification-package-0.2.json", "schema_id": f"{NS}:schema:specification-package:{VERSION}", "schema_path": "docs/accord-02e4r4/schema/accord-02e4r4-specification-package.schema.json", "status": "ACTIVE"})
    write("accord-02e4r4-specification-package-0.2.json", package)

    readme = """# ACCORD-02E4R4 — Executable Semantics and Standards Conformance\n\nStatus: `0.2 CANDIDATE_UNACCEPTED`. This additive candidate repairs E4R3 schema, identity, operator, per-rule execution, V013 binding, vector classification, and source-byte binding defects. Rejected candidates are provenance only and supply no active normative contract.\n\nAll 23 accepted vectors remain declarative expectation fixtures exactly as accepted 0.1 describes them. V013 additionally has a candidate-owned synthetic executable fixture; it is not represented as historical evidence. Standards validation requires `jsonschema==4.26.0`.\n"""
    (OUT / "ACCORD-02E4R4-EXECUTABLE-SEMANTICS-REMEDIATION.md").write_text(readme, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
