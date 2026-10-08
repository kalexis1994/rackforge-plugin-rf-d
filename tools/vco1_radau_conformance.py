"""Compare nominal Radau periods against already validated SPICE observables."""
import gzip,json
from vco1_radau_cycles_resume import ROOT,sha,GATES,comparison
OUT='evidence/voice_vco1_radau_conformance01.json'

def calculate(bank,old,validation):
    if not bank['passed'] or not validation['passed'] or validation['source_sha256']['evidence/vco1_circuit_convergence_v1.json.gz']!=sha(ROOT/'evidence/vco1_circuit_convergence_v1.json.gz'):raise ValueError('admitted source banks')
    expected=dict(keyboard_v=-2.1,other_control_v=-2.1,r8_fraction=.5,r11_active_ohm=500.,c4_f=1e-11,upper_contact=3,lower_contact=10,level_fraction=.5,imposed_mixer_v=0.,external_neg4_load_a=0.,duration_s=.03,order=2)
    rows=[]
    for profile in bank['profiles']:
        for label in ('c4-10-gear125','c4-10-trap125'):
            scene=old['cases'][label];receipt=scene['receipt']
            if any(scene['scenario'][k]!=v for k,v in expected.items()) or not receipt['trajectory_complete'] or receipt['exit_code']!=0 or receipt['source_sha256']!=receipt['source_sha256_after']:raise ValueError('complete identical conditional SPICE scene')
            cmp=comparison(profile['measurements'],scene['measurements']);ok=cmp['frequency_error_cents']<=GATES['frequency_refinement_cents'] and max(cmp['output_extrema_error_v'].values())<=GATES['output_extrema_refinement_v']
            rows.append(dict(native_half_ticks=profile['maximum_accepted_half_ticks'],reference_scene=label,comparison=cmp,passed=ok,reference_frequency_hz=scene['measurements']['frequency_hz'],native_frequency_hz=profile['measurements']['frequency_hz']))
    return rows

def main():
    out=ROOT/OUT
    if out.exists():raise ValueError('preserve conformance')
    names=['tools/vco1_radau_conformance.py','docs/VCO1_RADAU_CONFORMIDAD_PROTOCOLO.md','evidence/voice_vco1_radau_cycles04.json','evidence/vco1_circuit_convergence_v1.json.gz','evidence/vco1_circuit_validation.json']
    before={n:sha(ROOT/n) for n in names};r=dict(schema='rf-d/radau-nominal-archived-method-conformance/v1',passed=False,source_sha256=before,new_spice_processes=0,new_native_trajectories=0,new_audio=False,physical_fidelity=False,gates=GATES)
    try:
        bank=json.loads((ROOT/names[2]).read_text());old=json.load(gzip.open(ROOT/names[3],'rt'));validation=json.loads((ROOT/names[4]).read_text());rows=calculate(bank,old,validation);r.update(comparisons=rows,passed=len(rows)==4 and all(x['passed'] for x in rows))
    except Exception as exc:r['error']=repr(exc)
    r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['passed']=r['passed'] and before==r['source_sha256_after']
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('Radau archived method comparison',r['passed'],r.get('error',''),flush=True)

if __name__=='__main__':main()
