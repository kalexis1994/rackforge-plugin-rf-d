"""Independent stages, exact short prefix, cycle charges and Radau mean ledger."""
import argparse,json,struct,sys,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,trace,checkpoint,checkpoints,compare,TICK
from check_joint_reference import D,decode,ci
from check_joint_cycles import check as selected_check,bank
from analyze_joint_cycles import analyze
from check_joint_conditioned_cycles import cycle_changes
from check_joint_history_cycles import panel

def events(directory):
    lines=(directory/'events.txt').read_text(encoding='utf8').splitlines();require(lines[0]=='RFJEVENT01' and len(lines)==7,'two complete reset ledgers')
    rows=trace(directory/'trace.bin');selected=bank(directory/'selected.txt');halves=[p for i,p in enumerate(selected) if i%3!=0];indices=np.flatnonzero((rows['ramp'][:-1]<-2)&(rows['ramp'][1:]>=-2))+1;require(len(indices)==2,'two reset brackets');out=[]
    for n in range(2):
        raw=lines[1+3*n].split(',');require(raw[0]=='EVENT' and len(raw)==10,'event means codec');begin,end=int(raw[1]),int(raw[2]);before,after=decode(lines[2+3*n]),decode(lines[3+3*n]);i=indices[n]
        require((begin,end)==(int(rows[i-1]['ticks']),int(rows[i]['ticks'])),'event clocks');require(before[43]<Decimal(-2)<=after[43] and float(before[43])==float(rows[i-1]['ramp']) and float(after[43])==float(rows[i]['ramp']),'event phase voltage')
        packed=struct.pack('<400d',*map(float,lines[3+3*n].split(',')[1:]));require(any(case[2]==before and struct.pack('<400d',*values)==packed for case,values in halves),'event matches selected half pair')
        alpha=(Decimal(-2)-before[43])/(after[43]-before[43]);phase=[a+alpha*(b-a) for a,b in zip(before,after)];require(0<=alpha<=1 and abs(phase[43]+2)<Decimal('1e-90'),'Decimal phase interpolation')
        out.append(dict(begin_ticks=begin,end_ticks=end,bracket_width_s=(end-begin)*TICK,alpha_decimal=str(alpha),interpolated_time_s=str((D(begin)+alpha*D(end-begin))*D(TICK)),native_cumulative_c1_charge_c=raw[3],native_cumulative_absolute_c=raw[4],native_cumulative_mean_integrals=raw[5:],endpoint_state=list(map(str,after)),interpolated_phase_state=list(map(str,phase)),before_state=list(map(str,before))))
    return out

def ledger(before,after,integrals,seconds):
    require(seconds>0 and len(integrals)==5,'ledger duration')
    c27=lambda s:s[ci(6)]-s[12]
    delta=D(10e-6)*(c27(after)-c27(before));error=abs(delta+integrals[3]);gate=D(1e-12)*seconds
    mismatch=integrals[4]/seconds;series=integrals[3]/seconds
    identity=abs(mismatch-D(39250.)*series);recombination=abs(mismatch-(D(.5)*integrals[0]-integrals[1])/seconds)
    require(error<=gate and max(identity,recombination)<=D(1e-9),'C27 charge/Radau panel mean identities')
    return dict(duration_s=str(seconds),c27_charge_change_c=str(delta),series_charge_integral_c=str(integrals[3]),c27_charge_integral_error_c=str(error),c27_charge_integral_gate_c=str(gate),radau_mean_saw_v=str(integrals[0]/seconds),radau_mean_bus_v=str(integrals[1]/seconds),radau_mean_input6_v=str(integrals[2]/seconds),radau_mean_series_current_a=str(series),radau_mean_panel_mismatch_v=str(mismatch),panel_mean_identity_error_v=str(identity),panel_mean_recombination_error_v=str(recombination),not_an_independent_all_stage_quadrature=True)

