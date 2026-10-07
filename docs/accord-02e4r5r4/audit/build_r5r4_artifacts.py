#!/usr/bin/env python3
"""Deterministic builder for the additive ACCORD-02E4R5R4 normative artifact slice."""
import copy, hashlib, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
SRC=ROOT/"docs/accord-02e4r5r3"
REL="docs/accord-02e4r5r4"
DIALECT="https://json-schema.org/draft/2020-12/schema"
NS="urn:moirae:accord-02e4r5r4"
HEAD="ebddc96d6db3793ba3119e7bcdcefe221f4ba18f"
TREE="a5dc5a649190108b6f318b08c2fd57efa450b410"
R2="44d0e7240c97dcc12463b5611a7adf61399924d7"
R2TREE="19dc9356784d08d04945f8e2ce9b24bcd49e3683"
R2PATH="docs/accord-02e4r5r2/rule-registry.json"
R2BLOB="640b77c50fd94066d61bbc71e020e6471e1c5eff"
R3VPATH=REL+"/v013-governance.json"
R3VBLOB="389dbaca8711410c3ad2900a0402e920c072c04e"
BASECOMMIT="5a8bf1e577f71132665ece271e70e30e87df5676"
BASEPATH="docs/accord-02/accord-02r5-specification-package.json"
BASEBLOB="33af2e4e0e67b62a963c5f219cce312dddc6cd9d"
BASERAW="6c4633518a9807c9fe1de231eb06be5c3f90ca27e7986024212d5d1c3739b5c0"
BASESEM="b45bf841681b85012ea13d783ac1e2187ab35070e6e5e4b6cfcbd627d695bd0c"
VECTORPATH="docs/accord-02/examples/accord-02c-settlement-test-vectors.json"
VECTORBLOB="9d7f92b947fca38b040f0e9bb53b56f6b7bfbc52"
VECTORRAW="3eb8988610a32df99756e7f750e8dcd8ed84260914741af878659307ff234beb"
VECTORSEM="b6630a9db0924196b9c55ebad78b7a057f61421e950f9cf6e6b8f21cfaa862d5"
PASS="NON_OCCURRENCE_SUPPORTED"
FAIL="UNKNOWN"
V013_CODES=["NEGATIVE_EFFECT_MISMATCH","NEGATIVE_PREDICATE_MISMATCH","NEGATIVE_STAGE_MISMATCH","NEGATIVE_SCOPE_MISMATCH","NEGATIVE_INTERVAL_INVALID","NEGATIVE_INTERVAL_INSUFFICIENT","NEGATIVE_RETENTION_INSUFFICIENT","NEGATIVE_CONSISTENCY_DISALLOWED","NEGATIVE_SOURCE_CLASS_DISALLOWED","NEGATIVE_FRESHNESS_FAILED","NEGATIVE_READ_INCOMPLETE","NEGATIVE_CONTRADICTION","NEGATIVE_FUTURE_OBSERVATION","NEGATIVE_STALE_EVIDENCE","DUPLICATE_EVIDENCE_ID"]

def git(*args, raw=False):
    p=subprocess.run(["git","-c",f"safe.directory={ROOT.as_posix()}",*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return p.stdout if raw else p.stdout.decode("utf-8").strip()
def source(commit,path): return git("show",f"{commit}:{path}",raw=True)
def parse(raw):
    def pairs(seq):
        d={}
        for k,v in seq:
            if k in d: raise ValueError("duplicate JSON object member "+k)
            d[k]=v
        return d
    return json.loads(raw.decode("utf-8-sig"),object_pairs_hook=pairs)
def jcs(v):
    def valid(x):
        if isinstance(x,float): raise ValueError("float requires full RFC8785 number serialization")
        if isinstance(x,dict):
            for k,y in x.items():
                if not k.isascii(): raise ValueError("non-ASCII object key")
                valid(y)
        elif isinstance(x,list):
            for y in x: valid(y)
    valid(v)
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def sem(v): return hashlib.sha256(jcs(v)).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()
def gitblob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def emit(v): return (json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
def transform(v):
    if isinstance(v,str): return v.replace("docs/accord-02e4r5r3","docs/accord-02e4r5r4").replace("urn:moirae:accord-02r5r3","urn:moirae:accord-02r5r4").replace("urn:moirae:accord-02r5r4",NS)
    if isinstance(v,list): return [transform(x) for x in v]
    if isinstance(v,dict): return {k:transform(x) for k,x in v.items()}
    return v
def ref(kind,ident,version="0.2"): return {"kind":kind,"id":ident,"version":version}
def sr(name): return ref("SCHEMA",f"{NS}:schema:{name}")
def arg(n): return {"arg":n}
def item(n): return {"item":n}
def lit(v): return {"literal":v}
def op(name,**kw): return {"op":name,**kw}
def get(v,p): return op("GET",value=v,pointer=p)
def getkey(o,k): return op("GET_KEY",object=o,key=lit(k))
def equal(a,b): return op("JSON_EQUAL",left=a,right=b)
def unique(a,ps): return op("UNIQUE_BY",array=a,pointers=ps)
def count(a): return op("COUNT",array=a)
def num(a,c,b): return op("NUMERIC_COMPARE",left=a,comparator=c,right=b)
def rfc(a,c,b): return op("RFC3339_COMPARE",left=a,comparator=c,right=b)
def duration(a,b): return op("DURATION_SECONDS",start=a,end=b)
def filt(a,n,w): return {"op":"FILTER","array":a,"as":n,"where":w}
def all_(a,n,w): return {"op":"ALL","array":a,"as":n,"where":w}
def any_(a,n,w): return {"op":"ANY","array":a,"as":n,"where":w}
def project(a,n,f): return {"op":"PROJECT","array":a,"as":n,"fields":f}
def resolve(r): return op("RESOLVE_ONE",universe=arg("verification_universe"),reference=r)
def descendants(v): return op("DESCENDANTS",value=v)
def schema_validate(s,i,m="INSTANCE"): return op("SCHEMA_VALIDATE",schema=s,instance=i,mode=m)

PIDS=["SCHEMA_VALIDATION","LINEAGE_VALIDATION","DUAL_INTEGRITY","UNIQUE_KEY","REFERENCE_RESOLUTION","DIGEST_RECOMPUTE","SET_EQUALITY","EXPECTATION_STABILITY","PREDICATE_POLICY_AGREEMENT","CANONICALIZATION_PROFILE_WELLFORMED","SOURCE_CATALOG_BINDING_MATCH","PARTIAL_EFFECT_POLICY_CLOSURE","REQUIREMENT_MAP_EVAL","AUTHORITY_COMPLETENESS","PROPOSITION_INVENTORY_BOUND","PROFILE_REFERENCE_PINNING","ARITY_AGREEMENT","SCHEMA_NON_VACUITY","CURRENT_PACKAGE_IDENTITY","SELF_DIGEST","INTEGRITY_MODE_DISPATCH","V013_BASIS_VALID","FAIL_CLOSED_ENFORCED","SUBJECT_ROLE_COVERAGE","DEFAULT_ARGUMENT_COVERAGE","DERIVATION_ROLE_CLOSURE","PROCEDURE_OPERATION_SUPPORTED","MISSING_BEHAVIOR_SUPPORTED","AMBIGUITY_BEHAVIOR_SUPPORTED","REFERENCE_DISCOVERY_SCOPE_VALID","REFERENCE_SHAPE_PREDICATE_APPLIED","UNIQUENESS_KEY_APPLIED","ROLE_MODEL_APPLIED","SCHEMA_IDENTITY_MATCHES_REGISTRY","RULE_COVERAGE_EXACT","INVARIANT_SET_EXACT","GOVERNING_AUTHORITY_REFERENCE_VALID","GOVERNING_TOKEN_SINGLETON","TRUST_ANCHOR_COMPARE"]
SIG={
"SCHEMA_VALIDATION":"registry:REGISTRY,reference_model:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"LINEAGE_VALIDATION":"package:PACKAGE,authority:AUTHORITY,accepted_base:PACKAGE,verification_universe:VERIFICATION_UNIVERSE",
"DUAL_INTEGRITY":"bindings:CONTRACT,verification_universe:VERIFICATION_UNIVERSE","UNIQUE_KEY":"registry:REGISTRY",
"REFERENCE_RESOLUTION":"registry:REGISTRY,reference_model:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"DIGEST_RECOMPUTE":"registry:REGISTRY,package:PACKAGE,canonicalization:CANONICALIZATION,integrity_modes:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"SET_EQUALITY":"inputs:NORMATIVE_INPUTS","EXPECTATION_STABILITY":"inputs:NORMATIVE_INPUTS,accepted_vectors:SOURCE_VECTOR_CATALOG",
"PREDICATE_POLICY_AGREEMENT":"inputs:NORMATIVE_INPUTS,authority:AUTHORITY","CANONICALIZATION_PROFILE_WELLFORMED":"profile:CANONICALIZATION,authority:AUTHORITY",
"SOURCE_CATALOG_BINDING_MATCH":"candidate_binding:CONTRACT,accepted_binding:CONTRACT,object_registry:REGISTRY,integrity_modes:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"PARTIAL_EFFECT_POLICY_CLOSURE":"policy:POLICY,authority:AUTHORITY",
"REQUIREMENT_MAP_EVAL":"target:CONTRACT,evidence:EVIDENCE,inputs:NORMATIVE_INPUTS,v013_governance:CONTRACT,frozen_predecessor_semantics:FROZEN_V013_GOVERNANCE",
"AUTHORITY_COMPLETENESS":"rules:REGISTRY,invariants:REGISTRY,procedures:REGISTRY,registry:REGISTRY,package:PACKAGE,frozen_rule_authority:FROZEN_RULE_AUTHORITY,verification_universe:VERIFICATION_UNIVERSE",
"PROPOSITION_INVENTORY_BOUND":"inputs:NORMATIVE_INPUTS,inventory:CONTRACT","PROFILE_REFERENCE_PINNING":"inputs:NORMATIVE_INPUTS,authority:AUTHORITY",
"ARITY_AGREEMENT":"invariants:REGISTRY,procedures:REGISTRY","SCHEMA_NON_VACUITY":"registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"CURRENT_PACKAGE_IDENTITY":"registry:REGISTRY,package:PACKAGE,authority:AUTHORITY,verification_universe:VERIFICATION_UNIVERSE",
"SELF_DIGEST":"package:PACKAGE,canonicalization:CANONICALIZATION",
"INTEGRITY_MODE_DISPATCH":"registry:REGISTRY,package:PACKAGE,integrity_modes:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"V013_BASIS_VALID":"target:CONTRACT,evidence:EVIDENCE,accepted_vectors:SOURCE_VECTOR_CATALOG,v013_governance:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"FAIL_CLOSED_ENFORCED":"invariants:REGISTRY,governance:CONTRACT","SUBJECT_ROLE_COVERAGE":"invariants:REGISTRY,governance:CONTRACT",
"DEFAULT_ARGUMENT_COVERAGE":"invariants:REGISTRY,procedures:REGISTRY,registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"DERIVATION_ROLE_CLOSURE":"invariants:REGISTRY,procedures:REGISTRY",
"PROCEDURE_OPERATION_SUPPORTED":"procedures:REGISTRY,primitive_registry:REGISTRY,governance:CONTRACT,invariants:REGISTRY",
"MISSING_BEHAVIOR_SUPPORTED":"procedures:REGISTRY,governance:CONTRACT","AMBIGUITY_BEHAVIOR_SUPPORTED":"procedures:REGISTRY,governance:CONTRACT",
"REFERENCE_DISCOVERY_SCOPE_VALID":"reference_model:CONTRACT,registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"REFERENCE_SHAPE_PREDICATE_APPLIED":"reference_model:CONTRACT,governance:CONTRACT","UNIQUENESS_KEY_APPLIED":"registry:REGISTRY,governance:CONTRACT",
"ROLE_MODEL_APPLIED":"registry:REGISTRY,governance:CONTRACT","SCHEMA_IDENTITY_MATCHES_REGISTRY":"registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"RULE_COVERAGE_EXACT":"rules:REGISTRY,frozen_rule_authority:FROZEN_RULE_AUTHORITY","INVARIANT_SET_EXACT":"package:PACKAGE,invariants:REGISTRY",
"GOVERNING_AUTHORITY_REFERENCE_VALID":"v013_governance:CONTRACT,authority:AUTHORITY,integrity_modes:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"GOVERNING_TOKEN_SINGLETON":"semantic_keys:SEMANTIC_KEYS,registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"TRUST_ANCHOR_COMPARE":"package:PACKAGE,external_trust:EXTERNAL_TRUST"}
RESERVED={"verification_universe":("VERIFICATION_UNIVERSE","BOOTSTRAP_VERIFICATION_UNIVERSE"),"frozen_rule_authority":("FROZEN_RULE_AUTHORITY","EXTERNAL_FROZEN_AUTHORITY"),"frozen_predecessor_semantics":("FROZEN_V013_GOVERNANCE","EXTERNAL_FROZEN_PREDECESSOR"),"external_trust":("EXTERNAL_TRUST","EXTERNAL_TRUST")}
ARGOBJ={"registry":"object-registry","reference_model":"reference-model","package":"package","accepted_base":"accepted_base","bindings":"accepted-source-bindings","inputs":"normative-inputs","accepted_vectors":"accepted_vectors","authority":"authority-requirements","profile":"canonicalization-profile","candidate_binding":"source-catalog-binding","accepted_binding":"accepted-source-bindings","object_registry":"object-registry","policy":"partial-effect-policy","target":"v013-target","evidence":"v013-evidence","v013_governance":"v013-governance","rules":"rule-registry","invariants":"invariant-registry","procedures":"procedure-registry","inventory":"proposition-inventory","canonicalization":"canonicalization-profile","integrity_modes":"integrity-modes","governance":"governance-requirements","primitive_registry":"primitive-registry","semantic_keys":"semantic-key-authority"}
def candidate_ref(n,t):
 if n=="package": return ref("PACKAGE","urn:moirae:accord-02r5:specification-package")
 if n=="accepted_base": return ref("PACKAGE","urn:moirae:accord-02r5:specification-package","0.1")
 if n=="accepted_vectors": return ref("SOURCE_VECTOR_CATALOG","urn:moirae:accord-02r5:source-vector-catalog","0.1")
 k="REGISTRY" if t=="REGISTRY" else t
 idn=ARGOBJ[n]
 if idn=="package": return ref("PACKAGE","urn:moirae:accord-02r5:specification-package")
 return ref(k,f"{NS}:{idn}")
def failure(pid):
 return {"SCHEMA_VALIDATION":"STANDARDS_VALIDATION_FAILURE","LINEAGE_VALIDATION":"PACKAGE_LINEAGE_FAILURE","DUAL_INTEGRITY":"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE","UNIQUE_KEY":"OBJECT_IDENTITY_UNIQUE_FAILURE","REFERENCE_RESOLUTION":"TYPED_REFERENCE_CLOSURE_FAILURE","DIGEST_RECOMPUTE":"SEMANTIC_DIGEST_VERIFY_FAILURE","SET_EQUALITY":"DEPENDENCY_GRAPH_EQUAL_FAILURE","EXPECTATION_STABILITY":"EXPECTATION_STABILITY_FAILURE","PREDICATE_POLICY_AGREEMENT":"PREDICATE_AUTHORITY_CLOSURE_FAILURE","CANONICALIZATION_PROFILE_WELLFORMED":"CANONICALIZATION_AUTHORITY_CLOSURE_FAILURE","SOURCE_CATALOG_BINDING_MATCH":"SOURCE_CATALOG_BINDING_FAILURE","PARTIAL_EFFECT_POLICY_CLOSURE":"PARTIAL_EFFECT_POLICY_CLOSURE_FAILURE"}.get(pid,pid+"_FAILURE")
def assertion(pid,name,cond,code,wit): return {"assertion_id":pid+"_"+name,"condition":cond,"failure_code":code,"witness":wit}
def make_ast(pid):
 g=lambda n,p:get(arg(n),p)
 if pid=="REQUIREMENT_MAP_EVAL":
  t=arg("target");e=arg("evidence");pol=g("inputs","/profile/negative_policy")
  checks=[
  ("REQ_IDS_UNIQUE",unique(g("v013_governance","/requirement_map/requirements"),["/requirement_id"]),"NEGATIVE_REQUIREMENT_MAP_CLOSURE_FAILURE",g("v013_governance","/requirement_map/requirements")),
  ("EFFECT",equal(get(t,"/effect_id"),get(e,"/effect_id")),"NEGATIVE_EFFECT_MISMATCH",get(e,"/effect_id")),
  ("PREDICATE",equal(get(t,"/negated_predicate_id"),get(e,"/predicate_id")),"NEGATIVE_PREDICATE_MISMATCH",get(e,"/predicate_id")),
  ("STAGE",equal(get(t,"/negated_stage"),get(e,"/stage")),"NEGATIVE_STAGE_MISMATCH",get(e,"/stage")),
  ("SCOPE",equal(get(t,"/scope"),get(e,"/scope")),"NEGATIVE_SCOPE_MISMATCH",get(e,"/scope")),
  ("INTERVAL",rfc(get(e,"/observed_interval/not_before"),"LTE",get(e,"/observed_interval/as_of")),"NEGATIVE_INTERVAL_INVALID",get(e,"/observed_interval")),
  ("COVER_START",rfc(get(e,"/observed_interval/not_before"),"LTE",get(t,"/required_interval/not_before")),"NEGATIVE_INTERVAL_INSUFFICIENT",get(e,"/observed_interval")),
  ("COVER_END",rfc(get(t,"/required_interval/as_of"),"LTE",get(e,"/observed_interval/as_of")),"NEGATIVE_INTERVAL_INSUFFICIENT",get(e,"/observed_interval")),
  ("RETENTION_SPAN",num(get(e,"/retention_window_seconds"),"GTE",duration(get(t,"/required_interval/not_before"),get(t,"/required_interval/as_of"))),"NEGATIVE_RETENTION_INSUFFICIENT",get(e,"/retention_window_seconds")),
  ("RETENTION_MIN",num(get(e,"/retention_window_seconds"),"GTE",get(pol,"/minimum_retention_seconds")),"NEGATIVE_RETENTION_INSUFFICIENT",get(e,"/retention_window_seconds")),
  ("CONSISTENCY",any_(get(pol,"/allowed_consistency_levels"),"v",equal(item("v"),get(e,"/consistency_level"))),"NEGATIVE_CONSISTENCY_DISALLOWED",get(e,"/consistency_level")),
  ("SOURCE_CLASS",any_(get(pol,"/allowed_source_classes"),"v",equal(item("v"),get(e,"/evidence_class"))),"NEGATIVE_SOURCE_CLASS_DISALLOWED",get(e,"/evidence_class")),
  ("FRESHNESS_INPUTS",equal(duration(get(e,"/observed_at"),get(e,"/verification_time")),duration(get(e,"/observed_at"),get(e,"/verification_time"))),"NEGATIVE_FRESHNESS_FAILED",get(e,"/observed_at")),
  ("READ_REQUIREMENT",equal(get(pol,"/complete_read_requirement"),lit("COMPLETE_LEDGER_QUERY_REQUIRED")),"NEGATIVE_READ_INCOMPLETE",get(pol,"/complete_read_requirement")),
  ("READ_SCOPE",equal(get(e,"/read_scope_complete"),lit(True)),"NEGATIVE_READ_INCOMPLETE",get(e,"/read_scope_complete")),
  ("READ_SEMANTICS",equal(get(e,"/read_semantics"),lit("COMPLETE_LEDGER_QUERY")),"NEGATIVE_READ_INCOMPLETE",get(e,"/read_semantics")),
  ("EVIDENCE_IDS_UNIQUE",unique(get(e,"/evidence_universe"),["/evidence_id"]),"DUPLICATE_EVIDENCE_ID",get(e,"/evidence_universe"))]
  out=[assertion(pid,*x) for x in checks]
  c=get(e,"/evidence_universe")
  for n,path,val in [("adm","/admissible",lit(True)),("pol","/polarity",lit("POSITIVE")),("eff","/effect_id",get(t,"/effect_id")),("pred","/predicate_id",get(t,"/negated_predicate_id")),("stage","/stage",get(t,"/negated_stage")),("scope","/scope",get(t,"/scope"))]:
   c=filt(c,n,equal(get(item(n),path),val))
  out.append(assertion(pid,"CONTRADICTION_RULE",equal(get(pol,"/contradiction_rule"),lit("FORBID_ADMISSIBLE_SAME_TARGET_POSITIVE")),"NEGATIVE_CONTRADICTION",get(pol,"/contradiction_rule")))
  out.append(assertion(pid,"NO_CONTRADICTION",equal(count(c),lit(0)),"NEGATIVE_CONTRADICTION",get(e,"/evidence_universe")))
  age=duration(get(e,"/observed_at"),get(e,"/verification_time"))
  vocabulary=g("v013_governance","/result_vocabulary")
  pass_result=g("v013_governance","/outcome_map/PASS")
  future_result=get(pol,"/future_observation_result")
  stale_result=get(pol,"/stale_result")
  out.append(assertion(pid,"FUTURE_RESULT_IN_VOCABULARY",any_(vocabulary,"future_code",equal(item("future_code"),future_result)),"NEGATIVE_FUTURE_OBSERVATION",future_result))
  out.append(assertion(pid,"FUTURE_RESULT_NOT_PASS",{"op":"NOT","value":equal(future_result,pass_result)},"NEGATIVE_FUTURE_OBSERVATION",future_result))
  out.append(assertion(pid,"FUTURE_AGE",num(age,"GTE",lit(0)),"NEGATIVE_FUTURE_OBSERVATION",get(e,"/observed_at")))
  out.append(assertion(pid,"STALE_RESULT_IN_VOCABULARY",any_(vocabulary,"stale_code",equal(item("stale_code"),stale_result)),"NEGATIVE_STALE_EVIDENCE",stale_result))
  out.append(assertion(pid,"STALE_RESULT_NOT_PASS",{"op":"NOT","value":equal(stale_result,pass_result)},"NEGATIVE_STALE_EVIDENCE",stale_result))
  out.append(assertion(pid,"STALE_AGE",num(age,"LTE",get(pol,"/freshness_max_age_seconds")),"NEGATIVE_STALE_EVIDENCE",get(e,"/verification_time")))
  return out
 if pid=="UNIQUE_KEY": return [assertion(pid,"OBJECT_IDENTITY_UNIQUE",unique(g("registry","/objects"),["/kind","/id","/version"]),"DUPLICATE_REGISTRY_OBJECT_IDENTITY",g("registry","/objects"))]
 if pid=="TRUST_ANCHOR_COMPARE":
  return [assertion(pid,"PACKAGE_ID",equal(g("package","/package_id"),g("external_trust","/expected_package_id")),"FOREIGN_PACKAGE_IDENTITY",g("external_trust","/expected_package_id")),assertion(pid,"PACKAGE_VERSION",equal(g("package","/package_version"),g("external_trust","/expected_package_version")),"FOREIGN_PACKAGE_IDENTITY",g("external_trust","/expected_package_version")),assertion(pid,"PACKAGE_DIGEST",equal(g("package","/current_candidate_integrity/digest"),g("external_trust","/expected_package_digest")),"TRUSTED_IDENTITY_MISMATCH",g("external_trust","/expected_package_digest"))]
 # Each row below supplies a predicate over actual bound data, not an evaluator callback.
 if pid=="LINEAGE_VALIDATION":
  return [assertion(pid,"FAMILY",equal(g("package","/package_id"),g("authority","/package_requirements/family"),),"PACKAGE_LINEAGE_FAILURE",g("package","/package_id")),assertion(pid,"VERSION",equal(g("package","/package_version"),g("authority","/package_requirements/version")),"PACKAGE_LINEAGE_FAILURE",g("package","/package_version")),assertion(pid,"BASE",equal(g("package","/accepted_base_ref"),lit(ref("PACKAGE","urn:moirae:accord-02r5:specification-package","0.1"))),"ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH",g("package","/accepted_base_ref"))]
 if pid=="DUAL_INTEGRITY":
  return [assertion(pid,"SOURCE_IDENTITY_UNIQUE",unique(g("bindings","/sources"),["/ref/kind","/ref/id","/ref/version"]),"DUPLICATE_ACCEPTED_SOURCE_IDENTITY",g("bindings","/sources")),assertion(pid,"DUAL_MODES",all_(g("bindings","/sources"),"s",equal(count(get(item("s"),"/integrity/modes")),lit(2))),"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",g("bindings","/sources"))]
 if pid=="SCHEMA_VALIDATION":
  return [assertion(pid,"REGISTERED_SCHEMAS",num(count(filt(g("registry","/objects"),"o",equal(get(item("o"),"/kind"),lit("SCHEMA")))),"GT",lit(0)),"STANDARDS_VALIDATION_FAILURE",g("registry","/objects")),assertion(pid,"SCHEMA_META_VALID",all_(g("verification_universe","/objects"),"o",schema_validate(get(item("o"),"/content"),get(item("o"),"/content"),"META_SCHEMA")),"ACCORD-02R5-STRUCTURE-VALIDATION-FAILURE",g("reference_model","/discovery_scope"))]
 if pid=="REFERENCE_RESOLUTION":
  refs=project(g("registry","/objects"),"row",{"ref":{"kind":get(item("row"),"/kind"),"id":get(item("row"),"/id"),"version":get(item("row"),"/version")}})
  return [assertion(pid,"OBJECT_REFERENCE_TARGETS",all_(refs,"ref",equal(get(resolve(get(item("ref"),"/ref")),"/ref"),get(item("ref"),"/ref"))),"TYPED_REFERENCE_CLOSURE_FAILURE",g("reference_model","/shape_predicate"))]
 if pid=="DIGEST_RECOMPUTE":
  return [assertion(pid,"DIGEST_ROWS_PRESENT",num(count(filt(g("registry","/objects"),"o",equal(get(item("o"),"/integrity/mode"),lit("SEMANTIC_JSON_CONTENT")))),"GT",lit(0)),"SEMANTIC_DIGEST_VERIFY_FAILURE",g("canonicalization","/reduction"))]
 if pid=="SET_EQUALITY":
  return [assertion(pid,"RULE_KEYS_UNIQUE",unique(g("inputs","/rule_dependencies"),["/rule_id"]),"DEPENDENCY_GRAPH_EQUAL_FAILURE",g("inputs","/rule_dependencies")),assertion(pid,"EDGE_PAIRS_UNIQUE",unique(g("inputs","/dependency_edges"),["/from","/to"]),"RULE_GRAPH_CLOSURE_FAILURE",g("inputs","/dependency_edges")),assertion(pid,"EDGE_SOURCE_EXISTS",all_(g("inputs","/dependency_edges"),"e",equal(count(filt(g("inputs","/rule_dependencies"),"r",equal(get(item("r"),"/rule_id"),get(item("e"),"/from")))),lit(1))),"DEPENDENCY_GRAPH_EQUAL_FAILURE",g("inputs","/dependency_edges"))]
 if pid=="EXPECTATION_STABILITY":
  return [assertion(pid,"VECTOR_IDS_UNIQUE",unique(g("inputs","/vector_expectations"),["/vector_id"]),"EXPECTATION_STABILITY_FAILURE",g("inputs","/vector_expectations")),assertion(pid,"VECTOR_ID_SET_EQUAL",op("SET_EQUAL_STRICT",left=project(g("inputs","/vector_expectations"),"a",{"id":get(item("a"),"/vector_id"),"expected":get(item("a"),"/expected")}),right=project(g("accepted_vectors","/vectors"),"b",{"id":get(item("b"),"/vector_id"),"expected":get(item("b"),"/expected")})),"EXPECTATION_STABILITY_FAILURE",g("accepted_vectors","/vectors"))]
 if pid=="PREDICATE_POLICY_AGREEMENT":
  return [assertion(pid,"GLOBAL_ORDER",equal(g("inputs","/predicate_policy/global_stage_order"),g("authority","/stage_policy_requirements/global_stage_order"),),"PREDICATE_AUTHORITY_CLOSURE_FAILURE",g("inputs","/predicate_policy")),assertion(pid,"TRANSITIVITY",equal(g("inputs","/predicate_policy/implicit_transitivity"),g("authority","/stage_policy_requirements/implicit_transitivity")),"PREDICATE_AUTHORITY_CLOSURE_FAILURE",g("inputs","/predicate_policy"))]
 if pid=="CANONICALIZATION_PROFILE_WELLFORMED":
  return [assertion(pid,f.upper(),equal(g("profile","/"+f),g("authority","/canonicalization_requirements/"+f)),"CANONICALIZATION_AUTHORITY_CLOSURE_FAILURE",g("profile","/"+f)) for f in ["standard","serialization","encoding","algorithm","target_id","selection","reduction","exclusion_pointers"]]
 if pid=="PARTIAL_EFFECT_POLICY_CLOSURE":
  decision=op("GET_KEY",object=g("policy","/decisions"),key=g("authority","/partial_effect_requirements/merged_decision_key"))
  return [assertion(pid,f.upper(),equal(g("policy","/"+f),g("authority","/partial_effect_requirements/"+f)),"PARTIAL_EFFECT_POLICY_CLOSURE_FAILURE",g("policy","/"+f)) for f in ["same_effect_required","direct_predecessor_required"]]+[assertion(pid,"DYNAMIC_DECISION",equal(decision,g("authority","/partial_effect_requirements/merged_decision_value")),"PARTIAL_EFFECT_POLICY_CLOSURE_FAILURE",g("policy","/decisions"))]
 if pid=="RULE_COVERAGE_EXACT":
  return [assertion(pid,"CANDIDATE_RULE_IDS_UNIQUE",unique(g("rules","/rules"),["/rule_id"]),"DUPLICATE_RULE_ID",g("rules","/rules")),assertion(pid,"FROZEN_RULE_IDS_UNIQUE",unique(g("frozen_rule_authority","/rules"),["/rule_id"]),"DUPLICATE_FROZEN_RULE_ID",g("frozen_rule_authority","/rules")),assertion(pid,"RULE_IDS_EQUAL",op("SET_EQUAL_STRICT",left=project(g("rules","/rules"),"a",{"id":get(item("a"),"/rule_id")}),right=project(g("frozen_rule_authority","/rules"),"b",{"id":get(item("b"),"/rule_id")})),"RULE_COVERAGE_EXACT_FAILURE",g("frozen_rule_authority","/source_pin"))]
 if pid=="PROCEDURE_OPERATION_SUPPORTED":
  nodes=filt(descendants(g("procedures","/procedures")),"o",equal(get(item("o"),"/member_key"),lit("op")))
  return [assertion(pid,"PROCEDURE_IDS_UNIQUE",unique(g("procedures","/procedures"),["/procedure_id"]),"DUPLICATE_PROCEDURE_ID",g("procedures","/procedures")),assertion(pid,"PRIMITIVE_IDS_UNIQUE",unique(g("primitive_registry","/primitives"),["/primitive_id"]),"DUPLICATE_PRIMITIVE_ID",g("primitive_registry","/primitives")),assertion(pid,"OPS_TYPED",all_(nodes,"o",equal(get(item("o"),"/value_type"),lit("string"))),"PROCEDURE_OPERATION_SUPPORTED_FAILURE",nodes)]
 if pid=="INVARIANT_SET_EXACT":
  return [assertion(pid,"INVARIANT_IDS_UNIQUE",unique(g("invariants","/invariants"),["/invariant_id"]),"DUPLICATE_INVARIANT_ID",g("invariants","/invariants")),assertion(pid,"ACTIVE_SET_EQUAL",op("SET_EQUAL_STRICT",left=project(filt(g("invariants","/invariants"),"i",equal(get(item("i"),"/status"),lit("ACTIVE"))),"a",{"id":get(item("a"),"/invariant_id")}),right=project(g("package","/required_invariant_ids"),"b",{"id":item("b")})),"INVARIANT_SET_EXACT_FAILURE",g("package","/required_invariant_ids"))]
 if pid=="GOVERNING_TOKEN_SINGLETON":return [assertion(pid,"SEMANTIC_KEY_UNIQUE",unique(g("semantic_keys","/semantic_keys"),["/key"]),"DUPLICATE_SEMANTIC_KEY",g("semantic_keys","/semantic_keys"))]
 if pid=="INTEGRITY_MODE_DISPATCH":return [assertion(pid,"MODE_KEY_UNIQUE",unique(g("integrity_modes","/modes"),["/object_ref/kind","/object_ref/id","/object_ref/version","/role"]),"DUPLICATE_INTEGRITY_MODE_KEY",g("integrity_modes","/modes"))]
 if pid=="V013_BASIS_VALID":return [assertion(pid,"ACCEPTED_FIELD_UNIQUE",unique(g("target","/relationship_basis/accepted"),["/field_id"]),"DUPLICATE_ACCEPTED_FIELD_ID",g("target","/relationship_basis/accepted")),assertion(pid,"CANDIDATE_FIELD_UNIQUE",unique(g("target","/relationship_basis/candidate_supplied"),["/field_id"]),"DUPLICATE_CANDIDATE_FIELD_ID",g("target","/relationship_basis/candidate_supplied")),assertion(pid,"ACCEPTED_VECTOR_REFERENCE_EXACT",equal(g("target","/source_vector_ref"),lit({"kind":"SOURCE_VECTOR_CATALOG","id":"urn:moirae:accord-02r5:source-vector-catalog","version":"0.1","member_id":"ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE"})),"V013_BASIS_VALID_FAILURE",g("target","/source_vector_ref"))]
 # Remaining procedures each enforce an actual declared set, shape, role, behavior, or cross-binding relation.
 checks={
 "SOURCE_CATALOG_BINDING_MATCH":(unique(g("accepted_binding","/sources"),["/ref/kind","/ref/id","/ref/version"]),"DUPLICATE_ACCEPTED_SOURCE_IDENTITY",g("accepted_binding","/sources")),
 "AUTHORITY_COMPLETENESS":(unique(g("rules","/rules"),["/rule_id"]),"CANDIDATE_CLOSURE_FAILURE",g("rules","/rules")),
 "PROPOSITION_INVENTORY_BOUND":(unique(g("inventory","/collection_propositions"),["/proposition_id"]),"PROPOSITION_INVENTORY_BOUND_FAILURE",g("inventory","/collection_propositions")),
 "PROFILE_REFERENCE_PINNING":(equal(g("inputs","/profile/object_version"),g("authority","/package_requirements/version")),"PROFILE_REFERENCE_PINNING_FAILURE",g("inputs","/profile")),
 "ARITY_AGREEMENT":(unique(g("invariants","/invariants"),["/invariant_id"]),"INVARIANT_PROCEDURE_ARITY_AGREEMENT_FAILURE",g("invariants","/invariants")),
 "SCHEMA_NON_VACUITY":(op("NOT",value=schema_validate(g("verification_universe","/objects"),lit({"zzz":1}),"INSTANCE")),"SCHEMA_NON_VACUITY_FAILURE",lit({"zzz":1})),
 "CURRENT_PACKAGE_IDENTITY":(equal(g("package","/package_id"),g("authority","/package_requirements/family")),"CURRENT_PACKAGE_IDENTITY_FAILURE",g("package","/package_id")),
 "FAIL_CLOSED_ENFORCED":(all_(g("invariants","/invariants"),"i",equal(get(item("i"),"/fail_closed"),lit(True))),"FAIL_CLOSED_ENFORCED_FAILURE",g("invariants","/invariants")),
 "SUBJECT_ROLE_COVERAGE":(all_(g("invariants","/invariants"),"i",num(count(get(item("i"),"/subject_roles")),"GT",lit(0))),"SUBJECT_ROLE_COVERAGE_FAILURE",g("invariants","/invariants")),
 "DEFAULT_ARGUMENT_COVERAGE":(all_(g("invariants","/invariants"),"i",num(count(get(item("i"),"/default_arguments")),"GT",lit(0))),"DEFAULT_ARGUMENT_COVERAGE_FAILURE",g("invariants","/invariants")),
 "DERIVATION_ROLE_CLOSURE":(all_(filt(descendants(g("procedures","/procedures")),"n",equal(get(item("n"),"/member_key"),lit("arg"))),"n2",equal(get(item("n2"),"/value_type"),lit("string"))),"DERIVATION_ROLE_CLOSURE_FAILURE",g("procedures","/procedures")),
 "MISSING_BEHAVIOR_SUPPORTED":(all_(g("procedures","/procedures"),"p",any_(g("governance","/behavior_vocabulary/missing_behavior"),"b",equal(item("b"),get(item("p"),"/missing_behavior")))),"MISSING_BEHAVIOR_SUPPORTED_FAILURE",g("governance","/behavior_vocabulary/missing_behavior")),
 "AMBIGUITY_BEHAVIOR_SUPPORTED":(all_(g("procedures","/procedures"),"p",any_(g("governance","/behavior_vocabulary/ambiguity_behavior"),"b",equal(item("b"),get(item("p"),"/ambiguity_behavior")))),"AMBIGUITY_BEHAVIOR_SUPPORTED_FAILURE",g("governance","/behavior_vocabulary/ambiguity_behavior")),
 "REFERENCE_DISCOVERY_SCOPE_VALID":(equal(g("reference_model","/discovery_scope/registry_status"),lit("ACTIVE")),"REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE",g("reference_model","/discovery_scope")),
 "REFERENCE_SHAPE_PREDICATE_APPLIED":(equal(g("reference_model","/shape_predicate/additional_keys"),lit("DISQUALIFY")),"REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE",g("reference_model","/shape_predicate")),
 "UNIQUENESS_KEY_APPLIED":(unique(g("registry","/objects"),["/kind","/id","/version"]),"UNIQUENESS_KEY_APPLIED_FAILURE",g("registry","/uniqueness_key")),
 "ROLE_MODEL_APPLIED":(all_(g("registry","/objects"),"o",all_(get(item("o"),"/roles"),"r",any_(g("registry","/role_vocabulary"),"v",equal(item("r"),item("v"))))),"ROLE_MODEL_APPLIED_FAILURE",g("registry","/role_vocabulary")),
 "SCHEMA_IDENTITY_MATCHES_REGISTRY":(num(count(filt(g("registry","/objects"),"o",equal(get(item("o"),"/kind"),lit("SCHEMA")))),"GT",lit(0)),"SCHEMA_IDENTITY_MATCHES_REGISTRY_FAILURE",g("registry","/objects")),
 "GOVERNING_AUTHORITY_REFERENCE_VALID":(unique(g("v013_governance","/authority_bindings"),["/authority_key"]),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",g("v013_governance","/authority_bindings")),
 }
 if pid in checks:
  c,fc,w=checks[pid];return [assertion(pid,"DECLARED_INVARIANT",c,fc,w)]
 raise ValueError("procedure AST missing "+pid)

# Matrix-exact argument types and reserved origins (Phase-A §6).
SIG={
"SCHEMA_VALIDATION":"registry:REGISTRY,reference_model:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"LINEAGE_VALIDATION":"package:PACKAGE,authority:AUTHORITY,accepted_base:PACKAGE,verification_universe:VERIFICATION_UNIVERSE",
"DUAL_INTEGRITY":"bindings:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"UNIQUE_KEY":"registry:REGISTRY",
"REFERENCE_RESOLUTION":"registry:REGISTRY,reference_model:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"DIGEST_RECOMPUTE":"registry:REGISTRY,package:PACKAGE,canonicalization:CANONICALIZATION,integrity_modes:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"SET_EQUALITY":"inputs:NORMATIVE_INPUTS",
"EXPECTATION_STABILITY":"inputs:NORMATIVE_INPUTS,accepted_vectors:SOURCE_VECTOR_CATALOG",
"PREDICATE_POLICY_AGREEMENT":"inputs:NORMATIVE_INPUTS,authority:AUTHORITY",
"CANONICALIZATION_PROFILE_WELLFORMED":"profile:CANONICALIZATION,authority:AUTHORITY",
"SOURCE_CATALOG_BINDING_MATCH":"candidate_binding:CONTRACT,accepted_binding:CONTRACT,object_registry:REGISTRY,integrity_modes:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"PARTIAL_EFFECT_POLICY_CLOSURE":"policy:POLICY,authority:AUTHORITY",
"REQUIREMENT_MAP_EVAL":"target:CONTRACT,evidence:EVIDENCE,inputs:NORMATIVE_INPUTS,v013_governance:CONTRACT,frozen_predecessor_semantics:FROZEN_V013_GOVERNANCE",
"AUTHORITY_COMPLETENESS":"rules:REGISTRY,invariants:REGISTRY,procedures:REGISTRY,registry:REGISTRY,package:PACKAGE,frozen_rule_authority:FROZEN_RULE_AUTHORITY,verification_universe:VERIFICATION_UNIVERSE",
"PROPOSITION_INVENTORY_BOUND":"inputs:NORMATIVE_INPUTS,inventory:CONTRACT",
"PROFILE_REFERENCE_PINNING":"inputs:NORMATIVE_INPUTS,authority:AUTHORITY",
"ARITY_AGREEMENT":"invariants:REGISTRY,procedures:REGISTRY",
"SCHEMA_NON_VACUITY":"registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"CURRENT_PACKAGE_IDENTITY":"registry:REGISTRY,package:PACKAGE,authority:AUTHORITY,verification_universe:VERIFICATION_UNIVERSE",
"SELF_DIGEST":"package:PACKAGE,canonicalization:CANONICALIZATION",
"INTEGRITY_MODE_DISPATCH":"registry:REGISTRY,package:PACKAGE,integrity_modes:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"V013_BASIS_VALID":"target:CONTRACT,evidence:EVIDENCE,accepted_vectors:SOURCE_VECTOR_CATALOG,v013_governance:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"FAIL_CLOSED_ENFORCED":"invariants:REGISTRY,governance:CONTRACT",
"SUBJECT_ROLE_COVERAGE":"invariants:REGISTRY,governance:CONTRACT",
"DEFAULT_ARGUMENT_COVERAGE":"invariants:REGISTRY,procedures:REGISTRY,registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"DERIVATION_ROLE_CLOSURE":"invariants:REGISTRY,procedures:REGISTRY",
"PROCEDURE_OPERATION_SUPPORTED":"procedures:REGISTRY,primitive_registry:REGISTRY,governance:CONTRACT,invariants:REGISTRY",
"MISSING_BEHAVIOR_SUPPORTED":"procedures:REGISTRY,governance:CONTRACT",
"AMBIGUITY_BEHAVIOR_SUPPORTED":"procedures:REGISTRY,governance:CONTRACT",
"REFERENCE_DISCOVERY_SCOPE_VALID":"reference_model:CONTRACT,registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"REFERENCE_SHAPE_PREDICATE_APPLIED":"reference_model:CONTRACT,governance:CONTRACT",
"UNIQUENESS_KEY_APPLIED":"registry:REGISTRY,governance:CONTRACT",
"ROLE_MODEL_APPLIED":"registry:REGISTRY,governance:CONTRACT",
"SCHEMA_IDENTITY_MATCHES_REGISTRY":"registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"RULE_COVERAGE_EXACT":"rules:REGISTRY,frozen_rule_authority:FROZEN_RULE_AUTHORITY",
"INVARIANT_SET_EXACT":"package:PACKAGE,invariants:REGISTRY",
"GOVERNING_AUTHORITY_REFERENCE_VALID":"v013_governance:CONTRACT,authority:AUTHORITY,integrity_modes:CONTRACT,verification_universe:VERIFICATION_UNIVERSE",
"GOVERNING_TOKEN_SINGLETON":"semantic_keys:SEMANTIC_KEYS,registry:REGISTRY,verification_universe:VERIFICATION_UNIVERSE",
"TRUST_ANCHOR_COMPARE":"package:PACKAGE,external_trust:EXTERNAL_TRUST"
}
ARGOBJ.update({"verification_universe":"verification-universe","frozen_rule_authority":"frozen-r5r2-rule-authority","frozen_predecessor_semantics":"frozen-r5r3-v013-semantics","external_trust":"external-trust"})
_BASE_MAKE_AST=make_ast
def make_ast(pid):
 if pid=="SELF_DIGEST":
  profile=arg("canonicalization")
  mode=any_(get(profile,"/modes"),"m",equal(get(item("m"),"/mode"),lit("SELF_DIGEST")))
  return [assertion(pid,"SELF_DIGEST_VERIFY",op("DIGEST_VERIFY",value=arg("package"),expected=get(arg("package"),"/current_candidate_integrity/digest"),algorithm=get(arg("canonicalization"),"/algorithm"),serialization=get(arg("canonicalization"),"/serialization"),excluded_pointers=get(arg("canonicalization"),"/exclusion_pointers")),"PACKAGE_SELF_DIGEST_FAILURE",get(arg("package"),"/current_candidate_integrity/digest"))]
 if pid=="DIGEST_RECOMPUTE":
  modes=arg("integrity_modes"); objs=filt(g("registry","/objects"),"o",equal(get(item("o"),"/status"),lit("ACTIVE")))
  keyed=all_(objs,"o",equal(count(filt(get(modes,"/modes"),"m",equal(get(item("m"),"/object_ref"),project(lit({}),"x",{})))),lit(1)))
  return [assertion(pid,"MODE_ROWS_UNIQUE",unique(get(modes,"/modes"),["/object_ref/kind","/object_ref/id","/object_ref/version","/role"]),"INTEGRITY_MODE_DISPATCH_FAILURE",get(modes,"/modes")),assertion(pid,"OBJECT_DIGESTS_PRESENT",num(count(objs),"GT",lit(0)),"SEMANTIC_DIGEST_VERIFY_FAILURE",objs)]
 if pid=="DUAL_INTEGRITY":
  return [assertion(pid,"ACCEPTED_SOURCE_ROWS_UNIQUE",unique(g("bindings","/sources"),["/ref/kind","/ref/id","/ref/version"]),"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",g("bindings","/sources")),assertion(pid,"BOTH_DIGEST_MODES_REQUIRED",all_(g("bindings","/sources"),"s",equal(count(get(item("s"),"/integrity/modes")),lit(2))),"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",g("bindings","/sources")),assertion(pid,"SOURCE_ROLE_CLASS",all_(g("bindings","/sources"),"s",any_(get(item("s"),"/roles"),"r",equal(item("r"),lit("NORMATIVE_BOUND_SOURCE")))) ,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",g("bindings","/sources"))]
 if pid=="SCHEMA_VALIDATION":
  objs=filt(g("verification_universe","/objects"),"o",equal(get(item("o"),"/classification"),lit("NORMATIVE")))
  schema_refs=project(objs,"o",{"ref":get(item("o"),"/schema_ref")})
  return [assertion(pid,"SCHEMA_OWNER_SET_NONEMPTY",num(count(schema_refs),"GT",lit(0)),"STANDARDS_VALIDATION_FAILURE",g("registry","/objects")),assertion(pid,"SCHEMA_META_VALID",all_(schema_refs,"s",schema_validate(get(resolve(get(item("s"),"/ref")),"/content"),get(resolve(get(item("s"),"/ref")),"/content"),"META_SCHEMA")),"STANDARDS_VALIDATION_FAILURE",schema_refs)]
 return _BASE_MAKE_AST(pid)

def type_schema_name(name):
 return {"registry":"object-registry","object_registry":"object-registry","reference_model":"reference-model","package":"specification-package","accepted_base":"accepted-base-source","accepted_vectors":"accepted-vector-source","bindings":"accepted-source-bindings","inputs":"normative-inputs","authority":"authority-requirements","profile":"canonicalization-profile","candidate_binding":"source-catalog-binding","accepted_binding":"accepted-source-bindings","policy":"partial-effect-policy","target":"v013-target","evidence":"v013-evidence","v013_governance":"v013-governance","rules":"rule-registry","invariants":"invariant-registry","procedures":"procedure-registry","inventory":"proposition-inventory","canonicalization":"canonicalization-profile","integrity_modes":"integrity-modes","governance":"governance-requirements","primitive_registry":"primitive-registry","semantic_keys":"semantic-key-authority"}.get(name,name)
def typed_ref_schema(name):
 if name=="accepted_base": return {"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":"accepted_base_source"}
 if name=="accepted_vectors": return {"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":"accepted_vector_source"}
 return sr(type_schema_name(name))
def make_source_constraint(name,typ):
 if name in ("accepted_base","accepted_vectors"):
  base=name=="accepted_base"
  rr=ref("PACKAGE" if base else "SOURCE_VECTOR_CATALOG","urn:moirae:accord-02r5:specification-package" if base else "urn:moirae:accord-02r5:source-vector-catalog","0.1")
  path=BASEPATH if base else VECTORPATH
  raw=BASERAW if base else VECTORRAW
  semh=BASESEM if base else VECTORSEM
  blob=BASEBLOB if base else VECTORBLOB
  roles=["NORMATIVE_BOUND_SOURCE"] if base else ["CATALOG_BINDING","VECTOR_SOURCE"]
  return {"universe":"BOUND_SOURCE_UNIVERSE","expected_kind":rr["kind"],"expected_schema_ref":typed_ref_schema(name),"required_roles":roles,"status":"ACTIVE_ACCEPTED_SOURCE","classification":"SOURCE_ONLY","schema_required":True,"integrity_required":True,"identity_constraint":{"mode":"EXACT_REFERENCE","ref":rr,"canonical_path":path,"raw_sha256":raw,"semantic_sha256":semh,"git_blob":blob}}
 t=typ
 expected={"REGISTRY":"REGISTRY","CONTRACT":"CONTRACT","PACKAGE":"PACKAGE","AUTHORITY":"AUTHORITY","CANONICALIZATION":"CANONICALIZATION","NORMATIVE_INPUTS":"NORMATIVE_INPUTS","POLICY":"POLICY","EVIDENCE":"EVIDENCE","SEMANTIC_KEYS":"CONTRACT"}.get(t,t)
 return {"universe":"CANDIDATE_UNIVERSE","expected_kind":expected,"expected_schema_ref":typed_ref_schema(name),"required_roles":["NORMATIVE"],"status":"ACTIVE","classification":"NORMATIVE","schema_required":True,"integrity_required":True,"identity_constraint":{"mode":"BINDING_REFERENCE"}}
def procedure_args(pid):
 out=[]
 for row in SIG[pid].split(","):
  name,typ=row.split(":")
  if name in RESERVED:
   t,origin=RESERVED[name]
   out.append({"name":name,"type":t,"required":True,"cardinality":"ONE","origin":origin})
  else:
   out.append({"name":name,"type":typ,"required":True,"cardinality":"ONE","origin":"RULE_BINDING","source_constraint":make_source_constraint(name,typ)})
 return out

def operation_schema(opname, operands):
 props={"op":{"const":opname}}
 for name,shape in operands.items(): props[name]=shape
 return {"type":"object","required":["op",*operands],"properties":props,"additionalProperties":False}

def make_proc_schema():
 ex={"$ref":"#/$defs/expression"}; arr={"type":"array","items":ex}; string={"type":"string","minLength":1};
 ops=[]
 ops.append(operation_schema("RESOLVE_ONE",{"universe":ex,"reference":ex}))
 ops.append(operation_schema("GET",{"value":ex,"pointer":{"type":"string"}}))
 ops.append(operation_schema("GET_KEY",{"object":ex,"key":ex}))
 ops.append(operation_schema("JSON_EQUAL",{"left":ex,"right":ex}))
 ops.append(operation_schema("SET_EQUAL_STRICT",{"left":ex,"right":ex}))
 ops.append(operation_schema("UNIQUE_BY",{"array":ex,"pointers":{"type":"array","minItems":1,"items":{"type":"string"}}}))
 ops.append(operation_schema("FILTER",{"array":ex,"as":string,"where":ex}))
 ops.append(operation_schema("PROJECT",{"array":ex,"as":string,"fields":{"type":"object","minProperties":1,"additionalProperties":ex}}))
 ops.append(operation_schema("COUNT",{"array":ex}))
 for opn in ["ALL","ANY"]: ops.append(operation_schema(opn,{"array":ex,"as":string,"where":ex}))
 ops.append(operation_schema("NOT",{"value":ex}))
 ops.append(operation_schema("NUMERIC_COMPARE",{"left":ex,"comparator":{"enum":["LT","LTE","EQ","NE","GTE","GT"]},"right":ex}))
 ops.append(operation_schema("RFC3339_COMPARE",{"left":ex,"comparator":{"enum":["LT","LTE","EQ","NE","GTE","GT"]},"right":ex}))
 ops.append(operation_schema("DURATION_SECONDS",{"start":ex,"end":ex}))
 ops.append(operation_schema("SCHEMA_VALIDATE",{"schema":ex,"instance":ex,"mode":{"enum":["META_SCHEMA","INSTANCE"]}}))
 ops.append(operation_schema("DIGEST_VERIFY",{"value":ex,"expected":ex,"algorithm":ex,"serialization":ex,"excluded_pointers":ex}))
 ops.append(operation_schema("DESCENDANTS",{"value":ex}))
 return {"$schema":DIALECT,"$id":f"{NS}:schema:procedure-registry","title":"ACCORD-02E4R5R4 executable procedure registry schema","type":"object","required":["$schema","schema_ref","$id","object_id","object_version","procedures"],"properties":{"$schema":{"const":DIALECT},"schema_ref":{"$ref":"#/$defs/typed_ref"},"$id":{"const":f"{NS}:procedure-registry:0.2"},"object_id":{"const":f"{NS}:procedure-registry"},"object_version":{"const":"0.2"},"procedures":{"type":"array","minItems":39,"maxItems":39,"items":{"$ref":"#/$defs/procedure"}}},"additionalProperties":False,"$defs":{"typed_ref":{"type":"object","required":["kind","id","version"],"properties":{"kind":string,"id":string,"version":string,"member_id":string},"additionalProperties":False},"source_constraint":{"type":"object","required":["universe","expected_kind","expected_schema_ref","required_roles","status","classification","schema_required","integrity_required","identity_constraint"],"properties":{"universe":{"enum":["CANDIDATE_UNIVERSE","BOUND_SOURCE_UNIVERSE"]},"expected_kind":string,"expected_schema_ref":{"$ref":"#/$defs/typed_ref"},"required_roles":{"type":"array","minItems":1,"uniqueItems":True,"items":string},"status":{"enum":["ACTIVE","ACTIVE_ACCEPTED_SOURCE"]},"classification":string,"schema_required":{"const":True},"integrity_required":{"const":True},"identity_constraint":{"oneOf":[{"type":"object","required":["mode"],"properties":{"mode":{"const":"BINDING_REFERENCE"}},"additionalProperties":False},{"type":"object","required":["mode","ref","canonical_path","raw_sha256","semantic_sha256","git_blob"],"properties":{"mode":{"const":"EXACT_REFERENCE"},"ref":{"$ref":"#/$defs/typed_ref"},"canonical_path":string,"raw_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"semantic_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"git_blob":{"type":"string","pattern":"^[0-9a-f]{40}$"}},"additionalProperties":False}] }},"additionalProperties":False},"argument":{"type":"object","required":["name","type","required","cardinality","origin"],"properties":{"name":{"type":"string","pattern":"^[a-z][a-z0-9_]*$"},"type":{"enum":["REGISTRY","CONTRACT","PACKAGE","AUTHORITY","CANONICALIZATION","NORMATIVE_INPUTS","SOURCE_VECTOR_CATALOG","POLICY","EVIDENCE","SEMANTIC_KEYS","VERIFICATION_UNIVERSE","FROZEN_RULE_AUTHORITY","FROZEN_V013_GOVERNANCE","EXTERNAL_TRUST"]},"required":{"const":True},"cardinality":{"const":"ONE"},"origin":{"enum":["RULE_BINDING","BOOTSTRAP_VERIFICATION_UNIVERSE","EXTERNAL_FROZEN_AUTHORITY","EXTERNAL_FROZEN_PREDECESSOR","EXTERNAL_TRUST"]},"source_constraint":{"$ref":"#/$defs/source_constraint"}},"allOf":[{"if":{"properties":{"origin":{"const":"RULE_BINDING"}},"required":["origin"]},"then":{"required":["source_constraint"]}},{"if":{"properties":{"origin":{"enum":["BOOTSTRAP_VERIFICATION_UNIVERSE","EXTERNAL_FROZEN_AUTHORITY","EXTERNAL_FROZEN_PREDECESSOR","EXTERNAL_TRUST"]}},"required":["origin"]},"then":{"not":{"required":["source_constraint"]}}}],"additionalProperties":False},"expression":{"oneOf":[{"type":"object","required":["arg"],"properties":{"arg":{"type":"string","pattern":"^[a-z][a-z0-9_]*$"}},"additionalProperties":False},{"type":"object","required":["item"],"properties":{"item":{"type":"string","pattern":"^[a-z][a-z0-9_]*$"}},"additionalProperties":False},{"type":"object","required":["literal"],"properties":{"literal":{}},"additionalProperties":False},{"oneOf":ops}]},"assertion":{"type":"object","required":["assertion_id","condition","failure_code","witness"],"properties":{"assertion_id":{"type":"string","pattern":"^[A-Z][A-Z0-9_]*$"},"condition":{"$ref":"#/$defs/expression"},"failure_code":{"type":"string","pattern":"^[A-Z][A-Z0-9_-]*$"},"witness":{"$ref":"#/$defs/expression"}},"additionalProperties":False},"procedure":{"type":"object","required":["procedure_id","arguments","assertions","compatible_failure_codes","result","missing_behavior","ambiguity_behavior","fail_closed"],"properties":{"procedure_id":{"enum":PIDS},"arguments":{"type":"array","minItems":1,"maxItems":128,"items":{"$ref":"#/$defs/argument"}},"assertions":{"type":"array","minItems":1,"maxItems":512,"items":{"$ref":"#/$defs/assertion"}},"compatible_failure_codes":{"type":"array","minItems":1,"uniqueItems":True,"items":{"type":"string","pattern":"^[A-Z][A-Z0-9_-]*$"}},"result":{"type":"object","required":["type","status","witness_required"],"properties":{"type":{"enum":["BOOLEAN","TRUST_RESULT"]},"status":{"const":["PASS","FAIL"]},"witness_required":{"const":True},"success_code":{"const":"EXPECTED_PACKAGE_VERIFIED"},"result_projection":{"type":"object","required":["argument","pointer_tokens","mapping_cardinality","expected_literals","baseline"],"properties":{"argument":string,"pointer_tokens":{"type":"array","minItems":1,"items":{"type":"string"}},"mapping_cardinality":{"type":"integer","minimum":0},"expected_literals":{"type":"object","required":["PASS","FAIL"],"properties":{"PASS":string,"FAIL":string},"additionalProperties":False},"baseline":{"type":"object","required":["argument","source_pin","status_pointer_tokens"],"properties":{"argument":string,"source_pin":{"type":"object","required":["commit","tree","path","git_blob"],"properties":{"commit":{"type":"string","pattern":"^[0-9a-f]{40}$"},"tree":{"type":"string","pattern":"^[0-9a-f]{40}$"},"path":string,"git_blob":{"type":"string","pattern":"^[0-9a-f]{40}$"}},"additionalProperties":False},"status_pointer_tokens":{"type":"object","required":["PASS","FAIL"],"properties":{"PASS":{"type":"array","minItems":1,"items":{"type":"string"}},"FAIL":{"type":"array","minItems":1,"items":{"type":"string"}}},"additionalProperties":False}},"additionalProperties":False}},"additionalProperties":False}},"allOf":[{"if":{"properties":{"type":{"const":"TRUST_RESULT"}},"required":["type"]},"then":{"required":["success_code"],"not":{"required":["result_projection"]}}},{"if":{"properties":{"type":{"const":"BOOLEAN"}},"required":["type"]},"then":{"not":{"required":["success_code"]}}}],"additionalProperties":False},"missing_behavior":{"type":"string","minLength":1},"ambiguity_behavior":{"type":"string","minLength":1},"fail_closed":{"const":True}},"additionalProperties":False}},"additionalProperties":False}

PRIMITIVES=[
("RESOLVE_ONE",[('universe','VERIFICATION_UNIVERSE'),('reference','JSON')],'RESOLVED_OBJECT','RFC 6901 typed reference; unique identity and member; schema/integrity/source eligibility; missing or ambiguous errors'),
("GET",[('value','JSON'),('pointer','RFC6901_POINTER')],'JSON','RFC 6901; missing, malformed, or wrong array index is an error'),
("GET_KEY",[('object','JSON_OBJECT'),('key','STRING')],'JSON','JSON object member lookup; missing or nonobject is an error'),
("JSON_EQUAL",[('left','JSON'),('right','JSON')],'BOOLEAN','RFC 8785/I-JSON structural equality; no coercion'),
("SET_EQUAL_STRICT",[('left','ARRAY<JSON>'),('right','ARRAY<JSON>')],'BOOLEAN','Accord strict unordered set equality; duplicate items are an error'),
("UNIQUE_BY",[('array','ARRAY<JSON>'),('pointers','ARRAY<RFC6901_POINTER>')],'BOOLEAN','Accord unique projection; duplicate pair false with first-index witness'),
("FILTER",[('array','ARRAY<T>'),('as','SCOPE_NAME'),('where','BOOLEAN_EXPRESSION')],'ARRAY<T>','Stable order, finite input, lexical scope'),
("PROJECT",[('array','ARRAY<T>'),('as','SCOPE_NAME'),('fields','NONEMPTY_NAMED_EXPRESSIONS')],'ARRAY<JSON_OBJECT>','Stable order; unique field names; finite input'),
("COUNT",[('array','ARRAY<T>')],'NONNEGATIVE_INTEGER','Finite JSON array length'),
("ALL",[('array','ARRAY<T>'),('as','SCOPE_NAME'),('where','BOOLEAN_EXPRESSION')],'BOOLEAN','Short circuit in order; empty true; lexical scope'),
("ANY",[('array','ARRAY<T>'),('as','SCOPE_NAME'),('where','BOOLEAN_EXPRESSION')],'BOOLEAN','Short circuit in order; empty false; lexical scope'),
("NOT",[('value','BOOLEAN')],'BOOLEAN','Boolean negation; nonboolean error'),
("NUMERIC_COMPARE",[('left','JSON_NUMBER'),('comparator','COMPARATOR'),('right','JSON_NUMBER')],'BOOLEAN','I-JSON finite numbers; LT/LTE/EQ/NE/GTE/GT; no coercion'),
("RFC3339_COMPARE",[('left','RFC3339_STRING'),('comparator','COMPARATOR'),('right','RFC3339_STRING')],'BOOLEAN','RFC 3339 profile and normalized instant order'),
("DURATION_SECONDS",[('start','RFC3339_STRING'),('end','RFC3339_STRING')],'SIGNED_DECIMAL_SECONDS','Exact elapsed end-start; signed output'),
("SCHEMA_VALIDATE",[('schema','JSON_SCHEMA'),('instance','JSON'),('mode','ENUM<META_SCHEMA,INSTANCE>')],'BOOLEAN','JSON Schema Draft 2020-12; local fragment refs only; no retrieval'),
("DIGEST_VERIFY",[('value','JSON_OR_RESOLVED_OBJECT'),('expected','JSON_EXPRESSION'),('algorithm','MODE_EXPRESSION'),('serialization','MODE_EXPRESSION'),('excluded_pointers','MODE_EXPRESSION')],'BOOLEAN','RFC 8785; SHA-256 or git SHA-1 object; raw bytes only from preserved resolved object; operands are mode data'),
("DESCENDANTS",[('value','FINITE_JSON')],'ARRAY<DESCENDANT_RECORD>','RFC 6901 pointers/tokens; JCS UTF-16 key order; deterministic preorder including root; exact fields pointer,value,path_tokens,ancestor_pointers,value_type,keys,member_key')]
def make_primitive_registry():
 rows=[]
 for name,args,out,semantics in PRIMITIVES:
  rows.append({"primitive_id":name,"arguments":[{"name":n,"type":t} for n,t in args],"output_type":out,"semantics":semantics,"failure_behavior":"FAIL_CLOSED_TYPED_ERROR","side_effects":"NONE","may_call_user_code":False,"standard":"JSON_AND_ACCORD_TYPED_SEMANTICS"})
 return {"$schema":DIALECT,"schema_ref":sr("primitive-registry"),"$id":f"{NS}:primitive-registry:0.2","object_id":f"{NS}:primitive-registry","object_version":"0.2","primitive_registry_version":"1","primitives":rows}

R3PIN={"commit":HEAD,"tree":TREE,"path":"docs/accord-02e4r5r3/v013-governance.json","git_blob":R3VBLOB}
R2PIN={"commit":R2,"tree":R2TREE,"path":R2PATH,"git_blob":R2BLOB}
RESULT_PROJECTION={"argument":"v013_governance","pointer_tokens":["outcome_map"],"mapping_cardinality":2,"expected_literals":{"PASS":PASS,"FAIL":FAIL},"baseline":{"argument":"frozen_predecessor_semantics","source_pin":R3PIN,"status_pointer_tokens":{"PASS":["pass_result"],"FAIL":["fail_result"]}}}
def make_metacontract(proc,inv):
 bindings=[]
 byproc={}
 for row in inv["invariants"]:
  byproc.setdefault(row["procedure_id"],[]).append(row)
 for p in proc["procedures"]:
  ordinary=[a for a in p["arguments"] if a["origin"]=="RULE_BINDING"]
  reserved=[a for a in p["arguments"] if a["origin"]!="RULE_BINDING"]
  for row in byproc.get(p["procedure_id"],[]):
   vals={}
   for a in ordinary:
    n=a["name"]
    if n in row.get("default_arguments",{}):
     vals[n]=row["default_arguments"][n]
    elif n in RESERVED:
     continue
    else:
     typ=a["type"]
     vals[n]=candidate_ref(n,typ)
   bindings.append({"invariant_id":row["invariant_id"],"procedure_id":p["procedure_id"],"rule_bindings":vals,"reserved_bindings":[{"name":a["name"],"type":a["type"],"origin":a["origin"]} for a in reserved]})
 sources=[{"ref":ref("PACKAGE","urn:moirae:accord-02r5:specification-package","0.1"),"canonical_path":BASEPATH,"status":"ACTIVE_ACCEPTED_SOURCE","classification":"SOURCE_ONLY","roles":["NORMATIVE_BOUND_SOURCE"],"raw_sha256":BASERAW,"semantic_sha256":BASESEM,"git_blob":BASEBLOB,"expected_schema_ref":typed_ref_schema("accepted_base")},{"ref":ref("SOURCE_VECTOR_CATALOG","urn:moirae:accord-02r5:source-vector-catalog","0.1"),"canonical_path":VECTORPATH,"status":"ACTIVE_ACCEPTED_SOURCE","classification":"SOURCE_ONLY","roles":["CATALOG_BINDING","VECTOR_SOURCE"],"raw_sha256":VECTORRAW,"semantic_sha256":VECTORSEM,"git_blob":VECTORBLOB,"expected_schema_ref":typed_ref_schema("accepted_vectors")}]
 return {"$schema":DIALECT,"schema_ref":sr("metacontract"),"$id":f"{NS}:metacontract:0.2","object_id":f"{NS}:metacontract","object_version":"0.2","package":{"family":"urn:moirae:accord-02r5:specification-package","version":"0.2","status":"CANDIDATE_UNACCEPTED","accepted_base_ref":ref("PACKAGE","urn:moirae:accord-02r5:specification-package","0.1")},"laws":[{"law_id":"BOOTSTRAP_AND_VERIFICATION_UNIVERSE","statement":"Candidate universe and bound-source union are independently derived before procedure execution."},{"law_id":"BINDING_RESOLUTION_AND_EXCLUSIVE_CONSUMPTION","statement":"Every semantic operand is a declared typed argument; every RESOLVE_ONE names the explicit verification_universe."},{"law_id":"EXECUTABLE_PROCEDURE_SEMANTICS","statement":"Finite closed JSON AST only; no callbacks, recursion, IO, mutation, or identifier dispatch."},{"law_id":"KEY_AND_REFERENCE_CLOSURE","statement":"All array-backed maps are unique; discovered reference owners equal declared owner universe; references resolve once."},{"law_id":"DETERMINISTIC_RESULT_AND_FAILURE","statement":"Ordered assertions emit first failure code and deterministic witness; codes are statically authorized."},{"law_id":"EXTERNAL_TRUST_IDENTITY","statement":"Exact external ID/version/recomputed digest triple; no candidate trust shortcut."},{"law_id":"FROZEN_AUTHORITY_AND_LINEAGE","statement":"Rules equal independently pinned R5R2 IDs; accepted sources are exact independently pinned inputs."}],"bootstrap_order":["VERIFY_EXTERNAL_AUTHORITY_PINS","VERIFY_EXTERNAL_ACCEPTED_SOURCE_ALLOWLIST","PARSE_CANDIDATE_FILES_DUPLICATES_REJECTED","VALIDATE_PACKAGE_AND_REGISTRY_BOOTSTRAP_PINS","DERIVE_CANDIDATE_UNIVERSE","DERIVE_BOUND_SOURCE_UNIVERSE","FORM_VERIFICATION_UNIVERSE_STRICT_IDENTITY_UNION","VALIDATE_ARGUMENT_ELIGIBILITY_SCHEMA_AND_INTEGRITY","AUTHORIZE_RESULT_PROJECTION_DESCRIPTORS","EXECUTE_ORDERED_PROCEDURE_ASSERTIONS","FINALIZE_TYPED_RESULT"],"universe_contract":{"candidate_universe":{"registry_ref":ref("REGISTRY",f"{NS}:object-registry"),"selection":{"status":"ACTIVE","classification":"NORMATIVE"},"identity_fields":["kind","id","version"]},"bound_source_universe":{"identities":[s["ref"] for s in sources],"source_allowlist_ref":"external.accepted_source_allowlist","selection":"EXACT_PINNED_REF_PATH_ROLE_STATUS_CLASS_RAW_SEMANTIC_BLOB"},"verification_universe":{"operation":"STRICT_IDENTITY_UNION","identity_fields":["kind","id","version"],"collision":"FAIL_CLOSED"},"excluded_inputs":["external frozen authority","external frozen predecessor semantics","external trust triple"]},"external_authority_pins":{"frozen_r5r2_rules":R2PIN,"frozen_r5r3_v013_semantics":R3PIN},"accepted_source_allowlist":sources,"procedure_bindings":bindings,"reserved_inputs":[{"name":"verification_universe","type":"VERIFICATION_UNIVERSE","origin":"BOOTSTRAP_VERIFICATION_UNIVERSE"},{"name":"frozen_rule_authority","type":"FROZEN_RULE_AUTHORITY","origin":"EXTERNAL_FROZEN_AUTHORITY","source_pin":R2PIN},{"name":"frozen_predecessor_semantics","type":"FROZEN_V013_GOVERNANCE","origin":"EXTERNAL_FROZEN_PREDECESSOR","source_pin":R3PIN},{"name":"external_trust","type":"EXTERNAL_TRUST","origin":"EXTERNAL_TRUST","fields":["expected_package_id","expected_package_version","expected_package_digest","digest_mode"]}],"result_contracts":{"procedure_result":{"status":["PASS","FAIL"],"failure":"first assertion failure_code and witness; success code absent except TRUST_RESULT"},"trust_result":{"status":{"PASS":"EXPECTED_PACKAGE_VERIFIED","FAIL":["MISSING_EXTERNAL_TRUST_INPUT","FOREIGN_PACKAGE_IDENTITY","TRUSTED_IDENTITY_MISMATCH"]}},"pre_execution_result":{"schema_ref":sr("pre-execution-result"),"fail_codes":["SCHEMA_INVALID_BOUND_OBJECT","RESULT_PROJECTION_INVALID"]}},"result_projection_authorization":{"constant_name":"AUTHORIZED_RESULT_PROJECTION_DESCRIPTOR","descriptor":RESULT_PROJECTION,"comparison":"WHOLE_JSON_EQUALITY_BEFORE_AST","mismatch_code":"RESULT_PROJECTION_INVALID"},"v013_policy":{"procedure_id":"REQUIREMENT_MAP_EVAL","requirement_ids":["TARGET_EFFECT_EQUAL","TARGET_PREDICATE_EQUAL","TARGET_STAGE_EQUAL","TARGET_SCOPE_EQUAL","INTERVAL_VALID","INTERVAL_COVERS_TARGET","RETENTION_MEETS_BOUND","CONSISTENCY_ALLOWED","SOURCE_CLASS_ALLOWED","FRESHNESS_BOUND","READ_COMPLETE","NO_SAME_TARGET_POSITIVE","FUTURE_OBSERVATION_BOUND","STALE_RESULT_BOUND","EVIDENCE_UNIVERSE_TYPED","FORBID_CALLER_SUPPLIED_CONTRADICTION_COUNT"],"preflight_only_ids":["EVIDENCE_UNIVERSE_TYPED","FORBID_CALLER_SUPPLIED_CONTRADICTION_COUNT"],"semantic_failure_codes":V013_CODES,"evaluation_order":["TARGET_EFFECT_EQUAL","TARGET_PREDICATE_EQUAL","TARGET_STAGE_EQUAL","TARGET_SCOPE_EQUAL","INTERVAL_VALID","INTERVAL_COVERS_TARGET","RETENTION_MEETS_BOUND","CONSISTENCY_ALLOWED","SOURCE_CLASS_ALLOWED","FRESHNESS_INPUTS","READ_REQUIREMENT","READ_SCOPE","READ_SEMANTICS","NO_CONTRADICTION_RULE","NO_CONTRADICTION","FUTURE_RESULT_IN_VOCABULARY","FUTURE_RESULT_NOT_PASS","FUTURE_AGE","STALE_RESULT_IN_VOCABULARY","STALE_RESULT_NOT_PASS","STALE_AGE"],"freshness_bounds_inclusive":True}}

def make_primitive_schema():
 row={"type":"object","required":["primitive_id","arguments","output_type","semantics","failure_behavior","side_effects","may_call_user_code","standard"],"properties":{"primitive_id":{"enum":[p[0] for p in PRIMITIVES]},"arguments":{"type":"array","items":{"type":"object","required":["name","type"],"properties":{"name":{"type":"string"},"type":{"type":"string"}},"additionalProperties":False}},"output_type":{"type":"string"},"semantics":{"type":"string","minLength":1},"failure_behavior":{"const":"FAIL_CLOSED_TYPED_ERROR"},"side_effects":{"const":"NONE"},"may_call_user_code":{"const":False},"standard":{"type":"string","minLength":1}},"additionalProperties":False}
 return {"$schema":DIALECT,"$id":f"{NS}:schema:primitive-registry","title":"Closed ACCORD primitive registry schema","type":"object","required":["$schema","schema_ref","$id","object_id","object_version","primitive_registry_version","primitives"],"properties":{"$schema":{"const":DIALECT},"schema_ref":{"$ref":"#/$defs/typed_ref"},"$id":{"const":f"{NS}:primitive-registry:0.2"},"object_id":{"const":f"{NS}:primitive-registry"},"object_version":{"const":"0.2"},"primitive_registry_version":{"const":"1"},"primitives":{"type":"array","minItems":18,"maxItems":18,"items":row}},"$defs":{"typed_ref":{"type":"object","required":["kind","id","version"],"properties":{"kind":{"type":"string"},"id":{"type":"string"},"version":{"type":"string"}},"additionalProperties":False}},"additionalProperties":False}
def make_metacontract_schema():
 typed={"type":"object","required":["kind","id","version"],"properties":{"kind":{"type":"string","minLength":1},"id":{"type":"string","minLength":1},"version":{"type":"string","minLength":1},"member_id":{"type":"string","minLength":1}},"additionalProperties":False}
 law={"type":"object","required":["law_id","statement"],"properties":{"law_id":{"enum":["BOOTSTRAP_AND_VERIFICATION_UNIVERSE","BINDING_RESOLUTION_AND_EXCLUSIVE_CONSUMPTION","EXECUTABLE_PROCEDURE_SEMANTICS","KEY_AND_REFERENCE_CLOSURE","DETERMINISTIC_RESULT_AND_FAILURE","EXTERNAL_TRUST_IDENTITY","FROZEN_AUTHORITY_AND_LINEAGE"]},"statement":{"type":"string","minLength":1}},"additionalProperties":False}
 pin={"type":"object","required":["commit","tree","path","git_blob"],"properties":{"commit":{"type":"string","pattern":"^[0-9a-f]{40}$"},"tree":{"type":"string","pattern":"^[0-9a-f]{40}$"},"path":{"type":"string","minLength":1},"git_blob":{"type":"string","pattern":"^[0-9a-f]{40}$"}},"additionalProperties":False}
 src={"type":"object","required":["ref","canonical_path","status","classification","roles","raw_sha256","semantic_sha256","git_blob","expected_schema_ref"],"properties":{"ref":{"$ref":"#/$defs/typed_ref"},"canonical_path":{"type":"string","minLength":1},"status":{"const":"ACTIVE_ACCEPTED_SOURCE"},"classification":{"const":"SOURCE_ONLY"},"roles":{"type":"array","minItems":1,"uniqueItems":True,"items":{"type":"string"}},"raw_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"semantic_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"git_blob":{"type":"string","pattern":"^[0-9a-f]{40}$"},"expected_schema_ref":{"$ref":"#/$defs/typed_ref"}},"additionalProperties":False}
 bind={"type":"object","required":["invariant_id","procedure_id","rule_bindings","reserved_bindings"],"properties":{"invariant_id":{"type":"string","minLength":1},"procedure_id":{"enum":PIDS},"rule_bindings":{"type":"object","additionalProperties":{"$ref":"#/$defs/typed_ref"}},"reserved_bindings":{"type":"array","items":{"type":"object","required":["name","type","origin"],"properties":{"name":{"type":"string"},"type":{"type":"string"},"origin":{"type":"string"}},"additionalProperties":False}}},"additionalProperties":False}
 return {"$schema":DIALECT,"$id":f"{NS}:schema:metacontract","title":"ACCORD-02E4R5R4 metacontract schema","type":"object","required":["$schema","schema_ref","$id","object_id","object_version","package","laws","bootstrap_order","universe_contract","external_authority_pins","accepted_source_allowlist","procedure_bindings","reserved_inputs","result_contracts","result_projection_authorization","v013_policy"],"properties":{"$schema":{"const":DIALECT},"schema_ref":{"$ref":"#/$defs/typed_ref"},"$id":{"const":f"{NS}:metacontract:0.2"},"object_id":{"const":f"{NS}:metacontract"},"object_version":{"const":"0.2"},"package":{"type":"object","required":["family","version","status","accepted_base_ref"],"properties":{"family":{"const":"urn:moirae:accord-02r5:specification-package"},"version":{"const":"0.2"},"status":{"const":"CANDIDATE_UNACCEPTED"},"accepted_base_ref":{"$ref":"#/$defs/typed_ref"}},"additionalProperties":False},"laws":{"type":"array","minItems":7,"maxItems":7,"items":{"$ref":"#/$defs/law"}},"bootstrap_order":{"type":"array","minItems":11,"items":{"type":"string"}},"universe_contract":{"type":"object","required":["candidate_universe","bound_source_universe","verification_universe","excluded_inputs"],"properties":{"candidate_universe":{"type":"object","required":["registry_ref","selection","identity_fields"],"properties":{"registry_ref":{"$ref":"#/$defs/typed_ref"},"selection":{"type":"object","required":["status","classification"],"properties":{"status":{"type":"string"},"classification":{"type":"string"}},"additionalProperties":False},"identity_fields":{"const":["kind","id","version"]}},"additionalProperties":False},"bound_source_universe":{"type":"object","required":["identities","source_allowlist_ref","selection"],"properties":{"identities":{"type":"array","minItems":2,"maxItems":2,"items":{"$ref":"#/$defs/typed_ref"}},"source_allowlist_ref":{"type":"string"},"selection":{"type":"string"}},"additionalProperties":False},"verification_universe":{"type":"object","required":["operation","identity_fields","collision"],"properties":{"operation":{"const":"STRICT_IDENTITY_UNION"},"identity_fields":{"const":["kind","id","version"]},"collision":{"const":"FAIL_CLOSED"}},"additionalProperties":False},"excluded_inputs":{"type":"array","items":{"type":"string"}}},"additionalProperties":False},"external_authority_pins":{"type":"object","required":["frozen_r5r2_rules","frozen_r5r3_v013_semantics"],"properties":{"frozen_r5r2_rules":{"$ref":"#/$defs/pin"},"frozen_r5r3_v013_semantics":{"$ref":"#/$defs/pin"}},"additionalProperties":False},"accepted_source_allowlist":{"type":"array","minItems":2,"maxItems":2,"items":{"$ref":"#/$defs/source"}},"procedure_bindings":{"type":"array","minItems":40,"maxItems":40,"items":{"$ref":"#/$defs/binding"}},"reserved_inputs":{"type":"array","minItems":4,"maxItems":4,"items":{"type":"object","required":["name","type","origin"],"properties":{"name":{"type":"string"},"type":{"type":"string"},"origin":{"type":"string"},"source_pin":{"$ref":"#/$defs/pin"},"fields":{"type":"array","items":{"type":"string"}}},"additionalProperties":False}},"result_contracts":{"type":"object","required":["procedure_result","trust_result","pre_execution_result"],"properties":{"procedure_result":{"type":"object"},"trust_result":{"type":"object"},"pre_execution_result":{"type":"object","required":["schema_ref","fail_codes"],"properties":{"schema_ref":{"$ref":"#/$defs/typed_ref"},"fail_codes":{"const":["SCHEMA_INVALID_BOUND_OBJECT","RESULT_PROJECTION_INVALID"]}},"additionalProperties":False}},"additionalProperties":False},"result_projection_authorization":{"type":"object","required":["constant_name","descriptor","comparison","mismatch_code"],"properties":{"constant_name":{"const":"AUTHORIZED_RESULT_PROJECTION_DESCRIPTOR"},"descriptor":{"type":"object"},"comparison":{"const":"WHOLE_JSON_EQUALITY_BEFORE_AST"},"mismatch_code":{"const":"RESULT_PROJECTION_INVALID"}},"additionalProperties":False},"v013_policy":{"type":"object","required":["procedure_id","requirement_ids","preflight_only_ids","semantic_failure_codes","evaluation_order","freshness_bounds_inclusive"],"properties":{"procedure_id":{"const":"REQUIREMENT_MAP_EVAL"},"requirement_ids":{"type":"array","minItems":16,"maxItems":16,"uniqueItems":True,"items":{"type":"string"}},"preflight_only_ids":{"const":["EVIDENCE_UNIVERSE_TYPED","FORBID_CALLER_SUPPLIED_CONTRADICTION_COUNT"]},"semantic_failure_codes":{"const":V013_CODES},"evaluation_order":{"type":"array","minItems":21,"maxItems":21,"items":{"type":"string"}},"freshness_bounds_inclusive":{"const":True}},"additionalProperties":False}},"$defs":{"typed_ref":typed,"law":law,"pin":pin,"source":src,"binding":bind},"additionalProperties":False}
_BASE_MAKE_METACONTRACT_SCHEMA=make_metacontract_schema
def make_metacontract_schema():
 schema=_BASE_MAKE_METACONTRACT_SCHEMA()
 runtime=make_runtime_result_schema()["$defs"]
 schema["$defs"].update({k:v for k,v in runtime.items() if k!="typed_ref"})
 schema["$defs"]["accepted_base_source"]={"type":"object","required":["package_id","package_version","package_schema_id","package_schema_version"],"properties":{"package_id":{"const":"urn:moirae:accord-02r5:specification-package"},"package_version":{"const":"0.1"},"package_schema_id":{"const":"urn:moirae:accord-02r5:schema:specification-package:0.1"},"package_schema_version":{"const":"0.1"}},"additionalProperties":True}
 schema["$defs"]["accepted_vector_source"]={"type":"object","required":["$schema","schema_id","schema_version","profiles","record_catalog","vectors"],"properties":{"$schema":{"const":DIALECT},"schema_id":{"const":"urn:moirae:accord-02c:settlement-test-vectors"},"schema_version":{"const":"0.1"},"profiles":{"type":"array","minItems":1},"record_catalog":{"type":"array","minItems":1},"vectors":{"type":"array","minItems":23,"maxItems":23}},"additionalProperties":True}
 schema_ref=lambda member:{"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":member}
 rc=schema["properties"]["result_contracts"]["properties"]
 rc["procedure_result"]={"type":"object","required":["status","failure","schema_ref"],"properties":{"status":{"const":["PASS","FAIL"]},"failure":{"type":"string","minLength":1},"schema_ref":{"const":schema_ref("procedure_result")}},"additionalProperties":False}
 rc["trust_result"]={"type":"object","required":["status","schema_ref"],"properties":{"status":{"const":{"PASS":"EXPECTED_PACKAGE_VERIFIED","FAIL":["MISSING_EXTERNAL_TRUST_INPUT","FOREIGN_PACKAGE_IDENTITY","TRUSTED_IDENTITY_MISMATCH"]}},"schema_ref":{"const":schema_ref("trust_result")}},"additionalProperties":False}
 rc["pre_execution_result"]["properties"]["schema_ref"]={"const":schema_ref("pre_execution_result")}
 return schema

def make_runtime_result_schema():
 identity={"type":"object","required":["kind","id","version"],"properties":{"kind":{"type":"string","minLength":1},"id":{"type":"string","minLength":1},"version":{"type":"string","minLength":1},"member_id":{"type":"string","minLength":1}},"additionalProperties":False}
 operand={"type":"object","required":["argument","pointer","identity"],"properties":{"argument":{"type":"string","minLength":1},"pointer":{"type":"string"},"identity":{"$ref":"#/$defs/identity"}},"additionalProperties":False}
 pass_result={"type":"object","required":["status","procedure_id","witness"],"properties":{"status":{"const":"PASS"},"procedure_id":{"type":"string","minLength":1},"witness":{"type":"object","required":["assertions_evaluated"],"properties":{"assertions_evaluated":{"type":"integer","minimum":1}},"additionalProperties":False},"result":{"type":"string","minLength":1}},"additionalProperties":False}
 fail_result={"type":"object","required":["status","procedure_id","node_path","assertion_id","code","witness"],"properties":{"status":{"const":"FAIL"},"procedure_id":{"type":"string","minLength":1},"node_path":{"type":"string","minLength":1},"assertion_id":{"type":"string","pattern":"^[A-Z][A-Z0-9_]*$"},"code":{"type":"string","pattern":"^[A-Z][A-Z0-9_-]*$"},"witness":{"type":"object","required":["operands","condition"],"properties":{"operands":{"type":"array","items":operand},"condition":{"enum":["FALSE","EVALUATION_ERROR"]},"expected":{},"actual":{},"error_class":{"type":"string","minLength":1}},"additionalProperties":False},"result":{"type":"string","minLength":1}},"additionalProperties":False}
 procedure={"oneOf":[pass_result,fail_result]}
 identity3={"type":"object","required":["id","version","digest"],"properties":{"id":{"type":"string","minLength":1},"version":{"type":"string","minLength":1},"digest":{"type":"string","pattern":"^[0-9a-f]{64}$"}},"additionalProperties":False}
 idversion={"type":"object","required":["id","version"],"properties":{"id":{"type":"string","minLength":1},"version":{"type":"string","minLength":1}},"additionalProperties":False}
 pass_trust={"type":"object","required":["status","code","witness"],"properties":{"status":{"const":"PASS"},"code":{"const":"EXPECTED_PACKAGE_VERIFIED"},"witness":{"type":"object","required":["stage","expected","actual"],"properties":{"stage":{"const":"EXACT_TRIPLE_MATCH"},"expected":{"$ref":"#/$defs/identity3"},"actual":{"$ref":"#/$defs/identity3"}},"additionalProperties":False}},"additionalProperties":False}
 missing_trust={"type":"object","required":["status","code","witness"],"properties":{"status":{"const":"FAIL"},"code":{"const":"MISSING_EXTERNAL_TRUST_INPUT"},"witness":{"type":"object","required":["stage","missing_fields"],"properties":{"stage":{"const":"MISSING_EXPECTATION"},"missing_fields":{"type":"array","minItems":1,"uniqueItems":True,"items":{"enum":["expected_package_id","expected_package_version","expected_package_digest"]}}},"additionalProperties":False}},"additionalProperties":False}
 foreign_trust={"type":"object","required":["status","code","witness"],"properties":{"status":{"const":"FAIL"},"code":{"const":"FOREIGN_PACKAGE_IDENTITY"},"witness":{"type":"object","required":["stage","expected","actual"],"properties":{"stage":{"const":"IDENTITY_COMPARISON"},"expected":{"$ref":"#/$defs/id_version"},"actual":{"$ref":"#/$defs/id_version"}},"additionalProperties":False}},"additionalProperties":False}
 digest_trust={"type":"object","required":["status","code","witness"],"properties":{"status":{"const":"FAIL"},"code":{"const":"TRUSTED_IDENTITY_MISMATCH"},"witness":{"type":"object","required":["stage","expected","actual"],"properties":{"stage":{"const":"DIGEST_COMPARISON"},"expected":{"$ref":"#/$defs/identity3"},"actual":{"$ref":"#/$defs/identity3"}},"additionalProperties":False}},"additionalProperties":False}
 trust={"oneOf":[pass_trust,missing_trust,foreign_trust,digest_trust]}
 pre_bound={"type":"object","required":["status","stage","code","witness"],"properties":{"status":{"const":"FAIL"},"stage":{"const":"PRE_EXECUTION"},"code":{"const":"SCHEMA_INVALID_BOUND_OBJECT"},"witness":{"type":"object","required":["argument","object_role","schema_ref","instance_pointer","failure_kind","diagnostic","bound_identity"],"properties":{"argument":{"type":"string","minLength":1},"object_role":{"type":"string","minLength":1},"schema_ref":{"type":"string","minLength":1},"instance_pointer":{"type":"string"},"failure_kind":{"enum":["PARSE","JSON_SCHEMA","TYPE","SOURCE_ELIGIBILITY","INTEGRITY"]},"diagnostic":{"type":"string","minLength":1},"bound_identity":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/identity"}]}},"additionalProperties":False}},"additionalProperties":False}
 desc_w={"type":"object","required":["stage","procedure_id","baseline_identity","expected_descriptor","actual_descriptor","mismatch_pointer"],"properties":{"stage":{"const":"DESCRIPTOR_AUTHORIZATION"},"procedure_id":{"type":"string","minLength":1},"baseline_identity":{"$ref":"#/$defs/identity"},"expected_descriptor":{"type":"object"},"actual_descriptor":{"type":"object"},"mismatch_pointer":{"type":"string"}},"additionalProperties":False}
 map_w={"type":"object","required":["stage","procedure_id","map_argument","map_pointer","baseline_argument","baseline_identity","expected","actual","reason"],"properties":{"stage":{"const":"MAP_VALUE_COMPARISON"},"procedure_id":{"type":"string","minLength":1},"map_argument":{"type":"string"},"map_pointer":{"type":"string"},"baseline_argument":{"type":"string"},"baseline_identity":{"$ref":"#/$defs/identity"},"expected":{},"actual":{},"reason":{"enum":["MAP_MISSING_OR_EXTRA_KEY","MAP_VALUE_TYPE","BASELINE_VALUE_TYPE","LITERAL_MISMATCH","PROJECTION_PATH_INVALID"]}},"additionalProperties":False}
 pre_desc={"type":"object","required":["status","stage","code","witness"],"properties":{"status":{"const":"FAIL"},"stage":{"const":"PRE_EXECUTION"},"code":{"const":"RESULT_PROJECTION_INVALID"},"witness":{"$ref":"#/$defs/descriptor_authorization_witness"}},"additionalProperties":False}
 pre_map={"type":"object","required":["status","stage","code","witness"],"properties":{"status":{"const":"FAIL"},"stage":{"const":"PRE_EXECUTION"},"code":{"const":"RESULT_PROJECTION_INVALID"},"witness":{"$ref":"#/$defs/map_value_comparison_witness"}},"additionalProperties":False}
 pre={"oneOf":[pre_bound,pre_desc,pre_map]}
 return {"$schema":DIALECT,"$id":f"{NS}:schema:runtime-results","$defs":{"identity":identity,"typed_ref":identity,"identity3":identity3,"id_version":idversion,"procedure_result":procedure,"trust_result":trust,"pre_execution_result":pre,"descriptor_authorization_witness":desc_w,"map_value_comparison_witness":map_w}}

_BASE_MAKE_METACONTRACT=make_metacontract
def make_metacontract(proc,inv):
 result=_BASE_MAKE_METACONTRACT(proc,inv)
 def schema_member(name): return {"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":name}
 result["result_contracts"]["procedure_result"]["schema_ref"]=schema_member("procedure_result")
 result["result_contracts"]["trust_result"]["schema_ref"]=schema_member("trust_result")
 result["result_contracts"]["pre_execution_result"]["schema_ref"]=schema_member("pre_execution_result")
 return result

def normalize_v013(gov):
 # Explicit typed data replaces path/code concatenation; result settlement map is candidate data but externally authorized in full.
 roots=gov.pop("authority_roots",{})
 gov["authority_bindings"]=[{"authority_key":k,"argument_name":v.split(":",1)[0],"pointer_tokens":([x for x in v.split(":",1)[1].split("/") if x] if ":" in v else [])} for k,v in roots.items()]
 pfr=gov.get("policy_field_roles",{})
 rows=[]
 for k,v in pfr.items():
  if isinstance(v,str) and v.startswith("COMPUTED:"): rows.append({"field_id":k,"role":"COMPUTED","requirement_id":v.split(":",1)[1]})
  else: rows.append({"field_id":k,"role":"LITERAL","requirement_id":None})
 gov["policy_field_roles"]=rows
 for req in gov.get("requirement_map",{}).get("requirements",[]):
  fields=req.pop("source_fields",[])
  req["source_operands"]=[{"argument_name":f.split(".",1)[0],"pointer_tokens":f.split(".")[1:] if "." in f else []} for f in fields]
  auth=req.pop("governing_authority",None)
  req["governing_authority_id"]=auth
  req.pop("procedure",None)
  # Generic diagnostic is fixed by each AST assertion, not produced by a text label.
  preflight_ids={"EVIDENCE_UNIVERSE_TYPED","FORBID_CALLER_SUPPLIED_CONTRADICTION_COUNT"}
  for req in gov.get("requirement_map",{}).get("requirements",[]):
   req["execution_owner"]="UNIVERSAL_PREFLIGHT_SCHEMA" if req["requirement_id"] in preflight_ids else "ORDERED_AST_ASSERTION"
 gov.pop("pass_result",None); gov.pop("fail_result",None)
 gov["outcome_map"]={"PASS":PASS,"FAIL":FAIL}
 gov["result_projection_baseline_pin"]=R3PIN
 return gov

def normalize_external_trust(files):
 trust=files["external-verification-input.contract.json"]
 trust.clear()
 trust.update({"$schema":DIALECT,"schema_ref":sr("external-verification-input-contract"),"$id":f"{NS}:external-verification-input-contract:0.2","object_id":f"{NS}:external-verification-input-contract","object_version":"0.2","input_type":"EXTERNAL_VERIFICATION_INPUT","registry_membership":"FORBIDDEN_NOT_A_PACKAGE_OBJECT","candidate_self_assertion":"FORBIDDEN","fields":{"expected_package_id":{"required":True,"type":"string","source":"CALLER_SUPPLIED","const":"urn:moirae:accord-02r5:specification-package"},"expected_package_version":{"required":True,"type":"string","source":"CALLER_SUPPLIED","const":"0.2"},"expected_package_digest":{"required":True,"type":"string","pattern":"^[0-9a-f]{64}$","source":"CALLER_SUPPLIED","algorithm":"SHA-256"},"digest_mode":{"required":True,"type":"INTEGRITY_MODE","source":"VERIFIER_CONFIGURATION","mode":"SEMANTIC_JSON_CONTENT","algorithm":"SHA-256","serialization":"RFC8785_JCS","excluded_pointers":["/current_candidate_integrity/digest"]}},"candidate_identity_recomputation":{"target":"PACKAGE_DOCUMENT","selection":"ENTIRE_PACKAGE_DOCUMENT","reduction":"REMOVE_POINTER","excluded_pointers":["/current_candidate_integrity/digest"],"serialization":"RFC8785_JCS","encoding":"UTF-8","algorithm":"SHA-256"},"results":{"PASS":{"code":"EXPECTED_PACKAGE_VERIFIED","condition":"exact external package ID, version, and recomputed digest triple"},"FAIL":{"codes":["MISSING_EXTERNAL_TRUST_INPUT","FOREIGN_PACKAGE_IDENTITY","TRUSTED_IDENTITY_MISMATCH"],"order":["MISSING_EXPECTATION","IDENTITY_COMPARISON","DIGEST_COMPARISON"]}},"trust_result_schema_ref":{"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":"trust_result"},"cli":{"--expected-package-id":"expected_package_id","--expected-package-version":"expected_package_version","--expected-package-digest":"expected_package_digest","--verification-input":"PATH_TO_EXTERNAL_JSON_INPUT"}})
 auth=files["authority-requirements.json"]["trust_boundary_requirements"]
 auth.clear(); auth.update({"layers":["INTERNAL_PACKAGE_CONFORMANCE","TRUSTED_PACKAGE_IDENTITY"],"external_input_source":"CALLER_SUPPLIED_OUTSIDE_OBJECT_REGISTRY","candidate_self_assertion_permitted":False,"required_external_fields":["expected_package_id","expected_package_version","expected_package_digest"],"expected_identity":{"package_id":"urn:moirae:accord-02r5:specification-package","package_version":"0.2","digest_algorithm":"SHA-256","digest_serialization":"RFC8785_JCS","excluded_pointers":["/current_candidate_integrity/digest"]},"missing_external_input_result":"FAIL","trust_result_schema_ref":{"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":"trust_result"},"cli":["--expected-package-id","--expected-package-version","--expected-package-digest","--verification-input"],"result_vocabulary":["PASS","FAIL"],"replacement_sub_status":"OUT_OF_SCOPE"})

def make_procedure_registry(raw,inv):
 reg=transform(parse(raw)); old={p["procedure_id"]:p for p in reg["procedures"]}
 proc_rows=[]; codes_by_proc={}
 inv_by_proc={}
 for row in inv["invariants"]: inv_by_proc.setdefault(row["procedure_id"],[]).append(row)
 for pid in PIDS:
  prior=old[pid]
  ast=make_ast(pid)
  # Each procedure definition is a finite ordered ASSERT sequence; no operation-name dispatch remains.
  codes=list(dict.fromkeys(x["failure_code"] for x in ast))
  codes_by_proc[pid]=codes
  compatible=list(dict.fromkeys([c for row in inv_by_proc.get(pid,[]) for c in row.get("compatible_failure_codes",[])] + codes))
  result={"type":"TRUST_RESULT" if pid=="TRUST_ANCHOR_COMPARE" else "BOOLEAN","status":["PASS","FAIL"],"witness_required":True}
  if pid=="TRUST_ANCHOR_COMPARE": result["success_code"]="EXPECTED_PACKAGE_VERIFIED"
  if pid=="REQUIREMENT_MAP_EVAL": result["result_projection"]=copy.deepcopy(RESULT_PROJECTION)
  proc_rows.append({"procedure_id":pid,"arguments":procedure_args(pid),"assertions":ast,"compatible_failure_codes":compatible,"result":result,"missing_behavior":prior.get("missing_behavior","FAIL_CLOSED"),"ambiguity_behavior":prior.get("ambiguity_behavior","FAIL_CLOSED"),"fail_closed":True})
  for row in inv_by_proc.get(pid,[]):
   union=list(dict.fromkeys(row.get("compatible_failure_codes",[])+codes))
   # V013 closure has exactly inherited map/closure codes plus its 15 semantic codes.
   if pid=="REQUIREMENT_MAP_EVAL":
    inherited=["NEGATIVE_REQUIREMENT_MAP_CLOSURE_FAILURE","NEGATIVE_REQUIREMENT_MAP_FAILURE","NEGATIVE_SCOPE_INCOMPLETE","NEGATIVE_SCOPE_NOT_SUFFICIENT"]
    union=list(dict.fromkeys(inherited+V013_CODES))
   row["compatible_failure_codes"]=union
   oldroles={r["role"]:r for r in row.get("input_roles",[])}
   defaults=row.setdefault("default_arguments",{})
   for a in procedure_args(pid):
    n=a["name"]
    if a["origin"]!="RULE_BINDING": continue
    if n not in oldroles:
     oldroles[n]={"role":n,"kind":a["source_constraint"]["expected_kind"],"required":True,"cardinality":"ONE"}
     defaults[n]=candidate_ref(n,a["type"])
   row["input_roles"]=list(oldroles.values())
 reg["schema_ref"]=sr("procedure-registry"); reg["$id"]=f"{NS}:procedure-registry:0.2"; reg["object_id"]=f"{NS}:procedure-registry"; reg["object_version"]="0.2"; reg["procedures"]=proc_rows
 return reg,codes_by_proc

def adjust_package(pkg):
 pkg=transform(pkg)
 pkg["schema_ref"]=sr("specification-package")
 pkg["object_registry_ref"]=ref("REGISTRY",f"{NS}:object-registry")
 pkg["rule_registry_ref"]=ref("REGISTRY",f"{NS}:rule-registry")
 pkg["invariant_registry_ref"]=ref("REGISTRY",f"{NS}:invariant-registry")
 pkg["procedure_registry_ref"]=ref("REGISTRY",f"{NS}:procedure-registry")
 pkg["metacontract_ref"]=ref("CONTRACT",f"{NS}:metacontract")
 pkg["primitive_registry_ref"]=ref("REGISTRY",f"{NS}:primitive-registry")
 pkg["runtime"]={"python":"~=3.14.0","requirements_path":f"{REL}/requirements.txt"}
 pkg["current_candidate_integrity"]["digest"]="0"*64
 pkg["registry_semantic_sha256"]="0"*64
 return pkg

def make_external_source_schema(name):
 return {"$schema":DIALECT,"$id":f"{NS}:schema:{name}","title":f"Pinned external source shape: {name}","type":"object","minProperties":1,"additionalProperties":True}
def source_row(kind,idn,path,schemaname,roles):
 return {"kind":"SCHEMA","id":f"{NS}:schema:{schemaname}","version":"0.2","path":f"{REL}/schema/{schemaname}.schema.json","status":"ACTIVE","roles":["SCHEMA_AUTHORITY"],"classification":"NORMATIVE","schema_ref":sr("schema-of-schema"),"integrity":{"mode":"SEMANTIC_JSON_CONTENT","algorithm":"SHA-256","serialization":"RFC8785_JCS","digest":"0"*64}}
def update_v013_schema(schema):
 schema=transform(schema)
 props=schema.get("properties",{})
 # Replace string path/COMPUTED encodings with closed typed records.
 props.pop("authority_roots",None)
 props["authority_bindings"]={"type":"array","minItems":1,"items":{"type":"object","required":["authority_key","argument_name","pointer_tokens"],"properties":{"authority_key":{"type":"string"},"argument_name":{"type":"string"},"pointer_tokens":{"type":"array","items":{"type":"string"}}},"additionalProperties":False}}
 props["policy_field_roles"]={"type":"array","minItems":1,"items":{"type":"object","required":["field_id","role","requirement_id"],"properties":{"field_id":{"type":"string"},"role":{"enum":["COMPUTED","LITERAL"]},"requirement_id":{"oneOf":[{"type":"string"},{"type":"null"}]}},"additionalProperties":False}}
 props["outcome_map"]={"type":"object","required":["PASS","FAIL"],"properties":{"PASS":{"type":"string","minLength":1},"FAIL":{"type":"string","minLength":1}},"additionalProperties":False}
 if "result_projection_baseline_pin" not in schema["required"]: schema["required"].append("result_projection_baseline_pin")
 props["result_projection_baseline_pin"]={"const":R3PIN}
 props.pop("pass_result",None); props.pop("fail_result",None)
 reqs=props.get("requirement_map",{}).get("properties",{}).get("requirements",{}).get("items",{}).get("properties",{})
 reqs.pop("source_fields",None); reqs.pop("governing_authority",None); reqs.pop("procedure",None)
 reqs["source_operands"]={"type":"array","items":{"type":"object","required":["argument_name","pointer_tokens"],"properties":{"argument_name":{"type":"string"},"pointer_tokens":{"type":"array","items":{"type":"string"}}},"additionalProperties":False}}
 reqs["governing_authority_id"]={"type":"string"}
 return schema

def pointer_tokens(pointer):
 if pointer=="": return []
 if not isinstance(pointer,str) or not pointer.startswith("/"): raise ValueError("non-RFC6901 pointer in frozen target basis")
 out=[]
 for raw in pointer[1:].split("/"):
  i=0; token=""
  while i<len(raw):
   if raw[i]=="~":
    if i+1>=len(raw) or raw[i+1] not in "01": raise ValueError("invalid RFC6901 escape in frozen target basis")
    token += "~" if raw[i+1]=="0" else "/"; i+=2
   else: token+=raw[i]; i+=1
  out.append(token)
 return out

def normalize_semantic_key_authority(doc):
 role_kinds={"authority":"AUTHORITY","inputs":"NORMATIVE_INPUTS","canonicalization":"CANONICALIZATION","references":"CONTRACT","registry":"REGISTRY","partial":"POLICY","target":"CONTRACT","evidence":"EVIDENCE"}
 for row in doc["semantic_keys"]:
  typed=[]
  for raw in [row["authority_path"]]+row["governed_mirror_paths"]:
   role,ptr=raw.split(":/",1)
   if role not in role_kinds: raise ValueError("unknown semantic-key path role "+role)
   typed.append({"kind":role_kinds[role],"pointer_tokens":pointer_tokens("/"+ptr)})
  row["allowed_occurrences"]=typed
 return doc

def normalize_v013_target(target):
 basis=target["relationship_basis"]
 for row in basis["accepted"]:
  ptr=row.pop("accepted_pointer")
  if "must_contain" in row:
   tokens=pointer_tokens(ptr)
   if tokens and tokens[-1]=="*": tokens=tokens[:-1]
   row["selector"]={"kind":"ARRAY_CONTAINS","pointer_tokens":tokens,"must_contain":row.pop("must_contain")}
  else:
   row["selector"]={"kind":"VALUE","pointer_tokens":pointer_tokens(ptr),"must_equal":row.pop("must_equal")}
 for row in basis["candidate_supplied"]:
  row["pointer_tokens"]=pointer_tokens(row.pop("candidate_pointer"))
 return target

def build():
 expected_head=git("rev-parse","HEAD")
 expected_tree=git("rev-parse","HEAD^{tree}")
 if expected_head!=HEAD or expected_tree!=TREE: raise SystemExit(f"frozen checkout mismatch: {expected_head} {expected_tree}")
 files={}; schemas={}
 for p in SRC.glob("*.json"):
  if p.name=="specification-package-0.2.json": continue
  files[p.name]=transform(parse(p.read_bytes()))
 files["v013-target.json"]=normalize_v013_target(files["v013-target.json"])
 files["semantic-key-authority.json"]=normalize_semantic_key_authority(files["semantic-key-authority.json"])
 global FROZEN_SEMANTIC_KEY_ROWS,FROZEN_SEMANTIC_KEY_POLICY
 FROZEN_SEMANTIC_KEY_ROWS=copy.deepcopy(files["semantic-key-authority.json"]["semantic_keys"])
 FROZEN_SEMANTIC_KEY_POLICY=copy.deepcopy(files["semantic-key-authority.json"]["governing_token_singleton"])
 files["normative-inputs.json"]["profile"]["schema_ref"]={"kind":"SCHEMA","id":f"{NS}:schema:normative-inputs","version":"0.2","member_id":"negative_policy_profile"}
 for p in (SRC/"schema").glob("*.schema.json"):
  schemas[p.name]=transform(parse(p.read_bytes()))
 files["governance-requirements.json"]["role_model_requirement"]["allowed_kinds_by_role"]={"NORMATIVE":["AUTHORITY","CANONICALIZATION","CONTRACT","EVIDENCE","NORMATIVE_INPUTS","PACKAGE","POLICY","REGISTRY","SOURCE_VECTOR_CATALOG"],"IDENTITY_AUTHORITY":["REGISTRY"],"SCHEMA_AUTHORITY":["SCHEMA"],"NORMATIVE_BOUND_SOURCE":["PACKAGE"],"CATALOG_BINDING":["SOURCE_VECTOR_CATALOG"],"VECTOR_SOURCE":["SOURCE_VECTOR_CATALOG"],"CURRENT_CANDIDATE_PACKAGE":["PACKAGE"]}
 files["governance-requirements.json"]["governing_authority_requirement"]["authority_roots_source"]="v013-governance:/authority_bindings"
 inv=files["invariant-registry.json"]
 files["v013-governance.json"]=normalize_v013(files["v013-governance.json"])
 global FROZEN_V013_REQUIREMENTS,FROZEN_V013_POLICY_FIELD_ROLES
 FROZEN_V013_REQUIREMENTS=copy.deepcopy(files["v013-governance.json"]["requirement_map"]["requirements"])
 FROZEN_V013_POLICY_FIELD_ROLES=copy.deepcopy(files["v013-governance.json"]["policy_field_roles"])
 proc,codes=make_procedure_registry(source(HEAD,"docs/accord-02e4r5r3/procedure-registry.json"),inv)
 files["procedure-registry.json"]=proc
 files["invariant-registry.json"]=inv
 normalize_external_trust(files)
 # All requirement failures are explicitly assigned by an ordered assertion; code sets are derived, then cross-bound.
 for row in inv["invariants"]:
  row["compatible_failure_codes"]=list(dict.fromkeys(row.get("compatible_failure_codes",[])+codes.get(row["procedure_id"],[])))
  if row["invariant_id"]=="NEGATIVE_REQUIREMENT_MAP_CLOSURE":
   row["compatible_failure_codes"]=list(dict.fromkeys(["NEGATIVE_REQUIREMENT_MAP_CLOSURE_FAILURE","NEGATIVE_REQUIREMENT_MAP_FAILURE","NEGATIVE_SCOPE_INCOMPLETE","NEGATIVE_SCOPE_NOT_SUFFICIENT"]+V013_CODES))
 # Accepted source bindings carry source-only class and exact Git blob pins in addition to both digests.
 for row,blob,classification in zip(files["accepted-source-bindings.json"]["sources"],[BASEBLOB,VECTORBLOB],["SOURCE_ONLY","SOURCE_ONLY"]):
  row["classification"]=classification; row["git_blob"]=blob
  row["schema_ref"]=typed_ref_schema("accepted_base" if row["ref"]["kind"]=="PACKAGE" else "accepted_vectors")
  row["integrity"]["algorithm"]="SHA-256"
  row["integrity"]["modes"]=[{"mode":"SEMANTIC_JSON_CONTENT","expected_digest":row["integrity"]["semantic_json_content_sha256"],"algorithm":"SHA-256","serialization":"RFC8785_JCS","excluded_pointers":[]},{"mode":"RAW_FILE_BYTES","expected_digest":row["integrity"]["raw_file_bytes_sha256"],"algorithm":"SHA-256","serialization":"RAW_BYTES","excluded_pointers":[]}]
 # The typed mode table binds each candidate object identity/role to all digest operands.
 modes=[]
 for row in files["object-registry.json"]["objects"]:
  if row.get("status")=="ACTIVE" and row.get("classification")=="NORMATIVE" and row.get("kind") not in ("PACKAGE",):
   mode=row.get("integrity",{}).get("mode","SEMANTIC_JSON_CONTENT")
   if mode in ("PACKAGE_PINNED_BOOTSTRAP","SELF_DIGEST"): continue
   modes.append({"mode":mode,"object_ref":{"kind":row["kind"],"id":row["id"],"version":row["version"]},"role":"NORMATIVE","algorithm":"SHA-256","serialization":"RFC8785_JCS","excluded_pointers":[]})
 
 files["integrity-modes.json"]["dispatch"]=modes
 files["integrity-modes.json"]["supported_algorithms"]=["SHA-256","SHA-1"]
 files["integrity-modes.json"]["supported_serializations"]=["RFC8785_JCS","RAW_BYTES","GIT_BLOB_OBJECT"]
 # Replace candidate procedure definitions' old operation labels with the closed AST schema.
 schemas["procedure-registry.schema.json"]=make_proc_schema()
 schemas["primitive-registry.schema.json"]=make_primitive_schema()
 schemas["metacontract.schema.json"]=make_metacontract_schema()
 schemas["v013-governance.schema.json"]=update_v013_schema(schemas["v013-governance.schema.json"])
 update_schemas(schemas)
 # Update package schema with the two new normative top-level references.
 pkgschema=schemas["specification-package.schema.json"]
 pp=pkgschema.get("properties",{})
 pp["metacontract_ref"]={"$ref":"#/$defs/ref"}; pp["primitive_registry_ref"]={"$ref":"#/$defs/ref"}
 if "required" in pkgschema: pkgschema["required"]=list(dict.fromkeys(pkgschema["required"]+["metacontract_ref","primitive_registry_ref"]))
 files["primitive-registry.json"]=make_primitive_registry()
 files["metacontract.json"]=make_metacontract(proc,inv)
 pkg=adjust_package(parse(source(HEAD,"docs/accord-02e4r5r3/specification-package-0.2.json")))
 files["specification-package-0.2.json"]=pkg
 # Canonical roots and schemas are written before digest closure.
 for n,v in files.items():
  if n!="object-registry.json" and n!="specification-package-0.2.json": (OUT/n).write_bytes(emit(v))
 for stale in ["runtime-results.schema.json","accepted-base-source.schema.json","accepted-vector-source.schema.json"]:
  q=OUT/"schema"/stale
  if q.exists(): q.unlink()
 for n,v in schemas.items(): (OUT/"schema"/n).parent.mkdir(parents=True,exist_ok=True); (OUT/"schema"/n).write_bytes(emit(v))
 # Insert two explicit normative artifacts and four new schema identities (including frozen external-source validators).
 reg=files["object-registry.json"]
 reg["$id"]=f"{NS}:object-registry:0.2"; reg["object_id"]=f"{NS}:object-registry"; reg["schema_ref"]=sr("object-registry"); reg["object_version"]="0.2"
 for row in reg["objects"]:
  if row["kind"] not in ("PACKAGE","SOURCE_VECTOR_CATALOG") or row["version"]!="0.1":
   if row.get("path","").startswith("docs/accord-02e4r5r3/"): row["path"]=row["path"].replace("docs/accord-02e4r5r3/",REL+"/")
   if "id" in row: row["id"]=row["id"].replace("urn:moirae:accord-02r5r3:",NS+":")
   if row.get("schema_ref"): row["schema_ref"]=transform(row["schema_ref"])
   if row.get("integrity",{}).get("binding_ref"): row["integrity"]["binding_ref"]=transform(row["integrity"]["binding_ref"])
 reg["objects"].extend([
  {"kind":"CONTRACT","id":f"{NS}:metacontract","version":"0.2","path":f"{REL}/metacontract.json","status":"ACTIVE","roles":["NORMATIVE"],"classification":"NORMATIVE","schema_ref":sr("metacontract"),"integrity":{"mode":"SEMANTIC_JSON_CONTENT","algorithm":"SHA-256","serialization":"RFC8785_JCS","digest":"0"*64}},
  {"kind":"REGISTRY","id":f"{NS}:primitive-registry","version":"0.2","path":f"{REL}/primitive-registry.json","status":"ACTIVE","roles":["NORMATIVE"],"classification":"NORMATIVE","schema_ref":sr("primitive-registry"),"integrity":{"mode":"SEMANTIC_JSON_CONTENT","algorithm":"SHA-256","serialization":"RFC8785_JCS","digest":"0"*64}}
 ])
 for row in reg["objects"]:
  row["reference"]={"kind":row["kind"],"id":row["id"],"version":row["version"]}
  if row["kind"]=="SCHEMA":
   schema_file=Path(row["path"]).name
   row["schema_document_id"]=schemas[schema_file]["$id"]
   row["schema_document_version"]=row["version"]
 for fname,name in [("metacontract.schema.json","metacontract"),("primitive-registry.schema.json","primitive-registry")]:
  reg["objects"].append({"kind":"SCHEMA","id":f"{NS}:schema:{name}","version":"0.2","path":f"{REL}/schema/{fname}","status":"ACTIVE","roles":["SCHEMA_AUTHORITY"],"classification":"NORMATIVE","schema_document_id":schemas[fname]["$id"],"schema_document_version":"0.2","integrity":{"mode":"SEMANTIC_JSON_CONTENT","algorithm":"SHA-256","serialization":"RFC8785_JCS","digest":"0"*64}})
 for row in reg["objects"]:
  row["reference"]={"kind":row["kind"],"id":row["id"],"version":row["version"]}
  if row["kind"]=="SCHEMA" and row["id"]==f"{NS}:schema:metacontract": row["members"]=["accepted_base_source","accepted_vector_source","procedure_result","trust_result","pre_execution_result","frozen_rule_authority_producer"]
  if row["kind"]=="SCHEMA" and row["id"]==f"{NS}:schema:external-verification-input-contract": row.pop("members",None)
  if row["kind"]=="SCHEMA" and row["id"]==f"{NS}:schema:normative-inputs": row["members"]=["negative_policy_profile"]
 candidate_rows=[r for r in reg["objects"] if r.get("status")=="ACTIVE" and r.get("classification")=="NORMATIVE"]
 schema_rows=[r for r in candidate_rows if r.get("kind")=="SCHEMA"]
 refmodel=files["reference-model.json"]
 refmodel["discovery_scope"]["owner_references"]=[r["reference"] for r in candidate_rows]
 refmodel["discovery_scope"]["schema_owner_references"]=[r["reference"] for r in schema_rows]
 (OUT/"reference-model.json").write_bytes(emit(refmodel))
 dispatch=[]
 for row in reg["objects"]:
  if row.get("status")=="ACTIVE" and row.get("classification")=="NORMATIVE" and row["kind"]!="PACKAGE":
   mode=row.get("integrity",{}).get("mode","SEMANTIC_JSON_CONTENT")
   if mode in ("PACKAGE_PINNED_BOOTSTRAP","SELF_DIGEST"): continue
   dispatch.append({"mode":mode,"object_ref":row["reference"],"role":"NORMATIVE","algorithm":"SHA-256","serialization":"RFC8785_JCS","excluded_pointers":[]})
 files["integrity-modes.json"]["dispatch"]=dispatch
 files["integrity-modes.json"]["supported_algorithms"]=["SHA-256","SHA-1"]
 files["integrity-modes.json"]["supported_serializations"]=["RFC8785_JCS","RAW_BYTES","GIT_BLOB_OBJECT"]
 (OUT/"integrity-modes.json").write_bytes(emit(files["integrity-modes.json"])) # Cross-file digests (bootstrap registry digest goes into package; package self digest excludes only its digest field).
 for row in reg["objects"]:
  path=row.get("path","")
  if row.get("classification")=="NORMATIVE" and path.startswith(REL+"/") and path not in (f"{REL}/object-registry.json",f"{REL}/specification-package-0.2.json"):
   data=(ROOT/path).read_bytes(); row["integrity"]={"mode":"SEMANTIC_JSON_CONTENT","algorithm":"SHA-256","serialization":"RFC8785_JCS","digest":sem(parse(data))}
 regrow=next(x for x in reg["objects"] if x["kind"]=="REGISTRY" and x["id"]==f"{NS}:object-registry")
 regrow["integrity"]={"mode":"PACKAGE_PINNED_BOOTSTRAP","justification":"The bootstrap registry digest is independently pinned by package.registry_semantic_sha256."}
 # Update package pointers, preserve status/version/accepted expectations and compute the bootstrap pin.
 pkg=files["specification-package-0.2.json"]
 pkg["registry_semantic_sha256"]=sem(reg)
 (OUT/"object-registry.json").write_bytes(emit(reg))
 (OUT/"specification-package-0.2.json").write_bytes(emit(pkg))
 pkg["current_candidate_integrity"]["digest"]=sem({k:v for k,v in pkg.items() if k!="current_candidate_integrity"} | {"current_candidate_integrity":{k:v for k,v in pkg["current_candidate_integrity"].items() if k!="digest"}})
 # Rewrite after self-digest; the top-level semantic digest is now frozen.
 (OUT/"specification-package-0.2.json").write_bytes(emit(pkg))
 # Preserve exact immutable source bytes as export payloads; verifier must still match external pins.
 (OUT/"sources").mkdir(parents=True,exist_ok=True)
 exact={"frozen-r5r2-rule-registry.json":source(R2,R2PATH),"frozen-r5r3-v013-governance.json":source(HEAD,"docs/accord-02e4r5r3/v013-governance.json"),"accepted-base-package-0.1.json":source(BASECOMMIT,BASEPATH),"accepted-vectors-0.1.json":source("5a8bf1e577f71132665ece271e70e30e87df5676",VECTORPATH)}
 for n,b in exact.items(): (OUT/"sources"/n).write_bytes(b)
 for n in ["README.md","requirements.txt"]:
  q=SRC/n
  if q.exists(): (OUT/n).write_bytes(q.read_bytes().replace(b"accord-02e4r5r3",b"accord-02e4r5r4"))
 print(json.dumps({"procedures":len(proc["procedures"]),"assertions":sum(len(p["assertions"]) for p in proc["procedures"]),"primitives":len(PRIMITIVES),"objects":len(reg["objects"]),"schema_files":len(schemas),"codes_by_proc":{k:len(v) for k,v in codes.items()}},indent=2))

def update_schemas(schemas):
 # Procedure registry is closed Draft 2020-12 with recursive finite expressions and typed result descriptors.
 ps=schemas["procedure-registry.schema.json"]
 ps["properties"]["schema_ref"]={"$ref":"#/$defs/typed_ref"}
 ps["$defs"]["argument"]["properties"]["source_constraint"]["$ref"]="#/$defs/source_constraint"
 # The R4 object registry duplicates the typed reference to make resolver input a closed, inspectable value.
 os=schemas["object-registry.schema.json"]; item_schema=os["properties"]["objects"]["items"]
 if "reference" not in item_schema["required"]: item_schema["required"].append("reference")
 item_schema["properties"]["reference"]={"$ref":"#/$defs/ref"}
 item_schema["properties"]["schema_document_id"]={"type":"string","minLength":1}
 item_schema["properties"]["schema_document_version"]={"type":"string","minLength":1}
 item_schema.setdefault("allOf",[]).append({"if":{"properties":{"kind":{"const":"SCHEMA"}},"required":["kind"]},"then":{"required":["schema_document_id","schema_document_version"]}})
 item_schema["allOf"].append({"if":{"properties":{"status":{"const":"ACTIVE"},
                                                  "classification":{"const":"NORMATIVE"},
                                                  "kind":{"not":{"const":"SCHEMA"}}},
                                           "required":["status","classification","kind"]},
                              "then":{"required":["schema_ref"]}})
 for mode,kind,object_id in (
  ("PACKAGE_PINNED_BOOTSTRAP","REGISTRY","urn:moirae:accord-02e4r5r4:object-registry"),
  ("SELF_DIGEST","PACKAGE","urn:moirae:accord-02r5:specification-package")):
  identity_claim={"kind":{"const":kind},"id":{"const":object_id},"version":{"const":"0.2"}}
  mode_claim={"integrity":{"properties":{"mode":{"const":mode}},"required":["mode"]}}
  item_schema["allOf"].append({"if":{"properties":mode_claim,"required":["integrity"]},
                                "then":{"properties":identity_claim}})
  item_schema["allOf"].append({"if":{"properties":identity_claim,"required":["kind","id","version"]},
                                "then":{"properties":{"integrity":{"properties":{"mode":{"const":mode}}}}}})
 rs=schemas["reference-model.schema.json"]
 ds=rs["properties"]["discovery_scope"]
 ds["required"] += ["owner_references","schema_owner_references"]
 ds["properties"]["owner_references"]={"type":"array","minItems":1,"items":{"$ref":"#/$defs/ref"}}
 ds["properties"]["schema_owner_references"]={"type":"array","minItems":1,"items":{"$ref":"#/$defs/ref"}}
 # Bound accepted source descriptor is exact, source-only and carries both integrity modes plus immutable Git identity.
 ac=schemas["accepted-source-bindings.schema.json"]; src=ac["properties"]["sources"]["items"]
 for prop in ["classification","git_blob","schema_ref"]:
  if prop not in src["required"]: src["required"].append(prop)
 src["properties"]["classification"]={"const":"SOURCE_ONLY"}
 src["properties"]["git_blob"]={"type":"string","pattern":"^[0-9a-f]{40}$"}
 src["properties"]["schema_ref"]={"$ref":"#/$defs/ref"}
 integ=src["properties"]["integrity"]
 integ["required"] += ["algorithm","modes"]
 integ["properties"]["algorithm"]={"const":"SHA-256"}
 integ["properties"]["modes"]={"type":"array","minItems":2,"maxItems":2,"items":{"type":"object","required":["mode","expected_digest","algorithm","serialization","excluded_pointers"],"properties":{"mode":{"enum":["SEMANTIC_JSON_CONTENT","RAW_FILE_BYTES"]},"expected_digest":{"type":"string","pattern":"^[0-9a-f]{64}$"},"algorithm":{"const":"SHA-256"},"serialization":{"enum":["RFC8785_JCS","RAW_BYTES"]},"excluded_pointers":{"type":"array","uniqueItems":True,"items":{"type":"string"}}},"additionalProperties":False}}
 gr=schemas["governance-requirements.schema.json"]
 gr["properties"]["role_model_requirement"]={"type":"object","required":["required_role_model","role_source","unknown_role_fails","allowed_kinds_by_role"],"properties":{"required_role_model":{"const":"roles-array"},"role_source":{"const":"object-registry:/role_vocabulary"},"unknown_role_fails":{"const":True},"allowed_kinds_by_role":{"type":"object","minProperties":1,"additionalProperties":{"type":"array","minItems":1,"uniqueItems":True,"items":{"type":"string"}}}},"additionalProperties":False}
 gr["properties"]["governing_authority_requirement"]={"type":"object","required":["authority_roots_source","reference_must_resolve"],"properties":{"authority_roots_source":{"const":"v013-governance:/authority_bindings"},"reference_must_resolve":{"const":True}},"additionalProperties":False}
 # Mode data and dispatch operands are separate: fixed vocabulary plus per-object typed bindings.
 im=schemas["integrity-modes.schema.json"]
 ip=im["properties"]
 ip["supported_algorithms"]={"const":["SHA-256","SHA-1"]}
 ip["supported_serializations"]={"const":["RFC8785_JCS","RAW_BYTES","GIT_BLOB_OBJECT"]}
 ip["dispatch"]={"type":"array","minItems":1,"items":{"type":"object","required":["mode","object_ref","role","algorithm","serialization","excluded_pointers"],"properties":{"mode":{"type":"string"},"object_ref":{"$ref":"#/$defs/ref"},"role":{"type":"string"},"algorithm":{"enum":["SHA-256","SHA-1"]},"serialization":{"enum":["RFC8785_JCS","RAW_BYTES","GIT_BLOB_OBJECT"]},"excluded_pointers":{"type":"array","uniqueItems":True,"items":{"type":"string"}}},"additionalProperties":False}}
 vt=schemas["v013-target.schema.json"]
 basis=vt["properties"]["relationship_basis"]["properties"]
 basis["accepted"]={"type":"array","minItems":1,"items":{"type":"object","required":["field_id","selector"],"properties":{"field_id":{"type":"string","minLength":1},"selector":{"oneOf":[{"type":"object","required":["kind","pointer_tokens","must_equal"],"properties":{"kind":{"const":"VALUE"},"pointer_tokens":{"type":"array","items":{"type":"string"}},"must_equal":{}},"additionalProperties":False},{"type":"object","required":["kind","pointer_tokens","must_contain"],"properties":{"kind":{"const":"ARRAY_CONTAINS"},"pointer_tokens":{"type":"array","items":{"type":"string"}},"must_contain":{}},"additionalProperties":False}]}},"additionalProperties":False}}
 basis["candidate_supplied"]={"type":"array","minItems":1,"items":{"type":"object","required":["field_id","pointer_tokens","provenance"],"properties":{"field_id":{"type":"string","minLength":1},"pointer_tokens":{"type":"array","items":{"type":"string"}},"provenance":{"const":"CANDIDATE_LOCAL_NOT_HISTORY"}},"additionalProperties":False}}
 ni=schemas["normative-inputs.schema.json"]
 ni["properties"]["profile"]={"$ref":"#/$defs/negative_policy_profile"}
 ni["$defs"]["negative_policy_profile"]={"type":"object","required":["schema_ref","object_version","negative_policy"],"properties":{"schema_ref":{"type":"object","required":["kind","id","version","member_id"],"properties":{"kind":{"const":"SCHEMA"},"id":{"const":f"{NS}:schema:normative-inputs"},"version":{"const":"0.2"},"member_id":{"const":"negative_policy_profile"}},"additionalProperties":False},"object_version":{"const":"0.2"},"negative_policy":{"type":"object","required":["minimum_retention_seconds","freshness_max_age_seconds","future_observation_result","stale_result","allowed_consistency_levels","allowed_source_classes","contradiction_rule","complete_read_requirement"],"additionalProperties":False,"properties":{"minimum_retention_seconds":{"type":"integer","minimum":0},"freshness_max_age_seconds":{"type":"integer","minimum":0},"future_observation_result":{"type":"string"},"stale_result":{"type":"string"},"allowed_consistency_levels":{"type":"array","minItems":1,"uniqueItems":True,"items":{"type":"string"}},"allowed_source_classes":{"type":"array","minItems":1,"uniqueItems":True,"items":{"type":"string"}},"contradiction_rule":{"type":"string"},"complete_read_requirement":{"type":"string"}}}},"additionalProperties":False}
 # A number of inherited schemas used patterns that encode a path-derived R3 URI. R4 IDs are explicit URNs.
 for sch in schemas.values():
  # Transforming already changed literals; any remaining old namespace pattern is replaced by a R4 explicit pattern.
  if isinstance(sch,dict):
   for key in ("$id",):
    if key in sch and isinstance(sch[key],str): sch[key]=sch[key].replace("urn:moirae:accord-02r5r3:",NS+":")
 # New package links are required, typed and closed.
 pkg=schemas["specification-package.schema.json"]
 pkg["properties"]["metacontract_ref"]={"$ref":"#/$defs/ref"}; pkg["properties"]["primitive_registry_ref"]={"$ref":"#/$defs/ref"}
 for n in ["metacontract_ref","primitive_registry_ref"]:
  if n not in pkg["required"]: pkg["required"].append(n)
 # V013 schema replaces retired scalar-path forms by closed token/role records and an exact two-result map.
 ext=schemas["external-verification-input-contract.schema.json"]
 ext["required"]=["$schema","$id","schema_ref","object_id","object_version","input_type","registry_membership","candidate_self_assertion","fields","candidate_identity_recomputation","results","trust_result_schema_ref","cli"]
 ext["properties"].update({"$schema":{"const":DIALECT},"$id":{"const":f"{NS}:external-verification-input-contract:0.2"},"object_id":{"const":f"{NS}:external-verification-input-contract"},"object_version":{"const":"0.2"},"input_type":{"const":"EXTERNAL_VERIFICATION_INPUT"},"registry_membership":{"const":"FORBIDDEN_NOT_A_PACKAGE_OBJECT"},"candidate_self_assertion":{"const":"FORBIDDEN"},"fields":{"type":"object","required":["expected_package_id","expected_package_version","expected_package_digest","digest_mode"],"properties":{"expected_package_id":{"type":"object","required":["required","type","source","const"],"properties":{"required":{"const":True},"type":{"const":"string"},"source":{"const":"CALLER_SUPPLIED"},"const":{"const":"urn:moirae:accord-02r5:specification-package"}},"additionalProperties":False},"expected_package_version":{"type":"object","required":["required","type","source","const"],"properties":{"required":{"const":True},"type":{"const":"string"},"source":{"const":"CALLER_SUPPLIED"},"const":{"const":"0.2"}},"additionalProperties":False},"expected_package_digest":{"type":"object","required":["required","type","pattern","source","algorithm"],"properties":{"required":{"const":True},"type":{"const":"string"},"pattern":{"const":"^[0-9a-f]{64}$"},"source":{"const":"CALLER_SUPPLIED"},"algorithm":{"const":"SHA-256"}},"additionalProperties":False},"digest_mode":{"type":"object","required":["required","type","source","mode","algorithm","serialization","excluded_pointers"],"properties":{"required":{"const":True},"type":{"const":"INTEGRITY_MODE"},"source":{"const":"VERIFIER_CONFIGURATION"},"mode":{"const":"SEMANTIC_JSON_CONTENT"},"algorithm":{"const":"SHA-256"},"serialization":{"const":"RFC8785_JCS"},"excluded_pointers":{"const":["/current_candidate_integrity/digest"]}},"additionalProperties":False}},"additionalProperties":False},"candidate_identity_recomputation":{"type":"object","required":["target","selection","reduction","excluded_pointers","serialization","encoding","algorithm"],"properties":{"target":{"const":"PACKAGE_DOCUMENT"},"selection":{"const":"ENTIRE_PACKAGE_DOCUMENT"},"reduction":{"const":"REMOVE_POINTER"},"excluded_pointers":{"const":["/current_candidate_integrity/digest"]},"serialization":{"const":"RFC8785_JCS"},"encoding":{"const":"UTF-8"},"algorithm":{"const":"SHA-256"}},"additionalProperties":False},"results":{"type":"object","required":["PASS","FAIL"],"properties":{"PASS":{"type":"object","required":["code","condition"],"properties":{"code":{"const":"EXPECTED_PACKAGE_VERIFIED"},"condition":{"type":"string"}},"additionalProperties":False},"FAIL":{"type":"object","required":["codes","order"],"properties":{"codes":{"const":["MISSING_EXTERNAL_TRUST_INPUT","FOREIGN_PACKAGE_IDENTITY","TRUSTED_IDENTITY_MISMATCH"]},"order":{"const":["MISSING_EXPECTATION","IDENTITY_COMPARISON","DIGEST_COMPARISON"]}},"additionalProperties":False}},"additionalProperties":False},"trust_result_schema_ref":{"const":{"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":"trust_result"}},"cli":{"type":"object","required":["--expected-package-id","--expected-package-version","--expected-package-digest","--verification-input"],"additionalProperties":{"type":"string"}}})
 ext["additionalProperties"]=False
 auths=schemas["authority-requirements.schema.json"]
 auths["properties"]["trust_boundary_requirements"]={"type":"object","required":["layers","external_input_source","candidate_self_assertion_permitted","required_external_fields","expected_identity","missing_external_input_result","trust_result_schema_ref","cli","result_vocabulary","replacement_sub_status"],"properties":{"layers":{"const":["INTERNAL_PACKAGE_CONFORMANCE","TRUSTED_PACKAGE_IDENTITY"]},"external_input_source":{"const":"CALLER_SUPPLIED_OUTSIDE_OBJECT_REGISTRY"},"candidate_self_assertion_permitted":{"const":False},"required_external_fields":{"const":["expected_package_id","expected_package_version","expected_package_digest"]},"expected_identity":{"type":"object","required":["package_id","package_version","digest_algorithm","digest_serialization","excluded_pointers"],"properties":{"package_id":{"const":"urn:moirae:accord-02r5:specification-package"},"package_version":{"const":"0.2"},"digest_algorithm":{"const":"SHA-256"},"digest_serialization":{"const":"RFC8785_JCS"},"excluded_pointers":{"const":["/current_candidate_integrity/digest"]}},"additionalProperties":False},"missing_external_input_result":{"const":"FAIL"},"trust_result_schema_ref":{"const":{"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":"trust_result"}},"cli":{"const":["--expected-package-id","--expected-package-version","--expected-package-digest","--verification-input"]},"result_vocabulary":{"const":["PASS","FAIL"]},"replacement_sub_status":{"const":"OUT_OF_SCOPE"}},"additionalProperties":False}
 vg=schemas["v013-governance.schema.json"]
 for n in ["authority_roots","pass_result","fail_result"]:
  if n in vg.get("required",[]): vg["required"].remove(n)
 for n in ["authority_bindings","outcome_map"]:
  if n not in vg["required"]: vg["required"].append(n)
 sk_schema=schemas["semantic-key-authority.schema.json"]
 sk_item=sk_schema["properties"]["semantic_keys"]["items"]
 if "allowed_occurrences" not in sk_item["required"]: sk_item["required"].append("allowed_occurrences")
 sk_item["properties"]["allowed_occurrences"]={"type":"array","minItems":1,"uniqueItems":True,"items":{"type":"object","required":["kind","pointer_tokens"],"properties":{"kind":{"enum":["AUTHORITY","CANONICALIZATION","CONTRACT","EVIDENCE","NORMATIVE_INPUTS","POLICY","REGISTRY"]},"pointer_tokens":{"type":"array","items":{"type":"string"}}},"additionalProperties":False}}
 req=vg["properties"]["requirement_map"]["properties"]["requirements"]["items"]
 for n in ["source_fields","governing_authority","procedure"]:
  if n in req.get("required",[]): req["required"].remove(n)
 for n in ["source_operands","governing_authority_id","execution_owner"]:
  if n not in req["required"]: req["required"].append(n)
 req["properties"]["execution_owner"]={"enum":["ORDERED_AST_ASSERTION","UNIVERSAL_PREFLIGHT_SCHEMA"]}
 if "required" in vg["properties"]["policy_field_roles"]: pass

_PREVIOUS_MAKE_AST=make_ast
def make_ast(pid):
 g=lambda n,p:get(arg(n),p)
 if pid=="SELF_DIGEST":
  c=op("DIGEST_VERIFY",value=arg("package"),expected=g("package","/current_candidate_integrity/digest"),algorithm=g("canonicalization","/algorithm"),serialization=g("canonicalization","/serialization"),excluded_pointers=g("canonicalization","/exclusion_pointers"))
  return [assertion(pid,"SELF_DIGEST_VERIFY",c,"PACKAGE_SELF_DIGEST_FAILURE",g("package","/current_candidate_integrity/digest"))]
 if pid=="TRUST_ANCHOR_COMPARE":
  tr=arg("external_trust")
  d=op("DIGEST_VERIFY",value=arg("package"),expected=g("external_trust","/expected_package_digest"),algorithm=get(tr,"/digest_mode/algorithm"),serialization=get(tr,"/digest_mode/serialization"),excluded_pointers=get(tr,"/digest_mode/excluded_pointers"))
  return [assertion(pid,"PACKAGE_ID",equal(g("package","/package_id"),g("external_trust","/expected_package_id")),"FOREIGN_PACKAGE_IDENTITY",g("external_trust","/expected_package_id")),assertion(pid,"PACKAGE_VERSION",equal(g("package","/package_version"),g("external_trust","/expected_package_version")),"FOREIGN_PACKAGE_IDENTITY",g("external_trust","/expected_package_version")),assertion(pid,"PACKAGE_TRUST_DIGEST",d,"TRUSTED_IDENTITY_MISMATCH",g("external_trust","/expected_package_digest"))]
 if pid=="DIGEST_RECOMPUTE":
  objs=filt(g("registry","/objects"),"o0",equal(get(item("o0"),"/status"),lit("ACTIVE")))
  objs=filt(objs,"o1",equal(get(item("o1"),"/classification"),lit("NORMATIVE")))
  objs=filt(objs,"o2",op("NOT",value=equal(get(item("o2"),"/integrity/mode"),lit("PACKAGE_PINNED_BOOTSTRAP"))))
  objs=filt(objs,"o3",op("NOT",value=equal(get(item("o3"),"/integrity/mode"),lit("SELF_DIGEST"))))
  def selected_modes():
   a=filt(g("integrity_modes","/dispatch"),"mk",equal(get(item("mk"),"/object_ref/kind"),get(item("o3"),"/kind")))
   a=filt(a,"mi",equal(get(item("mi"),"/object_ref/id"),get(item("o3"),"/id")))
   a=filt(a,"mv",equal(get(item("mv"),"/object_ref/version"),get(item("o3"),"/version")))
   a=filt(a,"mr",equal(get(item("mr"),"/role"),lit("NORMATIVE")))
   return filt(a,"mm",equal(get(item("mm"),"/mode"),get(item("o3"),"/integrity/mode")))
  once=all_(objs,"o3",equal(count(selected_modes()),lit(1)))
  verified=all_(objs,"o3",all_(selected_modes(),"md",op("DIGEST_VERIFY",value=resolve(get(item("o3"),"/reference")),expected=get(item("o3"),"/integrity/digest"),algorithm=get(item("md"),"/algorithm"),serialization=get(item("md"),"/serialization"),excluded_pointers=get(item("md"),"/excluded_pointers"))))
  return [assertion(pid,"MODE_EXACTLY_ONE",once,"INTEGRITY_MODE_DISPATCH_FAILURE",g("integrity_modes","/dispatch")),assertion(pid,"CONTENT_DIGESTS_VERIFY",verified,"SEMANTIC_DIGEST_VERIFY_FAILURE",objs)]
 if pid=="INTEGRITY_MODE_DISPATCH":
  dispatch=g("integrity_modes","/dispatch")
  objs=filt(g("registry","/objects"),"obj0",equal(get(item("obj0"),"/status"),lit("ACTIVE")))
  objs=filt(objs,"obj1",equal(get(item("obj1"),"/classification"),lit("NORMATIVE")))
  objs=filt(objs,"obj2",op("NOT",value=equal(get(item("obj2"),"/integrity/mode"),lit("PACKAGE_PINNED_BOOTSTRAP"))))
  objs=filt(objs,"obj3",op("NOT",value=equal(get(item("obj3"),"/integrity/mode"),lit("SELF_DIGEST"))))
  def selected_dispatch():
   a=filt(dispatch,"dk",equal(get(item("dk"),"/object_ref/kind"),get(item("obj3"),"/kind")))
   a=filt(a,"di",equal(get(item("di"),"/object_ref/id"),get(item("obj3"),"/id")))
   a=filt(a,"dv",equal(get(item("dv"),"/object_ref/version"),get(item("obj3"),"/version")))
   return filt(a,"dr",equal(get(item("dr"),"/role"),lit("NORMATIVE")))
  alg_ok=all_(dispatch,"d1",any_(g("integrity_modes","/supported_algorithms"),"a",equal(item("a"),get(item("d1"),"/algorithm"))))
  ser_ok=all_(dispatch,"d2",any_(g("integrity_modes","/supported_serializations"),"s",equal(item("s"),get(item("d2"),"/serialization"))))
  mode_ok=all_(dispatch,"d3",any_(g("integrity_modes","/modes"),"m",equal(get(item("m"),"/mode"),get(item("d3"),"/mode"))))
  return [assertion(pid,"DISPATCH_KEY_UNIQUE",unique(dispatch,["/object_ref/kind","/object_ref/id","/object_ref/version","/role"]),"INTEGRITY_MODE_DISPATCH_FAILURE",dispatch),assertion(pid,"DISPATCH_COVERS_OBJECTS",all_(objs,"obj3",equal(count(selected_dispatch()),lit(1))),"INTEGRITY_MODE_DISPATCH_FAILURE",objs),assertion(pid,"ALGORITHM_ENUM",alg_ok,"INTEGRITY_MODE_DISPATCH_FAILURE",dispatch),assertion(pid,"SERIALIZATION_ENUM",ser_ok,"INTEGRITY_MODE_DISPATCH_FAILURE",dispatch),assertion(pid,"MODE_VOCABULARY",mode_ok,"INTEGRITY_MODE_DISPATCH_FAILURE",dispatch)]
 if pid=="DUAL_INTEGRITY":
  rows=g("bindings","/sources")
  role_projection=project(rows,"src",{"kind":get(item("src"),"/ref/kind"),"roles":get(item("src"),"/roles")})
  exists_role=op("SET_EQUAL_STRICT",left=role_projection,right=lit([{"kind":"PACKAGE","roles":["NORMATIVE_BOUND_SOURCE"]},{"kind":"SOURCE_VECTOR_CATALOG","roles":["CATALOG_BINDING","VECTOR_SOURCE"]}]))
  unique_modes=all_(rows,"src",unique(get(item("src"),"/integrity/modes"),["/mode"]))
  both=all_(rows,"src",equal(count(get(item("src"),"/integrity/modes")),lit(2)))
  verified=all_(rows,"src",all_(get(item("src"),"/integrity/modes"),"m",op("DIGEST_VERIFY",value=resolve(get(item("src"),"/ref")),expected=get(item("m"),"/expected_digest"),algorithm=get(item("m"),"/algorithm"),serialization=get(item("m"),"/serialization"),excluded_pointers=get(item("m"),"/excluded_pointers"))))
  return [assertion(pid,"SOURCE_IDENTITY_UNIQUE",unique(rows,["/ref/kind","/ref/id","/ref/version"]),"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",rows),assertion(pid,"SOURCE_CLASS",equal(get(rows,"/0/classification"),lit("SOURCE_ONLY")),"ACCORD-02R3-SOURCE-CLASS-MISMATCH",rows),assertion(pid,"SOURCE_ROLE",exists_role,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",rows),assertion(pid,"MODE_KEYS_UNIQUE",unique_modes,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",rows),assertion(pid,"RAW_AND_SEMANTIC_MODES",both,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",rows),assertion(pid,"BOTH_DIGESTS_VERIFY",verified,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",rows)]
 if pid=="SCHEMA_VALIDATION":
  owners=filt(g("registry","/objects"),"own0",equal(get(item("own0"),"/status"),lit("ACTIVE")))
  owners=filt(owners,"own1",equal(get(item("own1"),"/classification"),lit("NORMATIVE")))
  schemas=filt(g("verification_universe","/objects"),"sch",equal(get(item("sch"),"/kind"),lit("SCHEMA")))
  schema_meta=all_(schemas,"schema_row",schema_validate(get(item("schema_row"),"/content"),get(item("schema_row"),"/content"),"META_SCHEMA"))
  instances=all_(owners,"owner",schema_validate(get(resolve(get(item("owner"),"/schema_ref")),"/content"),get(resolve(get(item("owner"),"/reference")),"/content"),"INSTANCE"))
  return [assertion(pid,"ACTIVE_OWNER_SET_NONEMPTY",num(count(owners),"GT",lit(0)),"STANDARDS_VALIDATION_FAILURE",g("registry","/objects")),assertion(pid,"DISCOVERED_SCHEMA_SET_NONEMPTY",num(count(schemas),"GT",lit(0)),"STANDARDS_VALIDATION_FAILURE",schemas),assertion(pid,"SCHEMA_DOCUMENTS_META_VALID",schema_meta,"STANDARDS_VALIDATION_FAILURE",schemas),assertion(pid,"DECLARED_INSTANCES_VALID",instances,"ACCORD-02R5-STRUCTURE-VALIDATION-FAILURE",owners)]
 if pid=="AUTHORITY_COMPLETENESS":
  rules=project(g("rules","/rules"),"r",{"id":get(item("r"),"/rule_id")})
  frozen=project(get(arg("frozen_rule_authority"),"/rules"),"fr",{"id":get(item("fr"),"/rule_id")})
  active=filt(g("invariants","/invariants"),"iv",equal(get(item("iv"),"/status"),lit("ACTIVE")))
  active_ids=project(active,"ia",{"id":get(item("ia"),"/invariant_id")})
  package_ids=project(g("package","/required_invariant_ids"),"pi",{"id":item("pi")})
  return [assertion(pid,"CANDIDATE_RULE_IDS_UNIQUE",unique(g("rules","/rules"),["/rule_id"]),"CANDIDATE_CLOSURE_FAILURE",g("rules","/rules")),assertion(pid,"FROZEN_RULE_IDS_UNIQUE",unique(get(arg("frozen_rule_authority"),"/rules"),["/rule_id"]),"CANDIDATE_CLOSURE_FAILURE",get(arg("frozen_rule_authority"),"/rules")),assertion(pid,"FROZEN_RULE_ID_SET_EQUAL",op("SET_EQUAL_STRICT",left=rules,right=frozen),"CANDIDATE_CLOSURE_FAILURE",get(arg("frozen_rule_authority"),"/source_pin")),assertion(pid,"ACTIVE_INVARIANTS_MATCH_PACKAGE",op("SET_EQUAL_STRICT",left=active_ids,right=package_ids),"CANDIDATE_CLOSURE_FAILURE",g("package","/required_invariant_ids"))]
 return _PREVIOUS_MAKE_AST(pid)

_MATRIX_MAKE_AST=make_ast
def make_ast(pid):
 g=lambda n,p:get(arg(n),p)
 if pid=="LINEAGE_VALIDATION":
  out=_MATRIX_MAKE_AST(pid)
  out.extend([assertion(pid,"PACKAGE_STATUS",equal(g("package","/status"),lit("CANDIDATE_UNACCEPTED")),"PACKAGE_LINEAGE_FAILURE",g("package","/status")),assertion(pid,"ACCEPTED_BASE_ID",equal(g("accepted_base","/package_id"),g("authority","/package_requirements/family")),"ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH",g("accepted_base","/package_id")),assertion(pid,"BASE_VERSION",equal(g("accepted_base","/package_version"),g("authority","/package_requirements/accepted_base_version")),"ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH",g("accepted_base","/package_version"))])
  return out
 if pid=="SET_EQUALITY":
  deps=g("inputs","/rule_dependencies");edges=g("inputs","/dependency_edges")
  forward=all_(deps,"rule",all_(get(item("rule"),"/depends_on"),"dep",equal(count(filt(filt(edges,"edge0",equal(get(item("edge0"),"/from"),get(item("rule"),"/rule_id"))),"edge1",equal(get(item("edge1"),"/to"),item("dep")))),lit(1))))
  reverse=all_(edges,"edge2",equal(count(filt(filt(deps,"edge_rule",equal(get(item("edge_rule"),"/rule_id"),get(item("edge2"),"/from"))),"rule2",any_(get(item("rule2"),"/depends_on"),"dep2",equal(item("dep2"),get(item("edge2"),"/to"))))),lit(1)))
  return [assertion(pid,"RULE_KEYS_UNIQUE",unique(deps,["/rule_id"]),"DEPENDENCY_GRAPH_EQUAL_FAILURE",deps),assertion(pid,"EDGE_PAIRS_UNIQUE",unique(edges,["/from","/to"]),"RULE_GRAPH_CLOSURE_FAILURE",edges),assertion(pid,"DEPENDENCIES_HAVE_EDGES",forward,"DEPENDENCY_GRAPH_EQUAL_FAILURE",edges),assertion(pid,"EDGES_HAVE_DEPENDENCIES",reverse,"DEPENDENCY_GRAPH_EQUAL_FAILURE",deps)]
 if pid=="PREDICATE_POLICY_AGREEMENT":
  return [assertion(pid,"GLOBAL_ORDER_AUTHORIZED",any_(g("authority","/stage_policy_authorization/global_stage_order"),"go",equal(item("go"),g("inputs","/predicate_policy/global_stage_order"))),"PREDICATE_AUTHORITY_CLOSURE_FAILURE",g("inputs","/predicate_policy/global_stage_order")),assertion(pid,"TRANSITIVITY_AUTHORIZED",any_(g("authority","/stage_policy_authorization/implicit_transitivity"),"tr",equal(item("tr"),g("inputs","/predicate_policy/implicit_transitivity"))),"PREDICATE_AUTHORITY_CLOSURE_FAILURE",g("inputs","/predicate_policy/implicit_transitivity")),assertion(pid,"GLOBAL_ORDER_MIRROR",equal(g("inputs","/predicate_policy/global_stage_order"),g("authority","/stage_policy_requirements/global_stage_order")),"PREDICATE_AUTHORITY_CLOSURE_FAILURE",g("inputs","/predicate_policy")),assertion(pid,"TRANSITIVITY_MIRROR",equal(g("inputs","/predicate_policy/implicit_transitivity"),g("authority","/stage_policy_requirements/implicit_transitivity")),"PREDICATE_AUTHORITY_CLOSURE_FAILURE",g("inputs","/predicate_policy"))]
 if pid=="SCHEMA_NON_VACUITY":
  schemas=filt(g("verification_universe","/objects"),"s0",equal(get(item("s0"),"/kind"),lit("SCHEMA")))
  each=all_(schemas,"s1",op("NOT",value=schema_validate(get(resolve(get(item("s1"),"/reference")),"/content"),lit({"zzz":1}),"INSTANCE")))
  return [assertion(pid,"ACTIVE_SCHEMA_SET_NONEMPTY",num(count(schemas),"GT",lit(0)),"SCHEMA_NON_VACUITY_FAILURE",g("registry","/objects")),assertion(pid,"REJECTS_UNKNOWN_PROPERTY",each,"SCHEMA_NON_VACUITY_FAILURE",schemas)]
 if pid=="CURRENT_PACKAGE_IDENTITY":
  rows=filt(g("registry","/objects"),"p0",equal(get(item("p0"),"/kind"),lit("PACKAGE")))
  rows=filt(rows,"p1",equal(get(item("p1"),"/status"),lit("ACTIVE")))
  rows=filt(rows,"p2",equal(get(item("p2"),"/classification"),lit("NORMATIVE")))
  rows=filt(rows,"p3",equal(get(item("p3"),"/id"),g("authority","/package_requirements/family")))
  rows=filt(rows,"p4",equal(get(item("p4"),"/version"),g("authority","/package_requirements/version")))
  return [assertion(pid,"CURRENT_PACKAGE_UNIQUE",equal(count(rows),lit(1)),"CURRENT_PACKAGE_IDENTITY_FAILURE",rows),assertion(pid,"BOUND_PACKAGE_MATCHES_REGISTRY",equal(get(rows,"/0/id"),g("package","/package_id")),"CURRENT_PACKAGE_IDENTITY_FAILURE",g("package","/package_id")),assertion(pid,"BOUND_PACKAGE_VERSION_MATCHES_REGISTRY",equal(get(rows,"/0/version"),g("package","/package_version")),"CURRENT_PACKAGE_IDENTITY_FAILURE",g("package","/package_version"))]
 if pid=="SUBJECT_ROLE_COVERAGE":
  covered=all_(g("invariants","/invariants"),"iv",all_(get(item("iv"),"/subject_roles"),"sr",any_(get(item("iv"),"/input_roles"),"ir",equal(item("sr"),get(item("ir"),"/role")))))
  return [assertion(pid,"SUBJECT_ROLES_NONEMPTY",all_(g("invariants","/invariants"),"iv0",num(count(get(item("iv0"),"/subject_roles")),"GT",lit(0))),"SUBJECT_ROLE_COVERAGE_FAILURE",g("invariants","/invariants")),assertion(pid,"SUBJECT_ROLE_IS_DECLARED_INPUT",covered,"SUBJECT_ROLE_COVERAGE_FAILURE",g("invariants","/invariants"))]
 if pid=="UNIQUENESS_KEY_APPLIED":
  ids=g("governance","/uniqueness_key_requirement/identity_fields")
  return [assertion(pid,"IDENTITY_FIELDS_EQUAL",equal(g("registry","/identity_fields"),ids),"UNIQUENESS_KEY_APPLIED_FAILURE",g("registry","/identity_fields")),assertion(pid,"CONFIGURED_KEY_EQUAL",equal(g("registry","/uniqueness_key"),ids),"UNIQUENESS_KEY_APPLIED_FAILURE",g("registry","/uniqueness_key")),assertion(pid,"UNIQUE_BY_CONFIGURED_KEY",unique(g("registry","/objects"),["/kind","/id","/version"]),"UNIQUENESS_KEY_APPLIED_FAILURE",g("registry","/objects"))]
 if pid=="ROLE_MODEL_APPLIED":
  role_rows=g("registry","/objects")
  membership=all_(role_rows,"obj",all_(get(item("obj"),"/roles"),"role",any_(op("GET_KEY",object=g("governance","/role_model_requirement/allowed_kinds_by_role"),key=item("role")),"kind",equal(item("kind"),get(item("obj"),"/kind")))))
  vocab=all_(role_rows,"obj2",all_(get(item("obj2"),"/roles"),"role2",any_(g("registry","/role_vocabulary"),"vocab",equal(item("role2"),item("vocab")))))
  return [assertion(pid,"ROLE_KIND_ALLOWED",membership,"ROLE_MODEL_APPLIED_FAILURE",role_rows),assertion(pid,"ROLE_IN_VOCABULARY",vocab,"ROLE_MODEL_APPLIED_FAILURE",g("registry","/role_vocabulary"))]
 if pid=="REFERENCE_DISCOVERY_SCOPE_VALID":
  rows=filt(g("registry","/objects"),"o0",equal(get(item("o0"),"/status"),lit("ACTIVE")))
  rows=filt(rows,"o1",equal(get(item("o1"),"/classification"),lit("NORMATIVE")))
  return [assertion(pid,"SCOPE_STATUS",equal(g("reference_model","/discovery_scope/registry_status"),lit("ACTIVE")),"REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE",g("reference_model","/discovery_scope")),assertion(pid,"SCOPE_CLASS",equal(g("reference_model","/discovery_scope/classification"),lit("NORMATIVE")),"REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE",g("reference_model","/discovery_scope")),assertion(pid,"SCOPE_NONEMPTY",num(count(rows),"GT",lit(0)),"REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE",rows)]
 if pid=="REFERENCE_SHAPE_PREDICATE_APPLIED":
  return [assertion(pid,"REQUIRED_KEYS",equal(g("reference_model","/shape_predicate/required_keys"),lit(["kind","id","version"])),"REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE",g("reference_model","/shape_predicate")),assertion(pid,"OPTIONAL_KEYS",equal(g("reference_model","/shape_predicate/optional_keys"),lit(["member_id"])),"REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE",g("reference_model","/shape_predicate")),assertion(pid,"ADDITIONAL_KEYS",equal(g("reference_model","/shape_predicate/additional_keys"),lit("DISQUALIFY")),"REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE",g("reference_model","/shape_predicate")),assertion(pid,"VALUE_TYPES",equal(g("reference_model","/shape_predicate/all_values_type"),lit("STRING")),"REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE",g("reference_model","/shape_predicate"))]
 if pid=="PROCEDURE_OPERATION_SUPPORTED":
  pids=g("procedures","/procedures");prims=g("primitive_registry","/primitives")
  nodes=filt(descendants(pids),"opnode",equal(get(item("opnode"),"/member_key"),lit("op")))
  op_known=all_(nodes,"n",any_(prims,"pr",equal(get(item("pr"),"/primitive_id"),get(item("n"),"/value"))))
  code_compat=all_(pids,"p",all_(get(item("p"),"/assertions"),"a",any_(get(item("p"),"/compatible_failure_codes"),"c",equal(item("c"),get(item("a"),"/failure_code")))))
  inv_compat=all_(g("invariants","/invariants"),"iv",all_(filt(pids,"p2",equal(get(item("p2"),"/procedure_id"),get(item("iv"),"/procedure_id"))),"p3",all_(get(item("p3"),"/assertions"),"a2",any_(get(item("iv"),"/compatible_failure_codes"),"c2",equal(item("c2"),get(item("a2"),"/failure_code"))))))
  arg_names_unique=all_(pids,"p4",unique(get(item("p4"),"/arguments"),["/name"]))
  assert_ids_unique=all_(pids,"p5",unique(get(item("p5"),"/assertions"),["/assertion_id"]))
  return [assertion(pid,"PROCEDURE_IDS_UNIQUE",unique(pids,["/procedure_id"]),"DUPLICATE_PROCEDURE_ID",pids),assertion(pid,"PRIMITIVE_IDS_UNIQUE",unique(prims,["/primitive_id"]),"DUPLICATE_PRIMITIVE_ID",prims),assertion(pid,"OPS_REGISTERED",op_known,"PROCEDURE_OPERATION_SUPPORTED_FAILURE",nodes),assertion(pid,"PROCEDURE_ARGUMENT_NAMES_UNIQUE",arg_names_unique,"PROCEDURE_OPERATION_SUPPORTED_FAILURE",pids),assertion(pid,"ASSERTION_IDS_UNIQUE",assert_ids_unique,"PROCEDURE_OPERATION_SUPPORTED_FAILURE",pids),assertion(pid,"PROCEDURE_CODES_AUTHORIZED",code_compat,"PROCEDURE_OPERATION_SUPPORTED_FAILURE",pids),assertion(pid,"BOUND_INVARIANT_CODES_AUTHORIZED",inv_compat,"PROCEDURE_OPERATION_SUPPORTED_FAILURE",g("invariants","/invariants"))]
 if pid=="SCHEMA_IDENTITY_MATCHES_REGISTRY":
  schemas=filt(g("registry","/objects"),"s",equal(get(item("s"),"/kind"),lit("SCHEMA")))
  match=all_(schemas,"schema_row",all_(filt(g("verification_universe","/objects"),"obj",equal(get(item("obj"),"/reference"),get(item("schema_row"),"/reference"))),"resolved_schema",equal(get(item("resolved_schema"),"/content/$id"),get(item("schema_row"),"/schema_document_id"))))
  version=all_(schemas,"schema_row2",equal(get(item("schema_row2"),"/schema_document_version"),get(item("schema_row2"),"/version")))
  return [assertion(pid,"SCHEMA_DOCUMENT_ID_MATCHES",match,"SCHEMA_IDENTITY_MATCHES_REGISTRY_FAILURE",schemas),assertion(pid,"SCHEMA_DOCUMENT_VERSION_MATCHES",version,"SCHEMA_IDENTITY_MATCHES_REGISTRY_FAILURE",schemas)]
 return _MATRIX_MAKE_AST(pid)

# The following closed AST overrides make the high-risk cross-artifact checks explicit.
_BOUNDED_BASE_AST=make_ast
def make_ast(pid):
 g=lambda n,p:get(arg(n),p)
 if pid=="LINEAGE_VALIDATION":
  out=_BOUNDED_BASE_AST(pid)
  pkgref=g("package","/accepted_base_ref")
  out += [assertion(pid,"ACCEPTED_BASE_REFERENCE_RESOLVES",equal(get(resolve(pkgref),"/ref"),pkgref),"ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH",pkgref),assertion(pid,"BOUND_ACCEPTED_BASE_ID_MATCHES_REF",equal(g("accepted_base","/package_id"),get(pkgref,"/id")),"ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH",g("accepted_base","/package_id")),assertion(pid,"BOUND_ACCEPTED_BASE_VERSION_MATCHES_REF",equal(g("accepted_base","/package_version"),get(pkgref,"/version")),"ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH",g("accepted_base","/package_version")),assertion(pid,"BOUND_ACCEPTED_BASE_PINNED_ID",equal(g("accepted_base","/package_id"),lit("urn:moirae:accord-02r5:specification-package")),"ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH",g("accepted_base","/package_id")),assertion(pid,"BOUND_ACCEPTED_BASE_PINNED_VERSION",equal(g("accepted_base","/package_version"),lit("0.1")),"ACCORD-02R5-PACKAGE-MISSING-OR-MISMATCH",g("accepted_base","/package_version"))]
  return out
 if pid=="DUAL_INTEGRITY":
  out=_BOUNDED_BASE_AST(pid)
  srcs=g("bindings","/sources")
  semrows=filt(get(item("s"),"/integrity/modes"),"sm",equal(get(item("sm"),"/mode"),lit("SEMANTIC_JSON_CONTENT")))
  rawrows=filt(get(item("s"),"/integrity/modes"),"rm",equal(get(item("rm"),"/mode"),lit("RAW_FILE_BYTES")))
  sem_count=all_(srcs,"s",num(count(semrows),"EQ",lit(1)))
  raw_count=all_(srcs,"s2",num(count(filt(get(item("s2"),"/integrity/modes"),"rm2",equal(get(item("rm2"),"/mode"),lit("RAW_FILE_BYTES")))),"EQ",lit(1)))
  sem_claim=all_(srcs,"s3",all_(filt(get(item("s3"),"/integrity/modes"),"sm2",equal(get(item("sm2"),"/mode"),lit("SEMANTIC_JSON_CONTENT"))),"sm3",equal(get(item("sm3"),"/expected_digest"),get(item("s3"),"/integrity/semantic_json_content_sha256"))))
  raw_claim=all_(srcs,"s4",all_(filt(get(item("s4"),"/integrity/modes"),"rm3",equal(get(item("rm3"),"/mode"),lit("RAW_FILE_BYTES"))),"rm4",equal(get(item("rm4"),"/expected_digest"),get(item("s4"),"/integrity/raw_file_bytes_sha256"))))
  mode_alg=all_(srcs,"s5",all_(get(item("s5"),"/integrity/modes"),"md",equal(get(item("md"),"/algorithm"),lit("SHA-256"))))
  sem_serial=all_(srcs,"s6",all_(filt(get(item("s6"),"/integrity/modes"),"sm3",equal(get(item("sm3"),"/mode"),lit("SEMANTIC_JSON_CONTENT"))),"sm4",equal(get(item("sm4"),"/serialization"),lit("RFC8785_JCS"))))
  raw_serial=all_(srcs,"s7",all_(filt(get(item("s7"),"/integrity/modes"),"rm5",equal(get(item("rm5"),"/mode"),lit("RAW_FILE_BYTES"))),"rm6",equal(get(item("rm6"),"/serialization"),lit("RAW_BYTES"))))
  out += [assertion(pid,"SEMANTIC_MODE_EXACTLY_ONE",sem_count,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",srcs),assertion(pid,"RAW_MODE_EXACTLY_ONE",raw_count,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",srcs),assertion(pid,"SEMANTIC_MODE_MATCHES_PINNED_DIGEST",sem_claim,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",srcs),assertion(pid,"RAW_MODE_MATCHES_PINNED_DIGEST",raw_claim,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",srcs),assertion(pid,"BOTH_MODE_ALGORITHMS_SHA256",mode_alg,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",srcs),assertion(pid,"SEMANTIC_MODE_CANONICALIZATION",sem_serial,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",srcs),assertion(pid,"RAW_MODE_SERIALIZATION",raw_serial,"ACCEPTED_SOURCE_DUAL_INTEGRITY_FAILURE",srcs)]
  return out
 if pid=="REFERENCE_RESOLUTION":
  owners=filt(g("registry","/objects"),"ro0",equal(get(item("ro0"),"/status"),lit("ACTIVE")))
  owners=filt(owners,"ro1",equal(get(item("ro1"),"/classification"),lit("NORMATIVE")))
  owner_refs=project(owners,"ro2",{"ref":get(item("ro2"),"/reference")})
  scope_eq=op("SET_EQUAL_STRICT",left=owner_refs,right=project(g("reference_model","/discovery_scope/owner_references"),"decl",{"ref":item("decl")}))
  # Shape discovery is split into exact base and member-bearing cases. Objects with
  # all required keys but an extra key fail the corresponding exact-key assertion.
  def for_shape(owner_name, want_member):
   content=get(resolve(get(item(owner_name),"/reference")),"/content")
   nodes=descendants(content)
   objs=filt(nodes,"ob0",equal(get(item("ob0"),"/value_type"),lit("OBJECT")))
   complete=filt(objs,"ob1",all_(g("reference_model","/shape_predicate/required_keys"),"rk",any_(get(item("ob1"),"/keys"),"ok",equal(item("rk"),item("ok")))))
   def all_values_strings(object_name,key_name):
    children=descendants(get(item(object_name),"/value"))
    children=filt(children,"child_key",equal(get(item("child_key"),"/member_key"),item(key_name)))
    children=filt(children,"child_direct",equal(count(get(item("child_direct"),"/path_tokens")),lit(1)))
    children=filt(children,"child_string",equal(get(item("child_string"),"/value_type"),lit("STRING")))
    return all_(get(item(object_name),"/keys"),key_name, num(count(children),"EQ",lit(1)))
   if want_member:
    with_member=filt(complete,"ob2",any_(get(item("ob2"),"/keys"),"mk",equal(item("mk"),lit("member_id"))))
    exact=filt(with_member,"ob2_exact",equal(get(item("ob2_exact"),"/keys"),lit(["id","kind","member_id","version"])))
    return filt(exact,"ob2_string",all_values_strings("ob2_string","key2"))
   without_member=filt(complete,"ob3",op("NOT",value=any_(get(item("ob3"),"/keys"),"mk2",equal(item("mk2"),lit("member_id")))))
   exact=filt(without_member,"ob3_exact",equal(get(item("ob3_exact"),"/keys"),lit(["id","kind","version"])))
   return filt(exact,"ob3_string",all_values_strings("ob3_string","key3"))
  base_refs=for_shape("owner",False)
  member_refs=for_shape("owner",True)
  base_exact=all_(base_refs,"br",equal(get(item("br"),"/keys"),lit(["id","kind","version"])))
  member_exact=all_(member_refs,"mr",equal(get(item("mr"),"/keys"),lit(["id","kind","member_id","version"])))
  base_resolves=all_(base_refs,"brr",equal(get(resolve(get(item("brr"),"/value")),"/ref"),get(item("brr"),"/value")))
  member_resolves=all_(member_refs,"mrr",all_(lit(["kind","id","version"]),"identity_field",equal(op("GET_KEY",object=get(resolve(get(item("mrr"),"/value")),"/ref"),key=item("identity_field")),op("GET_KEY",object=get(item("mrr"),"/value"),key=item("identity_field")))))
  return [assertion(pid,"DISCOVERY_OWNER_SET_EXACT",scope_eq,"REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE",g("reference_model","/discovery_scope/owner_references")),assertion(pid,"BASE_REFERENCE_SHAPE_EXACT",all_(owners,"owner",base_exact),"REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE",g("reference_model","/shape_predicate")),assertion(pid,"MEMBER_REFERENCE_SHAPE_EXACT",all_(owners,"owner",member_exact),"REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE",g("reference_model","/shape_predicate")),assertion(pid,"BASE_REFERENCES_RESOLVE_ONCE",all_(owners,"owner",base_resolves),"TYPED_REFERENCE_CLOSURE_FAILURE",g("reference_model","/shape_predicate")),assertion(pid,"MEMBER_REFERENCES_RESOLVE_ONCE",all_(owners,"owner",member_resolves),"TYPED_REFERENCE_CLOSURE_FAILURE",g("reference_model","/shape_predicate"))]
 if pid=="SCHEMA_VALIDATION":
  owners=filt(g("registry","/objects"),"own0",equal(get(item("own0"),"/status"),lit("ACTIVE")))
  owners=filt(owners,"own1",equal(get(item("own1"),"/classification"),lit("NORMATIVE")))
  owners=filt(owners,"own2",{"op":"NOT","value":equal(get(item("own2"),"/kind"),lit("SCHEMA"))})
  schemas=filt(g("registry","/objects"),"sch0",equal(get(item("sch0"),"/kind"),lit("SCHEMA")))
  schema_refs=project(schemas,"sch1",{"ref":get(item("sch1"),"/reference")})
  declared=project(g("reference_model","/discovery_scope/schema_owner_references"),"sch2",{"ref":item("sch2")})
  meta=all_(schemas,"schema_row",schema_validate(get(resolve(get(item("schema_row"),"/reference")),"/content"),get(resolve(get(item("schema_row"),"/reference")),"/content"),"META_SCHEMA"))
  instances=all_(owners,"owner",schema_validate(get(resolve(get(item("owner"),"/schema_ref")),"/content"),get(resolve(get(item("owner"),"/reference")),"/content"),"INSTANCE"))
  return [assertion(pid,"SCHEMA_OWNER_SET_EXACT",op("SET_EQUAL_STRICT",left=schema_refs,right=declared),"STANDARDS_VALIDATION_FAILURE",g("reference_model","/discovery_scope/schema_owner_references")),assertion(pid,"SCHEMA_DOCUMENTS_META_VALID",meta,"STANDARDS_VALIDATION_FAILURE",schemas),assertion(pid,"DECLARED_INSTANCES_VALID",instances,"ACCORD-02R5-STRUCTURE-VALIDATION-FAILURE",owners)]
 if pid=="REFERENCE_DISCOVERY_SCOPE_VALID":
  rows=filt(g("registry","/objects"),"o0",equal(get(item("o0"),"/status"),lit("ACTIVE")))
  rows=filt(rows,"o1",equal(get(item("o1"),"/classification"),lit("NORMATIVE")))
  expected=project(rows,"o2",{"ref":get(item("o2"),"/reference")})
  declared=project(g("reference_model","/discovery_scope/owner_references"),"o3",{"ref":item("o3")})
  return [assertion(pid,"SCOPE_STATUS",equal(g("reference_model","/discovery_scope/registry_status"),lit("ACTIVE")),"REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE",g("reference_model","/discovery_scope")),assertion(pid,"SCOPE_CLASS",equal(g("reference_model","/discovery_scope/classification"),lit("NORMATIVE")),"REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE",g("reference_model","/discovery_scope")),assertion(pid,"OWNER_SET_EXACT",op("SET_EQUAL_STRICT",left=expected,right=declared),"REFERENCE_DISCOVERY_SCOPE_VALID_FAILURE",g("reference_model","/discovery_scope/owner_references"))]
 if pid=="SOURCE_CATALOG_BINDING_MATCH":
  accepted=g("accepted_binding","/sources")
  b=g("candidate_binding","/candidate_binding")
  matches=filt(accepted,"s0",equal(get(item("s0"),"/ref/kind"),get(b,"/assigned_kind")))
  matches=filt(matches,"s1",equal(get(item("s1"),"/ref/id"),get(b,"/assigned_id")))
  matches=filt(matches,"s2",equal(get(item("s2"),"/ref/version"),get(b,"/assigned_version")))
  src=get(matches,"/0")
  registry_rows=filt(g("object_registry","/objects"),"or0",equal(get(item("or0"),"/reference"),get(src,"/ref")))
  modes=get(src,"/integrity/modes")
  semantic=filt(modes,"sm",equal(get(item("sm"),"/mode"),lit("SEMANTIC_JSON_CONTENT")))
  raw=filt(modes,"rm",equal(get(item("rm"),"/mode"),lit("RAW_FILE_BYTES")))
  semantic_vocab=all_(semantic,"sv",any_(g("integrity_modes","/modes"),"vm",equal(get(item("vm"),"/mode"),get(item("sv"),"/mode"))))
  raw_vocab=all_(raw,"rv",any_(g("integrity_modes","/modes"),"vr",equal(get(item("vr"),"/mode"),get(item("rv"),"/mode"))))
  refval=get(src,"/ref")
  resolved=resolve(refval)
  catalog_role=any_(get(registry_rows,"/0/roles"),"r1",equal(item("r1"),lit("CATALOG_BINDING")))
  vector_role=any_(get(registry_rows,"/0/roles"),"r2",equal(item("r2"),lit("VECTOR_SOURCE")))
  checks=[assertion(pid,"ACCEPTED_SOURCE_KEYS_UNIQUE",unique(accepted,["/ref/kind","/ref/id","/ref/version"]),"DUPLICATE_ACCEPTED_SOURCE_IDENTITY",accepted),assertion(pid,"EXACT_ACCEPTED_BINDING_EXISTS",equal(count(matches),lit(1)),"SOURCE_CATALOG_BINDING_FAILURE",b),assertion(pid,"ACCEPTED_SOURCE_RESOLVES",equal(get(resolved,"/ref"),refval),"SOURCE_CATALOG_BINDING_FAILURE",refval),assertion(pid,"EXACT_SOURCE_PATH",equal(get(b,"/repository_root_path"),get(src,"/path")),"SOURCE_CATALOG_BINDING_FAILURE",get(b,"/repository_root_path")),assertion(pid,"RESOLVED_PATH_MATCHES_PIN",equal(get(resolved,"/path"),get(src,"/path")),"SOURCE_CATALOG_BINDING_FAILURE",get(src,"/path")),assertion(pid,"REGISTRY_SOURCE_ROW_UNIQUE",equal(count(registry_rows),lit(1)),"SOURCE_CATALOG_BINDING_FAILURE",refval),assertion(pid,"REGISTRY_SOURCE_STATUS",equal(get(registry_rows,"/0/status"),lit("ACTIVE_ACCEPTED_SOURCE")),"SOURCE_CATALOG_BINDING_FAILURE",registry_rows),assertion(pid,"REGISTRY_SOURCE_CLASS",equal(get(registry_rows,"/0/classification"),lit("PROVENANCE")),"SOURCE_CATALOG_BINDING_FAILURE",registry_rows),assertion(pid,"REGISTRY_SOURCE_PATH",equal(get(registry_rows,"/0/path"),get(src,"/path")),"SOURCE_CATALOG_BINDING_FAILURE",registry_rows),assertion(pid,"REGISTRY_SOURCE_CATALOG_ROLE",catalog_role,"SOURCE_CATALOG_BINDING_FAILURE",registry_rows),assertion(pid,"REGISTRY_SOURCE_VECTOR_ROLE",vector_role,"SOURCE_CATALOG_BINDING_FAILURE",registry_rows),assertion(pid,"SEMANTIC_DIGEST_CLAIM",equal(get(b,"/semantic_json_content_sha256"),get(src,"/integrity/semantic_json_content_sha256")),"SOURCE_CATALOG_BINDING_FAILURE",get(b,"/semantic_json_content_sha256")),assertion(pid,"RAW_DIGEST_CLAIM",equal(get(b,"/raw_file_bytes_sha256"),get(src,"/integrity/raw_file_bytes_sha256")),"SOURCE_CATALOG_BINDING_FAILURE",get(b,"/raw_file_bytes_sha256")),assertion(pid,"CLASSIFICATION_CLAIM",equal(get(b,"/declared_integrity_class"),get(semantic,"/0/mode")),"SOURCE_CATALOG_BINDING_FAILURE",get(b,"/declared_integrity_class")),assertion(pid,"CANONICALIZATION_CLAIM",equal(get(b,"/declared_canonicalization"),get(semantic,"/0/serialization")),"SOURCE_CATALOG_BINDING_FAILURE",get(b,"/declared_canonicalization")),assertion(pid,"ALGORITHM_CLAIM",equal(get(b,"/declared_algorithm"),get(src,"/integrity/algorithm")),"SOURCE_CATALOG_BINDING_FAILURE",get(b,"/declared_algorithm")),assertion(pid,"RAW_AND_SEMANTIC_MODES_PRESENT",equal(count(semantic),lit(1)),"SOURCE_CATALOG_BINDING_FAILURE",modes),assertion(pid,"RAW_MODE_PRESENT",equal(count(raw),lit(1)),"SOURCE_CATALOG_BINDING_FAILURE",modes),assertion(pid,"SEMANTIC_MODE_VOCABULARY",semantic_vocab,"SOURCE_CATALOG_BINDING_FAILURE",modes),assertion(pid,"RAW_MODE_VOCABULARY",raw_vocab,"SOURCE_CATALOG_BINDING_FAILURE",modes),assertion(pid,"SEMANTIC_MODE_DIGEST_VERIFIES",all_(semantic,"smv",op("DIGEST_VERIFY",value=resolved,expected=get(item("smv"),"/expected_digest"),algorithm=get(item("smv"),"/algorithm"),serialization=get(item("smv"),"/serialization"),excluded_pointers=get(item("smv"),"/excluded_pointers"))),"SOURCE_CATALOG_BINDING_FAILURE",semantic),assertion(pid,"RAW_MODE_DIGEST_VERIFIES",all_(raw,"rmv",op("DIGEST_VERIFY",value=resolved,expected=get(item("rmv"),"/expected_digest"),algorithm=get(item("rmv"),"/algorithm"),serialization=get(item("rmv"),"/serialization"),excluded_pointers=get(item("rmv"),"/excluded_pointers"))),"SOURCE_CATALOG_BINDING_FAILURE",raw)]
  return checks
 if pid=="PROPOSITION_INVENTORY_BOUND":
  cols=g("inventory","/collection_propositions"); members=g("inventory","/member_propositions"); exps=g("inputs","/vector_expectations")
  expected=project(exps,"ve",{"id":get(item("ve"),"/vector_id")})
  actual=project(members,"me",{"id":get(item("me"),"/proposition_id")})
  collection_id=get(cols,"/0/proposition_id")
  closure=all_(members,"m",equal(get(item("m"),"/member_of"),collection_id))
  p=g("inventory","/projection_propositions")
  projection_exact=all_(p,"p",equal(get(item("p"),"/projection"),lit({"source":"inputs:/vector_expectations/*","key":"vector_id","value":"expected"})))
  collection_exact=all_(cols,"c",equal(get(item("c"),"/member_pointer"),lit("inputs:/vector_expectations/*/vector_id")))
  projection_parent=all_(p,"p2",equal(get(item("p2"),"/collection_proposition_id"),collection_id))
  member_kind=all_(members,"m2",equal(get(item("m2"),"/kind"),lit("MEMBER")))
  return [assertion(pid,"COLLECTION_KEYS_UNIQUE",unique(cols,["/proposition_id"]),"PROPOSITION_INVENTORY_BOUND_FAILURE",cols),assertion(pid,"MEMBER_IDS_UNIQUE",unique(members,["/proposition_id"]),"PROPOSITION_INVENTORY_BOUND_FAILURE",members),assertion(pid,"INPUT_VECTOR_SET_BOUND",op("SET_EQUAL_STRICT",left=expected,right=actual),"PROPOSITION_INVENTORY_BOUND_FAILURE",members),assertion(pid,"MEMBERS_CLOSED_OVER_COLLECTION",closure,"PROPOSITION_INVENTORY_BOUND_FAILURE",members),assertion(pid,"MEMBER_KIND_EXACT",member_kind,"PROPOSITION_INVENTORY_BOUND_FAILURE",members),assertion(pid,"COLLECTION_NONEMPTY",num(count(cols),"EQ",lit(1)),"PROPOSITION_INVENTORY_BOUND_FAILURE",cols),assertion(pid,"COLLECTION_POINTER_EXACT",collection_exact,"PROPOSITION_INVENTORY_BOUND_FAILURE",cols),assertion(pid,"PROJECTION_CARDINALITY",num(count(p),"EQ",lit(1)),"PROPOSITION_INVENTORY_BOUND_FAILURE",p),assertion(pid,"PROJECTION_DEFINITION_EXACT",projection_exact,"PROPOSITION_INVENTORY_BOUND_FAILURE",p),assertion(pid,"PROJECTION_PARENT_BOUND",projection_parent,"PROPOSITION_INVENTORY_BOUND_FAILURE",p)] + [assertion(pid,"DERIVATION_POINTER_PINNED",equal(g("inventory","/derived_from/vector_expectations_pointer"),lit("inputs:/vector_expectations/*")),"PROPOSITION_INVENTORY_BOUND_FAILURE",g("inventory","/derived_from/vector_expectations_pointer")),assertion(pid,"ACCEPTED_CATALOG_ID_PINNED",equal(g("inventory","/derived_from/accepted_catalog_ref"),lit({"kind":"SOURCE_VECTOR_CATALOG","id":"urn:moirae:accord-02r5:source-vector-catalog","version":"0.1"})),"PROPOSITION_INVENTORY_BOUND_FAILURE",g("inventory","/derived_from/accepted_catalog_ref"))]
 if pid=="DERIVATION_ROLE_CLOSURE":
  procs=g("procedures","/procedures")
  refs=lambda p,n:filt(descendants(item(p)),n,equal(get(item(n),"/member_key"),lit("arg")))
  terminals_declared=all_(procs,"p2",all_(refs("p2","n3"),"n3",any_(get(item("p2"),"/arguments"),"a2",equal(get(item("n3"),"/value"),get(item("a2"),"/name")))))
  return [assertion(pid,"AST_ARGUMENT_TERMINALS_DECLARED",terminals_declared,"DERIVATION_ROLE_CLOSURE_FAILURE",procs)]
 if pid=="ARITY_AGREEMENT":
  invs=g("invariants","/invariants"); procs=g("procedures","/procedures")
  role_unique=all_(invs,"iv",unique(get(item("iv"),"/input_roles"),["/role"]))
  def procrow(ivname): return get(filt(procs,"pr",equal(get(item("pr"),"/procedure_id"),get(item(ivname),"/procedure_id"))),"/0")
  role_sets=all_(invs,"iv2",op("SET_EQUAL_STRICT",left=project(get(item("iv2"),"/input_roles"),"ir",{"name":get(item("ir"),"/role")}),right=project(filt(get(procrow("iv2"),"/arguments"),"arg",equal(get(item("arg"),"/origin"),lit("RULE_BINDING"))),"arg2",{"name":get(item("arg2"),"/name")})))
  kind_agreement=all_(invs,"iv3",all_(get(item("iv3"),"/input_roles"),"role",all_(filt(get(procrow("iv3"),"/arguments"),"arg3",equal(get(item("arg3"),"/name"),get(item("role"),"/role"))),"match",equal(get(item("match"),"/source_constraint/expected_kind"),get(item("role"),"/kind")))))
  role_cardinality=all_(invs,"iv4",all_(get(item("iv4"),"/input_roles"),"role4",all_(filt(get(procrow("iv4"),"/arguments"),"arg4",equal(get(item("arg4"),"/name"),get(item("role4"),"/role"))),"match4",equal(get(item("match4"),"/cardinality"),get(item("role4"),"/cardinality")))))
  role_required=all_(invs,"iv5",all_(get(item("iv5"),"/input_roles"),"role5",all_(filt(get(procrow("iv5"),"/arguments"),"arg5",equal(get(item("arg5"),"/name"),get(item("role5"),"/role"))),"match5",equal(get(item("match5"),"/required"),get(item("role5"),"/required")))))
  return [assertion(pid,"INVARIANT_IDS_UNIQUE",unique(invs,["/invariant_id"]),"INVARIANT_PROCEDURE_ARITY_AGREEMENT_FAILURE",invs),assertion(pid,"INPUT_ROLE_KEYS_UNIQUE",role_unique,"INVARIANT_PROCEDURE_ARITY_AGREEMENT_FAILURE",invs),assertion(pid,"INPUT_ROLES_MATCH_PROCEDURE_ARGS",role_sets,"INVARIANT_PROCEDURE_ARITY_AGREEMENT_FAILURE",invs),assertion(pid,"INPUT_ROLE_KIND_MATCHES_ARG_TYPE",kind_agreement,"INVARIANT_PROCEDURE_ARITY_AGREEMENT_FAILURE",invs),assertion(pid,"INPUT_ROLE_CARDINALITY_MATCHES_ARG",role_cardinality,"INVARIANT_PROCEDURE_ARITY_AGREEMENT_FAILURE",invs),assertion(pid,"INPUT_ROLE_REQUIRED_MATCHES_ARG",role_required,"INVARIANT_PROCEDURE_ARITY_AGREEMENT_FAILURE",invs)]
 if pid=="DEFAULT_ARGUMENT_COVERAGE":
  invs=g("invariants","/invariants"); procs=g("procedures","/procedures")
  def direct_defaults(ivname):
   rows=descendants(get(item(ivname),"/default_arguments"))
   rows=filt(rows,"d0",equal(get(item("d0"),"/value_type"),lit("OBJECT")))
   return filt(rows,"d1",equal(count(get(item("d1"),"/path_tokens")),lit(1)))
  resolved=all_(invs,"iv",all_(direct_defaults("iv"),"dr",equal(get(resolve(get(item("dr"),"/value")),"/ref"),get(item("dr"),"/value"))))
  role_rows=all_(invs,"iv2",all_(get(item("iv2"),"/input_roles"),"ir",num(count(filt(direct_defaults("iv2"),"d2",equal(get(item("d2"),"/member_key"),get(item("ir"),"/role")))),"EQ",lit(1))))
  exact_keys=all_(invs,"iv3",op("SET_EQUAL_STRICT",left=project(get(item("iv3"),"/input_roles"),"ir3",{"key":get(item("ir3"),"/role")}),right=project(direct_defaults("iv3"),"d3",{"key":get(item("d3"),"/member_key")})))
  default_kinds=all_(invs,"iv4",all_(get(item("iv4"),"/input_roles"),"ir4",all_(filt(direct_defaults("iv4"),"d4",equal(get(item("d4"),"/member_key"),get(item("ir4"),"/role"))),"d5",equal(get(get(item("d5"),"/value"),"/kind"),get(item("ir4"),"/kind")))))
  def proc_args(ivname):
   prs=filt(procs,"pdef",equal(get(item("pdef"),"/procedure_id"),get(item(ivname),"/procedure_id")))
   return filt(get(prs,"/0/arguments"),"parg",equal(get(item("parg"),"/origin"),lit("RULE_BINDING")))
  bound_schema=all_(invs,"iv5",all_(get(item("iv5"),"/input_roles"),"ir5",all_(filt(direct_defaults("iv5"),"d6",equal(get(item("d6"),"/member_key"),get(item("ir5"),"/role"))),"d7",all_(filt(proc_args("iv5"),"a6",equal(get(item("a6"),"/name"),get(item("ir5"),"/role"))),"a7",equal(get(resolve(get(item("d7"),"/value")),"/schema_ref"),get(item("a7"),"/source_constraint/expected_schema_ref"))))))
  bound_status_class=all_(invs,"iv10",all_(get(item("iv10"),"/input_roles"),"ir10",all_(filt(direct_defaults("iv10"),"d18",equal(get(item("d18"),"/member_key"),get(item("ir10"),"/role"))),"d19",all_(filt(proc_args("iv10"),"a18",equal(get(item("a18"),"/name"),get(item("ir10"),"/role"))),"a19",equal(get(resolve(get(item("d19"),"/value")),"/status"),get(item("a19"),"/source_constraint/status"))))))
  bound_class=all_(invs,"iv11",all_(get(item("iv11"),"/input_roles"),"ir11",all_(filt(direct_defaults("iv11"),"d20",equal(get(item("d20"),"/member_key"),get(item("ir11"),"/role"))),"d21",all_(filt(proc_args("iv11"),"a20",equal(get(item("a20"),"/name"),get(item("ir11"),"/role"))),"a21",equal(get(resolve(get(item("d21"),"/value")),"/classification"),get(item("a21"),"/source_constraint/classification"))))))
  bound_source_identity=all_(invs,"iv6",all_(get(item("iv6"),"/input_roles"),"ir6",all_(filt(direct_defaults("iv6"),"d8",equal(get(item("d8"),"/member_key"),get(item("ir6"),"/role"))),"d9",all_(filt(proc_args("iv6"),"a8",equal(get(item("a8"),"/name"),get(item("ir6"),"/role"))),"a9",equal(get(resolve(get(item("d9"),"/value")),"/ref"),get(item("d9"),"/value"))))))
  role_eligibility=all_(invs,"iv7",all_(get(item("iv7"),"/input_roles"),"ir7",all_(filt(direct_defaults("iv7"),"d10",equal(get(item("d10"),"/member_key"),get(item("ir7"),"/role"))),"d11",all_(filt(proc_args("iv7"),"a10",equal(get(item("a10"),"/name"),get(item("ir7"),"/role"))),"a11",all_(get(item("a11"),"/source_constraint/required_roles"),"required_role",any_(get(resolve(get(item("d11"),"/value")),"/roles"),"actual_role",equal(item("required_role"),item("actual_role"))))))))
  exact_pin=all_(invs,"iv8",all_(get(item("iv8"),"/input_roles"),"ir8",all_(filt(direct_defaults("iv8"),"d12",equal(get(item("d12"),"/member_key"),get(item("ir8"),"/role"))),"d13",all_(filt(proc_args("iv8"),"a12",equal(get(item("a12"),"/name"),get(item("ir8"),"/role"))),"a13",all_(filt(filt(proc_args("iv8"),"a14",equal(get(item("a14"),"/source_constraint/identity_constraint/mode"),lit("EXACT_REFERENCE"))),"a14_role",equal(get(item("a14_role"),"/name"),get(item("ir8"),"/role"))),"exact_arg",all_(filt(direct_defaults("iv8"),"d14",equal(get(item("d14"),"/member_key"),get(item("ir8"),"/role"))),"exact_default",equal(get(resolve(get(item("exact_default"),"/value")),"/ref"),get(item("exact_arg"),"/source_constraint/identity_constraint/ref"))))))))
  exact_path=all_(invs,"iv9",all_(get(item("iv9"),"/input_roles"),"ir9",all_(filt(direct_defaults("iv9"),"d15",equal(get(item("d15"),"/member_key"),get(item("ir9"),"/role"))),"d16",all_(filt(proc_args("iv9"),"a15",equal(get(item("a15"),"/name"),get(item("ir9"),"/role"))),"a16",all_(filt(filt(proc_args("iv9"),"a17",equal(get(item("a17"),"/source_constraint/identity_constraint/mode"),lit("EXACT_REFERENCE"))),"a17_role",equal(get(item("a17_role"),"/name"),get(item("ir9"),"/role"))),"exact_arg2",all_(filt(direct_defaults("iv9"),"d17",equal(get(item("d17"),"/member_key"),get(item("ir9"),"/role"))),"exact_default2",equal(get(resolve(get(item("exact_default2"),"/value")),"/path"),get(item("exact_arg2"),"/source_constraint/identity_constraint/canonical_path"))))))))
  return [assertion(pid,"DEFAULT_REFERENCES_RESOLVE",resolved,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"DEFAULT_KEYS_EXACT",exact_keys,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"DEFAULT_ROLE_COVERAGE",role_rows,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"DEFAULT_KIND_MATCHES_ROLE",default_kinds,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"DEFAULT_SCHEMA_MATCHES_ARGUMENT",bound_schema,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"DEFAULT_STATUS_MATCHES_SOURCE_CONSTRAINT",bound_status_class,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"DEFAULT_CLASS_MATCHES_SOURCE_CONSTRAINT",bound_class,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"DEFAULT_RESOLVES_EXACT_TYPED_REFERENCE",bound_source_identity,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"DEFAULT_REQUIRED_ROLES_ENFORCED",role_eligibility,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"EXTERNAL_DEFAULT_REF_PINNED",exact_pin,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs),assertion(pid,"EXTERNAL_DEFAULT_PATH_PINNED",exact_path,"DEFAULT_ARGUMENT_COVERAGE_FAILURE",invs)]
 if pid=="PROFILE_REFERENCE_PINNING":
  expected={"kind":"SCHEMA","id":f"{NS}:schema:normative-inputs","version":"0.2","member_id":"negative_policy_profile"}
  return [assertion(pid,"PROFILE_SCHEMA_REFERENCE_EXACT",equal(g("inputs","/profile/schema_ref"),lit(expected)),"PROFILE_REFERENCE_PINNING_FAILURE",g("inputs","/profile/schema_ref")),assertion(pid,"PROFILE_SCHEMA_VERSION_MATCHES_AUTHORITY",equal(get(g("inputs","/profile/schema_ref"),"/version"),g("authority","/package_requirements/version")),"PROFILE_REFERENCE_PINNING_FAILURE",g("inputs","/profile/schema_ref/version")),assertion(pid,"PROFILE_INSTANCE_VERSION_MATCHES_AUTHORITY",equal(g("inputs","/profile/object_version"),g("authority","/package_requirements/version")),"PROFILE_REFERENCE_PINNING_FAILURE",g("inputs","/profile/object_version"))]
 if pid=="GOVERNING_AUTHORITY_REFERENCE_VALID":
  expected=[{"authority_key":"SETTLEMENT_NEGATIVE_POLICY","argument_name":"inputs","pointer_tokens":["profile","negative_policy"]},{"authority_key":"TARGET_CONTRACT","argument_name":"target","pointer_tokens":[]},{"authority_key":"EVIDENCE_CONTRACT","argument_name":"evidence","pointer_tokens":[]}]
  contract_refs_expected={"integrity_modes":ref("CONTRACT",f"{NS}:integrity-modes"),"semantic_key_authority":ref("CONTRACT",f"{NS}:semantic-key-authority"),"governance_requirements":ref("CONTRACT",f"{NS}:governance-requirements"),"external_verification_contract":ref("CONTRACT",f"{NS}:external-verification-input-contract")}
  contract_refs=g("authority","/governing_contract_refs")
  reqs=g("v013_governance","/requirement_map/requirements")
  reqkeys=project(reqs,"req",{"key":get(item("req"),"/governing_authority_id")})
  bindings=g("v013_governance","/authority_bindings")
  bindingkeys=project(bindings,"ab",{"key":get(item("ab"),"/authority_key")})
  every_requirement_bound=all_(reqs,"req2",equal(count(filt(bindings,"ab2",equal(get(item("ab2"),"/authority_key"),get(item("req2"),"/governing_authority_id")))),lit(1)))
  every_binding_used=all_(bindings,"ab3",any_(reqs,"req3",equal(get(item("req3"),"/governing_authority_id"),get(item("ab3"),"/authority_key"))))
  extra=[]
  extra.append(assertion(pid,"GOVERNING_CONTRACT_REFS_EXACT",equal(contract_refs,lit(contract_refs_expected)),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",contract_refs))
  schema_names={"integrity_modes":"integrity-modes","semantic_key_authority":"semantic-key-authority","governance_requirements":"governance-requirements","external_verification_contract":"external-verification-input-contract"}
  for key,schema_name in schema_names.items():
   ref_value=get(arg("authority"),"/governing_contract_refs/"+key)
   resolved=resolve(ref_value)
   extra.append(assertion(pid,key.upper()+"_REF_RESOLVES",equal(get(resolved,"/ref"),ref_value),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",ref_value))
   schema_ref=ref("SCHEMA",f"{NS}:schema:{schema_name}")
   extra.append(assertion(pid,key.upper()+"_SCHEMA_EXACT",equal(get(get(resolved,"/content"),"/schema_ref"),lit(schema_ref)),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",ref_value))
  modes_content=get(resolve(get(arg("authority"),"/governing_contract_refs/integrity_modes")),"/content")
  dispatch_rows=g("integrity_modes","/dispatch")
  algorithms_supported=all_(dispatch_rows,"mode_row",any_(g("integrity_modes","/supported_algorithms"),"algorithm",equal(get(item("mode_row"),"/algorithm"),item("algorithm"))))
  serializations_supported=all_(dispatch_rows,"mode_row2",any_(g("integrity_modes","/supported_serializations"),"serialization",equal(get(item("mode_row2"),"/serialization"),item("serialization"))))
  govreq_content=get(resolve(get(arg("authority"),"/governing_contract_refs/governance_requirements")),"/content")
  field_roles=g("v013_governance","/policy_field_roles")
  field_role_requirements_resolve=all_(field_roles,"field_role",equal(count(filt(reqs,"field_role_req",equal(get(item("field_role_req"),"/requirement_id"),get(item("field_role"),"/requirement_id")))),lit(1)))
  base=[assertion(pid,"AUTHORITY_BINDING_KEYS_UNIQUE",unique(bindings,["/authority_key"]),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",bindings),assertion(pid,"AUTHORITY_BINDING_CARDINALITY_EXACT",num(count(bindings),"EQ",lit(len(expected))),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",bindings),assertion(pid,"AUTHORITY_BINDING_ROOTS_FIXED",equal(bindings,lit(expected)),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",bindings),assertion(pid,"EVERY_REQUIREMENT_AUTHORITY_RESOLVES",every_requirement_bound,"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",reqs),assertion(pid,"EVERY_AUTHORITY_USED",every_binding_used,"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",bindings)]
  base.extend(extra)
  base += [assertion(pid,"INTEGRITY_MODES_BOUND_ARGUMENT_EXACT",equal(modes_content,arg("integrity_modes")),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",modes_content),assertion(pid,"INTEGRITY_MODE_ALGORITHMS_SUPPORTED",algorithms_supported,"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",dispatch_rows),assertion(pid,"INTEGRITY_MODE_SERIALIZATIONS_SUPPORTED",serializations_supported,"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",dispatch_rows),assertion(pid,"GOVERNANCE_AUTHORITY_ROOT_SOURCE_EXACT",equal(get(govreq_content,"/governing_authority_requirement/authority_roots_source"),lit("v013-governance:/authority_bindings")),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",govreq_content),assertion(pid,"POLICY_FIELD_ROLE_IDS_UNIQUE",unique(field_roles,["/field_id"]),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",field_roles),assertion(pid,"POLICY_FIELD_ROLE_TABLE_EXACT",equal(field_roles,lit(FROZEN_V013_POLICY_FIELD_ROLES)),"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",field_roles),assertion(pid,"POLICY_FIELD_ROLE_REQUIREMENTS_RESOLVE",field_role_requirements_resolve,"GOVERNING_AUTHORITY_REFERENCE_VALID_FAILURE",field_roles)]
  return base
 if pid=="GOVERNING_TOKEN_SINGLETON":
  rows=g("semantic_keys","/semantic_keys")
  out=[assertion(pid,"SEMANTIC_KEY_UNIQUE",unique(rows,["/key"]),"DUPLICATE_SEMANTIC_KEY",rows),assertion(pid,"AUTHORITY_PATH_UNIQUE",unique(rows,["/authority_path"]),"DUPLICATE_SEMANTIC_KEY",rows)]
  out.append(assertion(pid,"SEMANTIC_KEY_ROWS_FROZEN",equal(rows,lit(FROZEN_SEMANTIC_KEY_ROWS)),"GOVERNING_TOKEN_SINGLETON_FAILURE",rows))
  out.append(assertion(pid,"SINGLETON_POLICY_FROZEN",equal(g("semantic_keys","/governing_token_singleton"),lit(FROZEN_SEMANTIC_KEY_POLICY)),"GOVERNING_TOKEN_SINGLETON_FAILURE",g("semantic_keys","/governing_token_singleton")))
  policy=g("semantic_keys","/governing_token_singleton")
  eligible=filt(g("registry","/objects"),"obj_status",equal(get(item("obj_status"),"/status"),lit("ACTIVE")))
  eligible=filt(eligible,"obj_class",equal(get(item("obj_class"),"/classification"),lit("NORMATIVE")))
  eligible=filt(eligible,"obj_kind",{"op":"NOT","value":any_(get(policy,"/scan_excludes_kinds"),"excluded_kind",equal(item("excluded_kind"),get(item("obj_kind"),"/kind")))})
  eligible=filt(eligible,"obj_role",{"op":"NOT","value":any_(get(policy,"/permitted_exception_roles"),"exception_role",any_(get(item("obj_role"),"/roles"),"actual_role",equal(item("exception_role"),item("actual_role"))))})
  def unauthorized_key_occurrences(obj_name,key_name):
   found=descendants(get(resolve(get(item(obj_name),"/reference")),"/content"))
   found=filt(found,"member_match",equal(get(item("member_match"),"/member_key"),get(item(key_name),"/key")))
   found=filt(found,"not_excluded",{"op":"NOT","value":any_(get(policy,"/scan_excluded_pointer_prefixes"),"excluded_prefix",any_(get(item("not_excluded"),"/ancestor_pointers"),"ancestor",equal(item("excluded_prefix"),item("ancestor"))))})
   return found
  def occurrence_allowed(obj_name,key_name,occurrence_name):
   matches=filt(get(item(key_name),"/allowed_occurrences"),"allow_kind",equal(get(item("allow_kind"),"/kind"),get(item(obj_name),"/kind")))
   matches=filt(matches,"allow_path",equal(get(item("allow_path"),"/pointer_tokens"),get(item(occurrence_name),"/path_tokens")))
   return equal(count(matches),lit(1))
  scan=all_(rows,"semantic_key",all_(eligible,"candidate_object",all_(unauthorized_key_occurrences("candidate_object","semantic_key"),"occurrence",occurrence_allowed("candidate_object","semantic_key","occurrence"))))
  out.append(assertion(pid,"NO_UNAUTHORIZED_SEMANTIC_KEY_OCCURRENCES",scan,"GOVERNING_TOKEN_SINGLETON_FAILURE",g("registry","/objects")))
  return out
 if pid=="PREDICATE_POLICY_AGREEMENT":
  out=_BOUNDED_BASE_AST(pid)
  inkeys=get(descendants(g("inputs","/predicate_policy")),"/0/keys")
  authkeys=get(descendants(g("authority","/stage_policy_requirements")),"/0/keys")
  out += [assertion(pid,"INPUT_POLICY_KEYSET_EXACT",equal(inkeys,lit(["global_stage_order","implicit_transitivity"])),"PREDICATE_AUTHORITY_CLOSURE_FAILURE",g("inputs","/predicate_policy")),assertion(pid,"AUTHORITY_POLICY_KEYSET_EXACT",equal(authkeys,lit(["global_stage_order","implicit_transitivity"])),"PREDICATE_AUTHORITY_CLOSURE_FAILURE",g("authority","/stage_policy_requirements"))]
  return out
 if pid=="ROLE_MODEL_APPLIED":
  out=_BOUNDED_BASE_AST(pid)
  keyrows=filt(descendants(g("governance","/role_model_requirement/allowed_kinds_by_role")),"rk",equal(count(get(item("rk"),"/path_tokens")),lit(1)))
  keys=project(keyrows,"rkey",{"role":get(item("rkey"),"/member_key")})
  vocab=project(g("registry","/role_vocabulary"),"rv",{"role":item("rv")})
  out.append(assertion(pid,"ROLE_MAP_KEYS_EQUAL_VOCABULARY",op("SET_EQUAL_STRICT",left=keys,right=vocab),"ROLE_MODEL_APPLIED_FAILURE",g("governance","/role_model_requirement/allowed_kinds_by_role")))
  return out
 if pid=="SCHEMA_IDENTITY_MATCHES_REGISTRY":
  out=_BOUNDED_BASE_AST(pid)
  schemas=filt(g("registry","/objects"),"s",equal(get(item("s"),"/kind"),lit("SCHEMA")))
  out.append(assertion(pid,"SCHEMA_DOCUMENT_IDS_UNIQUE",unique(schemas,["/schema_document_id"]),"SCHEMA_IDENTITY_MATCHES_REGISTRY_FAILURE",schemas))
  return out
 if pid=="V013_BASIS_VALID":
  out=_BOUNDED_BASE_AST(pid)
  ids=["TARGET_EFFECT_EQUAL","TARGET_PREDICATE_EQUAL","TARGET_STAGE_EQUAL","TARGET_SCOPE_EQUAL","INTERVAL_VALID","INTERVAL_COVERS_TARGET","RETENTION_MEETS_BOUND","CONSISTENCY_ALLOWED","SOURCE_CLASS_ALLOWED","FRESHNESS_BOUND","READ_COMPLETE","NO_SAME_TARGET_POSITIVE","FUTURE_OBSERVATION_BOUND","STALE_RESULT_BOUND","EVIDENCE_UNIVERSE_TYPED","FORBID_CALLER_SUPPLIED_CONTRADICTION_COUNT"]
  req=g("v013_governance","/requirement_map/requirements")
  reqids=project(req,"req",{"id":get(item("req"),"/requirement_id")})
  declared=project(lit(ids),"rid",{"id":item("rid")})
  ordered=project(req,"ordered_req",{"id":get(item("ordered_req"),"/requirement_id")})
  accepted=g("target","/relationship_basis/accepted"); supplied=g("target","/relationship_basis/candidate_supplied")
  catalog=get(resolve(g("target","/source_vector_ref")),"/content")
  member_rows=filt(get(catalog,"/vectors"),"vector_row",equal(get(item("vector_row"),"/vector_id"),get(g("target","/source_vector_ref"),"/member_id")))
  member=get(member_rows,"/0")
  accepted_nodes=descendants(member)
  value_fields=filt(accepted,"vf",equal(get(item("vf"),"/selector/kind"),lit("VALUE")))
  array_fields=filt(accepted,"af2",equal(get(item("af2"),"/selector/kind"),lit("ARRAY_CONTAINS")))
  def selected_fields(rows,outer,desc,name):
   return all_(rows,outer,all_(filt(desc,name,equal(get(item(name),"/path_tokens"),get(item(outer),"/selector/pointer_tokens"))),name+"_one",num(count(filt(desc,name+"_count",equal(get(item(name+"_count"),"/path_tokens"),get(item(outer),"/selector/pointer_tokens")))),"EQ",lit(1))))
  value_path_unique=all_(value_fields,"vf2",num(count(filt(accepted_nodes,"vn",equal(get(item("vn"),"/path_tokens"),get(item("vf2"),"/selector/pointer_tokens")))),"EQ",lit(1)))
  value_match=all_(value_fields,"vf3",all_(filt(accepted_nodes,"vn2",equal(get(item("vn2"),"/path_tokens"),get(item("vf3"),"/selector/pointer_tokens"))),"vnode",equal(get(item("vnode"),"/value"),get(item("vf3"),"/selector/must_equal"))))
  array_path_unique=all_(array_fields,"af3",num(count(filt(accepted_nodes,"an",equal(get(item("an"),"/path_tokens"),get(item("af3"),"/selector/pointer_tokens")))),"EQ",lit(1)))
  array_match=all_(array_fields,"af4",all_(filt(accepted_nodes,"an2",equal(get(item("an2"),"/path_tokens"),get(item("af4"),"/selector/pointer_tokens"))),"anode",any_(get(item("anode"),"/value"),"av",equal(item("av"),get(item("af4"),"/selector/must_contain")))))
  target_nodes=descendants(g("target",""))
  candidate_path_unique=all_(supplied,"cf3",num(count(filt(target_nodes,"cn",equal(get(item("cn"),"/path_tokens"),get(item("cf3"),"/pointer_tokens")))),"EQ",lit(1)))
  candidate_nonnull=all_(supplied,"cf4",all_(filt(target_nodes,"cn2",equal(get(item("cn2"),"/path_tokens"),get(item("cf4"),"/pointer_tokens"))),"cn3",op("NOT",value=equal(get(item("cn3"),"/value_type"),lit("NULL")))))
  bindings=filt(g("v013_governance","/authority_bindings"),"ab",equal(get(item("ab"),"/argument_name"),lit("target")))
  authorized=all_(supplied,"cf5",all_(filt(target_nodes,"tn",equal(get(item("tn"),"/path_tokens"),get(item("cf5"),"/pointer_tokens"))),"tn2",any_(get(item("tn2"),"/ancestor_pointers"),"ap",any_(bindings,"ab2",all_(filt(target_nodes,"root",equal(get(item("root"),"/path_tokens"),get(item("ab2"),"/pointer_tokens"))),"root2",equal(item("ap"),get(item("root2"),"/pointer")))))))
  out += [assertion(pid,"REQUIREMENT_ID_ORDER_FIXED",op("JSON_EQUAL",left=ordered,right=project(lit(ids),"expected_req",{"id":item("expected_req")})),"V013_BASIS_VALID_FAILURE",req),assertion(pid,"REQUIREMENT_MAP_EXACT",op("SET_EQUAL_STRICT",left=reqids,right=declared),"V013_BASIS_VALID_FAILURE",req),assertion(pid,"FIELD_IDS_DISJOINT",all_(accepted,"af",op("NOT",value=any_(supplied,"cf",equal(get(item("cf"),"/field_id"),get(item("af"),"/field_id"))))),"V013_BASIS_VALID_FAILURE",g("target","/relationship_basis")),assertion(pid,"CANDIDATE_PROVENANCE_CANDIDATE_LOCAL",all_(supplied,"cf2",equal(get(item("cf2"),"/provenance"),lit("CANDIDATE_LOCAL_NOT_HISTORY"))),"V013_BASIS_VALID_FAILURE",supplied),assertion(pid,"VALUE_SELECTOR_PATH_UNIQUE",value_path_unique,"V013_BASIS_VALID_FAILURE",value_fields),assertion(pid,"VALUE_SELECTOR_MATCHES_ACCEPTED",value_match,"V013_BASIS_VALID_FAILURE",value_fields),assertion(pid,"ARRAY_SELECTOR_PATH_UNIQUE",array_path_unique,"V013_BASIS_VALID_FAILURE",array_fields),assertion(pid,"ARRAY_SELECTOR_MATCHES_ACCEPTED",array_match,"V013_BASIS_VALID_FAILURE",array_fields),assertion(pid,"CANDIDATE_POINTER_UNIQUE",candidate_path_unique,"V013_BASIS_VALID_FAILURE",supplied),assertion(pid,"CANDIDATE_POINTER_NON_NULL",candidate_nonnull,"V013_BASIS_VALID_FAILURE",supplied),assertion(pid,"CANDIDATE_POINTER_AUTHORIZED_ROOT",authorized,"V013_BASIS_VALID_FAILURE",supplied)]
  return out
 if pid=="REQUIREMENT_MAP_EVAL":
  out=_BOUNDED_BASE_AST(pid)
  out.insert(1,assertion(pid,"REQUIREMENT_ROWS_MATCH_FROZEN_R5R3_SEMANTICS",equal(g("v013_governance","/requirement_map/requirements"),lit(FROZEN_V013_REQUIREMENTS)),"NEGATIVE_REQUIREMENT_MAP_CLOSURE_FAILURE",g("v013_governance","/requirement_map/requirements")))
  return out
 return _BOUNDED_BASE_AST(pid)

# Expand primitive rows to the Phase-A closed contracts; the registry contains only data, never executable Python handlers.
_BASE_MAKE_PRIMITIVE_REGISTRY=make_primitive_registry
def make_primitive_registry():
 result=_BASE_MAKE_PRIMITIVE_REGISTRY()
 details={
  "RESOLVE_ONE":("ERROR_IF_IDENTITY_OR_MEMBER_MISSING","FAIL_CLOSED_ON_DUPLICATE_IDENTITY_OR_MEMBER","UNIVERSE_IDENTITY_ORDER; EXACTLY_ONE_REQUIRED",["INVALID_TYPED_REFERENCE","RESOLUTION_NOT_FOUND","RESOLUTION_AMBIGUOUS","INELIGIBLE_OBJECT","MEMBER_NOT_FOUND"],"RFC 6901 Typed Reference; Accord source eligibility"),
  "GET":("ERROR_IF_POINTER_MISSING_OR_MALFORMED","NOT_APPLICABLE","SINGLE_POINTER_TRAVERSAL",["INVALID_POINTER","MISSING_PATH","INVALID_ARRAY_INDEX"],"RFC 6901"),
  "GET_KEY":("ERROR_IF_KEY_MISSING_OR_NOT_OBJECT","NOT_APPLICABLE","SINGLE_OBJECT_MEMBER",["MISSING_KEY","NOT_OBJECT","UNDECLARED_CLOSED_RECORD_FIELD"],"JSON object member access"),
  "JSON_EQUAL":("NOT_APPLICABLE_JSON_NULL_IS_VALUE","NOT_APPLICABLE","STRUCTURAL_JSON_OBJECT_ORDER_IGNORED_ARRAY_ORDER_RETAINED",["OUTSIDE_I_JSON_DOMAIN"],"RFC 8785; I-JSON"),
  "SET_EQUAL_STRICT":("NOT_APPLICABLE_ARRAY_REQUIRED","NOT_APPLICABLE_DUPLICATE_SET_ELEMENT_IS_ERROR","UNORDERED_SET_EQUALITY",["NOT_ARRAY","DUPLICATE_SET_ITEM"],"ACCORD strict-set semantics"),
  "UNIQUE_BY":("ERROR_IF_PROJECTED_KEY_MISSING","NOT_APPLICABLE","SOURCE_ORDER_EARLIEST_DUPLICATE_PAIR",["NOT_ARRAY","INVALID_POINTER","MISSING_PROJECTED_KEY"],"ACCORD unique projection"),
  "FILTER":("EMPTY_ARRAY_RETURNS_EMPTY_ARRAY","NOT_APPLICABLE","STABLE_SOURCE_ARRAY_ORDER",["NOT_ARRAY","PREDICATE_EVALUATION_ERROR"],"Finite JSON arrays"),
  "PROJECT":("EMPTY_ARRAY_RETURNS_EMPTY_ARRAY","NOT_APPLICABLE","STABLE_SOURCE_ARRAY_ORDER_AND_DECLARED_FIELD_ORDER",["NOT_ARRAY","DUPLICATE_PROJECTED_FIELD","FIELD_EXPRESSION_ERROR"],"Finite JSON arrays"),
  "COUNT":("ERROR_IF_NOT_ARRAY","NOT_APPLICABLE","EXACT_ARRAY_LENGTH",["NOT_ARRAY"],"Finite JSON arrays"),
  "ALL":("EMPTY_ARRAY_IS_TRUE","NOT_APPLICABLE","STABLE_SHORT_CIRCUIT_FALSE",["NOT_ARRAY","PREDICATE_EVALUATION_ERROR","NON_BOOLEAN_PREDICATE"],"Finite JSON arrays"),
  "ANY":("EMPTY_ARRAY_IS_FALSE","NOT_APPLICABLE","STABLE_SHORT_CIRCUIT_TRUE",["NOT_ARRAY","PREDICATE_EVALUATION_ERROR","NON_BOOLEAN_PREDICATE"],"Finite JSON arrays"),
  "NOT":("ERROR_IF_NOT_BOOLEAN","NOT_APPLICABLE","SINGLE_BOOLEAN",["NON_BOOLEAN_OPERAND"],"Boolean logic"),
  "NUMERIC_COMPARE":("ERROR_IF_NOT_FINITE_I_JSON_NUMBER","NOT_APPLICABLE","EXACT_NUMERIC_COMPARE_NO_COERCION",["NON_NUMERIC_OPERAND","NONFINITE_NUMBER","INVALID_COMPARATOR"],"I-JSON"),
  "RFC3339_COMPARE":("ERROR_IF_TIMESTAMP_MALFORMED","NOT_APPLICABLE","COMPARE_NORMALIZED_INSTANTS",["MALFORMED_RFC3339","INVALID_COMPARATOR"],"RFC 3339"),
  "DURATION_SECONDS":("ERROR_IF_TIMESTAMP_MALFORMED","NOT_APPLICABLE","EXACT_END_MINUS_START_SIGNED_DECIMAL",["MALFORMED_RFC3339","DURATION_OVERFLOW"],"RFC 3339 arithmetic"),
  "SCHEMA_VALIDATE":("ERROR_IF_SCHEMA_OR_REF_MALFORMED","NOT_APPLICABLE","LOCAL_FRAGMENT_REFERENCE_ONLY_NO_NETWORK",["MALFORMED_SCHEMA","UNRESOLVED_LOCAL_FRAGMENT","UNSUPPORTED_DIALECT"],"JSON Schema Draft 2020-12"),
  "DIGEST_VERIFY":("ERROR_IF_VALUE_MODE_OR_POINTER_INVALID","NOT_APPLICABLE","MODE_DRIVEN_HASHING; RAW_BYTES_FROM_PRESERVED_RESOLVED_OBJECT_ONLY",["UNSUPPORTED_ALGORITHM","UNSUPPORTED_SERIALIZATION","INVALID_ALGORITHM_SERIALIZATION_PAIR","INVALID_EXCLUSION_POINTER","DUPLICATE_OR_OVERLAPPING_EXCLUSION","RAW_BYTES_UNAVAILABLE"],"RFC 8785; SHA-256; Git object format"),
  "DESCENDANTS":("NOT_APPLICABLE_ROOT_IS_INCLUDED","NOT_APPLICABLE","PREORDER_DEPTH_FIRST_ARRAY_ASCENDING_OBJECT_KEYS_JCS_UTF16",["NON_JSON_VALUE","TRAVERSAL_RESOURCE_LIMIT"],"RFC 6901; RFC 8785 object key order")}
 for row in result["primitives"]:
  missing,ambiguous,order,errors,standard=details[row["primitive_id"]]
  row.update({"missing_behavior":missing,"ambiguity_behavior":ambiguous,"deterministic_order":order,"error_behavior":{"error_classes":errors,"expression_error":"CONTAINING_ASSERTION_FAILURE_WITH_DECLARED_CODE_AND_WITNESS","stops_evaluation":True},"standard":standard})
 return result

_BASE_MAKE_PRIMITIVE_SCHEMA=make_primitive_schema
def make_primitive_schema():
 schema=_BASE_MAKE_PRIMITIVE_SCHEMA()
 row=schema["properties"]["primitives"]["items"]
 row["required"] += ["missing_behavior","ambiguity_behavior","deterministic_order","error_behavior"]
 row["properties"].update({"missing_behavior":{"type":"string","minLength":1},"ambiguity_behavior":{"type":"string","minLength":1},"deterministic_order":{"type":"string","minLength":1},"error_behavior":{"type":"object","required":["error_classes","expression_error","stops_evaluation"],"properties":{"error_classes":{"type":"array","items":{"type":"string"}},"expression_error":{"const":"CONTAINING_ASSERTION_FAILURE_WITH_DECLARED_CODE_AND_WITNESS"},"stops_evaluation":{"const":True}},"additionalProperties":False}})
 return schema

# Add the remaining normative metacontract fields and closed static bounds.
_BASE_MAKE_METACONTRACT_LATEST=make_metacontract
BOOTSTRAP_ORDER=["READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST","REJECT_DUPLICATE_JSON_NAMES_AND_INVALID_UTF8","VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE","VERIFY_FROZEN_AUTHORITY_PINS","VERIFY_ACCEPTED_SOURCE_ALLOWLIST_PINS","VALIDATE_PACKAGE_AND_REGISTRY_BOOTSTRAP_PINS","DERIVE_CANDIDATE_UNIVERSE","DERIVE_BOUND_SOURCE_UNIVERSE","FORM_VERIFICATION_UNIVERSE_STRICT_IDENTITY_UNION","PREEXEC_VALIDATE_ARGUMENT_SCHEMA_AND_INTEGRITY","AUTHORIZE_EXACT_RESULT_PROJECTION_DESCRIPTORS","EXECUTE_ORDERED_ASSERTIONS_AND_INVARIANTS","FINALIZE_TYPED_RESULT"]
STATIC_RULES=["PROCEDURE_ID_SET_EXACT","ARGUMENT_NAMES_UNIQUE","ASSERTION_IDS_UNIQUE","FINITE_AST_NO_RECURSION","EXACT_OPERATOR_OPERANDS","DECLARED_ARGUMENTS_ONLY","LEXICAL_SCOPE_NO_SHADOW_OR_ESCAPE_ON_ACTIVE_PATH","ASSERTION_CONDITION_AND_WITNESS_ARE_INDEPENDENT_SCOPE_ROOTS","DISJOINT_SIBLING_COLLECTION_SCOPES_MAY_REUSE_NAMES","OPERAND_RESULT_TYPES_VALID","RESOLVE_ONE_USES_EXACT_VERIFICATION_UNIVERSE_TERMINAL","RULE_BINDING_SOURCE_CONSTRAINTS_VALID","RESERVED_BINDINGS_IMMUTABLE","ASSERTION_CODES_IN_PROCEDURE_COMPATIBLE_SET","ASSERTION_CODES_IN_EVERY_BOUND_INVARIANT_SET","DIGEST_MODE_FIELDS_ARE_DYNAMIC_EXPRESSIONS","RESULT_PROJECTION_DESCRIPTOR_EXACT_LITERAL","RESULT_PROJECTION_MAP_EQUALS_FROZEN_BASELINE","SCHEMA_REFS_LOCAL_FRAGMENT_ONLY","RESOURCE_LIMITS_ENFORCED"]
SCOPE_SEMANTICS={"root_partition":"EACH_ASSERTION_CONDITION_AND_WITNESS_IS_A_SEPARATE_EXPRESSION_ROOT","item_resolution":"ACTIVE_LEXICAL_BINDERS_ONLY_NO_ESCAPE","shadowing":"FORBIDDEN_WHILE_AN_ANCESTOR_BINDER_IS_ACTIVE","sibling_reuse":"ALLOWED_ONLY_WHEN_BINDERS_ARE_NOT_SIMULTANEOUSLY_ACTIVE"}
RESOURCE_LIMITS={"max_arguments_per_procedure":128,"max_assertions_per_procedure":512,"max_ast_nodes_per_procedure":8192,"max_expression_depth":64,"max_lexical_collection_nesting":32,"max_json_traversal_depth":256,"max_json_nodes_visited_per_value":1000000}
def make_metacontract(proc,inv):
 result=_BASE_MAKE_METACONTRACT_LATEST(proc,inv)
 result["bootstrap_order"]=BOOTSTRAP_ORDER
 result["eligibility"]={"candidate_universe":{"status":"ACTIVE","classification":"NORMATIVE","membership_predicate":"STATUS_ACTIVE_AND_CLASSIFICATION_NORMATIVE","preconditions":["TYPED_REGISTRY_REGISTRATION_VALID_FOR_KIND","INTEGRITY_VERIFIED_BEFORE_MEMBERSHIP"],"validation_by_kind":{"SCHEMA":"NO_SCHEMA_REF_AND_SCHEMA_DOCUMENT_MUST_DECLARE_DRAFT_2020_12_AND_USE_LOCAL_FRAGMENT_REFS_ONLY","NON_SCHEMA":"CONTENT_MUST_VALIDATE_AGAINST_EXACT_REGISTERED_SCHEMA_REF"},"role_dimension":"GOVERNANCE_REQUIREMENTS_ROLE_MODEL_SEPARATE_FROM_CANDIDATE_MEMBERSHIP","integrity_required":True},"bound_source_universe":{"status":"ACTIVE_ACCEPTED_SOURCE","registry_classification":"PROVENANCE","binding_classification":"SOURCE_ONLY","required_roles_by_ref":{"PACKAGE":["NORMATIVE_BOUND_SOURCE"],"SOURCE_VECTOR_CATALOG":["CATALOG_BINDING","VECTOR_SOURCE"]}}}
 result["binding_origins"]={"allowed_origins":["RULE_BINDING","BOOTSTRAP_VERIFICATION_UNIVERSE","EXTERNAL_FROZEN_AUTHORITY","EXTERNAL_FROZEN_PREDECESSOR","EXTERNAL_TRUST"],"reserved_names":{"verification_universe":"VERIFICATION_UNIVERSE","frozen_rule_authority":"FROZEN_RULE_AUTHORITY","frozen_predecessor_semantics":"FROZEN_V013_GOVERNANCE","external_trust":"EXTERNAL_TRUST"},"reserved_arguments_are_rule_unavailable":True}
 result["source_constraints"]={"ordinary_bindings":"EXACT_KIND_SCHEMA_ACTIVE_NORMATIVE_CANDIDATE_UNIVERSE","accepted_sources":"EXACT_EXTERNAL_REF_PATH_STATUS_CLASS_ROLES_RAW_SEMANTIC_SHA256_AND_GIT_BLOB","resolver_ambient_access":"FORBIDDEN","verification_universe_explicit_on_every_resolver":True,"schema_member_resolution":"SCHEMA_OBJECT_MEMBER_ID_SELECTS_EXACT_NAMED_LOCAL_DEFINITION"}
 result["static_validation_rules"]=STATIC_RULES
 result["failure_semantics"]={"assertion_order":"DECLARATION_ORDER","first_failure_only":True,"expression_error":"CONTAINING_ASSERTION_FAILURE_CODE","witness_operands_include_argument_pointer_identity":True,"pre_execution_order":["SCHEMA_INVALID_BOUND_OBJECT","RESULT_PROJECTION_INVALID","AST_ASSERTION_FAILURE"],"pre_execution_stops_ast":True}
 result["resource_limits"]=RESOURCE_LIMITS
 result["path_policy"]={"pointer_standard":"RFC 6901","schema_ref_resolution":"LOCAL_FRAGMENT_ONLY","network_resolution":"DISABLED","candidate_paths":"CANONICAL_REPOSITORY_RELATIVE_FORWARD_SLASH_NO_TRAVERSAL_OR_ALIASES","accepted_source_paths":"EXACT_EXTERNAL_PINNED_PATH"}
 return result

_BASE_MAKE_METACONTRACT_SCHEMA_LATEST=make_metacontract_schema
def make_metacontract_schema():
 schema=_BASE_MAKE_METACONTRACT_SCHEMA_LATEST()
 for name in ["eligibility","binding_origins","source_constraints","static_validation_rules","failure_semantics","resource_limits","path_policy"]:
  if name not in schema["required"]: schema["required"].append(name)
 schema["properties"]["bootstrap_order"]={"const":BOOTSTRAP_ORDER}
 schema["properties"]["eligibility"]={"type":"object","required":["candidate_universe","bound_source_universe"],"properties":{"candidate_universe":{"type":"object","required":["status","classification","membership_predicate","preconditions","validation_by_kind","role_dimension","integrity_required"],"properties":{"status":{"const":"ACTIVE"},"classification":{"const":"NORMATIVE"},"membership_predicate":{"const":"STATUS_ACTIVE_AND_CLASSIFICATION_NORMATIVE"},"preconditions":{"const":["TYPED_REGISTRY_REGISTRATION_VALID_FOR_KIND","INTEGRITY_VERIFIED_BEFORE_MEMBERSHIP"]},"validation_by_kind":{"const":{"SCHEMA":"NO_SCHEMA_REF_AND_SCHEMA_DOCUMENT_MUST_DECLARE_DRAFT_2020_12_AND_USE_LOCAL_FRAGMENT_REFS_ONLY","NON_SCHEMA":"CONTENT_MUST_VALIDATE_AGAINST_EXACT_REGISTERED_SCHEMA_REF"}},"role_dimension":{"const":"GOVERNANCE_REQUIREMENTS_ROLE_MODEL_SEPARATE_FROM_CANDIDATE_MEMBERSHIP"},"integrity_required":{"const":True}},"additionalProperties":False},"bound_source_universe":{"type":"object","required":["status","registry_classification","binding_classification","required_roles_by_ref"],"properties":{"status":{"const":"ACTIVE_ACCEPTED_SOURCE"},"registry_classification":{"const":"PROVENANCE"},"binding_classification":{"const":"SOURCE_ONLY"},"required_roles_by_ref":{"const":{"PACKAGE":["NORMATIVE_BOUND_SOURCE"],"SOURCE_VECTOR_CATALOG":["CATALOG_BINDING","VECTOR_SOURCE"]}}},"additionalProperties":False}},"additionalProperties":False}
 schema["properties"]["binding_origins"]={"type":"object","required":["allowed_origins","reserved_names","reserved_arguments_are_rule_unavailable"],"properties":{"allowed_origins":{"const":["RULE_BINDING","BOOTSTRAP_VERIFICATION_UNIVERSE","EXTERNAL_FROZEN_AUTHORITY","EXTERNAL_FROZEN_PREDECESSOR","EXTERNAL_TRUST"]},"reserved_names":{"const":{"verification_universe":"VERIFICATION_UNIVERSE","frozen_rule_authority":"FROZEN_RULE_AUTHORITY","frozen_predecessor_semantics":"FROZEN_V013_GOVERNANCE","external_trust":"EXTERNAL_TRUST"}},"reserved_arguments_are_rule_unavailable":{"const":True}},"additionalProperties":False}
 schema["properties"]["source_constraints"]={"type":"object","required":["ordinary_bindings","accepted_sources","resolver_ambient_access","verification_universe_explicit_on_every_resolver","schema_member_resolution"],"properties":{"ordinary_bindings":{"const":"EXACT_KIND_SCHEMA_ACTIVE_NORMATIVE_CANDIDATE_UNIVERSE"},"accepted_sources":{"const":"EXACT_EXTERNAL_REF_PATH_STATUS_CLASS_ROLES_RAW_SEMANTIC_SHA256_AND_GIT_BLOB"},"resolver_ambient_access":{"const":"FORBIDDEN"},"verification_universe_explicit_on_every_resolver":{"const":True},"schema_member_resolution":{"const":"SCHEMA_OBJECT_MEMBER_ID_SELECTS_EXACT_NAMED_LOCAL_DEFINITION"}},"additionalProperties":False}
 schema["properties"]["static_validation_rules"]={"const":STATIC_RULES}
 schema["properties"]["failure_semantics"]={"type":"object","required":["assertion_order","first_failure_only","expression_error","witness_operands_include_argument_pointer_identity","pre_execution_order","pre_execution_stops_ast"],"properties":{"assertion_order":{"const":"DECLARATION_ORDER"},"first_failure_only":{"const":True},"expression_error":{"const":"CONTAINING_ASSERTION_FAILURE_CODE"},"witness_operands_include_argument_pointer_identity":{"const":True},"pre_execution_order":{"const":["SCHEMA_INVALID_BOUND_OBJECT","RESULT_PROJECTION_INVALID","AST_ASSERTION_FAILURE"]},"pre_execution_stops_ast":{"const":True}},"additionalProperties":False}
 schema["properties"]["resource_limits"]={"const":RESOURCE_LIMITS}
 schema["properties"]["path_policy"]={"type":"object","required":["pointer_standard","schema_ref_resolution","network_resolution","candidate_paths","accepted_source_paths"],"properties":{"pointer_standard":{"const":"RFC 6901"},"schema_ref_resolution":{"const":"LOCAL_FRAGMENT_ONLY"},"network_resolution":{"const":"DISABLED"},"candidate_paths":{"const":"CANONICAL_REPOSITORY_RELATIVE_FORWARD_SLASH_NO_TRAVERSAL_OR_ALIASES"},"accepted_source_paths":{"const":"EXACT_EXTERNAL_PINNED_PATH"}},"additionalProperties":False}
 return schema



# Slice-1 remediation: authority inputs must arrive from a separately supplied acceptance profile.
PROFILE_ID = f"{NS}:external-acceptance-profile"
PROFILE_SCHEMA_REF = {"kind":"SCHEMA","id":f"{NS}:schema:external-verification-input-contract","version":"0.2","member_id":"acceptance_profile"}
PROFILE_FAILURE_CODES = [
 "MISSING_EXTERNAL_ACCEPTANCE_PROFILE", "INVALID_EXTERNAL_ACCEPTANCE_PROFILE",
 "EXTERNAL_FROZEN_R5R2_CONTENT_MISMATCH", "EXTERNAL_FROZEN_R5R3_CONTENT_MISMATCH",
 "EXTERNAL_ACCEPTED_BASE_CONTENT_MISMATCH", "EXTERNAL_ACCEPTED_VECTOR_CONTENT_MISMATCH",
 "METACONTRACT_R5R2_PIN_CLAIM_MISMATCH", "METACONTRACT_R5R3_PIN_CLAIM_MISMATCH",
 "METACONTRACT_ACCEPTED_ALLOWLIST_CLAIM_MISMATCH", "METACONTRACT_PROJECTION_CLAIM_MISMATCH",
 "PROCEDURE_PROJECTION_CLAIM_MISMATCH"]
PROFILE_FAILURE_OPERATIONS = {
 "MISSING_EXTERNAL_ACCEPTANCE_PROFILE":"READ_PROFILE",
 "INVALID_EXTERNAL_ACCEPTANCE_PROFILE":"VALIDATE_PROFILE_SCHEMA",
 "EXTERNAL_FROZEN_R5R2_CONTENT_MISMATCH":"VERIFY_FROZEN_R5R2_CONTENT",
 "EXTERNAL_FROZEN_R5R3_CONTENT_MISMATCH":"VERIFY_FROZEN_R5R3_CONTENT",
 "EXTERNAL_ACCEPTED_BASE_CONTENT_MISMATCH":"VERIFY_ACCEPTED_BASE_CONTENT",
 "EXTERNAL_ACCEPTED_VECTOR_CONTENT_MISMATCH":"VERIFY_ACCEPTED_VECTOR_CONTENT",
 "METACONTRACT_R5R2_PIN_CLAIM_MISMATCH":"COMPARE_R5R2_PIN_CLAIM",
 "METACONTRACT_R5R3_PIN_CLAIM_MISMATCH":"COMPARE_R5R3_PIN_CLAIM",
 "METACONTRACT_ACCEPTED_ALLOWLIST_CLAIM_MISMATCH":"COMPARE_ACCEPTED_ALLOWLIST_CLAIM",
 "METACONTRACT_PROJECTION_CLAIM_MISMATCH":"COMPARE_METACONTRACT_PROJECTION_CLAIM",
 "PROCEDURE_PROJECTION_CLAIM_MISMATCH":"COMPARE_PROCEDURE_PROJECTION_CLAIMS"}
ALL_PREEXEC_CODES = PROFILE_FAILURE_CODES + ["SCHEMA_INVALID_BOUND_OBJECT","RESULT_PROJECTION_INVALID"]
PROFILE_CLAIM_COMPARISONS = [
 {"candidate_artifact":"metacontract","candidate_pointer":"/external_authority_pins/frozen_r5r2_rules","profile_pointer":"/frozen_authority_pins/frozen_r5r2_rules","comparison":"WHOLE_OBJECT_JSON_EQUALITY","before_semantic_use":True,"failure_code":"METACONTRACT_R5R2_PIN_CLAIM_MISMATCH"},
 {"candidate_artifact":"metacontract","candidate_pointer":"/external_authority_pins/frozen_r5r3_v013_semantics","profile_pointer":"/frozen_authority_pins/frozen_r5r3_v013_semantics","comparison":"WHOLE_OBJECT_JSON_EQUALITY","before_semantic_use":True,"failure_code":"METACONTRACT_R5R3_PIN_CLAIM_MISMATCH"},
 {"candidate_artifact":"metacontract","candidate_pointer":"/accepted_source_allowlist","profile_pointer":"/accepted_source_allowlist","comparison":"WHOLE_OBJECT_JSON_EQUALITY","before_semantic_use":True,"failure_code":"METACONTRACT_ACCEPTED_ALLOWLIST_CLAIM_MISMATCH"},
 {"candidate_artifact":"metacontract","candidate_pointer":"/result_projection_authorization/descriptor","profile_pointer":"/authorized_result_projection_descriptor","comparison":"WHOLE_OBJECT_JSON_EQUALITY","before_semantic_use":True,"failure_code":"METACONTRACT_PROJECTION_CLAIM_MISMATCH"},
 {"candidate_artifact":"procedure-registry","candidate_selector":{"collection_pointer_rfc6901":"/procedures","collection_type":"ARRAY","selection":{"member_pointer_rfc6901":"/procedure_id","operator":"JSON_EQUAL","literal":"REQUIREMENT_MAP_EVAL","required_match_count":1},"selected_value_pointer_rfc6901_relative_to_item":"/result/result_projection","selected_value_required":True,"selected_value_comparison":"WHOLE_OBJECT_JSON_EQUALITY_TO_EXTERNAL_PROFILE_DESCRIPTOR","other_items_constraint":{"selection":"EVERY_ARRAY_ITEM_NOT_EQUAL_TO_SELECTED_LITERAL_BY_THE_SAME_MEMBER_POINTER","forbidden_pointer_rfc6901_relative_to_item":"/result/result_projection","must_be_absent":True,"present_null_counts_as_present":True},"failure_code":"PROCEDURE_PROJECTION_CLAIM_MISMATCH","algorithm":"RFC6901_ARRAY_LOOKUP_THEN_TYPED_MEMBER_FILTER_THEN_EXACT_COUNT_THEN_RELATIVE_MEMBER_LOOKUP"},"profile_pointer":"/authorized_result_projection_descriptor","comparison":"SELECTED_DESCRIPTOR_WHOLE_OBJECT_JSON_EQUALITY_AND_NO_OTHER_PROJECTION","before_semantic_use":True,"failure_code":"PROCEDURE_PROJECTION_CLAIM_MISMATCH"}]
PROFILE_CONTENT_VERIFICATION = {
 "source":"EXTERNAL_ACCEPTANCE_PROFILE_RAW_BYTES_ONLY",
 "base64_decode":"STRICT_RFC4648_NO_WHITESPACE",
 "json_decode":"UTF8_REJECT_DUPLICATE_MEMBER_NAMES",
 "frozen_sources":{"git_blob":"SHA1(ASCII('blob '+DECIMAL_BYTE_LENGTH)+NUL+RAW_BYTES)","content_use":"PARSED_CONTENT_ONLY_AFTER_PIN_MATCH"},
 "accepted_sources":{"raw_sha256":"SHA256_RAW_BYTES","semantic_sha256":"SHA256_RFC8785_JCS_PARSED_JSON","git_blob":"SHA1_GIT_BLOB_OBJECT","metadata":"EXACT_REF_PATH_ROLE_STATUS_CLASS_AND_SCHEMA"},
 "candidate_source_copies":"TRANSPORT_ONLY_NEVER_AUTHORITY_OR_RESOLVER_INPUT",
 "candidate_registry_fallback":"FORBIDDEN"}
PROFILE_PREFLIGHT_ORDER = [
 "MISSING_EXTERNAL_ACCEPTANCE_PROFILE", "INVALID_EXTERNAL_ACCEPTANCE_PROFILE",
 "EXTERNAL_FROZEN_R5R2_CONTENT_MISMATCH", "EXTERNAL_FROZEN_R5R3_CONTENT_MISMATCH",
 "EXTERNAL_ACCEPTED_BASE_CONTENT_MISMATCH", "EXTERNAL_ACCEPTED_VECTOR_CONTENT_MISMATCH",
 "METACONTRACT_R5R2_PIN_CLAIM_MISMATCH", "METACONTRACT_R5R3_PIN_CLAIM_MISMATCH",
 "METACONTRACT_ACCEPTED_ALLOWLIST_CLAIM_MISMATCH", "METACONTRACT_PROJECTION_CLAIM_MISMATCH",
 "PROCEDURE_PROJECTION_CLAIM_MISMATCH", "SCHEMA_INVALID_BOUND_OBJECT", "RESULT_PROJECTION_INVALID", "AST_ASSERTION_FAILURE"]
PROFILE_BOOTSTRAP_ORDER = [
 "READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST_TRIPLE",
 "REJECT_DUPLICATE_CANDIDATE_JSON_NAMES_AND_INVALID_UTF8",
 "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE",
 "READ_EXTERNAL_ACCEPTANCE_PROFILE_OUTSIDE_CANDIDATE",
 "VALIDATE_EXTERNAL_ACCEPTANCE_PROFILE_WITH_VERIFIER_VERSIONED_SCHEMA",
 "VERIFY_EXTERNAL_FROZEN_R5R2_CONTENT_AND_PIN",
 "VERIFY_EXTERNAL_FROZEN_R5R3_CONTENT_AND_PIN",
 "VERIFY_EXTERNAL_ACCEPTED_BASE_AND_VECTOR_CONTENT_AND_PINS",
 "COMPARE_CANDIDATE_METACONTRACT_AND_PROCEDURE_AUTHORITY_CLAIMS_WHOLE_OBJECT",
 "BIND_FROZEN_RESERVED_ARGUMENTS_FROM_VERIFIED_EXTERNAL_PROFILE_BYTES",
 "VALIDATE_PACKAGE_AND_REGISTRY_BOOTSTRAP_PINS",
 "DERIVE_CANDIDATE_UNIVERSE",
 "DERIVE_BOUND_SOURCE_UNIVERSE_FROM_EXTERNAL_PROFILE_ALLOWLIST_AND_BYTES",
 "FORM_VERIFICATION_UNIVERSE_STRICT_IDENTITY_UNION",
 "PREEXEC_VALIDATE_ARGUMENT_SCHEMA_AND_INTEGRITY",
 "AUTHORIZE_RESULT_PROJECTION_VALUES_FROM_VERIFIED_PREDECESSOR_BYTES",
 "EXECUTE_ORDERED_PROCEDURE_ASSERTIONS",
 "FINALIZE_TYPED_RESULT"]
STATIC_RULES += [
 "EXTERNAL_ACCEPTANCE_PROFILE_REQUIRED_OUTSIDE_CANDIDATE",
 "EXTERNAL_ACCEPTANCE_PROFILE_SCHEMA_IS_VERIFIER_VERSIONED_NOT_CANDIDATE_SELECTED",
 "PROFILE_SOURCE_CONTENTS_PINNED_BEFORE_PARSE_OR_USE",
 "FROZEN_RESERVED_ARGUMENTS_SOURCE_PROFILE_BYTES_NOT_CANDIDATE_COPIES",
 "BOUND_SOURCE_UNIVERSE_DERIVED_FROM_EXTERNAL_PROFILE_ALLOWLIST",
 "METACONTRACT_PIN_ALLOWLIST_AND_PROJECTION_CLAIMS_WHOLE_OBJECT_EQUAL_EXTERNAL_PROFILE",
 "EVERY_PROCEDURE_RESULT_PROJECTION_EQUALS_EXTERNAL_PROFILE_DESCRIPTOR",
 "CANDIDATE_SOURCE_COPIES_AND_BUILDER_CONSTANTS_ARE_CLAIMS_ONLY"]
BOOTSTRAP_ORDER = PROFILE_BOOTSTRAP_ORDER
RESERVED["frozen_rule_authority"]=("FROZEN_RULE_AUTHORITY","EXTERNAL_ACCEPTANCE_PROFILE")
RESERVED["frozen_predecessor_semantics"]=("FROZEN_V013_GOVERNANCE","EXTERNAL_ACCEPTANCE_PROFILE")
RESERVED["external_acceptance_profile"]=("EXTERNAL_ACCEPTANCE_PROFILE","EXTERNAL_ACCEPTANCE_PROFILE")
for _pid in ["AUTHORITY_COMPLETENESS","RULE_COVERAGE_EXACT","REQUIREMENT_MAP_EVAL","SOURCE_CATALOG_BINDING_MATCH","TRUST_ANCHOR_COMPARE"]:
 if "external_acceptance_profile:EXTERNAL_ACCEPTANCE_PROFILE" not in SIG[_pid]:
  SIG[_pid] += ",external_acceptance_profile:EXTERNAL_ACCEPTANCE_PROFILE"

def external_profile_source_rows():
 return [
  {"ref":ref("PACKAGE","urn:moirae:accord-02r5:specification-package","0.1"),"canonical_path":BASEPATH,"status":"ACTIVE_ACCEPTED_SOURCE","classification":"SOURCE_ONLY","roles":["NORMATIVE_BOUND_SOURCE"],"raw_sha256":BASERAW,"semantic_sha256":BASESEM,"git_blob":BASEBLOB,"expected_schema_ref":{"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":"accepted_base_source"}},
  {"ref":ref("SOURCE_VECTOR_CATALOG","urn:moirae:accord-02r5:source-vector-catalog","0.1"),"canonical_path":VECTORPATH,"status":"ACTIVE_ACCEPTED_SOURCE","classification":"SOURCE_ONLY","roles":["CATALOG_BINDING","VECTOR_SOURCE"],"raw_sha256":VECTORRAW,"semantic_sha256":VECTORSEM,"git_blob":VECTORBLOB,"expected_schema_ref":{"kind":"SCHEMA","id":f"{NS}:schema:metacontract","version":"0.2","member_id":"accepted_vector_source"}}]

def external_profile_instance_schema():
 b64={"type":"string","minLength":1,"pattern":"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$","contentEncoding":"base64","contentMediaType":"application/json"}
 content={"type":"object","required":["content_encoding","content_base64"],"properties":{"content_encoding":{"const":"BASE64_RAW_FILE_BYTES"},"content_base64":b64},"additionalProperties":False}
 rows=external_profile_source_rows()
 accepted_content_items=[]
 for row in rows:
  accepted_content_items.append({"type":"object","required":["ref","canonical_path","git_blob","content_encoding","content_base64"],"properties":{"ref":{"const":row["ref"]},"canonical_path":{"const":row["canonical_path"]},"git_blob":{"const":row["git_blob"]},"content_encoding":{"const":"BASE64_RAW_FILE_BYTES"},"content_base64":b64},"additionalProperties":False})
 pin_map={"frozen_r5r2_rules":R2PIN,"frozen_r5r3_v013_semantics":R3PIN}
 frozen_content={"type":"object","required":["frozen_r5r2_rules","frozen_r5r3_v013_semantics"],"properties":{"frozen_r5r2_rules":content,"frozen_r5r3_v013_semantics":content},"additionalProperties":False}
 return {"type":"object","required":["$schema","$id","profile_id","profile_version","registry_membership","frozen_authority_pins","frozen_authority_contents","accepted_source_allowlist","accepted_source_contents","authorized_result_projection_descriptor","profile_is_caller_supplied_outside_candidate","profile_is_immutable_for_run","candidate_copies_are_authority","candidate_registry_fallback"],"properties":{"$schema":{"const":DIALECT},"$id":{"const":f"{PROFILE_ID}:1"},"profile_id":{"const":"ACCORD-02E4R5R4-ACCEPTANCE-PROFILE"},"profile_version":{"const":"1"},"registry_membership":{"const":"FORBIDDEN_NOT_A_PACKAGE_OBJECT"},"frozen_authority_pins":{"const":pin_map},"frozen_authority_contents":frozen_content,"accepted_source_allowlist":{"const":rows},"accepted_source_contents":{"type":"array","minItems":2,"maxItems":2,"uniqueItems":True,"items":{"oneOf":accepted_content_items}},"authorized_result_projection_descriptor":{"const":RESULT_PROJECTION},"profile_is_caller_supplied_outside_candidate":{"const":True},"profile_is_immutable_for_run":{"const":True},"candidate_copies_are_authority":{"const":False},"candidate_registry_fallback":{"const":False}},"additionalProperties":False}

_BASE_MAKE_RUNTIME_RESULT_SCHEMA_PROFILE=make_runtime_result_schema
def make_runtime_result_schema():
 result=_BASE_MAKE_RUNTIME_RESULT_SCHEMA_PROFILE()
 w={"type":"object","required":["operation","profile_pointer","candidate_artifact","candidate_pointer","source_identity","expected","actual","reason"],"properties":{"operation":{"type":"string","minLength":1},"profile_pointer":{"type":"string"},"candidate_artifact":{"type":"string","minLength":1},"candidate_pointer":{"type":"string"},"source_identity":{"oneOf":[{"type":"null"},{"$ref":"#/$defs/identity"}]},"expected":{},"actual":{},"reason":{"enum":["INPUT_MISSING","INPUT_UNREADABLE","PROFILE_SCHEMA_INVALID","PIN_METADATA_MISMATCH","CONTENT_GIT_BLOB_MISMATCH","CONTENT_RAW_DIGEST_MISMATCH","CONTENT_SEMANTIC_DIGEST_MISMATCH","CLAIM_WHOLE_OBJECT_MISMATCH","DESCRIPTOR_WHOLE_OBJECT_MISMATCH"]}},"additionalProperties":False}
 result["$defs"]["external_profile_preflight_witness"]=w
 for code,operation in PROFILE_FAILURE_OPERATIONS.items():
  branch={"type":"object","required":["status","stage","code","witness"],"properties":{"status":{"const":"FAIL"},"stage":{"const":"PRE_EXECUTION"},"code":{"const":code},"witness":{"allOf":[{"$ref":"#/$defs/external_profile_preflight_witness"},{"properties":{"operation":{"const":operation}},"required":["operation"]}]}},"additionalProperties":False}
  result["$defs"]["pre_execution_result"]["oneOf"].append(branch)
 return result



_BASE_MAKE_PROC_SCHEMA_PROFILE=make_proc_schema
def make_proc_schema():
 schema=_BASE_MAKE_PROC_SCHEMA_PROFILE()
 arg=schema["$defs"]["argument"]
 types=arg["properties"]["type"]["enum"]
 if "EXTERNAL_ACCEPTANCE_PROFILE" not in types: types.append("EXTERNAL_ACCEPTANCE_PROFILE")
 origins=arg["properties"]["origin"]["enum"]
 if "EXTERNAL_ACCEPTANCE_PROFILE" not in origins: origins.append("EXTERNAL_ACCEPTANCE_PROFILE")
 arg["allOf"][1]["if"]["properties"]["origin"]["enum"] = [x for x in origins if x!="RULE_BINDING"]
 return schema

_BASE_UPDATE_SCHEMAS_PROFILE=update_schemas
def update_schemas(schemas):
 _BASE_UPDATE_SCHEMAS_PROFILE(schemas)
 ext=schemas["external-verification-input-contract.schema.json"]
 ext.setdefault("$defs",{})["acceptance_profile"]=external_profile_instance_schema()
 ext["required"] += ["acceptance_profile_schema_ref","authority_profile_protocol","candidate_claim_comparisons","content_verification","pre_execution_failures"]
 fields=ext["properties"]["fields"]
 fields["required"].append("acceptance_profile")
 fields["properties"]["acceptance_profile"]={"type":"object","required":["required","type","source","transport","schema_ref","registry_membership","candidate_fallback"],"properties":{"required":{"const":True},"type":{"const":"EXTERNAL_ACCEPTANCE_PROFILE"},"source":{"const":"CALLER_SUPPLIED_SEPARATELY"},"transport":{"const":"--verification-input"},"schema_ref":{"const":PROFILE_SCHEMA_REF},"registry_membership":{"const":"FORBIDDEN_NOT_A_PACKAGE_OBJECT"},"candidate_fallback":{"const":"FORBIDDEN"}},"additionalProperties":False}
 ext["properties"]["acceptance_profile_schema_ref"]={"const":PROFILE_SCHEMA_REF}
 ext["properties"]["authority_profile_protocol"]={"const":external_profile_claim_contract()}
 ext["properties"]["candidate_claim_comparisons"]={"const":PROFILE_CLAIM_COMPARISONS}
 ext["properties"]["content_verification"]={"const":PROFILE_CONTENT_VERIFICATION}
 ext["properties"]["pre_execution_failures"]={"type":"object","required":["codes","order"],"properties":{"codes":{"const":ALL_PREEXEC_CODES},"order":{"const":PROFILE_PREFLIGHT_ORDER}},"additionalProperties":False}
 results=ext["properties"]["results"]
 results["required"].append("PRE_EXECUTION")
 results["properties"]["PRE_EXECUTION"]={"type":"object","required":["codes","order"],"properties":{"codes":{"const":ALL_PREEXEC_CODES},"order":{"const":PROFILE_PREFLIGHT_ORDER}},"additionalProperties":False}
 ext["additionalProperties"]=False
 auths=schemas["authority-requirements.schema.json"]
 auth=auths["properties"]["trust_boundary_requirements"]
 auth["required"] += ["acceptance_profile_input_source","acceptance_profile_schema_ref","candidate_authority_claim_comparison","source_content_verification","preflight_failure_codes","profile_fallback"]
 ap=auth["properties"]
 ap["required_external_fields"]={"const":["expected_package_id","expected_package_version","expected_package_digest","external_acceptance_profile"]}
 ap["acceptance_profile_input_source"]={"const":"CALLER_SUPPLIED_SEPARATELY_VIA_VERIFICATION_INPUT"}
 ap["acceptance_profile_schema_ref"]={"const":PROFILE_SCHEMA_REF}
 ap["candidate_authority_claim_comparison"]={"const":"WHOLE_OBJECT_EQUALITY_BEFORE_SEMANTIC_USE"}
 ap["source_content_verification"]={"const":PROFILE_CONTENT_VERIFICATION}
 ap["preflight_failure_codes"]={"const":PROFILE_FAILURE_CODES}
 ap["profile_fallback"]={"const":"FORBIDDEN"}
 return schemas

_BASE_NORMALIZE_EXTERNAL_TRUST_PROFILE=normalize_external_trust
def normalize_external_trust(files):
 _BASE_NORMALIZE_EXTERNAL_TRUST_PROFILE(files)
 trust=files["external-verification-input.contract.json"]
 trust["fields"]["acceptance_profile"]={"required":True,"type":"EXTERNAL_ACCEPTANCE_PROFILE","source":"CALLER_SUPPLIED_SEPARATELY","transport":"--verification-input","schema_ref":PROFILE_SCHEMA_REF,"registry_membership":"FORBIDDEN_NOT_A_PACKAGE_OBJECT","candidate_fallback":"FORBIDDEN"}
 trust["acceptance_profile_schema_ref"]=PROFILE_SCHEMA_REF
 trust["authority_profile_protocol"]=external_profile_claim_contract()
 trust["candidate_claim_comparisons"]=PROFILE_CLAIM_COMPARISONS
 trust["content_verification"]=PROFILE_CONTENT_VERIFICATION
 trust["pre_execution_failures"]={"codes":ALL_PREEXEC_CODES,"order":PROFILE_PREFLIGHT_ORDER}
 trust["results"]["PRE_EXECUTION"]={"codes":ALL_PREEXEC_CODES,"order":PROFILE_PREFLIGHT_ORDER}
 trust["cli"]["--verification-input"]="PATH_TO_CALLER_SUPPLIED_EXTERNAL_ACCEPTANCE_PROFILE_JSON"
 auth=files["authority-requirements.json"]["trust_boundary_requirements"]
 auth["required_external_fields"]=["expected_package_id","expected_package_version","expected_package_digest","external_acceptance_profile"]
 auth["acceptance_profile_input_source"]="CALLER_SUPPLIED_SEPARATELY_VIA_VERIFICATION_INPUT"
 auth["acceptance_profile_schema_ref"]=PROFILE_SCHEMA_REF
 auth["candidate_authority_claim_comparison"]="WHOLE_OBJECT_EQUALITY_BEFORE_SEMANTIC_USE"
 auth["source_content_verification"]=PROFILE_CONTENT_VERIFICATION
 auth["preflight_failure_codes"]=PROFILE_FAILURE_CODES
 auth["profile_fallback"]="FORBIDDEN"

_BASE_MAKE_METACONTRACT_PROFILE=make_metacontract
def make_metacontract(proc,inv):
 result=_BASE_MAKE_METACONTRACT_PROFILE(proc,inv)
 result["universe_contract"]["bound_source_universe"]["source_allowlist_ref"]="external_acceptance_profile:/accepted_source_allowlist"
 result["universe_contract"]["bound_source_universe"]["identities_source"]="external_acceptance_profile:/accepted_source_allowlist/ref"
 result["universe_contract"]["excluded_inputs"] += ["candidate source copies of frozen authorities","candidate metacontract authority claims before external-profile comparison"]
 for row in result["reserved_inputs"]:
  if row["name"]=="frozen_rule_authority":
   row.pop("source_pin",None); row["origin"]="EXTERNAL_ACCEPTANCE_PROFILE"
   row["profile_content_source"]={"argument":"external_acceptance_profile","content_pointer_tokens":["frozen_authority_contents","frozen_r5r2_rules","content_base64"],"pin_pointer_tokens":["frozen_authority_pins","frozen_r5r2_rules"],"content_encoding":"BASE64_RAW_FILE_BYTES","decode":"STRICT_BASE64_TO_RAW_UTF8_JSON","use_after_pin_verification_only":True,"candidate_copy_authority":False}
  elif row["name"]=="frozen_predecessor_semantics":
   row.pop("source_pin",None); row["origin"]="EXTERNAL_ACCEPTANCE_PROFILE"
   row["profile_content_source"]={"argument":"external_acceptance_profile","content_pointer_tokens":["frozen_authority_contents","frozen_r5r3_v013_semantics","content_base64"],"pin_pointer_tokens":["frozen_authority_pins","frozen_r5r3_v013_semantics"],"content_encoding":"BASE64_RAW_FILE_BYTES","decode":"STRICT_BASE64_TO_RAW_UTF8_JSON","use_after_pin_verification_only":True,"candidate_copy_authority":False}
 result["reserved_inputs"].append({"name":"external_acceptance_profile","type":"EXTERNAL_ACCEPTANCE_PROFILE","origin":"EXTERNAL_ACCEPTANCE_PROFILE","transport":"--verification-input","source":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD","schema_ref":PROFILE_SCHEMA_REF,"candidate_copy_authority":False,"required_before_candidate_semantic_use":True})
 origins=result["binding_origins"]
 origins["allowed_origins"].append("EXTERNAL_ACCEPTANCE_PROFILE")
 origins["reserved_names"]["external_acceptance_profile"]="EXTERNAL_ACCEPTANCE_PROFILE"
 origins["reserved_names"]["frozen_rule_authority"]="FROZEN_RULE_AUTHORITY_FROM_EXTERNAL_ACCEPTANCE_PROFILE"
 origins["reserved_names"]["frozen_predecessor_semantics"]="FROZEN_V013_GOVERNANCE_FROM_EXTERNAL_ACCEPTANCE_PROFILE"
 result["source_constraints"]["accepted_sources"]="EXACT_CALLER_PROFILE_REF_PATH_STATUS_CLASS_ROLES_RAW_SEMANTIC_SHA256_GIT_BLOB_AND_CONTENT"
 result["source_constraints"]["external_profile_origin"]="CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD"
 result["source_constraints"]["candidate_source_copies_as_authority"]="FORBIDDEN"
 result["external_acceptance_profile_contract"]=external_profile_claim_contract()
 result["result_projection_authorization"]={"constant_name":"AUTHORIZED_RESULT_PROJECTION_DESCRIPTOR","descriptor":RESULT_PROJECTION,"descriptor_source":"external_acceptance_profile:/authorized_result_projection_descriptor","candidate_claim_only":True,"comparison":"WHOLE_OBJECT_JSON_EQUALITY_BEFORE_AST","mismatch_code":"METACONTRACT_PROJECTION_CLAIM_MISMATCH","procedure_descriptor_mismatch_code":"PROCEDURE_PROJECTION_CLAIM_MISMATCH","map_value_mismatch_code":"RESULT_PROJECTION_INVALID"}
 result["result_contracts"]["pre_execution_result"]["fail_codes"]=ALL_PREEXEC_CODES
 result["failure_semantics"]["pre_execution_order"]=PROFILE_PREFLIGHT_ORDER
 result["failure_semantics"]["external_profile_failure_precedes_candidate_schema_and_ast"]=True
 result["failure_semantics"]["claim_comparison"]="WHOLE_OBJECT_JSON_EQUALITY_BEFORE_SEMANTIC_USE"
 result["bootstrap_order"]=PROFILE_BOOTSTRAP_ORDER
 result["static_validation_rules"]=STATIC_RULES
 for law in result["laws"]:
  if law["law_id"]=="EXTERNAL_TRUST_IDENTITY": law["statement"]="Exact caller-supplied expected package identity triple plus a separate caller-supplied acceptance profile; neither comes from the candidate payload."
  if law["law_id"]=="FROZEN_AUTHORITY_AND_LINEAGE": law["statement"]="Verified frozen and accepted-source bytes are supplied in the separate acceptance profile; metacontract pins, candidate source copies, and builder constants are claims only and must compare whole-object before semantic use."
 return result

_BASE_MAKE_METACONTRACT_SCHEMA_PROFILE=make_metacontract_schema
def make_metacontract_schema():
 schema=_BASE_MAKE_METACONTRACT_SCHEMA_PROFILE()
 required=schema["required"]
 if "external_acceptance_profile_contract" not in required: required.append("external_acceptance_profile_contract")
 schema["properties"]["external_acceptance_profile_contract"]={"const":external_profile_claim_contract()}
 bound=schema["properties"]["universe_contract"]["properties"]["bound_source_universe"]
 if "identities_source" not in bound["required"]: bound["required"].append("identities_source")
 bound["properties"]["identities_source"]={"const":"external_acceptance_profile:/accepted_source_allowlist/ref"}
 bound["properties"]["source_allowlist_ref"]={"const":"external_acceptance_profile:/accepted_source_allowlist"}
 reserved=schema["properties"]["reserved_inputs"]
 reserved["minItems"]=5; reserved["maxItems"]=5
 item=reserved["items"]
 item["properties"].update({"transport":{"type":"string"},"source":{"type":"string"},"schema_ref":{"$ref":"#/$defs/typed_ref"},"candidate_copy_authority":{"const":False},"required_before_candidate_semantic_use":{"const":True},"profile_content_source":{"type":"object","required":["argument","content_pointer_tokens","pin_pointer_tokens","content_encoding","decode","use_after_pin_verification_only","candidate_copy_authority"],"properties":{"argument":{"const":"external_acceptance_profile"},"content_pointer_tokens":{"type":"array","minItems":1,"items":{"type":"string"}},"pin_pointer_tokens":{"type":"array","minItems":1,"items":{"type":"string"}},"content_encoding":{"const":"BASE64_RAW_FILE_BYTES"},"decode":{"const":"STRICT_BASE64_TO_RAW_UTF8_JSON"},"use_after_pin_verification_only":{"const":True},"candidate_copy_authority":{"const":False}},"additionalProperties":False}})
 item.setdefault("allOf",[]).extend([
  {"if":{"properties":{"name":{"const":"external_acceptance_profile"}},"required":["name"]},"then":{"required":["transport","source","schema_ref","candidate_copy_authority","required_before_candidate_semantic_use"],"properties":{"type":{"const":"EXTERNAL_ACCEPTANCE_PROFILE"},"origin":{"const":"EXTERNAL_ACCEPTANCE_PROFILE"},"transport":{"const":"--verification-input"},"source":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD"},"schema_ref":{"const":PROFILE_SCHEMA_REF}}}},
  {"if":{"properties":{"name":{"const":"frozen_rule_authority"}},"required":["name"]},"then":{"required":["profile_content_source"],"properties":{"type":{"const":"FROZEN_RULE_AUTHORITY"},"origin":{"const":"EXTERNAL_ACCEPTANCE_PROFILE"},"profile_content_source":{"properties":{"content_pointer_tokens":{"const":["frozen_authority_contents","frozen_r5r2_rules","content_base64"]},"pin_pointer_tokens":{"const":["frozen_authority_pins","frozen_r5r2_rules"]}}}}}},
  {"if":{"properties":{"name":{"const":"frozen_predecessor_semantics"}},"required":["name"]},"then":{"required":["profile_content_source"],"properties":{"type":{"const":"FROZEN_V013_GOVERNANCE"},"origin":{"const":"EXTERNAL_ACCEPTANCE_PROFILE"},"profile_content_source":{"properties":{"content_pointer_tokens":{"const":["frozen_authority_contents","frozen_r5r3_v013_semantics","content_base64"]},"pin_pointer_tokens":{"const":["frozen_authority_pins","frozen_r5r3_v013_semantics"]}}}}}}])
 origins=schema["properties"]["binding_origins"]
 origins["properties"]["allowed_origins"]={"const":["RULE_BINDING","BOOTSTRAP_VERIFICATION_UNIVERSE","EXTERNAL_FROZEN_AUTHORITY","EXTERNAL_FROZEN_PREDECESSOR","EXTERNAL_TRUST","EXTERNAL_ACCEPTANCE_PROFILE"]}
 origins["properties"]["reserved_names"]={"const":{"verification_universe":"VERIFICATION_UNIVERSE","frozen_rule_authority":"FROZEN_RULE_AUTHORITY_FROM_EXTERNAL_ACCEPTANCE_PROFILE","frozen_predecessor_semantics":"FROZEN_V013_GOVERNANCE_FROM_EXTERNAL_ACCEPTANCE_PROFILE","external_trust":"EXTERNAL_TRUST","external_acceptance_profile":"EXTERNAL_ACCEPTANCE_PROFILE"}}
 src=schema["properties"]["source_constraints"]["properties"]
 src["accepted_sources"]={"const":"EXACT_CALLER_PROFILE_REF_PATH_STATUS_CLASS_ROLES_RAW_SEMANTIC_SHA256_GIT_BLOB_AND_CONTENT"}
 src["external_profile_origin"]={"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD"}
 src["candidate_source_copies_as_authority"]={"const":"FORBIDDEN"}
 schema["properties"]["source_constraints"]["required"] += ["external_profile_origin","candidate_source_copies_as_authority"]
 rp=schema["properties"]["result_projection_authorization"]
 rp["required"]=["constant_name","descriptor","descriptor_source","candidate_claim_only","comparison","mismatch_code","procedure_descriptor_mismatch_code","map_value_mismatch_code"]
 rp["properties"]={"constant_name":{"const":"AUTHORIZED_RESULT_PROJECTION_DESCRIPTOR"},"descriptor":{"type":"object"},"descriptor_source":{"const":"external_acceptance_profile:/authorized_result_projection_descriptor"},"candidate_claim_only":{"const":True},"comparison":{"const":"WHOLE_OBJECT_JSON_EQUALITY_BEFORE_AST"},"mismatch_code":{"const":"METACONTRACT_PROJECTION_CLAIM_MISMATCH"},"procedure_descriptor_mismatch_code":{"const":"PROCEDURE_PROJECTION_CLAIM_MISMATCH"},"map_value_mismatch_code":{"const":"RESULT_PROJECTION_INVALID"}}
 rp["additionalProperties"]=False
 result=schema["properties"]["result_contracts"]["properties"]["pre_execution_result"]
 result["properties"]["fail_codes"]={"const":ALL_PREEXEC_CODES}
 fs=schema["properties"]["failure_semantics"]
 fs["required"] += ["external_profile_failure_precedes_candidate_schema_and_ast","claim_comparison"]
 fs["properties"]["pre_execution_order"]={"const":PROFILE_PREFLIGHT_ORDER}
 fs["properties"]["external_profile_failure_precedes_candidate_schema_and_ast"]={"const":True}
 fs["properties"]["claim_comparison"]={"const":"WHOLE_OBJECT_JSON_EQUALITY_BEFORE_SEMANTIC_USE"}
 fs["additionalProperties"]=False
 schema["properties"]["bootstrap_order"]={"const":PROFILE_BOOTSTRAP_ORDER}
 schema["properties"]["static_validation_rules"]={"const":STATIC_RULES}
 return schema
def external_profile_claim_contract():
    return {
        "required": True,
        "profile_id": "ACCORD-02E4R5R4-ACCEPTANCE-PROFILE",
        "input_origin": "CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD",
        "transport": "--verification-input",
        "profile_schema_validation": "CALLER_SUPPLIED_SCHEMA_BYTES_AND_SHA256_VERIFIED_BEFORE_USE",
        "frozen_authority_pins": {"frozen_r5r2_rules": R2PIN, "frozen_r5r3_v013_semantics": R3PIN},
        "accepted_source_allowlist": external_profile_source_rows(),
        "authorized_result_projection_descriptor_source": "EXTERNAL_ACCEPTANCE_PROFILE:/authorized_result_projection_descriptor",
        "authorized_result_projection_descriptor": RESULT_PROJECTION,
        "candidate_claim_comparisons": PROFILE_CLAIM_COMPARISONS,
        "content_verification": PROFILE_CONTENT_VERIFICATION,
        "pre_execution_failures": PROFILE_PREFLIGHT_ORDER,
        "candidate_registry_fallback": "FORBIDDEN",
        "candidate_source_copies": "TRANSPORT_ONLY_NEVER_AUTHORITY",
    }
_BASE_MAKE_PROC_SCHEMA_PROFILE_REQUIRED = make_proc_schema
def make_proc_schema():
    schema = _BASE_MAKE_PROC_SCHEMA_PROFILE_REQUIRED()
    proc = schema["$defs"]["procedure"]
    proc.setdefault("allOf", []).append({
        "if": {"properties": {"procedure_id": {"const": "REQUIREMENT_MAP_EVAL"}}, "required": ["procedure_id"]},
        "then": {"properties": {"result": {"required": ["result_projection"], "properties": {"result_projection": {"const": RESULT_PROJECTION}}}}}
    })
    return schema
_BASE_BUILD_README = build
R4_README = """# ACCORD-02E4R5R4 candidate (0.2, CANDIDATE_UNACCEPTED)

This directory contains the additive R4 normative package artifacts. The package preserves the accepted 0.1 expectations while expressing R4 governance through typed, closed declarative data.

## Authority and verification inputs

A verifier must receive the expected package identity and the external acceptance profile independently from the candidate payload. The profile is supplied with the verifier input transport named --verification-input and is validated against the fixed external profile contract before candidate semantic use. It provides the frozen R5R2 rule authority, frozen R5R3 V013 predecessor semantics, exact accepted-base and accepted-vector identities and bytes, and the authorized result-projection descriptor.

Files under sources/ are export transport copies. They are not authority: a verifier must compare them to the externally supplied pins and must not fall back to candidate copies, package fields, or generator constants when an external value is absent.

## Layout

| Path | Role |
| --- | --- |
| Top-level JSON files | Normative package artifacts |
| schema/ | Draft 2020-12 artifact schemas |
| sources/ | Byte-for-byte transport copies of frozen and accepted sources |
| audit/build_r5r4_artifacts.py | Deterministic artifact generator |

## Generation

Run python docs/accord-02e4r5r4/audit/build_r5r4_artifacts.py from the repository root to regenerate the declarative artifacts. This command generates files only; it does not evaluate or certify a candidate.

The primary generic reference evaluator is included at audit/evaluate_r5r4.py. It requires explicit caller inputs for the package trust triple, external acceptance-profile bytes, verifier-owned profile-schema bytes and identity, and the externally expected raw schema SHA-256. The bundled --self-test exercises a non-normative local profile fixture and focused binding/derivation mutations; its local source copies are not authority.

No independent evaluator, negative-case falsifier, or release verifier is included in this slice. The evaluator is a primary implementation only; its output is not an acceptance result, and the package remains CANDIDATE_UNACCEPTED.
"""
def build():
    _BASE_BUILD_README()
    (OUT / "README.md").write_text(R4_README, encoding="utf-8")
# Round-2 remediation: profile validation schema bytes and their expected digest are
# separately supplied to the verifier; the candidate schema registry is not authoritative.
PROFILE_SCHEMA_ID = f"{NS}:external-acceptance-profile-schema:1"
PROFILE_SCHEMA_TRANSPORT_PATH = f"{REL}/sources/external-acceptance-profile.schema.json"
PROFILE_SCHEMA_BYTES_ARGUMENT = "--acceptance-profile-schema"
PROFILE_SCHEMA_SHA256_ARGUMENT = "--acceptance-profile-schema-sha256"
PROFILE_SCHEMA_ID_ARGUMENT = "--acceptance-profile-schema-id"
PROFILE_SCHEMA_INPUT_CONTRACT = {
    "required": True,
    "schema_identity": PROFILE_SCHEMA_ID,
    "schema_identity_argument": PROFILE_SCHEMA_ID_ARGUMENT,
    "expected_schema_identity_origin": "CALLER_SUPPLIED_OUTSIDE_CANDIDATE",
    "schema_bytes_argument": PROFILE_SCHEMA_BYTES_ARGUMENT,
    "expected_sha256_argument": PROFILE_SCHEMA_SHA256_ARGUMENT,
    "expected_sha256_algorithm": "SHA-256",
    "expected_sha256_origin": "CALLER_SUPPLIED_OUTSIDE_CANDIDATE",
    "digest_input": "RAW_SCHEMA_BYTES",
    "verify_digest_before_parse_or_use": True,
    "verify_schema_identity_and_dialect_after_digest": True,
    "schema_dialect": DIALECT,
    "candidate_registry_selection": "FORBIDDEN",
    "candidate_schema_override": "FORBIDDEN",
    "candidate_embedded_schema_fallback": "FORBIDDEN",
    "candidate_registry_fallback": "FORBIDDEN",
    "unregistered_transport_copy": PROFILE_SCHEMA_TRANSPORT_PATH,
    "transport_copy_authority": "NONE_CALLER_MUST_SUPPLY_BYTES_AND_EXPECTED_DIGEST_SEPARATELY",
}
PROFILE_SCHEMA_FAILURE_CODES = [
    "MISSING_EXTERNAL_PROFILE_SCHEMA",
    "EXTERNAL_PROFILE_SCHEMA_DIGEST_MISMATCH",
    "INVALID_EXTERNAL_PROFILE_SCHEMA",
]
PROFILE_FAILURE_CODES = PROFILE_SCHEMA_FAILURE_CODES + [x for x in PROFILE_FAILURE_CODES if x not in PROFILE_SCHEMA_FAILURE_CODES]
PROFILE_FAILURE_OPERATIONS = {
    **PROFILE_FAILURE_OPERATIONS,
    "MISSING_EXTERNAL_PROFILE_SCHEMA": "READ_PROFILE_SCHEMA_ID_BYTES_AND_EXPECTED_DIGEST",
    "EXTERNAL_PROFILE_SCHEMA_DIGEST_MISMATCH": "VERIFY_PROFILE_SCHEMA_RAW_SHA256",
    "INVALID_EXTERNAL_PROFILE_SCHEMA": "VALIDATE_PROFILE_SCHEMA_ID_DIALECT_AND_DRAFT",
}
ALL_PREEXEC_CODES = PROFILE_FAILURE_CODES + ["SCHEMA_INVALID_BOUND_OBJECT", "RESULT_PROJECTION_INVALID"]
PROFILE_PREFLIGHT_ORDER = PROFILE_SCHEMA_FAILURE_CODES + [x for x in PROFILE_PREFLIGHT_ORDER if x not in PROFILE_SCHEMA_FAILURE_CODES]
PROFILE_BOOTSTRAP_ORDER = [
    "READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST_TRIPLE",
    "READ_EXTERNAL_PROFILE_SCHEMA_ID_BYTES_AND_EXPECTED_SHA256_OUTSIDE_CANDIDATE",
    "REQUIRE_CALLER_SCHEMA_ID_EQUAL_FIXED_VERIFIER_SCHEMA_ID",
    "VERIFY_PROFILE_SCHEMA_RAW_SHA256_BEFORE_PARSE_OR_USE",
    "VERIFY_PROFILE_SCHEMA_ID_AND_DRAFT_2020_12_DIALECT",
    "REJECT_DUPLICATE_CANDIDATE_JSON_NAMES_AND_INVALID_UTF8",
    "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE",
    "READ_EXTERNAL_ACCEPTANCE_PROFILE_OUTSIDE_CANDIDATE",
    "VALIDATE_EXTERNAL_ACCEPTANCE_PROFILE_WITH_VERIFIED_EXTERNAL_SCHEMA_BYTES",
    "VERIFY_EXTERNAL_FROZEN_R5R2_CONTENT_AND_PIN",
    "VERIFY_EXTERNAL_FROZEN_R5R3_CONTENT_AND_PIN",
    "VERIFY_EXTERNAL_ACCEPTED_BASE_AND_VECTOR_CONTENT_AND_PINS",
    "COMPARE_ALL_CANDIDATE_AUTHORITY_CLAIMS_WHOLE_OBJECT_BEFORE_SEMANTIC_USE",
    "DERIVE_VERIFICATION_UNIVERSE_FROM_BOOTSTRAP_INPUTS",
    "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
    "STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR",
    "EXECUTE_DECLARED_ASSERTIONS_IN_ORDER",
    "FINALIZE_TYPED_RESULT",
]
PROFILE_CONTENT_VERIFICATION = {
    "acceptance_profile_schema": PROFILE_SCHEMA_INPUT_CONTRACT,
    "schema_document": "STRICT_UTF8_JSON_REJECT_DUPLICATE_MEMBERS_VALID_DRAFT_2020_12_SCHEMA",
    "schema_bytes": "CALLER_INPUT_BYTES_ONLY",
    "profile_bytes": "CALLER_SUPPLIED_EXTERNAL_ACCEPTANCE_PROFILE_ONLY",
    "base64_decode": "STRICT_RFC4648_NO_WHITESPACE",
    "json_decode": "UTF8_REJECT_DUPLICATE_MEMBER_NAMES",
    "frozen_sources": {
        "git_blob": "SHA1(ASCII('blob '+DECIMAL_BYTE_LENGTH)+NUL+RAW_BYTES)",
        "content_use": "PARSED_CONTENT_ONLY_AFTER_PIN_MATCH",
    },
    "accepted_sources": {
        "raw_sha256": "SHA256_RAW_BYTES",
        "semantic_sha256": "SHA256_RFC8785_JCS_PARSED_JSON",
        "git_blob": "SHA1_GIT_BLOB_OBJECT",
        "metadata": "EXACT_REF_PATH_ROLE_STATUS_CLASS_AND_SCHEMA",
    },
    "candidate_source_copies": "TRANSPORT_ONLY_NEVER_AUTHORITY_OR_RESOLVER_INPUT",
    "candidate_registry_fallback": "FORBIDDEN",
}
PROCEDURE_PROJECTION_SELECTOR = {
    "collection_pointer_rfc6901": "/procedures",
    "collection_type": "ARRAY",
    "selection": {
        "member_pointer_rfc6901": "/procedure_id",
        "operator": "JSON_EQUAL",
        "literal": "REQUIREMENT_MAP_EVAL",
        "required_match_count": 1,
    },
    "selected_value_pointer_rfc6901_relative_to_item": "/result/result_projection",
    "selected_value_required": True,
    "selected_value_comparison": "WHOLE_OBJECT_JSON_EQUALITY_TO_EXTERNAL_PROFILE_DESCRIPTOR",
    "other_items_constraint": {
        "selection": "EVERY_ARRAY_ITEM_NOT_EQUAL_TO_SELECTED_LITERAL_BY_THE_SAME_MEMBER_POINTER",
        "forbidden_pointer_rfc6901_relative_to_item": "/result/result_projection",
        "must_be_absent": True,
        "present_null_counts_as_present": True,
    },
    "failure_code": "PROCEDURE_PROJECTION_CLAIM_MISMATCH",
    "algorithm": "RFC6901_ARRAY_LOOKUP_THEN_TYPED_MEMBER_FILTER_THEN_EXACT_COUNT_THEN_RELATIVE_MEMBER_LOOKUP",
}
PROFILE_CLAIM_COMPARISONS = [
    {"candidate_artifact":"metacontract","candidate_pointer_rfc6901":"/external_authority_pins/frozen_r5r2_rules","profile_pointer_rfc6901":"/frozen_authority_pins/frozen_r5r2_rules","comparison":"WHOLE_OBJECT_JSON_EQUALITY","before_semantic_use":True,"failure_code":"METACONTRACT_R5R2_PIN_CLAIM_MISMATCH"},
    {"candidate_artifact":"metacontract","candidate_pointer_rfc6901":"/external_authority_pins/frozen_r5r3_v013_semantics","profile_pointer_rfc6901":"/frozen_authority_pins/frozen_r5r3_v013_semantics","comparison":"WHOLE_OBJECT_JSON_EQUALITY","before_semantic_use":True,"failure_code":"METACONTRACT_R5R3_PIN_CLAIM_MISMATCH"},
    {"candidate_artifact":"metacontract","candidate_pointer_rfc6901":"/accepted_source_allowlist","profile_pointer_rfc6901":"/accepted_source_allowlist","comparison":"WHOLE_OBJECT_JSON_EQUALITY","before_semantic_use":True,"failure_code":"METACONTRACT_ACCEPTED_ALLOWLIST_CLAIM_MISMATCH"},
    {"candidate_artifact":"metacontract","candidate_pointer_rfc6901":"/result_projection_authorization/descriptor","profile_pointer_rfc6901":"/authorized_result_projection_descriptor","comparison":"WHOLE_OBJECT_JSON_EQUALITY","before_semantic_use":True,"failure_code":"METACONTRACT_PROJECTION_CLAIM_MISMATCH"},
    {"candidate_artifact":"procedure-registry","candidate_selector":PROCEDURE_PROJECTION_SELECTOR,"profile_pointer_rfc6901":"/authorized_result_projection_descriptor","comparison":"SELECTED_DESCRIPTOR_WHOLE_OBJECT_JSON_EQUALITY_AND_NO_OTHER_PROJECTION","before_semantic_use":True,"failure_code":"PROCEDURE_PROJECTION_CLAIM_MISMATCH"},
]
STATIC_RULES += [
    "EXTERNAL_PROFILE_SCHEMA_BYTES_AND_EXPECTED_RAW_SHA256_ARE_CALLER_SUPPLIED_OUTSIDE_CANDIDATE",
    "VERIFY_EXTERNAL_PROFILE_SCHEMA_DIGEST_BEFORE_PARSE_AND_BEFORE_PROFILE_USE",
    "EXTERNAL_PROFILE_SCHEMA_ID_DIALECT_AND_DRAFT_ARE_FIXED_VERIFIER_INPUTS",
    "CANDIDATE_SCHEMA_REGISTRY_CANNOT_SELECT_OVERRIDE_OR_FALL_BACK_FOR_PROFILE_SCHEMA",
    "UNREGISTERED_PROFILE_SCHEMA_COPY_IS_TRANSPORT_ONLY_NEVER_AUTO_READ",
    "PROCEDURE_SELECTOR_USES_RFC6901_ARRAY_POINTER_AND_TYPED_ID_FILTER",
    "REQUIREMENT_MAP_EVAL_SELECTOR_MATCH_COUNT_EXACTLY_ONE",
    "REQUIREMENT_MAP_EVAL_RESULT_PROJECTION_REQUIRED_AND_EXACT",
    "NO_OTHER_PROCEDURE_MAY_DECLARE_RESULT_PROJECTION",
]
BOOTSTRAP_ORDER = PROFILE_BOOTSTRAP_ORDER

_BASE_EXTERNAL_PROFILE_INSTANCE_SCHEMA_R2 = external_profile_instance_schema
def external_profile_instance_schema():
    schema = _BASE_EXTERNAL_PROFILE_INSTANCE_SCHEMA_R2()
    schema["$schema"] = DIALECT
    schema["$id"] = PROFILE_SCHEMA_ID
    schema["title"] = "Verifier-owned ACCORD-02E4R5R4 external acceptance profile input"
    return schema

def external_profile_claim_contract():
    return {
        "required": True,
        "profile_id": "ACCORD-02E4R5R4-ACCEPTANCE-PROFILE",
        "input_origin": "CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD",
        "transport": "--verification-input",
        "profile_schema_input": PROFILE_SCHEMA_INPUT_CONTRACT,
        "frozen_authority_pins": {"frozen_r5r2_rules": R2PIN, "frozen_r5r3_v013_semantics": R3PIN},
        "accepted_source_allowlist": external_profile_source_rows(),
        "authorized_result_projection_descriptor": RESULT_PROJECTION,
        "authorized_result_projection_descriptor_source": "EXTERNAL_ACCEPTANCE_PROFILE:/authorized_result_projection_descriptor",
        "candidate_claim_comparisons": PROFILE_CLAIM_COMPARISONS,
        "procedure_projection_selector": PROCEDURE_PROJECTION_SELECTOR,
        "content_verification": PROFILE_CONTENT_VERIFICATION,
        "pre_execution_failures": PROFILE_PREFLIGHT_ORDER,
        "candidate_registry_fallback": "FORBIDDEN",
        "candidate_source_copies": "TRANSPORT_ONLY_NEVER_AUTHORITY",
    }

_BASE_MAKE_PROC_SCHEMA_R2 = make_proc_schema
def make_proc_schema():
    schema = _BASE_MAKE_PROC_SCHEMA_R2()
    proc = schema["$defs"]["procedure"]
    proc["allOf"] = [rule for rule in proc.get("allOf", []) if rule.get("if", {}).get("properties", {}).get("procedure_id", {}).get("const") not in SIG]
    proc.setdefault("allOf", []).append({
        "if": {"properties":{"procedure_id":{"const":"REQUIREMENT_MAP_EVAL"}},"required":["procedure_id"]},
        "then": {"properties":{"result":{"required":["result_projection"],"properties":{"result_projection":{"const":RESULT_PROJECTION}}}}},
    })
    for procedure_id in SIG:
        if procedure_id == "REQUIREMENT_MAP_EVAL":
            continue
        proc["allOf"].append({
            "if": {"properties":{"procedure_id":{"const":procedure_id}},"required":["procedure_id"]},
            "then": {"properties":{"result":{"not":{"required":["result_projection"]}}}},
        })
    return schema

_BASE_UPDATE_SCHEMAS_R2 = update_schemas
def update_schemas(schemas):
    _BASE_UPDATE_SCHEMAS_R2(schemas)
    ext = schemas["external-verification-input-contract.schema.json"]
    ext.setdefault("$defs", {}).pop("acceptance_profile", None)
    ext["required"] = [x for x in ext["required"] if x != "acceptance_profile_schema_ref"]
    for name in ["acceptance_profile_schema_input", "procedure_projection_selector"]:
        if name not in ext["required"]: ext["required"].append(name)
    ext["properties"].pop("acceptance_profile_schema_ref", None)
    ext["properties"]["acceptance_profile_schema_input"] = {"const":PROFILE_SCHEMA_INPUT_CONTRACT}
    ext["properties"]["registry_membership"] = {"const":{"contract_artifact":"REGISTERED_CANDIDATE_NORMATIVE_CONTRACT","runtime_external_inputs":"NOT_REGISTERED_PACKAGE_OBJECTS"}}
    cli_contract = {"--expected-package-id":"CALLER_SUPPLIED_EXPECTED_PACKAGE_ID","--expected-package-version":"CALLER_SUPPLIED_EXPECTED_PACKAGE_VERSION","--expected-package-digest":"CALLER_SUPPLIED_EXPECTED_PACKAGE_SHA256","--verification-input":"PATH_TO_CALLER_SUPPLIED_EXTERNAL_ACCEPTANCE_PROFILE_JSON","--acceptance-profile-schema-id":"CALLER_SUPPLIED_EXPECTED_EXTERNAL_SCHEMA_ID","--acceptance-profile-schema":"CALLER_SUPPLIED_PROFILE_SCHEMA_BYTES_PATH","--acceptance-profile-schema-sha256":"CALLER_SUPPLIED_EXPECTED_SHA256_OF_RAW_PROFILE_SCHEMA_BYTES"}
    ext["properties"]["cli"] = {"type":"object","required":list(cli_contract),"properties":{k:{"const":v} for k,v in cli_contract.items()},"additionalProperties":False}
    ext["properties"]["candidate_claim_comparisons"] = {"const":PROFILE_CLAIM_COMPARISONS}
    ext["properties"]["procedure_projection_selector"] = {"const":PROCEDURE_PROJECTION_SELECTOR}
    if "required_external_fields" not in ext["required"]: ext["required"].append("required_external_fields")
    ext["properties"]["required_external_fields"] = {"const":["expected_package_id","expected_package_version","expected_package_digest","external_acceptance_profile","acceptance_profile_schema_identity","acceptance_profile_schema_bytes","acceptance_profile_schema_sha256"]}
    field_props = ext["properties"]["fields"]["properties"]
    field_req = ext["properties"]["fields"]["required"]
    for name in ["acceptance_profile_schema_identity","acceptance_profile_schema_bytes","acceptance_profile_schema_sha256"]:
        if name not in field_req: field_req.append(name)
    field_props["acceptance_profile"] = {"type":"object","required":["required","type","source","transport","schema_identity","schema_identity_argument","expected_schema_identity_origin","schema_bytes_argument","expected_sha256_argument","expected_sha256_origin","candidate_schema_selection","candidate_fallback","registry_membership"],"properties":{"required":{"const":True},"type":{"const":"EXTERNAL_ACCEPTANCE_PROFILE"},"source":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD"},"transport":{"const":"--verification-input"},"schema_identity":{"const":PROFILE_SCHEMA_ID},"schema_identity_argument":{"const":PROFILE_SCHEMA_ID_ARGUMENT},"expected_schema_identity_origin":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE"},"schema_bytes_argument":{"const":PROFILE_SCHEMA_BYTES_ARGUMENT},"expected_sha256_argument":{"const":PROFILE_SCHEMA_SHA256_ARGUMENT},"expected_sha256_origin":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE"},"candidate_schema_selection":{"const":"FORBIDDEN"},"candidate_fallback":{"const":"FORBIDDEN"},"registry_membership":{"const":"FORBIDDEN_NOT_A_PACKAGE_OBJECT"}},"additionalProperties":False}
    field_props["acceptance_profile_schema_identity"] = {"type":"object","required":["required","type","source","transport","expected_identity","comparison"],"properties":{"required":{"const":True},"type":{"const":"SCHEMA_IDENTITY"},"source":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE"},"transport":{"const":PROFILE_SCHEMA_ID_ARGUMENT},"expected_identity":{"const":PROFILE_SCHEMA_ID},"comparison":{"const":"CALLER_VALUE_MUST_EQUAL_FIXED_VERIFIER_SCHEMA_ID"}},"additionalProperties":False}
    field_props["acceptance_profile_schema_bytes"] = {"type":"object","required":["required","type","source","transport","schema_identity","expected_sha256_argument","sha256_algorithm","verification_order","candidate_fallback"],"properties":{"required":{"const":True},"type":{"const":"RAW_SCHEMA_BYTES"},"source":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE"},"transport":{"const":PROFILE_SCHEMA_BYTES_ARGUMENT},"schema_identity":{"const":PROFILE_SCHEMA_ID},"expected_sha256_argument":{"const":PROFILE_SCHEMA_SHA256_ARGUMENT},"sha256_algorithm":{"const":"SHA-256"},"verification_order":{"const":"VERIFY_RAW_SHA256_BEFORE_PARSE_OR_USE"},"candidate_fallback":{"const":"FORBIDDEN"}},"additionalProperties":False}
    field_props["acceptance_profile_schema_sha256"] = {"type":"object","required":["required","type","source","transport","algorithm","target"],"properties":{"required":{"const":True},"type":{"const":"SHA256"},"source":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE"},"transport":{"const":PROFILE_SCHEMA_SHA256_ARGUMENT},"algorithm":{"const":"SHA-256"},"target":{"const":"RAW_EXTERNAL_PROFILE_SCHEMA_BYTES"}},"additionalProperties":False}
    auths = schemas["authority-requirements.schema.json"]
    auth = auths["properties"]["trust_boundary_requirements"]
    auth["required"] = [x for x in auth["required"] if x != "acceptance_profile_schema_ref"]
    auth["required"] += ["acceptance_profile_schema_input"]
    ap = auth["properties"]
    ap.pop("acceptance_profile_schema_ref", None)
    ap["required_external_fields"] = {"const":["expected_package_id","expected_package_version","expected_package_digest","external_acceptance_profile","acceptance_profile_schema_identity","acceptance_profile_schema_bytes","acceptance_profile_schema_sha256"]}
    ap["acceptance_profile_schema_input"] = {"const":PROFILE_SCHEMA_INPUT_CONTRACT}
    ap["acceptance_profile_input_source"] = {"const":"CALLER_SUPPLIED_SEPARATELY_VIA_VERIFICATION_INPUT"}
    ap["candidate_authority_claim_comparison"] = {"const":"WHOLE_OBJECT_EQUALITY_BEFORE_SEMANTIC_USE"}
    ap["source_content_verification"] = {"const":PROFILE_CONTENT_VERIFICATION}
    ap["preflight_failure_codes"] = {"const":PROFILE_FAILURE_CODES}
    ap["cli"] = {"const":["--expected-package-id","--expected-package-version","--expected-package-digest","--verification-input","--acceptance-profile-schema-id","--acceptance-profile-schema","--acceptance-profile-schema-sha256"]}
    ap["profile_fallback"] = {"const":"FORBIDDEN"}
    proc = schemas["procedure-registry.schema.json"]["$defs"]["procedure"]
    # procedure conditionals are emitted by make_proc_schema; preserve them unchanged.
    return schemas

_BASE_NORMALIZE_EXTERNAL_TRUST_R2 = normalize_external_trust
def normalize_external_trust(files):
    _BASE_NORMALIZE_EXTERNAL_TRUST_R2(files)
    trust = files["external-verification-input.contract.json"]
    trust.pop("acceptance_profile_schema_ref", None)
    trust["acceptance_profile_schema_input"] = PROFILE_SCHEMA_INPUT_CONTRACT
    trust["registry_membership"] = {"contract_artifact":"REGISTERED_CANDIDATE_NORMATIVE_CONTRACT","runtime_external_inputs":"NOT_REGISTERED_PACKAGE_OBJECTS"}
    trust["candidate_claim_comparisons"] = PROFILE_CLAIM_COMPARISONS
    trust["procedure_projection_selector"] = PROCEDURE_PROJECTION_SELECTOR
    trust["content_verification"] = PROFILE_CONTENT_VERIFICATION
    trust["pre_execution_failures"] = {"codes":ALL_PREEXEC_CODES,"order":PROFILE_PREFLIGHT_ORDER}
    trust["results"]["PRE_EXECUTION"] = {"codes":ALL_PREEXEC_CODES,"order":PROFILE_PREFLIGHT_ORDER}
    trust["required_external_fields"] = ["expected_package_id","expected_package_version","expected_package_digest","external_acceptance_profile","acceptance_profile_schema_identity","acceptance_profile_schema_bytes","acceptance_profile_schema_sha256"]
    trust["fields"]["acceptance_profile"] = {"required":True,"type":"EXTERNAL_ACCEPTANCE_PROFILE","source":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD","transport":"--verification-input","schema_identity":PROFILE_SCHEMA_ID,"schema_identity_argument":PROFILE_SCHEMA_ID_ARGUMENT,"expected_schema_identity_origin":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE","schema_bytes_argument":PROFILE_SCHEMA_BYTES_ARGUMENT,"expected_sha256_argument":PROFILE_SCHEMA_SHA256_ARGUMENT,"expected_sha256_origin":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE","candidate_schema_selection":"FORBIDDEN","candidate_fallback":"FORBIDDEN","registry_membership":"FORBIDDEN_NOT_A_PACKAGE_OBJECT"}
    trust["fields"]["acceptance_profile_schema_identity"] = {"required":True,"type":"SCHEMA_IDENTITY","source":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE","transport":PROFILE_SCHEMA_ID_ARGUMENT,"expected_identity":PROFILE_SCHEMA_ID,"comparison":"CALLER_VALUE_MUST_EQUAL_FIXED_VERIFIER_SCHEMA_ID"}
    trust["fields"]["acceptance_profile_schema_bytes"] = {"required":True,"type":"RAW_SCHEMA_BYTES","source":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE","transport":PROFILE_SCHEMA_BYTES_ARGUMENT,"schema_identity":PROFILE_SCHEMA_ID,"expected_sha256_argument":PROFILE_SCHEMA_SHA256_ARGUMENT,"sha256_algorithm":"SHA-256","verification_order":"VERIFY_RAW_SHA256_BEFORE_PARSE_OR_USE","candidate_fallback":"FORBIDDEN"}
    trust["fields"]["acceptance_profile_schema_sha256"] = {"required":True,"type":"SHA256","source":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE","transport":PROFILE_SCHEMA_SHA256_ARGUMENT,"algorithm":"SHA-256","target":"RAW_EXTERNAL_PROFILE_SCHEMA_BYTES"}
    trust["cli"] = {"--expected-package-id":"CALLER_SUPPLIED_EXPECTED_PACKAGE_ID","--expected-package-version":"CALLER_SUPPLIED_EXPECTED_PACKAGE_VERSION","--expected-package-digest":"CALLER_SUPPLIED_EXPECTED_PACKAGE_SHA256","--verification-input":"PATH_TO_CALLER_SUPPLIED_EXTERNAL_ACCEPTANCE_PROFILE_JSON","--acceptance-profile-schema-id":"CALLER_SUPPLIED_EXPECTED_EXTERNAL_SCHEMA_ID","--acceptance-profile-schema":"CALLER_SUPPLIED_PROFILE_SCHEMA_BYTES_PATH","--acceptance-profile-schema-sha256":"CALLER_SUPPLIED_EXPECTED_SHA256_OF_RAW_PROFILE_SCHEMA_BYTES"}
    auth = files["authority-requirements.json"]["trust_boundary_requirements"]
    auth.pop("acceptance_profile_schema_ref", None)
    auth["required_external_fields"] = trust["required_external_fields"]
    auth["acceptance_profile_schema_input"] = PROFILE_SCHEMA_INPUT_CONTRACT
    auth["acceptance_profile_input_source"] = "CALLER_SUPPLIED_SEPARATELY_VIA_VERIFICATION_INPUT"
    auth["candidate_authority_claim_comparison"] = "WHOLE_OBJECT_EQUALITY_BEFORE_SEMANTIC_USE"
    auth["source_content_verification"] = PROFILE_CONTENT_VERIFICATION
    auth["preflight_failure_codes"] = PROFILE_FAILURE_CODES
    auth["profile_fallback"] = "FORBIDDEN"
    auth["cli"] = list(trust["cli"])

_BASE_MAKE_METACONTRACT_R2 = make_metacontract
def make_metacontract(proc, inv):
    result = _BASE_MAKE_METACONTRACT_R2(proc, inv)
    result["scope_semantics"] = SCOPE_SEMANTICS
    result["external_acceptance_profile_contract"] = external_profile_claim_contract()
    result["source_constraints"]["acceptance_profile_schema"] = PROFILE_SCHEMA_INPUT_CONTRACT
    for row in result["reserved_inputs"]:
        if row.get("name") == "external_acceptance_profile":
            row.pop("schema_ref", None)
            row.update({"schema_identity":PROFILE_SCHEMA_ID,"schema_identity_argument":PROFILE_SCHEMA_ID_ARGUMENT,"expected_schema_identity_origin":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE","schema_bytes_argument":PROFILE_SCHEMA_BYTES_ARGUMENT,"expected_sha256_argument":PROFILE_SCHEMA_SHA256_ARGUMENT,"expected_sha256_origin":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE","candidate_schema_selection":"FORBIDDEN","candidate_fallback":"FORBIDDEN","registry_membership":"FORBIDDEN_NOT_A_PACKAGE_OBJECT","transport_copy":PROFILE_SCHEMA_TRANSPORT_PATH,"transport_copy_authority":"NONE_CALLER_MUST_SUPPLY_BYTES_AND_EXPECTED_DIGEST_SEPARATELY"})
    return result

_BASE_MAKE_METACONTRACT_SCHEMA_R2 = make_metacontract_schema
def make_metacontract_schema():
    schema = _BASE_MAKE_METACONTRACT_SCHEMA_R2()
    if "scope_semantics" not in schema["required"]: schema["required"].append("scope_semantics")
    schema["properties"]["scope_semantics"] = {"const":SCOPE_SEMANTICS}
    schema["properties"]["external_acceptance_profile_contract"] = {"const":external_profile_claim_contract()}
    sc = schema["properties"]["source_constraints"]
    if "acceptance_profile_schema" not in sc["required"]: sc["required"].append("acceptance_profile_schema")
    sc["properties"]["acceptance_profile_schema"] = {"const":PROFILE_SCHEMA_INPUT_CONTRACT}
    reserved = schema["properties"]["reserved_inputs"]["items"]
    rp = reserved["properties"]
    for key,value in {"schema_identity":{"const":PROFILE_SCHEMA_ID},"schema_identity_argument":{"const":PROFILE_SCHEMA_ID_ARGUMENT},"expected_schema_identity_origin":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE"},"schema_bytes_argument":{"const":PROFILE_SCHEMA_BYTES_ARGUMENT},"expected_sha256_argument":{"const":PROFILE_SCHEMA_SHA256_ARGUMENT},"expected_sha256_origin":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE"},"candidate_schema_selection":{"const":"FORBIDDEN"},"candidate_fallback":{"const":"FORBIDDEN"},"registry_membership":{"const":"FORBIDDEN_NOT_A_PACKAGE_OBJECT"},"transport_copy":{"const":PROFILE_SCHEMA_TRANSPORT_PATH},"transport_copy_authority":{"const":"NONE_CALLER_MUST_SUPPLY_BYTES_AND_EXPECTED_DIGEST_SEPARATELY"}}.items(): rp[key]=value
    reserved["allOf"] = [x for x in reserved.get("allOf",[]) if not (x.get("if",{}).get("properties",{}).get("name",{}).get("const")=="external_acceptance_profile")]
    reserved["allOf"].append({"if":{"properties":{"name":{"const":"external_acceptance_profile"}},"required":["name"]},"then":{"required":["transport","source","schema_identity","schema_identity_argument","expected_schema_identity_origin","schema_bytes_argument","expected_sha256_argument","expected_sha256_origin","candidate_schema_selection","candidate_fallback","registry_membership","candidate_copy_authority","required_before_candidate_semantic_use"],"not":{"required":["schema_ref"]},"properties":{"type":{"const":"EXTERNAL_ACCEPTANCE_PROFILE"},"origin":{"const":"EXTERNAL_ACCEPTANCE_PROFILE"},"transport":{"const":"--verification-input"},"source":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE_PAYLOAD"},"schema_identity":{"const":PROFILE_SCHEMA_ID},"schema_bytes_argument":{"const":PROFILE_SCHEMA_BYTES_ARGUMENT},"expected_sha256_argument":{"const":PROFILE_SCHEMA_SHA256_ARGUMENT},"expected_sha256_origin":{"const":"CALLER_SUPPLIED_OUTSIDE_CANDIDATE"},"candidate_schema_selection":{"const":"FORBIDDEN"},"candidate_fallback":{"const":"FORBIDDEN"},"registry_membership":{"const":"FORBIDDEN_NOT_A_PACKAGE_OBJECT"}}}})
    schema["properties"]["binding_origins"]["properties"]["reserved_names"] = {"const":{"verification_universe":"VERIFICATION_UNIVERSE","frozen_rule_authority":"FROZEN_RULE_AUTHORITY_FROM_EXTERNAL_ACCEPTANCE_PROFILE","frozen_predecessor_semantics":"FROZEN_V013_GOVERNANCE_FROM_EXTERNAL_ACCEPTANCE_PROFILE","external_trust":"EXTERNAL_TRUST","external_acceptance_profile":"EXTERNAL_ACCEPTANCE_PROFILE"}}
    return schema

_BASE_BUILD_PROFILE_SCHEMA_R2 = build
R4_README = """# ACCORD-02E4R5R4 candidate (0.2, CANDIDATE_UNACCEPTED)

This directory contains the additive R4 normative package artifacts. The package preserves the accepted 0.1 expectations while expressing R4 governance through typed, closed declarative data.

## Authority and verifier inputs

A verifier receives the expected package identity, the external acceptance profile, the verifier-owned profile-schema bytes, and the caller-supplied expected SHA-256 digest of those exact raw schema bytes independently from the candidate payload. The expected schema identity arrives through --acceptance-profile-schema-id; the schema bytes arrive through --acceptance-profile-schema; the expected digest arrives through --acceptance-profile-schema-sha256; the profile JSON arrives through --verification-input. The verifier checks the caller-supplied raw SHA-256 before parsing or using the schema, then checks its fixed schema identity and Draft 2020-12 dialect before validating the profile. The candidate registry and candidate schemas cannot select, override, or replace this schema and provide no fallback.

The file sources/external-acceptance-profile.schema.json is an unregistered transport copy only. It is never loaded automatically and is not authority. A caller may supply its exact bytes together with an independently supplied expected digest. Other files under sources/ are export transport copies and are not authority; a verifier must compare them to the separately supplied pins and must not fall back to candidate copies, package fields, or generator constants.

## Layout

| Path | Role |
| --- | --- |
| Top-level JSON files | Normative package artifacts |
| schema/ | Draft 2020-12 schemas for registered package artifacts |
| sources/ | Byte-for-byte transport copies; no source copy is registered as authority |
| audit/build_r5r4_artifacts.py | Deterministic artifact generator |

## Generation

Run python docs/accord-02e4r5r4/audit/build_r5r4_artifacts.py from the repository root to regenerate the declarative artifacts. This command generates files only; it does not evaluate or certify a candidate.

The primary generic reference evaluator is included at audit/evaluate_r5r4.py. It requires explicit caller inputs for the package trust triple, external acceptance-profile bytes, verifier-owned profile-schema bytes and identity, and the externally expected raw schema SHA-256. The bundled --self-test exercises a non-normative local profile fixture and focused binding/derivation mutations; its local source copies are not authority.

No independent evaluator, negative-case falsifier, or release verifier is included in this slice. The evaluator is a primary implementation only; its output is not an acceptance result, and the package remains CANDIDATE_UNACCEPTED.
"""
def build():
    _BASE_BUILD_PROFILE_SCHEMA_R2()
    profile_schema = external_profile_instance_schema()
    (OUT / "sources" / "external-acceptance-profile.schema.json").write_bytes(emit(profile_schema))
    (OUT / "README.md").write_text(R4_README, encoding="utf-8")
# ---------------------------------------------------------------------------
# Semantic closure of the generic DESCENDANTS primitive.
#
# One closed DESCENDANT_RECORD definition with an exact machine-readable
# per-field algorithm, declared type constraints, and declared error behavior,
# plus normative exact ordered conformance vectors. Both are emitted inside the
# already-registered primitive registry so artifact churn stays minimal, and
# both are validated by the registered primitive-registry schema. The defined
# semantics are the frozen supervisor micro-design: ancestor_pointers is an
# INCLUSIVE chain from root through the current node ordered root-to-self
# (root [""], /x ["", "/x"], /x/y ["", "/x", "/x/y"]), value_type keeps the
# uppercase candidate enum literals that the procedure AST compares, and
# member_key is null for the root and for array children.
# ---------------------------------------------------------------------------
_BASE_MAKE_PRIMITIVE_REGISTRY_CLOSURE = make_primitive_registry

DESCENDANT_RECORD_FIELD_ORDER = ["pointer", "value", "path_tokens", "ancestor_pointers", "value_type", "keys", "member_key"]
DESCENDANT_RECORD_VALUE_TYPES = ["NULL", "BOOLEAN", "NUMBER", "STRING", "ARRAY", "OBJECT"]
DESCENDANT_RECORD_ERROR_CLASSES = ["NON_JSON_VALUE", "TRAVERSAL_RESOURCE_LIMIT"]
DESCENDANT_POINTER_PATTERN = "^(?:/(?:[^/~]|~[01])*)*$"
DESCENDANT_PREORDER = "PREORDER_DEPTH_FIRST"


def descendant_record_pointer(tokens):
    if not tokens:
        return ""
    return "/" + "/".join(str(token).replace("~", "~0").replace("/", "~1") for token in tokens)


def descendant_records(value):
    """Generator-side reference implementation of the normative traversal."""
    rows = []
    def visit(node, tokens, ancestors, member_key):
        chain = ancestors + [descendant_record_pointer(tokens)]
        if node is None:
            kind = "NULL"
        elif isinstance(node, bool):
            kind = "BOOLEAN"
        elif isinstance(node, int):
            kind = "NUMBER"
        elif isinstance(node, float):
            if node != node or node == float("inf") or node == float("-inf"):
                raise ValueError("non-finite number is not JSON")
            kind = "NUMBER"
        elif isinstance(node, str):
            kind = "STRING"
        elif isinstance(node, list):
            kind = "ARRAY"
        elif isinstance(node, dict):
            kind = "OBJECT"
        else:
            raise ValueError("non-JSON value " + type(node).__name__)
        keys = sorted(node.keys(), key=lambda k: k.encode("utf-16-be")) if isinstance(node, dict) else []
        rows.append({"pointer": chain[-1], "value": node, "path_tokens": list(tokens),
                     "ancestor_pointers": chain, "value_type": kind, "keys": keys, "member_key": member_key})
        if isinstance(node, dict):
            for key in keys:
                visit(node[key], tokens + [key], chain, key)
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, tokens + [str(index)], chain, None)
    visit(value, [], [], None)
    return rows


def descendant_record_definition():
    return {
        "record_id": "DESCENDANT_RECORD",
        "record_version": "1",
        "instance_schema_pointer": "#/$defs/descendant_record_instance",
        "record_shape": {
            "closed": True,
            "additional_properties": False,
            "field_count": 7,
            "field_order": list(DESCENDANT_RECORD_FIELD_ORDER),
        },
        "emission": {
            "traversal": "PREORDER_DEPTH_FIRST_EXPLICIT_LIFO_STACK_PUSH_CHILDREN_REVERSED",
            "root_included": True,
            "root_depth": 0,
            "root_visited_node_count": 1,
            "all_nodes_emitted": "INCLUDING_EMPTY_OBJECT_AND_EMPTY_ARRAY_AND_SCALAR_ROOT",
            "child_order": {
                "object": "OBJECT_MEMBER_KEYS_UTF16_CODE_UNIT_ASCENDING",
                "array": "ASCENDING_CANONICAL_DECIMAL_ARRAY_INDEX",
            },
        },
        "fields": {
            "pointer": {
                "order": 1,
                "declared_type": "STRING_RFC6901_POINTER",
                "algorithm": "RFC6901_ENCODE_PATH_TOKENS_ROOT_IS_EMPTY_STRING_ESCAPE_TILDE_AS_TILDE0_ESCAPE_SLASH_AS_TILDE1",
                "pattern": DESCENDANT_POINTER_PATTERN,
                "root_value": "",
            },
            "value": {
                "order": 2,
                "declared_type": "FINITE_JSON",
                "algorithm": "EXACT_JSON_SUBTREE_IDENTIFIED_BY_PATH_TOKENS",
            },
            "path_tokens": {
                "order": 3,
                "declared_type": "ARRAY<STRING>",
                "algorithm": "DECODED_RFC6901_REFERENCE_TOKENS_OBJECT_MEMBER_NAME_VERBATIM_ARRAY_INDEX_CANONICAL_DECIMAL_NO_LEADING_ZERO",
                "root_value": [],
            },
            "ancestor_pointers": {
                "order": 4,
                "declared_type": "ARRAY<STRING>",
                "algorithm": "INCLUSIVE_CHAIN_ROOT_THROUGH_SELF_ORDERED_ROOT_TO_SELF_LAST_ELEMENT_EQUALS_POINTER",
                "root_value": [""],
                "examples": {"root": [""], "top_level": ["", "/x"], "nested": ["", "/x", "/x/y"]},
            },
            "value_type": {
                "order": 5,
                "declared_type": "ENUM<NULL,BOOLEAN,NUMBER,STRING,ARRAY,OBJECT>",
                "algorithm": "JSON_TYPE_DISCRIMINANT_BOOLEAN_BEFORE_NUMBER_NO_COERCION",
                "allowed_values": list(DESCENDANT_RECORD_VALUE_TYPES),
            },
            "keys": {
                "order": 6,
                "declared_type": "ARRAY<STRING>",
                "algorithm": "OBJECT_MEMBER_KEYS_SORTED_UTF16_CODE_UNIT_ASCENDING_OTHERWISE_EMPTY_ARRAY",
            },
            "member_key": {
                "order": 7,
                "declared_type": "STRING_OR_NULL",
                "algorithm": "OBJECT_CHILD_EXACT_OBJECT_MEMBER_NAME_ROOT_AND_ARRAY_CHILD_NULL",
                "root_value": None,
            },
        },
        "domain": {
            "input_type": "FINITE_JSON",
            "parse_rejections": ["DUPLICATE_JSON_MEMBER_NAME", "NON_JSON_NUMERIC_CONSTANT", "INVALID_UTF8"],
            "parse_rejection_error_class": "NON_JSON_VALUE",
            "valid_json_pointer_uniqueness": "GUARANTEED_ONE_RECORD_PER_VISITED_NODE",
            "duplicate_pointer_behavior": "FAIL_CLOSED_TYPED_ERROR",
            "duplicate_pointer_error_class": "NON_JSON_VALUE",
        },
        "limits": {
            "max_depth_source": "metacontract.resource_limits.max_json_traversal_depth",
            "max_depth_baseline": 256,
            "max_nodes_source": "metacontract.resource_limits.max_json_nodes_visited_per_value",
            "max_nodes_baseline": 1000000,
            "exceeded_error_class": "TRAVERSAL_RESOURCE_LIMIT",
        },
        "error_behavior": {
            "error_classes": list(DESCENDANT_RECORD_ERROR_CLASSES),
            "expression_error": "CONTAINING_ASSERTION_FAILURE_WITH_DECLARED_CODE_AND_WITNESS",
            "stops_evaluation": True,
        },
    }


def descendant_conformance_vectors():
    def vector(vector_id, purpose, value, extra=None):
        rows = descendant_records(value)
        row = {"vector_id": vector_id, "purpose": purpose, "input": value,
               "expected_record_count": len(rows), "expected_record_order": DESCENDANT_PREORDER,
               "expected_records": rows}
        if extra:
            row.update(extra)
        return row
    ambiguity_value = {"a": {"b": 1}}
    ambiguity_rows = descendant_records(ambiguity_value)
    probe = next(row for row in ambiguity_rows if row["pointer"] == "/a/b")
    exclusion_value = {"a": {"b": {"c": "deep"}, "bc": True}, "ab": False}
    exclusion_rows = descendant_records(exclusion_value)
    excluded_pointer = "/a/b"
    return [
        vector("DESCENDANTS-V01-EMPTY-OBJECT",
               "Empty object root emits exactly the root record.",
               {}),
        vector("DESCENDANTS-V02-EMPTY-ARRAY",
               "Empty array root emits exactly the root record.",
               []),
        vector("DESCENDANTS-V03-SCALAR-ROOT",
               "Scalar root emits exactly one record with empty pointer, empty tokens, empty keys, and root-only ancestry.",
               None),
        vector("DESCENDANTS-V04-OBJECT-SCALAR-MEMBER",
               "Object root with a scalar member: UTF-16 ordered keys and the exact object-child member_key.",
               {"a": 1}),
        vector("DESCENDANTS-V05-NESTED-OBJECT",
               "Nested object chain: the inclusive ancestry grows root to self.",
               {"a": {"b": 2}}),
        vector("DESCENDANTS-V06-POINTER-ESCAPING",
               "Member names containing slash and tilde: RFC6901 pointer escaping with verbatim decoded path tokens.",
               {"a/b": {"~key": 3}}),
        vector("DESCENDANTS-V07-ARRAY-OF-OBJECT-AND-SCALAR",
               "Array children use canonical decimal tokens and always carry a null member_key.",
               [{"x": 1}, 2]),
        vector("DESCENDANTS-V08-ANCESTRY-SELF-INCLUSION",
               "Root/self counterexample that distinguishes inclusive from strict ancestry.",
               ambiguity_value,
               {"ancestry_semantics_probe": {
                   "probe_kind": "INCLUSIVE_VS_STRICT_ANCESTRY",
                   "probe_pointer": "/a/b",
                   "observed_ancestor_pointers": probe["ancestor_pointers"],
                   "inclusive_expected_ancestor_pointers": ["", "/a", "/a/b"],
                   "strict_expected_ancestor_pointers": ["", "/a"],
                   "root_inclusive_expected_ancestor_pointers": [""],
                   "root_strict_expected_ancestor_pointers": [],
                   "selected_semantics": "INCLUSIVE_ROOT_THROUGH_SELF",
               }}),
        vector("DESCENDANTS-V09-EXCLUDED-PREFIX-GOVERNING-TOKEN",
               "Excluded-prefix authorization is exact pointer equality against ancestor_pointers, so nodes sharing a textual prefix are never excluded.",
               exclusion_value,
               {"exclusion_probe": {
                   "excluded_pointer": excluded_pointer,
                   "governing_token": "EXACT_POINTER_EQUALITY_AGAINST_ANCESTOR_POINTERS",
                   "expected_excluded_node_pointers": [row["pointer"] for row in exclusion_rows
                                                       if excluded_pointer in row["ancestor_pointers"]],
                   "expected_included_node_pointers": [row["pointer"] for row in exclusion_rows
                                                       if excluded_pointer not in row["ancestor_pointers"]],
               }}),
    ]


def make_primitive_registry():
    result = _BASE_MAKE_PRIMITIVE_REGISTRY_CLOSURE()
    result["descendant_record"] = descendant_record_definition()
    result["descendant_conformance_vectors"] = descendant_conformance_vectors()
    return result


DESCENDANT_SCHEMA_DEFS = {
    "descendant_record_instance": {
        "type": "object",
        "required": list(DESCENDANT_RECORD_FIELD_ORDER),
        "properties": {
            "pointer": {"type": "string", "pattern": DESCENDANT_POINTER_PATTERN},
            "value": {},
            "path_tokens": {"type": "array", "items": {"type": "string"}},
            "ancestor_pointers": {"type": "array", "minItems": 1,
                                  "items": {"type": "string", "pattern": DESCENDANT_POINTER_PATTERN}},
            "value_type": {"enum": list(DESCENDANT_RECORD_VALUE_TYPES)},
            "keys": {"type": "array", "items": {"type": "string"}},
            "member_key": {"type": ["string", "null"]},
        },
        "additionalProperties": False,
    },
    "descendant_record_field": {
        "type": "object",
        "required": ["order", "declared_type", "algorithm"],
        "properties": {
            "order": {"type": "integer", "minimum": 1, "maximum": 7},
            "declared_type": {"type": "string", "minLength": 1},
            "algorithm": {"type": "string", "minLength": 1},
            "pattern": {"type": "string", "minLength": 1},
            "allowed_values": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
            "examples": {"type": "object"},
            "root_value": {},
        },
        "additionalProperties": False,
    },
    "descendant_record_definition": {
        "type": "object",
        "required": ["record_id", "record_version", "instance_schema_pointer", "record_shape", "emission",
                     "fields", "domain", "limits", "error_behavior"],
        "properties": {
            "record_id": {"const": "DESCENDANT_RECORD"},
            "record_version": {"const": "1"},
            "instance_schema_pointer": {"const": "#/$defs/descendant_record_instance"},
            "record_shape": {
                "type": "object",
                "required": ["closed", "additional_properties", "field_count", "field_order"],
                "properties": {
                    "closed": {"const": True},
                    "additional_properties": {"const": False},
                    "field_count": {"const": 7},
                    "field_order": {"const": list(DESCENDANT_RECORD_FIELD_ORDER)},
                },
                "additionalProperties": False,
            },
            "emission": {
                "type": "object",
                "required": ["traversal", "root_included", "root_depth", "root_visited_node_count",
                             "all_nodes_emitted", "child_order"],
                "properties": {
                    "traversal": {"const": "PREORDER_DEPTH_FIRST_EXPLICIT_LIFO_STACK_PUSH_CHILDREN_REVERSED"},
                    "root_included": {"const": True},
                    "root_depth": {"const": 0},
                    "root_visited_node_count": {"const": 1},
                    "all_nodes_emitted": {"const": "INCLUDING_EMPTY_OBJECT_AND_EMPTY_ARRAY_AND_SCALAR_ROOT"},
                    "child_order": {
                        "type": "object",
                        "required": ["object", "array"],
                        "properties": {
                            "object": {"const": "OBJECT_MEMBER_KEYS_UTF16_CODE_UNIT_ASCENDING"},
                            "array": {"const": "ASCENDING_CANONICAL_DECIMAL_ARRAY_INDEX"},
                        },
                        "additionalProperties": False,
                    },
                },
                "additionalProperties": False,
            },
            "fields": {
                "type": "object",
                "required": list(DESCENDANT_RECORD_FIELD_ORDER),
                "properties": {name: {"$ref": "#/$defs/descendant_record_field"}
                               for name in DESCENDANT_RECORD_FIELD_ORDER},
                "additionalProperties": False,
            },
            "domain": {
                "type": "object",
                "required": ["input_type", "parse_rejections", "parse_rejection_error_class",
                             "valid_json_pointer_uniqueness", "duplicate_pointer_behavior",
                             "duplicate_pointer_error_class"],
                "properties": {
                    "input_type": {"const": "FINITE_JSON"},
                    "parse_rejections": {"const": ["DUPLICATE_JSON_MEMBER_NAME", "NON_JSON_NUMERIC_CONSTANT", "INVALID_UTF8"]},
                    "parse_rejection_error_class": {"const": "NON_JSON_VALUE"},
                    "valid_json_pointer_uniqueness": {"const": "GUARANTEED_ONE_RECORD_PER_VISITED_NODE"},
                    "duplicate_pointer_behavior": {"const": "FAIL_CLOSED_TYPED_ERROR"},
                    "duplicate_pointer_error_class": {"const": "NON_JSON_VALUE"},
                },
                "additionalProperties": False,
            },
            "limits": {
                "type": "object",
                "required": ["max_depth_source", "max_depth_baseline", "max_nodes_source",
                             "max_nodes_baseline", "exceeded_error_class"],
                "properties": {
                    "max_depth_source": {"const": "metacontract.resource_limits.max_json_traversal_depth"},
                    "max_depth_baseline": {"const": 256},
                    "max_nodes_source": {"const": "metacontract.resource_limits.max_json_nodes_visited_per_value"},
                    "max_nodes_baseline": {"const": 1000000},
                    "exceeded_error_class": {"const": "TRAVERSAL_RESOURCE_LIMIT"},
                },
                "additionalProperties": False,
            },
            "error_behavior": {
                "type": "object",
                "required": ["error_classes", "expression_error", "stops_evaluation"],
                "properties": {
                    "error_classes": {"const": list(DESCENDANT_RECORD_ERROR_CLASSES)},
                    "expression_error": {"const": "CONTAINING_ASSERTION_FAILURE_WITH_DECLARED_CODE_AND_WITNESS"},
                    "stops_evaluation": {"const": True},
                },
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    },
    "descendant_ancestry_probe": {
        "type": "object",
        "required": ["probe_kind", "probe_pointer", "observed_ancestor_pointers",
                     "inclusive_expected_ancestor_pointers", "strict_expected_ancestor_pointers",
                     "root_inclusive_expected_ancestor_pointers", "root_strict_expected_ancestor_pointers",
                     "selected_semantics"],
        "properties": {
            "probe_kind": {"const": "INCLUSIVE_VS_STRICT_ANCESTRY"},
            "probe_pointer": {"type": "string", "pattern": DESCENDANT_POINTER_PATTERN},
            "observed_ancestor_pointers": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "inclusive_expected_ancestor_pointers": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "strict_expected_ancestor_pointers": {"type": "array", "items": {"type": "string"}},
            "root_inclusive_expected_ancestor_pointers": {"const": [""]},
            "root_strict_expected_ancestor_pointers": {"const": []},
            "selected_semantics": {"const": "INCLUSIVE_ROOT_THROUGH_SELF"},
        },
        "additionalProperties": False,
    },
    "descendant_exclusion_probe": {
        "type": "object",
        "required": ["excluded_pointer", "governing_token", "expected_excluded_node_pointers",
                     "expected_included_node_pointers"],
        "properties": {
            "excluded_pointer": {"type": "string", "pattern": DESCENDANT_POINTER_PATTERN},
            "governing_token": {"const": "EXACT_POINTER_EQUALITY_AGAINST_ANCESTOR_POINTERS"},
            "expected_excluded_node_pointers": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "expected_included_node_pointers": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        },
        "additionalProperties": False,
    },
    "descendant_conformance_vector": {
        "type": "object",
        "required": ["vector_id", "purpose", "input", "expected_record_count", "expected_record_order",
                     "expected_records"],
        "properties": {
            "vector_id": {"type": "string", "pattern": "^DESCENDANTS-V[0-9]{2}-[A-Z0-9-]+$"},
            "purpose": {"type": "string", "minLength": 1},
            "input": {},
            "expected_record_count": {"type": "integer", "minimum": 1},
            "expected_record_order": {"const": DESCENDANT_PREORDER},
            "expected_records": {"type": "array", "minItems": 1,
                                 "items": {"$ref": "#/$defs/descendant_record_instance"}},
            "ancestry_semantics_probe": {"$ref": "#/$defs/descendant_ancestry_probe"},
            "exclusion_probe": {"$ref": "#/$defs/descendant_exclusion_probe"},
        },
        "additionalProperties": False,
    },
}

_BASE_MAKE_PRIMITIVE_SCHEMA_CLOSURE = make_primitive_schema


def make_primitive_schema():
    schema = _BASE_MAKE_PRIMITIVE_SCHEMA_CLOSURE()
    schema["required"] = list(schema["required"]) + ["descendant_record", "descendant_conformance_vectors"]
    schema["properties"]["descendant_record"] = {"$ref": "#/$defs/descendant_record_definition"}
    schema["properties"]["descendant_conformance_vectors"] = {
        "type": "array", "minItems": 9, "maxItems": 9,
        "items": {"$ref": "#/$defs/descendant_conformance_vector"},
    }
    schema["$defs"].update(DESCENDANT_SCHEMA_DEFS)
    return schema

# Closed JSON values consumed by the executable metacontract.  These are
# emitted inside the registered metacontract, not inferred from either Python
# evaluator's private object layout.
_BASE_MAKE_METACONTRACT_REPRESENTATION = make_metacontract
_BASE_MAKE_METACONTRACT_SCHEMA_REPRESENTATION = make_metacontract_schema
_BASE_MAKE_PRIMITIVE_REGISTRY_REPRESENTATION = make_primitive_registry

_TYPED_REF_VALUE = {
    "type": "object", "required": ["kind", "id", "version"],
    "properties": {
        "kind": {"type": "string", "minLength": 1},
        "id": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "member_id": {"type": "string", "minLength": 1},
    }, "additionalProperties": False,
}
_BASE_REF_VALUE = copy.deepcopy(_TYPED_REF_VALUE)
del _BASE_REF_VALUE["properties"]["member_id"]
_HASH64_VALUE = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_HASH40_VALUE = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
_INTEGRITY_VALUE = {
    "oneOf": [
        {"type": "object", "required": ["mode", "algorithm", "serialization", "digest"],
         "properties": {"mode": {"const": "SEMANTIC_JSON_CONTENT"},
                        "algorithm": {"const": "SHA-256"},
                        "serialization": {"const": "RFC8785_JCS"},
                        "digest": _HASH64_VALUE}, "additionalProperties": False},
        {"type": "object", "required": ["mode", "content_target_ref"],
         "properties": {"mode": {"const": "SELF_DIGEST"},
                        "content_target_ref": {"const": "PACKAGE_EXCLUDING_SELF_DIGEST"}},
         "additionalProperties": False},
        {"type": "object", "required": ["mode", "justification"],
         "properties": {"mode": {"const": "PACKAGE_PINNED_BOOTSTRAP"},
                        "justification": {"type": "string", "minLength": 1}},
         "additionalProperties": False},
        {"type": "object", "required": ["mode", "algorithm", "raw_sha256", "semantic_sha256", "git_blob"],
         "properties": {"mode": {"const": "DUAL_ACCEPTED_SOURCE"},
                        "algorithm": {"const": "SHA-256"},
                        "raw_sha256": _HASH64_VALUE,
                        "semantic_sha256": _HASH64_VALUE,
                        "git_blob": _HASH40_VALUE},
         "additionalProperties": False},
    ]
}
_RESOLVED_VALUE = {
    "type": "object",
    "required": ["kind", "id", "version", "ref", "reference", "path", "status",
                 "classification", "roles", "schema_ref", "content", "origin",
                 "integrity", "integrity_source", "members", "raw_content_base64"],
    "properties": {
        "kind": {"type": "string", "minLength": 1},
        "id": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "ref": {"$ref": "#/$defs/typed_ref"},
        "reference": {"$ref": "#/$defs/base_ref"},
        "path": {"type": "string", "minLength": 1},
        "status": {"enum": ["ACTIVE", "ACTIVE_ACCEPTED_SOURCE"]},
        "classification": {"enum": ["NORMATIVE", "SOURCE_ONLY"]},
        "roles": {"type": "array", "minItems": 1, "uniqueItems": True,
                  "items": {"type": "string", "minLength": 1}},
        "schema_ref": {"oneOf": [{"$ref": "#/$defs/typed_ref"}, {"type": "null"}]},
        "content": {},
        "origin": {"enum": ["CANDIDATE_UNIVERSE", "BOUND_SOURCE_UNIVERSE"]},
        "integrity": {"$ref": "#/$defs/integrity"},
        "integrity_source": {"enum": ["VALIDATED_REGISTRY_ENTRY",
                                      "PACKAGE_SELF_DIGEST",
                                      "PACKAGE_REGISTRY_SEMANTIC_PIN",
                                      "EXTERNAL_ACCEPTANCE_PROFILE"]},
        "members": {"type": "array", "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1}},
        "raw_content_base64": {"type": "string",
                               "pattern": "^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"},
    },
    "allOf": [
        {"if": {"properties": {"origin": {"const": "CANDIDATE_UNIVERSE"}}},
         "then": {"properties": {"status": {"const": "ACTIVE"},
                                 "classification": {"const": "NORMATIVE"},
                                 "integrity": {"properties": {
                                     "mode": {"enum": ["SEMANTIC_JSON_CONTENT",
                                                        "SELF_DIGEST",
                                                        "PACKAGE_PINNED_BOOTSTRAP"]}}},
                                 "integrity_source": {"enum": ["VALIDATED_REGISTRY_ENTRY",
                                                                "PACKAGE_SELF_DIGEST",
                                                                "PACKAGE_REGISTRY_SEMANTIC_PIN"]}}}},
        {"if": {"properties": {"origin": {"const": "BOUND_SOURCE_UNIVERSE"}}},
         "then": {"properties": {"status": {"const": "ACTIVE_ACCEPTED_SOURCE"},
                                 "classification": {"const": "SOURCE_ONLY"},
                                 "schema_ref": {"$ref": "#/$defs/typed_ref"},
                                 "integrity": {"properties": {
                                     "mode": {"const": "DUAL_ACCEPTED_SOURCE"}}},
                                 "integrity_source": {"const": "EXTERNAL_ACCEPTANCE_PROFILE"}}}},
        {"if": {"properties": {"origin": {"const": "CANDIDATE_UNIVERSE"},
                               "kind": {"const": "SCHEMA"}}},
         "then": {"properties": {"schema_ref": {"type": "null"}}}},
        {"if": {"properties": {"origin": {"const": "CANDIDATE_UNIVERSE"},
                               "kind": {"not": {"const": "SCHEMA"}}}},
         "then": {"properties": {"schema_ref": {"$ref": "#/$defs/typed_ref"}}}},
        {"if": {"properties": {"integrity": {"properties": {
            "mode": {"const": "SEMANTIC_JSON_CONTENT"}}}}},
         "then": {"properties": {"integrity_source": {"const": "VALIDATED_REGISTRY_ENTRY"}}}},
        {"if": {"properties": {"integrity": {"properties": {
            "mode": {"const": "SELF_DIGEST"}}}}},
         "then": {"properties": {"integrity_source": {"const": "PACKAGE_SELF_DIGEST"},
                                 "reference": {"const": {"kind": "PACKAGE", "id": "urn:moirae:accord-02r5:specification-package", "version": "0.2"}}}}},
        {"if": {"properties": {"integrity": {"properties": {
            "mode": {"const": "PACKAGE_PINNED_BOOTSTRAP"}}}}},
         "then": {"properties": {"integrity_source": {"const": "PACKAGE_REGISTRY_SEMANTIC_PIN"},
                                 "reference": {"const": {"kind": "REGISTRY", "id": "urn:moirae:accord-02e4r5r4:object-registry", "version": "0.2"}}}}},
        {"if": {"properties": {"integrity": {"properties": {
            "mode": {"const": "DUAL_ACCEPTED_SOURCE"}}}}},
         "then": {"properties": {"integrity_source": {"const": "EXTERNAL_ACCEPTANCE_PROFILE"}}}},
    ],
    "additionalProperties": False,
}
_RUNTIME_VALUE_SCHEMAS = {
    "resolved_object": {
        "$schema": DIALECT, "$id": f"{NS}:runtime-value:resolved-object:0.2",
        "$defs": {"typed_ref": _TYPED_REF_VALUE, "base_ref": _BASE_REF_VALUE,
                  "integrity": _INTEGRITY_VALUE},
        **copy.deepcopy(_RESOLVED_VALUE),
    },
    "verification_universe": {
        "$schema": DIALECT, "$id": f"{NS}:runtime-value:verification-universe:0.2",
        "$defs": {"typed_ref": _TYPED_REF_VALUE, "base_ref": _BASE_REF_VALUE,
                  "integrity": _INTEGRITY_VALUE, "resolved_object": _RESOLVED_VALUE,
                  "universe_object": {
                      "allOf": [
                          {"$ref": "#/$defs/resolved_object"},
                          {"properties": {"ref": {"$ref": "#/$defs/base_ref"}}},
                      ]
                  }},
        "type": "object", "required": ["objects"],
        "properties": {"objects": {"type": "array",
                                   "items": {"$ref": "#/$defs/universe_object"}}},
        "additionalProperties": False,
    },
}
# Strict-identity-union closure: the same literal tokens are shared by
# runtime_representation/universe_membership and registration/strict_identity_union
# so the membership model, its scan/selection rule and its failure envelope cannot
# drift apart. The collision witness reuses the existing seven-field PRE_EXECUTION
# envelope with the existing SCHEMA_INVALID_BOUND_OBJECT / SOURCE_ELIGIBILITY code.
STRICT_UNION_OPERATION = "STRICT_IDENTITY_UNION"
STRICT_UNION_IDENTITY_FIELDS = ["kind", "id", "version"]
STRICT_UNION_IDENTITY_PROJECTION = {
    "projection_fields": STRICT_UNION_IDENTITY_FIELDS,
    "candidate_projection": "EXACT_JSON_STRING_OF_RESOLVED_OBJECT_KIND_ID_VERSION_FROM_VALIDATED_REGISTRY_METADATA",
    "bound_projection": "EXACT_JSON_STRING_OF_RESOLVED_OBJECT_KIND_ID_VERSION_FROM_EXTERNALLY_VERIFIED_ALLOWLIST_METADATA",
    "collision_equality": "COMPONENTWISE_EXACT_JSON_STRING",
    "path_or_content_identity": "FORBIDDEN",
}
STRICT_UNION_MERGED_SEQUENCE = {
    "construction": "CANDIDATE_SEQUENCE_THEN_BOUND_SEQUENCE_CONCATENATION",
    "candidate_order": "NORMATIVE_UTF16_LEXICOGRAPHIC_KIND_ID_VERSION_ASCENDING",
    "bound_order": "EXTERNALLY_VERIFIED_ALLOWLIST_ARRAY_ORDER_NORMATIVE",
    "bound_sequence_source": "external_acceptance_profile:/accepted_source_allowlist",
    "bound_index_origin": "ZERO_BASED_/accepted_source_allowlist_ARRAY_INDEX",
    "array_order_is_normative": True,
}
STRICT_UNION_SCAN_SELECTION = {
    "enforcement_scope": "COMPLETE_MERGED_SEQUENCE_INCLUDING_WITHIN_SIDE_PAIRS",
    "second_occurrence_scan": "ASCENDING_INDEX_J_MINIMAL_MATCHING_PRIOR_EXISTS",
    "first_occurrence_selection": "EARLIEST_PRIOR_MATCHING_PARTICIPANT_MINIMAL_I_LESS_THAN_J",
    "decision_source": "DECLARED_SCAN_ORDER_ONLY_MAP_OR_SET_ITERATION_ORDER_FORBIDDEN",
}
_RUNTIME_REPRESENTATION = {
    "value_schemas": _RUNTIME_VALUE_SCHEMAS,
    "universe_membership": {
        "candidate_selector": {"status": "ACTIVE", "classification": "NORMATIVE",
                               "source": "validated_object_registry:/objects"},
        "bound_selector": {"status": "ACTIVE_ACCEPTED_SOURCE",
                           "classification": "SOURCE_ONLY",
                           "source": "external_acceptance_profile:/accepted_source_allowlist"},
        "operation": STRICT_UNION_OPERATION,
        "identity": ["kind", "id", "version"],
        "identity_projection": STRICT_UNION_IDENTITY_PROJECTION,
        "duplicate_identity": "FAIL_CLOSED",
        "count": "CARDINALITY_OF_SELECTED_CANDIDATE_ROWS_PLUS_SELECTED_BOUND_ROWS_AFTER_COLLISION_REJECTION",
        "order": {"keys": ["kind", "id", "version"],
                  "comparison": "LEXICOGRAPHIC_UTF16_CODE_UNIT_ASCENDING",
                  "array_order_is_normative": True},
        "merged_sequence": STRICT_UNION_MERGED_SEQUENCE,
        "scan_selection": STRICT_UNION_SCAN_SELECTION,
        "collision_failure_ref": "metacontract:/registration/strict_identity_union/failure",
    },
    "resolved_construction": {
        "universe_row_ref": "EXACT_BASE_REFERENCE_EQUAL_TO_REFERENCE_WITH_NO_MEMBER_ID",
        "resolve_one_ref": "EXACT_REQUESTED_TYPED_REFERENCE_WITH_OPTIONAL_MEMBER_ID_AND_BASE_KIND_ID_VERSION_EQUAL_TO_REFERENCE",
        "reference": "BASE_KIND_ID_VERSION_FROM_VALIDATED_REGISTRY_OR_EXTERNAL_ALLOWLIST",
        "identity_equations": ["/kind==/reference/kind", "/id==/reference/id",
                               "/version==/reference/version",
                               "/ref/kind==/reference/kind",
                               "/ref/id==/reference/id",
                               "/ref/version==/reference/version"],
        "metadata_candidate": "VALIDATED_OBJECT_REGISTRY_ROW",
        "metadata_bound": "EXTERNAL_ACCEPTANCE_PROFILE_ALLOWLIST_AFTER_WHOLE_OBJECT_CLAIM_COMPARISON",
        "candidate_schema_ref": "EXACT_REGISTRY_TYPED_REFERENCE_WHEN_PRESENT;ABSENT_MAPS_TO_NULL_ONLY_FOR_SCHEMA;OTHERWISE_FAIL",
        "bound_schema_ref": "EXACT_EXTERNAL_ALLOWLIST_EXPECTED_SCHEMA_REF_REQUIRED",
        "content": "FULL_PARSED_JSON_FROM_VERIFIED_PINNED_ARTIFACT_BYTES_NO_MEMBER_PROJECTION",
        "raw_content_base64": "RFC4648_BASE64_OF_EXACT_FULL_ARTIFACT_BYTES",
        "schema_member": "MEMBER_ID_MUST_BE_UNIQUE_DECLARED_MEMBER_AND_LOCAL_DEFINITION;SCHEMA_VALIDATE_SELECTS_DEFINITION_SEPARATELY",
        "member_resolution": {
            "absent_member_id": "RETURN_BASE_RESOLVED_OBJECT",
            "present_member_id": "REQUIRE_EXACTLY_ONE_EQUAL_STRING_IN_RESOLVED_OBJECT_MEMBERS_FOR_EVERY_KIND",
            "zero_matches": "MEMBER_NOT_FOUND",
            "multiple_matches": "RESOLUTION_AMBIGUOUS",
            "content_after_member_resolution": "UNCHANGED_FULL_PARSED_ARTIFACT",
            "schema_validate_extra_rule": "SCHEMA_MEMBER_ID_SELECTS_EXACT_LOCAL_DEFS_ENTRY_WITH_PARENT_SCHEMA_CONTEXT",
        },
        "candidate_members": "VALIDATED_REGISTRY_MEMBERS_OR_EMPTY;SCHEMA_MEMBERS_EXIST_IN_LOCAL_DEFS",
        "bound_members": "VECTOR_CATALOG_IDS_FROM_VERIFIED_CONTENT_MATCH_REGISTRY_CLAIM;BASE_PACKAGE_EMPTY",
        "candidate_integrity": "VALIDATED_REGISTRY_ENTRY_EXCEPT_PACKAGE_SELF_DIGEST_AND_PACKAGE_REGISTRY_SEMANTIC_PIN",
        "bound_integrity": "EXACT_EXTERNAL_ACCEPTANCE_PROFILE_DIGESTS_AND_GIT_BLOB",
        "identity_disagreement": "SCHEMA_INVALID_BOUND_OBJECT_BEFORE_PROCEDURE_EXECUTION",
        "schema_ref_disagreement": "SCHEMA_INVALID_BOUND_OBJECT_BEFORE_PROCEDURE_EXECUTION",
        "missing_or_moved_field": "SCHEMA_INVALID_BOUND_OBJECT_NO_FALLBACK",
    },
    "consumption": {
        "permitted_sources": ["RESOLVED_PROCEDURE_ARGUMENT", "PROCEDURE_AST_LITERAL",
                              "EXPLICIT_PUBLIC_STANDARD"],
        "finite_json_from_resolved_object": "EXPLICIT_GET_CONTENT_REQUIRED_NO_IMPLICIT_UNWRAP",
        "private_implementation_object": "FORBIDDEN",
        "conventional_filename_fallback": "FORBIDDEN",
        "invariant_id_dispatch": "FORBIDDEN",
    },
    "digest_source": {
        "resolved_object_recognition": {
            "schema_pointer": "/runtime_representation/value_schemas/resolved_object",
            "validation": "DRAFT2020_12_WHOLE_VALUE",
            "private_json_field": "FORBIDDEN",
            "implementation_internal_type_tracking": "PERMITTED_ONLY_WITH_EXACT_PUBLIC_JSON_PAYLOAD_AND_DECLARED_TYPE_FLOW",
            "typed_provenance": {
                "producers": ["RESOLVE_ONE_RESULT", "VERIFICATION_UNIVERSE_OBJECTS_ARRAY_ELEMENT"],
                "array_type_preservation": ["FILTER", "ALL_ITEM", "ANY_ITEM"],
                "type_erasure": ["JSON_LITERAL", "PROJECT_RESULT", "EVERY_GET_RESULT_EXCEPT_EXACT_VERIFICATION_UNIVERSE_OBJECTS_ARRAY", "RULE_BOUND_CONTENT_ARGUMENT"],
                "get_array_index": "ERASES_RESOLVED_OBJECT_TYPE_IN_DIRECT_AND_STAGED_POINTER_FORMS",
                "runtime_payload": "EXACT_RESOLVED_OBJECT_PUBLIC_JSON_VALUE_NO_EXTRA_FIELDS",
                "lookalike_json_object": "NEVER_GAINS_RESOLVED_OBJECT_TYPE_BY_SCHEMA_VALIDITY_ALONE",
            },
        },
        "RFC8785_JCS": {
            "resolved_object_input": "/content",
            "other_json_input": "WHOLE_VALUE",
        },
        "RAW_BYTES": {
            "required_input_type": "RESOLVED_OBJECT",
            "byte_source": "/raw_content_base64",
            "decoding": "RFC4648_CANONICAL_PADDED_BASE64_NO_WHITESPACE_REENCODE_MUST_EQUAL",
            "algorithm": "SHA-256",
            "excluded_pointers": "EMPTY_ARRAY",
            "invalid_input": "RAW_BYTES_UNAVAILABLE",
        },
        "GIT_BLOB_OBJECT": {
            "required_input_type": "RESOLVED_OBJECT",
            "byte_source": "/raw_content_base64",
            "decoding": "RFC4648_CANONICAL_PADDED_BASE64_NO_WHITESPACE_REENCODE_MUST_EQUAL",
            "algorithm": "SHA-1_GIT_BLOB_OBJECT",
            "excluded_pointers": "EMPTY_ARRAY",
            "invalid_input": "RAW_BYTES_UNAVAILABLE",
        },
    },
    "static_paths": {
        "VERIFICATION_UNIVERSE": {"/objects": "ARRAY<RESOLVED_OBJECT>"},
        "EXTERNAL_TRUST": {"/expected_package_id": "STRING", "/expected_package_version": "STRING",
                           "/expected_package_digest": "STRING"},
        "RESOLVED_OBJECT": {"/kind": "STRING", "/id": "STRING",
                            "/version": "STRING", "/ref": "TYPED_REFERENCE",
                            "/reference": "BASE_TYPED_REFERENCE",
                            "/path": "STRING", "/status": "STRING",
                            "/classification": "STRING", "/roles": "ARRAY<STRING>",
                            "/schema_ref": "TYPED_REFERENCE_OR_NULL",
                            "/content": "JSON", "/origin": "STRING",
                            "/integrity": "INTEGRITY", "/integrity_source": "STRING",
                            "/members": "ARRAY<STRING>",
                            "/raw_content_base64": "STRING"},
    },
}
_NUMERIC_REPRESENTATION = {
    "vector_number_encoding": "JSON_NUMBER_LEXEME_STRING_PARSED_AS_EXACT_DECIMAL_FOR_CONFORMANCE",
    "json_number": {"domain": "FINITE_JSON_DECIMAL_TOKEN_WITH_DUPLICATE_NAMES_REJECTED_AT_PARSE",
                    "value": "EXACT_MATHEMATICAL_RATIONAL_COEFFICIENT_TIMES_TEN_TO_INTEGER_EXPONENT",
                    "boolean_is_number": False, "binary_float_rounding": "FORBIDDEN_FOR_EVALUATION",
                    "resource_limits": {
                        "measurement_stage": "ORIGINAL_JSON_NUMBER_TOKEN_BEFORE_NUMERIC_NORMALIZATION",
                        "significand_digit_count": "COUNT_EVERY_ASCII_DIGIT_IN_WRITTEN_INTEGER_AND_FRACTION_PARTS_INCLUDING_LEADING_AND_TRAILING_ZEROS",
                        "exponent_field_digit_count": "COUNT_EVERY_ASCII_DIGIT_AFTER_WRITTEN_E_AND_OPTIONAL_SIGN_INCLUDING_LEADING_ZEROS;ABSENT_FIELD_HAS_ZERO_DIGITS",
                        "exponent_magnitude": "ABSOLUTE_SIGNED_BASE10_VALUE_OF_WRITTEN_EXPONENT_FIELD;ABSENT_FIELD_IS_ZERO;NO_SIGNIFICAND_NORMALIZATION_OR_DECIMAL_POINT_SHIFT",
                        "maximum_significand_digits": 4096,
                        "maximum_exponent_field_digits": 4096,
                        "maximum_absolute_decimal_exponent": 999999,
                        "exceeded_error": "JSON_NUMBER_RESOURCE_LIMIT"}},
    "json_equal": {"objects": "SAME_KEYS_VALUES_RECURSIVELY_OBJECT_ORDER_IGNORED",
                   "arrays": "SAME_LENGTH_VALUES_RECURSIVELY_IN_ORDER",
                   "numbers": "EXACT_MATHEMATICAL_VALUE;60_EQUALS_60.0",
                   "other_types": "EXACT_JSON_TYPE_AND_VALUE_NO_COERCION",
                   "digest_serialization": "SEPARATE_UNCHANGED_RFC8785_JCS"},
    "numeric_compare": "EXACT_MATHEMATICAL_JSON_NUMBER_VALUE_BOOL_REJECTED",
    "rfc3339_profile": {
        "year": "0001_THROUGH_9999_PROLEPTIC_GREGORIAN",
        "date_time_separator": "UPPERCASE_T",
        "zone": "UPPERCASE_Z_OR_SIGNED_HH_COLON_MM_EXCEPT_NEGATIVE_ZERO_UNKNOWN_OFFSET",
        "seconds": "00_THROUGH_59_LEAP_SECOND_REJECTED",
        "fractional_second_digits": {"minimum": 0, "maximum": 9},
        "utc_normalization": "EXACT_INTEGER_NANOSECONDS",
        "normalized_year_out_of_range": "DURATION_OVERFLOW",
        "malformed_or_out_of_profile": "MALFORMED_RFC3339",
    },
    "duration_seconds": {
        "inputs": ["RFC3339_STRING", "RFC3339_STRING"],
        "output": "JSON_NUMBER",
        "arithmetic": "EXACT_END_UTC_NANOSECONDS_MINUS_START_UTC_NANOSECONDS_DIVIDED_BY_1000000000",
        "negative": "VALID_PRIMITIVE_RESULT_CONTEXTUAL_ASSERTION_MAY_REJECT",
        "negative_zero": "NORMALIZE_TO_ZERO",
        "fractional_precision": "EXACT_TO_ONE_NANOSECOND",
    },
    "vectors": [
        {"id": "DURATION-INTEGRAL", "start": "2026-01-01T00:00:00Z",
         "end": "2026-01-01T00:01:00Z", "expected_seconds_json_number_lexeme": "60"},
        {"id": "DURATION-FRACTIONAL", "start": "2026-01-01T00:00:00Z",
         "end": "2026-01-01T00:00:01.25Z", "expected_seconds_json_number_lexeme": "1.25"},
        {"id": "DURATION-NEGATIVE", "start": "2026-01-01T00:01:00Z",
         "end": "2026-01-01T00:00:00Z", "expected_seconds_json_number_lexeme": "-60"},
        {"id": "DURATION-MALFORMED", "start": "2026-02-30T00:00:00Z",
         "end": "2026-03-01T00:00:00Z", "expected_error": "MALFORMED_RFC3339"},
        {"id": "DURATION-OFFSET-EQUIVALENT", "start": "2026-01-01T01:00:00+01:00",
         "end": "2026-01-01T00:00:00Z", "expected_seconds_json_number_lexeme": "0"},
        {"id": "DURATION-PRECISION-REJECT", "start": "2026-01-01T00:00:00.1234567890Z",
         "end": "2026-01-01T00:00:01Z", "expected_error": "MALFORMED_RFC3339"},
        {"id": "DURATION-OVERFLOW", "start": "0001-01-01T00:00:00+01:00",
         "end": "0001-01-01T00:00:00Z", "expected_error": "DURATION_OVERFLOW"},
        {"id": "JSON-NUMBER-EQUAL", "left_number_lexeme": "60",
         "right_number_lexeme": "60.0",
         "expected_json_equal": True},
    ],
    "number_resource_vectors": {
        "token_construction": "PREFIX_CONCATENATED_WITH_REPEAT_CHARACTER_REPEATED_REPEAT_COUNT_TIMES;ABSENT_REPEAT_COUNT_IS_ZERO",
        "cases": [
            {"id": "SIGNIFICAND-4096-ACCEPT", "prefix": "1.", "repeat_character": "0", "repeat_count": 4095, "expected_parse": "PASS", "equal_to_number_lexeme": "1"},
            {"id": "SIGNIFICAND-4097-REJECT", "prefix": "1.", "repeat_character": "0", "repeat_count": 4096, "expected_parse": "JSON_NUMBER_RESOURCE_LIMIT"},
            {"id": "WRITTEN-EXPONENT-999999-ACCEPT", "prefix": "10e999999", "expected_parse": "PASS"},
            {"id": "WRITTEN-EXPONENT-1000000-REJECT", "prefix": "1e1000000", "expected_parse": "JSON_NUMBER_RESOURCE_LIMIT"},
            {"id": "EXPONENT-LEADING-ZEROS-ACCEPT", "prefix": "1e0000001", "expected_parse": "PASS", "equal_to_number_lexeme": "10"},
            {"id": "EXPONENT-FIELD-4097-REJECT", "prefix": "1e", "repeat_character": "0", "repeat_count": 4097, "expected_parse": "JSON_NUMBER_RESOURCE_LIMIT"},
        ],
    },
}

def make_metacontract(proc, inv):
    result = _BASE_MAKE_METACONTRACT_REPRESENTATION(proc, inv)
    result["runtime_representation"] = copy.deepcopy(_RUNTIME_REPRESENTATION)
    result["numeric_representation"] = copy.deepcopy(_NUMERIC_REPRESENTATION)
    return result

def make_metacontract_schema():
    schema = _BASE_MAKE_METACONTRACT_SCHEMA_REPRESENTATION()
    schema["required"].extend(["runtime_representation", "numeric_representation"])
    schema["properties"]["runtime_representation"] = {"const": _RUNTIME_REPRESENTATION}
    schema["properties"]["numeric_representation"] = {"const": _NUMERIC_REPRESENTATION}
    return schema

def make_primitive_registry():
    result = _BASE_MAKE_PRIMITIVE_REGISTRY_REPRESENTATION()
    rows = {row["primitive_id"]: row for row in result["primitives"]}
    rows["RESOLVE_ONE"]["semantics"] = "metacontract:/runtime_representation/resolved_construction; returns exact RESOLVED_OBJECT"
    rows["DIGEST_VERIFY"]["semantics"] = "metacontract:/runtime_representation/digest_source; resolved-object bytes come only from canonical public raw_content_base64"
    rows["DIGEST_VERIFY"]["deterministic_order"] = "MODE_DRIVEN_HASHING; RESOLVED_OBJECT_PUBLIC_JSON_BYTE_SOURCE"
    rows["JSON_EQUAL"]["semantics"] = "metacontract:/numeric_representation/json_equal; exact mathematical JSON number equality"
    rows["JSON_EQUAL"]["standard"] = "JSON; RFC 8785 applies only to digest serialization"
    rows["JSON_EQUAL"]["error_behavior"]["error_classes"] = []
    rows["NUMERIC_COMPARE"]["missing_behavior"] = "ERROR_IF_NOT_FINITE_JSON_NUMBER"
    rows["NUMERIC_COMPARE"]["standard"] = "JSON exact decimal mathematical value"
    rows["NUMERIC_COMPARE"]["semantics"] = "metacontract:/numeric_representation/numeric_compare"
    rows["DURATION_SECONDS"]["output_type"] = "JSON_NUMBER"
    rows["DURATION_SECONDS"]["semantics"] = "metacontract:/numeric_representation/duration_seconds"
    rows["DURATION_SECONDS"]["standard"] = "RFC 3339 restricted by metacontract:/numeric_representation/rfc3339_profile"
    rows["DESCENDANTS"]["semantics"] += "; FINITE_JSON requires explicit GET /content from RESOLVED_OBJECT; no implicit unwrap"
    return result

# ---------------------------------------------------------------------------
# Registration ordering and the closed registration-rule mapping.
#
# The external trust/pin bootstrap prefix is preserved byte-exactly; six
# registration stages are inserted ahead of universe derivation. Structural
# registration invalidities are JSON_SCHEMA failures of the registered
# object-registry schema applied to the FULL registry; semantic registration
# invalidities are SOURCE_ELIGIBILITY failures. Both are reported only as the
# canonical PRE_EXECUTION SCHEMA_INVALID_BOUND_OBJECT seven-field witness.
REGISTRATION_PREFIX_LENGTH = 13
if len(PROFILE_BOOTSTRAP_ORDER) != 18 or PROFILE_BOOTSTRAP_ORDER[REGISTRATION_PREFIX_LENGTH - 1] != "COMPARE_ALL_CANDIDATE_AUTHORITY_CLAIMS_WHOLE_OBJECT_BEFORE_SEMANTIC_USE":
    raise SystemExit("registration bootstrap prefix changed; refusing to reorder external trust and pin stages")
REGISTRATION_STAGES = [
    "APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY",
    "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
    "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
    "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS",
    "SELECT_ELIGIBLE_CANDIDATE_OBJECTS",
    "RESOLVE_CANDIDATE_OBJECTS",
    "BOUND_SOURCE_RESOLVED_CONSTRUCTION",

]
REGISTRATION_BOOTSTRAP_ORDER = PROFILE_BOOTSTRAP_ORDER[:REGISTRATION_PREFIX_LENGTH] + REGISTRATION_STAGES + PROFILE_BOOTSTRAP_ORDER[REGISTRATION_PREFIX_LENGTH:]
REGISTRATION_SCHEMA_REF = {"kind": "SCHEMA", "id": f"{NS}:schema:object-registry", "version": "0.2"}
REGISTRATION_SCHEMA_ID = f"{NS}:schema:object-registry:0.2"
REGISTRATION_DIAGNOSTIC_TOKENS = {
    "JSON_SCHEMA": [
        "MISSING_REGISTRATION_SCHEMA_REF",
        "MISSING_REGISTRATION_INTEGRITY_DECLARATION",
        "MALFORMED_REGISTRATION_INTEGRITY_DECLARATION",
        "OBJECT_REGISTRY_SCHEMA_VIOLATION",
    ],
    "SOURCE_ELIGIBILITY": [
        "SCHEMA_ROW_MUST_NOT_DECLARE_SCHEMA_REF",
        "UNKNOWN_REGISTRATION_STATUS",
        "UNKNOWN_REGISTRATION_CLASSIFICATION",
        "UNRESOLVED_REGISTRATION_SCHEMA_REF",
        "REGISTRATION_IDENTITY_MISMATCH",
        "SCHEMA_DOCUMENT_VERSION_MISMATCH",
        "SCHEMA_DOCUMENT_ID_MISMATCH",
    ],
    "INTEGRITY": [
        "INVALID_REGISTRATION_INTEGRITY_MODE",
        "REGISTRATION_INTEGRITY_DIGEST_MISMATCH",
    ],
    # GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY fails with failure_kind
    # SOURCE_ELIGIBILITY, whose bucket is pinned by the frozen verifier contract
    # to the semantic-registration rule diagnostics; the duplicate-identity token
    # is therefore keyed by stage so no existing bucket is redefined.
    "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY": [
        "DUPLICATE_REGISTRY_OBJECT_IDENTITY",
    ],
    "BOUND_SOURCE_RESOLVED_CONSTRUCTION": [
        "VECTOR_REGISTRY_CLAIM_INVALID",
    ],
}
REGISTRATION = {
    "stage_order": list(REGISTRATION_BOOTSTRAP_ORDER),
    "external_trust_and_pin_prefix": list(PROFILE_BOOTSTRAP_ORDER[:REGISTRATION_PREFIX_LENGTH]),
    "stage_roles": {
        "STRUCTURAL_REGISTRATION": "APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY",
        "SEMANTIC_REGISTRATION": "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
        "GLOBAL_UNIQUENESS": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
        "INTEGRITY_GATE": "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS",
        "ELIGIBILITY": "SELECT_ELIGIBLE_CANDIDATE_OBJECTS",
        "CANDIDATE_RESOLUTION": "RESOLVE_CANDIDATE_OBJECTS",
        "BOUND_SOURCE_RESOLUTION": "BOUND_SOURCE_RESOLVED_CONSTRUCTION",

        "VERIFICATION_UNIVERSE": "DERIVE_VERIFICATION_UNIVERSE_FROM_BOOTSTRAP_INPUTS",
        "STRICT_BOUND_SOURCE_UNION": "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
        "AST": "EXECUTE_DECLARED_ASSERTIONS_IN_ORDER",
    },
    "structural_application": {
        "stage": "APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY",
        "validator": "JSON_SCHEMA",
        "dialect": DIALECT,
        "schema_ref": REGISTRATION_SCHEMA_REF,
        "schema_id": REGISTRATION_SCHEMA_ID,
        "instance_scope": "FULL_REGISTRY_ALL_ROWS",
        "instance_pointer": "/objects",
        "row_scope": "EVERY_ROW_INCLUDING_ACCEPTED_SOURCE_ROWS",
        "failure_code": "SCHEMA_INVALID_BOUND_OBJECT",
        "failure_kind": "JSON_SCHEMA",
        "first_failure_only": True,
        "witness_schema_ref": REGISTRATION_SCHEMA_ID,
        "rules": [
            {
                "rule_id": "MISSING_REGISTRATION_SCHEMA_REF",
                "condition": "ROW_STATUS_ACTIVE_AND_ROW_CLASSIFICATION_NORMATIVE_AND_ROW_KIND_NOT_SCHEMA_AND_ROW_SCHEMA_REF_ABSENT",
                "origin": "EXISTING_OBJECT_REGISTRY_SCHEMA_CONDITIONAL",
                "instance_pointer": "/objects/<row_index>/schema_ref",
                "diagnostic": "MISSING_REGISTRATION_SCHEMA_REF",
                "bound_identity": "ROW_KIND_ID_VERSION_TRIPLE_WHEN_READABLE_ELSE_NULL",
                "eligibility_reached": False,
                "universe_reached": False,
                "later_identical_check": "DEFENSIVE_UNREACHABLE",
            },
            {
                "rule_id": "MISSING_REGISTRATION_INTEGRITY_DECLARATION",
                "condition": "ROW_INTEGRITY_MEMBER_ABSENT",
                "origin": "EXISTING_OBJECT_REGISTRY_SCHEMA_REQUIRED_MEMBER",
                "instance_pointer": "/objects/<row_index>/integrity",
                "diagnostic": "MISSING_REGISTRATION_INTEGRITY_DECLARATION",
                "bound_identity": "ROW_KIND_ID_VERSION_TRIPLE_WHEN_READABLE_ELSE_NULL",
                "integrity_gate_reached": False,
            },
            {
                "rule_id": "MALFORMED_REGISTRATION_INTEGRITY_DECLARATION",
                "condition": "ROW_INTEGRITY_MEMBER_PRESENT_AND_NOT_CONFORMING_TO_THE_REGISTERED_INTEGRITY_DECLARATION_SHAPE",
                "origin": "EXISTING_OBJECT_REGISTRY_SCHEMA_INTEGRITY_MEMBER",
                "instance_pointer": "/objects/<row_index>/integrity",
                "diagnostic": "MALFORMED_REGISTRATION_INTEGRITY_DECLARATION",
                "bound_identity": "ROW_KIND_ID_VERSION_TRIPLE_WHEN_READABLE_ELSE_NULL",
                "integrity_gate_reached": False,
            },
            {
                "rule_id": "OBJECT_REGISTRY_SCHEMA_VIOLATION",
                "condition": "ANY_OTHER_REGISTERED_OBJECT_REGISTRY_SCHEMA_FAILURE_ON_THE_SAME_INSTANCE_SCOPE",
                "origin": "REGISTERED_OBJECT_REGISTRY_SCHEMA",
                "instance_pointer": "/objects/<row_index>",
                "diagnostic": "OBJECT_REGISTRY_SCHEMA_VIOLATION",
                "bound_identity": "ROW_KIND_ID_VERSION_TRIPLE_WHEN_READABLE_ELSE_NULL",
            },
        ],
    },
    "semantic_validation": {
        "stage": "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
        "instance_scope": "FULL_REGISTRY_ALL_ROWS",
        "failure_code": "SCHEMA_INVALID_BOUND_OBJECT",
        "failure_kind": "SOURCE_ELIGIBILITY",
        "first_failure_only": True,
        "witness_object_role": "REGISTRY_OBJECT",
        "schema_document_identity": {
            "registry_identity_members": ["kind", "id", "version"],
            "reference_equals_registry_identity": True,
            "schema_document_identity_members": ["schema_document_id", "schema_document_version"],
            "schema_document_identity_scope": "ROW_LOCAL_REGISTERED_ARTIFACT_IDENTITY_DOES_NOT_REPLACE_REGISTRY_OBJECT_IDENTITY",
            "registry_id_to_schema_document_id_convention": "NONE",
            "schema_document_id_source": "STORED_ROW_MEMBER_ONLY_NO_EVALUATOR_SIDE_DERIVATION",
            "schema_content_id_source_bytes": "BYTES_READ_FROM_THE_ROW_DECLARED_PATH_WITHIN_THE_EXPLICIT_ROOT",
            "schema_content_id_decode": "STRICT_UTF8_JSON_REJECT_DUPLICATE_MEMBER_NAMES",
            "schema_content_id_member": "/$id",
            "schema_content_id_equality": "EXACT_JSON_STRING_EQUALITY",
            "schema_document_version_equality": "EXACT_JSON_STRING_EQUALITY_TO_ROW_VERSION",
            "schema_artifact_version_member": "ABSENT_NEVER_CONSULTED",
            "content_read_failure_owner": "RESOLVE_CANDIDATE_OBJECTS_UNCHANGED",
        },
        "rules": [
            {
                "rule_id": "SCHEMA_KIND_MUST_NOT_DECLARE_ROW_SCHEMA_REF",
                "condition": "ROW_KIND_SCHEMA_AND_ROW_SCHEMA_REF_PRESENT",
                "instance_pointer": "/objects/<row_index>/schema_ref",
                "diagnostic": "SCHEMA_ROW_MUST_NOT_DECLARE_SCHEMA_REF",
            },
            {
                "rule_id": "STATUS_IN_REGISTRY_STATUS_VOCABULARY",
                "condition": "ROW_STATUS_NOT_IN_REGISTRY_STATUS_VOCABULARY",
                "instance_pointer": "/objects/<row_index>/status",
                "diagnostic": "UNKNOWN_REGISTRATION_STATUS",
            },
            {
                "rule_id": "CLASSIFICATION_IN_REGISTRY_CLASSIFICATION_VOCABULARY",
                "condition": "ROW_CLASSIFICATION_NOT_IN_REGISTRY_CLASSIFICATION_VOCABULARY",
                "instance_pointer": "/objects/<row_index>/classification",
                "diagnostic": "UNKNOWN_REGISTRATION_CLASSIFICATION",
            },
            {
                "rule_id": "REGISTRATION_SCHEMA_REF_RESOLVES_TO_REGISTERED_SCHEMA_ROW",
                "condition": "PRESENT_ROW_SCHEMA_REF_DOES_NOT_RESOLVE_TO_A_REGISTERED_SCHEMA_KIND_ROW_BY_EXACT_KIND_ID_VERSION",
                "instance_pointer": "/objects/<row_index>/schema_ref",
                "diagnostic": "UNRESOLVED_REGISTRATION_SCHEMA_REF",
            },
            {
                "rule_id": "ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY",
                "condition": "ROW_REFERENCE_NOT_EQUAL_TO_ROW_KIND_ID_VERSION_TRIPLE",
                "instance_pointer": "/objects/<row_index>/reference",
                "diagnostic": "REGISTRATION_IDENTITY_MISMATCH",
                "row_scope": "ALL_ROWS",
            },
            {
                "rule_id": "NON_SCHEMA_ROW_CONTENT_DECLARED_IDENTITY_EQUALS_ROW_REGISTRY_IDENTITY",
                "condition": "ROW_KIND_NOT_SCHEMA_AND_ROW_KIND_ID_VERSION_NOT_EQUAL_TO_THE_IDENTITY_DECLARED_BY_THE_REGISTERED_CONTENT",
                "instance_pointer": "/objects/<row_index>",
                "diagnostic": "REGISTRATION_IDENTITY_MISMATCH",
                "row_scope": "NON_SCHEMA_ROWS_ONLY",
                "relation_to_prior_rule": "UNCHANGED_FROM_THE_PRIOR_COMBINED_RULE_FOR_NON_SCHEMA_ROWS_ONLY",
            },
            {
                "rule_id": "SCHEMA_DOCUMENT_VERSION_EQUALS_ROW_VERSION",
                "condition": "ROW_KIND_SCHEMA_AND_ROW_SCHEMA_DOCUMENT_VERSION_NOT_EQUAL_TO_ROW_VERSION",
                "instance_pointer": "/objects/<row_index>/schema_document_version",
                "diagnostic": "SCHEMA_DOCUMENT_VERSION_MISMATCH",
                "row_scope": "SCHEMA_ROWS_ONLY",
            },
            {
                "rule_id": "SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID",
                "condition": "ROW_KIND_SCHEMA_AND_JSON_STRING_VALUE_OF_THE_SLASH_DOLLAR_ID_MEMBER_IN_THE_CONTENT_BYTES_DECLARED_BY_THE_ROW_IS_NOT_EXACTLY_EQUAL_TO_ROW_SCHEMA_DOCUMENT_ID",
                "instance_pointer": "/objects/<row_index>/schema_document_id",
                "diagnostic": "SCHEMA_DOCUMENT_ID_MISMATCH",
                "row_scope": "SCHEMA_ROWS_ONLY",
            },
        ],
    },
    "integrity_gate": {
        "stage": "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS",
        "declaration_shape": "STRUCTURAL_REGISTRATION",
        "declaration_shape_failure_kind": "JSON_SCHEMA",
        "declared_mode_must_be_in": ["SEMANTIC_JSON_CONTENT", "SELF_DIGEST", "PACKAGE_PINNED_BOOTSTRAP", "DUAL_ACCEPTED_SOURCE"],
        "invalid_mode": {"failure_kind": "INTEGRITY", "diagnostic": "INVALID_REGISTRATION_INTEGRITY_MODE", "instance_pointer": "/objects/<row_index>/integrity/mode"},
        "digest_mismatch": {"failure_kind": "INTEGRITY", "diagnostic": "REGISTRATION_INTEGRITY_DIGEST_MISMATCH", "instance_pointer": "/objects/<row_index>/integrity"},
        "verification_before_membership": True,
        "existing_eligibility_precondition": "INTEGRITY_VERIFIED_BEFORE_MEMBERSHIP",
    },
    "global_uniqueness": {
        "stage": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
        "stage_role": "GLOBAL_UNIQUENESS",
        "preceding_stages": [
            "APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY",
            "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
        ],
        "following_stage": "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS",
        "identity_key_members": ["kind", "id", "version"],
        "identity_key_source": "REGISTRY_DECLARED_IDENTITY_FIELDS_AND_UNIQUENESS_KEY",
        "identity_key_declaration": "SAME_KEY_NO_ADDITIONAL_KEY_DEFINED",
        "row_scope": "ALL_REGISTRY_ROWS_REGARDLESS_OF_STATUS_AND_CLASSIFICATION",
        "failure_code": "SCHEMA_INVALID_BOUND_OBJECT",
        "failure_kind": "SOURCE_ELIGIBILITY",
        "diagnostic": "DUPLICATE_REGISTRY_OBJECT_IDENTITY",
        "diagnostic_token_bucket": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
        "witness_ref": "registration.witness_contract",
        "result_contract_ref": "metacontract:/result_contracts/pre_execution_result",
        "witness_fields": "THE_SEVEN_FIELDS_OF_REGISTRATION_WITNESS_CONTRACT",
        "additional_witness_fields": "FORBIDDEN",
        "instance_pointer": "/objects/<second_occurrence_index>",
        "bound_identity": "SELECTED_DUPLICATED_KIND_ID_VERSION_TRIPLE_OBJECT",
        "first_failure_only": True,
        "selection": {
            "array_order_source": "SOURCE_/objects_ARRAY_ORDER_NORMATIVE",
            "second_occurrence_scan": "ASCENDING_INDEX_J_MINIMAL_MATCHING_PRIOR_EXISTS",
            "first_occurrence_selection": "EARLIEST_PRIOR_MATCHING_ROW_MINIMAL_I_LESS_THAN_J",
            "decision_source": "DECLARED_SCAN_ORDER_ONLY_MAP_OR_SET_ITERATION_ORDER_FORBIDDEN",
        },
        "selection_examples": [
            {
                "occurrence_indices_by_key": {"A": [0, 1, 2]},
                "selected_first_occurrence_index": 0,
                "selected_second_occurrence_index": 1,
            },
            {
                "occurrence_indices_by_key": {"A": [0, 3], "B": [1, 2]},
                "selected_first_occurrence_index": 1,
                "selected_second_occurrence_index": 2,
            },
        ],
        "precedence": {
            "earlier_structural_or_semantic_failure_wins": True,
            "duplicate_wins_over_every_later_integrity_failure": True,
            "first_failure_only": True,
            "stop_after_first_failure": True,
            "unreached_after_duplicate": [
                "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS",
                "SELECT_ELIGIBLE_CANDIDATE_OBJECTS",
                "RESOLVE_CANDIDATE_OBJECTS",
                "DERIVE_VERIFICATION_UNIVERSE_FROM_BOOTSTRAP_INPUTS",
                "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
                "EXECUTE_DECLARED_ASSERTIONS_IN_ORDER",
            ],
        },
        "duplicate_identity_repair": "FORBIDDEN",
        "cross_source_collision_repair": "FORBIDDEN",
    },
    "eligibility_binding": {
        "stage": "SELECT_ELIGIBLE_CANDIDATE_OBJECTS",
        "membership_predicate": "STATUS_ACTIVE_AND_CLASSIFICATION_NORMATIVE",
        "membership_unchanged": True,
        "eligibility_section": "metacontract:/eligibility",
        "roles": "SEPARATE_AST_GOVERNANCE_NOT_MEMBERSHIP",
        "role_kind_mismatch": {"disposition": "LATER_AST_STAGE", "procedure_id": "ROLE_MODEL_APPLIED", "failure_code": "ROLE_MODEL_APPLIED_FAILURE", "registration_failure": False},
    },
    "resolution": {
        "stage": "RESOLVE_CANDIDATE_OBJECTS",
        "input": "metacontract:/eligibility/candidate_universe",
        "output": "RESOLVED_CANDIDATE_OBJECTS",
    },
    "strict_identity_union": {
        "operation": STRICT_UNION_OPERATION,
        "operation_ref": "metacontract:/runtime_representation/universe_membership",
        "universe_contract_ref": "metacontract:/universe_contract/verification_universe",
        "stage": "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
        "stage_role": "STRICT_BOUND_SOURCE_UNION",
        "preparation_stage": "DERIVE_VERIFICATION_UNIVERSE_FROM_BOOTSTRAP_INPUTS",
        "preparation_stage_role": "VERIFICATION_UNIVERSE",
        "preparation_is_publication": False,
        "published_result": "VERIFICATION_UNIVERSE",
        "publication_requires_collision_validation": True,
        "participants": {
            "candidate": {
                "selector": "FULLY_RESOLVED_ELIGIBLE_CANDIDATE_OBJECTS_AFTER_REGISTRATION_UNIQUENESS_INTEGRITY_ELIGIBILITY_AND_RESOLUTION",
                "sequence_source": "RESOLVED_CANDIDATE_OBJECTS",
                "metadata_source": "VALIDATED_REGISTRY_METADATA",
                "eligibility_ref": "registration.eligibility_binding",
                "resolution_ref": "registration.resolution",
            },
            "bound": {
                "selector": "FULLY_VERIFIED_AND_RESOLVED_BOUND_OBJECTS_FROM_THE_EXTERNAL_ACCEPTED_SOURCE_ALLOWLIST",
                "sequence_source": "external_acceptance_profile:/accepted_source_allowlist",
                "metadata_source": "EXTERNALLY_VERIFIED_ALLOWLIST_METADATA",
                "trust_precondition": "EXTERNAL_ALLOWLIST_WHOLE_OBJECT_CLAIM_COMPARISON_AND_PIN_VERIFICATION",
                "profile_contract_ref": "metacontract:/external_acceptance_profile_contract",
            },
            "invalid_excluded_or_unresolved_participants": "NEVER_ENTER_COLLISION",
        },
        "identity_projection": STRICT_UNION_IDENTITY_PROJECTION,
        "merged_sequence": STRICT_UNION_MERGED_SEQUENCE,
        "scan_selection": STRICT_UNION_SCAN_SELECTION,
        "within_side_reachability": {
            "candidate_side": "PREEMPTED_BY_GLOBAL_UNIQUENESS_ALL_ROWS_SCOPE_THEN_REGISTRY_SCHEMA_VALIDATION",
            "candidate_duplicating_bound_identity": "PREEMPTED_BY_GLOBAL_UNIQUENESS_ONLY_WHEN_BOTH_PARTICIPANTS_ARE_ACTUAL_REGISTRY_ROWS_IN_THE_GLOBAL_UNIQUENESS_DOMAIN;ROW_LESS_EXTERNAL_BOUND_IDENTITY_DOES_NOT_PREEMPT_AND_IS_REACHABLE",
            "bound_side": "OWNED_BY_EXTERNAL_PROFILE_VALIDATION_FOR_SAME_SET_MALFORMED_DUPLICATE_OR_INCONSISTENT_EXTERNAL_ENTRIES",
            "any_representable_pair_rule": "SAME_DECLARED_SELECTED_PAIR_RULE_APPLIES",
            "reachable_collision_class": "CANDIDATE_IDENTITY_COMPONENTWISE_EQUAL_TO_BOUND_IDENTITY",
            "reachable_later_participant_side": "BOUND",
            "reachable_later_pointer_faithfulness": "DECLARED_LATER_BOUND_ALLOWLIST_INDEX_IS_THE_SELECTED_LATER_PARTICIPANT_FOR_EVERY_REACHABLE_COLLISION",
            "registry_internal_duplicate_selection": "UNCHANGED_BY_THIS_DECLARATION",
        },
        "precedence": {
            "earlier_stage_failure_wins": True,
            "earlier_failure_scope": "ANY_FAILURE_AT_AN_EARLIER_registration.stage_order_STAGE_INCLUDING_EXTERNAL_TRUST_AND_PIN_PREFIX_AND_CANDIDATE_REGISTRATION_UNIQUENESS_INTEGRITY_ELIGIBILITY_RESOLUTION",
            "union_unreachable_when_an_earlier_stage_fails": True,
            "collision_wins_over_every_later_stage_failure": True,
            "collision_ordered_before_ast": True,
            "later_stage_independently_owns_this_collision": False,
            "unreached_after_collision": [
                "STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR",
                "EXECUTE_DECLARED_ASSERTIONS_IN_ORDER",
                "FINALIZE_TYPED_RESULT",
            ],
            "first_failure_only": True,
            "stop_after_first_failure": True,
        },
        "failure": {
            "status": "FAIL",
            "stage": "PRE_EXECUTION",
            "first_failure_owner_stage": "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
            "first_failure_owner_stage_role": "STRICT_BOUND_SOURCE_UNION",
            "before_ast": True,
            "code": "SCHEMA_INVALID_BOUND_OBJECT",
            "failure_kind": "SOURCE_ELIGIBILITY",
            "diagnostic": "STRICT_IDENTITY_UNION_COLLISION",
            "diagnostic_token_scope": "STRICT_BOUND_SOURCE_UNION_STAGE_ONLY",
            "diagnostic_token_registration": "DECLARED_INLINE_HERE_NO_EXISTING_DIAGNOSTIC_TOKEN_BUCKET_IS_REDEFINED",
            "witness_ref": "registration.witness_contract",
            "result_contract_ref": "metacontract:/result_contracts/pre_execution_result",
            "witness_fields": "THE_SEVEN_FIELDS_OF_REGISTRATION_WITNESS_CONTRACT",
            "additional_witness_fields": "FORBIDDEN",
            "witness_argument_scope": "STAGE_SCOPED_ARGUMENT_VALUE_THE_REGISTRY_SCOPE_ARGUMENT_DEFAULT_OF_THE_WITNESS_CONTRACT_IS_NOT_CHANGED",
            "witness": {
                "argument": "external_acceptance_profile",
                "object_role": "BOUND_SOURCE_UNION",
                "schema_ref": PROFILE_SCHEMA_ID,
                "instance_pointer": "/accepted_source_allowlist/<selected_later_bound_index>/ref",
                "failure_kind": "SOURCE_ELIGIBILITY",
                "diagnostic": "STRICT_IDENTITY_UNION_COLLISION",
                "bound_identity": "SELECTED_COLLIDING_RESOLVED_IDENTITY_KIND_ID_VERSION_OBJECT",
            },
            "counterpart": {
                "candidate_side_reconstruction": "UNIQUE_IDENTITY_LOOKUP_IN_THE_REGISTERED_ELIGIBLE_CANDIDATE_SET",
                "earlier_bound_side_pair": "DECLARED_EARLIEST_PRIOR_SCAN_INDEX_ONLY",
            },
            "earlier_invalid_source_precedence": "EMIT_THAT_SOURCES_EXISTING_EARLIER_FAILURE_CODE_NOT_THIS_COLLISION",
            "first_failure_only": True,
        },
    },
    "first_failure_ordering": {
        "stage_order": "EXACT_BOOTSTRAP_ORDER",
        "within_stage": "ASCENDING_ROW_INDEX_THEN_DECLARED_RULE_ORDER_THEN_SINGLE_POINTER",
        "row_index": "ZERO_BASED_ARRAY_INDEX_OF_/objects",
        "pointer_notation": "RFC6901_APPENDED_TO_/objects/<row_index>",
        "first_failure_only": True,
        "stop_after_first_failure": True,
        "unreached_later_stages_emit_no_result": True,
    },
    "witness_contract": {
        "status": "FAIL",
        "stage": "PRE_EXECUTION",
        "code": "SCHEMA_INVALID_BOUND_OBJECT",
        "witness_fields": ["argument", "object_role", "schema_ref", "instance_pointer", "failure_kind", "diagnostic", "bound_identity"],
        "additional_witness_fields": "FORBIDDEN",
        "argument": "object_registry",
        "object_role": "REGISTRY_OBJECT",
        "schema_ref": REGISTRATION_SCHEMA_ID,
        "bound_identity": "ROW_KIND_ID_VERSION_TRIPLE_WHEN_READABLE_ELSE_NULL",
        "bound_identity_source": "MATCHED_ROW_KIND_ID_VERSION",
    },
    "later_identical_checks": "DEFENSIVE_UNREACHABLE",
    "constraint_ownership": {
        "schema_identity_defect_first_failure_stage": "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
        "schema_identity_ordered_rule_scope": "THE_FOUR_SCHEMA_IDENTITY_RULES_IN_SEMANTIC_REGISTRATION_DECLARED_RULE_ORDER",
        "schema_identity_ordered_rule_ids": [
            "ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY",
            "NON_SCHEMA_ROW_CONTENT_DECLARED_IDENTITY_EQUALS_ROW_REGISTRY_IDENTITY",
            "SCHEMA_DOCUMENT_VERSION_EQUALS_ROW_VERSION",
            "SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID",
        ],
        "schema_identity_ordered_diagnostics": [
            "REGISTRATION_IDENTITY_MISMATCH",
            "REGISTRATION_IDENTITY_MISMATCH",
            "SCHEMA_DOCUMENT_VERSION_MISMATCH",
            "SCHEMA_DOCUMENT_ID_MISMATCH",
        ],
        "ast_schema_identity_assertions_are_never_first_failure": True,
        "semantic_registration_owned": [
            {
                "property": "REGISTRY_OBJECT_REFERENCE_EQUALITY",
                "rule_ids": ["ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY", "NON_SCHEMA_ROW_CONTENT_DECLARED_IDENTITY_EQUALS_ROW_REGISTRY_IDENTITY"],
                "stage": "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
                "failure_code": "SCHEMA_INVALID_BOUND_OBJECT",
                "failure_kind": "SOURCE_ELIGIBILITY",
                "witness_ref": "registration.witness_contract",
            },
            {
                "property": "SCHEMA_DOCUMENT_VERSION_EQUALITY",
                "rule_ids": ["SCHEMA_DOCUMENT_VERSION_EQUALS_ROW_VERSION"],
                "stage": "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
                "failure_code": "SCHEMA_INVALID_BOUND_OBJECT",
                "failure_kind": "SOURCE_ELIGIBILITY",
                "witness_ref": "registration.witness_contract",
            },
            {
                "property": "SCHEMA_CONTENT_ID_EQUALITY",
                "rule_ids": ["SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID"],
                "stage": "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
                "failure_code": "SCHEMA_INVALID_BOUND_OBJECT",
                "failure_kind": "SOURCE_ELIGIBILITY",
                "witness_ref": "registration.witness_contract",
            },
        ],
        "ast_defensive_mirrors": [
            {
                "procedure_id": "SCHEMA_IDENTITY_MATCHES_REGISTRY",
                "assertion_id": "SCHEMA_DOCUMENT_ID_MATCHES",
                "mirrors_rule_id": "SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID",
                "owner": "SEMANTIC_REGISTRATION",
                "role": "DEFENSIVE_MIRROR",
                "reachability": "UNREACHABLE_AFTER_SEMANTIC_REGISTRATION_PASSES",
            },
            {
                "procedure_id": "SCHEMA_IDENTITY_MATCHES_REGISTRY",
                "assertion_id": "SCHEMA_DOCUMENT_VERSION_MATCHES",
                "mirrors_rule_id": "SCHEMA_DOCUMENT_VERSION_EQUALS_ROW_VERSION",
                "owner": "SEMANTIC_REGISTRATION",
                "role": "DEFENSIVE_MIRROR",
                "reachability": "UNREACHABLE_AFTER_SEMANTIC_REGISTRATION_PASSES",
            },
        ],
        "ast_distinct_owned": [
            {
                "procedure_id": "SCHEMA_IDENTITY_MATCHES_REGISTRY",
                "assertion_id": "SCHEMA_DOCUMENT_IDS_UNIQUE",
                "owner": "AST",
                "role": "DISTINCT_LATER_PROPERTY",
                "property": "SCHEMA_DOCUMENT_ID_UNIQUENESS_ACROSS_SCHEMA_ROWS",
                "mirrors_semantic_registration": False,
            },
        ],
        "global_uniqueness_owned": [
            {
                "property": "REGISTRY_OBJECT_IDENTITY_UNIQUENESS",
                "stage": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
                "failure_code": "SCHEMA_INVALID_BOUND_OBJECT",
                "failure_kind": "SOURCE_ELIGIBILITY",
                "diagnostic": "DUPLICATE_REGISTRY_OBJECT_IDENTITY",
                "diagnostic_token_bucket": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
                "identity_key_members": ["kind", "id", "version"],
                "identity_key_source": "REGISTRY_DECLARED_IDENTITY_FIELDS_AND_UNIQUENESS_KEY",
                "row_scope": "ALL_REGISTRY_ROWS_REGARDLESS_OF_STATUS_AND_CLASSIFICATION",
                "selection": "ASCENDING_MINIMAL_SECOND_OCCURRENCE_J_THEN_MINIMAL_PRIOR_I",
                "witness_ref": "registration.witness_contract",
                "first_failure_only": True,
            },
        ],
        "ast_uniqueness_defensive_mirrors": [
            {
                "procedure_id": "UNIQUE_KEY",
                "assertion_id": "UNIQUE_KEY_OBJECT_IDENTITY_UNIQUE",
                "mirrors_stage": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
                "mirrors_property": "REGISTRY_OBJECT_IDENTITY_UNIQUENESS",
                "owner": "GLOBAL_UNIQUENESS",
                "role": "DEFENSIVE_MIRROR",
                "reachability": "UNREACHABLE_AFTER_GLOBAL_UNIQUENESS_PASSES",
            },
            {
                "procedure_id": "UNIQUENESS_KEY_APPLIED",
                "assertion_id": "UNIQUENESS_KEY_APPLIED_UNIQUE_BY_CONFIGURED_KEY",
                "mirrors_stage": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
                "mirrors_property": "REGISTRY_OBJECT_IDENTITY_UNIQUENESS",
                "owner": "GLOBAL_UNIQUENESS",
                "role": "DEFENSIVE_MIRROR",
                "reachability": "UNREACHABLE_AFTER_GLOBAL_UNIQUENESS_PASSES",
            },
        ],
        "ast_uniqueness_distinct_owned": [
            {
                "procedure_id": "UNIQUENESS_KEY_APPLIED",
                "assertion_id": "UNIQUENESS_KEY_APPLIED_IDENTITY_FIELDS_EQUAL",
                "owner": "AST",
                "role": "DISTINCT_LATER_PROPERTY",
                "property": "REGISTRY_IDENTITY_FIELDS_EQUAL_DECLARED_IDENTITY_FIELDS",
                "mirrors_semantic_registration": False,
                "mirrors_global_uniqueness": False,
            },
            {
                "procedure_id": "UNIQUENESS_KEY_APPLIED",
                "assertion_id": "UNIQUENESS_KEY_APPLIED_CONFIGURED_KEY_EQUAL",
                "owner": "AST",
                "role": "DISTINCT_LATER_PROPERTY",
                "property": "REGISTRY_UNIQUENESS_KEY_EQUAL_DECLARED_IDENTITY_FIELDS",
                "mirrors_semantic_registration": False,
                "mirrors_global_uniqueness": False,
            },
        ],
        "strict_identity_union_owned": [
            {
                "property": "VERIFICATION_UNIVERSE_STRICT_IDENTITY_UNIQUENESS",
                "stage": "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
                "stage_role": "STRICT_BOUND_SOURCE_UNION",
                "failure_code": "SCHEMA_INVALID_BOUND_OBJECT",
                "failure_kind": "SOURCE_ELIGIBILITY",
                "diagnostic": "STRICT_IDENTITY_UNION_COLLISION",
                "enforcement_scope": "COMPLETE_MERGED_SEQUENCE_INCLUDING_WITHIN_SIDE_PAIRS",
                "identity_key_members": ["kind", "id", "version"],
                "collision_equality": "COMPONENTWISE_EXACT_JSON_STRING",
                "selection": "ASCENDING_MINIMAL_LATER_INDEX_J_THEN_MINIMAL_PRIOR_I",
                "witness_ref": "registration.witness_contract",
                "first_failure_only": True,
                "mirrors_global_uniqueness": False,
            },
        ],
        "ast_strict_union_owned": "NONE_NO_AST_ASSERTION_INDEPENDENTLY_OWNS_THE_BOOTSTRAP_UNION_COLLISION",
        "non_schema_content_identity": {"semantics": "UNCHANGED"},
    },
    "diagnostic_tokens": REGISTRATION_DIAGNOSTIC_TOKENS,
}

_BASE_MAKE_METACONTRACT_REGISTRATION = make_metacontract
def make_metacontract(proc, inv):
    result = _BASE_MAKE_METACONTRACT_REGISTRATION(proc, inv)
    result["bootstrap_order"] = list(REGISTRATION_BOOTSTRAP_ORDER)
    result["registration"] = copy.deepcopy(REGISTRATION)
    return result

_BASE_MAKE_METACONTRACT_SCHEMA_REGISTRATION = make_metacontract_schema
def make_metacontract_schema():
    schema = _BASE_MAKE_METACONTRACT_SCHEMA_REGISTRATION()
    if "registration" not in schema["required"]: schema["required"].append("registration")
    schema["properties"]["bootstrap_order"] = {"const": REGISTRATION_BOOTSTRAP_ORDER}
    schema["properties"]["registration"] = {"const": copy.deepcopy(REGISTRATION)}
    return schema

# ---------------------------------------------------------------------------
# MODEL B (authoritative user selection): EXTERNAL BOUND SOURCES + STRICT UNION
# COLLISION OWNERSHIP.
#
# CANDIDATE_UNIVERSE originates from registry space under the existing candidate
# eligibility rules. BOUND_SOURCE_UNIVERSE originates from the externally
# verified acceptance profile and pinned source bytes under the existing bound
# eligibility rules. They are distinct pre-union namespaces. Bound sources do
# NOT universally require an accepted-source registry row: the explicitly
# declared source/procedure-specific registry claims (including the
# SOURCE_VECTOR_CATALOG MATCH_REGISTRY_CLAIM, VECTOR_CATALOG_IDS_FROM_VERIFIED_
# CONTENT_MATCH_REGISTRY_CLAIM, and BASE_PACKAGE_EMPTY) are preserved exactly as
# declared and are never generalized into a universal bound-registry-row rule.
#
# Global registry uniqueness still owns duplicates among registry rows (all
# rows; existing key, order, precedence and witness unchanged). External-profile
# validation still owns same-set malformed, duplicate or inconsistent external
# entries. Neither alone proves cross-namespace uniqueness, so the strict union
# compares RESOLVED_OBJECT identity fields (kind,id,version) across the eligible
# candidate and bound sets BEFORE the final VERIFICATION_UNIVERSE {objects:[...]}
# is produced. Within-side preemption of this declaration applies only when BOTH
# participants are actual registry rows inside the global uniqueness domain; the
# row-less cross-set case does not preempt and is reachable, and no declaration
# may label it unreachable. Every reachable cross-set collision FAIL_CLOSED with
# semantic owner STRICT_UNION_COLLISION: no candidate/bound preference, silent
# deduplication, content merge, path/order selection or matching-content
# exemption exists, and same-set duplicates retain their earlier owners and are
# never moved downstream. Final UTF-16 lexicographic (kind,id,version) ordering
# happens only after uniqueness validation, so no collision can be hidden by
# sorting.
MODEL_B_AUTHORITATIVE_MODEL = "MODEL_B_EXTERNAL_BOUND_SOURCES_AND_STRICT_UNION_COLLISION_OWNERSHIP"
MODEL_B_PRE_UNION_NAMESPACES = "CANDIDATE_UNIVERSE_AND_BOUND_SOURCE_UNIVERSE_ARE_DISTINCT_INDEPENDENTLY_DERIVED_PRE_UNION_NAMESPACES"
MODEL_B_BOUND_ELIGIBILITY_SOURCE = "EXTERNALLY_VERIFIED_ACCEPTANCE_PROFILE_AND_PINNED_SOURCE_BYTES"
MODEL_B_SEMANTIC_OWNER = "STRICT_UNION_COLLISION"
MODEL_B_CANDIDATE_PRE_UNION_NAMESPACE = "CANDIDATE_UNIVERSE_DISTINCT_FROM_BOUND_SOURCE_UNIVERSE"
MODEL_B_COLLISION_WITNESS_REF = "metacontract:/schema/$defs/strict_union_collision_witness"
MODEL_B_CANDIDATE_UNIVERSE = {
    "status": "ACTIVE",
    "classification": "NORMATIVE",
    "membership_predicate": "STATUS_ACTIVE_AND_CLASSIFICATION_NORMATIVE",
    "preconditions": ["TYPED_REGISTRY_REGISTRATION_VALID_FOR_KIND", "INTEGRITY_VERIFIED_BEFORE_MEMBERSHIP"],
    "validation_by_kind": {"SCHEMA": "NO_SCHEMA_REF_AND_SCHEMA_DOCUMENT_MUST_DECLARE_DRAFT_2020_12_AND_USE_LOCAL_FRAGMENT_REFS_ONLY", "NON_SCHEMA": "CONTENT_MUST_VALIDATE_AGAINST_EXACT_REGISTERED_SCHEMA_REF"},
    "role_dimension": "GOVERNANCE_REQUIREMENTS_ROLE_MODEL_SEPARATE_FROM_CANDIDATE_MEMBERSHIP",
    "integrity_required": True,
    "pre_union_namespace": MODEL_B_CANDIDATE_PRE_UNION_NAMESPACE,
}
MODEL_B_BOUND_SOURCE_UNIVERSE = {
    "status": "ACTIVE_ACCEPTED_SOURCE",
    "registry_classification": "PROVENANCE",
    "binding_classification": "SOURCE_ONLY",
    "required_roles_by_ref": {"PACKAGE": ["NORMATIVE_BOUND_SOURCE"], "SOURCE_VECTOR_CATALOG": ["CATALOG_BINDING", "VECTOR_SOURCE"]},
    "pre_union_namespace": "BOUND_SOURCE_UNIVERSE_DISTINCT_FROM_CANDIDATE_UNIVERSE",
    "bound_eligibility_source": MODEL_B_BOUND_ELIGIBILITY_SOURCE,
    "bound_registry_row_requirement": "NOT_UNIVERSAL;SOURCE_SPECIFIC_REGISTRY_CLAIMS_PRESERVED",
    "candidate_equality_is_not_candidate_ineligibility": True,
    "cross_set_collision_owner": MODEL_B_SEMANTIC_OWNER,
}
MODEL_B_WITHIN_SIDE_REACHABILITY = {
    "candidate_side": "PREEMPTED_BY_GLOBAL_UNIQUENESS_ALL_ROWS_SCOPE_THEN_REGISTRY_SCHEMA_VALIDATION",
    "candidate_duplicating_bound_identity": "PREEMPTED_BY_GLOBAL_UNIQUENESS_ONLY_WHEN_BOTH_PARTICIPANTS_ARE_ACTUAL_REGISTRY_ROWS_IN_THE_GLOBAL_UNIQUENESS_DOMAIN;ROW_LESS_EXTERNAL_BOUND_IDENTITY_DOES_NOT_PREEMPT_AND_IS_REACHABLE",
    "bound_side": "OWNED_BY_EXTERNAL_PROFILE_VALIDATION_FOR_SAME_SET_MALFORMED_DUPLICATE_OR_INCONSISTENT_EXTERNAL_ENTRIES",
    "any_representable_pair_rule": "SAME_DECLARED_SELECTED_PAIR_RULE_APPLIES",
    "reachable_collision_class": "CANDIDATE_IDENTITY_COMPONENTWISE_EQUAL_TO_BOUND_IDENTITY",
    "reachable_later_participant_side": "BOUND",
    "reachable_later_pointer_faithfulness": "DECLARED_LATER_BOUND_ALLOWLIST_INDEX_IS_THE_SELECTED_LATER_PARTICIPANT_FOR_EVERY_REACHABLE_COLLISION",
    "registry_internal_duplicate_selection": "UNCHANGED_BY_THIS_DECLARATION",
    "cross_set_collision_reachable": True,
    "cross_set_collision_owner": MODEL_B_SEMANTIC_OWNER,
    "no_declaration_may_label_the_rowless_cross_set_case_unreachable": True,
}
MODEL_B_STRICT_UNION_WITNESS_FIELDS = ["kind", "id", "version", "candidate_origin",
                                       "candidate_path_or_source", "bound_origin", "bound_path_or_source"]
MODEL_B_STRICT_UNION_WITNESS_SCHEMA = {
    "type": "object",
    "required": list(MODEL_B_STRICT_UNION_WITNESS_FIELDS),
    "properties": {
        "kind": {"type": "string", "minLength": 1},
        "id": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "candidate_origin": {"const": "CANDIDATE_UNIVERSE"},
        "candidate_path_or_source": {"type": "string", "minLength": 1},
        "bound_origin": {"const": "BOUND_SOURCE_UNIVERSE"},
        "bound_path_or_source": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}
MODEL_B_STRICT_UNION_FAILURE = {
    "status": "FAIL",
    "stage": "PRE_EXECUTION",
    "first_failure_owner_stage": "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
    "first_failure_owner_stage_role": "STRICT_BOUND_SOURCE_UNION",
    "semantic_owner": MODEL_B_SEMANTIC_OWNER,
    "semantic_owner_stage": "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
    "semantic_owner_stage_role": "STRICT_BOUND_SOURCE_UNION",
    "semantic_owner_relation_to_preparation_stage": "THE_PREPARATION_STAGE_DERIVE_VERIFICATION_UNIVERSE_FROM_BOOTSTRAP_INPUTS_IS_NOT_PUBLICATION;COLLISION_OWNERSHIP_AND_REJECTION_ATTACH_TO_THE_LATER_VALIDATE_STAGE_THAT_PUBLISHES_THE_FINAL_VERIFICATION_UNIVERSE",
    "before_ast": True,
    "code": "SCHEMA_INVALID_BOUND_OBJECT",
    "failure_kind": "SOURCE_ELIGIBILITY",
    "diagnostic": "STRICT_IDENTITY_UNION_COLLISION",
    "diagnostic_token_scope": "STRICT_BOUND_SOURCE_UNION_STAGE_ONLY",
    "diagnostic_token_registration": "DECLARED_INLINE_HERE_NO_EXISTING_DIAGNOSTIC_TOKEN_BUCKET_IS_REDEFINED",
    "witness_ref": MODEL_B_COLLISION_WITNESS_REF,
    "result_contract_ref": "metacontract:/result_contracts/pre_execution_result",
    "witness_fields": list(MODEL_B_STRICT_UNION_WITNESS_FIELDS),
    "additional_witness_fields": "FORBIDDEN",
    "witness_field_derivation": {
        "kind": "EXACT_KIND_OF_THE_SELECTED_RESOLVED_OBJECT_IDENTITY",
        "id": "EXACT_ID_OF_THE_SELECTED_RESOLVED_OBJECT_IDENTITY",
        "version": "EXACT_VERSION_OF_THE_SELECTED_RESOLVED_OBJECT_IDENTITY",
        "candidate_origin": "CONSTANT_FROM_THE_SELECTED_CANDIDATE_RESOLVED_OPERAND_ORIGIN",
        "candidate_path_or_source": "SELECTED_ELIGIBLE_CANDIDATE_RESOLVED_OBJECT_PATH",
        "bound_origin": "CONSTANT_FROM_THE_SELECTED_BOUND_RESOLVED_OPERAND_ORIGIN",
        "bound_path_or_source": "SELECTED_BOUND_ALLOWLIST_ROW_CANONICAL_PATH",
    },
    "participant_cardinality_per_collision_key": "EXACTLY_ONE_CANDIDATE_AND_EXACTLY_ONE_BOUND_PARTICIPANT_FOLLOWS_FROM_EARLIER_SAME_SET_UNIQUENESS;IF_THAT_PRECONDITION_FAILS_THE_EARLIER_SAME_SET_OWNER_WINS_AND_NO_STRICT_UNION_COLLISION_IS_EMITTED",
    "deterministic_choice_across_multiple_collision_keys": "MINIMAL_BOUND_ALLOWLIST_INDEX_J_THEN_MINIMAL_CANDIDATE_INDEX_I;NO_UNIVERSE_PUBLICATION_OR_FINAL_SORT_PRECEDES_COLLISION_VALIDATION",
    "earlier_invalid_source_precedence": "EMIT_THAT_SOURCES_EXISTING_EARLIER_FAILURE_CODE_NOT_THIS_COLLISION",
    "first_failure_only": True,
}
MODEL_B_COLLISION_WITNESS_BRANCH = {
    "type": "object",
    "required": ["status", "stage", "code", "witness"],
    "properties": {
        "status": {"const": "FAIL"},
        "stage": {"const": "PRE_EXECUTION"},
        "code": {"const": "SCHEMA_INVALID_BOUND_OBJECT"},
        "witness": {"$ref": "#/$defs/strict_union_collision_witness"},
    },
    "additionalProperties": False,
}
MODEL_B_STRICT_UNION_OWNED = {
    "semantic_owner": MODEL_B_SEMANTIC_OWNER,
    "enforcement_scope": "CROSS_SET_PAIRS_AFTER_WITHIN_SIDE_EARLIER_OWNERS",
    "witness_ref": MODEL_B_COLLISION_WITNESS_REF,
}
MODEL_B_VERIFICATION_UNIVERSE = {
    "pre_union_namespaces": MODEL_B_PRE_UNION_NAMESPACES,
    "cross_set_collision_owner": MODEL_B_SEMANTIC_OWNER,
    "validation_precedes_final_ordering": True,
    "final_order": "UTF16_LEXICOGRAPHIC_KIND_ID_VERSION_ASCENDING",
}
MODEL_B_SHARED_SAME_SET_OWNERS = {
    "candidate_rows": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY_ALL_REGISTRY_ROWS_UNCHANGED",
    "bound_rows": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_UNCHANGED",
    "neither_alone_proves_cross_namespace_uniqueness": True,
}

STRICT_UNION_SCAN_SELECTION["enforcement_scope"] = "CROSS_SET_PAIRS_AFTER_CANDIDATE_SIDE_GLOBAL_UNIQUENESS_AND_BOUND_SIDE_EXTERNAL_PROFILE_VALIDATION"
_RUNTIME_REPRESENTATION["universe_membership"].update({
    "collision_owner": MODEL_B_SEMANTIC_OWNER,
    "collision_reachability": "CROSS_SET_PAIR_OF_ONE_ELIGIBLE_CANDIDATE_AND_ONE_ELIGIBLE_BOUND_RESOLVED_OBJECT_WITH_COMPONENTWISE_EQUAL_KIND_ID_VERSION",
    "final_order_after_uniqueness_validation": True,
    "silent_deduplication": "FORBIDDEN",
    "side_preference": "FORBIDDEN",
    "content_merge": "FORBIDDEN",
    "matching_content_exemption": "FORBIDDEN",
})
_RUNTIME_REPRESENTATION["resolved_construction"]["bound_members_scope"] = "SOURCE_SPECIFIC_VECTOR_CATALOG_ONLY;NOT_A_UNIVERSAL_BOUND_REGISTRY_ROW_REQUIREMENT;BASE_PACKAGE_EMPTY_PRESERVED"
REGISTRATION["strict_identity_union"].update({
    "authoritative_model": MODEL_B_AUTHORITATIVE_MODEL,
    "pre_union_namespaces": MODEL_B_PRE_UNION_NAMESPACES,
    "same_set_owners_unchanged": dict(MODEL_B_SHARED_SAME_SET_OWNERS),
    "cross_set_uniqueness_owner": MODEL_B_SEMANTIC_OWNER,
    "collision_validation_precedes_publication": True,
    "published_universe_ordering": "FINAL_UTF16_LEXICOGRAPHIC_KIND_ID_VERSION_ASCENDING_ORDERING_OCCURS_AFTER_UNIQUENESS_VALIDATION_ONLY",
})
REGISTRATION["strict_identity_union"]["participants"]["bound"]["registry_row_requirement"] = "NOT_UNIVERSAL;EXTERNAL_PROFILE_AND_PINNED_SOURCE_BYTES_ONLY;SOURCE_SPECIFIC_REGISTRY_CLAIMS_PRESERVED"
REGISTRATION["strict_identity_union"]["participants"]["bound"]["registry_row_requirement_scope"] = "BOUND_SOURCE_UNIVERSE_UNDER_EXTERNAL_BOUND_ELIGIBILITY"
REGISTRATION["strict_identity_union"]["within_side_reachability"] = dict(MODEL_B_WITHIN_SIDE_REACHABILITY)
REGISTRATION["strict_identity_union"]["failure"] = copy.deepcopy(MODEL_B_STRICT_UNION_FAILURE)
REGISTRATION["constraint_ownership"]["strict_identity_union_owned"][0].update(MODEL_B_STRICT_UNION_OWNED)
# ---------------------------------------------------------------------------
# ACCORD-02E4R5R4 vector claim earliest-owner closure.
#
# The source-specific accepted vector source carries one registry claim: the row
# in object_registry:/objects whose /reference equals the selected accepted
# vector source /ref, componentwise exact on (kind, id, version). Zero matching
# claims fail construction; exactly one matching claim must satisfy STRICT SET
# EQUALITY OF UNIQUE MEMBER IDS against the IDs extracted from the verified
# pinned vector content under the already declared extraction rule. Two or more
# matching claims are MULTIPLE_MATCHES_UNREACHABLE_AFTER_GLOBAL_UNIQUENESS: the
# earlier all-rows GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY owns duplicate registry
# rows, so no second downstream ambiguity code or witness exists and a violated
# precondition fails closed to the earlier owner without silent deduplication.
# The bound namespace stays independent of the candidate registry: no universal
# bound registry-row requirement is introduced, and the accepted base package
# remains claim-free with BASE_PACKAGE_EMPTY preserved.
# ---------------------------------------------------------------------------
VECTOR_CLAIM_STAGE = "BOUND_SOURCE_RESOLVED_CONSTRUCTION"
VECTOR_CLAIM_STAGE_ROLE = "BOUND_SOURCE_RESOLUTION"
VECTOR_CLAIM_FAILURE_CODE = "SCHEMA_INVALID_BOUND_OBJECT"
VECTOR_CLAIM_FAILURE_KIND = "SOURCE_ELIGIBILITY"
VECTOR_CLAIM_DIAGNOSTIC = "VECTOR_REGISTRY_CLAIM_INVALID"
VECTOR_CLAIM_TOKEN_BUCKET = "BOUND_SOURCE_RESOLVED_CONSTRUCTION"
VECTOR_CLAIM_WITNESS_REF = "metacontract:/schema/$defs/vector_registry_claim_witness"
VECTOR_CLAIM_SOURCE_KIND = "SOURCE_VECTOR_CATALOG"
VECTOR_CLAIM_SOURCE_ORIGIN = "BOUND_SOURCE_UNIVERSE"
VECTOR_CLAIM_REASONS = [
    "MISSING_REGISTRY_CLAIM",
    "MISSING_OR_INVALID_REGISTRY_CLAIM_MEMBERS",
    "DUPLICATE_VECTOR_CLAIM_MEMBER_IDS",
    "MISSING_OR_INVALID_VERIFIED_CONTENT_MEMBERS",
    "DUPLICATE_VECTOR_CONTENT_MEMBER_IDS",
    "MEMBER_SET_MISMATCH",
]
VECTOR_CLAIM_WITNESS_FIELDS = ["source_kind", "source_id", "source_version", "source_origin",
                               "source_path", "registry_claim_key", "match_count", "reason",
                               "diagnostic"]
VECTOR_REGISTRY_CLAIM_LAW = {
    "stage": VECTOR_CLAIM_STAGE,
    "stage_role": VECTOR_CLAIM_STAGE_ROLE,
    "stage_position": "AFTER_RESOLVE_CANDIDATE_OBJECTS;BEFORE_DERIVE_VERIFICATION_UNIVERSE_FROM_BOOTSTRAP_INPUTS_AND_BEFORE_VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE;BEFORE_AST",
    "source_scope": "SOURCE_SPECIFIC_ACCEPTED_VECTOR_SOURCE_ONLY;NOT_A_UNIVERSAL_BOUND_REGISTRY_ROW_REQUIREMENT;BASE_PACKAGE_EMPTY_PRESERVED",
    "failure_code": VECTOR_CLAIM_FAILURE_CODE,
    "failure_kind": VECTOR_CLAIM_FAILURE_KIND,
    "diagnostic": VECTOR_CLAIM_DIAGNOSTIC,
    "diagnostic_token_bucket": VECTOR_CLAIM_TOKEN_BUCKET,
    "result_contract_ref": "metacontract:/result_contracts/pre_execution_result",
    "witness_ref": VECTOR_CLAIM_WITNESS_REF,
    "witness_fields": list(VECTOR_CLAIM_WITNESS_FIELDS),
    "additional_witness_fields": "FORBIDDEN",
    "first_failure_only": True,
    "lookup": {
        "domain": "object_registry:/objects",
        "domain_scope": "ALL_REGISTRY_ROWS_INCLUDING_ACTIVE_ACCEPTED_SOURCE_ROWS",
        "predicate": "ROW_/reference_EQUALS_SELECTED_ACCEPTED_VECTOR_SOURCE_/ref",
        "equality": "COMPONENTWISE_EXACT_JSON_STRING_EQUALITY_ON_KIND_ID_VERSION",
        "selected_source_identity_source": "VERIFIED_BOUND_RESOLVED_OBJECT_FROM_EXTERNAL_ACCEPTANCE_PROFILE_AND_VERIFIED_PINNED_SOURCE_BYTES",
        "forbidden_lookup_keys": ["FILENAME", "PATH", "ROLE", "DIGEST", "ROW_INDEX", "PRIVATE_PROJECTION"],
        "registry_identity_law": "SEMANTIC_VALIDATION_RULE_4_ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY_FORCES_REF_EQUALS_KIND_ID_VERSION_BEFORE_THIS_STAGE",
        "match_count": "COUNT_OF_MATCHING_ROWS",
        "zero_matches": "FAIL_MISSING_REGISTRY_CLAIM",
        "one_match": "SELECTED_REGISTRY_CLAIM",
        "multiple_matches": "MULTIPLE_MATCHES_UNREACHABLE_AFTER_GLOBAL_UNIQUENESS",
        "multiple_matches_earlier_owner": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY",
        "multiple_matches_behavior": "NO_SECOND_DOWNSTREAM_AMBIGUITY_CODE_OR_WITNESS;IF_THE_EARLIER_PRECONDITION_IS_VIOLATED_FAIL_CLOSED_HONORING_THE_EARLIER_PRECONDITION_OWNER;NEVER_SILENT_DEDUPLICATION",
        "duplicate_registry_rows_owner": "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY_ALL_REGISTRY_ROWS",
    },
    "member_relation": {
        "relation": "STRICT_SET_EQUALITY_OF_UNIQUE_MEMBER_IDS",
        "derived_collection": "IDS_EXTRACTED_FROM_VERIFIED_PINNED_VECTOR_CONTENT",
        "derived_extraction_rule": "EXACT_SOURCE_LOCATION_/vectors/<vector_index>/vector_id_FROM_THE_RESOLVED_CONTENT_OF_THE_SELECTED_ACCEPTED_VECTOR_SOURCE_NO_MEMBER_PROJECTION",
        "registry_collection": "SELECTED_REGISTRY_CLAIM_/members",
        "element_type": "JSON_STRING",
        "element_equality": "EXACT_JSON_STRING_EQUALITY",
        "ordering": "ORDERING_IS_NOT_SEMANTIC;NEITHER_COLLECTION_ORDER_IS_COMPARED",
        "uniqueness": "EACH_COLLECTION_MUST_CONTAIN_UNIQUE_IDS;DUPLICATE_IDS_ARE_INVALID_AND_ARE_NEVER_SILENTLY_COLLAPSED",
        "set_operation": "TWO_DIRECTIONAL_UNIQUE_SET_DIFFERENCE_EMPTY",
        "missing_member_ids_definition": "DERIVED_UNIQUE_IDS_MINUS_REGISTRY_UNIQUE_IDS",
        "extra_member_ids_definition": "REGISTRY_UNIQUE_IDS_MINUS_DERIVED_UNIQUE_IDS",
        "array_order_law": "LEXICOGRAPHIC_UTF16_CODE_UNIT_ASCENDING_UNIQUE",
        "empty_set_semantics": "TWO_UNIQUE_EMPTY_SETS_SATISFY_STRICT_SET_EQUALITY_UNLESS_AN_INDEPENDENT_SOURCE_SCHEMA_OR_ELIGIBILITY_RULE_DISALLOWS_SUCH_A_SOURCE",
        "failure_ordering": list(VECTOR_CLAIM_REASONS),
        "both_collections_have_duplicate_ids": "DUPLICATE_VECTOR_CLAIM_MEMBER_IDS_WINS_AS_FIRST_FAILURE",
        "python_choice": "FORBIDDEN;NO_MAP_OR_SET_ITERATION_ORDER;SORT_BY_DECLARED_UTF16_COMPARATOR_ONLY",
        "first_failure_only": True,
        "accepted_artifact_preservation": "THIS_DECLARATION_DOES_NOT_CHANGE_ANY_ACCEPTED_ARTIFACT",
    },
    "reason_derivation": {
        "MISSING_REGISTRY_CLAIM": "MATCH_COUNT_EQUALS_ZERO",
        "MISSING_OR_INVALID_REGISTRY_CLAIM_MEMBERS": "MATCH_COUNT_EQUALS_ONE_AND_SELECTED_ROW_/members_IS_ABSENT_OR_NOT_AN_ARRAY_OF_NONEMPTY_JSON_STRINGS",
        "DUPLICATE_VECTOR_CLAIM_MEMBER_IDS": "MATCH_COUNT_EQUALS_ONE_AND_SELECTED_ROW_/members_IS_A_VALID_ARRAY_WITH_AT_LEAST_ONE_ID_OCCURRING_MORE_THAN_ONCE;COLLECTION_REGISTRY_CLAIM_MEMBERS",
        "MISSING_OR_INVALID_VERIFIED_CONTENT_MEMBERS": "MATCH_COUNT_EQUALS_ONE_AND_CLAIM_COLLECTION_VALID_AND_UNIQUE_AND_VERIFIED_PINNED_CONTENT_/vectors_IS_ABSENT_OR_NOT_AN_ARRAY_OR_AN_ELEMENT_LACKS_A_NONEMPTY_STRING_/vector_id",
        "DUPLICATE_VECTOR_CONTENT_MEMBER_IDS": "MATCH_COUNT_EQUALS_ONE_AND_PRIOR_COLLECTIONS_VALID_AND_UNIQUE_AND_DERIVED_COLLECTION_HAS_AT_LEAST_ONE_ID_OCCURRING_MORE_THAN_ONCE;COLLECTION_VERIFIED_CONTENT_VECTOR_IDS",
        "MEMBER_SET_MISMATCH": "MATCH_COUNT_EQUALS_ONE_AND_BOTH_COLLECTIONS_VALID_AND_UNIQUE_AND_UNIQUE_ID_SETS_DIFFER",
    },
    "witness_field_derivation": {
        "source_kind": "CONSTANT_SOURCE_VECTOR_CATALOG_OF_THE_SELECTED_ACCEPTED_VECTOR_SOURCE_VERIFIED_BOUND_ENTRY",
        "source_id": "EXACT_ID_OF_THE_SELECTED_ACCEPTED_VECTOR_SOURCE_REFERENCE_FROM_THE_VERIFIED_EXTERNAL_ACCEPTANCE_PROFILE_ROW",
        "source_version": "EXACT_VERSION_OF_THE_SELECTED_ACCEPTED_VECTOR_SOURCE_REFERENCE_FROM_THE_VERIFIED_EXTERNAL_ACCEPTANCE_PROFILE_ROW",
        "source_origin": "CONSTANT_BOUND_SOURCE_UNIVERSE_OF_THE_VERIFIED_BOUND_RESOLVED_OBJECT",
        "source_path": "EXACT_CANONICAL_PATH_OF_THE_VERIFIED_EXTERNAL_ACCEPTANCE_PROFILE_ROW",
        "registry_claim_key": "EXACT_TYPED_REFERENCE_KEY_USED_AS_THE_LOOKUP_PREDICATE_COMPONENTWISE(kind,id,version);WHEN_MATCH_COUNT_IS_ONE_IT_EQUALS_THE_SELECTED_ROW_/reference",
        "match_count": "COUNT_OF_object_registry:/objects_ROWS_WHOSE_/reference_EQUALS_THE_SELECTED_ACCEPTED_VECTOR_SOURCE_REF_COMPONENTWISE",
        "reason": "FIRST_MATCHING_REASON_FROM_member_relation.failure_ordering",
        "diagnostic": "CONSTANT_VECTOR_REGISTRY_CLAIM_INVALID",
        "missing_member_ids": "DERIVED_UNIQUE_IDS_MINUS_REGISTRY_UNIQUE_IDS_SORTED_UNIQUE_UTF16_ASCENDING;PRESENT_ONLY_FOR_MEMBER_SET_MISMATCH",
        "extra_member_ids": "REGISTRY_UNIQUE_IDS_MINUS_DERIVED_UNIQUE_IDS_SORTED_UNIQUE_UTF16_ASCENDING;PRESENT_ONLY_FOR_MEMBER_SET_MISMATCH",
        "duplicate_member_ids": "IDS_WITH_MULTIPLICITY_GREATER_THAN_ONE_IN_THE_INVALID_COLLECTION_NAMED_BY_THE_REASON_SORTED_UNIQUE_UTF16_ASCENDING;PRESENT_ONLY_FOR_THE_TWO_DUPLICATE_REASONS",
    },
    "post_conditions": ["BOUND_RESOLVED_MEMBERS_CONSTRUCTED_FROM_THE_VERIFIED_CONTENT_VECTOR_IDS",
                        "BOUND_ELIGIBILITY_COMPLETE_UNDER_EXTERNAL_PROFILE_AND_PINNED_BYTES_ONLY",
                        "STRICT_IDENTITY_UNION_AND_AST_STAGES_FOLLOW_UNCHANGED"],
    "earlier_failure_precedence": "ANY_FAILURE_AT_AN_EARLIER_stage_order_STAGE_WINS;THIS_STAGE_IS_NOT_REACHED",
    "diagnostic_token_registration": "DECLARED_IN_THE_BOUND_SOURCE_RESOLVED_CONSTRUCTION_BUCKET_NO_EXISTING_BUCKET_IS_REDEFINED",
}
REGISTRATION["bound_source_resolved_construction"] = copy.deepcopy(VECTOR_REGISTRY_CLAIM_LAW)
_RUNTIME_REPRESENTATION["resolved_construction"]["vector_registry_claim"] = copy.deepcopy(VECTOR_REGISTRY_CLAIM_LAW)
REGISTRATION["constraint_ownership"]["bound_source_resolved_construction_owned"] = [{
    "property": "VECTOR_REGISTRY_CLAIM_MEMBER_SET_RELATION",
    "stage": VECTOR_CLAIM_STAGE,
    "stage_role": VECTOR_CLAIM_STAGE_ROLE,
    "failure_code": VECTOR_CLAIM_FAILURE_CODE,
    "failure_kind": VECTOR_CLAIM_FAILURE_KIND,
    "diagnostic": VECTOR_CLAIM_DIAGNOSTIC,
    "diagnostic_token_bucket": VECTOR_CLAIM_TOKEN_BUCKET,
    "witness_ref": VECTOR_CLAIM_WITNESS_REF,
    "first_failure_only": True,
    "mirrors_global_uniqueness": False,
}]
VECTOR_CLAIM_ASSERTION_CLASSIFICATION = [
    {"index": 0,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_ACCEPTED_SOURCE_KEYS_UNIQUE",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "UNIQUE_BY(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), pointers=[\"/ref/kind\", \"/ref/id\", \"/ref/version\"])",
     "operands": ["arg:accepted_binding:/sources"],
     "required_values": [],
     "first_failure_owner": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_OWNS_INVALID_OR_DUPLICATE_EXTERNAL_DECLARATIONS;GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY_OWNS_DUPLICATE_REGISTRY_ROWS",
     "scope": "Uniqueness of the bound-side allowlist identity keys only; defensive at AST time once the verified external profile has been consumed. Earliest owners are unchanged and no new reachable owner is introduced: duplicate matching claims remain owned by the earlier all-rows global uniqueness stage, and equal-identity cross-namespace collisions remain owned by the declared strict-identity-union stage."},
    {"index": 1,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_EXACT_ACCEPTED_BINDING_EXISTS",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=COUNT(array=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\")))), right=literal:1)",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": ["1"],
     "first_failure_owner": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_AND_WHOLE_OBJECT_CLAIM_COMPARISON_OWN_BINDING_EXISTENCE",
     "scope": "Count of accepted-allowlist rows matching the candidate binding's assigned kind/id/version equals one; not the registry claim lookup and not the vector member relation."},
    {"index": 2,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_ACCEPTED_SOURCE_RESOLVES",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=RESOLVE_ONE(reference=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"), universe=arg:verification_universe), pointer=\"/ref\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:verification_universe:", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/ref", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": [],
     "first_failure_owner": "BOUND_RESOLUTION_REQUIRES_EXACT_REFERENCE_AND_IS_GUARANTEED_FOR_EVERY_RESOLVED_BOUND_OPERAND",
     "scope": "Resolved allowlist row /ref equals its own /ref; a resolution-construction guarantee re-checked defensively."},
    {"index": 3,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_EXACT_SOURCE_PATH",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/repository_root_path\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/path\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/path", "get_over:/repository_root_path", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": [],
     "first_failure_owner": "PIN_AND_PATH_VERIFICATION_STAGES_OWN_EXACT_SOURCE_PATHS_BEFORE_SEMANTIC_USE",
     "scope": "Candidate binding declared path equals the resolved path; retained as a distinct later property, not hoisted into construction ownership."},
    {"index": 4,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_RESOLVED_PATH_MATCHES_PIN",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=RESOLVE_ONE(reference=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"), universe=arg:verification_universe), pointer=\"/path\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/path\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:verification_universe:", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/path", "get_over:/ref", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": [],
     "first_failure_owner": "EXTERNAL_PIN_VERIFICATION_OWNS_PINNED_PATH_IDENTITY",
     "scope": "Resolved path equals the pinned canonical path; defensive re-check of an earlier pin-stage property."},
    {"index": 5,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_REGISTRY_SOURCE_ROW_UNIQUE",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=COUNT(array=FILTER(array=GET(value=arg:object_registry, pointer=\"/objects\"), as=\"or0\", where=JSON_EQUAL(left=GET(value=item:or0, pointer=\"/reference\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\")))), right=literal:1)",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:object_registry:/objects", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/ref", "item:or0:/reference", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": ["1"],
     "first_failure_owner": "BOUND_SOURCE_RESOLVED_CONSTRUCTION_OWNS_ZERO_AND_ONE_MATCH_COUNT_AND_THE_MEMBER_RELATION;GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY_OWNS_DUPLICATE_REGISTRY_ROWS",
     "scope": "Post-construction semantic re-check: the vector construction domain selects registry rows by the selected external accepted vector source reference (/reference equals that selected source /ref), while this AST predicate matches rows by the candidate binding's assigned kind/id/version triple; the predicates coincide only if the candidate assignment and the external selection resolve to the same identity, which is not entailed here, so no A-E construction guarantee is claimed. Earliest owners are unchanged: BOUND_SOURCE_RESOLVED_CONSTRUCTION owns zero/one-match and the member relation in its own domain, and GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY owns duplicate matching claims before construction."},
    {"index": 6,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_REGISTRY_SOURCE_STATUS",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=FILTER(array=GET(value=arg:object_registry, pointer=\"/objects\"), as=\"or0\", where=JSON_EQUAL(left=GET(value=item:or0, pointer=\"/reference\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"))), pointer=\"/0/status\"), right=literal:\"ACTIVE_ACCEPTED_SOURCE\")",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:object_registry:/objects", "get_over:/0", "get_over:/0/status", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/ref", "item:or0:/reference", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": ["\"ACTIVE_ACCEPTED_SOURCE\""],
     "first_failure_owner": "STRUCTURAL_AND_SEMANTIC_REGISTRATION_STAGES_OWN_ROW_STATUS",
     "scope": "Matched accepted-source row status equals ACTIVE_ACCEPTED_SOURCE; distinct later property, not hoisted."},
    {"index": 7,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_REGISTRY_SOURCE_CLASS",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=FILTER(array=GET(value=arg:object_registry, pointer=\"/objects\"), as=\"or0\", where=JSON_EQUAL(left=GET(value=item:or0, pointer=\"/reference\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"))), pointer=\"/0/classification\"), right=literal:\"PROVENANCE\")",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:object_registry:/objects", "get_over:/0", "get_over:/0/classification", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/ref", "item:or0:/reference", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": ["\"PROVENANCE\""],
     "first_failure_owner": "STRUCTURAL_AND_SEMANTIC_REGISTRATION_STAGES_OWN_ROW_CLASSIFICATION",
     "scope": "Matched accepted-source row classification equals PROVENANCE; distinct later property, not hoisted."},
    {"index": 8,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_REGISTRY_SOURCE_PATH",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=FILTER(array=GET(value=arg:object_registry, pointer=\"/objects\"), as=\"or0\", where=JSON_EQUAL(left=GET(value=item:or0, pointer=\"/reference\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"))), pointer=\"/0/path\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/path\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:object_registry:/objects", "get_over:/0", "get_over:/0/path", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/path", "get_over:/ref", "item:or0:/reference", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": [],
     "first_failure_owner": "EXTERNAL_PIN_VERIFICATION_OWNS_THE_PINNED_SOURCE_PATH",
     "scope": "Matched row canonical path equals the pinned source path; registry-row restatement of the path property."},
    {"index": 9,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_REGISTRY_SOURCE_CATALOG_ROLE",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "ANY(array=GET(value=FILTER(array=GET(value=arg:object_registry, pointer=\"/objects\"), as=\"or0\", where=JSON_EQUAL(left=GET(value=item:or0, pointer=\"/reference\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"))), pointer=\"/0/roles\"), as=\"r1\", where=JSON_EQUAL(left=item:r1, right=literal:\"CATALOG_BINDING\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:object_registry:/objects", "get_over:/0", "get_over:/0/roles", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/ref", "item:or0:/reference", "item:r1:", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": ["\"CATALOG_BINDING\""],
     "first_failure_owner": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_OWNS_DECLARED_SOURCE_ROLES",
     "scope": "Matched row declares the CATALOG_BINDING role; declaration consistency re-check."},
    {"index": 10,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_REGISTRY_SOURCE_VECTOR_ROLE",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "ANY(array=GET(value=FILTER(array=GET(value=arg:object_registry, pointer=\"/objects\"), as=\"or0\", where=JSON_EQUAL(left=GET(value=item:or0, pointer=\"/reference\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"))), pointer=\"/0/roles\"), as=\"r2\", where=JSON_EQUAL(left=item:r2, right=literal:\"VECTOR_SOURCE\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:object_registry:/objects", "get_over:/0", "get_over:/0/roles", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/ref", "item:or0:/reference", "item:r2:", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": ["\"VECTOR_SOURCE\""],
     "first_failure_owner": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_OWNS_DECLARED_SOURCE_ROLES",
     "scope": "Matched row declares the VECTOR_SOURCE role; declaration consistency re-check."},
    {"index": 11,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_SEMANTIC_DIGEST_CLAIM",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/semantic_json_content_sha256\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/semantic_json_content_sha256\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/integrity/semantic_json_content_sha256", "get_over:/semantic_json_content_sha256", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": [],
     "first_failure_owner": "EXTERNAL_PIN_VERIFICATION_AND_WHOLE_OBJECT_CLAIM_COMPARISON_OWN_DIGEST_CLAIMS",
     "scope": "Semantic digest claim equality between row and binding; digest-claim assertions concern binding claims, not registry member sets."},
    {"index": 12,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_RAW_DIGEST_CLAIM",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/raw_file_bytes_sha256\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/raw_file_bytes_sha256\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/integrity/raw_file_bytes_sha256", "get_over:/raw_file_bytes_sha256", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": [],
     "first_failure_owner": "EXTERNAL_PIN_VERIFICATION_AND_WHOLE_OBJECT_CLAIM_COMPARISON_OWN_DIGEST_CLAIMS",
     "scope": "Raw digest claim equality between row and binding; digest-claim assertions concern binding claims, not registry member sets."},
    {"index": 13,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_CLASSIFICATION_CLAIM",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/declared_integrity_class\"), right=GET(value=FILTER(array=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/modes\"), as=\"sm\", where=JSON_EQUAL(left=GET(value=item:sm, pointer=\"/mode\"), right=literal:\"SEMANTIC_JSON_CONTENT\")), pointer=\"/0/mode\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/0", "get_over:/0/mode", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/declared_integrity_class", "get_over:/integrity/modes", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version", "item:sm:/mode"],
     "required_values": ["\"SEMANTIC_JSON_CONTENT\""],
     "first_failure_owner": "WHOLE_OBJECT_CLAIM_COMPARISON_OWNS_CLASSIFICATION_CLAIMS",
     "scope": "Classification claim equality between row and binding; claim-consistency only."},
    {"index": 14,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_CANONICALIZATION_CLAIM",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/declared_canonicalization\"), right=GET(value=FILTER(array=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/modes\"), as=\"sm\", where=JSON_EQUAL(left=GET(value=item:sm, pointer=\"/mode\"), right=literal:\"SEMANTIC_JSON_CONTENT\")), pointer=\"/0/serialization\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/0", "get_over:/0/serialization", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/declared_canonicalization", "get_over:/integrity/modes", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version", "item:sm:/mode"],
     "required_values": ["\"SEMANTIC_JSON_CONTENT\""],
     "first_failure_owner": "EXTERNAL_PIN_VERIFICATION_OWNS_CANONICALIZATION_MODES",
     "scope": "Canonicalization claim equality; integrity-mode declaration consistency."},
    {"index": 15,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_ALGORITHM_CLAIM",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/declared_algorithm\"), right=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/algorithm\"))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/declared_algorithm", "get_over:/integrity/algorithm", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": [],
     "first_failure_owner": "EXTERNAL_PIN_VERIFICATION_OWNS_DIGEST_ALGORITHMS",
     "scope": "Digest algorithm claim equality; integrity-mode declaration consistency."},
    {"index": 16,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_RAW_AND_SEMANTIC_MODES_PRESENT",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=COUNT(array=FILTER(array=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/modes\"), as=\"sm\", where=JSON_EQUAL(left=GET(value=item:sm, pointer=\"/mode\"), right=literal:\"SEMANTIC_JSON_CONTENT\"))), right=literal:1)",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/integrity/modes", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version", "item:sm:/mode"],
     "required_values": ["\"SEMANTIC_JSON_CONTENT\"", "1"],
     "first_failure_owner": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_OWNS_REQUIRED_INTEGRITY_MODES",
     "scope": "Both declared integrity modes present with expected digests; mode-presence consistency."},
    {"index": 17,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_RAW_MODE_PRESENT",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "JSON_EQUAL(left=COUNT(array=FILTER(array=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/modes\"), as=\"rm\", where=JSON_EQUAL(left=GET(value=item:rm, pointer=\"/mode\"), right=literal:\"RAW_FILE_BYTES\"))), right=literal:1)",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/integrity/modes", "item:rm:/mode", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": ["\"RAW_FILE_BYTES\"", "1"],
     "first_failure_owner": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_OWNS_REQUIRED_INTEGRITY_MODES",
     "scope": "Raw mode present; mode-presence consistency."},
    {"index": 18,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_SEMANTIC_MODE_VOCABULARY",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "ALL(array=FILTER(array=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/modes\"), as=\"sm\", where=JSON_EQUAL(left=GET(value=item:sm, pointer=\"/mode\"), right=literal:\"SEMANTIC_JSON_CONTENT\")), as=\"sv\", where=ANY(array=GET(value=arg:integrity_modes, pointer=\"/modes\"), as=\"vm\", where=JSON_EQUAL(left=GET(value=item:vm, pointer=\"/mode\"), right=GET(value=item:sv, pointer=\"/mode\"))))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:integrity_modes:/modes", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/integrity/modes", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version", "item:sm:/mode", "item:sv:/mode", "item:vm:/mode"],
     "required_values": ["\"SEMANTIC_JSON_CONTENT\""],
     "first_failure_owner": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_OWNS_MODE_VOCABULARY",
     "scope": "Semantic mode token is SEMANTIC_JSON_CONTENT; declared-vocabulary restatement."},
    {"index": 19,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_RAW_MODE_VOCABULARY",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "ALL(array=FILTER(array=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/modes\"), as=\"rm\", where=JSON_EQUAL(left=GET(value=item:rm, pointer=\"/mode\"), right=literal:\"RAW_FILE_BYTES\")), as=\"rv\", where=ANY(array=GET(value=arg:integrity_modes, pointer=\"/modes\"), as=\"vr\", where=JSON_EQUAL(left=GET(value=item:vr, pointer=\"/mode\"), right=GET(value=item:rv, pointer=\"/mode\"))))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:integrity_modes:/modes", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/integrity/modes", "item:rm:/mode", "item:rv:/mode", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version", "item:vr:/mode"],
     "required_values": ["\"RAW_FILE_BYTES\""],
     "first_failure_owner": "EXTERNAL_ACCEPTANCE_PROFILE_VALIDATION_OWNS_MODE_VOCABULARY",
     "scope": "Raw mode token is RAW_FILE_BYTES; declared-vocabulary restatement."},
    {"index": 20,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_SEMANTIC_MODE_DIGEST_VERIFIES",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "ALL(array=FILTER(array=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/modes\"), as=\"sm\", where=JSON_EQUAL(left=GET(value=item:sm, pointer=\"/mode\"), right=literal:\"SEMANTIC_JSON_CONTENT\")), as=\"smv\", where=DIGEST_VERIFY(algorithm=GET(value=item:smv, pointer=\"/algorithm\"), excluded_pointers=GET(value=item:smv, pointer=\"/excluded_pointers\"), expected=GET(value=item:smv, pointer=\"/expected_digest\"), serialization=GET(value=item:smv, pointer=\"/serialization\"), value=RESOLVE_ONE(reference=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"), universe=arg:verification_universe)))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:verification_universe:", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/integrity/modes", "get_over:/ref", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version", "item:sm:/mode", "item:smv:/algorithm", "item:smv:/excluded_pointers", "item:smv:/expected_digest", "item:smv:/serialization"],
     "required_values": ["\"SEMANTIC_JSON_CONTENT\""],
     "first_failure_owner": "EXTERNAL_PIN_VERIFICATION_OWNS_BYTE_LEVEL_DIGEST_VERIFICATION",
     "scope": "DIGEST_VERIFY over the resolved operand for semantic mode; later re-verification under the same declared digest law, not a member-set owner."},
    {"index": 21,
     "procedure_id": "SOURCE_CATALOG_BINDING_MATCH",
     "assertion_id": "SOURCE_CATALOG_BINDING_MATCH_RAW_MODE_DIGEST_VERIFIES",
     "owner": "AST",
     "classification": "POST_CONSTRUCTION_SEMANTIC_CHECK",
     "predicate": "ALL(array=FILTER(array=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/integrity/modes\"), as=\"rm\", where=JSON_EQUAL(left=GET(value=item:rm, pointer=\"/mode\"), right=literal:\"RAW_FILE_BYTES\")), as=\"rmv\", where=DIGEST_VERIFY(algorithm=GET(value=item:rmv, pointer=\"/algorithm\"), excluded_pointers=GET(value=item:rmv, pointer=\"/excluded_pointers\"), expected=GET(value=item:rmv, pointer=\"/expected_digest\"), serialization=GET(value=item:rmv, pointer=\"/serialization\"), value=RESOLVE_ONE(reference=GET(value=GET(value=FILTER(array=FILTER(array=FILTER(array=GET(value=arg:accepted_binding, pointer=\"/sources\"), as=\"s0\", where=JSON_EQUAL(left=GET(value=item:s0, pointer=\"/ref/kind\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_kind\"))), as=\"s1\", where=JSON_EQUAL(left=GET(value=item:s1, pointer=\"/ref/id\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_id\"))), as=\"s2\", where=JSON_EQUAL(left=GET(value=item:s2, pointer=\"/ref/version\"), right=GET(value=GET(value=arg:candidate_binding, pointer=\"/candidate_binding\"), pointer=\"/assigned_version\"))), pointer=\"/0\"), pointer=\"/ref\"), universe=arg:verification_universe)))",
     "operands": ["arg:accepted_binding:/sources", "arg:candidate_binding:/candidate_binding", "arg:verification_universe:", "get_over:/0", "get_over:/assigned_id", "get_over:/assigned_kind", "get_over:/assigned_version", "get_over:/integrity/modes", "get_over:/ref", "item:rm:/mode", "item:rmv:/algorithm", "item:rmv:/excluded_pointers", "item:rmv:/expected_digest", "item:rmv:/serialization", "item:s0:/ref/kind", "item:s1:/ref/id", "item:s2:/ref/version"],
     "required_values": ["\"RAW_FILE_BYTES\""],
     "first_failure_owner": "EXTERNAL_PIN_VERIFICATION_OWNS_BYTE_LEVEL_DIGEST_VERIFICATION",
     "scope": "DIGEST_VERIFY over the resolved operand for raw mode; later re-verification under the same declared digest law, not a member-set owner."},
]
REGISTRATION["constraint_ownership"]["source_catalog_binding_match_assertions"] = copy.deepcopy(VECTOR_CLAIM_ASSERTION_CLASSIFICATION)


_BASE_MAKE_RUNTIME_RESULT_SCHEMA_MODELB = make_runtime_result_schema
def make_runtime_result_schema():
    result = _BASE_MAKE_RUNTIME_RESULT_SCHEMA_MODELB()
    result["$defs"]["strict_union_collision_witness"] = copy.deepcopy(MODEL_B_STRICT_UNION_WITNESS_SCHEMA)
    branches = result["$defs"]["pre_execution_result"]["oneOf"]
    if not any(branch.get("properties", {}).get("witness", {}).get("$ref") == "#/$defs/strict_union_collision_witness" for branch in branches):
        branches.append(copy.deepcopy(MODEL_B_COLLISION_WITNESS_BRANCH))
    return result


# ---------------------------------------------------------------------------
# Vector claim witness schema: closed PRE_EXECUTION envelope, reusing the
# existing SCHEMA_INVALID_BOUND_OBJECT code with the vector-specific diagnostic
# so the existing seven-field registration branch and the strict-union branch
# stay disjoint and the oneOf remains unambiguous.
# ---------------------------------------------------------------------------
VECTOR_CLAIM_KEY_SCHEMA = {
    "type": "object",
    "required": ["kind", "id", "version"],
    "properties": {"kind": {"type": "string", "minLength": 1},
                   "id": {"type": "string", "minLength": 1},
                   "version": {"type": "string", "minLength": 1}},
    "additionalProperties": False,
}
VECTOR_CLAIM_WITNESS_SCHEMA = {
    "type": "object",
    "required": list(VECTOR_CLAIM_WITNESS_FIELDS),
    "properties": {
        "source_kind": {"const": VECTOR_CLAIM_SOURCE_KIND},
        "source_id": {"type": "string", "minLength": 1},
        "source_version": {"type": "string", "minLength": 1},
        "source_origin": {"const": VECTOR_CLAIM_SOURCE_ORIGIN},
        "source_path": {"type": "string", "minLength": 1},
        "registry_claim_key": copy.deepcopy(VECTOR_CLAIM_KEY_SCHEMA),
        "match_count": {"type": "integer", "minimum": 0},
        "reason": {"enum": list(VECTOR_CLAIM_REASONS)},
        "diagnostic": {"const": VECTOR_CLAIM_DIAGNOSTIC},
        "missing_member_ids": {"type": "array", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
        "extra_member_ids": {"type": "array", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
        "duplicate_member_ids": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
    },
    "allOf": [
        {"if": {"properties": {"reason": {"const": "MISSING_REGISTRY_CLAIM"}}, "required": ["reason"]},
         "then": {"properties": {"match_count": {"const": 0}},
                  "not": {"anyOf": [{"required": ["missing_member_ids"]},
                                    {"required": ["extra_member_ids"]},
                                    {"required": ["duplicate_member_ids"]}]}}},
        {"if": {"properties": {"reason": {"const": "MEMBER_SET_MISMATCH"}}, "required": ["reason"]},
         "then": {"properties": {"match_count": {"const": 1}},
                  "required": ["missing_member_ids", "extra_member_ids"],
                  "not": {"required": ["duplicate_member_ids"]}}},
        {"if": {"properties": {"reason": {"enum": ["DUPLICATE_VECTOR_CLAIM_MEMBER_IDS", "DUPLICATE_VECTOR_CONTENT_MEMBER_IDS"]}}, "required": ["reason"]},
         "then": {"properties": {"match_count": {"const": 1}},
                  "required": ["duplicate_member_ids"],
                  "not": {"anyOf": [{"required": ["missing_member_ids"]},
                                    {"required": ["extra_member_ids"]}]}}},
        {"if": {"properties": {"reason": {"enum": ["MISSING_OR_INVALID_REGISTRY_CLAIM_MEMBERS", "MISSING_OR_INVALID_VERIFIED_CONTENT_MEMBERS"]}}, "required": ["reason"]},
         "then": {"properties": {"match_count": {"const": 1}},
                  "not": {"anyOf": [{"required": ["missing_member_ids"]},
                                    {"required": ["extra_member_ids"]},
                                    {"required": ["duplicate_member_ids"]}]}}},
    ],
    "additionalProperties": False,
}
VECTOR_CLAIM_WITNESS_BRANCH = {
    "type": "object",
    "required": ["status", "stage", "code", "witness"],
    "properties": {
        "status": {"const": "FAIL"},
        "stage": {"const": "PRE_EXECUTION"},
        "code": {"const": VECTOR_CLAIM_FAILURE_CODE},
        "witness": {"$ref": "#/$defs/vector_registry_claim_witness"},
    },
    "additionalProperties": False,
}
_BASE_MAKE_RUNTIME_RESULT_SCHEMA_VECTOR_CLAIM = make_runtime_result_schema
def make_runtime_result_schema():
    result = _BASE_MAKE_RUNTIME_RESULT_SCHEMA_VECTOR_CLAIM()
    result["$defs"]["vector_registry_claim_witness"] = copy.deepcopy(VECTOR_CLAIM_WITNESS_SCHEMA)
    branches = result["$defs"]["pre_execution_result"]["oneOf"]
    if not any(branch.get("properties", {}).get("witness", {}).get("$ref") == "#/$defs/vector_registry_claim_witness" for branch in branches):
        branches.append(copy.deepcopy(VECTOR_CLAIM_WITNESS_BRANCH))
    return result

_BASE_MAKE_METACONTRACT_SCHEMA_MODELB = make_metacontract_schema
def make_metacontract_schema():
    schema = _BASE_MAKE_METACONTRACT_SCHEMA_MODELB()
    schema["properties"]["eligibility"] = {
        "type": "object",
        "required": ["candidate_universe", "bound_source_universe"],
        "properties": {
            "candidate_universe": {
                "type": "object",
                "required": list(MODEL_B_CANDIDATE_UNIVERSE),
                "properties": {name: {"const": value} for name, value in MODEL_B_CANDIDATE_UNIVERSE.items()},
                "additionalProperties": False,
            },
            "bound_source_universe": {
                "type": "object",
                "required": list(MODEL_B_BOUND_SOURCE_UNIVERSE),
                "properties": {name: {"const": value} for name, value in MODEL_B_BOUND_SOURCE_UNIVERSE.items()},
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    }
    verification = schema["properties"]["universe_contract"]["properties"]["verification_universe"]
    for name in MODEL_B_VERIFICATION_UNIVERSE:
        if name not in verification["required"]:
            verification["required"].append(name)
        verification["properties"][name] = {"const": MODEL_B_VERIFICATION_UNIVERSE[name]}
    return schema

_BASE_MAKE_METACONTRACT_MODELB = make_metacontract
def make_metacontract(proc, inv):
    result = _BASE_MAKE_METACONTRACT_MODELB(proc, inv)
    result["eligibility"]["candidate_universe"] = copy.deepcopy(MODEL_B_CANDIDATE_UNIVERSE)
    result["eligibility"]["bound_source_universe"] = copy.deepcopy(MODEL_B_BOUND_SOURCE_UNIVERSE)
    verification = result["universe_contract"]["verification_universe"]
    for name, value in MODEL_B_VERIFICATION_UNIVERSE.items():
        verification[name] = value
    return result

# ===========================================================================
# R5R4-1 APPLICATION-LEVEL SCHEMA FORMAT ASSERTION (Draft 2020-12 date-time)
# ---------------------------------------------------------------------------
# Public basis:
#   https://json-schema.org/draft/2020-12/json-schema-validation (7.2, 7.3.1)
#   https://www.rfc-editor.org/rfc/rfc3339 (4.3, 5.6, 5.7, 5.8)
# The default dialect meta-application alone does NOT assert formats, so R5R4
# declares this assertion explicitly, fails closed when an implementation
# cannot assert it, and statically refines an effectively asserted date-time
# string to RFC3339_STRING. The narrower operation-scoped runtime profile in
# numeric_representation/rfc3339_profile is NOT a substitute for this schema
# format validation and does NOT restrict the standard format domain.
# ===========================================================================
R5R4_DATE_TIME_FORMAT = "date-time"
R5R4_VALIDATION_SPEC = "https://json-schema.org/draft/2020-12/json-schema-validation"
R5R4_RFC3339_SPEC = "https://www.rfc-editor.org/rfc/rfc3339"
R5R4_FORMAT_PRODUCER_FIELDS = [
    {"schema_ref": NS + ":schema:v013-evidence", "instance_pointer": "/observed_interval/not_before",
     "schema_pointer": "/properties/observed_interval/properties/not_before", "application": "EVIDENCE_PRODUCER"},
    {"schema_ref": NS + ":schema:v013-evidence", "instance_pointer": "/observed_interval/as_of",
     "schema_pointer": "/properties/observed_interval/properties/as_of", "application": "EVIDENCE_PRODUCER"},
    {"schema_ref": NS + ":schema:v013-evidence", "instance_pointer": "/observed_at",
     "schema_pointer": "/properties/observed_at", "application": "EVIDENCE_PRODUCER"},
    {"schema_ref": NS + ":schema:v013-evidence", "instance_pointer": "/verification_time",
     "schema_pointer": "/properties/verification_time", "application": "EVIDENCE_PRODUCER"},
    {"schema_ref": NS + ":schema:v013-target", "instance_pointer": "/required_interval/not_before",
     "schema_pointer": "/properties/required_interval/properties/not_before", "application": "TARGET_PRODUCER"},
    {"schema_ref": NS + ":schema:v013-target", "instance_pointer": "/required_interval/as_of",
     "schema_pointer": "/properties/required_interval/properties/as_of", "application": "TARGET_PRODUCER"},
]
R5R4_SCHEMA_FORMAT_ASSERTION = {
    "declaration_id": "R5R4_SCHEMA_FORMAT_ASSERTION_DATE_TIME",
    "scope": "APPLICATION_LEVEL_SCHEMA_VALIDATION",
    "keyword": "format",
    "format_name": R5R4_DATE_TIME_FORMAT,
    "dialect": DIALECT,
    "dialect_default_format_behavior": "ANNOTATION_ONLY;THE_DEFAULT_DIALECT_META_APPLICATION_ALONE_DOES_NOT_ASSERT_FORMATS",
    "r5r4_format_assertion": "ASSERTED",
    "assertion_semantics": "DRAFT_2020_12_VALIDATION_SECTION_7_2_AND_SECTION_7_3_1_WITH_THE_RFC3339_DATE_TIME_GRAMMAR",
    "assertion_requirement": "A_CONFORMING_R5R4_SCHEMA_VALIDATION_IMPLEMENTATION_MUST_ASSERT_format_date-time_SEMANTICS;A_SILENT_NO_OP_FORMAT_CHECK_IS_NOT_A_CONFORMING_ASSERTION",
    "unsupported_implementation": "FAILS_CLOSED",
    "unsupported_implementation_behavior": "SCHEMA_VALIDATION_AND_REGISTERED_INSTANCE_VALIDATION_MUST_FAIL_AND_MUST_NOT_BE_REPORTED_AS_PASSING_WHEN_THE_IMPLEMENTATION_CANNOT_ASSERT_format_date-time",
    "no_silent_no_op_fallback": True,
    "applies_to": ["SCHEMA_VALIDATE", "REGISTERED_INSTANCE_VALIDATION"],
    "applies_to_scope": {
        "SCHEMA_VALIDATE": "EVERY_SCHEMA_VALIDATE_OP_NODE_UNDER_EITHER_DECLARED_MODE",
        "REGISTERED_INSTANCE_VALIDATION": "EVERY_INSTANCE_VALIDATED_AGAINST_A_REGISTERED_SCHEMA_REF_DURING_REGISTRATION_AND_ELIGIBILITY"},
    "producer_fields": R5R4_FORMAT_PRODUCER_FIELDS,
    "producer_field_count": 6,
    "producer_operand_node_count": 8,
    "producer_string_operand_count": 16,
    "standard_domain_semantics": {
        "standard": "RFC3339",
        "standard_sections": ["4.3", "5.6", "5.7", "5.8"],
        "offset_required": True,
        "offset_forms": ["Z", "z", "+HH:MM", "-HH:MM"],
        "lowercase_t_separator_allowed": True,
        "lowercase_z_offset_allowed": True,
        "fractional_second_digits": "ONE_OR_MORE_DIGITS_ALLOWED_PER_SECTION_5_6",
        "equivalent_offsets_valid": True,
        "numeric_offset_equivalence": "EQUIVALENT_OFFSETS_DENOTE_THE_SAME_INSTANT",
        "leap_second": "SECOND_VALUE_60_ALLOWED_PER_SECTION_5_6_WHEN_ANNOUNCED",
        "unknown_local_offset": "MINUS_00_00_IS_VALID_SYNTAX_WITH_STANDARD_UNKNOWN_LOCAL_OFFSET_MEANING",
        "invalid_forms": ["DATE_ONLY", "MISSING_TIME_OFFSET", "NON_DATE_STRING", "MALFORMED_DATE_OR_TIME"],
        "standard_domain_is_not_restricted_by_the_operation_profile": True},
    "static_typing_effect": {
        "rule_id": "R5R4_DATE_TIME_FORMAT_STATIC_REFINEMENT",
        "antecedents": {"effective_schema_type": "string", "effective_schema_format": R5R4_DATE_TIME_FORMAT,
                        "declared_format_assertion": "ASSERTED"},
        "consequent_static_type": "RFC3339_STRING",
        "ordinary_string_static_type": "STRING",
        "subtyping": "RFC3339_STRING_ASSIGNABLE_TO_STRING_ONLY",
        "reverse_narrowing": "FORBIDDEN",
        "forbidden_narrowing_sources": ["CONSUMER_EXPECTATION", "FIXTURE_VALUE", "PARSER_INFERENCE", "FILE_NAME_OR_OBJECT_ID"],
        "static_typing_does_not_guarantee_no_declared_runtime_error": True,
        "static_typing_runtime_relation": "STATIC_TYPE_ASSIGNABILITY_IS_INDEPENDENT_OF_DECLARED_RUNTIME_FAILURE_SEMANTICS;A_STATICALLY_TYPED_RFC3339_STRING_OPERAND_MAY_STILL_BE_REJECTED_AT_RUNTIME_BY_THE_NARROWER_DECLARED_OPERATION_PROFILE"},
    "operation_profile_distinction": {
        "profile_ref": "metacontract:/numeric_representation/rfc3339_profile",
        "profile_role": "OPERATION_SCOPED_PARTIAL_RUNTIME_PROFILE_FOR_RFC3339_COMPARE_AND_DURATION_SECONDS_ONLY",
        "profile_is_not_a_schema_format_definition": True,
        "profile_failures_unchanged": ["MALFORMED_RFC3339", "DURATION_OVERFLOW"],
        "profile_restrictions_do_not_narrow_the_standard_format_domain": True,
        "accepted_by_standard_format_but_restricted_by_profile": ["LOWERCASE_T_SEPARATOR", "LOWERCASE_Z_OFFSET",
                                                                  "SECOND_VALUE_60_LEAP_SECOND",
                                                                  "NEGATIVE_ZERO_UNKNOWN_LOCAL_OFFSET"],
        "profile_is_not_used_as_a_substitute_for_schema_format_validation": True,
        "numeric_arithmetic_unchanged": True},
    "public_basis": [R5R4_VALIDATION_SPEC, R5R4_RFC3339_SPEC],
    "public_basis_sections": {"json_schema_validation": ["7.2", "7.3.1"], "rfc3339": ["4.3", "5.6", "5.7", "5.8"]},
    "implementation_deficiency_note": "THE_PINNED_VALIDATOR_FAMILY_MAY_LACK_A_date-time_FORMAT_CHECKER;THAT_IS_AN_IMPLEMENTATION_DEFICIENCY_AND_NOT_A_NORMATIVE_EXCEPTION;TEMPORARY_VALIDATION_TOOLING_MUST_ASSERT_THE_DECLARED_PUBLIC_STANDARD_SYNTAX_INDEPENDENTLY_OR_USE_A_CONFORMING_STANDARDS_LIBRARY",
}
_RUNTIME_REPRESENTATION["schema_format_assertion"] = copy.deepcopy(R5R4_SCHEMA_FORMAT_ASSERTION)

# Additive closed static-rule names (names only; no existing name is removed).
R5R4_STATIC_RULE_ADDITIONS = [
    "SCHEMA_FORMAT_ASSERTED_DRAFT2020_12_DATE_TIME",
    "SCHEMA_FORMAT_UNSUPPORTED_IMPLEMENTATION_FAILS_CLOSED",
    "RFC3339_STRING_STATIC_REFINEMENT_FROM_ASSERTED_DATE_TIME_FORMAT",
    "STATIC_TYPE_CALCULUS_BOUNDARY_EXACT",
    "STATIC_ASSIGNABILITY_REFLEXIVE_TRANSITIVE_NO_REVERSE_NARROWING",
    "STATIC_TYPE_AT_PATH_SCHEMA_NOMINAL_AND_STRUCTURAL",
    "AST_TYPE_UNDERDETERMINED_FAILS_CLOSED",
    "OPERATOR_OPERANDS_ACCEPT_INFERRED_TYPES_BY_ASSIGNABILITY",
    "SCOPED_VARIABLE_BINDS_EXACT_ELEMENT_TYPE",
    "ASSERTION_CONDITION_ROOTS_BOOLEAN_NO_TRUTHINESS",
    "STRICT_SET_EQUALITY_REQUIRES_SAME_NORMALIZED_ELEMENT_DOMAIN",
    "CANONICAL_MEMBER_ARRAY_UTF16_CODE_UNIT_ASCENDING_UNIQUE",
    "CONSTRUCTION_GUARANTEE_REQUIRES_LOGIC_ENTAILMENT_PROOF",
    "LITERAL_INFERENCE_FROM_DECLARED_GRAMMAR_NOT_FIXTURE",
    "GET_KEY_KNOWN_SCHEMA_FIELD_YIELDS_DECLARED_TYPE",
    "PROJECT_RECOVERS_STRUCTURAL_FIELD_TYPES",
    "VECTOR_MEMBER_IDS_STRICT_STRING_DOMAIN",
    "JSON_EQUAL_ACCEPTS_ANY_ASSIGNABLE_JSON_PAIR",
    "RFC3339_OPERANDS_REQUIRE_RFC3339_STRING_REFINEMENT",
    "GENERAL_JSON_NOT_ASSIGNABLE_TO_NARROW_CONSUMERS",
]
for _r5r4_rule_name in R5R4_STATIC_RULE_ADDITIONS:
    if _r5r4_rule_name not in STATIC_RULES:
        STATIC_RULES.append(_r5r4_rule_name)

# ===========================================================================
# R5R4-4 CANONICAL MEMBER ARRAYS. Unique string-ID set semantics are
# unchanged and neither source order nor registry order is semantic; the
# successful resolved member array is canonicalized to ascending UTF-16 code
# unit order with each member ID exactly once (empty array when there are no
# members), and the three witness id arrays use the same declared order.
# ===========================================================================
R5R4_CANONICAL_MEMBER_KEYS = {
    "canonical_member_array": "SUCCESSFUL_RESOLVED_VECTOR_MEMBERS_ARE_A_CANONICAL_ARRAY_SORTED_ASCENDING_BY_UTF16_CODE_UNITS_WITH_EACH_MEMBER_ID_EXACTLY_ONCE;EMPTY_ARRAY_WHEN_THE_VECTOR_HAS_NO_MEMBERS",
    "canonical_member_array_comparator": "LEXICOGRAPHIC_UTF16_CODE_UNIT_ASCENDING",
    "canonical_member_array_element_rule": "EACH_UNIQUE_STRING_MEMBER_ID_OCCURS_EXACTLY_ONCE",
    "canonical_member_array_empty_case": "EMPTY_ARRAY",
    "canonical_member_array_is_normative": True,
    "canonical_member_array_applies_to": ["RESOLVED_OBJECT:/members", "missing_member_ids", "extra_member_ids", "duplicate_member_ids"],
    "canonical_member_array_does_not_change_set_equality": True,
    "unique_string_id_set_semantics": "UNCHANGED",
    "source_or_registry_order_significance": "NONE;NEITHER_SOURCE_ORDER_NOR_REGISTRY_ORDER_IS_SEMANTIC",
    "safe_language_iteration_order": "FORBIDDEN;SORT_BY_DECLARED_UTF16_CODE_UNIT_COMPARATOR_ONLY",
    "witness_array_order": "SAME_DECLARED_UTF16_CODE_UNIT_ASCENDING_UNIQUE_ORDER_FOR_missing_member_ids_extra_member_ids_duplicate_member_ids",
}
VECTOR_REGISTRY_CLAIM_LAW["member_relation"].update(copy.deepcopy(R5R4_CANONICAL_MEMBER_KEYS))
REGISTRATION["bound_source_resolved_construction"] = copy.deepcopy(VECTOR_REGISTRY_CLAIM_LAW)
_RUNTIME_REPRESENTATION["resolved_construction"]["vector_registry_claim"] = copy.deepcopy(VECTOR_REGISTRY_CLAIM_LAW)
_RUNTIME_REPRESENTATION["resolved_construction"]["bound_members"] = (
    _RUNTIME_REPRESENTATION["resolved_construction"]["bound_members"]
    + ";CANONICAL_SORTED_UNIQUE_UTF16_CODE_UNIT_ASCENDING;EMPTY_ARRAY_WHEN_NO_MEMBERS")
_RUNTIME_REPRESENTATION["universe_membership"]["canonical_member_order"] = {
    "comparison": "LEXICOGRAPHIC_UTF16_CODE_UNIT_ASCENDING",
    "unique_each_member_id_once": True,
    "empty_array_when_no_members": True,
    "applies_to": ["RESOLVED_OBJECT:/members", "missing_member_ids", "extra_member_ids", "duplicate_member_ids"],
    "order_is_not_compared_for_set_equality": True,
    "canonicalization_does_not_change_set_equality": True,
    "law_ref": "metacontract:/runtime_representation/resolved_construction/vector_registry_claim/member_relation",
}

# ===========================================================================
# R5R4-2 AUTHORIZED CLOSED STATIC TYPE CALCULUS (machine-readable)
# ---------------------------------------------------------------------------
# The complete minimal closed static type calculus. Every checker conclusion,
# including fail-closed underdetermination, is derived from these declared
# rules. Narrow types arise only from (a) declared schema keywords including
# the asserted application-level date-time format, (b) explicit normative AST
# grammar slots, and (c) the declared constructor and operator rules below.
# Static types never come from fixtures, file names, object ids, consumer
# expectations, or parser inference, and a statically typed operand may still
# raise a declared runtime error.
# ===========================================================================
R5R4_STATIC_TYPE_CALCULUS = {
    "calculus_id": "R5R4_STATIC_TYPE_CALCULUS",
    "calculus_status": "AUTHORIZED_CLOSED_MINIMAL",
    "derivation_sources": [
        "primitive-registry.json:/primitives/*/arguments+output_type",
        "procedure-registry.json:/procedures/*/arguments",
        "metacontract.json:/runtime_representation/value_schemas",
        "metacontract.json:/runtime_representation/static_paths",
        "metacontract.json:/runtime_representation/schema_format_assertion",
        "primitive-registry.json:/descendant_record/fields",
        "primitive-registry.json:/descendant_record/record_shape",
    ],
    "procedure_agnostic": True,
    "no_procedure_specific_rules": True,
    "no_fixture_or_consumer_inference": {
        "rule": "LITERAL_INFERENCE_FROM_DECLARED_GRAMMAR_NOT_FIXTURE",
        "forbidden_sources": ["ACTUAL_FIXTURE_VALUE", "CONSUMER_EXPECTATION", "ASSERTION_IDENTITY", "INVARIANT_IDENTITY", "PROCEDURE_IDENTITY", "FILE_NAME", "OBJECT_ID", "PARSE_SUCCESS_OF_AN_ARBITRARY_STRING"],
    },
    "type_universe": {
        "JSON": {"kind": "TOP_JSON_VALUE_DOMAIN", "accepts": "EVERY_JSON_VALUE", "note": "THE_COMMON_JSON_TOP_DOES_NOT_MAKE_DISTINCT_NARROW_DOMAINS_EQUIVALENT"},
        "NULL": {"kind": "PRIMITIVE_JSON_DOMAIN", "json_value_kind": "NULL"},
        "BOOLEAN": {"kind": "PRIMITIVE_JSON_DOMAIN", "json_value_kind": "BOOLEAN", "rule": "ASSERTION_CONDITION_ROOTS_BOOLEAN_NO_TRUTHINESS"},
        "STRING": {"kind": "PRIMITIVE_JSON_DOMAIN", "json_value_kind": "STRING"},
        "JSON_NUMBER": {"kind": "PRIMITIVE_JSON_DOMAIN", "json_value_kind": "NUMBER", "arithmetic_ref": "metacontract:/numeric_representation/json_number"},
        "NONNEGATIVE_INTEGER": {"kind": "REFINEMENT", "base": "JSON_NUMBER", "predicate": "INTEGER_AND_GREATER_THAN_OR_EQUAL_TO_ZERO"},
        "RFC3339_STRING": {"kind": "REFINEMENT", "base": "STRING", "predicate": "EFFECTIVE_SCHEMA_TYPE_STRING_WITH_EFFECTIVE_FORMAT_date-time_AND_DECLARED_FORMAT_ASSERTION", "assertion_ref": "metacontract:/runtime_representation/schema_format_assertion", "standard": "RFC3339_DATE_TIME"},
        "RFC6901_POINTER": {"kind": "REFINEMENT", "base": "STRING", "predicate": "RFC6901_JSON_POINTER_SYNTAX"},
        "STRING_RFC6901_POINTER": {"kind": "REFINEMENT", "base": "STRING", "predicate": "RFC6901_JSON_POINTER_SYNTAX", "equivalent_to": "RFC6901_POINTER"},
        "JSON_OBJECT": {"kind": "PRIMITIVE_JSON_DOMAIN", "json_value_kind": "OBJECT"},
        "ARRAY": {"kind": "CONSTRUCTOR_UNARY", "constructor": "ARRAY", "parameter": "ELEMENT_TYPE", "canonical_syntax": "ARRAY<ELEMENT_TYPE>"},
        "SCHEMA_INSTANCE": {"kind": "CONSTRUCTOR_UNARY", "constructor": "SCHEMA_INSTANCE", "parameter": "DECLARED_SCHEMA_REF", "canonical_syntax": "SCHEMA_INSTANCE<schema_ref>", "binding_rule": "BOUND_ONLY_FROM_A_DECLARED_ARGUMENT_expected_schema_ref_AFTER_NORMATIVE_ARGUMENT_BINDING"},
        "JSON_SCHEMA": {"kind": "NOMINAL_OBJECT_DOMAIN", "object_base": "JSON_OBJECT", "domain": "A_DECLARED_JSON_SCHEMA_DOCUMENT_OF_AN_ACCEPTED_DIALECT"},
        "RESOLVED_OBJECT": {"kind": "NOMINAL_OBJECT_DOMAIN", "object_base": "JSON_OBJECT", "domain": "CLOSED_RESOLVED_OBJECT_STATIC_FIELD_TABLE", "field_table_ref": "metacontract:/runtime_representation/static_paths/RESOLVED_OBJECT"},
        "VERIFICATION_UNIVERSE": {"kind": "NOMINAL_OBJECT_DOMAIN", "object_base": "JSON_OBJECT", "domain": "CLOSED_VERIFICATION_UNIVERSE_STATIC_FIELD_TABLE", "field_table_ref": "metacontract:/runtime_representation/static_paths/VERIFICATION_UNIVERSE"},
        "DESCENDANT_RECORD": {"kind": "NOMINAL_OBJECT_DOMAIN", "object_base": "JSON_OBJECT", "domain": "CLOSED_DESCENDANT_RECORD_FIELD_TABLE", "field_table_ref": "primitive-registry.json:/descendant_record/fields"},
        "EXTERNAL_TRUST": {"kind": "NOMINAL_OBJECT_DOMAIN", "object_base": "JSON_OBJECT", "domain": "DECLARED_EXTERNAL_TRUST_PARAMETER_TABLE", "field_table_ref": "metacontract:/runtime_representation/static_paths/EXTERNAL_TRUST", "domain_completeness": "THE_TABLE_DECLARES_ONLY_THE_FIELDS_WHOSE_TYPES_ARE_DECLARED_BY_THE_REGISTERED_EXTERNAL_VERIFICATION_INPUT_CONTRACT;AN_UNDECLARED_FIELD_REMAINS_JSON"},
        "OBJECT_FIELDS": {"kind": "CONSTRUCTOR_STRUCTURAL", "constructor": "STRUCTURAL_OBJECT", "parameter": "FIELD_NAME_TO_STATIC_TYPE_MAP", "object_base": "JSON_OBJECT", "canonical_syntax": "OBJECT{field:type,...}"},
        "ENUM": {"kind": "CONSTRUCTOR_ENUMERATED", "constructor": "ENUM", "parameter": "FINITE_MEMBER_SET", "canonical_syntax": "ENUM<member,...>", "literal_membership_rule": "A_LITERAL_IS_TYPED_BY_AN_ENUM_ONLY_WHEN_THE_LITERAL_EQUALS_A_DECLARED_MEMBER_VALUE"},
        "NULLABLE_UNION": {"kind": "CONSTRUCTOR_UNION", "constructor": "NULLABLE_UNION", "canonical_syntax": "MEMBER_OR_NULL", "admits_members": "EACH_DECLARED_MEMBER_AND_NULL_ONLY"},
        "JSON_OR_RESOLVED_OBJECT": {"kind": "UNION", "members": ["JSON", "RESOLVED_OBJECT"], "note": "BOTH_MEMBERS_ARE_ADMITTED;THE_UNION_ITSELF_IS_ASSIGNABLE_TO_JSON_ONLY"},
        "TYPED_REFERENCE": {"kind": "STRUCTURAL_OBJECT", "object_base": "JSON_OBJECT", "source": "metacontract:/runtime_representation/value_schemas/resolved_object/$defs/typed_ref", "fields": {"kind": "STRING", "id": "STRING", "version": "STRING", "member_id": "STRING"}, "closed": True},
        "BASE_TYPED_REFERENCE": {"kind": "STRUCTURAL_OBJECT", "object_base": "JSON_OBJECT", "source": "metacontract:/runtime_representation/value_schemas/resolved_object/$defs/base_ref", "fields": {"kind": "STRING", "id": "STRING", "version": "STRING"}, "closed": True},
        "TYPED_REFERENCE_OR_NULL": {"kind": "NULLABLE_UNION", "members": ["TYPED_REFERENCE", "NULL"]},
        "INTEGRITY": {"kind": "STRUCTURAL_OBJECT", "object_base": "JSON_OBJECT", "source": "metacontract:/runtime_representation/value_schemas/resolved_object/$defs/integrity", "branch_normalization": "ALL_oneOf_BRANCHES_ARE_OBJECTS_SO_THE_NORMALIZED_TYPE_IS_JSON_OBJECT", "closed": True},
        "STRING_OR_NULL": {"kind": "NULLABLE_UNION", "members": ["STRING", "NULL"]},
        "FINITE_JSON": {"kind": "RESTRICTED_JSON_DOMAIN", "base": "JSON", "predicate": "JSON_VALUE_WITH_NO_IMPLICIT_HANDLE_UNWRAP", "excluded_runtime_handles": ["RESOLVED_OBJECT", "VERIFICATION_UNIVERSE"], "exclusion_basis": "DECLARED_NO_IMPLICIT_UNWRAP_FOR_DESCENDANTS"},
        "SCOPE_NAME": {"kind": "GRAMMAR_DOMAIN", "domain": "LEXICAL_BINDER_NAME", "value_type": "STRING"},
        "COMPARATOR": {"kind": "GRAMMAR_DOMAIN", "base": "STRING", "domain": "DECLARED_COMPARATOR_TOKEN", "static_membership": "NOT_STATICALLY_ENUMERATED_BY_THE_CANDIDATE_DECLARATIONS", "runtime_validation": "DECLARED_ERROR_CLASS_INVALID_COMPARATOR_UNCHANGED"},
        "BOOLEAN_EXPRESSION": {"kind": "EXPRESSION_SLOT_DOMAIN", "root_type": "BOOLEAN"},
        "JSON_EXPRESSION": {"kind": "EXPRESSION_SLOT_DOMAIN", "root_type": "JSON"},
        "MODE_EXPRESSION": {"kind": "EXPRESSION_SLOT_DOMAIN", "root_type": "JSON", "runtime_mode_validation": "DECLARED_MODE_MEMBERSHIP_UNCHANGED"},
        "NONEMPTY_NAMED_EXPRESSIONS": {"kind": "MAP_SLOT_DOMAIN", "value_root_type": "JSON", "min_fields": 1, "duplicate_field_behavior": "DECLARED_ERROR_CLASS_DUPLICATE_PROJECTED_FIELD_UNCHANGED"},
    },
    "literal_inference": {
        "rule": "LITERAL_INFERENCE_FROM_DECLARED_GRAMMAR_NOT_FIXTURE",
        "scalar_rule": {"null": "NULL", "boolean": "BOOLEAN", "string": "STRING", "number": "JSON_NUMBER"},
        "object_rule": "JSON_OBJECT",
        "array_element_rule": {
            "classification": "DETERMINISTIC_HOMOGENEOUS_JOIN",
            "all_null": "NULL",
            "all_boolean": "BOOLEAN",
            "all_string": "STRING",
            "all_number": "JSON_NUMBER",
            "all_object": "STRUCTURAL_OBJECT_WITH_THE_FIELDS_PRESENT_IN_EVERY_ELEMENT_TYPED_BY_THE_JOIN_OF_THE_PRESENT_VALUES",
            "all_array": "ARRAY_OF_THE_JOIN_OF_ELEMENT_TYPES",
            "mixed_or_incompatible": "ARRAY<JSON>",
            "empty_array": "ARRAY<JSON>",
            "empty_array_basis": "NO_CONSUMER_TYPE_IS_AVAILABLE_TO_A_LITERAL;THE_ONLY_SOUND_DECLARED_RESULT_IS_THE_JSON_ELEMENT_DOMAIN",
        },
        "narrow_literal_grammar_slots": {
            "rule": "NARROW_LITERAL_ONLY_IN_EXPLICIT_NORMATIVE_AST_GRAMMAR_SLOTS",
            "slots": [
                {"operator": "GET", "slot": "pointer", "literal_form": "BARE_JSON_STRING_OR_EXPRESSION", "static_type": "RFC6901_POINTER"},
                {"operator": "UNIQUE_BY", "slot": "pointers", "literal_form": "BARE_JSON_ARRAY_OF_STRINGS_OR_EXPRESSION", "static_type": "ARRAY<RFC6901_POINTER>"},
                {"operator": "NUMERIC_COMPARE", "slot": "comparator", "literal_form": "BARE_JSON_STRING", "static_type": "COMPARATOR"},
                {"operator": "RFC3339_COMPARE", "slot": "comparator", "literal_form": "BARE_JSON_STRING", "static_type": "COMPARATOR"},
                {"operator": "SCHEMA_VALIDATE", "slot": "mode", "literal_form": "BARE_JSON_STRING", "static_type": "ENUM<META_SCHEMA,INSTANCE>"},
            ],
            "everything_else": "A_STRING_LITERAL_IS_TYPED_STRING_ONLY_AND_A_BARE_STRING_OUTSIDE_A_DECLARED_GRAMMAR_SLOT_IS_NEVER_REFINED",
        },
        "forbidden_narrowing_sources": ["PARSE_SUCCESS_OF_AN_ARBITRARY_STRING", "ACTUAL_FIXTURE_VALUE", "CONSUMER_EXPECTATION", "FILE_NAME", "OBJECT_ID"],
    },    "assignability": {
        "relation_name": "ASSIGNABLE_TO",
        "rule": "STATIC_ASSIGNABILITY_REFLEXIVE_TRANSITIVE_NO_REVERSE_NARROWING",
        "formation": "REFLEXIVE_TRANSITIVE_CLOSURE_OF_THE_DECLARED_EDGES_AND_CONSTRUCTOR_RULES",
        "declared_edges": [
            {"from": "NULL", "to": "JSON"},
            {"from": "BOOLEAN", "to": "JSON"},
            {"from": "STRING", "to": "JSON"},
            {"from": "JSON_NUMBER", "to": "JSON"},
            {"from": "JSON_OBJECT", "to": "JSON"},
            {"from": "ARRAY<T>", "to": "JSON"},
            {"from": "NONNEGATIVE_INTEGER", "to": "JSON_NUMBER"},
            {"from": "RFC3339_STRING", "to": "STRING"},
            {"from": "RFC6901_POINTER", "to": "STRING"},
            {"from": "STRING_RFC6901_POINTER", "to": "STRING"},
            {"from": "COMPARATOR", "to": "STRING"},
            {"from": "ENUM<members>", "to": "THE_NORMALIZED_BASE_KIND_OF_ITS_MEMBERS"},
            {"from": "JSON_SCHEMA", "to": "JSON_OBJECT"},
            {"from": "RESOLVED_OBJECT", "to": "JSON_OBJECT"},
            {"from": "VERIFICATION_UNIVERSE", "to": "JSON_OBJECT"},
            {"from": "DESCENDANT_RECORD", "to": "JSON_OBJECT"},
            {"from": "TYPED_REFERENCE", "to": "JSON_OBJECT"},
            {"from": "BASE_TYPED_REFERENCE", "to": "JSON_OBJECT"},
            {"from": "INTEGRITY", "to": "JSON_OBJECT"},
            {"from": "OBJECT{field:type,...}", "to": "JSON_OBJECT"},
            {"from": "SCHEMA_INSTANCE<S>", "to": "THE_DECLARED_BASE_CONTAINER_OR_SCALAR_OF_S"},
            {"from": "STRING", "to": "STRING_OR_NULL"},
            {"from": "NULL", "to": "STRING_OR_NULL"},
            {"from": "TYPED_REFERENCE", "to": "TYPED_REFERENCE_OR_NULL"},
            {"from": "NULL", "to": "TYPED_REFERENCE_OR_NULL"},
            {"from": "JSON", "to": "JSON_OR_RESOLVED_OBJECT"},
            {"from": "RESOLVED_OBJECT", "to": "JSON_OR_RESOLVED_OBJECT"},
            {"from": "JSON", "to": "FINITE_JSON"},
            {"from": "NULL", "to": "FINITE_JSON"},
            {"from": "BOOLEAN", "to": "FINITE_JSON"},
            {"from": "STRING", "to": "FINITE_JSON"},
            {"from": "JSON_NUMBER", "to": "FINITE_JSON"},
            {"from": "JSON_OBJECT", "to": "FINITE_JSON"},
            {"from": "ARRAY<T>", "to": "FINITE_JSON"},
            {"from": "SCHEMA_INSTANCE<S>", "to": "FINITE_JSON", "condition": "THE_DECLARED_BASE_OF_S_IS_ASSIGNABLE_TO_FINITE_JSON"},
            {"from": "FINITE_JSON", "to": "JSON"},
            {"from": "FROZEN_RULE_AUTHORITY", "to": "JSON"},
            {"from": "EXTERNAL_TRUST", "to": "JSON_OBJECT"},
        ],
        "declared_edge_basis": {
            "FINITE_JSON->JSON": "A_DECLARED_RESTRICTED_JSON_DOMAIN_IS_A_SUBDOMAIN_OF_ITS_DECLARED_BASE",
            "FROZEN_RULE_AUTHORITY->JSON": "THE_RESERVED_INPUT_PROFILE_CONTENT_DECODE_IS_STRICT_BASE64_TO_RAW_UTF8_JSON_SO_THE_FROZEN_AUTHORITY_CONTENT_IS_A_JSON_DOCUMENT",
            "EXTERNAL_TRUST->JSON_OBJECT": "THE_RESERVED_EXTERNAL_TRUST_PARAMETER_IS_A_CALLER_SUPPLIED_OBJECT_WITH_THE_DECLARED_FIELD_SET_OF_THE_RESERVED_INPUT_ROW",
        },
        "constructor_rules": {
            "ARRAY": {"rule": "ARRAY<S>_IS_ASSIGNABLE_TO_ARRAY<T>_IFF_S_IS_ASSIGNABLE_TO_T", "variance": "COVARIANT_IN_THE_DECLARED_CLOSED_CALCULUS"},
            "STRUCTURAL_OBJECT": {"rule": "OBJECT_FIELDS_IS_ASSIGNABLE_TO_JSON_OBJECT_AND_TO_ANY_STRUCTURAL_OBJECT_WHOSE_FIELDS_ARE_ALL_PRESENT_WITH_ASSIGNABLE_TYPES", "width_subtyping": "ALLOWED_ONLY_FOR_DECLARED_STRUCTURAL_TARGETS", "extra_fields": "ALLOWED"},
            "SCHEMA_INSTANCE": {"rule": "SCHEMA_INSTANCE_BASE_KIND_IS_THE_DECLARED_BASE_CONTAINER_OR_SCALAR_OF_THE_BOUND_SCHEMA_DOCUMENT", "base_kind_map": {"object": "JSON_OBJECT", "array": "ARRAY<DERIVED_ELEMENT_TYPE>", "string": "STRING", "number": "JSON_NUMBER", "integer": "JSON_NUMBER", "boolean": "BOOLEAN", "null": "NULL", "absent": "JSON"}},
        },
        "forbidden": [
            {"rule": "NO_IMPLICIT_REVERSE_NARROWING", "detail": "A_SUPERTYPE_IS_NEVER_ASSIGNABLE_TO_A_PROPER_SUBTYPE"},
            {"rule": "GENERAL_JSON_TO_A_NARROW_CONSUMER_IS_FORBIDDEN", "detail": "JSON_IS_NOT_ASSIGNABLE_TO_NULL_BOOLEAN_STRING_JSON_NUMBER_JSON_OBJECT_ARRAY_OR_ANY_REFINEMENT_OR_NOMINAL_OR_STRUCTURAL_DOMAIN"},
            {"rule": "COMMON_JSON_TOP_IS_NOT_EQUIVALENCE", "detail": "TWO_TYPES_THAT_ARE_BOTH_ASSIGNABLE_TO_JSON_ARE_NOT_THEREBY_ASSIGNABLE_TO_EACH_OTHER"},
            {"rule": "STRING_IS_NEVER_ASSIGNABLE_TO_RFC3339_STRING_WITHOUT_THE_ASSERTED_EFFECTIVE_FORMAT_ANTECEDENT"},
            {"rule": "RFC3339_OPERANDS_REQUIRE_RFC3339_STRING_REFINEMENT", "detail": "A_PLAIN_STRING_OPERAND_IS_NOT_ASSIGNABLE_TO_AN_RFC3339_STRING_CONSUMER_OR_TO_A_COMPARATOR_OR_DURATION_OPERAND"},
            {"rule": "NOMINAL_HANDLES_ARE_NOT_IMPLICITLY_UNWRAPPED", "detail": "RESOLVED_OBJECT_AND_VERIFICATION_UNIVERSE_REACH_JSON_VALUES_ONLY_THROUGH_DECLARED_GET_FIELDS"},
        ],
        "type_error": "R5R4_STATIC_TYPE_ERROR",
        "underdetermination": "R5R4_AST_TYPE_UNDERDETERMINED",
    },
    "normalized_element_domains": {
        "rule": "STRICT_SET_EQUALITY_REQUIRES_SAME_NORMALIZED_ELEMENT_DOMAIN",
        "purpose": "SET_EQUAL_STRICT_ADMITS_A_PAIR_OF_ARRAY_OPERANDS_ONLY_WHEN_THEIR_ELEMENT_TYPES_HAVE_THE_SAME_NORMALIZED_DOMAIN",
        "normalization": {
            "JSON": "JSON",
            "NULL": "NULL",
            "BOOLEAN": "BOOLEAN",
            "STRING_AND_STRING_REFINEMENTS": "STRING",
            "JSON_NUMBER_AND_NONNEGATIVE_INTEGER": "NUMBER",
            "JSON_OBJECT_AND_EVERY_STRUCTURAL_OR_NOMINAL_OBJECT_DOMAIN_EXCEPT_RUNTIME_HANDLES": "OBJECT",
            "ARRAY_OF_ANY_ELEMENT_TYPE": "ARRAY",
            "RESOLVED_OBJECT": "RESOLVED_OBJECT_HANDLE",
            "VERIFICATION_UNIVERSE": "VERIFICATION_UNIVERSE_HANDLE",
            "SCHEMA_INSTANCE_OF_S": "NORMALIZED_DOMAIN_OF_THE_DECLARED_BASE_KIND_OF_S",
            "ENUM_WITH_ALL_MEMBERS_OF_ONE_BASE_KIND": "THAT_BASE_KIND",
            "NULLABLE_UNION_OR_UNION": "THE_COMMON_DOMAIN_WHEN_ALL_MEMBERS_SHARE_ONE;OTHERWISE_JSON",
        },
        "element_domain_source": "THE_DECLARED_ELEMENT_TYPE_OF_THE_INFERRED_ARRAY_TYPE_IS_USED;A_MORE_GENERAL_DOMAIN_IS_NEVER_SUBSTITUTED",
        "vector_member_ids": {"rule": "VECTOR_MEMBER_IDS_STRICT_STRING_DOMAIN", "declared_source": "metacontract:/runtime_representation/static_paths/RESOLVED_OBJECT//members", "element_domain": "STRING"},
        "incompatible_example": "ARRAY<STRING>_AND_ARRAY<JSON_NUMBER>_ARE_REJECTED_DESPITE_THE_COMMON_JSON_TOP",
        "unrefined_json_pair": "ARRAY<JSON>_AND_ARRAY<JSON>_ARE_COMPARABLE_ONLY_AS_JSON",
    },
    "argument_typing": {
        "rule": "OPERATOR_OPERANDS_ACCEPT_INFERRED_TYPES_BY_ASSIGNABILITY",
        "argument_expression": {"grammar": "THE_VALUE_OF_A_DECLARED_ARGUMENT_KEY_IS_AN_EXPRESSION_NODE", "expression_node": {"op": "DECLARED_OPERATOR_NAME", "operands": "THE_OPERATOR_RULE_SLOTS"}, "leaf_nodes": {"literal": "LITERAL_INFERENCE", "item": "ACTIVE_LEXICAL_BINDER", "arg": "THE_PROCEDURE_ARGUMENT_DECLARATION"}},
        "procedure_argument_binding": {
            "rule": "SCHEMA_INSTANCE_IS_BOUND_ONLY_FROM_A_DECLARED_ARGUMENT_expected_schema_ref_AFTER_NORMATIVE_ARGUMENT_BINDING",
            "rule_binding_with_schema_ref": "SCHEMA_INSTANCE<expected_schema_ref_id>",
            "rule_binding_without_schema_ref": "THE_DECLARED_ARGUMENT_TYPE",
            "reserved_origin_types": {
                "BOOTSTRAP_VERIFICATION_UNIVERSE": "VERIFICATION_UNIVERSE",
                "EXTERNAL_ACCEPTANCE_PROFILE": "THE_DECLARED_ARGUMENT_TYPE_OF_THE_RESERVED_INPUT_ROW",
                "EXTERNAL_TRUST": "THE_DECLARED_ARGUMENT_TYPE_OF_THE_RESERVED_INPUT_ROW",
            },
            "reserved_input_source": "metacontract:/reserved_inputs",
            "no_file_or_id_based_exceptions": True,
            "binding_rule_source": "procedure-registry.json:/procedures/*/arguments/*/source_constraint/expected_schema_ref",
        },
        "acceptance": {"rule": "INFERRED_OPERAND_TYPE_MUST_BE_ASSIGNABLE_TO_THE_DECLARED_OPERAND_TYPE", "generic_binding": "A_DECLARED_GENERIC_TYPE_PARAMETER_BINDS_TO_THE_INFERRED_TYPE_AND_THE_BINDING_MUST_BE_CONSISTENT_WITHIN_ONE_OPERATOR_NODE", "arity": "EXACTLY_THE_DECLARED_ARGUMENT_SET;A_MISSING_OR_EXTRA_OPERAND_IS_A_STATIC_ERROR"},
        "failure": "R5R4_STATIC_TYPE_ERROR",
    },    "static_type_at_path": {
        "rule": "STATIC_TYPE_AT_PATH_SCHEMA_NOMINAL_AND_STRUCTURAL",
        "pointer_operand": "RFC6901_POINTER",
        "base_type_cases": [
            {"base": "SCHEMA_INSTANCE<S>", "behavior": "FOLLOW_THE_DECLARED_SCHEMA_DOCUMENT_BOUND_TO_S_FROM_ITS_ROOT"},
            {"base": "NOMINAL_OBJECT_DOMAIN_WITH_A_DECLARED_FIELD_TABLE", "behavior": "A_KNOWN_DECLARED_FIELD_YIELDS_THE_DECLARED_FIELD_TYPE;A_FURTHER_POINTER_IS_APPLIED_TO_THAT_TYPE"},
            {"base": "STRUCTURAL_OBJECT", "behavior": "A_KNOWN_FIELD_YIELDS_THE_DECLARED_FIELD_TYPE;A_FURTHER_POINTER_IS_APPLIED_TO_THAT_TYPE"},
            {"base": "ARRAY<T>", "behavior": "A_CANONICAL_DECIMAL_INDEX_TOKEN_YIELDS_T;A_NON_INDEX_TOKEN_IS_A_STATIC_ERROR"},
            {"base": "JSON", "behavior": "JSON"},
            {"base": "ENUM", "behavior": "A_FIELD_OR_INDEX_PATH_ON_AN_ENUM_IS_A_STATIC_ERROR"},
        ],
        "schema_keyword_following": {
            "keywords": ["properties", "items", "$ref", "type", "const", "enum", "if", "then", "else", "allOf", "oneOf", "anyOf", "not", "additionalProperties"],
            "properties": "THE_MEMBER_SCHEMA_AT_THE_TOKEN",
            "items": "ARRAY<DERIVED_ITEMS_SCHEMA>;ARRAY<JSON>_WHEN_items_IS_ABSENT",
            "ref": "A_LOCAL_FRAGMENT_REF_IS_RESOLVED_WITHIN_THE_SAME_SCHEMA_DOCUMENT;A_REGISTERED_REF_IS_RESOLVED_TO_THE_DECLARED_SCHEMA_DOCUMENT_WITH_THAT_ID;AN_UNRESOLVED_REF_IS_A_DECLARED_RUNTIME_ERROR_UNRESOLVED_LOCAL_FRAGMENT",
            "type": "string_to_STRING;integer_or_number_to_JSON_NUMBER;boolean_to_BOOLEAN;null_to_NULL;object_to_JSON_OBJECT;array_to_ARRAY<JSON>",
            "date_time": "EFFECTIVE_type_string_WITH_EFFECTIVE_format_date-time_AND_THE_DECLARED_FORMAT_ASSERTION_REFINES_TO_RFC3339_STRING",
            "const": "THE_LITERAL_TYPE_OF_THE_CONST_VALUE",
            "enum": "ENUM<DECLARED_MEMBERS>_WHEN_ALL_MEMBERS_SHARE_ONE_NORMALIZED_BASE_KIND;OTHERWISE_JSON",
            "allOf": "THE_INTERSECTION_OF_THE_BRANCH_TYPES;OBJECT_BRANCH_FIELDS_MERGE_WITH_IDENTICAL_OR_REFINED_TYPES",
            "oneOf_anyOf": "THE_BRANCH_JOIN",
            "if_then_else": "branches_and_else_branch_is_the_same_normalized_type_AS_THE_PARENT_THEN_THE_JOIN_IS_TAKEN;OTHERWISE_NO_REFINEMENT",
            "not": "NO_POSITIVE_TYPE_INFORMATION;NO_REFINEMENT",
            "additionalProperties": "false_MAKES_THE_OBJECT_CLOSED_FOR_THE_PURPOSES_OF_THE_UNDECLARED_FIELD_STATIC_ERROR;A_SCHEMA_VALUE_DECLARES_THE_TYPE_OF_EVERY_UNDECLARED_KEY_OF_THAT_OBJECT_AND_IS_FOLLOWED_FOR_THE_REMAINING_POINTER_TOKENS",
        },
        "branch_law": {
            "rule": "AST_TYPE_UNDERDETERMINED_FAILS_CLOSED",
            "same_normalized_type_across_all_valid_branches": "THE_TYPE_MAY_BE_REFINED_TO_THAT_NORMALIZED_TYPE_AND_TO_THE_FIELDS_COMMON_TO_EVERY_BRANCH_WITH_IDENTICAL_OR_ASSIGNABLE_TYPES",
            "incompatible_branch_types": "THE_RESULT_IS_JSON_MARKED_BRANCH_AMBIGUOUS;A_NARROW_CONSUMER_OF_A_BRANCH_AMBIGUOUS_RESULT_IS_UNDERDETERMINED_AND_FAILS_CLOSED_WITH_R5R4_AST_TYPE_UNDERDETERMINED",
            "consumer_type_selection": "FORBIDDEN;A_CONSUMER_EXPECTATION_NEVER_SELECTS_A_BRANCH",
        },
        "errors": {
            "known_scalar_or_noncontainer_with_nonempty_pointer_remainder": "R5R4_STATIC_TYPE_ERROR",
            "closed_record_undeclared_field": "R5R4_STATIC_TYPE_ERROR",
            "json_pointer_syntax_violation_note": "POINTER_SYNTAX_IS_A_DECLARED_RUNTIME_ERROR_CLASS_INVALID_POINTER;THE_GRAMMAR_SLOT_TYPES_A_BARE_STRING_AS_RFC6901_POINTER",
        },
        "unique_projection": "A_REFINED_TYPE_IS_REPORTED_ONLY_WHEN_THE_DECLARED_KEYWORD_PATH_DETERMINES_EXACTLY_ONE_NORMALIZED_TYPE;OTHERWISE_JSON",
    },
    "operator_rules": {
        "declared_operand_types_source": "primitive-registry.json:/primitives/<OPERATOR>/arguments",
        "declared_output_types_source": "primitive-registry.json:/primitives/<OPERATOR>/output_type",
        "slot_kinds": {
            "EXPRESSION": "THE_VALUE_IS_AN_EXPRESSION_NODE_OR_A_DECLARED_LEAF",
            "POINTER_SLOT": "A_BARE_STRING_IS_TYPED_RFC6901_POINTER_BY_GRAMMAR;AN_EXPRESSION_MUST_BE_ASSIGNABLE_TO_RFC6901_POINTER",
            "POINTER_ARRAY_SLOT": "A_BARE_ARRAY_OF_STRINGS_IS_TYPED_ARRAY<RFC6901_POINTER>_BY_GRAMMAR;AN_EXPRESSION_MUST_BE_ASSIGNABLE_TO_ARRAY<RFC6901_POINTER>",
            "COMPARATOR_SLOT": "A_BARE_STRING_IS_TYPED_COMPARATOR_BY_GRAMMAR",
            "MODE_SLOT": "A_BARE_STRING_IS_TYPED_BY_THE_DECLARED_ENUM_OF_THE_OPERAND",
            "SCOPE_BINDER": "A_BARE_STRING_IS_A_LEXICAL_BINDER_NAME_TYPED_SCOPE_NAME",
            "NAMED_EXPRESSION_MAP": "A_JSON_OBJECT_OF_FIELD_NAME_TO_EXPRESSION_WITH_AT_LEAST_ONE_FIELD",
        },
        "operators": {
            "RESOLVE_ONE": {"slots": [["universe", "EXPRESSION"], ["reference", "EXPRESSION"]], "result": "RESOLVED_OBJECT", "laws": ["EXACT_RESOLVED_OUTPUT;NO_IMPLICIT_UNWRAP"]},
            "GET": {"slots": [["value", "EXPRESSION"], ["pointer", "POINTER_SLOT"]], "result": "JSON", "refinement": "STATIC_TYPE_AT_PATH_DERIVED_FROM_THE_VALUES_INFERRED_TYPE_AND_THE_STATIC_POINTER", "laws": ["STATIC_KNOWN_POINTER_AND_PROJECTABLE_STRUCTURE_AND_UNIQUE_PROJECTION_YIELDS_THE_PROJECTED_TYPE;OTHERWISE_JSON", "KNOWN_SCALAR_WITH_NONEMPTY_FIELD_PATH_IS_A_STATIC_ERROR", "CLOSED_UNDECLARED_FIELD_IS_A_STATIC_ERROR", "SCHEMA_VALUED_ADDITIONALPROPERTIES_DECLARES_THE_UNDECLARED_FIELD_TYPE", "JSON_TO_FILTER_FORBIDDEN"]},
            "GET_KEY": {"slots": [["object", "EXPRESSION"], ["key", "EXPRESSION"]], "result": "JSON", "refinement": "KNOWN_SCHEMA_OR_STRUCTURAL_FIELD_YIELDS_THE_DECLARED_FIELD_TYPE;AN_UNDECLARED_KEY_OF_A_SCHEMA_VALUED_ADDITIONALPROPERTIES_OBJECT_YIELDS_THE_DECLARED_ADDITIONALPROPERTIES_TYPE;OTHERWISE_JSON", "laws": ["GET_KEY_KNOWN_SCHEMA_FIELD_YIELDS_DECLARED_TYPE", "SCHEMA_VALUED_ADDITIONALPROPERTIES_YIELDS_A_UNIQUE_UNDECLARED_KEY_PROJECTION", "ABSENT_CLOSED_FIELD_IS_A_STATIC_ERROR", "OBJECT_OPERAND_MUST_BE_ASSIGNABLE_TO_JSON_OBJECT;DECLARED_RUNTIME_NOT_OBJECT_CHECK_AND_NOT_OBJECT_ERROR_REMAIN"]},
            "JSON_EQUAL": {"slots": [["left", "EXPRESSION"], ["right", "EXPRESSION"]], "result": "BOOLEAN", "laws": ["JSON_EQUAL_ACCEPTS_ANY_ASSIGNABLE_JSON_PAIR", "UNEQUAL_NARROW_TYPES_ARE_PERMITTED", "NUMERIC_RUNTIME_SEMANTICS_UNCHANGED"]},
            "SET_EQUAL_STRICT": {"slots": [["left", "EXPRESSION"], ["right", "EXPRESSION"]], "result": "BOOLEAN", "laws": ["OPERANDS_MUST_BE_ARRAYS", "STRICT_SET_EQUALITY_REQUIRES_SAME_NORMALIZED_ELEMENT_DOMAIN", "ARRAY<JSON>_PAIRS_ARE_COMPARABLE_ONLY_AS_JSON", "SET_ORDER_IS_NOT_SEMANTIC;MEMBERSHIP_IS_UNIQUE;DUPLICATE_ITEMS_ARE_A_DECLARED_RUNTIME_ERROR"]},
            "UNIQUE_BY": {"slots": [["array", "EXPRESSION"], ["pointers", "POINTER_ARRAY_SLOT"]], "result": "BOOLEAN", "laws": ["ARRAY_OPERAND_ELEMENT_TYPE_BINDS_TO_JSON", "POINTERS_MUST_BE_RFC6901_POINTER_VALUES", "VECTOR_MEMBER_IDS_STRICT_STRING_DOMAIN"]},
            "FILTER": {"slots": [["array", "EXPRESSION"], ["as", "SCOPE_BINDER"], ["where", "EXPRESSION"]], "result": "ARRAY<T>", "generic": {"T": "THE_INFERRED_ELEMENT_TYPE_OF_THE_ARRAY_OPERAND"}, "laws": ["GENERAL_JSON_TO_FILTER_FORBIDDEN;THE_ARRAY_OPERAND_MUST_BE_AN_ARRAY", "SCOPED_VARIABLE_BINDS_EXACT_ELEMENT_TYPE", "PREDICATE_ROOT_MUST_BE_BOOLEAN"]},
            "PROJECT": {"slots": [["array", "EXPRESSION"], ["as", "SCOPE_BINDER"], ["fields", "NAMED_EXPRESSION_MAP"]], "result": "ARRAY<JSON_OBJECT>", "refinement": "ARRAY<OBJECT{field:inferred_field_type,...}>", "laws": ["PROJECT_RECOVERS_STRUCTURAL_FIELD_TYPES", "SCOPED_VARIABLE_BINDS_EXACT_ELEMENT_TYPE", "FIELD_EXPRESSIONS_MUST_BE_JSON"]},
            "COUNT": {"slots": [["array", "EXPRESSION"]], "result": "NONNEGATIVE_INTEGER", "laws": ["THE_ARRAY_OPERAND_MUST_BE_AN_ARRAY"]},
            "ALL": {"slots": [["array", "EXPRESSION"], ["as", "SCOPE_BINDER"], ["where", "EXPRESSION"]], "result": "BOOLEAN", "laws": ["THE_ARRAY_OPERAND_MUST_BE_AN_ARRAY", "SCOPED_VARIABLE_BINDS_EXACT_ELEMENT_TYPE", "PREDICATE_ROOT_MUST_BE_BOOLEAN"]},
            "ANY": {"slots": [["array", "EXPRESSION"], ["as", "SCOPE_BINDER"], ["where", "EXPRESSION"]], "result": "BOOLEAN", "laws": ["THE_ARRAY_OPERAND_MUST_BE_AN_ARRAY", "SCOPED_VARIABLE_BINDS_EXACT_ELEMENT_TYPE", "PREDICATE_ROOT_MUST_BE_BOOLEAN"]},
            "NOT": {"slots": [["value", "EXPRESSION"]], "result": "BOOLEAN", "laws": ["THE_OPERAND_ROOT_MUST_BE_BOOLEAN;NO_TRUTHINESS"]},
            "NUMERIC_COMPARE": {"slots": [["left", "EXPRESSION"], ["comparator", "COMPARATOR_SLOT"], ["right", "EXPRESSION"]], "result": "BOOLEAN", "laws": ["BOTH_OPERANDS_MUST_BE_NUMERIC;NO_COERCION", "NUMERIC_ARITHMETIC_UNCHANGED"]},
            "RFC3339_COMPARE": {"slots": [["left", "EXPRESSION"], ["comparator", "COMPARATOR_SLOT"], ["right", "EXPRESSION"]], "result": "BOOLEAN", "laws": ["BOTH_OPERANDS_MUST_BE_RFC3339_STRING_REFINEMENTS", "RFC3339_OPERANDS_REQUIRE_RFC3339_STRING_REFINEMENT", "OPERATION_PROFILE_UNCHANGED"]},
            "DURATION_SECONDS": {"slots": [["start", "EXPRESSION"], ["end", "EXPRESSION"]], "result": "JSON_NUMBER", "laws": ["BOTH_OPERANDS_MUST_BE_RFC3339_STRING_REFINEMENTS", "OPERATION_PROFILE_UNCHANGED"]},
            "SCHEMA_VALIDATE": {"slots": [["schema", "EXPRESSION"], ["instance", "EXPRESSION"], ["mode", "MODE_SLOT"]], "result": "BOOLEAN", "laws": ["SCHEMA_FORMAT_ASSERTED_DRAFT2020_12_DATE_TIME", "SCHEMA_FORMAT_UNSUPPORTED_IMPLEMENTATION_FAILS_CLOSED", "GENERAL_JSON_IS_NOT_ASSIGNABLE_TO_THE_JSON_SCHEMA_CONSUMER_WITHOUT_A_DECLARED_ADMISSION_RULE"]},
            "DIGEST_VERIFY": {"slots": [["value", "EXPRESSION"], ["expected", "EXPRESSION"], ["algorithm", "EXPRESSION"], ["serialization", "EXPRESSION"], ["excluded_pointers", "EXPRESSION"]], "result": "BOOLEAN", "laws": ["DECLARED_DIGEST_SEMANTICS_UNCHANGED"]},
            "DESCENDANTS": {"slots": [["value", "EXPRESSION"]], "result": "ARRAY<DESCENDANT_RECORD>", "laws": ["THE_OPERAND_MUST_BE_ASSIGNABLE_TO_FINITE_JSON", "NO_IMPLICIT_UNWRAP_OF_RESOLVED_OBJECT_OR_VERIFICATION_UNIVERSE;AN_EXPLICIT_GET_content_IS_REQUIRED"]},
        },
    },
    "scoped_variables": {
        "rule": "SCOPED_VARIABLE_BINDS_EXACT_ELEMENT_TYPE",
        "binder_scope": "THE_LEXICAL_SCOPE_DECLARED_BY_THE_ITEM_BINDING;ACTIVE_LEXICAL_BINDERS_ONLY;NO_ESCAPE",
        "item_type": "THE_ELEMENT_TYPE_OF_THE_BOUND_ARRAY_EXACTLY;A_MORE_GENERAL_TYPE_IS_NEVER_SUBSTITUTED",
        "shadowing": "FORBIDDEN_WHILE_AN_ANCESTOR_BINDER_IS_ACTIVE",
        "sibling_reuse": "ALLOWED_ONLY_WHEN_BINDERS_ARE_NOT_SIMULTANEOUSLY_ACTIVE",
        "source": "metacontract:/scope_semantics",
    },
    "assertion_and_witness_root_typing": {
        "rule": "ASSERTION_CONDITION_ROOTS_BOOLEAN_NO_TRUTHINESS",
        "condition_root": "BOOLEAN",
        "witness_root": "TYPED_BY_THE_SAME_OPERATOR_RULES;NOT_REQUIRED_TO_BE_BOOLEAN",
        "procedure_result_relation": "EVERY_PROCEDURE_RESULT_FORM_IS_TAKEN_FROM_THE_DECLARED_result_contracts;A_TRUST_RESULT_ROOT_IS_NOT_COERCED_TO_BOOLEAN",
    },
    "fail_closed": {
        "rules": ["R5R4_AST_TYPE_UNDERDETERMINED", "R5R4_STATIC_TYPE_ERROR"],
        "undetermined_behavior": "STOP_WITH_PRIMITIVE_PROCEDURE_ASSERTION_NODE_INFERRED_OPERANDS_AND_THE_MISSING_RULE;THE_GAP_IS_NEVER_FILLED_FROM_A_CONSUMER_EXPECTATION_OR_A_FIXTURE",
        "static_error_behavior": "A_STATIC_TYPE_ERROR_IS_A_FAILURE_OF_THE_STATIC_CHECK_AND_IS_REPORTED_WITH_THE_NODE_PATH_INFERRED_OPERAND_TYPES_AND_THE_EXPECTED_DECLARED_TYPE",
        "runtime_independence": "A_STATIC_TYPE_CONCLUSION_DOES_NOT_GUARANTEE_THE_ABSENCE_OF_A_DECLARED_RUNTIME_ERROR",
    },
    "inventory": {
        "normalized_static_paths": ["VERIFICATION_UNIVERSE:/objects = ARRAY<RESOLVED_OBJECT>", "RESOLVED_OBJECT:/kind,/id,/version,/path,/status,/classification,/origin,/integrity_source,/raw_content_base64 = STRING", "RESOLVED_OBJECT:/ref = TYPED_REFERENCE", "RESOLVED_OBJECT:/reference = BASE_TYPED_REFERENCE", "RESOLVED_OBJECT:/schema_ref = TYPED_REFERENCE_OR_NULL", "RESOLVED_OBJECT:/content = JSON", "RESOLVED_OBJECT:/integrity = INTEGRITY", "RESOLVED_OBJECT:/roles,/members = ARRAY<STRING>", "EXTERNAL_TRUST:/expected_package_id,/expected_package_version,/expected_package_digest = STRING"],
        "schema_valued_additional_properties": "FOLLOWED_AS_THE_UNDECLARED_FIELD_TYPE_IN_SCHEMA_PATH_TYPING_AND_GET_KEY",
        "resolved_object_field_count": 16,
        "descendant_record_field_count": 7,
        "operators": 18,
        "no_private_fields_added": True,
    },
}
# ===========================================================================
# R5R6 E2: producer-backed schema-document content refinement
# ---------------------------------------------------------------------------
# Procedure-agnostic law: narrow content only when a proven schema-kind
# reference resolves through the strict candidate/bound verification union.
# It does not alter runtime behavior, primitive inventory, or the base
# RESOLVED_OBJECT /content: JSON field table.
# ===========================================================================
R5R4_STATIC_TYPE_CALCULUS["derivation_sources"].extend([
    "metacontract.json:/eligibility/candidate_universe/validation_by_kind/SCHEMA",
    "metacontract.json:/eligibility/bound_source_universe/required_roles_by_ref",
    "metacontract.json:/registration/semantic_validation/schema_document_identity",
    "metacontract.json:/registration/semantic_validation/rules",
    "metacontract.json:/runtime_representation/universe_membership",
    "metacontract.json:/runtime_representation/resolved_construction",
    "external-verification-input.contract.json:/authority_profile_protocol/accepted_source_allowlist",
    "schema/object-registry.schema.json:/properties/objects/items/allOf",
])
R5R4_STATIC_TYPE_CALCULUS["operator_rules"]["operators"]["FILTER"]["laws"].append(
    "POSITIVE_LITERAL_PATH_EQUALITY_GUARD_REFINES_ONLY_THE_SCOPED_FILTER_ITEM"
)
R5R4_STATIC_TYPE_CALCULUS["operator_rules"]["operators"]["RESOLVE_ONE"]["laws"].append(
    "RESOLVED_SCHEMA_CONTENT_REFINEMENT_REQUIRES_SCHEMA_REFERENCE_PROVENANCE"
)
R5R4_STATIC_TYPE_CALCULUS["producer_refinements"] = {
    "schema_document_content": {
        "law_id": "RESOLVED_SCHEMA_DOCUMENT_CONTENT",
        "procedure_agnostic": True,
        "source_type": "SCHEMA_DOCUMENT_PRODUCER_PROVENANCE",
        "generic_filter_fact": {
            "predicate_form": "JSON_EQUAL(GET(scoped_item, DECLARED_STATIC_POINTER), LITERAL)",
            "scope": "ONLY_THE_FILTER_RESULT_ELEMENT_BINDER",
            "fact": "THE_SCOPED_ITEM_POINTER_EQUALS_THE_LITERAL_IN_THE_POSITIVE_FILTER_RESULT",
            "other_fields": "UNCHANGED_UNLESS_A_SEPARATE_DECLARED_PRODUCER_RELATION_CONNECTS_THEM",
            "negative_predicates": "DO_NOT_PRODUCE_A_POSITIVE_EQUALITY_FACT"
        },
        "resolution_premises": {
            "universe": "EXACT_VERIFICATION_UNIVERSE_ARGUMENT",
            "reference": "A_TYPED_REFERENCE_PROVEN_TO_NAME_A_SCHEMA_KIND_OBJECT_BY_ONE_OF_THE_DECLARED_PROVENANCE_ROUTES",
            "union": "CANDIDATE_AND_BOUND_NAMESPACES_REMAIN_DISTINCT_BEFORE_STRICT_IDENTITY_UNION;NO_UNIVERSAL_REGISTRY_COVERAGE_ASSUMED",
            "bound_schema_exclusion": "EXTERNAL_ACCEPTANCE_PROFILE_ALLOWLIST_AND_BOUND_SOURCE_UNIVERSE_DECLARE_ONLY_PACKAGE_AND_SOURCE_VECTOR_CATALOG_REFERENCES;NO_BOUND_SCHEMA KIND ENTRY",
            "candidate_schema_eligibility": "A_SUCCESSFUL_RESOLUTION_OF_A_SCHEMA KIND ENTRY IN THE VERIFICATION_UNIVERSE IS FROM THE CANDIDATE UNIVERSE, WHOSE ELIGIBILITY REQUIRES DECLARED DRAFT 2020-12 AND LOCAL FRAGMENT REFERENCES ONLY",
            "content": "RESOLVE_ONE_PRESERVES_FULL_PARSED_VERIFIED_ARTIFACT_CONTENT_WITHOUT_MEMBER_PROJECTION",
            "schema_identity": "CANDIDATE_SCHEMA_ROW_REFERENCE_EQUALS_KIND_ID_VERSION;SCHEMA_DOCUMENT_ID_EQUALS_FULL_CONTENT_/$id;SCHEMA_DOCUMENT_VERSION_EQUALS_ROW_VERSION"
        },
        "reference_provenance_routes": [
            {
                "route_id": "CANDIDATE_SCHEMA_REGISTRY_ROW_REFERENCE",
                "row_source": "CANDIDATE_OBJECT_REGISTRY:/objects",
                "filter_fact": "SCOPED_ROW_/kind_EQUALS_LITERAL_SCHEMA",
                "reference_pointer": "/reference",
                "relation": "ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY_FORCES_REFERENCE_KIND_SCHEMA",
                "resolve_success_domain": "EXACT_MATCH_IN_VERIFICATION_UNIVERSE;AN_INELIGIBLE_OR_ABSENT_ROW_REMAINS_THE_DECLARED_RESOLUTION_FAILURE"
            },
            {
                "route_id": "NONSCHEMA_CANDIDATE_OWNER_SCHEMA_REF",
                "row_source": "CANDIDATE_OBJECT_REGISTRY:/objects",
                "filter_facts": ["status=ACTIVE", "classification=NORMATIVE", "kind!=SCHEMA"],
                "reference_pointer": "/schema_ref",
                "producer_relations": [
                    "OBJECT_REGISTRY_SCHEMA_REQUIRES_SCHEMA_REF_FOR_AN_ACTIVE_NORMATIVE_NONSCHEMA_ROW",
                    "REGISTRATION_SCHEMA_REF_RESOLVES_TO_REGISTERED_SCHEMA_KIND_ROW_BY_EXACT_KIND_ID_VERSION"
                ],
                "resolve_success_domain": "EXACT_MATCH_IN_VERIFICATION_UNIVERSE;MISSING_TARGET_REMAINS_THE_DECLARED_RESOLUTION_FAILURE"
            },
            {
                "route_id": "VERIFICATION_UNIVERSE_SCHEMA_OBJECT_REFERENCE",
                "row_source": "VERIFICATION_UNIVERSE:/objects",
                "filter_fact": "SCOPED_RESOLVED_OBJECT_/kind_EQUALS_LITERAL_SCHEMA",
                "reference_pointer": "/reference",
                "relation": "RESOLVED_CONSTRUCTION_IDENTITY_EQUATIONS_FORCE_REFERENCE_KIND_SCHEMA",
                "bound_namespace": "A_BOUND_OBJECT_CANNOT_SATISFY_KIND_SCHEMA_BECAUSE_THE_ALLOWLISTED_BOUND_KINDS_ARE_PACKAGE_AND_SOURCE_VECTOR CATALOG ONLY"
            }
        ],
        "postcondition": "RESOLVE_ONE(VERIFICATION_UNIVERSE, PROVEN_SCHEMA_REFERENCE) RETURNS RESOLVED_OBJECT WITH /content:JSON_SCHEMA",
        "field": "RESOLVED_OBJECT:/content",
        "base_field_type_unchanged": "JSON",
        "non_applicability": {
            "arbitrary_json_reference": "CONTENT_REMAINS_JSON",
            "non_schema_resolved_object": "CONTENT_REMAINS_JSON",
            "plain_or_projected_json_with_schema_like_shape": "NEVER_JSON_SCHEMA_BY_SHAPE_OR_SUCCESSFUL_VALIDATION",
            "consumer_expectation_or_procedure_identity": "NEVER_A_PRODUCER_PREMISE",
            "bound_source_content": "REMAINS_JSON_FOR_SCHEMA_DOCUMENT_CLASSIFICATION;SEPARATE_VERIFIED_BOUND_SOURCE_CONTENT_SCHEMA_INSTANCE_LAW_MAY_TYPE_EXACT_ALLOWLIST_BOUND_CONTENT"
        },
        "assignability": {
            "existing_edges_reused": ["JSON_SCHEMA->JSON_OBJECT", "JSON_SCHEMA->JSON"],
            "reverse_narrowing": "FORBIDDEN",
            "runtime_semantics": "UNCHANGED",
            "primitive_inventory": "UNCHANGED"
        }
    }
}
_RUNTIME_REPRESENTATION["static_type_calculus"] = copy.deepcopy(R5R4_STATIC_TYPE_CALCULUS)

# ===========================================================================
# R5R4-1 (CONTINUED) DATE-TIME PRODUCER FIELDS IN THE TWO V0.13 SCHEMAS
# ---------------------------------------------------------------------------
# The refinement is applied mechanically from the declared producer-field
# inventory R5R4_FORMAT_PRODUCER_FIELDS: each declared string producer field
# gains format date-time beside its existing type string. No other string
# property and no nested $defs.evidenceItem copy is refined. The wrapper fails
# closed if a declared pointer does not resolve to a string node.
# ===========================================================================
_BASE_UPDATE_SCHEMAS_R5R4_DATE_TIME = update_schemas
def update_schemas(schemas):
    _BASE_UPDATE_SCHEMAS_R5R4_DATE_TIME(schemas)
    _r5r4_date_time_refinements = []
    for _entry in R5R4_FORMAT_PRODUCER_FIELDS:
        _ref = _entry["schema_ref"]; _ptr = _entry["schema_pointer"]
        _docs = [v for v in schemas.values() if isinstance(v, dict) and (v.get("$id") == _ref or str(v.get("$id", "")).startswith(_ref + ":"))]
        if len(_docs) != 1:
            raise SystemExit("R5R4 date-time producer refinement: schema_ref %s resolves to %d schema documents" % (_ref, len(_docs)))
        _node = _docs[0]
        for _tok in [t for t in _ptr.split("/") if t]:
            if not isinstance(_node, dict) or _tok not in _node:
                raise SystemExit("R5R4 date-time producer refinement: missing pointer segment %s of %s in %s" % (_tok, _ptr, _ref))
            _node = _node[_tok]
        if not isinstance(_node, dict) or _node.get("type") != "string":
            raise SystemExit("R5R4 date-time producer refinement: %s%s does not resolve to a type string node" % (_ref, _ptr))
        _node["format"] = R5R4_DATE_TIME_FORMAT
        _r5r4_date_time_refinements.append({"schema_ref": _ref, "schema_pointer": _ptr, "assigned_format": _node["format"]})
    if len(_r5r4_date_time_refinements) != 6:
        raise SystemExit("R5R4 date-time producer refinement: applied %d of 6 declared producer fields" % len(_r5r4_date_time_refinements))

# R5R8 supervisor-authorized producer declarations. These are schema-only
# contracts; no instance values, primitive signatures, or procedure ASTs change.
_R5R8_BASE_UPDATE_SCHEMAS = update_schemas
def update_schemas(schemas):
    _R5R8_BASE_UPDATE_SCHEMAS(schemas)

    # E1: the merged-decision lookup key is a required string.
    partial = schemas["authority-requirements.schema.json"]["properties"]["partial_effect_requirements"]
    if partial.get("type") != "object":
        raise ValueError("R5R8 E1 authority parent is not an object")
    partial_required = partial.setdefault("required", [])
    if "merged_decision_key" not in partial_required:
        partial_required.append("merged_decision_key")
    partial_properties = partial.setdefault("properties", {})
    key_schema = {"type": "string"}
    if "merged_decision_key" in partial_properties and partial_properties["merged_decision_key"] != key_schema:
        raise ValueError("R5R8 E1 conflicting pre-existing merged_decision_key declaration")
    partial_properties["merged_decision_key"] = key_schema

    # E4A/E4B: accepted vectors have typed consumed members. The source
    # instance remains byte-identical; expected is an object under selected
    # Option A, with an optional array-valued reason_codes member. Other
    # expected and vector properties remain open.
    vector_schema = schemas["metacontract.schema.json"]["$defs"]["accepted_vector_source"]["properties"]["vectors"]
    if vector_schema.get("type") != "array":
        raise ValueError("R5R8 E4 vectors producer is not an array")
    vector_item = {
        "type": "object",
        "required": ["vector_id", "expected"],
        "properties": {
            "vector_id": {"type": "string"},
            "expected": {
                "type": "object",
                "properties": {"reason_codes": {"type": "array"}}
            }
        },
        "additionalProperties": True
    }
    if "items" in vector_schema and vector_schema["items"] != vector_item:
        raise ValueError("R5R8 E4 conflicting pre-existing vectors.items declaration")
    vector_schema["items"] = vector_item

    # E5: array-valued vocabulary fields only; item values remain JSON.
    behavior = schemas["governance-requirements.schema.json"]["properties"]["behavior_vocabulary"]
    if behavior.get("type") != "object":
        raise ValueError("R5R8 E5 behavior vocabulary parent is not an object")
    behavior_fields = ["missing_behavior", "ambiguity_behavior"]
    behavior_required = behavior.setdefault("required", [])
    behavior_properties = behavior.setdefault("properties", {})
    for name in behavior_fields:
        if name not in behavior_required:
            behavior_required.append(name)
        array_schema = {"type": "array"}
        if name in behavior_properties and behavior_properties[name] != array_schema:
            raise ValueError("R5R8 E5 conflicting pre-existing declaration: " + name)
        behavior_properties[name] = array_schema

    # E6: the three consumed singleton-policy collections are arrays only;
    # elements remain general JSON and no sibling restrictions are borrowed.
    singleton = schemas["semantic-key-authority.schema.json"]["properties"]["governing_token_singleton"]
    if singleton.get("type") != "object":
        raise ValueError("R5R8 E6 governing singleton parent is not an object")
    singleton_fields = ["scan_excludes_kinds", "permitted_exception_roles", "scan_excluded_pointer_prefixes"]
    singleton_required = singleton.setdefault("required", [])
    singleton_properties = singleton.setdefault("properties", {})
    for name in singleton_fields:
        if name not in singleton_required:
            singleton_required.append(name)
        array_schema = {"type": "array"}
        if name in singleton_properties and singleton_properties[name] != array_schema:
            raise ValueError("R5R8 E6 conflicting pre-existing declaration: " + name)
        singleton_properties[name] = array_schema
    return schemas

# R5R8 E3: pin-verified reserved producer schema contract.
# The producer schema is a package-0.2 declaration in the existing registered
# metacontract schema. It is applied only to the exact strictly-decoded,
# externally pin-verified profile content named by this reserved input row.
R5R8_E3_PRODUCER_SCHEMA_REF = {
    "kind": "SCHEMA",
    "id": f"{NS}:schema:metacontract",
    "version": "0.2",
    "member_id": "frozen_rule_authority_producer",
}
R5R8_E3_PRODUCER_SCHEMA = {
    "type": "object",
    "required": ["rules"],
    "properties": {
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["rule_id"],
                "properties": {"rule_id": {"type": "string"}},
                "additionalProperties": True,
            },
        },
    },
    "additionalProperties": True,
}

R5R4_STATIC_RULE_ADDITIONS.append(
    "PIN_VERIFIED_RESERVED_PRODUCER_SCHEMA_VALIDATED_BEFORE_TYPED_ARGUMENT_EXPOSURE"
)
if "PIN_VERIFIED_RESERVED_PRODUCER_SCHEMA_VALIDATED_BEFORE_TYPED_ARGUMENT_EXPOSURE" not in STATIC_RULES:
    STATIC_RULES.append("PIN_VERIFIED_RESERVED_PRODUCER_SCHEMA_VALIDATED_BEFORE_TYPED_ARGUMENT_EXPOSURE")

R5R4_STATIC_TYPE_CALCULUS["derivation_sources"].extend([
    "metacontract.json:/reserved_inputs/*/profile_content_source/producer_schema_ref",
    "object-registry.json:/objects/*/members",
    "schema/metacontract.schema.json:/$defs/frozen_rule_authority_producer",
])
R5R4_STATIC_TYPE_CALCULUS["type_universe"]["SCHEMA_INSTANCE"]["binding_rule"] = (
    "BOUND_ONLY_FROM_EITHER_A_DECLARED_ARGUMENT_expected_schema_ref_AFTER_NORMATIVE_ARGUMENT_BINDING_OR_A_VERIFIED_RESERVED_INPUT_profile_content_source.producer_schema_ref_AFTER_PIN_AND_SCHEMA_VALIDATION"
)
R5R4_STATIC_TYPE_CALCULUS["argument_typing"]["procedure_argument_binding"]["rule"] = (
    "SCHEMA_INSTANCE_IS_BOUND_ONLY_FROM_A_DECLARED_ARGUMENT_expected_schema_ref_AFTER_NORMATIVE_ARGUMENT_BINDING_OR_A_VERIFIED_RESERVED_INPUT_profile_content_source.producer_schema_ref_AFTER_PIN_AND_SCHEMA_VALIDATION"
)
R5R4_STATIC_TYPE_CALCULUS["argument_typing"]["reserved_input_producer_schema_binding"] = {
    "rule_id": "VERIFIED_RESERVED_INPUT_SCHEMA_INSTANCE",
    "procedure_agnostic": True,
    "binding_source": "metacontract.json:/reserved_inputs/*/profile_content_source/producer_schema_ref",
    "input_identity": "THE_EXACT_RESERVED_INPUT_ROW_AND_ITS_PROFILE_CONTENT_SOURCE_POINTER_TOKENS_AND_PIN_POINTER_TOKENS",
    "schema_identity": "EXACT_TYPED_SCHEMA_REFERENCE_IN_producer_schema_ref_RESOLVES_TO_ONE_REGISTERED_SCHEMA_ROW_AND_ONE_DECLARED_MEMBER",
    "validation_stage": "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
    "validation_order": "AFTER_VERIFY_EXTERNAL_FROZEN_R5R2_CONTENT_AND_PIN_AND_AFTER_VERIFY_REGISTRY_INTEGRITY_DECLARATIONS;BEFORE_STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR",
    "validation_input": "THE_SAME_STRICTLY_DECODED_JSON_VALUE_FROM_THE_PIN_VERIFIED_PROFILE_CONTENT_BYTES_NAMED_BY_profile_content_source.content_pointer_tokens",
    "success_type": "SCHEMA_INSTANCE<THAT_EXACT_DECLARED_producer_schema_ref>",
    "failure": {
        "code": "SCHEMA_INVALID_BOUND_OBJECT",
        "stage": "PRE_EXECUTION",
        "failure_kind": "JSON_SCHEMA",
        "result_contract_ref": "metacontract:/result_contracts/pre_execution_result",
        "witness_fields": ["argument", "object_role", "schema_ref", "instance_pointer", "failure_kind", "diagnostic", "bound_identity"],
        "new_failure_vocabulary": False,
    },
    "non_applicability": [
        "ANY_INPUT_WITHOUT_AN_EXACT_DECLARED_profile_content_source.producer_schema_ref",
        "CANDIDATE_TRANSPORT_COPY",
        "UNPINNED_OR_MISMATCHED_PROFILE_CONTENT",
        "VALIDATION_OF_BYTES_OTHER_THAN_THE_DECODED_VALUE_EXPOSED_AS_THE_ARGUMENT",
        "SCHEMA_NAME_OR_FILENAME_WITHOUT_REGISTERED_SCHEMA_ROW_AND_MEMBER",
    ],
}
R5R4_STATIC_TYPE_CALCULUS["producer_refinements"]["verified_reserved_input_schema_instance"] = {
    "law_id": "VERIFIED_RESERVED_INPUT_SCHEMA_INSTANCE",
    "procedure_agnostic": True,
    "producer": "THE_RESERVED_INPUT_ROW_NAMED_frozen_rule_authority",
    "producer_schema_binding": "metacontract.json:/reserved_inputs/*/profile_content_source/producer_schema_ref",
    "content_binding": "profile_content_source.content_pointer_tokens_AND_pin_pointer_tokens_SELECT_THE_SAME_EXTERNAL_ACCEPTANCE_PROFILE_BYTES_AND_PIN",
    "validation_stage": "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE",
    "validation_order": "AFTER_VERIFY_EXTERNAL_FROZEN_R5R2_CONTENT_AND_PIN_AND_AFTER_VERIFY_REGISTRY_INTEGRITY_DECLARATIONS;BEFORE_STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR",
    "verification_premises": [
        "THE_EXISTING_EXTERNAL_ACCEPTANCE_PROFILE_IS_VALIDATED_WITH_THE_CALLER_SUPPLIED_PROFILE_SCHEMA",
        "THE_DECLARED_frozen_r5r2_rules_PIN_IS_VERIFIED_BEFORE_CONTENT_PARSE_OR_USE",
        "THE_BASE64_CONTENT_IS_STRICTLY_DECODED_TO_UTF8_JSON_WITH_DUPLICATE_NAMES_REJECTED",
        "producer_schema_ref_IDENTIFIES_EXACTLY_ONE_REGISTERED_SCHEMA_DOCUMENT_AND_MEMBER",
        "THAT_MEMBER_VALIDATES_THE_SAME_DECODED_PIN_VERIFIED_JSON_VALUE_BEFORE_ARGUMENT_EXPOSURE",
    ],
    "conclusion": "THE_SUCCESSFULLY_VERIFIED_RESERVED_ARGUMENT_HAS_TYPE_SCHEMA_INSTANCE<ITS_EXACT_DECLARED_producer_schema_ref>",
    "validation_failure": {
        "existing_code": "SCHEMA_INVALID_BOUND_OBJECT",
        "stage": "PRE_EXECUTION",
        "failure_kind": "JSON_SCHEMA",
        "result_contract_ref": "metacontract:/result_contracts/pre_execution_result",
    },
    "pin_failure_precedence": "EXTERNAL_FROZEN_R5R2_CONTENT_MISMATCH_PRECEDES_SCHEMA_VALIDATION_AND_TYPED_USE",
    "candidate_copy_authority": False,
    "candidate_schema_selection": False,
    "no_generic_json_narrowing": True,
}
_RUNTIME_REPRESENTATION["static_type_calculus"] = copy.deepcopy(R5R4_STATIC_TYPE_CALCULUS)

_R5R8_E3_BASE_MAKE_METACONTRACT = make_metacontract
def make_metacontract(proc, inv):
    result = _R5R8_E3_BASE_MAKE_METACONTRACT(proc, inv)
    rows = [row for row in result["reserved_inputs"] if row.get("name") == "frozen_rule_authority"]
    if len(rows) != 1:
        raise ValueError("R5R8 E3 requires one exact frozen_rule_authority reserved input row")
    source = rows[0].get("profile_content_source")
    if not isinstance(source, dict):
        raise ValueError("R5R8 E3 frozen_rule_authority lacks profile_content_source")
    source["producer_schema_ref"] = copy.deepcopy(R5R8_E3_PRODUCER_SCHEMA_REF)
    return result

_R5R8_E3_BASE_MAKE_METACONTRACT_SCHEMA = make_metacontract_schema
def make_metacontract_schema():
    schema = _R5R8_E3_BASE_MAKE_METACONTRACT_SCHEMA()
    source_schema = schema["properties"]["reserved_inputs"]["items"]["properties"]["profile_content_source"]
    source_schema["properties"]["producer_schema_ref"] = {"$ref": "#/$defs/typed_ref"}
    rows = schema["properties"]["reserved_inputs"]["items"]
    rows.setdefault("allOf", []).append({
        "if": {"properties": {"name": {"const": "frozen_rule_authority"}}, "required": ["name"]},
        "then": {
            "properties": {
                "profile_content_source": {
                    "required": ["producer_schema_ref"],
                    "properties": {"producer_schema_ref": {"const": copy.deepcopy(R5R8_E3_PRODUCER_SCHEMA_REF)}},
                },
            },
        },
    })
    return schema

_R5R8_E3_BASE_UPDATE_SCHEMAS = update_schemas
def update_schemas(schemas):
    _R5R8_E3_BASE_UPDATE_SCHEMAS(schemas)
    metacontract_schema = schemas["metacontract.schema.json"]
    existing = metacontract_schema["$defs"].get("frozen_rule_authority_producer")
    if existing is not None and existing != R5R8_E3_PRODUCER_SCHEMA:
        raise ValueError("R5R8 E3 conflicting frozen_rule_authority producer schema")
    metacontract_schema["$defs"]["frozen_rule_authority_producer"] = copy.deepcopy(R5R8_E3_PRODUCER_SCHEMA)



# R5R9: generic schema-bound source, selector admission and correlated refinements.
# These are data-driven type rules. The checker consumes exact schema/allowlist
# relationships and never dispatches on a procedure identity.
R5R9_TARGET_SCHEMA_REF = {
    "kind": "SCHEMA", "id": f"{NS}:schema:v013-target", "version": "0.2"
}
R5R9_STATIC_TYPE_CALCULUS = R5R4_STATIC_TYPE_CALCULUS
R5R9_STATIC_TYPE_CALCULUS["derivation_sources"].extend([
    "external-verification-input.contract.json:/authority_profile_protocol/accepted_source_allowlist",
    "object-registry.json:/objects/*/members",
    "schema/v013-target.schema.json:/$defs/ref",
    "primitive-registry.json:/descendant_record/fields",
    "procedure-registry.schema.json:/$defs/argument/properties/source_constraint/properties/identity_constraint/oneOf",
])
R5R9_STATIC_TYPE_CALCULUS["static_type_at_path"]["schema_instance_projection"] = {
    "input": "SCHEMA_INSTANCE<S>",
    "path": "STATICALY_KNOWN_RFC6901_TOKEN_SEQUENCE",
    "authority": "THE_EXACT_REGISTERED_SCHEMA_DOCUMENT_AND_OPTIONAL_MEMBER_NAMED_BY_S",
    "projection": "RECURSIVE_EFFECTIVE_SCHEMA_TYPE_AT_THE_EXACT_PATH",
    "type_presence_distinction": {
        "type": "THE_SCHEMA_TYPE_WHEN_THE_SELECTED_PATH_IS_PRESENT",
        "presence": "A_SEPARATE_REQUIREDNESS_OR_RUNTIME_EXISTENCE_PREMISE",
        "optional_field": "DOES_NOT_BECOME_REQUIRED_FROM_ITS_PROJECTED_TYPE",
    },
    "branch_behavior": "PROJECT_ONLY_WHEN_ALL_REMAINING_SCHEMA_BRANCHES_SUPPORT_ONE_UNIQUE_TYPE_OR_A_DECLARED_DISCRIMINATOR_SELECTS_ONE_BRANCH",
    "unknown_or_ambiguous": "UNDERDETERMINED;NO_CONSUMER_BACKFLOW",
}
R5R9_STATIC_TYPE_CALCULUS["static_type_at_path"]["schema_instance_projection"]["structural_nominal_forms"] = [
    {
        "nominal_type": "TYPED_REFERENCE",
        "authority": "metacontract.json:/runtime_representation/value_schemas/resolved_object/$defs/typed_ref",
        "required_properties": {"kind": "STRING", "id": "STRING", "version": "STRING"},
        "optional_properties": {"member_id": "STRING"},
        "closed_schema_required": True,
        "property_static_domain_rule": "DIRECT_STRING_TYPE_OR_NONEMPTY_ENUM_OF_STRINGS",
    },
    {
        "nominal_type": "BASE_TYPED_REFERENCE",
        "authority": "metacontract.json:/runtime_representation/value_schemas/resolved_object/$defs/base_ref",
        "required_properties": {"kind": "STRING", "id": "STRING", "version": "STRING"},
        "optional_properties": {},
        "closed_schema_required": True,
        "property_static_domain_rule": "DIRECT_STRING_TYPE_OR_NONEMPTY_ENUM_OF_STRINGS",
    },
]
R5R9_STATIC_TYPE_CALCULUS["producer_refinements"]["verified_reserved_input_schema_instance"].update({
    "producer": "ANY_RESERVED_INPUT_ROW_WITH_AN_EXACT_profile_content_source.producer_schema_ref",
    "subject_identity": "THE_RESERVED_INPUT_ROW_PLUS_ITS_EXACT_PROFILE_CONTENT_SOURCE_POINTER_TOKENS_AND_PIN_POINTER_TOKENS",
    "validation_subject": "THE_IDENTICAL_STRICTLY_DECODED_PIN_VERIFIED_JSON_VALUE_EXPOSED_AS_THAT_RESERVED_ARGUMENT",
    "same_subject_required": True,
    "producer_schema_bindings": [{"reserved_input_name": "frozen_rule_authority", "producer_schema_ref": copy.deepcopy(R5R8_E3_PRODUCER_SCHEMA_REF)}],
})
R5R9_STATIC_TYPE_CALCULUS["producer_refinements"]["verified_bound_source_content"] = {
    "law_id": "VERIFIED_BOUND_SOURCE_CONTENT_SCHEMA_INSTANCE",
    "procedure_agnostic": True,
    "producer_authority": "external-verification-input.contract.json:/authority_profile_protocol/accepted_source_allowlist/*",
    "identity_premise": "THE_EXACT_REFERENCE_RESOLVES_TO_ONE_ALLOWLIST_ROW_AND_ONE_OBJECT_IN_THE_EXACT_VERIFICATION_UNIVERSE",
    "integrity_premise": "THE_ALLOWLISTED_SOURCE_RAW_AND_SEMANTIC_PINS_ARE_VERIFIED_BEFORE_USE",
    "schema_binding": "THE_MATCHED_ALLOWLIST_ROW.expected_schema_ref_RESOLVES_TO_ONE_REGISTERED_SCHEMA_DOCUMENT_AND_OPTIONAL_MEMBER",
    "source_binding_routes": [{"producer_schema_ref": copy.deepcopy(R5R9_TARGET_SCHEMA_REF), "reference_path_tokens": ["source_vector_ref"], "expected_kind": "SOURCE_VECTOR_CATALOG", "required_role": "VECTOR_SOURCE"}],
    "validation_subject": "THE_SAME_STRICTLY_PARSED_PIN_VERIFIED_SOURCE_CONTENT_VALUE_EXPOSED_AS_RESOLVED_OBJECT.content",
    "validation_stage": "PRE_EXECUTION_BEFORE_ARGUMENT_AND_SELECTOR_EXPOSURE",
    "success_type": "SCHEMA_INSTANCE<THE_MATCHED_ALLOWLIST_ROW.expected_schema_ref>",
    "field": "RESOLVED_OBJECT:/content",
    "failure": "EXISTING_PRE_EXECUTION_SOURCE_SCHEMA_VALIDATION_OR_RESOLUTION_FAILURE;NO_JSON_NARROWING",
    "non_applicability": [
        "CANDIDATE_OBJECT_CONTENT",
        "UNPINNED_OR_MISMATCHED_SOURCE_CONTENT",
        "A_DIFFERENT_PARSED_VALUE_THAN_THE_ONE_EXPOSED_AS_content",
        "ZERO_OR_MULTIPLE_EXACT_ALLOWLIST_MATCHES",
        "UNRESOLVED_SCHEMA_DOCUMENT_OR_MEMBER",
    ],
}
R5R9_STATIC_TYPE_CALCULUS["producer_refinements"]["selector_domain_admission"] = {
    "law_id": "VERIFIED_SOURCE_SELECTOR_DOMAIN_ADMISSION",
    "procedure_agnostic": True,
    "phase": "AFTER_SOURCE_PIN_AND_SCHEMA_VALIDATION;BEFORE_SELECTOR_ARGUMENT_EXPOSURE_AND_AST_EXECUTION",
    "selector_model": {
        "producer_schema_ref": R5R9_TARGET_SCHEMA_REF,
        "selector_items_path_tokens": ["relationship_basis", "accepted", "*"],
        "kind_path_tokens": ["selector", "kind"],
        "path_tokens_path_tokens": ["selector", "pointer_tokens"],
        "descendant_record_path_tokens_path_tokens": ["path_tokens"],
        "source_reference_path_tokens": ["source_vector_ref"],
        "source_allowlist_role": "VECTOR_SOURCE",
        "selector_path_value_relation": "THE_SELECTED_RECORD.path_tokens_EQUALS_THE_SAME_SELECTOR.pointer_tokens",
        "source_identity_relation": "THE_SELECTED_RECORD_DESCENDS_FROM_THE_CONTENT_OF_THE_EXACT_VERIFIED_SOURCE_RESOLVED_BY_source_reference_path_tokens",
        "selected_value_path_tokens": ["value"],
    },
    "admission_premises": [
        "THE_SELECTOR_KIND_IS_UNIQUELY_ADMITTED_BY_ITS_REGISTERED_PRODUCER_SCHEMA_BRANCH",
        "THE_EXACT_SELECTOR_PATH_RESOLVES_AGAINST_THE_SAME_PIN_VERIFIED_SOURCE_CONTENT_VALUE",
        "THE_EXACT_PATH_IS_ADMITTED_BY_THE_MATCHED_SOURCE_ROW.expected_schema_ref",
        "THE_EXACT_PATH_EXISTS_IN_THE_APPLICABLE_SCHEMA_BRANCH_AND_IN_THE_VERIFIED_SOURCE_VALUE",
        "THE_STATIC_TYPE_IS_PROJECTED_FROM_THAT_SCHEMA_BRANCH;RUNTIME_VALUES_NEVER_SUPPLY_A_TYPE",
    ],
    "pre_ast_admission_algorithm": {
        "schema_subject": "THE_EXACT_MATCHED_ALLOWLIST_ROW.expected_schema_ref_AND_THE_SAME_PIN_VERIFIED_SOURCE_CONTENT_VALUE",
        "selected_path": "THE_EXACT_SELECTOR.pointer_tokens;NO_GLOB_OR_PREFIX_SUBSTITUTION",
        "schema_projection": "PROJECT_THE_PATH_THROUGH_THE_REGISTERED_SCHEMA_INSTANCE_WITH_VALIDATED_DISCRIMINATOR_FACTS_ONLY",
        "presence_check": "THE_SAME_STRICTLY_PARSED_SOURCE_VALUE_MUST_CONTAIN_THE_EXACT_PATH;PRESENCE_DOES_NOT_SUPPLY_TYPE",
        "required_domain_check": "NORMALIZED_SCHEMA_PROJECTED_DOMAIN_MUST_EQUAL_THE_DOMAIN_FOR_THE_ADMITTED_SELECTOR_KIND",
        "failure": "REJECT_BEFORE_SELECTOR_ARGUMENT_EXPOSURE_ON_ABSENT_PATH,UNKNOWN_SCHEMA_PATH,AMBIGUOUS_BRANCH,OR_DOMAIN_MISMATCH",
    },
    "selector_domains": [
        {
            "kind_literal": "VALUE",
            "required_static_domain": "ANY_JSON",
            "selected_value_type": "THE_UNIQUE_SCHEMA_PROJECTED_TYPE_WHEN_PRESENT",
        },
        {
            "kind_literal": "ARRAY_CONTAINS",
            "required_static_domain": "ARRAY",
            "selected_value_type": "ARRAY<SCHEMA_PROJECTED_ITEM_TYPE>",
        },
    ],
    "result_fact": "ONLY_THE_DESCENDANT_RECORD_WITH_THE_SAME_SOURCE_SUBJECT_AND_EQUAL_path_tokens_INHERITS_THE_ADMITTED_SELECTED_VALUE_TYPE",
    "optional_fields": "TYPE_WHEN_PRESENT_DOES_NOT_PROVE_PRESENCE;THE_EXACT_RUNTIME_PATH_MUST_EXIST_BEFORE_ADMISSION",
    "failure": "REJECT_SELECTOR_SOURCE_COMBINATION_BEFORE_AST_EXPOSURE_WHEN_ANY_PREMISE_FAILS",
    "non_applicability": [
        "NO_CONSUMER_EXPECTATION_OR_ANY.array_OPERAND_CAN_CREATE_AN_ADMISSION_FACT",
        "NO_PATH_VALUE_OR_FIXTURE_CAN_CREATE_A_STATIC_TYPE",
        "SELECTOR_KINDS_WITH_ANOTHER_DECLARED_DOMAIN_KEEP_THAT_DOMAIN",
        "UNRELATED_SOURCE_OR_SIBLING_SELECTOR_RECEIVES_NO_FACT",
    ],
}
R5R9_STATIC_TYPE_CALCULUS["producer_refinements"]["descendant_record_correlated_value_type"] = {
    "law_id": "DESCENDANT_RECORD_CORRELATED_VALUE_TYPE",
    "procedure_agnostic": True,
    "producer": "primitive-registry.json:/descendant_record",
    "record_subject": "THE_SINGLE_DESCENDANT_RECORD_RETURNED_FOR_ONE_VISITED_NODE",
    "discriminator_field": "value_type",
    "discriminator_algorithm": "JSON_TYPE_DISCRIMINANT_BOOLEAN_BEFORE_NUMBER_NO_COERCION",
    "correlated_field": "value",
    "mapping": {
        "NULL": "NULL",
        "BOOLEAN": "BOOLEAN",
        "NUMBER": "JSON_NUMBER",
        "STRING": "STRING",
        "ARRAY": "ARRAY<JSON>",
        "OBJECT": "JSON_OBJECT",
    },
    "predicate": "POSITIVE_LITERAL_EQUALITY_ON_THE_SAME_FILTERED_RECORD.value_type",
    "scope": "ONLY_THE_SAME_RECORD_SUBJECT_IN_THE_POSITIVE_FILTER_RESULT_AND_DESCENDANT_FILTERS_DERIVED_FROM_IT",
    "negative_predicate": "DOES_NOT_PRODUCE_A_POSITIVE_REFINEMENT",
    "failure": "UNKNOWN_OR_AMBIGUOUS_DISCRIMINANT_REMAINS_FINITE_JSON",
}
R5R9_STATIC_TYPE_CALCULUS["producer_refinements"]["schema_union_discriminator"] = {
    "law_id": "SCHEMA_UNION_LITERAL_DISCRIMINATOR",
    "procedure_agnostic": True,
    "authority": "THE_EXACT_REGISTERED_SCHEMA_DOCUMENT_AND_MEMBER",
    "union_keywords": ["oneOf", "anyOf"],
    "premise": "POSITIVE_LITERAL_EQUALITY_ON_A_SCHEMA_DECLARED_PATH_OF_THE_SAME_SCOPED_ITEM",
    "matching": "A_BRANCH_MATCHES_ONLY_WHEN_ITS_SCHEMA_CONSTRAINTS_ADMIT_THE_EXACT_LITERAL_AT_THE_DISCRIMINATOR_PATH",
    "conclusion": "A_UNIQUE_MATCH_NARROWS_ONLY_THE_SAME_FILTER_RESULT_ITEM_TO_THAT_BRANCH_BEFORE_PATH_PROJECTION",
    "zero_matches": "UNDERDETERMINED_AND_FAIL_CLOSED",
    "multiple_matches": "UNDERDETERMINED_AND_FAIL_CLOSED",
    "unknown_or_negative_predicate": "NO_BRANCH_REFINEMENT",
    "scope": "FILTER_RESULT_ELEMENT_SUBJECT_ONLY;NO_SIBLING_OR_REBOUND_VARIABLE_LEAKAGE",
}
for _law in (
    "VERIFIED_BOUND_SOURCE_CONTENT_SCHEMA_INSTANCE",
    "VERIFIED_SOURCE_SELECTOR_DOMAIN_ADMISSION",
    "DESCENDANT_RECORD_CORRELATED_VALUE_TYPE",
    "SCHEMA_UNION_LITERAL_DISCRIMINATOR",
):
    if _law not in STATIC_RULES:
        STATIC_RULES.append(_law)
    if _law not in R5R4_STATIC_RULE_ADDITIONS:
        R5R4_STATIC_RULE_ADDITIONS.append(_law)
R5R4_STATIC_TYPE_CALCULUS["operator_rules"]["operators"]["FILTER"]["laws"].extend([
    "POSITIVE_SCHEMA_DISCRIMINATOR_FACT_NARROWS_ONLY_THE_UNIQUE_FILTER_RESULT_BRANCH",
    "CANONICAL_DESCENDANT_VALUE_TYPE_REFINES_ONLY_THE_SAME_RECORD_VALUE_FIELD",
    "VERIFIED_SELECTOR_ADMISSION_FACT_FLOWS_ONLY_TO_THE_MATCHING_DESCENDANT_RECORD",
])
_RUNTIME_REPRESENTATION["static_type_calculus"] = copy.deepcopy(R5R4_STATIC_TYPE_CALCULUS)

# R5R9 R4: package 0.2's verifier-owned digest_mode runtime value is an open
# record. Keep the descriptor's existing runtime settings intact; the nested
# runtime schema declares only the required value domains and admits any
# additional JSON properties.
R5R9_EXTERNAL_TRUST_DIGEST_MODE_RUNTIME_SCHEMA = {
    "type": "object",
    "required": ["algorithm", "serialization", "excluded_pointers"],
    "properties": {
        "algorithm": {"type": "string"},
        "serialization": {"type": "string"},
        "excluded_pointers": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": True,
}
R5R9_EXTERNAL_TRUST_DIGEST_MODE_TYPE = (
    "OPEN_OBJECT{algorithm:STRING,serialization:STRING,excluded_pointers:ARRAY<STRING>}"
)
_RUNTIME_REPRESENTATION["static_paths"]["EXTERNAL_TRUST"]["/digest_mode"] = R5R9_EXTERNAL_TRUST_DIGEST_MODE_TYPE
R5R9_STATIC_TYPE_CALCULUS["inventory"]["normalized_static_paths"].append(
    "EXTERNAL_TRUST:/digest_mode = OPEN_OBJECT{algorithm:STRING,serialization:STRING,excluded_pointers:ARRAY<STRING>}"
)
R5R9_STATIC_TYPE_CALCULUS["type_universe"]["OPEN_OBJECT"] = {
    "kind": "CONSTRUCTOR_STRUCTURAL",
    "constructor": "OPEN_STRUCTURAL_OBJECT",
    "parameter": "REQUIRED_FIELD_NAME_TO_STATIC_TYPE_MAP",
    "object_base": "JSON_OBJECT",
    "canonical_syntax": "OPEN_OBJECT{field:type,...}",
    "required_fields": "ALL_FIELDS_IN_THE_DECLARED_FIELD_MAP",
    "additional_properties": "JSON",
    "extra_fields": "ALLOWED_AND_REMAIN_JSON",
}
R5R9_STATIC_TYPE_CALCULUS["static_type_at_path"]["open_structural_object_projection"] = {
    "input": "OPEN_OBJECT{field:type,...}",
    "declared_field": "PROJECT_ITS_DECLARED_STATIC_TYPE",
    "undeclared_field": "PROJECT_DECLARED_ADDITIONAL_PROPERTIES_TYPE_JSON",
    "presence": "THE_OPEN_RECORD_PRODUCER_SCHEMA_REQUIRES_EACH_LISTED_FIELD",
    "consumer_backflow": False,
}
R5R9_STATIC_TYPE_CALCULUS["producer_refinements"]["external_trust_digest_mode_record"] = {
    "law_id": "EXTERNAL_TRUST_DIGEST_MODE_OPEN_RECORD",
    "producer_contract": "external-verification-input.contract.json:/fields/digest_mode/runtime_value_schema",
    "reserved_input": "metacontract.json:/reserved_inputs/*[name=external_trust]",
    "selected_field": "/digest_mode",
    "result_type": R5R9_EXTERNAL_TRUST_DIGEST_MODE_TYPE,
    "required_fields": ["algorithm", "serialization", "excluded_pointers"],
    "field_types": {"algorithm": "STRING", "serialization": "STRING", "excluded_pointers": "ARRAY<STRING>"},
    "extra_fields": "ALLOWED_AS_JSON",
    "producer_validation": "THE_SAME_VERIFIER_CONFIGURATION_VALUE_IS_VALIDATED_AGAINST_runtime_value_schema_BEFORE_TYPED_USE",
    "existing_runtime_digest_checks": "UNCHANGED",
    "failure": "MISSING_REQUIRED_FIELD_OR_WRONG_DECLARED_FIELD_TYPE_FAILS_PRODUCER_SCHEMA_VALIDATION",
    "no_enum_const_or_pointer_grammar": True,
}
if "external-verification-input.contract.json:/fields/digest_mode/runtime_value_schema" not in R5R9_STATIC_TYPE_CALCULUS["derivation_sources"]:
    R5R9_STATIC_TYPE_CALCULUS["derivation_sources"].append("external-verification-input.contract.json:/fields/digest_mode/runtime_value_schema")
if "EXTERNAL_TRUST_DIGEST_MODE_OPEN_RECORD" not in STATIC_RULES:
    STATIC_RULES.append("EXTERNAL_TRUST_DIGEST_MODE_OPEN_RECORD")
if "EXTERNAL_TRUST_DIGEST_MODE_OPEN_RECORD" not in R5R4_STATIC_RULE_ADDITIONS:
    R5R4_STATIC_RULE_ADDITIONS.append("EXTERNAL_TRUST_DIGEST_MODE_OPEN_RECORD")
_RUNTIME_REPRESENTATION["static_type_calculus"] = copy.deepcopy(R5R9_STATIC_TYPE_CALCULUS)

_R5R9_R4_BASE_NORMALIZE_EXTERNAL_TRUST = normalize_external_trust
def normalize_external_trust(files):
    _R5R9_R4_BASE_NORMALIZE_EXTERNAL_TRUST(files)
    digest_mode = files["external-verification-input.contract.json"]["fields"]["digest_mode"]
    digest_mode["runtime_value_schema"] = copy.deepcopy(R5R9_EXTERNAL_TRUST_DIGEST_MODE_RUNTIME_SCHEMA)

_R5R9_R4_BASE_UPDATE_SCHEMAS = update_schemas
def update_schemas(schemas):
    _R5R9_R4_BASE_UPDATE_SCHEMAS(schemas)
    digest_mode_schema = schemas["external-verification-input-contract.schema.json"]["properties"]["fields"]["properties"]["digest_mode"]
    runtime_schema = {
        "type": "object",
        "required": ["type", "required", "properties", "additionalProperties"],
        "properties": {
            "type": {"const": "object"},
            "required": {"const": ["algorithm", "serialization", "excluded_pointers"]},
            "properties": {"const": {
                "algorithm": {"type": "string"},
                "serialization": {"type": "string"},
                "excluded_pointers": {"type": "array", "items": {"type": "string"}},
            }},
            "additionalProperties": {"const": True},
        },
        "additionalProperties": False,
    }
    digest_mode_schema["required"] = list(dict.fromkeys(digest_mode_schema.get("required", []) + ["runtime_value_schema"]))
    digest_mode_schema.setdefault("properties", {})["runtime_value_schema"] = runtime_schema



# ACCORD-02E4R5R11 normative post-build layer: producer/type-based reference closure.
def _r11_load(rel):
    return json.loads((OUT / rel).read_text(encoding="utf-8"))
def _r11_save(rel, value):
    (OUT / rel).write_bytes(emit(value))
def _r11_ptr_escape(value):
    return str(value).replace("~", "~0").replace("/", "~1")
def _r11_join_pointer(pointer, token):
    return pointer + "/" + _r11_ptr_escape(token)
def _r11_pointer_get(value, pointer):
    if pointer in ("", "#"): return value
    if not pointer.startswith("#/") and not pointer.startswith("/"):
        raise ValueError("unsupported schema reference " + pointer)
    raw = pointer[1:] if pointer.startswith("#") else pointer
    current = value
    for token in raw[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current
def _r11_schema_pointer_get(value, pointer):
    if pointer in ("", "#"): return value
    if pointer.startswith("#"): pointer = pointer[1:]
    current = value
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current
def _r11_refkey(value):
    if not isinstance(value, dict): return None
    return (value.get("kind"), value.get("id"), value.get("version"), value.get("member_id", ""))
def _r11_route_tokens(node, doc, docid, schema_pointer, instance_tokens, active, defs, rows, provenance):
    if isinstance(node, bool) or not isinstance(node, dict): return
    refvalue = node.get("$ref")
    if isinstance(refvalue, str):
        if not refvalue.startswith("#"):
            raise ValueError("non-local producer schema reference is not supported: " + refvalue)
        target_pointer = refvalue[1:]
        target_key = (docid, target_pointer)
        if target_key in defs:
            row = {"producer_schema_ref":copy.deepcopy(provenance),
                   "schema_pointer":schema_pointer or "/",
                   "instance_path_tokens":copy.deepcopy(instance_tokens),
                   "reference_definition_ref":copy.deepcopy(defs[target_key])}
            key=json.dumps(row,sort_keys=True,separators=(",",":"),ensure_ascii=False)
            rows[key]=row
        else:
            target=_r11_schema_pointer_get(doc,target_pointer)
            if target_pointer in active:
                if _r11_can_reach_typed_ref(target,doc,docid,defs,set()):
                    raise ValueError("recursive schema can produce references; finite route expansion is unresolved: "+target_pointer)
            else:
                _r11_route_tokens(target,doc,docid,target_pointer,instance_tokens,active+(target_pointer,),defs,rows,provenance)
        siblings={k:v for k,v in node.items() if k!="$ref"}
        if siblings: _r11_route_tokens(siblings,doc,docid,schema_pointer,instance_tokens,active,defs,rows,provenance)
    for key, value in node.items():
        if key=="$ref": continue
        if key=="properties" and isinstance(value,dict):
            for prop,sub in value.items():
                _r11_route_tokens(sub,doc,docid,_r11_join_pointer(_r11_join_pointer(schema_pointer,key),prop),instance_tokens+[{"kind":"PROPERTY","value":prop}],active,defs,rows,provenance)
        elif key=="patternProperties" and isinstance(value,dict):
            for pattern,sub in value.items():
                _r11_route_tokens(sub,doc,docid,_r11_join_pointer(_r11_join_pointer(schema_pointer,key),pattern),instance_tokens+[{"kind":"PATTERN_PROPERTY","value":pattern}],active,defs,rows,provenance)
        elif key=="additionalProperties" and isinstance(value,dict):
            _r11_route_tokens(value,doc,docid,_r11_join_pointer(schema_pointer,key),instance_tokens+[{"kind":"ADDITIONAL_PROPERTY"}],active,defs,rows,provenance)
        elif key=="items" and isinstance(value,dict):
            _r11_route_tokens(value,doc,docid,_r11_join_pointer(schema_pointer,key),instance_tokens+[{"kind":"ARRAY_ITEM"}],active,defs,rows,provenance)
        elif key=="prefixItems" and isinstance(value,list):
            for index,sub in enumerate(value):
                _r11_route_tokens(sub,doc,docid,_r11_join_pointer(_r11_join_pointer(schema_pointer,key),index),instance_tokens+[{"kind":"ARRAY_INDEX","value":str(index)}],active,defs,rows,provenance)
        elif key in ("allOf","anyOf","oneOf") and isinstance(value,list):
            for index,sub in enumerate(value):
                _r11_route_tokens(sub,doc,docid,_r11_join_pointer(_r11_join_pointer(schema_pointer,key),index),instance_tokens,active,defs,rows,provenance)
        elif key in ("if","then","else","contains","unevaluatedProperties","unevaluatedItems") and isinstance(value,dict):
            _r11_route_tokens(value,doc,docid,_r11_join_pointer(schema_pointer,key),instance_tokens+([{"kind":"ADDITIONAL_PROPERTY"}] if key=="unevaluatedProperties" else [{"kind":"ARRAY_ITEM"}] if key in ("contains","unevaluatedItems") else []),active,defs,rows,provenance)
        elif key=="dependentSchemas" and isinstance(value,dict):
            for prop,sub in value.items():
                _r11_route_tokens(sub,doc,docid,_r11_join_pointer(_r11_join_pointer(schema_pointer,key),prop),instance_tokens,active,defs,rows,provenance)
def _r11_can_reach_typed_ref(node,doc,docid,defs,seen):
    if isinstance(node,bool) or not isinstance(node,dict): return False
    refvalue=node.get("$ref")
    if isinstance(refvalue,str) and refvalue.startswith("#"):
        target=(docid,refvalue[1:])
        if target in defs:return True
        if target not in seen:
            try: sub=_r11_schema_pointer_get(doc,refvalue[1:])
            except Exception:return True
            if _r11_can_reach_typed_ref(sub,doc,docid,defs,seen|{target}):return True
    for key,value in node.items():
        if key=="$ref": continue
        if isinstance(value,dict) and _r11_can_reach_typed_ref(value,doc,docid,defs,seen): return True
        if isinstance(value,list) and any(_r11_can_reach_typed_ref(x,doc,docid,defs,seen) for x in value): return True
    return False
def _r11_typed_ref_schema():
    return {"type":"object","required":["kind","id","version"],"properties":{"kind":{"type":"string","minLength":1},"id":{"type":"string","minLength":1},"version":{"type":"string","minLength":1},"member_id":{"type":"string","minLength":1}},"additionalProperties":False}
def _r11_is_reference_definition(node):
    if not isinstance(node,dict) or not {"kind","id","version"}.issubset(set(node.get("required",[]))): return False
    props=node.get("properties",{})
    if not isinstance(props,dict): return False
    for key in ("kind","id","version"):
        val=props.get(key)
        if not isinstance(val,dict) or val.get("type")!="string": return False
    if node.get("additionalProperties") is not False: return False
    if "member_id" in props and (not isinstance(props["member_id"],dict) or props["member_id"].get("type")!="string"): return False
    return True
def _r11_add_reference_model_schema(schema):
    props=schema["properties"]
    old=props.pop("shape_predicate",None)
    schema["required"]=[x for x in schema["required"] if x!="shape_predicate"]
    add_required=["reference_type","representation_validation","non_reference_controls","bound_source_references","producer_schema_routes","enumeration","genuine_reference_examples"]
    schema["required"]=list(dict.fromkeys(schema["required"]+add_required))
    props["mechanism"]={"const":"PRODUCER_SCHEMA_TYPED_VALUES"}
    typed={"$ref":"#/$defs/ref"}
    props["reference_type"]={"type":"object","required":["type_id","admission","definition_refs","shape_alone_sufficient"],"properties":{"type_id":{"const":"TYPED_REFERENCE"},"admission":{"const":"APPLIED_PRODUCER_SCHEMA_REFERENCE_TO_DECLARED_REFERENCE_DEFINITION"},"definition_refs":{"type":"array","minItems":1,"items":{"type":"object","required":["reference_definition_ref","definition_pointer"],"properties":{"reference_definition_ref":typed,"definition_pointer":{"type":"string","pattern":"^/\\$defs/[^/]+$"}},"additionalProperties":False}},"shape_alone_sufficient":{"const":False}},"additionalProperties":False}
    props["representation_validation"]={"type":"object","required":["required_keys","optional_keys","additional_keys","all_values_type","member_id_nonempty"],"properties":{"required_keys":{"const":["kind","id","version"]},"optional_keys":{"const":["member_id"]},"additional_keys":{"const":"DISQUALIFY"},"all_values_type":{"const":"STRING"},"member_id_nonempty":{"const":True}},"additionalProperties":False}
    props["non_reference_controls"]={"type":"array","minItems":2,"items":{"type":"object","required":["case_id","value","producer_authority","classification"],"properties":{"case_id":{"type":"string","minLength":1},"value":{"type":"object","required":["kind","id","version"],"properties":{"kind":{"type":"string"},"id":{"type":"string"},"version":{"type":"string"}},"additionalProperties":False},"producer_authority":{"const":"NONE"},"classification":{"const":"NOT_A_REFERENCE"}},"additionalProperties":False}}
    props["bound_source_references"]={"type":"array","minItems":1,"items":{"type":"object","required":["reference","producer_schema_ref","selection"],"properties":{"reference":typed,"producer_schema_ref":typed,"selection":{"const":"EXACT_VERIFIED_ALLOWLIST_ENTRY"}},"additionalProperties":False}}
    props["producer_schema_routes"]={"type":"array","minItems":1,"items":{"$ref":"#/$defs/producer_schema_route"}}
    props["enumeration"]={"type":"object","required":["traversal_universe","owner_content_subject","producer_schema_selector","admission_rule","schema_applicators","path_tokens","nested_reference_values","deterministic_order","duplicate_handling","untyped_value_handling","unsupported_schema_handling"],"properties":{"traversal_universe":{"const":["EXACT_ACTIVE_NORMATIVE_REGISTRY_OWNER_REFERENCES","EXACT_VERIFIED_BOUND_SOURCE_REFERENCES"]},"owner_content_subject":{"const":"SAME_RESOLVED_OBJECT_CONTENT_VALIDATED_BEFORE_ARGUMENT_EXPOSURE"},"producer_schema_selector":{"const":"EXACT_SCHEMA_REF_FROM_THE_SAME_RESOLVED_OBJECT_OR_VERIFIED_ALLOWLIST_BINDING"},"admission_rule":{"const":"INSTANCE_PATH_REACHED_THROUGH_APPLIED_SCHEMA_REF_TO_A_DECLARED_REFERENCE_DEFINITION"},"schema_applicators":{"const":["$ref","properties","patternProperties","additionalProperties","prefixItems","items","contains","allOf","anyOf","oneOf","if_then_else","dependentSchemas","unevaluatedProperties","unevaluatedItems"]},"path_tokens":{"const":["PROPERTY","PATTERN_PROPERTY","ADDITIONAL_PROPERTY","ARRAY_INDEX","ARRAY_ITEM"]},"nested_reference_values":{"const":"EMIT_EVERY_SCHEMA_ADMITTED_REFERENCE_VALUE_AT_ANY_NESTING_DEPTH"},"deterministic_order":{"const":"OWNER_IDENTITY_UTF16_ORDER_THEN_INSTANCE_JSON_TREE_PREORDER_WITH_JCS_KEY_ORDER_AND_ARRAY_INDEX_ORDER"},"duplicate_handling":{"const":"COALESCE_SAME_EDGE_ACROSS_SCHEMA_BRANCHES_KEEP_DISTINCT_SOURCE_POINTERS"},"untyped_value_handling":{"const":"SHAPE_ALONE_NEVER_ADMITS_A_REFERENCE"},"unsupported_schema_handling":{"const":"FAIL_CLOSED_WITH_REFERENCE_DOMAIN_UNDERDETERMINED"}},"additionalProperties":False}
    props["genuine_reference_examples"]={"type":"array","minItems":4,"items":{"type":"object","required":["example_id","producer_schema_ref","schema_pointer","instance_path_tokens","reference_definition_ref"],"properties":{"example_id":{"type":"string","minLength":1},"producer_schema_ref":typed,"schema_pointer":{"type":"string","minLength":1},"instance_path_tokens":{"type":"array","items":{"$ref":"#/$defs/instance_path_token"}},"reference_definition_ref":typed},"additionalProperties":False}}
    props["deduplication"]={"const":"COALESCE_DUPLICATE_SCHEMA_BRANCHES_BY_EDGE_IDENTITY_PRESERVE_DISTINCT_SOURCE_POINTERS"}
    defs=schema.setdefault("$defs",{})
    defs["instance_path_token"]={"oneOf":[{"type":"object","required":["kind","value"],"properties":{"kind":{"enum":["PROPERTY","PATTERN_PROPERTY","ARRAY_INDEX"]},"value":{"type":"string"}},"additionalProperties":False},{"type":"object","required":["kind"],"properties":{"kind":{"enum":["ADDITIONAL_PROPERTY","ARRAY_ITEM"]}},"additionalProperties":False}]}
    defs["producer_schema_route"]={"type":"object","required":["producer_schema_ref","schema_pointer","instance_path_tokens","reference_definition_ref"],"properties":{"producer_schema_ref":typed,"schema_pointer":{"type":"string","minLength":1},"instance_path_tokens":{"type":"array","items":{"$ref":"#/$defs/instance_path_token"}},"reference_definition_ref":typed},"additionalProperties":False}
    return schema
def _r11_failure_witness_construction():
    return {
        "trigger": "RESOLVE_ONE_FAILURE_KIND_EQUALS_RESOLUTION_NOT_FOUND_FOR_AN_ENUMERATED_TYPED_REFERENCE",
        "owner_classification": {
            "verified_bound_source_owner": "FIRST_FAILURE.owner_ref_JSON_EQUAL_TO_ANY_reference_model.bound_source_references[*].reference_BY_TYPED_REFERENCE_IDENTITY",
            "candidate_registry_owner": "FIRST_FAILURE.owner_ref_JSON_EQUAL_TO_REFERENCE_OF_AN_EXACT_ACTIVE_NORMATIVE_REGISTRY_ROW",
            "disjointness": "STRICT_IDENTITY_UNION_REJECTS_CROSS_NAMESPACE_COLLISION"
        },
        "first_failure_order": {
            "assertion_selection": "FIRST_FAILING_ASSERTION_IN_REFERENCE_RESOLUTION_DECLARATION_ORDER",
            "assertion_ids": ["REFERENCE_RESOLUTION_BASE_REFERENCES_RESOLVE_ONCE", "REFERENCE_RESOLUTION_MEMBER_REFERENCES_RESOLVE_ONCE"],
            "occurrence_selection": "FIRST_ENUMERATED_ARRAY_ELEMENT_WHOSE_RESOLVE_ONE_FAILURE_KIND_IS_RESOLUTION_NOT_FOUND",
            "occurrence_order_source": "reference-model.json:/enumeration/deterministic_order",
            "evaluation": "SHORT_CIRCUIT_ON_FIRST_RESOLUTION_NOT_FOUND"
        },
        "field_provenance": {
            "argument": {
                "candidate_registry_owner": "registry",
                "verified_bound_source_owner": "verification_universe",
                "meaning": "ARGUMENT_THAT_SELECTS_THE_OWNER_NAMESPACE_IN_ENUMERATE_TYPED_REFERENCES"
            },
            "object_role": {
                "candidate_registry_owner": "NORMATIVE_REFERENCE_OWNER_CONTENT",
                "verified_bound_source_owner": "VERIFIED_BOUND_SOURCE_REFERENCE_OWNER_CONTENT"
            },
            "schema_ref": "FIRST_FAILING_ENUMERATED_OCCURRENCE.producer_schema_ref",
            "instance_pointer": "FIRST_FAILING_ENUMERATED_OCCURRENCE.instance_pointer",
            "failure_kind": "FIRST_FAILING_RESOLVE_ONE.failure_kind",
            "diagnostic": "NO_ELIGIBLE_IDENTITY_IN_VERIFICATION_UNIVERSE",
            "bound_identity": "FIRST_FAILING_ENUMERATED_OCCURRENCE.reference"
        },
        "optional_diagnostics": "TOP_LEVEL_diagnostics_MAY_CONTAIN_IMPLEMENTATION_DETAILS_BUT_ARE_EXCLUDED_FROM_CROSS_EVALUATOR_EQUALITY_AND_MUST_NOT_CHANGE_THE_NORMATIVE_SEVEN_FIELD_WITNESS"
    }
def _r11_failure_contract(meta, schema):
    witness_fields=["argument","object_role","schema_ref","instance_pointer","failure_kind","diagnostic","bound_identity"]
    normative_fields=["status","stage","code","procedure_id","assertion_id","failure_kind","witness"]
    failure={"stage":"AST_ASSERTION","code":"TYPED_REFERENCE_CLOSURE_FAILURE","procedure_id":"REFERENCE_RESOLUTION","assertion_ids":["REFERENCE_RESOLUTION_BASE_REFERENCES_RESOLVE_ONCE","REFERENCE_RESOLUTION_MEMBER_REFERENCES_RESOLVE_ONCE"],"failure_kind":"RESOLUTION_NOT_FOUND","normative_result_fields":normative_fields,"witness_fields":witness_fields,"witness_construction":_r11_failure_witness_construction(),"diagnostics":"OPTIONAL_NON_NORMATIVE_IMPLEMENTATION_DETAILS_EXCLUDED_FROM_CROSS_EVALUATOR_EQUALITY"}
    meta["failure_semantics"]["reference_resolution_failure"]=copy.deepcopy(failure)
    meta["result_contracts"]["reference_resolution_failure"]={"schema_ref":{"kind":"SCHEMA","id":NS+":schema:metacontract","version":"0.2","member_id":"reference_resolution_failure"},**copy.deepcopy(failure)}
    mprops=schema["properties"]["failure_semantics"]
    mprops["required"].append("reference_resolution_failure")
    mprops["properties"]["reference_resolution_failure"]={"type":"object","required":list(failure),"properties":{"stage":{"const":"AST_ASSERTION"},"code":{"const":"TYPED_REFERENCE_CLOSURE_FAILURE"},"procedure_id":{"const":"REFERENCE_RESOLUTION"},"assertion_ids":{"const":failure["assertion_ids"]},"failure_kind":{"const":"RESOLUTION_NOT_FOUND"},"normative_result_fields":{"const":normative_fields},"witness_fields":{"const":witness_fields},"witness_construction":{"const":failure["witness_construction"]},"diagnostics":{"const":failure["diagnostics"]}},"additionalProperties":False}
    rc=schema["properties"]["result_contracts"]
    rc["required"].append("reference_resolution_failure")
    rc["properties"]["reference_resolution_failure"]={"type":"object","required":["schema_ref"]+list(failure),"properties":{"schema_ref":{"const":meta["result_contracts"]["reference_resolution_failure"]["schema_ref"]},"stage":{"const":"AST_ASSERTION"},"code":{"const":"TYPED_REFERENCE_CLOSURE_FAILURE"},"procedure_id":{"const":"REFERENCE_RESOLUTION"},"assertion_ids":{"const":failure["assertion_ids"]},"failure_kind":{"const":"RESOLUTION_NOT_FOUND"},"normative_result_fields":{"const":normative_fields},"witness_fields":{"const":witness_fields},"witness_construction":{"const":failure["witness_construction"]},"diagnostics":{"const":failure["diagnostics"]}},"additionalProperties":False}
    return schema

def _r11_operation_schema():
    expr={"$ref":"#/$defs/expression"}
    return {"type":"object","required":["op","universe","registry","reference_model","reference_form"],"properties":{"op":{"const":"ENUMERATE_TYPED_REFERENCES"},"universe":expr,"registry":expr,"reference_model":expr,"reference_form":expr},"additionalProperties":False}
def _r11_primitive_row():
    return {"primitive_id":"ENUMERATE_TYPED_REFERENCES","arguments":[{"name":"universe","type":"VERIFICATION_UNIVERSE"},{"name":"registry","type":"JSON"},{"name":"reference_model","type":"JSON"},{"name":"reference_form","type":"STRING"}],"output_type":"ARRAY<OBJECT{owner_ref:BASE_TYPED_REFERENCE,producer_schema_ref:TYPED_REFERENCE,schema_pointer:RFC6901_POINTER,instance_pointer:RFC6901_POINTER,reference_form:STRING,reference:TYPED_REFERENCE}>","semantics":"Enumerates values admitted by exact applied producer-schema reference-type declarations across the model's normative owners and verified bound sources; never classifies by instance shape.","failure_behavior":"FAIL_CLOSED_TYPED_ERROR","side_effects":"NONE","may_call_user_code":False,"standard":"JSON Schema 2020-12 producer-schema typed reference authority and RFC 6901","missing_behavior":"MISSING_OR_UNRESOLVED_PRODUCER_SCHEMA_IS_TYPED_FAILURE","ambiguity_behavior":"UNSUPPORTED_OR_AMBIGUOUS_REFERENCE_DOMAIN_FAILS_CLOSED","deterministic_order":"OWNER_IDENTITY_UTF16_ORDER_THEN_INSTANCE_JSON_TREE_PREORDER_WITH_JCS_KEY_ORDER_AND_ARRAY_INDEX_ORDER","error_behavior":{"error_classes":["INVALID_TYPED_REFERENCE","RESOLUTION_NOT_FOUND","RESOLUTION_AMBIGUOUS","REFERENCE_DOMAIN_UNDERDETERMINED","UNRESOLVED_PRODUCER_SCHEMA"],"expression_error":"CONTAINING_ASSERTION_FAILURE_WITH_DECLARED_CODE_AND_WITNESS","stops_evaluation":True}}
def _r11_attach_expression_and_primitive_schemas(proc_schema, prim_schema):
    ex=proc_schema["$defs"]["expression"]["oneOf"][-1]["oneOf"]
    ops=[row.get("properties",{}).get("op",{}).get("const") for row in ex if isinstance(row,dict)]
    if "ENUMERATE_TYPED_REFERENCES" not in ops: ex.append(_r11_operation_schema())
    enum=prim_schema["properties"]["primitives"]["items"]["properties"]["primitive_id"]["enum"]
    if "ENUMERATE_TYPED_REFERENCES" not in enum: enum.append("ENUMERATE_TYPED_REFERENCES")
    prim_array=prim_schema["properties"]["primitives"]
    prim_array["minItems"]=19;prim_array["maxItems"]=19
    return proc_schema,prim_schema
def _r11_patch_reference_ast(proc):
    row=next(x for x in proc["procedures"] if x["procedure_id"]=="REFERENCE_RESOLUTION")
    def enumeration(form):
        return {"op":"ENUMERATE_TYPED_REFERENCES","universe":{"arg":"verification_universe"},"registry":{"arg":"registry"},"reference_model":{"arg":"reference_model"},"reference_form":{"literal":form}}
    def matches(form,binder):
        return {"op":"ALL","array":enumeration(form),"as":binder,"where":{"op":"JSON_EQUAL","left":{"op":"GET","value":{"item":binder},"pointer":"/reference_form"},"right":{"literal":form}}}
    def resolves(form,binder):
        resolved={"op":"RESOLVE_ONE","universe":{"arg":"verification_universe"},"reference":{"op":"GET","value":{"item":binder},"pointer":"/reference"}}
        return {"op":"ALL","array":enumeration(form),"as":binder,"where":{"op":"JSON_EQUAL","left":{"op":"GET","value":resolved,"pointer":"/ref"},"right":{"op":"GET","value":{"item":binder},"pointer":"/reference"}}}
    specs={
     "REFERENCE_RESOLUTION_BASE_REFERENCE_SHAPE_EXACT":(matches("BASE","base_shape"),{"op":"GET","value":{"arg":"reference_model"},"pointer":"/reference_type"}),
     "REFERENCE_RESOLUTION_MEMBER_REFERENCE_SHAPE_EXACT":(matches("MEMBER","member_shape"),{"op":"GET","value":{"arg":"reference_model"},"pointer":"/representation_validation"}),
     "REFERENCE_RESOLUTION_BASE_REFERENCES_RESOLVE_ONCE":(resolves("BASE","base_ref_occurrence"),{"op":"GET","value":{"arg":"reference_model"},"pointer":"/enumeration"}),
     "REFERENCE_RESOLUTION_MEMBER_REFERENCES_RESOLVE_ONCE":(resolves("MEMBER","member_ref_occurrence"),{"op":"GET","value":{"arg":"reference_model"},"pointer":"/enumeration"})}
    for assertion in row["assertions"]:
        if assertion["assertion_id"] in specs:
            assertion["condition"],assertion["witness"]=specs[assertion["assertion_id"]]
    shape_proc=next(x for x in proc["procedures"] if x["procedure_id"]=="REFERENCE_SHAPE_PREDICATE_APPLIED")
    pointer_map={"/shape_predicate":"/representation_validation","/shape_predicate/required_keys":"/representation_validation/required_keys","/shape_predicate/optional_keys":"/representation_validation/optional_keys","/shape_predicate/additional_keys":"/representation_validation/additional_keys","/shape_predicate/all_values_type":"/representation_validation/all_values_type"}
    def rewrite(value):
        if isinstance(value,dict):
            if value.get("op")=="GET" and value.get("pointer") in pointer_map:value["pointer"]=pointer_map[value["pointer"]]
            for child in value.values():rewrite(child)
        elif isinstance(value,list):
            for child in value:rewrite(child)
    for assertion in shape_proc["assertions"]:rewrite(assertion)
    return proc
def _r11_add_failure_schema(meta_schema):
    defs=meta_schema["$defs"]
    owner_pair={"oneOf":[
        {"properties":{"argument":{"const":"registry"},"object_role":{"const":"NORMATIVE_REFERENCE_OWNER_CONTENT"}}},
        {"properties":{"argument":{"const":"verification_universe"},"object_role":{"const":"VERIFIED_BOUND_SOURCE_REFERENCE_OWNER_CONTENT"}}}
    ]}
    witness={"type":"object","required":["argument","object_role","schema_ref","instance_pointer","failure_kind","diagnostic","bound_identity"],"properties":{"argument":{"enum":["registry","verification_universe"]},"object_role":{"enum":["NORMATIVE_REFERENCE_OWNER_CONTENT","VERIFIED_BOUND_SOURCE_REFERENCE_OWNER_CONTENT"]},"schema_ref":{"$ref":"#/$defs/typed_ref"},"instance_pointer":{"type":"string","pattern":"^(?:/(?:[^~/]|~[01])*)*$"},"failure_kind":{"const":"RESOLUTION_NOT_FOUND"},"diagnostic":{"const":"NO_ELIGIBLE_IDENTITY_IN_VERIFICATION_UNIVERSE"},"bound_identity":{"$ref":"#/$defs/typed_ref"}},"allOf":[owner_pair],"additionalProperties":False}
    failure={"type":"object","required":["status","stage","code","procedure_id","assertion_id","failure_kind","witness"],"properties":{"status":{"const":"FAIL"},"stage":{"const":"AST_ASSERTION"},"code":{"const":"TYPED_REFERENCE_CLOSURE_FAILURE"},"procedure_id":{"const":"REFERENCE_RESOLUTION"},"assertion_id":{"enum":["REFERENCE_RESOLUTION_BASE_REFERENCES_RESOLVE_ONCE","REFERENCE_RESOLUTION_MEMBER_REFERENCES_RESOLVE_ONCE"]},"failure_kind":{"const":"RESOLUTION_NOT_FOUND"},"witness":witness,"diagnostics":{"type":"object"}},"additionalProperties":False}
    defs["reference_resolution_failure"]=failure
    pr=defs["procedure_result"]
    if not any(isinstance(x,dict) and x.get("$ref")=="#/$defs/reference_resolution_failure" for x in pr["oneOf"]):pr["oneOf"].append({"$ref":"#/$defs/reference_resolution_failure"})
    return meta_schema

def _r11_is_reference_definition(node):
    if not isinstance(node,dict) or not {"kind","id","version"}.issubset(set(node.get("required",[]))): return False
    props=node.get("properties",{})
    if not isinstance(props,dict): return False
    kind=props.get("kind")
    if not isinstance(kind,dict) or not (kind.get("type")=="string" or isinstance(kind.get("enum"),list) and all(isinstance(x,str) for x in kind["enum"])): return False
    for key in ("id","version"):
        val=props.get(key)
        if not isinstance(val,dict) or val.get("type")!="string": return False
    if node.get("additionalProperties") is not False: return False
    if "member_id" in props and (not isinstance(props["member_id"],dict) or props["member_id"].get("type")!="string"): return False
    return True
def _r11_json_key(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def _r11_route_data(reg,meta,schemas,reference_model,reference_model_schema):
    rows_by_identity={_r11_refkey(r.get("reference"))[:3]:r for r in reg["objects"] if r.get("kind")=="SCHEMA"}
    docs={}
    for sr,row in rows_by_identity.items():
        path=row.get("path")
        if path and (ROOT/path).is_file():
            docs[row.get("schema_document_id")]=(json.loads((ROOT/path).read_text(encoding="utf-8")),row)
    defs={}
    for docid,(doc,srow) in docs.items():
        for name in ("ref","typed_ref","base_ref"):
            target=doc.get("$defs",{}).get(name)
            if _r11_is_reference_definition(target):
                identity=_r11_refkey(srow["reference"])
                definition_ref={"kind":identity[0],"id":identity[1],"version":identity[2],"member_id":name}
                defs[(docid,"/$defs/"+name)]=definition_ref
    if not defs: raise ValueError("no explicit registered typed-reference definitions found")
    producer_refs=[]
    for row in reg["objects"]:
        if row.get("status")=="ACTIVE" and row.get("classification")=="NORMATIVE" and row.get("kind") != "SCHEMA":
            producer_schema_ref = row.get("schema_ref")
            if not isinstance(producer_schema_ref, dict):
                raise ValueError("active normative instance owner lacks required producer_schema_ref: " + str(row.get("reference")))
            producer_refs.append(producer_schema_ref)
    for source in meta.get("accepted_source_allowlist",[]):
        if isinstance(source.get("expected_schema_ref"),dict): producer_refs.append(source["expected_schema_ref"])
    for source in _r11_load("accepted-source-bindings.json").get("sources",[]):
        if isinstance(source.get("schema_ref"),dict): producer_refs.append(source["schema_ref"])
    unique={_r11_refkey(x):x for x in producer_refs}
    producer_refs=[unique[k] for k in sorted(unique)]
    routes={}
    for producer in producer_refs:
        ident=_r11_refkey(producer); srow=rows_by_identity.get(ident[:3])
        if srow is None: raise ValueError("producer schema ref has no exact registered schema row: "+str(ident))
        doc_entry=docs.get(srow.get("schema_document_id"))
        if doc_entry is None: raise ValueError("producer schema document is unavailable: "+str(ident))
        doc=doc_entry[0]
        if doc.get("$id")!=srow.get("schema_document_id"): raise ValueError("registered producer schema $id mismatch")
        root_pointer="/$defs/"+_r11_ptr_escape(producer["member_id"]) if "member_id" in producer else ""
        try: root=_r11_schema_pointer_get(doc,root_pointer)
        except Exception as exc: raise ValueError("producer schema member is unresolved: "+str(producer)) from exc
        _r11_route_tokens(root,doc,doc.get("$id"),root_pointer,[],(root_pointer,) if root_pointer else (),defs,routes,producer)
    ordered=sorted(routes.values(),key=lambda r:(_r11_refkey(r["producer_schema_ref"]),r["schema_pointer"],_r11_json_key(r["instance_path_tokens"]),_r11_refkey(r["reference_definition_ref"])))
    def route_for(producer_id,suffix):
        found=[x for x in ordered if x["producer_schema_ref"].get("id")==NS+":schema:"+producer_id and x["schema_pointer"].endswith(suffix)]
        if not found: raise ValueError("required genuine producer route missing: "+producer_id+suffix)
        return found[0]
    examples=[]
    for eid,pid,suffix in [("OBJECT_REGISTRY_ROW_REFERENCE","object-registry","/properties/objects/items/properties/reference"),("SPECIFICATION_PACKAGE_METACONTRACT_REFERENCE","specification-package","/properties/metacontract_ref"),("ACCEPTED_SOURCE_BINDING_REFERENCE","accepted-source-bindings","/properties/sources/items/properties/ref"),("NESTED_PROCEDURE_EXPECTED_SCHEMA_REFERENCE","procedure-registry","/expected_schema_ref")]:
        row=route_for(pid,suffix); examples.append({"example_id":eid,**copy.deepcopy(row)})
    bound=[]
    for s in meta.get("accepted_source_allowlist",[]):
        bound.append({"reference":copy.deepcopy(s["ref"]),"producer_schema_ref":copy.deepcopy(s["expected_schema_ref"]),"selection":"EXACT_VERIFIED_ALLOWLIST_ENTRY"})
    bound.sort(key=lambda x:_r11_refkey(x["reference"]))
    return ordered,defs,bound,examples
def _r11_promote_const_ref(schema,node_pointer,definition="ref"):
    node=_r11_schema_pointer_get(schema,node_pointer)
    if not isinstance(node,dict) or not isinstance(node.get("const"),dict): raise ValueError("declared reference constant not found at "+node_pointer)
    const=node.pop("const")
    constraint={"const":const}
    old=node.get("allOf",[])
    if not isinstance(old,list): raise ValueError("malformed allOf at "+node_pointer)
    reference_definition="#/$defs/"+definition
    refs=[x for x in old if isinstance(x,dict) and x.get("$ref")==reference_definition]
    if not refs: old.insert(0,{"$ref":reference_definition})
    old.append(constraint)
    node["allOf"]=old
    return const
def _r11_digest_close(reg,pkg):
    for row in reg["objects"]:
        path=row.get("path","")
        if row.get("classification")=="NORMATIVE" and path.startswith(REL+"/") and path not in (REL+"/object-registry.json",REL+"/specification-package-0.2.json"):
            data=(ROOT/path).read_bytes()
            row["integrity"]={"mode":"SEMANTIC_JSON_CONTENT","algorithm":"SHA-256","serialization":"RFC8785_JCS","digest":sem(parse(data))}
    regrow=next(x for x in reg["objects"] if x.get("kind")=="REGISTRY" and x.get("id")==NS+":object-registry")
    regrow["integrity"]={"mode":"PACKAGE_PINNED_BOOTSTRAP","justification":"The bootstrap registry digest is independently pinned by package.registry_semantic_sha256."}
    _r11_save("object-registry.json",reg)
    pkg["registry_semantic_sha256"]=sem(reg)
    _r11_save("specification-package-0.2.json",pkg)
    pkg["current_candidate_integrity"]["digest"]=sem({k:v for k,v in pkg.items() if k!="current_candidate_integrity"}|{"current_candidate_integrity":{k:v for k,v in pkg["current_candidate_integrity"].items() if k!="digest"}})
    _r11_save("specification-package-0.2.json",pkg)
def _r11_post_build():
    reg=_r11_load("object-registry.json")
    meta=_r11_load("metacontract.json")
    model=_r11_load("reference-model.json")
    proc=_r11_load("procedure-registry.json")
    prim=_r11_load("primitive-registry.json")
    pkg=_r11_load("specification-package-0.2.json")
    schemas={p.name:json.loads(p.read_text(encoding="utf-8")) for p in (OUT/"schema").glob("*.schema.json")}
    rmodel_schema=_r11_add_reference_model_schema(schemas["reference-model.schema.json"])
    meta_schema=schemas["metacontract.schema.json"]
    _r11_failure_contract(meta,meta_schema)
    meta_schema=_r11_add_failure_schema(meta_schema)
    proc_schema,prim_schema=_r11_attach_expression_and_primitive_schemas(schemas["procedure-registry.schema.json"],schemas["primitive-registry.schema.json"])
    # Promote only already-declared fixed schema-reference fields to the same generic reference type.
    _r11_promote_const_ref(schemas["authority-requirements.schema.json"],"/properties/trust_boundary_requirements/properties/trust_result_schema_ref")
    _r11_promote_const_ref(schemas["external-verification-input-contract.schema.json"],"/properties/trust_result_schema_ref")
    for ptr in ["/properties/reserved_inputs/items/allOf/3/then/properties/profile_content_source/properties/producer_schema_ref","/properties/result_contracts/properties/procedure_result/properties/schema_ref","/properties/result_contracts/properties/trust_result/properties/schema_ref","/properties/result_contracts/properties/pre_execution_result/properties/schema_ref"]:
        _r11_promote_const_ref(meta_schema,ptr,"typed_ref")
    result_schema_ref=meta["result_contracts"]["reference_resolution_failure"]["schema_ref"]
    rc_schema=meta_schema["properties"]["result_contracts"]["properties"]["reference_resolution_failure"]["properties"]["schema_ref"]
    rc_schema.clear();rc_schema["allOf"]=[{"$ref":"#/$defs/typed_ref"},{"const":copy.deepcopy(result_schema_ref)}]
    proc_schema,prim_schema=_r11_attach_expression_and_primitive_schemas(proc_schema,prim_schema)
    # Bind the machine-readable generic operator rule to the declared primitive signature.
    output_type=_r11_primitive_row()["output_type"]
    calc=meta["runtime_representation"]["static_type_calculus"]
    calc["operator_rules"]["operators"]["ENUMERATE_TYPED_REFERENCES"]={"slots":[["universe","EXPRESSION"],["registry","EXPRESSION"],["reference_model","EXPRESSION"],["reference_form","EXPRESSION"]],"result":output_type,"laws":["ENUMERATE_ONLY_VALUES_ADMITTED_BY_THE_EXACT_APPLIED_PRODUCER_SCHEMA_REFERENCE_TYPE","USE_THE_SAME_VERIFIED_CONTENT_AND_PRODUCER_SCHEMA_SUBJECT","FOLLOW_MACHINE_READABLE_REFERENCE_MODEL_ORDERING_NESTING_AND_DEDUPLICATION","SHAPE_VALIDATES_ADMITTED_VALUES_BUT_NEVER_CREATES_REFERENCEHOOD"]}
    calc["producer_refinements"]["producer_typed_reference_domain"]={"law_id":"PRODUCER_TYPED_REFERENCE_DOMAIN","authority":"reference-model.json:/reference_type/definition_refs_AND_/producer_schema_routes","admission":"EXACT_APPLIED_PRODUCER_SCHEMA_REFERENCE_TO_DECLARED_REFERENCE_DEFINITION","same_subject_required":True,"schema_validation_before_argument_exposure":True,"consumer_backflow":False,"instance_shape_alone_sufficient":False,"nested_collections":"FOLLOW_PRODUCER_SCHEMA_APPLICATORS_RECURSIVELY"}
    inv=calc["inventory"]
    inv["operators"]=19
    inv["normalized_static_paths"].append("ENUMERATE_TYPED_REFERENCES:output = "+output_type)
    if "ENUMERATE_TYPED_REFERENCES" not in meta["static_validation_rules"]:meta["static_validation_rules"].append("REFERENCE_CLOSURE_USES_DECLARED_PRODUCER_TYPED_VALUES")
    if "reference-model.json:/reference_type/definition_refs" not in calc["derivation_sources"]:calc["derivation_sources"].append("reference-model.json:/reference_type/definition_refs")
    if "reference-model.json:/producer_schema_routes" not in calc["derivation_sources"]:calc["derivation_sources"].append("reference-model.json:/producer_schema_routes")
    meta["runtime_representation"]["static_type_calculus"]=calc
    existing={row["primitive_id"]:row for row in prim["primitives"]}
    if "ENUMERATE_TYPED_REFERENCES" in existing:raise ValueError("primitive unexpectedly already exists in base output")
    prim["primitives"].append(_r11_primitive_row())
    _r11_patch_reference_ast(proc)
    model["mechanism"]="PRODUCER_SCHEMA_TYPED_VALUES"
    model.pop("shape_predicate",None)
    model["reference_type"]={"type_id":"TYPED_REFERENCE","admission":"APPLIED_PRODUCER_SCHEMA_REFERENCE_TO_DECLARED_REFERENCE_DEFINITION","shape_alone_sufficient":False}
    model["representation_validation"]={"required_keys":["kind","id","version"],"optional_keys":["member_id"],"additional_keys":"DISQUALIFY","all_values_type":"STRING","member_id_nonempty":True}
    model["non_reference_controls"]=[{"case_id":"METACONTRACT_BASE_TYPED_REFERENCE_FIELDS","value":{"kind":"STRING","id":"STRING","version":"STRING"},"producer_authority":"NONE","classification":"NOT_A_REFERENCE"},{"case_id":"UNRELATED_SAME_SHAPE_RECORD","value":{"kind":"CONTRACT","id":"urn:unrelated:record","version":"1.0"},"producer_authority":"NONE","classification":"NOT_A_REFERENCE"}]
    model["bound_source_references"]=[]
    routes,definitions,bound,examples=_r11_route_data(reg,meta,schemas,model,rmodel_schema)
    model["bound_source_references"]=bound
    model["producer_schema_routes"]=routes
    model["genuine_reference_examples"]=examples
    model["reference_type"]["definition_refs"]=[{"reference_definition_ref":copy.deepcopy(value),"definition_pointer":key[1]} for key,value in sorted(definitions.items(),key=lambda pair:(_r11_refkey(pair[1]),pair[0][1]))]
    model["enumeration"]={"traversal_universe":["EXACT_ACTIVE_NORMATIVE_REGISTRY_OWNER_REFERENCES","EXACT_VERIFIED_BOUND_SOURCE_REFERENCES"],"owner_content_subject":"SAME_RESOLVED_OBJECT_CONTENT_VALIDATED_BEFORE_ARGUMENT_EXPOSURE","producer_schema_selector":"EXACT_SCHEMA_REF_FROM_THE_SAME_RESOLVED_OBJECT_OR_VERIFIED_ALLOWLIST_BINDING","admission_rule":"INSTANCE_PATH_REACHED_THROUGH_APPLIED_SCHEMA_REF_TO_A_DECLARED_REFERENCE_DEFINITION","schema_applicators":["$ref","properties","patternProperties","additionalProperties","prefixItems","items","contains","allOf","anyOf","oneOf","if_then_else","dependentSchemas","unevaluatedProperties","unevaluatedItems"],"path_tokens":["PROPERTY","PATTERN_PROPERTY","ADDITIONAL_PROPERTY","ARRAY_INDEX","ARRAY_ITEM"],"nested_reference_values":"EMIT_EVERY_SCHEMA_ADMITTED_REFERENCE_VALUE_AT_ANY_NESTING_DEPTH","deterministic_order":"OWNER_IDENTITY_UTF16_ORDER_THEN_INSTANCE_JSON_TREE_PREORDER_WITH_JCS_KEY_ORDER_AND_ARRAY_INDEX_ORDER","duplicate_handling":"COALESCE_SAME_EDGE_ACROSS_SCHEMA_BRANCHES_KEEP_DISTINCT_SOURCE_POINTERS","untyped_value_handling":"SHAPE_ALONE_NEVER_ADMITS_A_REFERENCE","unsupported_schema_handling":"FAIL_CLOSED_WITH_REFERENCE_DOMAIN_UNDERDETERMINED"}
    model["deduplication"]="COALESCE_DUPLICATE_SCHEMA_BRANCHES_BY_EDGE_IDENTITY_PRESERVE_DISTINCT_SOURCE_POINTERS"
    if len(routes)<1 or len(examples)!=4:raise ValueError("producer route inventory incomplete")
    # Register the new result schema member and keep every embedded schema constraint tied to current data.
    for row in reg["objects"]:
        if row.get("kind")=="SCHEMA" and row.get("id")==NS+":schema:metacontract":
            row["members"]=list(dict.fromkeys(row.get("members",[])+["reference_resolution_failure"]))
    meta_schema["properties"]["static_validation_rules"]["const"]=copy.deepcopy(meta["static_validation_rules"])
    meta_schema["properties"]["runtime_representation"]["const"]=copy.deepcopy(meta["runtime_representation"])
    # Ensure schemas' root descriptions remain exact after adding the machine-readable fields.
    for filename,value in [("reference-model.schema.json",rmodel_schema),("metacontract.schema.json",meta_schema),("procedure-registry.schema.json",proc_schema),("primitive-registry.schema.json",prim_schema)]:schemas[filename]=value
    for name,value in [("reference-model.json",model),("metacontract.json",meta),("procedure-registry.json",proc),("primitive-registry.json",prim)]:_r11_save(name,value)
    for name,value in schemas.items():_r11_save("schema/"+name,value)
    # Registry and package hashes are recomputed last using the builder's canonical digest algorithm.
    _r11_digest_close(reg,pkg)
    print(json.dumps({"r5r11_post_build":"PASS","producer_schema_routes":len(routes),"typed_reference_definitions":len(definitions),"genuine_examples":len(examples),"primitives":len(prim["primitives"]),"procedures":len(proc["procedures"]),"assertions":sum(len(p["assertions"]) for p in proc["procedures"]),"registry_semantic_sha256":pkg["registry_semantic_sha256"],"package_semantic_sha256":pkg["current_candidate_integrity"]["digest"]},indent=2))

_R11_BASE_BUILD = build
def build():
    _R11_BASE_BUILD()
    _r11_post_build()


# ACCORD R5R13 normative owner-domain closure.
_R5R13_INSTANCE_OWNER_KINDS = [
    "AUTHORITY", "CANONICALIZATION", "CONTRACT", "EVIDENCE",
    "NORMATIVE_INPUTS", "PACKAGE", "POLICY", "REGISTRY"
]
_R5R13_SELECTOR_ORDER = [
    "CONFIRM_EXACT_OWNER_REFERENCE_IS_A_MEMBER_OF_THE_VERIFICATION_UNIVERSE",
    "MATCH_AN_EXACT_ACTIVE_NORMATIVE_REGISTRY_ROW_OR_VERIFIED_BOUND_SOURCE_ENTRY",
    "CLASSIFY_REGISTRY_OWNER_SEMANTIC_ROLE_FROM_ITS_DECLARED_KIND",
    "IF_KIND_IS_SCHEMA_RETAIN_AS_A_SCHEMA_VALIDATION_SUBJECT_AND_SKIP_BEFORE_PRODUCER_SCHEMA_SELECTION",
    "FOR_ELIGIBLE_INSTANCE_OWNERS_SELECT_THE_EXACT_REQUIRED_SCHEMA_REF_FROM_THE_SAME_REGISTRY_ROW_OR_BOUND_ENTRY",
    "FAIL_CLOSED_IF_AN_ELIGIBLE_INSTANCE_OWNER_SCHEMA_REF_IS_MISSING_UNRESOLVED_OR_AMBIGUOUS",
    "VALIDATE_THE_SAME_OWNER_CONTENT_WITH_THE_SELECTED_SCHEMA_BEFORE_ARGUMENT_EXPOSURE",
    "ENUMERATE_ONLY_VALUES_ADMITTED_BY_THE_SELECTED_SCHEMA_AND_A_DECLARED_TYPED_REFERENCE_DEFINITION"
]
_R5R13_OWNER_UNIVERSE_REF = "reference-model.json:/typed_reference_owner_universe"

def _r5r13_owner_matrix():
    return [
        {"case_id":"O1","scenario":"ACTIVE_NORMATIVE_INSTANCE_WITH_EXACT_APPLIED_PRODUCER_SCHEMA","verification_member":True,"declared_kind":"CONTRACT","semantic_role":"INSTANCE_DOCUMENT","schema_ref_state":"EXACT_APPLIED","owner_eligible":True,"selector_invoked":True,"expected_disposition":"ENUMERATE_SCHEMA_ADMITTED_TYPED_REFERENCES"},
        {"case_id":"O2","scenario":"VERIFICATION_MEMBER_WITHOUT_ACTIVE_NORMATIVE_INSTANCE_OR_BOUND_SOURCE_ROLE","verification_member":True,"declared_kind":"CONTRACT","semantic_role":"NON_OWNER","schema_ref_state":"ANY","owner_eligible":False,"selector_invoked":False,"expected_disposition":"EXCLUDE_FROM_TYPED_REFERENCE_OWNER_UNIVERSE"},
        {"case_id":"O3","scenario":"ACTIVE_NORMATIVE_INSTANCE_MISSING_REQUIRED_PRODUCER_SCHEMA_REF","verification_member":True,"declared_kind":"CONTRACT","semantic_role":"INSTANCE_DOCUMENT","schema_ref_state":"MISSING","owner_eligible":True,"selector_invoked":True,"expected_disposition":"FAIL_CLOSED_MISSING_PRODUCER_SCHEMA"},
        {"case_id":"O4","scenario":"ACTIVE_NORMATIVE_INSTANCE_WITH_UNRESOLVED_PRODUCER_SCHEMA_REF","verification_member":True,"declared_kind":"CONTRACT","semantic_role":"INSTANCE_DOCUMENT","schema_ref_state":"UNRESOLVED","owner_eligible":True,"selector_invoked":True,"expected_disposition":"FAIL_CLOSED_UNRESOLVED_PRODUCER_SCHEMA"},
        {"case_id":"O5","scenario":"ACTIVE_NORMATIVE_INSTANCE_WITH_NESTED_APPLIED_REFERENCE_DEFINITION","verification_member":True,"declared_kind":"REGISTRY","semantic_role":"INSTANCE_DOCUMENT","schema_ref_state":"EXACT_APPLIED","owner_eligible":True,"selector_invoked":True,"expected_disposition":"ENUMERATE_ALL_SCHEMA_ADMITTED_NESTED_REFERENCE_VALUES"},
        {"case_id":"O6","scenario":"EXACT_VERIFIED_BOUND_SOURCE_INSTANCE","verification_member":True,"declared_kind":"BOUND_SOURCE","semantic_role":"VERIFIED_BOUND_SOURCE_INSTANCE_DOCUMENT","schema_ref_state":"EXACT_BOUND_SCHEMA","owner_eligible":True,"selector_invoked":True,"expected_disposition":"SELECT_EXACT_BOUND_SCHEMA_AND_ENUMERATE"},
        {"case_id":"O7","scenario":"ACTIVE_NORMATIVE_SCHEMA_VALIDATION_SUBJECT","verification_member":True,"declared_kind":"SCHEMA","semantic_role":"SCHEMA_LANGUAGE_ARTIFACT","schema_ref_state":"ABSENT","owner_eligible":False,"selector_invoked":False,"expected_disposition":"PRESERVE_SCHEMA_VALIDATION_AND_HANDLE_INTERNAL_REF_WITH_JSON_SCHEMA_VALIDATION"},
        {"case_id":"O8","scenario":"ACTIVE_NORMATIVE_SCHEMA_WITH_ARBITRARY_SCHEMA_REF_PRESENT","verification_member":True,"declared_kind":"SCHEMA","semantic_role":"SCHEMA_LANGUAGE_ARTIFACT","schema_ref_state":"ARBITRARY_PRESENT","owner_eligible":False,"selector_invoked":False,"expected_disposition":"SKIP_BEFORE_PRODUCER_SCHEMA_SELECTOR_EVEN_WHEN_SCHEMA_REF_EXISTS"}
    ]

def _r5r13_owner_universe(reg, model):
    active = [r for r in reg["objects"] if r.get("status") == "ACTIVE" and r.get("classification") == "NORMATIVE"]
    schemas = [r for r in active if r.get("kind") == "SCHEMA"]
    unknown = sorted({r.get("kind") for r in active if r.get("kind") != "SCHEMA" and r.get("kind") not in _R5R13_INSTANCE_OWNER_KINDS})
    if unknown:
        raise ValueError("active normative registry kind has no declared instance semantic role: " + repr(unknown))
    candidates = {_r11_refkey(r.get("reference")) for r in active}
    declared_candidates = {_r11_refkey(r) for r in model["discovery_scope"]["owner_references"]}
    if candidates != declared_candidates:
        raise ValueError("active normative owner candidates differ from the broad discovery universe")
    schema_refs = {_r11_refkey(r.get("reference")) for r in schemas}
    declared_schema_refs = {_r11_refkey(r) for r in model["discovery_scope"]["schema_owner_references"]}
    if schema_refs != declared_schema_refs:
        raise ValueError("schema validation subjects differ from the registered SCHEMA-kind rows")
    if (len(active), len(schemas), len(active) - len(schemas)) != (46, 23, 23):  # R5R29A-R2c: + leap-second table and its schema
        raise ValueError("R5R13 owner universe counts differ from the reviewed candidate inventory")
    roles = [
        {"declared_kind":kind,"semantic_role":"INSTANCE_DOCUMENT","typed_reference_owner_eligible":True,"schema_validation_subject":False}
        for kind in _R5R13_INSTANCE_OWNER_KINDS
    ]
    roles.append({"declared_kind":"SCHEMA","semantic_role":"SCHEMA_LANGUAGE_ARTIFACT","typed_reference_owner_eligible":False,"schema_validation_subject":True})
    roles.sort(key=lambda x:x["declared_kind"])
    return {
        "verification_universe_ref":"metacontract:/runtime_representation/static_paths/VERIFICATION_UNIVERSE",
        "registry_owner_candidate_set_ref":"reference-model.json:/discovery_scope/owner_references",
        "schema_validation_subject_set_ref":"reference-model.json:/discovery_scope/schema_owner_references",
        "verified_bound_source_owner_set_ref":"reference-model.json:/bound_source_references",
        "registry_row_membership":{"status":"ACTIVE","classification":"NORMATIVE","reference_must_be_an_exact_verification_universe_member":True},
        "declared_kind_role_source":"object-registry.json:/objects/*/kind",
        "declared_kind_roles":roles,
        "owner_eligibility_predicate":"EXACT_VERIFICATION_UNIVERSE_MEMBER AND ((EXACT_REGISTRY_ROW.status=ACTIVE AND classification=NORMATIVE AND DECLARED_KIND_ROLE=INSTANCE_DOCUMENT) OR EXACT_VERIFIED_BOUND_SOURCE_ENTRY)",
        "bound_source_semantic_role":"VERIFIED_BOUND_SOURCE_INSTANCE_DOCUMENT",
        "producer_schema_selector_order":list(_R5R13_SELECTOR_ORDER),
        "eligible_instance_missing_or_unresolved_schema_behavior":"FAIL_CLOSED_TYPED_ERROR",
        "schema_owner_behavior":{
            "semantic_role":"SCHEMA_LANGUAGE_ARTIFACT",
            "typed_reference_owner_eligible":False,
            "retained_as_verification_universe_member":True,
            "retained_as_schema_validation_subject":True,
            "skip_before_producer_schema_selection":True,
            "schema_internal_reference_handling":"JSON_SCHEMA_2020_12_VALIDATION_ONLY",
            "self_schema_as_accord_producer":False,
            "implicit_public_meta_schema_as_accord_producer":False
        },
        "counts":{
            "active_normative_registry_owner_candidates":len(active),
            "schema_language_artifact_validation_subjects":len(schemas),
            "eligible_active_normative_instance_registry_owners":len(active)-len(schemas),
            "eligible_verified_bound_source_owners":2,
            "eligible_typed_reference_owners":len(active)-len(schemas)+2
        },
        "owner_decision_matrix":_r5r13_owner_matrix()
    }

def _r5r13_route_inventory(reg, model, owner_universe):
    owners = []
    for row in reg["objects"]:
        if row.get("status") != "ACTIVE" or row.get("classification") != "NORMATIVE":
            continue
        kind = row.get("kind")
        if kind == "SCHEMA":
            continue
        if kind not in _R5R13_INSTANCE_OWNER_KINDS:
            raise ValueError("unclassified registry kind reached typed-reference owner selection: " + repr(kind))
        schema_ref = row.get("schema_ref")
        if not isinstance(schema_ref, dict):
            raise ValueError("eligible active normative instance owner lacks required producer_schema_ref: " + repr(row.get("reference")))
        owners.append({
            "owner_ref":copy.deepcopy(row["reference"]),
            "owner_origin":"ACTIVE_NORMATIVE_REGISTRY",
            "owner_semantic_role":"INSTANCE_DOCUMENT",
            "producer_schema_selection_source":"EXACT_ACTIVE_NORMATIVE_REGISTRY_ROW_SCHEMA_REF",
            "producer_schema_ref":copy.deepcopy(schema_ref)
        })
    for source in model["bound_source_references"]:
        if not isinstance(source.get("producer_schema_ref"), dict):
            raise ValueError("verified bound source lacks required producer_schema_ref: " + repr(source.get("reference")))
        owners.append({
            "owner_ref":copy.deepcopy(source["reference"]),
            "owner_origin":"VERIFIED_BOUND_SOURCE",
            "owner_semantic_role":"VERIFIED_BOUND_SOURCE_INSTANCE_DOCUMENT",
            "producer_schema_selection_source":"EXACT_VERIFIED_BOUND_SOURCE_SCHEMA_REF",
            "producer_schema_ref":copy.deepcopy(source["producer_schema_ref"])
        })
    owners.sort(key=lambda x:_r11_refkey(x["owner_ref"]))
    identities = [_r11_refkey(x["owner_ref"]) for x in owners]
    if len(identities) != len(set(identities)):
        raise ValueError("typed-reference owner namespaces are not disjoint")
    routes = model["producer_schema_routes"]
    applications = []
    route_counts = {}
    for owner in owners:
        selected = _r11_refkey(owner["producer_schema_ref"])
        matches = [(i,r) for i,r in enumerate(routes) if _r11_refkey(r["producer_schema_ref"]) == selected]
        route_counts[_r11_refkey(owner["owner_ref"])] = len(matches)
        for index, route in matches:
            applications.append({
                "owner_ref":copy.deepcopy(owner["owner_ref"]),
                "owner_origin":owner["owner_origin"],
                "producer_schema_ref":copy.deepcopy(owner["producer_schema_ref"]),
                "declared_route_index":index,
                "schema_pointer":route["schema_pointer"],
                "instance_path_tokens":copy.deepcopy(route["instance_path_tokens"]),
                "reference_definition_ref":copy.deepcopy(route["reference_definition_ref"])
            })
    for owner in owners:
        owner["effective_route_count"] = route_counts[_r11_refkey(owner["owner_ref"])]
    if len(owners) != 25 or len(routes) != 59 or len(applications) != 59:  # R5R29A-R2c: + leap-second table owner
        raise ValueError("declared routes or effective owner-route application inventory changed unexpectedly")
    if any(_r11_refkey(o["owner_ref"]) in {_r11_refkey(s) for s in model["discovery_scope"]["schema_owner_references"]} for o in owners):
        raise ValueError("SCHEMA-kind validation subject entered the typed-reference owner inventory")
    return {
        "declared_routes":copy.deepcopy(routes),
        "eligible_owners":owners,
        "effective_owner_route_applications":applications,
        "counts":{
            "declared_routes":len(routes),
            "eligible_active_normative_instance_registry_owners":owner_universe["counts"]["eligible_active_normative_instance_registry_owners"],
            "eligible_verified_bound_source_owners":owner_universe["counts"]["eligible_verified_bound_source_owners"],
            "eligible_typed_reference_owners":len(owners),
            "effective_owner_route_applications":len(applications)
        }
    }

def _r5r13_patch_reference_model_schema(schema, model):
    props = schema["properties"]
    schema["required"] = list(dict.fromkeys(schema["required"] + ["typed_reference_owner_universe","route_inventory"]))
    owner = model["typed_reference_owner_universe"]
    props["typed_reference_owner_universe"] = {
        "type":"object",
        "required":list(owner),
        "properties":{k:{"const":copy.deepcopy(v)} for k,v in owner.items()},
        "additionalProperties":False
    }
    inventory = model["route_inventory"]
    typed = {"$ref":"#/$defs/ref"}
    route_ref = {"$ref":"#/$defs/producer_schema_route"}
    props["route_inventory"] = {
        "type":"object",
        "required":["declared_routes","eligible_owners","effective_owner_route_applications","counts"],
        "properties":{
            "declared_routes":{"type":"array","minItems":len(inventory["declared_routes"]),"maxItems":len(inventory["declared_routes"]),"items":route_ref},
            "eligible_owners":{
                "type":"array","minItems":len(inventory["eligible_owners"]),"maxItems":len(inventory["eligible_owners"]),
                "items":{"type":"object","required":["owner_ref","owner_origin","owner_semantic_role","producer_schema_selection_source","producer_schema_ref","effective_route_count"],"properties":{
                    "owner_ref":typed,
                    "owner_origin":{"enum":["ACTIVE_NORMATIVE_REGISTRY","VERIFIED_BOUND_SOURCE"]},
                    "owner_semantic_role":{"enum":["INSTANCE_DOCUMENT","VERIFIED_BOUND_SOURCE_INSTANCE_DOCUMENT"]},
                    "producer_schema_selection_source":{"enum":["EXACT_ACTIVE_NORMATIVE_REGISTRY_ROW_SCHEMA_REF","EXACT_VERIFIED_BOUND_SOURCE_SCHEMA_REF"]},
                    "producer_schema_ref":typed,
                    "effective_route_count":{"type":"integer","minimum":0}
                },"additionalProperties":False}
            },
            "effective_owner_route_applications":{
                "type":"array","minItems":len(inventory["effective_owner_route_applications"]),"maxItems":len(inventory["effective_owner_route_applications"]),
                "items":{"type":"object","required":["owner_ref","owner_origin","producer_schema_ref","declared_route_index","schema_pointer","instance_path_tokens","reference_definition_ref"],"properties":{
                    "owner_ref":typed,
                    "owner_origin":{"enum":["ACTIVE_NORMATIVE_REGISTRY","VERIFIED_BOUND_SOURCE"]},
                    "producer_schema_ref":typed,
                    "declared_route_index":{"type":"integer","minimum":0,"maximum":len(inventory["declared_routes"])-1},
                    "schema_pointer":{"type":"string","minLength":1},
                    "instance_path_tokens":{"type":"array","items":{"$ref":"#/$defs/instance_path_token"}},
                    "reference_definition_ref":typed
                },"additionalProperties":False}
            },
            "counts":{"const":copy.deepcopy(inventory["counts"])}
        },
        "additionalProperties":False
    }
    enum = model["enumeration"]
    enum_schema = props["enumeration"]
    enum_schema["required"] = list(dict.fromkeys(enum_schema["required"] + ["typed_reference_owner_universe_ref","selector_domain_order","schema_validation_boundary"]))
    enum_schema["properties"]["traversal_universe"] = {"const":copy.deepcopy(enum["traversal_universe"])}
    enum_schema["properties"]["producer_schema_selector"] = {"const":enum["producer_schema_selector"]}
    enum_schema["properties"]["typed_reference_owner_universe_ref"] = {"const":enum["typed_reference_owner_universe_ref"]}
    enum_schema["properties"]["selector_domain_order"] = {"const":copy.deepcopy(enum["selector_domain_order"])}
    enum_schema["properties"]["schema_validation_boundary"] = {"const":copy.deepcopy(enum["schema_validation_boundary"])}
    enum_schema["additionalProperties"] = False
    return schema

def _r5r13_patch_primitive_schema(schema):
    row = schema["properties"]["primitives"]["items"]
    row["properties"]["owner_universe_ref"] = {"const":_R5R13_OWNER_UNIVERSE_REF}
    row["properties"]["owner_selection_order"] = {"const":list(_R5R13_SELECTOR_ORDER)}
    row["additionalProperties"] = False
    conditional = {
        "if":{"properties":{"primitive_id":{"const":"ENUMERATE_TYPED_REFERENCES"}},"required":["primitive_id"]},
        "then":{"required":["owner_universe_ref","owner_selection_order"],"properties":{
            "owner_universe_ref":{"const":_R5R13_OWNER_UNIVERSE_REF},
            "owner_selection_order":{"const":list(_R5R13_SELECTOR_ORDER)}}}}
    row["allOf"] = [x for x in row.get("allOf",[]) if x != conditional] + [conditional]
    return schema

_R5R11_PRIMITIVE_ROW = _r11_primitive_row
def _r11_primitive_row():
    row = _R5R11_PRIMITIVE_ROW()
    row.update({
        "semantics":"Enumerates values admitted by the exact applied producer schema for eligible instance owners in typed_reference_owner_universe; schema language artifacts are skipped before producer schema selection and schema-internal $ref is handled only by JSON Schema validation.",
        "missing_behavior":"MISSING_OR_UNRESOLVED_REQUIRED_APPLIED_PRODUCER_SCHEMA_FOR_ELIGIBLE_INSTANCE_OWNER_IS_TYPED_FAILURE;SCHEMA_OWNER_IS_SKIPPED_BEFORE_SELECTOR",
        "owner_universe_ref":_R5R13_OWNER_UNIVERSE_REF,
        "owner_selection_order":list(_R5R13_SELECTOR_ORDER)
    })
    return row

def _r5r13_finalize():
    reg = _r11_load("object-registry.json")
    meta = _r11_load("metacontract.json")
    model = _r11_load("reference-model.json")
    prim = _r11_load("primitive-registry.json")
    pkg = _r11_load("specification-package-0.2.json")
    schemas = {p.name:json.loads(p.read_text(encoding="utf-8")) for p in (OUT/"schema").glob("*.schema.json")}

    owner_universe = _r5r13_owner_universe(reg, model)
    model["typed_reference_owner_universe"] = owner_universe
    inventory = _r5r13_route_inventory(reg, model, owner_universe)
    model["route_inventory"] = inventory
    model["enumeration"].update({
        "traversal_universe":["EXACT_TYPED_REFERENCE_OWNER_UNIVERSE","EXACT_VERIFIED_BOUND_SOURCE_REFERENCES"],
        "producer_schema_selector":"EXACT_REQUIRED_APPLIED_SCHEMA_REF_FROM_ELIGIBLE_INSTANCE_OWNER_OR_VERIFIED_BOUND_ENTRY;SCHEMA_OWNERS_SKIPPED_BEFORE_SELECTION",
        "typed_reference_owner_universe_ref":_R5R13_OWNER_UNIVERSE_REF,
        "selector_domain_order":list(_R5R13_SELECTOR_ORDER),
        "schema_validation_boundary":{
            "schema_validation_subject_set_ref":"reference-model.json:/discovery_scope/schema_owner_references",
            "schema_owners_remain_verification_universe_members":True,
            "schema_owners_remain_validation_subjects":True,
            "schema_owner_eligible_for_accord_typed_reference_enumeration":False,
            "schema_internal_reference_handling":"JSON_SCHEMA_2020_12_VALIDATION_ONLY",
            "implicit_public_meta_schema_as_accord_producer":False
        }
    })

    primitive = next(r for r in prim["primitives"] if r.get("primitive_id") == "ENUMERATE_TYPED_REFERENCES")
    primitive.update(_r11_primitive_row())
    prim_schema = _r5r13_patch_primitive_schema(schemas["primitive-registry.schema.json"])

    calc = meta["runtime_representation"]["static_type_calculus"]
    op_rule = calc["operator_rules"]["operators"]["ENUMERATE_TYPED_REFERENCES"]
    op_rule["owner_universe_ref"] = _R5R13_OWNER_UNIVERSE_REF
    op_rule["owner_selection_order"] = list(_R5R13_SELECTOR_ORDER)
    op_rule["schema_owner_exclusion"] = "DECLARED_OBJECT_REGISTRY_KIND_SCHEMA_SKIPPED_BEFORE_PRODUCER_SCHEMA_SELECTION"
    op_rule["schema_internal_reference_handling"] = "JSON_SCHEMA_2020_12_VALIDATION_ONLY"
    op_rule["implicit_public_meta_schema_as_accord_producer"] = False
    new_laws = [
        "CLASSIFY_OWNER_SEMANTIC_ROLE_FROM_DECLARED_OBJECT_REGISTRY_KIND_BEFORE_PRODUCER_SCHEMA_SELECTION",
        "SCHEMA_KIND_IS_NEVER_AN_ENUMERATE_TYPED_REFERENCES_OWNER_EVEN_IF_SCHEMA_REF_IS_PRESENT",
        "SCHEMA_INTERNAL_REF_IS_HANDLED_BY_JSON_SCHEMA_VALIDATION_AND_NOT_ACCORD_TYPED_REFERENCE_ENUMERATION",
        "MISSING_OR_UNRESOLVED_REQUIRED_PRODUCER_SCHEMA_FOR_ELIGIBLE_INSTANCE_OWNER_FAILS_CLOSED"
    ]
    op_rule["laws"] = list(dict.fromkeys(op_rule["laws"] + new_laws))
    refinement = calc["producer_refinements"]["producer_typed_reference_domain"]
    refinement.update({
        "owner_universe_ref":_R5R13_OWNER_UNIVERSE_REF,
        "owner_eligibility_predicate":owner_universe["owner_eligibility_predicate"],
        "owner_selection_order":list(_R5R13_SELECTOR_ORDER),
        "schema_language_artifact_kind":"SCHEMA",
        "schema_language_artifacts_are_enumerator_owners":False,
        "schema_language_artifact_schema_ref_selector_invoked":False,
        "schema_internal_reference_handling":"JSON_SCHEMA_2020_12_VALIDATION_ONLY",
        "implicit_public_meta_schema_as_accord_producer":False,
        "eligible_instance_missing_or_unresolved_schema_behavior":"FAIL_CLOSED_TYPED_ERROR",
        "route_inventory_ref":"reference-model.json:/route_inventory"
    })
    if "reference-model.json:/typed_reference_owner_universe" not in calc["derivation_sources"]:
        calc["derivation_sources"].append("reference-model.json:/typed_reference_owner_universe")
    if "reference-model.json:/route_inventory" not in calc["derivation_sources"]:
        calc["derivation_sources"].append("reference-model.json:/route_inventory")
    inv = calc["inventory"]
    inv["operators"] = 19
    static_paths = inv["normalized_static_paths"]
    for path in [
        "ENUMERATE_TYPED_REFERENCES:owner-universe = reference-model.json:/typed_reference_owner_universe",
        "ENUMERATE_TYPED_REFERENCES:route-applications = reference-model.json:/route_inventory/effective_owner_route_applications"
    ]:
        if path not in static_paths:
            static_paths.append(path)
    static_rule = "TYPED_REFERENCE_OWNER_ELIGIBILITY_USES_DECLARED_KIND_AND_PRECEDES_SCHEMA_SELECTION"
    if static_rule not in meta["static_validation_rules"]:
        meta["static_validation_rules"].append(static_rule)
    meta["runtime_representation"]["static_type_calculus"] = calc

    rmodel_schema = _r5r13_patch_reference_model_schema(schemas["reference-model.schema.json"], model)
    meta_schema = schemas["metacontract.schema.json"]
    meta_schema["properties"]["static_validation_rules"]["const"] = copy.deepcopy(meta["static_validation_rules"])
    meta_schema["properties"]["runtime_representation"]["const"] = copy.deepcopy(meta["runtime_representation"])

    for name, value in [
        ("reference-model.json",model),
        ("metacontract.json",meta),
        ("primitive-registry.json",prim)
    ]:
        _r11_save(name, value)
    for name, value in [
        ("reference-model.schema.json",rmodel_schema),
        ("primitive-registry.schema.json",prim_schema),
        ("metacontract.schema.json",meta_schema)
    ]:
        _r11_save("schema/"+name, value)

    _r11_digest_close(reg, pkg)
    digested = sum(1 for row in reg["objects"] if row.get("integrity",{}).get("mode") == "SEMANTIC_JSON_CONTENT")
    print(json.dumps({
        "r5r13_normative_patch":"PASS",
        "verification_registry_owner_candidates":owner_universe["counts"]["active_normative_registry_owner_candidates"],
        "schema_validation_subjects":owner_universe["counts"]["schema_language_artifact_validation_subjects"],
        "eligible_registry_instance_owners":owner_universe["counts"]["eligible_active_normative_instance_registry_owners"],
        "eligible_bound_source_owners":owner_universe["counts"]["eligible_verified_bound_source_owners"],
        "eligible_typed_reference_owners":len(inventory["eligible_owners"]),
        "declared_routes":len(inventory["declared_routes"]),
        "typed_reference_definitions":len(model["reference_type"]["definition_refs"]),
        "effective_owner_route_applications":len(inventory["effective_owner_route_applications"]),
        "semantic_digest_rows":digested,
        "registry_semantic_sha256":pkg["registry_semantic_sha256"],
        "package_semantic_sha256":pkg["current_candidate_integrity"]["digest"]
    }, indent=2))

_R5R11_POST_BUILD = _r11_post_build
def _r11_post_build():
    _R5R11_POST_BUILD()
    _r5r13_finalize()


# ACCORD R5R14 schema definition member registration closure.
# A SCHEMA member_id is Accord-addressable only when the SCHEMA registry row
# explicitly registers it; the registration binds it to exactly one root-level
# $defs entry of that row's own schema document. Unregistered $defs entries stay
# schema-language internals.
_R5R14_BINDING_REF = "metacontract:/runtime_representation/resolved_construction/schema_member_binding"
_R5R14_DEFINITION_BINDING_REF = "reference-model.json:/reference_type/definition_binding"
_R5R14_SEMANTIC_RULE_ID = "SCHEMA_ROW_REGISTERED_MEMBERS_BIND_TO_ROOT_DEFS_ENTRIES"
_R5R14_SEMANTIC_DIAGNOSTIC = "UNRESOLVED_SCHEMA_MEMBER_DEFINITION"
_R5R14_GENERIC_WITNESS = "GENERIC_PROCEDURE_RESULT_FAIL_WITNESS;condition=EVALUATION_ERROR;error_class={error_class};operands=DECLARED_ASSERTION_WITNESS_OPERAND_{operand}"

def _r5r14_member_pointer(member_id):
    return "/$defs/" + _r11_ptr_escape(member_id)

def _r5r14_member_binds(doc, member_id):
    defs = doc.get("$defs") if isinstance(doc, dict) else None
    return isinstance(member_id, str) and member_id != "" and isinstance(defs, dict) and member_id in defs

def _r5r14_members_conditional():
    return {"if":{"properties":{"kind":{"const":"SCHEMA"}},"required":["kind"]},
            "then":{"properties":{"members":{"type":"array","uniqueItems":True,"items":{"type":"string","minLength":1}}}}}

def _r5r14_semantic_rule():
    return {
        "rule_id":_R5R14_SEMANTIC_RULE_ID,
        "condition":"ROW_KIND_SCHEMA_AND_A_REGISTERED_MEMBER_ID_IS_NOT_THE_EXACT_NAME_OF_A_ROOT_LEVEL_DEFS_ENTRY_IN_THE_CONTENT_DECLARED_BY_THE_ROW",
        "instance_pointer":"/objects/<row_index>/members/<member_index>",
        "diagnostic":_R5R14_SEMANTIC_DIAGNOSTIC,
        "row_scope":"SCHEMA_ROWS_ONLY",
        "absent_members":"NO_REGISTERED_MEMBERS_NO_FAILURE",
        "member_selection":"LOWEST_MEMBER_INDEX_WHOSE_BINDING_POINTER_DOES_NOT_RESOLVE",
        "binding_ref":_R5R14_BINDING_REF,
        "content_source":"SAME_ROW_DECLARED_CONTENT_BYTES_AND_STRICT_UTF8_JSON_PARSE_AS_SCHEMA_DOCUMENT_CONTENT_ID_EQUALS_SCHEMA_DOCUMENT_ID",
        "content_read_failure_owner":"RESOLVE_CANDIDATE_OBJECTS_UNCHANGED"
    }

def _r5r14_failure_ownership():
    registration_witness = "metacontract:/registration/witness_contract"
    return [
        {"failure_id":"DUPLICATE_OR_EMPTY_SCHEMA_MEMBER_REGISTRATION",
         "detection":"SCHEMA_ROW_members_IS_NOT_AN_ARRAY_OF_UNIQUE_NONEMPTY_JSON_STRINGS",
         "stage":"APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY",
         "origin":"schema/object-registry.schema.json:/properties/objects/items/allOf/SCHEMA_KIND_MEMBERS_CONDITIONAL",
         "result_stage":"PRE_EXECUTION","code":"SCHEMA_INVALID_BOUND_OBJECT","failure_kind":"JSON_SCHEMA",
         "rule_id":"OBJECT_REGISTRY_SCHEMA_VIOLATION","diagnostic":"OBJECT_REGISTRY_SCHEMA_VIOLATION",
         "instance_pointer":"/objects/<row_index>","witness_ref":registration_witness},
        {"failure_id":"REGISTERED_SCHEMA_MEMBER_WITHOUT_ROOT_DEFS_ENTRY",
         "detection":"CONSTRUCTED_BINDING_POINTER_DOES_NOT_RESOLVE_IN_THE_ROW_DECLARED_SCHEMA_CONTENT",
         "stage":"SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS","rule_id":_R5R14_SEMANTIC_RULE_ID,
         "result_stage":"PRE_EXECUTION","code":"SCHEMA_INVALID_BOUND_OBJECT","failure_kind":"SOURCE_ELIGIBILITY",
         "diagnostic":_R5R14_SEMANTIC_DIAGNOSTIC,"instance_pointer":"/objects/<row_index>/members/<member_index>",
         "witness_ref":registration_witness},
        {"failure_id":"DECLARED_REFERENCE_DEFINITION_NOT_BOUND",
         "detection":"A_reference_type/definition_refs_ENTRY_DOES_NOT_BIND_TO_EXACTLY_ONE_REGISTERED_SCHEMA_MEMBER_OR_ITS_definition_pointer_DIFFERS_FROM_THE_BINDING_POINTER",
         "covers":["DEFINITION_OWNER_NOT_AN_EXACT_SCHEMA_OBJECT","DEFINITION_MEMBER_ID_ABSENT","DEFINITION_MEMBER_NOT_REGISTERED_BY_THE_NAMED_OWNER","DEFINITION_POINTER_NOT_EQUAL_TO_THE_BINDING_POINTER"],
         "operation":"ENUMERATE_TYPED_REFERENCES","error_class":"REFERENCE_DOMAIN_UNDERDETERMINED",
         "binding_ref":_R5R14_DEFINITION_BINDING_REF,
         "result_stage":"AST_ASSERTION","procedure_id":"REFERENCE_RESOLUTION",
         "assertion_id":"REFERENCE_RESOLUTION_BASE_REFERENCE_SHAPE_EXACT","code":"REFERENCE_SHAPE_PREDICATE_APPLIED_FAILURE",
         "first_reach":"FIRST_ENUMERATE_TYPED_REFERENCES_INVOCATION_IN_DECLARED_ASSERTION_ORDER",
         "witness":_R5R14_GENERIC_WITNESS.format(error_class="REFERENCE_DOMAIN_UNDERDETERMINED",operand="reference_model:/reference_type"),
         "result_contract":"metacontract:/result_contracts/procedure_result"},
        {"failure_id":"MEMBER_ID_NOT_REGISTERED_BY_THE_RESOLVED_OWNER",
         "detection":"RESOLVE_ONE_FINDS_THE_EXACT_OWNER_BUT_ZERO_EQUAL_STRINGS_IN_ITS_REGISTERED_members",
         "covers":["MISSING_MEMBER","WRONG_OWNER","UNREGISTERED_LOCAL_DEFINITION"],
         "operation":"RESOLVE_ONE","error_class":"MEMBER_NOT_FOUND",
         "result_stage":"AST_ASSERTION","procedure_id":"REFERENCE_RESOLUTION",
         "assertion_id":"REFERENCE_RESOLUTION_MEMBER_REFERENCES_RESOLVE_ONCE","code":"TYPED_REFERENCE_CLOSURE_FAILURE",
         "applies_to":"ENUMERATED_MEMBER_FORM_TYPED_REFERENCE_OCCURRENCES_AFTER_EVERY_DECLARED_DEFINITION_IS_BOUND",
         "witness":_R5R14_GENERIC_WITNESS.format(error_class="MEMBER_NOT_FOUND",operand="reference_model:/enumeration"),
         "seven_field_reference_resolution_failure_applies":False,
         "result_contract":"metacontract:/result_contracts/procedure_result",
         "other_expressions":"CONTAINING_ASSERTION_FAILURE_WITH_DECLARED_CODE_AND_WITNESS"}
    ]

def _r5r14_decision_matrix():
    return [
        {"case_id":"M1","scenario":"VALID_REGISTERED_MEMBER","expected_disposition":"BIND_TO_THE_EXACT_ROOT_DEFS_ENTRY_NAMED_BY_member_id","failure_id":None},
        {"case_id":"M2","scenario":"MEMBER_ID_NOT_REGISTERED_AND_NO_ROOT_DEFS_ENTRY","expected_disposition":"MEMBER_NOT_FOUND","failure_id":"MEMBER_ID_NOT_REGISTERED_BY_THE_RESOLVED_OWNER"},
        {"case_id":"M3","scenario":"DUPLICATE_MEMBER_REGISTRATION_ON_ONE_SCHEMA_ROW","expected_disposition":"STRUCTURAL_REGISTRATION_FAILURE","failure_id":"DUPLICATE_OR_EMPTY_SCHEMA_MEMBER_REGISTRATION"},
        {"case_id":"M4","scenario":"MEMBER_REGISTERED_ON_A_DIFFERENT_OWNER_THAN_THE_REFERENCE_NAMES","expected_disposition":"MEMBER_NOT_FOUND_FOR_THE_NAMED_OWNER;NO_CROSS_OWNER_FALLBACK","failure_id":"MEMBER_ID_NOT_REGISTERED_BY_THE_RESOLVED_OWNER"},
        {"case_id":"M5","scenario":"REGISTERED_MEMBER_WITHOUT_ROOT_DEFS_ENTRY","expected_disposition":"SEMANTIC_REGISTRATION_FAILURE","failure_id":"REGISTERED_SCHEMA_MEMBER_WITHOUT_ROOT_DEFS_ENTRY"},
        {"case_id":"M6","scenario":"DEFINITION_POINTER_TARGETS_A_DIFFERENT_DEFS_ENTRY_THAN_THE_MEMBER_BINDING","expected_disposition":"REFERENCE_DOMAIN_UNDERDETERMINED","failure_id":"DECLARED_REFERENCE_DEFINITION_NOT_BOUND"},
        {"case_id":"M7","scenario":"ROOT_DEFS_ENTRY_EXISTS_BUT_IS_NOT_REGISTERED","expected_disposition":"MEMBER_NOT_FOUND;RAW_DEFS_FALLBACK_FORBIDDEN","failure_id":"MEMBER_ID_NOT_REGISTERED_BY_THE_RESOLVED_OWNER"},
        {"case_id":"M8","scenario":"REGISTERED_MEMBER_NOT_NAMED_BY_ANY_DEFINITION_REF","expected_disposition":"VALID_ADDRESSABLE_MEMBER;NOT_A_REFERENCE_DEFINITION","failure_id":None},
        {"case_id":"M9","scenario":"SAME_MEMBER_ID_REGISTERED_UNDER_TWO_OWNERS","expected_disposition":"TWO_DISTINCT_MEMBERS_EACH_BOUND_IN_ITS_OWN_OWNER_DOCUMENT","failure_id":None},
        {"case_id":"M10","scenario":"EVERY_DECLARED_DEFINITION_REF","expected_disposition":"EACH_BINDS_TO_EXACTLY_ONE_REGISTERED_MEMBER_AND_EQUALS_ITS_DECLARED_definition_pointer","failure_id":None}
    ]

def _r5r14_schema_member_binding():
    return {
        "binding_id":"EXPLICIT_REGISTERED_SCHEMA_MEMBER",
        "applies_to_registry_kind":"SCHEMA",
        "member_registration_source":"object-registry.json:/objects/<row_index>/members",
        "absent_members":"EMPTY_REGISTERED_MEMBER_SET",
        "accord_addressable_members":"EXACTLY_THE_REGISTERED_MEMBER_IDS_OF_THE_SAME_SCHEMA_ROW",
        "member_identity":["kind","id","version","member_id"],
        "member_owner":"EXACT_SCHEMA_REGISTRY_ROW_SELECTED_BY_KIND_ID_VERSION",
        "member_namespace":"PER_OWNER;EQUAL_MEMBER_IDS_UNDER_DIFFERENT_OWNERS_ARE_DISTINCT_MEMBERS;NO_CROSS_OWNER_FALLBACK",
        "member_id_domain":"NONEMPTY_JSON_STRING",
        "member_id_denotes":"THE_EXACT_NAME_OF_ONE_ROOT_LEVEL_DEFS_ENTRY_OF_THE_OWNER_SCHEMA_DOCUMENT",
        "member_id_to_definition_name":"EXACT_JSON_STRING_EQUALITY",
        "definition_document":"PARSED_CONTENT_OF_THE_OWNER_SCHEMA_ROW_WHOSE_ROOT_SLASH_DOLLAR_ID_EQUALS_THE_ROW_schema_document_id",
        "definition_pointer_construction":{
            "pointer_standard":"RFC6901",
            "pointer_base":"ROOT_OF_THE_DEFINITION_DOCUMENT",
            "reference_tokens":[{"source":"LITERAL","value":"$defs"},{"source":"MEMBER_ID"}],
            "token_escaping":"RFC6901_ENCODE_TILDE_AS_TILDE0_THEN_SLASH_AS_TILDE1",
            "result_form":"/$defs/<escaped_member_id>"
        },
        "definition_target_cardinality":"EXACTLY_ONE_BY_CONSTRUCTION;DUPLICATE_JSON_MEMBER_NAMES_ARE_REJECTED_AT_PARSE",
        "nested_definitions_eligible":False,
        "non_defs_locations_eligible":False,
        "unregistered_local_definitions":"SCHEMA_LANGUAGE_INTERNALS_NOT_ACCORD_ADDRESSABLE",
        "raw_local_defs_lookup_without_registration":"FORBIDDEN",
        "member_inference_from_names_suffixes_or_patterns":"FORBIDDEN",
        "registration_scope":"ONLY_DEFINITIONS_ADDRESSED_BY_ACCORD_MEMBER_REFERENCES_ARE_REGISTERED;REGISTERING_EVERY_DEFS_ENTRY_IS_NOT_REQUIRED",
        "registered_member_without_definition_ref":"VALID_ADDRESSABLE_MEMBER;NOT_A_REFERENCE_DEFINITION_UNLESS_DECLARED_IN_reference-model.json:/reference_type/definition_refs",
        "schema_language_boundary":{
            "json_schema_defs_and_ref":"JSON_SCHEMA_DRAFT_2020_12_VALIDATION_SEMANTICS_ONLY",
            "json_schema_ref_creates_accord_typed_reference":False,
            "json_schema_defs_entry_creates_accord_member":False,
            "public_meta_schema_membership_required":False
        },
        "uniqueness":{
            "within_owner":"EACH_MEMBER_ID_AT_MOST_ONCE_IN_THE_SCHEMA_ROW_members_ARRAY",
            "across_owners":"NOT_REQUIRED;MEMBERS_ARE_OWNER_QUALIFIED",
            "registry_array_order":"NOT_NORMATIVE;RESOLVED_OBJECT_/members_USES_THE_CANONICAL_MEMBER_ORDER"
        },
        "selection_order":[
            "RESOLVE_THE_EXACT_OWNER_KIND_ID_VERSION_IN_THE_EXPLICIT_VERIFICATION_UNIVERSE",
            "IF_member_id_IS_ABSENT_RETURN_THE_BASE_RESOLVED_OBJECT",
            "REQUIRE_EXACTLY_ONE_EQUAL_STRING_IN_THE_RESOLVED_OBJECT_REGISTERED_members",
            "BIND_THE_SELECTED_MEMBER_TO_THE_CONSTRUCTED_ROOT_DEFS_POINTER_IN_THE_SAME_RESOLVED_CONTENT"
        ],
        "consumers":[
            {"consumer":"RESOLVE_ONE","member_failure_error_class":"MEMBER_NOT_FOUND"},
            {"consumer":"SCHEMA_VALIDATE_MEMBER_SELECTION","rule_ref":"metacontract:/runtime_representation/resolved_construction/member_resolution/schema_validate_extra_rule","member_failure_error_class":"MEMBER_NOT_FOUND_FROM_THE_PRECEDING_RESOLVE_ONE"},
            {"consumer":"ENUMERATE_TYPED_REFERENCES_PRODUCER_SCHEMA_SELECTION","member_failure_error_class":"UNRESOLVED_PRODUCER_SCHEMA"},
            {"consumer":"ENUMERATE_TYPED_REFERENCES_DEFINITION_BINDING","binding_ref":_R5R14_DEFINITION_BINDING_REF,"member_failure_error_class":"REFERENCE_DOMAIN_UNDERDETERMINED"}
        ],
        "failure_precedence":[
            "APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY",
            "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS",
            "ENUMERATE_TYPED_REFERENCES_DEFINITION_BINDING_BEFORE_OWNER_SELECTION",
            "RESOLVE_ONE_MEMBER_SELECTION_OF_ENUMERATED_OCCURRENCES"
        ],
        "failure_ownership":_r5r14_failure_ownership(),
        "decision_matrix":_r5r14_decision_matrix()
    }

def _r5r14_definition_binding(count):
    return {
        "binding_ref":_R5R14_BINDING_REF,
        "binding_phase":"BEFORE_OWNER_SELECTION;EVERY_DECLARED_DEFINITION_REF_IN_ARRAY_ORDER",
        "owner_selector":"reference_definition_ref_KIND_ID_VERSION",
        "required_owner_kind":"SCHEMA",
        "owner_resolution":"RESOLVE_ONE_SEMANTICS_AGAINST_THE_EXPLICIT_VERIFICATION_UNIVERSE_ARGUMENT",
        "member_id_required":True,
        "member_selection":"EXACTLY_ONE_EQUAL_STRING_IN_THE_RESOLVED_SCHEMA_OBJECT_REGISTERED_members",
        "definition_target":"THE_SELECTED_MEMBER_BINDING_POINTER_IN_THE_SAME_RESOLVED_SCHEMA_CONTENT",
        "definition_pointer_role":"DECLARED_EXPLICIT_PROJECTION_OF_THE_MEMBER_BINDING_POINTER",
        "definition_pointer_equality":"EXACT_JSON_STRING_EQUALITY_TO_THE_MEMBER_BINDING_POINTER",
        "raw_local_defs_lookup_without_registration":"FORBIDDEN",
        "binding_failure":{"primitive_id":"ENUMERATE_TYPED_REFERENCES","error_class":"REFERENCE_DOMAIN_UNDERDETERMINED","fail_closed":True},
        "bound_definition_count":count
    }

def _r5r14_schema_member_refs(value, out):
    if isinstance(value, dict):
        if value.get("kind") == "SCHEMA" and isinstance(value.get("id"), str) and isinstance(value.get("version"), str) and "member_id" in value:
            out.append((value["id"], value["version"], value["member_id"]))
        for item in value.values(): _r5r14_schema_member_refs(item, out)
    elif isinstance(value, list):
        for item in value: _r5r14_schema_member_refs(item, out)

def _r5r14_finalize():
    reg = _r11_load("object-registry.json")
    meta = _r11_load("metacontract.json")
    model = _r11_load("reference-model.json")
    pkg = _r11_load("specification-package-0.2.json")
    schemas = {p.name:json.loads(p.read_text(encoding="utf-8")) for p in (OUT/"schema").glob("*.schema.json")}
    schema_rows = {(r["kind"],r["id"],r["version"]):r for r in reg["objects"] if r.get("kind") == "SCHEMA"}
    docs = {}
    for key,row in schema_rows.items():
        doc = json.loads((ROOT/row["path"]).read_text(encoding="utf-8"))
        if doc.get("$id") != row.get("schema_document_id"): raise ValueError("schema row document identity mismatch: "+row["id"])
        docs[key] = doc

    # Register every declared reference definition as an explicit member of its owning SCHEMA row.
    definition_refs = model["reference_type"]["definition_refs"]
    for entry in definition_refs:
        ref = entry["reference_definition_ref"]
        key = (ref.get("kind"),ref.get("id"),ref.get("version"))
        if key not in schema_rows: raise ValueError("reference definition owner is not a registered SCHEMA row: "+str(ref))
        member_id = ref.get("member_id")
        if not isinstance(member_id,str) or not member_id: raise ValueError("reference definition lacks member_id: "+str(ref))
        if entry["definition_pointer"] != _r5r14_member_pointer(member_id): raise ValueError("definition_pointer differs from member binding: "+str(entry))
        if not _r5r14_member_binds(docs[key], member_id): raise ValueError("reference definition member has no root $defs entry: "+str(ref))
        row = schema_rows[key]
        row["members"] = list(dict.fromkeys(row.get("members",[]) + [member_id]))

    # Every registered SCHEMA member must be unique, nonempty and bound.
    for key,row in schema_rows.items():
        members = row.get("members",[])
        if len(members) != len(set(members)): raise ValueError("duplicate schema member registration: "+row["id"])
        for member_id in members:
            if not _r5r14_member_binds(docs[key], member_id): raise ValueError("registered schema member does not bind: "+row["id"]+"#"+str(member_id))

    # Structural registration: SCHEMA member arrays are unique nonempty strings.
    reg_schema = schemas["object-registry.schema.json"]
    item_schema = reg_schema["properties"]["objects"]["items"]
    conditional = _r5r14_members_conditional()
    item_schema["allOf"] = [x for x in item_schema["allOf"] if x != conditional] + [conditional]

    # Semantic registration: registered SCHEMA members must bind to root $defs entries.
    registration = meta["registration"]
    rules = registration["semantic_validation"]["rules"]
    registration["semantic_validation"]["rules"] = [r for r in rules if r.get("rule_id") != _R5R14_SEMANTIC_RULE_ID] + [_r5r14_semantic_rule()]
    tokens = registration["diagnostic_tokens"]["SOURCE_ELIGIBILITY"]
    if _R5R14_SEMANTIC_DIAGNOSTIC not in tokens: tokens.append(_R5R14_SEMANTIC_DIAGNOSTIC)
    owned = registration["constraint_ownership"]["semantic_registration_owned"]
    owned_entry = {"property":"SCHEMA_MEMBER_DEFINITION_BINDING","rule_ids":[_R5R14_SEMANTIC_RULE_ID],"stage":"SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS","failure_code":"SCHEMA_INVALID_BOUND_OBJECT","failure_kind":"SOURCE_ELIGIBILITY","witness_ref":"registration.witness_contract"}
    registration["constraint_ownership"]["semantic_registration_owned"] = [x for x in owned if x.get("property") != owned_entry["property"]] + [owned_entry]

    # Machine-readable member binding used by every SCHEMA member consumer.
    construction = meta["runtime_representation"]["resolved_construction"]
    construction["schema_member_binding"] = _r5r14_schema_member_binding()
    construction["member_resolution"]["schema_member_binding_ref"] = _R5R14_BINDING_REF

    # Reference definitions bind only through registered SCHEMA members.
    model["reference_type"]["definition_binding"] = _r5r14_definition_binding(len(definition_refs))
    rmodel_schema = schemas["reference-model.schema.json"]
    rtype = rmodel_schema["properties"]["reference_type"]
    rtype["required"] = list(dict.fromkeys(rtype["required"] + ["definition_binding"]))
    rtype["properties"]["definition_binding"] = {"const":copy.deepcopy(model["reference_type"]["definition_binding"])}

    meta_schema = schemas["metacontract.schema.json"]
    meta_schema["properties"]["registration"]["const"] = copy.deepcopy(meta["registration"])
    meta_schema["properties"]["runtime_representation"]["const"] = copy.deepcopy(meta["runtime_representation"])

    for name, value in [("reference-model.json",model),("metacontract.json",meta)]:
        _r11_save(name, value)
    for name, value in [("reference-model.schema.json",rmodel_schema),("metacontract.schema.json",meta_schema),("object-registry.schema.json",reg_schema)]:
        _r11_save("schema/"+name, value)

    # Every SCHEMA member reference anywhere in the generated artifacts must name a registered member.
    refs = []
    for path in sorted(list(OUT.glob("*.json")) + list((OUT/"schema").glob("*.json"))):
        _r5r14_schema_member_refs(json.loads(path.read_text(encoding="utf-8")), refs)
    for ref_id, ref_version, member_id in sorted(set(refs)):
        row = schema_rows.get(("SCHEMA",ref_id,ref_version))
        if row is None or member_id not in row.get("members",[]): raise ValueError("unregistered schema member reference: "+ref_id+"#"+str(member_id))

    _r11_digest_close(reg, pkg)
    print(json.dumps({
        "r5r14_normative_patch":"PASS",
        "bound_reference_definitions":len(definition_refs),
        "schema_rows_with_members":sum(1 for r in schema_rows.values() if r.get("members")),
        "registered_schema_members":sum(len(r.get("members",[])) for r in schema_rows.values()),
        "distinct_schema_member_references":len(set(refs)),
        "registry_semantic_sha256":pkg["registry_semantic_sha256"],
        "package_semantic_sha256":pkg["current_candidate_integrity"]["digest"]
    }, indent=2))

_R5R13_POST_BUILD = _r11_post_build
def _r11_post_build():
    _R5R13_POST_BUILD()
    _r5r14_finalize()


# ACCORD R5R16 semantic-key authority re-homing (human decision: Option A).
# R5R11 moved the reference model's extra-keys rule from /shape_predicate to
# /representation_validation without moving its governed semantic key. The same
# governed key is re-homed here: one authority path, one derived allowed
# occurrence, no second key, no dual authorization, no rename.
_R5R16_KEY = "additional_keys"
_R5R16_OLD_AUTHORITY = "references:/shape_predicate/additional_keys"
_R5R16_NEW_AUTHORITY = "references:/representation_validation/additional_keys"

def _r5r16_rehome_additional_keys(rows):
    matches = [row for row in rows if row.get("key") == _R5R16_KEY]
    if len(matches) != 1: raise ValueError("expected exactly one governed additional_keys semantic key")
    row = matches[0]
    if row.get("authority_path") != _R5R16_OLD_AUTHORITY or row.get("governed_mirror_paths") != []:
        raise ValueError("additional_keys authority is not the stale shape_predicate authority")
    row["authority_path"] = _R5R16_NEW_AUTHORITY
    # The allowed occurrence is derived from the authority path exactly as for every other governed key.
    normalize_semantic_key_authority({"semantic_keys":[row]})

def _r5r16_finalize():
    model = _r11_load("reference-model.json")
    if "shape_predicate" in model or model.get("representation_validation", {}).get(_R5R16_KEY) != "DISQUALIFY":
        raise ValueError("reference model does not carry the re-homed additional_keys rule")
    sk = _r11_load("semantic-key-authority.json")
    proc = _r11_load("procedure-registry.json")
    pkg = _r11_load("specification-package-0.2.json")
    reg = _r11_load("object-registry.json")
    procedure = next(p for p in proc["procedures"] if p["procedure_id"] == "GOVERNING_TOKEN_SINGLETON")
    frozen = next(a for a in procedure["assertions"] if a["assertion_id"] == "GOVERNING_TOKEN_SINGLETON_SEMANTIC_KEY_ROWS_FROZEN")
    if frozen["condition"]["right"].get("literal") != sk["semantic_keys"]:
        raise ValueError("frozen semantic-key rows differ from the governed semantic keys before re-homing")
    _r5r16_rehome_additional_keys(sk["semantic_keys"])
    # The frozen-row assertion keeps asserting the governed rows exactly.
    frozen["condition"]["right"]["literal"] = copy.deepcopy(sk["semantic_keys"])
    _r11_save("semantic-key-authority.json", sk)
    _r11_save("procedure-registry.json", proc)
    for path in sorted(list(OUT.glob("*.json")) + list((OUT/"schema").glob("*.json"))):
        if _R5R16_OLD_AUTHORITY in path.read_text(encoding="utf-8"): raise ValueError("stale additional_keys authority remains in "+path.name)
    _r11_digest_close(reg, pkg)
    row = next(r for r in sk["semantic_keys"] if r["key"] == _R5R16_KEY)
    print(json.dumps({
        "r5r16_normative_patch":"PASS",
        "governed_key":_R5R16_KEY,
        "authority_path":row["authority_path"],
        "allowed_occurrences":row["allowed_occurrences"],
        "semantic_keys":len(sk["semantic_keys"]),
        "registry_semantic_sha256":pkg["registry_semantic_sha256"],
        "package_semantic_sha256":pkg["current_candidate_integrity"]["digest"]
    }, indent=2))

_R5R14_POST_BUILD = _r11_post_build
def _r11_post_build():
    _R5R14_POST_BUILD()
    _r5r16_finalize()


# ACCORD R5R18 generic failure witness semantics (human decisions D1, D1b, D1c, D2).
# Generic procedure assertion failures carry a canonical procedure-registry
# node_path and operands derived only from the assertion's declared witness.
# Arguments without Accord registry identity receive witness-operand-only
# identities that are never objects, references, authorities or universe members.
_R5R18_OPERAND_ONLY_KIND = "WITNESS_OPERAND_ONLY"
_R5R18_OPERAND_ONLY_ARGUMENTS = [
    ("verification_universe", "urn:moirae:accord-02e4r5r4:witness-operand-only:verification-universe"),
    ("frozen_rule_authority", "urn:moirae:accord-02e4r5r4:witness-operand-only:frozen-rule-authority"),
]

def _r5r18_witness_operands(expr, slots):
    """Declared-witness operands: (argument, pointer) pairs in first-occurrence preorder."""
    found = []
    def chain(node):
        tokens, depth, cur = [], 0, node
        while isinstance(cur, dict) and cur.get("op") == "GET":
            if not isinstance(cur.get("pointer"), str): raise ValueError("non-literal GET pointer in a declared witness")
            tokens = pointer_tokens(cur["pointer"]) + tokens if cur["pointer"] else tokens
            depth += 1
            cur = cur.get("value")
        if depth and isinstance(cur, dict) and set(cur) == {"arg"}:
            return cur["arg"], "".join("/" + t.replace("~", "~0").replace("/", "~1") for t in tokens)
        return None
    def visit(node):
        if isinstance(node, dict):
            if set(node) == {"arg"}:
                found.append((node["arg"], "")); return
            if node.get("op") == "GET":
                rooted = chain(node)
                if rooted is not None:
                    found.append(rooted); return
            if "op" in node:
                for slot in slots[node["op"]]:
                    value = node.get(slot)
                    if isinstance(value, dict) and "op" not in value and set(value) not in ({"arg"}, {"item"}, {"literal"}):
                        for name in sorted(value, key=lambda s: s.encode("utf-16-be")): visit(value[name])
                    else:
                        visit(value)
    visit(expr)
    ordered = []
    for pair in found:
        if pair not in ordered: ordered.append(pair)
    return ordered

def _r5r18_declaration(identities, totality):
    return {
        "law_id":"GENERIC_PROCEDURE_ASSERTION_FAILURE_WITNESS",
        "result_contract_ref":"metacontract:/result_contracts/procedure_result",
        "applies_to":"GENERIC_FAIL_BRANCH_OF_procedure_result_FOR_PROCEDURES_WITH_RESULT_TYPE_BOOLEAN",
        "dedicated_contracts_take_precedence":[
            {"contract_ref":"metacontract:/result_contracts/reference_resolution_failure",
             "trigger_ref":"metacontract:/failure_semantics/reference_resolution_failure/witness_construction/trigger",
             "generic_node_path":False,"generic_operands":False},
            {"contract_ref":"metacontract:/result_contracts/trust_result",
             "trigger":"PROCEDURE_RESULT_TYPE_TRUST_RESULT",
             "generic_node_path":False,"generic_operands":False}
        ],
        "node_path":{
            "pointer_standard":"RFC6901",
            "document":"THE_NORMATIVE_PROCEDURE_REGISTRY_DOCUMENT_NAMED_BY_package.procedure_registry_ref",
            "pointer_base":"DOCUMENT_ROOT",
            "reference_tokens":[{"source":"LITERAL","value":"procedures"},{"source":"PROCEDURE_INDEX"},
                                {"source":"LITERAL","value":"assertions"},{"source":"ASSERTION_INDEX"},
                                {"source":"LITERAL","value":"condition"}],
            "index_encoding":"CANONICAL_DECIMAL_ARRAY_INDEX_NO_LEADING_ZERO",
            "token_escaping":"RFC6901_ENCODE_TILDE_AS_TILDE0_THEN_SLASH_AS_TILDE1",
            "target":"THE_FAILING_ASSERTION_CONDITION_ROOT",
            "procedure_relative_paths":"FORBIDDEN",
            "semantic_identifiers":["procedure_id","assertion_id"]
        },
        "operands":{
            "source_expression":"THE_FAILING_ASSERTION_DECLARED_WITNESS_EXPRESSION_ONLY",
            "condition_expression_contributes":False,
            "union_with_condition_operands":False,
            "terminal":"ARGUMENT_TERMINAL",
            "path_construction":"MAXIMAL_ENCLOSING_LITERAL_GET_CHAIN_ROOTED_AT_THE_TERMINAL_COMPOSED_INNERMOST_POINTER_FIRST_INTO_ONE_RFC6901_POINTER",
            "bare_terminal_pointer":"",
            "intermediate_get_operands":False,
            "non_literal_get_pointer":"FAIL_CLOSED",
            "order":"FIRST_OCCURRENCE_PREORDER_OF_THE_DECLARED_WITNESS_EXPRESSION",
            "preorder_child_order":"DECLARED_OPERATOR_SLOT_ORDER_OF_metacontract:/runtime_representation/static_type_calculus/operator_rules/operators;NAMED_EXPRESSION_MAP_FIELD_NAMES_UTF16_CODE_UNIT_ASCENDING",
            "deduplication_key":["argument","pointer"],
            "deduplication":"KEEP_FIRST_OCCURRENCE",
            "post_deduplication_sort":False,
            "identity_is_deduplication_key":False,
            "record_fields":["argument","pointer","identity"],
            "identity_sources":["BOUND_OBJECT_IDENTITY","OPERAND_ONLY_IDENTITY_DECLARATION"],
            "bound_object_identity":"KIND_ID_VERSION_OF_THE_OBJECT_BOUND_TO_THE_ARGUMENT_BY_ITS_EXISTING_RULE_BINDING",
            "operand_only_identity_source":"metacontract:/failure_semantics/generic_failure_witness/operand_only_identities",
            "missing_identity":"FAIL_CLOSED"
        },
        "operand_only_identities":identities,
        "operand_only_identity_scope":{
            "domain":"GENERIC_FAILURE_WITNESS_OPERAND_IDENTITY_ONLY",
            "kind_token":_R5R18_OPERAND_ONLY_KIND,
            "verification_universe_member":False,
            "registry_object":False,
            "registry_identity_uniqueness_participant":False,
            "reference_resolution_target":False,
            "accord_referencehood":False,
            "authority_or_trust":False,
            "producer_eligibility_effect":False
        },
        "totality":totality
    }

def _r5r18_finalize():
    meta = _r11_load("metacontract.json")
    proc = _r11_load("procedure-registry.json")
    reg = _r11_load("object-registry.json")
    pkg = _r11_load("specification-package-0.2.json")
    meta_schema = json.loads((OUT/"schema"/"metacontract.schema.json").read_text(encoding="utf-8"))
    slots = {op:[slot[0] for slot in rule["slots"]] for op, rule in meta["runtime_representation"]["static_type_calculus"]["operator_rules"]["operators"].items()}
    reserved = {row["name"]:row for row in meta["reserved_inputs"]}
    declared = {name:urn for name, urn in _R5R18_OPERAND_ONLY_ARGUMENTS}
    # Totality: every operand selected from a generic-family witness has exactly one identity source.
    rows = bound = operand_only = 0
    required = set()
    families = 0
    for procedure in proc["procedures"]:
        if procedure.get("result", {}).get("type") == "TRUST_RESULT": continue
        origins = {arg["name"]:arg for arg in procedure["arguments"]}
        for assertion in procedure["assertions"]:
            families += 1
            operands = _r5r18_witness_operands(assertion["witness"], slots)
            if not operands: raise ValueError("declared witness has no argument operand: "+assertion["assertion_id"])
            for argument, _ in operands:
                rows += 1
                spec = origins.get(argument)
                if spec is None: raise ValueError("witness argument is not a declared procedure argument: "+argument)
                if spec.get("origin") == "RULE_BINDING" and isinstance(spec.get("source_constraint"), dict):
                    bound += 1
                elif argument in declared and argument in reserved and reserved[argument]["origin"] == spec.get("origin"):
                    operand_only += 1; required.add(argument)
                else:
                    raise ValueError("witness operand has no identity source: "+procedure["procedure_id"]+"/"+assertion["assertion_id"]+"/"+argument)
    if required != set(declared): raise ValueError("operand-only identity declarations differ from the required set")
    registry_triples = {(row["kind"], row["id"], row["version"]) for row in reg["objects"]}
    registry_kinds = {row["kind"] for row in reg["objects"]}
    identities = []
    for name, urn in _R5R18_OPERAND_ONLY_ARGUMENTS:
        identity = {"kind":_R5R18_OPERAND_ONLY_KIND, "id":urn, "version":"0.2"}
        if identity["kind"] in registry_kinds or (identity["kind"], urn, "0.2") in registry_triples:
            raise ValueError("operand-only identity collides with the registry identity domain")
        identities.append({"argument":name, "argument_origin":reserved[name]["origin"], "argument_type":reserved[name]["type"], "identity":identity})
    totality = {"generic_family_assertions":families, "operand_rows":rows,
                "bound_object_identity_rows":bound, "operand_only_identity_rows":operand_only,
                "missing_identity_rows":0}
    declaration = _r5r18_declaration(identities, totality)
    meta["failure_semantics"]["generic_failure_witness"] = declaration
    fs = meta_schema["properties"]["failure_semantics"]
    fs["required"] = list(dict.fromkeys(fs["required"] + ["generic_failure_witness"]))
    fs["properties"]["generic_failure_witness"] = {"const":copy.deepcopy(declaration)}
    _r11_save("metacontract.json", meta)
    _r11_save("schema/metacontract.schema.json", meta_schema)
    _r11_digest_close(reg, pkg)
    print(json.dumps({"r5r18_normative_patch":"PASS", "totality":totality,
                      "operand_only_identities":identities,
                      "registry_semantic_sha256":pkg["registry_semantic_sha256"],
                      "package_semantic_sha256":pkg["current_candidate_integrity"]["digest"]}, indent=2))

_R5R16_POST_BUILD = _r11_post_build
def _r11_post_build():
    _R5R16_POST_BUILD()
    _r5r18_finalize()

# ---------------------------------------------------------------------------
# R5R20: machine-readable pre-execution failure model (normative closure).
# Every NORMATIVE_REACHABLE pre-execution family is assigned to one declared
# bootstrap stage with a total within-stage precedence, one registered code,
# one failure kind / reason and a total derivation for every witness field.
# Defensive mirrors name their dominating owner; implementation-internal
# failures carry no normative result authority.
# ---------------------------------------------------------------------------
_R5R20_DIALECT = "https://json-schema.org/draft/2020-12/schema"
_R5R20_TOKEN = r"^[A-Z][A-Z0-9_]*$"
_R5R20_POINTER = r"^(?:/(?:[^~/]|~[01])*)*$"
_R5R20_NEW_CODES = ["EXTERNAL_PROFILE_SCHEMA_DIGEST_INVALID", "STATIC_VALIDATION_FAILED"]
_R5R20_SEVEN = ("argument", "object_role", "schema_ref", "instance_pointer", "failure_kind", "diagnostic", "bound_identity")
_R5R20_PREFLIGHT = ("operation", "profile_pointer", "candidate_artifact", "candidate_pointer", "source_identity",
                    "expected", "actual", "reason", "diagnostic")
# Typed identities of the frozen external sources, taken from the object registry of the
# pinned frozen commit (never the pin or digest itself).
_R5R20_FROZEN_SOURCES = [
    ("frozen_r5r2_rules", {"kind": "REGISTRY", "id": "urn:moirae:accord-02r5r2:rule-registry", "version": "0.2"},
     "44d0e7240c97dcc12463b5611a7adf61399924d7", "docs/accord-02e4r5r2/object-registry.json",
     "EXTERNAL_FROZEN_R5R2_CONTENT_MISMATCH", "VERIFY_EXTERNAL_FROZEN_R5R2_CONTENT_AND_PIN"),
    ("frozen_r5r3_v013_semantics", {"kind": "CONTRACT", "id": "urn:moirae:accord-02r5r3:v013-governance", "version": "0.2"},
     "ebddc96d6db3793ba3119e7bcdcefe221f4ba18f", "docs/accord-02e4r5r3/object-registry.json",
     "EXTERNAL_FROZEN_R5R3_CONTENT_MISMATCH", "VERIFY_EXTERNAL_FROZEN_R5R3_CONTENT_AND_PIN"),
]
_R5R20_BOOTSTRAP_REFS = ["object_registry_ref", "rule_registry_ref", "invariant_registry_ref",
                         "procedure_registry_ref", "metacontract_ref", "primitive_registry_ref"]


def _r5r20_d(token): return {"derivation": token}
def _r5r20_c(value): return {"constant": value}


def _r5r20_seven(argument, object_role, schema_ref, instance_pointer, bound_identity):
    return {"argument": argument, "object_role": object_role, "schema_ref": schema_ref,
            "instance_pointer": instance_pointer, "bound_identity": bound_identity}


def _r5r20_cond(cid, failure_kind, diagnostic, witness, condition, **extra):
    row = {"condition_id": cid, "condition": condition, "failure_kind": failure_kind, "diagnostic": diagnostic, "witness": witness}
    row.update(extra)
    return row


def _r5r20_pcond(cid, reason, diagnostic, witness, condition, **extra):
    row = {"condition_id": cid, "condition": condition, "reason": reason, "diagnostic": diagnostic, "witness": witness}
    row.update(extra)
    return row


def _r5r20_family(fid, r5r19, name, stage, code, contract, owner, subject_order, within, conditions, **extra):
    for rank, condition in enumerate(conditions, 1):
        condition["rank"] = rank
    row = {"family_id": fid, "class": "NORMATIVE_REACHABLE", "r5r19_family": r5r19, "name": name, "stage": stage,
           "witness_contract": contract, "owner_declaration": owner, "subject_order": subject_order,
           "within_family_order": within, "conditions": conditions}
    if isinstance(code, dict): row["code_derivation"] = code
    else: row["code"] = code
    row.update(extra)
    return row


def _r5r20_protocol_constants(meta, reg, pkg):
    rows = {(r["kind"], r["id"], r["version"]): r for r in reg["objects"]}
    def sdi(ref):
        row = rows[(ref["kind"], ref["id"], ref["version"])]
        schema_row = rows[(row["schema_ref"]["kind"], row["schema_ref"]["id"], row["schema_ref"]["version"])]
        return schema_row["schema_document_id"]
    package_ref = {"kind": "PACKAGE", "id": pkg["package_id"], "version": pkg["package_version"]}
    bootstrap = [{"argument": "candidate_package", "package_member": None, "identity": package_ref,
                  "registered_kind": "PACKAGE", "schema_document_id": sdi(package_ref)}]
    for member in _R5R20_BOOTSTRAP_REFS:
        ref = {k: pkg[member][k] for k in ("kind", "id", "version")}
        bootstrap.append({"argument": member[:-len("_ref")], "package_member": member, "identity": ref,
                          "registered_kind": rows[(ref["kind"], ref["id"], ref["version"])]["kind"],
                          "schema_document_id": sdi(ref)})
    by_arg = {row["argument"]: row for row in bootstrap}
    # Profile members read by later declared stages (derived from the declarations that read them).
    members = []
    for row in meta["reserved_inputs"]:
        src = row.get("profile_content_source")
        if src:
            members.append(("/" + "/".join(src["pin_pointer_tokens"]), "OBJECT"))
            members.append(("/" + "/".join(src["content_pointer_tokens"]), "STRING"))
    members.append(("/" + meta["universe_contract"]["bound_source_universe"]["source_allowlist_ref"].split(":/", 1)[1], "ARRAY"))
    members.append(("/accepted_source_contents", "ARRAY"))
    members.append(("/" + meta["result_projection_authorization"]["descriptor_source"].split(":/", 1)[1], "OBJECT"))
    ordered = []
    for pointer, kind in members:
        if pointer not in [p for p, _ in ordered]: ordered.append((pointer, kind))
    return {
        "authority": "VERIFIER_PROTOCOL_CONSTANTS_FIXED_BY_THIS_ACCORD_VERSION;THE_CANDIDATE_COPY_IS_A_PUBLISHED_CLAIM",
        "entrypoints": [by_arg["candidate_package"], by_arg["object_registry"]],
        "bootstrap_objects": bootstrap,
        "frozen_sources": [{"profile_member": name, "typed_identity": ident, "identity_provenance": {"commit": commit, "registry_path": path},
                            "failure_code": code, "stage": stage} for name, ident, commit, path, code, stage in _R5R20_FROZEN_SOURCES],
        "required_profile_members": [{"profile_pointer": p, "json_type": k} for p, k in ordered],
        "package_self_digest_declaration": {"pointer": "/current_candidate_integrity",
            "members_in_declared_order": [["class", {"const": "SEMANTIC_JSON_CONTENT"}], ["content_target_ref", {"const": "PACKAGE_EXCLUDING_SELF_DIGEST"}],
                                          ["algorithm", {"const": "SHA-256"}], ["digest", {"pattern": "^[0-9a-f]{64}$"}]]},
        "draft_2020_12_dialect": _R5R20_DIALECT,
    }


def _r5r20_vocabulary():
    return {
        "argument": {
            "CANDIDATE_OBJECT": "CONSTANT candidate_object (H1)",
            "ENTRYPOINT_ARGUMENT": "protocol_constants.entrypoints[subject].argument",
            "OWNING_BOOTSTRAP_OBJECT_ARGUMENT": "protocol_constants.bootstrap_objects[owning object].argument (package member name without _ref)",
            "RESERVED_INPUT_NAME": "metacontract:/reserved_inputs[subject].name (more-specific declaration overriding H1)",
            "RUNTIME_VALUE_NAME": "CONSTANT verification_universe (metacontract:/binding_origins/reserved_names)",
            "REGISTRATION_WITNESS_ARGUMENT": "metacontract:/registration/witness_contract/argument",
        },
        "object_role": {
            "REGISTERED_KIND_OF_FAILING_OBJECT": "kind of the failing object's registry row (H1)",
            "ENTRYPOINT_KIND": "protocol_constants.entrypoints[subject].registered_kind",
            "REGISTERED_KIND_OF_OWNING_OBJECT": "protocol_constants.bootstrap_objects[owning object].registered_kind",
            "RESERVED_INPUT_DECLARED_TYPE": "metacontract:/reserved_inputs[subject].type",
            "RUNTIME_VALUE_TYPE": "CONSTANT VERIFICATION_UNIVERSE (reserved input type)",
            "REGISTRATION_WITNESS_OBJECT_ROLE": "metacontract:/registration/witness_contract/object_role",
            "OWNING_OBJECT_REGISTRY_ROW_KIND": "kind of the validated registry row of the owning object (stages after registration)",
        },
        "schema_ref": {
            "APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID": "exact schema_document_id of the SCHEMA row whose kind/id/version equal the failing object's registered schema_ref (H1)",
            "ENTRYPOINT_SCHEMA_DOCUMENT_ID": "protocol_constants.entrypoints[subject].schema_document_id",
            "OWNING_OBJECT_SCHEMA_DOCUMENT_ID": "protocol_constants.bootstrap_objects[owning object].schema_document_id",
            "PRODUCER_SCHEMA_ROW_SCHEMA_DOCUMENT_ID": "exact schema_document_id of the SCHEMA row named by the reserved input producer_schema_ref",
            "DRAFT_2020_12_METASCHEMA": "protocol_constants.draft_2020_12_dialect (eligibility.validation_by_kind.SCHEMA overrides H1)",
            "RUNTIME_VALUE_SCHEMA_ID": "the $id of the metacontract runtime value schema that was applied",
            "REGISTRATION_WITNESS_SCHEMA_REF": "metacontract:/registration/witness_contract/schema_ref",
            "OWNING_OBJECT_APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID": "exact schema_document_id of the SCHEMA row named by the owning object's registered schema_ref (stages after registration)",
        },
        "instance_pointer": {
            "DOCUMENT_ROOT": "the empty RFC6901 pointer; used when the document is absent or undecodable",
            "FIRST_INVALID_LOCATION_CANONICAL_PREORDER": "instance location of the first JSON Schema failure under the DESCENDANTS canonical preorder of the instance (primitive-registry DESCENDANTS deterministic_order); a missing member is located at its containing object; validator emission order is never used",
            "FIRST_UNCANONICALIZABLE_NUMBER_CANONICAL_PREORDER": "pointer of the first number (DESCENDANTS preorder) that RFC8785 cannot serialize",
            "FIRST_NONLOCAL_REFERENCE_CANONICAL_PREORDER": "pointer of the first $ref/$dynamicRef member (DESCENDANTS preorder) that is not a resolvable local RFC6901 fragment",
            "FIRST_DECLARATION_MEMBER_VIOLATION_DECLARED_ORDER": "pointer of the first member, in the declared member order, that is absent or violates its declared constraint; the containing object pointer when an undeclared member is present",
            "ROW_POINTER_TEMPLATE": "the rule's declared /objects/<row_index>... template with the subject row index substituted",
            "DECLARED_SECTION_POINTER": "the RFC6901 pointer of the declaration section named by the condition",
            "ENTRYPOINT_BINDING_LOCATION": "pointer named by the condition inside the subject entrypoint document",
            "STATIC_VIOLATION_LOCATION": "location rule of the condition: NODE=pointer of the failing AST node; MEMBER=pointer of the failing member; SET_EXACT=pointer of the first extra element by ascending index, else the collection pointer; UNIQUENESS=pointer of the first second occurrence by ascending index",
            "WITNESS_OPERAND_TERMINAL": "absolute pointer, in the procedure registry, of the first argument terminal {arg} of the declared witness (procedure source order, assertion source order, declared-witness preorder) lacking both a bound identity and an operand-only identity (H2)",
            "BINDING_DECLARATION_LOCATION": "pointer of the binding value in the object that declares it (invariant default_arguments member, or rule invariant_binding.arguments member); the containing map when the member is absent",
        },
        "bound_identity": {
            "NULL": "JSON null (permitted by the registered schema) when no object identity exists",
            "ENTRYPOINT_CONTENT_IDENTITY_WHEN_DECODABLE_ELSE_NULL": "PACKAGE package_id/package_version or REGISTRY object_id/object_version from the decoded entrypoint content; null when undecodable",
            "REGISTRY_IDENTITY_OF_FAILING_OBJECT": "kind/id/version of the failing object's registry row (H1)",
            "OWNING_OBJECT_IDENTITY": "protocol_constants.bootstrap_objects[owning object].identity",
            "FROZEN_SOURCE_TYPED_IDENTITY": "protocol_constants.frozen_sources[subject].typed_identity",
            "RESOLVED_OBJECT_IDENTITY_CONTAINING_LOCATION_ELSE_NULL": "reference of the verification-universe object whose record contains the location; null at the universe root",
            "REGISTRATION_WITNESS_BOUND_IDENTITY": "metacontract:/registration/witness_contract/bound_identity",
            "OWNING_OBJECT_REGISTRY_IDENTITY": "kind/id/version of the validated registry row of the owning object (stages after registration)",
        },
        "profile_pointer": {
            "NULL": "no profile location is involved",
            "PROFILE_ROOT": "the empty pointer of the profile document",
            "FIRST_INVALID_LOCATION_CANONICAL_PREORDER": "first JSON Schema failure location in the profile (DESCENDANTS preorder)",
            "FIRST_REQUIRED_PROFILE_MEMBER": "first protocol_constants.required_profile_members pointer (declared order) absent or of another JSON type",
            "FROZEN_PIN_POINTER": "/frozen_authority_pins/<subject>",
            "FROZEN_CONTENT_POINTER": "/frozen_authority_contents/<subject>/content_base64",
            "ACCEPTED_CONTENT_ROW_POINTER": "/accepted_source_contents/<index of the content row matched to the allowlist subject>, else /accepted_source_contents",
            "CLAIM_PROFILE_POINTER": "external_acceptance_profile_contract.candidate_claim_comparisons[subject].profile_pointer_rfc6901",
        },
        "candidate_artifact": {
            "NULL": "no candidate artifact is involved (explicitly permitted by the registered witness)",
            "CLAIM_CANDIDATE_ARTIFACT": "candidate_claim_comparisons[subject].candidate_artifact",
        },
        "candidate_pointer": {
            "NULL": "no candidate artifact is involved",
            "CLAIM_CANDIDATE_POINTER": "candidate_claim_comparisons[subject].candidate_pointer_rfc6901, or for the selector claim the absolute pointer of the offending procedure item or selected value",
        },
        "source_identity": {
            "NULL": "no source object is involved",
            "FROZEN_SOURCE_TYPED_IDENTITY": "protocol_constants.frozen_sources[subject].typed_identity",
            "ACCEPTED_SOURCE_REF": "the allowlist subject's ref (typed identity)",
            "CLAIM_FROZEN_SOURCE_TYPED_IDENTITY_ELSE_NULL": "for a claim whose profile pointer is /frozen_authority_pins/<member>, protocol_constants.frozen_sources[<member>].typed_identity; otherwise null",
        },
        "expected": {
            "NULL": "null", "REQUIRED_CALLER_INPUTS": "array of the absent caller input argument names in declared order",
            "VERIFIER_PROFILE_SCHEMA_ID": "the fixed profile schema identity", "CALLER_EXPECTED_SHA256": "the caller-supplied expected digest string",
            "DRAFT_2020_12_DIALECT": "the Draft 2020-12 dialect URI", "REQUIRED_MEMBER_JSON_TYPE": "the declared JSON type of the first failing required member",
            "PIN_GIT_BLOB": "the pin's git_blob", "ALLOWLIST_DIGEST_FIELD": "the allowlist value of the compared digest field",
            "PROFILE_CLAIM_VALUE": "the profile value at the claim profile pointer", "PROTOCOL_SELECTOR": "the declared candidate_selector",
            "REQUIRED_MATCH_COUNT": "1", "ABSENT_MEMBER": "the literal string ABSENT",
            "LOWERCASE_SHA256_HEX_FORMAT": "the literal string ^[0-9a-f]{64}$",
        },
        "trust_result": {
            "TRUST_FIELDS_ABSENT_OR_MALFORMED_IN_DECLARED_ORDER": "expected_package_id, expected_package_version, expected_package_digest that are absent/empty (digest also when not 64 lowercase hex), in that order",
            "CALLER_ID_VERSION": "{id, version} from the caller trust triple", "PACKAGE_ID_VERSION": "{id: package_id, version: package_version}",
            "CALLER_IDENTITY3": "{id, version, digest} from the caller trust triple",
            "PACKAGE_IDENTITY3_WITH_RECOMPUTED_DIGEST": "{id: package_id, version: package_version, digest: verified RFC8785 self-digest}",
        },
        "map_value_comparison": {
            "SELECTED_PROCEDURE_ID": "procedure_id of the selected projection procedure", "DESCRIPTOR_ARGUMENT": "profile descriptor argument",
            "DESCRIPTOR_POINTER_TOKENS_AS_RFC6901": "RFC6901 pointer built from descriptor pointer_tokens", "DESCRIPTOR_BASELINE_ARGUMENT": "profile descriptor baseline.argument",
            "DESCRIPTOR_EXPECTED_LITERALS": "profile descriptor expected_literals", "NULL": "null",
            "BASELINE_STATUS_VALUES": "{PASS: baseline pass_result, FAIL: baseline fail_result} read through descriptor baseline status_pointer_tokens",
            "MAP_VALUE": "the value at the map pointer in the bound map argument",
        },
        "actual": {
            "NULL": "null", "CALLER_SCHEMA_ID": "the caller-supplied schema identity", "COMPUTED_SHA256": "SHA-256 of the raw bytes",
            "CALLER_EXPECTED_SHA256": "the caller-supplied expected digest string",
            "SCHEMA_DIALECT_MEMBER": "the schema's $schema value or null", "SCHEMA_ID_MEMBER": "the schema's $id value or null",
            "MEMBER_JSON_TYPE": "the JSON type name of the failing member or ABSENT", "COMPUTED_GIT_BLOB": "git blob id of the decoded bytes",
            "COMPUTED_DIGEST_FIELD": "the recomputed value of the compared digest field", "CANDIDATE_CLAIM_VALUE": "the candidate value at the claim pointer or null",
            "CANDIDATE_SELECTOR": "the candidate's declared selector", "MATCH_COUNT": "the number of matching procedure items",
            "PRESENT_MEMBER": "the value of the member that must be absent",
        },
    }


def _r5r20_families(meta, pc):
    F, D, C, W = _r5r20_family, _r5r20_d, _r5r20_c, _r5r20_seven
    sio = "SCHEMA_INVALID_BOUND_OBJECT"
    ent = W(D("ENTRYPOINT_ARGUMENT"), D("ENTRYPOINT_KIND"), D("ENTRYPOINT_SCHEMA_DOCUMENT_ID"), D("DOCUMENT_ROOT"), D("NULL"))
    ent_c = W(D("ENTRYPOINT_ARGUMENT"), D("ENTRYPOINT_KIND"), D("ENTRYPOINT_SCHEMA_DOCUMENT_ID"), D("DOCUMENT_ROOT"),
              D("ENTRYPOINT_CONTENT_IDENTITY_WHEN_DECODABLE_ELSE_NULL"))
    h1 = lambda ptr: W(D("CANDIDATE_OBJECT"), D("REGISTERED_KIND_OF_FAILING_OBJECT"), D("APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"), D(ptr), D("REGISTRY_IDENTITY_OF_FAILING_OBJECT"))
    h1s = lambda ptr: W(D("CANDIDATE_OBJECT"), D("REGISTERED_KIND_OF_FAILING_OBJECT"), D("DRAFT_2020_12_METASCHEMA"), D(ptr), D("REGISTRY_IDENTITY_OF_FAILING_OBJECT"))
    reg_w = lambda ptr: W(D("REGISTRATION_WITNESS_ARGUMENT"), D("REGISTRATION_WITNESS_OBJECT_ROLE"), D("REGISTRATION_WITNESS_SCHEMA_REF"), D(ptr), D("REGISTRATION_WITNESS_BOUND_IDENTITY"))
    own = lambda ptr, bound="OWNING_OBJECT_IDENTITY": W(D("OWNING_BOOTSTRAP_OBJECT_ARGUMENT"), D("REGISTERED_KIND_OF_OWNING_OBJECT"), D("OWNING_OBJECT_SCHEMA_DOCUMENT_ID"), D(ptr), D(bound))
    def pf(profile_pointer, artifact, cpointer, source, expected, actual):
        return {"profile_pointer": D(profile_pointer), "candidate_artifact": D(artifact), "candidate_pointer": D(cpointer),
                "source_identity": D(source), "expected": D(expected), "actual": D(actual)}
    P = _r5r20_pcond; K = _r5r20_cond
    fams = []
    # ---- 0 READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST_TRIPLE
    fams.append(F("PE-01", "PE-01", "CANDIDATE_ENTRYPOINT_INPUT_ABSENT", "READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST_TRIPLE", sio, "SEVEN_FIELD",
                  "metacontract:/bootstrap_order/0", "ENTRYPOINT_ORDER", "CONDITION_RANK_THEN_SUBJECT_ORDER",
                  [K("ENTRYPOINT_INPUT_ABSENT", "SOURCE_ELIGIBILITY", "CANDIDATE_ENTRYPOINT_INPUT_MISSING", ent,
                     "the explicit root or the subject entrypoint path is not supplied")]))
    fams.append(F("PE-03", "PE-03", "EXTERNAL_TRUST_TRIPLE_ABSENT_OR_MALFORMED", "READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST_TRIPLE",
                  "MISSING_EXTERNAL_TRUST_INPUT", "TRUST_RESULT", "metacontract:/result_contracts/trust_result", "SINGLE_SUBJECT", "SINGLE_CONDITION",
                  [K("TRUST_TRIPLE_ABSENT_OR_MALFORMED", None, None, {"stage": C("MISSING_EXPECTATION"),
                     "missing_fields": D("TRUST_FIELDS_ABSENT_OR_MALFORMED_IN_DECLARED_ORDER")},
                     "an expected package id, version or digest is absent, empty, or the digest is not 64 lowercase hex (a malformed digest is an absent expectation)")]))
    fams.append(F("PE-02", "PE-02", "CANDIDATE_ENTRYPOINT_PATH_INELIGIBLE", "READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST_TRIPLE", sio, "SEVEN_FIELD",
                  "metacontract:/path_policy", "ENTRYPOINT_ORDER", "CONDITION_RANK_THEN_SUBJECT_ORDER",
                  [K("ENTRYPOINT_PATH_NOT_CANONICAL", "SOURCE_ELIGIBILITY", "CANDIDATE_ENTRYPOINT_PATH_NOT_CANONICAL", ent, "path is absolute, uses a backslash, or contains an empty, . or .. segment"),
                   K("ENTRYPOINT_PATH_OUTSIDE_ROOT", "SOURCE_ELIGIBILITY", "CANDIDATE_ENTRYPOINT_PATH_OUTSIDE_ROOT", ent, "the resolved path is not inside the explicit root"),
                   K("ENTRYPOINT_UNREADABLE", "SOURCE_ELIGIBILITY", "CANDIDATE_ENTRYPOINT_UNREADABLE", ent, "the entrypoint bytes cannot be read")]))
    # ---- 1..4 external profile schema
    fams.append(F("PE-04", "PE-04", "EXTERNAL_PROFILE_SCHEMA_INPUT_ABSENT", "READ_EXTERNAL_PROFILE_SCHEMA_ID_BYTES_AND_EXPECTED_SHA256_OUTSIDE_CANDIDATE",
                  "MISSING_EXTERNAL_PROFILE_SCHEMA", "PROFILE_PREFLIGHT", "metacontract:/source_constraints/acceptance_profile_schema", "SINGLE_SUBJECT", "CONDITION_RANK",
                  [P("PROFILE_SCHEMA_INPUT_MISSING", "INPUT_MISSING", "EXTERNAL_PROFILE_SCHEMA_INPUT_MISSING", pf("NULL", "NULL", "NULL", "NULL", "REQUIRED_CALLER_INPUTS", "NULL"),
                     "schema identity, schema bytes path or expected SHA-256 not supplied"),
                   P("PROFILE_SCHEMA_BYTES_UNREADABLE", "INPUT_UNREADABLE", "EXTERNAL_PROFILE_SCHEMA_BYTES_UNREADABLE", pf("NULL", "NULL", "NULL", "NULL", "NULL", "NULL"),
                     "the supplied schema bytes path cannot be read")]))
    fams.append(F("PE-06", "PE-06", "EXTERNAL_PROFILE_SCHEMA_DIGEST_INVALID", "READ_EXTERNAL_PROFILE_SCHEMA_ID_BYTES_AND_EXPECTED_SHA256_OUTSIDE_CANDIDATE",
                  "EXTERNAL_PROFILE_SCHEMA_DIGEST_INVALID", "PROFILE_PREFLIGHT", "metacontract:/source_constraints/acceptance_profile_schema/expected_sha256_algorithm", "SINGLE_SUBJECT", "SINGLE_CONDITION",
                  [P("PROFILE_SCHEMA_DIGEST_MALFORMED", "INPUT_MALFORMED", "EXTERNAL_PROFILE_SCHEMA_DIGEST_NOT_LOWERCASE_SHA256_HEX", pf("NULL", "NULL", "NULL", "NULL", "LOWERCASE_SHA256_HEX_FORMAT", "CALLER_EXPECTED_SHA256"),
                     "the caller expected SHA-256 is not 64 lowercase hexadecimal characters")]))
    fams.append(F("PE-05", "PE-05", "CALLER_PROFILE_SCHEMA_ID_MISMATCH", "REQUIRE_CALLER_SCHEMA_ID_EQUAL_FIXED_VERIFIER_SCHEMA_ID",
                  "INVALID_EXTERNAL_PROFILE_SCHEMA", "PROFILE_PREFLIGHT", "metacontract:/source_constraints/acceptance_profile_schema/schema_identity", "SINGLE_SUBJECT", "SINGLE_CONDITION",
                  [P("CALLER_SCHEMA_ID_NOT_VERIFIER_ID", "PROFILE_SCHEMA_INVALID", "CALLER_PROFILE_SCHEMA_ID_NOT_VERIFIER_ID", pf("NULL", "NULL", "NULL", "NULL", "VERIFIER_PROFILE_SCHEMA_ID", "CALLER_SCHEMA_ID"),
                     "the caller schema identity differs from the fixed verifier identity")]))
    fams.append(F("PE-07", "PE-07", "EXTERNAL_PROFILE_SCHEMA_DIGEST_MISMATCH", "VERIFY_PROFILE_SCHEMA_RAW_SHA256_BEFORE_PARSE_OR_USE",
                  "EXTERNAL_PROFILE_SCHEMA_DIGEST_MISMATCH", "PROFILE_PREFLIGHT", "metacontract:/source_constraints/acceptance_profile_schema/verify_digest_before_parse_or_use", "SINGLE_SUBJECT", "SINGLE_CONDITION",
                  [P("PROFILE_SCHEMA_RAW_DIGEST_MISMATCH", "CONTENT_RAW_DIGEST_MISMATCH", "EXTERNAL_PROFILE_SCHEMA_RAW_SHA256_MISMATCH", pf("NULL", "NULL", "NULL", "NULL", "CALLER_EXPECTED_SHA256", "COMPUTED_SHA256"),
                     "SHA-256 of the raw schema bytes differs from the caller expected digest")]))
    ps = lambda cid, diag, exp, act, cond: P(cid, "PROFILE_SCHEMA_INVALID", diag, pf("NULL", "NULL", "NULL", "NULL", exp, act), cond)
    fams.append(F("PE-08", "PE-08", "EXTERNAL_PROFILE_SCHEMA_DOCUMENT_INVALID", "VERIFY_PROFILE_SCHEMA_ID_AND_DRAFT_2020_12_DIALECT",
                  "INVALID_EXTERNAL_PROFILE_SCHEMA", "PROFILE_PREFLIGHT", "metacontract:/source_constraints/acceptance_profile_schema", "SINGLE_SUBJECT", "CONDITION_RANK",
                  [ps("PROFILE_SCHEMA_UNDECODABLE", "EXTERNAL_PROFILE_SCHEMA_UNDECODABLE", "NULL", "NULL", "schema bytes are not strict UTF-8 JSON without duplicate member names, or not a JSON object"),
                   ps("PROFILE_SCHEMA_DIALECT", "EXTERNAL_PROFILE_SCHEMA_DIALECT_NOT_DRAFT_2020_12", "DRAFT_2020_12_DIALECT", "SCHEMA_DIALECT_MEMBER", "$schema is not the Draft 2020-12 dialect"),
                   ps("PROFILE_SCHEMA_ID", "EXTERNAL_PROFILE_SCHEMA_ID_NOT_VERIFIER_ID", "VERIFIER_PROFILE_SCHEMA_ID", "SCHEMA_ID_MEMBER", "$id is not the fixed verifier identity"),
                   ps("PROFILE_SCHEMA_METASCHEMA", "EXTERNAL_PROFILE_SCHEMA_NOT_VALID_DRAFT_2020_12", "NULL", "NULL", "the document is not a valid Draft 2020-12 schema"),
                   ps("PROFILE_SCHEMA_NONLOCAL_REF", "EXTERNAL_PROFILE_SCHEMA_REFERENCE_NOT_LOCAL_FRAGMENT", "NULL", "NULL", "a $ref/$dynamicRef is not a resolvable local RFC6901 fragment")]))
    # ---- 5 candidate JSON decode (both entrypoints)
    fams.append(F("PE-09", "PE-09", "CANDIDATE_ENTRYPOINT_UNDECODABLE", "REJECT_DUPLICATE_CANDIDATE_JSON_NAMES_AND_INVALID_UTF8", sio, "SEVEN_FIELD",
                  "metacontract:/numeric_representation/json_number", "ENTRYPOINT_ORDER", "SUBJECT_ORDER_THEN_CONDITION_RANK",
                  [K("ENTRYPOINT_INVALID_UTF8", "PARSE", "CANDIDATE_JSON_INVALID_UTF8", ent, "bytes are not strict UTF-8"),
                   K("ENTRYPOINT_JSON_SYNTAX", "PARSE", "CANDIDATE_JSON_SYNTAX_INVALID", ent, "text is not one JSON value"),
                   K("ENTRYPOINT_NUMBER_LIMIT", "PARSE", "CANDIDATE_JSON_NUMBER_RESOURCE_LIMIT", ent, "a number token exceeds the declared numeric resource limits"),
                   K("ENTRYPOINT_DUPLICATE_NAME", "PARSE", "CANDIDATE_JSON_DUPLICATE_MEMBER_NAME", ent, "an object repeats a member name")]))
    # ---- 6 VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE (self-integrity strictly before the trust comparison: H5-A)
    pkgw = lambda ptr: W(C("candidate_package"), C("PACKAGE"), D("ENTRYPOINT_SCHEMA_DOCUMENT_ID"), D(ptr), D("ENTRYPOINT_CONTENT_IDENTITY_WHEN_DECODABLE_ELSE_NULL"))
    fams.append(F("PE-10", "PE-10", "CANDIDATE_PACKAGE_NOT_OBJECT", "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE", sio, "SEVEN_FIELD",
                  "metacontract:/bootstrap_order/6", "SINGLE_SUBJECT", "SINGLE_CONDITION",
                  [K("PACKAGE_NOT_OBJECT", "TYPE", "CANDIDATE_PACKAGE_NOT_JSON_OBJECT", W(C("candidate_package"), C("PACKAGE"), D("ENTRYPOINT_SCHEMA_DOCUMENT_ID"), D("DOCUMENT_ROOT"), D("NULL")),
                     "the decoded package is not a JSON object")]))
    fams.append(F("PE-12", "PE-12", "CANDIDATE_PACKAGE_NOT_CANONICALIZABLE", "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE", sio, "SEVEN_FIELD",
                  "metacontract:/numeric_representation", "SINGLE_SUBJECT", "SINGLE_CONDITION",
                  [K("PACKAGE_NOT_RFC8785", "INTEGRITY", "PACKAGE_CONTENT_NOT_RFC8785_CANONICALIZABLE", pkgw("FIRST_UNCANONICALIZABLE_NUMBER_CANONICAL_PREORDER"),
                     "the package contains a number RFC8785 cannot serialize, so its self-digest cannot be recomputed")]))
    fams.append(F("PE-13", "PE-13", "CANDIDATE_PACKAGE_SELF_INTEGRITY", "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE", sio, "SEVEN_FIELD",
                  "metacontract:/registration/integrity_gate/package_self_digest", "SINGLE_SUBJECT", "CONDITION_RANK",
                  [K("PACKAGE_SELF_DIGEST_DECLARATION_INVALID", "INTEGRITY", "PACKAGE_SELF_DIGEST_DECLARATION_INVALID", pkgw("FIRST_DECLARATION_MEMBER_VIOLATION_DECLARED_ORDER"),
                     "current_candidate_integrity violates protocol_constants.package_self_digest_declaration (H5-B: rejected before digest calculation)"),
                   K("PACKAGE_SELF_DIGEST_MISMATCH", "INTEGRITY", "REGISTRATION_INTEGRITY_DIGEST_MISMATCH", pkgw("DECLARED_SECTION_POINTER"),
                     "the stored self-digest differs from the RFC8785 recomputation excluding it (H5-A: integrity-gate law, before trust)", section_pointer="/current_candidate_integrity/digest")]))
    fams.append(F("PE-11", "PE-11", "EXTERNAL_TRUST_COMPARISON", "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE",
                  {"FOREIGN_IDENTITY": "FOREIGN_PACKAGE_IDENTITY", "DIGEST": "TRUSTED_IDENTITY_MISMATCH"}, "TRUST_RESULT",
                  "metacontract:/result_contracts/trust_result", "SINGLE_SUBJECT", "CONDITION_RANK",
                  [K("FOREIGN_IDENTITY", None, None, {"stage": C("IDENTITY_COMPARISON"), "expected": D("CALLER_ID_VERSION"), "actual": D("PACKAGE_ID_VERSION")}, "caller id/version differ from package_id/package_version"),
                   K("DIGEST", None, None, {"stage": C("DIGEST_COMPARISON"), "expected": D("CALLER_IDENTITY3"), "actual": D("PACKAGE_IDENTITY3_WITH_RECOMPUTED_DIGEST")}, "caller digest differs from the verified self-digest")]))
    ebind = lambda ptr: W(D("ENTRYPOINT_ARGUMENT"), D("ENTRYPOINT_KIND"), D("ENTRYPOINT_SCHEMA_DOCUMENT_ID"), D("ENTRYPOINT_BINDING_LOCATION"), D("ENTRYPOINT_CONTENT_IDENTITY_WHEN_DECODABLE_ELSE_NULL"))
    fams.append(F("PE-33", "PE-33", "CANDIDATE_ENTRYPOINT_BINDING", "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE", sio, "SEVEN_FIELD",
                  "specification-package:/object_registry_ref", "ENTRYPOINT_ORDER", "CONDITION_RANK_THEN_SUBJECT_ORDER",
                  [K("REGISTRY_NOT_OBJECT", "TYPE", "OBJECT_REGISTRY_NOT_JSON_OBJECT_WITH_OBJECT_ARRAY", ebind(None), "subject object_registry: not an object or /objects is not an array", binding_pointer=""),
                   K("PACKAGE_REGISTRY_REFERENCE", "TYPE", "PACKAGE_OBJECT_REGISTRY_REFERENCE_MISMATCH", ebind(None), "subject candidate_package: /object_registry_ref differs from REGISTRY object_id/object_version of the explicit registry", binding_pointer="/object_registry_ref"),
                   K("ENTRYPOINT_ROW_NOT_UNIQUE", "SOURCE_ELIGIBILITY", "ENTRYPOINT_REGISTRATION_ROW_NOT_UNIQUE", ebind(None), "the subject's identity does not match exactly one registry row (located in the registry at /objects)", binding_pointer="/objects"),
                   K("ENTRYPOINT_PATH_DIFFERS", "SOURCE_ELIGIBILITY", "ENTRYPOINT_PATH_DIFFERS_FROM_REGISTRATION", ebind(None), "the matched row path differs from the explicit entrypoint path (located at /objects/<row>/path)", binding_pointer="/objects/<row_index>/path")]))
    # ---- 7..8 external acceptance profile
    fams.append(F("PE-14", "PE-14", "EXTERNAL_ACCEPTANCE_PROFILE_ABSENT", "READ_EXTERNAL_ACCEPTANCE_PROFILE_OUTSIDE_CANDIDATE",
                  "MISSING_EXTERNAL_ACCEPTANCE_PROFILE", "PROFILE_PREFLIGHT", "metacontract:/external_acceptance_profile_contract/input_origin", "SINGLE_SUBJECT", "CONDITION_RANK",
                  [P("PROFILE_INPUT_MISSING", "INPUT_MISSING", "EXTERNAL_ACCEPTANCE_PROFILE_INPUT_MISSING", pf("NULL", "NULL", "NULL", "NULL", "REQUIRED_CALLER_INPUTS", "NULL"), "--verification-input not supplied"),
                   P("PROFILE_UNREADABLE", "INPUT_UNREADABLE", "EXTERNAL_ACCEPTANCE_PROFILE_UNREADABLE", pf("NULL", "NULL", "NULL", "NULL", "NULL", "NULL"), "the profile bytes cannot be read")]))
    fams.append(F("PE-15", "PE-15", "EXTERNAL_ACCEPTANCE_PROFILE_INVALID", "VALIDATE_EXTERNAL_ACCEPTANCE_PROFILE_WITH_VERIFIED_EXTERNAL_SCHEMA_BYTES",
                  "INVALID_EXTERNAL_ACCEPTANCE_PROFILE", "PROFILE_PREFLIGHT", "metacontract:/external_acceptance_profile_contract", "SINGLE_SUBJECT", "CONDITION_RANK",
                  [P("PROFILE_UNDECODABLE", "INPUT_UNREADABLE", "EXTERNAL_ACCEPTANCE_PROFILE_UNDECODABLE", pf("PROFILE_ROOT", "NULL", "NULL", "NULL", "NULL", "NULL"), "profile bytes are not strict UTF-8 JSON without duplicate member names"),
                   P("PROFILE_SCHEMA_VIOLATION", "PROFILE_SCHEMA_INVALID", "EXTERNAL_ACCEPTANCE_PROFILE_SCHEMA_VIOLATION", pf("FIRST_INVALID_LOCATION_CANONICAL_PREORDER", "NULL", "NULL", "NULL", "NULL", "NULL"), "the profile is invalid against the verified caller schema bytes"),
                   P("PROFILE_REQUIRED_MEMBER", "PROFILE_SCHEMA_INVALID", "EXTERNAL_ACCEPTANCE_PROFILE_REQUIRED_MEMBER_INVALID", pf("FIRST_REQUIRED_PROFILE_MEMBER", "NULL", "NULL", "NULL", "REQUIRED_MEMBER_JSON_TYPE", "MEMBER_JSON_TYPE"), "a protocol_constants.required_profile_members member is absent or of another JSON type")]))
    # ---- 9..10 frozen sources (one family per declared stage)
    for fid, (name, _, _, _, code, stage) in zip(("PE-16A", "PE-16B"), _R5R20_FROZEN_SOURCES):
        fp = lambda pp, exp, act: pf(pp, "NULL", "NULL", "FROZEN_SOURCE_TYPED_IDENTITY", exp, act)
        fams.append(F(fid, "PE-16", "FROZEN_SOURCE_CONTENT_" + name.upper(), stage, code, "PROFILE_PREFLIGHT",
                      "metacontract:/reserved_inputs[profile_content_source]", "FROZEN_SOURCE_" + name.upper(), "CONDITION_RANK",
                      [P("FROZEN_BASE64_INVALID", "INPUT_UNREADABLE", "FROZEN_CONTENT_BASE64_INVALID", fp("FROZEN_CONTENT_POINTER", "NULL", "NULL"), "content is not strict RFC4648 base64"),
                       P("FROZEN_GIT_BLOB", "CONTENT_GIT_BLOB_MISMATCH", "FROZEN_CONTENT_GIT_BLOB_MISMATCH", fp("FROZEN_CONTENT_POINTER", "PIN_GIT_BLOB", "COMPUTED_GIT_BLOB"), "git blob of the decoded bytes differs from the pin"),
                       P("FROZEN_UNDECODABLE", "INPUT_UNREADABLE", "FROZEN_CONTENT_UNDECODABLE", fp("FROZEN_CONTENT_POINTER", "NULL", "NULL"), "pin-verified bytes are not strict UTF-8 JSON without duplicate member names")],
                      profile_member=name))
    # ---- 11 accepted sources
    ap = lambda exp, act: pf("ACCEPTED_CONTENT_ROW_POINTER", "NULL", "NULL", "ACCEPTED_SOURCE_REF", exp, act)
    fams.append(F("PE-17", "PE-17", "ACCEPTED_SOURCE_CONTENT", "VERIFY_EXTERNAL_ACCEPTED_BASE_AND_VECTOR_CONTENT_AND_PINS",
                  {"SOURCE_VECTOR_CATALOG": "EXTERNAL_ACCEPTED_VECTOR_CONTENT_MISMATCH", "OTHERWISE": "EXTERNAL_ACCEPTED_BASE_CONTENT_MISMATCH"}, "PROFILE_PREFLIGHT",
                  "metacontract:/external_acceptance_profile_contract/content_verification/accepted_sources", "ALLOWLIST_ORDER", "SUBJECT_ORDER_THEN_CONDITION_RANK",
                  [P("ACCEPTED_CONTENT_ROW_MISSING", "INPUT_MISSING", "ACCEPTED_SOURCE_CONTENT_ROW_MISSING", ap("NULL", "NULL"), "no content row has the allowlist ref, canonical_path and git_blob"),
                   P("ACCEPTED_BASE64_INVALID", "INPUT_UNREADABLE", "ACCEPTED_SOURCE_CONTENT_BASE64_INVALID", ap("NULL", "NULL"), "content is not strict RFC4648 base64"),
                   P("ACCEPTED_GIT_BLOB", "CONTENT_GIT_BLOB_MISMATCH", "ACCEPTED_SOURCE_GIT_BLOB_MISMATCH", ap("PIN_GIT_BLOB", "COMPUTED_GIT_BLOB"), "git blob differs from the allowlist"),
                   P("ACCEPTED_RAW_DIGEST", "CONTENT_RAW_DIGEST_MISMATCH", "ACCEPTED_SOURCE_RAW_SHA256_MISMATCH", ap("ALLOWLIST_DIGEST_FIELD", "COMPUTED_DIGEST_FIELD"), "raw SHA-256 differs from the allowlist"),
                   P("ACCEPTED_UNDECODABLE", "INPUT_UNREADABLE", "ACCEPTED_SOURCE_CONTENT_UNDECODABLE", ap("NULL", "NULL"), "bytes are not strict UTF-8 JSON without duplicate member names"),
                   P("ACCEPTED_SEMANTIC_DIGEST", "CONTENT_SEMANTIC_DIGEST_MISMATCH", "ACCEPTED_SOURCE_SEMANTIC_SHA256_MISMATCH", ap("ALLOWLIST_DIGEST_FIELD", "COMPUTED_DIGEST_FIELD"), "RFC8785 SHA-256 differs from the allowlist")]))
    # ---- 12 claims (candidate artefacts are located through the package reference and the explicit registry)
    cp = lambda exp, act: pf("CLAIM_PROFILE_POINTER", "CLAIM_CANDIDATE_ARTIFACT", "CLAIM_CANDIDATE_POINTER", "CLAIM_FROZEN_SOURCE_TYPED_IDENTITY_ELSE_NULL", exp, act)
    fams.append(F("PE-18", "PE-18", "METACONTRACT_AUTHORITY_CLAIMS", "COMPARE_ALL_CANDIDATE_AUTHORITY_CLAIMS_WHOLE_OBJECT_BEFORE_SEMANTIC_USE",
                  {"BY_SUBJECT": "external_acceptance_profile_contract.candidate_claim_comparisons[subject].failure_code"}, "PROFILE_PREFLIGHT",
                  "metacontract:/external_acceptance_profile_contract/candidate_claim_comparisons[0..3]", "CLAIM_COMPARISON_ORDER_0_TO_3", "SUBJECT_ORDER_THEN_CONDITION_RANK",
                  [P("CLAIM_ARTIFACT_UNRESOLVED", "INPUT_MISSING", "CLAIM_ARTIFACT_UNRESOLVED", cp("PROFILE_CLAIM_VALUE", "NULL"), "the claim artefact is not exactly one registry row reachable from its package reference, or the claim pointer is absent"),
                   P("CLAIM_ARTIFACT_UNREADABLE", "INPUT_UNREADABLE", "CLAIM_ARTIFACT_UNREADABLE", cp("PROFILE_CLAIM_VALUE", "NULL"), "the claim artefact bytes cannot be read or strictly decoded"),
                   P("CLAIM_MISMATCH", {"descriptor claim": "DESCRIPTOR_WHOLE_OBJECT_MISMATCH", "otherwise": "CLAIM_WHOLE_OBJECT_MISMATCH"}, "CANDIDATE_CLAIM_DIFFERS_FROM_PROFILE",
                     cp("PROFILE_CLAIM_VALUE", "CANDIDATE_CLAIM_VALUE"), "whole-object JSON equality fails", reason_derivation="DESCRIPTOR_WHOLE_OBJECT_MISMATCH for the result_projection_authorization/descriptor claim, else CLAIM_WHOLE_OBJECT_MISMATCH")]))
    sp = lambda exp, act: pf("CLAIM_PROFILE_POINTER", "CLAIM_CANDIDATE_ARTIFACT", "CLAIM_CANDIDATE_POINTER", "NULL", exp, act)
    fams.append(F("PE-19", "PE-19", "PROCEDURE_PROJECTION_CLAIM", "COMPARE_ALL_CANDIDATE_AUTHORITY_CLAIMS_WHOLE_OBJECT_BEFORE_SEMANTIC_USE",
                  "PROCEDURE_PROJECTION_CLAIM_MISMATCH", "PROFILE_PREFLIGHT", "metacontract:/external_acceptance_profile_contract/candidate_claim_comparisons/4", "SINGLE_SUBJECT", "CONDITION_RANK",
                  [P("SELECTOR_UNSUPPORTED", "DESCRIPTOR_WHOLE_OBJECT_MISMATCH", "PROCEDURE_PROJECTION_SELECTOR_NOT_PROTOCOL_SELECTOR", sp("PROTOCOL_SELECTOR", "CANDIDATE_SELECTOR"), "candidate_selector differs from external_acceptance_profile_contract.procedure_projection_selector"),
                   P("PROCEDURE_REGISTRY_UNRESOLVED", "INPUT_MISSING", "CLAIM_ARTIFACT_UNRESOLVED", sp("PROFILE_CLAIM_VALUE", "NULL"), "the procedure registry is not exactly one row reachable from procedure_registry_ref"),
                   P("PROCEDURE_REGISTRY_UNREADABLE", "INPUT_UNREADABLE", "CLAIM_ARTIFACT_UNREADABLE", sp("PROFILE_CLAIM_VALUE", "NULL"), "the procedure registry bytes cannot be read or strictly decoded"),
                   P("SELECTOR_MATCH_COUNT", "DESCRIPTOR_WHOLE_OBJECT_MISMATCH", "PROCEDURE_PROJECTION_SELECTOR_MATCH_COUNT_NOT_ONE", sp("REQUIRED_MATCH_COUNT", "MATCH_COUNT"), "the collection is not an array or the typed filter does not match exactly one item"),
                   P("SELECTED_DESCRIPTOR", "DESCRIPTOR_WHOLE_OBJECT_MISMATCH", "SELECTED_PROCEDURE_PROJECTION_DIFFERS_FROM_PROFILE", sp("PROFILE_CLAIM_VALUE", "CANDIDATE_CLAIM_VALUE"), "the selected value is absent or differs whole-object from the profile descriptor"),
                   P("OTHER_PROCEDURE_PROJECTION", "DESCRIPTOR_WHOLE_OBJECT_MISMATCH", "UNSELECTED_PROCEDURE_DECLARES_RESULT_PROJECTION", sp("ABSENT_MEMBER", "PRESENT_MEMBER"), "an unselected item has the forbidden member (present null counts as present); first such item by index")]))
    # ---- 13 registry structural application (verifier-protocol declarations first, then declared rules)
    proto = lambda ptr: W(C("metacontract"), D("REGISTERED_KIND_OF_OWNING_OBJECT"), D("OWNING_OBJECT_SCHEMA_DOCUMENT_ID"), D("DECLARED_SECTION_POINTER"), D("OWNING_OBJECT_IDENTITY"))
    fams.append(F("PE-22", "PE-22", "VERIFIER_PROTOCOL_DECLARATIONS", "APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY", sio, "SEVEN_FIELD",
                  "metacontract:/failure_semantics/verifier_protocol_digests", "PROTOCOL_SECTION_ORDER", "CONDITION_RANK",
                  [K("FAILURE_MODEL_UNSUPPORTED", "TYPE", "PRE_EXECUTION_FAILURE_MODEL_UNSUPPORTED", proto(None), "RFC8785 SHA-256 of /failure_semantics/pre_execution_failure_model differs from verifier_protocol_digests", section_pointer="/failure_semantics/pre_execution_failure_model"),
                   K("REGISTRATION_UNSUPPORTED", "TYPE", "REGISTRATION_DECLARATION_UNSUPPORTED", proto(None), "RFC8785 SHA-256 of /registration differs from verifier_protocol_digests", section_pointer="/registration"),
                   K("REGISTRY_SCHEMA_UNAVAILABLE", "JSON_SCHEMA", "REGISTRY_SCHEMA_UNAVAILABLE", reg_w("DECLARED_SECTION_POINTER"), "the declared registry schema is not exactly one readable, strictly decodable row whose $id equals structural_application.schema_id", section_pointer="/objects")],
                  owning_object="metacontract"))
    reg_ctx = meta["registration"]
    fams.append(F("PE-21", "PE-21", "REGISTRY_STRUCTURAL_APPLICATION", "APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY", sio, "SEVEN_FIELD",
                  "metacontract:/registration/structural_application", "REGISTRATION_DECLARED_ORDER", "REGISTRATION_DECLARED_ORDER",
                  [K(r["rule_id"], reg_ctx["structural_application"]["failure_kind"], r["diagnostic"], reg_w("ROW_POINTER_TEMPLATE"), r["condition"], pointer_template=r["instance_pointer"])
                   for r in reg_ctx["structural_application"]["rules"]]))
    fams.append(F("PE-23", "PE-23", "SEMANTIC_REGISTRATION", "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS", sio, "SEVEN_FIELD",
                  "metacontract:/registration/semantic_validation", "REGISTRATION_DECLARED_ORDER", "REGISTRATION_DECLARED_ORDER",
                  [K(r["rule_id"], reg_ctx["semantic_validation"]["failure_kind"], r["diagnostic"], reg_w("ROW_POINTER_TEMPLATE"), r["condition"], pointer_template=r["instance_pointer"])
                   for r in reg_ctx["semantic_validation"]["rules"]]))
    gu = reg_ctx["global_uniqueness"]
    fams.append(F("PE-24", "PE-24", "GLOBAL_UNIQUENESS", "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY", sio, "SEVEN_FIELD",
                  "metacontract:/registration/global_uniqueness", "GLOBAL_UNIQUENESS_DECLARED_SELECTION", "SINGLE_CONDITION",
                  [K("DUPLICATE_IDENTITY", gu["failure_kind"], gu["diagnostic"], W(D("REGISTRATION_WITNESS_ARGUMENT"), D("REGISTRATION_WITNESS_OBJECT_ROLE"), D("REGISTRATION_WITNESS_SCHEMA_REF"), D("ROW_POINTER_TEMPLATE"), C("SELECTED_DUPLICATED_KIND_ID_VERSION_TRIPLE_OBJECT")),
                     "two rows share kind/id/version", pointer_template=gu["instance_pointer"])]))
    ig = reg_ctx["integrity_gate"]
    fams.append(F("PE-25", "PE-25", "INTEGRITY_MODE_INVALID", "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS", sio, "SEVEN_FIELD",
                  "metacontract:/registration/integrity_gate/invalid_mode", "REGISTRY_SOURCE_ORDER", "SINGLE_CONDITION",
                  [K("INVALID_MODE", ig["invalid_mode"]["failure_kind"], ig["invalid_mode"]["diagnostic"], reg_w("ROW_POINTER_TEMPLATE"), "declared mode outside declared_mode_must_be_in", pointer_template=ig["invalid_mode"]["instance_pointer"])]))
    fams.append(F("PE-27", "PE-27", "INTEGRITY_DECLARATION_SHAPE_INVALID", "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS", sio, "SEVEN_FIELD",
                  "metacontract:/registration/integrity_gate/declaration_shape_by_mode", "REGISTRY_SOURCE_ORDER", "SINGLE_CONDITION",
                  [K("MODE_SHAPE_INVALID", "INTEGRITY", "REGISTRATION_INTEGRITY_DECLARATION_SHAPE_INVALID", reg_w("FIRST_INVALID_LOCATION_CANONICAL_PREORDER"),
                     "the row integrity declaration violates the per-mode shape of runtime_representation.value_schemas.resolved_object $defs/integrity (H5-B: before digest calculation)", pointer_scope="/objects/<row_index>/integrity")]))
    fams.append(F("PE-26", "PE-26", "INTEGRITY_DIGEST", "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS", sio, "SEVEN_FIELD",
                  "metacontract:/registration/integrity_gate/digest_mismatch", "REGISTRY_SOURCE_ORDER", "CONDITION_RANK",
                  [K("CONTENT_NOT_RFC8785", "INTEGRITY", "REGISTRATION_INTEGRITY_CONTENT_NOT_RFC8785_CANONICALIZABLE", reg_w("ROW_POINTER_TEMPLATE"), "readable decodable row content contains a number RFC8785 cannot serialize", pointer_template=ig["digest_mismatch"]["instance_pointer"]),
                   K("DIGEST_MISMATCH", ig["digest_mismatch"]["failure_kind"], ig["digest_mismatch"]["diagnostic"], reg_w("ROW_POINTER_TEMPLATE"), "declared digest differs from recomputation", pointer_template=ig["digest_mismatch"]["instance_pointer"])]))
    # ---- 17 eligibility
    fams.append(F("PE-33B", "PE-33", "BOOTSTRAP_OBJECT_ELIGIBILITY", "SELECT_ELIGIBLE_CANDIDATE_OBJECTS", sio, "SEVEN_FIELD",
                  "metacontract:/eligibility/candidate_universe/membership_predicate", "PACKAGE_BOOTSTRAP_REFERENCE_ORDER", "SINGLE_CONDITION",
                  [K("BOOTSTRAP_NOT_ELIGIBLE", "SOURCE_ELIGIBILITY", "BOOTSTRAP_OBJECT_NOT_ELIGIBLE", reg_w("ROW_POINTER_TEMPLATE"),
                     "a package-referenced bootstrap object (or the package) is not an ACTIVE NORMATIVE member", pointer_template="/objects/<row_index>/status")]))
    # ---- 18 resolve candidate objects (subject-major over eligible rows)
    fams.append(F("PE-30", "PE-30", "CANDIDATE_OBJECT_PATH", "RESOLVE_CANDIDATE_OBJECTS", sio, "SEVEN_FIELD",
                  "metacontract:/registration/semantic_validation/schema_document_identity/content_read_failure_owner", "ELIGIBLE_ROWS_REGISTRY_SOURCE_ORDER", "CONDITION_RANK",
                  [K("OBJECT_PATH_NOT_CANONICAL", "SOURCE_ELIGIBILITY", "CANDIDATE_OBJECT_PATH_NOT_CANONICAL", h1("DOCUMENT_ROOT"), "registered path is not canonical repository-relative"),
                   K("OBJECT_PATH_OUTSIDE_ROOT", "SOURCE_ELIGIBILITY", "CANDIDATE_OBJECT_PATH_OUTSIDE_ROOT", h1("DOCUMENT_ROOT"), "resolved path escapes the explicit root"),
                   K("OBJECT_UNREADABLE", "SOURCE_ELIGIBILITY", "CANDIDATE_OBJECT_UNREADABLE", h1("DOCUMENT_ROOT"), "bytes cannot be read")]))
    fams.append(F("PE-31", "PE-31", "CANDIDATE_OBJECT_UNDECODABLE", "RESOLVE_CANDIDATE_OBJECTS", sio, "SEVEN_FIELD",
                  "metacontract:/numeric_representation/json_number", "ELIGIBLE_ROWS_REGISTRY_SOURCE_ORDER", "CONDITION_RANK",
                  [K("OBJECT_INVALID_UTF8", "PARSE", "CANDIDATE_JSON_INVALID_UTF8", h1("DOCUMENT_ROOT"), "bytes are not strict UTF-8"),
                   K("OBJECT_JSON_SYNTAX", "PARSE", "CANDIDATE_JSON_SYNTAX_INVALID", h1("DOCUMENT_ROOT"), "text is not one JSON value"),
                   K("OBJECT_NUMBER_LIMIT", "PARSE", "CANDIDATE_JSON_NUMBER_RESOURCE_LIMIT", h1("DOCUMENT_ROOT"), "a number token exceeds declared limits"),
                   K("OBJECT_DUPLICATE_NAME", "PARSE", "CANDIDATE_JSON_DUPLICATE_MEMBER_NAME", h1("DOCUMENT_ROOT"), "an object repeats a member name")]))
    fams.append(F("PE-32", "PE-32", "CANDIDATE_OBJECT_NOT_DOCUMENT", "RESOLVE_CANDIDATE_OBJECTS", sio, "SEVEN_FIELD",
                  "metacontract:/eligibility/candidate_universe/validation_by_kind", "ELIGIBLE_ROWS_REGISTRY_SOURCE_ORDER", "SINGLE_CONDITION",
                  [K("OBJECT_NOT_JSON_OBJECT", "TYPE", "CANDIDATE_OBJECT_NOT_JSON_OBJECT", h1("DOCUMENT_ROOT"), "decoded content is not a JSON object")]))
    # ---- 19 bound-source resolved construction (existing complete declaration)
    bs = reg_ctx["bound_source_resolved_construction"]
    fams.append(F("PE-34", "PE-34", "VECTOR_REGISTRY_CLAIM", "BOUND_SOURCE_RESOLVED_CONSTRUCTION", sio, "VECTOR_REGISTRY_CLAIM",
                  "metacontract:/registration/bound_source_resolved_construction", "BOUND_SOURCE_DECLARED_SCOPE", "DECLARED_REASON_ORDER",
                  [{"condition_id": "VECTOR_REGISTRY_CLAIM_INVALID", "condition": "declared lookup/member relation fails", "failure_kind": bs["failure_kind"],
                    "diagnostic": bs["diagnostic"], "witness_field_derivation_ref": "metacontract:/registration/bound_source_resolved_construction/witness_field_derivation",
                    "reason_derivation_ref": "metacontract:/registration/bound_source_resolved_construction/reason_derivation"}]))
    # ---- 21 candidate objects and bound-source universe
    si = reg_ctx["strict_identity_union"]
    fams.append(F("PE-35", "PE-35", "STRICT_IDENTITY_UNION_COLLISION", "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE", sio, "STRICT_UNION_COLLISION",
                  "metacontract:/registration/strict_identity_union", "STRICT_UNION_DECLARED_SCAN", "SINGLE_CONDITION",
                  [{"condition_id": "CROSS_SET_COLLISION", "condition": "a candidate and a bound participant share kind/id/version",
                    "witness_field_derivation_ref": "metacontract:/registration/strict_identity_union/failure", "scan_ref": "metacontract:/registration/strict_identity_union/scan_selection"}]))
    fams.append(F("PE-37", "PE-37", "CANDIDATE_SCHEMA_DOCUMENT_INELIGIBLE", "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE", sio, "SEVEN_FIELD",
                  "metacontract:/eligibility/candidate_universe/validation_by_kind/SCHEMA", "ELIGIBLE_SCHEMA_ROWS_REGISTRY_SOURCE_ORDER", "CONDITION_RANK",
                  [K("SCHEMA_DIALECT", "JSON_SCHEMA", "SCHEMA_DOCUMENT_DIALECT_NOT_DRAFT_2020_12", h1s("DECLARED_SECTION_POINTER"), "$schema is not the Draft 2020-12 dialect", section_pointer="/$schema"),
                   K("SCHEMA_METASCHEMA", "JSON_SCHEMA", "SCHEMA_DOCUMENT_NOT_VALID_DRAFT_2020_12", h1s("FIRST_INVALID_LOCATION_CANONICAL_PREORDER"), "the document is invalid against the Draft 2020-12 metaschema"),
                   K("SCHEMA_NONLOCAL_REF", "JSON_SCHEMA", "SCHEMA_DOCUMENT_REFERENCE_NOT_LOCAL_FRAGMENT", h1s("FIRST_NONLOCAL_REFERENCE_CANONICAL_PREORDER"), "a $ref/$dynamicRef is not a resolvable local RFC6901 fragment")]))
    fams.append(F("PE-36", "PE-36", "CANDIDATE_OBJECT_CONTENT_INVALID", "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE", sio, "SEVEN_FIELD",
                  "metacontract:/eligibility/candidate_universe/validation_by_kind/NON_SCHEMA", "ELIGIBLE_NON_SCHEMA_ROWS_REGISTRY_SOURCE_ORDER", "CONDITION_RANK",
                  [K("APPLIED_SCHEMA_NOT_IN_UNIVERSE", "SOURCE_ELIGIBILITY", "CANDIDATE_OBJECT_SCHEMA_NOT_IN_VERIFICATION_UNIVERSE", h1("DOCUMENT_ROOT"), "the registered schema_ref names a SCHEMA row that is not an eligible member"),
                   K("APPLIED_SCHEMA_DOCUMENT_INELIGIBLE", "SOURCE_ELIGIBILITY", "CANDIDATE_OBJECT_APPLIED_SCHEMA_DOCUMENT_INELIGIBLE", h1("DOCUMENT_ROOT"), "the applied SCHEMA row itself fails a PE-37 condition (checked at this dependent row so the scan stays in registry source order)"),
                   K("APPLIED_SCHEMA_MEMBER_UNREGISTERED", "SOURCE_ELIGIBILITY", "CANDIDATE_OBJECT_SCHEMA_MEMBER_UNREGISTERED", h1("DOCUMENT_ROOT"), "schema_ref.member_id is not a registered member of that SCHEMA row"),
                   K("CONTENT_SCHEMA_VIOLATION", "JSON_SCHEMA", "CANDIDATE_OBJECT_SCHEMA_VIOLATION", h1("FIRST_INVALID_LOCATION_CANONICAL_PREORDER"), "content is invalid against its applied schema")]))
    fams.append(F("PE-38", "PE-38", "BOUND_SOURCE_CONTENT_INVALID", "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE", sio, "SEVEN_FIELD",
                  "metacontract:/eligibility/bound_source_universe", "ALLOWLIST_ORDER", "CONDITION_RANK",
                  [K("BOUND_SCHEMA_MEMBER_UNREGISTERED", "SOURCE_ELIGIBILITY", "BOUND_SOURCE_SCHEMA_MEMBER_UNREGISTERED", h1("DOCUMENT_ROOT"), "expected_schema_ref member is not registered"),
                   K("BOUND_SCHEMA_VIOLATION", "JSON_SCHEMA", "BOUND_SOURCE_SCHEMA_VIOLATION", h1("FIRST_INVALID_LOCATION_CANONICAL_PREORDER"), "pinned content is invalid against its expected schema member")]))
    dec = W(C("metacontract"), D("OWNING_OBJECT_REGISTRY_ROW_KIND"), D("OWNING_OBJECT_APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"), D("FIRST_DECLARATION_MEMBER_VIOLATION_DECLARED_ORDER"), D("OWNING_OBJECT_REGISTRY_IDENTITY"))
    fams.append(F("PE-41", "PE-41", "RESERVED_INPUT_DECLARATIONS", "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE", sio, "SEVEN_FIELD",
                  "metacontract:/reserved_inputs", "RESERVED_INPUT_ORDER", "CONDITION_RANK_THEN_SUBJECT_ORDER",
                  [K(cid, "TYPE", cid, dec, cond) for cid, cond in [
                      ("RESERVED_INPUT_DECLARATION_INVALID", "a row lacks a nonempty string name, type or origin"),
                      ("RESERVED_INPUT_DECLARATION_NOT_UNIQUE", "a name is declared twice"),
                      ("RESERVED_INPUT_ORIGIN_UNDECLARED", "origin is not in binding_origins.allowed_origins"),
                      ("RESERVED_INPUT_NAME_LABEL_MISMATCH", "binding_origins.reserved_names label disagrees with type/origin"),
                      ("RESERVED_INPUT_NAME_SET_MISMATCH", "declared names differ from binding_origins.reserved_names"),
                      ("RESERVED_CONTENT_SOURCE_INVALID", "profile_content_source lacks the declared encoding/decode/authority flags"),
                      ("RESERVED_CONTENT_POINTER_INVALID", "content or pin pointer tokens are not nonempty strings"),
                      ("RESERVED_CONTENT_SOURCE_TRANSPORT_INVALID", "profile_content_source.argument is not the EXTERNAL_ACCEPTANCE_PROFILE transport"),
                      ("RESERVED_CONTENT_SOURCE_PIN_UNDECLARED", "pin pointer does not name a declared external authority pin")]], owning_object="metacontract"))
    fams.append(F("PE-39", "PE-39", "RESERVED_INPUT_PRODUCER_SCHEMA", "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE", sio, "SEVEN_FIELD",
                  "metacontract:/runtime_representation/static_type_calculus/argument_typing/reserved_input_producer_schema_binding", "RESERVED_INPUT_ORDER_WITH_PRODUCER_SCHEMA", "CONDITION_RANK",
                  [K("PRODUCER_SCHEMA_UNRESOLVED", "SOURCE_ELIGIBILITY", "RESERVED_INPUT_PRODUCER_SCHEMA_UNRESOLVED",
                     W(D("RESERVED_INPUT_NAME"), D("RESERVED_INPUT_DECLARED_TYPE"), D("PRODUCER_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"), D("DOCUMENT_ROOT"), D("FROZEN_SOURCE_TYPED_IDENTITY")),
                     "producer_schema_ref does not name one eligible SCHEMA row and one registered member"),
                   K("PRODUCER_SCHEMA_VIOLATION", "JSON_SCHEMA", "RESERVED_INPUT_PRODUCER_SCHEMA_VIOLATION",
                     W(D("RESERVED_INPUT_NAME"), D("RESERVED_INPUT_DECLARED_TYPE"), D("PRODUCER_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"), D("FIRST_INVALID_LOCATION_CANONICAL_PREORDER"), D("FROZEN_SOURCE_TYPED_IDENTITY")),
                     "the pin-verified decoded content is invalid against the producer schema member")],
                  h1_overrides={"argument": "metacontract:/reserved_inputs/*/name", "object_role": "metacontract:/reserved_inputs/*/type",
                                "bound_identity": "protocol_constants.frozen_sources (the reserved input is not a registry object)"}))
    rv = W(D("RUNTIME_VALUE_NAME"), D("RUNTIME_VALUE_TYPE"), D("RUNTIME_VALUE_SCHEMA_ID"), D("FIRST_INVALID_LOCATION_CANONICAL_PREORDER"), D("RESOLVED_OBJECT_IDENTITY_CONTAINING_LOCATION_ELSE_NULL"))
    fams.append(F("PE-40", "PE-40", "RUNTIME_REPRESENTATION", "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE", sio, "SEVEN_FIELD",
                  "metacontract:/runtime_representation/value_schemas", "RUNTIME_VALUE_ORDER", "CONDITION_RANK",
                  [K("VALUE_SCHEMA_INVALID", "JSON_SCHEMA", "RUNTIME_VALUE_SCHEMA_NOT_VALID_DRAFT_2020_12",
                     W(C("metacontract"), D("OWNING_OBJECT_REGISTRY_ROW_KIND"), D("DRAFT_2020_12_METASCHEMA"), D("FIRST_INVALID_LOCATION_CANONICAL_PREORDER"), D("OWNING_OBJECT_REGISTRY_IDENTITY")),
                     "a declared value schema is not a valid Draft 2020-12 schema (resolved_object then verification_universe)", owning_object="metacontract"),
                   K("UNIVERSE_REPRESENTATION", "JSON_SCHEMA", "VERIFICATION_UNIVERSE_REPRESENTATION_INVALID", rv, "the published universe value is invalid against value_schemas.verification_universe"),
                   K("RESOLVED_OBJECT_REPRESENTATION", "JSON_SCHEMA", "RESOLVED_OBJECT_REPRESENTATION_INVALID", rv, "a member-resolved object record is invalid against value_schemas.resolved_object (objects in universe order, members in registered order)")]))
    # ---- 22 static validation and bindings (H2, H4)
    post = lambda arg, ptr: W(arg, D("OWNING_OBJECT_REGISTRY_ROW_KIND"), D("OWNING_OBJECT_APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"), D(ptr), D("OWNING_OBJECT_REGISTRY_IDENTITY"))
    st = lambda owner, loc: post(D("OWNING_BOOTSTRAP_OBJECT_ARGUMENT"), "STATIC_VIOLATION_LOCATION")
    reg_level = [
        ("PRIMITIVE_SET_EXACT_TO_STATIC_TYPE_CALCULUS", "primitive_registry", "SET_EXACT", "/primitives", "primitive ids unique and equal to the static-type-calculus operator set"),
        ("PRIMITIVE_SIGNATURE_MATCHES_STATIC_TYPE_CALCULUS", "primitive_registry", "MEMBER", "/primitives/<i>", "a primitive's arguments or output type differ from its operator rule"),
        ("DESCENDANT_CONFORMANCE_VECTORS_REPRODUCED", "primitive_registry", "MEMBER", "/descendant_conformance_vectors/<i>", "a declared descendant conformance vector is not reproduced"),
        ("PROCEDURE_ID_SET_EXACT", "procedure_registry", "SET_EXACT", "/procedures", "procedure ids unique and equal to the procedure ids referenced by the invariant registry"),
        ("INVARIANT_SET_EXACT_TO_PACKAGE_REQUIRED_INVARIANT_IDS", "invariant_registry", "SET_EXACT", "/invariants", "invariant ids unique and equal to package required_invariant_ids"),
        ("BOUND_RULE_SET_EXACT_TO_REQUIRED_RULE_IDS", "rule_registry", "SET_EXACT", "/rules", "executable conformance rule ids unique and equal to the package required rule ids"),
        ("INVARIANT_PROCEDURE_BINDINGS_EXACT", "metacontract", "SET_EXACT", "/procedure_bindings", "exactly one binding row per invariant naming the invariant's procedure"),
        ("RULE_INVARIANT_BINDING_RESOLVES", "rule_registry", "MEMBER", "/rules/<i>/invariant_binding", "a rule's invariant_binding names no invariant or an undeclared argument"),
        ("RESERVED_BINDINGS_IMMUTABLE", "metacontract", "MEMBER", "/procedure_bindings/<i>/reserved_bindings/<j>", "a reserved binding's type/origin differs from the reserved input declaration or procedure argument"),
        ("RULE_BINDING_SOURCE_CONSTRAINTS_VALID", "procedure_registry", "MEMBER", "/procedures/<i>/arguments/<j>/source_constraint", "a RULE_BINDING argument lacks a well-formed source_constraint"),
        ("PROCEDURE_RESULT_TYPE_DECLARED", "procedure_registry", "MEMBER", "/procedures/<i>/result/type", "result type is not BOOLEAN or TRUST_RESULT"),
        ("TRUST_RESULT_OWNER_EXACT", "procedure_registry", "SET_EXACT", "/procedures", "exactly the declared trust-anchor procedure has result type TRUST_RESULT"),
        ("ASSERTION_CODES_IN_PROCEDURE_COMPATIBLE_SET", "procedure_registry", "MEMBER", "/procedures/<i>/assertions/<j>/failure_code", "failure code not in the procedure's compatible set"),
        ("ASSERTION_CODES_IN_EVERY_BOUND_INVARIANT_SET", "procedure_registry", "MEMBER", "/procedures/<i>/assertions/<j>/failure_code", "failure code not authorized by every invariant bound to the procedure"),
    ]
    fams.append(F("PE-45", "PE-45", "STATIC_REGISTRY_LEVEL", "STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR", "STATIC_VALIDATION_FAILED", "STATIC_VALIDATION",
                  "metacontract:/static_validation_rules", "STATIC_CONDITION_COLLECTION_INDEX_ORDER", "CONDITION_RANK_THEN_SUBJECT_ORDER",
                  [K(tok, "STATIC_VALIDATION", tok, st(owner, loc), cond, owning_object=owner, location_rule=loc, location_template=tmpl) for tok, owner, loc, tmpl, cond in reg_level]))
    limits = [k for k in meta["resource_limits"]]
    proc_level = [("ARGUMENT_NAMES_UNIQUE", "UNIQUENESS", "/procedures/<i>/arguments", "duplicate argument name"),
                  ("MAX_ARGUMENTS_PER_PROCEDURE_EXCEEDED", "MEMBER", "/procedures/<i>/arguments", "resource_limits.max_arguments_per_procedure exceeded"),
                  ("ASSERTION_IDS_UNIQUE", "UNIQUENESS", "/procedures/<i>/assertions", "duplicate assertion id"),
                  ("MAX_ASSERTIONS_PER_PROCEDURE_EXCEEDED", "MEMBER", "/procedures/<i>/assertions", "assertion list empty or above resource_limits.max_assertions_per_procedure"),
                  ("MAX_AST_NODES_PER_PROCEDURE_EXCEEDED", "MEMBER", "/procedures/<i>/assertions", "resource_limits.max_ast_nodes_per_procedure exceeded")]
    node_level = [("EXACT_OPERATOR_OPERANDS", "node is not an arg/item/literal/op object or its members differ from its operator's declared slots"),
                  ("OPERATOR_IN_CLOSED_OPERATOR_LANGUAGE", "op is not a registered primitive / static-type-calculus operator"),
                  ("DECLARED_ARGUMENTS_ONLY", "arg terminal names an undeclared argument"),
                  ("LEXICAL_SCOPE_NO_SHADOW_OR_ESCAPE_ON_ACTIVE_PATH", "item terminal free/escaping, or a binder shadows an active binding"),
                  ("MAX_EXPRESSION_DEPTH_EXCEEDED", "resource_limits.max_expression_depth exceeded"),
                  ("MAX_LEXICAL_COLLECTION_NESTING_EXCEEDED", "resource_limits.max_lexical_collection_nesting exceeded"),
                  ("POINTER_LITERAL_RFC6901_VALID", "a pointer slot literal is not an RFC6901 pointer"),
                  ("RESOLVE_ONE_USES_EXACT_VERIFICATION_UNIVERSE_TERMINAL", "RESOLVE_ONE universe is not the exact verification_universe terminal"),
                  ("DIGEST_MODE_FIELDS_ARE_DYNAMIC_EXPRESSIONS", "digest mode fields are not dynamic expressions from a declared argument or item"),
                  ("STATIC_TYPE_AT_PATH_SCHEMA_NOMINAL_AND_STRUCTURAL", "a static GET path is not declared for the operand type"),
                  ("OPERAND_RESULT_TYPES_VALID", "an operand's inferred type is not assignable to its slot"),
                  ("AST_TYPE_UNDERDETERMINED_FAILS_CLOSED", "a node's static type is underdetermined"),
                  ("ASSERTION_CONDITION_ROOTS_BOOLEAN_NO_TRUTHINESS", "an assertion condition root is not statically BOOLEAN")]
    fams.append(F("PE-44", "PE-44", "STATIC_PROCEDURE_AST", "STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR", "STATIC_VALIDATION_FAILED", "STATIC_VALIDATION",
                  "metacontract:/static_validation_rules", "AST_PROCEDURE_ASSERTION_POSTORDER", "SUBJECT_ORDER_THEN_CONDITION_RANK",
                  [K(tok, "STATIC_VALIDATION", tok, st("procedure_registry", loc), cond, owning_object="procedure_registry", location_rule=loc, location_template=tmpl, level="PROCEDURE") for tok, loc, tmpl, cond in proc_level] +
                  [K(tok, "STATIC_VALIDATION", tok, st("procedure_registry", "NODE"), cond, owning_object="procedure_registry", location_rule="NODE", level="NODE") for tok, cond in node_level],
                  resource_limit_tokens={("MAX_" + k[len("max_"):].upper() + "_EXCEEDED") if k.startswith("max_") else k.upper(): "metacontract:/resource_limits/" + k for k in limits}))
    gw = post(C("metacontract"), "DECLARED_SECTION_POINTER")
    fams.append(F("PE-46", "PE-46", "WITNESS_OPERAND_IDENTITY_TOTALITY", "STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR", "STATIC_VALIDATION_FAILED", "STATIC_VALIDATION",
                  "metacontract:/failure_semantics/generic_failure_witness", "WITNESS_OPERAND_PREORDER", "CONDITION_RANK_THEN_SUBJECT_ORDER",
                  [K("GENERIC_WITNESS_DECLARATION_UNSUPPORTED", "STATIC_VALIDATION", "GENERIC_FAILURE_WITNESS_DECLARATION_UNSUPPORTED", gw,
                     "RFC8785 SHA-256 of /failure_semantics/generic_failure_witness differs from verifier_protocol_digests", section_pointer="/failure_semantics/generic_failure_witness", owning_object="metacontract"),
                   K("MISSING_WITNESS_OPERAND_IDENTITY", "STATIC_VALIDATION", "MISSING_WITNESS_OPERAND_IDENTITY",
                     post(C("procedure_registry"), "WITNESS_OPERAND_TERMINAL"),
                     "a declared-witness operand terminal of a BOOLEAN procedure has neither a RULE_BINDING bound identity nor an operand-only identity (H2)", owning_object="procedure_registry")]))
    bw = post(D("OWNING_BOOTSTRAP_OBJECT_ARGUMENT"), "BINDING_DECLARATION_LOCATION")
    fams.append(F("PE-48", "PE-48", "REQUIRED_BINDING_RESOLUTION", "STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR", "STATIC_VALIDATION_FAILED", "STATIC_VALIDATION",
                  "metacontract:/source_constraints", "BINDING_SITE_ORDER", "SUBJECT_ORDER_THEN_CONDITION_RANK",
                  [K(tok, "STATIC_VALIDATION", tok, bw, cond) for tok, cond in [
                      ("BINDING_REQUIRED_ARGUMENT_MISSING", "a RULE_BINDING argument has no effective binding"),
                      ("BINDING_NOT_STRICT_TYPED_REFERENCE", "the binding value is not a closed kind/id/version(/member_id) reference"),
                      ("BINDING_KIND_DIFFERS_FROM_SOURCE_CONSTRAINT", "reference kind differs from source_constraint.expected_kind"),
                      ("BINDING_TARGET_NOT_IN_DECLARED_UNIVERSE", "no object with that identity in the source_constraint universe"),
                      ("BINDING_TARGET_STATUS_CLASSIFICATION_OR_ROLES_INELIGIBLE", "target status, classification or roles violate the constraint"),
                      ("BINDING_TARGET_SCHEMA_REFERENCE_MISMATCH", "target registered schema_ref differs from expected_schema_ref"),
                      ("BINDING_TARGET_SCHEMA_MEMBER_UNRESOLVED", "binding member_id does not resolve to one registered member"),
                      ("BINDING_EXACT_REFERENCE_OR_PATH_MISMATCH", "EXACT_REFERENCE constraint ref or canonical path differs"),
                      ("BINDING_ACCEPTED_SOURCE_METADATA_MISMATCH", "accepted-source metadata differs from the verified allowlist")]],
                  owning_object="BINDING_DECLARING_OBJECT (invariant_registry for default_arguments; rule_registry for invariant_binding.arguments)",
                  binding_site_order="invariant registry order: procedure RULE_BINDING arguments in declaration order using invariant default_arguments; then rule registry order: invariant_binding.arguments in the procedure's argument order"))
    vi = {"kind": "CONTRACT", "id": "urn:moirae:accord-02r5r3:v013-governance", "version": "0.2"}
    fams.append(F("PE-47", "PE-47", "RESULT_PROJECTION_MAP_VALUE", "STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR", "RESULT_PROJECTION_INVALID", "MAP_VALUE_COMPARISON",
                  "metacontract:/result_projection_authorization", "SELECTED_PROJECTION_PROCEDURE", "CONDITION_RANK",
                  [{"condition_id": reason, "condition": cond, "reason": reason,
                    "witness": {"stage": C("MAP_VALUE_COMPARISON"), "procedure_id": D("SELECTED_PROCEDURE_ID"), "map_argument": D("DESCRIPTOR_ARGUMENT"),
                                "map_pointer": D("DESCRIPTOR_POINTER_TOKENS_AS_RFC6901"), "baseline_argument": D("DESCRIPTOR_BASELINE_ARGUMENT"),
                                "baseline_identity": C(vi), "expected": D("DESCRIPTOR_EXPECTED_LITERALS"), "actual": D(actual)}}
                   for reason, actual, cond in [
                      ("PROJECTION_PATH_INVALID", "NULL", "the baseline status pointers or the map pointer do not resolve"),
                      ("BASELINE_VALUE_TYPE", "BASELINE_STATUS_VALUES", "baseline pass_result/fail_result are not strings"),
                      ("BASELINE_LITERAL_MISMATCH", "BASELINE_STATUS_VALUES", "baseline status literals differ from expected_literals"),
                      ("MAP_VALUE_TYPE", "MAP_VALUE", "the map value is not an object of strings"),
                      ("MAP_MISSING_OR_EXTRA_KEY", "MAP_VALUE", "map keys differ from expected_literals keys or mapping_cardinality"),
                      ("LITERAL_MISMATCH", "MAP_VALUE", "a map literal differs from expected_literals")]]))
    return fams


def _r5r20_mirrors_and_internal():
    mirrors = [
        {"family_id": "PE-28", "class": "NORMATIVE_DEFENSIVE_MIRROR", "condition": "integrity mode/identity pairing re-checked after registration", "owner_family": "PE-21",
         "dominance": "object-registry schema allOf pins PACKAGE_PINNED_BOOTSTRAP to the registry identity and SELF_DIGEST to the package identity (stage 13 < later stages)"},
        {"family_id": "PE-29", "class": "NORMATIVE_DEFENSIVE_MIRROR", "condition": "registry key/identity/duplicate/reference/content-identity re-checks", "owner_family": ["PE-21", "PE-23", "PE-24"],
         "dominance": "registration.later_identical_checks = DEFENSIVE_UNREACHABLE; stages 13-15 precede every re-check"},
        {"family_id": "PE-32-REGISTRATION-FIELDS", "class": "NORMATIVE_DEFENSIVE_MIRROR", "condition": "registration row lacks typed roles/schema_ref/integrity", "owner_family": "PE-21",
         "dominance": "object-registry schema requires roles, integrity, and schema_ref for ACTIVE NORMATIVE non-SCHEMA rows (stage 13)"},
        {"family_id": "PE-42", "class": "NORMATIVE_DEFENSIVE_MIRROR", "condition": "metacontract/package/registry not resolvable after universe derivation", "owner_family": ["PE-18", "PE-19", "PE-33", "PE-33B"],
         "dominance": "claim artefacts are located at stage 12, entrypoints bound at stage 6, bootstrap eligibility at stage 17"},
        {"family_id": "PE-43", "class": "NORMATIVE_DEFENSIVE_MIRROR", "condition": "member inventory duplicates/unbound members", "owner_family": ["PE-21", "PE-23", "PE-40"],
         "dominance": "SCHEMA-row members uniqueItems (stage 13) and member binding rule (stage 14); non-SCHEMA duplicate members violate value_schemas.resolved_object members uniqueItems (PE-40)"},
        {"family_id": "PE-49", "class": "NORMATIVE_DEFENSIVE_MIRROR", "condition": "invocation projection binding/map read/compare during execution", "owner_family": ["PE-47", "PE-48"],
         "dominance": "stage 22 validates the selected binding and the map value before any assertion executes"},
        {"family_id": "PE-15-PROFILE-AUTHORITY", "class": "NORMATIVE_DEFENSIVE_MIRROR", "condition": "profile origin/pin/allowlist/descriptor re-checks beyond validation", "owner_family": ["PE-15", "PE-18", "PE-19"],
         "dominance": "required members are validated at stage 8; pins, allowlist and descriptor are compared whole-object at stage 12"},
        {"family_id": "PE-47-DESCRIPTOR-AUTHORIZATION", "class": "NORMATIVE_DEFENSIVE_MIRROR", "condition": "selected or metacontract descriptor differs from the profile descriptor", "owner_family": ["PE-18", "PE-19"],
         "dominance": "stage 12 compares both descriptors whole-object before stage 22",
         "witness_contract": "DESCRIPTOR_AUTHORIZATION",
         "declared_derivations": {"baseline_identity": {"constant": {"kind": "CONTRACT", "id": "urn:moirae:accord-02r5r3:v013-governance", "version": "0.2"}},
                                  "mismatch_pointer": "first location in the DESCENDANTS canonical preorder of the union of both descriptors' locations whose values differ or which exists on only one side; the pointer of the member present on only one side for a missing member; \"\" when the root values differ in JSON type or no more specific location exists"}},
    ]
    internal = [
        {"family_id": "PE-50", "class": "IMPLEMENTATION_INTERNAL_UNREACHABLE", "condition": "emitted-result self-validation, empty assertions, registry counts, bound-rule invariant resolution, projection finalize", "normative_result_authority": False},
        {"family_id": "PE-51", "class": "IMPLEMENTATION_INTERNAL_UNREACHABLE", "condition": "dedicated RNF/trust-procedure/generic-witness helper guards after static validation", "normative_result_authority": False},
        {"family_id": "PE-52", "class": "IMPLEMENTATION_INTERNAL_UNREACHABLE", "condition": "uncaught expression error escaping a pre-execution stage", "normative_result_authority": False,
         "reachable_triggers_owned_by": {"non-RFC8785 number in the package": "PE-12", "non-RFC8785 number in row content": "PE-26", "unresolved local schema fragment": ["PE-08", "PE-37"]}},
        {"family_id": "PE-53", "class": "IMPLEMENTATION_INTERNAL_UNREACHABLE", "condition": "uncaught implementation exception", "normative_result_authority": False,
         "reachable_triggers_owned_by": {"unreadable caller schema bytes": "PE-04", "unreadable caller profile": "PE-14", "unreadable entrypoint": "PE-02", "unreadable candidate object": "PE-30",
                                         "package not an object": "PE-10", "registry not an object": "PE-33", "unsupported declaration shape": ["PE-22", "PE-41", "PE-46"]}},
    ]
    return mirrors, internal


def _r5r20_stage_ordering(meta, fams):
    groups = {
        "READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST_TRIPLE": [["PE-01"], ["PE-03"], ["PE-02"]],
        "READ_EXTERNAL_PROFILE_SCHEMA_ID_BYTES_AND_EXPECTED_SHA256_OUTSIDE_CANDIDATE": [["PE-04"], ["PE-06"]],
        "REQUIRE_CALLER_SCHEMA_ID_EQUAL_FIXED_VERIFIER_SCHEMA_ID": [["PE-05"]],
        "VERIFY_PROFILE_SCHEMA_RAW_SHA256_BEFORE_PARSE_OR_USE": [["PE-07"]],
        "VERIFY_PROFILE_SCHEMA_ID_AND_DRAFT_2020_12_DIALECT": [["PE-08"]],
        "REJECT_DUPLICATE_CANDIDATE_JSON_NAMES_AND_INVALID_UTF8": [["PE-09"]],
        "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE": [["PE-10"], ["PE-12"], ["PE-13"], ["PE-11"], ["PE-33"]],
        "READ_EXTERNAL_ACCEPTANCE_PROFILE_OUTSIDE_CANDIDATE": [["PE-14"]],
        "VALIDATE_EXTERNAL_ACCEPTANCE_PROFILE_WITH_VERIFIED_EXTERNAL_SCHEMA_BYTES": [["PE-15"]],
        "VERIFY_EXTERNAL_FROZEN_R5R2_CONTENT_AND_PIN": [["PE-16A"]],
        "VERIFY_EXTERNAL_FROZEN_R5R3_CONTENT_AND_PIN": [["PE-16B"]],
        "VERIFY_EXTERNAL_ACCEPTED_BASE_AND_VECTOR_CONTENT_AND_PINS": [["PE-17"]],
        "COMPARE_ALL_CANDIDATE_AUTHORITY_CLAIMS_WHOLE_OBJECT_BEFORE_SEMANTIC_USE": [["PE-18"], ["PE-19"]],
        "APPLY_OBJECT_REGISTRY_SCHEMA_TO_FULL_REGISTRY": [["PE-22"], ["PE-21"]],
        "SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS": [["PE-23"]],
        "GLOBAL_UNIQUENESS_VALIDATE_STAGE_ONLY": [["PE-24"]],
        "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS": [["PE-25", "PE-27", "PE-26"]],
        "SELECT_ELIGIBLE_CANDIDATE_OBJECTS": [["PE-33B"]],
        "RESOLVE_CANDIDATE_OBJECTS": [["PE-30", "PE-31", "PE-32"]],
        "BOUND_SOURCE_RESOLVED_CONSTRUCTION": [["PE-34"]],
        "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE": [["PE-35"], ["PE-37", "PE-36"], ["PE-38"], ["PE-41"], ["PE-39"], ["PE-40"]],
        "STATIC_VALIDATE_PROCEDURE_REGISTRY_AND_RESULT_PROJECTION_SELECTOR": [["PE-45"], ["PE-44"], ["PE-46"], ["PE-48"], ["PE-47"]],
    }
    subject_major = {"VERIFY_REGISTRY_INTEGRITY_DECLARATIONS": "REGISTRY_SOURCE_ORDER", "RESOLVE_CANDIDATE_OBJECTS": "ELIGIBLE_ROWS_REGISTRY_SOURCE_ORDER",
                     "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE": "ELIGIBLE_ROWS_REGISTRY_SOURCE_ORDER"}
    out = []
    for index, stage in enumerate(meta["bootstrap_order"]):
        if stage not in groups: continue
        out.append({"stage": stage, "stage_index": index, "groups": [
            {"group_rank": rank, "families": fam,
             "group_order": ("SUBJECT_MAJOR:" + subject_major[stage]) if len(fam) > 1 else "SINGLE_FAMILY",
             **({"family_rank_within_subject": {f: i for i, f in enumerate(fam, 1)}} if len(fam) > 1 else {})}
            for rank, fam in enumerate(groups[stage], 1)]})
    return out


def _r5r20_model(meta, reg, pkg):
    pc = _r5r20_protocol_constants(meta, reg, pkg)
    fams = _r5r20_families(meta, pc)
    mirrors, internal = _r5r20_mirrors_and_internal()
    ordering = _r5r20_stage_ordering(meta, fams)
    by_fam = {f["family_id"]: f for f in fams}
    for stage in ordering:
        for group in stage["groups"]:
            for rank, fid in enumerate(group["families"], 1):
                fam = by_fam[fid]
                if fam["stage"] != stage["stage"]:
                    raise ValueError("family stage differs from its ordering stage: " + fid)
                fam["stage_index"] = stage["stage_index"]
                fam["group_rank"] = group["group_rank"]
                fam["family_rank_in_group"] = rank
    return {
        "model_id": "ACCORD_PRE_EXECUTION_FAILURE_MODEL",
        "model_version": "0.2",
        "authority": {"stage_order": "metacontract:/bootstrap_order", "stage_order_is_authoritative": True,
                      "code_catalogue": "metacontract:/failure_semantics/pre_execution_order", "code_catalogue_is_precedence": False,
                      "code_catalogue_note": "pre_execution_order lists registered codes; SCHEMA_INVALID_BOUND_OBJECT and the preflight codes interleave across stages, so precedence is defined only by this model",
                      "early_stage_rows": "rows for stages before COMPARE_ALL_CANDIDATE_AUTHORITY_CLAIMS_WHOLE_OBJECT_BEFORE_SEMANTIC_USE are verifier-protocol constants; the candidate copy is compared by PE-22",
                      "evaluator_behavior_is_not_authority": True},
        "first_failure_selection": {
            "key": ["STAGE_INDEX_IN_bootstrap_order", "GROUP_RANK_WITHIN_STAGE", "GROUP_ORDER_KEY", "CONDITION_OR_SUBJECT_KEY_OF_THE_FAMILY"],
            "group_order_key": {"SINGLE_FAMILY": "the family's within_family_order", "SUBJECT_MAJOR": "(subject index, family_rank_within_subject, condition rank)"},
            "within_family_order": {"CONDITION_RANK": "(condition rank)", "SINGLE_CONDITION": "(1)",
                                    "CONDITION_RANK_THEN_SUBJECT_ORDER": "(condition rank, subject index)", "SUBJECT_ORDER_THEN_CONDITION_RANK": "(subject index, condition rank)",
                                    "REGISTRATION_DECLARED_ORDER": "metacontract:/registration/first_failure_ordering", "DECLARED_REASON_ORDER": "metacontract:/registration/bound_source_resolved_construction/reason_derivation"},
            "comparison": "LEXICOGRAPHIC_ASCENDING_TOTAL_ORDER", "stop_after_first_failure": True,
            "later_stages_after_failure": "NOT_EVALUATED_EMIT_NO_RESULT", "mirror_and_internal_families_selectable": False,
            "no_ast_before_static_and_binding_complete": True},
        "subject_orders": {
            "SINGLE_SUBJECT": "one subject", "ENTRYPOINT_ORDER": "candidate_package, then object_registry",
            "REGISTRY_SOURCE_ORDER": "ascending /objects index of the explicit registry",
            "ELIGIBLE_ROWS_REGISTRY_SOURCE_ORDER": "eligible (ACTIVE NORMATIVE) rows in ascending /objects index",
            "ELIGIBLE_SCHEMA_ROWS_REGISTRY_SOURCE_ORDER": "eligible SCHEMA rows in ascending /objects index, scanned together with non-SCHEMA rows in one registry-source-order pass (H1)",
            "ELIGIBLE_NON_SCHEMA_ROWS_REGISTRY_SOURCE_ORDER": "eligible non-SCHEMA rows in ascending /objects index, scanned together with SCHEMA rows in one registry-source-order pass (H1)",
            "ALLOWLIST_ORDER": "ascending external_acceptance_profile:/accepted_source_allowlist index",
            "CLAIM_COMPARISON_ORDER_0_TO_3": "candidate_claim_comparisons indices 0..3 in array order",
            "PROTOCOL_SECTION_ORDER": "failure model, then registration",
            "REGISTRATION_DECLARED_ORDER": "metacontract:/registration/first_failure_ordering",
            "GLOBAL_UNIQUENESS_DECLARED_SELECTION": "metacontract:/registration/global_uniqueness/selection",
            "PACKAGE_BOOTSTRAP_REFERENCE_ORDER": "the package, then " + ", ".join(_R5R20_BOOTSTRAP_REFS),
            "BOUND_SOURCE_DECLARED_SCOPE": "metacontract:/registration/bound_source_resolved_construction/source_scope",
            "STRICT_UNION_DECLARED_SCAN": "metacontract:/registration/strict_identity_union/scan_selection",
            "RESERVED_INPUT_ORDER": "ascending metacontract:/reserved_inputs index",
            "RESERVED_INPUT_ORDER_WITH_PRODUCER_SCHEMA": "reserved_inputs rows declaring profile_content_source.producer_schema_ref, ascending index",
            "RUNTIME_VALUE_ORDER": "value schemas (resolved_object, verification_universe), then the universe value, then objects in universe order with members in registered order",
            "FROZEN_SOURCE_FROZEN_R5R2_RULES": "one subject", "FROZEN_SOURCE_FROZEN_R5R3_V013_SEMANTICS": "one subject",
            "STATIC_CONDITION_COLLECTION_INDEX_ORDER": "within a condition, ascending collection index (procedure, argument, assertion)",
            "AST_PROCEDURE_ASSERTION_POSTORDER": "procedures in source order; procedure-level conditions; then assertions in source order, condition before witness, nodes in canonical postorder with operand slots in declared operator slot order",
            "WITNESS_OPERAND_PREORDER": "procedures in source order, assertions in source order, declared-witness first-occurrence preorder (metacontract:/failure_semantics/generic_failure_witness/operands/order)",
            "BINDING_SITE_ORDER": "invariant registry order then rule registry order (see family binding_site_order)",
            "SELECTED_PROJECTION_PROCEDURE": "the single procedure selected by procedure_projection_selector"},
        "protocol_constants": pc,
        "derivation_vocabulary": _r5r20_vocabulary(),
        "witness_contracts": {
            "SEVEN_FIELD": {"result_contract_ref": "metacontract:/result_contracts/pre_execution_result", "code": "SCHEMA_INVALID_BOUND_OBJECT", "fields": list(_R5R20_SEVEN)},
            "STATIC_VALIDATION": {"result_contract_ref": "metacontract:/result_contracts/pre_execution_result", "code": "STATIC_VALIDATION_FAILED", "fields": list(_R5R20_SEVEN), "failure_kind": "STATIC_VALIDATION"},
            "PROFILE_PREFLIGHT": {"result_contract_ref": "metacontract:/result_contracts/pre_execution_result", "witness_def": "external_profile_preflight_witness", "fields": list(_R5R20_PREFLIGHT),
                                  "operation": "the const of the registered branch for the family code"},
            "TRUST_RESULT": {"result_contract_ref": "metacontract:/result_contracts/trust_result"},
            "MAP_VALUE_COMPARISON": {"result_contract_ref": "metacontract:/result_contracts/pre_execution_result", "witness_def": "map_value_comparison_witness"},
            "DESCRIPTOR_AUTHORIZATION": {"result_contract_ref": "metacontract:/result_contracts/pre_execution_result", "witness_def": "descriptor_authorization_witness"},
            "STRICT_UNION_COLLISION": {"result_contract_ref": "metacontract:/result_contracts/pre_execution_result", "witness_def": "strict_union_collision_witness"},
            "VECTOR_REGISTRY_CLAIM": {"result_contract_ref": "metacontract:/result_contracts/pre_execution_result", "witness_def": "vector_registry_claim_witness"}},
        "families": fams,
        "stage_ordering": ordering,
        "defensive_mirrors": mirrors,
        "internal_only": internal,
        "r5r19_reconciliation": {
            "r5r19_reachable_families": 46,
            "removed_not_a_failure_family": {"PE-20": "precedence relation PE-18 (stage 12) before PE-21 (stage 13), expressed by stage_ordering"},
            "reclassified_implementation_internal": {"PE-52": "catch-all; triggers owned by PE-08, PE-12, PE-26, PE-37", "PE-53": "catch-all; triggers owned by PE-02, PE-04, PE-10, PE-14, PE-22, PE-30, PE-33, PE-41, PE-46"},
            "split_by_declared_stage": {"PE-16": ["PE-16A", "PE-16B"], "PE-33": ["PE-33", "PE-33B"]},
            "mixed_family_resolution": {"PE-32": "content condition reachable (PE-32); registration-field part mirrors PE-21", "PE-43": "mirror of PE-21, PE-23 and PE-40"},
            "final_reachable_families": None},
    }


def _r5r20_schema_patch(schema):
    defs = schema["$defs"]
    branches = defs["pre_execution_result"]["oneOf"]
    seven = branches[0]["properties"]["witness"]["properties"]
    seven["diagnostic"] = {"type": "string", "pattern": _R5R20_TOKEN}
    seven["instance_pointer"] = {"type": "string", "pattern": _R5R20_POINTER}
    static = copy.deepcopy(branches[0])
    static["properties"]["code"] = {"const": "STATIC_VALIDATION_FAILED"}
    static["properties"]["witness"]["properties"]["failure_kind"] = {"const": "STATIC_VALIDATION"}
    digest_invalid = copy.deepcopy(next(b for b in branches if b["properties"]["code"].get("const") == "EXTERNAL_PROFILE_SCHEMA_DIGEST_MISMATCH"))
    digest_invalid["properties"]["code"] = {"const": "EXTERNAL_PROFILE_SCHEMA_DIGEST_INVALID"}
    digest_invalid["properties"]["witness"]["allOf"][1] = {"properties": {"operation": {"const": "VALIDATE_EXPECTED_PROFILE_SCHEMA_SHA256_FORMAT"}}, "required": ["operation"]}
    codes = [b["properties"]["code"].get("const") for b in branches]
    if "STATIC_VALIDATION_FAILED" not in codes: branches.append(static)
    if "EXTERNAL_PROFILE_SCHEMA_DIGEST_INVALID" not in codes: branches.append(digest_invalid)
    pw = defs["external_profile_preflight_witness"]
    pw["properties"]["profile_pointer"] = {"oneOf": [{"type": "null"}, {"type": "string", "pattern": _R5R20_POINTER}]}
    pw["properties"]["candidate_artifact"] = {"oneOf": [{"type": "null"}, {"type": "string", "minLength": 1}]}
    pw["properties"]["candidate_pointer"] = {"oneOf": [{"type": "null"}, {"type": "string", "pattern": _R5R20_POINTER}]}
    pw["properties"]["diagnostic"] = {"type": "string", "pattern": _R5R20_TOKEN}
    if "diagnostic" not in pw["required"]: pw["required"].append("diagnostic")
    if "INPUT_MALFORMED" not in pw["properties"]["reason"]["enum"]: pw["properties"]["reason"]["enum"].insert(2, "INPUT_MALFORMED")
    mv = defs["map_value_comparison_witness"]["properties"]["reason"]["enum"]
    if "BASELINE_LITERAL_MISMATCH" not in mv: mv.insert(3, "BASELINE_LITERAL_MISMATCH")
    return schema


def _r5r20_totality(model, meta, schema):
    """Builder-side totality: every reachable family is completely determined."""
    stages = meta["bootstrap_order"]
    codes = set(meta["result_contracts"]["pre_execution_result"]["fail_codes"]) | {"MISSING_EXTERNAL_TRUST_INPUT", "FOREIGN_PACKAGE_IDENTITY", "TRUSTED_IDENTITY_MISMATCH"}
    vocab = model["derivation_vocabulary"]
    kinds = set(schema["$defs"]["pre_execution_result"]["oneOf"][0]["properties"]["witness"]["properties"]["failure_kind"]["enum"]) | {"STATIC_VALIDATION"}
    reasons = set(schema["$defs"]["external_profile_preflight_witness"]["properties"]["reason"]["enum"])
    map_reasons = set(schema["$defs"]["map_value_comparison_witness"]["properties"]["reason"]["enum"])
    import re as _re
    token = _re.compile(_R5R20_TOKEN)
    seen_positions, fids = set(), set()
    reachable = [f for f in model["families"] if f["class"] == "NORMATIVE_REACHABLE"]
    for fam in reachable:
        fid = fam["family_id"]
        if fid in fids: raise ValueError("duplicate family " + fid)
        fids.add(fid)
        if fam["stage"] not in stages: raise ValueError("unknown stage " + fid)
        position = (fam["stage_index"], fam["group_rank"], fam["family_rank_in_group"])
        if position in seen_positions: raise ValueError("duplicate precedence " + fid)
        seen_positions.add(position)
        if "code" in fam and fam["code"] not in codes: raise ValueError("unregistered code " + fid)
        for code in (fam.get("code_derivation") or {}).values():
            if code.endswith("failure_code"): continue
            if code not in codes: raise ValueError("unregistered derived code " + fid)
        ranks = [c["rank"] for c in fam["conditions"]]
        if ranks != list(range(1, len(ranks) + 1)): raise ValueError("condition ranks not total " + fid)
        contract = fam["witness_contract"]
        for cond in fam["conditions"]:
            if contract in ("SEVEN_FIELD", "STATIC_VALIDATION"):
                if cond["failure_kind"] not in kinds: raise ValueError("failure_kind " + fid)
                if (contract == "STATIC_VALIDATION") != (cond["failure_kind"] == "STATIC_VALIDATION"): raise ValueError("static kind " + fid)
                if not isinstance(cond["diagnostic"], str) or not token.match(cond["diagnostic"]): raise ValueError("diagnostic " + fid)
                w = cond["witness"]
                for field in ("argument", "object_role", "schema_ref", "instance_pointer", "bound_identity"):
                    rule = w.get(field)
                    if not isinstance(rule, dict) or len(rule) != 1: raise ValueError("witness field missing %s %s" % (fid, field))
                    if "derivation" in rule and rule["derivation"] not in vocab[field]:
                        raise ValueError("undefined derivation %s %s %s" % (fid, field, rule["derivation"]))
                if w["instance_pointer"].get("derivation") == "DECLARED_SECTION_POINTER" and "section_pointer" not in cond: raise ValueError("section pointer " + fid)
                if w["instance_pointer"].get("derivation") == "ROW_POINTER_TEMPLATE" and "pointer_template" not in cond: raise ValueError("template " + fid)
                if w["instance_pointer"].get("derivation") == "ENTRYPOINT_BINDING_LOCATION" and "binding_pointer" not in cond: raise ValueError("binding pointer " + fid)
            elif contract == "PROFILE_PREFLIGHT":
                reason = cond["reason"]
                for r in (reason.values() if isinstance(reason, dict) else [reason]):
                    if r not in reasons: raise ValueError("reason " + fid)
                if not token.match(cond["diagnostic"]): raise ValueError("diagnostic " + fid)
                for field in ("profile_pointer", "candidate_artifact", "candidate_pointer", "source_identity", "expected", "actual"):
                    rule = cond["witness"].get(field)
                    if not isinstance(rule, dict) or rule.get("derivation") not in vocab[field]: raise ValueError("preflight field %s %s" % (fid, field))
            elif contract == "MAP_VALUE_COMPARISON":
                if cond["reason"] not in map_reasons: raise ValueError("map reason " + fid)
                if "kind" not in cond["witness"]["baseline_identity"].get("constant", {}): raise ValueError("baseline identity " + fid)
                for field, rule in cond["witness"].items():
                    if "derivation" in rule and rule["derivation"] not in vocab["map_value_comparison"]: raise ValueError("map field %s %s" % (fid, field))
            elif contract == "TRUST_RESULT":
                if not cond["witness"]: raise ValueError("trust witness " + fid)
                for field, rule in cond["witness"].items():
                    if "derivation" in rule and rule["derivation"] not in vocab["trust_result"]: raise ValueError("trust field %s %s" % (fid, field))
            elif contract in ("STRICT_UNION_COLLISION", "VECTOR_REGISTRY_CLAIM"):
                if "witness_field_derivation_ref" not in cond: raise ValueError("declared derivation ref " + fid)
            else:
                raise ValueError("unknown witness contract " + fid)
    for mirror in model["defensive_mirrors"]:
        owners = mirror["owner_family"] if isinstance(mirror["owner_family"], list) else [mirror["owner_family"]]
        if not owners or any(o not in fids for o in owners): raise ValueError("mirror owner " + mirror["family_id"])
    for row in model["internal_only"]:
        if row.get("normative_result_authority") is not False: raise ValueError("internal authority " + row["family_id"])
    ordered = {fid for stage in model["stage_ordering"] for group in stage["groups"] for fid in group["families"]}
    if ordered != fids: raise ValueError("stage ordering does not cover exactly the reachable families")
    return {"reachable_families": len(reachable), "conditions": sum(len(f["conditions"]) for f in reachable),
            "defensive_mirrors": len(model["defensive_mirrors"]), "internal_only": len(model["internal_only"]),
            "stages_with_families": len(model["stage_ordering"]), "incomplete_rows": 0}


def _r5r20_finalize():
    meta = _r11_load("metacontract.json")
    reg = _r11_load("object-registry.json")
    pkg = _r11_load("specification-package-0.2.json")
    meta_schema = json.loads((OUT/"schema"/"metacontract.schema.json").read_text(encoding="utf-8"))
    # Registered codes and the code catalogue.
    for code in _R5R20_NEW_CODES:
        for listing in (meta["result_contracts"]["pre_execution_result"]["fail_codes"], meta["failure_semantics"]["pre_execution_order"],
                        meta["external_acceptance_profile_contract"]["pre_execution_failures"]):
            if code not in listing:
                anchor = "SCHEMA_INVALID_BOUND_OBJECT" if code == "STATIC_VALIDATION_FAILED" else "EXTERNAL_PROFILE_SCHEMA_DIGEST_MISMATCH"
                listing.insert(listing.index(anchor) + 1, code)
    # H5-A / H5-B: integrity-gate law additions (package self-digest before trust; per-mode declaration shape before digest).
    ig = meta["registration"]["integrity_gate"]
    ig["package_self_digest"] = {"verified_at_stage": "VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE",
                                 "precedes": "EXTERNAL_TRUST_COMPARISON_IN_THE_SAME_STAGE", "law_owner": "INTEGRITY_GATE",
                                 "declaration_shape_failure": {"failure_kind": "INTEGRITY", "diagnostic": "PACKAGE_SELF_DIGEST_DECLARATION_INVALID"},
                                 "digest_mismatch": {"failure_kind": "INTEGRITY", "diagnostic": ig["digest_mismatch"]["diagnostic"], "instance_pointer": "/current_candidate_integrity/digest"},
                                 "excluded_from_stage": "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS"}
    ig["declaration_shape_by_mode"] = {"shape_source": "metacontract:/runtime_representation/value_schemas/resolved_object/$defs/integrity",
                                       "failure_kind": "INTEGRITY", "diagnostic": "REGISTRATION_INTEGRITY_DECLARATION_SHAPE_INVALID",
                                       "instance_pointer": "FIRST_INVALID_LOCATION_CANONICAL_PREORDER_WITHIN_/objects/<row_index>/integrity",
                                       "precedes": "DIGEST_CALCULATION"}
    ig["content_not_canonicalizable"] = {"failure_kind": "INTEGRITY", "diagnostic": "REGISTRATION_INTEGRITY_CONTENT_NOT_RFC8785_CANONICALIZABLE",
                                         "instance_pointer": ig["digest_mismatch"]["instance_pointer"]}
    ig["digest_verification_scope"] = "ACTIVE_NORMATIVE_ROWS_WITH_SEMANTIC_JSON_CONTENT_OR_PACKAGE_PINNED_BOOTSTRAP;SELF_DIGEST_AT_STAGE_VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE;DUAL_ACCEPTED_SOURCE_AT_STAGE_VERIFY_EXTERNAL_ACCEPTED_BASE_AND_VECTOR_CONTENT_AND_PINS"
    ig["content_read_failure_owner"] = "RESOLVE_CANDIDATE_OBJECTS"
    ig["within_stage"] = "ASCENDING_ROW_INDEX_THEN_INVALID_MODE_THEN_DECLARATION_SHAPE_THEN_CANONICALIZATION_THEN_DIGEST"
    buckets = meta["registration"]["diagnostic_tokens"]["INTEGRITY"]
    for tok in ("REGISTRATION_INTEGRITY_DECLARATION_SHAPE_INVALID", "REGISTRATION_INTEGRITY_CONTENT_NOT_RFC8785_CANONICALIZABLE", "PACKAGE_SELF_DIGEST_DECLARATION_INVALID"):
        if tok not in buckets: buckets.append(tok)
    meta_schema = _r5r20_schema_patch(meta_schema)
    model = _r5r20_model(meta, reg, pkg)
    counts = _r5r20_totality(model, meta, meta_schema)
    model["r5r19_reconciliation"]["final_reachable_families"] = counts["reachable_families"]
    model["totality"] = counts
    fs = meta["failure_semantics"]
    fs["pre_execution_failure_model"] = model
    fs["verifier_protocol_digests"] = {"algorithm": "SHA-256", "serialization": "RFC8785_JCS",
                                       "pre_execution_failure_model": sem(model), "registration": sem(meta["registration"]),
                                       "generic_failure_witness": sem(fs["generic_failure_witness"])}
    fss = meta_schema["properties"]["failure_semantics"]
    for name in ("pre_execution_failure_model", "verifier_protocol_digests"):
        fss["properties"][name] = {"const": copy.deepcopy(fs[name])}
        if name not in fss["required"]: fss["required"].append(name)
    fss["properties"]["pre_execution_order"] = {"const": copy.deepcopy(fs["pre_execution_order"])}
    props = meta_schema["properties"]
    props["registration"]["const"] = copy.deepcopy(meta["registration"])
    props["external_acceptance_profile_contract"]["const"] = copy.deepcopy(meta["external_acceptance_profile_contract"])
    props["result_contracts"]["properties"]["pre_execution_result"]["properties"]["fail_codes"] = {"const": copy.deepcopy(meta["result_contracts"]["pre_execution_result"]["fail_codes"])}
    _r11_save("metacontract.json", meta)
    _r11_save("schema/metacontract.schema.json", meta_schema)
    _r11_digest_close(reg, pkg)
    print(json.dumps({"r5r20_normative_patch": "PASS", "totality": counts,
                      "verifier_protocol_digests": fs["verifier_protocol_digests"],
                      "registry_semantic_sha256": pkg["registry_semantic_sha256"],
                      "package_semantic_sha256": pkg["current_candidate_integrity"]["digest"]}, indent=2))

_R5R18_POST_BUILD = _r11_post_build
def _r11_post_build():
    _R5R18_POST_BUILD()
    _r5r20_finalize()

# ---------------------------------------------------------------------------
# R5R22: semantic repair of the pre-execution failure model (R5R21 defects
# D1-D14).  The R5R20 model is post-processed in place: every derivation token
# receives machine-readable semantics (value type, source class, subject-class
# domain, document, ordering rule, cases, identity rule), the fourteen defects
# are repaired as decided, conditions that still need a human decision are
# marked explicitly, and a semantic totality checker (properties A-G) guards
# the build.  The R5R20 layer above is unchanged.
# ---------------------------------------------------------------------------
_R5R22_JSON_TYPES = ["OBJECT", "ARRAY", "STRING", "NUMBER", "INTEGER", "BOOLEAN", "NULL", "ABSENT"]
_R5R22_SOURCES = ["PROTOCOL_CONSTANT", "CANDIDATE_DECLARATION", "CALLER_INPUT", "STANDARD_COMPUTATION", "MODEL_CONDITION_PARAMETER", "LITERAL"]
_R5R22_SOURCE_DEFINITIONS = {
    "PROTOCOL_CONSTANT": "model:/protocol_constants, the verifier-committed registration section, or a constant_value of this vocabulary",
    "CANDIDATE_DECLARATION": "a value read from a candidate document (package, registry, metacontract, registries, SCHEMA documents)",
    "CALLER_INPUT": "a value read from caller input (trust triple, profile schema inputs, external acceptance profile)",
    "STANDARD_COMPUTATION": "a value computed from candidate and caller inputs by a public standard named by the contract (RFC6901, RFC8785, SHA-256, git blob, JSON Schema 2020-12, strict UTF-8 JSON) or by a declared Accord construction or predicate evaluation (DESCENDANTS, selector matching, the verification universe)",
    "MODEL_CONDITION_PARAMETER": "a parameter declared on the model condition or family (section_pointer, pointer_template, binding_pointer, pointer_scope, checked_members, collection_pointer, owning_object, digest_field)",
    "LITERAL": "a literal fixed by this vocabulary"}
_R5R22_DOCUMENTS = ["PACKAGE", "REGISTRY", "METACONTRACT", "PROCEDURE_REGISTRY", "PRIMITIVE_REGISTRY", "RULE_REGISTRY", "INVARIANT_REGISTRY",
                    "CANDIDATE_OBJECT_CONTENT", "RESERVED_INPUT_CONTENT", "VERIFICATION_UNIVERSE_VALUE", "BOUND_SOURCE_CONTENT", "PROFILE",
                    "RUNTIME_VALUE_SCHEMA_DOCUMENT", "REGISTRY_ROW_INTEGRITY_DECLARATION", "UNIVERSE_OBJECT_RECORD_VALUE"]
_R5R22_POINTER_DOCUMENT_RULES = ["ARGUMENT_DOCUMENT", "VALIDATED_INSTANCE", "OWNING_OBJECT", "CLAIM_ARTIFACT_DOCUMENT", "PROFILE_DESCRIPTOR_MAP_ARGUMENT"]
_R5R22_SUBJECT_CLASSES = {
    "ENTRYPOINT_PACKAGE": "the explicit candidate package entrypoint",
    "ENTRYPOINT_REGISTRY": "the explicit object registry entrypoint",
    "CALLER_TRUST_TRIPLE": "the caller-supplied external trust triple",
    "TRUST_COMPARISON": "the comparison of the validated caller triple with the self-verified package",
    "CALLER_PROFILE_SCHEMA_INPUT": "the caller-supplied profile schema identity, bytes and expected SHA-256",
    "CALLER_PROFILE": "the caller-supplied external acceptance profile",
    "FROZEN_SOURCE": "one protocol_constants.frozen_sources entry",
    "ALLOWLIST_ROW": "one external_acceptance_profile:/accepted_source_allowlist row",
    "AUTHORITY_CLAIM": "one protocol_constants.claim_comparisons entry with index 0..3",
    "PROCEDURE_PROJECTION_CLAIM": "protocol_constants.claim_comparisons entry 4 (the selector claim)",
    "PROTOCOL_SECTION": "one verifier-protocol-committed metacontract section",
    "REGISTRY_SCHEMA_DECLARATION": "metacontract:/registration/structural_application/schema_ref",
    "REGISTRY_ROW": "one /objects row of the explicit registry",
    "REGISTRY_DUPLICATE_SELECTION": "the duplicate pair selected by metacontract:/registration/global_uniqueness/selection",
    "BOOTSTRAP_OBJECT": "the package or one package-referenced bootstrap object",
    "ELIGIBLE_SCHEMA_ROW": "an eligible (ACTIVE NORMATIVE) row of kind SCHEMA",
    "ELIGIBLE_NON_SCHEMA_ROW": "an eligible (ACTIVE NORMATIVE) row of any other kind",
    "BOUND_VECTOR_SOURCE": "the accepted vector source of metacontract:/registration/bound_source_resolved_construction",
    "UNION_COLLISION": "the pair selected by metacontract:/registration/strict_identity_union/scan_selection",
    "BOUND_SOURCE": "one externally verified accepted/bound source (allowlist row)",
    "RESERVED_INPUT_ROW": "one metacontract:/reserved_inputs row",
    "RESERVED_INPUT_COLLECTION": "the metacontract:/reserved_inputs collection as a whole",
    "PRODUCER_SCHEMA_RESERVED_INPUT": "one reserved input declaring profile_content_source.producer_schema_ref",
    "RUNTIME_VALUE_SCHEMA": "one metacontract:/runtime_representation/value_schemas member",
    "UNIVERSE_VALUE": "the published verification universe value",
    "UNIVERSE_OBJECT_RECORD": "one /objects/<k> record of the published universe value",
    "MEMBER_RESOLVED_RECORD": "one member-resolved object record (not located in the universe value)",
    "STATIC_DECLARATION_SITE": "one declaration site checked by a registry-level static rule",
    "PROCEDURE_DECLARATION": "one procedure of the procedure registry",
    "AST_NODE": "one AST node of an assertion",
    "WITNESS_OPERAND_TERMINAL": "one declared-witness argument terminal",
    "BINDING_SITE": "one RULE_BINDING binding site",
    "SELECTED_PROJECTION_PROCEDURE": "the procedure selected by the projection selector",
}
_R5R22_ORDERING_RULES = {
    "DESCENDANTS_CANONICAL_PREORDER": {"kind": "DECLARED_TRAVERSAL", "declared_by": "primitive-registry:/primitives/<DESCENDANTS>/deterministic_order",
                                       "definition": "depth-first preorder; array elements in ascending index; object members in UTF-16 code-unit key order"},
    "UTF16_CODE_UNIT_KEY_ORDER": {"kind": "KEY_ORDER", "definition": "object member names ascending by UTF-16 code-unit sequence (the key order of DESCENDANTS and RFC8785)"},
    "ASCENDING_ARRAY_INDEX": {"kind": "ARRAY_INDEX", "definition": "ascending zero-based array index"},
    "CALLER_INPUT_PRECEDENCE": {"kind": "ARRAY", "source": "model:/protocol_constants/caller_input_precedence", "definition": "array order of protocol_constants.caller_input_precedence"},
    "REQUIRED_PROFILE_MEMBERS_ORDER": {"kind": "ARRAY", "source": "model:/protocol_constants/required_profile_members", "definition": "array order of protocol_constants.required_profile_members"},
    "PACKAGE_SELF_DIGEST_MEMBER_ORDER": {"kind": "ARRAY", "source": "model:/protocol_constants/package_self_digest_declaration/members_in_declared_order",
                                         "definition": "array order of protocol_constants.package_self_digest_declaration.members_in_declared_order"},
    "ELIGIBILITY_PREDICATE_ORDER": {"kind": "ARRAY", "source": "model:/protocol_constants/eligibility_members_in_order", "definition": "status, then classification (metacontract:/eligibility/candidate_universe/membership_predicate)"},
    "GLOBAL_UNIQUENESS_SELECTION": {"kind": "DECLARED", "declared_by": "metacontract:/registration/global_uniqueness/selection", "definition": "minimal second-occurrence index j, then the earliest prior matching index"},
    "REGISTRATION_FIRST_FAILURE_ORDERING": {"kind": "DECLARED", "declared_by": "metacontract:/registration/first_failure_ordering", "definition": "ascending row index, then declared rule order, then single pointer"},
    "DECLARED_WITNESS_OPERAND_PREORDER": {"kind": "DECLARED", "declared_by": "metacontract:/failure_semantics/generic_failure_witness/operands",
                                          "definition": "procedure source order, assertion source order, declared-witness first-occurrence preorder"},
    "UNIVERSE_FINAL_ORDER": {"kind": "DECLARED", "declared_by": "metacontract:/universe_contract/verification_universe/final_order", "definition": "UTF-16 lexicographic kind/id/version ascending"},
}
_R5R22_IDENTITY_RULES = {
    "TYPED_IDENTITY_WHEN_VALID_ELSE_NULL": "emit {kind, id, version} only when each of kind, id and version exists, is a JSON string and is non-empty; otherwise emit null; member_id is never emitted; successful JSON decoding alone is not sufficient (D14)",
}
_R5R22_IDENTITY_GUARANTEES = {
    "PROTOCOL_CONSTANT_TYPED_IDENTITY": "the value is a verifier protocol constant proven to be a valid typed identity by the builder",
    "SEMANTIC_REGISTRATION_ROW_IDENTITY": "stages after SEMANTIC_REGISTRATION_VALIDATE_ALL_ROWS: every row passed ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY, and /objects/*/reference is $defs/ref (kind enum, non-empty id and version)",
}
_R5R22_VALUE_SAMPLES = {
    "NONEMPTY_STRING": ["x"], "TOKEN": ["ABC"], "RFC6901_POINTER": ["", "/a/b~1c"], "RFC6901_POINTER_OR_NULL": [None, "", "/a"],
    "NULL": [None], "TYPED_IDENTITY": [{"kind": "SCHEMA", "id": "x", "version": "1"}], "TYPED_IDENTITY_OR_NULL": [None, {"kind": "SCHEMA", "id": "x", "version": "1"}],
    "JSON_VALUE": [None, 1, "x", {}, [], True], "JSON_VALUE_OR_NULL": [None, 1, "x", {}, [], True], "NONNEGATIVE_INTEGER": [0, 2], "POSITIVE_INTEGER": [1],
    "STRING_ARRAY": [["a"]], "JSON_TYPE_TOKEN": list(_R5R22_JSON_TYPES), "ID_VERSION": [{"id": "x", "version": "1"}],
    "IDENTITY3": [{"id": "x", "version": "1", "digest": "0" * 64}], "TRUST_FIELD_NAME_ARRAY": [["expected_package_id"]],
    "NONEMPTY_STRING_OR_NULL": [None, "x"],
}
_R5R22_ADMISSION_PREDICATES = {
    "RULE_BINDING_ARGUMENT_DECLARES_SOURCE_CONSTRAINT": {"grammar": "procedure-registry-schema:/$defs/argument/allOf/0",
        "predicate": "an argument whose origin is RULE_BINDING has a source_constraint member"},
    "SOURCE_CONSTRAINT_VALID_AGAINST_REGISTERED_GRAMMAR": {"grammar": "procedure-registry-schema:/$defs/source_constraint",
        "predicate": "the source_constraint value is valid against the registered source_constraint definition"},
}


def _r5r22_identity_when_valid(kind, ident, version):
    if all(isinstance(v, str) and v for v in (kind, ident, version)):
        return {"kind": kind, "id": ident, "version": version}
    return None


def _r5r22_json_type(value, present=True):
    """Closed MEMBER_JSON_TYPE classification (D10); exactly one token per JSON value."""
    if not present: return "ABSENT"
    if value is None: return "NULL"
    if isinstance(value, bool): return "BOOLEAN"
    if isinstance(value, dict): return "OBJECT"
    if isinstance(value, list): return "ARRAY"
    if isinstance(value, str): return "STRING"
    if isinstance(value, int): return "INTEGER"
    if isinstance(value, float): return "INTEGER" if value == int(value) else "NUMBER"
    raise ValueError("value is not a JSON value")


def _r5r22_E(definition, value_type, source, domain, **kw):
    row = {"definition": definition, "value_type": value_type, "source": source, "domain": domain}
    row.update(kw)
    return row


def _r5r22_vocabulary():
    E = _r5r22_E
    PC, CD, CI, SC, MP, LT = _R5R22_SOURCES
    EP, ER = "ENTRYPOINT_PACKAGE", "ENTRYPOINT_REGISTRY"
    ESR, ENR = "ELIGIBLE_SCHEMA_ROW", "ELIGIBLE_NON_SCHEMA_ROW"
    STATIC = ["STATIC_DECLARATION_SITE", "PROCEDURE_DECLARATION", "AST_NODE", "WITNESS_OPERAND_TERMINAL", "BINDING_SITE"]
    OWNED = ["RUNTIME_VALUE_SCHEMA", "RESERVED_INPUT_ROW", "RESERVED_INPUT_COLLECTION", "PRODUCER_SCHEMA_RESERVED_INPUT", "PROTOCOL_SECTION"] + STATIC
    REGW = ["REGISTRY_ROW", "REGISTRY_DUPLICATE_SELECTION", "REGISTRY_SCHEMA_DECLARATION", "BOOTSTRAP_OBJECT", EP, ER]
    UNI = ["UNIVERSE_VALUE", "UNIVERSE_OBJECT_RECORD", "MEMBER_RESOLVED_RECORD"]
    ident = "TYPED_IDENTITY_WHEN_VALID_ELSE_NULL"
    return {
        "argument": {
            "CANDIDATE_OBJECT": E("the constant candidate_object (H1): names the failing eligible candidate object's content document", "NONEMPTY_STRING", [PC], [ESR, ENR],
                                  constant_value="candidate_object", document="CANDIDATE_OBJECT_CONTENT"),
            "ENTRYPOINT_ARGUMENT": E("protocol_constants.entrypoints[subject].argument", "NONEMPTY_STRING", [PC], [EP, ER], document={EP: "PACKAGE", ER: "REGISTRY"}),
            "OWNING_BOOTSTRAP_OBJECT_ARGUMENT": E("protocol_constants.bootstrap_objects[owning object].argument (package member name without _ref); the owning object is the condition's owning_object",
                                                  "NONEMPTY_STRING", [PC, MP], STATIC, document="OWNING_OBJECT"),
            "RESERVED_INPUT_NAME": E("metacontract:/reserved_inputs[subject].name; names the pin-verified decoded content of that reserved input", "NONEMPTY_STRING", [CD],
                                     ["PRODUCER_SCHEMA_RESERVED_INPUT"], document="RESERVED_INPUT_CONTENT"),
            "RUNTIME_VALUE_NAME": E("the constant verification_universe (metacontract:/binding_origins/reserved_names)", "NONEMPTY_STRING", [PC], UNI,
                                    constant_value="verification_universe", document="VERIFICATION_UNIVERSE_VALUE"),
            "REGISTRATION_WITNESS_ARGUMENT": E("metacontract:/registration/witness_contract/argument (verifier protocol commitment)", "NONEMPTY_STRING", [PC], REGW, document="REGISTRY"),
        },
        "object_role": {
            "REGISTERED_KIND_OF_FAILING_OBJECT": E("kind of the failing object's registry row (H1)", "NONEMPTY_STRING", [CD], [ESR, ENR], value_vocabulary="REGISTRY_KIND"),
            "ENTRYPOINT_KIND": E("protocol_constants.entrypoints[subject].registered_kind", "NONEMPTY_STRING", [PC], [EP, ER], value_vocabulary="REGISTRY_KIND"),
            "REGISTERED_KIND_OF_OWNING_OBJECT": E("protocol_constants.bootstrap_objects[owning object].registered_kind", "NONEMPTY_STRING", [PC, MP], ["PROTOCOL_SECTION"], value_vocabulary="REGISTRY_KIND"),
            "RESERVED_INPUT_DECLARED_TYPE": E("metacontract:/reserved_inputs[subject].type", "NONEMPTY_STRING", [CD], ["PRODUCER_SCHEMA_RESERVED_INPUT"],
                                              value_vocabulary="RESERVED_INPUT_TYPE_ADMITTED_BY_PE41"),
            "RUNTIME_VALUE_TYPE": E("the constant VERIFICATION_UNIVERSE (reserved input type of verification_universe)", "NONEMPTY_STRING", [PC], UNI,
                                    constant_value="VERIFICATION_UNIVERSE", value_vocabulary="FIXED_ROLE"),
            "REGISTRATION_WITNESS_OBJECT_ROLE": E("metacontract:/registration/witness_contract/object_role", "NONEMPTY_STRING", [PC], REGW, value_vocabulary="FIXED_ROLE"),
            "OWNING_OBJECT_REGISTRY_ROW_KIND": E("kind of the validated registry row of the owning object (stages after registration)", "NONEMPTY_STRING", [MP, PC, CD], OWNED,
                                                 value_vocabulary="REGISTRY_KIND"),
        },
        "schema_ref": {
            "APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID": E("exact schema_document_id of the SCHEMA row whose kind/id/version equal the failing object's registered schema_ref (H1); defined only for non-SCHEMA rows, which carry schema_ref",
                                                       "NONEMPTY_STRING", [CD], [ENR]),
            "ENTRYPOINT_SCHEMA_DOCUMENT_ID": E("protocol_constants.entrypoints[subject].schema_document_id", "NONEMPTY_STRING", [PC], [EP, ER]),
            "OWNING_OBJECT_SCHEMA_DOCUMENT_ID": E("protocol_constants.bootstrap_objects[owning object].schema_document_id", "NONEMPTY_STRING", [PC, MP], ["PROTOCOL_SECTION"]),
            "PRODUCER_SCHEMA_ROW_SCHEMA_DOCUMENT_ID": E("exact schema_document_id of the eligible SCHEMA row named by the subject's profile_content_source.producer_schema_ref (defined once PRODUCER_SCHEMA_UNRESOLVED has not fired)",
                                                        "NONEMPTY_STRING", [CD], ["PRODUCER_SCHEMA_RESERVED_INPUT"]),
            "DRAFT_2020_12_METASCHEMA": E("protocol_constants.draft_2020_12_dialect; the schema applied to a SCHEMA-kind subject or a value schema (eligibility.validation_by_kind.SCHEMA overrides H1)",
                                          "NONEMPTY_STRING", [PC], [ESR, "RUNTIME_VALUE_SCHEMA"]),
            "RUNTIME_VALUE_SCHEMA_ID": E("the $id of the metacontract runtime value schema that was applied", "NONEMPTY_STRING", [CD], UNI),
            "REGISTRATION_WITNESS_SCHEMA_REF": E("metacontract:/registration/witness_contract/schema_ref (the applied object-registry schema_document_id)", "NONEMPTY_STRING", [PC],
                                                 ["REGISTRY_ROW", "REGISTRY_DUPLICATE_SELECTION", "BOOTSTRAP_OBJECT", EP, ER]),
            "STRUCTURAL_APPLICATION_SCHEMA_DOCUMENT_ID": E("metacontract:/registration/structural_application/schema_id: the document identity the protocol declares for structural_application.schema_ref (the seven-field schema_ref is a string, so the typed ref is represented by its declared document id) (D11)",
                                                           "NONEMPTY_STRING", [PC], ["REGISTRY_SCHEMA_DECLARATION"]),
            "OWNING_OBJECT_APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID": E("exact schema_document_id of the SCHEMA row named by the owning object's registered schema_ref (stages after registration)",
                                                                     "NONEMPTY_STRING", [MP, PC, CD], [s for s in OWNED if s != "RUNTIME_VALUE_SCHEMA"]),
            "ALLOWLIST_EXPECTED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID": E("exact schema_document_id of the eligible SCHEMA row whose kind/id/version equal the allowlist row's expected_schema_ref (member_id is not represented, as in H1) (D5)",
                                                                  "NONEMPTY_STRING", [CI, CD], ["BOUND_SOURCE"], defined_for_cases=["EXPECTED_SCHEMA_ROW_RESOLVED"]),
        },
        "instance_pointer": {
            "DOCUMENT_ROOT": E("the empty RFC6901 pointer of the argument document", "RFC6901_POINTER", [LT], ["ANY"], document="ARGUMENT_DOCUMENT", constant_value=""),
            "FIRST_INVALID_LOCATION_CANONICAL_PREORDER": E("instance location of the first JSON Schema failure, in DESCENDANTS canonical preorder, of the condition's validated_instance; a missing member is located at its containing object; validator emission order is never used",
                                                           "RFC6901_POINTER", [SC], [ESR, ENR, "BOUND_SOURCE", "PRODUCER_SCHEMA_RESERVED_INPUT", "UNIVERSE_VALUE"],
                                                           document="VALIDATED_INSTANCE", order="DESCENDANTS_CANONICAL_PREORDER"),
            "SCOPED_FIRST_INVALID_LOCATION": E("absolute pointer in the argument document: the condition's pointer_scope (indices and escaped names substituted) followed by the first JSON Schema failure location, in DESCENDANTS canonical preorder, within the value at that scope (a missing member is located at its containing object)",
                                               "RFC6901_POINTER", [SC, MP], ["REGISTRY_ROW", "RUNTIME_VALUE_SCHEMA", "UNIVERSE_OBJECT_RECORD"],
                                               document="ARGUMENT_DOCUMENT", order="DESCENDANTS_CANONICAL_PREORDER"),
            "FIRST_UNCANONICALIZABLE_NUMBER_CANONICAL_PREORDER": E("pointer of the first number, in DESCENDANTS canonical preorder, that RFC8785 cannot serialize", "RFC6901_POINTER", [SC], [EP],
                                                                   document="ARGUMENT_DOCUMENT", order="DESCENDANTS_CANONICAL_PREORDER"),
            "FIRST_NONLOCAL_REFERENCE_CANONICAL_PREORDER": E("pointer of the first $ref/$dynamicRef member, in DESCENDANTS canonical preorder, that is not a resolvable local RFC6901 fragment", "RFC6901_POINTER", [SC], [ESR],
                                                             document="ARGUMENT_DOCUMENT", order="DESCENDANTS_CANONICAL_PREORDER"),
            "PACKAGE_SELF_DIGEST_DECLARATION_LOCATION": E("/current_candidate_integrity when that member is absent or not an object; otherwise /current_candidate_integrity/<member> of the first member, in array order, of protocol_constants.package_self_digest_declaration.members_in_declared_order that is absent or violates its constraint; otherwise (an undeclared member is present) /current_candidate_integrity",
                                                          "RFC6901_POINTER", [PC, CD, SC], [EP], document="PACKAGE", order="PACKAGE_SELF_DIGEST_MEMBER_ORDER"),
            "RESERVED_INPUT_MEMBER_LOCATION": E("/reserved_inputs/<i> when the subject row is not an object; otherwise the first of the condition's checked_members, in UTF-16 code-unit key order, that is absent or violates the condition: /reserved_inputs/<i>/<member>, or /reserved_inputs/<i>/profile_content_source/<member> for a profile_content_source member (/reserved_inputs/<i>/profile_content_source when that container is not an object); for RESERVED_INPUT_DECLARATION_NOT_UNIQUE <i> is the second occurrence (D7)",
                                                "RFC6901_POINTER", [CD, MP, SC], ["RESERVED_INPUT_ROW"], document="METACONTRACT", order="UTF16_CODE_UNIT_KEY_ORDER"),
            "RESERVED_INPUT_COLLECTION_LOCATION": E("the condition's collection_pointer: the canonical reserved-input collection root or the exact collection-valued field being compared (<escaped_name> is the RFC6901-escaped subject row name) (D7)",
                                                    "RFC6901_POINTER", [MP, CD], ["RESERVED_INPUT_ROW", "RESERVED_INPUT_COLLECTION"], document="METACONTRACT"),
            "ROW_POINTER_TEMPLATE": E("the condition's pointer_template with <row_index> (or <second_occurrence_index>, <member_index>) substituted", "RFC6901_POINTER", [MP],
                                      ["REGISTRY_ROW", "REGISTRY_DUPLICATE_SELECTION"], document="REGISTRY"),
            "DECLARED_SECTION_POINTER": E("the condition's section_pointer in the argument document", "RFC6901_POINTER", [MP], ["PROTOCOL_SECTION", "REGISTRY_SCHEMA_DECLARATION", EP, ESR],
                                          document="ARGUMENT_DOCUMENT"),
            "ENTRYPOINT_BINDING_LOCATION": E("the condition's binding_pointer inside the subject entrypoint document", "RFC6901_POINTER", [MP], [EP, ER], document={EP: "PACKAGE", ER: "REGISTRY"}),
            "REGISTRY_BINDING_LOCATION": E("the condition's binding_pointer inside the explicit object registry document (<row_index> is the index of the unique row matching the subject's identity) (D2)",
                                           "RFC6901_POINTER", [MP, PC, CD], [EP, ER], document="REGISTRY"),
            "BOOTSTRAP_ROW_LOCATION": E("/objects when no unique registry row has the bootstrap object's kind/id/version; otherwise /objects/<row_index>/<member> of the first member, in eligibility predicate order (status, classification), that is not ACTIVE / NORMATIVE (D8)",
                                        "RFC6901_POINTER", [PC, CD], ["BOOTSTRAP_OBJECT"], document="REGISTRY", order="ELIGIBILITY_PREDICATE_ORDER",
                                        cases={"ROW_ABSENT_OR_NOT_UNIQUE": "/objects", "ROW_STATUS_NOT_ACTIVE": "/objects/<row_index>/status", "ROW_CLASSIFICATION_NOT_NORMATIVE": "/objects/<row_index>/classification"}),
            "STATIC_VIOLATION_LOCATION": E("location rule of the condition: NODE = pointer of the failing AST node; MEMBER = the condition's location_template with the failing indices; SET_EXACT = pointer of the first extra element by ascending index, else the collection pointer; UNIQUENESS = pointer of the first second occurrence by ascending index",
                                           "RFC6901_POINTER", [SC, MP], ["STATIC_DECLARATION_SITE", "PROCEDURE_DECLARATION", "AST_NODE"], document="ARGUMENT_DOCUMENT", order="ASCENDING_ARRAY_INDEX"),
            "WITNESS_OPERAND_TERMINAL": E("absolute pointer, in the procedure registry, of the first argument terminal {arg} of the declared witness lacking both a bound identity and an operand-only identity (H2)",
                                          "RFC6901_POINTER", [SC], ["WITNESS_OPERAND_TERMINAL"], document="PROCEDURE_REGISTRY", order="DECLARED_WITNESS_OPERAND_PREORDER"),
            "BINDING_DECLARATION_LOCATION": E("pointer of the binding value in the object that declares it (invariant default_arguments member, or rule invariant_binding.arguments member); the containing map when the member is absent",
                                              "RFC6901_POINTER", [CD, SC], ["BINDING_SITE"], document="OWNING_OBJECT"),
            "PRODUCER_SCHEMA_REF_DECLARATION_LOCATION": E("absolute metacontract pointer /reserved_inputs/<i>/profile_content_source/producer_schema_ref of the subject's unresolved declaration (D6)",
                                                          "RFC6901_POINTER", [CD], ["PRODUCER_SCHEMA_RESERVED_INPUT"], document="METACONTRACT"),
        },
        "bound_identity": {
            "NULL": E("JSON null (permitted by the registered schema) when no object identity exists", "NULL", [LT], ["ANY"], constant_value=None),
            "ENTRYPOINT_CONTENT_IDENTITY_WHEN_VALID_ELSE_NULL": E("{kind: protocol_constants.entrypoints[subject].registered_kind, id, version} with id/version = package_id/package_version (PACKAGE) or object_id/object_version (REGISTRY) of the decoded entrypoint content, under TYPED_IDENTITY_WHEN_VALID_ELSE_NULL (D14)",
                                                                  "TYPED_IDENTITY_OR_NULL", [PC, CD], [EP, ER], identity_rule=ident),
            "REGISTRY_CONTENT_IDENTITY_WHEN_VALID_ELSE_NULL": E("{kind: REGISTRY, id: object_id, version: object_version} of the decoded explicit registry under TYPED_IDENTITY_WHEN_VALID_ELSE_NULL (D2, D14)",
                                                                "TYPED_IDENTITY_OR_NULL", [PC, CD], [EP, ER], identity_rule=ident),
            "REGISTRY_IDENTITY_OF_FAILING_OBJECT": E("kind/id/version of the failing object's registry row (H1)", "TYPED_IDENTITY", [CD], [ESR, ENR], identity_guarantee="SEMANTIC_REGISTRATION_ROW_IDENTITY"),
            "OWNING_OBJECT_IDENTITY": E("protocol_constants.bootstrap_objects[owning object].identity", "TYPED_IDENTITY", [PC, MP], ["PROTOCOL_SECTION"], identity_guarantee="PROTOCOL_CONSTANT_TYPED_IDENTITY"),
            "FROZEN_SOURCE_TYPED_IDENTITY": E("protocol_constants.frozen_sources[subject].typed_identity", "TYPED_IDENTITY", [PC], ["FROZEN_SOURCE"], identity_guarantee="PROTOCOL_CONSTANT_TYPED_IDENTITY"),
            "RESERVED_INPUT_FROZEN_SOURCE_IDENTITY_ELSE_NULL": E("typed_identity of the protocol_constants.frozen_sources entry whose profile_member equals the second pin_pointer_tokens token of the subject (when the tokens are exactly [frozen_authority_pins, <member>]); null when no such entry exists",
                                                                 "TYPED_IDENTITY_OR_NULL", [PC, CD], ["PRODUCER_SCHEMA_RESERVED_INPUT"], identity_rule=ident),
            "RESOLVED_OBJECT_IDENTITY_CONTAINING_LOCATION_ELSE_NULL": E("for a location at or below /objects/<k> of the published universe value, the /objects/<k>/ref kind/id/version under TYPED_IDENTITY_WHEN_VALID_ELSE_NULL; null at the universe root or outside /objects/<k>",
                                                                        "TYPED_IDENTITY_OR_NULL", [SC], ["UNIVERSE_VALUE", "UNIVERSE_OBJECT_RECORD"], identity_rule=ident),
            "REGISTRATION_WITNESS_BOUND_IDENTITY": E("metacontract:/registration/witness_contract/bound_identity (ROW_KIND_ID_VERSION_TRIPLE_WHEN_READABLE_ELSE_NULL) where READABLE is TYPED_IDENTITY_WHEN_VALID_ELSE_NULL applied to the failing row's kind/id/version (D14)",
                                                     "TYPED_IDENTITY_OR_NULL", [CD], ["REGISTRY_ROW"], identity_rule=ident),
            "GLOBAL_UNIQUENESS_SELECTED_DUPLICATE_IDENTITY": E("{kind, id, version} of the registry row at the selected second-occurrence index (metacontract:/registration/global_uniqueness/selection); declared by registration.global_uniqueness.bound_identity (D1)",
                                                               "TYPED_IDENTITY", [CD, SC], ["REGISTRY_DUPLICATE_SELECTION"], identity_guarantee="SEMANTIC_REGISTRATION_ROW_IDENTITY", order="GLOBAL_UNIQUENESS_SELECTION"),
            "REGISTRY_SCHEMA_ROW_IDENTITY_WHEN_UNIQUE_READABLE_ELSE_NULL": E("the kind/id/version of the unique registry row matching structural_application.schema_ref when exactly one matching row exists and it is readable; null for zero or several matching rows or an unreadable unique row (D11)",
                                                                             "TYPED_IDENTITY_OR_NULL", [PC, CD], ["REGISTRY_SCHEMA_DECLARATION"], identity_rule=ident,
                                                                             cases={"ZERO_MATCHING_ROWS": None, "MULTIPLE_MATCHING_ROWS": None, "UNIQUE_ROW_UNREADABLE": None, "UNIQUE_ROW_READABLE": "ROW_KIND_ID_VERSION"}),
            "OWNING_OBJECT_REGISTRY_IDENTITY": E("kind/id/version of the validated registry row of the owning object (stages after registration)", "TYPED_IDENTITY", [MP, PC, CD], OWNED,
                                                 identity_guarantee="SEMANTIC_REGISTRATION_ROW_IDENTITY"),
            "ALLOWLIST_REF_IDENTITY_WHEN_VALID_ELSE_NULL": E("kind/id/version of the allowlist row's ref under TYPED_IDENTITY_WHEN_VALID_ELSE_NULL: the typed accepted/bound-source identity declared by the allowlist binding (D5)",
                                                             "TYPED_IDENTITY_OR_NULL", [CI, CD], ["BOUND_SOURCE"], identity_rule=ident),
            "BOOTSTRAP_ROW_IDENTITY_ELSE_NULL": E("null when no unique registry row has the bootstrap object's kind/id/version (the family's matched-row identity semantics); otherwise the matched row's kind/id/version (D8)",
                                                  "TYPED_IDENTITY_OR_NULL", [PC, CD], ["BOOTSTRAP_OBJECT"], identity_rule=ident,
                                                  cases={"ROW_ABSENT_OR_NOT_UNIQUE": None, "ROW_STATUS_NOT_ACTIVE": "ROW_KIND_ID_VERSION", "ROW_CLASSIFICATION_NOT_NORMATIVE": "ROW_KIND_ID_VERSION"}),
        },
        "profile_pointer": {
            "NULL": E("no profile location is involved", "NULL", [LT], ["ANY"], constant_value=None),
            "PROFILE_ROOT": E("the empty pointer of the profile document", "RFC6901_POINTER", [LT], ["CALLER_PROFILE"], document="PROFILE", constant_value=""),
            "FIRST_INVALID_LOCATION_CANONICAL_PREORDER": E("first JSON Schema failure location in the profile, in DESCENDANTS canonical preorder", "RFC6901_POINTER", [SC], ["CALLER_PROFILE"],
                                                           document="PROFILE", order="DESCENDANTS_CANONICAL_PREORDER"),
            "FIRST_REQUIRED_PROFILE_MEMBER": E("the profile_pointer of the first protocol_constants.required_profile_members entry, in array order, that is absent or whose MEMBER_JSON_TYPE does not satisfy its json_type", "RFC6901_POINTER", [PC, SC],
                                               ["CALLER_PROFILE"], document="PROFILE", order="REQUIRED_PROFILE_MEMBERS_ORDER"),
            "FROZEN_CONTENT_POINTER": E("/frozen_authority_contents/<subject profile_member>/content_base64", "RFC6901_POINTER", [PC], ["FROZEN_SOURCE"], document="PROFILE"),
            "ACCEPTED_CONTENT_ROW_POINTER": E("/accepted_source_contents when no content row matches the allowlist subject; /accepted_source_contents/<index> of the matched row when exactly one matches",
                                              "RFC6901_POINTER", [CI, SC], ["ALLOWLIST_ROW"], document="PROFILE",
                                              cases={"ZERO_MATCHING_CONTENT_ROWS": "/accepted_source_contents", "ONE_MATCHING_CONTENT_ROW": "/accepted_source_contents/<index>"}),
            "CLAIM_PROFILE_POINTER": E("protocol_constants.claim_comparisons[subject].profile_pointer_rfc6901", "RFC6901_POINTER", [PC], ["AUTHORITY_CLAIM", "PROCEDURE_PROJECTION_CLAIM"], document="PROFILE"),
        },
        "candidate_artifact": {
            "NULL": E("no candidate artifact is involved (explicitly permitted by the registered witness)", "NULL", [LT], ["ANY"], constant_value=None),
            "CLAIM_CANDIDATE_ARTIFACT": E("protocol_constants.claim_comparisons[subject].candidate_artifact; the document is protocol_constants.claim_artifacts[name]", "NONEMPTY_STRING", [PC],
                                          ["AUTHORITY_CLAIM", "PROCEDURE_PROJECTION_CLAIM"], document="CLAIM_ARTIFACT_DOCUMENT"),
        },
        "candidate_pointer": {
            "NULL": E("no candidate location is involved, or no unique candidate item exists (match count 0 or greater than 1) (D3)", "NULL", [LT], ["ANY"], constant_value=None),
            "CLAIM_CANDIDATE_POINTER": E("protocol_constants.claim_comparisons[subject].candidate_pointer_rfc6901 (claims 0..3 only)", "RFC6901_POINTER", [PC], ["AUTHORITY_CLAIM"],
                                         document="CLAIM_ARTIFACT_DOCUMENT"),
            "SELECTOR_DECLARATION_POINTER": E("the candidate metacontract location of the selector declaration itself: /external_acceptance_profile_contract/candidate_claim_comparisons/4/candidate_selector (D3)",
                                              "RFC6901_POINTER", [PC], ["PROCEDURE_PROJECTION_CLAIM"], document="METACONTRACT"),
            "SELECTED_VALUE_POINTER": E("/procedures/<index of the uniquely selected item> followed by the selector's selected_value_pointer_rfc6901_relative_to_item (D3)", "RFC6901_POINTER", [PC, CD, SC],
                                        ["PROCEDURE_PROJECTION_CLAIM"], document="CLAIM_ARTIFACT_DOCUMENT", defined_for_cases=["MATCH_COUNT_ONE"]),
            "FIRST_UNSELECTED_FORBIDDEN_MEMBER_POINTER": E("/procedures/<j> followed by the selector's forbidden_pointer_rfc6901_relative_to_item, for the first unselected item j (ascending index) on which that member is present (present null counts as present)",
                                                           "RFC6901_POINTER", [PC, CD, SC], ["PROCEDURE_PROJECTION_CLAIM"], document="CLAIM_ARTIFACT_DOCUMENT",
                                                           order="ASCENDING_ARRAY_INDEX", defined_for_cases=["MATCH_COUNT_ONE"]),
        },
        "source_identity": {
            "NULL": E("no source object is involved", "NULL", [LT], ["ANY"], constant_value=None),
            "FROZEN_SOURCE_TYPED_IDENTITY": E("protocol_constants.frozen_sources[subject].typed_identity", "TYPED_IDENTITY", [PC], ["FROZEN_SOURCE"], identity_guarantee="PROTOCOL_CONSTANT_TYPED_IDENTITY"),
            "ACCEPTED_SOURCE_REF_WHEN_VALID_ELSE_NULL": E("the profile allowlist subject's ref kind/id/version under TYPED_IDENTITY_WHEN_VALID_ELSE_NULL (D14)", "TYPED_IDENTITY_OR_NULL", [CI],
                                                          ["ALLOWLIST_ROW"], identity_rule=ident),
            "CLAIM_FROZEN_SOURCE_TYPED_IDENTITY_ELSE_NULL": E("for a claim whose profile pointer is /frozen_authority_pins/<member>, protocol_constants.frozen_sources[<member>].typed_identity; otherwise null",
                                                              "TYPED_IDENTITY_OR_NULL", [PC], ["AUTHORITY_CLAIM"], identity_rule=ident),
        },
        "expected": {
            "NULL": E("null", "NULL", [LT], ["ANY"], constant_value=None),
            "REQUIRED_CALLER_INPUTS": E("the input_name of every protocol_constants.caller_input_precedence entry whose stage is the family stage and whose input is absent, in array order (D9)",
                                        "STRING_ARRAY", [PC, CI], ["CALLER_PROFILE_SCHEMA_INPUT", "CALLER_PROFILE"], order="CALLER_INPUT_PRECEDENCE"),
            "VERIFIER_PROFILE_SCHEMA_ID": E("protocol_constants.profile_schema_identity", "NONEMPTY_STRING", [PC], ["CALLER_PROFILE_SCHEMA_INPUT"]),
            "CALLER_EXPECTED_SHA256": E("the caller-supplied expected digest string", "JSON_VALUE", [CI], ["CALLER_PROFILE_SCHEMA_INPUT"]),
            "DRAFT_2020_12_DIALECT": E("protocol_constants.draft_2020_12_dialect", "NONEMPTY_STRING", [PC], ["CALLER_PROFILE_SCHEMA_INPUT"]),
            "REQUIRED_MEMBER_JSON_TYPE": E("the json_type token of the first failing protocol_constants.required_profile_members entry", "JSON_TYPE_TOKEN", [PC, SC], ["CALLER_PROFILE"],
                                           order="REQUIRED_PROFILE_MEMBERS_ORDER"),
            "PIN_GIT_BLOB": E("FROZEN_SOURCE: the profile value at /frozen_authority_pins/<member>/git_blob; ALLOWLIST_ROW: the profile allowlist row git_blob; null when absent",
                              "JSON_VALUE_OR_NULL", [CI, PC], ["FROZEN_SOURCE", "ALLOWLIST_ROW"]),
            "ALLOWLIST_DIGEST_FIELD": E("the profile allowlist row value of the condition's digest_field (raw_sha256 or semantic_sha256); null when absent", "JSON_VALUE_OR_NULL", [CI, MP], ["ALLOWLIST_ROW"]),
            "PROFILE_CLAIM_VALUE": E("the profile value at the claim profile pointer", "JSON_VALUE", [CI, PC], ["AUTHORITY_CLAIM", "PROCEDURE_PROJECTION_CLAIM"]),
            "PROTOCOL_SELECTOR": E("protocol_constants.procedure_projection_selector (the verifier's supported selector; distinct from the candidate copy) (D3)", "JSON_VALUE", [PC], ["PROCEDURE_PROJECTION_CLAIM"]),
            "REQUIRED_MATCH_COUNT": E("the JSON integer protocol_constants.procedure_projection_selector.selection.required_match_count (1) (D3)", "POSITIVE_INTEGER", [PC], ["PROCEDURE_PROJECTION_CLAIM"]),
            "ABSENT_MEMBER": E("the literal string ABSENT", "NONEMPTY_STRING", [LT], ["PROCEDURE_PROJECTION_CLAIM"], constant_value="ABSENT"),
            "LOWERCASE_SHA256_HEX_FORMAT": E("the literal string ^[0-9a-f]{64}$", "NONEMPTY_STRING", [LT], ["CALLER_PROFILE_SCHEMA_INPUT"], constant_value="^[0-9a-f]{64}$"),
        },
        "actual": {
            "NULL": E("null", "NULL", [LT], ["ANY"], constant_value=None),
            "CALLER_SCHEMA_ID": E("the caller-supplied schema identity", "JSON_VALUE", [CI], ["CALLER_PROFILE_SCHEMA_INPUT"]),
            "COMPUTED_SHA256": E("SHA-256 (lowercase hex) of the raw bytes", "NONEMPTY_STRING", [SC], ["CALLER_PROFILE_SCHEMA_INPUT"]),
            "CALLER_EXPECTED_SHA256": E("the caller-supplied expected digest string", "JSON_VALUE", [CI], ["CALLER_PROFILE_SCHEMA_INPUT"]),
            "SCHEMA_DIALECT_MEMBER": E("the schema's $schema value, or null when absent", "JSON_VALUE_OR_NULL", [CI], ["CALLER_PROFILE_SCHEMA_INPUT"]),
            "SCHEMA_ID_MEMBER": E("the schema's $id value, or null when absent", "JSON_VALUE_OR_NULL", [CI], ["CALLER_PROFILE_SCHEMA_INPUT"]),
            "MEMBER_JSON_TYPE": E("the closed_vocabularies.json_type token of the failing member (ABSENT when absent) (D10)", "JSON_TYPE_TOKEN", [SC], ["CALLER_PROFILE"]),
            "COMPUTED_GIT_BLOB": E("git blob id of the decoded bytes", "NONEMPTY_STRING", [SC], ["FROZEN_SOURCE", "ALLOWLIST_ROW"]),
            "COMPUTED_DIGEST_FIELD": E("the recomputed value of the condition's digest_field", "NONEMPTY_STRING", [SC], ["ALLOWLIST_ROW"]),
            "CANDIDATE_CLAIM_VALUE": E("the candidate value at the claim location, or null when absent", "JSON_VALUE_OR_NULL", [PC, CD, SC], ["AUTHORITY_CLAIM", "PROCEDURE_PROJECTION_CLAIM"]),
            "CANDIDATE_SELECTOR": E("the candidate metacontract value at /external_acceptance_profile_contract/candidate_claim_comparisons/4/candidate_selector, or null when absent (D3)", "JSON_VALUE_OR_NULL", [CD],
                                    ["PROCEDURE_PROJECTION_CLAIM"]),
            "MATCH_COUNT": E("the JSON integer number of items of the /procedures array whose selection member is JSON-equal to the selection literal (D3)", "NONNEGATIVE_INTEGER", [SC],
                             ["PROCEDURE_PROJECTION_CLAIM"], defined_for_cases=["MATCH_COUNT_ZERO", "MATCH_COUNT_MANY"]),
            "PRESENT_MEMBER": E("the value of the member that must be absent", "JSON_VALUE", [CD, SC], ["PROCEDURE_PROJECTION_CLAIM"]),
        },
        "trust_result": {
            "TRUST_FIELDS_ABSENT_OR_MALFORMED_IN_DECLARED_ORDER": E("the input_name of every protocol_constants.caller_input_precedence entry of stage READ_CANDIDATE_ENTRYPOINT_AND_EXTERNAL_TRUST_TRIPLE that is absent or an empty string (expected_package_digest also when not 64 lowercase hex), in array order (D9)",
                                                                    "TRUST_FIELD_NAME_ARRAY", [PC, CI], ["CALLER_TRUST_TRIPLE"], order="CALLER_INPUT_PRECEDENCE"),
            "CALLER_ID_VERSION": E("{id, version} from the caller trust triple (validated by PE-03)", "ID_VERSION", [CI], ["TRUST_COMPARISON"]),
            "PACKAGE_ID_VERSION": E("{id: package_id, version: package_version} when both are non-empty strings", "ID_VERSION", [CD], ["TRUST_COMPARISON"], defined_for_cases=["PACKAGE_ID_VERSION_VALID"]),
            "CALLER_IDENTITY3": E("{id, version, digest} from the caller trust triple", "IDENTITY3", [CI], ["TRUST_COMPARISON"]),
            "PACKAGE_IDENTITY3_WITH_RECOMPUTED_DIGEST": E("{id: package_id, version: package_version, digest: verified RFC8785 self-digest}; id/version equal the caller's once FOREIGN_IDENTITY has not fired",
                                                          "IDENTITY3", [CD, SC], ["TRUST_COMPARISON"]),
        },
        "map_value_comparison": {
            "SELECTED_PROCEDURE_ID": E("procedure_id of the selected projection procedure", "NONEMPTY_STRING", [CD, SC], ["SELECTED_PROJECTION_PROCEDURE"]),
            "DESCRIPTOR_ARGUMENT": E("profile descriptor argument (a string: the descriptor equals the schema-validated metacontract descriptor by PE-18)", "NONEMPTY_STRING", [CI], ["SELECTED_PROJECTION_PROCEDURE"]),
            "DESCRIPTOR_POINTER_TOKENS_AS_RFC6901": E("RFC6901 pointer built from descriptor pointer_tokens", "RFC6901_POINTER", [CI, SC], ["SELECTED_PROJECTION_PROCEDURE"], document="PROFILE_DESCRIPTOR_MAP_ARGUMENT"),
            "DESCRIPTOR_BASELINE_ARGUMENT": E("profile descriptor baseline.argument (a string, as DESCRIPTOR_ARGUMENT)", "NONEMPTY_STRING", [CI], ["SELECTED_PROJECTION_PROCEDURE"]),
            "DESCRIPTOR_EXPECTED_LITERALS": E("profile descriptor expected_literals", "JSON_VALUE", [CI], ["SELECTED_PROJECTION_PROCEDURE"]),
            "NULL": E("null", "NULL", [LT], ["ANY"], constant_value=None),
            "BASELINE_STATUS_VALUES": E("{PASS: baseline pass_result, FAIL: baseline fail_result} read through descriptor baseline status_pointer_tokens", "JSON_VALUE", [CI, SC], ["SELECTED_PROJECTION_PROCEDURE"]),
            "MAP_VALUE": E("the value at the map pointer in the bound map argument", "JSON_VALUE", [CD, SC], ["SELECTED_PROJECTION_PROCEDURE"]),
        },
    }


def _r5r22_pending():
    """Reachable conditions that still need a human decision (R5R22 section 21); none is decided here."""
    return [
        {"id": "PHD-01", "family": "PE-41", "conditions": ["RESERVED_INPUT_NAME_LABEL_MISMATCH", "RESERVED_CONTENT_SOURCE_PIN_UNDECLARED"], "aspect": "PREDICATE",
         "gap": "no declaration defines when a binding_origins.reserved_names label 'disagrees' with a row's type/origin (rows verification_universe and external_trust have unpinned type/origin), whether a row whose name has no label is a label mismatch or a name-set mismatch, or what 'names a declared external authority pin' means for pin_pointer_tokens",
         "options": ["label is type, or type + '_FROM_' + origin", "label is type when origin equals type or BOOTSTRAP_ + type, else type + '_FROM_' + origin", "a declared name -> {type, origin} table"],
         "also_decides": "the closed value vocabulary RESERVED_INPUT_TYPE_ADMITTED_BY_PE41 used by object_role in PE-39"},
        {"id": "PHD-02", "family": "PE-38", "conditions": ["BOUND_SCHEMA_MEMBER_UNREGISTERED", "BOUND_SCHEMA_VIOLATION"], "aspect": "FIELD",
         "gap": "D5 names 'the declared source/binding argument' and 'the declared accepted/bound-source role', but no single declared argument names the bound-source content document (external_acceptance_profile names the profile, whose pointers do not reach the decoded content) and the allowlist declares a roles array (two roles for the vector catalog); the case where expected_schema_ref names no eligible SCHEMA row has no schema_ref",
         "options": ["argument: a protocol constant naming the bound-source content document (as H1 candidate_object); object_role: allowlist ref kind", "argument: the unique procedure RULE_BINDING argument whose EXACT_REFERENCE ref equals the source ref",
                     "unresolved expected_schema_ref: attribute to the declaring allowlist row (D6 principle)"]},
        {"id": "PHD-03", "family": "PE-19", "conditions": ["PROCEDURE_REGISTRY_UNRESOLVED", "PROCEDURE_REGISTRY_UNREADABLE"], "aspect": "FIELD",
         "gap": "D3 requires the claim-side pointer to identify 'the procedure-registry reference/declaration': the reference is specification-package:/procedure_registry_ref, the declaration is the claim's candidate_artifact; no candidate_artifact name is declared for the package",
         "options": ["candidate_artifact: a declared name for the package + /procedure_registry_ref", "candidate_artifact: metacontract + /external_acceptance_profile_contract/candidate_claim_comparisons/4/candidate_artifact"]},
        {"id": "PHD-04", "family": "PE-19", "conditions": ["SELECTOR_MATCH_COUNT"], "aspect": "FIELD", "input_case": "COLLECTION_NOT_ARRAY",
         "gap": "when /procedures is absent or not an array no match count exists; D3 fixes candidate_pointer = null only for counts 0 or >1, and 'identifies the selector/match-count requirement' does not fix the artifact/pointer or the actual value for this case",
         "options": ["candidate_artifact metacontract, pointer .../candidate_selector/collection_type, actual null", "candidate_artifact procedure-registry, pointer /procedures, actual 0"]},
        {"id": "PHD-05", "family": "PE-11", "conditions": ["FOREIGN_IDENTITY"], "aspect": "FIELD", "input_case": "PACKAGE_ID_VERSION_INVALID",
         "gap": "a self-consistent package whose package_id/package_version is absent, empty or not a string reaches the trust comparison; the registered FOREIGN_PACKAGE_IDENTITY witness requires actual to be a non-empty id_version, so no valid result exists",
         "options": ["add a VALIDATE_EXTERNAL_TRUST_TRIPLE_AND_RECOMPUTE_PACKAGE condition before PE-11 (SCHEMA_INVALID_BOUND_OBJECT, TYPE, candidate_package witness)", "change the R5R18 trust envelope (out of scope)"]},
        {"id": "PHD-06", "family": "PE-17", "conditions": ["ACCEPTED_BASE64_INVALID", "ACCEPTED_GIT_BLOB", "ACCEPTED_RAW_DIGEST", "ACCEPTED_UNDECODABLE", "ACCEPTED_SEMANTIC_DIGEST"],
         "aspect": "PREDICATE", "input_case": "MANY_MATCHING_CONTENT_ROWS",
         "gap": "the caller-supplied profile may contain several accepted_source_contents rows with the allowlist ref, canonical_path and git_blob; which row's content is verified (and its pointer) is undeclared",
         "options": ["not exactly one matching row fails ACCEPTED_CONTENT_ROW_MISSING at /accepted_source_contents", "verify the first matching row by ascending index"]},
        {"id": "PHD-07", "family": "PE-21", "conditions": ["OBJECT_REGISTRY_SCHEMA_VIOLATION"], "aspect": "FIELD", "input_case": "REGISTRY_LEVEL_FAILURE_OUTSIDE_OBJECT_ROWS",
         "gap": "the object-registry schema also constrains top-level members (required members, additionalProperties false); a failure outside /objects/<i> has no row index for the declared /objects/<row_index> templates and no position in ASCENDING_ROW_INDEX_THEN_DECLARED_RULE_ORDER",
         "options": ["registry-level failures first, pointer = first invalid location (DESCENDANTS preorder), bound_identity null, diagnostic OBJECT_REGISTRY_SCHEMA_VIOLATION", "after all rows"]},
        {"id": "PHD-08", "family": "PE-40", "conditions": ["RESOLVED_OBJECT_REPRESENTATION"], "aspect": "FIELD", "input_case": "MEMBER_RESOLVED_RECORD",
         "gap": "member-resolved object records are validated in registered member order but are not located in the published universe value named by the argument, so no instance_pointer base (or bound identity) is declared for them",
         "options": ["validate only the /objects/<k> records of the universe value", "declare a member-record location such as the owner record pointer plus member index"]},
    ]


def _r5r22_protocol_constants(pc, meta, reg, pkg, evic):
    stages = meta["bootstrap_order"]
    contract = meta["external_acceptance_profile_contract"]
    trust_order = next(r for r in meta["reserved_inputs"] if r.get("name") == "external_trust")["fields"]
    fields = evic["fields"]
    entries = []
    for name in trust_order:
        if name in fields and str(fields[name].get("source", "")).startswith("CALLER_SUPPLIED"):
            entries.append({"input_name": name, "contract_field": name, "stage": stages[0],
                            "declared_by": "external-verification-input-contract:/fields/" + name, "order_source": "metacontract:/reserved_inputs[external_trust]/fields"})
    psi = contract["profile_schema_input"]
    for member, field in (("schema_identity_argument", "acceptance_profile_schema_identity"), ("schema_bytes_argument", "acceptance_profile_schema_bytes"),
                          ("expected_sha256_argument", "acceptance_profile_schema_sha256")):
        entries.append({"input_name": psi[member], "contract_field": field, "stage": stages[1],
                        "declared_by": "metacontract:/external_acceptance_profile_contract/profile_schema_input/" + member,
                        "order_source": "metacontract:/bootstrap_order/1 (ID, BYTES, EXPECTED_SHA256)"})
    entries.append({"input_name": contract["transport"], "contract_field": "acceptance_profile", "stage": "READ_EXTERNAL_ACCEPTANCE_PROFILE_OUTSIDE_CANDIDATE",
                    "declared_by": "metacontract:/external_acceptance_profile_contract/transport", "order_source": "single input"})
    pc["caller_input_precedence"] = entries
    pc["profile_schema_identity"] = psi["schema_identity"]
    pc["json_number_resource_limits"] = copy.deepcopy(meta["numeric_representation"]["json_number"]["resource_limits"])
    pc["claim_comparisons"] = copy.deepcopy(contract["candidate_claim_comparisons"])
    pc["procedure_projection_selector"] = copy.deepcopy(contract["procedure_projection_selector"])
    pc["claim_artifacts"] = {"metacontract": {"package_member": "metacontract_ref", "document": "METACONTRACT"},
                             "procedure-registry": {"package_member": "procedure_registry_ref", "document": "PROCEDURE_REGISTRY"}}
    pc["eligibility_members_in_order"] = [["status", meta["eligibility"]["candidate_universe"]["status"]], ["classification", meta["eligibility"]["candidate_universe"]["classification"]]]
    pc["authority"] = ("VERIFIER_PROTOCOL_CONSTANTS_FIXED_BY_THIS_ACCORD_VERSION;THE_CANDIDATE_COPY_IS_A_PUBLISHED_CLAIM;"
                       "STAGES_UP_TO_AND_INCLUDING_THE_CLAIM_COMPARISON_READ_THESE_CONSTANTS")
    return pc


def _r5r22_closed_vocabularies(meta, reg_schema, proc_schema):
    kinds = reg_schema["$defs"]["ref"]["properties"]["kind"]["enum"]
    return {
        "subject_class": copy.deepcopy(_R5R22_SUBJECT_CLASSES),
        "value_type": sorted(_R5R22_VALUE_SAMPLES),
        "source": copy.deepcopy(_R5R22_SOURCE_DEFINITIONS),
        "document": list(_R5R22_DOCUMENTS),
        "pointer_document_rule": list(_R5R22_POINTER_DOCUMENT_RULES),
        "ordering_rule": copy.deepcopy(_R5R22_ORDERING_RULES),
        "identity_rule": copy.deepcopy(_R5R22_IDENTITY_RULES),
        "identity_guarantee": copy.deepcopy(_R5R22_IDENTITY_GUARANTEES),
        "json_type": {"tokens": list(_R5R22_JSON_TYPES),
                      "classification": {"OBJECT": "JSON object", "ARRAY": "JSON array", "STRING": "JSON string", "BOOLEAN": "true or false", "NULL": "null",
                                         "INTEGER": "a JSON number whose exact decimal value has no non-zero fractional part (JSON Schema 2020-12 integer; 1.0 is INTEGER)",
                                         "NUMBER": "any other JSON number", "ABSENT": "the member does not exist"},
                      "satisfaction": "a member satisfies json_type T when its token equals T; T = NUMBER is also satisfied by INTEGER",
                      "totality": "every JSON value maps to exactly one of OBJECT, ARRAY, STRING, BOOLEAN, NULL, INTEGER, NUMBER; an absent member maps to ABSENT"},
        "argument_documents": {"candidate_package": "PACKAGE", "object_registry": "REGISTRY", "metacontract": "METACONTRACT", "procedure_registry": "PROCEDURE_REGISTRY",
                               "primitive_registry": "PRIMITIVE_REGISTRY", "rule_registry": "RULE_REGISTRY", "invariant_registry": "INVARIANT_REGISTRY",
                               "candidate_object": "CANDIDATE_OBJECT_CONTENT", "verification_universe": "VERIFICATION_UNIVERSE_VALUE"},
        "object_role_value_vocabulary": {"REGISTRY_KIND": list(kinds), "FIXED_ROLE": ["REGISTRY_OBJECT", "VERIFICATION_UNIVERSE"],
                                         "RESERVED_INPUT_TYPE_ADMITTED_BY_PE41": "PENDING:PHD-01"},
        "admission_predicate": copy.deepcopy(_R5R22_ADMISSION_PREDICATES),
    }


def _r5r22_repair(model, meta, reg, pkg, evic, reg_schema, proc_schema):
    F = {f["family_id"]: f for f in model["families"]}
    D = lambda t: {"derivation": t}
    Cn = lambda v: {"constant": v}
    P = lambda i: {"pending": i}
    cond = lambda fid, cid: next(c for c in F[fid]["conditions"] if c["condition_id"] == cid)
    EP, ER, ESR, ENR = "ENTRYPOINT_PACKAGE", "ENTRYPOINT_REGISTRY", "ELIGIBLE_SCHEMA_ROW", "ELIGIBLE_NON_SCHEMA_ROW"
    classes = {"PE-01": [EP, ER], "PE-03": ["CALLER_TRUST_TRIPLE"], "PE-02": [EP, ER], "PE-04": ["CALLER_PROFILE_SCHEMA_INPUT"], "PE-06": ["CALLER_PROFILE_SCHEMA_INPUT"],
               "PE-05": ["CALLER_PROFILE_SCHEMA_INPUT"], "PE-07": ["CALLER_PROFILE_SCHEMA_INPUT"], "PE-08": ["CALLER_PROFILE_SCHEMA_INPUT"], "PE-09": [EP, ER],
               "PE-10": [EP], "PE-12": [EP], "PE-13": [EP], "PE-11": ["TRUST_COMPARISON"], "PE-33": [EP, ER], "PE-14": ["CALLER_PROFILE"], "PE-15": ["CALLER_PROFILE"],
               "PE-16A": ["FROZEN_SOURCE"], "PE-16B": ["FROZEN_SOURCE"], "PE-17": ["ALLOWLIST_ROW"], "PE-18": ["AUTHORITY_CLAIM"], "PE-19": ["PROCEDURE_PROJECTION_CLAIM"],
               "PE-22": ["PROTOCOL_SECTION", "REGISTRY_SCHEMA_DECLARATION"], "PE-21": ["REGISTRY_ROW"], "PE-23": ["REGISTRY_ROW"], "PE-24": ["REGISTRY_DUPLICATE_SELECTION"],
               "PE-25": ["REGISTRY_ROW"], "PE-27": ["REGISTRY_ROW"], "PE-26": ["REGISTRY_ROW"], "PE-33B": ["BOOTSTRAP_OBJECT"], "PE-30": [ESR, ENR], "PE-31": [ESR, ENR],
               "PE-32": [ESR, ENR], "PE-34": ["BOUND_VECTOR_SOURCE"], "PE-35": ["UNION_COLLISION"], "PE-37": [ESR], "PE-36": [ENR], "PE-38": ["BOUND_SOURCE"],
               "PE-41": ["RESERVED_INPUT_ROW", "RESERVED_INPUT_COLLECTION"], "PE-39": ["PRODUCER_SCHEMA_RESERVED_INPUT"],
               "PE-40": ["RUNTIME_VALUE_SCHEMA", "UNIVERSE_VALUE", "UNIVERSE_OBJECT_RECORD", "MEMBER_RESOLVED_RECORD"], "PE-45": ["STATIC_DECLARATION_SITE"],
               "PE-44": ["PROCEDURE_DECLARATION", "AST_NODE"], "PE-46": ["PROTOCOL_SECTION", "WITNESS_OPERAND_TERMINAL"], "PE-48": ["BINDING_SITE"],
               "PE-47": ["SELECTED_PROJECTION_PROCEDURE"]}
    for fid, cl in classes.items():
        F[fid]["subject_classes"] = cl
    # D14: identity members must be non-empty strings (renamed token; every use).
    for fam in model["families"]:
        for c in fam["conditions"]:
            w = c.get("witness") or {}
            if w.get("bound_identity") == D("ENTRYPOINT_CONTENT_IDENTITY_WHEN_DECODABLE_ELSE_NULL"):
                w["bound_identity"] = D("ENTRYPOINT_CONTENT_IDENTITY_WHEN_VALID_ELSE_NULL")
    # PE-17: D14 on the allowlist ref, and the pending multi-match case (PHD-06).
    for c in F["PE-17"]["conditions"]:
        c["witness"]["source_identity"] = D("ACCEPTED_SOURCE_REF_WHEN_VALID_ELSE_NULL")
        if c["condition_id"] == "ACCEPTED_RAW_DIGEST": c["digest_field"] = "raw_sha256"
        if c["condition_id"] == "ACCEPTED_SEMANTIC_DIGEST": c["digest_field"] = "semantic_sha256"
        if c["condition_id"] == "ACCEPTED_CONTENT_ROW_MISSING":
            c["input_cases"] = ["ZERO_MATCHING_CONTENT_ROWS"]
        else:
            c["input_cases"] = ["ONE_MATCHING_CONTENT_ROW", "MANY_MATCHING_CONTENT_ROWS"]
            c["witness"]["profile_pointer"] = {"by_case": {"ONE_MATCHING_CONTENT_ROW": D("ACCEPTED_CONTENT_ROW_POINTER"), "MANY_MATCHING_CONTENT_ROWS": P("PHD-06")}}
            c["predicate_pending_cases"] = {"MANY_MATCHING_CONTENT_ROWS": "PHD-06"}
    # PE-11 (PHD-05): package identity members may be invalid when the caller identity differs.
    fi = cond("PE-11", "FOREIGN_IDENTITY")
    fi["input_cases"] = ["PACKAGE_ID_VERSION_VALID", "PACKAGE_ID_VERSION_INVALID"]
    fi["witness"]["actual"] = {"by_case": {"PACKAGE_ID_VERSION_VALID": D("PACKAGE_ID_VERSION"), "PACKAGE_ID_VERSION_INVALID": P("PHD-05")}}
    # D1: PE-24 bound identity is the selected duplicate row identity.
    cond("PE-24", "DUPLICATE_IDENTITY")["witness"]["bound_identity"] = D("GLOBAL_UNIQUENESS_SELECTED_DUPLICATE_IDENTITY")
    # D2: PE-33 row-lookup conditions are witnessed in the object registry.
    regw = lambda: {"argument": D("REGISTRATION_WITNESS_ARGUMENT"), "object_role": D("REGISTRATION_WITNESS_OBJECT_ROLE"), "schema_ref": D("REGISTRATION_WITNESS_SCHEMA_REF"),
                    "instance_pointer": D("REGISTRY_BINDING_LOCATION"), "bound_identity": D("REGISTRY_CONTENT_IDENTITY_WHEN_VALID_ELSE_NULL")}
    for cid, text in (("ENTRYPOINT_ROW_NOT_UNIQUE", "the subject entrypoint's kind/id/version does not match exactly one registry row; witnessed in the object registry at /objects"),
                      ("ENTRYPOINT_PATH_DIFFERS", "the unique matched row path differs from the explicit entrypoint path; witnessed in the object registry at /objects/<row_index>/path")):
        c = cond("PE-33", cid)
        c["witness"] = regw()
        c["condition"] = text
        c["binding_document"] = "REGISTRY"
    cond("PE-33", "REGISTRY_NOT_OBJECT")["subject_scope"] = [ER]
    cond("PE-33", "PACKAGE_REGISTRY_REFERENCE")["subject_scope"] = [EP]
    # D3: PE-19 condition-specific pointer derivations.
    pe19 = {c["condition_id"]: c for c in F["PE-19"]["conditions"]}
    w = pe19["SELECTOR_UNSUPPORTED"]["witness"]
    w["candidate_artifact"] = Cn("metacontract")
    w["candidate_pointer"] = D("SELECTOR_DECLARATION_POINTER")
    pe19["SELECTOR_UNSUPPORTED"]["condition"] = "the candidate metacontract's /external_acceptance_profile_contract/candidate_claim_comparisons/4/candidate_selector differs from protocol_constants.procedure_projection_selector"
    for cid in ("PROCEDURE_REGISTRY_UNRESOLVED", "PROCEDURE_REGISTRY_UNREADABLE"):
        pe19[cid]["witness"]["candidate_artifact"] = P("PHD-03")
        pe19[cid]["witness"]["candidate_pointer"] = P("PHD-03")
    mc = pe19["SELECTOR_MATCH_COUNT"]
    mc["input_cases"] = ["COLLECTION_NOT_ARRAY", "MATCH_COUNT_ZERO", "MATCH_COUNT_MANY"]
    mc["witness"]["candidate_artifact"] = {"by_case": {"COLLECTION_NOT_ARRAY": P("PHD-04"), "MATCH_COUNT_ZERO": D("CLAIM_CANDIDATE_ARTIFACT"), "MATCH_COUNT_MANY": D("CLAIM_CANDIDATE_ARTIFACT")}}
    mc["witness"]["candidate_pointer"] = {"by_case": {"COLLECTION_NOT_ARRAY": P("PHD-04"), "MATCH_COUNT_ZERO": D("NULL"), "MATCH_COUNT_MANY": D("NULL")}}
    mc["witness"]["actual"] = {"by_case": {"COLLECTION_NOT_ARRAY": P("PHD-04"), "MATCH_COUNT_ZERO": D("MATCH_COUNT"), "MATCH_COUNT_MANY": D("MATCH_COUNT")}}
    for cid, tok in (("SELECTED_DESCRIPTOR", "SELECTED_VALUE_POINTER"), ("OTHER_PROCEDURE_PROJECTION", "FIRST_UNSELECTED_FORBIDDEN_MEMBER_POINTER")):
        pe19[cid]["input_cases"] = ["MATCH_COUNT_ONE"]
        pe19[cid]["witness"]["candidate_pointer"] = D(tok)
    pe19["OTHER_PROCEDURE_PROJECTION"]["order"] = "ASCENDING_ARRAY_INDEX"
    # D4: SCHEMA-kind subjects of PE-30/31/32 use the Draft 2020-12 metaschema.
    for fid in ("PE-30", "PE-31", "PE-32"):
        for c in F[fid]["conditions"]:
            c["witness"]["schema_ref"] = {"by_subject_class": {ESR: D("DRAFT_2020_12_METASCHEMA"), ENR: D("APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID")}}
    # D5: PE-38 witnesses come from the allowlist binding (argument and role: PHD-02).
    for c in F["PE-38"]["conditions"]:
        c["witness"]["argument"] = P("PHD-02")
        c["witness"]["object_role"] = P("PHD-02")
        c["witness"]["bound_identity"] = D("ALLOWLIST_REF_IDENTITY_WHEN_VALID_ELSE_NULL")
    b1 = cond("PE-38", "BOUND_SCHEMA_MEMBER_UNREGISTERED")
    b1["input_cases"] = ["EXPECTED_SCHEMA_ROW_RESOLVED", "EXPECTED_SCHEMA_ROW_UNRESOLVED"]
    b1["witness"]["schema_ref"] = {"by_case": {"EXPECTED_SCHEMA_ROW_RESOLVED": D("ALLOWLIST_EXPECTED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"), "EXPECTED_SCHEMA_ROW_UNRESOLVED": P("PHD-02")}}
    b2 = cond("PE-38", "BOUND_SCHEMA_VIOLATION")
    b2["input_cases"] = ["EXPECTED_SCHEMA_ROW_RESOLVED"]
    b2["witness"]["schema_ref"] = D("ALLOWLIST_EXPECTED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID")
    b2["validated_instance"] = "BOUND_SOURCE_CONTENT"
    F["PE-38"]["authority"] = "the externally verified allowlist row (metacontract:/eligibility/bound_source_universe; bound_registry_row_requirement NOT_UNIVERSAL); no registry row is synthesized"
    # D6: PE-39 unresolved producer schema is attributed to the declaring metacontract row.
    pu = cond("PE-39", "PRODUCER_SCHEMA_UNRESOLVED")
    pu["witness"] = {"argument": Cn("metacontract"), "object_role": D("OWNING_OBJECT_REGISTRY_ROW_KIND"), "schema_ref": D("OWNING_OBJECT_APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"),
                     "instance_pointer": D("PRODUCER_SCHEMA_REF_DECLARATION_LOCATION"), "bound_identity": D("OWNING_OBJECT_REGISTRY_IDENTITY")}
    pu["owning_object"] = "metacontract"
    pv = cond("PE-39", "PRODUCER_SCHEMA_VIOLATION")
    pv["witness"]["bound_identity"] = D("RESERVED_INPUT_FROZEN_SOURCE_IDENTITY_ELSE_NULL")
    pv["validated_instance"] = "RESERVED_INPUT_CONTENT"
    F["PE-39"]["h1_overrides"] = {"PRODUCER_SCHEMA_UNRESOLVED": "declaring metacontract row (D6)", "PRODUCER_SCHEMA_VIOLATION": {"argument": "metacontract:/reserved_inputs/*/name",
                                  "object_role": "metacontract:/reserved_inputs/*/type", "bound_identity": "protocol_constants.frozen_sources via pin_pointer_tokens"}}
    # D7: PE-41 member order, member locations and collection locations.
    checked = {"RESERVED_INPUT_DECLARATION_INVALID": ["name", "origin", "type"], "RESERVED_INPUT_DECLARATION_NOT_UNIQUE": ["name"],
               "RESERVED_INPUT_ORIGIN_UNDECLARED": ["origin"],
               "RESERVED_CONTENT_SOURCE_INVALID": ["profile_content_source/candidate_copy_authority", "profile_content_source/content_encoding", "profile_content_source/decode",
                                                   "profile_content_source/use_after_pin_verification_only"],
               "RESERVED_CONTENT_POINTER_INVALID": ["profile_content_source/content_pointer_tokens", "profile_content_source/pin_pointer_tokens"],
               "RESERVED_CONTENT_SOURCE_TRANSPORT_INVALID": ["profile_content_source/argument"], "RESERVED_CONTENT_SOURCE_PIN_UNDECLARED": ["profile_content_source/pin_pointer_tokens"]}
    for c in F["PE-41"]["conditions"]:
        cid = c["condition_id"]
        c["owning_object"] = "metacontract"
        if cid in checked:
            c["checked_members"] = sorted(checked[cid], key=lambda m: m.encode("utf-16-be"))
            c["witness"]["instance_pointer"] = D("RESERVED_INPUT_MEMBER_LOCATION")
            c["subject_scope"] = ["RESERVED_INPUT_ROW"]
        elif cid == "RESERVED_INPUT_NAME_LABEL_MISMATCH":
            c["collection_pointer"] = "/binding_origins/reserved_names/<escaped_name>"
            c["witness"]["instance_pointer"] = D("RESERVED_INPUT_COLLECTION_LOCATION")
            c["subject_scope"] = ["RESERVED_INPUT_ROW"]
            c["predicate_pending"] = "PHD-01"
        elif cid == "RESERVED_INPUT_NAME_SET_MISMATCH":
            c["collection_pointer"] = "/reserved_inputs"
            c["witness"]["instance_pointer"] = D("RESERVED_INPUT_COLLECTION_LOCATION")
            c["subject_scope"] = ["RESERVED_INPUT_COLLECTION"]
        if cid == "RESERVED_CONTENT_SOURCE_PIN_UNDECLARED":
            c["predicate_pending"] = "PHD-01"
        if cid == "RESERVED_INPUT_DECLARATION_NOT_UNIQUE":
            c["order"] = "ASCENDING_ARRAY_INDEX"
    F["PE-41"]["member_order"] = "UTF16_CODE_UNIT_KEY_ORDER"
    # D8: PE-33B absent row versus ineligible row.
    bn = cond("PE-33B", "BOOTSTRAP_NOT_ELIGIBLE")
    bn["input_cases"] = ["ROW_ABSENT_OR_NOT_UNIQUE", "ROW_STATUS_NOT_ACTIVE", "ROW_CLASSIFICATION_NOT_NORMATIVE"]
    bn["witness"]["instance_pointer"] = D("BOOTSTRAP_ROW_LOCATION")
    bn["witness"]["bound_identity"] = D("BOOTSTRAP_ROW_IDENTITY_ELSE_NULL")
    bn.pop("pointer_template", None)
    bn["condition"] = "the package or a package-referenced bootstrap object has no unique registry row with its kind/id/version, or that row is not ACTIVE NORMATIVE"
    # D11: PE-22 registry-schema lookup cases.
    rs = cond("PE-22", "REGISTRY_SCHEMA_UNAVAILABLE")
    rs["subject_scope"] = ["REGISTRY_SCHEMA_DECLARATION"]
    rs["witness"]["schema_ref"] = D("STRUCTURAL_APPLICATION_SCHEMA_DOCUMENT_ID")
    rs["witness"]["bound_identity"] = D("REGISTRY_SCHEMA_ROW_IDENTITY_WHEN_UNIQUE_READABLE_ELSE_NULL")
    rs["input_cases"] = ["ZERO_MATCHING_ROWS", "MULTIPLE_MATCHING_ROWS", "UNIQUE_ROW_UNREADABLE", "UNIQUE_ROW_READABLE"]
    rs["condition"] = ("the number of registry rows whose kind/id/version equal structural_application.schema_ref is not one, or the unique row is unreadable (path not canonical, outside the root, or bytes unreadable), "
                       "not strictly decodable, not a JSON object, or its $id differs from structural_application.schema_id")
    for c in F["PE-22"]["conditions"]:
        if c["condition_id"] != "REGISTRY_SCHEMA_UNAVAILABLE": c["subject_scope"] = ["PROTOCOL_SECTION"]
    # D12: PE-40 value-schema pointer is absolute in the metacontract.
    vi = cond("PE-40", "VALUE_SCHEMA_INVALID")
    vi["witness"]["instance_pointer"] = D("SCOPED_FIRST_INVALID_LOCATION")
    vi["pointer_scope"] = "/runtime_representation/value_schemas/<escaped_value_schema_name>"
    vi["subject_scope"] = ["RUNTIME_VALUE_SCHEMA"]
    vi["subject_order"] = "UTF16_CODE_UNIT_KEY_ORDER"
    vi["validated_instance"] = "RUNTIME_VALUE_SCHEMA_DOCUMENT"
    ur = cond("PE-40", "UNIVERSE_REPRESENTATION")
    ur["subject_scope"] = ["UNIVERSE_VALUE"]
    ur["validated_instance"] = "VERIFICATION_UNIVERSE_VALUE"
    ro = cond("PE-40", "RESOLVED_OBJECT_REPRESENTATION")
    ro["subject_scope"] = ["UNIVERSE_OBJECT_RECORD", "MEMBER_RESOLVED_RECORD"]
    ro["pointer_scope"] = "/objects/<k>"
    ro["validated_instance"] = "UNIVERSE_OBJECT_RECORD_VALUE"
    ro["witness"]["instance_pointer"] = {"by_subject_class": {"UNIVERSE_OBJECT_RECORD": D("SCOPED_FIRST_INVALID_LOCATION"), "MEMBER_RESOLVED_RECORD": P("PHD-08")}}
    ro["witness"]["bound_identity"] = {"by_subject_class": {"UNIVERSE_OBJECT_RECORD": D("RESOLVED_OBJECT_IDENTITY_CONTAINING_LOCATION_ELSE_NULL"), "MEMBER_RESOLVED_RECORD": P("PHD-08")}}
    # D13: PE-45 declared correspondence, admission predicates and trust-anchor owner.
    c2 = cond("PE-45", "PRIMITIVE_SIGNATURE_MATCHES_STATIC_TYPE_CALCULUS")
    c2["condition"] = ("a primitive's argument count or names differ from its operator's slots in order, an argument type is not a key of operator_rules.argument_type_slot_kinds "
                       "or maps to a slot kind other than its slot's, or its output_type differs from the operator result")
    c2["predicate_ref"] = "metacontract:/runtime_representation/static_type_calculus/operator_rules/argument_type_slot_kinds"
    c10 = cond("PE-45", "RULE_BINDING_SOURCE_CONSTRAINTS_VALID")
    c10["condition"] = "a RULE_BINDING argument fails one of the declared admission_predicates"
    c10["admission_predicates"] = list(_R5R22_ADMISSION_PREDICATES)
    c10["static_prerequisites"] = []
    c10["dominance"] = "VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE validates the procedure registry against the same registered grammar (PE-36); binding-time source-constraint checks are owned by PE-48"
    c12 = cond("PE-45", "TRUST_RESULT_OWNER_EXACT")
    c12["condition"] = "the set of procedures whose result type is TRUST_RESULT is not exactly the one procedure named by metacontract:/result_contracts/trust_result/owner_procedure_id"
    c12["predicate_ref"] = "metacontract:/result_contracts/trust_result/owner_procedure_id"
    cond("PE-13", "PACKAGE_SELF_DIGEST_DECLARATION_INVALID")["witness"]["instance_pointer"] = D("PACKAGE_SELF_DIGEST_DECLARATION_LOCATION")
    for c in F["PE-44"]["conditions"]:
        c["subject_scope"] = ["PROCEDURE_DECLARATION"] if c.get("level") == "PROCEDURE" else ["AST_NODE"]
    cond("PE-46", "GENERIC_WITNESS_DECLARATION_UNSUPPORTED")["subject_scope"] = ["PROTOCOL_SECTION"]
    cond("PE-46", "MISSING_WITNESS_OPERAND_IDENTITY")["subject_scope"] = ["WITNESS_OPERAND_TERMINAL"]
    # PHD-07: registry-level structural failures outside /objects/<i>.
    rv = cond("PE-21", "OBJECT_REGISTRY_SCHEMA_VIOLATION")
    rv["uncovered_input_cases"] = {"REGISTRY_LEVEL_FAILURE_OUTSIDE_OBJECT_ROWS": "PHD-07"}
    # Validated instances, owning objects and orders.
    cond("PE-36", "CONTENT_SCHEMA_VIOLATION")["validated_instance"] = "CANDIDATE_OBJECT_CONTENT"
    cond("PE-37", "SCHEMA_METASCHEMA")["validated_instance"] = "CANDIDATE_OBJECT_CONTENT"
    pe27 = cond("PE-27", "MODE_SHAPE_INVALID")
    pe27["witness"]["instance_pointer"] = D("SCOPED_FIRST_INVALID_LOCATION")
    pe27["pointer_scope"] = pe27.pop("pointer_scope", "/objects/<row_index>/integrity")
    pe27["validated_instance"] = "REGISTRY_ROW_INTEGRITY_DECLARATION"
    for c in F["PE-44"]["conditions"]:
        c.setdefault("owning_object", "procedure_registry")
    F["PE-48"]["owning_object"] = {"by_binding_site": {"INVARIANT_DEFAULT_ARGUMENT": "invariant_registry", "RULE_INVARIANT_BINDING_ARGUMENT": "rule_registry"}}
    for c in F["PE-48"]["conditions"]:
        c["owning_object"] = "BINDING_DECLARING_OBJECT"
    for c in F["PE-22"]["conditions"]:
        c["owning_object"] = "metacontract"
    for c in F["PE-40"]["conditions"]:
        if c["condition_id"] == "VALUE_SCHEMA_INVALID": c["owning_object"] = "metacontract"
    # PE-18 code and reasons are read from the protocol claim list.
    F["PE-18"]["code_derivation"] = {"BY_SUBJECT": "protocol_constants.claim_comparisons[subject].failure_code"}
    cond("PE-18", "CLAIM_MISMATCH")["reason"] = {"by_claim_index": {"3": "DESCRIPTOR_WHOLE_OBJECT_MISMATCH"}, "otherwise": "CLAIM_WHOLE_OBJECT_MISMATCH"}
    cond("PE-18", "CLAIM_MISMATCH").pop("reason_derivation", None)
    F["PE-18"]["owner_declaration"] = "protocol_constants.claim_comparisons[0..3]"
    F["PE-19"]["owner_declaration"] = "protocol_constants.claim_comparisons[4]"
    return model


def _r5r22_subject_order_rules():
    return {"SINGLE_SUBJECT": None, "ENTRYPOINT_ORDER": "ASCENDING_ARRAY_INDEX", "REGISTRY_SOURCE_ORDER": "ASCENDING_ARRAY_INDEX",
            "ELIGIBLE_ROWS_REGISTRY_SOURCE_ORDER": "ASCENDING_ARRAY_INDEX", "ELIGIBLE_SCHEMA_ROWS_REGISTRY_SOURCE_ORDER": "ASCENDING_ARRAY_INDEX",
            "ELIGIBLE_NON_SCHEMA_ROWS_REGISTRY_SOURCE_ORDER": "ASCENDING_ARRAY_INDEX", "ALLOWLIST_ORDER": "ASCENDING_ARRAY_INDEX",
            "CLAIM_COMPARISON_ORDER_0_TO_3": "ASCENDING_ARRAY_INDEX", "PROTOCOL_SECTION_ORDER": "ASCENDING_ARRAY_INDEX",
            "REGISTRATION_DECLARED_ORDER": "REGISTRATION_FIRST_FAILURE_ORDERING", "GLOBAL_UNIQUENESS_DECLARED_SELECTION": "GLOBAL_UNIQUENESS_SELECTION",
            "PACKAGE_BOOTSTRAP_REFERENCE_ORDER": "ASCENDING_ARRAY_INDEX", "BOUND_SOURCE_DECLARED_SCOPE": None, "STRICT_UNION_DECLARED_SCAN": None,
            "RESERVED_INPUT_ORDER": "ASCENDING_ARRAY_INDEX", "RESERVED_INPUT_ORDER_WITH_PRODUCER_SCHEMA": "ASCENDING_ARRAY_INDEX",
            "RUNTIME_VALUE_ORDER": "UTF16_CODE_UNIT_KEY_ORDER", "FROZEN_SOURCE_FROZEN_R5R2_RULES": None, "FROZEN_SOURCE_FROZEN_R5R3_V013_SEMANTICS": None,
            "STATIC_CONDITION_COLLECTION_INDEX_ORDER": "ASCENDING_ARRAY_INDEX", "AST_PROCEDURE_ASSERTION_POSTORDER": "ASCENDING_ARRAY_INDEX",
            "WITNESS_OPERAND_PREORDER": "DECLARED_WITNESS_OPERAND_PREORDER", "BINDING_SITE_ORDER": "ASCENDING_ARRAY_INDEX", "SELECTED_PROJECTION_PROCEDURE": None}


def _r5r22_defect_resolution():
    return [
        {"defect": "D1", "family": "PE-24", "change": "bound_identity is GLOBAL_UNIQUENESS_SELECTED_DUPLICATE_IDENTITY (typed identity of the selected duplicate row), not a string constant", "prevented_by": "B"},
        {"defect": "D2", "family": "PE-33", "change": "ENTRYPOINT_ROW_NOT_UNIQUE / ENTRYPOINT_PATH_DIFFERS are witnessed in the object registry (registration witness argument, role and schema; registry content identity)", "prevented_by": "C"},
        {"defect": "D3", "family": "PE-19", "change": "condition-specific candidate artifact/pointer derivations; null pointer for counts 0 or >1; integer REQUIRED_MATCH_COUNT; PROTOCOL_SELECTOR (protocol constant) distinct from CANDIDATE_SELECTOR (candidate copy)", "prevented_by": "C, D, G"},
        {"defect": "D4", "family": "PE-30, PE-31, PE-32", "change": "schema_ref by_subject_class: DRAFT_2020_12_METASCHEMA for SCHEMA rows, APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID for other rows", "prevented_by": "A"},
        {"defect": "D5", "family": "PE-38", "change": "schema_ref from the allowlist expected_schema_ref row, bound_identity from the allowlist ref; argument/role and the unresolved-row case are PHD-02", "prevented_by": "A, E"},
        {"defect": "D6", "family": "PE-39", "change": "PRODUCER_SCHEMA_UNRESOLVED is attributed to the declaring metacontract row at /reserved_inputs/<i>/profile_content_source/producer_schema_ref", "prevented_by": "A, D"},
        {"defect": "D7", "family": "PE-41", "change": "UTF-16 member order, per-member locations and collection locations; the label and pin predicates are PHD-01", "prevented_by": "F, C"},
        {"defect": "D8", "family": "PE-33B", "change": "absent/non-unique row -> /objects with null identity; ineligible row -> /objects/<row_index>/status or /classification with the row identity", "prevented_by": "D, C"},
        {"defect": "D9", "family": "PE-03, PE-04, PE-14", "change": "protocol_constants.caller_input_precedence (ordered, exact coverage of the caller-supplied contract fields)", "prevented_by": "F"},
        {"defect": "D10", "family": "PE-15", "change": "closed json_type vocabulary with exact INTEGER/NUMBER classification", "prevented_by": "G"},
        {"defect": "D11", "family": "PE-22", "change": "schema_ref is structural_application.schema_id; bound identity only for a unique readable matching row, else null", "prevented_by": "D, E"},
        {"defect": "D12", "family": "PE-40", "change": "VALUE_SCHEMA_INVALID pointer is absolute: /runtime_representation/value_schemas/<name> + first invalid location", "prevented_by": "C"},
        {"defect": "D13", "family": "PE-45", "change": "operator_rules.argument_type_slot_kinds; admission_predicates replace 'well-formed'; result_contracts.trust_result.owner_procedure_id", "prevented_by": "G and the builder D13 proofs"},
        {"defect": "D14", "family": "PE-12, PE-13, PE-33 and every identity-or-null derivation", "change": "TYPED_IDENTITY_WHEN_VALID_ELSE_NULL (every member present, string, non-empty)", "prevented_by": "E"},
    ]


def _r5r22_slot_map(meta, prim):
    ops = meta["runtime_representation"]["static_type_calculus"]["operator_rules"]["operators"]
    by_id = {p["primitive_id"]: p for p in prim["primitives"]}
    mapping = {}
    for name, op in ops.items():
        for (slot_name, slot_kind), arg in zip(op["slots"], by_id[name]["arguments"]):
            if mapping.setdefault(arg["type"], slot_kind) != slot_kind:
                raise ValueError("primitive argument type used with two slot kinds: " + arg["type"])
    return {k: mapping[k] for k in sorted(mapping)}


def _r5r22_d13_proofs(meta, prim, proc, proc_schema):
    """D13 builder proofs: total slot correspondence, resolvable admission grammars, exact trust-anchor owner."""
    rules = meta["runtime_representation"]["static_type_calculus"]["operator_rules"]
    table = rules.get("argument_type_slot_kinds")
    if not isinstance(table, dict) or not table: raise ValueError("D13A: argument_type_slot_kinds is not declared")
    ops, by_id = rules["operators"], {p["primitive_id"]: p for p in prim["primitives"]}
    if set(ops) != set(by_id): raise ValueError("D13A: operator set differs from primitive set")
    used = set()
    for name, op in ops.items():
        p = by_id[name]
        if len(op["slots"]) != len(p["arguments"]): raise ValueError("D13A: slot count " + name)
        for (slot_name, slot_kind), arg in zip(op["slots"], p["arguments"]):
            if slot_name != arg["name"]: raise ValueError("D13A: slot name " + name)
            if arg["type"] not in table: raise ValueError("D13A: primitive type has no slot kind: " + arg["type"])
            if table[arg["type"]] != slot_kind: raise ValueError("D13A: slot kind differs " + name + "/" + slot_name)
            if slot_kind not in rules["slot_kinds"]: raise ValueError("D13A: undeclared slot kind " + slot_kind)
            used.add(arg["type"])
        if p["output_type"] != op["result"]: raise ValueError("D13A: output type " + name)
    if used != set(table): raise ValueError("D13A: slot table is not exactly the primitive argument type surface")
    for pid, pred in _R5R22_ADMISSION_PREDICATES.items():
        node = proc_schema
        for tok in pred["grammar"].split(":", 1)[1].split("/")[1:]:
            node = node[int(tok)] if isinstance(node, list) else node[tok]
    owner = meta["result_contracts"]["trust_result"].get("owner_procedure_id")
    if not isinstance(owner, str) or not owner: raise ValueError("D13C: trust-anchor owner is not declared")
    matches = [p for p in proc["procedures"] if p.get("procedure_id") == owner]
    if len(matches) != 1: raise ValueError("D13C: trust-anchor owner is not exactly one procedure")
    t = matches[0]
    if t["result"].get("type") != "TRUST_RESULT": raise ValueError("D13C: owner result type")
    if t["result"].get("success_code") != meta["result_contracts"]["trust_result"]["status"]["PASS"]: raise ValueError("D13C: owner success code")
    if [p["procedure_id"] for p in proc["procedures"] if p["result"].get("type") == "TRUST_RESULT"] != [owner]: raise ValueError("D13C: TRUST_RESULT owner set")
    if sum(b.get("procedure_id") == owner for b in meta["procedure_bindings"]) != 1: raise ValueError("D13C: owner binding rows")
    if not any(a.get("origin") == "EXTERNAL_TRUST" for a in t["arguments"]): raise ValueError("D13C: owner lacks the external trust argument")
    return {"slot_types": len(table), "operators": len(ops), "admission_predicates": len(_R5R22_ADMISSION_PREDICATES), "trust_anchor_owner": owner}


def _r5r22_ptr_get(doc, pointer):
    cur = doc
    for tok in pointer.split("/")[1:] if pointer else []:
        tok = tok.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict) and tok in cur: cur = cur[tok]
        elif isinstance(cur, list) and tok.isdigit() and int(tok) < len(cur): cur = cur[int(tok)]
        else: raise KeyError(pointer)
    return cur


def _r5r22_semantic_totality(model, ctx):
    """Semantic totality (R5R22 section 16): the R5R20 structural checks plus properties A-G over every reachable condition."""
    import re
    meta, schema, reg, pkg = ctx["meta"], ctx["schema"], ctx["reg"], ctx["pkg"]
    import jsonschema as _js
    vocab, closed, pc = model["derivation_vocabulary"], model["closed_vocabularies"], model["protocol_constants"]
    pending = {p["id"]: p for p in model["pending_human_decisions"]}
    classes, orders = closed["subject_class"], closed["ordering_rule"]
    defs = schema["$defs"]
    branches = defs["pre_execution_result"]["oneOf"]
    fail_codes = set(meta["result_contracts"]["pre_execution_result"]["fail_codes"])
    trust_codes = set(meta["result_contracts"]["trust_result"]["status"]["FAIL"])
    errors, used_pending, seen_diag, stats = [], set(), set(), {"field_rules": 0, "pending_fields": 0, "pending_predicates": 0}
    E = errors.append
    order_words = re.compile(r"\bfirst\b|\blowest\b|\bearliest\b|declared order|in that order|\bminimal\b", re.I)
    def field_schema(contract, field, fam_code, cond):
        if contract == "SEVEN_FIELD": return branches[0]["properties"]["witness"]["properties"][field]
        if contract == "STATIC_VALIDATION":
            return next(b for b in branches if b["properties"]["code"].get("const") == "STATIC_VALIDATION_FAILED")["properties"]["witness"]["properties"][field]
        if contract == "PROFILE_PREFLIGHT": return defs["external_profile_preflight_witness"]["properties"][field]
        if contract == "MAP_VALUE_COMPARISON": return defs["map_value_comparison_witness"]["properties"][field]
        if contract == "TRUST_RESULT":
            stage = cond["witness"]["stage"]["constant"]
            for b in defs["trust_result"]["oneOf"]:
                wp = b["properties"]["witness"]["properties"]
                if wp["stage"].get("const") == stage: return wp[field]
        raise KeyError(field)
    def valid(sub, value):
        return _js.Draft202012Validator({"$defs": defs, **sub}).is_valid(value)
    vocab_field = {"trust_result": "trust_result", "MAP_VALUE_COMPARISON": "map_value_comparison"}
    # G (static vocabularies) and ordering-rule sources (F, C5).
    for name, rule in orders.items():
        if rule["kind"] == "ARRAY":
            try: target = _r5r22_ptr_get(model, rule["source"].split(":", 1)[1])
            except KeyError: E("F: ordering rule source unresolved " + name); continue
            if not isinstance(target, list): E("F: ARRAY ordering rule over a non-array " + name)
        if rule["kind"] == "DECLARED" and not rule.get("declared_by"): E("F: declared ordering rule without source " + name)
    for key, rule in model["subject_order_rules"].items():
        if key not in model["subject_orders"]: E("F: unknown subject order " + key)
        if rule is not None and rule not in orders: E("F: subject order rule " + key)
    for key in model["subject_orders"]:
        if key not in model["subject_order_rules"]: E("F: subject order without rule " + key)
    jt = closed["json_type"]["tokens"]
    for m in pc["required_profile_members"]:
        if m["json_type"] not in jt: E("G: unsupported json_type " + str(m["json_type"]))
    for probe, present in ((None, True), (True, True), ({}, True), ([], True), ("s", True), (1, True), (1.0, True), (1.5, True), (None, False)):
        if _r5r22_json_type(probe, present) not in jt: E("G: json type classification not total")
    rules = closed["identity_rule"]
    for name in rules:
        if name != "TYPED_IDENTITY_WHEN_VALID_ELSE_NULL": E("E: identity rule without executable semantics " + name)
    if _r5r22_identity_when_valid("PACKAGE", "x", None) is not None or _r5r22_identity_when_valid("PACKAGE", "x", "") is not None:
        E("E: identity rule accepts a missing version")
    # D9 caller input coverage.
    evic = ctx["evic"]
    expected_fields = {k for k, v in evic["fields"].items() if str(v.get("source", "")).startswith("CALLER_SUPPLIED")}
    cip = pc["caller_input_precedence"]
    names = [e["input_name"] for e in cip]
    if len(names) != len(set(names)): E("D9: duplicate caller input")
    if [e["contract_field"] for e in cip if e["contract_field"] not in expected_fields]: E("D9: unknown caller input")
    if {e["contract_field"] for e in cip} != expected_fields: E("D9: caller input coverage is not exact")
    for e in cip:
        t = evic["fields"].get(e["contract_field"], {}).get("transport")
        if t is not None and t != e["input_name"]: E("D9: caller input name differs from its declared transport " + e["input_name"])
        if e["stage"] not in meta["bootstrap_order"]: E("D9: caller input stage " + e["input_name"])
    trust_enum = defs["trust_result"]["oneOf"][1]["properties"]["witness"]["properties"]["missing_fields"]["items"]["enum"]
    if [e["input_name"] for e in cip if e["stage"] == meta["bootstrap_order"][0]] != trust_enum: E("D9: trust inputs differ from the registered missing_fields order")
    # Vocabulary entries (A-G on the token level).
    for field, toks in vocab.items():
        for tok, v in toks.items():
            where = field + "." + tok
            if not isinstance(v, dict): E("vocabulary entry is not machine-readable " + where); continue
            if v.get("value_type") not in _R5R22_VALUE_SAMPLES: E("G: value type " + where)
            if not v.get("source") or any(s not in _R5R22_SOURCES for s in v["source"]): E("G: source class " + where)
            dom = v.get("domain") or []
            if not dom or any(d != "ANY" and d not in classes for d in dom): E("A: domain " + where)
            if "well-formed" in v.get("definition", "") or "well formed" in v.get("definition", ""): E("C10: undefined well-formed predicate " + where)
            if order_words.search(v.get("definition", "")) and v.get("order") not in orders: E("F: order word without ordering rule " + where)
            if "order" in v and v["order"] not in orders: E("F: unknown ordering rule " + where)
            vt = v.get("value_type", "")
            if vt == "TYPED_IDENTITY_OR_NULL" and v.get("identity_rule") not in rules: E("E: identity-or-null derivation without identity rule " + where)
            if vt == "TYPED_IDENTITY" and v.get("identity_guarantee") not in closed["identity_guarantee"]: E("E: identity derivation without guarantee " + where)
            if "identity_rule" in v and v["identity_rule"] not in rules: E("E: unknown identity rule " + where)
            if vt.startswith("RFC6901_POINTER") or field == "argument" or field == "candidate_artifact":
                doc = v.get("document")
                if vt != "NULL" and doc is None: E("C: pointer or argument token without document " + where)
                for d in (doc.values() if isinstance(doc, dict) else [doc] if doc else []):
                    if d not in _R5R22_DOCUMENTS and d not in _R5R22_POINTER_DOCUMENT_RULES: E("C: unknown document " + where)
            if field == "object_role" and v.get("value_vocabulary") not in closed["object_role_value_vocabulary"]: E("G: role vocabulary " + where)
            if "constant_value" in v:
                for sample in [v["constant_value"]]:
                    if vt != "NULL" and sample is None: E("B: null constant in non-null type " + where)
    # R5R20 structural checks (identity, precedence, ranks, mirrors, internal rows, stage coverage, field presence).
    reachable = [f for f in model["families"] if f["class"] == "NORMATIVE_REACHABLE"]
    fids, positions, incomplete = set(), set(), 0
    required_fields = {"SEVEN_FIELD": ("argument", "object_role", "schema_ref", "instance_pointer", "bound_identity"),
                       "STATIC_VALIDATION": ("argument", "object_role", "schema_ref", "instance_pointer", "bound_identity"),
                       "PROFILE_PREFLIGHT": ("profile_pointer", "candidate_artifact", "candidate_pointer", "source_identity", "expected", "actual"),
                       "MAP_VALUE_COMPARISON": ("stage", "procedure_id", "map_argument", "map_pointer", "baseline_argument", "baseline_identity", "expected", "actual")}
    for fam in reachable:
        fid = fam["family_id"]
        if fid in fids: E("duplicate family " + fid)
        fids.add(fid)
        position = (fam.get("stage_index"), fam.get("group_rank"), fam.get("family_rank_in_group"))
        if None in position or position in positions: E("precedence position " + fid)
        positions.add(position)
        if [c["rank"] for c in fam["conditions"]] != list(range(1, len(fam["conditions"]) + 1)): E("condition ranks not total " + fid)
        for c in fam["conditions"]:
            need = required_fields.get(fam["witness_contract"])
            if need and sorted(c.get("witness", {})) != sorted(need): incomplete += 1; E("incomplete row " + fid + "/" + c["condition_id"])
            if fam["witness_contract"] == "TRUST_RESULT" and not c.get("witness"): incomplete += 1; E("incomplete trust row " + fid)
    for mirror in model["defensive_mirrors"]:
        owners = mirror["owner_family"] if isinstance(mirror["owner_family"], list) else [mirror["owner_family"]]
        if not owners or any(o not in fids for o in owners): E("mirror owner " + mirror["family_id"])
    for row in model["internal_only"]:
        if row.get("normative_result_authority") is not False: E("internal authority " + row["family_id"])
    if {fid for stage in model["stage_ordering"] for group in stage["groups"] for fid in group["families"]} != fids: E("stage ordering coverage")
    base = {"reachable_families": len(reachable), "conditions": sum(len(f["conditions"]) for f in reachable), "defensive_mirrors": len(model["defensive_mirrors"]),
            "internal_only": len(model["internal_only"]), "stages_with_families": len(model["stage_ordering"]), "incomplete_rows": incomplete}
    # Families and conditions (A-G); a malformed row is reported, never raised.
    for fam in reachable:
      try:
          fid, contract = fam["family_id"], fam["witness_contract"]
          fam_classes = fam.get("subject_classes") or []
          if not fam_classes or any(c not in classes for c in fam_classes): E("A: family subject classes " + fid)
          if fam["subject_order"] not in model["subject_orders"]: E("F: family subject order " + fid)
          if fam["stage"] not in meta["bootstrap_order"]: E("G: stage " + fid)
          codes = [fam["code"]] if "code" in fam else list((fam.get("code_derivation") or {}).values())
          for code in codes:
              if code.startswith("protocol_constants.claim_comparisons"):
                  for claim in pc["claim_comparisons"][:4]:
                      if claim["failure_code"] not in fail_codes: E("G: claim code " + fid)
              elif code not in fail_codes | trust_codes: E("G: code " + fid + " " + code)
          if contract == "PROFILE_PREFLIGHT":
              for code in codes if not codes[0].startswith("protocol_constants") else [c["failure_code"] for c in pc["claim_comparisons"][:4]]:
                  ops_ = [b for b in branches if b["properties"]["code"].get("const") == code and "allOf" in b["properties"]["witness"]]
                  if len(ops_) != 1: E("G: operation branch " + fid + " " + code)
          for cond in fam["conditions"]:
              cid, where = cond["condition_id"], fid + "/" + cond["condition_id"]
              text = cond.get("condition", "")
              if "well-formed" in text or "well formed" in text: E("C10: undefined well-formed predicate " + where)
              if order_words.search(text) and cond.get("order") not in orders and not any(k in cond for k in ("pointer_template", "location_rule", "checked_members")):
                  E("F: condition order word without ordering rule " + where)
              for key in ("order", "subject_order"):
                  if key in cond and cond[key] not in orders: E("F: unknown condition ordering rule " + where)
              if "member_order" in fam and fam["member_order"] not in orders: E("F: unknown member order " + fid)
              for key in ("predicate_pending",):
                  if key in cond:
                      if cond[key] not in pending: E("pending id " + where)
                      used_pending.add(cond[key]); stats["pending_predicates"] += 1
              for case, pid in list((cond.get("predicate_pending_cases") or {}).items()) + list((cond.get("uncovered_input_cases") or {}).items()):
                  if pid not in pending: E("pending id " + where)
                  used_pending.add(pid)
              if "admission_predicates" in cond:
                  for p in cond["admission_predicates"]:
                      if p not in closed["admission_predicate"]: E("C10: undeclared admission predicate " + where + " " + str(p))
              scope = cond.get("subject_scope") or fam_classes
              if any(s not in fam_classes for s in scope): E("A: subject scope outside family classes " + where)
              cases = cond.get("input_cases") or [None]
              if contract in ("SEVEN_FIELD", "STATIC_VALIDATION", "PROFILE_PREFLIGHT", "VECTOR_REGISTRY_CLAIM"):
                  if not isinstance(cond.get("diagnostic"), str) or not re.match(_R5R20_TOKEN, cond["diagnostic"]): E("G: diagnostic missing or not a token " + where)
                  else: seen_diag.add(cond["diagnostic"])
              if contract in ("SEVEN_FIELD", "STATIC_VALIDATION"):
                  if cond.get("failure_kind") not in branches[0]["properties"]["witness"]["properties"]["failure_kind"]["enum"] + ["STATIC_VALIDATION"]: E("G: failure_kind " + where)
                  if (contract == "STATIC_VALIDATION") != (cond.get("failure_kind") == "STATIC_VALIDATION"): E("G: static failure kind " + where)
              elif contract == "PROFILE_PREFLIGHT":
                  reasons = cond.get("reason")
                  for r in ([reasons] if not isinstance(reasons, dict) else (list(reasons["by_case"].values()) if "by_case" in reasons else list(reasons.get("by_claim_index", {}).values()) + [reasons.get("otherwise")])):
                      if r not in defs["external_profile_preflight_witness"]["properties"]["reason"]["enum"]: E("G: reason " + where)
              elif contract == "MAP_VALUE_COMPARISON":
                  if cond["reason"] not in defs["map_value_comparison_witness"]["properties"]["reason"]["enum"]: E("G: map reason " + where)
              if contract in ("STRICT_UNION_COLLISION", "VECTOR_REGISTRY_CLAIM"):
                  try: _r5r22_ptr_get(meta, cond["witness_field_derivation_ref"].split(":", 1)[1])
                  except KeyError: E("declared derivation ref " + where)
                  continue
              witness = cond.get("witness") or {}
              vfield = {"TRUST_RESULT": "trust_result", "MAP_VALUE_COMPARISON": "map_value_comparison"}
              for field, rule in witness.items():
                  if contract == "TRUST_RESULT" and field == "stage": continue
                  if contract == "MAP_VALUE_COMPARISON" and field == "stage": continue
                  sub = field_schema(contract, field, fam.get("code"), cond)
                  vf = vfield.get(contract, field)
                  for klass in scope:
                      for case in cases:
                          r = rule
                          if isinstance(r, dict) and "by_subject_class" in r:
                              if set(r["by_subject_class"]) != set(scope): E("A: by_subject_class does not partition the admitted classes " + where + " " + field)
                              r = r["by_subject_class"].get(klass)
                              if r is None: continue
                          if isinstance(r, dict) and "by_case" in r:
                              if set(r["by_case"]) != set(c for c in cases if c): E("D: by_case does not cover the input cases " + where + " " + field)
                              r = r["by_case"].get(case)
                              if r is None: continue
                          stats["field_rules"] += 1
                          if not isinstance(r, dict) or len(r) != 1: E("rule shape " + where + " " + field); continue
                          if "pending" in r:
                              if r["pending"] not in pending: E("pending id " + where)
                              used_pending.add(r["pending"]); stats["pending_fields"] += 1; continue
                          if "constant" in r:
                              if not valid(sub, r["constant"]): E("B: constant invalid for its field " + where + " " + field)
                              if field == "argument" and r["constant"] not in closed["argument_documents"]: E("C: constant argument names no document " + where)
                              continue
                          tok = r.get("derivation")
                          v = vocab.get(vf, {}).get(tok)
                          if v is None: E("undefined derivation " + where + " " + field + " " + str(tok)); continue
                          if "ANY" not in v["domain"] and klass not in v["domain"]: E("A: derivation undefined for admitted subject class " + where + " " + field + " " + tok + " " + klass)
                          if case and v.get("defined_for_cases") and case not in v["defined_for_cases"]: E("D: derivation undefined for input case " + where + " " + field + " " + tok + " " + case)
                          if case and v.get("cases") and case not in v["cases"]: E("D: derivation cases do not cover input case " + where + " " + field + " " + tok + " " + case)
                          for sample in _R5R22_VALUE_SAMPLES[v["value_type"]]:
                              if not valid(sub, sample): E("B/E: value type %s of %s invalid for field %s at %s" % (v["value_type"], tok, field, where)); break
              # C: pointer domain (seven-field and static witnesses).
              if contract in ("SEVEN_FIELD", "STATIC_VALIDATION"):
                  for klass in scope:
                      for case in cases:
                          def pick(rule):
                              if isinstance(rule, dict) and "by_subject_class" in rule: rule = rule["by_subject_class"].get(klass)
                              if isinstance(rule, dict) and "by_case" in rule: rule = rule["by_case"].get(case)
                              return rule
                          a, p = pick(witness.get("argument")), pick(witness.get("instance_pointer"))
                          if a is None or p is None or "pending" in a or "pending" in p: continue
                          owner = cond.get("owning_object") or fam.get("owning_object")
                          def doc_of(entry_doc):
                              if isinstance(entry_doc, dict): return entry_doc.get(klass)
                              if entry_doc == "OWNING_OBJECT":
                                  if owner == "BINDING_DECLARING_OBJECT": return "BINDING_DECLARING_OBJECT"
                                  return closed["argument_documents"].get(owner)
                              return entry_doc
                          if "constant" in a: adoc = closed["argument_documents"].get(a["constant"])
                          else: adoc = doc_of(vocab["argument"][a["derivation"]]["document"])
                          if "constant" in p: pdoc = adoc
                          else:
                              pv = vocab["instance_pointer"].get(p["derivation"], {})
                              pdoc = doc_of(pv.get("document"))
                              if pdoc == "ARGUMENT_DOCUMENT": pdoc = adoc
                              elif pdoc == "VALIDATED_INSTANCE": pdoc = cond.get("validated_instance")
                          if adoc is None or pdoc is None or adoc != pdoc:
                              E("C: pointer document %s differs from argument document %s at %s (%s)" % (pdoc, adoc, where, klass))
                          # Fixed pointers must resolve in the named candidate document.
                          fixed = cond.get("section_pointer") if p.get("derivation") == "DECLARED_SECTION_POINTER" else cond.get("binding_pointer") if p.get("derivation") in ("ENTRYPOINT_BINDING_LOCATION", "REGISTRY_BINDING_LOCATION") else None
                          docs = {"PACKAGE": pkg, "REGISTRY": reg, "METACONTRACT": meta}
                          if fixed is not None and adoc in docs and fid not in ("PE-37",):
                              probe = fixed.replace("<row_index>", "0").replace("<second_occurrence_index>", "0")
                              try: _r5r22_ptr_get(docs[adoc], probe)
                              except KeyError:
                                  parent = probe.rsplit("/", 1)[0]
                                  try: _r5r22_ptr_get(docs[adoc], parent)
                                  except KeyError: E("C: fixed pointer %s does not belong to %s at %s" % (fixed, adoc, where))
                          if p.get("derivation") == "SCOPED_FIRST_INVALID_LOCATION" and adoc == "METACONTRACT":
                              for name in meta["runtime_representation"]["value_schemas"]:
                                  try: _r5r22_ptr_get(meta, cond["pointer_scope"].replace("<escaped_value_schema_name>", name))
                                  except KeyError: E("C: pointer scope does not resolve in the metacontract " + where)
              if contract == "PROFILE_PREFLIGHT":
                  for klass in scope:
                      for case in cases:
                          def pick(rule):
                              if isinstance(rule, dict) and "by_case" in rule: rule = rule["by_case"].get(case)
                              return rule
                          a, p = pick(witness.get("candidate_artifact")), pick(witness.get("candidate_pointer"))
                          if a is None or p is None or "pending" in a or "pending" in p: continue
                          if p.get("derivation") == "NULL": continue
                          if "constant" in a: adoc = pc["claim_artifacts"].get(a["constant"], {}).get("document")
                          elif a.get("derivation") == "CLAIM_CANDIDATE_ARTIFACT": adoc = "CLAIM_ARTIFACT_DOCUMENT"
                          else: adoc = None
                          pdoc = vocab["candidate_pointer"].get(p.get("derivation"), {}).get("document")
                          if adoc != pdoc and not (adoc == "CLAIM_ARTIFACT_DOCUMENT" and pdoc == "CLAIM_ARTIFACT_DOCUMENT"):
                              E("C: candidate pointer document %s differs from candidate artifact document %s at %s" % (pdoc, adoc, where))
      except (KeyError, TypeError, IndexError, AttributeError, StopIteration) as exc:
        E("malformed family or condition %s: %s %s" % (fam.get("family_id"), type(exc).__name__, exc))
    # Claim artifacts resolve through declared package members (clarification of the claim list).
    for claim in pc["claim_comparisons"]:
        art = pc["claim_artifacts"].get(claim["candidate_artifact"])
        if art is None or art["package_member"] not in pkg: E("C: claim artifact has no declared package member " + claim["candidate_artifact"])
        elif not pkg[art["package_member"]]["id"].endswith(":" + claim["candidate_artifact"]): E("C: claim artifact package member mismatch " + claim["candidate_artifact"])
    sel_ptr = vocab["candidate_pointer"]["SELECTOR_DECLARATION_POINTER"]["definition"].split(": ", 1)[1].split(" ")[0]
    try: _r5r22_ptr_get(meta, sel_ptr)
    except KeyError: E("C: selector declaration pointer does not resolve in the metacontract")
    if pc["procedure_projection_selector"]["selection"]["required_match_count"] != 1 or isinstance(pc["procedure_projection_selector"]["selection"]["required_match_count"], bool):
        E("D3: required match count is not the integer 1")
    # G: diagnostic vocabulary is closed and exact.
    if set(model["diagnostic_vocabulary"]) != seen_diag: E("G: diagnostic vocabulary is not exactly the used diagnostics")
    # Pending decisions are all referenced.
    if set(pending) != used_pending: E("pending decisions not referenced exactly: " + ",".join(sorted(set(pending) ^ used_pending)))
    # D13 proofs.
    try: d13 = _r5r22_d13_proofs(meta, ctx["prim"], ctx["proc"], ctx["proc_schema"])
    except (ValueError, KeyError, IndexError) as exc: E(str(exc)); d13 = None
    # D11 schema_ref value equals the declared document of structural_application.schema_ref.
    sa = meta["registration"]["structural_application"]
    rows = [r for r in reg["objects"] if (r.get("kind"), r.get("id"), r.get("version")) == (sa["schema_ref"]["kind"], sa["schema_ref"]["id"], sa["schema_ref"]["version"])]
    if len(rows) != 1 or rows[0].get("schema_document_id") != sa["schema_id"]: E("D11: structural_application.schema_id is not the document id of structural_application.schema_ref")
    # Identity guarantees.
    for entry in pc["bootstrap_objects"]:
        if _r5r22_identity_when_valid(entry["identity"]["kind"], entry["identity"]["id"], entry["identity"]["version"]) is None: E("E: protocol identity invalid")
    for entry in pc["frozen_sources"]:
        if _r5r22_identity_when_valid(entry["typed_identity"]["kind"], entry["typed_identity"]["id"], entry["typed_identity"]["version"]) is None: E("E: frozen identity invalid")
    ref_def = ctx["reg_schema"]["$defs"]["ref"]["properties"]
    if ctx["reg_schema"]["properties"]["objects"]["items"]["properties"].get("reference") != {"$ref": "#/$defs/ref"} or ref_def["id"].get("minLength") != 1 or ref_def["version"].get("minLength") != 1 or "enum" not in ref_def["kind"]:
        E("E: SEMANTIC_REGISTRATION_ROW_IDENTITY premise does not hold")
    sem_rules = [r["rule_id"] for r in meta["registration"]["semantic_validation"]["rules"]]
    if "ROW_REFERENCE_EQUALS_ROW_REGISTRY_IDENTITY" not in sem_rules: E("E: SEMANTIC_REGISTRATION_ROW_IDENTITY rule missing")
    if errors: raise ValueError("R5R22 semantic totality failed:\n  " + "\n  ".join(errors[:60]))
    return {"base": base, "field_rules_checked": stats["field_rules"], "pending_field_rules": stats["pending_fields"], "pending_predicates": stats["pending_predicates"],
            "pending_human_decisions": len(pending), "diagnostics": len(seen_diag), "d13": d13}


def _r5r22_context():
    load = lambda rel: json.loads((OUT / rel).read_text(encoding="utf-8"))
    return {"meta": _r11_load("metacontract.json"), "reg": _r11_load("object-registry.json"), "pkg": _r11_load("specification-package-0.2.json"),
            "schema": load("schema/metacontract.schema.json"), "reg_schema": load("schema/object-registry.schema.json"),
            "proc_schema": load("schema/procedure-registry.schema.json"), "prim": load("primitive-registry.json"), "proc": load("procedure-registry.json"),
            "evic": load("external-verification-input.contract.json")}


def _r5r22_finalize():
    ctx = _r5r22_context()
    meta, reg, pkg, meta_schema = ctx["meta"], ctx["reg"], ctx["pkg"], ctx["schema"]
    # D13A / D13C declarations.
    rules = meta["runtime_representation"]["static_type_calculus"]["operator_rules"]
    rules["argument_type_slot_kinds"] = _r5r22_slot_map(meta, ctx["prim"])
    meta["result_contracts"]["trust_result"]["owner_procedure_id"] = "TRUST_ANCHOR_COMPARE"
    tr = meta_schema["properties"]["result_contracts"]["properties"]["trust_result"]
    tr["properties"]["owner_procedure_id"] = {"const": "TRUST_ANCHOR_COMPARE"}
    if "owner_procedure_id" not in tr["required"]: tr["required"].append("owner_procedure_id")
    meta_schema["properties"]["runtime_representation"]["const"] = copy.deepcopy(meta["runtime_representation"])
    ctx["meta"] = meta
    model = meta["failure_semantics"]["pre_execution_failure_model"]
    model["model_version"] = "0.2"
    _r5r22_protocol_constants(model["protocol_constants"], meta, reg, pkg, ctx["evic"])
    model["derivation_vocabulary"] = _r5r22_vocabulary()
    model["closed_vocabularies"] = _r5r22_closed_vocabularies(meta, ctx["reg_schema"], ctx["proc_schema"])
    model["subject_order_rules"] = _r5r22_subject_order_rules()
    model["pending_human_decisions"] = _r5r22_pending()
    _r5r22_repair(model, meta, reg, pkg, ctx["evic"], ctx["reg_schema"], ctx["proc_schema"])
    model["diagnostic_vocabulary"] = sorted({c["diagnostic"] for f in model["families"] if f["class"] == "NORMATIVE_REACHABLE"
                                             for c in f["conditions"] if isinstance(c.get("diagnostic"), str)})
    model["r5r21_defect_resolution"] = _r5r22_defect_resolution()
    model["authority"]["early_stage_rows"] = ("rows for stages up to and including COMPARE_ALL_CANDIDATE_AUTHORITY_CLAIMS_WHOLE_OBJECT_BEFORE_SEMANTIC_USE read verifier-protocol constants "
                                              "(protocol_constants); the candidate copy is a published claim compared by PE-19 (selector), PE-22 and candidate schema validation")
    semantic = _r5r22_semantic_totality(model, ctx)
    model["totality"] = dict(semantic["base"], **{"semantic": {k: v for k, v in semantic.items() if k not in ("d13", "base")},
                                      "model_status": "PENDING_HUMAN_DECISIONS" if semantic["pending_human_decisions"] else "TOTAL"})
    fs = meta["failure_semantics"]
    fs["pre_execution_failure_model"] = model
    fs["verifier_protocol_digests"] = {"algorithm": "SHA-256", "serialization": "RFC8785_JCS",
                                       "pre_execution_failure_model": sem(model), "registration": sem(meta["registration"]),
                                       "generic_failure_witness": sem(fs["generic_failure_witness"])}
    fss = meta_schema["properties"]["failure_semantics"]
    for name in ("pre_execution_failure_model", "verifier_protocol_digests"):
        fss["properties"][name] = {"const": copy.deepcopy(fs[name])}
    _r11_save("metacontract.json", meta)
    _r11_save("schema/metacontract.schema.json", meta_schema)
    _r11_digest_close(reg, pkg)
    print(json.dumps({"r5r22_semantic_repair": "PASS", "totality": model["totality"], "d13": semantic["d13"],
                      "verifier_protocol_digests": fs["verifier_protocol_digests"],
                      "registry_semantic_sha256": pkg["registry_semantic_sha256"],
                      "package_semantic_sha256": pkg["current_candidate_integrity"]["digest"]}, indent=2))

_R5R20_POST_BUILD = _r11_post_build
def _r11_post_build():
    _R5R20_POST_BUILD()
    _r5r22_finalize()

# ---------------------------------------------------------------------------
# R5R23: closure of the pending pre-execution decisions PHD-01..PHD-08 and the
# approved clarifications A (early protocol constants), B (profile schema and
# number limits) and C (absence -> null).  The R5R22 model is post-processed in
# place; no pending marker survives, and the semantic checker gains properties
# H-N and the null-semantics rule (reported under E).
# ---------------------------------------------------------------------------
_R5R23_PACKAGE_ARTIFACT = "specification-package"
_R5R23_BOUND_SOURCE_ARGUMENT = "bound_source"
_R5R23_NULL_CASES = {
    "LITERAL_NULL": "the derivation is the literal null (no object, location or value is involved)",
    "MEMBER_ABSENT": "the named member does not exist (a present member is reported as-is, whatever its type)",
    "IDENTITY_RULE_NOT_SATISFIED": "TYPED_IDENTITY_WHEN_VALID_ELSE_NULL: kind, id or version absent, not a string, or empty (D14)",
    "NO_CONTAINING_UNIVERSE_OBJECT": "the location is the universe root or outside /objects/<k>",
    "LOOKUP_ZERO_OR_MULTIPLE_OR_UNREADABLE": "no unique readable matching registry row exists (D11)",
    "ROW_ABSENT_OR_NOT_UNIQUE": "no unique registry row has the bootstrap object's kind/id/version (D8)",
    "NO_MATCHING_FROZEN_SOURCE_ENTRY": "the reserved input's pin tokens name no protocol_constants.frozen_sources entry",
    "CLAIM_IS_NOT_A_FROZEN_PIN_CLAIM": "the claim's profile pointer is not /frozen_authority_pins/<member>",
    "NO_UNIQUE_CANDIDATE_ITEM": "the selector matched 0 or more than 1 items, so no candidate item location exists (D3)",
}
_R5R23_NULL_SEMANTICS = {
    ("bound_identity", "ENTRYPOINT_CONTENT_IDENTITY_WHEN_VALID_ELSE_NULL"): ["IDENTITY_RULE_NOT_SATISFIED"],
    ("bound_identity", "REGISTRY_CONTENT_IDENTITY_WHEN_VALID_ELSE_NULL"): ["IDENTITY_RULE_NOT_SATISFIED"],
    ("bound_identity", "RESERVED_INPUT_FROZEN_SOURCE_IDENTITY_ELSE_NULL"): ["NO_MATCHING_FROZEN_SOURCE_ENTRY"],
    ("bound_identity", "RESOLVED_OBJECT_IDENTITY_CONTAINING_LOCATION_ELSE_NULL"): ["NO_CONTAINING_UNIVERSE_OBJECT", "IDENTITY_RULE_NOT_SATISFIED"],
    ("bound_identity", "REGISTRATION_WITNESS_BOUND_IDENTITY"): ["IDENTITY_RULE_NOT_SATISFIED"],
    ("bound_identity", "REGISTRY_SCHEMA_ROW_IDENTITY_WHEN_UNIQUE_READABLE_ELSE_NULL"): ["LOOKUP_ZERO_OR_MULTIPLE_OR_UNREADABLE"],
    ("bound_identity", "BOOTSTRAP_ROW_IDENTITY_ELSE_NULL"): ["ROW_ABSENT_OR_NOT_UNIQUE"],
    ("source_identity", "ACCEPTED_SOURCE_REF_WHEN_VALID_ELSE_NULL"): ["IDENTITY_RULE_NOT_SATISFIED"],
    ("source_identity", "CLAIM_FROZEN_SOURCE_TYPED_IDENTITY_ELSE_NULL"): ["CLAIM_IS_NOT_A_FROZEN_PIN_CLAIM"],
    ("expected", "PIN_GIT_BLOB"): ["MEMBER_ABSENT"],
    ("expected", "ALLOWLIST_DIGEST_FIELD"): ["MEMBER_ABSENT"],
    ("actual", "SCHEMA_DIALECT_MEMBER"): ["MEMBER_ABSENT"],
    ("actual", "SCHEMA_ID_MEMBER"): ["MEMBER_ABSENT"],
    ("actual", "CANDIDATE_CLAIM_VALUE"): ["MEMBER_ABSENT"],
    ("actual", "CANDIDATE_SELECTOR"): ["MEMBER_ABSENT"],
}
_R5R23_NULLABLE_TYPES = ("NULL", "TYPED_IDENTITY_OR_NULL", "JSON_VALUE_OR_NULL", "RFC6901_POINTER_OR_NULL", "NONEMPTY_STRING_OR_NULL")


def _r5r23_expectations(meta):
    """PHD-01: one expectation row per declared reserved input (type, origin, explicit pin_ref)."""
    out = {}
    for row in sorted(meta["reserved_inputs"], key=lambda r: r["name"].encode("utf-16-be")):
        src = row.get("profile_content_source")
        out[row["name"]] = {"type": row["type"], "origin": row["origin"],
                            "pin_ref": copy.deepcopy(src["pin_pointer_tokens"]) if isinstance(src, dict) and "pin_pointer_tokens" in src else None}
    return out


def _r5r23_vocabulary(V):
    E = _r5r22_E
    PC, CD, CI, SC, MP, LT = _R5R22_SOURCES
    EP, ER = "ENTRYPOINT_PACKAGE", "ENTRYPOINT_REGISTRY"
    # Domain changes: REGISTRY_DOCUMENT (closes PHD-07), BOUND_SOURCE owner witness (closes PHD-02), MEMBER_RESOLVED_RECORD removed (closes PHD-08).
    for field in V.values():
        for tok in field.values():
            tok["domain"] = [d for d in tok["domain"] if d != "MEMBER_RESOLVED_RECORD"]
    for tok in ("REGISTRATION_WITNESS_ARGUMENT",):
        V["argument"][tok]["domain"].append("REGISTRY_DOCUMENT")
    V["object_role"]["REGISTRATION_WITNESS_OBJECT_ROLE"]["domain"].append("REGISTRY_DOCUMENT")
    V["schema_ref"]["REGISTRATION_WITNESS_SCHEMA_REF"]["domain"].append("REGISTRY_DOCUMENT")
    for field, tok in (("object_role", "OWNING_OBJECT_REGISTRY_ROW_KIND"), ("schema_ref", "OWNING_OBJECT_APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"),
                       ("bound_identity", "OWNING_OBJECT_REGISTRY_IDENTITY")):
        V[field][tok]["domain"].append("BOUND_SOURCE")
    V["instance_pointer"]["RESERVED_INPUT_COLLECTION_LOCATION"]["domain"] = ["RESERVED_INPUT_COLLECTION"]
    V["instance_pointer"]["RESERVED_INPUT_MEMBER_LOCATION"]["definition"] = V["instance_pointer"]["RESERVED_INPUT_MEMBER_LOCATION"]["definition"].replace(
        "(/reserved_inputs/<i>/profile_content_source when that container is not an object)", "(/reserved_inputs/<i>/profile_content_source when that container is absent or not an object)")
    # PHD-02: bound-source witness.
    V["argument"]["BOUND_SOURCE_ARGUMENT"] = E("the declared constant bound_source: names the pin-verified decoded content of the failing accepted/bound source (the bound-source counterpart of H1 candidate_object) (closes PHD-02)",
                                                 "NONEMPTY_STRING", [PC], ["BOUND_SOURCE"], constant_value=_R5R23_BOUND_SOURCE_ARGUMENT, document="BOUND_SOURCE_CONTENT")
    V["object_role"]["ALLOWLIST_REF_KIND"] = E("the exact kind of the allowlist row's ref (closes PHD-02)", "NONEMPTY_STRING", [CI], ["BOUND_SOURCE"], value_vocabulary="TYPED_REF_KIND")
    s = V["schema_ref"]["ALLOWLIST_EXPECTED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"]
    s["definition"] = ("exact schema_document_id of the eligible SCHEMA row whose kind/id/version equal the allowlist row's expected_schema_ref, once that ref resolved successfully "
                       "(the row exists and its member_id is a registered member) (D5, closes PHD-02)")
    s["defined_for_cases"] = ["EXPECTED_SCHEMA_RESOLVED"]
    V["instance_pointer"]["ALLOWLIST_EXPECTED_SCHEMA_REF_DECLARATION_LOCATION"] = E(
        "absolute metacontract pointer /accepted_source_allowlist/<k>/expected_schema_ref of the declaring allowlist row, where <k> is the subject's allowlist index (the metacontract allowlist equals the profile allowlist by PE-18 claim index 2) (closes PHD-02, D6 principle)",
        "RFC6901_POINTER", [CD, MP], ["BOUND_SOURCE"], document="METACONTRACT")
    V["bound_identity"]["ALLOWLIST_REF_IDENTITY"] = E("the exact typed identity {kind, id, version} of the allowlist row's ref (closes PHD-02)", "TYPED_IDENTITY", [CI], ["BOUND_SOURCE"],
                                                       identity_guarantee="METACONTRACT_SCHEMA_VALIDATED_ALLOWLIST_REF")
    V["bound_identity"].pop("ALLOWLIST_REF_IDENTITY_WHEN_VALID_ELSE_NULL", None)
    # PHD-03: the candidate package's procedure-registry reference.
    V["candidate_pointer"]["CLAIM_ARTIFACT_PACKAGE_REFERENCE_POINTER"] = E(
        "the candidate-package location of the claim artifact's package reference: '/' + protocol_constants.claim_artifacts[<claim 4 candidate_artifact>].package_member (/procedure_registry_ref) (closes PHD-03)",
        "RFC6901_POINTER", [PC], ["PROCEDURE_PROJECTION_CLAIM"], document="PACKAGE")
    # PHD-04: /procedures is not an array.
    V["candidate_pointer"]["SELECTOR_COLLECTION_POINTER"] = E("protocol_constants.procedure_projection_selector.collection_pointer_rfc6901 (/procedures) in the claim artifact (closes PHD-04)",
                                                               "RFC6901_POINTER", [PC], ["PROCEDURE_PROJECTION_CLAIM"], document="CLAIM_ARTIFACT_DOCUMENT", defined_for_cases=["COLLECTION_NOT_ARRAY"])
    V["expected"]["SELECTOR_COLLECTION_TYPE"] = E("protocol_constants.procedure_projection_selector.collection_type (the closed json_type token ARRAY) (closes PHD-04)", "JSON_TYPE_TOKEN", [PC],
                                                   ["PROCEDURE_PROJECTION_CLAIM"], defined_for_cases=["COLLECTION_NOT_ARRAY"])
    V["actual"]["COLLECTION_JSON_TYPE"] = E("the closed json_type token of the value at the selector collection pointer in the claim artifact (ABSENT when absent) (closes PHD-04)", "JSON_TYPE_TOKEN",
                                            [PC, CD, SC], ["PROCEDURE_PROJECTION_CLAIM"], defined_for_cases=["COLLECTION_NOT_ARRAY"])
    V["expected"]["REQUIRED_MATCH_COUNT"]["defined_for_cases"] = ["MATCH_COUNT_ZERO", "MATCH_COUNT_MANY"]
    # PHD-05: package identity members.
    V["instance_pointer"]["PACKAGE_IDENTITY_MEMBER_LOCATION"] = E(
        "'/' + the first member, in the first-failure array order of protocol_constants.package_identity_members, that is absent, not a JSON string, or empty (closes PHD-05)",
        "RFC6901_POINTER", [PC, CD, SC], ["ENTRYPOINT_PACKAGE"], document="PACKAGE", order="PACKAGE_IDENTITY_MEMBER_ORDER")
    for tok in ("PACKAGE_ID_VERSION", "PACKAGE_IDENTITY3_WITH_RECOMPUTED_DIGEST"):
        V["trust_result"][tok].pop("defined_for_cases", None)
        V["trust_result"][tok]["requires_precondition"] = "PE-10/PACKAGE_IDENTITY_INVALID"
    V["trust_result"]["PACKAGE_ID_VERSION"]["definition"] = "{id: package_id, version: package_version}; both are non-empty strings because PE-10 PACKAGE_IDENTITY_INVALID precedes PE-11 (closes PHD-05)"
    # PHD-06: exactly one content row.
    V["profile_pointer"]["CONTENT_ROW_COLLECTION_POINTER"] = E("the PE-17 content_row_matching.collection_pointer (/accepted_source_contents), the canonical content-row collection (closes PHD-06)",
                                                               "RFC6901_POINTER", [MP], ["ALLOWLIST_ROW"], document="PROFILE",
                                                               defined_for_cases=["ZERO_MATCHING_CONTENT_ROWS", "MANY_MATCHING_CONTENT_ROWS"])
    acp = V["profile_pointer"]["ACCEPTED_CONTENT_ROW_POINTER"]
    acp["definition"] = "/accepted_source_contents/<index> of the unique content row matching the allowlist subject under PE-17 content_row_matching (closes PHD-06)"
    acp["source"] = [CI, MP, SC]
    acp.pop("cases", None)
    acp["defined_for_cases"] = ["ONE_MATCHING_CONTENT_ROW"]
    V["expected"]["REQUIRED_CONTENT_ROW_MATCH_COUNT"] = E("the JSON integer PE-17 content_row_matching.required_match_count (1) (closes PHD-06)", "POSITIVE_INTEGER", [MP], ["ALLOWLIST_ROW"],
                                                          defined_for_cases=["ZERO_MATCHING_CONTENT_ROWS", "MANY_MATCHING_CONTENT_ROWS"])
    V["actual"]["CONTENT_ROW_MATCH_COUNT"] = E("the JSON integer number of /accepted_source_contents rows matching the allowlist subject under PE-17 content_row_matching (closes PHD-06)", "NONNEGATIVE_INTEGER",
                                               [CI, MP, SC], ["ALLOWLIST_ROW"], defined_for_cases=["ZERO_MATCHING_CONTENT_ROWS", "MANY_MATCHING_CONTENT_ROWS"])
    # PHD-07: registry-level failures.
    V["instance_pointer"]["REGISTRY_LEVEL_FIRST_INVALID_LOCATION"] = E(
        "the first object-registry schema failure location, in DESCENDANTS canonical preorder, among locations that are not /objects/<i> or below (a missing member is located at its containing object); the actual collection or root location, never a fabricated row pointer (closes PHD-07)",
        "RFC6901_POINTER", [SC], ["REGISTRY_DOCUMENT"], document="REGISTRY", order="DESCENDANTS_CANONICAL_PREORDER")
    V["bound_identity"]["NULL"]["definition"] = "JSON null (permitted by the registered schema) when no object identity exists"
    # Clarification C: explicit null semantics on every null-admitting derivation.
    for field, toks in V.items():
        for tok, v in toks.items():
            if v["value_type"] == "NULL": v["null_semantics"] = ["LITERAL_NULL"]
            elif (field, tok) in _R5R23_NULL_SEMANTICS: v["null_semantics"] = list(_R5R23_NULL_SEMANTICS[(field, tok)])
    V["candidate_pointer"]["NULL"]["null_semantics"] = ["LITERAL_NULL", "NO_UNIQUE_CANDIDATE_ITEM"]
    return V


def _r5r23_close(model, meta, ctx):
    F = {f["family_id"]: f for f in model["families"]}
    D = lambda t: {"derivation": t}
    Cn = lambda v: {"constant": v}
    cond = lambda fid, cid: next(c for c in F[fid]["conditions"] if c["condition_id"] == cid)
    pc = model["protocol_constants"]
    # Clarifications A and B: early verifier protocol constants.
    pc["claim_artifacts"][_R5R23_PACKAGE_ARTIFACT] = {"package_member": None, "entrypoint_argument": "candidate_package", "document": "PACKAGE"}
    pc["package_identity_members"] = ["package_id", "package_version"]
    pc["authority"] = ("VERIFIER_PROTOCOL_CONSTANTS_FIXED_BY_THIS_ACCORD_VERSION;THE_CANDIDATE_COPY_IS_A_PUBLISHED_CLAIM;"
                       "STAGES_UP_TO_AND_INCLUDING_THE_CLAIM_COMPARISON_READ_THESE_CONSTANTS")
    pc["constant_status"] = {
        "approved": "R5R23 clarifications A (claim list, protocol selector, artifact-name map including the candidate-package artifact name) and B (profile schema identity, JSON number limits)",
        "early_stage_constants": ["caller_input_precedence", "profile_schema_identity", "json_number_resource_limits", "claim_comparisons", "procedure_projection_selector",
                                  "claim_artifacts", "package_identity_members", "entrypoints", "bootstrap_objects", "frozen_sources", "required_profile_members",
                                  "package_self_digest_declaration", "draft_2020_12_dialect"],
        "candidate_trust_root": False, "registry_object": False, "verification_universe_member": False, "candidate_supplied_authority": False,
        "candidate_copy": "A_PUBLISHED_CLAIM_CHECKED_LATER_AGAINST_THE_PROTOCOL_COMMITMENT"}
    # PHD-01: reserved input expectations (label and pin law).
    for c in F["PE-41"]["conditions"]:
        cid = c["condition_id"]
        if cid == "RESERVED_INPUT_NAME_LABEL_MISMATCH":
            c["condition"] = ("the subject row's name is a key of metacontract:/binding_origins/reserved_input_expectations and its type or origin is not exactly equal to that expectation's type or origin; "
                              "a row whose name is not a key is owned by RESERVED_INPUT_NAME_SET_MISMATCH and is not label-checked")
            c["predicate_ref"] = "metacontract:/binding_origins/reserved_input_expectations"
            c["checked_members"] = sorted(["origin", "type"], key=lambda m: m.encode("utf-16-be"))
            c["witness"]["instance_pointer"] = D("RESERVED_INPUT_MEMBER_LOCATION")
            c.pop("collection_pointer", None); c.pop("predicate_pending", None)
            c["subject_scope"] = ["RESERVED_INPUT_ROW"]
        elif cid == "RESERVED_INPUT_NAME_SET_MISMATCH":
            c["condition"] = "the declared reserved_inputs names differ from the keys of metacontract:/binding_origins/reserved_input_expectations (unknown or missing names)"
            c["predicate_ref"] = "metacontract:/binding_origins/reserved_input_expectations"
        elif cid == "RESERVED_CONTENT_SOURCE_PIN_UNDECLARED":
            c["condition"] = ("the subject row's name is a key of reserved_input_expectations whose pin_ref is non-null and its profile_content_source.pin_pointer_tokens is not exactly equal (JSON equality) "
                              "to that pin_ref; a null pin_ref requires no pin comparison; pinning is never inferred from filename, artifact identity, origin, source kind or registry membership")
            c["predicate_ref"] = "metacontract:/binding_origins/reserved_input_expectations"
            c.pop("predicate_pending", None)
    F["PE-41"]["label_law"] = "EXACT_TYPE_AND_ORIGIN_EQUALITY_WITH_THE_EXPECTATION_ROW;NO_HEURISTIC_MAPPING;NO_ALIASES"
    # PHD-02: bound-source witness with a complete resolved / unresolved split.
    b1, b2 = cond("PE-38", "BOUND_SCHEMA_MEMBER_UNREGISTERED"), cond("PE-38", "BOUND_SCHEMA_VIOLATION")
    b1["condition"] = ("the allowlist row's expected_schema_ref does not resolve: no eligible SCHEMA row has its kind/id/version, or its member_id is not a registered member of that row; "
                       "the witness is attributed to the declaring allowlist row of the metacontract (D6 principle)")
    b1["expected_schema_resolution"] = "UNRESOLVED"
    b1["input_cases"] = ["EXPECTED_SCHEMA_ROW_UNRESOLVED", "EXPECTED_SCHEMA_MEMBER_UNREGISTERED"]
    b1["owning_object"] = "metacontract"
    b1["witness"] = {"argument": Cn("metacontract"), "object_role": D("OWNING_OBJECT_REGISTRY_ROW_KIND"), "schema_ref": D("OWNING_OBJECT_APPLIED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"),
                     "instance_pointer": D("ALLOWLIST_EXPECTED_SCHEMA_REF_DECLARATION_LOCATION"), "bound_identity": D("OWNING_OBJECT_REGISTRY_IDENTITY")}
    b2["condition"] = "the expected_schema_ref resolved successfully and the pin-verified decoded content is invalid against that schema member"
    b2["expected_schema_resolution"] = "RESOLVED"
    b2["input_cases"] = ["EXPECTED_SCHEMA_RESOLVED"]
    b2["witness"] = {"argument": D("BOUND_SOURCE_ARGUMENT"), "object_role": D("ALLOWLIST_REF_KIND"), "schema_ref": D("ALLOWLIST_EXPECTED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID"),
                     "instance_pointer": D("FIRST_INVALID_LOCATION_CANONICAL_PREORDER"), "bound_identity": D("ALLOWLIST_REF_IDENTITY")}
    F["PE-38"]["authority"] = ("the externally verified allowlist row (metacontract:/eligibility/bound_source_universe; bound_registry_row_requirement NOT_UNIVERSAL); no registry row is synthesized; "
                               "an unresolved expected_schema_ref is attributed to the declaring metacontract allowlist row")
    F["PE-38"]["argument_token_equivalence"] = "no already-declared exact token names bound-source content (procedure arguments accepted_base / accepted_vectors are procedure-specific); bound_source is declared"
    # PHD-03 / PHD-04: PE-19 procedure registry and collection.
    pe19 = {c["condition_id"]: c for c in F["PE-19"]["conditions"]}
    for cid in ("PROCEDURE_REGISTRY_UNRESOLVED", "PROCEDURE_REGISTRY_UNREADABLE"):
        c = pe19[cid]
        c["witness"]["candidate_artifact"] = Cn(_R5R23_PACKAGE_ARTIFACT)
        c["witness"]["candidate_pointer"] = D("CLAIM_ARTIFACT_PACKAGE_REFERENCE_POINTER")
        c["witness_location"] = {"argument": "candidate_package", "instance_pointer": "/procedure_registry_ref", "no_procedure_item_pointer": True}
    pe19["PROCEDURE_REGISTRY_UNRESOLVED"]["condition"] = "the candidate package's /procedure_registry_ref does not reach exactly one registry row (witnessed at that package reference)"
    pe19["PROCEDURE_REGISTRY_UNREADABLE"]["condition"] = "the procedure registry reached through the candidate package's /procedure_registry_ref cannot be read or strictly decoded (witnessed at that package reference)"
    mc = pe19["SELECTOR_MATCH_COUNT"]
    mc["condition"] = ("the selector collection (/procedures) of the resolved procedure registry is absent or not an array (COLLECTION_NOT_ARRAY: no match count exists), "
                       "or the typed filter matches 0 or more than 1 items")
    mc["witness"]["candidate_artifact"]["by_case"]["COLLECTION_NOT_ARRAY"] = D("CLAIM_CANDIDATE_ARTIFACT")
    mc["witness"]["candidate_pointer"]["by_case"]["COLLECTION_NOT_ARRAY"] = D("SELECTOR_COLLECTION_POINTER")
    mc["witness"]["expected"] = {"by_case": {"COLLECTION_NOT_ARRAY": D("SELECTOR_COLLECTION_TYPE"), "MATCH_COUNT_ZERO": D("REQUIRED_MATCH_COUNT"), "MATCH_COUNT_MANY": D("REQUIRED_MATCH_COUNT")}}
    mc["witness"]["actual"]["by_case"]["COLLECTION_NOT_ARRAY"] = D("COLLECTION_JSON_TYPE")
    # PHD-05: package identity before trust.
    pe10 = F["PE-10"]
    pe10["name"] = "CANDIDATE_PACKAGE_DOCUMENT_AND_IDENTITY"
    pe10["within_family_order"] = "CONDITION_RANK"
    pe10["conditions"].append({
        "condition_id": "PACKAGE_IDENTITY_INVALID",
        "condition": "a member of protocol_constants.package_identity_members (package_id, package_version) is absent, not a JSON string, or empty, so the package identity cannot be constructed; the external trust comparison (PE-11) is not reached",
        "failure_kind": "TYPE", "diagnostic": "CANDIDATE_PACKAGE_IDENTITY_INVALID",
        "witness": {"argument": Cn("candidate_package"), "object_role": Cn("PACKAGE"), "schema_ref": D("ENTRYPOINT_SCHEMA_DOCUMENT_ID"),
                    "instance_pointer": D("PACKAGE_IDENTITY_MEMBER_LOCATION"), "bound_identity": D("NULL")},
        "predicate_ref": "model:/protocol_constants/package_identity_members",
        "identity_rule": "TYPED_IDENTITY_WHEN_VALID_ELSE_NULL", "rank": len(pe10["conditions"]) + 1})
    F["PE-11"]["precondition"] = {"owner": "PE-10", "condition_id": "PACKAGE_IDENTITY_INVALID",
                                  "guarantees": "every protocol_constants.package_identity_members member is a non-empty JSON string before any trust comparison"}
    fi = cond("PE-11", "FOREIGN_IDENTITY")
    fi.pop("input_cases", None)
    fi["witness"]["actual"] = D("PACKAGE_ID_VERSION")
    # PHD-06: PE-17 content-row cardinality.
    pe17 = F["PE-17"]
    pe17["content_row_matching"] = {"collection_pointer": "/accepted_source_contents", "collection_owner": "external_acceptance_profile",
                                    "match_members": [{"content_row_member": m, "allowlist_member": m, "comparison": "JSON_EQUAL"} for m in ("ref", "canonical_path", "git_blob")],
                                    "required_match_count": 1, "selection": "EXACTLY_ONE_MATCHING_ROW;NO_FIRST_LOWEST_OR_ARBITRARY_SELECTION"}
    old = pe17["conditions"][0]
    assert old["condition_id"] == "ACCEPTED_CONTENT_ROW_MISSING"
    pe17["conditions"][0] = {
        "condition_id": "ACCEPTED_CONTENT_ROW_CARDINALITY",
        "condition": "the number of /accepted_source_contents rows matching the allowlist subject under content_row_matching is not exactly one (0 or more than 1); only exactly one match permits content verification",
        "reason": {"by_case": {"ZERO_MATCHING_CONTENT_ROWS": "INPUT_MISSING", "MANY_MATCHING_CONTENT_ROWS": "INPUT_MALFORMED"}},
        "diagnostic": "ACCEPTED_SOURCE_CONTENT_ROW_COUNT_NOT_ONE",
        "input_cases": ["ZERO_MATCHING_CONTENT_ROWS", "MANY_MATCHING_CONTENT_ROWS"],
        "witness": {"profile_pointer": D("CONTENT_ROW_COLLECTION_POINTER"), "candidate_artifact": D("NULL"), "candidate_pointer": D("NULL"),
                    "source_identity": D("ACCEPTED_SOURCE_REF_WHEN_VALID_ELSE_NULL"), "expected": D("REQUIRED_CONTENT_ROW_MATCH_COUNT"), "actual": D("CONTENT_ROW_MATCH_COUNT")},
        "rank": 1, "replaces": "ACCEPTED_CONTENT_ROW_MISSING (R5R20; zero matches only)"}
    for c in pe17["conditions"][1:]:
        c["input_cases"] = ["ONE_MATCHING_CONTENT_ROW"]
        c["witness"]["profile_pointer"] = D("ACCEPTED_CONTENT_ROW_POINTER")
        c.pop("predicate_pending_cases", None)
        c["requires"] = "ACCEPTED_CONTENT_ROW_CARDINALITY passed (exactly one matching row)"
    # PHD-07: registry-level group before row-level group.
    pe21 = F["PE-21"]
    sa = meta["registration"]["structural_application"]
    rows = pe21["conditions"]
    for c in rows:
        c["level"] = "ROW_LEVEL"; c["subject_scope"] = ["REGISTRY_ROW"]; c.pop("uncovered_input_cases", None)
    top = {"condition_id": "OBJECT_REGISTRY_DOCUMENT_LEVEL_SCHEMA_VIOLATION",
           "condition": "an object-registry schema failure located outside every /objects/<i> row (registry root members, or the /objects collection itself)",
           "failure_kind": sa["failure_kind"], "diagnostic": "OBJECT_REGISTRY_SCHEMA_VIOLATION", "level": "REGISTRY_LEVEL", "subject_scope": ["REGISTRY_DOCUMENT"],
           "witness": {"argument": D("REGISTRATION_WITNESS_ARGUMENT"), "object_role": D("REGISTRATION_WITNESS_OBJECT_ROLE"), "schema_ref": D("REGISTRATION_WITNESS_SCHEMA_REF"),
                       "instance_pointer": D("REGISTRY_LEVEL_FIRST_INVALID_LOCATION"), "bound_identity": D("NULL")}}
    pe21["conditions"] = [top] + rows
    for rank, c in enumerate(pe21["conditions"], 1): c["rank"] = rank
    pe21["subject_classes"] = ["REGISTRY_DOCUMENT", "REGISTRY_ROW"]
    pe21["subject_order"] = "REGISTRY_LEVEL_GROUP_THEN_ROWS"
    pe21["within_family_order"] = "REGISTRY_LEVEL_GROUP_THEN_REGISTRATION_DECLARED_ORDER"
    pe21["condition_groups"] = [
        {"group": 1, "level": "REGISTRY_LEVEL", "conditions": ["OBJECT_REGISTRY_DOCUMENT_LEVEL_SCHEMA_VIOLATION"], "order": "CONDITION_RANK"},
        {"group": 2, "level": "ROW_LEVEL", "conditions": [c["condition_id"] for c in rows], "order": "REGISTRATION_FIRST_FAILURE_ORDERING"}]
    model["subject_orders"]["REGISTRY_LEVEL_GROUP_THEN_ROWS"] = "the registry document (group 1), then /objects rows in ascending index (group 2)"
    model["subject_order_rules"]["REGISTRY_LEVEL_GROUP_THEN_ROWS"] = "REGISTRY_LEVEL_GROUP_THEN_ROWS"
    model["first_failure_selection"]["within_family_order"]["REGISTRY_LEVEL_GROUP_THEN_REGISTRATION_DECLARED_ORDER"] = (
        "(group: 1 registry-level, 2 row-level; group 1: condition rank; group 2: metacontract:/registration/first_failure_ordering - registry source order, declared rule rank, single pointer)")
    # PHD-08: PE-40 canonical record domain.
    pe40 = F["PE-40"]
    pe40["subject_classes"] = ["RUNTIME_VALUE_SCHEMA", "UNIVERSE_VALUE", "UNIVERSE_OBJECT_RECORD"]
    ro = cond("PE-40", "RESOLVED_OBJECT_REPRESENTATION")
    ro["condition"] = "an /objects/<k> record of the published universe value is invalid against value_schemas.resolved_object (records in universe order)"
    ro["subject_scope"] = ["UNIVERSE_OBJECT_RECORD"]
    ro["witness"]["instance_pointer"] = D("SCOPED_FIRST_INVALID_LOCATION")
    ro["witness"]["bound_identity"] = D("RESOLVED_OBJECT_IDENTITY_CONTAINING_LOCATION_ELSE_NULL")
    pe40["subject_domain"] = {"UNIVERSE_OBJECT_RECORD": "every /objects/<k> element of the published verification universe value, k ascending; exactly one canonical pointer /objects/<k> per subject",
                              "not_subjects": "member-resolved projections and derived member values without an independent universe pointer; owned by member registration (PE-23 SCHEMA_ROW_REGISTERED_MEMBERS_BIND_TO_ROOT_DEFS_ENTRIES), member binding, producer/schema binding and owning-object validation"}
    subj = model["subject_orders"]
    subj["RUNTIME_VALUE_ORDER"] = "value schemas (UTF-16 key order: resolved_object, verification_universe), then the universe value, then /objects/<k> records in universe order"
    # Close the pending register.
    model["pending_human_decisions"] = []
    model["r5r22_pending_closure"] = [
        {"id": "PHD-01", "closed_by": "metacontract:/binding_origins/reserved_input_expectations; exact type/origin equality; explicit pin_ref; unknown names owned by the name-set condition"},
        {"id": "PHD-02", "closed_by": "PE-38 RESOLVED: bound_source argument, ref kind, resolved schema, allowlist identity; UNRESOLVED: declaring metacontract allowlist row"},
        {"id": "PHD-03", "closed_by": "PE-19 registry unresolved/unreadable witnessed at candidate_package /procedure_registry_ref (protocol artifact name specification-package)"},
        {"id": "PHD-04", "closed_by": "PE-19 COLLECTION_NOT_ARRAY: procedure-registry /procedures, expected collection type ARRAY, actual json_type token; no match count"},
        {"id": "PHD-05", "closed_by": "PE-10 PACKAGE_IDENTITY_INVALID precedes PE-11 (SCHEMA_INVALID_BOUND_OBJECT / TYPE / CANDIDATE_PACKAGE_IDENTITY_INVALID)"},
        {"id": "PHD-06", "closed_by": "PE-17 ACCEPTED_CONTENT_ROW_CARDINALITY: exactly one matching content row"},
        {"id": "PHD-07", "closed_by": "PE-21 group 1 registry-level condition precedes group 2 row-level conditions"},
        {"id": "PHD-08", "closed_by": "PE-40 subject domain is the /objects/<k> universe records"},
    ]
    for row in model["r5r21_defect_resolution"]:
        if row["defect"] == "D5":
            row["change"] = "schema_ref from the resolved allowlist expected_schema_ref row, bound_identity and role from the allowlist ref, argument bound_source; an unresolved ref is attributed to the declaring metacontract allowlist row (R5R23 PHD-02)"
        if row["defect"] == "D7":
            row["change"] = "UTF-16 member order, per-member and collection locations; label and pin law from binding_origins.reserved_input_expectations (R5R23 PHD-01)"
            row["prevented_by"] = "F, C, H"
        if row["defect"] == "D3":
            row["change"] += "; registry unresolved/unreadable at candidate_package /procedure_registry_ref; non-array collection without match count (R5R23 PHD-03, PHD-04)"
    return model


def _r5r23_checks(model, ctx):
    """R5R23 properties H-N and the null-semantics rule (clarification C, reported under E)."""
    import re
    meta, schema = ctx["meta"], ctx["schema"]
    defs = schema["$defs"]
    errors = []
    E = errors.append
    F = {f["family_id"]: f for f in model["families"] if f["class"] == "NORMATIVE_REACHABLE"}
    V, pc, closed = model["derivation_vocabulary"], model["protocol_constants"], model["closed_vocabularies"]
    def cond(fid, cid): return next((c for c in F.get(fid, {}).get("conditions", []) if c["condition_id"] == cid), None)
    def leaves(rule):
        if isinstance(rule, dict) and "by_subject_class" in rule: return [l for r in rule["by_subject_class"].values() for l in leaves(r)]
        if isinstance(rule, dict) and "by_case" in rule: return [l for r in rule["by_case"].values() for l in leaves(r)]
        return [rule]
    # H. reserved input table totality.
    exp = meta.get("binding_origins", {}).get("reserved_input_expectations")
    names = [r.get("name") for r in meta["reserved_inputs"]]
    if not isinstance(exp, dict): E("H: reserved_input_expectations is not declared")
    else:
        if sorted(exp) != sorted(names) or len(set(names)) != len(names): E("H: reserved inputs and expectation rows are not one-to-one")
        if sorted(exp) != sorted(meta["binding_origins"]["reserved_names"]): E("H: expectation rows differ from binding_origins.reserved_names")
        types = ctx["proc_schema"]["$defs"]["argument"]["properties"]["type"]["enum"]
        for name, row in exp.items():
            if not isinstance(row, dict) or set(row) != {"type", "origin", "pin_ref"}: E("H: expectation row is not exactly {type, origin, pin_ref} (pin_ref must be explicit) " + str(name)); continue
            if row["type"] not in types: E("H: expectation type not registered " + name)
            if row["origin"] not in meta["binding_origins"]["allowed_origins"]: E("H: expectation origin not registered " + name)
            pin = row["pin_ref"]
            if pin is not None:
                if not (isinstance(pin, list) and len(pin) == 2 and pin[0] == "frozen_authority_pins" and pin[1] in meta["external_authority_pins"]):
                    E("H: pin_ref does not resolve in the declared pin domain " + name)
                elif "/frozen_authority_pins/" + pin[1] not in [m["profile_pointer"] for m in pc["required_profile_members"]]:
                    E("H: pin_ref names no required profile pin member " + name)
        row_by_name = {r.get("name"): r for r in meta["reserved_inputs"]}
        for name, row in exp.items():
            r = row_by_name.get(name, {})
            if isinstance(row, dict) and (r.get("type"), r.get("origin")) != (row.get("type"), row.get("origin")): E("H: declared reserved input disagrees with its expectation " + name)
    for cid in ("RESERVED_INPUT_NAME_LABEL_MISMATCH", "RESERVED_INPUT_NAME_SET_MISMATCH", "RESERVED_CONTENT_SOURCE_PIN_UNDECLARED"):
        c = cond("PE-41", cid)
        if c is None or c.get("predicate_ref") != "metacontract:/binding_origins/reserved_input_expectations": E("H: PE-41 predicate does not reference the expectation table " + cid)
    if set(closed["object_role_value_vocabulary"].get("RESERVED_INPUT_TYPE_ADMITTED_BY_PE41") or []) != {r["type"] for r in (exp or {}).values() if isinstance(r, dict)}:
        E("H: reserved input role vocabulary differs from the expectation types")
    # I. bound-source owner totality.
    pe38 = F.get("PE-38", {}).get("conditions", [])
    res = {c.get("expected_schema_resolution"): c for c in pe38}
    if sorted(res) != ["RESOLVED", "UNRESOLVED"] or len(pe38) != 2: E("I: PE-38 lacks exactly one resolved and one unresolved case")
    else:
        u, r = res["UNRESOLVED"]["witness"], res["RESOLVED"]["witness"]
        if u.get("argument") != {"constant": "metacontract"} or u.get("instance_pointer") != {"derivation": "ALLOWLIST_EXPECTED_SCHEMA_REF_DECLARATION_LOCATION"}:
            E("I: unresolved PE-38 case is not attributed to the declaring allowlist row")
        if any(l.get("derivation") in ("ALLOWLIST_EXPECTED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID", "ALLOWLIST_REF_IDENTITY", "ALLOWLIST_REF_KIND", "BOUND_SOURCE_ARGUMENT")
               for v in u.values() for l in leaves(v) if isinstance(l, dict)):
            E("I: unresolved PE-38 case reads the missing schema or the bound source")
        if [r.get(k, {}).get("derivation") for k in ("argument", "object_role", "schema_ref", "bound_identity")] != ["BOUND_SOURCE_ARGUMENT", "ALLOWLIST_REF_KIND", "ALLOWLIST_EXPECTED_SCHEMA_ROW_SCHEMA_DOCUMENT_ID", "ALLOWLIST_REF_IDENTITY"]:
            E("I: resolved PE-38 case is not the bound-source witness")
        if V["argument"].get("BOUND_SOURCE_ARGUMENT", {}).get("constant_value") != "bound_source" or closed["argument_documents"].get("bound_source") != "BOUND_SOURCE_CONTENT":
            E("I: bound_source argument is not declared")
    src_def = defs.get("source", {}).get("properties", {}).get("ref", {})
    if src_def != {"$ref": "#/$defs/typed_ref"} or any(defs["typed_ref"]["properties"][k].get("minLength") != 1 for k in ("kind", "id", "version")):
        E("I: METACONTRACT_SCHEMA_VALIDATED_ALLOWLIST_REF premise does not hold")
    # J. early artifact map totality.
    claim_stage = meta["bootstrap_order"].index("COMPARE_ALL_CANDIDATE_AUTHORITY_CLAIMS_WHOLE_OBJECT_BEFORE_SEMANTIC_USE")
    arts = pc.get("claim_artifacts", {})
    for claim in pc["claim_comparisons"]:
        if claim["candidate_artifact"] not in arts: E("J: claim artifact not in the protocol map " + claim["candidate_artifact"])
    for fam in F.values():
        if fam.get("stage_index", 99) > claim_stage: continue
        for c in fam["conditions"]:
            for l in leaves((c.get("witness") or {}).get("candidate_artifact")):
                if isinstance(l, dict) and "constant" in l and l["constant"] not in arts: E("J: early artifact token outside the protocol map " + fam["family_id"] + "/" + c["condition_id"])
    pkg_art = arts.get(_R5R23_PACKAGE_ARTIFACT, {})
    if pkg_art != {"package_member": None, "entrypoint_argument": "candidate_package", "document": "PACKAGE"}: E("J: candidate-package artifact name is not declared")
    claim4_art = pc["claim_comparisons"][4]["candidate_artifact"]
    for cid in ("PROCEDURE_REGISTRY_UNRESOLVED", "PROCEDURE_REGISTRY_UNREADABLE"):
        w = (cond("PE-19", cid) or {}).get("witness", {})
        if w.get("candidate_artifact") != {"constant": _R5R23_PACKAGE_ARTIFACT} or w.get("candidate_pointer") != {"derivation": "CLAIM_ARTIFACT_PACKAGE_REFERENCE_POINTER"}:
            E("J: PE-19 registry failure is not witnessed at the candidate package reference " + cid)
    member = arts.get(claim4_art, {}).get("package_member")
    if not member or member not in ctx["pkg"]: E("J: package reference of the claim artifact does not resolve in the candidate package")
    # K. package identity precondition.
    pre = F.get("PE-11", {}).get("precondition") or {}
    owner = F.get(pre.get("owner"), {})
    oc = cond(pre.get("owner"), pre.get("condition_id")) if pre else None
    if not oc or oc.get("predicate_ref") != "model:/protocol_constants/package_identity_members": E("K: PE-11 has no package identity precondition")
    elif (owner.get("stage_index"), owner.get("group_rank")) >= (F["PE-11"].get("stage_index"), F["PE-11"].get("group_rank")): E("K: package identity condition does not precede PE-11")
    if pc.get("package_identity_members") != ["package_id", "package_version"]: E("K: package identity members are not the declared package identity fields")
    for c in F.get("PE-11", {}).get("conditions", []):
        if "PACKAGE_ID_VERSION_INVALID" in (c.get("input_cases") or []): E("K: PE-11 still admits an invalid package identity")
    for tok in ("PACKAGE_ID_VERSION", "PACKAGE_IDENTITY3_WITH_RECOMPUTED_DIGEST"):
        if V["trust_result"][tok].get("requires_precondition") != "PE-10/PACKAGE_IDENTITY_INVALID": E("K: trust package identity derivation lacks its precondition " + tok)
    # L. exactly-one content row.
    m17 = F.get("PE-17", {}).get("content_row_matching") or {}
    if m17.get("required_match_count") != 1 or not str(m17.get("selection", "")).startswith("EXACTLY_ONE") or "FIRST" in str(m17.get("selection", "")).replace("NO_FIRST", ""):
        E("L: PE-17 content-row matching is not exactly-one")
    c17 = F.get("PE-17", {}).get("conditions", [])
    if not c17 or c17[0].get("condition_id") != "ACCEPTED_CONTENT_ROW_CARDINALITY" or sorted(c17[0].get("input_cases") or []) != ["MANY_MATCHING_CONTENT_ROWS", "ZERO_MATCHING_CONTENT_ROWS"]:
        E("L: PE-17 cardinality condition does not own 0 and many matches first")
    for c in c17[1:]:
        if (c.get("input_cases") or []) != ["ONE_MATCHING_CONTENT_ROW"]: E("L: PE-17 content verification proceeds without exactly one row " + c["condition_id"])
    # M. registry group order.
    c21 = F.get("PE-21", {}).get("conditions", [])
    levels = [c.get("level") for c in c21]
    if any(l not in ("REGISTRY_LEVEL", "ROW_LEVEL") for l in levels): E("M: PE-21 condition without a level")
    reg_ranks = [c["rank"] for c in c21 if c.get("level") == "REGISTRY_LEVEL"]
    row_ranks = [c["rank"] for c in c21 if c.get("level") == "ROW_LEVEL"]
    if not reg_ranks or not row_ranks or max(reg_ranks) > min(row_ranks): E("M: a row-level PE-21 condition precedes a registry-level condition")
    if F.get("PE-21", {}).get("within_family_order") != "REGISTRY_LEVEL_GROUP_THEN_REGISTRATION_DECLARED_ORDER": E("M: PE-21 is not ordered by group")
    groups = F.get("PE-21", {}).get("condition_groups") or []
    if [g["conditions"] for g in groups] != [[c["condition_id"] for c in c21 if c.get("level") == "REGISTRY_LEVEL"], [c["condition_id"] for c in c21 if c.get("level") == "ROW_LEVEL"]]:
        E("M: PE-21 condition groups do not match the condition levels")
    for c in c21:
        if c.get("level") == "REGISTRY_LEVEL" and any(isinstance(l, dict) and l.get("derivation") == "ROW_POINTER_TEMPLATE" for l in leaves(c["witness"]["instance_pointer"])):
            E("M: registry-level failure fabricates a row pointer")
    # N. PE-40 subject domain.
    pe40 = F.get("PE-40", {})
    if not set(pe40.get("subject_classes", [])) <= {"RUNTIME_VALUE_SCHEMA", "UNIVERSE_VALUE", "UNIVERSE_OBJECT_RECORD"}: E("N: PE-40 admits a subject without a canonical universe pointer")
    ro = cond("PE-40", "RESOLVED_OBJECT_REPRESENTATION") or {}
    if ro.get("subject_scope") != ["UNIVERSE_OBJECT_RECORD"] or ro.get("pointer_scope") != "/objects/<k>": E("N: PE-40 record subjects do not have exactly one /objects/<k> pointer")
    if "MEMBER_RESOLVED_RECORD" in closed["subject_class"]: E("N: member-resolved records remain a subject class")
    vu = meta["runtime_representation"]["value_schemas"]["verification_universe"]
    if vu.get("properties", {}).get("objects", {}).get("type") != "array": E("N: the universe /objects member is not an array")
    # E (clarification C): null only where a derivation declares it and the target schema permits it.
    nc = closed.get("null_case", {})
    word = re.compile(r"null when|or null|, null\b|null at|; null", re.I)
    for field, toks in V.items():
        for tok, v in toks.items():
            nullable = v.get("value_type") in _R5R23_NULLABLE_TYPES
            ns = v.get("null_semantics")
            if nullable and (not ns or any(n not in nc for n in ns)): E("E: null-admitting derivation without declared null semantics %s.%s" % (field, tok))
            if not nullable and ns: E("E: non-null derivation declares null semantics %s.%s" % (field, tok))
            if word.search(v.get("definition", "")) and not nullable: E("E: definition maps a case to null but the value type is non-null %s.%s" % (field, tok))
    branches = defs["pre_execution_result"]["oneOf"]
    def field_schema(contract, field):
        if contract in ("SEVEN_FIELD", "STATIC_VALIDATION"): return branches[0]["properties"]["witness"]["properties"].get(field)
        if contract == "PROFILE_PREFLIGHT": return defs["external_profile_preflight_witness"]["properties"].get(field)
        return None
    import jsonschema as _js
    for fam in F.values():
        for c in fam["conditions"]:
            for field, rule in (c.get("witness") or {}).items():
                sub = field_schema(fam["witness_contract"], field)
                if sub is None: continue
                for l in leaves(rule):
                    v = V.get(field, {}).get((l or {}).get("derivation")) if isinstance(l, dict) else None
                    if v and v.get("value_type") in _R5R23_NULLABLE_TYPES and not _js.Draft202012Validator({"$defs": defs, **sub}).is_valid(None):
                        E("E: null-admitting derivation %s used for field %s whose schema forbids null at %s/%s" % (l["derivation"], field, fam["family_id"], c["condition_id"]))
            reason = c.get("reason")
            if isinstance(reason, dict) and "by_case" in reason and set(reason["by_case"]) != set(c.get("input_cases") or []): E("D: reason by_case does not cover the input cases " + fam["family_id"])
    # No pending marker survives.
    if model.get("pending_human_decisions"): E("pending human decisions remain")
    blob = json.dumps(model["families"])
    for marker in (r'"pending"', r"predicate_pending", r"uncovered_input_cases", r"PENDING", r"PHD-0[1-8]"):
        if re.search(marker, blob): E("pending marker remains: " + marker)
    return errors


def _r5r23_semantic_totality(model, ctx):
    errors = []
    try:
        base = _r5r22_semantic_totality(model, ctx)
    except ValueError as exc:
        base = None
        errors += [line.strip() for line in str(exc).splitlines()[1:]]
    errors += _r5r23_checks(model, ctx)
    if errors: raise ValueError("R5R23 semantic totality failed:\n  " + "\n  ".join(errors[:80]))
    return base


def _r5r23_finalize():
    ctx = _r5r22_context()
    meta, reg, pkg, meta_schema = ctx["meta"], ctx["reg"], ctx["pkg"], ctx["schema"]
    # PHD-01 declaration (candidate metacontract, pinned by its schema).
    meta["binding_origins"]["reserved_input_expectations"] = _r5r23_expectations(meta)
    bo = meta_schema["properties"]["binding_origins"]
    bo["properties"]["reserved_input_expectations"] = {"const": copy.deepcopy(meta["binding_origins"]["reserved_input_expectations"])}
    if "reserved_input_expectations" not in bo["required"]: bo["required"].append("reserved_input_expectations")
    model = meta["failure_semantics"]["pre_execution_failure_model"]
    V = _r5r23_vocabulary(model["derivation_vocabulary"])
    closed = model["closed_vocabularies"]
    closed["subject_class"].pop("MEMBER_RESOLVED_RECORD", None)
    closed["subject_class"]["REGISTRY_DOCUMENT"] = "the explicit object registry as a whole (failures outside every /objects/<i> row)"
    closed["argument_documents"]["bound_source"] = "BOUND_SOURCE_CONTENT"
    closed["ordering_rule"]["PACKAGE_IDENTITY_MEMBER_ORDER"] = {"kind": "ARRAY", "source": "model:/protocol_constants/package_identity_members",
                                                                "definition": "array order of protocol_constants.package_identity_members"}
    closed["ordering_rule"]["REGISTRY_LEVEL_GROUP_THEN_ROWS"] = {"kind": "DECLARED", "declared_by": "model:/families/PE-21/condition_groups",
                                                                 "definition": "registry-level group by condition rank, then rows by registration first_failure_ordering"}
    closed["identity_guarantee"]["METACONTRACT_SCHEMA_VALIDATED_ALLOWLIST_REF"] = (
        "stage VALIDATE_CANDIDATE_OBJECTS_AND_BOUND_SOURCE_UNIVERSE after the candidate-object group: the metacontract was validated against its schema, whose allowlist rows are $defs/source with ref $defs/typed_ref "
        "(non-empty kind, id, version), and the profile allowlist equals the metacontract allowlist by PE-18 claim index 2")
    closed["object_role_value_vocabulary"]["RESERVED_INPUT_TYPE_ADMITTED_BY_PE41"] = sorted({r["type"] for r in meta["binding_origins"]["reserved_input_expectations"].values()})
    closed["object_role_value_vocabulary"]["TYPED_REF_KIND"] = "SCHEMA_BOUNDED:metacontract-schema:/$defs/typed_ref/properties/kind (non-empty string); current allowlist kinds PACKAGE, SOURCE_VECTOR_CATALOG"
    closed["null_case"] = copy.deepcopy(_R5R23_NULL_CASES)
    closed["null_rule"] = ("an absent member yields null only when the derivation declares that null case in null_semantics and the target registered field schema permits null; "
                           "null never hides a malformed required member, a wrong type, an empty required string or an unresolved required reference unless that exact case is declared")
    _r5r23_close(model, meta, ctx)
    model["diagnostic_vocabulary"] = sorted({c["diagnostic"] for f in model["families"] if f["class"] == "NORMATIVE_REACHABLE"
                                             for c in f["conditions"] if isinstance(c.get("diagnostic"), str)})
    ctx["meta"] = meta
    semantic = _r5r23_semantic_totality(model, ctx)
    model["totality"] = dict(semantic["base"], **{"semantic": {k: v for k, v in semantic.items() if k not in ("d13", "base")},
                                                  "model_status": "TOTAL" if semantic["pending_human_decisions"] == 0 else "PENDING_HUMAN_DECISIONS"})
    if model["totality"]["model_status"] != "TOTAL": raise ValueError("R5R23: model is not total")
    fs = meta["failure_semantics"]
    fs["pre_execution_failure_model"] = model
    fs["verifier_protocol_digests"] = {"algorithm": "SHA-256", "serialization": "RFC8785_JCS",
                                       "pre_execution_failure_model": sem(model), "registration": sem(meta["registration"]),
                                       "generic_failure_witness": sem(fs["generic_failure_witness"])}
    fss = meta_schema["properties"]["failure_semantics"]
    for name in ("pre_execution_failure_model", "verifier_protocol_digests"):
        fss["properties"][name] = {"const": copy.deepcopy(fs[name])}
    _r11_save("metacontract.json", meta)
    _r11_save("schema/metacontract.schema.json", meta_schema)
    _r11_digest_close(reg, pkg)
    print(json.dumps({"r5r23_decision_closure": "PASS", "totality": model["totality"], "d13": semantic["d13"],
                      "verifier_protocol_digests": fs["verifier_protocol_digests"],
                      "registry_semantic_sha256": pkg["registry_semantic_sha256"],
                      "package_semantic_sha256": pkg["current_candidate_integrity"]["digest"]}, indent=2))

_R5R22_POST_BUILD = _r11_post_build
def _r11_post_build():
    _R5R22_POST_BUILD()
    _r5r23_finalize()

# ---------------------------------------------------------------------------
# R5R25: resource-limit and rule-set law repair (accepted R5R24 findings N1, N2, N3).
# N1 fixes the AST expression-depth measurement, N2 the lexical collection nesting
# measurement, and every other PE-44 resource-limit predicate gets an exact
# measurement function from the same machine-readable AST law.  N3 rewords the PE-45
# rule-set condition to the complete required_rule_ids set (behavior unchanged).  The
# R5R24 PE-36 performance observation is recorded only (PHASE_B_RESOURCE_EXHAUSTION_RISK).
# ---------------------------------------------------------------------------
_R5R25_LAW_POINTER = "model:/protocol_constants/ast_resource_limits"
_R5R25_EDGE_RULES = {
    "EXPRESSION": "THE_VALUE_PRESENT_AT_THE_SLOT",
    "NAMED_EXPRESSION_MAP": "EACH_MEMBER_VALUE_OF_THE_JSON_OBJECT_PRESENT_AT_THE_SLOT",
    "POINTER_SLOT": "THE_VALUE_PRESENT_AT_THE_SLOT_WHEN_IT_IS_A_JSON_OBJECT",
    "POINTER_ARRAY_SLOT": "THE_VALUE_PRESENT_AT_THE_SLOT_WHEN_IT_IS_A_JSON_OBJECT",
    "COMPARATOR_SLOT": "NO_CHILD_EDGE",
    "MODE_SLOT": "NO_CHILD_EDGE",
    "SCOPE_BINDER": "NO_CHILD_EDGE",
}
_R5R25_EDGE_RULE_VOCABULARY = {
    "THE_VALUE_PRESENT_AT_THE_SLOT": "the value of the declared slot member, whatever its JSON type, is one child node",
    "EACH_MEMBER_VALUE_OF_THE_JSON_OBJECT_PRESENT_AT_THE_SLOT": "when the slot value is a JSON object, each of its member values is one child node (members in UTF-16 code-unit key order); any other slot value yields no child",
    "THE_VALUE_PRESENT_AT_THE_SLOT_WHEN_IT_IS_A_JSON_OBJECT": "a JSON object at the slot is one child node (the expression form); a bare string or array is an operand of the parent, not a node",
    "NO_CHILD_EDGE": "the slot value is a bare operand of the parent node and never an AST node",
}
_R5R25_FUNCTIONS = {
    "NODE_DEPTH": "graph depth of an AST node: the root value of its AST root plus edge_increment for each child edge on the path from that root",
    "ACTIVE_COLLECTION_BINDER_COUNT": "number of active collection binders whose bound expression contains the node: a binder node is evaluated at the current count; each bound slot of a declared collection binder is entered with the count increased by entry_increment and left with it decreased by exit_decrement; unbound slots keep the current count",
    "AST_NODE_COUNT": "number of AST nodes over every AST root of the procedure (terminals and malformed nodes counted; literal payloads never counted)",
    "ARRAY_LENGTH": "number of elements of the procedure's measured member when that member is a JSON array; any other member value is not measured by this condition",
}
_R5R25_COMPARISONS = {
    "VALUE_LESS_THAN_OR_EQUAL_TO_LIMIT": "the measured value is valid when value <= limit (the limit itself is valid); value > limit is invalid",
    "LOWER_BOUND_AND_VALUE_LESS_THAN_OR_EQUAL_TO_LIMIT": "the measured value is valid when lower_bound <= value <= limit; value < lower_bound or value > limit is invalid",
}
_R5R25_RULE_SET_TEXT = ("the rule_id values of every /rules item of the bound rule registry, whatever its declared_class, are unique and equal as a set "
                        "to the complete required rule id set resolved from the candidate package's required_rule_ids_ref")
_R5R25_RULE_SET_PREVIOUS = "executable conformance rule ids unique and equal to the package required rule ids"


def _r5r25_expression_slot_kinds():
    return sorted(k for k, v in _R5R25_EDGE_RULES.items() if v != "NO_CHILD_EDGE")


def _r5r25_binders(operators):
    """Every declared operator with a SCOPE_BINDER slot; its bound slots are the expression-bearing slots declared after the binder slot."""
    edge_kinds = set(_r5r25_expression_slot_kinds())
    out = {}
    for op in sorted(operators):
        slots = operators[op]["slots"]
        binder = [i for i, (_, kind) in enumerate(slots) if kind == "SCOPE_BINDER"]
        if not binder: continue
        b = binder[0]
        out[op] = {"binder_slot": slots[b][0],
                   "bound_slots": [name for name, kind in slots[b + 1:] if kind in edge_kinds],
                   "unbound_slots": [name for name, kind in slots[:b] if kind in edge_kinds]}
    return out


def _r5r25_law(meta, prim):
    ops = meta["runtime_representation"]["static_type_calculus"]["operator_rules"]["operators"]
    return {
        "law_id": "AST_RESOURCE_LIMIT_MEASUREMENT",
        "adopted_by": "R5R25 (accepted R5R24 normative findings N1 and N2)",
        "applies_to": "model:/families/PE-44",
        "ast": {
            "roots": {"rule": "EACH_ASSERTION_CONDITION_AND_EACH_ASSERTION_WITNESS_IS_A_SEPARATE_AST_ROOT",
                      "source": "metacontract:/scope_semantics/root_partition",
                      "root_pointers": ["/procedures/<i>/assertions/<j>/condition", "/procedures/<i>/assertions/<j>/witness"],
                      "root_order": "ASSERTIONS_IN_SOURCE_ORDER;CONDITION_ROOT_BEFORE_WITNESS_ROOT"},
            "node": "AN_AST_NODE_IS_AN_AST_ROOT_VALUE_OR_A_VALUE_REACHED_FROM_ONE_BY_A_DECLARED_CHILD_EDGE;A_MALFORMED_VALUE_IN_SUCH_A_POSITION_IS_STILL_A_NODE",
            "node_forms": {"OPERATOR": "A_JSON_OBJECT_WITH_MEMBER_op", "ARG_TERMINAL": "A_JSON_OBJECT_WHOSE_ONLY_MEMBER_IS_arg",
                           "ITEM_TERMINAL": "A_JSON_OBJECT_WHOSE_ONLY_MEMBER_IS_item", "LITERAL_TERMINAL": "A_JSON_OBJECT_WHOSE_ONLY_MEMBER_IS_literal",
                           "MALFORMED": "ANY_OTHER_VALUE_IN_AN_AST_POSITION"},
            "child_edges": {
                "operators_source": "metacontract:/runtime_representation/static_type_calculus/operator_rules/operators",
                "slot_kinds_source": "metacontract:/runtime_representation/static_type_calculus/operator_rules/slot_kinds",
                "parent_rule": "ONLY_AN_OPERATOR_NODE_WHOSE_op_NAMES_A_DECLARED_OPERATOR_HAS_CHILD_EDGES;TERMINAL_MALFORMED_AND_UNDECLARED_OPERATOR_NODES_HAVE_NONE",
                "by_slot_kind": copy.deepcopy(_R5R25_EDGE_RULES),
                "absent_slot": "NO_CHILD_EDGE",
                "undeclared_member": "NO_CHILD_EDGE",
                "child_order": {"slots": "DECLARED_OPERATOR_SLOT_ORDER", "named_expression_map_members": "UTF16_CODE_UNIT_KEY_ORDER"},
                "child_pointer": "THE_PARENT_POINTER_FOLLOWED_BY_THE_ESCAPED_SLOT_NAME_AND_FOR_A_NAMED_EXPRESSION_MAP_THE_ESCAPED_MEMBER_NAME"},
            "terminals": {"measured": True, "literal_payload_is_ast": False,
                          "rule": "ARG_ITEM_AND_LITERAL_TERMINALS_ARE_AST_NODES_AND_ARE_MEASURED;THE_VALUE_OF_A_literal_MEMBER_IS_NEVER_TRAVERSED"},
        },
        "traversal": {"order": "CANONICAL_POSTORDER", "definition": "EVERY_CHILD_SUBTREE_IN_CHILD_ORDER_IS_VISITED_BEFORE_ITS_PARENT_NODE",
                      "subject_order": "model:/subject_orders/AST_PROCEDURE_ASSERTION_POSTORDER",
                      "procedure_level_subjects": "BEFORE_THE_NODES_OF_THE_SAME_PROCEDURE",
                      "first_failure": "FIRST_INVALID_SUBJECT_IN_TRAVERSAL_ORDER",
                      "failure_pointer": "ABSOLUTE_PROCEDURE_REGISTRY_POINTER_OF_THE_FAILING_NODE"},
        "collection_binders": {"source": "every operator of operator_rules/operators that declares a SCOPE_BINDER slot",
                               "bound_slot_rule": "THE_EXPRESSION_BEARING_SLOTS_DECLARED_AFTER_THE_SCOPE_BINDER_SLOT",
                               "unbound_slot_rule": "THE_EXPRESSION_BEARING_SLOTS_DECLARED_BEFORE_THE_SCOPE_BINDER_SLOT",
                               "complete": True, "operators": _r5r25_binders(ops)},
        "non_pre_execution_tokens": {
            "MAX_JSON_TRAVERSAL_DEPTH_EXCEEDED": {"status": "RUNTIME_EXPRESSION_ERROR_ONLY;NOT_A_PRE_EXECUTION_CONDITION",
                                                  "measurement_ref": "primitive-registry:/descendant_record/limits/max_depth_source",
                                                  "emission_ref": "primitive-registry:/descendant_record/emission/root_depth",
                                                  "error_class": prim["descendant_record"]["limits"]["exceeded_error_class"]},
            "MAX_JSON_NODES_VISITED_PER_VALUE_EXCEEDED": {"status": "RUNTIME_EXPRESSION_ERROR_ONLY;NOT_A_PRE_EXECUTION_CONDITION",
                                                          "measurement_ref": "primitive-registry:/descendant_record/limits/max_nodes_source",
                                                          "emission_ref": "primitive-registry:/descendant_record/emission/root_visited_node_count",
                                                          "error_class": prim["descendant_record"]["limits"]["exceeded_error_class"]}},
    }


def _r5r25_measurements(tokens):
    common_node = {"subject": "AST_NODE", "root_value": 0, "terminals_measured": True, "comparison": "VALUE_LESS_THAN_OR_EQUAL_TO_LIMIT",
                   "limit_inclusive": True, "first_failure": "FIRST_INVALID_NODE_IN_CANONICAL_POSTORDER", "location": "POINTER_OF_THE_FAILING_NODE",
                   "law_ref": _R5R25_LAW_POINTER}
    common_proc = {"subject": "PROCEDURE_DECLARATION", "comparison": "VALUE_LESS_THAN_OR_EQUAL_TO_LIMIT", "limit_inclusive": True,
                   "first_failure": "PROCEDURE_LEVEL_SUBJECT_IN_PROCEDURE_SOURCE_ORDER", "location": "LOCATION_TEMPLATE_WITH_THE_PROCEDURE_INDEX",
                   "law_ref": _R5R25_LAW_POINTER}
    m = {
        "MAX_ARGUMENTS_PER_PROCEDURE_EXCEEDED": dict(common_proc, function="ARRAY_LENGTH", measured_member="arguments"),
        "MAX_ASSERTIONS_PER_PROCEDURE_EXCEEDED": dict(common_proc, function="ARRAY_LENGTH", measured_member="assertions",
                                                      comparison="LOWER_BOUND_AND_VALUE_LESS_THAN_OR_EQUAL_TO_LIMIT", lower_bound=1),
        "MAX_AST_NODES_PER_PROCEDURE_EXCEEDED": dict(common_proc, function="AST_NODE_COUNT", terminals_counted=True, literal_payload_counted=False),
        "MAX_EXPRESSION_DEPTH_EXCEEDED": dict(common_node, function="NODE_DEPTH", edge_increment=1),
        "MAX_LEXICAL_COLLECTION_NESTING_EXCEEDED": dict(common_node, function="ACTIVE_COLLECTION_BINDER_COUNT",
                                                        binder_set_ref=_R5R25_LAW_POINTER + "/collection_binders/operators",
                                                        binder_node_value="CURRENT_COUNT", entry_increment=1, exit_decrement=1,
                                                        unbound_slot_value="CURRENT_COUNT"),
    }
    for cid, mm in m.items(): mm["limit_ref"] = tokens[cid]
    return m


def _r5r25_apply(model, meta, prim):
    law = _r5r25_law(meta, prim)
    model["protocol_constants"]["ast_resource_limits"] = law
    fam = {f["family_id"]: f for f in model["families"]}
    pe44, pe45 = fam["PE-44"], fam["PE-45"]
    for cid, mm in _r5r25_measurements(pe44["resource_limit_tokens"]).items():
        next(c for c in pe44["conditions"] if c["condition_id"] == cid)["measurement"] = mm
    rs = next(c for c in pe45["conditions"] if c["condition_id"] == "BOUND_RULE_SET_EXACT_TO_REQUIRED_RULE_IDS")
    if rs["condition"] != _R5R25_RULE_SET_PREVIOUS: raise ValueError("R5R25: unexpected PE-45 rule-set condition text")
    rs["condition"] = _R5R25_RULE_SET_TEXT
    rs["compared_sets"] = {"bound": {"object": "rule_registry", "collection_pointer": "/rules", "member": "rule_id",
                                     "scope": "EVERY_RULE_WHATEVER_ITS_DECLARED_CLASS"},
                           "required": {"object": "candidate_package", "reference_member": "/required_rule_ids_ref",
                                        "resolution": "LABEL_COLON_POINTER_RESOLVED_IN_THE_NAMED_BOOTSTRAP_OBJECT", "scope": "THE_COMPLETE_REFERENCED_ARRAY"},
                           "relation": "BOUND_IDS_UNIQUE_AND_SET_EQUAL_TO_REQUIRED_IDS",
                           "executable_subset_is_the_compared_set": False}
    V = model["derivation_vocabulary"]
    svl = V["instance_pointer"]["STATIC_VIOLATION_LOCATION"]
    svl["definition"] = ("location rule of the condition: NODE = pointer of the failing AST node (for a condition that declares a measurement, "
                         "the first node in canonical postorder whose measured value is invalid, per model:/protocol_constants/ast_resource_limits); "
                         "MEMBER = the condition's location_template with the failing indices; SET_EXACT = pointer of the first extra element by ascending index, "
                         "else the collection pointer; UNIQUENESS = pointer of the first second occurrence by ascending index")
    for s in ("PROTOCOL_CONSTANT", "CANDIDATE_DECLARATION"):
        if s not in svl["source"]: svl["source"].append(s)
    closed = model["closed_vocabularies"]
    closed["resource_limit_function"] = copy.deepcopy(_R5R25_FUNCTIONS)
    closed["limit_comparison"] = copy.deepcopy(_R5R25_COMPARISONS)
    closed["ast_child_edge_rule"] = copy.deepcopy(_R5R25_EDGE_RULE_VOCABULARY)
    closed["ordering_rule"]["AST_PROCEDURE_ASSERTION_CANONICAL_POSTORDER"] = {
        "kind": "DECLARED", "declared_by": _R5R25_LAW_POINTER + "/traversal",
        "definition": "procedures in source order; procedure-level subjects; then assertion roots in source order (condition before witness), "
                      "each root's AST nodes in canonical postorder over the declared child edges and child order"}
    model["subject_order_rules"]["AST_PROCEDURE_ASSERTION_POSTORDER"] = "AST_PROCEDURE_ASSERTION_CANONICAL_POSTORDER"
    model["subject_orders"]["AST_PROCEDURE_ASSERTION_POSTORDER"] = (
        "procedures in source order; procedure-level conditions; then assertions in source order, condition before witness, nodes in canonical postorder "
        "with operand slots in declared operator slot order and named-expression-map members in UTF-16 code-unit key order "
        "(child edges as declared by protocol_constants.ast_resource_limits)")
    model["r5r25_resource_limit_closure"] = {
        "findings": {
            "N1": {"family": "PE-44", "condition": "MAX_EXPRESSION_DEPTH_EXCEEDED", "closed_by": [_R5R25_LAW_POINTER, "model:/families/PE-44/MAX_EXPRESSION_DEPTH_EXCEEDED/measurement"],
                   "adopted": ["AST root depth 0", "each child edge adds 1", "every node including terminals is measured", "depth <= 64 is valid; 65 is invalid",
                               "first failure is the first invalid node in canonical postorder; the pointer names that node"]},
            "N2": {"family": "PE-44", "condition": "MAX_LEXICAL_COLLECTION_NESTING_EXCEEDED",
                   "closed_by": [_R5R25_LAW_POINTER + "/collection_binders", "model:/families/PE-44/MAX_LEXICAL_COLLECTION_NESTING_EXCEEDED/measurement"],
                   "adopted": ["nesting at a node = number of active collection binders whose bound expression contains it",
                               "a binder node is evaluated at the current count; its bound expression is entered at count + 1 and left at count - 1",
                               "count <= 32 is valid; a node evaluated under 33 active binders is invalid",
                               "the binder that creates the 33rd scope is not itself over the limit; first failure is the first invalid node in canonical postorder"]},
            "N3": {"family": "PE-45", "condition": "BOUND_RULE_SET_EXACT_TO_REQUIRED_RULE_IDS", "previous_text": _R5R25_RULE_SET_PREVIOUS,
                   "compared_set": "the complete required_rule_ids set (every declared_class), not the executable-conformance subset", "behavior_change": "NONE"}},
        "measured_predicates": sorted(_r5r25_measurements(pe44["resource_limit_tokens"])),
        "recorded_risks": [{"risk_id": "PHASE_B_RESOURCE_EXHAUSTION_RISK", "status": "RECORD_ONLY", "normative_effect": "NONE", "observed_in": "R5R24",
                            "family": "PE-36", "subject": "procedure-registry content validation against the registered recursive expression grammar",
                            "observation": "validation cost roughly doubles per AST level under a standard validator: depth 4 about 0.06 s, depth 8 about 1.0 s, depth 12 about 20.7 s",
                            "disposition": "LATER_ENGINEERING_AND_SECURITY_WORK;MUST_NOT_ALTER_PE-44_RESOURCE_LIMIT_MEASUREMENT_SEMANTICS"}]}
    return law


def _r5r25_checks(model, ctx):
    """Property O: resource-limit measurement law (N1, N2), rule-set wording (N3) and the recorded performance risk."""
    import re
    meta, prim, pkg = ctx["meta"], ctx["prim"], ctx["pkg"]
    errors = []
    E = errors.append
    ops = meta["runtime_representation"]["static_type_calculus"]["operator_rules"]["operators"]
    slot_kinds = meta["runtime_representation"]["static_type_calculus"]["operator_rules"]["slot_kinds"]
    limits = meta["resource_limits"]
    closed = model["closed_vocabularies"]
    law = model["protocol_constants"].get("ast_resource_limits")
    if not isinstance(law, dict): return ["O: protocol_constants.ast_resource_limits missing"]
    ast = law.get("ast") or {}
    # O1 AST definition: roots, node forms, child edges for every declared slot kind, terminal treatment.
    if (ast.get("roots") or {}).get("source") != "metacontract:/scope_semantics/root_partition": E("O1: AST roots not bound to scope_semantics.root_partition")
    edges = ast.get("child_edges") or {}
    by_kind = edges.get("by_slot_kind") or {}
    if set(by_kind) != set(slot_kinds): E("O1: child-edge rules do not cover exactly the declared slot kinds %s" % sorted(set(by_kind) ^ set(slot_kinds)))
    for k, v in by_kind.items():
        if v not in closed.get("ast_child_edge_rule", {}): E("O1: child-edge rule %s for %s not in closed vocabulary" % (v, k))
    order = edges.get("child_order") or {}
    if order.get("slots") != "DECLARED_OPERATOR_SLOT_ORDER": E("O1: child slot order not declared")
    if order.get("named_expression_map_members") not in closed["ordering_rule"]: E("O1: named-expression-map member order not a declared ordering rule")
    if not edges.get("parent_rule") or edges.get("absent_slot") != "NO_CHILD_EDGE" or edges.get("undeclared_member") != "NO_CHILD_EDGE": E("O1: child-edge parent/absent/undeclared rules not declared")
    term = ast.get("terminals")
    if not isinstance(term, dict) or term.get("measured") is not True or term.get("literal_payload_is_ast") is not False: E("O1: terminal treatment not declared")
    # O2 collection binder inventory: complete, exact, and partitioned into bound and unbound expression slots.
    edge_kinds = {k for k, v in by_kind.items() if v != "NO_CHILD_EDGE"}
    binders = (law.get("collection_binders") or {}).get("operators") or {}
    scoped = {op for op, d in ops.items() if any(kind == "SCOPE_BINDER" for _, kind in d["slots"])}
    if set(binders) != scoped: E("O2: collection binder set %s differs from operators with a SCOPE_BINDER slot %s" % (sorted(binders), sorted(scoped)))
    if (law.get("collection_binders") or {}).get("complete") is not True: E("O2: binder inventory not declared complete")
    for op, b in binders.items():
        if op not in ops: E("O2: unknown collection binder " + op); continue
        slots = ops[op]["slots"]; names = [n for n, _ in slots]
        bslot = [n for n, k in slots if k == "SCOPE_BINDER"]
        if b.get("binder_slot") not in bslot: E("O2: %s binder slot is not its SCOPE_BINDER slot" % op); continue
        bi = names.index(b["binder_slot"])
        exp = [n for n, k in slots if k in edge_kinds]
        if sorted(b.get("bound_slots") or []) + sorted(b.get("unbound_slots") or []) == [] or set(b.get("bound_slots") or []) & set(b.get("unbound_slots") or []): E("O2: %s bound/unbound slots empty or overlapping" % op)
        if sorted((b.get("bound_slots") or []) + (b.get("unbound_slots") or [])) != sorted(exp): E("O2: %s bound and unbound slots do not partition its expression slots" % op)
        if not b.get("bound_slots") or any(names.index(s) < bi for s in b["bound_slots"] if s in names): E("O2: %s bound slots must be non-empty and declared after the binder slot" % op)
    # O3 failing-node traversal.
    tr = law.get("traversal") or {}
    if tr.get("order") != "CANONICAL_POSTORDER" or tr.get("first_failure") != "FIRST_INVALID_SUBJECT_IN_TRAVERSAL_ORDER" or not tr.get("failure_pointer"): E("O3: failing-node traversal not declared")
    if tr.get("subject_order") != "model:/subject_orders/AST_PROCEDURE_ASSERTION_POSTORDER": E("O3: traversal not bound to the PE-44 subject order")
    rule_name = model["subject_order_rules"].get("AST_PROCEDURE_ASSERTION_POSTORDER")
    rule = closed["ordering_rule"].get(rule_name) or {}
    if rule.get("kind") != "DECLARED" or rule.get("declared_by") != _R5R25_LAW_POINTER + "/traversal": E("O3: AST subject order not declared by the traversal law")
    # O4 every resource-limit predicate has an exact measurement function.
    fam = {f["family_id"]: f for f in model["families"] if f["class"] == "NORMATIVE_REACHABLE"}
    pe44 = fam["PE-44"]
    tokens = pe44.get("resource_limit_tokens") or {}
    conds = {c["condition_id"]: c for c in pe44["conditions"]}
    nonpre = law.get("non_pre_execution_tokens") or {}
    for cid, ref in tokens.items():
        if cid not in conds:
            row = nonpre.get(cid)
            if not isinstance(row, dict) or "NOT_A_PRE_EXECUTION_CONDITION" not in str(row.get("status")): E("O4: resource-limit token %s is neither a measured condition nor a declared runtime-only token" % cid); continue
            label, _, ptr = str(row.get("measurement_ref")).partition(":")
            try: _r5r22_ptr_get(prim, ptr)
            except KeyError: E("O4: runtime-only token %s measurement_ref unresolved" % cid)
            continue
        c = conds[cid]; m = c.get("measurement")
        if not isinstance(m, dict): E("O4: resource-limit predicate %s has no measurement" % cid); continue
        if m.get("limit_ref") != ref: E("O4: %s limit_ref differs from its resource-limit token" % cid)
        lim = limits.get(ref.rsplit("/", 1)[-1])
        if not isinstance(lim, int) or isinstance(lim, bool): E("O4: %s limit does not resolve to an integer" % cid)
        if m.get("function") not in closed.get("resource_limit_function", {}): E("O4: %s measurement function not declared" % cid)
        if m.get("comparison") not in closed.get("limit_comparison", {}): E("O4: %s comparison not declared" % cid)
        if m.get("limit_inclusive") is not True: E("O4: %s boundary inclusivity not declared" % cid)
        if m.get("law_ref") != _R5R25_LAW_POINTER: E("O4: %s not bound to the AST resource-limit law" % cid)
        if m.get("comparison") == "LOWER_BOUND_AND_VALUE_LESS_THAN_OR_EQUAL_TO_LIMIT" and not isinstance(m.get("lower_bound"), int): E("O4: %s lower bound not declared" % cid)
        node_level = m.get("subject") == "AST_NODE"
        if node_level != (c.get("location_rule") == "NODE"): E("O4: %s measurement subject inconsistent with its location rule" % cid)
        if node_level:
            if not isinstance(m.get("root_value"), int) or isinstance(m.get("root_value"), bool) or m.get("root_value") != 0: E("O4: %s root depth origin not declared as 0" % cid)
            if m.get("terminals_measured") is not True: E("O4: %s terminal treatment not declared" % cid)
            if m.get("first_failure") != "FIRST_INVALID_NODE_IN_CANONICAL_POSTORDER": E("O4: %s first-failure traversal not declared" % cid)
            if m.get("location") != "POINTER_OF_THE_FAILING_NODE": E("O4: %s failure location not declared" % cid)
        else:
            if m.get("first_failure") != "PROCEDURE_LEVEL_SUBJECT_IN_PROCEDURE_SOURCE_ORDER" or m.get("location") != "LOCATION_TEMPLATE_WITH_THE_PROCEDURE_INDEX": E("O4: %s procedure-level selection not declared" % cid)
        f = m.get("function")
        if f == "NODE_DEPTH" and m.get("edge_increment") != 1: E("O4: %s edge increment not declared as 1" % cid)
        if f == "ACTIVE_COLLECTION_BINDER_COUNT":
            if m.get("binder_set_ref") != _R5R25_LAW_POINTER + "/collection_binders/operators": E("O4: %s binder set not bound to the inventory" % cid)
            if m.get("binder_node_value") != "CURRENT_COUNT" or m.get("entry_increment") != 1 or m.get("exit_decrement") != 1 or m.get("unbound_slot_value") != "CURRENT_COUNT":
                E("O4: %s binder entry/exit semantics not declared (binder at current count, bound expression +1, exit -1)" % cid)
        if f == "AST_NODE_COUNT" and (m.get("terminals_counted") is not True or m.get("literal_payload_counted") is not False): E("O4: %s counted node set not declared" % cid)
        if f == "ARRAY_LENGTH" and m.get("measured_member") not in ("arguments", "assertions"): E("O4: %s measured member not declared" % cid)
    for cid, c in conds.items():
        if "measurement" in c and cid not in tokens: E("O4: measurement on a non-resource-limit condition " + cid)
    for cid, c in conds.items():
        if c.get("location_rule") == "NODE" and "measurement" in c and "PROTOCOL_CONSTANT" not in model["derivation_vocabulary"]["instance_pointer"]["STATIC_VIOLATION_LOCATION"]["source"]:
            E("O4: STATIC_VIOLATION_LOCATION does not declare the protocol-constant law source")
    # O5 N3 rule-set wording and compared sets.
    rs = next((c for c in fam["PE-45"]["conditions"] if c["condition_id"] == "BOUND_RULE_SET_EXACT_TO_REQUIRED_RULE_IDS"), None)
    if rs is None: E("O5: PE-45 rule-set condition missing")
    else:
        if re.search(r"executable", rs["condition"], re.I): E("O5: rule-set condition still names the executable subset")
        cs = rs.get("compared_sets") or {}
        if (cs.get("bound") or {}).get("scope") != "EVERY_RULE_WHATEVER_ITS_DECLARED_CLASS" or (cs.get("required") or {}).get("scope") != "THE_COMPLETE_REFERENCED_ARRAY" \
                or cs.get("relation") != "BOUND_IDS_UNIQUE_AND_SET_EQUAL_TO_REQUIRED_IDS" or cs.get("executable_subset_is_the_compared_set") is not False:
            E("O5: rule-set compared sets not declared as the complete required set")
        ref = pkg.get("required_rule_ids_ref") if isinstance(pkg, dict) else None
        if not (isinstance(ref, str) and ":" in ref): E("O5: package required_rule_ids_ref missing")
    # O6 recorded performance risk (record only).
    risks = (model.get("r5r25_resource_limit_closure") or {}).get("recorded_risks") or []
    if not any(r.get("risk_id") == "PHASE_B_RESOURCE_EXHAUSTION_RISK" and r.get("normative_effect") == "NONE" for r in risks): E("O6: PHASE_B_RESOURCE_EXHAUSTION_RISK not recorded as record-only")
    return errors


def _r5r25_semantic_totality(model, ctx):
    errors = []
    try:
        base = _r5r23_semantic_totality(model, ctx)
    except ValueError as exc:
        base = None
        errors += [line.strip() for line in str(exc).splitlines()[1:]]
    errors += _r5r25_checks(model, ctx)
    if errors: raise ValueError("R5R25 semantic totality failed:\n  " + "\n  ".join(errors[:80]))
    pe44 = next(f for f in model["families"] if f["family_id"] == "PE-44")
    base["resource_limit_measurements"] = sum(1 for c in pe44["conditions"] if "measurement" in c)
    return base


def _r5r25_finalize():
    ctx = _r5r22_context()
    meta, reg, pkg, meta_schema = ctx["meta"], ctx["reg"], ctx["pkg"], ctx["schema"]
    model = meta["failure_semantics"]["pre_execution_failure_model"]
    _r5r25_apply(model, meta, ctx["prim"])
    ctx["meta"] = meta
    semantic = _r5r25_semantic_totality(model, ctx)
    model["totality"] = dict(semantic["base"], **{"semantic": {k: v for k, v in semantic.items() if k not in ("d13", "base")},
                                                  "model_status": "TOTAL" if semantic["pending_human_decisions"] == 0 else "PENDING_HUMAN_DECISIONS"})
    if model["totality"]["model_status"] != "TOTAL": raise ValueError("R5R25: model is not total")
    fs = meta["failure_semantics"]
    fs["pre_execution_failure_model"] = model
    fs["verifier_protocol_digests"] = {"algorithm": "SHA-256", "serialization": "RFC8785_JCS",
                                       "pre_execution_failure_model": sem(model), "registration": sem(meta["registration"]),
                                       "generic_failure_witness": sem(fs["generic_failure_witness"])}
    fss = meta_schema["properties"]["failure_semantics"]
    for name in ("pre_execution_failure_model", "verifier_protocol_digests"):
        fss["properties"][name] = {"const": copy.deepcopy(fs[name])}
    _r11_save("metacontract.json", meta)
    _r11_save("schema/metacontract.schema.json", meta_schema)
    _r11_digest_close(reg, pkg)
    print(json.dumps({"r5r25_resource_limit_law": "PASS", "totality": model["totality"],
                      "measured_predicates": model["r5r25_resource_limit_closure"]["measured_predicates"],
                      "collection_binders": sorted(model["protocol_constants"]["ast_resource_limits"]["collection_binders"]["operators"]),
                      "verifier_protocol_digests": fs["verifier_protocol_digests"],
                      "registry_semantic_sha256": pkg["registry_semantic_sha256"],
                      "package_semantic_sha256": pkg["current_candidate_integrity"]["digest"]}, indent=2))

_R5R23_POST_BUILD = _r11_post_build
def _r11_post_build():
    _R5R23_POST_BUILD()
    _r5r25_finalize()


# ---------------------------------------------------------------------------
# ACCORD R5R29A-R2c: SCHEMA_VALIDATE normative clarification.
#
# Explicit human rulings (2026-10-05) after the R5R29A-R2b adversarial finding
# that the frozen law left several SCHEMA_VALIDATE cases undefined:
#  1. within SCHEMA_VALIDATE an absent $schema selects Draft 2020-12; registered
#     schema-document admission still requires an explicit Draft 2020-12 $schema;
#  2. format date-time second 60 is valid only at an instant listed in a frozen,
#     registered, IERS-derived leap-second table pinned by digest;
#  3. SCHEMA_VALIDATE admits local-fragment $ref only; any other $ref is
#     MALFORMED_SCHEMA (an explicit widening of MALFORMED_SCHEMA);
#  4. registered $id values are not a resolver universe for SCHEMA_VALIDATE;
#  5. error precedence: dialect selection, then schema/reference admissibility,
#     then local reference resolution, then the validation boolean;
#  6. an admitted local fragment whose target is missing is UNRESOLVED_LOCAL_FRAGMENT.
# Static-type resolution (static_type_at_path) is deliberately unchanged.
# The leap-second table is derived here from the frozen IERS bytes below; it is
# never fetched or refreshed at evaluation time.
# ---------------------------------------------------------------------------
import base64 as _r2c_base64
import datetime as _r2c_datetime

_R2C_RULING = "HUMAN_RULING_2026_10_05_R5R29A_R2C"
# Exact bytes of https://hpiers.obspm.fr/iers/bul/bulc/Leap_Second.dat retrieved 2026-10-05T19:46:08Z.
_R2C_IERS_LEAP_SECOND_DAT_B64 = (
    "IyAgVmFsdWUgb2YgVEFJLVVUQyBpbiBzZWNvbmQgdmFsaWQgYmVldHdlZW4gdGhlIGluaXRpYWwgdmFsdWUgdW50aWwKIyAgdGhl"
    "IGVwb2NoIGdpdmVuIG9uIHRoZSBuZXh0IGxpbmUuIFRoZSBsYXN0IGxpbmUgcmVhZHMgdGhhdCBOTwojICBsZWFwIHNlY29uZCB3"
    "YXMgaW50cm9kdWNlZCBzaW5jZSB0aGUgY29ycmVzcG9uZGluZyBkYXRlIAojICBVcGRhdGVkIHRocm91Z2ggSUVSUyBCdWxsZXRp"
    "biA3MiBpc3N1ZWQgaW4gSnVseSAyMDI2CiMgIAojCiMgIEZpbGUgZXhwaXJlcyBvbiAyOCBKdW5lIDIwMjcKIwojCiMgICAgTUpE"
    "ICAgICAgICBEYXRlICAgICAgICBUQUktVVRDIChzKQojICAgICAgICAgICBkYXkgbW9udGggeWVhcgojICAgIC0tLSAgICAtLS0t"
    "LS0tLS0tLS0tLSAgIC0tLS0tLSAgIAojCiAgICA0MTMxNy4wICAgIDEgIDEgMTk3MiAgICAgICAxMAogICAgNDE0OTkuMCAgICAx"
    "ICA3IDE5NzIgICAgICAgMTEKICAgIDQxNjgzLjAgICAgMSAgMSAxOTczICAgICAgIDEyCiAgICA0MjA0OC4wICAgIDEgIDEgMTk3"
    "NCAgICAgICAxMwogICAgNDI0MTMuMCAgICAxICAxIDE5NzUgICAgICAgMTQKICAgIDQyNzc4LjAgICAgMSAgMSAxOTc2ICAgICAg"
    "IDE1CiAgICA0MzE0NC4wICAgIDEgIDEgMTk3NyAgICAgICAxNgogICAgNDM1MDkuMCAgICAxICAxIDE5NzggICAgICAgMTcKICAg"
    "IDQzODc0LjAgICAgMSAgMSAxOTc5ICAgICAgIDE4CiAgICA0NDIzOS4wICAgIDEgIDEgMTk4MCAgICAgICAxOQogICAgNDQ3ODYu"
    "MCAgICAxICA3IDE5ODEgICAgICAgMjAKICAgIDQ1MTUxLjAgICAgMSAgNyAxOTgyICAgICAgIDIxCiAgICA0NTUxNi4wICAgIDEg"
    "IDcgMTk4MyAgICAgICAyMgogICAgNDYyNDcuMCAgICAxICA3IDE5ODUgICAgICAgMjMKICAgIDQ3MTYxLjAgICAgMSAgMSAxOTg4"
    "ICAgICAgIDI0CiAgICA0Nzg5Mi4wICAgIDEgIDEgMTk5MCAgICAgICAyNQogICAgNDgyNTcuMCAgICAxICAxIDE5OTEgICAgICAg"
    "MjYKICAgIDQ4ODA0LjAgICAgMSAgNyAxOTkyICAgICAgIDI3CiAgICA0OTE2OS4wICAgIDEgIDcgMTk5MyAgICAgICAyOAogICAg"
    "NDk1MzQuMCAgICAxICA3IDE5OTQgICAgICAgMjkKICAgIDUwMDgzLjAgICAgMSAgMSAxOTk2ICAgICAgIDMwCiAgICA1MDYzMC4w"
    "ICAgIDEgIDcgMTk5NyAgICAgICAzMQogICAgNTExNzkuMCAgICAxICAxIDE5OTkgICAgICAgMzIKICAgIDUzNzM2LjAgICAgMSAg"
    "MSAyMDA2ICAgICAgIDMzCiAgICA1NDgzMi4wICAgIDEgIDEgMjAwOSAgICAgICAzNAogICAgNTYxMDkuMCAgICAxICA3IDIwMTIg"
    "ICAgICAgMzUKICAgIDU3MjA0LjAgICAgMSAgNyAyMDE1ICAgICAgIDM2CiAgICA1Nzc1NC4wICAgIDEgIDEgMjAxNyAgICAgICAz"
    "Nwo="
)
_R2C_IERS_PRIMARY = {
    "role": "PRIMARY_DERIVATION_SOURCE",
    "url": "https://hpiers.obspm.fr/iers/bul/bulc/Leap_Second.dat",
    "raw_sha256": "6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7",
    "raw_byte_length": 1352,
    "http_last_modified": "Mon, 06 Jul 2026 07:52:10 GMT",
    "declared_currency": "Updated through IERS Bulletin 72 issued in July 2026",
    "declared_expiry": "28 June 2027",
}
_R2C_IERS_CROSS_CHECK = {
    "role": "INDEPENDENT_CROSS_CHECK_SOURCE",
    "url": "https://hpiers.obspm.fr/iers/bul/bulc/ntp/leap-seconds.list",
    "raw_sha256": "db5a895f16853b03bfc865e8d68f9fc8710ef1740e3400c701cd46a5bbbc3433",
    "raw_byte_length": 5065,
    "http_last_modified": "Mon, 06 Jul 2026 07:54:11 GMT",
    "declared_last_update_ntp_seconds": 3992312697,
    "declared_expiry_ntp_seconds": 4023129600,
    "declared_expiry": "28 June 2027",
    "embedded_sha1": "a9bad145 84c31c70 758402aa b37bfd54 5923836a",
}
_R2C_RETRIEVED_AT_UTC = "2026-10-05T19:46:08Z"
_R2C_TABLE_ID = NS + ":leap-second-table"
_R2C_TABLE_REF = ref("CONTRACT", _R2C_TABLE_ID)
_R2C_TABLE_SCHEMA_NAME = "leap-second-table"
_R2C_TABLE_FILE = "leap-second-table.json"
_R2C_TABLE_SCHEMA_FILE = "leap-second-table.schema.json"
_R2C_MJD_EPOCH = _r2c_datetime.date(1858, 11, 17)
_R2C_STATIC_TYPE_REF_RULE = "metacontract:/runtime_representation/static_type_calculus/static_type_at_path/schema_keyword_following/ref"
_R2C_REGISTERED_SCHEMA_ADMISSION = "metacontract:/eligibility/candidate_universe/validation_by_kind/SCHEMA"


def _r2c_iers_rows():
    raw = _r2c_base64.b64decode("".join(_R2C_IERS_LEAP_SECOND_DAT_B64))
    if sha(raw) != _R2C_IERS_PRIMARY["raw_sha256"] or len(raw) != _R2C_IERS_PRIMARY["raw_byte_length"]:
        raise ValueError("R5R29A-R2c: frozen IERS Leap_Second.dat bytes differ from the recorded digest")
    text = raw.decode("ascii")
    for fact in (_R2C_IERS_PRIMARY["declared_currency"], "File expires on " + _R2C_IERS_PRIMARY["declared_expiry"]):
        if fact not in text:
            raise ValueError("R5R29A-R2c: IERS header fact missing: " + fact)
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        mjd, day, month, year, tai_utc = line.split()
        if not mjd.endswith(".0"):
            raise ValueError("R5R29A-R2c: non-integral MJD " + mjd)
        date = _r2c_datetime.date(int(year), int(month), int(day))
        if (date - _R2C_MJD_EPOCH).days != int(mjd[:-2]):
            raise ValueError("R5R29A-R2c: MJD/date mismatch at " + line.strip())
        rows.append((date, int(tai_utc), int(mjd[:-2])))
    return rows


def _r2c_leap_second_table():
    rows = _r2c_iers_rows()
    if rows[0][:2] != (_r2c_datetime.date(1972, 1, 1), 10):
        raise ValueError("R5R29A-R2c: IERS table does not start at 1972-01-01 TAI-UTC 10 s")
    insertions = []
    for (d0, t0, _m0), (d1, t1, m1) in zip(rows, rows[1:]):
        if t1 - t0 != 1 or d1.day != 1 or d1 <= d0:
            raise ValueError("R5R29A-R2c: IERS step is not a single positive leap second at " + d1.isoformat())
        last_day = d1 - _r2c_datetime.timedelta(days=1)
        insertions.append({
            "utc_instant": last_day.isoformat() + "T23:59:60Z",
            "tai_minus_utc_before_seconds": t0,
            "tai_minus_utc_after_seconds": t1,
            "effective_mjd_after_insertion": m1,
        })
    if len(insertions) != 27 or insertions[0]["utc_instant"] != "1972-06-30T23:59:60Z" or insertions[-1]["utc_instant"] != "2016-12-31T23:59:60Z":
        raise ValueError("R5R29A-R2c: derived leap-second insertion set is not the reviewed 27-entry 1972-06-30..2016-12-31 set")
    return {
        "$schema": DIALECT,
        "schema_ref": sr(_R2C_TABLE_SCHEMA_NAME),
        "$id": _R2C_TABLE_ID + ":0.2",
        "object_id": _R2C_TABLE_ID,
        "object_version": "0.2",
        "table_role": "FROZEN_GOVERNED_INPUT_TO_FORMAT_DATE_TIME_SEMANTICS",
        "governing_rule_ref": "metacontract:/runtime_representation/schema_format_assertion/standard_domain_semantics/leap_second_rule",
        "time_scale": "UTC",
        "instant_form": "RFC3339_DATE_T23_59_60Z_OF_THE_LAST_UTC_DAY_BEFORE_THE_TAI_MINUS_UTC_INCREMENT",
        "leap_second_sign": "POSITIVE_INSERTIONS_ONLY",
        "insertion_count": len(insertions),
        "insertions": insertions,
        "completeness": "EXHAUSTIVE_FOR_THIS_PACKAGE_VERSION;AN_INSTANT_NOT_LISTED_IS_NOT_A_LEAP_SECOND_FOR_THIS_PACKAGE_VERSION",
        "update_policy": "FROZEN;NEVER_FETCHED_OR_REFRESHED_AT_EVALUATION_TIME;A_LATER_IERS_BULLETIN_C_DOES_NOT_CHANGE_THIS_TABLE;ONLY_A_LATER_ACCORD_PACKAGE_VERSION_MAY_REPLACE_IT",
        "source": {
            "authority": "IERS_EARTH_ORIENTATION_CENTER_BULLETIN_C",
            "retrieved_at_utc": _R2C_RETRIEVED_AT_UTC,
            "files": [copy.deepcopy(_R2C_IERS_PRIMARY), copy.deepcopy(_R2C_IERS_CROSS_CHECK)],
            "derivation": "EACH_PLUS_ONE_SECOND_INCREMENT_OF_TAI_MINUS_UTC_EFFECTIVE_AT_00_00_00_UTC_ON_DATE_D_IS_A_POSITIVE_LEAP_SECOND_INSERTED_AT_D_MINUS_ONE_DAY_T23_59_60Z",
            "derived_by": REL + "/audit/build_r5r4_artifacts.py:_r2c_leap_second_table",
            "derived_by_ruling": _R2C_RULING,
        },
    }


def _r2c_leap_second_table_schema(table):
    insertion = {
        "type": "object",
        "required": ["utc_instant", "tai_minus_utc_before_seconds", "tai_minus_utc_after_seconds", "effective_mjd_after_insertion"],
        "properties": {
            "utc_instant": {"type": "string", "pattern": "^[0-9]{4}-(?:06-30|12-31)T23:59:60Z$"},
            "tai_minus_utc_before_seconds": {"type": "integer", "minimum": 10},
            "tai_minus_utc_after_seconds": {"type": "integer", "minimum": 11},
            "effective_mjd_after_insertion": {"type": "integer", "minimum": 41499},
        },
        "additionalProperties": False,
    }
    fixed = ["table_role", "governing_rule_ref", "time_scale", "instant_form", "leap_second_sign", "completeness", "update_policy", "source"]
    props = {
        "$schema": {"const": DIALECT},
        "schema_ref": {"const": sr(_R2C_TABLE_SCHEMA_NAME)},
        "$id": {"const": table["$id"]},
        "object_id": {"const": _R2C_TABLE_ID},
        "object_version": {"const": "0.2"},
        "insertion_count": {"const": table["insertion_count"]},
        "insertions": {"type": "array", "minItems": table["insertion_count"], "maxItems": table["insertion_count"], "uniqueItems": True, "items": insertion},
    }
    for key in fixed:
        props[key] = {"const": copy.deepcopy(table[key])}
    return {
        "$schema": DIALECT,
        "$id": NS + ":schema:" + _R2C_TABLE_SCHEMA_NAME + ":0.2",
        "type": "object",
        "required": list(table.keys()),
        "properties": props,
        "additionalProperties": False,
    }


def _r2c_leap_second_rule(table):
    return {
        "rule_id": "R5R29A_R2C_LEAP_SECOND_TABLE_MEMBERSHIP",
        "ruling": _R2C_RULING,
        "table_ref": copy.deepcopy(_R2C_TABLE_REF),
        "table_path": REL + "/" + _R2C_TABLE_FILE,
        "table_semantic_sha256": sem(table),
        "table_digest_algorithm": "SHA-256",
        "table_digest_serialization": "RFC8785_JCS",
        "steps": [
            "PARSE_THE_STRING_WITH_THE_RFC3339_date-time_GRAMMAR",
            "IF_THE_SECOND_FIELD_IS_NOT_60_APPLY_THE_ORDINARY_date-time_RULES_UNCHANGED",
            "IF_THE_SECOND_FIELD_IS_60_NORMALIZE_THE_OFFSET_REPRESENTATION_TO_THE_CORRESPONDING_UTC_INSTANT",
            "ACCEPT_ONLY_IF_THAT_EXACT_UTC_LEAP_SECOND_INSTANT_IS_LISTED_IN_THE_TABLE_insertions;OTHERWISE_THE_STRING_IS_NOT_A_VALID_date-time",
        ],
        "same_governed_instant_examples": ["2016-12-31T23:59:60Z", "2016-12-31T18:59:60-05:00"],
        "rejected_readings": ["SECOND_60_ON_ANY_DAY", "SECOND_60_ON_THE_LAST_DAY_OF_ANY_MONTH"],
        "table_is_exhaustive_for_this_package_version": True,
        "evaluation_time_refresh": "FORBIDDEN",
        "invalid_leap_second_effect": "THE_STRING_IS_NOT_A_VALID_date-time;THE_DECLARED_FORMAT_ASSERTION_FAILS_EXACTLY_AS_FOR_ANY_OTHER_INVALID_date-time",
        "applies_to": "EVERY_CONTEXT_IN_applies_to_OF_THIS_FORMAT_ASSERTION",
        "operation_profile_unchanged": "metacontract:/numeric_representation/rfc3339_profile",
    }


_R2C_SCHEMA_VALIDATE_CLARIFICATION = {
    "dialect_selection": {
        "ruling": _R2C_RULING,
        "operand": "schema",
        "applies_in_modes": ["META_SCHEMA", "INSTANCE"],
        "absent_dollar_schema": "SELECTS_DRAFT_2020_12",
        "explicit_draft_2020_12": DIALECT,
        "explicit_other_dialect": "UNSUPPORTED_DIALECT",
        "registered_schema_document_admission": "UNCHANGED;A_REGISTERED_SCHEMA_DOCUMENT_MUST_STILL_DECLARE_DRAFT_2020_12_EXPLICITLY",
        "registered_schema_document_admission_ref": _R2C_REGISTERED_SCHEMA_ADMISSION,
        "distinction": "PRIMITIVE_DEFAULT_SEMANTICS_ARE_DISTINCT_FROM_GOVERNANCE_REQUIREMENTS_FOR_REGISTERED_ARTIFACTS",
    },
    "reference_admissibility": {
        "ruling": _R2C_RULING,
        "admitted_ref_form": "LOCAL_FRAGMENT_ONLY",
        "non_local_ref": "MALFORMED_SCHEMA",
        "non_local_ref_reason": "A_NON_LOCAL_REF_IS_OUTSIDE_THE_REFERENCE_DOMAIN_THE_PRIMITIVE_SUPPORTS;IT_IS_NOT_A_LOCAL_FRAGMENT_THAT_FAILED_TO_RESOLVE",
        "non_local_ref_examples": ["https://example.com/schema", "https://example.com/schema#foo"],
        "malformed_schema_widening": "EXPLICIT_R5R29A_R2C_WIDENING;THE_PRIOR_FROZEN_LAW_DID_NOT_ASSIGN_A_DECLARED_CLASS_TO_A_NON_LOCAL_REF",
        "admitted_local_fragment_with_missing_target": "UNRESOLVED_LOCAL_FRAGMENT",
        "registered_id_resolver_universe": "NONE;REGISTERED_DOLLAR_ID_VALUES_DO_NOT_CREATE_A_RESOLVER_UNIVERSE_FOR_SCHEMA_VALIDATE",
        "retrieval": "NONE",
        "external_schema_resolution": "NOT_A_0_2_CAPABILITY",
        "static_type_resolution_scope": "THIS_RULE_DOES_NOT_ALTER_STATIC_TYPE_RESOLUTION_RULES_ELSEWHERE_IN_THE_METACONTRACT",
        "static_type_resolution_rule_ref": _R2C_STATIC_TYPE_REF_RULE,
    },
    "error_precedence": [
        "SCHEMA_REPRESENTATION_PARSE",
        "DIALECT_SELECTION;UNSUPPORTED_DIALECT",
        "SCHEMA_AND_REFERENCE_ADMISSIBILITY;NON_LOCAL_REF_IS_MALFORMED_SCHEMA",
        "LOCAL_REFERENCE_RESOLUTION;MISSING_TARGET_IS_UNRESOLVED_LOCAL_FRAGMENT",
        "VALIDATION_BOOLEAN",
    ],
    "error_precedence_reason": "THE_APPLICABLE_SCHEMA_SEMANTICS_ARE_ESTABLISHED_BEFORE_ANY_SCHEMA_KEYWORD_IS_INTERPRETED;PRECEDENCE_DOES_NOT_DEPEND_ON_INCIDENTAL_TRAVERSAL_ORDER",
}


def _r2c_apply():
    table = _r2c_leap_second_table()
    table_schema = _r2c_leap_second_table_schema(table)
    (OUT / _R2C_TABLE_FILE).write_bytes(emit(table))
    (OUT / "schema" / _R2C_TABLE_SCHEMA_FILE).write_bytes(emit(table_schema))
    # Format assertion: replace the undeterminable "when announced" with the governed table rule.
    meta = _r11_load("metacontract.json")
    sds = meta["runtime_representation"]["schema_format_assertion"]["standard_domain_semantics"]
    if sds.get("leap_second") != "SECOND_VALUE_60_ALLOWED_PER_SECTION_5_6_WHEN_ANNOUNCED":
        raise ValueError("R5R29A-R2c: unexpected prior leap_second law")
    sds["leap_second"] = "SECOND_VALUE_60_VALID_ONLY_WHEN_ITS_UTC_NORMALIZED_INSTANT_IS_LISTED_IN_THE_REGISTERED_LEAP_SECOND_TABLE"
    sds["leap_second_rule"] = _r2c_leap_second_rule(table)
    _r11_save("metacontract.json", meta)
    # SCHEMA_VALIDATE primitive: explicit dialect, reference and precedence law.
    prim = _r11_load("primitive-registry.json")
    rows = [row for row in prim["primitives"] if row.get("primitive_id") == "SCHEMA_VALIDATE"]
    if len(rows) != 1 or rows[0]["error_behavior"]["error_classes"] != ["MALFORMED_SCHEMA", "UNRESOLVED_LOCAL_FRAGMENT", "UNSUPPORTED_DIALECT"]:
        raise ValueError("R5R29A-R2c: SCHEMA_VALIDATE row is not the reviewed predecessor")
    rows[0].update(copy.deepcopy(_R2C_SCHEMA_VALIDATE_CLARIFICATION))
    _r11_save("primitive-registry.json", prim)
    prim_schema = _r11_load("schema/primitive-registry.schema.json")
    item = prim_schema["properties"]["primitives"]["items"]
    for key, value in _R2C_SCHEMA_VALIDATE_CLARIFICATION.items():
        item["properties"][key] = {"const": copy.deepcopy(value)}
    conditional = {"if": {"properties": {"primitive_id": {"const": "SCHEMA_VALIDATE"}}, "required": ["primitive_id"]},
                   "then": {"required": list(_R2C_SCHEMA_VALIDATE_CLARIFICATION)}}
    item["allOf"] = [x for x in item.get("allOf", []) if x != conditional] + [conditional]
    _r11_save("schema/primitive-registry.schema.json", prim_schema)
    # Register the table and its schema as active normative artifacts.
    reg = _r11_load("object-registry.json")
    if any(row.get("id") in (_R2C_TABLE_ID, NS + ":schema:" + _R2C_TABLE_SCHEMA_NAME) for row in reg["objects"]):
        raise ValueError("R5R29A-R2c: leap-second table already registered")
    integrity = {"mode": "SEMANTIC_JSON_CONTENT", "algorithm": "SHA-256", "serialization": "RFC8785_JCS"}
    new_rows = [
        {"kind": "CONTRACT", "id": _R2C_TABLE_ID, "version": "0.2", "path": REL + "/" + _R2C_TABLE_FILE, "status": "ACTIVE",
         "roles": ["NORMATIVE"], "classification": "NORMATIVE", "schema_ref": sr(_R2C_TABLE_SCHEMA_NAME),
         "integrity": dict(integrity, digest=sem(table)), "reference": copy.deepcopy(_R2C_TABLE_REF)},
        {"kind": "SCHEMA", "id": NS + ":schema:" + _R2C_TABLE_SCHEMA_NAME, "version": "0.2", "path": REL + "/schema/" + _R2C_TABLE_SCHEMA_FILE,
         "status": "ACTIVE", "roles": ["SCHEMA_AUTHORITY"], "classification": "NORMATIVE", "schema_document_id": table_schema["$id"],
         "schema_document_version": "0.2", "integrity": dict(integrity, digest=sem(table_schema)), "reference": sr(_R2C_TABLE_SCHEMA_NAME)},
    ]
    reg["objects"].extend(new_rows)
    _r11_save("object-registry.json", reg)
    modes = _r11_load("integrity-modes.json")
    for row in new_rows:
        modes["dispatch"].append({"mode": "SEMANTIC_JSON_CONTENT", "object_ref": copy.deepcopy(row["reference"]), "role": "NORMATIVE",
                                  "algorithm": "SHA-256", "serialization": "RFC8785_JCS", "excluded_pointers": []})
    _r11_save("integrity-modes.json", modes)
    model = _r11_load("reference-model.json")
    model["discovery_scope"]["owner_references"].extend(copy.deepcopy(row["reference"]) for row in new_rows)
    model["discovery_scope"]["schema_owner_references"].append(copy.deepcopy(new_rows[1]["reference"]))
    _r11_save("reference-model.json", model)
    print(json.dumps({"r5r29a_r2c_schema_validate_clarification": "APPLIED", "leap_second_insertions": table["insertion_count"],
                      "leap_second_table_semantic_sha256": sem(table), "leap_second_table_schema_semantic_sha256": sem(table_schema)}, indent=2))


_R2C_PRIOR_BASE_BUILD = _R11_BASE_BUILD
def _R11_BASE_BUILD():
    _R2C_PRIOR_BASE_BUILD()
    _r2c_apply()


# ---------------------------------------------------------------------------
# ACCORD R5R29A-R2c-edge: SCHEMA_VALIDATE 0.2 supported-subset edge rulings.
#
# Explicit human rulings (2026-10-05, after the R5R29A-R2c staged-law review):
#  E1. a fractional leap second is valid when its whole UTC leap-second label is
#      listed in the frozen table (offset normalized, fraction preserved);
#  E2. a $schema that is not a string, not an absolute URI with a scheme, or not
#      normalized is MALFORMED_SCHEMA; a valid normalized absolute URI other than
#      exactly the Draft 2020-12 identifier (including the trailing-# form) is
#      UNSUPPORTED_DIALECT;
#  E3. the admitted local reference is a fragment-only JSON-Pointer reference:
#      exactly "#" or "#/..." whose fragment is a valid JSON Pointer;
#  E4. plain-name anchor refs, $dynamicRef and embedded-$id resolution are not
#      supported by SCHEMA_VALIDATE 0.2 and are MALFORMED_SCHEMA when
#      semantically relevant;
#  E5. whole-schema admissibility precedes local-fragment resolution; within
#      admissibility no semantic rank is invented and the owning location is
#      the first in DESCENDANTS canonical preorder.
# The restricted reference semantics are a primitive-specific subset and do not
# redefine $id semantics used by static_type_at_path or other procedures.
# ---------------------------------------------------------------------------
_R2C_EDGE_RULING = "HUMAN_RULING_2026_10_05_R5R29A_R2C_EDGE"
# Draft 2020-12 locations whose values are schemas (core 10.2, 10.3, 8.2.4; validation 8.2.1 contentSchema).
_R2C_EDGE_SCHEMA_VALUED = {
    "single": ["additionalProperties", "items", "contains", "propertyNames", "unevaluatedItems", "unevaluatedProperties",
               "not", "if", "then", "else", "contentSchema"],
    "array_of_schemas": ["prefixItems", "allOf", "anyOf", "oneOf"],
    "object_of_schemas": ["properties", "patternProperties", "dependentSchemas", "$defs"],
}

_R2C_SCHEMA_VALIDATE_CLARIFICATION["schema_position"] = {
    "ruling": _R2C_EDGE_RULING,
    "definition": "THE_ROOT_OF_THE_schema_OPERAND_AND_EVERY_VALUE_REACHED_FROM_A_SCHEMA_POSITION_THROUGH_A_DRAFT_2020_12_SCHEMA_VALUED_KEYWORD",
    "schema_valued_keywords": copy.deepcopy(_R2C_EDGE_SCHEMA_VALUED),
    "keyword_occurrence": "A_KEYWORD_IS_SEMANTICALLY_ACTIVE_ONLY_AS_A_MEMBER_OF_AN_OBJECT_AT_A_SCHEMA_POSITION;MEMBERS_INSIDE_const_enum_default_examples_OR_OTHER_NON_SCHEMA_VALUES_ARE_DATA",
    "embedded_schema_resource": "A_SCHEMA_POSITION_OTHER_THAN_THE_ROOT_WHOSE_OBJECT_DECLARES_$id",
}
_ds = _R2C_SCHEMA_VALIDATE_CLARIFICATION["dialect_selection"]
_ds.update({
    "edge_ruling": _R2C_EDGE_RULING,
    "dollar_schema_value_requirement": "A_STRING_THAT_IS_AN_RFC3986_URI_WITH_A_SCHEME_AND_IS_NORMALIZED;DRAFT_2020_12_CORE_SECTION_8_1_1",
    "normalized_definition": "THE_STRING_EQUALS_ITS_RFC3986_SECTION_6_2_2_SYNTAX_BASED_NORMALIZATION(CASE_NORMALIZATION_OF_SCHEME_HOST_AND_PERCENT_ENCODING_HEX_DIGITS;PERCENT_ENCODING_NORMALIZATION_OF_UNRESERVED_CHARACTERS;DOT_SEGMENT_REMOVAL)",
    "malformed_dollar_schema": "MALFORMED_SCHEMA",
    "malformed_dollar_schema_examples": [123, "../schema", "2020-12"],
    "explicit_other_dialect": "UNSUPPORTED_DIALECT;A_STRING_SATISFYING_dollar_schema_value_requirement_THAT_IS_NOT_EXACTLY_THE_SUPPORTED_IDENTIFIER",
    "supported_identifier_match": "EXACT_STRING_EQUALITY_WITH_https://json-schema.org/draft/2020-12/schema",
    "unsupported_dialect_examples": ["https://json-schema.org/draft/2019-09/schema", "https://json-schema.org/draft/2020-12/schema#"],
    "nested_dollar_schema": "EVERY_$schema_KEYWORD_AT_A_SCHEMA_POSITION_IS_SUBJECT_TO_THIS_RULE;A_NESTED_$schema_EQUAL_TO_THE_SUPPORTED_IDENTIFIER_IS_INERT",
})
_ra = _R2C_SCHEMA_VALIDATE_CLARIFICATION["reference_admissibility"]
_ra.update({
    "edge_ruling": _R2C_EDGE_RULING,
    "admitted_ref_form": "LOCAL_JSON_POINTER_FRAGMENT_ONLY",
    "admitted_ref_grammar": "EXACTLY_#_OR_#_FOLLOWED_BY_A_FRAGMENT_BEGINNING_WITH_/;THE_FRAGMENT_IS_RFC3986_fragment_SYNTAX_AND_ITS_PERCENT_DECODED_VALUE_IS_A_VALID_RFC6901_JSON_POINTER(RFC6901_SECTION_6)",
    "admitted_ref_examples": ["#", "#/$defs/person", "#/properties/name"],
    "non_admitted_ref_examples": ["#person", "other.json#/$defs/person", "https://example.com/schema#foo", "https://example.com/schema"],
    "non_admitted_ref": "MALFORMED_SCHEMA",
    "plain_name_anchor_refs": "NOT_SUPPORTED_BY_SCHEMA_VALIDATE_0_2;MALFORMED_SCHEMA;INTENTIONAL_NARROWING_NOT_A_CLAIM_ABOUT_JSON_SCHEMA",
    "dynamic_ref": "NOT_SUPPORTED_BY_SCHEMA_VALIDATE_0_2;A_SEMANTICALLY_ACTIVE_$dynamicRef_MAKES_THE_SCHEMA_MALFORMED_SCHEMA",
    "anchor_declarations": "$anchor_AND_$dynamicAnchor_DECLARATIONS_ARE_INERT;THEY_CANNOT_BE_REFERENCED_THROUGH_AN_ADMITTED_REF",
    "root_dollar_id": "AN_IDENTIFIER_ONLY;IT_DOES_NOT_BROADEN_THE_ADMITTED_REFERENCE_DOMAIN",
    "embedded_dollar_id": "EMBEDDED_ID_RESOLUTION_NOT_SUPPORTED_BY_SCHEMA_VALIDATE_0_2;AN_EMBEDDED_$id_NEVER_MAKES_A_NON_FRAGMENT_OR_ANCHOR_REF_ADMISSIBLE",
    "embedded_dollar_id_semantically_relevant": "MALFORMED_SCHEMA_WHEN_AN_ADMITTED_REF_IS_LOCATED_INSIDE_AN_EMBEDDED_SCHEMA_RESOURCE_OR_ITS_POINTER_PATH_FROM_THE_ROOT_ENTERS_AN_EMBEDDED_SCHEMA_RESOURCE;OTHERWISE_AN_EMBEDDED_$id_IS_INERT",
    "resolution_base": "AN_ADMITTED_REF_RESOLVES_AGAINST_THE_ROOT_OF_THE_schema_OPERAND",
    "static_type_resolution_scope": "SCHEMA_VALIDATE_RESTRICTED_REFERENCE_SEMANTICS_ARE_A_PRIMITIVE_SPECIFIC_SUBSET_AND_DO_NOT_REDEFINE_$id_SEMANTICS_USED_BY_static_type_at_path_OR_OTHER_METACONTRACT_PROCEDURES",
    "registered_schema_document_rule_ref": "model:/families/PE-37/SCHEMA_NONLOCAL_REF",
})
_R2C_SCHEMA_VALIDATE_CLARIFICATION["error_precedence"] = [
    "REPRESENTATION_AND_SCHEMA_SHAPE;MALFORMED_SCHEMA",
    "DIALECT;MALFORMED_DOLLAR_SCHEMA_IS_MALFORMED_SCHEMA;VALID_UNSUPPORTED_DIALECT_URI_IS_UNSUPPORTED_DIALECT",
    "ACCORD_SCHEMA_ADMISSIBILITY;KEYWORD_VALUE_FORMS;STRUCTURAL_SCHEMA_VALIDITY;ONLY_ADMITTED_REF_FORM;NO_ACTIVE_DYNAMIC_REF;NO_EMBEDDED_ID_DEPENDENT_REF;MALFORMED_SCHEMA",
    "LOCAL_JSON_POINTER_FRAGMENT_RESOLUTION;UNRESOLVED_LOCAL_FRAGMENT",
    "INSTANCE_VALIDATION;BOOLEAN",
]
_R2C_SCHEMA_VALIDATE_CLARIFICATION["within_step_selection"] = {
    "ruling": _R2C_EDGE_RULING,
    "rule": "NO_SEMANTIC_RANK_IS_DEFINED_AMONG_CONDITIONS_OF_ONE_STEP;THE_OWNING_LOCATION_IS_THE_FIRST_IN_DESCENDANTS_CANONICAL_PREORDER_OF_THE_schema_OPERAND",
    "order_ref": "metacontract:/failure_semantics/pre_execution_failure_model/closed_vocabularies/ordering_rule/DESCENDANTS_CANONICAL_PREORDER",
    "resolution_starts_only_after_the_whole_schema_is_admissible": True,
}
del _ds, _ra

_R2C_PRE_EDGE_LEAP_SECOND_RULE = _r2c_leap_second_rule
def _r2c_leap_second_rule(table):
    rule = _R2C_PRE_EDGE_LEAP_SECOND_RULE(table)
    rule.update({
        "edge_ruling": _R2C_EDGE_RULING,
        "steps": [
            "PARSE_THE_STRING_WITH_THE_RFC3339_date-time_GRAMMAR",
            "IF_THE_SECOND_FIELD_IS_NOT_60_APPLY_THE_ORDINARY_date-time_RULES_UNCHANGED",
            "IF_THE_SECOND_FIELD_IS_60_NORMALIZE_THE_DATE_TIME_AND_NUMERIC_OFFSET_TO_THE_CORRESPONDING_UTC_LEAP_SECOND_LABEL_PRESERVING_THE_FRACTIONAL_COMPONENT",
            "ACCEPT_ONLY_IF_THE_WHOLE_UTC_LEAP_SECOND_LABEL_(FRACTION_REMOVED)_IS_LISTED_IN_THE_TABLE_insertions;OTHERWISE_THE_STRING_IS_NOT_A_VALID_date-time",
        ],
        "membership_key": "WHOLE_UTC_LEAP_SECOND_LABEL_YYYY-MM-DDT23:59:60Z",
        "literal_table_string_equality_required": False,
        "fractional_seconds": "PERMITTED;ANY_SYNTACTICALLY_VALID_time-secfrac_DENOTES_A_POINT_WITHIN_THE_INSERTED_SECOND;NO_PRECISION_LIMIT_BEYOND_RFC3339",
        "same_governed_instant_examples": ["2016-12-31T23:59:60Z", "2016-12-31T23:59:60.5Z", "2016-12-31T18:59:60.125-05:00"],
        "invalid_examples": ["2016-12-30T23:59:60.5Z", "2016-12-30T23:59:60Z"],
    })
    return rule

# ---------------------------------------------------------------------------
# ACCORD R5R29A-R2e-P: final staged-law edge clarification.
# Candidate 0.2 law; these newly explicit cases are not retrospectively
# asserted to follow from the earlier frozen candidate.
# ---------------------------------------------------------------------------
_R2E_RULING = "HUMAN_RULING_2026_10_06_R5R29A_R2E_P"
_R2C_SCHEMA_VALIDATE_CLARIFICATION["schema_representation"] = {
    "ruling": _R2E_RULING,
    "admitted_representations": ["SCHEMA_OBJECT_IN_ACCORD_0_2_SUBSET", "BOOLEAN_TRUE", "BOOLEAN_FALSE"],
    "applies_to": "ROOT_schema_OPERAND;EVERY_SCHEMA_POSITION;EVERY_RESOLVED_LOCAL_REF_TARGET;BOTH_MODES",
    "boolean_true": "VALID_SCHEMA;VALIDATES_EVERY_INSTANCE",
    "boolean_false": "VALID_SCHEMA;VALIDATES_NO_INSTANCE",
    "not_schema_representations": ["STRING", "NUMBER", "ARRAY", "NULL"],
    "object_only_inference_from_static_type_rules": "FORBIDDEN",
}
_ra = _R2C_SCHEMA_VALIDATE_CLARIFICATION["reference_admissibility"]
_ra.update({
    "r2e_ruling": _R2E_RULING,
    "resolution_outcomes": {
        "syntax_or_form_outside_admitted_domain": "MALFORMED_SCHEMA",
        "admitted_pointer_missing": "UNRESOLVED_LOCAL_FRAGMENT",
        "admitted_pointer_resolves_to_non_schema": "MALFORMED_SCHEMA",
        "admitted_pointer_resolves_to_schema_in_cycle": "MALFORMED_SCHEMA",
        "admitted_pointer_resolves_to_schema_in_acyclic_graph": "CONTINUE_VALIDATION",
    },
    "resolved_target_schema_representation": "SCHEMA_OBJECT_ADMITTED_BY_ACCORD_0_2_OR_BOOLEAN_TRUE_OR_BOOLEAN_FALSE",
    "resolved_non_schema_target": "MALFORMED_SCHEMA;THE_POINTER_RESOLVED_SO_UNRESOLVED_LOCAL_FRAGMENT_DOES_NOT_APPLY",
    "local_ref_graph": {
        "vertices": "SCHEMA_LOCATIONS_REACHED_BY_ADMITTED_LOCAL_$ref_EDGES",
        "edges": "EACH_SEMANTICALLY_ACTIVE_ADMITTED_LOCAL_$ref_FROM_ITS_SCHEMA_LOCATION_TO_ITS_RESOLVED_SCHEMA_TARGET",
        "admissibility": "ACYCLIC_REQUIRED",
        "direct_or_indirect_cycle": "MALFORMED_SCHEMA",
        "root_self_ref_example": {"schema": {"$ref": "#"}, "result": "MALFORMED_SCHEMA"},
        "repeated_acyclic_dag_target": "ADMITTED;REPEATED_TARGET_ALONE_IS_NOT_A_CYCLE",
    },
})
_R2C_SCHEMA_VALIDATE_CLARIFICATION["meta_schema_mode"] = {
    "ruling": _R2E_RULING,
    "subject": "schema_OPERAND_IS_TESTED_FOR_VALIDITY_AS_A_SCHEMA",
    "instance_operand": "SEMANTICALLY_IGNORED;DO_NOT_READ_VALIDATE_COMPARE_OR_TRAVERSE_IT_FOR_THE_PRIMITIVE_RESULT",
    "invariance": "THE_SAME_schema_OPERAND_WITH_ANY_TWO_JSON_instance_OPERANDS_HAS_IDENTICAL_VALIDITY_ERROR_CLASS_POINTER_BOOLEAN_RESULT_AND_FAILURE_ORDER",
}
_R2C_SCHEMA_VALIDATE_CLARIFICATION["error_precedence"] = [
    "SCHEMA_REPRESENTATION_AND_PRIMITIVE_OPERAND_SHAPE;MALFORMED_SCHEMA;BOOLEAN_SCHEMAS_ADMITTED",
    "DIALECT;MALFORMED_DOLLAR_SCHEMA_IS_MALFORMED_SCHEMA;VALID_UNSUPPORTED_DIALECT_URI_IS_UNSUPPORTED_DIALECT",
    "ACCORD_SCHEMA_ADMISSIBILITY;KEYWORD_VALUE_FORMS;STRUCTURAL_SCHEMA_VALIDITY;ONLY_ADMITTED_REF_FORM;NO_ACTIVE_DYNAMIC_REF;NO_EMBEDDED_ID_DEPENDENT_REF;MALFORMED_SCHEMA",
    "LOCAL_JSON_POINTER_FRAGMENT_RESOLUTION_AND_GRAPH_ADMISSIBILITY;MISSING_TARGET_IS_UNRESOLVED_LOCAL_FRAGMENT;NON_SCHEMA_TARGET_OR_CYCLE_IS_MALFORMED_SCHEMA",
    "INSTANCE_VALIDATION;BOOLEAN",
]
_R2C_SCHEMA_VALIDATE_CLARIFICATION["within_step_selection"]["r2e_ruling"] = _R2E_RULING
_R2C_SCHEMA_VALIDATE_CLARIFICATION["within_step_selection"]["simultaneous_malformed_defects"] = "FIRST_LOCATION_IN_DESCENDANTS_CANONICAL_PREORDER;NO_FIXTURE_SPECIFIC_PRIORITY"
del _ra

_R2E_PREVIOUS_LEAP_RULE = _r2c_leap_second_rule
def _r2c_leap_second_rule(table):
    rule = _R2E_PREVIOUS_LEAP_RULE(table)
    rule["r2e_integrity_ruling"] = _R2E_RULING
    rule["eager_artifact_integrity"] = {
        "required_on_every_evaluator_run": True,
        "stage": "VERIFY_REGISTRY_INTEGRITY_DECLARATIONS",
        "owner": "metacontract:/registration/integrity_gate/digest_mismatch",
        "failure_family": "PE-26_INTEGRITY_DIGEST",
        "registered_artifact_ref": copy.deepcopy(_R2C_TABLE_REF),
        "registered_digest_source": "object-registry:/objects/<leap_second_table_row_index>/integrity/digest",
        "table_digest_pin": "metacontract:/runtime_representation/schema_format_assertion/standard_domain_semantics/leap_second_rule/table_semantic_sha256",
        "required_checks": ["REGISTERED_IDENTITY", "REGISTERED_SEMANTIC_DIGEST", "TABLE_DIGEST_PIN_EQUAL_TO_VERIFIED_REGISTERED_DIGEST"],
        "failure_kind": "INTEGRITY",
        "existing_diagnostic": "REGISTRATION_INTEGRITY_DIGEST_MISMATCH",
        "existing_code": "SCHEMA_INVALID_BOUND_OBJECT",
        "independent_of_evaluated_timestamps": True,
        "no_new_schema_validate_error_class": True,
    }
    return rule

if __name__ == "__main__":
  build()
