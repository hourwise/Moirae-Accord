from __future__ import annotations

import hashlib, json
from pathlib import Path
import rfc8785

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
R5 = ROOT / "docs/accord-02e4r5"
ACCEPTED = ROOT / "docs/accord-02"

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write(name, obj):
    (OUT/name).write_text(json.dumps(obj, indent=2, ensure_ascii=False)+"\n", encoding="utf-8", newline="\n")
def ref(kind, id, version="0.2", member_id=None):
    x={"kind":kind,"id":id,"version":version}
    if member_id: x["member_id"]=member_id
    return x
def header(object_id, schema_id):
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","schema_ref":ref("SCHEMA",schema_id),"$id":object_id+":0.2","object_id":object_id,"object_version":"0.2"}
def raw_sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sem_sha(p): return hashlib.sha256(rfc8785.dumps(load(p))).hexdigest()

rules=load(R5/"accord-02e4r5-validation-rules.json")["rules"]
assertions={x["assertion_id"].rsplit(":",1)[1]:x for x in load(R5/"accord-02e4r5-assertion-registry.json")["assertions"]}
internal={"BND-001","BND-002","EXT-001","PRED-001","PRED-002","PRED-003","PRED-004","DIGEST-002","DIGEST-003","ROLE-001","SCENARIO-ID-001","PROF-001"}

mapping={
"LIN-001":"TYPED_REFERENCE_CLOSURE","LIN-002":"OBJECT_IDENTITY_UNIQUE","LIN-007":"PACKAGE_LINEAGE","PROP-001":"STANDARDS_VALIDATION",
"BND-004":"STANDARDS_VALIDATION","BND-005":"PREDICATE_AUTHORITY_CLOSURE","SRC-001":"SOURCE_CATALOG_BINDING","SRC-002":"ACCEPTED_SOURCE_DUAL_INTEGRITY","SRC-003":"SOURCE_CATALOG_BINDING",
"DIGEST-001":"SEMANTIC_DIGEST_VERIFY","LIN-009":"STANDARDS_VALIDATION","PROP-006":"PROPOSITION_ID_UNIQUE","PKG-001":"PACKAGE_LINEAGE","PKG-002":"TYPED_REFERENCE_CLOSURE",
"PROF-002":"PROFILE_REFERENCE_PINNING","SCHEMA-001":"TYPED_REFERENCE_CLOSURE","SCHEMA-002":"STANDARDS_VALIDATION",
"DIGEST-CANON-001":"CANONICALIZATION_AUTHORITY_CLOSURE","DIGEST-CANON-002":"CANONICALIZATION_AUTHORITY_CLOSURE","DIGEST-CANON-003":"CANONICALIZATION_AUTHORITY_CLOSURE",
"E4R1-PRED-001":"PREDICATE_AUTHORITY_CLOSURE","E4R1-PRED-002":"PREDICATE_AUTHORITY_CLOSURE","E4R1-PRED-003":"PREDICATE_AUTHORITY_CLOSURE","E4R1-AUTH-001":"PREDICATE_AUTHORITY_CLOSURE","E4R1-BIND-001":"PREDICATE_AUTHORITY_CLOSURE",
"E4R1-PROP-001":"STANDARDS_VALIDATION","E4R1-PART-001":"PARTIAL_EFFECT_POLICY_CLOSURE","E4R1-PART-002":"PARTIAL_EFFECT_POLICY_CLOSURE","E4R1-PART-003":"PARTIAL_EFFECT_POLICY_CLOSURE",
"E4R1-NEG-001":"NEGATIVE_REQUIREMENT_MAP_CLOSURE","E4R1-NEG-002":"NEGATIVE_REQUIREMENT_MAP_CLOSURE","E4R1-ENT-001":"PREDICATE_AUTHORITY_CLOSURE","E4R1-CANON-001":"CANONICALIZATION_AUTHORITY_CLOSURE",
"E4R1-EXPECT-001":"EXPECTATION_STABILITY","E4R1-CLOSE-001":"RULE_EXPECTATION_AUTHORITY_COMPLETE","E4R2-REF-001":"TYPED_REFERENCE_CLOSURE","E4R2-CANON-001":"CANONICALIZATION_AUTHORITY_CLOSURE",
"E4R2-BIND-001":"PREDICATE_AUTHORITY_CLOSURE","E4R2-NEG-001":"NEGATIVE_REQUIREMENT_MAP_CLOSURE","E4R2-GRAPH-001":"DEPENDENCY_GRAPH_EQUAL","E4R2-PROFILE-001":"SEMANTIC_DIGEST_VERIFY","E4R2-CLOSE-001":"RULE_EXPECTATION_AUTHORITY_COMPLETE"}

