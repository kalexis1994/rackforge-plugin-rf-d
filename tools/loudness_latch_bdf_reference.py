"""Offline variable-step BDF2 on charge, with two accepted histories.

Quadratic interpolation at t, t-h, t-h-k gives a0=(1+2r)/(1+r),
a1=-(1+r), a2=r*r/(1+r), r=h/k. The derivative is evaluated as
[a0*(Qnew-Qold)-a2*(Qold-Qolder)]/h, avoiding absolute charge origins.
Static laws, topology and Newton gates are the existing conditioned model.
"""
from dataclasses import dataclass
import math
from loudness_chain94_reference import State as JointState
from loudness_contour_reference import State as ContourState
from loudness_latch_charge_reference import History as LatchHistory
from bjt_charge_reference import History as DeviceHistory
from loudness_latch_increment_reference import IncrementNetwork,IncrementState,pair


def coefficients(h,k):
    if not all(math.isfinite(v) and v>0 for v in (h,k)):
        raise ValueError("two positive finite adjacent intervals required")
    ratio=h/k
    if not math.isfinite(ratio) or not 0<ratio<=2:
        raise ValueError("finite positive BDF2 ratio with interval growth at most two required")
    a0=(1+2*ratio)/(1+ratio);a2=ratio*ratio/(1+ratio)
    return dict(ratio=ratio,a0=a0,a1=-(1+ratio),a2=a2,effective_dt_s=h/a0,gamma=a2/a0)


@dataclass(frozen=True)
class History:
    current: IncrementState
    previous: IncrementState | None
    previous_dt_s: float | None
    time_s: float
    key_v: float
    previous_key_v: float | None

    def __post_init__(self):
        if not isinstance(self.current,IncrementState) or not math.isfinite(self.time_s) or self.time_s<0 or not math.isfinite(self.key_v):
            raise ValueError("complete current state, source and finite nonnegative time required")
        if self.previous is None:
            if self.previous_dt_s is not None or self.previous_key_v is not None or self.time_s!=0:
                raise ValueError("only explicit initial DC may lack the preceding state")
        elif (not isinstance(self.previous,IncrementState) or self.previous_dt_s is None
                or not math.isfinite(self.previous_dt_s) or not 0<self.previous_dt_s<=self.time_s
                or self.previous_key_v is None or not math.isfinite(self.previous_key_v)):
            raise ValueError("two accepted states with their adjacent interval and sources required")


class BdfNetwork:
    def __init__(self,r61,parameters):
        self.network=IncrementNetwork(r61,parameters)

    def initial_history(self):
        state,diag=self.network.initial_state()
        return History(state,None,None,0.,0.,None),diag

    def validate(self,history):
        if not isinstance(history,History):raise ValueError("versioned two-state history required")
        self.network.validate(history.current)
        if history.previous is not None:self.network.validate(history.previous)

    def effective_history(self,history,h):
        """Virtual derivative coefficients, never published as a physical state."""
        self.validate(history)
        if history.previous is None:raise ValueError("BDF2 requires a preceding accepted interval")
        c=coefficients(h,history.previous_dt_s);gamma=c["gamma"]
        old,older=history.current,history.previous
        caps=tuple(pair((*a,gamma*math.fsum((*a,*(-v for v in b)))))
                   for a,b in zip(old.capacitor_pairs_v,older.capacitor_pairs_v))
        devices=tuple(DeviceHistory(a.parameters,
            math.fsum((a.be_c,gamma*(a.be_c-b.be_c))),
            math.fsum((a.bc_c,gamma*(a.bc_c-b.bc_c)))) for a,b in zip(old.latch.devices,older.latch.devices))
        contour=ContourState(old.joint.contour.node_v,
            {ref:caps[18+k][0] for k,(ref,_,_,_) in enumerate(self.network.joint.contour.caps)})
        joint=JointState(old.joint.node_v,tuple(v[0] for v in caps[:17]),caps[17][0],contour)
        virtual=IncrementState(joint,LatchHistory(old.latch.layout,devices),old.node_low_v,caps,old.circuit_signature)
        self.network.validate(virtual)
        return virtual,c

    def advance(self,history,key,h,**budget):
        self.validate(history)
        if not math.isfinite(key) or not math.isfinite(h) or h<=0:
            raise ValueError("finite source and positive interval required")
        if history.previous is None:
            # Only startup; no fallback or restart after a failed BDF solve.
            state,diag=self.network.step(history.current,key,h,**budget)
            diag=dict(diag,method="backward-euler-startup",actual_dt_s=h)
        else:
            virtual,c=self.effective_history(history,h)
            state,diag=self.network.step(virtual,key,c["effective_dt_s"],**budget)
            diag=dict(diag,method="variable-bdf2-charge/v1",actual_dt_s=h,coefficients=c)
        return History(state,history.current,h,history.time_s+h,key,history.key_v),diag
