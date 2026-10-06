"""Documented board-2 loudness circuit loaded by the complete board-4 oracle.

Finite sine input, ideal trigger/supply and Q21 boundary. No digital ADSR.
Gummel-Poon charge hypotheses match the existing board-4 device card.
"""
from dataclasses import asdict,dataclass,field,replace
import math
from pathlib import Path
import numpy as np
import filter_vca_circuit_reference as f
import loudness_contour_reference as envelope
import vco1_circuit_reference as vco

ROOT=vco.ROOT
GRAPH=ROOT/'evidence/loudness_contour_graph.json'
EXTRA=['v(e2_timing_c2)','v(e2_reset_collector)','v(e2_attack_gate_lower)',
       'v(e2_attack_panel_in)','v(e2_decay_out)','v(e2_follower_base)',
       'v(e2_reset_driver)','v(e2_trigger_collector)','v(e2_set_base)',
       'v(e2_reset_base)','v(e2_sustain_driver_emitter)','v(e2_key_rc)',
       'v(e2_supply)','v(e2_keyboard_trigger)','v(f4_q18_base)']
VECTORS=f.VECTORS+EXTRA


@dataclass(frozen=True)
class Scenario:
    audio:f.Scenario=field(default_factory=lambda:replace(f.Scenario(),
        board=replace(f.Scenario().board,oscillator=replace(f.Scenario().oscillator,
                      duration_s=.35,max_step_s=8e-6))))
    controls:envelope.Controls=field(default_factory=envelope.Controls)
    trigger_on_s:float=.01
    trigger_off_s:float=.2
    trigger_transition_s:float=10e-6
    trigger_high_v:float=10
    contour_supply_v:float=9.3

    @property
    def oscillator(self):return self.audio.oscillator

    @property
    def vectors(self):
        return VECTORS if self.controls.final_decay else VECTORS+['@de2_cr4[id]']

    def validate(self):
        self.audio.validate();self.controls.validate()
        values=(self.trigger_on_s,self.trigger_off_s,self.trigger_transition_s,self.trigger_high_v,self.contour_supply_v)
        if not all(math.isfinite(x) for x in values):raise ValueError('finite electrical boundary required')
        if not 0<self.trigger_on_s<self.trigger_on_s+self.trigger_transition_s<self.trigger_off_s<self.trigger_off_s+self.trigger_transition_s<self.oscillator.duration_s:
            raise ValueError('resolved ordered trigger edges required')
        if self.trigger_high_v!=10 or self.contour_supply_v!=9.3:
            raise ValueError('registered laboratory supply/trigger required')
        if self.controls.external_s_short:raise ValueError('keyboard-trigger bank requires S-trigger open')


