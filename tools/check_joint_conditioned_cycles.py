"""Exact seams, independent selected equations and observed cycle charge drift."""
import argparse,json,struct,sys,time,traceback
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from analyze_joint_cycles import analyze
from joint_cycles_analysis import require,trace,TICK
from check_joint_reference import D,decode,ci
from check_joint_cycles import check as selected_check,bank
from chain_charge_reference import CAPS
from check_joint_history_cycles import panel

def event_bank(directory):
    path=directory/'events.txt';lines=path.read_text(encoding='utf8').splitlines();require(lines[0]=='RFJEVENT01' and (len(lines)-1)%3==0,'complete event ledger');result=[]
    rows=trace(directory/'trace.bin',start_ticks=262144000);selected=bank(directory/'selected.txt');halves=[p for i,p in enumerate(selected) if i%3!=0]
    indices=np.flatnonzero((rows['ramp'][:-1]<-2)&(rows['ramp'][1:]>=-2))+1
    require(len(indices)==2 and len(lines)==7,'two observed resets')
    for n in range(2):
        label,begin,end,charge,absolute=lines[1+3*n].split(',');require(label=='EVENT','event marker');before,after=decode(lines[2+3*n]),decode(lines[3+3*n]);i=indices[n]
        require((int(begin),int(end))==(int(rows[i-1]['ticks']),int(rows[i]['ticks'])),'event exact trace bracket')
        require(before[43]<Decimal(-2)<=after[43] and float(before[43])==float(rows[i-1]['ramp']) and float(after[43])==float(rows[i]['ramp']),'event phase and trace voltage')
        raw=struct.pack('<400d',*map(float,lines[3+3*n].split(',')[1:]));require(any(case[2]==before and struct.pack('<400d',*values)==raw for case,values in halves),'event states belong to selected admitted half pair')
        alpha=(Decimal(-2)-before[43])/(after[43]-before[43]);require(0<=alpha<=1,'interpolated phase bracket');phase=[a+alpha*(b-a) for a,b in zip(before,after)];require(abs(phase[43]+2)<Decimal('1e-90'),'Decimal phase rampa=-2')
        result.append(dict(begin_ticks=int(begin),end_ticks=int(end),bracket_width_s=(int(end)-int(begin))*TICK,alpha_decimal=str(alpha),interpolated_time_s=str((D(int(begin))+alpha*D(int(end)-int(begin)))*D(TICK)),native_cumulative_c1_charge_c=charge,native_cumulative_absolute_c=absolute,endpoint_state=list(map(str,after)),interpolated_phase_state=list(map(str,phase)),before_state=list(map(str,before))))
    return result

def cycle_changes(events):
    endpoints=[list(map(Decimal,x['endpoint_state'])) for x in events];phases=[list(map(Decimal,x['interpolated_phase_state'])) for x in events]
    charge=D(float(events[1]['native_cumulative_c1_charge_c']))-D(float(events[0]['native_cumulative_c1_charge_c']));absolute=D(float(events[1]['native_cumulative_absolute_c']))-D(float(events[0]['native_cumulative_absolute_c']));require(absolute>0,'cycle absolute current integral');delta=endpoints[1][43]-endpoints[0][43];balance=abs(charge+D(1e-8)*delta)/absolute;require(balance<=D(.002),'C1 balance between actual observed event endpoints')
    capacitors=[]
    for k,(a,b,farad) in enumerate([*CAPS,(67,7,10e-6)]):
        b=b if isinstance(b,int) else 66 if b=='BUS' else None
        def voltage(state):return state[ci(a)]-(state[ci(b)] if b is not None else Decimal(0))
        actual=[voltage(x) for x in endpoints];phase=[voltage(x) for x in phases]
        capacitors.append(dict(index=k,a=a,b=b,capacitance_f=farad,endpoint_voltage_change_v=str(actual[1]-actual[0]),endpoint_charge_change_c=str(D(farad)*(actual[1]-actual[0])),interpolated_phase_voltage_change_v=str(phase[1]-phase[0]),interpolated_phase_charge_change_c=str(D(farad)*(phase[1]-phase[0]))))
    difference=[b-a for a,b in zip(*phases)];ratios=[abs(x)/D(2e-9 if 98<=k<133 else 2e-6) for k,x in enumerate(difference)];worst=max(ratios)
    return dict(c1_charge_integral_between_event_endpoints_c=str(charge),c1_absolute_current_integral_c=str(absolute),endpoint_ramp_phase_difference_v=str(delta),c1_integrated_balance_relative=str(balance),capacitor_changes=capacitors,phase_state_difference=list(map(str,difference)),phase_difference_in_refinement_units=str(worst),worst_phase_coordinate=ratios.index(worst),phase_interpolation_is_observation=True,steady_periodicity_admitted=False)

