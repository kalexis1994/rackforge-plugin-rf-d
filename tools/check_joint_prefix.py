"""Independent selected equations and exact initial/same-clock prefix checks."""
import argparse,json,re,struct,sys,time,traceback
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,trace,checkpoints,checkpoint,compare
from check_joint_cycles import check as selected_check
from chain_charge_reference import CAPS
from check_joint_reference import ci,D

def check(native):
    require(native['passed'] and len(native['profiles'])==2,'complete native prefix')
    original=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text());lines=original['commands'][-1]['stdout'].splitlines();i=next(i for i,line in enumerate(lines) if line.startswith('STARTUP_ROOT,0,'));root=struct.pack('<400d',*map(float,lines[i+1].split(',')[1:]))
    all_points=[];profiles=[]
    for p in native['profiles']:
        directory=Path(p['command'][3]);points=checkpoints(directory/'checkpoints.bin');rows=trace(directory/'trace.bin');final=checkpoint((directory/'final.ckp').read_bytes())
        require([v['ticks'] for v in points]==[0,131072000,262144000] and int(rows[-1]['ticks'])==262144000,'exact duration and anchors')
        require(struct.pack('<400d',*points[0]['high'],*points[0]['low'])==root,'bit exact conditioned root')
        require(points[-1]['raw_sha256']==final['raw_sha256'],'final checkpoint identity');require(points[0]['maximum']==p['maximum_half_ticks'],'declared profile')
        summary=next(s for s in p['stderr'].splitlines() if s.startswith('SUMMARY,'));fields=dict(v.split('=',1) for v in summary.split(',')[1:]);require(int(fields['ticks'])==262144000 and int(fields['intervals'])*2==len(rows) and int(fields['restore_replays'])==1,'interval/restore counts')
        a,b=points[0],points[-1];delta=D(b['high'][43])+D(b['low'][43])-D(a['high'][43])-D(a['low'][43]);require(abs(delta-D(float(fields['delta_ramp'])))<=D(2e-9),'compensated endpoint charge change')
        charge,absolute=D(float(fields['charge'])),D(float(fields['absolute']));require(absolute>0,'current integral positive');balance=abs(charge+D(1e-8)*delta)/absolute;require(balance<=D(.002),'native quadrature plus independently decoded C1 endpoint balance')
        caps=[]
        for k,(left,right,farad) in enumerate([*CAPS,(67,7,10e-6)]):
            right=right if isinstance(right,int) else 66 if right=='BUS' else None
            def voltage(p):return D(p['high'][ci(left)])+D(p['low'][ci(left)])-(D(p['high'][ci(right)])+D(p['low'][ci(right)]) if right is not None else Decimal(0))
            before,after=voltage(a),voltage(b);caps.append(dict(index=k,a=left,b=right,capacitance_f=farad,initial_v=str(before),final_v=str(after),change_v=str(after-before),charge_change_c=str(D(farad)*(after-before))))
        profiles.append(dict(maximum_half_ticks=p['maximum_half_ticks'],accepted_intervals=len(rows)//2,published_half_steps=len(rows),reset_crossings=int(fields['crossings']),restore_replays=1,c1_charge_integral_c=str(charge),c1_absolute_current_integral_c=str(absolute),c1_endpoint_delta_v=str(delta),c1_balance_relative=str(balance),native_balance_relative=fields['balance'],capacitor_change=caps,extrema={n:dict(min_v=float(min(rows[n])),max_v=float(max(rows[n]))) for n in ['ramp','saw','tri','pulse','bus','j7']},maximum_lte=float(max(rows['lte'])),max_bus_kcl_a=float(max(abs(rows['bus_kcl']))),max_c1_kcl_a=float(max(abs(rows['c1_kcl'])))));all_points.append(points)
    independent=selected_check(native['profiles']);require(len(independent['root_checks'])==12 and sum(v['rows'] for v in independent['root_checks'])==4800,'24 independent selected stage points')
    require(len(independent['temporal_checks'])==4 and len(independent['current_checks'])==8,'selected time/current coverage')
    return dict(profiles=profiles,same_clock=compare(*all_points),initial_root_bit_identical=True,**independent,native_candidate_points_used=True,independent_root_search=False,initialized_cycle_admitted=False,steady_periodicity_admitted=False,global_settling_bound=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args();out=ROOT/f'evidence/voice_joint_prefix_reference{a.attempt:02d}.json';require(not out.exists(),'new receipt');name='evidence/voice_joint_prefix_native01.json';native=json.loads((ROOT/name).read_text())
    names={name,'evidence/voice_joint_startup_native01.json','docs/VOZ_PREFIJO_CONDICIONADO_PROTOCOLO.md','tools/check_joint_prefix.py'}
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            p=Path(path).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/joint-prefix-reference/v1',passed=False,source_sha256=before,new_audio=False,new_spice_processes=0);s=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check(native))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_prefix.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['wall_s']=time.perf_counter()-s;r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==r['source_sha256_after'],'unchanged analysis sources');out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('PREFIX_REFERENCE',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
