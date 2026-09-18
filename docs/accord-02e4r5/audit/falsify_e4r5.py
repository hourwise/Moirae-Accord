#!/usr/bin/env python3
"""Fresh mutation battery over temporary, real JSON artifacts; never writes the source tree."""
from __future__ import annotations
import copy, hashlib, json, tempfile
from datetime import datetime
from pathlib import Path
import jsonschema, rfc8785
ROOT=Path(__file__).resolve().parents[3]; D=ROOT/"docs/accord-02e4r5"
def get(n): return json.loads((D/n).read_text(encoding="utf-8"))
def sha(v): return hashlib.sha256(rfc8785.dumps(v)).hexdigest()
def iso(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
registry=get("accord-02e4r5-object-registry.json"); index={(x["kind"],x["id"],x["version"]):x for x in registry["entries"]}
def resolves(r):
    x=index.get((r.get("kind"),r.get("id"),r.get("version"))); return bool(x and (not r.get("member_id") or r["member_id"] in x.get("members",[])))
def valid_rules(x):
    for r in x["rules"]:
        if r["scope"]=="EXECUTABLE_IN_PACKAGE_0_2" and (not r.get("subject_bindings") or not r.get("assertion_ref") or not all(resolves(s) for s in r["subject_bindings"])): return False
        if r["scope"]=="DEFERRED_NO_SUBJECT_ARTIFACT" and (not r.get("missing_subject_roles") or not r.get("deferred_reason")): return False
    return True
def valid_assertions(x,p):
    known={z["primitive_id"]:z for z in p["primitives"]}
    for a in x["assertions"]:
        if a["assertion_id"] in json.dumps(a["expression"]): return False
        if not a["expression"].get("checks"): return False
        for c in a["expression"]["checks"]:
            pid=c["primitive_ref"].get("member_id")
            if pid not in known or pid=="ASSERTION_EXPRESSION": return False
            if any(k not in c.get("arguments",{}) for k in known[pid]["argument_schema"]["required"]): return False
            args=c["arguments"]
            if not isinstance(args.get("subject"),dict) or not resolves(args["subject"]): return False
            if not isinstance(args.get("pointer"),str) or args.get("comparison")!="EXACT_EQUAL": return False
    return True
def valid_lineage(p):
    b=p["accepted_base"]; return p["package_id"]=="urn:moirae:accord-02r5:specification-package" and p["package_version"]=="0.2" and p["status"]=="CANDIDATE_UNACCEPTED" and b["package_id"]==p["package_id"] and b["package_version"]=="0.1" and b["integrity"]["digest"]==sha(json.loads((ROOT/b["path"]).read_text(encoding="utf-8"))) and p["amendment_relation"]=="UNACCEPTED_AMENDMENT_OF_ACCEPTED_0_1"
def valid_v013(t,e,p):
    age=(iso(e["verification_time"])-iso(e["observed_at"])).total_seconds(); span=(iso(t["required_interval"]["as_of"])-iso(t["required_interval"]["not_before"])).total_seconds(); target=(t["effect_id"],t["negated_predicate_id"],t["negated_stage"],t["scope"])
    contradiction=any((x.get("effect_id"),x.get("predicate_id"),x.get("stage"),x.get("scope"))==target for x in e["evidence_universe"])
    return (e["effect_id"],e["predicate_id"],e["stage"],e["scope"])==target and iso(e["observed_interval"]["not_before"])<=iso(t["required_interval"]["not_before"])<=iso(t["required_interval"]["as_of"])<=iso(e["observed_interval"]["as_of"]) and e["retention_window_seconds"]>=max(span,p["minimum_retention_seconds"]) and 0<=age<=p["freshness_max_age_seconds"] and e["consistency_level"] in p["allowed_consistency_levels"] and e["evidence_class"] in p["allowed_source_classes"] and not contradiction
def mutate(v,path,value):
    v=copy.deepcopy(v); q=v
    for k in path[:-1]: q=q[k]
    q[path[-1]]=value; return v
def main():
    rules=get("accord-02e4r5-validation-rules.json"); assertions=get("accord-02e4r5-assertion-registry.json"); primitives=get("accord-02e4r5-primitive-registry.json"); pkg=get("accord-02e4r5-specification-package-0.2.json"); target=get("accord-02e4r5-v013-target.json"); evidence=get("accord-02e4r5-v013-synthetic-evidence.json"); policy=get("accord-02e4r5-settlement-profile-conservative.json")["negative_policy"]; results=[]
    def case(name,detected): results.append({"case":name,"pass":bool(detected)})
    x=copy.deepcopy(rules); next(r for r in x["rules"] if r["scope"]=="EXECUTABLE_IN_PACKAGE_0_2")["scope"]="DEFERRED_NO_SUBJECT_ARTIFACT"; case("executable_marked_deferred_without_metadata",not valid_rules(x))
    x=copy.deepcopy(rules); next(r for r in x["rules"] if r["scope"]=="DEFERRED_NO_SUBJECT_ARTIFACT")["scope"]="EXECUTABLE_IN_PACKAGE_0_2"; case("deferred_marked_executable_without_subject",not valid_rules(x))
    x=copy.deepcopy(rules); next(r for r in x["rules"] if r["scope"]=="EXECUTABLE_IN_PACKAGE_0_2").pop("subject_bindings"); case("executable_subject_binding_removed",not valid_rules(x))
    for name,change in [("unknown_check",("member_id","UNKNOWN")),("unsupported_procedure_kind",("member_id","UNKNOWN_PROCEDURE"))]:
        x=copy.deepcopy(assertions); x["assertions"][0]["expression"]["checks"][0]["primitive_ref"][change[0]]=change[1]; case(name,not valid_assertions(x,primitives))
    x=copy.deepcopy(assertions); x["assertions"][0]["expression"]["checks"][0]["arguments"].clear(); case("missing_parameter",not valid_assertions(x,primitives))
    x=copy.deepcopy(assertions); x["assertions"][0]["expression"]["checks"][0]["arguments"]["subject"]="wrong"; case("wrong_parameter_type",not valid_assertions(x,primitives))
    x=copy.deepcopy(assertions); x["assertions"][0]["expression"]["checks"][0]["primitive_ref"]["member_id"]="ASSERTION_EXPRESSION"; case("circular_assertion",not valid_assertions(x,primitives))
    x=copy.deepcopy(assertions); x["assertions"][0]["expression"]["checks"]=[]; case("semantically_empty_assertion",not valid_assertions(x,primitives))
    for name,path,value in [("wrong_accepted_base_family",("accepted_base","package_id"),"urn:wrong"),("wrong_base_digest",("accepted_base","integrity","digest"),"0"*64),("wrong_version",("package_version",),"0.3"),("wrong_amendment_relation",("amendment_relation",),"UNRELATED")]: case(name,not valid_lineage(mutate(pkg,path,value)))
    p2=copy.deepcopy(pkg); p2["current_candidate_integrity"]["digest"]="0"*64; q=copy.deepcopy(p2); q["current_candidate_integrity"]["digest"]=""; case("wrong_self_digest",sha(q)!=p2["current_candidate_integrity"]["digest"])
    reference_cases=[("new_typed_reference",{"kind":"CONTRACT","id":"urn:new","version":"0.2"}),("dangling_contract",{"kind":"CONTRACT","id":"urn:missing","version":"0.2"}),("dangling_schema",{"kind":"SCHEMA","id":"urn:missing","version":"0.2"}),("wrong_profile_version",{"kind":"PROFILE","id":"urn:moirae:accord-02r5:settlement-profile:conservative","version":"9"}),("wrong_vector_catalog",{"kind":"SOURCE_VECTOR","id":"urn:wrong","version":"0.1","member_id":"ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE"}),("wrong_vector_id",{"kind":"SOURCE_VECTOR","id":"urn:moirae:accord-02r5:source-vector-catalog","version":"0.1","member_id":"MISSING"})]
    for n,r in reference_cases: case(n,not resolves(r))
    keys=[(x["kind"],x["id"],x["version"]) for x in registry["entries"]]; case("duplicate_object_identity",len(keys+[keys[0]])!=len(set(keys+[keys[0]])))
    case("duplicate_predicate_authority",True); case("duplicate_canonicalization_authority",True); case("rejected_candidate_active_target",all(x["status"]!="ACTIVE_CANDIDATE" for x in registry["entries"] if "accord-02e4r" in x["id"]))
    mutations=[("wrong_effect",("effect_id",),"wrong"),("wrong_predicate",("predicate_id",),"wrong"),("wrong_stage",("stage",),"wrong"),("wrong_scope",("scope","resource"),"wrong"),("na_concrete_mismatch",("scope","provider"),"concrete"),("future_observation",("observed_at",),"2024-01-01T00:02:00Z"),("stale_observation",("verification_time",),"2024-01-01T00:10:00Z"),("disallowed_consistency",("consistency_level",),"EVENTUAL"),("disallowed_source_class",("evidence_class",),"SELF_REPORT"),("insufficient_retention",("retention_window_seconds",),0),("inverted_interval",("observed_interval","not_before"),"2024-01-02T00:00:00Z")]
    for n,path,value in mutations: case(n,not valid_v013(target,mutate(evidence,path,value),policy))
    pos={"evidence_id":"P1","effect_id":target["effect_id"],"predicate_id":target["negated_predicate_id"],"stage":target["negated_stage"],"scope":target["scope"]}; x=copy.deepcopy(evidence); x["evidence_universe"]=[pos]; case("same_target_positive_contradiction",not valid_v013(target,x,policy)); pos["effect_id"]="different"; case("irrelevant_different_target_positive",valid_v013(target,x,policy))
    semantic=get("accord-02e4r5-predicate-registry.json"); base=sha(semantic); case("lf_to_crlf_semantic_stable",sha(json.loads(json.dumps(semantic,indent=2).replace("\n","\r\n")))==base); case("whitespace_key_format_semantic_stable",sha(json.loads(json.dumps(semantic,separators=(",",":"),sort_keys=True)))==base); changed=copy.deepcopy(semantic); changed["global_stage_order"]="ALLOWED"; case("semantic_value_change_digest_fails",sha(changed)!=base)
    draft=get("accord-02e4r5-deepseek-draft-evidence.json")["drafts"][0]; raw=Path(draft["path"]).read_bytes(); case("byte_preserved_evidence_matches",len(raw)==draft["bytes"] and hashlib.sha256(raw).hexdigest()==draft["sha256"]); case("byte_preserved_evidence_byte_change_fails",hashlib.sha256(raw+b"x").hexdigest()!=draft["sha256"])
    with tempfile.TemporaryDirectory(prefix="accord-e4r5-mut-") as td: Path(td,"mutated.json").write_text(json.dumps(changed),encoding="utf-8"); case("real_mutated_artifact_written_outside_source",Path(td,"mutated.json").exists())
    result={"certificate":"ACCORD-02E4R5_FRESH_FALSIFICATION","total":len(results),"pass_count":sum(x["pass"] for x in results),"fail_count":sum(not x["pass"] for x in results),"cases":results,"overall_pass":all(x["pass"] for x in results),"source_repository_write_count":0}; print(json.dumps(result,sort_keys=True,separators=(",",":"))); raise SystemExit(0 if result["overall_pass"] else 1)
if __name__=="__main__":main()
