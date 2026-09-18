from __future__ import annotations
import copy, hashlib, json, subprocess
from pathlib import Path
import rfc8785

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent; SCHEMA=OUT/'schema'; SCHEMA.mkdir(parents=True,exist_ok=True); (OUT/'audit').mkdir(exist_ok=True)
R1=ROOT/'docs/accord-02e4r5r1'; R5=ROOT/'docs/accord-02e4r5'; ACCEPTED=ROOT/'docs/accord-02'
VERSION='0.2'; DIALECT='https://json-schema.org/draft/2020-12/schema'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,x): Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def sem(x): return hashlib.sha256(rfc8785.dumps(x if not isinstance(x,Path) else load(x))).hexdigest()
def raw_blob(path): return subprocess.check_output(['git','show','f75352c0d673d77873fb96a9975a6c37abceb519:'+path])
def tref(kind,id,version=VERSION,member_id=None):
    x={'kind':kind,'id':id,'version':version}
    if member_id is not None:x['member_id']=member_id
    return x
def hdr(id,schema): return {'$schema':DIALECT,'schema_ref':tref('SCHEMA',schema),'$id':id+':'+VERSION,'object_id':id,'object_version':VERSION}

old_matrix=load(R1/'accord-02e4r5r1-rule-authority-matrix.json')['rules']; old_inv=load(R1/'accord-02e4r5r1-invariant-registry.json')['invariants']; old_assert={x['assertion_id'].rsplit(':',1)[1]:x for x in load(R5/'accord-02e4r5-assertion-registry.json')['assertions']}
old_pred=load(R5/'accord-02e4r5-predicate-registry.json'); old_graph=load(R5/'accord-02e4r5-dependency-graph.json'); old_rules=load(R5/'accord-02e4r5-validation-rules.json')['rules']; old_vec=load(R5/'accord-02e4r5-vector-catalog.json'); old_profile=load(R5/'accord-02e4r5-settlement-profile-conservative.json'); old_source=load(R5/'accord-02e4r5-source-catalog-binding.json'); old_neg=load(R5/'accord-02e4r5-negative-requirement-map.json')

ids={
'rules':'urn:moirae:accord-02r5r2:rule-registry','invariants':'urn:moirae:accord-02r5r2:invariant-registry','procedures':'urn:moirae:accord-02r5r2:procedure-registry','registry':'urn:moirae:accord-02r5r2:object-registry','references':'urn:moirae:accord-02r5r2:reference-model','authority':'urn:moirae:accord-02r5r2:authority-requirements','inputs':'urn:moirae:accord-02r5r2:normative-inputs','bindings':'urn:moirae:accord-02r5r2:accepted-source-bindings','canon':'urn:moirae:accord-02r5r2:canonicalization-profile','partial':'urn:moirae:accord-02r5r2:partial-effect-policy','target':'urn:moirae:accord-02r5r2:v013-target','evidence':'urn:moirae:accord-02r5r2:v013-evidence','package':'urn:moirae:accord-02r5:specification-package'}
schema_ids={k:'urn:moirae:accord-02r5r2:schema:'+k for k in ['rule-registry','invariant-registry','procedure-registry','object-registry','reference-model','authority-requirements','normative-inputs','accepted-source-bindings','canonicalization-profile','partial-effect-policy','v013-target','v013-evidence','specification-package']}

authority=hdr(ids['authority'],schema_ids['authority-requirements']); authority.update({
'package_requirements':{'family':ids['package'],'version':VERSION,'status':'CANDIDATE_UNACCEPTED','accepted_base_version':'0.1','required_rejected_revision':{'revision':'E4R5R1','commit':'f75352c0d673d77873fb96a9975a6c37abceb519'}},
'stage_policy_requirements':{'global_stage_order':old_pred['global_stage_order'],'implicit_transitivity':old_pred['implicit_transitivity']},
'stage_policy_authorization':{'global_stage_order':[old_pred['global_stage_order']],'implicit_transitivity':[old_pred['implicit_transitivity']]},
'canonicalization_requirements':{'standard':'RFC8785','serialization':'RFC8785_JCS','encoding':'UTF-8','algorithm':'SHA-256','target_id':'PACKAGE_EXCLUDING_SELF_DIGEST','selection':'ENTIRE_PACKAGE_DOCUMENT','reduction':'REMOVE_POINTER','exclusion_pointers':['/current_candidate_integrity/digest']},
'partial_effect_requirements':{'same_effect_required':True,'direct_predecessor_required':True,'merged_decision_key':'UNKNOWN_TUPLE_OR_WRONG_STAGE','merged_decision_value':'REJECT'},
'classification_requirements':{'conformance':'invariant_binding exists and validates','internal':'internal_check exists and no invariant_binding','deferred':'missing_subject_roles and later_lifecycle_stage exist and no binding/check'}})
dump(OUT/'authority-requirements.json',authority)