def check(native):
    require(native['passed'] and len(native['profiles'])==4,'complete four-profile campaign');inputs=json.loads((ROOT/'evidence/voice_joint_seed_cycles_inputs01.json').read_text());short=json.loads((ROOT/'evidence/voice_joint_charge_seed_native02.json').read_text());lines=short['commands'][-1]['stdout'].splitlines();short_states={}
    for i,line in enumerate(lines):
        if line.startswith('RELEASE_PROFILE,'):
            id,maximum=map(int,line.split(',')[1:3]);short_states[id,maximum]=struct.pack('<400d',*map(float,lines[i+1].split(',')[1:]))
    aggregates=[];cycles=[];private={};initial_refinement=[]
    for id in [0,1]:
        profiles=[p for p in native['profiles'] if p['seed_id']==id];require({p['maximum_half_ticks'] for p in profiles}=={65536,32768},'both seed resolutions');aggregate=analyze(dict(profiles=profiles));aggregates.append(dict(seed_id=id,**aggregate));private.update(aggregate['input_sha256']);prefix_points=[]
        for p in profiles:
            maximum=p['maximum_half_ticks'];directory=Path(p['command'][3]);points=checkpoints(directory/'checkpoints.bin');seed=next(s for s in inputs['outputs'] if s['id']==id and s['maximum_half_ticks']==maximum);require(points[0]['raw_sha256']==seed['sha256'],'exact initial checkpoint')
            prefix=next(s for s in points if s['ticks']==1048576);require(len(points)==23,'initial/2us/21 anchors');require(struct.pack('<400d',*prefix['high'],*prefix['low'])==short_states[id,maximum],'short release bit-identical at 2us');prefix_points.append([points[0],prefix])
            ev=events(directory);changes=cycle_changes(ev);rows=trace(directory/'trace.bin');duration=D(ev[1]['end_ticks']-ev[0]['end_ticks'])*D(TICK);old,new=[list(map(Decimal,x['endpoint_state'])) for x in ev];integrals=[D(float(b))-D(float(a)) for a,b in zip(ev[0]['native_cumulative_mean_integrals'],ev[1]['native_cumulative_mean_integrals'])];mean=ledger(old,new,integrals,duration)
            rail= json.loads((ROOT/'evidence/voice_joint_seed_cycles_rail_reference01.json').read_text());require(rail['passed'],'fixed-rail semantics')
            for cap in changes['capacitor_changes']:
                cap['physical_b']=cap['b'] if cap['b'] is not None else 'PLUS' if cap['index']==11 else 'GROUND'
                cap['fixed_reference_v']=rail['fixed_plus_lab_v'] if cap['index']==11 else '0' if cap['b'] is None else None
                cap['fixed_reference_cancels_in_reported_changes']=True
            totals=[s for s in p['stderr'].splitlines() if s.startswith('MEAN_LEDGER,')];require(len(totals)==1,'final mean ledger');integrals=list(map(lambda s:D(float(s)),totals[0].split(',')[1:]));last=checkpoint((directory/'final.ckp').read_bytes());lift=lambda cp:[D(h)+D(l) for h,l in zip(cp['high'],cp['low'])];full=ledger(lift(points[0]),lift(last),integrals,D(last['ticks'])*D(TICK))
            cycles.append(dict(seed_id=id,maximum_half_ticks=maximum,events=ev,**changes,nominal_panel=panel(rows),cycle_radau_mean_ledger=mean,full_radau_mean_ledger=full,short_prefix_bit_identical=True))
            n=(directory/'events.txt').relative_to(ROOT).as_posix();private[n]=sha(ROOT/n)
        initial_refinement.append(dict(seed_id=id,shared_clock_points=compare(*prefix_points)))
    independent=selected_check(native['profiles']);private.update(independent['input_sha256']);require(len(independent['root_checks'])==48 and len(independent['current_checks'])==32 and len(independent['temporal_checks'])==16,'selected four-profile coverage')
    history=json.loads((ROOT/'evidence/voice_joint_history_cycles_reference01.json').read_text());held=json.loads((ROOT/'evidence/voice_joint_conditioned_cycles_reference01.json').read_text());contrast=[]
    for maximum in [65536,32768]:
        a,b=[next(c for c in cycles if c['seed_id']==id and c['maximum_half_ticks']==maximum) for id in [0,1]];h=next(c for c in history['histories'] if c['maximum_half_ticks']==maximum);d=next(c for c in held['cycles'] if c['maximum_half_ticks']==maximum)
        c27=lambda c:Decimal(c['capacitor_changes'][5]['interpolated_phase_voltage_change_v']);j7=lambda c:Decimal(c['phase_state_difference'][194])
        contrast.append(dict(maximum_half_ticks=maximum,c27_historical_v=str(c27(h)),c27_held_dc_v=str(c27(d)),c27_seed0_v=str(c27(a)),c27_seed1_v=str(c27(b)),j7_historical_v=str(j7(h)),j7_held_dc_v=str(j7(d)),j7_seed0_v=str(j7(a)),j7_seed1_v=str(j7(b)),seed1_c27_absolute_drift_ratio_to_seed0=str(abs(c27(b)/c27(a))) if c27(a)!=0 else None,seed1_j7_absolute_drift_ratio_to_seed0=str(abs(j7(b)/j7(a))) if j7(a)!=0 else None,histories_have_same_nominal_scene=True,none_admits_steady_periodicity=True))
    return dict(aggregates=aggregates,new_independent=independent,short_prefix_refinement=initial_refinement,cycles=cycles,history_contrast=contrast,input_sha256=private,own_seed_cycles_admitted=True,steady_periodicity_admitted=False,global_settling_bound=False,native_candidate_points_used=True,independent_root_search=False,new_audio=False,new_spice_processes=0)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args();out=ROOT/f'evidence/voice_joint_seed_cycles_reference{a.attempt:02d}.json';require(not out.exists(),'new reference');name='evidence/voice_joint_seed_cycles_native01.json';native=json.loads((ROOT/name).read_text())
    names={name,'evidence/voice_joint_seed_cycles_inputs01.json','evidence/voice_joint_charge_seed_native02.json','evidence/voice_joint_history_cycles_reference01.json','evidence/voice_joint_conditioned_cycles_reference01.json','evidence/voice_joint_seed_cycles_rail_reference01.json','docs/VOZ_CARGAS_RIELES_NOTA.md','docs/VOZ_CICLOS_SEMILLAS_PROTOCOLO.md','tools/check_joint_seed_cycles.py'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/joint-seed-cycles-reference/v1',passed=False,source_sha256=before);started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check(native))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_seed_cycles.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==r['source_sha256_after'],'unchanged reference sources');r['wall_s']=time.perf_counter()-started;out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('SEED_CYCLES_REFERENCE',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