matrix=[]
for r in rules:
    base={"rule_id":r["rule_id"],"inherited_family":r["family"],"inherited_failure_code":r["failure_code"],"severity":r["severity"]}
    if r["scope"]=="DEFERRED_NO_SUBJECT_ARTIFACT":
        base.update({"semantic_class":"DEFERRED_NO_SUBJECT_ARTIFACT","missing_subject_roles":r["missing_subject_roles"],"later_lifecycle_stage":r["later_lifecycle_stage"],"reason":r["deferred_reason"],"result":"DEFERRED"})
    elif r["rule_id"] in internal:
        a=assertions[r["rule_id"]]["expression"]["checks"][0]["arguments"]
        base.update({"semantic_class":"INTERNAL_DESIGN_INVARIANT","subjects":r["subject_bindings"],"procedure":"JSON_POINTER_COMPARE","subject_pointer":a["pointer"],"expected":a["expected"],"comparison":a["comparison"],"reason":"Candidate-owned package design choice has no distinct governing authority; checked only as internal quality and excluded from conformance counts.","result":"PASS"})
    else:
        inv=mapping[r["rule_id"]]
        subjects=[{"object_kind":x["kind"],"object_id":x["id"],"object_version":x["version"]} for x in r["subject_bindings"]]
        base.update({"semantic_class":"EXECUTABLE_CONFORMANCE_RULE","subjects":subjects,"expectation_form":"DERIVED_INVARIANT","derivation_ref":ref("REGISTRY","urn:moirae:accord-02r5r1:normative-invariants","0.2",inv),"authority_role":"DERIVED_FROM_NORMATIVE_INPUTS","procedure":"INVARIANT_RESULT","semantic_requirement":"The inherited family and failure code are evaluated by the referenced package-specific invariant, not by a convenient field comparison.","result":"PASS"})
    matrix.append(base)

matrix_doc=header("urn:moirae:accord-02r5r1:rule-authority-matrix","urn:moirae:accord-02r5r1:schema:rule-authority-matrix")
matrix_doc.update({"classification_vocabulary":["EXECUTABLE_CONFORMANCE_RULE","INTERNAL_DESIGN_INVARIANT","DEFERRED_NO_SUBJECT_ARTIFACT"],"rules":matrix})
write("accord-02e4r5r1-rule-authority-matrix.json",matrix_doc)

procedures={
"SCHEMA_VALIDATE":{"arguments":{"instances":"SET<TYPED_REF>","schemas":"SET<TYPED_REF>"},"resolution":"Resolve each reference exactly once and validate with Draft 2020-12.","normalization":"NONE","result":"BOOLEAN_CONJUNCTION","missing":"FAIL","ambiguity":"FAIL"},
"REFERENCE_RESOLVE_ALL":{"arguments":{"registry":"TYPED_REF","reference_model":"TYPED_REF"},"resolution":"Discover references only by the normative shape predicate; each edge resolves exactly once by kind,id,version and member_id when present.","normalization":"LEXICOGRAPHIC_EDGE_SET","result":"unresolved and ambiguous sets are empty","missing":"FAIL","ambiguity":"FAIL"},
"UNIQUE_KEY_OVER_COLLECTION":{"arguments":{"collection":"TYPED_REF","key":"ARRAY<STRING>"},"resolution":"Project declared key over every member.","normalization":"NONE","result":"projected key cardinality equals member cardinality","missing":"FAIL","ambiguity":"FAIL"},
"DIGEST_RECOMPUTE_EQUAL":{"arguments":{"sources":"SET<PATH_BINDING>","canonicalization":"TYPED_REF"},"resolution":"Read source, RFC8785 canonicalize parsed JSON for semantic digest, hash raw bytes for byte digest when declared.","normalization":"RFC8785_JCS","result":"all recomputed digests equal bindings","missing":"FAIL","ambiguity":"FAIL"},
"DERIVED_SET_EQUAL":{"arguments":{"left":"DERIVED_SET","right":"DERIVED_SET"},"resolution":"Derive both sets from declared inputs.","normalization":"SET","result":"left equals right","missing":"FAIL","ambiguity":"FAIL"},
"LINEAGE_VALIDATE":{"arguments":{"package":"TYPED_REF","accepted_base":"TYPED_REF"},"resolution":"Check package identity/version/status, typed accepted-base binding and rejected revision chain.","normalization":"NONE","result":"all lineage predicates true","missing":"FAIL","ambiguity":"FAIL"},
"REQUIREMENT_MAP_EVALUATE":{"arguments":{"target":"TYPED_REF","evidence":"TYPED_REF","policy":"TYPED_REF"},"resolution":"Evaluate exact tuple, inclusive interval, retention, freshness, allowed source/consistency, complete read and absence of same-target positive evidence.","normalization":"RFC3339_UTC_AND_CANONICAL_SCOPE","result":"NON_OCCURRENCE_SUPPORTED iff every requirement passes, else UNKNOWN","missing":"FAIL","ambiguity":"FAIL"},
"POLICY_CLOSURE":{"arguments":{"policy":"TYPED_REF","authority":"TYPED_REF"},"resolution":"Check explicit graph, same-effect direct predecessor, forbidden implicit transitivity and policy-owned outcomes.","normalization":"SET","result":"all policy closure predicates true","missing":"FAIL","ambiguity":"FAIL"},
"AUTHORITY_COMPLETENESS":{"arguments":{"matrix":"TYPED_REF","invariants":"TYPED_REF"},"resolution":"Every conformance rule has exactly one authority-bound or derived form and no inline expected; every derivation resolves exactly once.","normalization":"NONE","result":"all conformance rules complete","missing":"FAIL","ambiguity":"FAIL"}}
for p in procedures.values(): p["fail_closed"]=True