inputs=hdr(ids['inputs'],schema_ids['normative-inputs']); inputs.update({
'predicate_policy':{'global_stage_order':old_pred['global_stage_order'],'implicit_transitivity':old_pred['implicit_transitivity']},
'rule_dependencies':[{'rule_id':r['rule_id'],'depends_on':r.get('depends_on',[])} for r in old_rules],
'dependency_edges':[{'from':x['from'],'to':x['to']} for x in old_graph['edges']],
'vector_expectations':[{'vector_id':x['vector_id'],'expected':x['expected']} for x in old_vec['vectors']],
'proposition_ids':[x.get('candidate_proposition_id',x['vector_id']) for x in old_vec['vectors']],
'profile':{'negative_policy':old_profile['negative_policy'],'object_version':old_profile['object_version']},
'source_catalog_binding':{k:v for k,v in old_source.items() if k not in ('$schema','$id','object_id','object_version')},
'negative_requirement_map':{k:v for k,v in old_neg.items() if k not in ('$schema','$id','object_id','object_version')},
'internal_design_values':{}})
for r in old_matrix:
    if r['semantic_class']=='INTERNAL_DESIGN_INVARIANT': inputs['internal_design_values'][r['rule_id']]=r['expected']
inputs['profile']['negative_policy'].pop('requirement_map_ref',None)
inputs['negative_requirement_map'].pop('governing_profile_ref',None)
if 'assigned_catalog_ref' in inputs['source_catalog_binding']:
    inputs['source_catalog_binding']['assigned_catalog_ref']=tref('SOURCE_VECTOR_CATALOG','urn:moirae:accord-02r5:source-vector-catalog','0.1')
dump(OUT/'normative-inputs.json',inputs)

partial=hdr(ids['partial'],schema_ids['partial-effect-policy']); partial.update({'stage_authority_ref':tref('AUTHORITY',ids['authority']),'same_effect_required':True,'direct_predecessor_required':True,'decisions':{'VALID_SUPPORTED_DIRECT_PREDECESSOR':'PARTIAL_EFFECT','TARGET_ALREADY_SUPPORTED':'NOT_PARTIAL_EFFECT','NO_PREDECESSOR':'UNKNOWN','WRONG_EFFECT':'REJECT','UNSUPPORTED_TUPLE':'REJECT','UNKNOWN_TUPLE_OR_WRONG_STAGE':'REJECT','SELF_EDGE':'REJECT','CYCLE':'REJECT','DANGLING_TARGET':'REJECT','INCOMPATIBLE_EVIDENCE':'UNKNOWN','INADMISSIBLE_EVIDENCE':'UNKNOWN'}}); dump(OUT/'partial-effect-policy.json',partial)
old_t=load(R1/'accord-02e4r5r1-v013-target.json'); target=hdr(ids['target'],schema_ids['v013-target']); target.update({k:v for k,v in old_t.items() if k not in ('$schema','schema_ref','$id','object_id','object_version')}); dump(OUT/'v013-target.json',target)
target['settlement_profile_ref']=tref('NORMATIVE_INPUTS',ids['inputs']); dump(OUT/'v013-target.json',target)
old_e=load(R1/'accord-02e4r5r1-v013-evidence.json'); evidence=hdr(ids['evidence'],schema_ids['v013-evidence']); evidence.update({k:v for k,v in old_e.items() if k not in ('$schema','schema_ref','$id','object_id','object_version','requirement_map_ref')}); evidence['evidence_universe'].append({'evidence_id':'E-IRRELEVANT-INADMISSIBLE-SAME-TARGET','effect_id':target['effect_id'],'predicate_id':target['negated_predicate_id'],'stage':target['negated_stage'],'scope':target['scope'],'polarity':'POSITIVE','admissible':False}); dump(OUT/'v013-evidence.json',evidence)
canon=hdr(ids['canon'],schema_ids['canonicalization-profile']); canon.update(authority['canonicalization_requirements']); dump(OUT/'canonicalization-profile.json',canon)

accepted_paths=['docs/accord-02/accord-02r5-specification-package.json','docs/accord-02/examples/accord-02c-settlement-test-vectors.json']
bindings=hdr(ids['bindings'],schema_ids['accepted-source-bindings']); bindings['sources']=[]
for path,kind,id in [(accepted_paths[0],'PACKAGE',ids['package']),(accepted_paths[1],'SOURCE_VECTOR_CATALOG','urn:moirae:accord-02r5:source-vector-catalog')]:
    blob=raw_blob(path); obj=json.loads(blob)
    bindings['sources'].append({'ref':tref(kind,id,'0.1'),'path':path,'status':'ACTIVE_ACCEPTED_SOURCE','roles':['NORMATIVE_BOUND_SOURCE'] if kind=='PACKAGE' else ['CATALOG_BINDING','VECTOR_SOURCE'],'integrity':{'semantic_json_content_sha256':hashlib.sha256(rfc8785.dumps(obj)).hexdigest(),'raw_file_bytes_sha256':hashlib.sha256(blob).hexdigest(),'raw_byte_preservation':'GIT_ATTRIBUTES_MINUS_TEXT'}})