def netlist(s,export):
    s.validate();text,meta=f.netlist(s.audio,export);graph=vco.read(GRAPH)
    old='VF4_contour F4_LOUDNESS_CONTOUR 0 '
    if sum(line.startswith(old) for line in text.splitlines())!=1:
        raise ValueError('exactly one contour voltage boundary required')
    text='\n'.join(line for line in text.splitlines() if not line.startswith(old))+'\n'
    def node(n):
        return {'GROUND':'0','PLUS_10':'POS10_V','MINUS_10':'NEG10_V',
                'CONTOUR_SUPPLY':'E2_SUPPLY','LOUDNESS_OUT':'F4_LOUDNESS_CONTOUR'}.get(n,'E2_'+n)
    pot=dict(attack_ohm=s.controls.attack_ohm,decay_ohm=s.controls.decay_ohm,
             sustain_lower_ohm=s.controls.sustain_lower_ohm,
             sustain_upper_ohm=5000-s.controls.sustain_lower_ohm)
    parts=[];manifest=[]
    for p in graph['resistors']:
        if p['ref']=='R49' or p['ref']=='LHC_FAST_DECAY' and s.controls.final_decay:continue
        value=pot[p['ohm']] if isinstance(p['ohm'],str) else p['ohm']
        if p['ref']=='R_TRIGGER_BASE_DRAWING':value=s.controls.trigger_base_ohm
        if p['ref']=='R25_DRAWING':value=s.controls.reset_pullup_ohm
        a,b=map(node,p['between']);name=('R' if value else 'V')+'E2_'+p['ref']
        parts.append(f'{name} {a} {b} {value:.17g}')
        manifest.append(dict(ref=p['ref'],terminals=[a,b],value=value,kind='R' if value else 'contact'))
    for p in graph['capacitors']:
        a,b=map(node,p['between']);parts.append(f"CE2_{p['ref']} {a} {b} {p['farad']:.17g}")
        manifest.append(dict(ref=p['ref'],terminals=[a,b],value=p['farad'],kind='C'))
    for p in graph['transistors']:
        pins=' '.join(node(p[k]) for k in ('collector','base','emitter'))
        parts.append(f"QE2_{p['ref']} {pins} LAB_{p['kind']}");manifest.append(p)
    # Match the explicit exploratory diode hypotheses in the earlier contour.
    # Zero storage remains unidentified; no manufacturer card is asserted.
    parts += ['.model E2_GE D(IS=1e-8 N=1.5 TNOM=25)',
              '.model E2_SI D(IS=1e-12 N=1.5 TNOM=25)']
    for p in graph['diodes']:
        if p.get('condition')=='final_decay_off' and s.controls.final_decay:continue
        card='E2_GE' if p['marking']=='1N34A' else 'E2_SI'
        parts.append(f"DE2_{p['ref']} {node(p['anode'])} {node(p['cathode'])} {card}")
        manifest.append(p)
    on,off,rise=s.trigger_on_s,s.trigger_off_s,s.trigger_transition_s
    parts += [f'VE2_supply E2_SUPPLY 0 {s.contour_supply_v:.17g}',
              f'VE2_keyboard E2_KEYBOARD_TRIGGER 0 PWL(0 0 {on:.17g} 0 {on+rise:.17g} 10 {off:.17g} 10 {off+rise:.17g} 0)']
    text=text.replace('.options ','\n'.join(parts)+'\n.options ',1)
    text=text.replace('.save '+' '.join(f.VECTORS),'.save '+' '.join(s.vectors))
    text=text.replace(' '.join(f.VECTORS)+'\nquit',' '.join(s.vectors)+'\nquit')
    text=text.replace('RF-D conditional independent ladder VCAs output electrical fixture',
                      'RF-D conditional loudness circuit loaded by ladder and both VCAs',1)
    meta.update(schema='rf-d/loudness-board4-netlist/v1',scenario=asdict(s),
        contour_branches=manifest,contour_load='R59 into physical Q18 base and both loaded VCAs')
    # Replace inherited envelope omission with the actual remaining boundaries.
    meta['boundary_scope']=[x for x in meta['boundary_scope'] if 'imposed loudness contour' not in x]
    meta['boundary_scope'] += ['board2 supply 9.3V imposed; Q26/raw rail omitted',
        'filter contour and its common trigger/reset loads omitted',
        'keyboard ideal PWL 0/10V with 10us edges; S-trigger open; Q21 base imposed',
        'exploratory diode conduction; diode storage and vintage parameters unidentified']
    for p in (GRAPH,Path(envelope.__file__),Path(__file__)):
        meta['source_sha256'][p.relative_to(ROOT).as_posix()]=vco.sha(p)
    return text,meta


def run(s,label,work,exe):
    return __import__('voice_circuit_reference').run(s,label,work,exe,netlist_factory=netlist,vectors=s.vectors)


def measure(raw,s):
    cols={n:i+1 for i,n in enumerate(s.vectors)};t=raw[:,0]
    def values(n):return raw[:,cols[n]]
    timing=values('v(e2_timing_c2)');out=values('v(f4_loudness_contour)')
    main=values('v(f4_main_output)')
    current=(values('v(e2_attack_panel_in)')-timing)/s.controls.attack_ohm if s.controls.attack_ohm else None
    if current is None or not s.controls.decay_ohm:raise ValueError('timing balance currently requires interior pots')
    current+=(values('v(e2_decay_out)')-timing)/s.controls.decay_ohm
    current-=(timing-values('v(e2_follower_base)'))/10000
    if not s.controls.final_decay:current-=values('@de2_cr4[id]')
    # Every accepted nonuniform clock interval contributes to the cumulative balance.
    delivered=np.r_[0,np.cumsum(np.diff(t)*(current[:-1]+current[1:])/2)]
    defect=10e-6*(timing-timing[0])-delivered
    right=values('v(f4_c2_right)');q17=values('v(f4_q17_collector)')
    supplied=(right-main)/1000+(right-values('v(f4_headphone_input)'))/1000
    out_delivered=np.r_[0,np.cumsum(np.diff(t)*(supplied[:-1]+supplied[1:])/2)]
    out_defect=10e-6*((q17-right)-(q17-right)[0])-out_delivered
    windows={}
    for label,a,b in [('rest',.002,.008),('attack',.02,.08),('held',.12,.19),('release',.23,.34)]:
        clock=np.r_[a,t[(t>a)&(t<b)],b];wave=np.interp(clock,t,main)
        dc=float(np.trapezoid(wave,clock)/(b-a))
        windows[label]=dict(output_ac_rms_v=float(np.sqrt(np.trapezoid((wave-dc)**2,clock)/(b-a))),
            contour_mean_v=float(np.trapezoid(np.interp(clock,t,out),clock)/(b-a)))
    return dict(timing_c2_min_v=float(timing.min()),timing_c2_max_v=float(timing.max()),
        contour_min_v=float(out.min()),contour_max_v=float(out.max()),
        timing_balance_max_c=float(np.max(np.abs(defect))),output_balance_max_c=float(np.max(np.abs(out_defect))),
        windows=windows)