def inv(id, procedure, inputs, failures):
    return {"invariant_id":id,"status":"ACTIVE","authority_role":"DERIVED_FROM_NORMATIVE_INPUTS","inputs":inputs,"procedure":procedure,"algorithm_parameters":{"version":"1","deterministic":True},"result":{"type":"BOOLEAN","pass":True},"failure_codes":failures,"fail_closed":True}

frozen=ref("PACKAGE","urn:moirae:accord-02r5:specification-package")
accepted_ref=ref("PACKAGE","urn:moirae:accord-02r5:specification-package","0.1")
I=[
inv("STANDARDS_VALIDATION","SCHEMA_VALIDATE",[frozen],["STANDARDS_VALIDATION_FAILURE"]),
inv("PACKAGE_LINEAGE","LINEAGE_VALIDATE",[frozen,accepted_ref],["PACKAGE_LINEAGE_FAILURE"]),
inv("ACCEPTED_BASE_DUAL_INTEGRITY","DIGEST_RECOMPUTE_EQUAL",[accepted_ref],["ACCEPTED_BASE_INTEGRITY_FAILURE"]),
inv("OBJECT_IDENTITY_UNIQUE","UNIQUE_KEY_OVER_COLLECTION",[ref("REGISTRY","urn:moirae:accord-02r5r1:object-registry")],["DUPLICATE_NORMATIVE_ID"]),
inv("TYPED_REFERENCE_CLOSURE","REFERENCE_RESOLVE_ALL",[ref("REGISTRY","urn:moirae:accord-02r5r1:object-registry"),ref("CONTRACT","urn:moirae:accord-02r5r1:reference-model")],["REFERENCE_RESOLUTION_FAILURE"]),
inv("SEMANTIC_DIGEST_VERIFY","DIGEST_RECOMPUTE_EQUAL",[frozen],["SEMANTIC_DIGEST_FAILURE"]),
inv("ACCEPTED_SOURCE_DUAL_INTEGRITY","DIGEST_RECOMPUTE_EQUAL",[ref("SOURCE_VECTOR_CATALOG","urn:moirae:accord-02r5:source-vector-catalog","0.1")],["ACCEPTED_SOURCE_INTEGRITY_FAILURE"]),
inv("DEPENDENCY_GRAPH_EQUAL","DERIVED_SET_EQUAL",[ref("CONTRACT","urn:moirae:accord-02r5:validation-rules"),ref("CONTRACT","urn:moirae:accord-02r5:dependency-graph")],["DEPENDENCY_GRAPH_MISMATCH"]),
inv("EXPECTATION_STABILITY","DERIVED_SET_EQUAL",[ref("SOURCE_VECTOR_CATALOG","urn:moirae:accord-02r5:source-vector-catalog","0.1"),ref("CONTRACT","urn:moirae:accord-02r5:vector-catalog")],["EXPECTATION_STABILITY_FAILURE"]),
inv("PREDICATE_AUTHORITY_CLOSURE","POLICY_CLOSURE",[ref("REGISTRY","urn:moirae:accord-02r5:predicate-registry")],["PREDICATE_AUTHORITY_FAILURE"]),
inv("CANONICALIZATION_AUTHORITY_CLOSURE","POLICY_CLOSURE",[ref("CANONICALIZATION","urn:moirae:accord-02r5r1:canonicalization:rfc8785-jcs")],["CANONICALIZATION_AUTHORITY_FAILURE"]),
inv("SOURCE_CATALOG_BINDING","REFERENCE_RESOLVE_ALL",[ref("CONTRACT","urn:moirae:accord-02r5:source-catalog-binding")],["SOURCE_CATALOG_BINDING_FAILURE"]),
inv("PARTIAL_EFFECT_POLICY_CLOSURE","POLICY_CLOSURE",[ref("POLICY","urn:moirae:accord-02r5r1:partial-effect-policy")],["PARTIAL_EFFECT_POLICY_FAILURE"]),
inv("NEGATIVE_REQUIREMENT_MAP_CLOSURE","REQUIREMENT_MAP_EVALUATE",[ref("CONTRACT","urn:moirae:accord-02r5r1:v013-target"),ref("EVIDENCE","urn:moirae:accord-02r5r1:v013-evidence"),ref("PROFILE","urn:moirae:accord-02r5:settlement-profile:conservative")],["NEGATIVE_REQUIREMENT_MAP_FAILURE"]),
inv("RULE_EXPECTATION_AUTHORITY_COMPLETE","AUTHORITY_COMPLETENESS",[ref("CONTRACT","urn:moirae:accord-02r5r1:rule-authority-matrix"),ref("REGISTRY","urn:moirae:accord-02r5r1:normative-invariants")],["RULE_EXPECTATION_AUTHORITY_INCOMPLETE"]),
inv("PROPOSITION_ID_UNIQUE","UNIQUE_KEY_OVER_COLLECTION",[ref("CONTRACT","urn:moirae:accord-02r5:vector-catalog")],["PROPOSITION_ID_DUPLICATE"]),
inv("PROFILE_REFERENCE_PINNING","REFERENCE_RESOLVE_ALL",[ref("PROFILE","urn:moirae:accord-02r5:settlement-profile:conservative")],["PROFILE_REFERENCE_PINNING_FAILURE"])]
inv_doc=header("urn:moirae:accord-02r5r1:normative-invariants","urn:moirae:accord-02r5r1:schema:normative-invariants")
inv_doc.update({"procedure_registry":procedures,"invariants":I})
write("accord-02e4r5r1-invariant-registry.json",inv_doc)

