"""Compare all four central perturbation sizes without changing their gates."""
import json,time,traceback
from decimal import localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_joint_charge_response import bank,D
from check_joint_charge_response_fine import bank as fine_bank
from joint_cycles_analysis import require

def check():
    names=['evidence/voice_joint_charge_response_native01.json','evidence/voice_joint_charge_response_fine_native03.json'];banks=[decoder(json.loads((ROOT/n).read_text())) for decoder,n in zip([bank,fine_bank],names)];records=[]
    floors=np.array([1e-10 if 98<=k<133 or k>=200 else 1e-6 for k in range(218)])[:,None]
    for id in range(2):
        matrices=[np.column_stack([cols[id,k] for k in range(18)]) for roots,cols in banks];require(np.array_equal(*matrices),'identical analytic tangent across callers');expected=matrices[0]
        for (roots,cols),pair in zip(banks,[[.001,.0005],[.000125,.0000625]]):
            for h in pair:
                columns=[]
                for k in range(18):
                    q=[next(r for r in roots if r['label']=='RESPONSE_PERTURB' and r['id']==id and r['index']==k and r['h']==sign*h) for sign in [-1,1]]
                    columns.append([float((b-a)/(D(2)*D(h))) for a,b in zip(q[0]['state']+q[0]['current'],q[1]['state']+q[1]['current'])])
                fd=np.column_stack(columns);error=np.abs(fd-expected);ratio=error/(floors+3e-4*np.abs(expected));row,col=np.unravel_index(np.argmax(ratio),ratio.shape);passed=float(ratio[row,col])<=1
                if h<=.000125:require(passed,'fine central gate')
                records.append(dict(id=id,half_perturbation_v=h,gate_passed=passed,max_gate_ratio=float(ratio[row,col]),worst_row=int(row),worst_column=int(col),observed_response=float(fd[row,col]),analytic_response=float(expected[row,col]),worst_response_unit='A/V' if 98<=row<133 or row>=200 else 'V/V',max_voltage_error_v_per_v=float(np.max(error[[k for k in range(200) if not 98<=k<133]])),max_current_error_a_per_v=float(np.max(error[[k for k in range(218) if 98<=k<133 or k>=200]]))))
    return dict(records=records,analytic_tangents_bit_identical=True,coarse_response_admitted=False,fine_response_gates_passed=True,new_root_searches=0,new_trajectories=0)

def main():
    out='evidence/voice_joint_charge_response_refinement02.json';require(not (ROOT/out).exists(),'exclusive refinement receipt')
    names=['tools/check_joint_charge_response_refinement.py','tools/check_joint_charge_response.py','tools/check_joint_charge_response_fine.py','tools/check_joint_charge_seed.py','tools/check_joint_reference.py','tools/joint_cycles_analysis.py','docs/VOZ_CARGAS_RESPUESTA_PROTOCOLO.md','docs/VOZ_CARGAS_RESPUESTA_FINA_PROTOCOLO.md','evidence/voice_joint_charge_response_native01.json','evidence/voice_joint_charge_response_fine_native03.json']
    before={n:sha(ROOT/n) for n in names};r=dict(schema='rf-d/joint-charge-response-refinement/v1',passed=False,source_sha256=before);start=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check())
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_charge_response_refinement.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check()
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==r['source_sha256_after'],'unchanged refinement sources');r['wall_s']=time.perf_counter()-start;write(out,r);print('CHARGE_RESPONSE_REFINEMENT',r['passed'],r.get('failure',''),[(x['id'],x['half_perturbation_v'],x['max_gate_ratio']) for x in r.get('records',[])],flush=True)

if __name__=='__main__':main()
