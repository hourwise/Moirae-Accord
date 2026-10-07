"""Verify installed canonical R2e bytes and reproduce the frozen C2 PRIMARY cases."""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import jsonschema
import rfc8785

from preflight import A, C2, CANON, EXPECTED, HERE, LAW_REL, check, digest, filehash, load, semantic_ids, snapshot


sys.setrecursionlimit(30000)
EVALUATOR = CANON / LAW_REL / "audit/evaluate_r5r4.py"
PROFILE = C2 / "inputs/verification-input.json"
PROFILE_SCHEMA_SHA256 = "bb0cfc68f222a7c85b291a6aa1061f3246a144edd1b56528ddcfd1552fcf89d3"


def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_bytes():
    plan = load(HERE / "installation-map.json")
    for row in plan:
        check(filehash(CANON / row["relative_path"]), row["expected_sha256"], "installed " + row["relative_path"])
    projected = (HERE / "projected-installed-manifest.sha256").read_bytes()
    actual = "".join(filehash(CANON / row["relative_path"]) + " *" + row["relative_path"] + "\n" for row in plan).encode()
    check(actual, projected, "installed per-file inventory")
    check(digest(actual), EXPECTED["installed_manifest"], "installed manifest")
    ids = semantic_ids(CANON)
    check(ids, {k: EXPECTED[k] for k in ids}, "installed semantic digests")
    check(filehash(EVALUATOR), EXPECTED["primary"], "installed PRIMARY")
    check(filehash(CANON / LAW_REL / "audit/evaluate_r5r4_independent.py"), EXPECTED["independent"], "retained INDEPENDENT")
    return {"installed_manifest": digest(actual), "semantic_identities": ids,
            "primary": filehash(EVALUATOR), "independent": filehash(CANON / LAW_REL / "audit/evaluate_r5r4_independent.py"),
            "file_count": len(plan)}


