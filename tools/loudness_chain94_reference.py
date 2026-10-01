"""Offline simultaneous full contour and BUS-to-J7 chain (94 interior nodes).

SVC-9 Figs.9-7/9-11/9-8/9-17, pp.9/13/10/19. R59 is one physical
branch; all 21 capacitor histories share ONE interval. No latch policy.
Requires NumPy for this laboratory, never called by the plugin.
"""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import numpy as np

from circuit66_dc_vectors import dc_evaluator
from circuit66_r21_vectors import charges
from circuit66_vca_dc_vectors import boundary_values
from circuit66_vca_release_probes import transient_evaluator
from cutoff_j7_vectors import setup
from loudness_contour_reference import Network, Controls, State as ContourState

ROOT=Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class State:
    node_v:tuple
    audio_capacitor_v:tuple
    c10_v:float
    contour:ContourState


class JointNetwork:
    def __init__(self,r61=200,controls=Controls()):
        self.contour=Network(controls,load_conductance_s=1/68000)
        self.values=boundary_values(setup(r61),0.0,2.0)
        self.r61=r61
        self.out=66+self.contour.index[self.contour.alias["LOUDNESS_OUT"]]
        self.n=66+len(self.contour.nodes)
        self.dc=dc_evaluator(self.values,self.values[4])

    def evaluator(self,keyboard_v,previous=None,dt_s=None,bus_v=0.0):
        if not math.isfinite(bus_v):raise ValueError("finite BUS required")
        if previous is None:
            audio=self.dc
        else:
            if len(previous.node_v)!=self.n or not all(math.isfinite(v) for v in previous.node_v):
                raise ValueError("complete finite previous joint nodes required")
            if dt_s is None or not math.isfinite(dt_s) or dt_s<=0:
                raise ValueError("positive finite joint transient interval required")
            if len(previous.audio_capacitor_v)!=17 or not all(math.isfinite(v) for v in previous.audio_capacitor_v) or not math.isfinite(previous.c10_v):
                raise ValueError("complete finite eighteen audio capacitor histories required")
            audio=transient_evaluator(self.values,
                dict(capacitor_v=previous.audio_capacitor_v,c10_v=previous.c10_v),
                dict(bus_v=bus_v,loudness_v=0.0,q21_base_v=2.0,dt_s=dt_s))
        old=None if previous is None else previous.contour

        def evaluate(x,jacobian=True,use_fd=False):
            if len(x)!=self.n or not np.isfinite(x).all():raise ValueError("finite joint candidate required")
            ar,_=audio(list(x[:66]))
            # Independent audio oracle's first 48 rows use incoming current.
            # All joint rows are outgoing physical KCL in A; R21 is interior.
            r=np.array([-v if i<48 else v for i,v in enumerate(ar)]+[0.0]*(self.n-66))
            cr,cj=self.contour.evaluate(list(x[66:]),keyboard_v,old,dt_s,jacobian=jacobian and not use_fd)
            r[66:]=cr
            r[32]-=x[self.out]/68000
            r[self.out]-=x[32]/68000
            if not jacobian:return r,None
            j=np.zeros((self.n,self.n))
            if use_fd:
                for k in range(self.n):
                    a=np.array(x,copy=True);b=np.array(x,copy=True)
                    a[k]+=1e-6;b[k]-=1e-6
                    ra,_=evaluate(a,False);rb,_=evaluate(b,False)
                    j[:,k]=(ra-rb)/2e-6
            else:
                for k in range(66):
                    a=list(x[:66]);b=list(x[:66]);a[k]+=1e-6;b[k]-=1e-6
                    ra,_=audio(a);rb,_=audio(b)
                    j[:66,k]=np.array([(u-v)/2e-6 for u,v in zip(ra,rb)])
                    j[:48,k]*=-1
                j[66:,66:]=cj
                j[32,self.out]=-1/68000
                j[self.out,32]=-1/68000
            return r,j
        return evaluate

    def state(self,x,keyboard_v,previous=None,dt_s=None,bus_v=0.0):
        values=dict(self.contour.rails,KEYBOARD_TRIGGER=keyboard_v)
        values.update(zip(self.contour.nodes,map(float,x[66:])))
        values.update({name:values[alias] for name,alias in self.contour.alias.items()})
        contour=ContourState(values,{ref:values[a]-values[b] for ref,a,b,_ in self.contour.caps})
        c10=x[22]-x[7]
        if previous is not None:
            gc=10e-6/dt_s
            i10=gc/(1+gc*25500)*(c10-previous.c10_v)
            c10-=25500*i10
        return State(tuple(map(float,x)),tuple(charges(x[:66],bus_v)),float(c10),contour)

    def solve(self,seed,keyboard_v,previous=None,dt_s=None,bus_v=0.0,*,use_fd=False,iterations=80,halvings=24):
        if type(iterations)is not int or iterations<1 or type(halvings)is not int or halvings<1:
            raise ValueError("positive integer offline budgets required")
        evaluate=self.evaluator(keyboard_v,previous,dt_s,bus_v)
        x=np.array(seed,dtype=float,copy=True)
        cached=None
        for iteration in range(iterations):
            if cached is None:
                r,j=evaluate(x,use_fd=use_fd)
                d=np.linalg.solve(j,-r)
            else:r,d=cached;cached=None
            error=float(np.max(np.abs(r)));correction=float(np.max(np.abs(d)))
            if error<1e-11 and correction<1e-8:
                return self.state(x,keyboard_v,previous,dt_s,bus_v),dict(iterations=iteration,max_kcl_a=error,
                    correction_v=correction,unknowns=self.n)
            for power in range(halvings):
                trial=x+2.0**-power*d
                try:
                    rt,_=evaluate(trial,False);te=float(np.max(np.abs(rt)))
                    if te>=error and not(error<1e-11 and te<1e-11):continue
                    rt,jt=evaluate(trial,use_fd=use_fd)
                    td=np.linalg.solve(jt,-rt)
                    if error<1e-11 and np.max(np.abs(td))>=correction:continue
                    x=trial;cached=(rt,td);break
                except (ValueError,OverflowError,np.linalg.LinAlgError):continue
            else:raise ValueError(f"joint line search: KCL={error}, correction={correction}")
        raise ValueError("joint iteration budget exhausted")

    def initial_state(self,*,use_fd=False):
        isolated,_=self.contour.initial_state()
        fixture=json.loads((ROOT/"evidence/circuit71_loudness_vectors.json").read_text())
        case=next(c for c in fixture["cases"] if c["r61_ohm"]==self.r61 and c["reset_base_v"]==.7)
        seed=case["dc_rows"][0]["node_v"][:66]+[isolated.node_v[n] for n in self.contour.nodes]
        return self.solve(seed,0.0,use_fd=use_fd)

    def step(self,previous,keyboard_v,dt_s,bus_v=0.0,**budget):
        seed=list(previous.node_v)
        k=66+self.contour.index[self.contour.alias["KEY_DIODE_K"]]
        if keyboard_v-seed[k]>1.0:seed[k]=keyboard_v-.3
        return self.solve(seed,keyboard_v,previous,dt_s,bus_v,**budget)

    def probe_step_roots(self,previous,keyboard_v,dt_s,bus_v=0.0,*,use_fd=False):
        roots=[];rejected=[]
        def attempt(seed,policy):
            try:
                state,diag=self.solve(seed,keyboard_v,previous,dt_s,bus_v,use_fd=use_fd)
                if all(max(abs(a-b) for a,b in zip(state.node_v,r["state"].node_v))>=1e-6 for r in roots):
                    roots.append(dict(state=state,diagnostics=diag,seed_policy=policy))
            except (ValueError,np.linalg.LinAlgError) as exc:rejected.append(dict(seed_policy=policy,error=str(exc)))
        seed=list(previous.node_v)
        k=66+self.contour.index[self.contour.alias["KEY_DIODE_K"]]
        if keyboard_v-seed[k]>1.0:seed[k]=keyboard_v-.3
        attempt(seed,"previous")
        # Same diagnostic latch/trigger seeds as the earlier isolated probe.
        for active in (False,True):
            for trigger_on in (False,True):
                v=dict(previous.contour.node_v)
                v.update(SET_BASE=.7 if active else .01,RESET_BASE=.01 if active else .7,
                    RESET_COLLECTOR=.05 if active else 8.3,ATTACK_GATE_LOWER=5.0 if active else .01,
                    ATTACK_PNP_BASE=8.6 if active else 9.15,DECAY_DRIVER_EMITTER=-.6 if active else 7.6,
                    DECAY_SWITCH_BASE=-.6 if active else min(7.6,v["SUSTAIN_DRIVER_EMITTER"]+.7),
                    Q12_BASE=.01 if trigger_on else .7,RESET_DRIVER=9.0 if trigger_on else .03,
                    TRIGGER_COLLECTOR=.05 if trigger_on else 6.0,Q20_BASE=.7 if trigger_on else .01,
                    RESET_DIODE_A=.05 if trigger_on else 1.1)
                v["KEY_DIODE_K"]=max(v["KEY_DIODE_K"],keyboard_v-.3)
                attempt(list(previous.node_v[:66])+[v[n] for n in self.contour.nodes],
                        f"latch_{int(active)}_trigger_{int(trigger_on)}")
        return dict(roots=roots,rejected=rejected,selected=None)
