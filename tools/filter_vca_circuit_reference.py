"""Independent board-4 electrical oracle, with an explicit lab input port.

The failed coupled VCO reset is preserved separately. This oracle resolves
the loaded ladder, regeneration, both VCAs and outputs without claiming
to close the VCO/mixer interface or a real-time implementation.
"""
from dataclasses import asdict, dataclass, field, replace
import math
from pathlib import Path

import numpy as np

import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT
VECTORS=['v(fixture)', 'v(mix_bus_board4_pin4)']+voice.EXTRA[1:]


@dataclass(frozen=True)
class Scenario:
    board: voice.Scenario = field(default_factory=lambda: replace(voice.Scenario(),
        oscillator=replace(voice.Scenario().oscillator,duration_s=.08,max_step_s=2e-6)))
    frequency_hz: float = 440
    amplitude_v: float = .1
    source_ohm: float = 1000

    @property
    def oscillator(self): return self.board.oscillator

    def validate(self):
        self.board.validate()
        if not all(math.isfinite(v) for v in (self.frequency_hz,self.amplitude_v,self.source_ohm)):
            raise ValueError('finite electrical input required')
        if self.frequency_hz<=0 or self.amplitude_v<0 or self.source_ohm<=0:
            raise ValueError('positive frequency/source resistance and nonnegative amplitude required')
        if self.frequency_hz*self.oscillator.max_step_s>=.1:
            raise ValueError('input frequency not resolved by declared maximum step')


def netlist(s, export):
    s.validate()
    full,meta=voice.netlist(s.board,export)
    # Take the independently transcribed board-4 branches, not any VCO branch.
    start=full.index('RF4_R4 ')
    stop=full.index('.options ',start)
    board=full[start:stop]
    cards='\n'.join(l for l in full.splitlines() if l.startswith('.model LAB_NPN ') or l.startswith('.model LAB_PNP '))
    if len(cards.splitlines())!=2 or 'Vmixer ' in board or 'Qic2' in board:
        raise ValueError('invalid independent board extraction')
    lines=['RF-D conditional independent ladder VCAs output electrical fixture',
           'Vpos10 POS10_V 0 10', 'Vneg10 NEG10_V 0 -10', cards, board,
           f'Vfixture FIXTURE 0 SIN(0 {s.amplitude_v:.17g} {s.frequency_hz:.17g})',
           f'Rfixture FIXTURE MIX_BUS_BOARD4_PIN4 {s.source_ohm:.17g}',
           f'.options bypass=0 itl4=100 temp=25 tnom=25 method={s.oscillator.method} maxord={s.oscillator.order} reltol=1e-7 abstol=1e-13 vntol=1e-8 gmin=1e-12',
           '.save '+' '.join(VECTORS), '.control','set numdgt=17',
           'set wr_singlescale','set wr_vecnames',
           f'tran {s.oscillator.max_step_s:.17g} {s.oscillator.duration_s:.17g} 0 {s.oscillator.max_step_s:.17g}',
           f"wrdata {export.as_posix()} {' '.join(VECTORS)}",'quit','.endc','.end','']
    # Inputs are the graph, device hypotheses and the two generating helpers.
    actual=[voice.GRAPH,vco.DEVICES,Path(vco.__file__),Path(voice.__file__),Path(__file__)]
    meta.update(schema='rf-d/filter-vca-circuit-netlist/v1',scenario=asdict(s),
        source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in actual},
        input_port='laboratory sine, finite source resistance; VCO/mixer coupling not closed',
        branches=None, boundary_scope=meta['boundary_scope']+['VCO omitted; finite-resistance sine at BUS'])
    return '\n'.join(lines),meta


def run(s,label,work,executable):
    return voice.run(s,label,work,executable,netlist_factory=netlist,vectors=VECTORS)


def measure(raw, s, settle_s=.04):
    # Integer cycles ending at the final clock; includes exact interpolated bounds.
    stop=raw[-1,0]
    count=math.floor((stop-settle_s)*s.frequency_hz)
    if count<2: raise ValueError('at least two complete observed cycles required')
    start=stop-count/s.frequency_hz
    t=np.r_[start,raw[(raw[:,0]>start)&(raw[:,0]<stop),0],stop]
    waves={}
    for k,name in enumerate(VECTORS,start=1):
        x=np.interp(t,raw[:,0],raw[:,k])
        mean=float(np.trapezoid(x,t)/(stop-start))
        cosine=2*np.trapezoid(x*np.cos(2*np.pi*s.frequency_hz*t),t)/(stop-start)
        sine=2*np.trapezoid(x*np.sin(2*np.pi*s.frequency_hz*t),t)/(stop-start)
        rms=float(np.sqrt(np.trapezoid((x-mean)**2,t)/(stop-start)))
        waves[name]=dict(min=float(x.min()),max=float(x.max()),mean=float(mean),ac_rms=rms,
                         fundamental_peak=float(np.hypot(cosine,sine)))
    cols={n:i+1 for i,n in enumerate(VECTORS)}
    def values(n): return np.interp(t,raw[:,0],raw[:,cols['v(f4_'+n+')']])
    q17,right,main,hp=map(values,('q17_collector','c2_right','main_output','headphone_input'))
    delivered=float(np.trapezoid((right-main)/1000+(right-hp)/1000,t))
    change=float(10e-6*((q17-right)[-1]-(q17-right)[0]))
    output=waves['v(f4_main_output)']
    bus=waves['v(mix_bus_board4_pin4)']
    return dict(observation_start_s=start,observation_stop_s=stop,cycles=count,windows=waves,
        transfer_fundamental=output['fundamental_peak']/bus['fundamental_peak'] if bus['fundamental_peak'] else None,
        output_ac_rms_v=output['ac_rms'],c2_delivered_c=delivered,c2_charge_change_c=change,
        c2_balance_absolute_c=abs(change-delivered),
        headroom_v=[waves['v(f4_q17_collector)']['min'],10-waves['v(f4_q17_collector)']['max']])
