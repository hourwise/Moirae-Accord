from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve(); PRIMARY='docs/accord-02e4r5r1/audit/certify_e4r5r1.py'; INDEPENDENT='docs/accord-02e4r5r1/audit/independent_evaluate_e4r5r1.py'
MATRIX='docs/accord-02e4r5r1/accord-02e4r5r1-rule-authority-matrix.json'; INVARIANTS='docs/accord-02e4r5r1/accord-02e4r5r1-invariant-registry.json'; REGISTRY='docs/accord-02e4r5r1/accord-02e4r5r1-object-registry.json'; PACKAGE='docs/accord-02e4r5r1/accord-02e4r5r1-specification-package-0.2.json'
AUTH='docs/accord-02e4r5r1/accord-02e4r5r1-predicate-authority.json'; PRED='docs/accord-02e4r5/accord-02e4r5-predicate-registry.json'; CANON='docs/accord-02e4r5r1/accord-02e4r5r1-canonicalization-profile.json'; TARGET='docs/accord-02e4r5r1/accord-02e4r5r1-v013-target.json'; EVIDENCE='docs/accord-02e4r5r1/accord-02e4r5r1-v013-evidence.json'; PARTIAL='docs/accord-02e4r5r1/accord-02e4r5r1-partial-effect-policy.json'

