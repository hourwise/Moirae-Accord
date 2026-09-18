#!/usr/bin/env python3
"""Read-only primary certifier for the ACCORD-02E4R5 candidate."""
from __future__ import annotations
import argparse, copy, hashlib, json
from datetime import datetime
from pathlib import Path
import jsonschema, rfc8785

ROOT=Path(__file__).resolve().parents[3]; PKG=ROOT/"docs/accord-02e4r5"
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def digest(v): return hashlib.sha256(rfc8785.dumps(v)).hexdigest()
def rm_pointer(v,p):
    v=copy.deepcopy(v); cur=v; parts=p.split("/")[1:]
    for raw in parts[:-1]:
        key=raw.replace("~1","/").replace("~0","~"); cur=cur[int(key)] if isinstance(cur,list) else cur[key]
    key=parts[-1].replace("~1","/").replace("~0","~")
    if isinstance(cur,list): del cur[int(key)]
    else: del cur[key]
    return v
def projected(v,ps):
    for p in ps: v=rm_pointer(v,p)
    return digest(v)
def refs(v,path=""):
    out=[]
    if isinstance(v,dict):
        if {"kind","id","version"}<=set(v) and set(v)<={"kind","id","version","member_id"} and all(isinstance(v[x],str) for x in ("kind","id","version")): out.append((path,v))
        for k,x in v.items(): out.extend(refs(x,path+"/"+k.replace("~","~0").replace("/","~1")))
    elif isinstance(v,list):
        for i,x in enumerate(v): out.extend(refs(x,path+f"/{i}"))
    return out
