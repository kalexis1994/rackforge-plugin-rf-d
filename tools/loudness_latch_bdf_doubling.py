"""BDF2 full versus two provisional half steps; accepted path stays full."""
import math
import numpy as np
from loudness_latch_bdf_probes import pack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_increment_time import Policy,nodes,junctions,differences,error
from loudness_latch_time_reference import frozen_rate


def cubic_error_factors(r):
    """Exact cubic forcing, exact incoming states: errors normalized by h^3.

    For y=t^3, y'=3t^2, incoming times 0,-k and r=h/k, the
    derivative defect is -h(h+k)y'''/6. Solve the full step and
    propagate the first-half error through the second-half recurrence.
    This scalar example is not an error calibration for the 94-node DAE.
    """
    if not math.isfinite(r) or not 0<r<=2:raise ValueError("positive ratio at most two required")
    full=(r+1)**2/(r*(2*r+1))
    fine=(3*r*r+6*r+4)/(12*r*(r+1))
    return dict(full=full,fine=fine,difference=full-fine,fine_over_difference=fine/(full-fine))


def estimate(network,old,key,h,minimum_step_s=1e-12):
    network.validate(old)
    if (old.previous is None or not math.isfinite(key) or key!=old.key_v
            or not math.isfinite(h) or not math.isfinite(minimum_step_s)
            or minimum_step_s<=0 or h/2<minimum_step_s):
        raise ValueError("two accepted histories, unchanged source and two in-domain half steps required")
    snapshot=state_hash(old)
    full,fd=network.advance(old,key,h)
    middle,md=network.advance(old,key,h/2)
    second=full.time_s-middle.time_s
    if second<minimum_step_s:raise ValueError("remaining half interval outside declared minimum")
    fine,nd=network.advance(middle,key,second)
    if fine.time_s!=full.time_s:raise ValueError("full and half paths must reach the exact same binary clock time")
    checks=[publication_check(network,a,b,d["actual_dt_s"],d)
            for a,b,d in ((old,full,fd),(old,middle,md),(middle,fine,nd))]
    if any(not c["round_trip_exact"] or c["max_published_kcl_a"]>=1e-11
           or c["max_branch_equation_error_v"]>=1e-14 for c in checks):
        raise ValueError("full or provisional half publication failed its unchanged charge gate")
    if state_hash(old)!=snapshot:raise ValueError("step doubling modified either incoming accepted state")
    n=network.network
    diag=dict(error_estimator="BDF2 full versus two BDF2 half steps; raw difference without Richardson division",
        error_metric_version="BDF2-step-doubling-voltage/v4",previous_history_sha256=snapshot,
        maximum_node_difference_v=float(np.max(np.abs(differences(nodes(full.current),nodes(fine.current))))),
        maximum_junction_difference_v=float(np.max(np.abs(differences(junctions(n,full.current),junctions(n,fine.current))))),
        full_publication=checks[0],shadow_half_steps=[dict(history=pack(b),diagnostics=d,publication=c,published=False)
            for b,d,c in ((middle,md,checks[1]),(fine,nd,checks[2]))],
        full_time_s=full.time_s,fine_time_s=fine.time_s,richardson_factor_applied=False,
        published_candidate="full-step",history_reset_count=0)
    return full,fd,fine,diag


def trial(network,old,key,h,policy,previous_rate):
    if (not isinstance(policy,Policy) or not math.isfinite(h)
            or not policy.minimum_step_s<=h<=policy.maximum_step_s
            or not math.isfinite(previous_rate) or previous_rate<0):
        raise ValueError("declared policy, interval and incoming frozen rate required")
    full,fd,fine,diag=estimate(network,old,key,h,policy.minimum_step_s)
    n=network.network
    ve=error(nodes(full.current),nodes(fine.current),policy.voltage_abs_v,policy.voltage_relative)
    je=error(junctions(n,full.current),junctions(n,fine.current),policy.junction_abs_v,policy.junction_relative)
    increment=float(np.max(np.abs(differences(junctions(n,full.current),junctions(n,old.current)))))
    diag.update(voltage_error_ratio=ve,junction_voltage_error_ratio=je,junction_increment_v=increment)
    if max(ve,je)>1 or increment>policy.junction_increment_v:
        return None,dict(diag,reason="voltage-error-or-junction-increment"),None
    # Test full published interval and both provisional intervals separately.
    from loudness_latch_bdf_probes import unpack
    middle=unpack(network,diag["shadow_half_steps"][0]["history"])
    rates=(previous_rate,frozen_rate(n,full.current,key),frozen_rate(n,middle.current,key),frozen_rate(n,fine.current,key))
    halves=diag["shadow_half_steps"]
    product=max(h*max(rates[:2]),halves[0]["diagnostics"]["actual_dt_s"]*max(rates[0],rates[2]),
                halves[1]["diagnostics"]["actual_dt_s"]*max(rates[2:]))
    diag.update(frozen_positive_rates_per_s=rates,positive_mode_step_product=product)
    if product>policy.positive_mode_step_product:
        return None,dict(diag,reason="frozen-positive-mode-underresolved"),None
    return ((full,fd),),diag,rates[1]
