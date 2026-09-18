#!/usr/bin/env python3
"""Exercise LF, CRLF, and exported-no-Git semantic portability without source writes."""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PRIMARY=Path("docs/accord-02e4r5/audit/certify_e4r5.py")
INDEPENDENT=Path("docs/accord-02e4r5/audit/independent_evaluate_e4r5.py")
def snapshot():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"docs/accord-02e4r5").rglob("*") if p.is_file()}
def run_variant(label,eol):
    with tempfile.TemporaryDirectory(prefix="accord-e4r5-portable-") as td:
        dst=Path(td)/"export"; shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns(".git","__pycache__","*.pyc"))
        for p in dst.rglob("*.json"):
            value=json.loads(p.read_text(encoding="utf-8")); text=json.dumps(value,indent=2,ensure_ascii=False)+"\n"
            p.write_bytes(text.replace("\n",eol).encode("utf-8"))
        env=dict(os.environ); env["PYTHONDONTWRITEBYTECODE"]="1"
        results=[]
        for script in (PRIMARY,INDEPENDENT):
            cp=subprocess.run([sys.executable,str(dst/script)],cwd=dst,env=env,text=True,capture_output=True)
            payload=json.loads(cp.stdout); results.append({"evaluator":payload["certificate"],"exit_code":cp.returncode,"overall_pass":payload["overall_pass"],"standards":payload["package_invariants"]["standards"]["pass"],"semantic_digests":payload["package_invariants"]["digests"]["pass"],"references":payload["package_invariants"]["references"]["pass"],"executable_rules":payload["rule_counts"],"v013":payload["package_invariants"]["v013"]["result"],"expectation_stability":payload["package_invariants"]["expectation_stability"]["pass"],"repository_write_count":payload["repository_write_count"]})
        return {"representation":label,"git_metadata_present":(dst/".git").exists(),"results":results}
def main():
    before=snapshot(); variants=[run_variant("LF","\n"),run_variant("CRLF","\r\n"),run_variant("EXPORT_NO_GIT","\n")]; after=snapshot()
    result={"certificate":"ACCORD-02E4R5_PORTABILITY","variants":variants,"source_repository_write_count":sum(before.get(k)!=after.get(k) for k in set(before)|set(after)),"pass":all(x["overall_pass"] for v in variants for x in v["results"]) and before==after and all(not v["git_metadata_present"] for v in variants)}
    print(json.dumps(result,sort_keys=True,separators=(",",":"))); raise SystemExit(0 if result["pass"] else 1)
if __name__=="__main__":main()