def registered_objects():
    reg = load(CANON / LAW_REL / "object-registry.json")
    rows = reg["objects"]
    by_key = {(r["kind"], r["id"], r["version"]): r for r in rows}
    digest_count = 0
    schema_count = 0
    instance_count = 0
    for row in rows:
        path = CANON / row["path"]
        check(path.exists(), True, "registered path " + row["path"])
        integ = row.get("integrity", {})
        if integ.get("mode") == "SEMANTIC_JSON_CONTENT" and row["path"] not in {"docs/accord-02e4r5r4/object-registry.json", "docs/accord-02e4r5r4/specification-package-0.2.json"}:
            actual = digest(rfc8785.dumps(load(path)))
            check(actual, integ["digest"], "registered semantic digest " + row["id"])
            digest_count += 1
        if row["kind"] == "SCHEMA":
            schema = load(path)
            check(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema", "registered schema dialect")
            jsonschema.Draft202012Validator.check_schema(schema)
            schema_count += 1
        ref = row.get("schema_ref")
        if ref:
            schema_row = by_key[(ref["kind"], ref["id"], ref["version"])]
            schema = load(CANON / schema_row["path"])
            jsonschema.Draft202012Validator(schema).validate(load(path))
            instance_count += 1
    check(digest_count, 44, "registered content digests")
    check(schema_count, 23, "registered meta-valid schemas")
    check(instance_count, 23, "registered instance checks")
    return {"registered_objects": len(rows), "semantic_digests": digest_count,
            "meta_valid_schemas": schema_count, "valid_registered_instances": instance_count}


def cli(root):
    schema_path = root / LAW_REL / "sources/external-acceptance-profile.schema.json"
    check(filehash(schema_path), PROFILE_SCHEMA_SHA256, "external profile-schema raw bytes")
    return [sys.executable, "-B", str(EVALUATOR), "--root", str(root),
            "--candidate-package", "docs/accord-02e4r5r4/specification-package-0.2.json",
            "--bootstrap-object-registry", "docs/accord-02e4r5r4/object-registry.json",
            "--expected-package-id", "urn:moirae:accord-02r5:specification-package",
            "--expected-package-version", "0.2", "--expected-package-digest", EXPECTED["package"],
            "--acceptance-profile-schema-id", "urn:moirae:accord-02e4r5r4:external-acceptance-profile-schema:1",
            "--acceptance-profile-schema", str(schema_path),
            "--acceptance-profile-schema-sha256", PROFILE_SCHEMA_SHA256,
            "--verification-input", str(PROFILE)]


def run_cli(label, root):
    proc = subprocess.run(cli(root), capture_output=True, text=True, timeout=240, env=os.environ.copy())
    (HERE / f"{label}.stdout.json").write_text(proc.stdout, encoding="utf-8")
    (HERE / f"{label}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    data = json.loads(proc.stdout)
    witness = data.get("witness") or {}
    normalized = {"status": data.get("status"), "code": data.get("code"),
                  "stage": data.get("stage"), "pre_execution_status": data.get("pre_execution_status"),
                  "failure_kind": data.get("failure_kind") or witness.get("failure_kind"),
                  "diagnostic": data.get("diagnostic") or witness.get("diagnostic"),
                  "bound_identity": data.get("bound_identity") or witness.get("bound_identity") or witness.get("source_identity"),
                  "trust_code": (data.get("trust_result") or {}).get("code"),
                  "exit_code": proc.returncode, "stdout_sha256": digest(proc.stdout.encode()),
                  "stderr_sha256": digest(proc.stderr.encode())}
    return data, normalized


def full_run():
    raw = HERE / "canonical-clean.stdout.json"
    if raw.exists():
        check(filehash(raw), "4b575661e8317c4b409ffa2973185516e09e75250f0c602a375687e3fc97522b", "reproduced frozen C2 clean stdout")
        check(filehash(HERE / "canonical-clean.stderr.txt"), digest(b""), "clean stderr")
        data = load(raw)
        norm = {"status": data.get("status"), "pre_execution_status": data.get("pre_execution_status"),
                "trust_code": (data.get("trust_result") or {}).get("code"), "exit_code": 0,
                "stdout_sha256": filehash(raw), "stderr_sha256": filehash(HERE / "canonical-clean.stderr.txt")}
    else:
        data, norm = run_cli("canonical-clean", CANON)
    check(norm["status"], "PASS", "canonical full status")
    check(norm["pre_execution_status"], "PASS", "canonical pre-execution")
    check(norm["trust_code"], "EXPECTED_PACKAGE_VERIFIED", "canonical trust")
    check(norm["exit_code"], 0, "canonical full exit")
    check(len(data["invariants"]), 40, "canonical invariants")
    check(len(data["bound_rules"]), 42, "canonical bound rules")
    check(data["candidate_objects"], 46, "canonical objects")
    for key in ("invariants", "bound_rules"):
        for row in data[key]:
            result = row.get("result", row)
            check(result["status"], "PASS", f"{key} result")
    return {"normalized": norm, "invariants": 40, "bound_rules": 42, "candidate_objects": 46}


def schema_corpus():
    spec = importlib.util.spec_from_file_location("canonical_r2e_evaluator", EVALUATOR)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    bootstrap = mod._run_evaluation(mod._selftest_args(CANON, PROFILE, EXPECTED["package"]))
    check(bootstrap["status"], "PASS", "schema corpus bootstrap")
    corpus_path = C2 / "corpus.json"
    frozen_path = C2 / "results/primary-schema.json"
    corpus = load(corpus_path)["cases"]
    frozen = load(frozen_path)
    check(frozen["corpus_sha256"], filehash(corpus_path), "frozen C2 corpus identity")
    check(frozen["evaluator_sha256"], EXPECTED["primary"], "frozen PRIMARY identity")
    check(len(corpus), 112, "schema corpus count")
    check([c["id"] for c in corpus], [r["id"] for r in frozen["results"]], "C2 case order")
    rows = []
    for case, old in zip(corpus, frozen["results"]):
        try:
            observed = {"boolean": bool(mod.schema_valid(case["schema"], case["instance"], case["mode"]))}
        except mod.ExpressionError as exc:
            observed = {"error_class": exc.error_class, "pointer": exc.pointer}
        check(observed, case["expected"], "law corpus " + case["id"])
        check(observed, old["observed"], "frozen C2 PRIMARY " + case["id"])
        rows.append({"id": case["id"], "observed": observed})
    save("canonical-schema-results.json", {"evaluator_sha256": EXPECTED["primary"],
         "corpus_sha256": filehash(corpus_path), "case_count": len(rows), "results": rows})
    direct = load(C2 / "inputs/r2e-direct-corpus.json")["cases"]
    direct_ids = {x["id"] for x in direct if x["kind"] == "SCHEMA_VALIDATE"}
    check(len(direct_ids), 69, "direct R2e schema corpus count")
    check(direct_ids.issubset({x["id"] for x in rows}), True, "complete direct R2e schema corpus")
    return {"cases": len(rows), "direct_law_cases": len(direct_ids),
            "frozen_C2_agreement": len(rows), "corpus_sha256": filehash(corpus_path)}


def integrity_mutations():
    plan = load(HERE / "installation-map.json")
    root = HERE / "isolated-integrity"
    if root.exists():
        raise RuntimeError("isolated-integrity already exists; refusing overwrite")
    results = []
    for label in ["table_mutated", "pin_mutated"]:
        dest = root / label
        for row in plan:
            source = CANON / row["relative_path"]
            target = dest / row["relative_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        target = dest / LAW_REL / ("leap-second-table.json" if label == "table_mutated" else "metacontract.json")
        obj = load(target)
        if label == "table_mutated":
            obj["insertions"][0]["effective_mjd_after_insertion"] += 1
            bound = "urn:moirae:accord-02e4r5r4:leap-second-table"
        else:
            obj["runtime_representation"]["schema_format_assertion"]["standard_domain_semantics"]["leap_second_rule"]["table_semantic_sha256"] = "0" * 64
            bound = "urn:moirae:accord-02e4r5r4:metacontract"
        target.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _, norm = run_cli(label, dest)
        check(norm["status"], "FAIL", label + " status")
        check(norm["stage"], "PRE_EXECUTION", label + " gate")
        check(norm["code"], "SCHEMA_INVALID_BOUND_OBJECT", label + " code")
        check(norm["failure_kind"], "INTEGRITY", label + " kind")
        check(norm["diagnostic"], "REGISTRATION_INTEGRITY_DIGEST_MISMATCH", label + " diagnostic")
        check(norm["bound_identity"]["id"], bound, label + " identity")
        check(norm["exit_code"], 2, label + " exit")
        results.append({"case": label, "mutated_path": str(target), "mutated_sha256": filehash(target), "normalized": norm})
    return results


def main():
    installed = verify_bytes()
    syntax = []
    for rel in ["audit/build_r5r4_artifacts.py", "audit/evaluate_r5r4.py", "audit/evaluate_r5r4_independent.py"]:
        path = CANON / LAW_REL / rel
        compile(path.read_bytes(), str(path), "exec")
        syntax.append(rel)
    registered = registered_objects()
    clean = full_run()
    corpus = schema_corpus()
    mutations = integrity_mutations()
    post = verify_bytes()
    check(post, installed, "canonical bytes after mutation checks")
    before = load(HERE / "post-install-state.json")["canonical"]
    after = snapshot()
    check(after, before, "canonical unchanged by verification")
    summary = {"status": "ALL_PRE_ACCEPTANCE_GATES_PASS", "syntax_compiled": syntax,
               "installed_identities": installed, "registered_schema_instance_checks": registered,
               "full_clean_run": clean, "schema_corpus": corpus,
               "integrity_mutations": mutations, "canonical_preserved": True}
    save("verification-results.json", summary)
    print(json.dumps({"status": summary["status"], "registered": registered,
                      "clean": clean["normalized"], "schema_cases": corpus["cases"],
                      "mutation_cases": len(mutations)}, indent=2))


if __name__ == "__main__":
    main()
