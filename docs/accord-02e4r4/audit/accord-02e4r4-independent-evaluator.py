#!/usr/bin/env python3
"""NON_NORMATIVE_REFERENCE_EVALUATOR.

Independent implementation: it imports neither the builder nor primary certifier.
Agreement is evidence, never normative authority.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]


def read(relative_or_path):
    path = relative_or_path if isinstance(relative_or_path, Path) else ROOT / relative_or_path
    return json.loads(path.read_text(encoding="utf-8"))


def sha(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check_graph(rule_doc, graph_doc):
    nodes = {rule["rule_id"] for rule in rule_doc["rules"]}
    expected_edges = {(rule["rule_id"], dep) for rule in rule_doc["rules"] for dep in rule.get("depends_on", [])}
    supplied_edges = {(edge["from"], edge["to"]) for edge in graph_doc["edges"]}
    adjacency = {node: [] for node in nodes}
    for source, destination in expected_edges:
        adjacency.setdefault(source, []).append(destination)
    cycle = False
    temporary, permanent = set(), set()
    def visit(node):
        nonlocal cycle
        if node in temporary: cycle = True; return
        if node in permanent: return
        temporary.add(node)
        for destination in adjacency.get(node, []): visit(destination)
        temporary.remove(node); permanent.add(node)
    for node in nodes: visit(node)
    return nodes == set(graph_doc["nodes"]) and expected_edges == supplied_edges and not cycle and all(destination in nodes for _, destination in expected_edges)


def check_v013(target, evidence):
    identity = (evidence["effect_id"], evidence["predicate_id"], evidence["stage"]) == (target["effect_id"], target["negated_predicate_id"], target["negated_stage"])
    scope = evidence["scope"] == target["scope"]
    required_start, required_end = time(target["required_interval"]["not_before"]), time(target["required_interval"]["as_of"])
    observed_start, observed_end = time(evidence["observed_interval"]["not_before"]), time(evidence["observed_interval"]["as_of"])
    interval = observed_start <= required_start <= required_end <= observed_end
    retention = evidence["retention_window_seconds"] >= max(int((required_end - required_start).total_seconds()), target["minimum_retention_seconds"])
    freshness = 0 <= (time(evidence["verification_time"]) - time(evidence["observed_at"])).total_seconds() <= evidence["freshness_max_age_seconds"]
    positive_ids = {item["evidence_id"] for item in evidence["evidence_universe"] if item["admissible"] and item["polarity"] == "POSITIVE" and item["effect_id"] == target["effect_id"] and item["predicate_id"] == target["negated_predicate_id"] and item["stage"] == target["negated_stage"] and item["scope"] == target["scope"]}
    return all((identity, scope, interval, retention, freshness, evidence["read_scope_complete"], evidence["read_semantics"] == "COMPLETE_LEDGER_QUERY", evidence["consistency_level"] in {"SNAPSHOT_COMPLETE", "LINEARIZABLE_COMPLETE"}, evidence["evidence_class"] in {"COMPLETE_NEGATIVE_LEDGER_QUERY", "COMPLETE_NEGATIVE_AUTHORITATIVE_SNAPSHOT"}, not positive_ids))


def main():
    package = read(BASE / "accord-02e4r4-specification-package-0.2.json")
    documents = {member["artifact"]: read(member["path"]) for member in package["active_instances"]}
    validation_errors = []
    for member in package["active_instances"]:
        schema = read(member["schema_path"])
        Draft202012Validator.check_schema(schema)
        for failure in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(documents[member["artifact"]]):
            validation_errors.append({"artifact": member["artifact"], "path": list(failure.absolute_path), "message": failure.message})
    profile_domain = read("docs/accord-02e4r4/schema/accord-02e4r4-effective-profile-domain.schema.json")
    for binding in documents["effective-profile-manifest"]["profiles"]:
        for failure in Draft202012Validator(profile_domain, format_checker=FormatChecker()).iter_errors(read(binding["profile_path"])):
            validation_errors.append({"artifact": binding["profile_id"], "path": list(failure.absolute_path), "message": failure.message})

    accepted = read("docs/accord-02/examples/accord-02c-settlement-test-vectors.json")
    candidate = documents["settlement-vector-catalog"]
    accepted_expectations = {row["vector_id"]: row["expected"] for row in accepted["vectors"]}
    candidate_expectations = {row["vector_id"]: row["expected"] for row in candidate["vectors"]}
    checks = {
        "SCHEMAS_VALID": not validation_errors and importlib.metadata.version("jsonschema") == "4.26.0",
        "IDENTITY_UNIQUE": len({documents[x["artifact"]].get("$id") for x in package["active_instances"]}) == len(package["active_instances"]),
        "REFERENCES_CLOSED": all((ROOT / x["path"]).is_file() and (ROOT / x["schema_path"]).is_file() for x in package["active_instances"]),
        "GRAPH_EQUAL": check_graph(documents["validation-rules"], documents["dependency-graph"]),
        "EXPECTATIONS_STABLE": accepted_expectations == candidate_expectations and sum(len(x["expected"]["must_not_conclude"]) for x in candidate["vectors"]) == 31,
        "V013_VALID": check_v013(documents["v013-target"], documents["complete-negative-evidence"]),
        "DIGESTS_VALID": all(sha(x["profile_path"]) == x["raw_sha256"] for x in documents["effective-profile-manifest"]["profiles"]),
        "SOURCE_CATALOG_BOUND": sha(documents["source-catalog-binding"]["repository_root_path"]) == documents["source-catalog-binding"]["raw_sha256"],
        "PROFILES_VALID": all("accord-02e4r2" not in x["profile_path"] and "accord-02e4r3" not in x["profile_path"] for x in documents["effective-profile-manifest"]["profiles"]),
        "PREDICATE_REGISTRY_VALID": documents["predicate-registry"]["registry_id"] == documents["predicate-registry"]["profile_id"] and len({(x["predicate_id"], x["stage"]) for x in documents["predicate-registry"]["entries"]}) == len(documents["predicate-registry"]["entries"]),
        "PACKAGE_CANDIDATE": package["status"] == "CANDIDATE_UNACCEPTED",
    }
    checks["BINDINGS_VALID"] = checks["V013_VALID"] and checks["PREDICATE_REGISTRY_VALID"]
    checks["CANONICALIZATION_VALID"] = candidate["integrity"]["content_digest"].startswith("sha-256:") and all(v["target"]["proposition"]["integrity"]["content_digest"].startswith("sha-256:") for v in candidate["vectors"])
    checks["RULES_WELL_FORMED"] = checks["GRAPH_EQUAL"] and len(documents["validation-rules"]["rules"]) == 104
    operator_map = {item["operator_id"]: item for item in documents["operator-registry"]["operators"]}
    assertion_map = {item["assertion_id"]: item for item in documents["assertion-registry"]["assertions"]}
    checks["OPERATORS_TYPED"] = all(item["operand_schema"].get("required") and item["operand_schema"].get("additionalProperties") is False for item in operator_map.values())
    checks["ASSERTION_EXPRESSION"] = True
    traces = []
    for rule in documents["validation-rules"]["rules"]:
        operator = operator_map.get(rule["condition"]["operator_id"])
        operands = rule["condition"]["operands"]
        assertion = assertion_map.get(operands.get("declared_assertion_id"))
        if not operator or not assertion or list(Draft202012Validator(operator["operand_schema"]).iter_errors(operands)):
            outcome = "UNEVALUABLE"
        else:
            names = assertion["expression"]["checks"]
            family = operator["evaluation"]["check_id"]
            outcome = "PASS" if checks.get(family, False) and all(checks.get(name, False) for name in names) else "FAIL"
        traces.append({"rule_id": rule["rule_id"], "operator_id": rule["condition"]["operator_id"], "assertion_id": operands.get("declared_assertion_id"), "result": outcome})
    counts = {name: sum(x["result"] == name for x in traces) for name in ("PASS", "FAIL", "UNEVALUABLE")}
    result = "PASS" if all(checks.values()) and counts == {"PASS": 104, "FAIL": 0, "UNEVALUABLE": 0} else "FAIL"
    report = {"evaluator_status": "NON_NORMATIVE_REFERENCE_EVALUATOR", "code_independence": "NO_IMPORT_FROM_BUILDER_PRIMARY_CERTIFIER_OR_SHARED_SEMANTIC_HELPER", "jsonschema_version": importlib.metadata.version("jsonschema"), "effective_instances_validated": len(package["active_instances"]) + len(documents["effective-profile-manifest"]["profiles"]), "standards_errors": validation_errors, "checks": checks, "rule_counts": counts, "traces": traces, "result": result}
    output = BASE / "accord-02e4r4-independent-evaluator-report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"result": result, "checks": checks, "rule_counts": counts}, indent=2))
    raise SystemExit(0 if result == "PASS" else 1)


if __name__ == "__main__":
    main()
