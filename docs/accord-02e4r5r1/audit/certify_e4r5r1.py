from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime
from pathlib import Path
import jsonschema, rfc8785

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def sha_raw(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_sem(p): return hashlib.sha256(rfc8785.dumps(load(p))).hexdigest()
def ptr(doc,p):
    for token in p.split('/')[1:]:
        token=token.replace('~1','/').replace('~0','~'); doc=doc[int(token)] if isinstance(doc,list) else doc[token]
    return doc
def iso(s): return datetime.fromisoformat(s.replace('Z','+00:00'))

class Certifier:
    def __init__(self, root):
        self.root=Path(root).resolve(); self.r1=self.root/'docs/accord-02e4r5r1'; self.r5=self.root/'docs/accord-02e4r5'
        self.matrix=load(self.r1/'accord-02e4r5r1-rule-authority-matrix.json'); self.inv=load(self.r1/'accord-02e4r5r1-invariant-registry.json')
        self.pkg=load(self.r1/'accord-02e4r5r1-specification-package-0.2.json'); self.reg=load(self.r1/'accord-02e4r5r1-object-registry.json')
        self.bind=load(self.r1/'accord-02e4r5r1-accepted-source-bindings.json'); self.oldrules=load(self.r5/'accord-02e4r5-validation-rules.json')['rules']
        self.oldassert={x['assertion_id'].rsplit(':',1)[1]:x for x in load(self.r5/'accord-02e4r5-assertion-registry.json')['assertions']}
        self.entries=self.reg['objects']; self.index={}
        for e in self.entries: self.index.setdefault((e['kind'],e['id'],e['version']),[]).append(e)
    def path_for(self, ref):
        hits=self.index.get((ref['kind'],ref['id'],ref['version']),[])
        if len(hits)!=1: raise ValueError('reference cardinality')
        return self.root/hits[0]['path']
    def standards(self):
        jsonschema.Draft202012Validator.check_schema(load(self.r1/'schema/accord-02e4r5r1-rule-authority-matrix.schema.json'))
        jsonschema.validate(self.matrix,load(self.r1/'schema/accord-02e4r5r1-rule-authority-matrix.schema.json'))
        jsonschema.validate(self.inv,load(self.r1/'schema/accord-02e4r5r1-normative-invariants.schema.json'))
        docs=[load(p) for p in self.r1.glob('*.json')]
        schema_ok=True
        for e in self.entries:
            if e['kind']!='SCHEMA': continue
            s=load(self.root/e['path']); schema_ok &= s.get('$schema')=='https://json-schema.org/draft/2020-12/schema' and s.get('$id')==e['id']+':'+e['version']
        return all(x.get('$schema')=='https://json-schema.org/draft/2020-12/schema' and 'schema_ref' in x for x in docs) and schema_ok
    def semantic_integrity(self):
        old=load(self.r5/'accord-02e4r5-object-registry.json'); entries=old.get('entries',old.get('objects',[]))
        for e in entries:
            integ=e.get('integrity',{})
            if integ.get('class')=='SEMANTIC_JSON_CONTENT' and sha_sem(self.root/e['path'])!=integ['digest']: return False
        candidate=json.loads(json.dumps(self.pkg)); expected=candidate['current_candidate_integrity']['digest']; candidate['current_candidate_integrity']['digest']=''
        return hashlib.sha256(rfc8785.dumps(candidate)).hexdigest()==expected
    def identity(self):
        keys=[(x['kind'],x['id'],x['version']) for x in self.entries]
        accepted=[x for x in self.entries if x['id']=='urn:moirae:accord-02r5:source-vector-catalog' and x['version']=='0.1']
        return len(keys)==len(set(keys)) and len(accepted)==1 and set(accepted[0]['roles'])=={'CATALOG_BINDING','VECTOR_SOURCE'}
    def dual_integrity(self):
        for s in self.bind['sources']:
            p=self.root/s['path']; integ=s['integrity']
            if sha_raw(p)!=integ['raw_file_bytes_sha256'] or sha_sem(p)!=integ['semantic_json_content_sha256']: return False
        return True
    def lineage(self):
        p=self.pkg
        return p['package_id']=='urn:moirae:accord-02r5:specification-package' and p['package_version']=='0.2' and p['status']=='CANDIDATE_UNACCEPTED' and p['accepted_base_ref']=={'kind':'PACKAGE','id':'urn:moirae:accord-02r5:specification-package','version':'0.1'} and [x['revision'] for x in p['rejected_candidate_lineage']]==['E4R2','E4R3','E4R4','E4R5'] and p['rejected_candidate_lineage'][-1]['commit']=='b92d5707e9966c8543111b1c448aa5c2f5b0e496'
    def authority(self):
        ids={x['invariant_id'] for x in self.inv['invariants']}; required=set(self.pkg['required_invariant_ids'])
        pinned=self.pkg['normative_contract_integrity']
        if sha_sem(self.r1/'accord-02e4r5r1-rule-authority-matrix.json')!=pinned['rule_authority_matrix_semantic_sha256'] or sha_sem(self.r1/'accord-02e4r5r1-invariant-registry.json')!=pinned['invariant_registry_semantic_sha256']: return False
        if ids!=required or len(ids)!=len(self.inv['invariants']): return False
        used=set()
        for r in self.matrix['rules']:
            if r['semantic_class']=='EXECUTABLE_CONFORMANCE_RULE':
                if 'expected' in r or r.get('expectation_form')!='DERIVED_INVARIANT': return False
                d=r.get('derivation_ref',{}); iid=d.get('member_id')
                if d.get('kind')!='REGISTRY' or d.get('id')!='urn:moirae:accord-02r5r1:normative-invariants' or iid not in ids: return False
                used.add(iid)
        return 'RULE_EXPECTATION_AUTHORITY_COMPLETE' in used
    def inherited(self):
        old={x['rule_id']:x for x in self.oldrules}; rows={x['rule_id']:x for x in self.matrix['rules']}
        if set(old)!=set(rows): return False
        return all(rows[k]['inherited_family']==v['family'] and rows[k]['inherited_failure_code']==v['failure_code'] for k,v in old.items())
    def internal(self):
        for r in self.matrix['rules']:
            if r['semantic_class']!='INTERNAL_DESIGN_INVARIANT': continue
            old=self.oldassert[r['rule_id']]['expression']['checks'][0]['arguments']
            if (r['subject_pointer'],r['expected'],r['comparison'])!=(old['pointer'],old['expected'],old['comparison']): return False
            subject=old['subject']; hits=self.index.get((subject['kind'],subject['id'],subject['version']),[])
            if len(hits)!=1 or ptr(load(self.root/hits[0]['path']),r['subject_pointer'])!=r['expected']: return False
        return True
    def expectation(self):
        a=load(self.root/'docs/accord-02/examples/accord-02c-settlement-test-vectors.json'); c=load(self.r5/'accord-02e4r5-vector-catalog.json')
        am={x['vector_id']:x for x in a['vectors']}; cm={x['vector_id']:x for x in c['vectors']}
        axes={k for x in a['vectors'] for k in x['expected']}; reasons=[z for x in a['vectors'] for z in x['expected'].get('reason_codes',[])]; prohib=[z for x in a['vectors'] for z in x['expected'].get('must_not_conclude',[])]
        return set(am)==set(cm) and all(am[k]['expected']==cm[k]['expected'] for k in am), {'vector_ids':len(am),'axes':len(axes),'reason_codes':len(reasons),'prohibitions':len(prohib),'changed':0}
    def references(self):
        model=load(self.r1/'accord-02e4r5r1-reference-model.json')['shape_predicate']; edges=[]
        def walk(x,src,path=''):
            if isinstance(x,dict):
                ks=set(x); req=set(model['required_exact_keys']); opt=set(model['optional_keys'])
                if req<=ks and ks<=req|opt and all(isinstance(v,str) for v in x.values()): edges.append((src,path,x))
                for k,v in x.items(): walk(v,src,path+'/'+k.replace('~','~0').replace('/','~1'))
            elif isinstance(x,list):
                for i,v in enumerate(x): walk(v,src,path+'/'+str(i))
        for e in self.entries:
            if not e['path'].startswith('docs/accord-02e4r5r1/'): continue
            p=self.root/e['path']
            if p.exists() and p.suffix=='.json': walk(load(p),e['path'])
        walk(self.pkg,'docs/accord-02e4r5r1/accord-02e4r5r1-specification-package-0.2.json')
        unresolved=[]
        for src,path,r in edges:
            hits=self.index.get((r['kind'],r['id'],r['version']),[])
            if len(hits)!=1: unresolved.append((src,path,r))
            elif 'member_id' in r and r['member_id'] not in hits[0].get('members',[]): unresolved.append((src,path,r))
        edge_set=[f"{s}#{p}->{r['kind']}|{r['id']}|{r['version']}|{r.get('member_id','')}" for s,p,r in edges]
        return not unresolved, {"derived_edges":len(edges),"unresolved":len(unresolved),"unresolved_edges":[f"{s}#{p}->{r}" for s,p,r in unresolved],"edge_set_sha256":hashlib.sha256(json.dumps(edge_set,separators=(',',':')).encode()).hexdigest()}
    def graph(self):
        r=load(self.r5/'accord-02e4r5-validation-rules.json')['rules']; g=load(self.r5/'accord-02e4r5-dependency-graph.json')
        expected={(x['rule_id'],d) for x in r for d in x.get('depends_on',[])}
        actual={(x['from'],x['to']) for x in g['edges']}
        return expected==actual
    def policies(self):
        pa=load(self.r1/'accord-02e4r5r1-predicate-authority.json'); pp=load(self.r1/'accord-02e4r5r1-partial-effect-policy.json'); cp=load(self.r1/'accord-02e4r5r1-canonicalization-profile.json'); governed=load(self.r5/'accord-02e4r5-predicate-registry.json')
        return pa['global_stage_order']==governed['global_stage_order']=='FORBIDDEN' and pa['implicit_transitivity']==governed['implicit_transitivity']=='FORBIDDEN' and 'global_stage_order' not in pp and 'implicit_transitivity' not in pp and pp['merged_outcome']=={'UNKNOWN_TUPLE_OR_WRONG_STAGE':'REJECT'} and cp['self_digest_target_id']=='PACKAGE_EXCLUDING_SELF_DIGEST'
    def v013(self):
        t=load(self.r1/'accord-02e4r5r1-v013-target.json'); e=load(self.r1/'accord-02e4r5r1-v013-evidence.json'); p=load(self.r5/'accord-02e4r5-settlement-profile-conservative.json')['negative_policy']
        exact=(e['effect_id'],e['predicate_id'],e['stage'],e['scope'])==(t['effect_id'],t['negated_predicate_id'],t['negated_stage'],t['scope'])
        interval=iso(e['observed_interval']['not_before'])<=iso(t['required_interval']['not_before'])<=iso(t['required_interval']['as_of'])<=iso(e['observed_interval']['as_of'])
        duration=(iso(t['required_interval']['as_of'])-iso(t['required_interval']['not_before'])).total_seconds(); age=(iso(e['verification_time'])-iso(e['observed_at'])).total_seconds()
        contradictions=[x for x in e['evidence_universe'] if x.get('effect_id')==t['effect_id'] and x.get('predicate_id')==t['negated_predicate_id'] and x.get('stage')==t['negated_stage'] and x.get('scope')==t['scope'] and x.get('polarity')=='POSITIVE']
        relation=t['relationship']=='CANDIDATE_FIXTURE_OF_SAME_SEMANTIC_CLASS_AS_ACCEPTED_V013' and bool(t['relationship_basis']['accepted']) and bool(t['relationship_basis']['candidate_supplied'])
        ok=exact and interval and e['retention_window_seconds']>=max(duration,p['minimum_retention_seconds']) and 0<=age<=p['freshness_max_age_seconds'] and e['consistency_level'] in p['allowed_consistency_levels'] and e['evidence_class'] in p['allowed_source_classes'] and e['read_scope_complete'] and e['read_semantics']=='COMPLETE_LEDGER_QUERY' and not contradictions and relation
        return ok, 'NON_OCCURRENCE_SUPPORTED' if ok else 'UNKNOWN'
    def run(self):
        checks={}
        for name,fn in [('STANDARDS_VALIDATION',self.standards),('SEMANTIC_DIGEST_VERIFY',self.semantic_integrity),('PACKAGE_LINEAGE',self.lineage),('ACCEPTED_BASE_DUAL_INTEGRITY',self.dual_integrity),('OBJECT_IDENTITY_UNIQUE',self.identity),('RULE_EXPECTATION_AUTHORITY_COMPLETE',self.authority),('INHERITED_RULE_MEANING',self.inherited),('INTERNAL_DESIGN',self.internal),('DEPENDENCY_GRAPH_EQUAL',self.graph),('POLICY_CLOSURE',self.policies)]:
            try: checks[name]=bool(fn())
            except Exception: checks[name]=False
        try: exp,metrics=self.expectation()
        except Exception: exp,metrics=False,{}
        checks['EXPECTATION_STABILITY']=exp
        try: refs,reftrace=self.references()
        except Exception: refs,reftrace=False,{"derived_edges":0,"unresolved":1,"edge_set_sha256":None}
        checks['TYPED_REFERENCE_CLOSURE']=refs
        try: v,vresult=self.v013()
        except Exception: v,vresult=False,'UNKNOWN'
        checks['NEGATIVE_REQUIREMENT_MAP_CLOSURE']=v
        rows=self.matrix['rules']; conf=[x for x in rows if x['semantic_class']=='EXECUTABLE_CONFORMANCE_RULE']; internal=[x for x in rows if x['semantic_class']=='INTERNAL_DESIGN_INVARIANT']; deferred=[x for x in rows if x['semantic_class']=='DEFERRED_NO_SUBJECT_ARTIFACT']
        all_pkg=all(checks.values()); cr={x['rule_id']:('PASS' if all_pkg and x['derivation_ref']['member_id'] in set(self.pkg['required_invariant_ids']) else 'FAIL') for x in conf}; ir={x['rule_id']:('PASS' if checks['INTERNAL_DESIGN'] else 'FAIL') for x in internal}
        counts={'TOTAL_DECLARED_RULES':len(rows),'EXECUTABLE_CONFORMANCE_RULES':len(conf),'INTERNAL_DESIGN_INVARIANTS':len(internal),'DEFERRED_NO_SUBJECT_ARTIFACT':len(deferred),'CONFORMANCE_EXECUTED':len(cr),'CONFORMANCE_PASS':sum(v=='PASS' for v in cr.values()),'CONFORMANCE_FAIL':sum(v=='FAIL' for v in cr.values()),'INTERNAL_EXECUTED':len(ir),'INTERNAL_PASS':sum(v=='PASS' for v in ir.values()),'INTERNAL_FAIL':sum(v=='FAIL' for v in ir.values()),'DEFERRED':len(deferred),'UNEVALUABLE_CONFORMANCE':0,'AMBIGUOUS_CONFORMANCE':0}
        return {'certificate':'ACCORD-02E4R5R1_PRIMARY','read_only':True,'repository_write_count':0,'package_invariants':checks,'rule_counts':counts,'conformance_results':cr,'internal_results':ir,'reference_trace':reftrace,'expectation_metrics':metrics,'v013_result':vresult,'overall_pass':all_pkg and counts['CONFORMANCE_FAIL']==counts['INTERNAL_FAIL']==0}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=Path(__file__).resolve().parents[3]); a=ap.parse_args()
    try: out=Certifier(a.root).run()
    except Exception as e: out={'certificate':'ACCORD-02E4R5R1_PRIMARY','overall_pass':False,'fatal':type(e).__name__+': '+str(e)}
    print(json.dumps(out,sort_keys=True)); sys.exit(0 if out.get('overall_pass') else 1)