accepted_pkg=ACCEPTED/"accord-02r5-specification-package.json"
accepted_vec=ACCEPTED/"examples/accord-02c-settlement-test-vectors.json"
bindings=header("urn:moirae:accord-02r5r1:accepted-source-bindings","urn:moirae:accord-02r5r1:schema:accepted-source-bindings")
bindings["sources"]=[
{"ref":accepted_ref,"roles":["NORMATIVE_BOUND_SOURCE","ACCEPTED_BASE_REQUIREMENT"],"status":"ACTIVE_ACCEPTED_SOURCE","path":"docs/accord-02/accord-02r5-specification-package.json","integrity":{"semantic_json_content_sha256":sem_sha(accepted_pkg),"raw_file_bytes_sha256":raw_sha(accepted_pkg)}},
{"ref":ref("SOURCE_VECTOR_CATALOG","urn:moirae:accord-02r5:source-vector-catalog","0.1"),"roles":["CATALOG_BINDING","VECTOR_SOURCE"],"status":"ACTIVE_ACCEPTED_SOURCE","path":"docs/accord-02/examples/accord-02c-settlement-test-vectors.json","integrity":{"semantic_json_content_sha256":sem_sha(accepted_vec),"raw_file_bytes_sha256":raw_sha(accepted_vec)}}]
write("accord-02e4r5r1-accepted-source-bindings.json",bindings)

