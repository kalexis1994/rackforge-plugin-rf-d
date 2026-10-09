"""Retrospective phase/charge observations and exact nominal panel identities."""
import argparse,json,struct,sys,time,traceback
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from check_joint_cycles import bank
from check_joint_reference import D,ci
from chain_charge_reference import CAPS
from joint_cycles_analysis import require,trace,checkpoints,checkpoint,TICK

GROUPS={65536:['references-local/joint-cycles01/65536'],32768:['references-local/joint-cycles01/32768','references-local/joint-cycles-resume01/32768','references-local/joint-cycles-resume02/32768']}
def panel(rows):
    cursor=rows['cursor'];saw=rows['saw'];bus=rows['bus'];current=(cursor-bus)/33000.
    kcl=float(max(abs((cursor-saw)/12500.+cursor/12500.+current)));c27=float(max(abs(rows['c27_a']-current)));formula=float(max(abs(current-(.5*saw-bus)/39250.)))
    require(max(kcl,c27,formula)<=1e-12,'nominal cursor/BUS/C27 endpoint identities')
    return dict(endpoint_count=len(rows),cursor_kcl_max_a=kcl,c27_direction_max_a=c27,thevenin_current_max_error_a=formula,panel_thevenin_ohm=39250.,conditional_rc_time_s=.3925,conditional_rc_is_whole_voice_pole=False)

def analyze_history(maximum,names):
    pieces=[];pairs=[];previous=None;inputs={};seams=0
    for name in names:
        d=ROOT/name;points=checkpoints(d/'checkpoints.bin');last=checkpoint((d/'final.ckp').read_bytes())
        if previous:require(previous['raw_sha256']==points[0]['raw_sha256'],'historical exact seam');seams+=1
        else:require(points[0]['ticks']==0,'historical initial clock')
        require(points[0]['maximum']==last['maximum']==maximum,'historical profile');rows=trace(d/'trace.bin',start_ticks=points[0]['ticks']);require(int(rows[-1]['ticks'])==last['ticks'],'historical complete segment')
        pieces.append(rows);previous=last;pairs.extend(case for i,case in enumerate(bank(d/'selected.txt')) if i%3!=0)
        for n in ['checkpoints.bin','final.ckp','trace.bin','selected.txt']:inputs[f'{name}/{n}']=sha(d/n)
    require(previous['ticks']==2752512000,'historical final clock');rows=np.concatenate(pieces);require(np.all(np.diff(rows['ticks'])>0),'historical ordered timeline');ids=np.flatnonzero((rows['ramp'][:-1]<-2)&(rows['ramp'][1:]>=-2))+1;require(len(ids)==2,'historical two resets');events=[];phases=[];actual=[]
    for i in ids:
        row=rows[i];matches=[]
        for case,raw in pairs:
            if all(raw[k]+raw[200+k]==row[field] for k,field in [(43,'ramp'),(46,'saw'),(54,'tri'),(44,'pulse'),(12,'bus'),(39,'cursor'),(194,'j7')]):matches.append(case)
        require(len(matches)==1,'unique historical selected event endpoint');case=matches[0];before,after=case[2],case[-1];require(float(before[43])==float(rows[i-1]['ramp']) and before[43]<-2<=after[43],'historical event previous state')
        alpha=(Decimal(-2)-before[43])/(after[43]-before[43]);phase=[a+alpha*(b-a) for a,b in zip(before,after)];phases.append(phase);actual.append(after)
        events.append(dict(begin_ticks=int(rows[i-1]['ticks']),end_ticks=int(row['ticks']),bracket_width_s=(int(row['ticks'])-int(rows[i-1]['ticks']))*TICK,alpha_decimal=str(alpha),endpoint_state=list(map(str,after)),interpolated_phase_state=list(map(str,phase))))
    caps=[]
    for k,(a,b,farad) in enumerate([*CAPS,(67,7,10e-6)]):
        b=b if isinstance(b,int) else 66 if b=='BUS' else None
        voltage=lambda x:x[ci(a)]-(x[ci(b)] if b is not None else Decimal(0));de=voltage(actual[1])-voltage(actual[0]);dp=voltage(phases[1])-voltage(phases[0]);caps.append(dict(index=k,a=a,b=b,capacitance_f=farad,endpoint_voltage_change_v=str(de),endpoint_charge_change_c=str(D(farad)*de),interpolated_phase_voltage_change_v=str(dp),interpolated_phase_charge_change_c=str(D(farad)*dp)))
    difference=[b-a for a,b in zip(*phases)];period=D(events[1]['end_ticks']-events[0]['end_ticks'])*D(TICK);implied=-Decimal(caps[5]['endpoint_charge_change_c'])/period
    return dict(maximum_half_ticks=maximum,segments=len(names),checkpoint_seams=seams,events=events,capacitor_changes=caps,phase_state_difference=list(map(str,difference)),panel=panel(rows),endpoint_period_s=str(period),c27_mean_current_implied_from_endpoint_charge_a=str(implied),required_panel_mean_mismatch_v=str(D(39250.)*implied),phase_interpolation_is_observation=True,c1_quadrature_between_events_available=False,steady_periodicity_admitted=False,input_sha256=inputs)

def check():
    old=json.loads((ROOT/'evidence/voice_joint_cycles_tests01.json').read_text());require(old['passed'],'historical admitted cycles');results=[]
    for maximum,names in GROUPS.items():
        q=analyze_history(maximum,names)
        for n,h in q['input_sha256'].items():require(old['private_input_sha256'][n]==h,'admitted historical raw identity '+n)
        results.append(q)
    return dict(histories=results,nominal_panel_thevenin_ohm=39250.,conditional_rc_time_s=.3925,conditional_rc_is_whole_voice_pole=False,necessary_periodic_mean_relation='Radau mean(0.5*saw-BUS)=0 when C27 charge repeats and other sources are OFF',new_roots=0,new_time_integration=False,steady_periodicity_admitted=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args();out=ROOT/f'evidence/voice_joint_history_cycles_reference{a.attempt:02d}.json';require(not out.exists(),'new history receipt');names={'tools/check_joint_history_cycles.py','docs/VOZ_CICLOS_HISTORIA_PROTOCOLO.md','evidence/voice_joint_cycles_tests01.json'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    data={f'{d}/{n}' for ds in GROUPS.values() for d in ds for n in ['checkpoints.bin','final.ckp','trace.bin','selected.txt']};before={n:sha(ROOT/n) for n in sorted(names)};private={n:sha(ROOT/n) for n in sorted(data)};r=dict(schema='rf-d/joint-history-cycles-reference/v1',passed=False,source_sha256=before,private_input_sha256=private,new_audio=False,new_spice_processes=0,new_native_processes=0);start=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check())
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_history_cycles.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check()
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};r['private_input_sha256_after']={n:sha(ROOT/n) for n in sorted(data)};require(before==r['source_sha256_after'] and private==r['private_input_sha256_after'],'unchanged historical sources/data');r['wall_s']=time.perf_counter()-start;out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('HISTORY_CYCLES',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
