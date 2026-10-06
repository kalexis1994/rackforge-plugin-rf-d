"""Exact row equivalence and history-preserving stamps for the 741 experiment."""
from fractions import Fraction as F


def stamps(req,veq,g,gm):
    if g<=0 or gm<=0 or req<0:raise ValueError('positive frozen conductances and nonnegative resistance')
    gain=(req+1/g)*gm;scale=max(F(1),abs(gain))
    return (1/scale,F(0),-1/scale,gain/scale,-gain/scale,F(0)),veq/scale


def original_rows(req,g,gm):
    return ((F(1),F(-1),F(0),F(0),F(0),-req),
            (F(0),g,-g,F(0),F(0),F(-1)),
            (F(0),-g,g,-gm,gm,F(0)))


def history_stamp(order,coefficients,history,inductance):
    if order not in (1,2) or len(history)!=2:raise ValueError('Gear 1/2 with two retained histories')
    a0,a1,a2=coefficients;phi1,phi2=history
    return a0*inductance,a1*phi1+(a2*phi2 if order==2 else F(0))
