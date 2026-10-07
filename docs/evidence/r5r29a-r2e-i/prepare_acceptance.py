"""Build bounded R2e acceptance records from verified installed evidence."""

import json
from pathlib import Path

from preflight import A, C2, CANON, EXPECTED, HERE, check, digest, filehash, load, semantic_ids, snapshot


def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    pre = load(HERE / "preflight.json")
    post = load(HERE / "post-install-state.json")
    verification = load(HERE / "verification-results.json")
    deep = load(HERE / "deep-regression-results.json")
    check(verification["status"], "ALL_PRE_ACCEPTANCE_GATES_PASS", "verification status")
    check(deep["status"], "PASS", "deep regression")
    check(verification["schema_corpus"]["cases"], 112, "schema reconciliation")
    check(verification["schema_corpus"]["direct_law_cases"], 69, "direct law corpus")
    check(len(verification["integrity_mutations"]), 2, "integrity cases")
    frozen_raw = {
        "canonical-clean": C2 / "results/integrity/primary/clean.stdout.json",
        "table_mutated": C2 / "results/integrity/primary/table_mutated.stdout.json",
        "pin_mutated": C2 / "results/integrity/primary/pin_mutated.stdout.json",
    }
    for label, frozen in frozen_raw.items():
        check(filehash(HERE / (label + ".stdout.json")), filehash(frozen), label + " C2 raw output")
    for row in verification["integrity_mutations"]:
        row["normalized"]["stdout_sha256"] = filehash(HERE / (row["case"] + ".stdout.json"))
        row["normalized"]["stderr_sha256"] = filehash(HERE / (row["case"] + ".stderr.txt"))
    save("verification-results.json", verification)
    check(snapshot(), post["canonical"], "canonical state before acceptance record")
    check(semantic_ids(CANON), {k: EXPECTED[k] for k in ("package", "registry", "model", "leap_table")}, "canonical semantic identities")
    check(filehash(A / "evidence-manifest.sha256"), EXPECTED["adjudication_manifest"], "adjudication identity")
    check(filehash(A / "report.md"), EXPECTED["adjudication_report"], "adjudication report")
    check(filehash(C2 / "evidence-manifest.sha256"), EXPECTED["c2_manifest"], "C2 identity")
    record = {
        "acceptance_version": "1.0", "accepted_slice": "ACCORD-02E4R5R4-R2e",
        "acceptance_status": "ACCEPTED_LOCAL_CANONICAL_CANDIDATE",
        "scope": "The exact adjudicated R5R29A R2e candidate law and selected evaluator, within the verified R2e behaviours only.",
        "acceptance_authority": {"adjudication_verdict": "R5R29A_R2E_ACCEPTANCE_ADJUDICATION_READY",
                                 "adjudication_evidence_manifest_sha256": EXPECTED["adjudication_manifest"],
                                 "adjudication_report_sha256": EXPECTED["adjudication_report"],
                                 "c2_evidence_manifest_sha256": EXPECTED["c2_manifest"]},
        "accepted_object": {k: EXPECTED[k] for k in ("package", "registry", "model", "leap_table", "staged_manifest", "installed_manifest", "primary", "independent")},
        "canonical_pre_install": {k: pre["pre_install"][k] for k in ("branch", "head", "tree", "protected_main", "origin_main", "untracked_count", "untracked_manifest_sha256")},
        "installation_map_sha256": filehash(HERE / "installation-map.json"),
        "verification_results_sha256": filehash(HERE / "verification-results.json"),
        "deep_regression_results_sha256": filehash(HERE / "deep-regression-results.json"),
        "reconciliation": {"total_cases": 115, "schema_cases": 112, "integrity_cases": 3,
                           "classification": "AGREE_AND_CONFORM", "installed_primary_raw_integrity_outputs_equal_frozen_c2": True},
        "historical_limitation": "R2e-I received a 52-file neutral package. C2 later independently verified the complete 56-file staged tree.",
        "known_non_governed_difference": "Failure CLI exit codes: PRIMARY 2, INDEPENDENT 1.",
        "publication": "LOCAL_ONLY; no push authorized by this mission",
    }
    save("accord-02e4r5r4-r2e-acceptance-manifest.json", record)
    manifest_sha = filehash(HERE / "accord-02e4r5r4-r2e-acceptance-manifest.json")
    acceptance = f"""# ACCORD-02E4R5R4 R2e Acceptance

## Status and scope

**R2e is accepted in the local canonical candidate** only for the exact frozen object and governed behaviours recorded in [the machine-readable manifest](accord-02e4r5r4-r2e-acceptance-manifest.json). This record does not accept any later R5R29A phase or broaden the established R2e law.

The staged 56-file law tree has SHA-256 `{EXPECTED['staged_manifest']}`. Its canonical 56-file installation, with the adjudicated evaluator overlay, has SHA-256 `{EXPECTED['installed_manifest']}`. The staged package has semantic SHA-256 `{EXPECTED['package']}` and remains byte-for-byte frozen; the embedded candidate status was not edited during acceptance.

## Authority and verification

The adjudication evidence manifest is `{EXPECTED['adjudication_manifest']}` and its report is `{EXPECTED['adjudication_report']}`. The C2 evidence manifest is `{EXPECTED['c2_manifest']}`. The installed PRIMARY evaluator is `{EXPECTED['primary']}`. The retained INDEPENDENT evaluator is `{EXPECTED['independent']}` and remains audit evidence, not the executable canonical evaluator.

The installation map is SHA-256 `{record['installation_map_sha256']}`. It records all 56 source-to-destination actions: two additions, twelve replacements, and forty-two byte-identical files. Verification checked 44 registered semantic digests, 23 schema meta-validations, 23 registered instances, all 40 invariants and 42 bound rules, 46 candidate objects, 112 C2 schema cases (including all 69 direct R2e schema cases), and the three governed integrity cases. The installed PRIMARY outputs match the frozen C2 PRIMARY outputs on all 115 cases. Deep regression reached schema depth 2000 and runtime-value depth 1200. Mutations ran only on isolated copies. The clean full output and both mutation raw outputs are byte-identical to C2 PRIMARY evidence.

R2e-I historically received a 52-file neutral package; C2 later verified the complete 56-file staged tree. PRIMARY and INDEPENDENT differ in numeric CLI failure exit codes (2 and 1), which the staged law does not govern. These facts remain part of the acceptance record.

## Repository disposition

This is a local branch acceptance. Protected `main` and remote refs are left unchanged. The containing Git commit, tree, parent, committed paths, and any acceptance tag target are recorded in repository metadata and the final installation report outside the self-hashing acceptance content. The next phase requires separate authorization.
"""
    (HERE / "ACCORD-02E4R5R4-R2E-ACCEPTANCE.md").write_text(acceptance, encoding="utf-8")
    seal = f"""# ACCORD-02E4R5R4 R2e Seal

The exact R2e candidate identified by package `{EXPECTED['package']}`, staged manifest `{EXPECTED['staged_manifest']}`, and installed manifest `{EXPECTED['installed_manifest']}` is accepted in the local canonical branch within [the bounded acceptance statement](ACCORD-02E4R5R4-R2E-ACCEPTANCE.md).

The machine-readable acceptance manifest is SHA-256 `{manifest_sha}`. The selected PRIMARY is `{EXPECTED['primary']}`; the retained INDEPENDENT is `{EXPECTED['independent']}`. C2 and adjudication evidence manifests are `{EXPECTED['c2_manifest']}` and `{EXPECTED['adjudication_manifest']}`. The acceptance commit is the commit containing this seal; its identity is established after commit, as in earlier Accord seals.

Protected `main` is not changed. Remote publication and all later phases require separate authorization.
"""
    (HERE / "ACCORD-02E4R5R4-R2E-SEAL.md").write_text(seal, encoding="utf-8")
    core_names = [p.name for p in HERE.iterdir() if p.is_file() and p.name not in {"evidence-manifest.sha256", "prepare_acceptance.py", "install.py", "preflight.py", "verify.py", "deep_regression.py"}]
    core_names += ["prepare_acceptance.py", "install.py", "preflight.py", "verify.py", "deep_regression.py"]
    core_names.sort()
    manifest = "".join(filehash(HERE / name) + " *" + name + "\n" for name in core_names)
    (HERE / "evidence-manifest.sha256").write_bytes(manifest.encode())
    print(json.dumps({"acceptance_manifest_sha256": manifest_sha,
                      "evidence_files": len(core_names),
                      "evidence_manifest_sha256": filehash(HERE / "evidence-manifest.sha256")}, indent=2))


if __name__ == "__main__":
    main()
