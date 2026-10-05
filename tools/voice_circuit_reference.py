"""Conditional coupled VCO1 -> loaded ladder -> two VCAs -> board outputs.

SVC-9 Fig 9-11/9-17; fixed controls are declared laboratory boundaries.
No buffering, ideal waves or imposed tail current join the audio blocks.
"""
from dataclasses import asdict, dataclass, field
import gzip
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np

import vco1_circuit_reference as vco

ROOT = vco.ROOT
GRAPH = ROOT / 'evidence/voice_board4_graph.json'
EXTRA = ['v(mix_bus_board4_pin4)', 'v(f4_base_q29)', 'v(f4_base_q30)',
         'v(f4_recover_collector)', 'v(f4_q16_collector)', 'v(f4_q15_collector)',
         'v(f4_q17_collector)', 'v(f4_c2_right)', 'v(f4_main_output)',
         'v(f4_headphone_input)', 'v(f4_control_base)', 'v(f4_bottom)',
         '@qf4_q28[ic]', '@qf4_q18[ic]', '@qf4_q21[ic]']
VECTORS = vco.VECTORS + EXTRA


@dataclass(frozen=True)
class Scenario:
    oscillator: vco.Scenario = field(default_factory=lambda: vco.Scenario(
        r11_active_ohm=521.3126579373712, r8_fraction=.2613404652606161,
        duration_s=.04, max_step_s=.5e-6))
    cutoff_fraction: float = .5
    range_fraction: float = .5
    scale_ohm: float = 250
    emphasis_ohm: float = 50000
    regen_bottom_ohm: float = 500
    r61_ohm: int = 200
    first_loudness_v: float = 2
    second_loudness_base_v: float = 2
    contour_amount_v: float = 0
    first_balance_ohm: float = 12.5
    second_balance_ohm: float = 50
    main_load_ohm: float = 100000
    headphone_input_ohm: float = 100000

    def validate(self):
        self.oscillator.validate()
        if self.oscillator.imposed_mixer_v != 0:
            raise ValueError('mixer voltage boundary is removed in coupled circuit')
        values = asdict(self)
        values.pop('oscillator')
        if not all(math.isfinite(v) for v in values.values()):
            raise ValueError('finite electrical scenario required')
        for name, high in [('cutoff_fraction', 1), ('range_fraction', 1),
                           ('scale_ohm', 500), ('emphasis_ohm', 50000),
                           ('regen_bottom_ohm', 1000), ('first_balance_ohm', 25),
                           ('second_balance_ohm', 100)]:
            if not 0 <= values[name] <= high:
                raise ValueError('electrical track outside documented range: '+name)
        if self.r61_ohm not in (200, 200000):
            raise ValueError('retain documentary R61 alternatives')
        if min(self.main_load_ohm, self.headphone_input_ohm) <= 0:
            raise ValueError('positive output loads required')


