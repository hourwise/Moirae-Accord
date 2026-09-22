#!/usr/bin/env python3
"""Release verifier for ACCORD-02E4R5R3.

Compares the exact reported surfaces of the primary and independent evaluators
(not merely counts), re-derives the reference edge set with a third scanner,
and exercises clean exports (no .git, no predecessor live trees, Windows-like
and Linux-like checkouts, builder and primary evaluator deleted).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REL = "docs/accord-02e4r5r3"
HERE = Path(__file__).resolve()
SOURCE_ROOT = HERE.parents[3]
PRIMARY = REL + "/audit/certify_e4r5r3.py"
INDEPENDENT = REL + "/audit/independent_evaluate_e4r5r3.py"
FALSIFIER = REL + "/audit/falsify_e4r5r3.py"
FIXTURE = REL + "/audit/fixtures/external-trust-root.json"
PREDECESSORS = ["docs/accord-02e4r5", "docs/accord-02e4r5r1", "docs/accord-02e4r5r2"]


def run(script, root, extra=()):
    process = subprocess.run(
        [sys.executable, str(Path(root) / script), "--root", str(root), *extra],
        capture_output=True, text=True, timeout=600,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    payload = None
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError:
        payload = None
    for line in reversed(process.stdout.strip().splitlines()):
        if payload is not None:
            break
        try:
            payload = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    return process.returncode, payload, process.stderr[-800:]


def external_args(root):
    fixture = json.loads((Path(root) / FIXTURE).read_text(encoding="utf-8"))
    return ["--expected-package-id", fixture["package_id"],
            "--expected-package-version", fixture["package_version"],
            "--expected-package-digest", fixture["package_digest"]]


def third_party_edges(root):
    base = Path(root)
    registry = json.loads((base / REL / "object-registry.json").read_text(encoding="utf-8"))
    shape = json.loads((base / REL / "reference-model.json").read_text(encoding="utf-8"))["shape_predicate"]
    signature = set(shape["required_keys"])
    extras = set(shape["optional_keys"])
    permissive = shape["additional_keys"] == "ALLOW"
    found = set()

    def scan(node, owner, trail=""):
        if isinstance(node, dict):
            labels = set(node)
            if signature <= labels and (permissive or labels <= signature | extras) \
                    and all(isinstance(v, str) for v in node.values()):
                found.add((owner["kind"], owner["id"], owner["version"], trail,
                           node["kind"], node["id"], node["version"], node.get("member_id", "")))
            for label, child in node.items():
                scan(child, owner, trail + "/" + label.replace("~", "~0").replace("/", "~1"))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                scan(child, owner, trail + "/" + str(index))

    for item in registry["objects"]:
        if item["status"] == "ACTIVE" and item["classification"] == "NORMATIVE":
            scan(json.loads((base / item["path"]).read_text(encoding="utf-8")), item)
    return [list(edge) for edge in sorted(found)]


def statuses(mapping):
    return {k: (v.get("status") if isinstance(v, dict) else v) for k, v in mapping.items()}


def copy_export(destination: Path, drop_git=True):
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".deps")
    shutil.copytree(SOURCE_ROOT, destination, ignore=ignore,
                    ignore_dangling_symlinks=True)
    if drop_git:
        remove_tree(destination / ".git")


def remove_tree(path):
    import stat as _stat

    def on_error(function, target, _exc):
        try:
            os.chmod(target, _stat.S_IWRITE)
            function(target)
        except Exception:
            pass

    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path, onerror=on_error)


def compare(primary, independent, third):
    return {
        "active_object_set": primary.get("active_object_set") == independent.get("active_object_set"),
        "schema_result_set": primary.get("schema_result_set") == independent.get("schema_result_set"),
        "reference_edge_set": (primary.get("reference_edge_set")
                               == independent.get("reference_edge_set") == third),
        "governance_invariant_map": statuses(primary.get("governance_invariant_map", {}))
        == independent.get("governance_invariant_map", {}),
        "package_invariant_map": statuses(primary.get("package_invariant_map", {}))
        == independent.get("package_invariant_map", {}),
        "binding_map": statuses(primary.get("binding_map", {})) == independent.get("binding_map", {}),
        "member_rule_map": primary.get("member_rule_map") == independent.get("member_rule_map"),
        "internal_map": primary.get("internal_map") == independent.get("internal_map"),
        "class_map": primary.get("class_map") == independent.get("class_map"),
        "rule_set": primary.get("rule_set") == independent.get("rule_set"),
        "procedure_role_closure": primary.get("procedure_role_closure")
        == independent.get("procedure_role_closure"),
        "v013_requirement_map_result": statuses(
            primary.get("v013_requirement_map_result", {}).get("requirements", {}))
        == {k: v["status"] for k, v in independent.get(
            "v013_requirement_map_result", {}).get("requirements", {}).items()},
        "v013_result": primary.get("v013_result") == independent.get("v013_result"),
        "expectation_stability_result": primary.get("expectation_stability_result")
        == independent.get("expectation_stability_result"),
        "trusted_identity_result": primary.get("trusted_package_identity", {}).get("status")
        == independent.get("trusted_package_identity", {}).get("status")
        and primary.get("trusted_package_identity", {}).get("recomputed_identity")
        == independent.get("trusted_package_identity", {}).get("recomputed_identity"),
        "internal_conformance_status": primary.get("internal_package_conformance")
        == independent.get("internal_package_conformance"),
        "governance_conformance_status": primary.get("governance_conformance")
        == independent.get("governance_conformance"),
    }


def clean_export_scenarios(temporary: Path):
    report = {}
    export = temporary / "clean"
    copy_export(export)
    for predecessor in PREDECESSORS:
        remove_tree(export / predecessor)
    report["no_git_export"] = not (export / ".git").exists()
    args = external_args(export)
    code_p, payload_p, diag_p = run(PRIMARY, export, args)
    code_i, payload_i, diag_i = run(INDEPENDENT, export, args)
    report["clean_export_primary"] = code_p == 0 and bool(payload_p and payload_p.get("overall_pass"))
    report["clean_export_independent"] = code_i == 0 and bool(payload_i and payload_i.get("overall_pass"))
    report["clean_export_diagnostic"] = (diag_p or diag_i)[:300]

    # Windows-like checkout: CRLF in a non-pinned normative artifact.
    windows = temporary / "windows"
    copy_export(windows)
    for predecessor in PREDECESSORS:
        remove_tree(windows / predecessor)
    rule_path = windows / REL / "rule-registry.json"
    rule_path.write_bytes(rule_path.read_bytes().replace(b"\n", b"\r\n"))
    schema_path = windows / REL / "schema" / "rule-registry.schema.json"
    schema_path.write_bytes(schema_path.read_bytes().replace(b"\n", b"\r\n"))
    code, payload, diag = run(INDEPENDENT, windows, external_args(windows))
    report["windows_like_crlf"] = code == 0 and bool(payload and payload.get("overall_pass"))
    report["windows_like_diagnostic"] = diag[:300]

    # Linux-like checkout: pinned accepted sources stay byte-identical (LF).
    report["linux_like_pinned_lf"] = all(
        b"\r\n" not in (SOURCE_ROOT / path).read_bytes()
        for path in ("docs/accord-02/accord-02r5-specification-package.json",
                     "docs/accord-02/examples/accord-02c-settlement-test-vectors.json"))

    # Delete-the-Python: independent evaluator with builder and primary removed.
    stripped = temporary / "stripped"
    copy_export(stripped)
    (stripped / REL / "_build_candidate.py").unlink()
    (stripped / PRIMARY).unlink()
    code, payload, diag = run(INDEPENDENT, stripped, external_args(stripped))
    report["delete_python_independent"] = code == 0 and bool(payload and payload.get("overall_pass"))
    report["delete_python_diagnostic"] = diag[:300]
    report["delete_python_surfaces"] = {
        "counts": (payload or {}).get("counts"),
        "internal": (payload or {}).get("internal_package_conformance"),
        "governance": (payload or {}).get("governance_conformance"),
        "trust": (payload or {}).get("trusted_package_identity", {}).get("status"),
        "v013": (payload or {}).get("v013_result"),
    }
    # Falsifier must run from a clean export (no .git, no predecessor live trees).
    code, payload, diag = run(FALSIFIER, export)
    report["falsifier_in_clean_export"] = code == 0 and bool(payload and payload.get("overall_pass"))
    report["falsifier_diagnostic"] = diag[:300]
    report["falsifier_summary"] = (payload or {}).get("summary")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(SOURCE_ROOT))
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    external = external_args(root)
    code_p, primary, diag_p = run(PRIMARY, root, external)
    code_i, independent, diag_i = run(INDEPENDENT, root, external)
    primary = primary or {}
    independent = independent or {}
    third = third_party_edges(root) if primary else []
    comparisons = compare(primary, independent, third)
    with tempfile.TemporaryDirectory(prefix="accord-e4r5r3-release-") as tmp:
        exports = clean_export_scenarios(Path(tmp))
    overall = (
        code_p == 0 and code_i == 0
        and primary.get("overall_pass") and independent.get("overall_pass")
        and all(comparisons.values())
        and all(value for key, value in exports.items() if isinstance(value, bool))
    )
    report = {
        "release_verifier": "ACCORD-02E4R5R3",
        "primary_pass": code_p == 0 and bool(primary.get("overall_pass")),
        "independent_pass": code_i == 0 and bool(independent.get("overall_pass")),
        "primary_diagnostic": diag_p[:300],
        "independent_diagnostic": diag_i[:300],
        "comparisons": comparisons,
        "clean_export_scenarios": exports,
        "derived_reference_edges": len(third),
        "counts": primary.get("counts"),
        "internal_package_conformance": primary.get("internal_package_conformance"),
        "governance_conformance": primary.get("governance_conformance"),
        "trusted_package_identity": primary.get("trusted_package_identity", {}).get("status"),
        "v013_result": primary.get("v013_result"),
        "overall_pass": overall,
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
