"""Offline representable endpoint schedule; preserve the ratio <=2 domain."""
from fractions import Fraction as F
import math


def plan(history,target,count,minimum=1e-12):
    if type(count) is not int or count<2:raise ValueError('at least two declared slices required')
    if history.previous_dt_s is None:raise ValueError('double-history anchor required')
    start=history.time_s
    if not math.isfinite(target) or target<=start:raise ValueError('later finite endpoint required')
    quantum=F.from_float(math.ulp(start))
    if F.from_float(math.ulp(target))!=quantum:raise ValueError('constant clock binade required')
    total=(F.from_float(target)-F.from_float(start))/quantum
    if total.denominator!=1:raise ValueError('integer endpoint ticks required')
    remaining=total.numerator;previous=F.from_float(history.previous_dt_s)/quantum
    minimum_ticks=math.ceil(F.from_float(minimum)/quantum);ticks=[]
    for i in range(count):
        slots=count-i
        # Nearest nominal share, capped by the exact adjacent-interval domain.
        wanted=(2*remaining+slots)//(2*slots)
        size=min(wanted,math.floor(2*previous)) if slots>1 else remaining
        if size<minimum_ticks or F(size)>2*previous:
            raise ValueError('declared slices cannot satisfy minimum and ratio domain')
        remaining-=size;previous=F(size);ticks.append(size)
    if remaining!=0:raise ValueError('endpoint ticks not exhausted')
    endpoints=[];time=F.from_float(start)
    for size in ticks:
        time+=size*quantum;endpoint=float(time)
        if F.from_float(endpoint)!=time:raise ValueError('subclock is not exactly representable')
        endpoints.append(endpoint)
    if endpoints[-1]!=target:raise ValueError('coarse endpoint changed')
    return endpoints
