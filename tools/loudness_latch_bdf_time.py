"""Adaptive BDF2 with same-state BE predictor; complete history is atomic."""
import math
import numpy as np
from loudness_latch_bdf_reference import History
from loudness_latch_increment_time import Policy,nodes,junctions,error,differences
from loudness_latch_time_reference import frozen_rate


def trial(network,old,key,h,policy,previous_rate):
    if (not isinstance(old,History) or not isinstance(policy,Policy) or not math.isfinite(h)
            or not policy.minimum_step_s<=h<=policy.maximum_step_s
            or not math.isfinite(previous_rate) or previous_rate<0):
        raise ValueError("complete BDF history and in-policy interval required")
    n=network.network
    predictor,pd=n.step(old.current,key,h)
    if old.previous is None:
        middle,md=network.advance(old,key,h/2)
        fine,fd=network.advance(middle,key,h/2)
        steps=((middle,md),(fine,fd))
        estimate="startup BE-full versus BE-half plus BDF2-half"
    else:
        fine,fd=network.advance(old,key,h)
        steps=((fine,fd),);estimate="same-current-state BE versus BDF2"
    ve=error(nodes(predictor),nodes(fine.current),policy.voltage_abs_v,policy.voltage_relative)
    je=error(junctions(n,predictor),junctions(n,fine.current),policy.junction_abs_v,policy.junction_relative)
    increments=[];previous=old
    for history,d in steps:
        increments.append(float(np.max(np.abs(differences(junctions(n,history.current),junctions(n,previous.current))))))
        previous=history
    diag=dict(voltage_error_ratio=ve,junction_voltage_error_ratio=je,junction_increment_v=max(increments),
        predictor=pd,corrector=fd,error_estimator=estimate,error_metric_version="BE-BDF2-voltage/v3")
    if max(ve,je)>1 or max(increments)>policy.junction_increment_v:
        return None,dict(diag,reason="voltage-error-or-junction-increment"),None
    rates=[previous_rate];products=[]
    for history,d in steps:
        rates.append(frozen_rate(n,history.current,key))
        products.append(d["actual_dt_s"]*max(rates[-2:]))
    diag.update(frozen_positive_rates_per_s=rates,positive_mode_step_product=max(products))
    if max(products)>policy.positive_mode_step_product:
        return None,dict(diag,reason="frozen-positive-mode-underresolved"),None
    return steps,diag,rates[-1]
