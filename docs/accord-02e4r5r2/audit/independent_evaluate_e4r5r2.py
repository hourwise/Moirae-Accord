from __future__ import annotations
import argparse,copy,hashlib,json,sys
from datetime import datetime
from pathlib import Path
import jsonschema,rfc8785

def get(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def canon(x): return hashlib.sha256(rfc8785.dumps(x)).hexdigest()
def pointer(x,p):
    for part in p.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~');x=x[int(part)] if type(x) is list else x[part]
    return x
def stamp(x):return datetime.fromisoformat(x.replace('Z','+00:00'))

class Independent:
    def __init__(self,root):
        self.base=Path(root).resolve();self.d=self.base/'docs/accord-02e4r5r2'
        self.catalog=get(self.d/'object-registry.json');self.pkg=get(self.d/'specification-package-0.2.json');self.rr=get(self.d/'rule-registry.json');self.ir=get(self.d/'invariant-registry.json');self.pr=get(self.d/'procedure-registry.json');self.rm=get(self.d/'reference-model.json');self.auth=get(self.d/'authority-requirements.json')
        self.objects=self.catalog['objects'];self.by_key={}
        for x in self.objects:self.by_key.setdefault((x['kind'],x['id'],x['version']),[]).append(x)
        self.iv={x['invariant_id']:x for x in self.ir['invariants']};self.pv={x['procedure_id']:x for x in self.pr['procedures']}
    def entry(self,r):
        found=self.by_key.get((r['kind'],r['id'],r['version']),[])
        if len(found)!=1:raise LookupError('not exactly one')
        if r.get('member_id') not in (None,'') and r['member_id'] not in found[0].get('members',[]):raise LookupError('missing member')
        return found[0]
    def obj(self,r):return get(self.base/self.entry(r)['path'])
    def universe(self):return [x for x in self.objects if x['status']=='ACTIVE' and x['classification']=='NORMATIVE']
    def schema_results(self):
        answer={};schemas={}
        for item in self.objects:
            if item['kind']=='SCHEMA' and item['status']=='ACTIVE':
                try:s=get(self.base/item['path']);jsonschema.Draft202012Validator.check_schema(s);schemas[(item['id'],item['version'])]=s;answer[item['id']]='PASS'
                except Exception:answer[item['id']]='FAIL'
        for item in self.universe():
            if item['kind']=='SCHEMA':continue
            try:ref=item['schema_ref'];jsonschema.validate(get(self.base/item['path']),schemas[(ref['id'],ref['version'])]);answer[item['id']]='PASS'
            except Exception:answer[item['id']]='FAIL'
        return answer
    def reference_edges(self):
        shape=self.rm['shape_predicate'];found=[]
        def visit(value,source,at=''):
            if type(value) is dict:
                keys=set(value);required=set(shape['required_keys']);optional=set(shape['optional_keys'])
                if required<=keys and keys<=required|optional and all(type(v) is str for v in value.values()):found.append((source['kind'],source['id'],source['version'],at,value['kind'],value['id'],value['version'],value.get('member_id','')))
                for k,v in value.items():visit(v,source,at+'/'+k.replace('~','~0').replace('/','~1'))
            elif type(value) is list:
                for n,v in enumerate(value):visit(v,source,at+'/'+str(n))
        for source in self.universe():visit(get(self.base/source['path']),source)
        return sorted(set(found))
    def references_pass(self,edges):
        for edge in edges:
            ref={'kind':edge[4],'id':edge[5],'version':edge[6]}
            if edge[7]:ref['member_id']=edge[7]
            try:self.entry(ref)
            except Exception:return False
        return True
    def integrity_pass(self):
        for item in self.universe():
            mode=item['integrity']['mode'];document=get(self.base/item['path'])
            if mode=='SEMANTIC_JSON_CONTENT' and canon(document)!=item['integrity']['digest']:return False
            if mode=='PACKAGE_PINNED_BOOTSTRAP' and canon(document)!=self.pkg['registry_semantic_sha256']:return False
            if mode=='SELF_DIGEST':
                expected=document['current_candidate_integrity']['digest'];reduced=copy.deepcopy(document);del reduced['current_candidate_integrity']['digest']
                if canon(reduced)!=expected:return False
        return True
    def dual(self,b):
        for source in b['sources']:
            data=(self.base/source['path']).read_bytes();claim=source['integrity']
            if hashlib.sha256(data).hexdigest()!=claim['raw_file_bytes_sha256'] or canon(json.loads(data))!=claim['semantic_json_content_sha256']:return False
        return True
    def arity_pass(self):
        for inv in self.iv.values():
            proc=self.pv.get(inv['procedure_id']);left={x['role'] for x in inv['input_roles'] if x['required']};right={x['name'] for x in proc['arguments'] if x['required']} if proc else set()
            if left!=right or set(inv['default_arguments'])!=left or inv['fail_closed'] is not True:return False
        return True
    def classes(self):
        cmap={};valid={}
        for rule in self.rr['rules']:
            if 'invariant_binding' in rule:
                cls='EXECUTABLE_CONFORMANCE_RULE';bind=rule['invariant_binding'];inv=self.iv.get(bind['invariant_id']);ok=bool(inv) and inv['status']=='ACTIVE' and set(bind['arguments'])=={x['role'] for x in inv['input_roles'] if x['required']} and bind['arguments']==inv['default_arguments'] and rule['inherited_failure_code'] in inv['compatible_failure_codes'] and 'subjects' not in rule
                if ok:
                    for spec in inv['input_roles']:
                        a=bind['arguments'][spec['role']];ok &= a['kind']==spec['kind']
                        try:self.entry(a)
                        except Exception:ok=False
                valid[rule['rule_id']]=bool(ok)
            elif 'internal_check' in rule and 'invariant_binding' not in rule:cls='INTERNAL_DESIGN_INVARIANT';valid[rule['rule_id']]=True
            elif rule.get('missing_subject_roles') and rule.get('later_lifecycle_stage') and 'internal_check' not in rule and 'invariant_binding' not in rule:cls='DEFERRED_NO_SUBJECT_ARTIFACT';valid[rule['rule_id']]=True
            else:cls='INVALID';valid[rule['rule_id']]=False
            cmap[rule['rule_id']]=cls
        return cmap,{k for k in cmap if cmap[k]!=next(x for x in self.rr['rules'] if x['rule_id']==k)['declared_class'] or not valid[k]}
    def run_invariant(self,iid,arguments):
        inv=self.iv[iid];proc=self.pv[inv['procedure_id']];operation=proc['derivation']['operation'];a={k:self.obj(v) for k,v in arguments.items()};ok=False;note={}
        try:
            if operation=='VALIDATE_ACTIVE_UNIVERSE':r=self.schema_results();ok=all(x=='PASS' for x in r.values());note=r
            elif iid=='PACKAGE_LINEAGE':
                p=a['package'];q=a['authority']['package_requirements'];wanted=q['required_rejected_revision'];ok=p['package_id']==q['family'] and p['package_version']==q['version'] and p['status']==q['status'] and wanted in [{k:x[k] for k in ('revision','commit') if k in x} for x in p['rejected_candidate_lineage']]
            elif operation=='DIGEST_RECOMPUTE' and iid in ('ACCEPTED_BASE_DUAL_INTEGRITY','ACCEPTED_SOURCE_DUAL_INTEGRITY'):ok=self.dual(a['bindings'])
            elif iid=='OBJECT_IDENTITY_UNIQUE':keys=[(x['kind'],x['id'],x['version']) for x in a['registry']['objects']];ok=len(keys)==len(set(keys))
            elif operation=='REFERENCE_RESOLUTION':edges=self.reference_edges();ok=self.references_pass(edges);note={'edges':[list(x) for x in edges]}
            elif operation=='DIGEST_RECOMPUTE':ok=self.integrity_pass()
            elif iid=='DEPENDENCY_GRAPH_EQUAL':
                def projected(spec):
                    role,path=spec['source'].split(':',1);rows=pointer(a[role],path[:-2]);fields=spec['projection'];answer=set()
                    for row in rows:
                        fixed=tuple(pointer(row,'/'+field) for field in fields if not field.endswith('/*'));repeating=[field for field in fields if field.endswith('/*')]
                        if repeating:
                            for value in pointer(row,'/'+repeating[0][:-2]):answer.add(fixed+(value,))
                        else:answer.add(fixed)
                    return answer
                ok=projected(proc['derivation']['left'])==projected(proc['derivation']['right'])
            elif iid=='EXPECTATION_STABILITY':left={x['vector_id']:x['expected'] for x in a['inputs']['vector_expectations']};right={x['vector_id']:x['expected'] for x in a['accepted_vectors']['vectors']};ok=left==right;note={'vector_ids':len(left),'changed':sorted(k for k in set(left)|set(right) if left.get(k)!=right.get(k))}
            elif iid=='PREDICATE_AUTHORITY_CLOSURE':required=a['authority']['stage_policy_requirements'];allowed=a['authority']['stage_policy_authorization'];ok=a['inputs']['predicate_policy']==required and all(required[k] in allowed[k] for k in required)
            elif iid=='CANONICALIZATION_AUTHORITY_CLOSURE':required=a['authority']['canonicalization_requirements'];ok={k:a['profile'][k] for k in required}==required
            elif iid=='SOURCE_CATALOG_BINDING':ok=sum(x['ref']['kind']=='SOURCE_VECTOR_CATALOG' for x in a['bindings']['sources'])==1 and bool(a['inputs']['source_catalog_binding'])
            elif iid=='PARTIAL_EFFECT_POLICY_CLOSURE':p=a['policy'];q=a['authority']['partial_effect_requirements'];ok=p['same_effect_required']==q['same_effect_required'] and p['direct_predecessor_required']==q['direct_predecessor_required'] and p['decisions'][q['merged_decision_key']]==q['merged_decision_value']
            elif operation=='REQUIREMENT_MAP_EVAL':
                t=a['target'];e=a['evidence'];p=a['inputs']['profile']['negative_policy'];same=(e['effect_id'],e['predicate_id'],e['stage'],e['scope'])==(t['effect_id'],t['negated_predicate_id'],t['negated_stage'],t['scope']);within=stamp(e['observed_interval']['not_before'])<=stamp(t['required_interval']['not_before'])<=stamp(t['required_interval']['as_of'])<=stamp(e['observed_interval']['as_of']);span=(stamp(t['required_interval']['as_of'])-stamp(t['required_interval']['not_before'])).total_seconds();age=(stamp(e['verification_time'])-stamp(e['observed_at'])).total_seconds();positive=any(x.get('admissible',True) and x.get('polarity')=='POSITIVE' and (x.get('effect_id'),x.get('predicate_id'),x.get('stage'),x.get('scope'))==(t['effect_id'],t['negated_predicate_id'],t['negated_stage'],t['scope']) for x in e['evidence_universe']);ok=all([same,within,e['retention_window_seconds']>=max(span,p['minimum_retention_seconds']),0<=age<=p['freshness_max_age_seconds'],e['consistency_level'] in p['allowed_consistency_levels'],e['evidence_class'] in p['allowed_source_classes'],e['read_scope_complete'],e['read_semantics']=='COMPLETE_LEDGER_QUERY',not positive]);note={'result':proc['derivation']['pass_result'] if ok else proc['derivation']['fail_result']}
            elif operation=='AUTHORITY_COMPLETENESS':
                cmap,errors=self.classes();active={k for k,v in self.iv.items() if v['status']=='ACTIVE'};required=set(self.pkg['required_invariant_ids']);bound={r['invariant_binding']['invariant_id'] for r in self.rr['rules'] if 'invariant_binding' in r};package_only={k for k,v in self.iv.items() if v['usage']=='PACKAGE_ONLY_REQUIRED'};ok=not errors and active==required==bound|package_only
            elif iid=='PROPOSITION_ID_UNIQUE':x=a['inputs']['proposition_ids'];ok=len(x)==len(set(x))
            elif iid=='PROFILE_REFERENCE_PINNING':ok=a['inputs']['profile']['object_version']==self.auth['package_requirements']['version']
            elif operation=='ARITY_AGREEMENT':ok=self.arity_pass()
            elif operation=='SCHEMA_NON_VACUITY':ok=all(list(jsonschema.Draft202012Validator(get(self.base/x['path'])).iter_errors(proc['derivation']['probe'])) for x in self.objects if x['kind']=='SCHEMA' and x['status']=='ACTIVE')
            elif operation=='CURRENT_PACKAGE_IDENTITY':q=self.auth['package_requirements'];hits=self.by_key.get(('PACKAGE',q['family'],q['version']),[]);ok=len(hits)==proc['derivation']['required_resolution_count'] and hits[0]['path']==self.entry(arguments['package'])['path']
            elif operation=='SELF_DIGEST':p=a['package'];expected=p['current_candidate_integrity']['digest'];reduced=copy.deepcopy(p);del reduced['current_candidate_integrity']['digest'];ok=canon(reduced)==expected
        except Exception as e:ok=False;note={'exception':type(e).__name__+': '+str(e)}
        return {'status':'PASS' if ok else 'FAIL','failure_codes':[] if ok else inv['compatible_failure_codes'],'procedure':inv['procedure_id'],'note':note}
    def evaluate(self):
        cmap,class_errors=self.classes();invariant={k:self.run_invariant(k,v['default_arguments']) for k,v in self.iv.items() if v['status']=='ACTIVE'};bindings={};groups={};rules={};internal={}
        for r in self.rr['rules']:
            cls=cmap[r['rule_id']]
            if cls=='EXECUTABLE_CONFORMANCE_RULE':b=r['invariant_binding'];key=b['invariant_id']+'|'+rfc8785.dumps(b['arguments']).decode();bindings.setdefault(key,self.run_invariant(b['invariant_id'],b['arguments']));groups.setdefault(key,[]).append(r['rule_id']);rules[r['rule_id']]=bindings[key]['status'] if not class_errors else 'FAIL'
            elif cls=='INTERNAL_DESIGN_INVARIANT':c=r['internal_check'];internal[r['rule_id']]='PASS' if pointer(self.obj(c['subject']),c['pointer'])==c['expected'] else 'FAIL'
            else:rules[r['rule_id']]='DEFERRED'
        active=set(self.pkg['required_invariant_ids']);overall=active==set(invariant) and not class_errors and all(x['status']=='PASS' for x in invariant.values()) and all(x['status']=='PASS' for x in bindings.values()) and all(x=='PASS' for x in internal.values());conf=[r for r in self.rr['rules'] if cmap[r['rule_id']]=='EXECUTABLE_CONFORMANCE_RULE'];deferred=[r for r in self.rr['rules'] if cmap[r['rule_id']]=='DEFERRED_NO_SUBJECT_ARTIFACT']
        counts={'TOTAL_DECLARED_RULES':len(self.rr['rules']),'CONFORMANCE_MEMBER_RULES':len(conf),'INDEPENDENT_CONFORMANCE_BINDINGS':len(bindings),'CONFORMANCE_BINDINGS_PASS':sum(x['status']=='PASS' for x in bindings.values()),'CONFORMANCE_BINDINGS_FAIL':sum(x['status']=='FAIL' for x in bindings.values()),'CONFORMANCE_MEMBER_RULES_PASS':sum(rules[x['rule_id']]=='PASS' for x in conf),'CONFORMANCE_MEMBER_RULES_FAIL':sum(rules[x['rule_id']]=='FAIL' for x in conf),'INTERNAL_DESIGN_INVARIANTS':len(internal),'INTERNAL_PASS':sum(x=='PASS' for x in internal.values()),'INTERNAL_FAIL':sum(x=='FAIL' for x in internal.values()),'DEFERRED':len(deferred),'PACKAGE_INVARIANTS_REQUIRED':len(active),'PACKAGE_INVARIANTS_EXECUTED':len(invariant),'PACKAGE_INVARIANTS_PASS':sum(x['status']=='PASS' for x in invariant.values()),'PACKAGE_INVARIANTS_FAIL':sum(x['status']=='FAIL' for x in invariant.values()),'UNEVALUABLE_CONFORMANCE_BINDINGS':0,'AMBIGUOUS_CONFORMANCE_BINDINGS':0}
        return {'certificate':'ACCORD-02E4R5R2_INDEPENDENT','read_only':True,'repository_write_count':0,'active_object_set':sorted((x['kind'],x['id'],x['version']) for x in self.universe()),'schema_validation_results':self.schema_results(),'reference_edge_set':[list(x) for x in self.reference_edges()],'invariant_results':{k:v['status'] for k,v in invariant.items()},'invariant_failure_code_map':{k:v['failure_codes'] for k,v in invariant.items()},'binding_results':{k:v['status'] for k,v in bindings.items()},'collapse_groups':groups,'rule_results':rules,'internal_results':internal,'class_map':cmap,'v013_result':invariant['NEGATIVE_REQUIREMENT_MAP_CLOSURE']['note'].get('result'),'expectation_stability_result':invariant['EXPECTATION_STABILITY']['note'],'counts':counts,'overall_pass':overall}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=Path(__file__).resolve().parents[3]);a=p.parse_args()
    try:o=Independent(a.root).evaluate()
    except Exception as e:o={'certificate':'ACCORD-02E4R5R2_INDEPENDENT','overall_pass':False,'fatal':type(e).__name__+': '+str(e)}
    print(json.dumps(o,sort_keys=True));sys.exit(0 if o.get('overall_pass') else 1)
