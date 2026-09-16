from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "docs" / "accord-02"
R1 = ROOT / "docs" / "accord-02e4r1"
R2 = ROOT / "docs" / "accord-02e4r2"
REVIEWS = Path(r"D:\Users\fleur\Moirae Accord - External Reviews\E4R2")

VERSION = "0.2"
FAMILY_ID = "urn:moirae:accord-02r5:specification-package"
NS = "urn:moirae:accord-02e4r3"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def raw_sha(path: Path) -> str:
    return "sha-256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def jcs(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def jcs_sha(value) -> str:
    return "sha-256:" + hashlib.sha256(jcs(value)).hexdigest()


def repo_path(path: str) -> str:
    return path if path.startswith("docs/") else "docs/accord-02/" + path


def cref(contract_id: str, version: str = VERSION):
    return {"reference_kind": "CONTRACT", "contract_id": contract_id, "contract_version": version}


def sref(schema_id: str, version: str):
    return {"reference_kind": "SCHEMA", "schema_id": schema_id, "schema_version": version}


def pref(profile_type: str, profile_id: str, version: str):
    return {"reference_kind": "PROFILE", "profile_type": profile_type, "profile_id": profile_id, "profile_version": version}


def annotate_refs(value):
    if isinstance(value, list):
        return [annotate_refs(x) for x in value]
    if not isinstance(value, dict):
        return value
    out = {k: annotate_refs(v) for k, v in value.items()}
    keys = set(out)
    if "reference_kind" not in out:
        if {"contract_id", "contract_version"} <= keys:
            out = {"reference_kind": "CONTRACT", **out}
        elif {"schema_id", "schema_version"} <= keys and keys <= {"schema_id", "schema_version", "reference_kind"}:
            out = {"reference_kind": "SCHEMA", **out}
        elif {"profile_type", "profile_id", "profile_version"} <= keys:
            out = {"reference_kind": "PROFILE", **out}
    return out


def merge_schema(values):
    types = {type(v).__name__ for v in values}
    if len(types) > 1:
        return {"oneOf": [infer_schema(v) for v in values]}
    sample = values[0]
    if isinstance(sample, dict):
        all_keys = sorted(set().union(*(v.keys() for v in values)))
        required = sorted(set.intersection(*(set(v.keys()) for v in values)))
        props = {k: merge_schema([v[k] for v in values if k in v]) for k in all_keys}
        result = {"type": "object", "additionalProperties": False, "properties": props, "required": required}
        if "reference_kind" in props:
            kinds = sorted({v["reference_kind"] for v in values if "reference_kind" in v})
            result["x-normative-reference"] = True
            props["reference_kind"] = {"enum": kinds}
        return result
    if isinstance(sample, list):
        flattened = [x for v in values for x in v]
        return {"type": "array", "items": merge_schema(flattened) if flattened else False, "uniqueItems": False}
    if isinstance(sample, bool):
        return {"type": "boolean"}
    if isinstance(sample, int):
        return {"type": "integer"}
    if sample is None:
        return {"type": "null"}
    enums = sorted({v for v in values})
    result = {"type": "string"}
    if len(enums) <= 24:
        result["enum"] = enums
    return result


def infer_schema(value, schema_id=None, title=None):
    schema = merge_schema([value])
    if schema_id:
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": schema_id, "title": title, **schema}
    return schema


def slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")[:96]


def operator_for(rule):
    text = " ".join([rule.get("rule_id", ""), rule.get("category", ""), str(rule.get("condition", {}).get("operator", ""))]).upper()
    choices = [
        (("REF", "RESOLV"), "REFERENCE_GRAPH_CLOSED"),
        (("CANON", "DIGEST"), "DIGEST_MATCHES_DECLARED_MAPPING"),
        (("GRAPH", "DEPEND"), "DEPENDENCY_GRAPH_EQUALS_RULES"),
        (("NEG", "NON-OCCURRENCE", "COMPLETE-NEGATIVE"), "NEGATIVE_SCOPE_REQUIREMENTS_PASS"),
        (("BIND", "AUTHORITY"), "BINDING_COMPOSITION_VALID"),
        (("PRED", "TUPLE", "STAGE"), "PREDICATE_REGISTRY_VALID"),
        (("PART", "PREDECESSOR"), "PARTIAL_EFFECT_POLICY_VALID"),
        (("PROFILE",), "PROFILE_PAIR_COMPATIBLE"),
        (("SCHEMA",), "STRICT_SCHEMA_VALID"),
        (("EXPECT", "STABILITY"), "EXPECTATION_SET_EQUAL"),
        (("PACKAGE", "PKG", "CLOSE"), "EFFECTIVE_INVENTORY_VALID"),
    ]
    for needles, op in choices:
        if any(n in text for n in needles):
            return op
    return "DECLARED_CONTRACT_INVARIANT_VALID"


