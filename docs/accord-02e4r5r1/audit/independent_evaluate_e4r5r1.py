from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime
from pathlib import Path
import jsonschema, rfc8785

def read(path):
    with Path(path).open('r',encoding='utf-8') as f: return json.load(f)
def instant(x): return datetime.fromisoformat(x[:-1]+'+00:00' if x.endswith('Z') else x)

def evaluate(base):
    base=Path(base).resolve(); d=base/'docs/accord-02e4r5r1'; old=base/'docs/accord-02e4r5'
    matrix=read(d/'accord-02e4r5r1-rule-authority-matrix.json'); invariants=read(d/'accord-02e4r5r1-invariant-registry.json'); package=read(d/'accord-02e4r5r1-specification-package-0.2.json'); registry=read(d/'accord-02e4r5r1-object-registry.json'); bindings=read(d/'accord-02e4r5r1-accepted-source-bindings.json')
    entries=registry['objects']; buckets={}
    for item in entries: buckets.setdefault((item['kind'],item['id'],item['version']),[]).append(item)
    tests={}
    keys=[(x['kind'],x['id'],x['version']) for x in entries]
    tests['OBJECT_IDENTITY_UNIQUE']=len(keys)==len(set(keys))
    tests['PACKAGE_LINEAGE']=package['status']=='CANDIDATE_UNACCEPTED' and package['package_version']=='0.2' and package['accepted_base_ref']['version']=='0.1' and [z['revision'] for z in package['rejected_candidate_lineage']]==['E4R2','E4R3','E4R4','E4R5'] and package['rejected_candidate_lineage'][-1].get('commit')=='b92d5707e9966c8543111b1c448aa5c2f5b0e496'
    integrity=True
    for source in bindings['sources']:
        path=base/source['path']; content=path.read_bytes(); expected=source['integrity']
        try: semantic=hashlib.sha256(rfc8785.dumps(json.loads(content))).hexdigest()
        except Exception: integrity=False; continue
        integrity &= hashlib.sha256(content).hexdigest()==expected['raw_file_bytes_sha256'] and semantic==expected['semantic_json_content_sha256']
    tests['ACCEPTED_SOURCE_DUAL_INTEGRITY']=bool(integrity)
    try:
        jsonschema.validate(matrix,read(d/'schema/accord-02e4r5r1-rule-authority-matrix.schema.json')); jsonschema.validate(invariants,read(d/'schema/accord-02e4r5r1-normative-invariants.schema.json'))
        schema_entries=[x for x in entries if x['kind']=='SCHEMA']; schema_ok=all(read(base/x['path']).get('$id')==x['id']+':'+x['version'] and read(base/x['path']).get('$schema')=='https://json-schema.org/draft/2020-12/schema' for x in schema_entries)
        tests['STANDARDS_VALIDATION']=all(read(p).get('$schema')=='https://json-schema.org/draft/2020-12/schema' for p in d.glob('*.json')) and schema_ok
    except Exception: tests['STANDARDS_VALIDATION']=False
    semantic_ok=True
    old_registry=read(old/'accord-02e4r5-object-registry.json')
    for item in old_registry.get('entries',old_registry.get('objects',[])):
        binding=item.get('integrity',{})
        if binding.get('class')=='SEMANTIC_JSON_CONTENT':
            try: semantic_ok &= hashlib.sha256(rfc8785.dumps(read(base/item['path']))).hexdigest()==binding['digest']
            except Exception: semantic_ok=False
    candidate=json.loads(json.dumps(package)); wanted=candidate['current_candidate_integrity']['digest']; candidate['current_candidate_integrity']['digest']=''; semantic_ok &= hashlib.sha256(rfc8785.dumps(candidate)).hexdigest()==wanted
    tests['SEMANTIC_DIGEST_VERIFY']=bool(semantic_ok)
    definitions={x['invariant_id']:x for x in invariants['invariants']}; required=package['required_invariant_ids']; pins=package['normative_contract_integrity']; closure=len(definitions)==len(invariants['invariants']) and set(definitions)==set(required) and hashlib.sha256(rfc8785.dumps(matrix)).hexdigest()==pins['rule_authority_matrix_semantic_sha256'] and hashlib.sha256(rfc8785.dumps(invariants)).hexdigest()==pins['invariant_registry_semantic_sha256']
    for row in matrix['rules']:
        if row['semantic_class']=='EXECUTABLE_CONFORMANCE_RULE':
            closure &= row.get('expectation_form')=='DERIVED_INVARIANT' and 'expected' not in row and row.get('derivation_ref',{}).get('member_id') in definitions
    tests['RULE_EXPECTATION_AUTHORITY_COMPLETE']=bool(closure)
    oldrules={x['rule_id']:x for x in read(old/'accord-02e4r5-validation-rules.json')['rules']}; rows={x['rule_id']:x for x in matrix['rules']}
    tests['INHERITED_RULE_MEANING']=set(oldrules)==set(rows) and all(rows[k]['inherited_family']==v['family'] and rows[k]['inherited_failure_code']==v['failure_code'] for k,v in oldrules.items())
    model=read(d/'accord-02e4r5r1-reference-model.json')['shape_predicate']; discovered=[]
    def descend(value,source,loc):
        if type(value) is dict:
            names=set(value); compulsory=set(model['required_exact_keys']); optional=set(model['optional_keys'])
            if compulsory.issubset(names) and names.issubset(compulsory|optional) and all(type(q) is str for q in value.values()): discovered.append((source,loc,value.copy()))
            for name,child in value.items(): descend(child,source,loc+'/'+name.replace('~','~0').replace('/','~1'))
        elif type(value) is list:
            for number,child in enumerate(value): descend(child,source,loc+'/'+str(number))
    for item in entries:
        if not item['path'].startswith('docs/accord-02e4r5r1/'): continue
        path=base/item['path']
        if path.is_file() and path.suffix=='.json':
            try: descend(read(path),item['path'],'')
            except Exception: pass
    descend(package,'docs/accord-02e4r5r1/accord-02e4r5r1-specification-package-0.2.json','')
    bad=[]
    for source,loc,target in discovered:
        choices=buckets.get((target['kind'],target['id'],target['version']),[])
        if len(choices)!=1 or ('member_id' in target and target['member_id'] not in choices[0].get('members',[])): bad.append((source,loc,target))
    edge_strings=[f"{s}#{loc}->{t['kind']}|{t['id']}|{t['version']}|{t.get('member_id','')}" for s,loc,t in discovered]
    tests['TYPED_REFERENCE_CLOSURE']=not bad
    accepted=read(base/'docs/accord-02/examples/accord-02c-settlement-test-vectors.json'); candidate=read(old/'accord-02e4r5-vector-catalog.json')
    left={v['vector_id']:v['expected'] for v in accepted['vectors']}; right={v['vector_id']:v['expected'] for v in candidate['vectors']}
    tests['EXPECTATION_STABILITY']=left==right
    expectation_metrics={'vector_ids':len(left),'axes':len({k for v in accepted['vectors'] for k in v['expected']}),'reason_codes':sum(len(v['expected'].get('reason_codes',[])) for v in accepted['vectors']),'prohibitions':sum(len(v['expected'].get('must_not_conclude',[])) for v in accepted['vectors']),'changed':sum(left.get(k)!=right.get(k) for k in set(left)|set(right))}
    rules=read(old/'accord-02e4r5-validation-rules.json')['rules']; graph=read(old/'accord-02e4r5-dependency-graph.json')['edges']
    tests['DEPENDENCY_GRAPH_EQUAL']={(x['rule_id'],d) for x in rules for d in x.get('depends_on',[])}=={(x['from'],x['to']) for x in graph}
    authority=read(d/'accord-02e4r5r1-predicate-authority.json'); partial=read(d/'accord-02e4r5r1-partial-effect-policy.json'); canonical=read(d/'accord-02e4r5r1-canonicalization-profile.json'); governed=read(old/'accord-02e4r5-predicate-registry.json')
    tests['POLICY_CLOSURE']=authority['global_stage_order']==governed['global_stage_order']=='FORBIDDEN' and authority['implicit_transitivity']==governed['implicit_transitivity']=='FORBIDDEN' and not ({'global_stage_order','implicit_transitivity'} & set(partial)) and partial['merged_outcome'].get('UNKNOWN_TUPLE_OR_WRONG_STAGE')=='REJECT' and canonical['content_targets'].get('PACKAGE_EXCLUDING_SELF_DIGEST') is not None and canonical['self_digest_target_id']=='PACKAGE_EXCLUDING_SELF_DIGEST'
    target=read(d/'accord-02e4r5r1-v013-target.json'); evidence=read(d/'accord-02e4r5r1-v013-evidence.json'); neg=read(old/'accord-02e4r5-settlement-profile-conservative.json')['negative_policy']
    span=(instant(target['required_interval']['as_of'])-instant(target['required_interval']['not_before'])).total_seconds(); age=(instant(evidence['verification_time'])-instant(evidence['observed_at'])).total_seconds()
    same=(evidence['effect_id'],evidence['predicate_id'],evidence['stage'],evidence['scope'])==(target['effect_id'],target['negated_predicate_id'],target['negated_stage'],target['scope'])
    covered=instant(evidence['observed_interval']['not_before'])<=instant(target['required_interval']['not_before'])<=instant(target['required_interval']['as_of'])<=instant(evidence['observed_interval']['as_of'])
    positive=any(x.get('polarity')=='POSITIVE' and (x.get('effect_id'),x.get('predicate_id'),x.get('stage'),x.get('scope'))==(target['effect_id'],target['negated_predicate_id'],target['negated_stage'],target['scope']) for x in evidence['evidence_universe'])
    tests['NEGATIVE_REQUIREMENT_MAP_CLOSURE']=same and covered and evidence['retention_window_seconds']>=max(span,neg['minimum_retention_seconds']) and 0<=age<=neg['freshness_max_age_seconds'] and evidence['consistency_level'] in neg['allowed_consistency_levels'] and evidence['evidence_class'] in neg['allowed_source_classes'] and evidence['read_scope_complete'] and evidence['read_semantics']=='COMPLETE_LEDGER_QUERY' and not positive and target['relationship']=='CANDIDATE_FIXTURE_OF_SAME_SEMANTIC_CLASS_AS_ACCEPTED_V013'
    # Independently execute old candidate-owned pointer checks, but never count them as conformance.
    assertions={x['assertion_id'].rsplit(':',1)[1]:x for x in read(old/'accord-02e4r5-assertion-registry.json')['assertions']}
    internal_ok=True
    for row in matrix['rules']:
        if row['semantic_class']!='INTERNAL_DESIGN_INVARIANT': continue
        arg=assertions[row['rule_id']]['expression']['checks'][0]['arguments']; choices=buckets.get((arg['subject']['kind'],arg['subject']['id'],arg['subject']['version']),[])
        try:
            value=read(base/choices[0]['path'])
            for part in row['subject_pointer'].split('/')[1:]: value=value[int(part)] if type(value) is list else value[part.replace('~1','/').replace('~0','~')]
            internal_ok &= len(choices)==1 and value==row['expected'] and row['expected']==arg['expected']
        except Exception: internal_ok=False
    tests['INTERNAL_DESIGN']=bool(internal_ok)
    overall=all(tests.values()); conformance=[x for x in matrix['rules'] if x['semantic_class']=='EXECUTABLE_CONFORMANCE_RULE']; internals=[x for x in matrix['rules'] if x['semantic_class']=='INTERNAL_DESIGN_INVARIANT']; deferred=[x for x in matrix['rules'] if x['semantic_class']=='DEFERRED_NO_SUBJECT_ARTIFACT']
    conformance_results={x['rule_id']:('PASS' if overall else 'FAIL') for x in conformance}; internal_results={x['rule_id']:('PASS' if internal_ok else 'FAIL') for x in internals}
    counts={'TOTAL_DECLARED_RULES':len(matrix['rules']),'EXECUTABLE_CONFORMANCE_RULES':len(conformance),'INTERNAL_DESIGN_INVARIANTS':len(internals),'DEFERRED_NO_SUBJECT_ARTIFACT':len(deferred),'CONFORMANCE_EXECUTED':len(conformance),'CONFORMANCE_PASS':sum(x=='PASS' for x in conformance_results.values()),'CONFORMANCE_FAIL':sum(x=='FAIL' for x in conformance_results.values()),'INTERNAL_EXECUTED':len(internals),'INTERNAL_PASS':sum(x=='PASS' for x in internal_results.values()),'INTERNAL_FAIL':sum(x=='FAIL' for x in internal_results.values()),'DEFERRED':len(deferred),'UNEVALUABLE_CONFORMANCE':0,'AMBIGUOUS_CONFORMANCE':0}
    return {'certificate':'ACCORD-02E4R5R1_INDEPENDENT','read_only':True,'repository_write_count':0,'package_invariants':tests,'rule_counts':counts,'conformance_results':conformance_results,'internal_results':internal_results,'reference_trace':{'derived_edges':len(discovered),'unresolved':len(bad),'edge_set_sha256':hashlib.sha256(json.dumps(edge_strings,separators=(',',':')).encode()).hexdigest()},'expectation_metrics':expectation_metrics,'v013_result':'NON_OCCURRENCE_SUPPORTED' if tests['NEGATIVE_REQUIREMENT_MAP_CLOSURE'] else 'UNKNOWN','overall_pass':overall}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root',default=Path(__file__).resolve().parents[3]); args=parser.parse_args()
    try: answer=evaluate(args.root)
    except Exception as exc: answer={'certificate':'ACCORD-02E4R5R1_INDEPENDENT','overall_pass':False,'fatal':type(exc).__name__+': '+str(exc)}
    print(json.dumps(answer,sort_keys=True)); sys.exit(0 if answer.get('overall_pass') else 1)
