from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "docs" / "accord-02"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def jcs(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return "sha-256:" + hashlib.sha256(jcs(value)).hexdigest()


def raw_digest(path):
    return "sha-256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_path(declared):
    p = PurePosixPath(declared)
    if p.is_absolute() or ".." in p.parts or not declared.startswith("docs/"):
        raise ValueError("PATH_POLICY_VIOLATION")
    resolved = ROOT.joinpath(*p.parts).resolve()
    if ROOT.resolve() not in resolved.parents:
        raise ValueError("PATH_OUTSIDE_REPOSITORY")
    return resolved


def pointer_get(value, pointer):
    cur = value
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        cur = cur[int(token)] if isinstance(cur, list) else cur[token]
    return cur


def pointer_remove(value, pointer):
    result = copy.deepcopy(value)
    parts = pointer.split("/")[1:]
    cur = result
    for raw in parts[:-1]:
        token = raw.replace("~1", "/").replace("~0", "~")
        cur = cur[int(token)] if isinstance(cur, list) else cur[token]
    token = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(cur, list):
        del cur[int(token)]
    else:
        del cur[token]
    return result


def execute_content_target(value, target):
    pointers = target["json_pointers"]
    if len(pointers) != len(set(pointers)):
        raise ValueError("DUPLICATE_POINTER")
    if target["mode"] == "EXCLUDE_JSON_POINTERS":
        result = copy.deepcopy(value)
        for p in pointers:
            result = pointer_remove(result, p)
        return result
    if target["mode"] == "INCLUDE_JSON_POINTERS":
        if len(pointers) == 1:
            return copy.deepcopy(pointer_get(value, pointers[0]))
        return [copy.deepcopy(pointer_get(value, p)) for p in pointers]
    raise ValueError("UNKNOWN_CONTENT_TARGET_MODE")


def strict_schema_errors(schema, location=""):
    errors = []
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            if schema.get("additionalProperties") is not False:
                errors.append(location + ":OPEN_OBJECT")
            if "required" not in schema:
                errors.append(location + ":REQUIRED_MISSING")
        for key, value in schema.items():
            errors += strict_schema_errors(value, location + "/" + key)
    elif isinstance(schema, list):
        for i, value in enumerate(schema):
            errors += strict_schema_errors(value, location + f"/{i}")
    return errors


def structural_validate(value, schema, location=""):
    errors = []
    if schema is False:
        return [location + ":VALUE_FORBIDDEN"]
    if "oneOf" in schema:
        outcomes = [structural_validate(value, s, location) for s in schema["oneOf"]]
        return [] if any(not x for x in outcomes) else [location + ":NO_ONEOF_MATCH"]
    expected = schema.get("type")
    actual_ok = {"object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str), "integer": isinstance(value, int) and not isinstance(value, bool), "boolean": isinstance(value, bool), "null": value is None}.get(expected, True)
    if not actual_ok:
        return [location + ":TYPE"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(location + ":ENUM")
    if expected == "object":
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(location + "/" + key + ":REQUIRED")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(location + "/" + key + ":ADDITIONAL")
        for key, child in value.items():
            if key in props:
                errors += structural_validate(child, props[key], location + "/" + key)
    elif expected == "array":
        for i, child in enumerate(value):
            errors += structural_validate(child, schema.get("items", {}), location + f"/{i}")
    return errors


def walk_refs(value, pointer=""):
    found = []
    if isinstance(value, dict):
        if value.get("reference_kind") in {"CONTRACT", "SCHEMA", "PROFILE", "SOURCE_VECTOR"}:
            found.append((pointer or "/", value))
        for key, child in value.items():
            found += walk_refs(child, pointer + "/" + key.replace("~", "~0").replace("/", "~1"))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            found += walk_refs(child, pointer + f"/{i}")
    return found


def ref_key(ref):
    kind = ref["reference_kind"]
    if kind == "CONTRACT": return (kind, ref.get("contract_id"), ref.get("contract_version"))
    if kind == "SCHEMA": return (kind, ref.get("schema_id"), ref.get("schema_version"))
    if kind == "PROFILE": return (kind, ref.get("profile_type"), ref.get("profile_id"), ref.get("profile_version"))
    return (kind, ref.get("catalog_id"), ref.get("catalog_version"), ref.get("vector_id"))


def make_targets(package, instances):
    targets = set()
    targets.add(("CONTRACT", package["package_id"], package["package_version"]))
    for item in package["schema_contracts"]:
        targets.add(("SCHEMA", item["schema_id"], item["schema_version"]))
    for item in package["profile_contracts"]:
        targets.add(("PROFILE", item["profile_type"], item["profile_id"], item["profile_version"]))
    for item in package["active_contracts"]:
        if item["contract_class"] != "SCHEMA":
            targets.add(("CONTRACT", item["object_id"], item["object_version"]))
    accepted = load(BASE / "examples" / "accord-02c-settlement-test-vectors.json")
    for vector in accepted["vectors"]:
        targets.add(("SOURCE_VECTOR", "urn:moirae:accord-02c:settlement-test-vectors", "0.1", vector["vector_id"]))
    # The registered normative-contract artifact explicitly owns these definitions.
    normative = next((x["value"] for k, x in instances.items() if k.endswith("normative-contracts.json")), None)
    if normative:
        for cap in normative.get("evidence_capability_contracts", []):
            targets.add(("CONTRACT", cap["capability_id"], cap["capability_version"]))
        for contract in normative.get("negative_scope_contracts", []):
            targets.add(("CONTRACT", contract["contract_id"], contract["contract_version"]))
    return targets


def graph_errors(rules, graph):
    nodes = {r["rule_id"] for r in rules["rules"]}
    material_nodes = set(graph["node_inventory"])
    derived = {(r["rule_id"], d) for r in rules["rules"] for d in r.get("depends_on", [])}
    material = {(e["from"], d) for e in graph["edges"] for d in e["depends_on"]}
    errors = []
    if nodes != material_nodes: errors.append("NODE_SET_MISMATCH")
    if derived != material: errors.append("EDGE_SET_MISMATCH")
    if any(d not in nodes for _, d in derived): errors.append("MISSING_DEPENDENCY_TARGET")
    adjacency = {n: [] for n in nodes}
    for a, b in derived: adjacency[a].append(b)
    visiting, visited = set(), set()
    def visit(n):
        if n in visiting: errors.append("DEPENDENCY_CYCLE:" + n); return
        if n in visited: return
        visiting.add(n)
        for d in adjacency.get(n, []): visit(d)
        visiting.remove(n); visited.add(n)
    for n in nodes: visit(n)
    return errors, derived


def binding_errors(registry, normative):
    errors, tuples = [], set()
    caps = {x["capability_id"]: x for x in normative["evidence_capability_contracts"]}
    provenance = {"observer_principal_id", "issuer_principal_id", "observer_id", "issuer_id"}
    for entry in registry["entries"]:
        key = (entry["predicate_id"], entry["stage"])
        if key in tuples: errors.append("DUPLICATE_TUPLE")
        tuples.add(key)
        required, optional, na = map(set, (entry.get("required_bindings", []), entry.get("optional_bindings", []), entry.get("not_applicable_bindings", [])))
        if required & optional or required & na or optional & na: errors.append("BINDING_INTERSECTION:" + str(key))
        if required & provenance: errors.append("PROVENANCE_AS_IDENTITY:" + str(key))
        cap_ref = entry.get("evidence_capability_ref")
        if cap_ref:
            cap = caps.get(cap_ref.get("contract_id"))
            if not cap: errors.append("CAPABILITY_UNRESOLVED:" + str(key)); continue
            cap_req = set(cap.get("required_proposition_bindings", []))
            if not cap_req <= required | optional: errors.append("CAPABILITY_NOT_SUBSET:" + str(key))
            if cap_req & na: errors.append("CAPABILITY_NA_CONFLICT:" + str(key))
    return errors


def predicate_errors(registry, partial):
    errors = []
    rows = {(x["predicate_id"], x["stage"]): x for x in registry["entries"]}
    if len(rows) != len(registry["entries"]): errors.append("DUPLICATE_PREDICATE_STAGE")
    for key, row in rows.items():
        for edge in row.get("predecessors", row.get("predecessor_edges", [])):
            target = (edge.get("predicate_id", key[0]), edge.get("stage"))
            if target == key: errors.append("SELF_PREDECESSOR")
            if target not in rows: errors.append("DANGLING_PREDECESSOR")
            elif rows[target].get("support_status") == "UNSUPPORTED": errors.append("UNSUPPORTED_PREDECESSOR")
    if partial["target_already_supported"] != "NOT_PARTIAL_EFFECT": errors.append("SUPPORTED_TARGET_PARTIAL_EFFECT")
    return errors


def negative_errors(evidence, requirements):
    errors = []
    def dt(v): return datetime.fromisoformat(v.replace("Z", "+00:00"))
    for req in requirements["requirements"]:
        op, operands = req["operator_id"], req["operands"]
        ok = True
        try:
            if op == "EXACT_VALUE_EQUAL": ok = pointer_get(evidence, operands["pointer"]) == operands["expected"]
            elif op == "EXACT_TUPLE_EXISTS": ok = all(evidence.get(x) for x in operands["fields"])
            elif op == "SCOPE_BINDINGS_COMPLETE": ok = all(evidence["scope_bindings"].get(x) for x in operands["fields"])
            elif op == "RFC3339_INTERVAL_VALID": ok = dt(evidence["observed_interval"]["not_before"]) <= dt(evidence["observed_interval"]["as_of"])
            elif op == "INTEGER_RANGE_COVERS": ok = evidence["retention_window_seconds"] >= (dt(evidence["observed_interval"]["as_of"]) - dt(evidence["observed_interval"]["not_before"])).total_seconds()
            elif op == "ENUM_ALLOWED": ok = pointer_get(evidence, operands["pointer"]) in operands["allowed"]
            elif op == "TIMESTAMP_AGE_LE_MAX": ok = 0 <= (dt(evidence["verification_time"]) - dt(evidence["observed_at"])).total_seconds() <= evidence["freshness_max_age_seconds"]
            elif op == "COUNT_ADMISSIBLE_EVIDENCE_EQ":
                positives = {x["evidence_id"] for x in evidence["evidence_universe"] if x.get("admissible") and x.get("proposition") == "POSITIVE" and x.get("effect_id") == evidence["effect_id"] and x.get("predicate_id") == evidence["predicate_id"] and x.get("stage") == evidence["stage"]}
                ok = len(positives) == operands["expected"]
            else: ok = False
        except (KeyError, TypeError, ValueError): ok = False
        if not ok: errors.append(req["requirement_id"])
    return errors


def expectation_errors(catalog):
    accepted = load(BASE / "examples" / "accord-02c-settlement-test-vectors.json")
    a = {x["vector_id"]: x["expected"] for x in accepted["vectors"]}
    c = {x["vector_id"]: x["expected"] for x in catalog["vectors"]}
    errors = []
    if set(a) != set(c): errors.append("VECTOR_SET_MISMATCH")
    for vid in set(a) & set(c):
        if a[vid] != c[vid]: errors.append("EXPECTED_OUTCOME_CHANGED:" + vid)
    if sum(len(x["expected"]["must_not_conclude"]) for x in catalog["vectors"]) != 31: errors.append("PROHIBITION_COUNT_CHANGED")
    return errors


def canonical_errors(canon, catalog):
    errors = []
    targets = {x["content_target_id"]: x for x in canon["content_target_registry"]}
    if len(targets) != len(canon["content_target_registry"]): errors.append("DUPLICATE_TARGET")
    if any("content_target" in x for x in canon["applies_to"]): errors.append("INLINE_TARGET_DUPLICATION")
    for vector in catalog["vectors"]:
        prop = vector["target"]["proposition"]
        mapping = next((m for m in canon["applies_to"] if m["container_type"] == "VERIFIER_RECORD_ENTRY" and m["schema_id"] == prop["schema_id"] and m["schema_version"] == prop["schema_version"] and prop["record_type"] in m["record_types"]), None)
        if not mapping or mapping["content_target_id"] not in targets: errors.append("MAPPING_UNRESOLVED:" + vector["vector_id"]); continue
        try: actual = digest(execute_content_target(prop, targets[mapping["content_target_id"]]))
        except Exception as exc: errors.append(type(exc).__name__ + ":" + vector["vector_id"]); continue
        if actual != prop["integrity"]["content_digest"]: errors.append("DIGEST_MISMATCH:" + vector["vector_id"])
    mapping = next((m for m in canon["applies_to"] if m["container_type"] == "EXPERIMENT_RECORD_ENTRY" and "SETTLEMENT_VECTOR_CATALOG" in m["record_types"]), None)
    if not mapping or mapping["content_target_id"] not in targets:
        errors.append("CATALOG_MAPPING_UNRESOLVED")
    else:
        try: actual = digest(execute_content_target(catalog, targets[mapping["content_target_id"]]))
        except Exception as exc: errors.append(type(exc).__name__ + ":CATALOG")
        else:
            if actual != catalog["integrity"]["content_digest"]: errors.append("CATALOG_DIGEST_MISMATCH")
    return errors


def load_candidate():
    package = load(HERE / "accord-02e4r3-specification-package-0.2.json")
    values = {}
    for item in package["active_contracts"]:
        if item["contract_class"] == "SCHEMA": continue
        values[item["path"]] = {"path": item["path"], "value": load(resolve_path(item["path"]))}
    return package, values


def verify(package, values):
    by_suffix = {Path(k).stem.replace("accord-02e4r3-", ""): v["value"] for k, v in values.items()}
    rules, graph = by_suffix["validation-rules"], by_suffix["dependency-graph"]
    errors = []
    # Lineage and path/inventory.
    if package["package_id"] != "urn:moirae:accord-02r5:specification-package" or package["on_acceptance"]["replaces"] != {"package_id": package["package_id"], "package_version": "0.1"}: errors.append("LINEAGE_IDENTITY")
    if package.get("contract_policy") != "CLOSED_EXACT_VERSION": errors.append("OPEN_CONTRACT_POLICY")
    if package["path_resolution"].get("path_base") != "REPOSITORY_ROOT": errors.append("WRONG_PATH_BASE")
    for name in ("base_package", "previous_rejected_candidate"):
        item = package["lineage"][name]
        try:
            if raw_digest(resolve_path(item["path"])) != item["digest"]: errors.append("LINEAGE_DIGEST:" + name)
        except Exception: errors.append("LINEAGE_PATH:" + name)
    target = copy.deepcopy(package); del target["lineage"]["current_candidate"]["digest"]
    if digest(target) != package["lineage"]["current_candidate"]["digest"]: errors.append("SELF_DIGEST")
    for item in package["schema_contracts"] + package["profile_contracts"] + package["active_contracts"]:
        path = item.get("schema_path", item.get("profile_path", item.get("path")))
        try:
            if not resolve_path(path).is_file(): errors.append("MISSING_PATH:" + path)
        except Exception: errors.append("INVALID_PATH:" + str(path))
    # Strict candidate schemas and instance validation.
    schema_by_id = {}
    for item in package["schema_contracts"]:
        try:
            schema_by_id[(item["schema_id"], item["schema_version"])] = load(resolve_path(item["schema_path"]))
        except Exception:
            errors.append("SCHEMA_PATH_INVALID:" + item["schema_id"])
    for item in package["active_contracts"]:
        if item["contract_class"] == "SCHEMA":
            errors += ["SCHEMA:" + x for x in strict_schema_errors(load(resolve_path(item["path"])), item["object_id"])]
        elif "schema" in item:
            schema = schema_by_id.get((item["schema"]["schema_id"], item["schema"]["schema_version"]))
            if not schema: errors.append("INSTANCE_SCHEMA_MISSING:" + item["object_id"])
            else:
                try:
                    instance_value = values[item["path"]]["value"] if item["path"] in values else load(resolve_path(item["path"]))
                    errors += ["INSTANCE:" + item["object_id"] + x for x in structural_validate(instance_value, schema)]
                except Exception:
                    errors.append("INSTANCE_PATH_INVALID:" + item["object_id"])
    for profile in package["profile_contracts"]:
        if profile.get("status") == "RETIRED" or profile.get("retired"):
            continue
        schema = schema_by_id.get((profile["schema_id"], profile["schema_version"]))
        if not schema:
            errors.append("PROFILE_SCHEMA_MISSING:" + profile["profile_id"])
            continue
        try:
            profile_value = load(resolve_path(profile["profile_path"]))
            errors += ["PROFILE:" + profile["profile_id"] + x for x in structural_validate(profile_value, schema)]
        except Exception:
            errors.append("PROFILE_PATH_INVALID:" + profile["profile_id"])
    targets = make_targets(package, values)
    refs = []
    for path, wrapped in values.items():
        refs += [(path + ptr, ref) for ptr, ref in walk_refs(wrapped["value"])]
    refs += [("package" + ptr, ref) for ptr, ref in walk_refs(package)]
    unresolved = [(p, ref_key(r)) for p, r in refs if ref_key(r) not in targets]
    if unresolved: errors += ["UNRESOLVED_REFERENCE:" + p + ":" + str(k) for p, k in unresolved]
    ge, derived = graph_errors(rules, graph); errors += ge
    errors += canonical_errors(by_suffix["canonicalization-profile"], by_suffix["settlement-vector-catalog"])
    errors += binding_errors(by_suffix["predicate-registry"], by_suffix["normative-contracts"])
    errors += predicate_errors(by_suffix["predicate-registry"], by_suffix["partial-effect-policy"])
    errors += ["NEGATIVE:" + x for x in negative_errors(by_suffix["complete-negative-evidence"], by_suffix["negative-scope-requirements"])]
    errors += expectation_errors(by_suffix["settlement-vector-catalog"])
    v018 = next(x for x in by_suffix["settlement-vector-catalog"]["vectors"] if "V018" in x["vector_id"])
    semantics = by_suffix["profile-semantics"]
    left, right = v018["settlement_profile_ref"], v018["evidence_profile_ref"]
    same = (left["profile_type"], left["profile_id"], left["profile_version"]) == (right["profile_type"], right["profile_id"], right["profile_version"])
    pair_result = semantics["same_profile_result"] if same else semantics["undeclared_different_pair_result"]
    if pair_result != v018["expected"]["profile_compatibility"]: errors.append("V018_PROFILE_PAIR_SEMANTICS")
    registered_ops = {x["operator_id"] for x in by_suffix["operator-registry"]["operators"]}
    for rule in rules["rules"]:
        if rule["condition"]["operator_id"] not in registered_ops: errors.append("UNKNOWN_RULE_OPERATOR:" + rule["rule_id"])
        if not isinstance(rule["condition"].get("operands"), dict): errors.append("MALFORMED_RULE_OPERANDS:" + rule["rule_id"])
    traces = [{"rule_id": r["rule_id"], "operator": r["condition"]["operator_id"], "operands": r["condition"]["operands"], "source_artifacts": r["condition"]["operands"].get("source_artifact_classes", []) if isinstance(r["condition"]["operands"], dict) else [], "result": "PASS" if not errors else "FAIL"} for r in rules["rules"] if r["severity"] == "BLOCKING"]
    return errors, {"references": len(refs), "unresolved": len(unresolved), "rules": len(rules["rules"]), "dependency_pairs": len(derived), "blocking_traces": traces}


def mutations(package, values):
    cases = []
    def run(mid, mutate, refresh=True):
        p, v = copy.deepcopy(package), copy.deepcopy(values)
        mutate(p, v)
        if refresh:
            target = copy.deepcopy(p)
            del target["lineage"]["current_candidate"]["digest"]
            p["lineage"]["current_candidate"]["digest"] = digest(target)
        errs, _ = verify(p, v)
        cases.append({"mutation_id": mid, "detected": bool(errs), "failure_codes": errs[:8]})
    suffix = lambda v, n: next(x for k, x in v.items() if Path(k).stem == "accord-02e4r3-" + n)["value"]
    run("LINEAGE-UNRELATED", lambda p,v: p.__setitem__("package_id", "urn:unrelated"))
    run("LINEAGE-BASE-DIGEST", lambda p,v: p["lineage"]["base_package"].__setitem__("digest", "sha-256:"+"0"*64))
    run("LINEAGE-SELF-DIGEST", lambda p,v: p["lineage"]["current_candidate"].__setitem__("digest", "sha-256:"+"0"*64), False)
    run("LINEAGE-OPEN-POLICY", lambda p,v: p.__setitem__("contract_policy", "OPEN"))
    run("PATH-WRONG-BASE", lambda p,v: p["path_resolution"].__setitem__("path_base", "PACKAGE_DIRECTORY"))
    run("PATH-TRAVERSAL", lambda p,v: p["active_contracts"][0].__setitem__("path", "docs/../escape.json"))
    run("PATH-INHERITED-WRONG-ROOT", lambda p,v: p["schema_contracts"][0].__setitem__("schema_path", "schema/missing.json"))
    run("REFERENCE-GARBAGE", lambda p,v: p.__setitem__("operator_registry_ref", {"reference_kind":"CONTRACT","contract_id":"urn:garbage","contract_version":"0.2"}))
    run("REFERENCE-OMITTED-VERSION", lambda p,v: p["operator_registry_ref"].pop("contract_version"))
    run("CANON-INCLUDE", lambda p,v: suffix(v,"canonicalization-profile")["content_target_registry"][0].update({"mode":"INCLUDE_JSON_POINTERS","json_pointers":["/integrity"]}))
    run("CANON-MISSING-POINTER", lambda p,v: suffix(v,"canonicalization-profile")["content_target_registry"][0].update({"json_pointers":["/missing"]}))
    run("CANON-DUPLICATE-TARGET", lambda p,v: suffix(v,"canonicalization-profile")["content_target_registry"].append(copy.deepcopy(suffix(v,"canonicalization-profile")["content_target_registry"][0])))
    run("CANON-WRONG-TARGET-ID", lambda p,v: suffix(v,"canonicalization-profile")["applies_to"][0].update({"content_target_id":"UNKNOWN"}))
    run("RULE-UNKNOWN-OPERATOR", lambda p,v: suffix(v,"validation-rules")["rules"][0]["condition"].update({"operator_id":"UNKNOWN"}))
    run("RULE-MALFORMED-OPERANDS", lambda p,v: suffix(v,"validation-rules")["rules"][0]["condition"].update({"operands":[]}))
    run("RULE-MISSING-DEPENDENCY", lambda p,v: suffix(v,"validation-rules")["rules"][0].setdefault("depends_on",[]).append("MISSING"))
    run("RULE-CYCLE", lambda p,v: suffix(v,"validation-rules")["rules"][0].setdefault("depends_on",[]).append(suffix(v,"validation-rules")["rules"][0]["rule_id"]))
    run("GRAPH-RULE-OMITTED", lambda p,v: suffix(v,"dependency-graph")["node_inventory"].pop())
    run("BINDING-RECIPIENT-REMOVED", lambda p,v: next(x for x in suffix(v,"predicate-registry")["entries"] if "recipient" in x["predicate_id"])["required_bindings"].clear())
    run("BINDING-NA-CONFLICT", lambda p,v: suffix(v,"predicate-registry")["entries"][0]["not_applicable_bindings"].append(suffix(v,"predicate-registry")["entries"][0]["required_bindings"][0]))
    run("BINDING-PROVENANCE-PROMOTED", lambda p,v: suffix(v,"predicate-registry")["entries"][0]["required_bindings"].append("observer_principal_id"))
    run("BINDING-UNSUPPORTED-CAPABILITY", lambda p,v: suffix(v,"predicate-registry")["entries"][0].update({"evidence_capability_ref":{"reference_kind":"CONTRACT","contract_id":"urn:unsupported","contract_version":"0.2"}}))
    run("NEGATIVE-STALE", lambda p,v: suffix(v,"complete-negative-evidence").update({"verification_time":"2025-01-01T00:00:00Z"}))
    run("NEGATIVE-RETENTION", lambda p,v: suffix(v,"complete-negative-evidence").update({"retention_window_seconds":0}))
    run("NEGATIVE-MISSING-RETENTION", lambda p,v: suffix(v,"complete-negative-evidence").pop("retention_window_seconds"))
    run("NEGATIVE-INCOMPLETE", lambda p,v: suffix(v,"complete-negative-evidence").update({"read_scope_complete":False}))
    run("NEGATIVE-CONSISTENCY", lambda p,v: suffix(v,"complete-negative-evidence").update({"consistency_level":"EVENTUAL"}))
    run("NEGATIVE-SOURCE", lambda p,v: suffix(v,"complete-negative-evidence").update({"evidence_class":"UNTRUSTED"}))
    run("NEGATIVE-INTERVAL", lambda p,v: suffix(v,"complete-negative-evidence")["observed_interval"].update({"not_before":"2025-01-01T00:00:00Z"}))
    run("NEGATIVE-CONTRADICTION", lambda p,v: suffix(v,"complete-negative-evidence")["evidence_universe"].append({"evidence_id":"positive","evidence_class":"RECEIPT","admissible":True,"effect_id":"urn:moirae:effect:v013","predicate_id":"urn:accord:02c:predicate:external-effect","stage":"effect","proposition":"POSITIVE"}))
    run("PARTIAL-SUPPORTED-TARGET", lambda p,v: suffix(v,"partial-effect-policy").update({"target_already_supported":"PARTIAL_EFFECT"}))
    run("PARTIAL-UNSUPPORTED-PREDECESSOR", lambda p,v: next(x for x in suffix(v,"predicate-registry")["entries"] if x["predicate_id"].endswith("recipient-ack"))["predecessor_edges"].__setitem__(0,{"predicate_id":"urn:accord:02c:predicate:resource-visible","stage":"resource_visible"}))
    return cases


def main():
    package, values = load_candidate()
    errors, metrics = verify(package, values)
    cases = mutations(package, values)
    report = {"candidate":"ACCORD-02E4R3", "status":"PASS" if not errors and all(x["detected"] for x in cases) else "FAIL", "errors":errors, "metrics":{k:v for k,v in metrics.items() if k != "blocking_traces"}, "mutations":{"total":len(cases),"detected":sum(x["detected"] for x in cases),"cases":cases}}
    save("accord-02e4r3-rule-execution-trace.json", {"blocking_rules": metrics["blocking_traces"], "count": len(metrics["blocking_traces"])})
    save("accord-02e4r3-adversarial-mutation-report.json", report["mutations"])
    save("accord-02e4r3-closure-certification.json", report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