def check(native):
    require(native['passed'],'completed native continuations');prefix=json.loads((ROOT/'evidence/voice_joint_prefix_native01.json').read_text());admitted=json.loads((ROOT/'evidence/voice_joint_prefix_reference01.json').read_text());require(prefix['passed'] and admitted['passed'],'admitted prefix')
    total=analyze(prefix,native);independent=selected_check(native['profiles']);require(len(independent['root_checks'])==24 and sum(x['rows'] for x in independent['root_checks'])==9600 and len(independent['current_checks'])==16 and len(independent['temporal_checks'])==8,'new selected coverage')
    histories=json.loads((ROOT/'evidence/voice_joint_history_cycles_reference01.json').read_text());require(histories['passed'],'retrospective history reference')
    cycles=[];contrast=[];inputs=dict(total['input_sha256']);inputs.update(independent['input_sha256'])
    for p in native['profiles']:
        directory=Path(p['command'][3]);events=event_bank(directory);changes=cycle_changes(events);maximum=p['maximum_half_ticks'];rows=np.concatenate([trace(ROOT/f'references-local/joint-prefix01/{maximum}/trace.bin'),trace(directory/'trace.bin',start_ticks=262144000)])
        period=D(events[1]['end_ticks']-events[0]['end_ticks'])*D(TICK);implied=-Decimal(changes['capacitor_changes'][5]['endpoint_charge_change_c'])/period
        cycles.append(dict(maximum_half_ticks=maximum,events=events,**changes,nominal_panel=panel(rows),c27_mean_current_implied_from_endpoint_charge_a=str(implied),required_panel_mean_mismatch_v=str(D(39250.)*implied)));n=(directory/'events.txt').relative_to(ROOT).as_posix();inputs[n]=sha(ROOT/n)
        old=next(h for h in histories['histories'] if h['maximum_half_ticks']==maximum)
        contrast.append(dict(maximum_half_ticks=maximum,old_c27_phase_change_v=old['capacitor_changes'][5]['interpolated_phase_voltage_change_v'],new_c27_phase_change_v=changes['capacitor_changes'][5]['interpolated_phase_voltage_change_v'],old_c10_phase_change_v=old['capacitor_changes'][17]['interpolated_phase_voltage_change_v'],new_c10_phase_change_v=changes['capacitor_changes'][17]['interpolated_phase_voltage_change_v'],old_j7_phase_change_v=old['phase_state_difference'][194],new_j7_phase_change_v=changes['phase_state_difference'][194],old_required_panel_mean_mismatch_v=old['required_panel_mean_mismatch_v'],new_required_panel_mean_mismatch_v=str(D(39250.)*implied),histories_have_same_nominal_scene=True,neither_history_admits_settled_periodicity=True))
    return dict(aggregate=total,new_independent=independent,cycles=cycles,history_contrast=contrast,history_reference='evidence/voice_joint_history_cycles_reference01.json',input_sha256=inputs,inherited_prefix_reference='evidence/voice_joint_prefix_reference01.json',inherited_prefix_stage_rows=4800,own_conditioned_cycles_admitted=True,steady_periodicity_admitted=False,global_settling_bound=False,native_candidate_points_used=True,independent_root_search=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args();out=ROOT/f'evidence/voice_joint_conditioned_cycles_reference{a.attempt:02d}.json';require(not out.exists(),'new receipt');name='evidence/voice_joint_conditioned_cycles_native01.json';native=json.loads((ROOT/name).read_text())
    names={name,'evidence/voice_joint_prefix_native01.json','evidence/voice_joint_prefix_reference01.json','evidence/voice_joint_history_cycles_reference01.json','docs/VOZ_CICLOS_CONDICIONADOS_PROTOCOLO.md','docs/VOZ_CICLOS_HISTORIA_PROTOCOLO.md','tools/check_joint_conditioned_cycles.py'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/joint-conditioned-cycles-reference/v1',passed=False,source_sha256=before,new_audio=False,new_spice_processes=0);started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check(native))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_conditioned_cycles.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==r['source_sha256_after'],'unchanged reference sources');r['wall_s']=time.perf_counter()-started;out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CONDITIONED_CYCLES_REFERENCE',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
