"""Loaded three-node BJT lab, fixed accepted charge history, no latch policy."""
from dataclasses import dataclass
import math
import numpy as np
from bjt_charge_reference import Device,History
from junction_charge_reference import finite

KCL_A = 1e-12
CORRECTION_V = 1e-9
RESISTANCE_OHM = (10000.0,3300.0,1000.0)  # synthetic B,C,E lab loads
PWL = ((0.0,0.0),(50e-9,0.0),(70e-9,3.0),(1000e-9,3.0),(1020e-9,0.0),(2000e-9,0.0))


def input_voltage(time_s,polarity):
    finite(time_s)
    if time_s<0 or time_s>PWL[-1][0] or type(polarity)is not int or polarity not in (-1,1):
        raise ValueError("registered time and polarity required")
    for (a,va),(b,vb) in zip(PWL,PWL[1:]):
        if time_s<=b:
            return polarity*(va+(vb-va)*(time_s-a)/(b-a))
    return 0.0


@dataclass(frozen=True)
class State:
    node_v: tuple
    charge: History

    def __post_init__(self):
        if not isinstance(self.node_v,tuple) or len(self.node_v)!=3 or not isinstance(self.charge,History):
            raise ValueError("complete loaded state required")
        finite(*self.node_v)


class Circuit:
    def __init__(self,parameters):
        self.device = Device(parameters)
        self.polarity = parameters.polarity

    def evaluate(self,x,source_v,previous=None,dt_s=None,use_fd=False):
        finite(source_v)
        if previous is not None and not isinstance(previous,State):
            raise ValueError("complete immutable loaded history required")
        result = self.device.evaluate(x,None if previous is None else previous.charge,dt_s)
        rails = (source_v,5.0*self.polarity,0.0)
        r = np.asarray(result.current_a)+[(v-s)/ohm for v,s,ohm in zip(x,rails,RESISTANCE_OHM)]
        j = np.asarray(result.jacobian_s)+np.diag([1/v for v in RESISTANCE_OHM])
        if use_fd:
            j = np.zeros((3,3))
            for col in range(3):
                a,b = np.array(x,copy=True),np.array(x,copy=True)
                a[col]+=1e-6; b[col]-=1e-6
                ra,_,_ = self.evaluate(a,source_v,previous,dt_s)
                rb,_,_ = self.evaluate(b,source_v,previous,dt_s)
                j[:,col] = (ra-rb)/2e-6
        return r,j,result

    def solve(self,seed,source_v,previous=None,dt_s=None,*,use_fd=False,iterations=40,halvings=24):
        if type(iterations)is not int or type(halvings)is not int or min(iterations,halvings)<1:
            raise ValueError("positive integer solve budgets required")
        x = np.asarray(seed,dtype=float).copy()
        for iteration in range(iterations):
            r,j,result = self.evaluate(x,source_v,previous,dt_s,use_fd)
            direction = np.linalg.solve(j,-r)
            error,correction = float(np.max(np.abs(r))),float(np.max(np.abs(direction)))
            if error<KCL_A and correction<CORRECTION_V:
                return State(tuple(map(float,x)),result.candidate),dict(iterations=iteration,max_kcl_a=error,correction_v=correction)
            for power in range(halvings):
                trial = x+2.0**-power*direction
                try:
                    rt,jt,_ = self.evaluate(trial,source_v,previous,dt_s,use_fd)
                    next_error = float(np.max(np.abs(rt)))
                    accept = next_error<error
                    if error<KCL_A:
                        accept = next_error<KCL_A and np.max(np.abs(np.linalg.solve(jt,-rt)))<correction
                    if accept:
                        x = trial
                        break
                except (ValueError,np.linalg.LinAlgError):
                    continue
            else:
                raise ValueError("loaded BJT line-search budget exhausted")
        raise ValueError("loaded BJT iteration budget exhausted")

    def initial(self,use_fd=False):
        return self.solve((0,5*self.polarity,0),0,use_fd=use_fd)
