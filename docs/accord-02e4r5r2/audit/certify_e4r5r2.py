from __future__ import annotations
import argparse, copy, hashlib, json, sys
from datetime import datetime
from pathlib import Path
import jsonschema, rfc8785

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def jcs_hash(x): return hashlib.sha256(rfc8785.dumps(x)).hexdigest()
def jp(x,p):
    if p in ('','/'): return x
    for t in p.split('/')[1:]:
        t=t.replace('~1','/').replace('~0','~'); x=x[int(t)] if isinstance(x,list) else x[t]
    return x
def iso(s): return datetime.fromisoformat(s.replace('Z','+00:00'))

class Engine:
    def __init__(self,root):
        self.root=Path(root).resolve(); self.dir=self.root/'docs/accord-02e4r5r2'
        self.registry=read(self.dir/'object-registry.json'); self.package=read(self.dir/'specification-package-0.2.json')
        self.rules=read(self.dir/'rule-registry.json'); self.invariants=read(self.dir/'invariant-registry.json'); self.procedures=read(self.dir/'procedure-registry.json')
        self.reference_model=read(self.dir/'reference-model.json'); self.authority=read(self.dir/'authority-requirements.json')
        self.objects=self.registry['objects']; self.index={}
        for o in self.objects:self.index.setdefault((o['kind'],o['id'],o['version']),[]).append(o)
        self.inv={x['invariant_id']:x for x in self.invariants['invariants']}; self.proc={x['procedure_id']:x for x in self.procedures['procedures']}
    def resolve_entry(self,r):
        h=self.index.get((r['kind'],r['id'],r['version']),[])
        if len(h)!=1: raise ValueError('resolution cardinality')
        if r.get('member_id') and r['member_id'] not in h[0].get('members',[]): raise ValueError('member resolution')
        return h[0]
    def resolve(self,r): return read(self.root/self.resolve_entry(r)['path'])
    def active_normative(self): return [x for x in self.objects if x['status']=='ACTIVE' and x['classification']=='NORMATIVE']
    def edges(self):
        model=self.reference_model['shape_predicate']; edges=[]
        def walk(x,source,p=''):
            if isinstance(x,dict):
                k=set(x); req=set(model['required_keys']); opt=set(model['optional_keys'])
                if req<=k and k<=req|opt and all(isinstance(v,str) for v in x.values()): edges.append((source['kind'],source['id'],source['version'],p,x['kind'],x['id'],x['version'],x.get('member_id','')))
                for n,v in x.items():walk(v,source,p+'/'+n.replace('~','~0').replace('/','~1'))
            elif isinstance(x,list):
                for n,v in enumerate(x):walk(v,source,p+'/'+str(n))
        for o in self.active_normative(): walk(read(self.root/o['path']),o)
        return sorted(set(edges))
    def reference_result(self):
        edges=self.edges(); bad=[]
        for e in edges:
            r={'kind':e[4],'id':e[5],'version':e[6]}
            if e[7]:r['member_id']=e[7]
            try:self.resolve_entry(r)
            except Exception as z:bad.append({'edge':e,'error':str(z)})
        return not bad,{'edges':[list(x) for x in edges],'unresolved_or_ambiguous':bad}
    def standards(self):
        result={}; schemas={}
        for o in self.objects:
            if o['kind']=='SCHEMA' and o['status']=='ACTIVE':
                s=read(self.root/o['path']);
                try:jsonschema.Draft202012Validator.check_schema(s); result[o['id']]={'status':'PASS','kind':'SCHEMA_META'}; schemas[(o['id'],o['version'])]=s
                except Exception as e:result[o['id']]={'status':'FAIL','detail':str(e)}
        for o in self.active_normative():
            if o['kind']=='SCHEMA':continue
            key=o['id']; sr=o.get('schema_ref')
            try:
                s=schemas[(sr['id'],sr['version'])]; jsonschema.validate(read(self.root/o['path']),s); result[key]={'status':'PASS','kind':'INSTANCE'}
            except Exception as e:result[key]={'status':'FAIL','detail':str(e)}
        return all(x['status']=='PASS' for x in result.values()),result
    def nonvacuity(self):
        out={}
        for o in self.objects:
            if o['kind']=='SCHEMA' and o['status']=='ACTIVE':
                errors=list(jsonschema.Draft202012Validator(read(self.root/o['path'])).iter_errors({'zzz':1})); out[o['id']]='PASS' if errors else 'FAIL'
        return all(x=='PASS' for x in out.values()),out
    def integrity(self):
        out={}
        for o in self.active_normative():
            mode=o['integrity']['mode']; p=self.root/o['path']
            if mode=='SEMANTIC_JSON_CONTENT': ok=jcs_hash(read(p))==o['integrity']['digest']
            elif mode=='PACKAGE_PINNED_BOOTSTRAP': ok=jcs_hash(read(p))==self.package['registry_semantic_sha256']
            elif mode=='SELF_DIGEST':
                x=read(p); expected=x['current_candidate_integrity']['digest']; y=copy.deepcopy(x); del y['current_candidate_integrity']['digest']; ok=jcs_hash(y)==expected
            else: ok=False
            out[o['id']]={'status':'PASS' if ok else 'FAIL','mode':mode}
        return all(x['status']=='PASS' for x in out.values()),out
    def dual_integrity(self,bindings):
        out={}
        for s in bindings['sources']:
            p=self.root/s['path']; b=p.read_bytes(); semantic=jcs_hash(json.loads(b)); i=s['integrity']; ok=hashlib.sha256(b).hexdigest()==i['raw_file_bytes_sha256'] and semantic==i['semantic_json_content_sha256']; out[s['path']]={'status':'PASS' if ok else 'FAIL','raw':hashlib.sha256(b).hexdigest(),'semantic':semantic}
        return all(x['status']=='PASS' for x in out.values()),out
    def arity(self):
        out={}
        for iid,i in self.inv.items():
            p=self.proc.get(i['procedure_id']); a={x['role'] for x in i['input_roles'] if x['required']}; b={x['name'] for x in p['arguments'] if x['required']} if p else set(); ok=a==b and set(i['default_arguments'])==a and i['fail_closed'] is True; out[iid]={'status':'PASS' if ok else 'FAIL','invariant_roles':sorted(a),'procedure_arguments':sorted(b)}
        return all(x['status']=='PASS' for x in out.values()),out
    def class_and_bindings(self):
        classes={}; errors={}; compat={}
        for r in self.rules['rules']:
            if 'invariant_binding' in r:
                derived='EXECUTABLE_CONFORMANCE_RULE'; b=r['invariant_binding']; inv=self.inv.get(b['invariant_id']); ok=inv is not None and inv['status']=='ACTIVE' and set(b['arguments'])=={x['role'] for x in inv['input_roles'] if x['required']} and b['arguments']==inv['default_arguments'] and r['inherited_failure_code'] in inv['compatible_failure_codes'] and 'subjects' not in r
                if ok:
                    for role,spec in [(x['role'],x) for x in inv['input_roles']]:
                        arg=b['arguments'][role]; ok &= arg['kind']==spec['kind']
                        try:self.resolve_entry(arg)
                        except Exception:ok=False
                compat[r['rule_id']]=ok
            elif 'internal_check' in r and 'invariant_binding' not in r: derived='INTERNAL_DESIGN_INVARIANT'; compat[r['rule_id']]=True
            elif r.get('missing_subject_roles') and r.get('later_lifecycle_stage') and 'invariant_binding' not in r and 'internal_check' not in r: derived='DEFERRED_NO_SUBJECT_ARTIFACT'; compat[r['rule_id']]=True
            else: derived='INVALID'; compat[r['rule_id']]=False
            classes[r['rule_id']]=derived
            if derived!=r['declared_class'] or not compat[r['rule_id']]:errors[r['rule_id']]={'declared':r['declared_class'],'derived':derived,'compatible':compat[r['rule_id']]}
        return not errors,classes,errors
    def pointer_pair(self,expr,args):
        role,path=expr.split(':',1); return jp(args[role],path)
    def execute(self,iid,args):
        inv=self.inv[iid]; proc=self.proc[inv['procedure_id']]; op=proc['derivation']['operation']; resolved={k:self.resolve(v) for k,v in args.items()}; ok=False; witness={}
        try:
            if op=='VALIDATE_ACTIVE_UNIVERSE':ok,witness=self.standards()
            elif op=='LINEAGE_VALIDATION' or (op=='SECTION_ENTAILMENT' and iid=='PACKAGE_LINEAGE'):
                p=resolved['package']; a=resolved['authority']['package_requirements']; required=a['required_rejected_revision']; ok=p['package_id']==a['family'] and p['package_version']==a['version'] and p['status']==a['status'] and required in [{k:x[k] for k in ('revision','commit') if k in x} for x in p['rejected_candidate_lineage']]; witness={'required':required}
            elif op=='DIGEST_RECOMPUTE' and iid in ('ACCEPTED_BASE_DUAL_INTEGRITY','ACCEPTED_SOURCE_DUAL_INTEGRITY'):ok,witness=self.dual_integrity(resolved['bindings'])
            elif op=='UNIQUE_KEY' and iid=='OBJECT_IDENTITY_UNIQUE':
                keys=[(x['kind'],x['id'],x['version']) for x in resolved['registry']['objects']]; ok=len(keys)==len(set(keys)); witness={'keys':len(keys),'unique':len(set(keys))}
            elif op=='REFERENCE_RESOLUTION':ok,witness=self.reference_result()
            elif op=='DIGEST_RECOMPUTE':ok,witness=self.integrity()
            elif op=='SET_EQUALITY' and iid=='DEPENDENCY_GRAPH_EQUAL':
                def project(spec):
                    role,path=spec['source'].split(':',1); rows=jp(resolved[role],path[:-2]); fields=spec['projection']; out=set()
                    for row in rows:
                        fixed=tuple(jp(row,'/'+field) for field in fields if not field.endswith('/*')); repeating=[field for field in fields if field.endswith('/*')]
                        if repeating:
                            for value in jp(row,'/'+repeating[0][:-2]):out.add(fixed+(value,))
                        else:out.add(fixed)
                    return out
                left=project(proc['derivation']['left']); right=project(proc['derivation']['right']); ok=left==right; witness={'left':sorted(left),'right':sorted(right)}
            elif op=='SET_EQUALITY':
                left={x['vector_id']:x['expected'] for x in resolved['inputs']['vector_expectations']}; right={x['vector_id']:x['expected'] for x in resolved['accepted_vectors']['vectors']}; ok=left==right; witness={'vector_ids':len(left),'changed':sorted(k for k in set(left)|set(right) if left.get(k)!=right.get(k))}
            elif op=='POLICY_AGREEMENT' and iid=='PREDICATE_AUTHORITY_CLOSURE':
                left=resolved['inputs']['predicate_policy']; right=resolved['authority']['stage_policy_requirements']; allowed=resolved['authority']['stage_policy_authorization']; ok=left==right and all(right[k] in allowed[k] for k in right); witness={'governed':left,'required':right,'authorized':allowed}
            elif op=='POLICY_AGREEMENT' and iid=='CANONICALIZATION_AUTHORITY_CLOSURE':
                left={k:v for k,v in resolved['profile'].items() if k in resolved['authority']['canonicalization_requirements']}; right=resolved['authority']['canonicalization_requirements']; ok=left==right; witness={'governed':left,'required':right}
            elif op=='MEMBERSHIP_RESOLVE':
                b=resolved['bindings']['sources']; ok=len([x for x in b if x['ref']['kind']=='SOURCE_VECTOR_CATALOG'])==1 and bool(resolved['inputs']['source_catalog_binding']); witness={'catalog_bindings':sum(x['ref']['kind']=='SOURCE_VECTOR_CATALOG' for x in b)}
            elif op=='POLICY_AGREEMENT' and iid=='PARTIAL_EFFECT_POLICY_CLOSURE':
                p=resolved['policy']; a=resolved['authority']['partial_effect_requirements']; ok=p['same_effect_required']==a['same_effect_required'] and p['direct_predecessor_required']==a['direct_predecessor_required'] and p['decisions'][a['merged_decision_key']]==a['merged_decision_value']; witness={'decision':p['decisions'][a['merged_decision_key']]}
            elif op=='REQUIREMENT_MAP_EVAL':
                t=resolved['target']; e=resolved['evidence']; pol=resolved['inputs']['profile']['negative_policy']; same=(e['effect_id'],e['predicate_id'],e['stage'],e['scope'])==(t['effect_id'],t['negated_predicate_id'],t['negated_stage'],t['scope']); interval=iso(e['observed_interval']['not_before'])<=iso(t['required_interval']['not_before'])<=iso(t['required_interval']['as_of'])<=iso(e['observed_interval']['as_of']); duration=(iso(t['required_interval']['as_of'])-iso(t['required_interval']['not_before'])).total_seconds(); age=(iso(e['verification_time'])-iso(e['observed_at'])).total_seconds(); contradictions=[x for x in e['evidence_universe'] if x.get('admissible',True) and x.get('polarity')=='POSITIVE' and (x.get('effect_id'),x.get('predicate_id'),x.get('stage'),x.get('scope'))==(t['effect_id'],t['negated_predicate_id'],t['negated_stage'],t['scope'])]; checks={'exact_target':same,'interval':interval,'retention':e['retention_window_seconds']>=max(duration,pol['minimum_retention_seconds']),'freshness':0<=age<=pol['freshness_max_age_seconds'],'consistency':e['consistency_level'] in pol['allowed_consistency_levels'],'source':e['evidence_class'] in pol['allowed_source_classes'],'complete_read':e['read_scope_complete'] and e['read_semantics']=='COMPLETE_LEDGER_QUERY','no_positive':not contradictions}; ok=all(checks.values()); witness={'checks':checks,'result':proc['derivation']['pass_result'] if ok else proc['derivation']['fail_result']}
            elif op=='AUTHORITY_COMPLETENESS':
                class_ok,_,class_errors=self.class_and_bindings(); active={x for x,v in self.inv.items() if v['status']=='ACTIVE'}; required=set(self.package['required_invariant_ids']); referenced={r['invariant_binding']['invariant_id'] for r in self.rules['rules'] if 'invariant_binding' in r}; package_only={x for x,v in self.inv.items() if v['usage']=='PACKAGE_ONLY_REQUIRED'}; ok=class_ok and active==required==referenced|package_only; witness={'class_errors':class_errors,'active':sorted(active),'required':sorted(required),'referenced_or_package_only':sorted(referenced|package_only)}
            elif op=='UNIQUE_KEY':
                vals=resolved['inputs']['proposition_ids']; ok=len(vals)==len(set(vals)); witness={'members':len(vals),'unique':len(set(vals))}
            elif op=='SECTION_ENTAILMENT':
                ok=resolved['inputs']['profile']['object_version']==resolved.get('authority',self.authority)['package_requirements']['version']; witness={'profile_version':resolved['inputs']['profile']['object_version']}
            elif op=='ARITY_AGREEMENT':ok,witness=self.arity()
            elif op=='SCHEMA_NON_VACUITY':ok,witness=self.nonvacuity()
            elif op=='CURRENT_PACKAGE_IDENTITY':
                a=self.authority['package_requirements']; hits=self.index.get(('PACKAGE',a['family'],a['version']),[]); ok=len(hits)==1 and hits[0]['path']==self.resolve_entry(args['package'])['path']; witness={'hits':[x['path'] for x in hits]}
            elif op=='SELF_DIGEST':
                p=resolved['package']; expected=p['current_candidate_integrity']['digest']; q=copy.deepcopy(p); del q['current_candidate_integrity']['digest']; actual=jcs_hash(q); ok=actual==expected; witness={'expected':expected,'actual':actual,'reduction':resolved['canonicalization']['reduction']}
        except Exception as e:ok=False; witness={'exception':type(e).__name__+': '+str(e)}
        return {'invariant_id':iid,'status':'PASS' if ok else 'FAIL','resolved_arguments':args,'procedure':inv['procedure_id'],'witness':witness,'failure_codes':[] if ok else inv['compatible_failure_codes']}
    def run(self):
        arity_ok,arity_trace=self.arity(); class_ok,class_map,class_errors=self.class_and_bindings()
        invariant_results={iid:self.execute(iid,inv['default_arguments']) for iid,inv in self.inv.items() if inv['status']=='ACTIVE'}
        binding_results={}; collapse={}; rule_results={}; internal_results={}
        for r in self.rules['rules']:
            cls=class_map[r['rule_id']]
            if cls=='EXECUTABLE_CONFORMANCE_RULE':
                b=r['invariant_binding']; key=b['invariant_id']+'|'+rfc8785.dumps(b['arguments']).decode();
                if key not in binding_results:binding_results[key]=self.execute(b['invariant_id'],b['arguments'])
                collapse.setdefault(key,[]).append(r['rule_id']); rule_results[r['rule_id']]=binding_results[key]['status'] if class_ok else 'FAIL'
            elif cls=='INTERNAL_DESIGN_INVARIANT':
                c=r['internal_check']; actual=jp(self.resolve(c['subject']),c['pointer']); internal_results[r['rule_id']]='PASS' if actual==c['expected'] else 'FAIL'
            else:rule_results[r['rule_id']]='DEFERRED'
        active=set(self.package['required_invariant_ids']); exact_exec=active==set(invariant_results); package_pass=exact_exec and arity_ok and class_ok and all(x['status']=='PASS' for x in invariant_results.values()) and all(x['status']=='PASS' for x in binding_results.values()) and all(x=='PASS' for x in internal_results.values())
        conf=[r for r in self.rules['rules'] if class_map[r['rule_id']]=='EXECUTABLE_CONFORMANCE_RULE']; deferred=[r for r in self.rules['rules'] if class_map[r['rule_id']]=='DEFERRED_NO_SUBJECT_ARTIFACT']
        counts={'TOTAL_DECLARED_RULES':len(self.rules['rules']),'CONFORMANCE_MEMBER_RULES':len(conf),'INDEPENDENT_CONFORMANCE_BINDINGS':len(binding_results),'CONFORMANCE_BINDINGS_PASS':sum(x['status']=='PASS' for x in binding_results.values()),'CONFORMANCE_BINDINGS_FAIL':sum(x['status']=='FAIL' for x in binding_results.values()),'CONFORMANCE_MEMBER_RULES_PASS':sum(rule_results[r['rule_id']]=='PASS' for r in conf),'CONFORMANCE_MEMBER_RULES_FAIL':sum(rule_results[r['rule_id']]=='FAIL' for r in conf),'INTERNAL_DESIGN_INVARIANTS':len(internal_results),'INTERNAL_PASS':sum(x=='PASS' for x in internal_results.values()),'INTERNAL_FAIL':sum(x=='FAIL' for x in internal_results.values()),'DEFERRED':len(deferred),'PACKAGE_INVARIANTS_REQUIRED':len(active),'PACKAGE_INVARIANTS_EXECUTED':len(invariant_results),'PACKAGE_INVARIANTS_PASS':sum(x['status']=='PASS' for x in invariant_results.values()),'PACKAGE_INVARIANTS_FAIL':sum(x['status']=='FAIL' for x in invariant_results.values()),'UNEVALUABLE_CONFORMANCE_BINDINGS':0,'AMBIGUOUS_CONFORMANCE_BINDINGS':0}
        return {'certificate':'ACCORD-02E4R5R2_PRIMARY','read_only':True,'repository_write_count':0,'active_object_set':sorted((x['kind'],x['id'],x['version']) for x in self.active_normative()),'schema_validation_results':invariant_results['STANDARDS_VALIDATION']['witness'],'reference_edge_set':invariant_results['TYPED_REFERENCE_CLOSURE']['witness'].get('edges',[]),'invariant_results':invariant_results,'invariant_failure_code_map':{k:v['failure_codes'] for k,v in invariant_results.items()},'binding_results':binding_results,'collapse_groups':collapse,'rule_results':rule_results,'internal_results':internal_results,'class_map':class_map,'class_errors':class_errors,'arity_trace':arity_trace,'v013_result':invariant_results['NEGATIVE_REQUIREMENT_MAP_CLOSURE']['witness'].get('result'),'expectation_stability_result':invariant_results['EXPECTATION_STABILITY'],'counts':counts,'overall_pass':package_pass}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=Path(__file__).resolve().parents[3]);a=ap.parse_args()
    try:o=Engine(a.root).run()
    except Exception as e:o={'certificate':'ACCORD-02E4R5R2_PRIMARY','overall_pass':False,'fatal':type(e).__name__+': '+str(e)}
    print(json.dumps(o,sort_keys=True));sys.exit(0 if o.get('overall_pass') else 1)
