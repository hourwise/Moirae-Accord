from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def call(script):
    p=subprocess.run([sys.executable,str(ROOT/script),'--root',str(ROOT)],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'});return p.returncode,json.loads(p.stdout.strip().splitlines()[-1])
def status_map(x):return {k:(v['status'] if isinstance(v,dict) and 'status' in v else v) for k,v in x.items()}
def external_edges():
    reg=json.loads((ROOT/'docs/accord-02e4r5r2/object-registry.json').read_text());model=json.loads((ROOT/'docs/accord-02e4r5r2/reference-model.json').read_text())['shape_predicate'];found=[]
    def scan(v,src,p=''):
        if isinstance(v,dict):
            keys=set(v);req=set(model['required_keys']);opt=set(model['optional_keys'])
            if req<=keys and keys<=req|opt and all(isinstance(x,str) for x in v.values()):found.append([src['kind'],src['id'],src['version'],p,v['kind'],v['id'],v['version'],v.get('member_id','')])
            for k,x in v.items():scan(x,src,p+'/'+k.replace('~','~0').replace('/','~1'))
        elif isinstance(v,list):
            for i,x in enumerate(v):scan(x,src,p+'/'+str(i))
    for src in reg['objects']:
        if src['status']=='ACTIVE' and src['classification']=='NORMATIVE':scan(json.loads((ROOT/src['path']).read_text()),src)
    return sorted({tuple(x) for x in found})
pc,p=call('docs/accord-02e4r5r2/audit/certify_e4r5r2.py');ic,i=call('docs/accord-02e4r5r2/audit/independent_evaluate_e4r5r2.py');third=[list(x) for x in external_edges()]
comparisons={
'active_object_set':p.get('active_object_set')==i.get('active_object_set'),
'schema_validation_result_set':status_map(p.get('schema_validation_results',{}))==i.get('schema_validation_results'),
'reference_edge_set':p.get('reference_edge_set')==i.get('reference_edge_set')==third,
'invariant_result_map':status_map(p.get('invariant_results',{}))==i.get('invariant_results'),
'invariant_failure_code_map':p.get('invariant_failure_code_map')==i.get('invariant_failure_code_map'),
'binding_result_map':status_map(p.get('binding_results',{}))==i.get('binding_results'),
'rule_result_map':p.get('rule_results')==i.get('rule_results'),
'internal_result_map':p.get('internal_results')==i.get('internal_results'),
'class_map':p.get('class_map')==i.get('class_map'),
'v013_result':p.get('v013_result')==i.get('v013_result'),
'expectation_stability_result':p.get('expectation_stability_result',{}).get('status')==i.get('invariant_results',{}).get('EXPECTATION_STABILITY') and p.get('expectation_stability_result',{}).get('witness')==i.get('expectation_stability_result')}
out={'release_verifier':'ACCORD-02E4R5R2','primary_pass':pc==0 and p.get('overall_pass'),'independent_pass':ic==0 and i.get('overall_pass'),'comparisons':comparisons,'derived_reference_edges':len(third),'counts':p.get('counts'),'overall_pass':pc==ic==0 and p.get('overall_pass') and i.get('overall_pass') and all(comparisons.values())}
print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['overall_pass'] else 1)