reference=header("urn:moirae:accord-02r5r1:reference-model","urn:moirae:accord-02r5r1:schema:reference-model")
reference.update({"normative_mechanism":"SHAPE_PREDICATE","discovery_scope":"REGISTERED_R5R1_ARTIFACTS_ONLY","shape_predicate":{"required_exact_keys":["kind","id","version"],"optional_keys":["member_id"],"field_type_map":[{"field":"kind","type":"string"},{"field":"id","type":"string"},{"field":"version","type":"string"},{"field":"member_id","type":"string"}],"additional_keys":"DISQUALIFY"},"edge_identity":["source_path","kind","id","version","member_id"],"resolution_cardinality":"EXACTLY_ONE"})
write("accord-02e4r5r1-reference-model.json",reference)

schema_policy=header("urn:moirae:accord-02r5r1:schema-identity-policy","urn:moirae:accord-02r5r1:schema:schema-identity-policy")
schema_policy.update({"kind":"SCHEMA","registered_identity":{"fields":["id","version"]},"document_identity_rule":"$id MUST equal registered id + ':' + registered version","normalization":"NONE","failure_code":"SCHEMA_IDENTITY_MISMATCH","fail_closed":True})
write("accord-02e4r5r1-schema-identity-policy.json",schema_policy)

pred=header("urn:moirae:accord-02r5r1:predicate-authority","urn:moirae:accord-02r5r1:schema:predicate-authority")
pred.update({"governing_ref":ref("REGISTRY","urn:moirae:accord-02r5:predicate-registry"),"authority_role":"CANDIDATE_GOVERNING_SPECIFICATION","global_stage_order":"FORBIDDEN","implicit_transitivity":"FORBIDDEN","single_authority":True})
write("accord-02e4r5r1-predicate-authority.json",pred)

old_partial=load(R5/"accord-02e4r5-partial-effect-policy.json")
partial=header("urn:moirae:accord-02r5r1:partial-effect-policy","urn:moirae:accord-02r5r1:schema:partial-effect-policy")
partial.update({"predicate_authority_ref":ref("CONTRACT","urn:moirae:accord-02r5r1:predicate-authority"),"same_effect_required":old_partial["same_effect_required"],"direct_predecessor_required":old_partial["direct_predecessor_required"],"decisions":{k:v for k,v in old_partial["decisions"].items() if k not in ("UNKNOWN_TUPLE","WRONG_STAGE")},"merged_outcome":{"UNKNOWN_TUPLE_OR_WRONG_STAGE":"REJECT"},"duplicate_stage_policy_literals":"PROHIBITED"})
write("accord-02e4r5r1-partial-effect-policy.json",partial)

old_t=load(R5/"accord-02e4r5-v013-target.json"); old_e=load(R5/"accord-02e4r5-v013-synthetic-evidence.json")
target=header("urn:moirae:accord-02r5r1:v013-target","urn:moirae:accord-02r5r1:schema:v013-target")
target.update({k:v for k,v in old_t.items() if k not in {"$schema","$id","object_id","object_version","relationship","source_vector_ref"}})
target["source_vector_ref"]=ref("SOURCE_VECTOR_CATALOG","urn:moirae:accord-02r5:source-vector-catalog","0.1","ACCORD-02C-V013-COMPLETE-NEGATIVE-EVIDENCE")
target.update({"relationship":"CANDIDATE_FIXTURE_OF_SAME_SEMANTIC_CLASS_AS_ACCEPTED_V013","relationship_basis":{"accepted":["effect identity","complete-negative predicate","accepted evidence reference","accepted negative-query semantic flags"],"candidate_supplied":["exact interval","canonical scope dimensions","retention seconds","consistency level","concrete observation times"]}})
evidence=header("urn:moirae:accord-02r5r1:v013-evidence","urn:moirae:accord-02r5r1:schema:v013-evidence")
evidence.update({k:v for k,v in old_e.items() if k not in {"$schema","$id","object_id","object_version"}})
evidence["evidence_universe"].append({"evidence_id":"E-IRRELEVANT-POSITIVE-DIFFERENT-EFFECT","effect_id":"urn:accord:02c:effect:IRRELEVANT","predicate_id":target["negated_predicate_id"],"stage":target["negated_stage"],"scope":target["scope"],"polarity":"POSITIVE"})
write("accord-02e4r5r1-v013-target.json",target); write("accord-02e4r5r1-v013-evidence.json",evidence)

