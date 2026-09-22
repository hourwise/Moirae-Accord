#!/usr/bin/env python3
"""Disposable negative-case falsifier for ACCORD-02E4R5R3.

Every case first runs an exact-environment baseline for both evaluators.  A
case whose baseline does not pass is reported INVALID_TEST_ENVIRONMENT.  A
mutation is only PASS when both evaluators reject it *and* the intended
invariant/binding fails with a compatible failure code (the reason oracle).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import rfc8785

REL = "docs/accord-02e4r5r3"
SOURCE_ROOT = Path(__file__).resolve().parents[3]
PRIMARY = REL + "/audit/certify_e4r5r3.py"
INDEPENDENT = REL + "/audit/independent_evaluate_e4r5r3.py"
FIXTURE = REL + "/audit/fixtures/external-trust-root.json"
PREDECESSORS = ["docs/accord-02e4r5", "docs/accord-02e4r5r1", "docs/accord-02e4r5r2"]


def jcs(value):
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8", newline="\n")


def rebind(root):
    """Recompute every candidate-local digest so failures stay attributable."""
    registry_path = Path(root) / REL / "object-registry.json"
    registry = read(registry_path)
    for entry in registry["objects"]:
        if entry.get("integrity", {}).get("mode") == "SEMANTIC_JSON_CONTENT":
            entry["integrity"]["digest"] = jcs(read(Path(root) / entry["path"]))
    write(registry_path, registry)
    package_path = Path(root) / REL / "specification-package-0.2.json"
    package = read(package_path)
    package["registry_semantic_sha256"] = jcs(registry)
    clone = copy.deepcopy(package)
    del clone["current_candidate_integrity"]["digest"]
    package["current_candidate_integrity"]["digest"] = jcs(clone)
    write(package_path, package)
    return package["current_candidate_integrity"]["digest"]


def edit(root, name, mutate):
    path = Path(root) / REL / name
    document = read(path)
    mutate(document)
    write(path, document)


def run(script, root, extra=()):
    process = subprocess.run(
        [sys.executable, str(Path(root) / script), "--root", str(root), *extra],
        capture_output=True, text=True, timeout=600,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    payload = None
    for line in reversed(process.stdout.strip().splitlines()):
        try:
            payload = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    return process.returncode, payload, process.stderr[-400:]


def external(root, trust_mode, baseline_digest):
    fixture = read(Path(root) / FIXTURE)
    package = read(Path(root) / REL / "specification-package-0.2.json")
    identity = fixture if trust_mode == "original" else {
        "package_id": package["package_id"],
        "package_version": package["package_version"],
        "package_digest": package["current_candidate_integrity"]["digest"],
    }
    kind = "REPLACED_TRUST_ROOT" if trust_mode == "replaced_root" else "PINNED_ACCEPTED_TRUST_ROOT"
    return ["--verification-input", json.dumps({
        "input_type": "EXTERNAL_VERIFICATION_INPUT",
        "package_id": identity["package_id"],
        "package_version": identity["package_version"],
        "package_digest": identity["package_digest"],
        "trust_root": {"root_id": "falsifier", "root_kind": kind}})]


def failures(report):
    """invariant id -> set of emitted failure codes / trust codes."""
    found = {}
    codes = report.get("invariant_failure_code_map", {})
    for scope in ("package_invariant_map", "governance_invariant_map"):
        for ident, status in report.get(scope, {}).items():
            if status != "PASS":
                found.setdefault(ident, set()).update(codes.get(ident, []))
    for key, status in report.get("binding_map", {}).items():
        if status != "PASS":
            ident = key.split("|")[0]
            found.setdefault(ident, set()).update(codes.get(ident, []))
    trust = report.get("trusted_package_identity", {})
    if trust.get("status") not in (None, "PASS"):
        ident = "TRUSTED_PACKAGE_IDENTITY"
        found.setdefault(ident, set())
        if trust.get("code"):
            found[ident].add(trust["code"])
    return found


CASES = []


def case(name, invariant, codes, trust_mode="recomputed"):
    def decorate(function):
        CASES.append({"name": name, "invariant": invariant, "codes": list(codes),
                      "trust_mode": trust_mode, "mutate": function})
        return function
    return decorate


CONTROLS = []


def control(name, judge=None):
    def decorate(function):
        CONTROLS.append({"name": name, "judge": judge, "prepare": function})
        return function
    return decorate


SOURCE_CODES = ["ACCORD-02R3-SOURCE-SCHEMA-NOT-PERMITTED",
                "ACCORD-02R3-SOURCE-FILENAME-NOT-AUTHORITY"]


@case("WRONG_SOURCE_PATH", "SOURCE_CATALOG_BINDING", SOURCE_CODES)
def _(root, _baseline):
    edit(root, "source-catalog-binding.json",
         lambda d: d["candidate_binding"].update(repository_root_path="docs/accord-02/nope.json"))


@case("REDIRECT_TO_PACKAGE", "SOURCE_CATALOG_BINDING", SOURCE_CODES)
def _(root, _baseline):
    package_path = "docs/accord-02/accord-02r5-specification-package.json"
    payload = (Path(root) / package_path).read_bytes()
    semantic = jcs(json.loads(payload))
    raw = hashlib.sha256(payload).hexdigest()
    edit(root, "source-catalog-binding.json",
         lambda d: d["candidate_binding"].update(
             repository_root_path=package_path,
             semantic_json_content_sha256=semantic,
             raw_file_bytes_sha256=raw))


@case("WRONG_SOURCE_IDENTITY", "SOURCE_CATALOG_BINDING", SOURCE_CODES)
def _(root, _baseline):
    edit(root, "source-catalog-binding.json",
         lambda d: d["candidate_binding"].update(assigned_id="urn:moirae:accord-02r5:not-the-catalog"))


@case("WRONG_SOURCE_SEMANTIC_MAPPING", "SOURCE_CATALOG_BINDING", SOURCE_CODES)
def _(root, _baseline):
    edit(root, "source-catalog-binding.json",
         lambda d: d["candidate_binding"].update(declared_canonicalization="NONE"))


@case("CORRUPT_CANDIDATE_BINDING_DIGEST", "SOURCE_CATALOG_BINDING", SOURCE_CODES)
def _(root, _baseline):
    edit(root, "source-catalog-binding.json",
         lambda d: d["candidate_binding"].update(semantic_json_content_sha256="0" * 64))


@case("NONEXISTENT_SOURCE_PATH", "SOURCE_CATALOG_BINDING", SOURCE_CODES)
def _(root, _baseline):
    edit(root, "source-catalog-binding.json",
         lambda d: d["candidate_binding"].update(
             repository_root_path="docs/accord-02/absent-catalog.json"))


@case("MISSING_ADMISSIBLE", "NEGATIVE_REQUIREMENT_MAP_CLOSURE",
      ["NEGATIVE_UNIVERSE_UNTYPED", "NEGATIVE_REQUIREMENT_MAP_FAILURE"])
def _(root, _baseline):
    edit(root, "v013-evidence.json",
         lambda d: d["evidence_universe"][0].pop("admissible"))


@case("UNSUPPORTED_INTEGRITY_MODE", "INTEGRITY_MODE_DISPATCH",
      ["INTEGRITY_MODE_DISPATCH_FAILURE"])
def _(root, _baseline):
    def mutate(d):
        for entry in d["objects"]:
            if entry["kind"] == "REGISTRY" and entry["integrity"]["mode"] == "SEMANTIC_JSON_CONTENT":
                entry["integrity"]["mode"] = "NOT_A_DECLARED_MODE"
                return
    edit(root, "object-registry.json", mutate)


@case("UNDECLARED_DERIVATION_ROLE", "DERIVATION_ROLE_CLOSURE",
      ["DERIVATION_ROLE_CLOSURE_FAILURE"])
def _(root, _baseline):
    def mutate(d):
        for procedure in d["procedures"]:
            if procedure["procedure_id"] == "SET_EQUALITY":
                procedure["derivation"]["left"]["source"] = "rogue_role:/dependency_edges/*"
    edit(root, "procedure-registry.json", mutate)


@case("FAIL_CLOSED_FALSE", "FAIL_CLOSED_ENFORCED", ["FAIL_CLOSED_ENFORCED_FAILURE"])
def _(root, _baseline):
    edit(root, "invariant-registry.json",
         lambda d: d["invariants"][0].update(fail_closed=False))


@case("MISSING_BEHAVIOR", "MISSING_BEHAVIOR_SUPPORTED",
      ["MISSING_BEHAVIOR_SUPPORTED_FAILURE"])
def _(root, _baseline):
    edit(root, "procedure-registry.json",
         lambda d: d["procedures"][0].update(missing_behavior="IGNORE"))


@case("AMBIGUITY_BEHAVIOR", "AMBIGUITY_BEHAVIOR_SUPPORTED",
      ["AMBIGUITY_BEHAVIOR_SUPPORTED_FAILURE"])
def _(root, _baseline):
    edit(root, "procedure-registry.json",
         lambda d: d["procedures"][0].update(ambiguity_behavior="LAST_WRITE_WINS"))


@case("SUBJECT_ROLES", "SUBJECT_ROLE_COVERAGE", ["SUBJECT_ROLE_COVERAGE_FAILURE"])
def _(root, _baseline):
    edit(root, "invariant-registry.json",
         lambda d: d["invariants"][0].update(subject_roles=["undeclared_subject"]))


@case("DEFAULT_ARGUMENTS", "DEFAULT_ARGUMENT_COVERAGE",
      ["DEFAULT_ARGUMENT_COVERAGE_FAILURE"])
def _(root, _baseline):
    def mutate(d):
        first = d["invariants"][0]
        first["default_arguments"].pop(next(iter(first["default_arguments"])))
    edit(root, "invariant-registry.json", mutate)


@case("EMPTY_DISCOVERY_UNIVERSE", "REFERENCE_DISCOVERY_SCOPE_VALID",
      ["REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE"])
def _(root, _baseline):
    edit(root, "reference-model.json",
         lambda d: d["discovery_scope"].update(registry_status="RETIRED"))


@case("WIDENED_SHAPE_PREDICATE", "REFERENCE_SHAPE_PREDICATE_APPLIED",
      ["REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE"])
def _(root, _baseline):
    edit(root, "reference-model.json",
         lambda d: d["shape_predicate"].update(additional_keys="ALLOW"))


@case("WEAKENED_UNIQUENESS_KEY", "UNIQUENESS_KEY_APPLIED",
      ["UNIQUENESS_KEY_APPLIED_FAILURE"])
def _(root, _baseline):
    edit(root, "object-registry.json", lambda d: d.update(uniqueness_key=["id"]))


@case("ROLE_MODEL", "ROLE_MODEL_APPLIED", ["ROLE_MODEL_APPLIED_FAILURE"])
def _(root, _baseline):
    edit(root, "object-registry.json", lambda d: d.update(role_model="set-of-roles"))


@case("SCHEMA_ID_MISMATCH", "SCHEMA_IDENTITY_MATCHES_REGISTRY",
      ["SCHEMA_IDENTITY_MATCHES_REGISTRY_FAILURE"])
def _(root, _baseline):
    path = Path(root) / REL / "schema" / "v013-target.schema.json"
    document = read(path)
    document["$id"] = "urn:moirae:accord-02r5r3:schema:not-v013-target:0.2"
    write(path, document)


@case("DELETED_RULE", "RULE_COVERAGE_EXACT", ["RULE_COVERAGE_EXACT_FAILURE"])
def _(root, _baseline):
    edit(root, "rule-registry.json",
         lambda d: d.update(rules=[r for r in d["rules"] if r["rule_id"] != "LIN-001"]))


@case("EXTRA_RULE", "RULE_COVERAGE_EXACT", ["RULE_COVERAGE_EXACT_FAILURE"])
def _(root, _baseline):
    def mutate(d):
        clone = copy.deepcopy(next(r for r in d["rules"] if r["rule_id"] == "LIN-001"))
        clone["rule_id"] = "ZZZ-999"
        d["rules"].append(clone)
    edit(root, "rule-registry.json", mutate)


@case("DUPLICATE_GOVERNING_POLICY_DECLARATION", "GOVERNING_TOKEN_SINGLETON",
      ["GOVERNING_TOKEN_SINGLETON_FAILURE"])
def _(root, _baseline):
    edit(root, "authority-requirements.json",
         lambda d: d.update(shadow_stage_policy={"global_stage_order": "ALLOWED"}))


@case("FORGED_V013_BASIS", "V013_BASIS_VALID", ["V013_BASIS_VALID_FAILURE"])
def _(root, _baseline):
    edit(root, "v013-target.json",
         lambda d: d["relationship_basis"]["accepted"][0].update(
             must_equal="urn:accord:02c:effect:FORGED"))


@case("MISSING_V013_REQUIREMENT", "NEGATIVE_REQUIREMENT_MAP_CLOSURE",
      ["NEGATIVE_REQUIREMENT_MAP_FAILURE"])
def _(root, _baseline):
    def mutate(d):
        dropped = d["requirement_map"]["requirements"].pop()
        d["requirement_map"]["evaluation_order"] = [
            r for r in d["requirement_map"]["evaluation_order"]
            if r != dropped["requirement_id"]]
    edit(root, "v013-governance.json", mutate)


@case("DUPLICATE_REQUIREMENT_ID", "NEGATIVE_REQUIREMENT_MAP_CLOSURE",
      ["NEGATIVE_REQUIREMENT_MAP_FAILURE"])
def _(root, _baseline):
    edit(root, "v013-governance.json",
         lambda d: d["requirement_map"]["requirements"].append(
             copy.deepcopy(d["requirement_map"]["requirements"][0])))


@case("EVALUATION_ORDER_OMISSION", "NEGATIVE_REQUIREMENT_MAP_CLOSURE",
      ["NEGATIVE_REQUIREMENT_MAP_FAILURE"])
def _(root, _baseline):
    edit(root, "v013-governance.json",
         lambda d: d["requirement_map"].update(
             evaluation_order=d["requirement_map"]["evaluation_order"][:-1]))


@case("CONTRADICTION_COUNT_RELAXATION", "NEGATIVE_REQUIREMENT_MAP_CLOSURE",
      ["NEGATIVE_CALLER_SUPPLIED_COUNT_FORBIDDEN", "NEGATIVE_REQUIREMENT_MAP_FAILURE"])
def _(root, _baseline):
    edit(root, "v013-evidence.json",
         lambda d: d.update(caller_supplied_contradiction_count=0))
    path = Path(root) / REL / "schema" / "v013-evidence.schema.json"
    document = read(path)
    document["properties"]["caller_supplied_contradiction_count"] = {"type": "integer"}
    write(path, document)


@case("FUTURE_OBSERVATION_MUTATION", "NEGATIVE_REQUIREMENT_MAP_CLOSURE",
      ["NEGATIVE_REQUIREMENT_MAP_FAILURE"])
def _(root, _baseline):
    edit(root, "v013-evidence.json",
         lambda d: d.update(observed_at="2024-06-01T00:00:00Z"))


@case("CONTRADICTION_RULE_MUTATION", "NEGATIVE_REQUIREMENT_MAP_CLOSURE",
      ["NEGATIVE_REQUIREMENT_MAP_FAILURE"])
def _(root, _baseline):
    edit(root, "normative-inputs.json",
         lambda d: d["profile"]["negative_policy"].update(contradiction_rule="ALLOW"))


@case("DUPLICATE_PROPOSITION_ID", "PROPOSITION_INVENTORY_BOUND",
      ["PROPOSITION_INVENTORY_BOUND_FAILURE"])
def _(root, _baseline):
    edit(root, "proposition-inventory.json",
         lambda d: d["projection_propositions"][0].update(
             proposition_id=d["member_propositions"][0]["proposition_id"]))


@case("MISSING_PROPOSITION_ID", "PROPOSITION_INVENTORY_BOUND",
      ["PROPOSITION_INVENTORY_BOUND_FAILURE"])
def _(root, _baseline):
    edit(root, "proposition-inventory.json",
         lambda d: d.update(member_propositions=d["member_propositions"][1:]))


@case("INVARIANT_ACTIVE_REMOVED", "INVARIANT_SET_EXACT", ["INVARIANT_SET_EXACT_FAILURE"])
def _(root, _baseline):
    edit(root, "invariant-registry.json",
         lambda d: d.update(invariants=d["invariants"][1:]))


@case("COHERENT_REWRITE_ORIGINAL_TRUST_ROOT", "TRUSTED_PACKAGE_IDENTITY",
      ["TRUSTED_IDENTITY_MISMATCH"], trust_mode="original")
def _(root, _baseline):
    edit(root, "specification-package-0.2.json",
         lambda d: d.update(runtime={"python": ">=3.14", "requirements_path":
                                     d["runtime"]["requirements_path"]}))


@control("COHERENT_REWRITE_REPLACED_TRUST_ROOT")
def _(root, baseline):
    edit(root, "specification-package-0.2.json",
         lambda d: d.update(runtime={"python": ">=3.14", "requirements_path":
                                     d["runtime"]["requirements_path"]}))


@control("NO_EXTERNAL_TRUST_INPUT")
def _(root, baseline):
    pass


@control("SELF_DIGEST_FORMATTING_STABLE")
def _(root, baseline):
    path = Path(root) / REL / "rule-registry.json"
    path.write_text(json.dumps(read(path), separators=(",", ":")), encoding="utf-8")


@control("REFERENCE_DEDUPLICATION")
def _(root, baseline):
    edit(root, "authority-requirements.json",
         lambda d: d["governing_contract_refs"].update(
             dedup_fixture={"kind": "CANONICALIZATION",
                            "id": "urn:moirae:accord-02r5r3:canonicalization-profile",
                            "version": "0.2"}))


def judge_replaced_root(root, baseline):
    detail, okay = {}, True
    for label, script in (("primary", PRIMARY), ("independent", INDEPENDENT)):
        code, report, diag = run(script, root, external(root, "replaced_root", baseline))
        trust = (report or {}).get("trusted_package_identity", {})
        good = (code != 0 and trust.get("status") == "DIFFERENT_PACKAGE_VERIFIED"
                and trust.get("sub_status") == "OUT_OF_SCOPE_TRUST_ROOT_REPLACEMENT")
        detail[label] = {"status": trust.get("status"), "ok": good, "diagnostic": diag[:200]}
        okay = okay and good
    return okay, detail


def judge_no_external(root, baseline):
    detail, okay = {}, True
    for label, script in (("primary", PRIMARY), ("independent", INDEPENDENT)):
        code, report, diag = run(script, root, [])
        trust = (report or {}).get("trusted_package_identity", {})
        good = (code != 0 and trust.get("status") == "FAIL"
                and trust.get("code") == "MISSING_EXTERNAL_TRUST_INPUT"
                and (report or {}).get("internal_package_conformance") == "PASS")
        detail[label] = {"status": trust.get("status"), "code": trust.get("code"), "ok": good,
                         "diagnostic": diag[:200]}
        okay = okay and good
    return okay, detail


def judge_both_pass(root, baseline):
    detail, okay = {}, True
    for label, script in (("primary", PRIMARY), ("independent", INDEPENDENT)):
        code, report, diag = run(script, root, external(root, "recomputed", baseline))
        good = code == 0 and bool(report and report.get("overall_pass"))
        detail[label] = {"ok": good, "diagnostic": diag[:200]}
        okay = okay and good
    return okay, detail


CONTROL_JUDGES = {
    "COHERENT_REWRITE_REPLACED_TRUST_ROOT": judge_replaced_root,
    "NO_EXTERNAL_TRUST_INPUT": judge_no_external,
    "SELF_DIGEST_FORMATTING_STABLE": judge_both_pass,
    "REFERENCE_DEDUPLICATION": judge_both_pass,
}


def remove_tree(path):
    import stat as _stat

    def on_error(function, target, _exc):
        try:
            os.chmod(target, _stat.S_IWRITE)
            function(target)
        except Exception:
            pass

    shutil.rmtree(path, onerror=on_error)


def copy_export(destination, source_root=SOURCE_ROOT):
    shutil.copytree(source_root, destination,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".deps"))
    remove_tree(destination / ".git")
    for predecessor in PREDECESSORS:
        if (destination / predecessor).exists():
            remove_tree(destination / predecessor)


def run_case(case_row, export, pristine, baseline_digest):
    shutil.rmtree(export / REL)
    shutil.copytree(pristine, export / REL)
    case_row["mutate"](export, baseline_digest)
    rebind(export)
    args = external(export, case_row["trust_mode"], baseline_digest)
    detail, rejected = {}, True
    codes_seen = {}
    for label, script in (("primary", PRIMARY), ("independent", INDEPENDENT)):
        code, report, diag = run(script, export, args)
        report = report or {}
        failed = failures(report)
        codes_seen[label] = sorted({c for codes in failed.values() for c in codes})
        intended = case_row["invariant"] in failed
        code_hit = (not case_row["codes"]) or bool(set(case_row["codes"]) & failed.get(
            case_row["invariant"], set()))
        good = code != 0 and not report.get("overall_pass") and intended and code_hit
        detail[label] = {"rejected": code != 0 and not report.get("overall_pass"),
                         "failed_invariants": sorted(failed),
                         "intended_failed": intended, "code_ok": code_hit,
                         "diagnostic": diag[:200]}
        rejected = rejected and good
    return rejected, {"expected_invariant": case_row["invariant"],
                      "expected_codes": case_row["codes"],
                      "observed_codes": codes_seen, "detail": detail}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--report")
    parser.add_argument("--root", default=str(SOURCE_ROOT))
    args = parser.parse_args(argv)
    source_root = Path(args.root).resolve()
    results = {"baseline": {}, "mutation_cases": {}, "controls": {}}
    with tempfile.TemporaryDirectory(prefix="accord-e4r5r3-falsifier-") as tmp:
        temp = Path(tmp)
        export = temp / "export"
        copy_export(export, source_root)
        pristine = temp / "pristine-r5r3"
        shutil.copytree(export / REL, pristine)
        baseline_digest = read(export / REL / "specification-package-0.2.json")[
            "current_candidate_integrity"]["digest"]

        baseline_ok, baseline_detail = judge_both_pass(
            export, baseline_digest)
        results["baseline"] = {"passed": baseline_ok, "detail": baseline_detail}
        baseline_digest = read(export / REL / "specification-package-0.2.json")[
            "current_candidate_integrity"]["digest"]

        for row in CASES:
            if not baseline_ok:
                results["mutation_cases"][row["name"]] = {
                    "passed": False, "status": "INVALID_TEST_ENVIRONMENT",
                    "detail": baseline_detail}
                continue
            passed, detail = run_case(row, export, pristine, baseline_digest)
            results["mutation_cases"][row["name"]] = {"passed": passed, "detail": detail}

        for row in CONTROLS:
            if not baseline_ok:
                results["controls"][row["name"]] = {
                    "passed": False, "status": "INVALID_TEST_ENVIRONMENT"}
                continue
            shutil.rmtree(export / REL)
            shutil.copytree(pristine, export / REL)
            row["prepare"](export, baseline_digest)
            rebind(export)
            judge = row["judge"] or CONTROL_JUDGES[row["name"]]
            passed, detail = judge(export, baseline_digest)
            results["controls"][row["name"]] = {"passed": passed, "detail": detail}

    summary = {
        "baseline": results["baseline"]["passed"],
        "mutation_cases": len(results["mutation_cases"]),
        "mutation_pass": sum(v["passed"] for v in results["mutation_cases"].values()),
        "controls": len(results["controls"]),
        "control_pass": sum(v["passed"] for v in results["controls"].values()),
    }
    overall = (summary["baseline"] and summary["mutation_cases"] == summary["mutation_pass"]
               and summary["controls"] == summary["control_pass"])
    results["summary"] = summary
    results["overall_pass"] = overall
    public = {
        "baseline": results["baseline"],
        "mutation_cases": {k: v["passed"] for k, v in results["mutation_cases"].items()},
        "controls": {k: v["passed"] for k, v in results["controls"].items()},
        "failures": {k: v for k, v in results["mutation_cases"].items() if not v["passed"]},
        "control_failures": {k: v for k, v in results["controls"].items() if not v["passed"]},
        "summary": summary,
        "overall_pass": overall,
    }
    if args.report:
        Path(args.report).write_text(json.dumps(results, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(public, indent=2, sort_keys=True))
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
