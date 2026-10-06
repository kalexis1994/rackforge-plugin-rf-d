"""Exact rational decomposition for three linear rows with observed controls fixed."""
from fractions import Fraction
import voice_kcl_trace as kcl

pairs=kcl.pairs


def evaluate(p):
    F=Fraction.from_float;s=p['solve'];l=p['inductor']['load']
    V=lambda n:F(s['new_'+str(n)+'_v'])
    g=F(p['conductance_s']);gm=F(p['transconductance_s']);req=F(l['req_ohm']);veq=F(l['veq_v'])
    i=F(s['new_current_a']);ig=gm*(V(3)-V(49));istar=-ig
    v17star=V(98)-req*istar-veq;v16star=v17star-istar/g
    rL=V(98)-V(17)-req*i-veq;r17=g*(V(17)-V(16))-i
    gap=V(16)-v16star;amplified=-(req+1/g)*(i+ig);lterm=-rL;kterm=-r17/g
    if gap!=amplified+lterm+kterm:raise ValueError('exact rational reduction identity')
    return dict(fixed_control_voltage_gap_16_v=float(gap),current_constraint_amplified_v=float(amplified),
                inductor_row_term_v=float(lterm),kcl17_term_v=float(kterm),rational_identity_exact=True)


def summarize(ps):
    report=kcl.summarize(ps);es=[dict(attempt=p['attempt'],measurements=evaluate(p)) for p in ps]
    tail=[p for p in es if p['attempt']==es[-1]['attempt']]
    keys=('fixed_control_voltage_gap_16_v','current_constraint_amplified_v','inductor_row_term_v','kcl17_term_v')
    def peaks(records):return {key:max(abs(p['measurements'][key]) for p in records) for key in keys}
    report['fixed_control_reduction']=dict(records=len(es),all_rational_identities_exact=True,
        all_window_absolute_peaks_v=peaks(es),final_attempt_absolute_peaks_v=peaks(tail),
        final_attempt_tail=tail[-12:],coupled_network_solution_error_observed=False)
    return report
