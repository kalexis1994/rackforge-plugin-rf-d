"""Offline adaptive backward Euler with complete unpublished trial histories.

Step doubling is an error estimate, not a separate circuit oracle. Frozen
positive-mode guards are numerical diagnostics, not trajectory stability.
"""
from dataclasses import dataclass
import math
import numpy as np
from loudness_latch_charge_reference import LatchCharge,State
from loudness_descriptor_stability import joint_static,reduced_modes


@dataclass(frozen=True)
class Policy:
    voltage_abs_v: float
    voltage_relative: float
    charge_abs_c: float
    charge_relative: float
    junction_increment_v: float
    positive_mode_step_product: float
    maximum_step_s: float
    minimum_step_s: float
    maximum_attempts: int

    def __post_init__(self):
        values=tuple(v for k,v in vars(self).items() if k!="maximum_attempts")
        if any(not math.isfinite(v) or v<=0 for v in values) or self.minimum_step_s>self.maximum_step_s:
            raise ValueError("positive finite adaptive policy and ordered interval limits required")
        if type(self.maximum_attempts) is not int or self.maximum_attempts<1:
            raise ValueError("positive integer attempt budget required")


def voltages(network,state):
    result=[]
    for terminals in network.latch.terminals:
        b,c,e=[state.joint.node_v[i] if i is not None else fixed for i,fixed in terminals]
        result.extend((b-e,b-c))
    return np.array(result)


def charges(state):
    return np.array([q for d in state.latch.devices for q in (d.be_c,d.bc_c)])


def scaled_error(a,b,absolute,relative):
    a,b=np.asarray(a),np.asarray(b)
    return float(np.max(np.abs(a-b)/(absolute+relative*np.maximum(np.abs(a),np.abs(b)))))


def frozen_rate(network,state,key):
    x=list(state.joint.node_v)
    g,caps=joint_static(network.joint,x,key)
    latch=LatchCharge(network.joint.contour,66,len(g),network.latch.device.parameters)
    modes=reduced_modes(g,caps+latch.capacitors(np.array(x+[x[7]])),1.0)
    if modes["coordinate_error"]>=1e-12 or modes["max_eigen_residual"]>=1e-9:
        raise ValueError("frozen descriptor failed its existing coordinate/eigen-residual gates")
    return max(0.0,modes["max_real_per_s"])


def trial(network,previous,key,h,policy,previous_rate):
    """Return a candidate and two accepted subintervals; never edit previous."""
    if (not isinstance(previous,State) or not isinstance(policy,Policy) or not math.isfinite(h)
            or not policy.minimum_step_s<=h<=policy.maximum_step_s
            or not math.isfinite(previous_rate) or previous_rate<0):
        raise ValueError("complete state and in-policy trial interval required")
    full,full_diag=network.step(previous,key,h)
    half,half_diag=network.step(previous,key,h/2)
    fine,fine_diag=network.step(half,key,h/2)
    ve=scaled_error(full.joint.node_v,fine.joint.node_v,policy.voltage_abs_v,policy.voltage_relative)
    qe=scaled_error(charges(full),charges(fine),policy.charge_abs_c,policy.charge_relative)
    changes=(float(np.max(np.abs(voltages(network,half)-voltages(network,previous)))),
             float(np.max(np.abs(voltages(network,fine)-voltages(network,half)))))
    diagnostics=dict(voltage_error_ratio=ve,charge_error_ratio=qe,junction_increment_v=max(changes),
                     full=full_diag,half=half_diag,fine=fine_diag)
    if max(ve,qe)>1 or max(changes)>policy.junction_increment_v:
        return None,dict(diagnostics,reason="local-error-or-junction-increment"),None
    rates=(previous_rate,frozen_rate(network,half,key),frozen_rate(network,fine,key))
    product=h/2*max(rates)
    diagnostics.update(frozen_positive_rates_per_s=rates,positive_mode_step_product=product)
    if product>policy.positive_mode_step_product:
        return None,dict(diagnostics,reason="frozen-positive-mode-underresolved"),None
    return (half,fine),diagnostics,rates[-1]
