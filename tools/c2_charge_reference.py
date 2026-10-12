"""Independent driver assembled by restricting the reviewed documentary Python graph."""
from functools import lru_cache
from loudness_contour_reference import Network,Controls
NAMES=['TIMING_C2','ATTACK_PNP_BASE','ATTACK_OUT','ATTACK_PANEL_IN','DECAY_DRIVER_EMITTER','DECAY_SWITCH_BASE','DECAY_OUT','SUSTAIN_WIPER','SUSTAIN_BASE','SUSTAIN_DRIVER_EMITTER','SUSTAIN_COLLECTOR','FAST_DIODE_K']
REFS={'R40','R41','R42','PANEL_R13','PANEL_R16','R43','R44','R45','R51','R47_POSITION','R46','PANEL_R19_LOWER','PANEL_R19_UPPER','LHC_FAST_DECAY'}
def network(q25,reset_driver,final_decay,c2=None):
 n=Network(Controls(final_decay=False));n.resistors=[r for r in n.resistors if r[0] in REFS];n.bjts=[p for p in n.bjts if p['ref'] in ['Q16','Q17','Q18','Q19']];n.diodes=[p for p in n.diodes if p['ref']=='CR9' or p['ref']=='CR4' and not final_decay];n.caps=[p for p in n.caps if p[0]=='C2'];n.rails.update(RESET_COLLECTOR=q25,RESET_DRIVER=reset_driver,LOUDNESS_OUT=0.)
 if c2 is not None:n.rails['TIMING_C2']=c2
 names=set(NAMES)|set(n.rails);n.alias={name:name for name in names};n.nodes=[name for name in NAMES if name not in n.rails];n.index={name:i for i,name in enumerate(n.nodes)};return n
@lru_cache(None)
def problem(q25,reset_driver,final_decay):
 n=network(q25,reset_driver,final_decay)
 def dc(x):return n.evaluate(x.tolist() if hasattr(x,'tolist') else x,0.,jacobian=False)[0]
 return n,dc
def prepare(final_decay):
 n=network(8.3,9.,final_decay,c2=3.2);values=dict(ATTACK_PNP_BASE=9.15,ATTACK_OUT=3.2,ATTACK_PANEL_IN=3.2,DECAY_DRIVER_EMITTER=7.7,DECAY_SWITCH_BASE=3.7,DECAY_OUT=3.2,SUSTAIN_WIPER=5.,SUSTAIN_BASE=2.5,SUSTAIN_DRIVER_EMITTER=3.1,SUSTAIN_COLLECTOR=.02,FAST_DIODE_K=9.)
 state,diagnostics=n.solve([values[k] for k in n.nodes],0.,use_fd=True);return [state.node_v[k] for k in NAMES],diagnostics
