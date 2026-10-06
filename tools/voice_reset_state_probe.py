"""Observe the preserved failing VCO without changing any circuit branch."""
import gzip,json
from pathlib import Path
import numpy as np
import voice_vco_rshunt as source
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT
EXTRA=['v(xic3.3)','v(xic3.4)','v(xic3.10)','v(xic3.11)','v(xic3.12)',
       'v(xic3.20)','v(xic3.21)','v(xic3.22)','v(fet_left_drain)',
       'v(fet_common_source)','v(q10_base)']
VECTORS=source.port.VCO_VECTORS+EXTRA


def factory(s,export):
    frozen,_=source.factory('returned',source.REFINED[0]);deck,meta=frozen(s,export)
    deck=deck.replace(f'rshunt={source.REFINED[0]:.17g} ','',1)
    old=' '.join(source.port.VCO_VECTORS);new=' '.join(VECTORS)
    deck=deck.replace('.save '+old,'.save '+new)
    deck=deck.replace(old+'\nquit',new+'\nquit')
    meta.update(rshunt_ohm=None,per_node_extra_conductance_s=0,exact_original_equations=True,
                observation_only=True,exported_vectors=VECTORS)
    meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
    return deck,meta


def main():
    work=ROOT/'references-local/voice-circuit/reset-state-probe01';output=ROOT/'evidence/voice_reset_state_probe01.json'
    if work.exists() or output.exists():raise ValueError('preserve prior observation')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe';s=source.coupled.Scenario()
    label='returned-bus-state'
    try:
        voice.run(s,label,work,exe,netlist_factory=factory,vectors=VECTORS,timeout=120)
        raise ValueError('expected preserved failure did not reproduce')
    except ValueError:
        receipt=vco.read(work/(label+'.json'))
        if receipt['trajectory_complete'] or 'SPICE reported failure' not in receipt.get('error',''):
            raise ValueError('probe must preserve the original reset rejection')
    raw=np.loadtxt(work/(label+'.txt'),skiprows=1,ndmin=2)
    bank=json.loads(gzip.decompress((ROOT/'evidence/voice_port_behavioral01.json.gz').read_bytes()))
    original=bank['cases']['fixed-contour-control']['iterations'][2]['vco_receipt']
    path=ROOT/'references-local/voice-circuit'/bank['bank']/(original['label']+'.txt')
    if vco.sha(path)!=original['partial_export_sha256']:raise ValueError('original partial trace identity')
    reference=np.loadtxt(path,skiprows=1,ndmin=2)
    width=len(source.port.VCO_VECTORS)+1
    if raw[:,:width].shape!=reference.shape or not np.array_equal(raw[:,:width],reference):
        raise ValueError('additional observations changed the preserved trajectory')
    if raw.shape[1]!=len(VECTORS)+1 or not np.isfinite(raw).all() or receipt['source_sha256']!=receipt['source_sha256_after']:
        raise ValueError('finite observation and stable sources required')
    a=float(raw[-1,0]-100e-9);mask=raw[:,0]>=a;window={}
    for i,name in enumerate(VECTORS,1):
        x=raw[mask,i];window[name]=dict(min_v=float(x.min()),max_v=float(x.max()),last_v=float(x[-1]))
    report=dict(schema='rf-d/reset-state-observation/v1',observation_replay_passed=True,
                trajectory_complete=False,coupling_admitted=False,new_solves=1,
                receipt=receipt,original_partial_export_sha256=vco.sha(path),
                identical_original_clock_and_observations=True,last_clock_s=float(raw[-1,0]),
                observed_final_window_s=100e-9,final_window_rows=int(mask.sum()),accepted_state_window=window,
                failed_newton_iterates_observed=False,physical_fidelity=False,real_time=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('state observation reproduced the original partial clock and six vectors exactly',flush=True)


if __name__=='__main__':main()