dump(OUT/'accepted-source-bindings.json',bindings)

reference=hdr(ids['references'],schema_ids['reference-model']); reference.update({'mechanism':'SHAPE_PREDICATE','discovery_scope':{'registry_status':'ACTIVE','classification':'NORMATIVE'},'shape_predicate':{'required_keys':['kind','id','version'],'optional_keys':['member_id'],'additional_keys':'DISQUALIFY','all_values_type':'STRING'},'edge_identity':['source_kind','source_id','source_version','source_pointer','target_kind','target_id','target_version','member_id_or_empty'],'deduplication':'SET_BY_EDGE_IDENTITY','resolution_cardinality':'EXACTLY_ONE'}); dump(OUT/'reference-model.json',reference)

arg_specs={
'SCHEMA_VALIDATION':[('registry','REGISTRY'),('reference_model','CONTRACT')],
'LINEAGE_VALIDATION':[('package','PACKAGE'),('authority','AUTHORITY')],
'DUAL_INTEGRITY':[('bindings','CONTRACT')],
'UNIQUE_KEY':[('registry','REGISTRY')],
'REFERENCE_RESOLUTION':[('registry','REGISTRY'),('reference_model','CONTRACT')],
'DIGEST_RECOMPUTE':[('registry','REGISTRY'),('package','PACKAGE'),('canonicalization','CANONICALIZATION')],
'SET_EQUALITY':[('inputs','NORMATIVE_INPUTS')],
'EXPECTATION_STABILITY':[('inputs','NORMATIVE_INPUTS'),('accepted_vectors','SOURCE_VECTOR_CATALOG')],
'PREDICATE_POLICY_AGREEMENT':[('inputs','NORMATIVE_INPUTS'),('authority','AUTHORITY')],
'CANONICALIZATION_PROFILE_WELLFORMED':[('profile','CANONICALIZATION'),('authority','AUTHORITY')],
'SOURCE_CATALOG_BINDING':[('inputs','NORMATIVE_INPUTS'),('bindings','CONTRACT')],
'PARTIAL_EFFECT_POLICY_CLOSURE':[('policy','POLICY'),('authority','AUTHORITY')],
'REQUIREMENT_MAP_EVAL':[('target','CONTRACT'),('evidence','EVIDENCE'),('inputs','NORMATIVE_INPUTS')],
'AUTHORITY_COMPLETENESS':[('rules','REGISTRY'),('invariants','REGISTRY'),('procedures','REGISTRY'),('registry','REGISTRY')],
'PROPOSITION_UNIQUENESS':[('inputs','NORMATIVE_INPUTS')],
'PROFILE_REFERENCE_PINNING':[('inputs','NORMATIVE_INPUTS')],
'ARITY_AGREEMENT':[('invariants','REGISTRY'),('procedures','REGISTRY')],
'SCHEMA_NON_VACUITY':[('registry','REGISTRY')],
'CURRENT_PACKAGE_IDENTITY':[('registry','REGISTRY'),('package','PACKAGE')],
'SELF_DIGEST':[('package','PACKAGE'),('canonicalization','CANONICALIZATION')]
}
derivations={
'SCHEMA_VALIDATION':{'operation':'VALIDATE_ACTIVE_UNIVERSE','meta_validate_schemas':True,'validate_declared_instances':True,'validate_embedded_propositions':True},
'LINEAGE_VALIDATION':{'operation':'SECTION_ENTAILMENT','comparisons':[{'left':'package:/package_id','right':'authority:/package_requirements/family'},{'left':'package:/package_version','right':'authority:/package_requirements/version'},{'left':'package:/status','right':'authority:/package_requirements/status'}],'required_lineage_entry':'authority:/package_requirements/required_rejected_revision'},
'DUAL_INTEGRITY':{'operation':'DIGEST_RECOMPUTE','source_selector':'bindings:/sources/*','semantic_serialization':'RFC8785_JCS','raw_serialization':'RAW_BYTES','algorithms':['SHA-256']},
'UNIQUE_KEY':{'operation':'UNIQUE_KEY','source':'registry:/objects/*','projection':['kind','id','version']},
'REFERENCE_RESOLUTION':{'operation':'REFERENCE_RESOLUTION','model':'reference_model:/shape_predicate','scope':'reference_model:/discovery_scope','edge_identity':'reference_model:/edge_identity','cardinality':'reference_model:/resolution_cardinality'},
'DIGEST_RECOMPUTE':{'operation':'DIGEST_RECOMPUTE','registry_integrity_selector':'registry:/objects/*/integrity','self_digest_contract':'canonicalization'},
'SET_EQUALITY':{'operation':'SET_EQUALITY','left':{'source':'inputs:/rule_dependencies/*','projection':['rule_id','depends_on/*']},'right':{'source':'inputs:/dependency_edges/*','projection':['from','to']},'comparison':'SET_EQUAL'},
'EXPECTATION_STABILITY':{'operation':'SET_EQUALITY','left':{'source':'inputs:/vector_expectations/*','key':'vector_id','value':'expected'},'right':{'source':'accepted_vectors:/vectors/*','key':'vector_id','value':'expected'},'comparison':'MAP_EQUAL'},
'PREDICATE_POLICY_AGREEMENT':{'operation':'POLICY_AGREEMENT','comparisons':[{'left':'inputs:/predicate_policy/global_stage_order','right':'authority:/stage_policy_requirements/global_stage_order','authorized_by':'authority:/stage_policy_authorization/global_stage_order'},{'left':'inputs:/predicate_policy/implicit_transitivity','right':'authority:/stage_policy_requirements/implicit_transitivity','authorized_by':'authority:/stage_policy_authorization/implicit_transitivity'}]},
'CANONICALIZATION_PROFILE_WELLFORMED':{'operation':'POLICY_AGREEMENT','comparison_root_left':'profile','comparison_root_right':'authority:/canonicalization_requirements'},
'SOURCE_CATALOG_BINDING':{'operation':'MEMBERSHIP_RESOLVE','catalog':'bindings:/sources','binding':'inputs:/source_catalog_binding'},
'PARTIAL_EFFECT_POLICY_CLOSURE':{'operation':'POLICY_AGREEMENT','comparisons':[{'left':'policy:/same_effect_required','right':'authority:/partial_effect_requirements/same_effect_required'},{'left':'policy:/direct_predecessor_required','right':'authority:/partial_effect_requirements/direct_predecessor_required'},{'left_dynamic':'policy:/decisions/{authority:/partial_effect_requirements/merged_decision_key}','right':'authority:/partial_effect_requirements/merged_decision_value'}]},
'REQUIREMENT_MAP_EVAL':{'operation':'REQUIREMENT_MAP_EVAL','checks':['EXACT_TARGET','INCLUSIVE_INTERVAL','RETENTION','FRESHNESS','ALLOWED_CONSISTENCY','ALLOWED_SOURCE_CLASS','COMPLETE_READ','NO_ADMISSIBLE_SAME_TARGET_POSITIVE'],'pass_result':'NON_OCCURRENCE_SUPPORTED','fail_result':'UNKNOWN'},
'AUTHORITY_COMPLETENESS':{'operation':'AUTHORITY_COMPLETENESS','requirements':['BINDING_ROLE_EXACT','REFERENCE_EXACTLY_ONE','FAILURE_COMPATIBLE','DECLARED_CLASS_EQUALS_DERIVED','NO_CONFORMANCE_SUBJECTS','EXACT_ACTIVE_INVARIANT_SET']},
'PROPOSITION_UNIQUENESS':{'operation':'UNIQUE_KEY','source':'inputs:/proposition_ids/*','projection':'SELF'},
'PROFILE_REFERENCE_PINNING':{'operation':'SECTION_ENTAILMENT','required_pointer':'inputs:/profile/object_version','governing_pointer':'authority:/package_requirements/version'},
'ARITY_AGREEMENT':{'operation':'ARITY_AGREEMENT','left':'invariants:/invariants/*/input_roles/*/role','right':'procedures:/procedures/{procedure_id}/arguments/*/name'},
'SCHEMA_NON_VACUITY':{'operation':'SCHEMA_NON_VACUITY','probe':{'zzz':1},'expected':'REJECT_ALL_ACTIVE_SCHEMAS'},
'CURRENT_PACKAGE_IDENTITY':{'operation':'CURRENT_PACKAGE_IDENTITY','identity_from':'authority:/package_requirements','required_resolution_count':1,'required_path':'package'},
'SELF_DIGEST':{'operation':'SELF_DIGEST','steps':['DEEP_COPY','READ_EXPECTED','REMOVE_POINTER','RFC8785_JCS','UTF8','SHA256','COMPARE'],'contract':'canonicalization'}
}
procedures=hdr(ids['procedures'],schema_ids['procedure-registry']); procedures['procedures']=[]
for pid,args in arg_specs.items(): procedures['procedures'].append({'procedure_id':pid,'arguments':[{'name':n,'kind':k,'required':True,'cardinality':'ONE'} for n,k in args],'derivation':derivations[pid],'result':{'type':'BOOLEAN','status':['PASS','FAIL'],'witness_required':True},'missing_behavior':'FAIL','ambiguity_behavior':'FAIL','fail_closed':True})
dump(OUT/'procedure-registry.json',procedures)

