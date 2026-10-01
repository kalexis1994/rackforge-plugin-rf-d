"""Versioned offline increment coordinates and compensated linear histories.

Same documentary topology and restricted Q25/Q15 laws as the charged network.
Static laws see rounded node potentials; linear capacitor differences retain
two-component histories. No residual relaxation, alternate roots or audio use.
"""
from dataclasses import dataclass
import math
import numpy as np
from circuit66_vca_release_probes import CAPS
from loudness_chain94_reference import State as JointState
from loudness_contour_reference import State as ContourState
from loudness_latch_charge_reference import ChargedNetwork, State


def pair(terms):
    """Rounded sum and its residual, in volts (offline math.fsum)."""
    terms=tuple(float(v) for v in terms)
    if not all(math.isfinite(v) for v in terms):
        raise ValueError("finite compensated voltage terms required")
    high=math.fsum(terms)
    return high,math.fsum((*terms,-high))


@dataclass(frozen=True)
class IncrementState(State):
    node_low_v: tuple
    capacitor_pairs_v: tuple
    circuit_signature: tuple


class IncrementNetwork(ChargedNetwork):
    def __init__(self,r61,parameters):
        super().__init__(r61,parameters)
        # Branch order: 17 audio capacitors, series C10, 3 contour capacitors.
        # Fixed endpoints are ground, fixed BUS=0 and fixed +10 V.
        self.branches=[]
        for left,right,c in CAPS:
            self.branches.append((left,right if isinstance(right,int) else None,
                                  10.0 if right=="PLUS" else 0.0,c,0.0))
        self.branches.append((22,7,0.0,10e-6,25500.0))
        contour=self.joint.contour
        for ref,left,right,c in contour.caps:
            left=contour.alias[left];right=contour.alias[right]
            self.branches.append((66+contour.index[left],
                66+contour.index[right] if right in contour.index else None,
                contour.rails.get(right,0.0),c,0.0))
        self.branches=tuple(self.branches)
        self.signature=(r61,parameters,self.branches)

    def convert(self,old):
        """Lossless lift of a legacy state: existing memories get zero tails."""
        if not isinstance(old,State) or isinstance(old,IncrementState):
            raise ValueError("legacy charged state required for explicit conversion")
        self.latch.evaluate(old.joint.node_v,old.latch,1.0)
        caps=(*old.joint.audio_capacitor_v,old.joint.c10_v,
              *(old.joint.contour.capacitor_v[ref] for ref,_,_,_ in self.joint.contour.caps))
        result=IncrementState(old.joint,old.latch,(0.0,)*self.joint.n,
                              tuple((float(v),0.0) for v in caps),self.signature)
        self.validate(result)
        return result

    def initial_state(self):
        old,diag=super().initial_state()
        return self.convert(old),diag

    def validate(self,old):
        if (not isinstance(old,IncrementState) or old.circuit_signature!=self.signature
                or type(old.node_low_v) is not tuple or len(old.node_low_v)!=self.joint.n
                or type(old.capacitor_pairs_v) is not tuple or len(old.capacitor_pairs_v)!=21
                or len(old.joint.node_v)!=self.joint.n):
            raise ValueError("complete same-circuit compensated history required")
        if not all(math.isfinite(v) for v in (*old.joint.node_v,*old.node_low_v)):
            raise ValueError("finite node history required")
        if any((high,low)!=pair((high,low)) for high,low in zip(old.joint.node_v,old.node_low_v)):
            raise ValueError("normalized node pairs required")
        for high,low in old.capacitor_pairs_v:
            if (high,low)!=pair((high,low)):
                raise ValueError("normalized finite capacitor pairs required")
        mirror=(*old.joint.audio_capacitor_v,old.joint.c10_v,
                *(old.joint.contour.capacitor_v[ref] for ref,_,_,_ in self.joint.contour.caps))
        if tuple(mirror)!=tuple(p[0] for p in old.capacitor_pairs_v):
            raise ValueError("legacy mirror must agree with authoritative capacitor pairs")
        self.latch.evaluate(old.joint.node_v,old.latch,1.0)

    def linear(self,delta,old,dt_s):
        currents=[]
        for (left,right,fixed,c,resistance),(high,low) in zip(self.branches,old.capacitor_pairs_v):
            terms=[old.joint.node_v[left],old.node_low_v[left],delta[left],-high,-low]
            if right is None:terms.append(-fixed)
            else:terms.extend((-old.joint.node_v[right],-old.node_low_v[right],-delta[right]))
            # C10 retains its physical series resistance; all others R=0.
            conductance=1/(dt_s/c+resistance)
            currents.append(conductance*math.fsum(terms))
        return tuple(currents)

    def increment_evaluator(self,key,old,dt_s):
        self.validate(old)
        if not math.isfinite(dt_s) or dt_s<=0:raise ValueError("positive finite interval required")
        static=self.joint.evaluator(key)
        cap_j=np.zeros((self.joint.n,self.joint.n))
        for left,right,_,c,resistance in self.branches:
            g=1/(dt_s/c+resistance)
            cap_j[left,left]+=g
            if right is not None:
                cap_j[right,right]+=g;cap_j[left,right]-=g;cap_j[right,left]-=g
        def evaluate(delta,jacobian=True,use_fd=False):
            delta=np.asarray(delta,dtype=float)
            if delta.shape!=(self.joint.n,) or not np.isfinite(delta).all():
                raise ValueError("complete finite increment candidate required")
            x=np.array([math.fsum((a,b,d)) for a,b,d in zip(old.joint.node_v,old.node_low_v,delta)])
            r,j=static(x,jacobian=jacobian and not use_fd)
            for (left,right,_,_,_),current in zip(self.branches,self.linear(delta,old,dt_s)):
                r[left]+=current
                if right is not None:r[right]-=current
            charge=self.latch.evaluate(x,old.latch,dt_s)
            r+=charge["increment_a"]
            if not jacobian:return r,None
            if use_fd:
                j=np.zeros_like(cap_j)
                for k in range(self.joint.n):
                    a=delta.copy();b=delta.copy();a[k]+=1e-6;b[k]-=1e-6
                    ra,_=evaluate(a,False);rb,_=evaluate(b,False)
                    j[:,k]=(ra-rb)/2e-6
            else:j+=cap_j+charge["capacitance_f"]/dt_s
            return r,j
        return evaluate

    def evaluator(self,key,previous,dt_s,bus_v=0.0):
        if isinstance(previous,IncrementState):
            raise ValueError("use increment_evaluator: absolute coordinates would discard compensated histories")
        return super().evaluator(key,previous,dt_s,bus_v)

    def publish(self,delta,key,old,dt_s):
        nodes=tuple(pair((a,b,d)) for a,b,d in zip(old.joint.node_v,old.node_low_v,delta))
        caps=[]
        currents=self.linear(delta,old,dt_s)
        for k,(left,right,fixed,c,resistance) in enumerate(self.branches):
            if resistance:
                caps.append(pair((*old.capacitor_pairs_v[k],dt_s*currents[k]/c)))
            else:
                terms=nodes[left]+((-fixed,) if right is None else tuple(-v for v in nodes[right]))
                caps.append(pair(terms))
        x=tuple(p[0] for p in nodes)
        mirror=self.joint.state(x,key)
        contour=ContourState(mirror.contour.node_v,
            {ref:caps[18+k][0] for k,(ref,_,_,_) in enumerate(self.joint.contour.caps)})
        joint=JointState(x,tuple(p[0] for p in caps[:17]),caps[17][0],contour)
        return IncrementState(joint,self.latch.prepare(x),tuple(p[1] for p in nodes),
                              tuple(caps),self.signature)

    def step(self,old,key,dt_s,*,use_fd=False,iterations=80,halvings=24):
        if type(iterations) is not int or iterations<1 or type(halvings) is not int or halvings<1:
            raise ValueError("positive integer offline budgets required")
        evaluate=self.increment_evaluator(key,old,dt_s)
        delta=np.zeros(self.joint.n)
        k=66+self.joint.contour.index[self.joint.contour.alias["KEY_DIODE_K"]]
        if key-old.joint.node_v[k]>1.0:delta[k]=key-.3-old.joint.node_v[k]
        for iteration in range(iterations):
            r,j=evaluate(delta,use_fd=use_fd);d=np.linalg.solve(j,-r)
            error=float(np.max(np.abs(r)));correction=float(np.max(np.abs(d)))
            if error<1e-11 and correction<1e-8:
                result=self.publish(delta,key,old,dt_s)
                return result,dict(iterations=iteration,max_kcl_a=error,correction_v=correction,
                                   increment_v=delta.tolist(),coordinate_version="increment-pair/v1")
            for power in range(halvings):
                candidate=delta+2.0**-power*d
                try:
                    rt,_=evaluate(candidate,False);te=float(np.max(np.abs(rt)))
                    if te>=error and not(error<1e-11 and te<1e-11):continue
                    if error<1e-11:
                        rt,jt=evaluate(candidate,use_fd=use_fd)
                        if np.max(np.abs(np.linalg.solve(jt,-rt)))>=correction:continue
                    delta=candidate;break
                except (ValueError,OverflowError,np.linalg.LinAlgError):continue
            else:raise ValueError("increment joint line search exhausted")
        raise ValueError("increment joint iteration budget exhausted")