def netlist(s, export):
    s.validate()
    text, metadata = vco.netlist(s.oscillator, export)
    graph = vco.read(GRAPH)
    lines, manifest = [], []
    def node(n):
        return n if n in ('0', 'POS10_V', 'NEG10_V', 'MIX_BUS_BOARD4_PIN4') else 'F4_'+n
    def branch(ref, a, b, value, kind='R'):
        name = (kind if value else 'V')+'F4_'+ref
        lines.append(f'{name} {node(a)} {node(b)} {value:.17g}')
        manifest.append(dict(ref=ref, terminals=[a,b], value=value, kind=kind if value else 'contact'))
    for p in graph['resistors']:
        branch(p['ref'], p['a'], p['b'], p['ohm'])
    for p in graph['capacitors']:
        branch(p['ref'], p['a'], p['b'], p['farad'], 'C')
    for p in graph['transistors']:
        pins = ' '.join(node(p[k]) for k in ('collector','base','emitter'))
        lines.append(f"QF4_{p['ref']} {pins} LAB_{p['polarity']}")
        manifest.append(p)
    # Diode family: exploratory 0.9 V at 100 mA, n=2, DS-458 limit 1 V.
    # Not a measured vintage card; no capacitance or recovery identification.
    vt = 1.380649e-23 * 298.15 / 1.602176634e-19
    diode_is = .1 / math.expm1(.9/(2*vt))
    lines.append(f'.model LAB_458 D(IS={diode_is:.17g} N=2 TNOM=25)')
    for p in graph['diodes']:
        lines.append(f"DF4_{p['ref']} {node(p['anode'])} {node(p['cathode'])} LAB_458")
    branch('R61','BOTTOM','0',s.r61_ohm)
    branch('R73_bottom','REGEN_BOTTOM','BASE_Q30',s.regen_bottom_ohm)
    branch('R73_top','BASE_Q30','EMPHASIS_PIN6',1000-s.regen_bottom_ohm)
    branch('R14_PANEL','EMPHASIS_PIN7','EMPHASIS_PIN6',s.emphasis_ohm)
    branch('R39_low','0','RANGE_WIPER',10000*s.range_fraction)
    branch('R39_high','RANGE_WIPER','POS10_V',10000*(1-s.range_fraction))
    branch('R49','CONTROL_BASE','SCALE_LOW',s.scale_ohm)
    branch('R11_PANEL_low','NEG10_V','CUTOFF_WIPER',5000*s.cutoff_fraction)
    branch('R11_PANEL_high','CUTOFF_WIPER','POS10_V',5000*(1-s.cutoff_fraction))
    branch('R55_PANEL','CUTOFF_WIPER','CONTROL_BASE',200000)
    branch('R51_PANEL','0','CONTROL_BASE',100000)  # J2 normalled ground
    branch('R52_PANEL','0','CONTROL_BASE',33000)   # SW15 OFF
    # SW16/17 OFF -> open. Exact series elimination of unbranched pot ends.
    branch('R19_R14','FIRST_BAL_WIPER','Q16_COLLECTOR',100+s.first_balance_ohm)
    branch('R23_R14','FIRST_BAL_WIPER','Q15_COLLECTOR',100+25-s.first_balance_ohm)
    branch('R18_R12','SECOND_BAL_WIPER','Q14_COLLECTOR',330+s.second_balance_ohm)
    branch('R21_R12','SECOND_BAL_WIPER','Q13_COLLECTOR',330+100-s.second_balance_ohm)
    branch('MAIN_LOAD','MAIN_OUTPUT','0',s.main_load_ohm)
    branch('HEADPHONE_LOAD','HEADPHONE_INPUT','0',s.headphone_input_ohm)
    for ref,n,v in [('contour','LOUDNESS_CONTOUR',s.first_loudness_v),
                    ('external','Q21_BASE',s.second_loudness_base_v),
                    ('amount','CONTOUR_AMOUNT',s.contour_amount_v)]:
        lines.append(f'VF4_{ref} {node(n)} 0 {v:.17g}')
    # The original VCO mixer source must disappear, including at zero volts.
    text = '\n'.join(l for l in text.splitlines() if not l.startswith('Vmixer '))+'\n'
    text = text.replace('.options ', '\n'.join(lines)+'\n.options ', 1)
    text = text.replace('.save '+' '.join(vco.VECTORS), '.save '+' '.join(VECTORS))
    text = text.replace(' '.join(vco.VECTORS)+'\nquit', ' '.join(VECTORS)+'\nquit')
    text = text.replace('RF-D conditional VCO1 CA3046 complete circuit', 'RF-D coupled conditional VCO1 ladder VCAs board outputs', 1)
    metadata.update(schema='rf-d/voice-circuit-netlist/v1', scenario=asdict(s),
                    board4_branches=manifest, boundary_scope=graph['boundaries'],
                    diode_card=dict(n=2, saturation_a=diode_is, reference_v=.9, reference_a=.1))
    for p in (GRAPH,Path(__file__)):
        metadata['source_sha256'][p.relative_to(ROOT).as_posix()] = vco.sha(p)
    return text, metadata