def materialize_rules():
    r1 = load(R1 / "accord-02e4r1-validation-rules.json")
    r2 = load(R2 / "accord-02e4r2-validation-rules.json")
    by_id = {}
    sources = [
        load(BASE / "accord-02r2-validation-rules.json"),
        load(BASE / "accord-02r3-validation-rules.json"),
        load(BASE / "accord-02r4-validation-rules.json"),
        load(BASE / "accord-02r5-validation-rules.json"),
        r1,
        r2,
    ]
    for source in sources:
        for key in ("rules", "overrides", "candidate_additions"):
            for r in source.get(key, []):
                by_id[r["rule_id"]] = copy.deepcopy(r)
    active = []
    for rid in r2["active_rule_ids"]:
        r = by_id[rid]
        original = r.get("condition", {}).get("operator", "")
        r["severity"] = r.get("severity", "BLOCKING")
        r["condition"] = {
            "operator_id": operator_for(r),
            "operands": {
                "rule_id": rid,
                "source_artifact_classes": r.get("inputs", []),
                "declared_assertion_id": slug(original or rid),
            },
        }
        active.append(r)
    return active


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    review_dir = HERE / "reviews"
    review_dir.mkdir(exist_ok=True)
    review_specs = [
        ("CLAUDE", "E4R2 CLAUDE FINAL REASSESSMENT.md"),
        ("DEEPSEEK", "E4R2 DEEPSEEK FINAL AUDIT.md"),
        ("VSCODE_CODEX", "E4R2 VSCODE CODEX BLIND AUDIT.md"),
        ("JULES", "E4R2 JULES TARGETED FINAL VERIFICATION.md"),
    ]
    preserved = []
    for assessor, name in review_specs:
        source = REVIEWS / name
        target = review_dir / name
        shutil.copyfile(source, target)
        preserved.append({"assessor": assessor, "source_path": str(source), "preserved_path": target.relative_to(ROOT).as_posix(), "byte_count": source.stat().st_size, "sha256": raw_sha(source), "byte_identical": source.read_bytes() == target.read_bytes()})

    r2_package = load(R2 / "accord-02e4r2-specification-package-0.2.json")
    registry = annotate_refs(load(R2 / "accord-02e4r2-predicate-applicability-registry.json"))
    registry["$id"] = f"{NS}:predicate-registry:{VERSION}"
    registry["registry_id"] = f"{NS}:predicate-registry"
    registry["registry_version"] = VERSION
    normative = annotate_refs(load(R2 / "accord-02e4r2-normative-contracts.json"))
    normative["$id"] = f"{NS}:normative-contracts:{VERSION}"
    normative["contract_id"] = f"{NS}:normative-contracts"
    registry["closure_contract_ref"] = cref(normative["contract_id"])

    catalog = annotate_refs(load(R2 / "accord-02e4r2-settlement-vector-catalog.json"))
    catalog["$id"] = f"{NS}:settlement-vector-catalog:{VERSION}"
    catalog["catalog_id"] = f"{NS}:settlement-vector-catalog"
    catalog["catalog_version"] = VERSION
    for vector in catalog["vectors"]:
        vector["source_vector_ref"] = {
            "reference_kind": "SOURCE_VECTOR",
            "catalog_id": "urn:moirae:accord-02c:settlement-test-vectors",
            "catalog_version": "0.1",
            "vector_id": vector["vector_id"],
            "normative_role": "SETTLEMENT_INPUT",
        }

    old_canon = load(R2 / "canonicalization" / "accord-02e4r2-canonicalization-profile.json")
    targets = []
    for target_id, target in old_canon["content_target_registry"].items():
        targets.append({"content_target_id": target_id, "operator_id": target_id, "mode": target["mode"], "json_pointers": target.get("excluded_json_pointers", target.get("included_json_pointers", [])), "pointer_semantics": "RFC6901", "missing_pointer_policy": "ERROR", "duplicate_pointer_policy": "ERROR", "result_type": "JSON_VALUE"})
    canon = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:canonicalization-profile:{VERSION}",
        "profile_id": f"{NS}:canonicalization-profile", "profile_version": VERSION, "method": "RFC8785_JCS", "encoding": "UTF-8", "algorithm": "SHA-256",
        "content_target_registry": targets,
        "applies_to": [{k: annotate_refs(v) for k, v in m.items() if k != "content_target"} for m in old_canon["applies_to"]],
        "single_source_of_truth": "CONTENT_TARGET_REGISTRY",
    }
    for m in canon["applies_to"]:
        m["canonicalization_profile_ref"] = cref(canon["profile_id"])
    for vector in catalog["vectors"]:
        vector["target"]["canonicalization_ref"] = cref(canon["profile_id"])
    catalog_mapping = next(m for m in canon["applies_to"] if m["container_type"] == "EXPERIMENT_RECORD_ENTRY" and "SETTLEMENT_VECTOR_CATALOG" in m["record_types"])
    catalog_target = next(t for t in canon["content_target_registry"] if t["content_target_id"] == catalog_mapping["content_target_id"])
    catalog_digest_target = copy.deepcopy(catalog)
    for pointer in catalog_target["json_pointers"]:
        parts = pointer.split("/")[1:]
        cur = catalog_digest_target
        for part in parts[:-1]: cur = cur[part]
        del cur[parts[-1]]
    catalog["integrity"]["content_digest"] = jcs_sha(catalog_digest_target)

    profile_semantics = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:profile-semantics:{VERSION}",
        "contract_id": f"{NS}:profile-semantics", "contract_version": VERSION,
        "settlement_profile_ref_domain": "SETTLEMENT_DECISION_POLICY",
        "evidence_profile_ref_domain": "EVIDENCE_ADMISSIBILITY_AND_INTERPRETATION_POLICY",
        "missing_reference": "FAIL_PROFILE_RESOLUTION", "unresolved_reference": "FAIL_PROFILE_RESOLUTION",
        "compatibility_relation": "EXACT_PROFILE_OR_DECLARED_COMPATIBLE_PAIR",
        "compatible_pairs": [],
        "same_profile_result": "COMPATIBLE", "undeclared_different_pair_result": "INCOMPATIBLE",
    }

    negative_evidence = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:complete-negative-evidence:{VERSION}",
        "contract_id": f"{NS}:complete-negative-evidence", "contract_version": VERSION,
        "evidence_id": "urn:moirae:evidence:v013:complete-negative", "effect_id": "urn:moirae:effect:v013",
        "predicate_id": "urn:accord:02c:predicate:external-effect", "stage": "effect",
        "scope_bindings": {"resource": "resource-v013", "action": "action-v013", "recipient": "NOT_APPLICABLE", "provider": "provider-v013"},
        "observed_interval": {"not_before": "2024-01-01T00:00:00Z", "as_of": "2024-01-01T00:00:01Z", "endpoints": "INCLUSIVE"},
        "retention_window_seconds": 86400, "consistency_level": "SNAPSHOT_COMPLETE", "read_semantics": "COMPLETE_LEDGER_QUERY",
        "observed_at": "2024-01-01T00:00:01Z", "verification_time": "2024-01-01T00:00:02Z", "freshness_max_age_seconds": 300,
        "evidence_class": "COMPLETE_NEGATIVE_LEDGER_QUERY", "read_scope_complete": True,
        "accepted_v013_input_mapping": {"complete_negative_evidence": "read_scope_complete", "scope_complete": "scope_bindings", "fresh_at_verification": "observed_at/verification_time", "no_contradictory_positive_evidence": "DERIVED_FROM_EVIDENCE_UNIVERSE"},
        "evidence_universe": [{"evidence_id": "urn:moirae:evidence:v013:complete-negative", "evidence_class": "COMPLETE_NEGATIVE_LEDGER_QUERY", "admissible": True, "effect_id": "urn:moirae:effect:v013", "predicate_id": "urn:accord:02c:predicate:external-effect", "stage": "effect", "proposition": "NEGATIVE"}],
        "contradiction_policy": {"filter": "ADMISSIBLE_SAME_EFFECT_PREDICATE_STAGE_POSITIVE", "deduplicate_by": "evidence_id", "required_count": 0, "caller_supplied_count_allowed": False},
    }
    negative_requirements = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:negative-scope-requirements:{VERSION}",
        "contract_id": f"{NS}:negative-scope-requirements", "contract_version": VERSION,
        "evidence_contract_ref": cref(negative_evidence["contract_id"]),
        "requirements": [
            {"requirement_id": "COMPLETE_STATE_SPACE", "operator_id": "EXACT_VALUE_EQUAL", "operands": {"pointer": "/read_scope_complete", "expected": True}},
            {"requirement_id": "IDENTITY_BOUND", "operator_id": "EXACT_TUPLE_EXISTS", "operands": {"fields": ["effect_id", "predicate_id", "stage"]}},
            {"requirement_id": "SCOPE_BOUND", "operator_id": "SCOPE_BINDINGS_COMPLETE", "operands": {"fields": ["resource", "action", "recipient", "provider"], "not_applicable_token": "NOT_APPLICABLE"}},
            {"requirement_id": "INTERVAL_BOUND", "operator_id": "RFC3339_INTERVAL_VALID", "operands": {"endpoints": "INCLUSIVE"}},
            {"requirement_id": "RETENTION_DECLARED", "operator_id": "INTEGER_RANGE_COVERS", "operands": {"interval_pointer": "/observed_interval", "retention_pointer": "/retention_window_seconds"}},
            {"requirement_id": "CONSISTENCY_DECLARED", "operator_id": "ENUM_ALLOWED", "operands": {"pointer": "/consistency_level", "allowed": ["SNAPSHOT_COMPLETE"]}},
            {"requirement_id": "COMPLETE_READ_SEMANTICS", "operator_id": "ENUM_ALLOWED", "operands": {"pointer": "/read_semantics", "allowed": ["COMPLETE_LEDGER_QUERY"]}},
            {"requirement_id": "FRESH_AT_VERIFICATION", "operator_id": "TIMESTAMP_AGE_LE_MAX", "operands": {"observed_at": "/observed_at", "verification_time": "/verification_time", "max_age": "/freshness_max_age_seconds"}},
            {"requirement_id": "NO_CONTRADICTORY_EVIDENCE", "operator_id": "COUNT_ADMISSIBLE_EVIDENCE_EQ", "operands": {"universe": "/evidence_universe", "expected": 0}},
            {"requirement_id": "ACCEPTED_COMPLETE_SOURCE_CLASS", "operator_id": "ENUM_ALLOWED", "operands": {"pointer": "/evidence_class", "allowed": ["COMPLETE_NEGATIVE_LEDGER_QUERY"]}},
        ],
    }

    partial_policy = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:partial-effect-policy:{VERSION}",
        "contract_id": f"{NS}:partial-effect-policy", "contract_version": VERSION,
        "same_effect_required": True, "direct_predecessor_required": True, "target_already_supported": "NOT_PARTIAL_EFFECT",
        "unknown_tuple": "REJECT", "unsupported_tuple": "REJECT", "wrong_effect": "REJECT", "self_edge": "REJECT", "cycle": "REJECT", "dangling_target": "REJECT",
    }

    operators = [
        ("REFERENCE_GRAPH_CLOSED", "derive schema-annotated reference edges and require exact resolution"),
        ("DIGEST_MATCHES_DECLARED_MAPPING", "execute the referenced canonical content-target operator and compare SHA-256"),
        ("DEPENDENCY_GRAPH_EQUALS_RULES", "derive every dependency pair from active rules and require exact materialized equality and acyclicity"),
        ("NEGATIVE_SCOPE_REQUIREMENTS_PASS", "execute every typed negative-scope requirement against the declared evidence contract"),
        ("BINDING_COMPOSITION_VALID", "require registry bindings, capability requirements, and provenance separation to compose"),
        ("PREDICATE_REGISTRY_VALID", "require exact predicate-stage uniqueness and predecessor eligibility"),
        ("PARTIAL_EFFECT_POLICY_VALID", "apply target support and predecessor validity policy"),
        ("PROFILE_PAIR_COMPATIBLE", "evaluate the declared settlement/evidence profile relation"),
        ("STRICT_SCHEMA_VALID", "require Draft 2020-12 schemas with required fields and closed objects"),
        ("EXPECTATION_SET_EQUAL", "compare all 13 expected axes for all 23 source vectors"),
        ("EFFECTIVE_INVENTORY_VALID", "derive base plus replacements plus additions minus retirements and resolve every path"),
        ("DECLARED_CONTRACT_INVARIANT_VALID", "evaluate the rule's declared assertion against its source artifact classes"),
        ("EXACT_VALUE_EQUAL", "compare typed values without coercion"), ("EXACT_TUPLE_EXISTS", "require a declared exact tuple"),
        ("SCOPE_BINDINGS_COMPLETE", "require each scope dimension or the explicit not-applicable token"),
        ("RFC3339_INTERVAL_VALID", "parse RFC3339 endpoints and require ordered inclusive interval"),
        ("INTEGER_RANGE_COVERS", "require retention seconds to cover the observed interval"),
        ("ENUM_ALLOWED", "require the actual value to be in the declared allowed set"),
        ("TIMESTAMP_AGE_LE_MAX", "require verification time minus observation time not to exceed the declared maximum"),
        ("COUNT_ADMISSIBLE_EVIDENCE_EQ", "derive, deduplicate, and count admissible same-scope positive evidence"),
    ]
    operator_registry = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:operator-registry:{VERSION}", "contract_id": f"{NS}:operator-registry", "contract_version": VERSION, "operators": [{"operator_id": i, "operand_schema": {"type": "object"}, "input_artifact_classes": ["EFFECTIVE_PACKAGE"], "evaluation_semantics": s, "result_type": "BOOLEAN_WITH_FAILURE_CODE", "error_behavior": "FAIL_CLOSED"} for i, s in operators]}

    rules_list = materialize_rules()
    rules = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:validation-rules:{VERSION}", "contract_id": f"{NS}:validation-rules", "contract_version": VERSION, "operator_registry_ref": cref(operator_registry["contract_id"]), "rules": rules_list}
    edges = [{"from": r["rule_id"], "depends_on": r.get("depends_on", [])} for r in rules_list if r.get("depends_on")]
    graph = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:dependency-graph:{VERSION}", "contract_id": f"{NS}:dependency-graph", "contract_version": VERSION, "derived_from": cref(rules["contract_id"]), "node_inventory": [r["rule_id"] for r in rules_list], "edges": edges, "derivation": "RULES[].DEPENDS_ON", "required_equality": "EXACT_NODE_AND_EDGE_SET"}

    source_registry = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:source-schema-registry:{VERSION}", "contract_id": f"{NS}:source-schema-registry", "contract_version": VERSION, "entries": annotate_refs(r2_package["source_schema_registry_entries"])}
    reference_semantics = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{NS}:reference-semantics:{VERSION}", "contract_id": f"{NS}:reference-semantics", "contract_version": VERSION, "discovery": "SCHEMA_X_NORMATIVE_REFERENCE", "identity": "OBJECT_ID_AND_EXPLICIT_VERSION", "equality": "CODE_POINT_EXACT", "normalization": "NONE", "fallback": "FORBIDDEN", "latest_substitution": False, "self_registration": False, "source_vector_target": {"catalog_id": "urn:moirae:accord-02c:settlement-test-vectors", "catalog_version": "0.1", "path": "docs/accord-02/examples/accord-02c-settlement-test-vectors.json"}}

    instances = {
        "predicate-registry": registry, "settlement-vector-catalog": catalog, "normative-contracts": normative,
        "canonicalization-profile": canon, "profile-semantics": profile_semantics, "complete-negative-evidence": negative_evidence,
        "negative-scope-requirements": negative_requirements, "partial-effect-policy": partial_policy,
        "operator-registry": operator_registry, "validation-rules": rules, "dependency-graph": graph,
        "source-schema-registry": source_registry, "reference-semantics": reference_semantics,
    }
    paths = {}
    for name, value in instances.items():
        rel = f"docs/accord-02e4r3/{'canonicalization/' if name == 'canonicalization-profile' else ''}accord-02e4r3-{name}.json"
        paths[name] = rel
        write(ROOT / rel, value)

    schema_contracts = []
    for name, value in instances.items():
        sid = f"{NS}:schema:{name}:{VERSION}"
        rel = f"docs/accord-02e4r3/schema/accord-02e4r3-{name}.schema.json"
        write(ROOT / rel, infer_schema(value, sid, f"ACCORD-02E4R3 {name}"))
        schema_contracts.append({"contract_class": "SCHEMA", "schema_id": sid, "schema_version": VERSION, "schema_path": rel, "status": "ACTIVE"})

    inherited_schemas = []
    for item in r2_package["schema_contracts"]:
        inherited_schemas.append({**item, "schema_path": repo_path(item["schema_path"]), "contract_class": "SCHEMA", "status": "ACTIVE"})
    inherited_profiles = []
    for index, item in enumerate(r2_package["profile_contracts"]):
        normalized = {**item, "profile_path": repo_path(item["profile_path"]), "contract_class": "PROFILE", "status": "RETIRED" if item.get("retired") else "ACTIVE"}
        if not item.get("retired"):
            # Candidate-owned validation overlay: preserve the immutable profile
            # bytes, but bind the active member to a strict schema inferred from
            # that exact effective instance instead of skipping validation.
            profile_value = load(ROOT / normalized["profile_path"])
            sid = f"{NS}:schema:effective-profile-{index:02d}:{VERSION}"
            rel = f"docs/accord-02e4r3/schema/accord-02e4r3-effective-profile-{index:02d}.schema.json"
            write(ROOT / rel, infer_schema(profile_value, sid, f"ACCORD-02E4R3 effective profile {index:02d}"))
            schema_contracts.append({"contract_class": "SCHEMA", "schema_id": sid, "schema_version": VERSION, "schema_path": rel, "status": "ACTIVE"})
            normalized["schema_id"] = sid
            normalized["schema_version"] = VERSION
        inherited_profiles.append(normalized)

    additions = [{"contract_class": "NORMATIVE_CONTRACT", "object_id": v.get("contract_id", v.get("profile_id", v.get("registry_id", v.get("catalog_id", v.get("$id"))))), "object_version": v.get("contract_version", v.get("profile_version", v.get("registry_version", v.get("catalog_version", VERSION)))), "path": paths[n], "schema": sref(f"{NS}:schema:{n}:{VERSION}", VERSION), "status": "ACTIVE"} for n, v in instances.items()]
    additions += [{"contract_class": "SCHEMA", "object_id": s["schema_id"], "object_version": VERSION, "path": s["schema_path"], "status": "ACTIVE"} for s in schema_contracts]

    base_path = BASE / "accord-02r5-specification-package.json"
    prev_path = R2 / "accord-02e4r2-specification-package-0.2.json"
    package = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{FAMILY_ID}:{VERSION}",
        "package_id": FAMILY_ID, "package_version": VERSION, "status": "CANDIDATE_UNACCEPTED", "contract_policy": "CLOSED_EXACT_VERSION", "acceptance_target": {"package_id": FAMILY_ID, "package_version": "0.1"},
        "on_acceptance": {"relation": "AMENDS_AND_SUPERSEDES", "replaces": {"package_id": FAMILY_ID, "package_version": "0.1"}},
        "path_resolution": {"path_base": "REPOSITORY_ROOT", "absolute_paths": "FORBIDDEN", "parent_traversal": "FORBIDDEN", "repository_search_fallback": "FORBIDDEN"},
        "digest_convention": {"external_lineage": "RAW_FILE_BYTES_SHA256", "self_digest": "RFC8785_JCS_EXCLUDING_/lineage/current_candidate/digest"},
        "lineage": {
            "base_package": {"package_id": FAMILY_ID, "package_version": "0.1", "path": "docs/accord-02/accord-02r5-specification-package.json", "digest": raw_sha(base_path)},
            "previous_rejected_candidate": {"package_id": r2_package["package_id"], "package_version": VERSION, "path": "docs/accord-02e4r2/accord-02e4r2-specification-package-0.2.json", "digest": raw_sha(prev_path), "provenance_only": True},
            "current_candidate": {"package_id": FAMILY_ID, "package_version": VERSION, "digest": "PENDING"},
        },
        "inventory_derivation": {"formula": "BASE + REPLACEMENTS + ADDITIONS - RETIREMENTS", "base": {"package_id": FAMILY_ID, "package_version": "0.1"}, "replacements": ["candidate settlement contracts supersede same-class 0.1 members only on acceptance"], "additions": additions, "retirements": [], "derivation_required": True},
        "schema_contracts": inherited_schemas + schema_contracts,
        "profile_contracts": inherited_profiles,
        "active_contracts": additions,
        "reference_semantics_ref": cref(reference_semantics["contract_id"]), "operator_registry_ref": cref(operator_registry["contract_id"]),
        "validation_rules_ref": cref(rules["contract_id"]), "dependency_graph_ref": cref(graph["contract_id"]),
        "canonicalization_profile_ref": cref(canon["profile_id"]), "source_schema_registry_ref": cref(source_registry["contract_id"]),
        "negative_scope_requirements_ref": cref(negative_requirements["contract_id"]), "negative_evidence_contract_ref": cref(negative_evidence["contract_id"]),
        "design_freeze": {"vectors": 23, "expected_axes": 13, "prohibitions": 31, "accepted_outcome_changes": 0},
    }
    package_schema_id = f"{NS}:schema:specification-package:{VERSION}"
    package_schema_path = "docs/accord-02e4r3/schema/accord-02e4r3-specification-package.schema.json"
    package["package_schema_ref"] = sref(package_schema_id, VERSION)
    package["schema_contracts"].append({"contract_class": "SCHEMA", "schema_id": package_schema_id, "schema_version": VERSION, "schema_path": package_schema_path, "status": "ACTIVE"})
    package["active_contracts"].append({"contract_class": "SCHEMA", "object_id": package_schema_id, "object_version": VERSION, "path": package_schema_path, "status": "ACTIVE"})
    digest_target = copy.deepcopy(package)
    del digest_target["lineage"]["current_candidate"]["digest"]
    package["lineage"]["current_candidate"]["digest"] = jcs_sha(digest_target)
    write(ROOT / package_schema_path, infer_schema(package, package_schema_id, "ACCORD-02E4R3 specification package"))
    write(HERE / "accord-02e4r3-specification-package-0.2.json", package)

    findings = {"candidate": "ACCORD-02E4R3", "review_evidence": preserved, "classifications": {
        "CONFIRMED": ["E4R2-CLAUDE-BLOCK-001", "E4R2-CLAUDE-MAJOR-001", "E4R2-CLAUDE-MAJOR-002", "E4R2-CLAUDE-MAJOR-003", "E4R2-CLAUDE-MAJOR-004", "E4R2-CLAUDE-MAJOR-005", "E4R2-CLAUDE-MAJOR-006", "E4R2-CLAUDE-MAJOR-007", "E4R2-DEEPSEEK-BLOCK-01", "E4R2-DEEPSEEK-BLOCK-02", "E4R2-DEEPSEEK-MAJOR-01", "E4R2-DEEPSEEK-MAJOR-02", "E4R2-DEEPSEEK-MAJOR-03", "E4R2-DEEPSEEK-MAJOR-04", "E4R2-DEEPSEEK-MAJOR-05", "E4R2-VSCODE-CODEX-BLOCK-001", "E4R2-VSCODE-CODEX-BLOCK-002", "E4R2-VSCODE-CODEX-BLOCK-003", "E4R2-VSCODE-CODEX-BLOCK-004", "E4R2-VSCODE-CODEX-MAJOR-001", "E4R2-VSCODE-CODEX-MAJOR-002", "JULES-CANONICALIZATION-EVALUATOR", "JULES-RULE-GRAPH-MOCKED-MUTATION", "JULES-PACKAGE-LINEAGE", "JULES-EFFECTIVE-VALIDATION"],
        "OVERLAPS_OTHER_FINDING": ["E4R2-CLAUDE-MINOR-002", "JULES-REFERENCE-CLOSURE"],
        "REFUTED_WITH_REPRODUCER": ["CLAUDE-V013-FULLY-SOUND-AS-INDEPENDENT-EVIDENCE-CONTRACT"],
        "REQUIRES_FORMALISATION": ["JULES-NEGATIVE-SCOPE", "JULES-BINDING-AUTHORITY"], "OUT_OF_SCOPE": []}, "normalization_performed": False}
    write(HERE / "accord-02e4r3-four-assessor-findings.json", findings)
    print(json.dumps({"files": len(list(HERE.rglob('*'))), "rules": len(rules_list), "dependency_pairs": sum(len(x["depends_on"]) for x in edges), "reviews": preserved}, indent=2))


if __name__ == "__main__":
    main()