base_args={
'STANDARDS_VALIDATION':{'registry':tref('REGISTRY',ids['registry']),'reference_model':tref('CONTRACT',ids['references'])},
'PACKAGE_LINEAGE':{'package':tref('PACKAGE',ids['package']),'authority':tref('AUTHORITY',ids['authority'])},
'ACCEPTED_BASE_DUAL_INTEGRITY':{'bindings':tref('CONTRACT',ids['bindings'])},'OBJECT_IDENTITY_UNIQUE':{'registry':tref('REGISTRY',ids['registry'])},
'TYPED_REFERENCE_CLOSURE':{'registry':tref('REGISTRY',ids['registry']),'reference_model':tref('CONTRACT',ids['references'])},
'SEMANTIC_DIGEST_VERIFY':{'registry':tref('REGISTRY',ids['registry']),'package':tref('PACKAGE',ids['package']),'canonicalization':tref('CANONICALIZATION',ids['canon'])},
'ACCEPTED_SOURCE_DUAL_INTEGRITY':{'bindings':tref('CONTRACT',ids['bindings'])},'DEPENDENCY_GRAPH_EQUAL':{'inputs':tref('NORMATIVE_INPUTS',ids['inputs'])},
'EXPECTATION_STABILITY':{'inputs':tref('NORMATIVE_INPUTS',ids['inputs']),'accepted_vectors':tref('SOURCE_VECTOR_CATALOG','urn:moirae:accord-02r5:source-vector-catalog','0.1')},
'PREDICATE_AUTHORITY_CLOSURE':{'inputs':tref('NORMATIVE_INPUTS',ids['inputs']),'authority':tref('AUTHORITY',ids['authority'])},
'CANONICALIZATION_AUTHORITY_CLOSURE':{'profile':tref('CANONICALIZATION',ids['canon']),'authority':tref('AUTHORITY',ids['authority'])},
'SOURCE_CATALOG_BINDING':{'inputs':tref('NORMATIVE_INPUTS',ids['inputs']),'bindings':tref('CONTRACT',ids['bindings'])},
'PARTIAL_EFFECT_POLICY_CLOSURE':{'policy':tref('POLICY',ids['partial']),'authority':tref('AUTHORITY',ids['authority'])},
'NEGATIVE_REQUIREMENT_MAP_CLOSURE':{'target':tref('CONTRACT',ids['target']),'evidence':tref('EVIDENCE',ids['evidence']),'inputs':tref('NORMATIVE_INPUTS',ids['inputs'])},
'RULE_EXPECTATION_AUTHORITY_COMPLETE':{'rules':tref('REGISTRY',ids['rules']),'invariants':tref('REGISTRY',ids['invariants']),'procedures':tref('REGISTRY',ids['procedures']),'registry':tref('REGISTRY',ids['registry'])},
'PROPOSITION_ID_UNIQUE':{'inputs':tref('NORMATIVE_INPUTS',ids['inputs'])},'PROFILE_REFERENCE_PINNING':{'inputs':tref('NORMATIVE_INPUTS',ids['inputs'])},
'INVARIANT_PROCEDURE_ARITY_AGREEMENT':{'invariants':tref('REGISTRY',ids['invariants']),'procedures':tref('REGISTRY',ids['procedures'])},
'SCHEMA_NON_VACUITY':{'registry':tref('REGISTRY',ids['registry'])},'CURRENT_PACKAGE_IDENTITY':{'registry':tref('REGISTRY',ids['registry']),'package':tref('PACKAGE',ids['package'])},
'PACKAGE_SELF_DIGEST':{'package':tref('PACKAGE',ids['package']),'canonicalization':tref('CANONICALIZATION',ids['canon'])}}
proc_for={x['invariant_id']:x['procedure'] for x in old_inv}; proc_for.update({'INVARIANT_PROCEDURE_ARITY_AGREEMENT':'ARITY_AGREEMENT','SCHEMA_NON_VACUITY':'SCHEMA_NON_VACUITY','CURRENT_PACKAGE_IDENTITY':'CURRENT_PACKAGE_IDENTITY','PACKAGE_SELF_DIGEST':'SELF_DIGEST'})
proc_for.update({'STANDARDS_VALIDATION':'SCHEMA_VALIDATION','PACKAGE_LINEAGE':'LINEAGE_VALIDATION','ACCEPTED_BASE_DUAL_INTEGRITY':'DUAL_INTEGRITY','ACCEPTED_SOURCE_DUAL_INTEGRITY':'DUAL_INTEGRITY','OBJECT_IDENTITY_UNIQUE':'UNIQUE_KEY','TYPED_REFERENCE_CLOSURE':'REFERENCE_RESOLUTION','SEMANTIC_DIGEST_VERIFY':'DIGEST_RECOMPUTE','DEPENDENCY_GRAPH_EQUAL':'SET_EQUALITY','EXPECTATION_STABILITY':'EXPECTATION_STABILITY','PREDICATE_AUTHORITY_CLOSURE':'PREDICATE_POLICY_AGREEMENT','CANONICALIZATION_AUTHORITY_CLOSURE':'CANONICALIZATION_PROFILE_WELLFORMED','SOURCE_CATALOG_BINDING':'SOURCE_CATALOG_BINDING','PARTIAL_EFFECT_POLICY_CLOSURE':'PARTIAL_EFFECT_POLICY_CLOSURE','NEGATIVE_REQUIREMENT_MAP_CLOSURE':'REQUIREMENT_MAP_EVAL','RULE_EXPECTATION_AUTHORITY_COMPLETE':'AUTHORITY_COMPLETENESS','PROPOSITION_ID_UNIQUE':'PROPOSITION_UNIQUENESS','PROFILE_REFERENCE_PINNING':'PROFILE_REFERENCE_PINNING'})

