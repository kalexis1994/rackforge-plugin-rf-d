"""Conditioned Q25/Q15 charge stamps and simultaneous 94-node replay.

SVC-9 Fig.9-7 connectivity from loudness_contour_graph; synthetic low-injection
laws only. Eight other contour BJTs and all audio semiconductors remain static.
No choice of latch root, physical transition, or native audio admission.
"""
from dataclasses import dataclass
import math
import numpy as np
from bjt_charge_reference import Device, History as DeviceHistory
from loudness_chain94_reference import JointNetwork, State as JointState


@dataclass(frozen=True)
class History:
    layout: tuple
    devices: tuple

    def __post_init__(self):
        if type(self.layout) is not tuple or type(self.devices) is not tuple or len(self.devices)!=2:
            raise ValueError("immutable complete latch history required")
        if any(not isinstance(h,DeviceHistory) for h in self.devices):
            raise ValueError("typed device histories required")


class LatchCharge:
    def __init__(self,contour,offset,n,parameters):
        if type(offset) is not int or type(n) is not int or offset<0 or n<offset+len(contour.nodes):
            raise ValueError("complete circuit node layout required")
        d=contour.devices
        p=parameters
        if (p.polarity,p.saturation_a,p.beta_forward,p.beta_reverse,p.emission_be_v,p.emission_bc_v)!=(
                1,d.is_a,d.beta_forward,d.beta_reverse,contour.vt,contour.vt):
            raise ValueError("charge law must share the existing static BJT hypothesis")
        self.n=n
        self.device=Device(p)
        self.terminals=[]
        for ref in ("Q25","Q15"):
            part=next(p for p in contour.bjts if p["ref"]==ref)
            if part["kind"]!="NPN":raise ValueError("registered latch polarity required")
            row=[]
            for terminal in ("base","collector","emitter"):
                name=contour.alias[part[terminal]]
                row.append((offset+contour.index[name],None) if name in contour.index else (None,contour.rails[name]))
            self.terminals.append(tuple(row))
        self.layout=(n,tuple(self.terminals))

    def evaluate(self,x,previous=None,dt_s=None):
        x=np.asarray(x,dtype=float)
        if x.shape!=(self.n,) or not np.isfinite(x).all():raise ValueError("complete finite circuit candidate required")
        if previous is None:
            if dt_s is not None:raise ValueError("interval without latch history is ambiguous")
        elif (not isinstance(previous,History) or previous.layout!=self.layout
              or dt_s is None or not math.isfinite(dt_s) or dt_s<=0):
            raise ValueError("same-layout history and positive interval required")
        q=np.zeros(self.n); c=np.zeros((self.n,self.n)); increment=np.zeros(self.n)
        candidates=[]; junction_caps=[]
        for k,terminals in enumerate(self.terminals):
            voltage=tuple(x[i] if i is not None else fixed for i,fixed in terminals)
            old=None if previous is None else previous.devices[k]
            evaluation=self.device.evaluate(voltage,old,dt_s)
            candidates.append(evaluation.candidate)
            # In this restricted conservative subset, BE/BC are positive branches.
            junction_caps.append((evaluation.capacitance_f[2][2],evaluation.capacitance_f[1][1]))
            if old is not None:
                old_q=(old.be_c+old.bc_c,-old.bc_c,-old.be_c)
            for a,(i,_) in enumerate(terminals):
                if i is None:continue
                q[i]+=evaluation.terminal_charge_c[a]
                if old is not None:increment[i]+=(evaluation.terminal_charge_c[a]-old_q[a])/dt_s
                for b,(j,_) in enumerate(terminals):
                    if j is not None:c[i,j]+=evaluation.capacitance_f[a][b]
        return dict(charge_c=q,capacitance_f=c,increment_a=increment,
                    candidate=History(self.layout,tuple(candidates)),junction_cap_f=tuple(junction_caps))

    def prepare(self,x):
        """Initialize only from explicitly supplied circuit nodes; no DC claim."""
        return self.evaluate(x)["candidate"]

    def capacitors(self,x):
        values=self.evaluate(x)["junction_cap_f"]
        result=[]
        for terminals,(be,bc) in zip(self.terminals,values):
            b,c,e=[i for i,_ in terminals]
            result.extend(((b,e,be),(c,b,bc)))
        return result