def read(root,rel): return json.loads((root/rel).read_text(encoding='utf-8'))
def write(root,rel,obj,newline='\n'): (root/rel).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline=newline)
def run_one(root,script):
    cp=subprocess.run([sys.executable,str(root/script),'--root',str(root)],text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    try: data=json.loads(cp.stdout.strip().splitlines()[-1])
    except Exception: return False,{'fatal':'invalid evaluator output','stderr':cp.stderr[-300:]}
    return cp.returncode==0 and data.get('overall_pass') is True,data
def both(root):
    a,ad=run_one(root,PRIMARY); b,bd=run_one(root,INDEPENDENT)
    agreement=ad.get('rule_counts')==bd.get('rule_counts') and ad.get('conformance_results')==bd.get('conformance_results') and ad.get('internal_results')==bd.get('internal_results') and ad.get('reference_trace',{}).get('edge_set_sha256')==bd.get('reference_trace',{}).get('edge_set_sha256')
    return a and b and agreement,{'primary_pass':a,'independent_pass':b,'agreement':agreement,'primary':ad,'independent':bd}
def row(doc,id): return next(x for x in doc['rules'] if x['rule_id']==id)
def entry(doc,id): return next(x for x in doc['objects'] if x['id']==id)

def mutate_json(rel,fn):
    def action(root):
        x=read(root,rel); fn(x); write(root,rel,x)
    return action
def whitespace(rel):
    def action(root): (root/rel).write_bytes((root/rel).read_bytes()+b' ')
    return action
def crlf_all(root):
    for p in (root/'docs/accord-02e4r5r1').rglob('*.json'):
        text=p.read_text(encoding='utf-8').replace('\r\n','\n'); p.write_text(text,encoding='utf-8',newline='\r\n')

def cases():
    return [
      ('subject_only_mutation',mutate_json(PRED,lambda x:x.__setitem__('global_stage_order','ALLOWED')),False),
      ('old_subject_inline_literal_co_mutation',mutate_json(MATRIX,lambda x:(row(x,'E4R1-ENT-001').__setitem__('expected','ALLOWED'),row(x,'E4R1-ENT-001').__setitem__('subject_pointer','/global_stage_order'))),False),
      ('authority_only_mutation',mutate_json(AUTH,lambda x:x.__setitem__('global_stage_order','ALLOWED')),False),
      ('authority_disagreement',mutate_json(PRED,lambda x:x.__setitem__('implicit_transitivity','ALLOWED')),False),
      ('pointer_redirection',mutate_json(MATRIX,lambda x:(row(x,'LIN-001').__setitem__('subject_pointer','/object_version'),row(x,'LIN-001').__setitem__('expected','0.2'))),False),
      ('subject_authority_swap',mutate_json(MATRIX,lambda x:row(x,'LIN-001').__setitem__('derivation_ref',{'kind':'CONTRACT','id':'urn:moirae:accord-02r5:validation-rules','version':'0.2'})),False),
      ('governing_authority_removal',mutate_json(MATRIX,lambda x:row(x,'LIN-001').pop('derivation_ref')),False),
      ('governing_authority_retarget',mutate_json(MATRIX,lambda x:row(x,'LIN-001')['derivation_ref'].__setitem__('member_id','NOT_AN_INVARIANT')),False),
      ('derived_invariant_procedure_mutation',mutate_json(INVARIANTS,lambda x:x['invariants'][0].__setitem__('procedure','CARDINALITY_EQUAL')),False),
      ('package_invariant_deletion',mutate_json(INVARIANTS,lambda x:x['invariants'].pop()),False),
      ('duplicate_identity',mutate_json(REGISTRY,lambda x:x['objects'].append(dict(x['objects'][0]))),False),
      ('reference_dangling',mutate_json(AUTH,lambda x:x['governing_ref'].__setitem__('id','urn:missing')),False),
      ('reference_alias_collision',mutate_json(REGISTRY,lambda x:x['objects'].append({**x['objects'][0],'path':x['objects'][1]['path']})),False),
      ('source_catalog_raw_byte_only_mutation',whitespace('docs/accord-02/examples/accord-02c-settlement-test-vectors.json'),False),
      ('source_catalog_semantic_mutation',mutate_json('docs/accord-02/examples/accord-02c-settlement-test-vectors.json',lambda x:x['vectors'][0].__setitem__('vector_id','MUTATED')),False),
      ('accepted_base_raw_byte_mutation',whitespace('docs/accord-02/accord-02r5-specification-package.json'),False),
      ('accepted_base_semantic_mutation',mutate_json('docs/accord-02/accord-02r5-specification-package.json',lambda x:x.__setitem__('package_version','MUTATED')),False),
      ('lf_transformation',lambda root:None,True),
      ('crlf_transformation',crlf_all,True),
      ('lineage_mutation',mutate_json(PACKAGE,lambda x:x['rejected_candidate_lineage'][-1].__setitem__('commit','0'*40)),False),
      ('canonicalization_target_mutation',mutate_json(CANON,lambda x:x.__setitem__('self_digest_target_id','ENTIRE_PACKAGE')),False),
      ('v013_relationship_mutation',mutate_json(TARGET,lambda x:x.__setitem__('relationship','EXECUTABLE_REALIZATION_OF_EXACT_ACCEPTED_DECLARATIVE_V013')),False),
      ('v013_policy_attack',mutate_json(EVIDENCE,lambda x:x.__setitem__('read_scope_complete',False)),False),
      ('executable_to_internal_reclassification_attack',mutate_json(MATRIX,lambda x:row(x,'LIN-001').__setitem__('semantic_class','INTERNAL_DESIGN_INVARIANT')),False),
      ('internal_to_deferred_attack',mutate_json(MATRIX,lambda x:row(x,'BND-001').__setitem__('semantic_class','DEFERRED_NO_SUBJECT_ARTIFACT')),False),
      ('conformance_rule_without_authority',mutate_json(MATRIX,lambda x:row(x,'LIN-002').pop('derivation_ref')),False),
      ('partial_effect_policy_attack',mutate_json(PARTIAL,lambda x:x['merged_outcome'].__setitem__('UNKNOWN_TUPLE_OR_WRONG_STAGE','UNKNOWN')),False),
    ]

def main(root,smoke=False):
    root=Path(root).resolve()
    if smoke:
        ok,detail=both(root); print(json.dumps({'mode':'smoke','pass':ok,'details':detail},sort_keys=True)); return 0 if ok else 1
    with tempfile.TemporaryDirectory(prefix='accord-e4r5r1-falsify-') as td:
        export=Path(td)/'export'; shutil.copytree(root,export,ignore=shutil.ignore_patterns('.git','.pytest_cache','__pycache__'))
        results=[]
        for name,mutation,expected_pass in cases():
            case=Path(td)/name; shutil.copytree(export,case); mutation(case); passed,detail=both(case); gate=(passed and detail['agreement']) if expected_pass else (not detail['primary_pass'] and not detail['independent_pass']); results.append({'case':name,'expected_pass':expected_pass,'actual_pass':passed,'pass':gate,'primary_pass':detail['primary_pass'],'independent_pass':detail['independent_pass'],'agreement':detail['agreement']}); shutil.rmtree(case)
        cp=subprocess.run([sys.executable,str(export/'docs/accord-02e4r5r1/audit/falsify_e4r5r1.py'),'--root',str(export),'--smoke'],text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        results.append({'case':'clean_export_without_git_or_sibling_worktrees_falsifier_execution','expected_pass':True,'actual_pass':cp.returncode==0,'pass':cp.returncode==0})
        (export/PRIMARY).unlink(); (export/'docs/accord-02e4r5r1/_build_candidate.py').unlink()
        independent_ok,_=run_one(export,INDEPENDENT)
        results.append({'case':'delete_builder_and_primary_independent_derivation','expected_pass':True,'actual_pass':independent_ok,'pass':independent_ok})
    out={'falsifier':'ACCORD-02E4R5R1_REAL_SYSTEM','real_evaluator_subprocesses':True,'case_count':len(results),'passed':sum(x['pass'] for x in results),'failed':[x for x in results if not x['pass']],'cases':results,'overall_pass':all(x['pass'] for x in results)}
    print(json.dumps(out,sort_keys=True)); return 0 if out['overall_pass'] else 1

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=HERE.parents[3]); ap.add_argument('--smoke',action='store_true'); a=ap.parse_args(); raise SystemExit(main(a.root,a.smoke))
