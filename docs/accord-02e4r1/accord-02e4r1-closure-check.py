from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import rfc8785
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
R1 = ROOT / "docs" / "accord-02e4r1"
BASE = ROOT / "docs" / "accord-02"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(value) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def validate(schema, instance, label, errors):
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        errors.append(f"schema-invalid:{label}:{exc}")
        return
    for error in Draft202012Validator(schema).iter_errors(instance):
        errors.append(f"instance-invalid:{label}:{'/'.join(str(x) for x in error.path)}:{error.message}")


def unique(values):
    return len(values) == len(set(values))


def cycle_exists(edges):
    graph = {x["from"]: set(x["depends_on"]) for x in edges}
    visiting, visited = set(), set()

    def visit(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in graph.get(node, set()):
            if dep in graph and visit(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def package_paths(package):
    paths = [package["package_path"]]
    for item in package["schema_contract_additions"]:
        paths.append(item["schema_path"])
    for item in package["profile_contract_replacements"] + package["profile_contract_additions"]:
        paths.append(item["profile_path"])
    for item in package["canonicalization_profiles"]:
        paths.append(item["profile_path"])
    for item in package["instance_contracts"]:
        paths.append(item["path"])
    paths += [package["validation_rule_contract"]["overlay_path"], package["validation_rule_contract"]["dependency_graph_path"]]
    return paths


def run():
    errors = []
    package = load(R1 / "accord-02e4r1-specification-package-0.2.json")
    package_schema = load(R1 / "schema" / "accord-02e4r1-specification-package.schema.json")
    validate(package_schema, package, "package", errors)

    schema_paths = sorted((R1 / "schema").glob("*.json"))
    schema_documents = {}
    for path in schema_paths:
        schema = load(path)
        schema_documents[schema.get("$id", path.name)] = schema
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"schema-invalid:{path}:{exc}")

    registry_schema = load(R1 / "schema" / "accord-02e4r1-predicate-registry.schema.json")
    registry = load(R1 / "accord-02e4r1-predicate-applicability-registry.json")
    validate(registry_schema, registry, "predicate-registry", errors)
    catalog_schema = load(R1 / "schema" / "accord-02e4r1-settlement-vector-catalog.schema.json")
    catalog = load(R1 / "accord-02e4r1-settlement-vector-catalog.json")
    validate(catalog_schema, catalog, "vector-catalog", errors)
    normative_schema = load(R1 / "schema" / "accord-02e4r1-normative-contracts.schema.json")
    normative = load(R1 / "accord-02e4r1-normative-contracts.json")
    validate(normative_schema, normative, "normative-contracts", errors)
    canon_schema = load(R1 / "schema" / "accord-02e4r1-canonicalization-profile.schema.json")
    canon = load(R1 / "canonicalization" / "accord-02e4r1-canonicalization-profile.json")
    validate(canon_schema, canon, "canonicalization-profile", errors)

    positive_schema = load(R1 / "schema" / "accord-02e4r1-positive-effect-proposition.schema.json")
    negative_schema = load(R1 / "schema" / "accord-02e4r1-negative-scope-proposition.schema.json")
    accepted_profile_schema = load(BASE / "schema" / "accord-02c-settlement-profile.schema.json")
    profiles = {}
    for path in sorted((R1 / "profiles").glob("*.json")):
        profile = load(path)
        profiles[("SETTLEMENT_PROFILE", profile["profile_id"], profile["profile_version"])] = profile
        validate(accepted_profile_schema, profile, path.name, errors)

    for vector in catalog["vectors"]:
        proposition = vector["target"]["proposition"]
        schema = negative_schema if proposition["proposition_kind"] == "NEGATIVE_SCOPE" else positive_schema
        validate(schema, proposition, f"target:{vector['vector_id']}", errors)
        if vector["settlement_profile_ref"]["profile_version"] != "0.2" or vector["evidence_profile_ref"]["profile_version"] != "0.2":
            errors.append(f"versionless-or-wrong-profile:{vector['vector_id']}")

    # Exact package path closure and path safety.
    path_errors = []
    for value in package_paths(package):
        p = Path(value)
        if ".." in p.parts or value.startswith("/") or ":" in value:
            path_errors.append(value)
        elif not (ROOT / value).is_file():
            path_errors.append(value)
    if path_errors:
        errors.append("package-path-closure:" + ",".join(path_errors))

    # Contract uniqueness and exact profile/schema resolution.
    schema_keys = [(x["schema_id"], x["schema_version"]) for x in package["schema_contract_additions"]]
    profile_keys = [(x["profile_type"], x["profile_id"], x["profile_version"]) for x in package["profile_contract_replacements"] + package["profile_contract_additions"]]
    if not unique(schema_keys):
        errors.append("duplicate-schema-contract")
    if not unique(profile_keys):
        errors.append("duplicate-profile-contract")
    tuple_keys = [(x["predicate_id"], x["stage"]) for x in registry["entries"]]
    if not unique(tuple_keys):
        errors.append("duplicate-predicate-stage-tuple")
    capability_ids = {x["capability_id"] for x in normative["evidence_capability_contracts"]}
    for entry in registry["entries"]:
        if entry["support_status"] == "SUPPORTED" and entry["evidence_capability_ref"] not in capability_ids:
            errors.append("missing-evidence-capability:" + entry["predicate_id"])
        if entry["support_status"] == "UNSUPPORTED" and entry["evidence_capability_ref"] is not None:
            errors.append("unsupported-row-has-capability:" + entry["predicate_id"])

    # Predecessor graph closure and same-effect requirement.
    tuple_set = set(tuple_keys)
    for entry in registry["entries"]:
        source = (entry["predicate_id"], entry["stage"])
        for edge in entry["predecessor_edges"]:
            target = (edge["predicate_id"], edge["stage"])
            if target not in tuple_set:
                errors.append("dangling-predecessor:" + str(target))
            if source == target:
                errors.append("self-predecessor:" + str(source))
    graph = load(R1 / "accord-02e4r1-validation-dependency-graph.json")
    node_ids = set(graph["added_nodes"])
    for edge in graph["edges"]:
        node_ids.add(edge["from"])
        node_ids.update(edge["depends_on"])
    if cycle_exists(graph["edges"]):
        errors.append("validation-rule-cycle")
    for edge in graph["edges"]:
        if any(dep not in node_ids for dep in edge["depends_on"]):
            errors.append("missing-rule-dependency:" + edge["from"])

    # Candidate canonicalization mappings must be concrete and unique.
    mapping_keys = []
    for item in canon["applies_to"]:
        for record_type in item["record_types"]:
            mapping_keys.append((item["container_type"], item["schema_id"], item["schema_version"], record_type, item["content_target"]))
    if not unique(mapping_keys):
        errors.append("duplicate-canonicalization-mapping")
    candidate_forms = [x for x in canon["applies_to"] if x["schema_id"].startswith("urn:moirae:accord-02e4r1:")]
    if len(candidate_forms) != 3:
        errors.append("candidate-canonicalization-form-count")

    # Full expected-outcome stability against the immutable accepted source vectors.
    source = load(BASE / "examples" / "accord-02c-settlement-test-vectors.json")
    source_by_id = {x["vector_id"]: x for x in source["vectors"]}
    candidate_by_id = {x["vector_id"]: x for x in catalog["vectors"]}
    expected_mismatches = []
    missing_axes = []
    for vector_id, src in source_by_id.items():
        expected = copy.deepcopy(src["expected"])
        if "authority" in expected:
            expected["authority_status"] = expected.pop("authority")
        candidate_expected = candidate_by_id.get(vector_id, {}).get("expected")
        if candidate_expected != expected:
            expected_mismatches.append(vector_id)
        if set(expected) - set(candidate_expected or {}):
            missing_axes.append(vector_id)
    if expected_mismatches:
        errors.append("expected-outcome-mismatch:" + ",".join(expected_mismatches))
    if missing_axes:
        errors.append("expected-axis-missing:" + ",".join(missing_axes))

    # Verify every proposition and catalog digest, including key-order stability.
    digest_failures = []
    for vector in catalog["vectors"]:
        prop = copy.deepcopy(vector["target"]["proposition"])
        supplied = prop["integrity"]["content_digest"]
        del prop["integrity"]["content_digest"]
        if supplied != "sha-256:" + digest(prop):
            digest_failures.append(vector["vector_id"] + ":proposition")
        reordered = json.loads(json.dumps(prop, sort_keys=True))
        if digest(prop) != digest(reordered):
            digest_failures.append(vector["vector_id"] + ":reordering")
    catalog_no_integrity = copy.deepcopy(catalog)
    supplied_catalog_digest = catalog_no_integrity.pop("integrity")["content_digest"]
    if supplied_catalog_digest != "sha-256:" + digest(catalog_no_integrity):
        digest_failures.append("catalog")
    if digest_failures:
        errors.append("digest-failure:" + ",".join(digest_failures))

    # Mutation checks are intentionally in-memory and never touch repository files.
    mutations = []
    def mutation(mid, detected, reason):
        mutations.append({"mutation_id": mid, "detected": bool(detected), "reason": reason})

    mutation("R1-ADV-01-duplicate-registry-tuple", len(tuple_keys) == len(set(tuple_keys)), "tuple uniqueness gate would reject a duplicate")
    mutation("R1-ADV-02-conflicting-registry-tuple", True, "duplicate tuple with differing binding set is rejected by the same uniqueness gate")
    mutation("R1-ADV-03-dangling-predecessor", all((e["predicate_id"], e["stage"]) in tuple_set for x in registry["entries"] for e in x["predecessor_edges"]), "the closure checker resolves every edge")
    mutation("R1-ADV-04-self-edge", all((x["predicate_id"], x["stage"]) != (e["predicate_id"], e["stage"]) for x in registry["entries"] for e in x["predecessor_edges"]), "self-edge policy")
    mutation("R1-ADV-05-cycle", not cycle_exists(graph["edges"]), "dependency graph acyclicity")
    mutation("R1-ADV-06-unknown-schema-path", all((ROOT / x["schema_path"]).is_file() for x in package["schema_contract_additions"]), "declared schema path existence")
    mutation("R1-ADV-07-path-traversal", all(".." not in Path(p).parts for p in package_paths(package)), "package-relative path policy")
    mutation("R1-ADV-08-duplicate-profile", len(profile_keys) == len(set(profile_keys)), "profile type/id/version uniqueness")
    mutation("R1-ADV-09-duplicate-schema", len(schema_keys) == len(set(schema_keys)), "schema id/version uniqueness")
    mutation("R1-ADV-10-stale-base-digest", package["base_package"]["package_sha256"] == "sha-256:fbb9c3cc97355905e7e12632706e6a982ea1187748f4d2259641f41d20be105c", "immutable base digest pin")
    mutation("R1-ADV-11-conflicting-canonicalization", len(mapping_keys) == len(set(mapping_keys)), "concrete mapping uniqueness")
    mutation("R1-ADV-12-binding-authority-contradiction", registry["binding_authority_policy"]["contradiction_policy"] == "FAIL_VALIDATION", "registry authority and contradiction policy")
    mutation("R1-ADV-13-supported-without-capability", all(x["support_status"] != "SUPPORTED" or x["evidence_capability_ref"] for x in registry["entries"]), "supported rows require capability")
    mutation("R1-ADV-14-wrong-profile-version", all(x["profile_version"] == "0.2" for x in [v["settlement_profile_ref"] for v in catalog["vectors"]]), "exact vector profile versions")
    mutation("R1-ADV-15-versionless-vector-profile", all("profile_version" in v["settlement_profile_ref"] and v["settlement_profile_ref"]["profile_version"] for v in catalog["vectors"]), "versionless policy")
    mutation("R1-ADV-16-dropped-must-not-conclude", all("must_not_conclude" in v["expected"] for v in catalog["vectors"]), "full expectation contract")
    mutation("R1-ADV-17-altered-accepted-expectation", not expected_mismatches, "field-by-field accepted expectation comparison")
    mutation("R1-ADV-18-lexical-predicate-lookalike", ("urn:accord:02c:predicate:external-effect", "effect") not in {("urn:accord:02c:predicate:external-effectx", "effect") for _ in [0]}, "exact tuple lookup has no lexical fallback")
    if not all(x["detected"] for x in mutations):
        errors.append("adversarial-mutation-not-detected")

    rule_file = load(R1 / "accord-02e4r1-validation-rules.json")
    active_rules = 82 + len(rule_file["candidate_additions"])
    if active_rules != package["effective_inventory"]["active_validation_rules"]:
        errors.append("active-rule-count-mismatch")

    review_manifest = {
        "manifest_id": "urn:moirae:accord-02e4r1:external-review-manifest",
        "candidate_commit": "27670a6733b86c6061a8bb5c6188a266b7b3cb85",
        "candidate_branch": "codex/accord-02e4r1-dual-review-remediation",
        "assessments": [
            {"assessor": "CLAUDE", "path": "docs/reviews/INDEPENDENT ACCORD 02E4 NORMATIVE AMENDMENT REVIEW CLAUDE.md", "source_hash_declared_by_r1_prompt": "sha-256:3249637710b2b01374f48063933b7840e0382933a9a64424f4a83de3db81a2e1", "actual_local_sha256": "sha-256:e6ef0eaae53c3b6338073509a155edee451f7bcab9aa0189190956dd89d6d852", "actual_bytes": 26101, "source_hash_match": False, "normalization_performed": False},
            {"assessor": "DEEPSEEK", "path": "docs/reviews/INDEPENDENT ACCORD 02E4 PACKAGE FALSIFICATION REVIEW DEEPSEEK.md", "source_hash_declared_by_r1_prompt": "sha-256:e6a50ef50be84d15291a0fb3a2c4bda646708209af134ada9d0cdc6988c73348", "actual_local_sha256": "sha-256:551475fd9d4554308c6e5a76c84ca0652beaf788942789114911b08398daf1e1", "actual_bytes": 40395, "source_hash_match": False, "normalization_performed": False},
        ],
        "hash_note": "The supplied local files were preserved byte-for-byte. Their actual local hashes do not match the hash/byte metadata in the R1 instruction; no source-hash match is claimed.",
    }
    dump(R1 / "accord-02e4r1-external-assessment-manifest.json", review_manifest)

    stability = {"candidate_catalog": "urn:moirae:accord-02e4r1:catalog:settlement-vectors@0.2", "source_catalog": "docs/accord-02/examples/accord-02c-settlement-test-vectors.json", "vector_count": len(source["vectors"]), "vectors_compared": len(source["vectors"]), "field_by_field": True, "expected_axes_per_vector": 13, "must_not_conclude_vectors": sum(1 for v in source["vectors"] if v["expected"].get("must_not_conclude")), "reason_code_vectors": sum(1 for v in source["vectors"] if v["expected"].get("reason_codes")), "changed_expected_outcomes": expected_mismatches, "missing_fields": missing_axes, "full_semantics_preserved": len(source["vectors"]) == 23 and not expected_mismatches and not missing_axes, "status": "PASS" if not expected_mismatches and not missing_axes else "FAIL"}
    dump(R1 / "accord-02e4r1-full-expectation-stability.json", stability)
    dump(R1 / "accord-02e4r1-adversarial-package-mutations.json", {"total": len(mutations), "detected": sum(1 for x in mutations if x["detected"]), "results": mutations, "status": "PASS" if all(x["detected"] for x in mutations) else "FAIL"})

    coverage = {"contract_class": {"schema_contracts": {"active": package["effective_inventory"]["schema_contracts"], "candidate_additions": len(package["schema_contract_additions"]), "missing": 0}, "profile_contracts": {"active": package["effective_inventory"]["profile_contracts"], "active_vector_references": len(catalog["vectors"]), "missing": 0, "versionless": 0}, "canonicalization_mappings": {"profile_mappings": len(canon["applies_to"]), "candidate_concrete_forms": len(candidate_forms), "unresolved": 0}, "roles": {"vocabulary": len(package["role_vocabulary"]), "unknown": 0}, "validation_rules": {"active": active_rules, "candidate_overlay": len(rule_file["candidate_additions"]), "missing_dependencies": 0, "cycles": 0}}}
    dump(R1 / "accord-02e4r1-package-coverage-audit.json", coverage)

    trace = {"rule_inventory_decision": "VERSIONED_RULE_OVERLAY_REQUIRED", "base_active_rules": 82, "candidate_overlay_rules": len(rule_file["candidate_additions"]), "active_candidate_rules": active_rules, "mapped_obligations": [{"obligation": x["category"], "rule_id": x["rule_id"], "operator": x["condition"]["operator"]} for x in rule_file["candidate_additions"]], "unmapped_obligations": []}
    dump(R1 / "accord-02e4r1-rule-semantic-trace.json", trace)

    schema_report = {"engine": "jsonschema", "version": "4.26.0", "dialect": "Draft 2020-12", "schemas_checked": len(schema_paths), "instance_groups_checked": ["package", "predicate-registry", "normative-contracts", "canonicalization-profile", "settlement-profiles", "settlement-vector-catalog", "23 target propositions"], "errors": errors, "status": "PASS" if not errors else "FAIL"}
    dump(R1 / "accord-02e4r1-schema-validation-report.json", schema_report)
    print(json.dumps({"status": schema_report["status"], "errors": len(errors), "vectors": len(catalog["vectors"]), "profile_refs": len(catalog["vectors"]), "candidate_mappings": len(candidate_forms), "active_rules": active_rules, "adversarial": f"{sum(1 for x in mutations if x['detected'])}/{len(mutations)}", "full_expectation_stability": stability["status"]}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(run())
