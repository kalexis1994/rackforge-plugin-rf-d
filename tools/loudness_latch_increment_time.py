"""Adaptive v2: node and BE/BC voltage errors, independent of charge origin.

Q(v) is single valued in the explicit restricted device model. Junction
voltage error controls its arguments; this is not a bound on charge/current
error or a physical calibration. Both actual half intervals remain atomic.
"""
from dataclasses import dataclass
import math
import numpy as np
from loudness_latch_increment_reference import IncrementState,pair
from loudness_latch_time_reference import frozen_rate


@dataclass(frozen=True)
class Policy:
    voltage_abs_v: float
    voltage_relative: float
    junction_abs_v: float
    junction_relative: float
    junction_increment_v: float
    positive_mode_step_product: float
    maximum_step_s: float
    minimum_step_s: float
    maximum_attempts: int

    def __post_init__(self):
        values=[v for k,v in vars(self).items() if k!="maximum_attempts"]
        if any(not math.isfinite(v) or v<=0 for v in values) or self.minimum_step_s>self.maximum_step_s:
            raise ValueError("positive finite error gates and ordered interval limits required")
        if type(self.maximum_attempts) is not int or self.maximum_attempts<1:
            raise ValueError("positive integer attempt budget required")


def nodes(state):
    return tuple(zip(state.joint.node_v,state.node_low_v))


def junctions(network,state):
    result=[]
    for terminals in network.latch.terminals:
        b,c,e=[(state.joint.node_v[i],state.node_low_v[i]) if i is not None else (fixed,0.0)
               for i,fixed in terminals]
        result.extend((pair((*b,*(-v for v in e))),pair((*b,*(-v for v in c)))))
    return tuple(result)


def differences(a,b):
    return np.array([math.fsum((*x,*(-v for v in y))) for x,y in zip(a,b)])


def error(a,b,absolute,relative):
    return float(np.max(np.abs(differences(a,b))/
        np.array([absolute+relative*max(abs(math.fsum(x)),abs(math.fsum(y))) for x,y in zip(a,b)])))


def trial(network,old,key,h,policy,previous_rate):
    if (not isinstance(old,IncrementState) or not isinstance(policy,Policy)
            or not math.isfinite(h) or not policy.minimum_step_s<=h<=policy.maximum_step_s
            or not math.isfinite(previous_rate) or previous_rate<0):
        raise ValueError("complete compensated state and in-policy interval required")
    full,fd=network.step(old,key,h)
    half,hd=network.step(old,key,h/2)
    fine,nd=network.step(half,key,h/2)
    ve=error(nodes(full),nodes(fine),policy.voltage_abs_v,policy.voltage_relative)
    je=error(junctions(network,full),junctions(network,fine),policy.junction_abs_v,policy.junction_relative)
    increment=max(float(np.max(np.abs(differences(junctions(network,half),junctions(network,old))))),
                  float(np.max(np.abs(differences(junctions(network,fine),junctions(network,half))))))
    diag=dict(voltage_error_ratio=ve,junction_voltage_error_ratio=je,junction_increment_v=increment,
              full=fd,half=hd,fine=nd,error_metric_version="node-and-junction-voltage/v2")
    if max(ve,je)>1 or increment>policy.junction_increment_v:
        return None,dict(diag,reason="voltage-error-or-junction-increment"),None
    rates=(previous_rate,frozen_rate(network,half,key),frozen_rate(network,fine,key))
    product=h/2*max(rates)
    diag.update(frozen_positive_rates_per_s=rates,positive_mode_step_product=product)
    if product>policy.positive_mode_step_product:
        return None,dict(diag,reason="frozen-positive-mode-underresolved"),None
    return (half,fine),diag,rates[-1]
