"""Exact scalar witnesses: shared BDF2 memory can hide accumulated error."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_memory_defect.json"
RATIOS=(F(1,4),F(1,2),F(1),F(2))
COUNTS=(1,2,4,16,64,256)


def rational(value):
    value=F(value)
    return dict(numerator=value.numerator,denominator=value.denominator)


def step(t,current,previous,k,h):
    r=h/k;a0=(1+2*r)/(1+r);a1=-(1+r);a2=r*r/(1+r)
    return (h*3*(t+h)**2-a1*current-a2*previous)/a0


def doubling(t,current,previous,k,h):
    full=step(t,current,previous,k,h)
    middle=step(t,current,previous,k,h/2)
    fine=step(t+h/2,middle,current,h/2,h/2)
    return full,fine


def memory_gain(r):
    r=F(r)
    if not 0<r<=2:raise ValueError("positive BDF2 ratio <=2 required")
    return r*r*(r+2)/(3*(r+1)*(2*r+1))


def uniform_error(n,h=F(1)):
    if type(n) is not int or n<1:raise ValueError("positive integer count required")
    return h**3*(2*n-1+F(1,3**n))


def uniform_difference(n,h=F(1)):
    if type(n) is not int or n<1:raise ValueError("positive integer count required")
    return h**3*(F(9,8)-F(1,3**n))


def generate():
    source=Path(__file__).resolve();before=hashlib.sha256(source.read_bytes()).hexdigest()
    ratios=[]
    for r in RATIOS:
        h=F(1);k=h/r
        full,fine=doubling(F(0),F(0),-k**3,k,h)
        offset=F(1,100)
        shifted=doubling(F(0),offset,-k**3+offset,k,h)
        gain=memory_gain(r)
        previous_error=(full-fine)/gain
        cancelled=doubling(F(0),F(0),-k**3+previous_error,k,h)
        ratios.append(dict(ratio=rational(r),full=rational(full),fine=rational(fine),
            exact_destination=rational(h**3),difference=rational(full-fine),
            incoming_difference_gain=rational(gain),common_offset=rational(offset),
            shifted_full=rational(shifted[0]),shifted_fine=rational(shifted[1]),
            shifted_difference=rational(shifted[0]-shifted[1]),
            cancelling_current_error=rational(F(0)),cancelling_previous_error=rational(previous_error),
            cancelled_full=rational(cancelled[0]),cancelled_fine=rational(cancelled[1]),
            cancelled_difference=rational(cancelled[0]-cancelled[1]),
            cancelled_full_error=rational(cancelled[0]-h**3)))
    previous=F(-1);current=F(0);uniform=[]
    for n in range(1,max(COUNTS)+1):
        full,fine=doubling(F(n-1),current,previous,F(1),F(1))
        error=full-F(n)**3;difference=full-fine
        if error!=uniform_error(n) or difference!=uniform_difference(n):
            raise ValueError("exact uniform recurrence differs from closed form")
        if n in COUNTS:
            uniform.append(dict(steps=n,global_error=rational(error),local_difference=rational(difference),
                                global_over_local=rational(error/difference)))
        previous,current=current,full
    if hashlib.sha256(source.read_bytes()).hexdigest()!=before:raise ValueError("proof source changed")
    return dict(schema="rf-d/bdf-memory-defect/v1",source_sha256={source.relative_to(ROOT).as_posix():before},
        arithmetic="exact rational integers; no binary floating-point solve",problem="y=t^3; y'=3t^2",
        units="normalized scalar time and state, not circuit volts or seconds",ratios=ratios,uniform=uniform,
        incoming_history_is_numerical=True,published_candidate="full-step",diagnostic_only=True,
        nonlinear_DAE_calibrated=False,temporal_error_bound_admitted=False,physical_switching_admitted=False,
        audio_admitted=False,
        limitation="exact forcing is independent of y; the scalar counterexample does not identify RF-D's trajectory error or prescribe a DAE correction")


if __name__=="__main__":
    OUTPUT.write_text(json.dumps(generate(),indent=2,allow_nan=False)+"\n",encoding="utf-8")