def iso(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
def pointer_get(value,pointer):
    cur=value
    if pointer=="": return cur
    if not isinstance(pointer,str) or not pointer.startswith("/"): raise KeyError(pointer)
    for raw in pointer.split("/")[1:]:
        key=raw.replace("~1","/").replace("~0","~")
        cur=cur[int(key)] if isinstance(cur,list) else cur[key]
    return cur

class Certifier:
    def __init__(self):
        self.registry=load(PKG/"accord-02e4r5-object-registry.json"); self.entries=self.registry["entries"]
        self.index={(x["kind"],x["id"],x["version"]):x for x in self.entries}
        self.docs={x["id"]:load(ROOT/x["path"]) for x in self.entries if x["path"].endswith(".json") and (ROOT/x["path"]).exists()}
        self.rules=self.docs["urn:moirae:accord-02r5:validation-rules"]["rules"]
        self.assertions={x["assertion_id"]:x for x in self.docs["urn:moirae:accord-02r5:assertion-registry"]["assertions"]}
        self.primitives={x["primitive_id"]:x for x in self.docs["urn:moirae:accord-02r5:primitive-registry"]["primitives"]}
    def resolve(self,r):
        e=self.index.get((r["kind"],r["id"],r["version"])); return bool(e and (not r.get("member_id") or r["member_id"] in e.get("members",[])))
    def standards(self):
        errors=[]; schemas={}
        for p in sorted((PKG/"schema").glob("*.json")):
            s=load(p); schemas[s["$id"]]=s
            try: jsonschema.Draft202012Validator.check_schema(s)
            except Exception as e: errors.append(f"meta:{p.name}:{e}")
        for e in self.entries:
            if e["kind"]=="SCHEMA" or e["role"]!="NORMATIVE": continue
            v=load(ROOT/e["path"]); sid=v.get("$schema"); s=schemas.get(sid)
            if not s: errors.append(f"schema-missing:{e['id']}:{sid}"); continue
            for err in jsonschema.Draft202012Validator(s,format_checker=jsonschema.FormatChecker()).iter_errors(v): errors.append(f"instance:{e['id']}:{err.json_path}:{err.message}")
        cat=self.docs["urn:moirae:accord-02r5:vector-catalog"]
        for v in cat["vectors"]:
            p=v["target"]["proposition"]; sid=p["schema_ref"]["id"]+":"+p["schema_ref"]["version"]
            for err in jsonschema.Draft202012Validator(schemas[sid],format_checker=jsonschema.FormatChecker()).iter_errors(p): errors.append(f"proposition:{v['vector_id']}:{err.json_path}:{err.message}")
        return {"pass":not errors,"schemas":len(schemas),"errors":errors}
    def identity(self):
        keys=[(e["kind"],e["id"],e["version"]) for e in self.entries]; errors=[]
        if len(keys)!=len(set(keys)): errors.append("DUPLICATE_IDENTITY")
        for e in self.entries:
            if e["role"]=="NORMATIVE_BOUND_SOURCE": continue
            p=ROOT/e["path"]
            if not p.exists(): errors.append("MISSING_PATH:"+e["path"]); continue
            v=load(p); actual=v["$id"].rsplit(":",1)[0] if e["kind"]=="SCHEMA" else v.get("object_id")
            if actual!=e["id"]: errors.append("SELF_ID_MISMATCH:"+e["id"])
        return {"pass":not errors,"objects":len(self.entries),"errors":errors}
    def integrity(self):
        errors=[]
        for i,e in enumerate(self.entries):
            v=load(ROOT/e["path"])
            actual=projected(v,[f"/entries/{i}/integrity/digest"]) if e["id"]=="urn:moirae:accord-02r5:object-registry" else digest(v)
            if actual!=e["integrity"]["digest"]: errors.append("DIGEST_MISMATCH:"+e["id"])
        p=self.docs["urn:moirae:accord-02r5:specification-package"]
        if projected(p,p["current_candidate_integrity"]["exclusion_pointers"])!=p["current_candidate_integrity"]["digest"]: errors.append("PACKAGE_SELF_DIGEST")
        return {"pass":not errors,"checked":len(self.entries)+1,"errors":errors}
    def reference_closure(self):
        found=[]; unresolved=[]
        for e in self.entries:
            if e["role"]!="NORMATIVE": continue
            for pointer,r in refs(load(ROOT/e["path"])):
                item={"source":e["id"],"pointer":pointer,"reference":r}; found.append(item)
                if not self.resolve(r): unresolved.append(item)
        return {"pass":not unresolved,"derived_reference_count":len(found),"unresolved":unresolved}
    def graph(self):
        g=self.docs["urn:moirae:accord-02r5:dependency-graph"]; nodes={r["rule_id"] for r in self.rules}; edges={(r["rule_id"],d) for r in self.rules for d in r["depends_on"]}; declared={(x["from"],x["to"]) for x in g["edges"]}; dangling=sorted((a,b) for a,b in edges if b not in nodes); visiting=set(); done=set()
        def visit(n):
            if n in visiting:return False
            if n in done:return True
            visiting.add(n)
            if any(a==n and not visit(b) for a,b in edges):return False
            visiting.remove(n); done.add(n); return True
        acyclic=all(visit(n) for n in nodes); return {"pass":nodes==set(g["nodes"]) and edges==declared and not dangling and acyclic,"node_count":len(nodes),"edge_count":len(edges),"dangling":dangling,"acyclic":acyclic}
    def lineage(self):
        p=self.docs["urn:moirae:accord-02r5:specification-package"]; b=p["accepted_base"]; base=load(ROOT/b["path"]); checks={"family":p["package_id"]=="urn:moirae:accord-02r5:specification-package","version":p["package_version"]=="0.2","status":p["status"]=="CANDIDATE_UNACCEPTED","base_family":b["package_id"]==p["package_id"],"base_version":b["package_version"]=="0.1","base_digest":digest(base)==b["integrity"]["digest"],"relation":p["amendment_relation"]=="UNACCEPTED_AMENDMENT_OF_ACCEPTED_0_1"}; return {"pass":all(checks.values()),"checks":checks}
    def expectation(self):
        accepted=load(ROOT/"docs/accord-02/examples/accord-02c-settlement-test-vectors.json"); cand=self.docs["urn:moirae:accord-02r5:vector-catalog"]; am={x["vector_id"]:x for x in accepted["vectors"]}; cm={x["vector_id"]:x for x in cand["vectors"]}; errors=[vid for vid,a in am.items() if vid not in cm or a["expected"]!=cm[vid]["expected"]]; axes={k for x in accepted["vectors"] for k in x["expected"]}; reasons=[x for v in accepted["vectors"] for x in v["expected"].get("reason_codes",[])]; prohibitions=[x for v in accepted["vectors"] for x in v["expected"].get("must_not_conclude",[])]; return {"pass":not errors and set(am)==set(cm),"vectors_preserved":len(set(am)&set(cm)),"expectation_axes":len(axes),"reason_codes":len(reasons),"prohibitions":len(prohibitions),"changed":errors}
    def v013(self):
        t=self.docs["urn:moirae:accord-02r5:v013-target"]; e=self.docs["urn:moirae:accord-02r5:v013-synthetic-evidence"]; p=self.docs["urn:moirae:accord-02r5:settlement-profile:conservative"]["negative_policy"]; duration=(iso(t["required_interval"]["as_of"])-iso(t["required_interval"]["not_before"])).total_seconds(); age=(iso(e["verification_time"])-iso(e["observed_at"])).total_seconds(); target=(t["effect_id"],t["negated_predicate_id"],t["negated_stage"],json.dumps(t["scope"],sort_keys=True)); contradictions={x.get("evidence_id") for x in e["evidence_universe"] if (x.get("effect_id"),x.get("predicate_id"),x.get("stage"),json.dumps(x.get("scope"),sort_keys=True))==target}; checks={"target":(e["effect_id"],e["predicate_id"],e["stage"],e["scope"])==(t["effect_id"],t["negated_predicate_id"],t["negated_stage"],t["scope"]),"interval_inclusive":iso(e["observed_interval"]["not_before"])<=iso(t["required_interval"]["not_before"])<=iso(t["required_interval"]["as_of"])<=iso(e["observed_interval"]["as_of"]),"retention":e["retention_window_seconds"]>=max(duration,p["minimum_retention_seconds"]),"freshness_nonnegative_bounded":0<=age<=p["freshness_max_age_seconds"],"profile_policy":e["consistency_level"] in p["allowed_consistency_levels"] and e["evidence_class"] in p["allowed_source_classes"] and e["read_scope_complete"] and e["read_semantics"]=="COMPLETE_LEDGER_QUERY","no_same_target_positive":not contradictions,"synthetic_provenance":e["fixture_status"]=="SYNTHETIC_CANDIDATE_0_2_NOT_ACCEPTED_HISTORY"}; return {"pass":all(checks.values()),"result":"NON_OCCURRENCE_SUPPORTED" if all(checks.values()) else "UNKNOWN","checks":checks}
    def predicate_contract(self):
        p=self.docs["urn:moirae:accord-02r5:predicate-registry"]; keys=[(x["predicate_id"],x["stage"]) for x in p["entries"]]
        return len(keys)==len(set(keys)) and p["global_stage_order"]==p["implicit_transitivity"]=="FORBIDDEN" and all(self.resolve(x["proposition_schema_ref"]) and (x["kind"]!="NEGATIVE_SCOPE" or self.resolve(x["negative_requirement_map_ref"])) for x in p["entries"])
    def canonical_contract(self):
        c=self.docs["urn:moirae:accord-02r5:canonicalization:rfc8785-jcs"]; cat=self.docs["urn:moirae:accord-02r5:vector-catalog"]
        return c["method"]=="RFC8785_JCS" and c["algorithm"]=="SHA-256" and c["pointer_semantics"]=="RFC6901" and projected(cat,["/integrity/content_digest"])==cat["integrity"]["content_digest"].removeprefix("sha-256:") and all(projected(v["target"]["proposition"],["/integrity/content_digest"])==v["target"]["proposition"]["integrity"]["content_digest"].removeprefix("sha-256:") for v in cat["vectors"])
    def source_contract(self):
        b=self.docs["urn:moirae:accord-02r5:source-catalog-binding"]; cat=self.docs["urn:moirae:accord-02r5:vector-catalog"]
        return b["integrity"]["digest"]==digest(load(ROOT/b["repository_root_path"])) and all(v["source_vector_ref"]["id"]==b["assigned_catalog_ref"]["id"] and self.resolve(v["source_vector_ref"]) for v in cat["vectors"])
    def partial_contract(self):
        p=self.docs["urn:moirae:accord-02r5:partial-effect-policy"]; required={"VALID_SUPPORTED_DIRECT_PREDECESSOR","TARGET_ALREADY_SUPPORTED","NO_PREDECESSOR","WRONG_EFFECT","UNSUPPORTED_TUPLE","UNKNOWN_TUPLE","WRONG_STAGE","SELF_EDGE","CYCLE","DANGLING_TARGET","INCOMPATIBLE_EVIDENCE","INADMISSIBLE_EVIDENCE"}
        return set(p["decisions"])==required and p["same_effect_required"] and p["direct_predecessor_required"] and p["implicit_transitivity"]==p["global_stage_order"]=="FORBIDDEN"
    def execute_rule(self,r):
        if r["scope"]!="EXECUTABLE_IN_PACKAGE_0_2":return {"rule_id":r["rule_id"],"scope":"DEFERRED_NO_SUBJECT_ARTIFACT","missing_subject_roles":r["missing_subject_roles"],"later_lifecycle_stage":r["later_lifecycle_stage"],"status":"DEFERRED_NO_SUBJECT_ARTIFACT"}
        if not r.get("subject_bindings") or any(not self.resolve(x) for x in r["subject_bindings"]):return {"status":"UNEVALUABLE","failure":"SUBJECT_BINDING"}
        a=self.assertions.get(r["assertion_ref"].get("member_id"))
        if not a:return {"status":"UNEVALUABLE","failure":"ASSERTION"}
        results=[]; traces=[]
        for check in a["expression"]["checks"]:
            pid=check["primitive_ref"].get("member_id"); prim=self.primitives.get(pid); args=check.get("arguments",{})
            if not prim or any(x not in args for x in prim["argument_schema"]["required"]):return {"status":"UNEVALUABLE","failure":"PRIMITIVE_OR_ARGUMENT"}
            if pid!="JSON_POINTER_COMPARE" or not isinstance(args.get("subject"),dict) or not isinstance(args.get("pointer"),str) or args.get("comparison")!="EXACT_EQUAL":return {"status":"UNEVALUABLE","failure":"INVALID_ARGUMENT"}
            entry=self.index.get((args["subject"]["kind"],args["subject"]["id"],args["subject"]["version"]))
            if not entry:return {"status":"UNEVALUABLE","failure":"SUBJECT_RESOLUTION_FAILED"}
            try: actual=pointer_get(load(ROOT/entry["path"]),args["pointer"])
            except (KeyError,IndexError,TypeError,ValueError): return {"status":"FAIL","failure":"POINTER_RESOLUTION_FAILED"}
            result=type(actual) is type(args["expected"]) and actual==args["expected"]; results.append(result); traces.append({"procedure_id":pid,"normalized_operands":json.loads(rfc8785.dumps(args)),"resolved_object_ids":[entry["id"]],"resolved_artifact_paths":[entry["path"]],"json_pointers":[args["pointer"]],"actual_input_values":[actual],"result":result,"failure_code":None if result else "VALUE_NOT_EQUAL"})
        ok=all(results) if a["expression"]["operator"]=="ALL" else any(results); return {"rule_id":r["rule_id"],"scope":r["scope"],"status":"PASS" if ok else "FAIL","checks":traces}
    def run(self):
        invariants={"standards":self.standards(),"lineage":self.lineage(),"identity":self.identity(),"references":self.reference_closure(),"digests":self.integrity(),"graph":self.graph(),"expectation_stability":self.expectation(),"v013":self.v013(),"predicate_contract":{"pass":self.predicate_contract()},"canonicalization_contract":{"pass":self.canonical_contract()},"partial_effect_contract":{"pass":self.partial_contract()},"source_catalog_binding":{"pass":self.source_contract()}}; rr={r["rule_id"]:self.execute_rule(r) for r in self.rules}; ex=[x for x in rr.values() if x["status"]!="DEFERRED_NO_SUBJECT_ARTIFACT"]; counts={"TOTAL_DECLARED_RULES":len(rr),"EXECUTABLE_IN_PACKAGE_0_2":sum(r["scope"]=="EXECUTABLE_IN_PACKAGE_0_2" for r in self.rules),"DEFERRED_NO_SUBJECT_ARTIFACT":sum(r["scope"]=="DEFERRED_NO_SUBJECT_ARTIFACT" for r in self.rules),"EXECUTED":sum(x["status"] in ("PASS","FAIL") for x in ex),"PASS":sum(x["status"]=="PASS" for x in ex),"FAIL":sum(x["status"]=="FAIL" for x in ex),"UNEVALUABLE_EXECUTABLE":sum(x["status"]=="UNEVALUABLE" for x in ex),"AMBIGUOUS_EXECUTABLE":0}; return {"certificate":"ACCORD-02E4R5_PRIMARY","read_only":True,"repository_write_count":0,"package_invariants":invariants,"rule_counts":counts,"rule_results":rr,"overall_pass":all(x["pass"] for x in invariants.values()) and counts["FAIL"]==counts["UNEVALUABLE_EXECUTABLE"]==0 and counts["EXECUTED"]==counts["EXECUTABLE_IN_PACKAGE_0_2"]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out-dir"); args=ap.parse_args()
    if args.out_dir:
        out=Path(args.out_dir).resolve()
        if PKG.resolve()==out or PKG.resolve() in out.parents: raise SystemExit("output inside protected candidate source is forbidden")
    result=Certifier().run(); print(json.dumps(result,sort_keys=True,separators=(",",":"))); raise SystemExit(0 if result["overall_pass"] else 1)
if __name__=="__main__":main()
