from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
def invoke(script):
    p=subprocess.run([sys.executable,str(ROOT/script),'--root',str(ROOT)],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    return p.returncode,json.loads(p.stdout.strip().splitlines()[-1])

pa,p=invoke('docs/accord-02e4r5r1/audit/certify_e4r5r1.py'); ia,i=invoke('docs/accord-02e4r5r1/audit/independent_evaluate_e4r5r1.py')
catalog=json.loads((ROOT/'docs/accord-02e4r5/accord-02e4r5-vector-catalog.json').read_text(encoding='utf-8'))
outcomes={x['expected']['occurrence'] for x in catalog['vectors']}
reasons={r for x in catalog['vectors'] for r in x['expected'].get('reason_codes',[])}
positive={'resource_created_or_bound_receipt':'BOUND_PROVIDER_EFFECT_RECEIPT' in reasons,'corroborated_occurrence':'CORROBORATED_BY_OBSERVER_DISTINCT_SOURCE' in reasons,'partial_effect':'PARTIAL_EFFECT' in outcomes,'non_occurrence_supported':'NON_OCCURRENCE_SUPPORTED' in outcomes,'not_all_unknown':outcomes!={'UNKNOWN'}}
agreement=p.get('rule_counts')==i.get('rule_counts') and p.get('conformance_results')==i.get('conformance_results') and p.get('internal_results')==i.get('internal_results') and p.get('reference_trace',{}).get('edge_set_sha256')==i.get('reference_trace',{}).get('edge_set_sha256')
result={'release_verification':'ACCORD-02E4R5R1','primary_pass':pa==0 and p.get('overall_pass'),'independent_pass':ia==0 and i.get('overall_pass'),'exact_result_agreement':agreement,'reference_edge_set_agreement':p.get('reference_trace')=={**i.get('reference_trace',{}),'unresolved_edges':[]} or p.get('reference_trace',{}).get('edge_set_sha256')==i.get('reference_trace',{}).get('edge_set_sha256'),'expectation_stability':p.get('expectation_metrics'),'positive_usefulness':positive}
result['overall_pass']=all([result['primary_pass'],result['independent_pass'],agreement,all(positive.values()),result['expectation_stability']=={'vector_ids':23,'axes':13,'reason_codes':30,'prohibitions':31,'changed':0}])
print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if result['overall_pass'] else 1)
