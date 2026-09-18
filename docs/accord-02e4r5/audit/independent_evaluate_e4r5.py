#!/usr/bin/env python3
"""Independent, read-only evaluator; imports neither builder nor primary certifier."""
from __future__ import annotations
import copy, hashlib, json
from datetime import datetime
from pathlib import Path
import jsonschema, rfc8785

ROOT=Path(__file__).resolve().parents[3]; D=ROOT/"docs/accord-02e4r5"
def get(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(o): return hashlib.sha256(rfc8785.dumps(o)).hexdigest()
def drop(o,p):
    o=copy.deepcopy(o); q=o; a=p.split("/")[1:]
    for s in a[:-1]: q=q[int(s)] if isinstance(q,list) else q[s]
    if isinstance(q,list): del q[int(a[-1])]
    else: del q[a[-1]]
    return o
def walk(o):
    if isinstance(o,dict):
        if {"kind","id","version"}<=set(o) and set(o)<={"kind","id","version","member_id"} and all(isinstance(o[x],str) for x in ("kind","id","version")): yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
def when(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
def at(value,pointer):
    cur=value
    if pointer=="": return cur
    if not isinstance(pointer,str) or not pointer.startswith("/"): raise KeyError(pointer)
    for raw in pointer.split("/")[1:]:
        token=raw.replace("~1","/").replace("~0","~"); cur=cur[int(token)] if isinstance(cur,list) else cur[token]
    return cur

def evaluate():
    reg=get(D/"accord-02e4r5-object-registry.json"); entries=reg["entries"]; idx={(e["kind"],e["id"],e["version"]):e for e in entries}
    docs={e["id"]:get(ROOT/e["path"]) for e in entries if (ROOT/e["path"]).exists()}; schemas={get(p)["$id"]:get(p) for p in (D/"schema").glob("*.json")}; errors=[]
    for sid,s in schemas.items():
        try: jsonschema.Draft202012Validator.check_schema(s)
        except Exception as x: errors.append("META:"+sid+":"+str(x))
    for e in entries:
        if e["kind"]!="SCHEMA" and e["role"]=="NORMATIVE":
            v=docs[e["id"]]; s=schemas.get(v.get("$schema"))
            if not s: errors.append("NO_SCHEMA:"+e["id"])
            else: errors += ["INSTANCE:"+e["id"]+":"+x.json_path for x in jsonschema.Draft202012Validator(s,format_checker=jsonschema.FormatChecker()).iter_errors(v)]
    cat=docs["urn:moirae:accord-02r5:vector-catalog"]
    for v in cat["vectors"]:
        p=v["target"]["proposition"]; s=schemas[p["schema_ref"]["id"]+":"+p["schema_ref"]["version"]]; errors += ["PROPOSITION:"+v["vector_id"]+":"+x.json_path for x in jsonschema.Draft202012Validator(s,format_checker=jsonschema.FormatChecker()).iter_errors(p)]
    digest_errors=[]
    for n,e in enumerate(entries):
        v=get(ROOT/e["path"]); actual=sha(drop(v,f"/entries/{n}/integrity/digest")) if e["id"]=="urn:moirae:accord-02r5:object-registry" else sha(v)
        if actual!=e["integrity"]["digest"]: digest_errors.append(e["id"])
    pkg=docs["urn:moirae:accord-02r5:specification-package"]; self_value=drop(pkg,"/current_candidate_integrity/digest")
    if sha(self_value)!=pkg["current_candidate_integrity"]["digest"]: digest_errors.append("PACKAGE_SELF")
    unresolved=[]; ref_count=0
    for e in entries:
        if e["role"]!="NORMATIVE": continue
        for r in walk(get(ROOT/e["path"])):
            ref_count+=1; target=idx.get((r["kind"],r["id"],r["version"]));
            if not target or (r.get("member_id") and r["member_id"] not in target.get("members",[])): unresolved.append(r)
    keys=[(e["kind"],e["id"],e["version"]) for e in entries]; identity_ok=len(keys)==len(set(keys)) and all(e["role"]=="NORMATIVE_BOUND_SOURCE" or (get(ROOT/e["path"])["$id"].rsplit(":",1)[0] if e["kind"]=="SCHEMA" else get(ROOT/e["path"]).get("object_id"))==e["id"] for e in entries)
    base=pkg["accepted_base"]; lineage_ok=pkg["package_id"]=="urn:moirae:accord-02r5:specification-package" and pkg["package_version"]=="0.2" and pkg["status"]=="CANDIDATE_UNACCEPTED" and base["package_id"]==pkg["package_id"] and base["package_version"]=="0.1" and sha(get(ROOT/base["path"]))==base["integrity"]["digest"] and pkg["amendment_relation"]=="UNACCEPTED_AMENDMENT_OF_ACCEPTED_0_1"
    rules=docs["urn:moirae:accord-02r5:validation-rules"]["rules"]; graph=docs["urn:moirae:accord-02r5:dependency-graph"]; nodes={r["rule_id"] for r in rules}; edges={(r["rule_id"],x) for r in rules for x in r["depends_on"]}; graph_ok=nodes==set(graph["nodes"]) and edges=={(x["from"],x["to"]) for x in graph["edges"]} and all(b in nodes for a,b in edges)
    accepted=get(ROOT/"docs/accord-02/examples/accord-02c-settlement-test-vectors.json"); aa={x["vector_id"]:x["expected"] for x in accepted["vectors"]}; cc={x["vector_id"]:x["expected"] for x in cat["vectors"]}; expect_ok=aa==cc
    t=docs["urn:moirae:accord-02r5:v013-target"]; e=docs["urn:moirae:accord-02r5:v013-synthetic-evidence"]; pol=docs["urn:moirae:accord-02r5:settlement-profile:conservative"]["negative_policy"]; age=(when(e["verification_time"])-when(e["observed_at"])).total_seconds(); span=(when(t["required_interval"]["as_of"])-when(t["required_interval"]["not_before"])).total_seconds(); target=(t["effect_id"],t["negated_predicate_id"],t["negated_stage"],t["scope"]); v013_ok=(e["effect_id"],e["predicate_id"],e["stage"],e["scope"])==target and when(e["observed_interval"]["not_before"])<=when(t["required_interval"]["not_before"])<=when(t["required_interval"]["as_of"])<=when(e["observed_interval"]["as_of"]) and e["retention_window_seconds"]>=max(span,pol["minimum_retention_seconds"]) and 0<=age<=pol["freshness_max_age_seconds"] and e["consistency_level"] in pol["allowed_consistency_levels"] and e["evidence_class"] in pol["allowed_source_classes"] and not any((x.get("effect_id"),x.get("predicate_id"),x.get("stage"),x.get("scope"))==target for x in e["evidence_universe"])
    primitive_members=set(idx[("REGISTRY","urn:moirae:accord-02r5:primitive-registry","0.2")]["members"]); assertions={x["assertion_id"]:x for x in docs["urn:moirae:accord-02r5:assertion-registry"]["assertions"]}; rr={}
    pred=docs["urn:moirae:accord-02r5:predicate-registry"]; pred_keys=[(x["predicate_id"],x["stage"]) for x in pred["entries"]]; predicate_ok=len(pred_keys)==len(set(pred_keys)) and pred["global_stage_order"]==pred["implicit_transitivity"]=="FORBIDDEN"
    canon=docs["urn:moirae:accord-02r5:canonicalization:rfc8785-jcs"]; canonical_ok=canon["method"]=="RFC8785_JCS" and canon["algorithm"]=="SHA-256" and canon["pointer_semantics"]=="RFC6901"
    part=docs["urn:moirae:accord-02r5:partial-effect-policy"]; partial_ok=part["same_effect_required"] and part["direct_predecessor_required"] and part["implicit_transitivity"]==part["global_stage_order"]=="FORBIDDEN" and len(part["decisions"])==12
    binding=docs["urn:moirae:accord-02r5:source-catalog-binding"]; source_ok=binding["integrity"]["digest"]==sha(get(ROOT/binding["repository_root_path"])) and all(v["source_vector_ref"]["id"]==binding["assigned_catalog_ref"]["id"] for v in cat["vectors"])
    for r in rules:
        if r["scope"]=="DEFERRED_NO_SUBJECT_ARTIFACT": rr[r["rule_id"]]={"rule_id":r["rule_id"],"scope":r["scope"],"missing_subject_roles":r["missing_subject_roles"],"later_lifecycle_stage":r["later_lifecycle_stage"],"status":"DEFERRED_NO_SUBJECT_ARTIFACT"}; continue
        a=assertions.get(r["assertion_ref"].get("member_id")); checks=a and a["expression"]["checks"] or []; values=[]; traces=[]; unevaluable=False
        for c in checks:
            args=c.get("arguments",{}); pid=c["primitive_ref"].get("member_id")
            if pid!="JSON_POINTER_COMPARE" or pid not in primitive_members or not isinstance(args.get("subject"),dict) or args.get("comparison")!="EXACT_EQUAL": unevaluable=True; break
            entry=idx.get((args["subject"].get("kind"),args["subject"].get("id"),args["subject"].get("version")))
            if not entry: unevaluable=True; break
            try: actual=at(get(ROOT/entry["path"]),args["pointer"])
            except (KeyError,IndexError,TypeError,ValueError): values.append(False); continue
            value=type(actual) is type(args["expected"]) and actual==args["expected"]; values.append(value); traces.append({"procedure_id":pid,"normalized_operands":json.loads(rfc8785.dumps(args)),"resolved_object_ids":[entry["id"]],"resolved_artifact_paths":[entry["path"]],"json_pointers":[args["pointer"]],"actual_input_values":[actual],"result":value,"failure_code":None if value else "VALUE_NOT_EQUAL"})
        status="UNEVALUABLE" if unevaluable else "PASS" if values and (all(values) if a["expression"]["operator"]=="ALL" else any(values)) else "FAIL"; rr[r["rule_id"]]={"rule_id":r["rule_id"],"scope":r["scope"],"status":status,"checks":traces}
    counts={"TOTAL_DECLARED_RULES":len(rules),"EXECUTABLE_IN_PACKAGE_0_2":sum(r["scope"]=="EXECUTABLE_IN_PACKAGE_0_2" for r in rules),"DEFERRED_NO_SUBJECT_ARTIFACT":sum(r["scope"]=="DEFERRED_NO_SUBJECT_ARTIFACT" for r in rules),"EXECUTED":sum(x["status"] in ("PASS","FAIL") for x in rr.values()),"PASS":sum(x["status"]=="PASS" for x in rr.values()),"FAIL":sum(x["status"]=="FAIL" for x in rr.values()),"UNEVALUABLE_EXECUTABLE":sum(x["status"]=="UNEVALUABLE" for x in rr.values()),"AMBIGUOUS_EXECUTABLE":0}
    inv={"standards":{"pass":not errors,"errors":errors},"lineage":{"pass":lineage_ok},"identity":{"pass":identity_ok},"references":{"pass":not unresolved,"derived_reference_count":ref_count,"unresolved":unresolved},"digests":{"pass":not digest_errors,"errors":digest_errors},"graph":{"pass":graph_ok},"expectation_stability":{"pass":expect_ok},"v013":{"pass":v013_ok,"result":"NON_OCCURRENCE_SUPPORTED" if v013_ok else "UNKNOWN"}}
    return {"certificate":"ACCORD-02E4R5_INDEPENDENT","imports_primary":False,"imports_builder":False,"read_only":True,"repository_write_count":0,"package_invariants":inv,"rule_counts":counts,"rule_results":rr,"overall_pass":all(x["pass"] for x in inv.values()) and counts["FAIL"]==counts["UNEVALUABLE_EXECUTABLE"]==counts["AMBIGUOUS_EXECUTABLE"]==0 and counts["EXECUTED"]==counts["EXECUTABLE_IN_PACKAGE_0_2"]}
if __name__=="__main__":
    result=evaluate(); print(json.dumps(result,sort_keys=True,separators=(",",":"))); raise SystemExit(0 if result["overall_pass"] else 1)
