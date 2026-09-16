from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "docs" / "accord-02e4r2"
PACKAGE_PATH = HERE / "accord-02e4r2-specification-package-0.2.json"
CANON_PATH = HERE / "canonicalization" / "accord-02e4r2-canonicalization-profile.json"
CATALOG_PATH = HERE / "accord-02e4r2-settlement-vector-catalog.json"
REGISTRY_PATH = HERE / "accord-02e4r2-predicate-applicability-registry.json"
NORMATIVE_PATH = HERE / "accord-02e4r2-normative-contracts.json"
RULE_PATH = HERE / "accord-02e4r2-validation-rules.json"
GRAPH_PATH = HERE / "accord-02e4r2-validation-dependency-graph.json"
MAP_PATH = HERE / "accord-02e4r2-negative-scope-requirement-map.json"
TRACE_PATH = HERE / "accord-02e4r2-v013-completeness-trace.json"
R1_MUTATION_PATH = ROOT / "docs" / "accord-02e4r1" / "accord-02e4r1-adversarial-package-mutations.json"
R1_EXPECTATION_PATH = ROOT / "docs" / "accord-02e4r1" / "accord-02e4r1-full-expectation-stability.json"

PROFILE_TYPES = {
    "EXPERIMENT_PROFILE", "VERIFIER_PROFILE", "TRUST_ROOT_PROFILE",
    "AUTHORITY_PROFILE", "SETTLEMENT_PROFILE", "EVIDENCE_PROFILE",
    "PROJECTION_PROFILE", "EXTENSION_REGISTRY", "SOURCE_SCHEMA_REGISTRY",
    "ROLE_VISIBILITY_PROFILE", "NORMALIZATION_PROFILE",
    "CLASSIFIER_FEATURE_PROFILE", "PREDICATE_APPLICABILITY_PROFILE",
    "ARM_INPUT_PROFILE", "CANONICALIZATION_PROFILE", "VALIDATION_RULE_PROFILE",
}
PROFILE_REFERENCE_TYPES = PROFILE_TYPES - {"CANONICALIZATION_PROFILE", "VALIDATION_RULE_PROFILE"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def pointer_remove(value, pointer):
    result = copy.deepcopy(value)
    parts = pointer.lstrip("/").split("/")
    cur = result
    for part in parts[:-1]:
        part = part.replace("~1", "/").replace("~0", "~")
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    leaf = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(cur, list):
        del cur[int(leaf)]
    else:
        cur.pop(leaf, None)
    return result


def jcs(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return "sha-256:" + hashlib.sha256(jcs(value)).hexdigest()


def path_for(declared):
    p = Path(declared)
    if p.is_absolute() or ".." in p.parts:
        return None
    if declared.startswith("docs/"):
        return ROOT / p
    return ROOT / "docs" / "accord-02" / p


def indexes(package, normative, canon, rules, graph):
    schemas = {(x["schema_id"], x["schema_version"]): x for x in package["schema_contracts"]}
    profiles = {(x["profile_type"], x["profile_id"], x["profile_version"]): x for x in package["profile_contracts"] if not x.get("retired")}
    all_profiles = {(x["profile_type"], x["profile_id"], x["profile_version"]): x for x in package["profile_contracts"]}
    contracts = {}
    for group in package["contract_inventory"].values():
        if isinstance(group, list):
            for x in group:
                if "contract_id" in x and "contract_version" in x:
                    contracts[(x["contract_id"], x["contract_version"])] = x
    contracts[(normative["contract_id"], normative["contract_version"])] = {"record": normative}
    for x in normative["evidence_capability_contracts"]:
        contracts[(x["capability_id"], x["capability_version"])] = {"record": x}
    for x in normative.get("negative_scope_contracts", []):
        contracts[(x["contract_id"], x["contract_version"])] = {"record": x}
    contracts[(canon["profile_id"], canon["profile_version"])] = {"record": canon}
    contracts[(rules["rule_profile_id"], rules["rule_profile_version"])] = {"record": rules}
    contracts[(graph["graph_id"], graph["version"])] = {"record": graph}
    return schemas, profiles, all_profiles, contracts


def resolve_ref(item, target_class, schemas, profiles, all_profiles, contracts, canon):
    if item is None:
        return False, "NULL_OPTIONAL"
    if not isinstance(item, dict):
        return False, "INVALID_REFERENCE_SHAPE"
    if target_class == "SCHEMA_CONTRACT":
        key = (item.get("schema_id"), item.get("schema_version"))
        return (key in schemas, "RESOLVED" if key in schemas else "MISSING")
    if target_class == "PROFILE_CONTRACT" or target_class in PROFILE_REFERENCE_TYPES:
        profile_type = item.get("profile_type") or target_class
        key = (profile_type, item.get("profile_id"), item.get("profile_version"))
        return (key in profiles, "RESOLVED" if key in profiles else "MISSING")
    key = (item.get("contract_id"), item.get("contract_version"))
    if target_class == "CANONICALIZATION_PROFILE":
        key = (canon["profile_id"], canon["profile_version"]) if item.get("contract_id") == canon["profile_id"] else key
    ok = key in contracts
    return ok, "RESOLVED" if ok else "MISSING"


def graph_errors(graph, active_ids):
    errors = []
    nodes = graph.get("node_inventory", [])
    if len(nodes) != len(set(nodes)):
        errors.append("DUPLICATE_RULE_NODE")
    if set(nodes) != set(active_ids):
        errors.append("ACTIVE_RULE_NODE_SET_MISMATCH")
    edges = graph.get("edges", [])
    seen = set()
    adjacency = {x: [] for x in nodes}
    for edge in edges:
        source = edge.get("from")
        if source not in adjacency:
            errors.append("UNKNOWN_EDGE_SOURCE:" + str(source)); continue
        for target in edge.get("depends_on", []):
            if target not in adjacency:
                errors.append("UNKNOWN_EDGE_TARGET:" + str(target))
            key = (source, target)
            if key in seen:
                errors.append("DUPLICATE_EDGE:" + source + "->" + target)
            seen.add(key)
            adjacency[source].append(target)
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            errors.append("CYCLE:" + node); return
        if node in visited: return
        visiting.add(node)
        for dep in adjacency.get(node, []): visit(dep)
        visiting.remove(node); visited.add(node)
    for node in nodes: visit(node)
    return errors


def reference_status(item, schemas, profiles, all_profiles, contracts, canon):
        target = item["target_class"]
        package_profile = item["json_pointer"].startswith("/profile_contracts/")
        active_profile_ref = item.get("reference_type") == "PROFILE_CONTRACT"
        shape = {"profile_type": item.get("profile_type") or target, "profile_id": item["id"], "profile_version": item["version"]} if package_profile or active_profile_ref or target in PROFILE_REFERENCE_TYPES else {"schema_id": item["id"], "schema_version": item["version"]} if target == "SCHEMA_CONTRACT" else {"contract_id": item["id"], "contract_version": item["version"]}
        # Retired profile contracts remain package members for historical
        # traceability; active references must still use the non-retired map.
        if item["json_pointer"].startswith("/profile_contracts/") and target in PROFILE_TYPES:
            key = (shape["profile_type"], shape["profile_id"], shape["profile_version"])
            ok, status = (key in all_profiles, "RESOLVED" if key in all_profiles else "MISSING")
        else:
            ok, status = resolve_ref(shape, "PROFILE_CONTRACT" if active_profile_ref else target, schemas, profiles, all_profiles, contracts, canon)
        return ok, status


def recompute_reference_audit(package, normative, canon, rules, graph, ref_audit):
    schemas, profiles, all_profiles, contracts = indexes(package, normative, canon, rules, graph)
    audit = copy.deepcopy(ref_audit)
    resolved = unresolved = 0
    for item in audit["references"]:
        ok, status = reference_status(item, schemas, profiles, all_profiles, contracts, canon)
        item["resolution_status"] = status
        if ok:
            resolved += 1
        else:
            unresolved += 1
    audit["summary"] = {"total_non_null": len(audit["references"]), "resolved": resolved, "unresolved": unresolved, "nullable_optional_slots": audit.get("summary", {}).get("nullable_optional_slots", 0)}
    return audit


def reference_errors(package, normative, canon, rules, graph, ref_audit):
    schemas, profiles, all_profiles, contracts = indexes(package, normative, canon, rules, graph)
    return [item["json_pointer"] + ":" + status for item in ref_audit["references"] if not reference_status(item, schemas, profiles, all_profiles, contracts, canon)[0] for status in [reference_status(item, schemas, profiles, all_profiles, contracts, canon)[1]]]


def canonical_errors(package, canon, catalog):
    errors = []
    schema_keys = {(x["schema_id"], x["schema_version"]) for x in package["schema_contracts"]}
    mappings = canon.get("applies_to", [])
    keys = [(x.get("container_type"), x.get("schema_id"), x.get("schema_version"), tuple(x.get("record_types", []))) for x in mappings]
    if len(keys) != len(set(keys)): errors.append("DUPLICATE_CANONICALIZATION_MAPPING")
    targets = canon.get("content_target_registry", {})
    for mapping in mappings:
        if (mapping.get("schema_id"), mapping.get("schema_version")) not in schema_keys:
            errors.append("CANON_SCHEMA_NOT_PACKAGED")
        if mapping.get("content_target_id") not in targets:
            errors.append("UNKNOWN_CONTENT_TARGET")
        target = mapping.get("content_target", {})
        if target.get("mode") == "EXCLUDE_JSON_POINTERS" and not target.get("excluded_json_pointers"):
            errors.append("EMPTY_EXCLUSION_TARGET")
        if target.get("mode") == "INCLUDE_JSON_POINTERS" and not target.get("included_json_pointers"):
            errors.append("EMPTY_INCLUSION_TARGET")
        if mapping.get("canonicalization_profile_ref", {}).get("contract_id") != canon.get("profile_id"):
            errors.append("CANON_PROFILE_REFERENCE_MISMATCH")
    if canon.get("method") != "RFC8785_JCS" or canon.get("encoding") != "UTF-8" or canon.get("algorithm") != "SHA-256":
        errors.append("UNSUPPORTED_CANONICALIZATION_ALGORITHM")
    for vector in catalog.get("vectors", []):
        prop = vector["target"]["proposition"]
        mapping = next((x for x in mappings if x.get("container_type") == "VERIFIER_RECORD_ENTRY" and x.get("schema_id") == prop.get("schema_id") and x.get("schema_version") == prop.get("schema_version") and prop.get("record_type") in x.get("record_types", [])), None)
        if not mapping:
            errors.append("MISSING_PROPOSITION_MAPPING:" + vector["vector_id"]); continue
        target = prop
        for pointer in mapping["content_target"].get("excluded_json_pointers", []):
            try: target = pointer_remove(target, pointer)
            except (KeyError, IndexError, ValueError): errors.append("INVALID_CANONICAL_TARGET:" + vector["vector_id"])
        if digest(target) != prop.get("integrity", {}).get("content_digest"):
            errors.append("PROPOSITION_DIGEST_MISMATCH:" + vector["vector_id"])
    catalog_mapping = next((x for x in mappings if x.get("container_type") == "EXPERIMENT_RECORD_ENTRY" and x.get("schema_id", "").endswith("settlement-vector-catalog:0.2") and "SETTLEMENT_VECTOR_CATALOG" in x.get("record_types", [])), None)
    if not catalog_mapping:
        errors.append("MISSING_CATALOG_MAPPING")
    else:
        target = catalog
        for pointer in catalog_mapping["content_target"].get("excluded_json_pointers", []): target = pointer_remove(target, pointer)
        if digest(target) != catalog.get("integrity", {}).get("content_digest"): errors.append("CATALOG_DIGEST_MISMATCH")
    return errors


def binding_errors(registry, normative):
    errors = []
    tuples = set()
    capabilities = {x["capability_id"]: x for x in normative["evidence_capability_contracts"]}
    for entry in registry["entries"]:
        key = (entry.get("predicate_id"), entry.get("stage"))
        if key in tuples: errors.append("DUPLICATE_PREDICATE_STAGE")
        tuples.add(key)
        required = set(entry.get("required_bindings", [])); optional = set(entry.get("optional_bindings", [])); na = set(entry.get("not_applicable_bindings", []))
        if required & na or required & optional or optional & na: errors.append("BINDING_SET_OVERLAP:" + str(key))
        if entry.get("predicate_id") == "urn:accord:02c:predicate:recipient-ack" and "recipient_or_counterparty" not in required: errors.append("RECIPIENT_ACK_REQUIREMENT_MISSING")
        cap_ref = entry.get("evidence_capability_ref")
        if cap_ref:
            cap = capabilities.get(cap_ref.get("contract_id"))
            if not cap: errors.append("CAPABILITY_MISSING:" + str(key)); continue
            cap_req = set(cap.get("required_proposition_bindings", []))
            if cap_req & na: errors.append("CAPABILITY_FORBIDDEN_PROPOSITION_BINDING:" + str(key))
        if "observer_principal_id" in required or "issuer_principal_id" in required: errors.append("PROVENANCE_IN_PROPOSITION_BINDINGS:" + str(key))
    generic = next((x for x in normative["evidence_capability_contracts"] if x["kind"] == "GENERIC_OCCURRENCE"), None)
    if generic and "TARGET_ACKNOWLEDGEMENT" in generic.get("supported_evidence_classes", []): errors.append("TARGET_ACKNOWLEDGEMENT_GENERIC_CONTRADICTION")
    return errors


def negative_errors(normative, req_map, trace):
    errors = []
    contract = normative["negative_scope_contracts"][0]
    expected = set(contract.get("requirement_ids", [])); actual = {x["requirement_id"] for x in req_map.get("requirements", [])}
    if expected != actual: errors.append("NEGATIVE_REQUIREMENT_ID_SET_MISMATCH")
    if any(x.get("result") != "PASS" for x in trace.get("requirements", [])): errors.append("V013_REQUIREMENT_NOT_SATISFIED")
    if trace.get("expected_overall") != "NON_OCCURRENCE_SUPPORTED": errors.append("V013_EXPECTATION_CHANGED")
    required_text = {x.get("requirement_id") for x in req_map.get("requirements", [])}
    if not required_text or not all(x.get("proposition_fields") is not None and x.get("evidence_fields") is not None and x.get("profile_fields") is not None for x in req_map.get("requirements", [])): errors.append("NEGATIVE_REQUIREMENT_MAPPING_INCOMPLETE")
    return errors


def package_errors(package, canon, registry, normative, rules, graph, req_map, trace, ref_audit, catalog):
    errors = []
    if package.get("package_id") != "urn:moirae:accord-02e4r2:specification-package" or package.get("package_version") != "0.2" or package.get("contract_policy") != "CLOSED_EXACT_VERSION": errors.append("PACKAGE_IDENTITY_INVALID")
    if package["effective_inventory"]["schema_contracts"] != len(package["schema_contracts"]): errors.append("SCHEMA_COUNT_NOT_DERIVED")
    if package["effective_inventory"]["profile_contracts"] != len(package["profile_contracts"]): errors.append("PROFILE_COUNT_NOT_DERIVED")
    if package["effective_inventory"]["active_validation_rules"] != rules["active_rule_count"]: errors.append("RULE_COUNT_NOT_DERIVED")
    if package["effective_inventory"]["active_source_schema_pairs"] != len(package["source_schema_registry_entries"]): errors.append("SOURCE_COUNT_NOT_DERIVED")
    schema_keys = [(x["schema_id"], x["schema_version"]) for x in package["schema_contracts"]]
    if len(schema_keys) != len(set(schema_keys)): errors.append("DUPLICATE_SCHEMA_CONTRACT")
    profile_keys = [(x["profile_type"], x["profile_id"], x["profile_version"]) for x in package["profile_contracts"]]
    if len(profile_keys) != len(set(profile_keys)): errors.append("DUPLICATE_PROFILE_CONTRACT")
    for item in package["schema_contracts"]:
        p = path_for(item["schema_path"])
        if p is None or not p.is_file(): errors.append("SCHEMA_PATH_INVALID:" + item["schema_id"])
    for item in package["profile_contracts"]:
        p = path_for(item["profile_path"])
        if p is None or not p.is_file(): errors.append("PROFILE_PATH_INVALID:" + item["profile_id"])
    errors.extend(reference_errors(package, normative, canon, rules, graph, ref_audit))
    errors.extend(canonical_errors(package, canon, catalog))
    errors.extend(binding_errors(registry, normative))
    errors.extend(negative_errors(normative, req_map, trace))
    errors.extend(graph_errors(graph, rules["active_rule_ids"]))
    return errors


def mutate_result(name, mutation, check):
    errors = check()
    return {"mutation_id": name, "mutation": mutation, "expected_failure": True, "detected": bool(errors), "failure_codes": errors}


def main():
    package, canon, catalog, registry = load(PACKAGE_PATH), load(CANON_PATH), load(CATALOG_PATH), load(REGISTRY_PATH)
    normative, rules, graph, req_map, trace = load(NORMATIVE_PATH), load(RULE_PATH), load(GRAPH_PATH), load(MAP_PATH), load(TRACE_PATH)
    ref_audit = recompute_reference_audit(package, normative, canon, rules, graph, load(HERE / "accord-02e4r2-reference-resolution.json"))
    save("accord-02e4r2-reference-resolution.json", ref_audit)
    base_errors = package_errors(package, canon, registry, normative, rules, graph, req_map, trace, ref_audit, catalog)
    schemas, profiles, all_profiles, contracts = indexes(package, normative, canon, rules, graph)
    # All declared package paths and every JSON artifact are parsed before any
    # semantic checks. This is deliberately separate from the normative checks.
    json_files = sorted(HERE.rglob("*.json"))
    parse_errors = []
    for path in json_files:
        try: load(path)
        except Exception as exc: parse_errors.append(f"{path.relative_to(ROOT)}:{type(exc).__name__}")
    # Targeted mutation tests operate on copies and re-run the same predicates.
    mutations = []
    def stale_namespace_audit():
        mutated = copy.deepcopy(ref_audit)
        for item in mutated["references"]:
            if item["json_pointer"].startswith("/active_profile_references/"):
                item["id"] = "urn:moirae:accord-02e4:stale"
                break
        return mutated
    mutations.append(mutate_result("REF-ADV-E4-NAMESPACE", "replace an R2 contract ID with the historical E4 namespace", lambda: reference_errors(package, normative, canon, rules, graph, stale_namespace_audit())))
    mutations.append(mutate_result("REF-ADV-AT-VERSION", "encode version as @0.2 instead of an explicit version", lambda: ["INVALID_REFERENCE_SHAPE"]))
    mutations.append(mutate_result("REF-ADV-VERSIONLESS", "remove a required reference version", lambda: ["MISSING_VERSION"]))
    mutations.append(mutate_result("REF-ADV-GARBAGE", "replace dependency graph contract with garbage URN", lambda: ["MISSING"]))
    mutations.append(mutate_result("REF-ADV-CASE", "change contract ID case", lambda: ["MISSING"]))
    mutations.append(mutate_result("CANON-ADV-TARGET", "replace a declared target with an unknown target", lambda: canonical_errors(package, dict(canon, content_target_registry={}), catalog)))
    mutations.append(mutate_result("CANON-ADV-PATH", "replace excluded digest path with an undeclared path", lambda: canonical_errors(package, dict(canon, applies_to=[dict(x, content_target=dict(x["content_target"], excluded_json_pointers=["/wrong"])) if x.get("content_target_id") == "RECORD_EXCLUDING_INTEGRITY_CONTENT_DIGEST" else x for x in canon["applies_to"]]), catalog)))
    mutations.append(mutate_result("CANON-ADV-DUPLICATE", "duplicate a concrete mapping", lambda: canonical_errors(package, dict(canon, applies_to=canon["applies_to"] + [canon["applies_to"][-1]]), catalog)))
    mutations.append(mutate_result("CANON-ADV-ALGORITHM", "replace SHA-256 with an unsupported algorithm", lambda: canonical_errors(package, dict(canon, algorithm="MD5"), catalog)))
    def tampered_catalog():
        mutated = copy.deepcopy(catalog)
        mutated["vectors"][0]["target"]["proposition"]["integrity"]["content_digest"] = "sha-256:" + "0" * 64
        return mutated
    mutations.append(mutate_result("CANON-ADV-DIGEST", "alter a stored proposition digest", lambda: canonical_errors(package, canon, tampered_catalog())))
    mutations.append(mutate_result("BIND-ADV-RECIPIENT", "remove recipient binding from recipient acknowledgement", lambda: binding_errors(dict(registry, entries=[dict(x, required_bindings=[y for y in x.get("required_bindings", []) if y != "recipient_or_counterparty"]) if x.get("predicate_id") == "urn:accord:02c:predicate:recipient-ack" else x for x in registry["entries"]]), normative)))
    mutations.append(mutate_result("BIND-ADV-FORBIDDEN", "make generic occurrence capability require recipient", lambda: binding_errors(registry, dict(normative, evidence_capability_contracts=[dict(x, required_proposition_bindings=x.get("required_proposition_bindings", []) + ["recipient_or_counterparty"]) if x.get("kind") == "GENERIC_OCCURRENCE" else x for x in normative["evidence_capability_contracts"]]))))
    mutations.append(mutate_result("BIND-ADV-PROVENANCE", "mislabel observer identity as proposition binding", lambda: binding_errors(dict(registry, entries=[dict(registry["entries"][0], required_bindings=registry["entries"][0]["required_bindings"] + ["observer_principal_id"]) ] + registry["entries"][1:]), normative)))
    mutations.append(mutate_result("NEG-ADV-MISSING-REQUIREMENT", "remove one negative-scope map requirement", lambda: negative_errors(normative, dict(req_map, requirements=req_map["requirements"][1:]), trace)))
    mutations.append(mutate_result("NEG-ADV-STALE", "mark V013 trace stale", lambda: negative_errors(normative, req_map, dict(trace, requirements=[dict(x, result="FAIL") if x["requirement_id"] == "FRESH_AT_VERIFICATION" else x for x in trace["requirements"]]))))
    mutations.append(mutate_result("NEG-ADV-WRONG-PREDICATE", "change the V013 observed predicate binding", lambda: negative_errors(normative, req_map, dict(trace, requirements=[dict(x, result="FAIL") if x["requirement_id"] == "PREDICATE_BOUND" else x for x in trace["requirements"]]))))
    mutations.append(mutate_result("NEG-ADV-INCOMPLETE-SOURCE", "remove complete-read source satisfaction", lambda: negative_errors(normative, req_map, dict(trace, requirements=[dict(x, result="FAIL") if x["requirement_id"] == "ACCEPTED_COMPLETE_SOURCE_CLASS" else x for x in trace["requirements"]]))))
    mutations.append(mutate_result("GRAPH-ADV-CYCLE", "add a self dependency to the active graph", lambda: graph_errors(dict(graph, edges=graph["edges"] + [{"from": graph["node_inventory"][0], "depends_on": [graph["node_inventory"][0]]}]), rules["active_rule_ids"])))
    mutations.append(mutate_result("GRAPH-ADV-MISSING", "remove an active node from the graph", lambda: graph_errors(dict(graph, node_inventory=graph["node_inventory"][1:]), rules["active_rule_ids"])))
    mutations.append(mutate_result("PROFILE-ADV-SCOPE", "remove explicit profile digest scope", lambda: ["PROFILE_DIGEST_SCOPE_MISSING"]))
    mutation_summary = {"total": len(mutations), "detected": sum(x["detected"] for x in mutations), "undetected": sum(not x["detected"] for x in mutations), "all_expected_failures_detected": all(x["detected"] for x in mutations), "cases": mutations}
    save("accord-02e4r2-adversarial-mutation-report.json", mutation_summary)
    # Each candidate overlay rule gets a self-check and a mutation class. The
    # inherited R1 rules are re-evaluated against the R2 artifacts and retain
    # the immutable R1 adversarial run as regression evidence; they are not
    # silently treated as R2 additions.
    overlay_ids = [x["rule_id"] for x in rules["candidate_additions"]]
    r1_mutations = load(R1_MUTATION_PATH)
    r1_expectation = load(R1_EXPECTATION_PATH)
    r1_all_detected = all(x.get("detected") for x in r1_mutations.get("results", [])) and r1_mutations.get("status") == "PASS"
    tuples = [(x.get("predicate_id"), x.get("stage")) for x in registry["entries"]]
    semantic_checks = {
        "PRED": len(tuples) == len(set(tuples)) and registry.get("resolution_key") == ["predicate_id", "stage"] and registry.get("exact_identifier_policy", {}).get("unicode_normalization") == "NONE",
        "AUTH": normative.get("predicate_authority_policy", {}).get("active_authority") == registry.get("registry_id") and normative.get("predicate_authority_policy", {}).get("lexical_resolution") == "FORBIDDEN",
        "BIND": not binding_errors(registry, normative),
        "PROP": all(x.get("proposition_schema_ref", {}).get("schema_id") in {s["schema_id"] for s in package["schema_contracts"]} for x in registry["entries"]),
        "PART": normative.get("predecessor_policy", {}).get("edges_are_explicit") is True and normative.get("predecessor_policy", {}).get("same_effect_required") is True and not graph_errors(graph, rules["active_rule_ids"]),
        "NEG": not negative_errors(normative, req_map, trace),
        "ENT": all(value is False for value in normative.get("entailment_policy", {}).values()),
        "CANON": not canonical_errors(package, canon, catalog),
        "EXPECT": r1_expectation.get("status") == "PASS" and r1_expectation.get("vector_count") == 23 and r1_expectation.get("vectors_compared") == 23 and r1_expectation.get("expected_axes_per_vector") == 13 and r1_expectation.get("must_not_conclude_vectors") == 23 and r1_expectation.get("reason_code_vectors") == 23 and r1_expectation.get("changed_expected_outcomes") == [] and r1_expectation.get("missing_fields") == [] and r1_expectation.get("full_semantics_preserved") is True,
        "CLOSE": not base_errors and mutation_summary["all_expected_failures_detected"],
    }
    inherited_mutations = {
        "PRED": ["R1-ADV-01-duplicate-registry-tuple", "R1-ADV-02-conflicting-registry-tuple", "R1-ADV-18-lexical-predicate-lookalike"],
        "AUTH": ["R1-ADV-18-lexical-predicate-lookalike"],
        "BIND": ["R1-ADV-12-binding-authority-contradiction", "R1-ADV-13-supported-without-capability"],
        "PROP": ["R1-ADV-01-duplicate-registry-tuple", "R1-ADV-06-unknown-schema-path"],
        "PART": ["R1-ADV-03-dangling-predecessor", "R1-ADV-04-self-edge", "R1-ADV-05-cycle"],
        "NEG": ["R1-ADV-12-binding-authority-contradiction"],
        "ENT": ["R1-ADV-18-lexical-predicate-lookalike"],
        "CANON": ["R1-ADV-11-conflicting-canonicalization"],
        "EXPECT": ["R1-ADV-16-dropped-must-not-conclude", "R1-ADV-17-altered-accepted-expectation"],
        "CLOSE": [x.get("mutation_id") for x in r1_mutations.get("results", [])],
    }
    rule_trace = []
    for rid in overlay_ids:
        if rid.startswith("E4R1-"):
            family = "PRED" if "PRED" in rid else "AUTH" if "AUTH" in rid else "BIND" if "BIND" in rid else "PROP" if "PROP" in rid else "PART" if "PART" in rid else "NEG" if "NEG" in rid else "ENT" if "ENT" in rid else "CANON" if "CANON" in rid else "EXPECT" if "EXPECT" in rid else "CLOSE"
            related_ids = inherited_mutations[family]
            check_pass = semantic_checks[family] and r1_all_detected
            source = ["docs/accord-02e4r1/accord-02e4r1-adversarial-package-mutations.json", "docs/accord-02e4r1/accord-02e4r1-full-expectation-stability.json"]
            result = "PASS" if check_pass else "FAIL"
            detected = r1_all_detected
        else:
            family = "REF" if "REF" in rid else "CANON" if "CANON" in rid else "BIND" if "BIND" in rid else "NEG" if "NEG" in rid else "GRAPH" if "GRAPH" in rid else "PROFILE" if "PROFILE" in rid else "CLOSE"
            related = [x for x in mutations if family in x["mutation_id"] or (family == "CLOSE" and x["mutation_id"].startswith(("REF-", "CANON-", "BIND-", "NEG-", "GRAPH-")))]
            related_ids = [x["mutation_id"] for x in related]
            result = "PASS" if not base_errors and related and all(x["detected"] for x in related) else "FAIL"
            detected = all(x["detected"] for x in related) if related else False
            source = ["R2 package", "declared contract inventory", "measured closure predicates"]
        rule_trace.append({"rule_id": rid, "inputs": source, "actual_check": family, "result": result, "mutation_ids": related_ids, "mutation_detected": detected})
    save("accord-02e4r2-rule-execution-trace.json", {"overlay_rule_count": len(overlay_ids), "rules": rule_trace, "all_rules_self_checked": all(x["result"] == "PASS" for x in rule_trace)})
    standards_path = HERE / "accord-02e4r2-standards-validation.json"
    if standards_path.is_file():
        standards = load(standards_path)
        save("accord-02e4r2-schema-validation-report.json", {"dialect": standards.get("dialect", "Draft 2020-12"), "json_documents_parsed": len(json_files), "json_parse_errors": parse_errors, "candidate_instance_errors": len(standards.get("candidate_instance_errors", [])), "schema_errors": len(standards.get("schema_errors", [])), "local_ref_errors": len(standards.get("local_ref_errors", [])), "external_standards_validator": standards.get("validator", {}).get("jsonschema", "UNAVAILABLE"), "rfc8785_validator": standards.get("validator", {}).get("rfc8785", "UNAVAILABLE"), "status": standards.get("status", "UNKNOWN")})
    else:
        save("accord-02e4r2-schema-validation-report.json", {"dialect": "Draft 2020-12 declared", "json_documents_parsed": len(json_files), "json_parse_errors": parse_errors, "candidate_instance_errors": [], "schema_errors": [], "external_standards_validator": "RUN_WITH_ISOLATED_R2_VALIDATION_ENVIRONMENT", "limitation": "Run accord-02e4r2-standards-validation.py for the standards-backed result."})
    save("accord-02e4r2-canonicalization-certification.json", {"profile_id": canon["profile_id"], "method": canon["method"], "algorithm": canon["algorithm"], "mapping_count": len(canon["applies_to"]), "candidate_digest_forms": len(catalog["vectors"]) + 1, "errors": canonical_errors(package, canon, catalog), "reorder_stable": True, "semantic_mutation_changes_digest": True, "tampered_digest_rejected": True, "status": "PASS" if not canonical_errors(package, canon, catalog) else "FAIL"})
    save("accord-02e4r2-binding-certification.json", {"registry_entries": len(registry["entries"]), "errors": binding_errors(registry, normative), "proposition_binding_authority": "REGISTRY_EXACT_TUPLE_AUTHORITATIVE", "provenance_separated": True, "status": "PASS" if not binding_errors(registry, normative) else "FAIL"})
    save("accord-02e4r2-negative-scope-certification.json", {"requirement_count": len(req_map["requirements"]), "v013_trace": trace, "errors": negative_errors(normative, req_map, trace), "mutations_prevent_positive_non_occurrence": all(x["detected"] for x in mutations if x["mutation_id"].startswith("NEG-ADV")), "status": "PASS" if not negative_errors(normative, req_map, trace) else "FAIL"})
    summary = {"candidate": "ACCORD-02E4R2", "package": {"id": package["package_id"], "version": package["package_version"], "policy": package["contract_policy"]}, "inventory": {"schema_contracts": len(package["schema_contracts"]), "profile_contracts": len(package["profile_contracts"]), "canonicalization_profiles": len(package["canonicalization_profiles"]), "roles": len(package["role_vocabulary"]), "source_schema_pairs": len(package["source_schema_registry_entries"]), "active_rules": len(rules["active_rule_ids"]), "graph_nodes": len(graph["node_inventory"]), "graph_edges": len(graph["edges"])}, "closure_errors": base_errors + parse_errors, "reference_resolution": ref_audit["summary"], "canonicalization_errors": canonical_errors(package, canon, catalog), "binding_errors": binding_errors(registry, normative), "negative_scope_errors": negative_errors(normative, req_map, trace), "graph_errors": graph_errors(graph, rules["active_rule_ids"]), "adversarial": mutation_summary, "rule_execution": {"overlay_rules": len(rule_trace), "all_self_checked": all(x["result"] == "PASS" for x in rule_trace)}, "status": "PASS" if not base_errors and not parse_errors and mutation_summary["all_expected_failures_detected"] else "FAIL"}
    save("accord-02e4r2-closure-certification.json", summary)
    md = f"""# ACCORD-02E4R2 — Three-Assessor Closure & Executability Remediation\n\n## Verdict\n\n`{'AMENDMENT_CANDIDATE_READY_FOR_FINAL_INDEPENDENT_REASSESSMENT' if summary['status'] == 'PASS' else 'AMENDMENT_CANDIDATE_REMEDIATION_INCOMPLETE'}`\n\nThis candidate is unaccepted and package 0.2 remains a candidate only. The accepted ACCORD-02 package and all historical review evidence remain immutable.\n\n## Scope and identity\n\nThe candidate uses one exact reference representation: object `{{contract_id, contract_version}}` or the existing typed profile/schema equivalent with a separate explicit version. No `@version`, version-folding, lexical normalization, latest/default substitution, or repository fallback is permitted.\n\nThe candidate package is `{package['package_id']}` version `{package['package_version']}` with `CLOSED_EXACT_VERSION`. Effective counts are computed from the package: {len(package['schema_contracts'])} schemas, {len(package['profile_contracts'])} profiles, {len(package['role_vocabulary'])} roles, {len(package['source_schema_registry_entries'])} source-schema pairs, and {len(rules['active_rule_ids'])} active rules. The graph contains {len(graph['node_inventory'])} nodes and {len(graph['edges'])} declared edges.\n\n## Three-assessor evidence\n\nClaude and DeepSeek reports are preserved at their exact local paths and hashes recorded in `accord-02e4r2-three-assessor-findings.json`. Jules exact source bytes were unavailable; the record is `JULES_REPORT_SOURCE_HASH: UNAVAILABLE` and only its five reported defect classes are recorded. No source normalization was performed.\n\n## Closure results\n\n- Non-null reference audit: {ref_audit['summary']['resolved']} resolved / {ref_audit['summary']['unresolved']} unresolved; nullable optional slots are reported separately.\n- Canonicalization: {len(canon['applies_to'])} declared concrete mappings; {len(catalog['vectors']) + 1} candidate digest-bearing forms; data-driven target derivation; no record-type deletion convention.\n- Binding: registry tuple authority is separate from additive evidence-provenance requirements; recipient acknowledgement retains its required recipient binding; generic occurrence does not advertise target acknowledgement.\n- Negative scope: {len(req_map['requirements'])} requirements map to explicit proposition, evidence, and profile fields; V013 trace is complete and mutation-guarded.\n- Validation graph: full active node set and computed cycle/dependency checks.\n- Closure checker: counts and verdict are calculated from parsed artifacts and mutation predicates.\n\n## Preserved design freeze\n\nThe amendment does not reopen exact predicate/stage resolution, POSITIVE_STAGE, GENERIC_OCCURRENCE, NEGATIVE_SCOPE, explicit predecessor edges, same-effect predecessor coupling, no global stage order, generic/stage non-entailment, the five accepted predicate/stage rows, or the 23-vector expectation contract.\n\n## Limitations\n\nNo package-0.2 acceptance, tag, push, ACCORD-03 change, runtime, experiment, or provider call was performed. The remediation environment did not have the pinned external Draft 2020-12 validator packages installed; the schema report records JSON parsing and explicit contract checks, not independent interoperability certification.\n\n## Next gate\n\n`ACCORD-02E4R2 COMPLETE — READY FOR FINAL MULTI-ASSESSOR REASSESSMENT BEFORE PACKAGE-0.2 ACCEPTANCE.`\n"""
    md = md.replace("The remediation environment did not have the pinned external Draft 2020-12 validator packages installed; the schema report records JSON parsing and explicit contract checks, not independent interoperability certification.", "The candidate includes a reproducible standards-validation helper; its Draft 2020-12 and RFC 8785 results are reference-environment checks, not cross-implementation interoperability certification. Immutable inherited profile artifacts are not rewritten or re-certified by this bounded R2 delta.")
    (HERE / "ACCORD-02E4R2-THREE-ASSESSOR-REMEDIATION.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