rule_by_id={x['rule_id']:x for x in old_matrix}; mapping={x['rule_id']:x.get('derivation_ref',{}).get('member_id') for x in old_matrix if x['semantic_class']=='EXECUTABLE_CONFORMANCE_RULE'}
extra=['INVARIANT_PROCEDURE_ARITY_AGREEMENT','SCHEMA_NON_VACUITY','CURRENT_PACKAGE_IDENTITY','PACKAGE_SELF_DIGEST']; all_inv=list(base_args)
failures={i:sorted({rule_by_id[r]['inherited_failure_code'] for r,v in mapping.items() if v==i}) for i in all_inv}; failures.update({x:[x+'_FAILURE'] for x in extra})
invariants=hdr(ids['invariants'],schema_ids['invariant-registry']); invariants['invariants']=[]
for iid in all_inv:
    pid=proc_for[iid]; roles=[{'role':n,'kind':k,'required':True,'cardinality':'ONE'} for n,k in arg_specs[pid]]
    invariants['invariants'].append({'invariant_id':iid,'status':'ACTIVE','usage':'PACKAGE_ONLY_REQUIRED' if iid in extra or iid not in set(mapping.values()) else 'CONFORMANCE_BOUND','procedure_id':pid,'input_roles':roles,'subject_roles':[x['role'] for x in roles[:1]],'default_arguments':base_args[iid],'compatible_failure_codes':failures[iid],'fail_closed':True})
