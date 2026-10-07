"""Read-only R5R29A R2e installation preflight; writes evidence here only."""

import hashlib
import json
import os
from pathlib import Path
import subprocess

import rfc8785


HERE = Path(__file__).resolve().parent
SCRATCH = Path(r"D:\Users\fleur\Moirae Accord - Scratch")
A = SCRATCH / "R5R29A-R2e-A"
C2 = SCRATCH / "R5R29A-R2e-C2"
P = SCRATCH / "R5R29A-R2e-P"
B = SCRATCH / "R5R29A-R2c"
CANON = Path(r"D:\Users\fleur\Moirae Accord - E4R5R4 Sol")
LAW_REL = Path("docs/accord-02e4r5r4")
STAGE = P / "S"
EXPECTED = {
    "package": "4b343600039c73f3ee4bc64edbb4abdd2912b18941966d51fcd25360901697f1",
    "registry": "c183e0433b508c331d70680e5568be8985667d0be9c362ca016158e53f9a6793",
    "model": "b88f7559e157d318f194d9df3b33c4b4418406e54d358d81aed89fdab2702d9b",
    "leap_table": "5a7679ce687349348a89a223988e3c2a8f0c9b3046433ccee3c9830242b999c1",
    "staged_manifest": "0d2f567c65d5a9a91d86c12faabb21655cc6b2724d5539d799ef7325bf734ce8",
    "installed_manifest": "7485da2f29c13fb7d7cd9e365de85c573fcc96fe28e2e272b03e70c9d0105fd2",
    "primary": "8facf456d00d72a4eb3217a3ef624cc99d7f351cc7626b66366371dafd0dca04",
    "independent": "69230e1c5afbafd5ea653ac7b3d68934ed13991d7c061e9a46d2673478782ad1",
    "c2_manifest": "2587805b38bc6b39b1b69275f1ec9b5e3b22e15aeda74204da3cd7e80213fad9",
    "adjudication_manifest": "7bc846732fbeaaa20a6b1f6b6c560c30c194fcea4267876f62243670fff5dc73",
    "adjudication_report": "6f3518067ac6ccafdda64b7ad1772541d571e3029812e89705bb06dda97b2833",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def filehash(path):
    return digest(path.read_bytes())


def check(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: {actual} != {expected}")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        h, rel = line.split(" *", 1)
        rows.append((rel, h))
    return rows


def verify_manifest(root, manifest, count):
    rows = lines(manifest)
    check(len(rows), count, str(manifest) + " count")
    check(len({p for p, _ in rows}), count, str(manifest) + " unique")
    for rel, expected in rows:
        check(filehash(root / rel), expected, rel)
    return rows


def semantic_ids(root):
    law = root / LAW_REL
    pkg = load(law / "specification-package-0.2.json")
    stripped = json.loads(json.dumps(pkg))
    del stripped["current_candidate_integrity"]["digest"]
    reg = load(law / "object-registry.json")
    meta = load(law / "metacontract.json")
    leap = load(law / "leap-second-table.json")
    ids = {
        "package": digest(rfc8785.dumps(stripped)),
        "registry": digest(rfc8785.dumps(reg)),
        "model": digest(rfc8785.dumps(meta["failure_semantics"]["pre_execution_failure_model"])),
        "leap_table": digest(rfc8785.dumps(leap)),
    }
    check(pkg["current_candidate_integrity"]["digest"], ids["package"], "package embedded digest")
    check(pkg["registry_semantic_sha256"], ids["registry"], "registry embedded digest")
    return ids


def git(*args):
    cmd = ["git", "-c", f"safe.directory={CANON.as_posix()}", *args]
    proc = subprocess.run(cmd, cwd=CANON, text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def snapshot():
    status = git("status", "--porcelain=v1", "-uall").splitlines()
    untracked = sorted(x[3:] for x in status if x.startswith("?? "))
    rows = [{"path": p, "sha256": filehash(CANON / p)} for p in untracked]
    payload = "".join(x["sha256"] + " *" + x["path"] + "\n" for x in rows).encode()
    return {
        "worktree": str(CANON),
        "branch": git("symbolic-ref", "--short", "HEAD"),
        "head": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "protected_main": git("rev-parse", "refs/heads/main"),
        "origin_main": git("rev-parse", "--verify", "refs/remotes/origin/main"),
        "tracked_diff": git("diff", "--name-status"),
        "staged_diff": git("diff", "--cached", "--name-status"),
        "status_porcelain": status,
        "untracked_files": rows,
        "untracked_count": len(rows),
        "untracked_manifest_sha256": digest(payload),
        "stash": git("stash", "list"),
        "remotes": git("remote", "-v"),
        "tags": git("show-ref", "--tags", "-d"),
    }


def main():
    check(filehash(A / "evidence-manifest.sha256"), EXPECTED["adjudication_manifest"], "adjudication manifest")
    check(filehash(A / "report.md"), EXPECTED["adjudication_report"], "adjudication report")
    check(filehash(C2 / "evidence-manifest.sha256"), EXPECTED["c2_manifest"], "C2 manifest")
    verify_manifest(A, A / "evidence-manifest.sha256", 11)
    verify_manifest(C2, C2 / "evidence-manifest.sha256", 333)
    acceptance = load(A / "acceptance-object.json")
    check(acceptance["status"], "ADJUDICATED_FOR_LATER_INSTALLATION_ONLY", "adjudication status")
    check(acceptance["staged_law_file_count"], 56, "staged count")
    check(acceptance["staged_law_package_semantic_sha256"], EXPECTED["package"], "adjudicated package")
    check(acceptance["registry_semantic_sha256"], EXPECTED["registry"], "adjudicated registry")
    check(acceptance["pre_execution_model_sha256"], EXPECTED["model"], "adjudicated model")
    check(acceptance["frozen_leap_table_semantic_sha256"], EXPECTED["leap_table"], "adjudicated leap")
    check(acceptance["staged_56_file_manifest_sha256"], EXPECTED["staged_manifest"], "adjudicated staged manifest")
    check(acceptance["c2_evidence_manifest_sha256"], EXPECTED["c2_manifest"], "adjudicated C2")
    check(acceptance["projected_post_overlay_56_file_manifest_sha256"], EXPECTED["installed_manifest"], "projected installed manifest")
    stage_manifest = P / "build1-manifest.sha256"
    check(filehash(stage_manifest), EXPECTED["staged_manifest"], "staged manifest")
    staged_rows = verify_manifest(STAGE, stage_manifest, 56)
    actual_stage_paths = {p.relative_to(STAGE).as_posix() for p in (STAGE / LAW_REL).rglob("*") if p.is_file()}
    check(actual_stage_paths, {p for p, _ in staged_rows}, "staged tree inventory")
    ids = semantic_ids(STAGE)
    for k, v in ids.items():
        check(v, EXPECTED[k], "staged " + k)
    primary = Path(acceptance["selected_canonical_evaluator"]["source"])
    independent = Path(acceptance["retained_reconciliation_evaluator"]["source"])
    check(primary, P / "primary/evaluate_r5r4.py", "PRIMARY source")
    check(independent, P / "neutral/independent-worker-output/evaluate_r5r4_independent.py", "INDEPENDENT source")
    check(filehash(primary), EXPECTED["primary"], "PRIMARY bytes")
    check(filehash(independent), EXPECTED["independent"], "INDEPENDENT bytes")
    check(acceptance["selected_canonical_evaluator"]["sha256"], EXPECTED["primary"], "PRIMARY claim")
    check(acceptance["retained_reconciliation_evaluator"]["sha256"], EXPECTED["independent"], "INDEPENDENT claim")
    before = snapshot()
    previous = load(A / "canonical-start.json")
    for key in previous:
        check(before[key], previous[key], "canonical pre-install " + key)
    check(before["origin_main"], "7d0bc13ceb5a58e80644b976e72df25ee2114441", "origin/main")
    baseline_rows = verify_manifest(B / "S", B / "sup/S-edge-build1.sha256", 56)
    baseline = dict(baseline_rows)
    changed = sorted(p for p, h in staged_rows if h != baseline[p])
    check(changed, sorted(load(A / "normative-diff.json")["changed_files"]), "seven-file staged delta")
    overlays = {
        acceptance["selected_canonical_evaluator"]["target_relative_path"]: (primary, EXPECTED["primary"]),
        acceptance["retained_reconciliation_evaluator"]["target_relative_path"]: (independent, EXPECTED["independent"]),
    }
    staged = dict(staged_rows)
    check(set(overlays), {"docs/accord-02e4r5r4/audit/evaluate_r5r4.py", "docs/accord-02e4r5r4/audit/evaluate_r5r4_independent.py"}, "overlay paths")
    projected = dict(staged)
    for rel, (_, h) in overlays.items():
        projected[rel] = h
    manifest_bytes = "".join(projected[p] + " *" + p + "\n" for p in sorted(projected)).encode()
    check(digest(manifest_bytes), EXPECTED["installed_manifest"], "projected installed inventory")
    installation = []
    for rel in sorted(projected):
        source = overlays[rel][0] if rel in overlays else STAGE / rel
        target = CANON / rel
        current = filehash(target) if target.exists() else None
        action = "ADD" if current is None else "UNCHANGED" if current == projected[rel] else "REPLACE"
        installation.append({"source_artifact": str(source), "canonical_destination": str(target),
                             "relative_path": rel, "expected_sha256": projected[rel],
                             "pre_install_sha256": current, "action": action,
                             "source_role": "FROZEN_EVALUATOR" if rel in overlays else "ADJUDICATED_STAGED_TREE"})
    check({x["relative_path"] for x in installation}, set(projected), "map inventory")
    preflight = {"verified_authority": EXPECTED, "pre_install": before,
                 "staged_semantic_identities": ids, "staged_file_count": len(staged_rows),
                 "staged_delta": changed, "c2_manifest_entries": 333,
                 "adjudication_manifest_entries": 11, "installed_manifest_projection": digest(manifest_bytes),
                 "installation_action_counts": {a: sum(x["action"] == a for x in installation) for a in ["ADD", "REPLACE", "UNCHANGED"]}}
    (HERE / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n", encoding="utf-8")
    (HERE / "installation-map.json").write_text(json.dumps(installation, indent=2) + "\n", encoding="utf-8")
    (HERE / "projected-installed-manifest.sha256").write_bytes(manifest_bytes)
    print(json.dumps({"authority": "PASS", "canonical_start": "PASS", "staged_delta_files": len(changed),
                      "installation_actions": preflight["installation_action_counts"],
                      "projected_installed_manifest": digest(manifest_bytes)}, indent=2))


if __name__ == "__main__":
    main()