@dataclass(frozen=True)
class State:
    joint: JointState
    latch: History


class ChargedNetwork:
    def __init__(self,r61,parameters):
        self.joint=JointNetwork(r61)
        self.latch=LatchCharge(self.joint.contour,66,self.joint.n,parameters)

    def prepare(self,accepted_joint):
        # Preserves all 21 older capacitor histories. This is a declared
        # conditioned starting point, not a recomputed trajectory or reset.
        if not isinstance(accepted_joint,JointState):raise ValueError("accepted joint state required")
        return State(accepted_joint,self.latch.prepare(accepted_joint.node_v))

    def initial_state(self):
        joint,diagnostics=self.joint.initial_state()
        return self.prepare(joint),diagnostics

    def step(self,previous,key,dt_s,**budget):
        seed=list(previous.joint.node_v)
        k=66+self.joint.contour.index[self.joint.contour.alias["KEY_DIODE_K"]]
        # A Newton seed for the algebraic source diode, never a history edit.
        if key-seed[k]>1.0:seed[k]=key-.3
        return self.solve(seed,key,previous,dt_s,**budget)

    def evaluator(self,key,previous,dt_s,bus_v=0.0):
        if not isinstance(previous,State):raise ValueError("complete charged joint state required")
        base=self.joint.evaluator(key,previous.joint,dt_s,bus_v)
        # Validate even before the first Newton trial.
        self.latch.evaluate(previous.joint.node_v,previous.latch,dt_s)
        def evaluate(x,jacobian=True,use_fd=False):
            r,j=base(x,jacobian=jacobian and not use_fd)
            charge=self.latch.evaluate(x,previous.latch,dt_s)
            r=r+charge["increment_a"]
            if not jacobian:return r,None
            if use_fd:
                j=np.zeros((self.joint.n,self.joint.n))
                for k in range(self.joint.n):
                    a=np.array(x,copy=True);b=np.array(x,copy=True);a[k]+=1e-6;b[k]-=1e-6
                    ra,_=evaluate(a,False);rb,_=evaluate(b,False)
                    j[:,k]=(ra-rb)/2e-6
            else:j=j+charge["capacitance_f"]/dt_s
            return r,j
        return evaluate

    def solve(self,seed,key,previous,dt_s,*,use_fd=False,iterations=80,halvings=24):
        if type(iterations) is not int or iterations<1 or type(halvings) is not int or halvings<1:
            raise ValueError("positive integer offline budgets required")
        evaluate=self.evaluator(key,previous,dt_s)
        x=np.array(seed,dtype=float,copy=True)
        for iteration in range(iterations):
            r,j=evaluate(x,use_fd=use_fd)
            d=np.linalg.solve(j,-r)
            error=float(np.max(np.abs(r)));correction=float(np.max(np.abs(d)))
            if error<1e-11 and correction<1e-8:
                joint=self.joint.state(x,key,previous.joint,dt_s)
                latch=self.latch.evaluate(x,previous.latch,dt_s)["candidate"]
                return State(joint,latch),dict(iterations=iteration,max_kcl_a=error,correction_v=correction)
            for power in range(halvings):
                trial=x+2.0**-power*d
                try:
                    rt,_=evaluate(trial,False);te=float(np.max(np.abs(rt)))
                    if te>=error and not(error<1e-11 and te<1e-11):continue
                    if error<1e-11:
                        rt,jt=evaluate(trial,use_fd=use_fd)
                        if np.max(np.abs(np.linalg.solve(jt,-rt)))>=correction:continue
                    x=trial;break
                except (ValueError,OverflowError,np.linalg.LinAlgError):continue
            else:raise ValueError("charged joint line search exhausted")
        raise ValueError("charged joint iteration budget exhausted")