dump(OUT/'invariant-registry.json',invariants)

source_digest=sem(load(R1/'accord-02e4r5r1-rule-authority-matrix.json'))
rules=hdr(ids['rules'],schema_ids['rule-registry']); rules['provenance']={'source_revision':'E4R5R1','source_commit':'f75352c0d673d77873fb96a9975a6c37abceb519','source_semantic_digest':source_digest}; rules['rules']=[]
for old in old_matrix:
    row={'rule_id':old['rule_id'],'declared_class':old['semantic_class'],'inherited_family':old['inherited_family'],'inherited_failure_code':old['inherited_failure_code'],'provenance_source_revision':'E4R5R1','provenance_source_commit':'f75352c0d673d77873fb96a9975a6c37abceb519','provenance_source_semantic_digest':source_digest}
    if old['semantic_class']=='EXECUTABLE_CONFORMANCE_RULE': row['invariant_binding']={'invariant_id':mapping[old['rule_id']],'arguments':copy.deepcopy(base_args[mapping[old['rule_id']]])}
    elif old['semantic_class']=='INTERNAL_DESIGN_INVARIANT': row['internal_check']={'procedure':'JSON_POINTER_COMPARE','subject':tref('NORMATIVE_INPUTS',ids['inputs']),'pointer':'/internal_design_values/'+old['rule_id'],'comparison':'EXACT_EQUAL','expected':old['expected'],'conformance_excluded':True}
    else: row.update({'missing_subject_roles':old['missing_subject_roles'],'later_lifecycle_stage':old['later_lifecycle_stage'],'deferred_reason':old['reason']})
    rules['rules'].append(row)
dump(OUT/'rule-registry.json',rules)

