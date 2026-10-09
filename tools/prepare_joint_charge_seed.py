"""Freeze lineage, preserve a documentation defect, and derive charge targets."""
import base64,json,re,subprocess
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_joint_reference import decode,D,ci
from chain_charge_reference import CAPS
from check_joint_history_cycles import GROUPS
from joint_cycles_analysis import trace,TICK

def main():
    previous='evidence/voice_joint_conditioned_cycles_tests01.json'
    old=json.loads((ROOT/previous).read_text())
    assert old['passed']
    for key in ['source_sha256','private_input_sha256']:
        for n,h in old[key].items():assert sha(ROOT/n)==h,n
    names=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','.gitattributes','docs/VOZ_CICLOS_CONDICIONADOS_RESULTADOS.md']
    write('evidence/voice_joint_charge_seed_before01.json',dict(schema='rf-d/joint-charge-seed-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    path=ROOT/names[-1];text=path.read_text(encoding='utf8');broken=[]
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if not (path.parent/link).exists():broken.append(link)
    assert len(broken)==4,broken
    write('evidence/voice_joint_charge_seed_links_before01.json',dict(schema='rf-d/document-link-defect/v1',passed=False,source_sha256=sha(path),broken_targets=broken,replay_broken_targets=[link for link in broken if not (path.parent/link).exists()],cause='Prior formatting regex inserted spaces before numeric suffixes and component numbers; previous QA did not audit RF local Markdown links.',preserved_original_in='evidence/voice_joint_charge_seed_before01.json'))
    fixed=text.replace('_native 01.json','_native01.json').replace('_reference 01.json','_reference01.json').replace('_tests 01.json','_tests01.json')
    fixed=re.sub(r'\b(C|J|R|CA) (?=[0-9])',r'\1',fixed)
    path.write_text(fixed,encoding='utf8',newline='\n')
    data=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text());lines=data['commands'][-1]['stdout'].splitlines()
    with localcontext() as ctx:
        ctx.prec=100
        initial=decode(lines[lines.index('INITIAL_HISTORY')+1]);targets=[];mean=[];private={}
        for maximum,names in GROUPS.items():
            rows=[]
            for n in names:
                p=ROOT/n/'trace.bin';assert sha(p)==old['private_input_sha256'][p.relative_to(ROOT).as_posix()]
                rows.append(trace(p,start_ticks=0 if not rows else int(rows[-1][-1]['ticks'])))
                private[p.relative_to(ROOT).as_posix()]=sha(p)
            rows=np.concatenate(rows);events=np.flatnonzero((rows['ramp'][:-1]<-2)&(rows['ramp'][1:]>=-2))+1;assert len(events)==2
            selected=rows[events[0]:events[1]+1];dt=np.diff(selected['ticks']).astype(float)*TICK
            value=float(np.sum(dt*(selected['saw'][1:]+selected['saw'][:-1])*.5)/np.sum(dt))
            mean.append(dict(maximum_half_ticks=maximum,saw_endpoint_trapezoid_mean_v=value,begin_ticks=int(selected[0]['ticks']),end_ticks=int(selected[-1]['ticks']),endpoint_quadrature_is_seed_heuristic=True,not_radau_integral=True))
        for mode in [0,1]:
            row=[];volts=[]
            for k,(a,b,c) in enumerate([*CAPS,(67,7,10e-6)]):
                b=b if isinstance(b,int) else 66 if b=='BUS' else None
                voltage=initial[ci(a)]-(initial[ci(b)] if b is not None else Decimal(0))
                if mode==1 and k==5:voltage=initial[ci(6)]-D(.5)*D(mean[1]['saw_endpoint_trapezoid_mean_v'])
                hi=float(voltage);lo=float(voltage-D(hi));row.extend([hi,lo]);volts.append(str(voltage))
            targets.append(dict(id=mode,voltages_decimal=volts,packed_pairs=row))
        file=ROOT/'evidence/voice_joint_charge_seed_targets01.txt';assert not file.exists()
        file.write_text('\n'.join(' '.join(format(v,'.17e') for v in t['packed_pairs']) for t in targets)+'\n',encoding='utf8',newline='\n')
        write('evidence/voice_joint_charge_seed_targets01.json',dict(schema='rf-d/joint-charge-targets/v1',passed=True,source_sha256={'evidence/voice_joint_startup_native01.json':sha(ROOT/'evidence/voice_joint_startup_native01.json'),'tools/prepare_joint_charge_seed.py':sha(ROOT/'tools/prepare_joint_charge_seed.py')},private_input_sha256=private,mean_observations=mean,mean_refinement_difference_v=abs(mean[0]['saw_endpoint_trapezoid_mean_v']-mean[1]['saw_endpoint_trapezoid_mean_v']),targets=targets,targets_sha256=sha(file),physical_fidelity=False,steady_periodicity_admitted=False))
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_charge_seed_runner.rs text eol=lf\n')
    print('CHARGE_SEED_PREPARED',len(old['source_sha256']),len(old['private_input_sha256']),mean,flush=True)
if __name__=='__main__':main()
