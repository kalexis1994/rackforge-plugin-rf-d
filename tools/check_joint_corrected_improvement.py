"""Backtest a held-phase predictor against its own measured cycle histories."""
import json,sys,traceback
from pathlib import Path
from decimal import Decimal,localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_joint_charge_response import mean_drift
from joint_cycles_analysis import require

def comparison(old,new):
    a,b=Decimal(old),Decimal(new)
    return dict(before=str(a),after=str(b),absolute_reduction=str(abs(a)-abs(b)),absolute_ratio=str(abs(b/a)) if a else None,improved=abs(b)<abs(a),zero_baseline=a==0)

def check():
    old=json.loads((ROOT/'evidence/voice_joint_seed_cycles_reference01.json').read_text());new=json.loads((ROOT/'evidence/voice_joint_corrected_cycles_reference01.json').read_text());prediction=json.loads((ROOT/'evidence/voice_joint_charge_response_fine_reference01.json').read_text());require(all(q['passed'] for q in [old,new,prediction]),'admitted histories and predictor');records=[];summaries=[]
    for id in [0,1]:
        for maximum in [65536,32768]:
            a,b=[next(c for c in q['cycles'] if c['seed_id']==id and c['maximum_half_ticks']==maximum) for q in [old,new]];ma,mb=mean_drift(a),mean_drift(b);caps=[]
            for k,(x,y) in enumerate(zip(a['capacitor_changes'],b['capacitor_changes'])):
                require((x['index'],x['a'],x['physical_b'],x['capacitance_f'])==(y['index'],y['a'],y['physical_b'],y['capacitance_f']),'same physical branch')
                v=comparison(x['interpolated_phase_voltage_change_v'],y['interpolated_phase_voltage_change_v']);m=comparison(str(ma[k]),str(mb[k]));pred=prediction['records'][id]['predictor']['linear_predicted_drift_current_a'][k]
                caps.append(dict(index=k,a=x['a'],physical_b=x['physical_b'],capacitance_f=x['capacitance_f'],voltage_drift_v=v,phase_inferred_mean_current_a=m,static_predicted_current_a=pred,measured_minus_static_prediction_a=str(mb[k]-Decimal.from_float(pred)),prediction_is_not_period_map=True))
            records.append(dict(seed_id=id,maximum_half_ticks=maximum,capacitors=caps,j7_drift_v=comparison(a['phase_state_difference'][194],b['phase_state_difference'][194]),radau_mean_panel_mismatch_v=comparison(a['cycle_radau_mean_ledger']['radau_mean_panel_mismatch_v'],b['cycle_radau_mean_ledger']['radau_mean_panel_mismatch_v']),improved_voltage_drift_capacitors=sum(c['voltage_drift_v']['improved'] for c in caps),neither_admits_steady_periodicity=True))
        coarse,fine=[next(r for r in records if r['seed_id']==id and r['maximum_half_ticks']==maximum) for maximum in [65536,32768]];trends=[]
        for a,b in zip(coarse['capacitors'],fine['capacitors']):
            va,vb=a['voltage_drift_v'],b['voltage_drift_v'];difference=abs(Decimal(va['before'])-Decimal(vb['before']))+abs(Decimal(va['after'])-Decimal(vb['after']));change=Decimal(vb['absolute_reduction'])
            trends.append(dict(index=b['index'],absolute_reduction_fine_v=str(change),sum_observed_refinement_differences_v=str(difference),trend_exceeds_observed_refinement=abs(change)>difference,not_a_continuous_error_bound=True))
        summaries.append(dict(seed_id=id,capacitor_trends=trends,improved_fine_voltage_drift_capacitors=fine['improved_voltage_drift_capacitors'],j7_improved_fine=fine['j7_drift_v']['improved'],periodic_root_admitted=False))
    return dict(records=records,summaries=summaries,static_prediction_backtested=True,own_histories_required=True,new_native_roots=0,new_trajectories=0,steady_periodicity_admitted=False,physical_cards_changed=False,new_audio=False)

def main():
    out='evidence/voice_joint_corrected_improvement01.json';require(not (ROOT/out).exists(),'exclusive receipt');names={'evidence/voice_joint_seed_cycles_reference01.json','evidence/voice_joint_corrected_cycles_reference01.json','evidence/voice_joint_charge_response_fine_reference01.json','tools/check_joint_corrected_improvement.py','docs/VOZ_CICLOS_CORREGIDOS_PROTOCOLO.md'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/joint-corrected-improvement/v1',passed=False,source_sha256=before)
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check())
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_corrected_improvement.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check()
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==r['source_sha256_after'],'unchanged sources');write(out,r);print('CORRECTED_IMPROVEMENT',r['passed'],r.get('failure',''),flush=True)

if __name__=='__main__':main()
