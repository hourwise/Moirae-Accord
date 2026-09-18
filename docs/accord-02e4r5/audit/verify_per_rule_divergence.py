#!/usr/bin/env python3
"""Run operand-isolation mutations through both real evaluator entry points."""
from __future__ import annotations
import copy, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SCRIPTS=[Path("docs/accord-02e4r5/audit/certify_e4r5.py"),Path("docs/accord-02e4r5/audit/independent_evaluate_e4r5.py")]
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def save(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
def evaluate(root):
    env=dict(os.environ); env["PYTHONDONTWRITEBYTECODE"]="1"; out={}
    for script in SCRIPTS:
        cp=subprocess.run([sys.executable,str(root/script)],cwd=root,env=env,text=True,capture_output=True); data=json.loads(cp.stdout); out[data["certificate"]]={k:v["status"] for k,v in data["rule_results"].items()}
    return out
def assert_status(results,expected): return all(all(values.get(k)==v for k,v in expected.items()) for values in results.values())
def run_case(name,mutation,expected):
    with tempfile.TemporaryDirectory(prefix="accord-e4r5-rule-") as td:
        root=Path(td)/"export"; shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns(".git","__pycache__","*.pyc")); mutation(root); results=evaluate(root)
        return {"case":name,"expected":expected,"implementations":results,"pass":assert_status(results,expected)}
def json_mutator(rel,fn):
    def apply(root): p=root/rel; v=load(p); fn(v); save(p,v)
    return apply
def main():
    pred=Path("docs/accord-02e4r5/accord-02e4r5-predicate-registry.json"); part=Path("docs/accord-02e4r5/accord-02e4r5-partial-effect-policy.json"); assertions=Path("docs/accord-02e4r5/accord-02e4r5-assertion-registry.json"); rules=Path("docs/accord-02e4r5/accord-02e4r5-validation-rules.json")
    cases=[]
    cases.append(run_case("PRED_PAIR_MUTATE_A",json_mutator(pred,lambda v:v.__setitem__("global_stage_order","MUTATED")),{"PRED-001":"FAIL","PRED-002":"PASS"}))
    cases.append(run_case("PRED_PAIR_MUTATE_B",json_mutator(pred,lambda v:v.__setitem__("implicit_transitivity","MUTATED")),{"PRED-001":"PASS","PRED-002":"FAIL"}))
    cases.append(run_case("PART_PAIR_MUTATE_A",json_mutator(part,lambda v:v.__setitem__("same_effect_required",False)),{"E4R1-PART-001":"FAIL","E4R1-PART-002":"PASS"}))
    cases.append(run_case("PART_PAIR_MUTATE_B",json_mutator(part,lambda v:v.__setitem__("direct_predecessor_required",False)),{"E4R1-PART-001":"PASS","E4R1-PART-002":"FAIL"}))
    def swap(v):
        m={x["assertion_id"].rsplit(":",1)[-1]:x for x in v["assertions"]}; a=m["DIGEST-CANON-001"]["expression"]["checks"][0]; b=m["DIGEST-CANON-002"]["expression"]["checks"][0]; a["arguments"],b["arguments"]=copy.deepcopy(b["arguments"]),copy.deepcopy(a["arguments"])
    cases.append(run_case("SWAPPED_OPERANDS_FOLLOW_VALUES",json_mutator(assertions,swap),{"DIGEST-CANON-001":"PASS","DIGEST-CANON-002":"PASS"}))
    def rename(v): next(x for x in v["rules"] if x["rule_id"]=="PRED-001")["rule_id"]="BOGUS-RULE-ID"
    cases.append(run_case("BOGUS_RULE_ID_OPERAND_DERIVED",json_mutator(rules,rename),{"BOGUS-RULE-ID":"PASS","PRED-002":"PASS"}))
    cases.append(run_case("CACHE_COLLISION_ISOLATED",json_mutator(pred,lambda v:v.__setitem__("global_stage_order","COLLISION")),{"PRED-001":"FAIL","PRED-002":"PASS","PRED-003":"PASS"}))
    cases.append(run_case("SHARED_ARTIFACT_DIFFERENT_POINTER",json_mutator(part,lambda v:v.__setitem__("same_effect_required",False)),{"E4R1-PART-001":"FAIL","E4R1-PART-002":"PASS","E4R1-PART-003":"PASS"}))
    def omit(v):
        m=next(x for x in v["assertions"] if x["assertion_id"].endswith(":PRED-001")); m["expression"]["checks"][0]["arguments"].pop("comparison")
    cases.append(run_case("PROCEDURE_PARAMETER_MISSING_FAIL_CLOSED",json_mutator(assertions,omit),{"PRED-001":"UNEVALUABLE","PRED-002":"PASS"}))
    result={"certificate":"ACCORD-02E4R5_PER_RULE_DIVERGENCE","cases":cases,"pass_count":sum(x["pass"] for x in cases),"fail_count":sum(not x["pass"] for x in cases),"source_repository_write_count":0,"overall_pass":all(x["pass"] for x in cases)}; print(json.dumps(result,sort_keys=True,separators=(",",":"))); raise SystemExit(0 if result["overall_pass"] else 1)
if __name__=="__main__":main()