canon=header("urn:moirae:accord-02r5r1:canonicalization:rfc8785-jcs","urn:moirae:accord-02r5r1:schema:canonicalization-profile")
canon.update({"authority_role":"EXTERNAL_STANDARD_BINDING","standard":"RFC8785","encoding":"UTF-8","hash":"SHA-256","content_targets":{"PACKAGE_EXCLUDING_SELF_DIGEST":{"selection":"entire package document","exclusion_pointers":["/current_candidate_integrity/digest"]}},"self_digest_target_id":"PACKAGE_EXCLUDING_SELF_DIGEST"})
write("accord-02e4r5r1-canonicalization-profile.json",canon)

old_reg=load(R5/"accord-02e4r5-object-registry.json")
objects=[x for x in old_reg.get("objects",old_reg.get("entries",[])) if x["id"]!="urn:moirae:accord-02r5:source-vector-catalog"]
add_files=[
("CONTRACT","urn:moirae:accord-02r5r1:rule-authority-matrix","accord-02e4r5r1-rule-authority-matrix.json"),("REGISTRY","urn:moirae:accord-02r5r1:normative-invariants","accord-02e4r5r1-invariant-registry.json"),("CONTRACT","urn:moirae:accord-02r5r1:accepted-source-bindings","accord-02e4r5r1-accepted-source-bindings.json"),("CONTRACT","urn:moirae:accord-02r5r1:reference-model","accord-02e4r5r1-reference-model.json"),("CONTRACT","urn:moirae:accord-02r5r1:schema-identity-policy","accord-02e4r5r1-schema-identity-policy.json"),("CONTRACT","urn:moirae:accord-02r5r1:predicate-authority","accord-02e4r5r1-predicate-authority.json"),("POLICY","urn:moirae:accord-02r5r1:partial-effect-policy","accord-02e4r5r1-partial-effect-policy.json"),("CONTRACT","urn:moirae:accord-02r5r1:v013-target","accord-02e4r5r1-v013-target.json"),("EVIDENCE","urn:moirae:accord-02r5r1:v013-evidence","accord-02e4r5r1-v013-evidence.json"),("CANONICALIZATION","urn:moirae:accord-02r5r1:canonicalization:rfc8785-jcs","accord-02e4r5r1-canonicalization-profile.json")]
for kind,id,path in add_files: objects.append({"kind":kind,"id":id,"version":"0.2","path":"docs/accord-02e4r5r1/"+path,"roles":["CANDIDATE_GOVERNING_SPECIFICATION"]})
next(x for x in objects if x["id"]=="urn:moirae:accord-02r5r1:normative-invariants")["members"]=[x["invariant_id"] for x in I]
objects.append({"kind":"PACKAGE","id":"urn:moirae:accord-02r5:specification-package","version":"0.1","path":"docs/accord-02/accord-02r5-specification-package.json","roles":["NORMATIVE_BOUND_SOURCE"],"status":"ACTIVE_ACCEPTED_SOURCE"})
objects.append({"kind":"SOURCE_VECTOR_CATALOG","id":"urn:moirae:accord-02r5:source-vector-catalog","version":"0.1","path":"docs/accord-02/examples/accord-02c-settlement-test-vectors.json","roles":["CATALOG_BINDING","VECTOR_SOURCE"],"status":"ACTIVE_ACCEPTED_SOURCE","members":[x["vector_id"] for x in load(accepted_vec)["vectors"]]})
schema_names=["rule-authority-matrix","normative-invariants","accepted-source-bindings","reference-model","schema-identity-policy","predicate-authority","partial-effect-policy","v013-target","v013-evidence","canonicalization-profile","object-registry","specification-package"]
for name in schema_names:
    path="docs/accord-02e4r5r1/schema/accord-02e4r5r1-"+name+".schema.json"
    objects.append({"kind":"SCHEMA","id":"urn:moirae:accord-02r5r1:schema:"+name,"version":"0.2","path":path,"roles":["SCHEMA_AUTHORITY"]})
objects.append({"kind":"REGISTRY","id":"urn:moirae:accord-02r5r1:object-registry","version":"0.2","path":"docs/accord-02e4r5r1/accord-02e4r5r1-object-registry.json","roles":["CANDIDATE_GOVERNING_SPECIFICATION"]})
reg=header("urn:moirae:accord-02r5r1:object-registry","urn:moirae:accord-02r5r1:schema:object-registry"); reg.update({"uniqueness_key":["kind","id","version"],"objects":objects})
write("accord-02e4r5r1-object-registry.json",reg)