# Substantive family schemas. They reject the universal vacuity probe and enforce the contract envelope plus family fields.
schema_requirements={
'rule-registry':['rules','provenance'],'invariant-registry':['invariants'],'procedure-registry':['procedures'],'object-registry':['objects','uniqueness_key'],'reference-model':['mechanism','shape_predicate','edge_identity','discovery_scope'],'authority-requirements':['package_requirements','stage_policy_requirements','stage_policy_authorization','canonicalization_requirements','partial_effect_requirements','classification_requirements'],'normative-inputs':['predicate_policy','rule_dependencies','dependency_edges','vector_expectations','profile','internal_design_values'],'accepted-source-bindings':['sources'],'canonicalization-profile':['standard','serialization','encoding','algorithm','target_id','selection','reduction','exclusion_pointers'],'partial-effect-policy':['stage_authority_ref','same_effect_required','direct_predecessor_required','decisions'],'v013-target':['relationship','relationship_basis','effect_id','negated_predicate_id','negated_stage','scope','required_interval'],'v013-evidence':['fixture_status','effect_id','predicate_id','stage','scope','observed_interval','retention_window_seconds','consistency_level','read_semantics','read_scope_complete','evidence_universe'],'specification-package':['package_id','package_version','status','accepted_base_ref','rejected_candidate_lineage','object_registry_ref','rule_registry_ref','invariant_registry_ref','procedure_registry_ref','required_invariant_ids','current_candidate_integrity']}
for name,required in schema_requirements.items():
    props={'$schema':{'const':DIALECT},'$id':{'type':'string','minLength':1},'schema_ref':{'$ref':'#/$defs/ref'},'object_id':{'type':'string','minLength':1},'object_version':{'type':'string','minLength':1}}
    array_fields=('rules','invariants','procedures','objects','sources','edge_identity','exclusion_pointers','rejected_candidate_lineage','required_invariant_ids','evidence_universe','rule_dependencies','dependency_edges','vector_expectations','uniqueness_key')
    object_fields=('provenance','shape_predicate','discovery_scope','package_requirements','stage_policy_requirements','stage_policy_authorization','canonicalization_requirements','partial_effect_requirements','classification_requirements','predicate_policy','profile','internal_design_values','stage_authority_ref','decisions','relationship_basis','scope','required_interval','observed_interval','accepted_base_ref','object_registry_ref','rule_registry_ref','invariant_registry_ref','procedure_registry_ref','current_candidate_integrity')
    boolean_fields=('same_effect_required','direct_predecessor_required','read_scope_complete')
    number_fields=('retention_window_seconds',)
    for field in required: props[field]={'type':'array' if field in array_fields else 'object' if field in object_fields else 'boolean' if field in boolean_fields else 'number' if field in number_fields else 'string'}
    schema={'$schema':DIALECT,'$id':schema_ids[name]+':'+VERSION,'type':'object','required':['$schema','$id','schema_ref','object_id','object_version']+required,'properties':props,'additionalProperties':True,'allOf':[{'not':{'required':['zzz']}}],'$defs':{'ref':{'type':'object','required':['kind','id','version'],'properties':{'kind':{'type':'string'},'id':{'type':'string'},'version':{'type':'string'},'member_id':{'type':'string'}},'additionalProperties':False}}}
    dump(SCHEMA/(name+'.schema.json'),schema)