def run(s, label, work, executable, timeout=90):
    if not label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in label):
        raise ValueError('safe unique label required')
    if vco.sha(executable) != vco.EXPECTED_EXE_SHA:
        raise ValueError('recorded ngspice46 binary required')
    work.mkdir(parents=True, exist_ok=True)
    deck, export, log, receipt = [work/f'{label}.{ext}' for ext in ('cir','txt','log','json')]
    if any(p.exists() for p in (deck,export,log,receipt,export.with_suffix('.txt.gz'))):
        raise ValueError('preserve previous attempt')
    text, record = netlist(s,export)
    deck.write_text(text,encoding='utf-8',newline='\n')
    record.update(label=label, deck_sha256=vco.sha(deck), trajectory_complete=False,
        physical_fidelity=False, real_time=False,
        command=[str(executable),'-n','-b',str(deck)], executable_sha256=vco.sha(executable),
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True))
    start = time.perf_counter()
    try:
        p = subprocess.run(record['command'],cwd=executable.parent,capture_output=True,text=True,timeout=timeout)
        output=p.stdout+p.stderr
        log.write_text(output,encoding='utf-8',newline='\n')
        record['exit_code']=p.returncode
        if p.returncode or any(w in output.lower() for w in ('error','aborted','timestep too small')):
            raise ValueError('SPICE reported failure; preserved run log')
        raw=np.loadtxt(export,skiprows=1,ndmin=2)
        if raw.shape[1]!=len(VECTORS)+1 or not np.isfinite(raw).all():
            raise ValueError('invalid export')
        dt=np.diff(raw[:,0])
        if raw[0,0]!=0 or np.any(dt<=0) or abs(raw[-1,0]-s.oscillator.duration_s)>1e-14:
            raise ValueError('incomplete trajectory')
        if dt.max()>s.oscillator.max_step_s*(1+1e-7):
            raise ValueError('maximum timestep exceeded')
        record.update(trajectory_complete=True,rows=len(raw),raw_export_sha256=vco.sha(export))
        export.with_suffix('.txt.gz').write_bytes(gzip.compress(export.read_bytes(),compresslevel=3,mtime=0))
        return raw,record
    except Exception as e:
        record.update(error_type=type(e).__name__,error=str(e))
        if isinstance(e,subprocess.TimeoutExpired):
            log.write_bytes((e.stdout or b'')+(e.stderr or b''))
        if export.exists(): record['partial_export_sha256']=vco.sha(export)
        raise
    finally:
        record['wall_s']=time.perf_counter()-start
        if log.exists(): record['log_sha256']=vco.sha(log)
        record['source_sha256_after']={p:vco.sha(ROOT/p) for p in record['source_sha256']}
        receipt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')


def measure(raw, settle_s=.02):
    core=vco.measure(raw,settle_s)
    a,b=core['reset_crossings_s'][-3],core['reset_crossings_s'][-1]
    t=np.r_[a,raw[(raw[:,0]>a)&(raw[:,0]<b),0],b]
    waves={}
    for k,name in enumerate(EXTRA,start=len(vco.VECTORS)+1):
        x=np.interp(t,raw[:,0],raw[:,k])
        mean=float(np.trapezoid(x,t)/(b-a))
        rms=float(np.sqrt(np.trapezoid((x-mean)**2,t)/(b-a)))
        waves[name]=dict(min=float(x.min()),max=float(x.max()),mean=mean,ac_rms=rms)
    def value(n): return waves['v(f4_'+n+')']
    # Integrated C2 charge equals current delivered through the two R75/R77 legs.
    c2=10e-6
    cols={n:i+1 for i,n in enumerate(VECTORS)}
    q17=np.interp(t,raw[:,0],raw[:,cols['v(f4_q17_collector)']])
    right=np.interp(t,raw[:,0],raw[:,cols['v(f4_c2_right)']])
    main=np.interp(t,raw[:,0],raw[:,cols['v(f4_main_output)']])
    headphone=np.interp(t,raw[:,0],raw[:,cols['v(f4_headphone_input)']])
    delivered=float(np.trapezoid((right-main)/1000+(right-headphone)/1000,t))
    change=float(c2*((q17-right)[-1]-(q17-right)[0]))
    return dict(frequency_hz=core['frequency_hz'], period_spread_relative=core['period_spread_relative'],
        reset_crossings_s=core['reset_crossings_s'], windows=waves,
        c2_charge_change_c=change,c2_delivered_c=delivered,c2_balance_absolute_c=abs(change-delivered),
        output_ac_rms_v=value('main_output')['ac_rms'])
