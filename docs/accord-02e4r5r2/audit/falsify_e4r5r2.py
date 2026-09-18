#!/usr/bin/env python3
"""Disposable-export mutation and portability tests for ACCORD-02E4R5R2."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable

import rfc8785


HERE = Path(__file__).resolve()
SOURCE_ROOT = HERE.parents[3]
REL = Path("docs/accord-02e4r5r2")
PRIMARY = REL / "audit/certify_e4r5r2.py"
INDEPENDENT = REL / "audit/independent_evaluate_e4r5r2.py"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def digest(value: Any) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def package_digest(package: dict[str, Any]) -> str:
    candidate = copy.deepcopy(package)
    del candidate["current_candidate_integrity"]["digest"]
    return digest(candidate)


def rebind(root: Path, changed: list[str]) -> None:
    """Refresh declared semantic integrity after an intentional coherent rewrite."""
    base = root / REL
    registry_path = base / "object-registry.json"
    registry = read_json(registry_path)
    changed_paths = {str((REL / item).as_posix()) for item in changed}
    for entry in registry["objects"]:
        integrity = entry.get("integrity", {})
        if entry.get("path") in changed_paths and integrity.get("mode") == "SEMANTIC_JSON_CONTENT":
            integrity["digest"] = digest(read_json(root / entry["path"]))
    write_json(registry_path, registry)
    package_path = base / "specification-package-0.2.json"
    package = read_json(package_path)
    package["registry_semantic_sha256"] = digest(registry)
    package["current_candidate_integrity"]["digest"] = package_digest(package)
    write_json(package_path, package)


def alter(root: Path, name: str, edit: Callable[[Any], None], coherent: bool = True) -> None:
    path = root / REL / name
    value = read_json(path)
    edit(value)
    write_json(path, value)
    if coherent:
        rebind(root, [name])


def run_evaluator(root: Path, script: Path) -> tuple[int, dict[str, Any] | None, str]:
    env = dict(os.environ)
    process = subprocess.run(
        [sys.executable, str(root / script)],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
    )
    output = process.stdout.strip()
    parsed = None
    if output:
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            pass
    return process.returncode, parsed, (process.stderr.strip() or output[-1000:])


def both_fail(root: Path) -> tuple[bool, dict[str, Any]]:
    detail: dict[str, Any] = {}
    passed = True
    for label, script in (("primary", PRIMARY), ("independent", INDEPENDENT)):
        code, value, diagnostic = run_evaluator(root, script)
        rejected = code != 0 or not value or not value.get("overall_pass", False)
        detail[label] = {"exit": code, "rejected": rejected, "diagnostic": diagnostic[:300]}
        passed &= rejected
    return passed, detail


def both_pass(root: Path) -> tuple[bool, dict[str, Any]]:
    detail: dict[str, Any] = {}
    passed = True
    for label, script in (("primary", PRIMARY), ("independent", INDEPENDENT)):
        code, value, diagnostic = run_evaluator(root, script)
        accepted = code == 0 and bool(value and value.get("overall_pass", False))
        detail[label] = {"exit": code, "accepted": accepted, "diagnostic": diagnostic[:300]}
        passed &= accepted
    return passed, detail


def first_by(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    return next(item for item in items if item.get(key) == value)


def export_source(destination: Path) -> None:
    shutil.copytree(
        SOURCE_ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", ".deps", "__pycache__", "*.pyc"),
    )


def reset_candidate(export: Path, baseline: Path) -> None:
    target = export / REL
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(baseline, target)
    for accepted in ("docs/accord-02/accord-02r5-specification-package.json", "docs/accord-02/examples/accord-02c-settlement-test-vectors.json"):
        (export / accepted).write_bytes((SOURCE_ROOT / accepted).read_bytes())
    for predecessor in ("docs/accord-02e4r5", "docs/accord-02e4r5r1"):
        source = SOURCE_ROOT / predecessor
        target_predecessor = export / predecessor
        if target_predecessor.exists():
            shutil.rmtree(target_predecessor)
        if source.exists():
            shutil.copytree(source, target_predecessor)


def main() -> int:
    mutation_cases: list[tuple[str, Callable[[Path], None]]] = []
    controls: list[tuple[str, Callable[[Path], None], Callable[[Path], tuple[bool, dict[str, Any]]]]] = []

    def mutation(name: str):
        def decorate(function: Callable[[Path], None]):
            mutation_cases.append((name, function))
            return function
        return decorate

    def control(name: str, judge: Callable[[Path], tuple[bool, dict[str, Any]]] = both_pass):
        def decorate(function: Callable[[Path], None]):
            controls.append((name, function, judge))
            return function
        return decorate

    @mutation("SELF_DIGEST_BLANK_FIELD")
    def _(root: Path) -> None:
        alter(root, "specification-package-0.2.json", lambda d: d["current_candidate_integrity"].update(digest=""), False)

    @mutation("SELF_DIGEST_NULL_FIELD")
    def _(root: Path) -> None:
        alter(root, "specification-package-0.2.json", lambda d: d["current_candidate_integrity"].update(digest=None), False)

    @mutation("SELF_DIGEST_SEMANTIC_CHANGE")
    def _(root: Path) -> None:
        alter(root, "specification-package-0.2.json", lambda d: d.update(status="ALTERED"), False)

    @mutation("REFERENCE_DANGLING")
    def _(root: Path) -> None:
        alter(root, "authority-requirements.json", lambda d: d.update(falsifier_ref={"kind": "CONTRACT", "id": "urn:missing", "version": "0.2"}))

    @mutation("REFERENCE_AMBIGUOUS_TARGET")
    def _(root: Path) -> None:
        def edit(d: dict[str, Any]) -> None:
            item = copy.deepcopy(first_by(d["objects"], "id", "urn:moirae:accord-02r5r2:reference-model"))
            d["objects"].append(item)
        alter(root, "object-registry.json", edit)

    @mutation("PACKAGE_CURRENT_UNREGISTERED")
    def _(root: Path) -> None:
        alter(root, "object-registry.json", lambda d: d.update(objects=[x for x in d["objects"] if not (x["kind"] == "PACKAGE" and x["version"] == "0.2")]))

    @mutation("PACKAGE_REJECTED_PREDECESSOR_REACTIVATED")
    def _(root: Path) -> None:
        def edit(d: dict[str, Any]) -> None:
            d["objects"].append({"kind":"PACKAGE","id":"urn:moirae:accord-02r5:specification-package","version":"0.2","path":"docs/accord-02e4r5/specification-package-0.2.json","status":"ACTIVE","roles":["NORMATIVE"],"classification":"NORMATIVE","integrity":{"mode":"JUSTIFIED_EXEMPTION","reason":"falsifier"}})
        alter(root, "object-registry.json", edit)

    @mutation("PACKAGE_TWO_ACTIVE_IDENTITIES")
    def _(root: Path) -> None:
        def edit(d: dict[str, Any]) -> None:
            item = copy.deepcopy(first_by(d["objects"], "id", "urn:moirae:accord-02r5:specification-package"))
            item["version"] = "0.2"
            item["status"] = "ACTIVE"
            d["objects"].append(item)
        alter(root, "object-registry.json", edit)

    def edit_conformance(root: Path, edit: Callable[[dict[str, Any]], None]) -> None:
        def apply(d: dict[str, Any]) -> None:
            edit(next(r for r in d["rules"] if r["declared_class"] == "EXECUTABLE_CONFORMANCE_RULE"))
        alter(root, "rule-registry.json", apply)

    @mutation("BINDING_ARGUMENT_REDIRECTED")
    def _(root: Path) -> None:
        edit_conformance(root, lambda r: r["invariant_binding"]["arguments"].update(registry={"kind":"REGISTRY","id":"urn:moirae:accord-02r5r2:rule-registry","version":"0.2"}))

    @mutation("BINDING_REQUIRED_ROLE_REMOVED")
    def _(root: Path) -> None:
        edit_conformance(root, lambda r: r["invariant_binding"]["arguments"].pop(next(iter(r["invariant_binding"]["arguments"]))))

    @mutation("BINDING_WRONG_KIND")
    def _(root: Path) -> None:
        edit_conformance(root, lambda r: next(iter(r["invariant_binding"]["arguments"].values())).update(kind="SCHEMA"))

    @mutation("BINDING_UNRELATED_INVARIANT_RETARGET")
    def _(root: Path) -> None:
        edit_conformance(root, lambda r: r["invariant_binding"].update(invariant_id="PREDICATE_AUTHORITY_CLOSURE"))

    @mutation("BINDING_FAILURE_CODE_MISMATCH")
    def _(root: Path) -> None:
        edit_conformance(root, lambda r: r.update(inherited_failure_code="UNRELATED_FAILURE"))

    @mutation("CLASSIFICATION_CONFORMANCE_20_TO_DEFERRED")
    def _(root: Path) -> None:
        def edit(d: dict[str, Any]) -> None:
            rows = [r for r in d["rules"] if r["declared_class"] == "EXECUTABLE_CONFORMANCE_RULE"][:20]
            for row in rows:
                row["declared_class"] = "DEFERRED_NO_SUBJECT_ARTIFACT"
        alter(root, "rule-registry.json", edit)

    @mutation("CLASSIFICATION_INTERNAL_TO_CONFORMANCE")
    def _(root: Path) -> None:
        alter(root, "rule-registry.json", lambda d: next(r for r in d["rules"] if r["declared_class"] == "INTERNAL_DESIGN_INVARIANT").update(declared_class="EXECUTABLE_CONFORMANCE_RULE"))

    @mutation("CLASSIFICATION_DEFERRED_TO_CONFORMANCE")
    def _(root: Path) -> None:
        alter(root, "rule-registry.json", lambda d: next(r for r in d["rules"] if r["declared_class"] == "DEFERRED_NO_SUBJECT_ARTIFACT").update(declared_class="EXECUTABLE_CONFORMANCE_RULE"))

    @mutation("INVARIANT_ACTIVE_REMOVED")
    def _(root: Path) -> None:
        alter(root, "invariant-registry.json", lambda d: d.update(invariants=d["invariants"][1:]))

    @mutation("INVARIANT_UNDECLARED_REQUIRED")
    def _(root: Path) -> None:
        alter(root, "specification-package-0.2.json", lambda d: d["required_invariant_ids"].append("UNDECLARED_INVARIANT"), False)

    @mutation("INVARIANT_PROCEDURE_CHANGED")
    def _(root: Path) -> None:
        alter(root, "invariant-registry.json", lambda d: d["invariants"][0].update(procedure_id="LINEAGE_VALIDATION"))

    @mutation("INVARIANT_INPUT_ROLE_REMOVED")
    def _(root: Path) -> None:
        alter(root, "invariant-registry.json", lambda d: d["invariants"][0].update(input_roles=d["invariants"][0]["input_roles"][1:]))

    @mutation("INVARIANT_ARITY_MISMATCH")
    def _(root: Path) -> None:
        alter(root, "procedure-registry.json", lambda d: d["procedures"][0]["arguments"].append({"name":"extra","kind":"CONTRACT","required":True,"cardinality":"ONE"}))

    @mutation("INVARIANT_FAIL_CLOSED_FALSE")
    def _(root: Path) -> None:
        alter(root, "invariant-registry.json", lambda d: d["invariants"][0].update(fail_closed=False))

    @mutation("INVARIANT_STATUS_RETIRED")
    def _(root: Path) -> None:
        alter(root, "invariant-registry.json", lambda d: d["invariants"][0].update(status="RETIRED"))

    @mutation("PROCEDURE_PROJECTION_CHANGED")
    def _(root: Path) -> None:
        def edit(d: dict[str, Any]) -> None:
            procedure = next(p for p in d["procedures"] if p["procedure_id"] == "SET_EQUALITY")
            procedure["derivation"]["left"]["projection"] = ["rule_id", "wrong_edges/*"]
        alter(root, "procedure-registry.json", edit)

    @mutation("POLICY_GOVERNED_ONLY")
    def _(root: Path) -> None:
        alter(root, "normative-inputs.json", lambda d: d["predicate_policy"].update(global_stage_order="ALLOWED"))

    @mutation("POLICY_AUTHORITY_ONLY")
    def _(root: Path) -> None:
        alter(root, "authority-requirements.json", lambda d: d["stage_policy_requirements"].update(global_stage_order="ALLOWED"))

    @mutation("POLICY_BOTH_UNAUTHORIZED")
    def _(root: Path) -> None:
        alter(root, "normative-inputs.json", lambda d: d["predicate_policy"].update(global_stage_order="ALLOWED"))
        alter(root, "authority-requirements.json", lambda d: d["stage_policy_requirements"].update(global_stage_order="ALLOWED"))

    @mutation("SCHEMA_VACUOUS")
    def _(root: Path) -> None:
        path = root / REL / "schema/normative-inputs.schema.json"
        write_json(path, {"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object"})
        rebind(root, ["schema/normative-inputs.schema.json"])

    @mutation("SCHEMA_MALFORMED")
    def _(root: Path) -> None:
        (root / REL / "schema/normative-inputs.schema.json").write_text("{malformed", encoding="utf-8")

    @mutation("ACTIVE_INSTANCE_INVALID")
    def _(root: Path) -> None:
        alter(root, "normative-inputs.json", lambda d: d.pop("predicate_policy"))

    @mutation("RAW_ACCEPTED_SOURCE_MUTATION")
    def _(root: Path) -> None:
        path = root / "docs/accord-02/accord-02r5-specification-package.json"
        path.write_bytes(path.read_bytes() + b"\n")

    @control("BASELINE_NO_GIT_EXPORT")
    def _(root: Path) -> None:
        assert not (root / ".git").exists()

    @control("SELF_DIGEST_REMOVE_POINTER_RECOMPUTES")
    def _(root: Path) -> None:
        package = read_json(root / REL / "specification-package-0.2.json")
        assert package_digest(package) == package["current_candidate_integrity"]["digest"]

    @control("SELF_DIGEST_FORMATTING_ONLY_STABLE")
    def _(root: Path) -> None:
        path = root / REL / "specification-package-0.2.json"
        value = read_json(path)
        path.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")

    @control("REFERENCE_DUPLICATE_SCAN_DEDUP")
    def _(root: Path) -> None:
        code, report, _ = run_evaluator(root, PRIMARY)
        assert code == 0 and report
        edges = report["reference_edge_set"]
        assert len({json.dumps(e, sort_keys=True) for e in edges + edges}) == len(edges)

    @control("REFERENCE_DUPLICATE_EDGE_DEDUP")
    def _(root: Path) -> None:
        code, report, _ = run_evaluator(root, INDEPENDENT)
        assert code == 0 and report
        edges = report["reference_edge_set"]
        assert len({json.dumps(e, sort_keys=True) for e in [*edges, edges[0]]}) == len(edges)

    @control("REFERENCE_ADDED_VALID_GENERIC_DISCOVERED")
    def _(root: Path) -> None:
        alter(root, "authority-requirements.json", lambda d: d.update(falsifier_ref={"kind":"CANONICALIZATION","id":"urn:moirae:accord-02r5r2:canonicalization-profile","version":"0.2"}))

    @control("CONFORMANCE_HAS_NO_SUBJECT_RESTATEMENT")
    def _(root: Path) -> None:
        rules = read_json(root / REL / "rule-registry.json")["rules"]
        assert all("subjects" not in r for r in rules if r["declared_class"] == "EXECUTABLE_CONFORMANCE_RULE")

    @control("PREDECESSOR_LIVE_TREES_ABSENT")
    def _(root: Path) -> None:
        for predecessor in ("docs/accord-02e4r5", "docs/accord-02e4r5r1"):
            path = root / predecessor
            if path.exists():
                shutil.rmtree(path)

    @control("WINDOWS_LIKE_CRLF_NONPINNED")
    def _(root: Path) -> None:
        path = root / REL / "rule-registry.json"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))

    @control("LINUX_LIKE_LF_CHECKOUT")
    def _(root: Path) -> None:
        for rel in ("docs/accord-02/accord-02r5-specification-package.json", "docs/accord-02/examples/accord-02c-settlement-test-vectors.json"):
            assert b"\r\n" not in (root / rel).read_bytes()

    @control("DELETE_BUILDER_AND_PRIMARY", judge=lambda root: independent_only(root))
    def _(root: Path) -> None:
        (root / REL / "_build_candidate.py").unlink()
        (root / PRIMARY).unlink()

    def granularity_judge(root: Path) -> tuple[bool, dict[str, Any]]:
        detail: dict[str, Any] = {}
        okay = True
        for label, script in (("primary", PRIMARY), ("independent", INDEPENDENT)):
            code, report, diagnostic = run_evaluator(root, script)
            binding_map = (report or {}).get("binding_results", {})
            values = [v.get("status") if isinstance(v, dict) else v for v in binding_map.values()]
            condition = code != 0 and "FAIL" in values and "PASS" in values
            detail[label] = {"mixed_binding_results": condition, "diagnostic": diagnostic[:300]}
            okay &= condition
        return okay, detail

    @control("PER_BINDING_GRANULARITY", judge=granularity_judge)
    def _(root: Path) -> None:
        alter(root, "normative-inputs.json", lambda d: d["predicate_policy"].update(global_stage_order="ALLOWED"))

    def independent_only(root: Path) -> tuple[bool, dict[str, Any]]:
        code, report, diagnostic = run_evaluator(root, INDEPENDENT)
        okay = code == 0 and bool(report and report.get("overall_pass"))
        return okay, {"independent": {"exit": code, "accepted": okay, "diagnostic": diagnostic[:300]}}

    results: dict[str, Any] = {"mutation_cases": {}, "controls": {}}
    with tempfile.TemporaryDirectory(prefix="accord-e4r5r2-falsifier-") as temporary:
        temp = Path(temporary)
        export = temp / "export"
        export_source(export)
        baseline = temp / "candidate-baseline"
        shutil.copytree(export / REL, baseline)

        for name, mutate in mutation_cases:
            reset_candidate(export, baseline)
            try:
                mutate(export)
                passed, detail = both_fail(export)
            except Exception as exc:  # mutation construction failure is a test failure
                passed, detail = False, {"exception": repr(exc)}
            results["mutation_cases"][name] = {"passed": passed, "detail": detail}

        for name, prepare, judge in controls:
            reset_candidate(export, baseline)
            try:
                prepare(export)
                passed, detail = judge(export)
            except Exception as exc:
                passed, detail = False, {"exception": repr(exc)}
            results["controls"][name] = {"passed": passed, "detail": detail}

    results["summary"] = {
        "mutation_cases": len(results["mutation_cases"]),
        "mutation_pass": sum(v["passed"] for v in results["mutation_cases"].values()),
        "controls": len(results["controls"]),
        "control_pass": sum(v["passed"] for v in results["controls"].values()),
    }
    results["overall_pass"] = (
        results["summary"]["mutation_cases"] == results["summary"]["mutation_pass"]
        and results["summary"]["controls"] == results["summary"]["control_pass"]
    )
    public_report = {
        "mutation_cases": {name: value["passed"] for name, value in results["mutation_cases"].items()},
        "controls": {name: value["passed"] for name, value in results["controls"].items()},
        "summary": results["summary"],
        "overall_pass": results["overall_pass"],
    }
    print(json.dumps(public_report, indent=2, sort_keys=True))
    return 0 if results["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
