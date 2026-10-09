"""Independent selected-stage equations, LTE and C1 terminal observations.
Native candidates are intentional. Current gate 2e-11 A inherits the nodal
oracle current gate; Decimal100 includes the full high/low terminal state.
No independent roots or independent all-stage trajectory integration claimed.
"""
import argparse,json,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from check_joint_reference import evaluate,decode,D,N,B
from vco1_increment_devices import bjt_reference,jfet_reference
from joint_cycles_analysis import trace,checkpoints,require,TICK

def bank(path):
    lines=path.read_text().splitlines();out=[]
    for i,line in enumerate(lines):
        if line.startswith('JOINT_ROOT,'):
            _,mask,h,res,corr=line.split(',')
            require(all(s.startswith('JOINT_STATE,') for s in lines[i+1:i+6]),'five selected states')
            states=[decode(s) for s in lines[i+1:i+6]]
            raw=list(map(float,lines[i+5].split(',')[1:]))
            out.append(((int(mask),float(h),*states),raw))
    require(len(out)>0 and len(out)%3==0,'full/mid/end bank')
    return out

def currents(case):
    _,h,old,da,db,sa,sb=case
    def device(s,history,k):
        nodes=([43,33,18,None],[43,21,None,None],[5,43,4])[k]
        lift=lambda state:[Decimal(0) if n is None else state[n] for n in nodes]
        if k<2:
            v=bjt_reference(1 if k==0 else -1,lift(s),lift(history),h)
            return v[0],v[4]
        v=jfet_reference(lift(s),lift(history),h)
        return v[1],v[4]
    result=[]
    for k in range(3):
        static=[];dynamic=[]
        for s in [sa,sb]:
            f,e=device(s,old,k);static.append(f);dynamic.append(e-f)
        result.append(static[1]+B[1][0]*dynamic[0]+B[1][1]*dynamic[1])
    return result

def check(parts):
    roots=[];temporal=[];observations=[];inputs={}
    for p in parts:
        directory=Path(p['command'][3]);points=checkpoints(directory/'checkpoints.bin')
        rows=trace(directory/'trace.bin',start_ticks=points[0]['ticks']);cases=bank(directory/'selected.txt')
        for n in ['selected.txt','trace.bin','checkpoints.bin']:
            path=(directory/n).relative_to(ROOT).as_posix();inputs[path]=sha(ROOT/path)
        for case,raw in cases:roots.append(dict(segment=directory.relative_to(ROOT).as_posix(),**evaluate(case)))
        for i in range(0,len(cases),3):
            full,mid,end=[c[0] for c in cases[i:i+3]]
            require(full[0]==mid[0]==end[0]==0 and full[1]==2*mid[1] and mid[1]==end[1],'nominal selected clocks')
            require(full[2]==mid[2] and mid[-1]==end[2],'shared history and chained midpoint')
            ratio=max(abs(a-b)/D(2e-9 if 98<=k<133 else 2e-6) for k,(a,b) in enumerate(zip(full[-1],end[-1])))
            require(ratio<=1,'selected Decimal LTE')
            temporal.append(dict(full_h_s=full[1],error_ratio_decimal=str(ratio)))
            for case,raw in cases[i+1:i+3]:
                found=np.ones(len(rows),dtype=bool)
                for name,k in [('ramp',43),('saw',46),('tri',54),('pulse',44),('bus',12),('cursor',39),('j7',194)]:
                    found&=rows[name]==raw[k]+raw[N+k]
                indices=np.flatnonzero(found);require(len(indices)==1,'unique actual half-endpoint in trace')
                row=rows[indices[0]];require(case[1]==int(row['half_ticks'])*TICK,'actual half clock')
                oracle=currents(case)
                errors=[abs(D(row[n])-v) for n,v in zip(['qa_a','q10_a','q7_a'],oracle)]
                require(max(errors)<=D(2e-11),'independent terminal current gate')
                observations.append(dict(ticks=int(row['ticks']),h_s=case[1],max_error_a=str(max(errors)),terminal_errors_a=[str(v) for v in errors]))
    return dict(root_checks=roots,temporal_checks=temporal,current_checks=observations,input_sha256=inputs)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    choice=parser.add_mutually_exclusive_group();choice.add_argument('--coarse-only',action='store_true');choice.add_argument('--coarse-cache');a=parser.parse_args()
    label='coarse_reference' if a.coarse_only else 'reference'
    out=ROOT/f'evidence/voice_joint_cycles_{label}{a.attempt:02d}.json';require(not out.exists(),'new reference receipt')
    names=['evidence/voice_joint_cycles_native01.json','tools/check_joint_cycles.py','tools/check_joint_reference.py','tools/vco1_increment_circuit.py','tools/vco1_increment_devices.py','tools/vco1_native_inventory.py','tools/lm741_port_reference.py','tools/chain_charge_reference.py','tools/circuit66_dc_vectors.py','tools/circuit66_vca_release_probes.py','tools/mixer_on_native_vectors.py','tools/cutoff_j7_vectors.py','tools/joint_cycles_analysis.py','docs/VOZ_PRIMER_CICLO_PROTOCOLO.md']
    if not a.coarse_only:names.append('evidence/voice_joint_cycles_resume01.json')
    if a.coarse_cache:names.append(a.coarse_cache)
    before={n:sha(ROOT/n) for n in names};report=dict(schema='rf-d/joint-cycles-reference/v1',passed=False,source_sha256=before,native_candidate_points_used=True,independent_root_solve=False,new_spice_processes=0,current_gate_a=2e-11)
    native=json.loads((ROOT/names[0]).read_text());parts=native['profiles'][:1] if a.coarse_only else native['profiles']
    cache=None
    if not a.coarse_only:
        extension=json.loads((ROOT/'evidence/voice_joint_cycles_resume01.json').read_text());require(extension['passed'],'completed continuation');parts=[*parts,*extension['profiles']]
    if a.coarse_cache:
        cache=json.loads((ROOT/a.coarse_cache).read_text());require(cache['passed'] and cache['coarse_only'] and cache['source_sha256']==cache['source_sha256_after'],'admitted coarse cache')
        for n,h in {**cache['source_sha256'],**cache['input_sha256']}.items():require(sha(ROOT/n)==h,'unchanged cached input '+n)
        parts=parts[1:]
    report['coarse_only']=a.coarse_only;report['cached_coarse_receipt']=a.coarse_cache
    started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;report.update(check(parts))
        if cache:
            for key in ['root_checks','temporal_checks','current_checks']:report[key]=cache[key]+report[key]
            report['input_sha256']={**cache['input_sha256'],**report['input_sha256']}
        report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_joint_cycles.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(parts)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['wall_s']=time.perf_counter()-started;report['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==report['source_sha256_after'],'unchanged reference sources')
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('CYCLES_REFERENCE',report['passed'],'rows',sum(c['rows'] for c in report.get('root_checks',[])),'currents',len(report.get('current_checks',[])),report.get('failure',''))
if __name__=='__main__':main()
