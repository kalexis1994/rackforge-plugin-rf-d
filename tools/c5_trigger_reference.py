"""Original dual-contour branches, explicit Amount cursor, independent FD DC.

The original volume graph is frozen; filter/trigger additions follow reviewed
SVC-9 p9/p19. No native solver or reduced Amount matrix is imported.
"""
import json
import math
import struct
from decimal import Decimal, localcontext
from pathlib import Path
import loudness_contour_reference as volume_oracle
from loudness_contour_reference import Network, Controls, State
# Runtime policy for this new bank; the frozen source is not edited.
volume_oracle.KCL_A=1e-12
volume_oracle.CORRECTION_V=2e-9
from filter_ladder_ebers_moll_dc_reference import _solve_linear

ROOT=Path(__file__).resolve().parents[1]
VOLUME=['FOLLOWER_BASE','FOLLOWER_MID','FOLLOWER_SUPPLY','LOUDNESS_OUT','RESET_FEEDBACK','TIMING_C2','ATTACK_PNP_BASE','ATTACK_OUT','ATTACK_PANEL_IN','DECAY_DRIVER_EMITTER','DECAY_SWITCH_BASE','DECAY_OUT','SUSTAIN_WIPER','SUSTAIN_BASE','SUSTAIN_DRIVER_EMITTER','SUSTAIN_COLLECTOR','FAST_DIODE_K','RESET_DRIVER','TRIGGER_COLLECTOR','Q12_BASE','Q20_BASE','KEY_RC','KEY_DIODE_K','C4_LEFT','RESET_DIODE_A','SET_BASE','RESET_COLLECTOR','RESET_BASE','ATTACK_GATE_LOWER']
FILTER=['F_Q22B','F_Q22C_Q21B','F_Q21E','F_OUT','F_FEEDBACK','F_Q26B','F_Q26E_Q28B','F_Q26C','F_Q28C']
TIMER=['F_C5','F_Q1B','F_Q1C','F_Q4B','F_Q4C','F_Q5B','F_Q5C','F_Q6E','F_Q7B','F_Q7C','F_SUSTE','F_Q8B','F_Q8C','F_SUSTW','F_C1L','F_CR1A']
NAMES=VOLUME+FILTER+TIMER
RAILS=['GROUND','CONTOUR_SUPPLY','MINUS_10','PLUS_10','KEYBOARD_TRIGGER','VCA_CONTROL_LOAD','TAIL','CUTOFF_TH','RANGE_TH']
CAPS=[(5,54,1e-5),(21,54,1e-7),(23,25,1e-8),(38,54,1e-5),(52,39,1e-8),(48,54,1e-10),(34,54,1e-10)]
LATCH=[(25,26),(27,28),(39,40),(41,42),(19,17),(20,18)]


def network(optional=False,short=False):
    n=Network(Controls(attack_ohm=1000.,decay_ohm=10000.,external_s_short=short))
    n.rails.update(VCA_CONTROL_LOAD=0.,TAIL=1.4,CUTOFF_TH=0.,RANGE_TH=1.)
    n.resistors += [('R59','LOUDNESS_OUT','VCA_CONTROL_LOAD',68000.),
                    ('LHC_FLOATING_ALIAS','FAST_DIODE_K','RESET_DRIVER',1500.)]
    def r(name,a,b,value):n.resistors.append((name,a,b,value))
    for name,a,b,value in [
        ('F_R48','F_C5','F_Q22B',10000.),('F_R50','CONTOUR_SUPPLY','F_Q21E',560.),
        ('F_R33','F_OUT','F_FEEDBACK',5600.),('F_R29','F_FEEDBACK','MINUS_10',16900.),
        ('AMOUNT_UPPER','F_OUT','AMOUNT_CURSOR',25000.),('AMOUNT_LOWER','AMOUNT_CURSOR','GROUND',25000.),
        ('R74','AMOUNT_CURSOR','F_Q26B',47000.),('CUTOFF_KNOB','F_Q26B','CUTOFF_TH',201250.),
        ('SCALE','F_Q26B','GROUND',2050.),('R51_NO_PLUG','F_Q26B','GROUND',100000.),
        ('R52_MOD_OFF','F_Q26B','GROUND',33000.),('RANGE','F_Q26E_Q28B','RANGE_TH',68900.),
        ('R45_FILTER','F_Q26C','MINUS_10',330.),('R60_FILTER','F_Q28C','TAIL',680.),
        ('F_R32','CONTOUR_SUPPLY','RESET_DRIVER',10000.),('F_R37','CONTOUR_SUPPLY','TRIGGER_COLLECTOR',10000.),
        ('F_R35','TRIGGER_COLLECTOR','F_CR1A',10000.),('F_R26','RESET_DRIVER','F_C1L',10000.),
        ('F_R3','F_Q4C','F_Q1B',10000.),('F_R4','CONTOUR_SUPPLY','F_Q4C',10000.),
        ('F_R14','F_Q1C','F_Q4B',33000.),('F_R6','CONTOUR_SUPPLY','F_Q5B',560.),
        ('F_R5','F_Q5B','F_Q1C',3300.),('F_R1_ATTACK_ZERO_CONTACT','F_Q5C','F_C5',100.),
        ('F_R8','F_Q6E','MINUS_10',10000.),('F_R9','F_Q6E','F_Q7B',4700.),
        ('F_PANEL_R15','F_Q7C','F_C5',1000.),('F_R10','CONTOUR_SUPPLY','F_SUSTE',27000.),
        ('F_R13','F_SUSTW','F_Q8B',4700.),('F_BOARD_R17','F_Q8B','MINUS_10',150000.),
        ('F_R11','F_Q8C','GROUND',100.),('F_R18_LOW','F_SUSTW','GROUND',2500.),
        ('F_R18_HIGH','F_SUSTW','PLUS_10',2500.)]:r(name,a,b,value)
    for name,kind,b,c,e in [
        ('F_Q22','NPN','F_Q22B','F_Q22C_Q21B','F_OUT'),
        ('F_Q21','PNP','F_Q22C_Q21B','F_OUT','F_Q21E'),
        ('F_Q26','PNP','F_Q26B','F_Q26C','F_Q26E_Q28B'),
        ('F_Q28','NPN','F_Q26E_Q28B','F_Q28C','GROUND'),
        ('F_Q1','NPN','F_Q1B','F_Q1C','GROUND'),('F_Q4','NPN','F_Q4B','F_Q4C','GROUND'),
        ('F_Q5','PNP','F_Q5B','F_Q5C','CONTOUR_SUPPLY'),('F_Q6','NPN','F_Q1C','CONTOUR_SUPPLY','F_Q6E'),
        ('F_Q7','NPN','F_Q7B','F_Q7C','F_SUSTE'),('F_Q8','PNP','F_Q8B','F_Q8C','F_SUSTE')]:
        n.bjts=list(n.bjts)+[dict(ref=name,kind=kind,base=b,collector=c,emitter=e)]
    for name,a,c,mark in [('F_CR3','F_FEEDBACK','F_Q4B','1N34A'),('F_CR1','F_CR1A','F_Q4B','1N34A'),('F_CR2','F_SUSTE','RESET_DRIVER','1N4004')]:
        n.diodes=list(n.diodes)+[dict(ref=name,anode=a,cathode=c,marking=mark)]
    n.nodes=NAMES+['AMOUNT_CURSOR'];n.index={v:k for k,v in enumerate(n.nodes)}
    n.alias={v:v for v in set(n.nodes)|set(n.rails)}
    n.optional=optional
    return n


