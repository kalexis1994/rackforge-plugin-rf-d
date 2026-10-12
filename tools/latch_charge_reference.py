"""Full reviewed board-2 DC graph and Decimal100 Q25/Q15 charge oracle."""
from decimal import Decimal
from loudness_contour_reference import Network,Controls
from check_joint_reference import D
NAMES=['FOLLOWER_BASE','FOLLOWER_MID','FOLLOWER_SUPPLY','LOUDNESS_OUT','RESET_FEEDBACK','TIMING_C2','ATTACK_PNP_BASE','ATTACK_OUT','ATTACK_PANEL_IN','DECAY_DRIVER_EMITTER','DECAY_SWITCH_BASE','DECAY_OUT','SUSTAIN_WIPER','SUSTAIN_BASE','SUSTAIN_DRIVER_EMITTER','SUSTAIN_COLLECTOR','FAST_DIODE_K','RESET_DRIVER','TRIGGER_COLLECTOR','Q12_BASE','Q20_BASE','KEY_RC','KEY_DIODE_K','C4_LEFT','RESET_DIODE_A','SET_BASE','RESET_COLLECTOR','RESET_BASE','ATTACK_GATE_LOWER']
RAILS=['GROUND','CONTOUR_SUPPLY','MINUS_10','PLUS_10','KEYBOARD_TRIGGER','VCA_CONTROL_LOAD']
def network(on,short):
 n=Network(Controls(final_decay=on,external_s_short=short));n.nodes=NAMES[:];n.index={v:k for k,v in enumerate(NAMES)};n.alias={v:v for v in set(NAMES)|set(RAILS)};n.rails['VCA_CONTROL_LOAD']=0.;n.resistors.append(('R59','LOUDNESS_OUT','VCA_CONTROL_LOAD',68000.));return n
def depletion(v,c,vp,m):
 c,vp,m,fc=map(D,[c,vp,m,.4]);vf=fc*vp;p=1-m
 def low(w):return c*vp/p*(1-(1-w/vp)**p)
 if v<vf:return low(v),c*(1-v/vp)**(-m)
 cf=c*(1-fc)**(-m);slope=cf*m/(vp*(1-fc));z=v-vf;return low(vf)+z*(cf+slope*z/2),cf+slope*z
def junction(v,be):
 q,c=depletion(v,*([7e-12,.75,.5] if be else [5e-12,.7,.33]));t=D(1e-9 if be else 3e-9);vt=D(1.380649e-23*298.15/1.602176634e-19);i=D(1e-14)*(v/vt).exp();return q+t*(i-D(1e-14)),c+t*i/vt
def charges(x):
 out=[Decimal(0)]*229;mass={}
 for b,c in [(225,226),(227,228)]:
  qe,ce=junction(x[b],True);qc,cc=junction(x[b]-x[c],False);out[b]+=qe+qc;out[c]-=qc
  for i,j,v in [(b,b,ce+cc),(b,c,-cc),(c,b,-cc),(c,c,cc)]:mass[i,j]=mass.get((i,j),Decimal(0))+v
 return out,mass
