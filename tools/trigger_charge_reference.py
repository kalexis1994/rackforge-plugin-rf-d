"""Trigger KCL from the reviewed Python graph, with a loaded Q12 collector."""
from functools import lru_cache
from loudness_contour_reference import Network,Controls
from semiconductor_ideal import thermal_voltage_v
NAMES=['RESET_DRIVER','TRIGGER_COLLECTOR','Q12_BASE','Q20_BASE','KEY_RC','KEY_DIODE_K','C4_LEFT','RESET_DIODE_A']
REFS={'R23','R25_DRAWING','R_TRIGGER_BASE_DRAWING','R49','R55','R60','R28','R36'}
def network(reset_base,short,key_rc=None):
 n=Network(Controls(external_s_short=short));n.resistors=[r for r in n.resistors if r[0] in REFS];n.bjts=[p for p in n.bjts if p['ref'] in ['Q12','Q20']];n.diodes=[p for p in n.diodes if p['ref'] in ['CR8','CR10']];n.caps=[p for p in n.caps if p[0] in ['C4','C7']];n.rails.update(RESET_BASE=reset_base,SET_BASE=.01,LOUDNESS_OUT=0.)
 if key_rc is not None:n.rails['KEY_RC']=key_rc
 n.alias={name:name for name in set(NAMES)|set(n.rails)};n.nodes=[name for name in NAMES if name not in n.rails];n.index={name:i for i,name in enumerate(n.nodes)};return n
def prepare(sustain,fast,reset_base):
 n=network(reset_base,False,key_rc=0.);base=n.evaluate;scale=1.5*thermal_voltage_v(298.15)
 def loaded(x,key,previous=None,dt_s=None,*,jacobian=True):
  r,j=base(x,key,previous,dt_s,jacobian=jacobian);k=n.index['RESET_DRIVER'];v=x[k];diode=1e-12*__import__('math').expm1((sustain-v)/scale);r[k]+=(v-fast)/1500.-diode
  if j is not None:j[k][k]+=1/1500.+1e-12*__import__('math').exp((sustain-v)/scale)/scale
  return r,j
 n.evaluate=loaded;values=dict(RESET_DRIVER=.03,TRIGGER_COLLECTOR=6.,Q12_BASE=.7,Q20_BASE=0.,KEY_DIODE_K=0.,C4_LEFT=.03,RESET_DIODE_A=.4);s,d=n.solve([values[k] for k in n.nodes],0.,use_fd=True);return [s.node_v[k] for k in NAMES],d