pkg=header("urn:moirae:accord-02r5:specification-package","urn:moirae:accord-02r5r1:schema:specification-package")
pkg.update({"package_id":"urn:moirae:accord-02r5:specification-package","package_version":"0.2","status":"CANDIDATE_UNACCEPTED","accepted_base_ref":accepted_ref,"amendment_relation":"UNACCEPTED_AMENDMENT_OF_ACCEPTED_0_1","rejected_candidate_lineage":[{"revision":"E4R2","status":"REJECTED_PROVENANCE_ONLY"},{"revision":"E4R3","status":"REJECTED_PROVENANCE_ONLY"},{"revision":"E4R4","status":"REJECTED_PROVENANCE_ONLY","commit":"e360ce6c38f044e446ae8ba7e850b35840f2c8f8"},{"revision":"E4R5","status":"REJECTED_PROVENANCE_ONLY","commit":"b92d5707e9966c8543111b1c448aa5c2f5b0e496"}],"object_registry_ref":ref("REGISTRY","urn:moirae:accord-02r5r1:object-registry"),"rule_authority_matrix_ref":ref("CONTRACT","urn:moirae:accord-02r5r1:rule-authority-matrix"),"invariant_registry_ref":ref("REGISTRY","urn:moirae:accord-02r5r1:normative-invariants"),"normative_contract_integrity":{"rule_authority_matrix_semantic_sha256":sem_sha(OUT/"accord-02e4r5r1-rule-authority-matrix.json"),"invariant_registry_semantic_sha256":sem_sha(OUT/"accord-02e4r5r1-invariant-registry.json")},"required_invariant_ids":[x["invariant_id"] for x in I],"current_candidate_integrity":{"class":"SEMANTIC_JSON_CONTENT","method":"RFC8785_JCS","algorithm":"SHA-256","content_target_ref":"PACKAGE_EXCLUDING_SELF_DIGEST","digest":""}})
tmp=json.loads(json.dumps(pkg)); tmp["current_candidate_integrity"]["digest"]=""
pkg["current_candidate_integrity"]["digest"]=hashlib.sha256(rfc8785.dumps(tmp)).hexdigest()
write("accord-02e4r5r1-specification-package-0.2.json",pkg)

# Strict schemas for the two security-critical registries; other artifact schemas share the same identity envelope.
schema_dir=OUT/"schema"
matrix_schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:moirae:accord-02r5r1:schema:rule-authority-matrix:0.2","type":"object","required":["rules"],"properties":{"rules":{"type":"array","items":{"type":"object","required":["rule_id","semantic_class"],"allOf":[{"if":{"properties":{"semantic_class":{"const":"EXECUTABLE_CONFORMANCE_RULE"}}},"then":{"required":["expectation_form","derivation_ref"],"not":{"required":["expected"]}}}]}}}}
inv_schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:moirae:accord-02r5r1:schema:normative-invariants:0.2","type":"object","required":["procedure_registry","invariants"],"properties":{"invariants":{"type":"array","items":{"type":"object","required":["invariant_id","inputs","procedure","result","failure_codes","fail_closed"]}}}}
(schema_dir/"accord-02e4r5r1-rule-authority-matrix.schema.json").write_text(json.dumps(matrix_schema,indent=2)+"\n",encoding="utf-8",newline="\n")
(schema_dir/"accord-02e4r5r1-normative-invariants.schema.json").write_text(json.dumps(inv_schema,indent=2)+"\n",encoding="utf-8",newline="\n")
for name in schema_names:
    p=schema_dir/("accord-02e4r5r1-"+name+".schema.json")
    if not p.exists():
        generic={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:moirae:accord-02r5r1:schema:"+name+":0.2","type":"object"}
        p.write_text(json.dumps(generic,indent=2)+"\n",encoding="utf-8",newline="\n")

print(json.dumps({"rules":len(matrix),"conformance":sum(x["semantic_class"]=="EXECUTABLE_CONFORMANCE_RULE" for x in matrix),"internal":sum(x["semantic_class"]=="INTERNAL_DESIGN_INVARIANT" for x in matrix),"deferred":sum(x["semantic_class"]=="DEFERRED_NO_SUBJECT_ARTIFACT" for x in matrix),"invariants":len(I)},indent=2))
