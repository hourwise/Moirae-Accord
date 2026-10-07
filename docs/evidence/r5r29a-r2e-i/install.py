"""Install only the frozen R2e map after rechecking all preconditions."""

import json
from pathlib import Path
import shutil

from preflight import CANON, EXPECTED, HERE, check, filehash, semantic_ids, snapshot


MAP_SHA256 = "8f829d40630d1d25ed1b998c152bc3494b652885142e2e086291589a6074c3d4"
PREFLIGHT_SHA256 = "965c2a33b677ceecc0453bb8c950d167f6df9be3922a5664ddc19e6a1b76863e"


def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def main():
    check(filehash(HERE / "installation-map.json"), MAP_SHA256, "frozen map")
    check(filehash(HERE / "preflight.json"), PREFLIGHT_SHA256, "frozen preflight")
    plan = json.loads((HERE / "installation-map.json").read_text(encoding="utf-8"))
    before = json.loads((HERE / "preflight.json").read_text(encoding="utf-8"))["pre_install"]
    check(snapshot(), before, "unchanged canonical pre-install snapshot")
    for row in plan:
        src = Path(row["source_artifact"])
        dest = Path(row["canonical_destination"])
        check(dest, CANON / row["relative_path"], "canonical destination")
        check(filehash(src), row["expected_sha256"], "frozen source " + row["relative_path"])
        actual = filehash(dest) if dest.exists() else None
        check(actual, row["pre_install_sha256"], "pre-install destination " + row["relative_path"])
        check(row["action"], "ADD" if actual is None else "UNCHANGED" if actual == row["expected_sha256"] else "REPLACE", "map action")
    changed = []
    try:
        for row in plan:
            if row["action"] == "UNCHANGED":
                continue
            src = Path(row["source_artifact"])
            dest = Path(row["canonical_destination"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            check(filehash(dest), row["expected_sha256"], "installed " + row["relative_path"])
            changed.append(row["relative_path"])
        for row in plan:
            check(filehash(Path(row["canonical_destination"])), row["expected_sha256"], "final " + row["relative_path"])
        check(semantic_ids(CANON), {k: EXPECTED[k] for k in ["package", "registry", "model", "leap_table"]}, "installed semantic identities")
        rows = sorted((row["relative_path"], row["expected_sha256"]) for row in plan)
        actual = "".join(filehash(CANON / p) + " *" + p + "\n" for p, _ in rows).encode()
        import hashlib
        check(hashlib.sha256(actual).hexdigest(), EXPECTED["installed_manifest"], "installed 56-file manifest")
        check(filehash(CANON / "docs/accord-02e4r5r4/audit/evaluate_r5r4.py"), EXPECTED["primary"], "installed PRIMARY")
        check(filehash(CANON / "docs/accord-02e4r5r4/audit/evaluate_r5r4_independent.py"), EXPECTED["independent"], "installed INDEPENDENT")
        check({p for p, _ in rows}, {p.relative_to(CANON).as_posix() for p in (CANON / "docs/accord-02e4r5r4").rglob("*") if p.is_file()}, "installed tree paths")
        after = snapshot()
        for key in ["branch", "head", "tree", "protected_main", "origin_main", "tracked_diff", "staged_diff", "stash", "remotes", "tags"]:
            check(after[key], before[key], "preserved Git state " + key)
        save("post-install-state.json", {"status": "INSTALLED_UNACCEPTED", "changed_paths": changed,
             "installed_manifest_sha256": EXPECTED["installed_manifest"], "semantic_identities": semantic_ids(CANON),
             "canonical": after})
        print(json.dumps({"installed": len(changed), "manifest": EXPECTED["installed_manifest"], "head": after["head"]}, indent=2))
    except Exception as exc:
        save("installation-failure.json", {"error": repr(exc), "changed_paths": changed, "canonical": snapshot()})
        raise


if __name__ == "__main__":
    main()
