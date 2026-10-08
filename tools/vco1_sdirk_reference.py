"""Independent charge-form SDIRK2; full Decimal100 device/history interfaces."""
from decimal import Decimal
import math
import vco1_increment_circuit as circuit
D=Decimal.from_float
GAMMA=1.-1./math.sqrt(2.)
# Python 1/sqrt(2) can differ by one ULP from Rust FRAC_1_SQRT_2. Pin the published binary64 constant.
GAMMA=1.-float.fromhex('0x1.6a09e667f3bcdp-1')
WEIGHT=(1.-GAMMA)/GAMMA

def forced_reference(x,old,dt,c,forcing,ground):
 r,j,g=circuit.reference_decimal(x,old,dt,c);return [v-D(WEIGHT)*q for v,q in zip(r,forcing)],j,g-D(WEIGHT)*ground

def step(old,h,c):
 dt=GAMMA*h;stage,it1,res1,g1=circuit.solve(old,dt,c);dc,j,gd=circuit.reference_decimal(stage,old,0.,c);forcing=[a-b for a,b in zip(res1,dc)];ground=g1-gd
 if any(v!=0 for k,v in enumerate(forcing) if k>=98 and k not in (118,119,129,130)):raise ValueError('algebraic forcing')
 x=list(stage)
 for it in range(64):
  r,j,g=forced_reference(x,old,dt,c,forcing,ground);norm=max(abs(v)/D(2e-14 if k<98 else 2e-12) for k,v in enumerate(r));d=circuit.op.dense([row[:] for row in j],[-v for v in r]);corr=max(abs(v)/D(2e-10 if k<98 else 2e-13) for k,v in enumerate(d))
  if norm<=1 and corr<=1:return dict(stage=stage,endpoint=x,stage_iterations=it1,endpoint_iterations=it+1,stage_residual=res1,stage_ground=g1,endpoint_residual=r,endpoint_ground=g,forcing=forcing,ground_dynamic=ground)
  for power in range(24):
   alpha=Decimal(2)**(-power);trial=[v+alpha*q for v,q in zip(x,d)]
   if not circuit.valid(trial,c):continue
   rr,jj,gg=forced_reference(trial,old,dt,c,forcing,ground);new=max(abs(v)/D(2e-14 if k<98 else 2e-12) for k,v in enumerate(rr))
   if new<norm or new<=1:x=trial;break
  else:raise ValueError('SDIRK Decimal line search')
 raise ValueError('SDIRK Decimal iterations')
