"""Coupled VCO1, mixer, board4 and physically loaded loudness contour.

No imposed audio/envelope waveform. Trigger, contour rail and Q21 remain
declared lab boundaries. Existing component graphs/device cards unchanged.
"""
from dataclasses import asdict,dataclass,field,replace
import math
from pathlib import Path
import numpy as np
import loudness_board4_circuit as contour
import filter_vca_circuit_reference as f
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT
VECTORS=['v(ramp_c1)','v(schmitt_drive)','v(saw_output_9b)',
         'v(mix_bus_board4_pin4)','v(f4_recover_collector)','v(f4_main_output)',
         'v(f4_q17_collector)','v(f4_c2_right)','v(f4_headphone_input)',
         'v(f4_loudness_contour)','v(e2_timing_c2)','v(e2_attack_panel_in)',
         'v(e2_decay_out)','v(e2_follower_base)','v(e2_reset_collector)',
         'v(e2_attack_gate_lower)','v(e2_keyboard_trigger)','v(f4_q18_base)']


@dataclass(frozen=True)
class Scenario:
    board:voice.Scenario=field(default_factory=voice.Scenario)
    controls:contour.envelope.Controls=field(default_factory=contour.envelope.Controls)
    trigger_on_s:float=.002
    trigger_off_s:float=.025
    trigger_transition_s:float=10e-6
    contour_supply_v:float=9.3

    @property
    def oscillator(self):return self.board.oscillator

    @property
    def vectors(self):return VECTORS if self.controls.final_decay else VECTORS+['@de2_cr4[id]']

    def contour_scenario(self):
        return contour.Scenario(audio=f.Scenario(board=self.board),controls=self.controls,
            trigger_on_s=self.trigger_on_s,trigger_off_s=self.trigger_off_s,
            trigger_transition_s=self.trigger_transition_s,contour_supply_v=self.contour_supply_v)

    def validate(self):
        self.board.validate();self.contour_scenario().validate()
        if self.controls.attack_ohm<=0 or self.controls.decay_ohm<=0:
            raise ValueError('this measurement bank requires interior attack/decay tracks')


def netlist(s,export):
    s.validate();text,meta=voice.netlist(s.board,export,linear_solver='klu')
    envelope,env_meta=contour.netlist(s.contour_scenario(),export)
    start=envelope.index('RE2_R23 ');stop=envelope.index('.options ',start)
    block=envelope[start:stop]
    if 'VF4_' in block or 'FIXTURE' in block or block.count('VE2_keyboard ')!=1:
        raise ValueError('invalid independently defined contour extraction')
    old='VF4_contour F4_LOUDNESS_CONTOUR 0 '
    if sum(line.startswith(old) for line in text.splitlines())!=1:raise ValueError('contour boundary count')
    text='\n'.join(line for line in text.splitlines() if not line.startswith(old))+'\n'
    text=text.replace('.options ',block+'.options ',1)
    text=text.replace('.save '+' '.join(voice.VECTORS),'.save '+' '.join(s.vectors))
    text=text.replace(' '.join(voice.VECTORS)+'\nquit',' '.join(s.vectors)+'\nquit')
    text=text.replace('RF-D coupled conditional VCO1 ladder VCAs board outputs',
                      'RF-D coupled VCO1 ladder both VCAs and loaded loudness contour',1)
    meta.update(schema='rf-d/loudness-voice-netlist/v1',scenario=asdict(s),
        contour_branches=env_meta['contour_branches'],vco_electrically_coupled=True,
        imposed_audio_waveform=False,imposed_loudness_contour=False)
    meta['boundary_scope']=[x for x in env_meta['boundary_scope'] if 'VCO omitted' not in x]
    for name,digest in env_meta['source_sha256'].items():meta['source_sha256'][name]=digest
    meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
    return text,meta


def run(s,label,work,exe,factory=None,timeout=120):
    return voice.run(s,label,work,exe,netlist_factory=netlist if factory is None else factory,
                     vectors=s.vectors,timeout=timeout)


def measurement(raw,s):
    col={n:i+1 for i,n in enumerate(s.vectors)};t=raw[:,0]
    val=lambda n:raw[:,col[n]]
    timing=val('v(e2_timing_c2)');main=val('v(f4_main_output)');right=val('v(f4_c2_right)')
    current=(val('v(e2_attack_panel_in)')-timing)/s.controls.attack_ohm
    current+=(val('v(e2_decay_out)')-timing)/s.controls.decay_ohm
    current-=(timing-val('v(e2_follower_base)'))/10000
    if not s.controls.final_decay:current-=val('@de2_cr4[id]')
    integrated=lambda x:np.r_[0,np.cumsum(np.diff(t)*(x[:-1]+x[1:])/2)]
    qerr=10e-6*(timing-timing[0])-integrated(current)
    delivered=(right-main)/1000+(right-val('v(f4_headphone_input)'))/1000
    vcap=val('v(f4_q17_collector)')-right
    outerr=10e-6*(vcap-vcap[0])-integrated(delivered)
    edges=vco.crossings(t,val('v(schmitt_drive)'),0,False)
    edges=edges[edges>=s.trigger_on_s+s.trigger_transition_s]
    if len(edges)<5:raise ValueError('measured reset train too short')
    periods=np.diff(edges)
    windows={}
    spans={'rest':(s.trigger_on_s*.2,s.trigger_on_s*.8),
           'attack':(s.trigger_on_s+s.trigger_transition_s,s.trigger_off_s),
           'release':(s.trigger_off_s+s.trigger_transition_s,s.oscillator.duration_s)}
    for name,(a,b) in spans.items():
        tt=np.r_[a,t[(t>a)&(t<b)],b];x=np.interp(tt,t,main);dc=np.trapezoid(x,tt)/(b-a)
        windows[name]=dict(output_ac_rms_v=float(np.sqrt(np.trapezoid((x-dc)**2,tt)/(b-a))),
            contour_mean_v=float(np.trapezoid(np.interp(tt,t,val('v(f4_loudness_contour)')),tt)/(b-a)))
    return dict(frequency_hz=float(1/np.mean(periods)),reset_crossings_s=edges.tolist(),
        period_spread_relative=float(np.ptp(periods)/np.mean(periods)),
        contour_min_v=float(val('v(f4_loudness_contour)').min()),
        contour_max_v=float(val('v(f4_loudness_contour)').max()),
        timing_balance_max_c=float(np.max(np.abs(qerr))),output_balance_max_c=float(np.max(np.abs(outerr))),
        windows=windows)