def expanded(x):
    # Independent original three-resistor star; native Amount uses G reduction.
    cursor=(x[32]/25000.+x[34]/47000.)/(2./25000.+1./47000.)
    return list(x)+[cursor]


def dc_seed():
    old=Network(Controls(attack_ohm=1000.,decay_ohm=10000.),load_conductance_s=1./68000.)
    s,_=old.initial_state()
    vol=[s.node_v.get(n,s.node_v['RESET_DRIVER']) for n in VOLUME]
    f=[.3,8.75,9.25,.0,-2.,.005,.52,-9.998,1.39]
    timer=[.85,.01,8.3,.7,.03,9.15,.85,7.6,1.,.85,.7,4.8,.001,5.,.03,1.1]
    return vol+f+timer


def fd(function,x,h=1e-6):
    columns=[]
    for k in range(len(x)):
        lo,hi=x.copy(),x.copy();lo[k]-=h;hi[k]+=h
        columns.append([(a-b)/(2*h) for a,b in zip(function(hi),function(lo))])
    return [list(v) for v in zip(*columns)]


def root(n,seed):
    s,d=n.solve(seed,0.,use_fd=True,iterations=100,halvings=28)
    assert d['max_kcl_a']<=1e-12 and d['correction_v']<=2e-9,d
    return [s.node_v[name] for name in n.nodes],d


def prepare(directory):
    directory=Path(directory);directory.mkdir(exist_ok=True)
    seed=dc_seed();results=[]
    for optional in [False,True]:
        n=network(optional);x,d=root(n,expanded(seed))
        (directory/f'seed{int(optional)}.bin').write_bytes(struct.pack('<54d',*seed))
        results.append(dict(optional=optional,original_root=x,diagnostics=d))
    return dict(nodes=NAMES,original_nodes=NAMES+['AMOUNT_CURSOR'],dc=results,
                original_resistors=[dict(ref=r[0],a=r[1],b=r[2],ohm=r[3]) for r in n.resistors],
                original_transistors=n.bjts,original_diodes=n.diodes)


def D(v):return Decimal.from_float(v)


def junction(v,be):
    c,vp,m=map(D,[7e-12,.75,.5] if be else [5e-12,.7,.33]);fc=D(.4);vf=fc*vp
    def low(w):return c*vp/(1-m)*(1-(1-w/vp)**(1-m))
    if v<vf:q=low(v)
    else:
        cf=c*(1-fc)**(-m);slope=cf*m/(vp*(1-fc));z=v-vf
        q=low(vf)+z*(cf+slope*z/2)
    vt=D(1.380649e-23*298.15/1.602176634e-19)
    return q+D(1e-9 if be else 3e-9)*D(1e-14)*((v/vt).exp()-1)


def charge_increment(old,now,optional):
    with localcontext() as ctx:
        ctx.prec=65
        a=[D(h)+D(l) for h,l in zip(old[:54],old[54:])]+[Decimal(0),D(9.3)]
        b=[D(h)+D(l) for h,l in zip(now[:54],now[54:])]+[Decimal(0),D(9.3)]
        q=[Decimal(0)]*54
        pairs=list(CAPS)+([(30,31,47e-12),(31,55,500e-12)] if optional else [])
        for i,j,c in pairs:
            diff=D(c)*((b[i]-b[j])-(a[i]-a[j]));q[i]+=diff
            if j<54:q[j]-=diff
        for base,col in LATCH:
            be=junction(b[base],True)-junction(a[base],True)
            bc=junction(b[base]-b[col],False)-junction(a[base]-a[col],False)
            q[base]+=be+bc;q[col]-=bc
        return [float(v) for v in q]


if __name__=='__main__':
    import sys
    print(json.dumps(prepare(sys.argv[1]),indent=2))