# Registry is built after every non-package object exists; package pins this registry and self-verifies.
files=[('REGISTRY',ids['rules'],'rule-registry.json','rule-registry'),('REGISTRY',ids['invariants'],'invariant-registry.json','invariant-registry'),('REGISTRY',ids['procedures'],'procedure-registry.json','procedure-registry'),('CONTRACT',ids['references'],'reference-model.json','reference-model'),('AUTHORITY',ids['authority'],'authority-requirements.json','authority-requirements'),('NORMATIVE_INPUTS',ids['inputs'],'normative-inputs.json','normative-inputs'),('CONTRACT',ids['bindings'],'accepted-source-bindings.json','accepted-source-bindings'),('CANONICALIZATION',ids['canon'],'canonicalization-profile.json','canonicalization-profile'),('POLICY',ids['partial'],'partial-effect-policy.json','partial-effect-policy'),('CONTRACT',ids['target'],'v013-target.json','v013-target'),('EVIDENCE',ids['evidence'],'v013-evidence.json','v013-evidence')]
objects=[]
for kind,id,file,schema in files: objects.append({'kind':kind,'id':id,'version':VERSION,'path':'docs/accord-02e4r5r2/'+file,'status':'ACTIVE','roles':['NORMATIVE'],'classification':'NORMATIVE','schema_ref':tref('SCHEMA',schema_ids[schema]),'integrity':{'mode':'SEMANTIC_JSON_CONTENT','algorithm':'SHA-256','serialization':'RFC8785_JCS','digest':sem(OUT/file)}})
for name in schema_requirements: objects.append({'kind':'SCHEMA','id':schema_ids[name],'version':VERSION,'path':'docs/accord-02e4r5r2/schema/'+name+'.schema.json','status':'ACTIVE','roles':['SCHEMA_AUTHORITY'],'classification':'NORMATIVE','integrity':{'mode':'SEMANTIC_JSON_CONTENT','algorithm':'SHA-256','serialization':'RFC8785_JCS','digest':sem(SCHEMA/(name+'.schema.json'))}})
for s in bindings['sources']: objects.append({'kind':s['ref']['kind'],'id':s['ref']['id'],'version':s['ref']['version'],'path':s['path'],'status':'ACTIVE_ACCEPTED_SOURCE','roles':s['roles'],'classification':'PROVENANCE','integrity':{'mode':'DUAL_ACCEPTED_SOURCE','binding_ref':tref('CONTRACT',ids['bindings'])},'members':[x['vector_id'] for x in load(ACCEPTED/'examples/accord-02c-settlement-test-vectors.json')['vectors']] if s['ref']['kind']=='SOURCE_VECTOR_CATALOG' else []})
objects.append({'kind':'REGISTRY','id':ids['registry'],'version':VERSION,'path':'docs/accord-02e4r5r2/object-registry.json','status':'ACTIVE','roles':['NORMATIVE','IDENTITY_AUTHORITY'],'classification':'NORMATIVE','schema_ref':tref('SCHEMA',schema_ids['object-registry']),'integrity':{'mode':'PACKAGE_PINNED_BOOTSTRAP','justification':'Registry digest is pinned by the current package to avoid self-reference.'}})
objects.append({'kind':'PACKAGE','id':ids['package'],'version':VERSION,'path':'docs/accord-02e4r5r2/specification-package-0.2.json','status':'ACTIVE','roles':['CURRENT_CANDIDATE_PACKAGE','NORMATIVE'],'classification':'NORMATIVE','schema_ref':tref('SCHEMA',schema_ids['specification-package']),'integrity':{'mode':'SELF_DIGEST','content_target_ref':'PACKAGE_EXCLUDING_SELF_DIGEST'}})
registry=hdr(ids['registry'],schema_ids['object-registry']); registry.update({'uniqueness_key':['kind','id','version'],'role_model':'roles-array','objects':objects}); dump(OUT/'object-registry.json',registry)

package=hdr(ids['package'],schema_ids['specification-package']); package.update({'package_id':ids['package'],'package_version':VERSION,'status':'CANDIDATE_UNACCEPTED','accepted_base_ref':tref('PACKAGE',ids['package'],'0.1'),'rejected_candidate_lineage':[{'revision':'E4R2','status':'REJECTED_PROVENANCE_ONLY'},{'revision':'E4R3','status':'REJECTED_PROVENANCE_ONLY'},{'revision':'E4R4','status':'REJECTED_PROVENANCE_ONLY','commit':'e360ce6c38f044e446ae8ba7e850b35840f2c8f8'},{'revision':'E4R5','status':'REJECTED_PROVENANCE_ONLY','commit':'b92d5707e9966c8543111b1c448aa5c2f5b0e496'},{'revision':'E4R5R1','status':'REJECTED_PROVENANCE_ONLY','commit':'f75352c0d673d77873fb96a9975a6c37abceb519'}],'object_registry_ref':tref('REGISTRY',ids['registry']),'rule_registry_ref':tref('REGISTRY',ids['rules']),'invariant_registry_ref':tref('REGISTRY',ids['invariants']),'procedure_registry_ref':tref('REGISTRY',ids['procedures']),'required_invariant_ids':[x['invariant_id'] for x in invariants['invariants'] if x['status']=='ACTIVE'],'registry_semantic_sha256':sem(registry),'runtime':{'python':'~=3.14.0','requirements_path':'docs/accord-02e4r5r2/requirements.txt'},'current_candidate_integrity':{'class':'SEMANTIC_JSON_CONTENT','content_target_ref':'PACKAGE_EXCLUDING_SELF_DIGEST','algorithm':'SHA-256','digest':None}})
reduced=copy.deepcopy(package); del reduced['current_candidate_integrity']['digest']; package['current_candidate_integrity']['digest']=sem(reduced); dump(OUT/'specification-package-0.2.json',package)

print(json.dumps({'rules':len(rules['rules']),'conformance':sum(x['declared_class']=='EXECUTABLE_CONFORMANCE_RULE' for x in rules['rules']),'internal':sum(x['declared_class']=='INTERNAL_DESIGN_INVARIANT' for x in rules['rules']),'deferred':sum(x['declared_class']=='DEFERRED_NO_SUBJECT_ARTIFACT' for x in rules['rules']),'active_invariants':len(package['required_invariant_ids']),'registered_objects':len(objects)},indent=2))
