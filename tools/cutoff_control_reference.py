"""Original 229 equations scoped to the documentary cutoff pot fraction."""
import inspect
from functools import lru_cache
import decay_control_reference as previous
import check_joint_loudness as follower
from decay_control_reference import state,lift,packed,currents,ledger,D
from joint_cycles_analysis import require
@lru_cache(None)
def scoped(key,on,short,alpha):
 require(alpha in [1.,.5],'declared cutoff fractions')
 # Build the independent Python DC graph with its actual panel resistors.
 body=inspect.getsource(follower.problem).replace("controls['panel']['cutoff_fraction_from_neg10']=1.", "controls['panel']['cutoff_fraction_from_neg10']=ALPHA")
 ns=dict(follower.__dict__,ALPHA=alpha);exec(compile(body,'<original cutoff panel graph>','exec'),ns);f=ns['problem']
 body=inspect.getsource(previous.problem);ns=dict(previous.__dict__,follower_problem=f);exec(compile(body,'<original loaded contour graph>','exec'),ns);problem=ns['problem']
 body=inspect.getsource(previous.scoped);ns=dict(previous.__dict__,problem=problem);exec(compile(body,'<original cutoff Radau graph>','exec'),ns);return ns['scoped'](key,on,short)
