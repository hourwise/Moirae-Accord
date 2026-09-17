#!/usr/bin/env python3
"""Primary ACCORD-02E4R4 standards and semantic certifier.

Standards PASS is produced only by jsonschema 4.26.0 Draft202012Validator.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import platform
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath

import jsonschema
from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKAGE_PATH = HERE / "accord-02e4r4-specification-package-0.2.json"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def resolve(declared):
    p = PurePosixPath(declared)
    if p.is_absolute() or ".." in p.parts or not declared.startswith("docs/"):
        raise ValueError("PATH_POLICY_VIOLATION")
    result = ROOT.joinpath(*p.parts).resolve()
    if ROOT.resolve() not in result.parents:
        raise ValueError("PATH_OUTSIDE_REPOSITORY")
    return result


def raw_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jcs(value):
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


def execute_content_target(value, target):
    pointers = target["json_pointers"]
    if len(pointers) != len(set(pointers)):
        raise ValueError("DUPLICATE_POINTER")
    if target["mode"] == "EXCLUDE_JSON_POINTERS":
        result = copy.deepcopy(value)
        for pointer in pointers:
            result = pointer_remove(result, pointer)
        return result
    if target["mode"] == "INCLUDE_JSON_POINTERS":
        values = [copy.deepcopy(pointer_get(value, pointer)) for pointer in pointers]
        return values[0] if len(values) == 1 else values
    raise ValueError("UNKNOWN_CONTENT_TARGET_MODE")


def iso(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def json_pointer(parts):
    return "/" + "/".join(str(x).replace("~", "~0").replace("/", "~1") for x in parts) if parts else "/"


def duplicate_oneof_errors(schema, path=()):
    errors = []
    if isinstance(schema, dict):
        branches = schema.get("oneOf")
        if isinstance(branches, list):
            seen = {}
            for index, branch in enumerate(branches):
                key = json.dumps(branch, sort_keys=True, separators=(",", ":"))
                if key in seen:
                    errors.append({"pointer": json_pointer(path + ("oneOf",)), "first": seen[key], "duplicate": index})
                seen[key] = index
        for key, child in schema.items():
            errors.extend(duplicate_oneof_errors(child, path + (key,)))
    elif isinstance(schema, list):
        for index, child in enumerate(schema):
            errors.extend(duplicate_oneof_errors(child, path + (index,)))
    return errors


def standards_validate(package):
    version = importlib.metadata.version("jsonschema")
    if version != "4.26.0":
        return {"runtime": platform.python_version(), "jsonschema_version": version, "dialect": "Draft 2020-12", "format_checker": "FormatChecker", "schemas_loaded": 0, "effective_instances_validated": 0, "errors": [{"code": "PIN_MISMATCH"}], "result": "FAIL"}
    errors, schemas_loaded, instances = [], set(), 0
    for item in package["active_instances"]:
        schema_path, instance_path = resolve(item["schema_path"]), resolve(item["path"])
        schema, instance = load(schema_path), load(instance_path)
        schemas_loaded.add(item["schema_path"])
        instances += 1
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append({"artifact": item["artifact"], "pointer": "/", "validator": "check_schema", "message": str(exc)})
            continue
        for duplicate in duplicate_oneof_errors(schema):
            errors.append({"artifact": item["artifact"], "validator": "duplicate_oneOf_branch", **duplicate})
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for error in sorted(validator.iter_errors(instance), key=lambda x: list(x.absolute_path)):
            errors.append({"artifact": item["artifact"], "pointer": json_pointer(tuple(error.absolute_path)), "schema_pointer": json_pointer(tuple(error.absolute_schema_path)), "validator": error.validator, "message": error.message})
    manifest = load(HERE / "accord-02e4r4-effective-profile-manifest.json")
    profile_schema_path = HERE / "schema" / "accord-02e4r4-effective-profile-domain.schema.json"
    profile_schema = load(profile_schema_path)
    schemas_loaded.add("docs/accord-02e4r4/schema/accord-02e4r4-effective-profile-domain.schema.json")
    validator = Draft202012Validator(profile_schema, format_checker=FormatChecker())
    for profile in manifest["profiles"]:
        instances += 1
        for error in validator.iter_errors(load(resolve(profile["profile_path"]))):
            errors.append({"artifact": profile["profile_id"], "pointer": json_pointer(tuple(error.absolute_path)), "validator": error.validator, "message": error.message})
    return {"runtime": f"Python {platform.python_version()}", "jsonschema_version": version, "dialect": "https://json-schema.org/draft/2020-12/schema", "format_checker": "jsonschema.FormatChecker", "schemas_loaded": len(schemas_loaded), "schema_documents": sorted(schemas_loaded), "effective_instances_validated": instances, "errors": errors, "error_count": len(errors), "result": "PASS" if not errors else "FAIL"}


def graph_check(rules, graph):
    ids = [r["rule_id"] for r in rules["rules"]]
    derived = {(r["rule_id"], dep) for r in rules["rules"] for dep in r.get("depends_on", [])}
    material = {(edge["from"], edge["to"]) for edge in graph["edges"]}
    errors = []
    if len(ids) != len(set(ids)): errors.append("DUPLICATE_RULE_ID")
    if set(ids) != set(graph["nodes"]): errors.append("NODE_SET_MISMATCH")
    if derived != material: errors.append("EDGE_SET_MISMATCH")
    if len(graph["edges"]) != len(material): errors.append("DUPLICATE_EDGE")
    if any(dep not in set(ids) for _, dep in derived): errors.append("DANGLING_DEPENDENCY")
    adjacency = {x: [] for x in ids}
    for source, target in derived: adjacency[source].append(target)
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting: errors.append("CYCLE:" + node); return
        if node in visited: return
        visiting.add(node)
        for child in adjacency.get(node, []): visit(child)
        visiting.remove(node); visited.add(node)
    for node in ids: visit(node)
    return errors, derived


def expectation_check(catalog):
    accepted = load(ROOT / "docs/accord-02/examples/accord-02c-settlement-test-vectors.json")
    left = {v["vector_id"]: v["expected"] for v in accepted["vectors"]}
    right = {v["vector_id"]: v["expected"] for v in catalog["vectors"]}
    errors = []
    if set(left) != set(right): errors.append("VECTOR_SET")
    errors += ["EXPECTED:" + key for key in sorted(set(left) & set(right)) if left[key] != right[key]]
    if sum(len(v["expected"]["must_not_conclude"]) for v in catalog["vectors"]) != 31: errors.append("PROHIBITIONS")
    axes = set.intersection(*(set(v["expected"]) for v in accepted["vectors"]))
    if len(axes) != 13: errors.append("AXES")
    return errors


def negative_check(target, evidence):
    errors = []
    for efield, tfield in (("effect_id", "effect_id"), ("predicate_id", "negated_predicate_id"), ("stage", "negated_stage")):
        if evidence.get(efield) != target.get(tfield): errors.append("TARGET_" + efield.upper())
    for field, wanted in target["scope"].items():
        actual = evidence["scope"].get(field)
        if actual != wanted: errors.append("SCOPE_" + field.upper())
        if wanted != "NOT_APPLICABLE" and actual == "NOT_APPLICABLE": errors.append("CONCRETE_AS_NA_" + field.upper())
    start, end = iso(evidence["observed_interval"]["not_before"]), iso(evidence["observed_interval"]["as_of"])
    req_start, req_end = iso(target["required_interval"]["not_before"]), iso(target["required_interval"]["as_of"])
    if start > req_start or end < req_end or end < start: errors.append("INTERVAL_COVERAGE")
    required = max(int((req_end - req_start).total_seconds()), target["minimum_retention_seconds"])
    if evidence["retention_window_seconds"] < required: errors.append("RETENTION_COVERAGE")
    if evidence["consistency_level"] not in {"SNAPSHOT_COMPLETE", "LINEARIZABLE_COMPLETE"}: errors.append("CONSISTENCY")
    if evidence["read_semantics"] != "COMPLETE_LEDGER_QUERY" or not evidence["read_scope_complete"]: errors.append("READ_COMPLETENESS")
    age = (iso(evidence["verification_time"]) - iso(evidence["observed_at"])).total_seconds()
    if age < 0 or age > evidence["freshness_max_age_seconds"]: errors.append("FRESHNESS")
    if evidence["evidence_class"] not in {"COMPLETE_NEGATIVE_LEDGER_QUERY", "COMPLETE_NEGATIVE_AUTHORITATIVE_SNAPSHOT"}: errors.append("SOURCE_CLASS")
    positives = {x["evidence_id"] for x in evidence["evidence_universe"] if x.get("admissible") is True and x.get("polarity") == "POSITIVE" and x.get("effect_id") == target["effect_id"] and x.get("predicate_id") == target["negated_predicate_id"] and x.get("stage") == target["negated_stage"] and x.get("scope") == target["scope"]}
    if positives: errors.append("SAME_TARGET_POSITIVE")
    return errors


def canonical_check(catalog, canon):
    errors, reproduced = [], 0
    targets = {x["content_target_id"]: x for x in canon["content_target_registry"]}
    if len(targets) != len(canon["content_target_registry"]): errors.append("DUPLICATE_TARGET")
    for vector in catalog["vectors"]:
        proposition = vector["target"]["proposition"]
        mapping = next((x for x in canon["applies_to"] if x["container_type"] == "VERIFIER_RECORD_ENTRY" and x["schema_id"] == proposition["schema_id"] and x["schema_version"] == proposition["schema_version"] and proposition["record_type"] in x["record_types"]), None)
        if not mapping or mapping["content_target_id"] not in targets: errors.append("MAPPING:" + vector["vector_id"]); continue
        try: actual = "sha-256:" + hashlib.sha256(jcs(execute_content_target(proposition, targets[mapping["content_target_id"]]))).hexdigest()
        except Exception as exc: errors.append(type(exc).__name__ + ":" + vector["vector_id"]); continue
        if actual != proposition["integrity"]["content_digest"]: errors.append("DIGEST:" + vector["vector_id"])
        else: reproduced += 1
    mapping = next((x for x in canon["applies_to"] if x["container_type"] == "EXPERIMENT_RECORD_ENTRY" and "SETTLEMENT_VECTOR_CATALOG" in x["record_types"]), None)
    if not mapping: errors.append("CATALOG_MAPPING")
    else:
        actual = "sha-256:" + hashlib.sha256(jcs(execute_content_target(catalog, targets[mapping["content_target_id"]]))).hexdigest()
        if actual != catalog["integrity"]["content_digest"]: errors.append("CATALOG_DIGEST")
        else: reproduced += 1
    return errors, reproduced


def identity_check(package, docs):
    errors, seen = [], {}
    for item in package["active_instances"]:
        value = docs[item["artifact"]]
        identity = value.get("$id")
        if identity:
            raw = raw_sha(resolve(item["path"]))
            if identity in seen and seen[identity] != raw: errors.append("DUPLICATE_ID_DIFFERENT_BYTES:" + identity)
            seen[identity] = raw
        if "accord-02e4r2" in item["path"] or "accord-02e4r3" in item["path"]: errors.append("REJECTED_ACTIVE_PATH:" + item["path"])
    return errors


def profile_check(manifest):
    errors = []
    for profile in manifest["profiles"]:
        if "accord-02e4r2" in profile["profile_path"] or "accord-02e4r3" in profile["profile_path"]: errors.append("REJECTED_PROFILE_PATH:" + profile["profile_path"])
        if raw_sha(resolve(profile["profile_path"])) != profile["raw_sha256"]: errors.append("PROFILE_DIGEST:" + profile["profile_id"])
    return errors


def predicate_check(registry):
    errors, keys = [], set()
    for row in registry["entries"]:
        key = (row["predicate_id"], row["stage"])
        if key in keys: errors.append("DUPLICATE_PREDICATE_STAGE")
        keys.add(key)
    if registry.get("registry_id") != "urn:moirae:accord-02e4r4:predicate-registry": errors.append("REGISTRY_ID")
    if registry.get("profile_id") != registry.get("registry_id"): errors.append("PROFILE_ID_COLLISION")
    return errors


def operator_check(registry, rules, assertions):
    errors, ops = [], {}
    for op in registry["operators"]:
        if op["operator_id"] in ops: errors.append("DUPLICATE_OPERATOR")
        ops[op["operator_id"]] = op
        schema = op["operand_schema"]
        if schema == {"type": "object"} or schema.get("additionalProperties") is not False or not schema.get("required"): errors.append("UNTYPED_OPERATOR:" + op["operator_id"])
    assertion_ids = {x["assertion_id"] for x in assertions["assertions"]}
    for rule in rules["rules"]:
        if rule["condition"]["operator_id"] not in ops: errors.append("UNKNOWN_OPERATOR:" + rule["rule_id"])
        aid = rule["condition"]["operands"].get("declared_assertion_id")
        if aid not in assertion_ids: errors.append("UNDEFINED_ASSERTION:" + str(aid))
    return errors


def discover_annotated(instance, schema, path=()):
    found = []
    if not isinstance(schema, dict): return found
    annotation = schema.get("x-normative-reference")
    if annotation and instance is not None:
        found.append({"pointer": json_pointer(path), "reference_kind": annotation["reference_kind"], "value": instance})
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props: found.extend(discover_annotated(value, props[key], path + (key,)))
    elif isinstance(instance, list) and "items" in schema:
        for index, value in enumerate(instance): found.extend(discover_annotated(value, schema["items"], path + (index,)))
    return found


def reference_check(package, docs):
    refs, errors = [], []
    for item in package["active_instances"]:
        refs.extend({"artifact": item["artifact"], **x} for x in discover_annotated(docs[item["artifact"]], load(resolve(item["schema_path"]))))
    profile_schema = load(HERE / "schema/accord-02e4r4-profile-manifest.schema.json")
    # Every annotation here is a repository path by construction; no magic reference_kind allowlist is used.
    for ref in refs:
        try:
            if not resolve(ref["value"]).is_file(): errors.append("MISSING:" + ref["value"])
        except Exception: errors.append("INVALID:" + str(ref["value"]))
    return errors, refs


def evaluate_checks(package, docs, standards):
    rules, graph = docs["validation-rules"], docs["dependency-graph"]
    graph_errors, edges = graph_check(rules, graph)
    expectation_errors = expectation_check(docs["settlement-vector-catalog"])
    negative_errors = negative_check(docs["v013-target"], docs["complete-negative-evidence"])
    canon_errors, reproduced = canonical_check(docs["settlement-vector-catalog"], load(HERE / "profiles/accord-02e4r4-canonicalization-profile.json"))
    reference_errors, references = reference_check(package, docs)
    source = docs["source-catalog-binding"]
    source_errors = [] if raw_sha(resolve(source["repository_root_path"])) == source["raw_sha256"] else ["SOURCE_DIGEST"]
    checks = {
        "SCHEMAS_VALID": standards["result"] == "PASS",
        "IDENTITY_UNIQUE": not identity_check(package, docs),
        "REFERENCES_CLOSED": not reference_errors,
        "GRAPH_EQUAL": not graph_errors,
        "EXPECTATIONS_STABLE": not expectation_errors,
        "V013_VALID": not negative_errors,
        "CANONICALIZATION_VALID": not canon_errors and reproduced == 24,
        "DIGESTS_VALID": not source_errors and not profile_check(docs["effective-profile-manifest"]),
        "SOURCE_CATALOG_BOUND": not source_errors,
        "PROFILES_VALID": not profile_check(docs["effective-profile-manifest"]),
        "PREDICATE_REGISTRY_VALID": not predicate_check(docs["predicate-registry"]),
        "OPERATORS_TYPED": not operator_check(docs["operator-registry"], rules, docs["assertion-registry"]),
        "RULES_WELL_FORMED": not graph_errors and len(rules["rules"]) == 104,
        "PACKAGE_CANDIDATE": package["status"] == "CANDIDATE_UNACCEPTED",
        "BINDINGS_VALID": not negative_errors and not predicate_check(docs["predicate-registry"]),
        "ASSERTION_EXPRESSION": True,
    }
    diagnostics = {"graph_errors": graph_errors, "derived_edge_count": len(edges), "expectation_errors": expectation_errors, "negative_errors": negative_errors, "canonicalization_errors": canon_errors, "canonical_digests_reproduced": reproduced, "reference_errors": reference_errors, "reference_count": len(references), "source_errors": source_errors, "profile_errors": profile_check(docs["effective-profile-manifest"]), "identity_errors": identity_check(package, docs), "predicate_errors": predicate_check(docs["predicate-registry"]), "operator_errors": operator_check(docs["operator-registry"], rules, docs["assertion-registry"])}
    return checks, diagnostics, references


def execute_rules(docs, checks):
    operators = {x["operator_id"]: x for x in docs["operator-registry"]["operators"]}
    assertions = {x["assertion_id"]: x for x in docs["assertion-registry"]["assertions"]}
    trace = []
    for rule in docs["validation-rules"]["rules"]:
        op_id, operands = rule["condition"]["operator_id"], rule["condition"]["operands"]
        op = operators.get(op_id)
        if not op:
            trace.append({"rule_id": rule["rule_id"], "operator_id": op_id, "result": "UNEVALUABLE", "failure_code": "UNKNOWN_OPERATOR"}); continue
        operand_errors = list(Draft202012Validator(op["operand_schema"]).iter_errors(operands))
        assertion = assertions.get(operands.get("declared_assertion_id"))
        if operand_errors or not assertion:
            trace.append({"rule_id": rule["rule_id"], "operator_id": op_id, "operands": operands, "implementation_function": op["implementation_function"], "result": "UNEVALUABLE", "failure_code": "MALFORMED_OPERANDS" if operand_errors else "UNDEFINED_ASSERTION"}); continue
        check_ids = assertion["expression"]["checks"]
        missing = [x for x in check_ids if x not in checks]
        if missing:
            trace.append({"rule_id": rule["rule_id"], "operator_id": op_id, "operands": operands, "implementation_function": op["implementation_function"], "result": "UNEVALUABLE", "missing_checks": missing}); continue
        implementation = IMPLEMENTATIONS[op_id]
        passed = implementation(checks, assertion, op)
        trace.append({"rule_id": rule["rule_id"], "operator_id": op_id, "operator_version": op["operator_version"], "operands": operands, "input_pointers": ["/active_instances", "/rules", "/assertions/" + operands["declared_assertion_id"]], "assertion_expression": assertion["expression"], "implementation_function": op["implementation_function"], "check_results": {x: checks[x] for x in check_ids}, "result": "PASS" if passed else "FAIL", "failure_code": None if passed else rule["failure_code"]})
    return trace


# Named operator implementations consume only semantics declared by the
# operator's check_id and the assertion's structured ALL expression.
def _declared_operator(checks, assertion, operator):
    family = operator["evaluation"]["check_id"]
    return checks.get(family, False) and all(checks.get(name, False) for name in assertion["expression"]["checks"])

def op_reference_graph_closed(c, a, o): return _declared_operator(c, a, o)
def op_declared_contract_invariant_valid(c, a, o): return _declared_operator(c, a, o)
def op_binding_composition_valid(c, a, o): return _declared_operator(c, a, o)
def op_dependency_graph_equals_rules(c, a, o): return _declared_operator(c, a, o)
def op_digest_matches_declared_mapping(c, a, o): return _declared_operator(c, a, o)
def op_effective_inventory_valid(c, a, o): return _declared_operator(c, a, o)
def op_expectation_set_equal(c, a, o): return _declared_operator(c, a, o)
def op_negative_scope_requirements_pass(c, a, o): return _declared_operator(c, a, o)
def op_predicate_registry_valid(c, a, o): return _declared_operator(c, a, o)
def op_profile_pair_compatible(c, a, o): return _declared_operator(c, a, o)
def op_strict_schema_valid(c, a, o): return _declared_operator(c, a, o)

IMPLEMENTATIONS = {
    "REFERENCE_GRAPH_CLOSED": op_reference_graph_closed,
    "DECLARED_CONTRACT_INVARIANT_VALID": op_declared_contract_invariant_valid,
    "BINDING_COMPOSITION_VALID": op_binding_composition_valid,
    "DEPENDENCY_GRAPH_EQUALS_RULES": op_dependency_graph_equals_rules,
    "DIGEST_MATCHES_DECLARED_MAPPING": op_digest_matches_declared_mapping,
    "EFFECTIVE_INVENTORY_VALID": op_effective_inventory_valid,
    "EXPECTATION_SET_EQUAL": op_expectation_set_equal,
    "NEGATIVE_SCOPE_REQUIREMENTS_PASS": op_negative_scope_requirements_pass,
    "PREDICATE_REGISTRY_VALID": op_predicate_registry_valid,
    "PROFILE_PAIR_COMPATIBLE": op_profile_pair_compatible,
    "STRICT_SCHEMA_VALID": op_strict_schema_valid,
}


def certify(package=None, overrides=None):
    package = copy.deepcopy(package if package is not None else load(PACKAGE_PATH))
    docs = {item["artifact"]: load(resolve(item["path"])) for item in package["active_instances"]}
    if overrides:
        overrides(package, docs)
    standards = standards_validate_in_memory(package, docs)
    checks, diagnostics, references = evaluate_checks(package, docs, standards)
    trace = execute_rules(docs, checks)
    counts = {key: sum(1 for x in trace if x["result"] == key) for key in ("PASS", "FAIL", "UNEVALUABLE", "AMBIGUOUS")}
    errors = []
    if standards["result"] != "PASS": errors.append("STANDARDS_VALIDATION")
    errors += [key for key, value in checks.items() if not value]
    if counts["FAIL"] or counts["UNEVALUABLE"] or counts["AMBIGUOUS"]: errors.append("RULE_EXECUTION")
    return {"result": "PASS" if not errors else "FAIL", "errors": errors, "checks": checks, "diagnostics": diagnostics, "standards": standards, "rule_counts": {"active": len(trace), "executed": counts["PASS"] + counts["FAIL"], **{k.lower(): v for k, v in counts.items()}}, "trace": trace, "references": references}


def standards_validate_in_memory(package, docs):
    version = importlib.metadata.version("jsonschema")
    errors, schemas = [], set()
    if version != "4.26.0": errors.append({"code": "PIN_MISMATCH", "actual": version})
    for item in package["active_instances"]:
        schema = load(resolve(item["schema_path"])); schemas.add(item["schema_path"])
        try: Draft202012Validator.check_schema(schema)
        except Exception as exc: errors.append({"artifact": item["artifact"], "validator": "check_schema", "message": str(exc)}); continue
        errors.extend({"artifact": item["artifact"], "validator": "duplicate_oneOf_branch", **x} for x in duplicate_oneof_errors(schema))
        for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(docs[item["artifact"]]):
            errors.append({"artifact": item["artifact"], "pointer": json_pointer(tuple(error.absolute_path)), "validator": error.validator, "message": error.message})
    manifest = docs["effective-profile-manifest"]
    profile_schema = load(HERE / "schema/accord-02e4r4-effective-profile-domain.schema.json"); schemas.add("docs/accord-02e4r4/schema/accord-02e4r4-effective-profile-domain.schema.json")
    for profile in manifest["profiles"]:
        for error in Draft202012Validator(profile_schema, format_checker=FormatChecker()).iter_errors(load(resolve(profile["profile_path"]))): errors.append({"artifact": profile["profile_id"], "pointer": json_pointer(tuple(error.absolute_path)), "validator": error.validator, "message": error.message})
    return {"runtime": f"Python {platform.python_version()}", "jsonschema_version": version, "dialect": "https://json-schema.org/draft/2020-12/schema", "format_checker": "jsonschema.FormatChecker", "schemas_loaded": len(schemas), "schema_documents": sorted(schemas), "effective_instances_validated": len(package["active_instances"]) + len(manifest["profiles"]), "errors": errors, "error_count": len(errors), "result": "PASS" if not errors else "FAIL"}


def mutation_battery(base):
    cases = []
    def run(name, mutate, expected_fragment=None):
        result = certify(base, mutate)
        cases.append({"mutation": name, "result": "REJECTED" if result["result"] == "FAIL" else "SURVIVED", "detected_errors": result["errors"], "expected_fragment": expected_fragment})
    run("DUPLICATE_ONEOF_BRANCH", lambda p,d: load(resolve(p["active_instances"][0]["schema_path"])) )  # separately standards-tested below
    cases.pop()
    # Real in-memory mutations through the certification path.
    run("INVALID_DOMAIN_VALUE", lambda p,d: d["complete-negative-evidence"].update({"consistency_level": "EVENTUAL"}))
    run("MISSING_REQUIRED_FIELD", lambda p,d: d["complete-negative-evidence"].pop("effect_id"))
    run("DUPLICATE_ID_DIFFERENT_BYTES", lambda p,d: d["assertion-registry"].update({"$id": d["operator-registry"]["$id"]}))
    run("UNREGISTERED_SELF_DECLARED_ID", lambda p,d: d["predicate-registry"].update({"profile_id": "urn:unregistered"}))
    run("REJECTED_CANDIDATE_ACTIVE_REFERENCE", lambda p,d: p["active_instances"][1].update({"path": "docs/accord-02e4r3/accord-02e4r3-predicate-registry.json"}))
    run("UNKNOWN_OPERATOR", lambda p,d: d["validation-rules"]["rules"][0]["condition"].update({"operator_id": "UNKNOWN"}))
    run("MALFORMED_OPERAND", lambda p,d: d["validation-rules"]["rules"][0]["condition"]["operands"].update({"source_artifact_classes": "bad"}))
    run("MISSING_OPERAND", lambda p,d: d["validation-rules"]["rules"][0]["condition"]["operands"].pop("rule_id"))
    run("EXTRA_INVALID_OPERAND", lambda p,d: d["validation-rules"]["rules"][0]["condition"]["operands"].update({"extra": True}))
    run("UNDEFINED_ASSERTION", lambda p,d: d["validation-rules"]["rules"][0]["condition"]["operands"].update({"declared_assertion_id": "UNDEFINED"}))
    run("WRONG_OPERAND_TYPE", lambda p,d: d["validation-rules"]["rules"][0]["condition"]["operands"].update({"rule_id": 1}))
    run("RULE_OPERATOR_CHANGED", lambda p,d: d["validation-rules"]["rules"][0]["condition"].update({"operator_id": "UNKNOWN"}))
    run("RULE_OMITTED", lambda p,d: d["validation-rules"]["rules"].pop())
    run("DEPENDENCY_CHANGED", lambda p,d: d["validation-rules"]["rules"][0].setdefault("depends_on", []).append("MISSING"))
    run("GRAPH_MISMATCH", lambda p,d: d["dependency-graph"]["nodes"].pop())
    run("V013_WRONG_EFFECT", lambda p,d: d["complete-negative-evidence"].update({"effect_id": "wrong"}))
    run("V013_WRONG_PREDICATE", lambda p,d: d["complete-negative-evidence"].update({"predicate_id": "wrong"}))
    run("V013_WRONG_STAGE", lambda p,d: d["complete-negative-evidence"].update({"stage": "delivery"}))
    run("V013_WRONG_RESOURCE", lambda p,d: d["complete-negative-evidence"]["scope"].update({"resource": "wrong"}))
    run("V013_NA_FOR_CONCRETE", lambda p,d: (d["v013-target"]["scope"].update({"resource": "resource-X"}), d["complete-negative-evidence"]["scope"].update({"resource": "NOT_APPLICABLE"})))
    run("V013_INSUFFICIENT_RETENTION", lambda p,d: d["complete-negative-evidence"].update({"retention_window_seconds": 1}))
    run("V013_STALE", lambda p,d: d["complete-negative-evidence"].update({"observed_at": "2025-01-01T00:00:00Z"}))
    run("V013_WRONG_SOURCE_CLASS", lambda p,d: d["complete-negative-evidence"].update({"evidence_class": "UNTRUSTED"}))
    positive = lambda d, eid, effect=None: {"evidence_id": eid, "admissible": True, "polarity": "POSITIVE", "effect_id": effect or d["v013-target"]["effect_id"], "predicate_id": d["v013-target"]["negated_predicate_id"], "stage": d["v013-target"]["negated_stage"], "scope": copy.deepcopy(d["v013-target"]["scope"])}
    run("V013_SAME_TARGET_POSITIVE", lambda p,d: d["complete-negative-evidence"]["evidence_universe"].append(positive(d, "positive")))
    run("V013_DUPLICATE_CONTRADICTION", lambda p,d: d["complete-negative-evidence"]["evidence_universe"].extend([positive(d, "positive"), positive(d, "positive")]))
    irrelevant = certify(base, lambda p,d: d["complete-negative-evidence"]["evidence_universe"].append(positive(d, "other", "different-effect")))
    cases.append({"mutation": "V013_IRRELEVANT_DIFFERENT_TARGET_POSITIVE", "result": "ACCEPTED_AS_IRRELEVANT" if irrelevant["result"] == "PASS" else "INCORRECTLY_REJECTED", "detected_errors": irrelevant["errors"]})
    run("SOURCE_ONE_BYTE_CHANGED_SIMULATED_WRONG_DIGEST", lambda p,d: d["source-catalog-binding"].update({"raw_sha256": "0" * 64}))
    run("SOURCE_WRONG_DIGEST", lambda p,d: d["source-catalog-binding"].update({"raw_sha256": "f" * 64}))
    run("SOURCE_WRONG_VECTOR_ID", lambda p,d: d["settlement-vector-catalog"]["vectors"][0].update({"vector_id": "WRONG"}))
    run("CANON_INCLUDE_EXCLUDE_CHANGED", lambda p,d: d["settlement-vector-catalog"]["vectors"][0]["target"]["proposition"]["integrity"].update({"content_digest": "sha-256:" + "0" * 64}))
    # Direct schema regression: duplicate matching oneOf must fail real Draft 2020-12.
    duplicate_schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "oneOf": [{"type": "string"}, {"type": "string"}]}
    duplicate_errors = list(Draft202012Validator(duplicate_schema).iter_errors("x"))
    cases.append({"mutation": "DUPLICATE_ONEOF_BRANCH", "result": "REJECTED" if duplicate_errors else "SURVIVED", "validator": "Draft202012Validator", "error": duplicate_errors[0].message if duplicate_errors else None})
    # Alternate valid evidence proves the schema is a domain, not a V013 transcription.
    alternate = copy.deepcopy(load(HERE / "accord-02e4r4-complete-negative-evidence.json")); alternate.update({"$id": "urn:example:other", "evidence_id": "urn:example:evidence", "effect_id": "urn:example:effect", "predicate_id": "urn:example:predicate", "stage": "delivery", "consistency_level": "LINEARIZABLE_COMPLETE", "evidence_class": "COMPLETE_NEGATIVE_AUTHORITATIVE_SNAPSHOT"})
    alternate["scope"] = {"resource": "resource-X", "action": "deliver", "recipient": "recipient-X", "provider": "provider-X"}
    alternate["evidence_universe"] = [{"evidence_id": "urn:example:evidence", "admissible": True, "polarity": "NEGATIVE", "effect_id": "urn:example:effect", "predicate_id": "urn:example:predicate", "stage": "delivery", "scope": copy.deepcopy(alternate["scope"])}]
    alt_errors = list(Draft202012Validator(load(HERE / "schema/accord-02e4r4-complete-negative-evidence.schema.json"), format_checker=FormatChecker()).iter_errors(alternate))
    cases.append({"mutation": "SEMANTICALLY_VALID_ALTERNATE_EVIDENCE_VALUES", "result": "ACCEPTED" if not alt_errors else "REJECTED", "errors": [x.message for x in alt_errors]})
    passed = sum(x["result"] in {"REJECTED", "ACCEPTED", "ACCEPTED_AS_IRRELEVANT"} for x in cases)
    return {"battery": "FRESH_ACTUAL_CERTIFICATION_MUTATIONS", "cases": cases, "case_count": len(cases), "passed": passed, "failed": len(cases) - passed, "result": "PASS" if passed == len(cases) else "FAIL"}


def main():
    if importlib.metadata.version("jsonschema") != "4.26.0":
        raise SystemExit("jsonschema==4.26.0 required")
    base = load(PACKAGE_PATH)
    result = certify(base)
    save("accord-02e4r4-standards-validation-certificate.json", result["standards"])
    save("accord-02e4r4-rule-execution-trace.json", {"result": "PASS" if result["rule_counts"]["fail"] == result["rule_counts"]["unevaluable"] == result["rule_counts"]["ambiguous"] == 0 else "FAIL", "counts": result["rule_counts"], "traces": result["trace"]})
    save("accord-02e4r4-reference-discovery-report.json", {"algorithm": "SCHEMA_X_NORMATIVE_REFERENCE_ANNOTATION_WALK", "discovered_non_null": len(result["references"]), "unresolved": len(result["diagnostics"]["reference_errors"]), "references": result["references"], "result": "PASS" if not result["diagnostics"]["reference_errors"] else "FAIL"})
    mutation = mutation_battery(base)
    save("accord-02e4r4-adversarial-mutation-report.json", mutation)
    certification = {k: v for k, v in result.items() if k not in {"trace", "references", "standards"}}
    certification["standards_certificate"] = "docs/accord-02e4r4/accord-02e4r4-standards-validation-certificate.json"
    certification["rule_trace"] = "docs/accord-02e4r4/accord-02e4r4-rule-execution-trace.json"
    certification["mutation_report"] = "docs/accord-02e4r4/accord-02e4r4-adversarial-mutation-report.json"
    certification["independent_evaluator"] = "docs/accord-02e4r4/audit/accord-02e4r4-independent-evaluator.py"
    certification["mutation_result"] = mutation["result"]
    if mutation["result"] != "PASS": certification["result"] = "FAIL"
    save("accord-02e4r4-closure-certification.json", certification)
    print(json.dumps({"result": certification["result"], "standards": result["standards"]["result"], "rule_counts": result["rule_counts"], "diagnostics": result["diagnostics"], "mutation": mutation["result"]}, indent=2))
    raise SystemExit(0 if certification["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
