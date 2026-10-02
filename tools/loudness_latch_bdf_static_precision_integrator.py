"""Explicit offline candidate: original increment residual, compensated static J66.

Inherited Newton, line search, two-state BDF, charge publication and gates.
Not used by the plugin or by any historical reference producer.
"""
import math
import numpy as np
from circuit66_decimal_static import graph
from circuit66_static_binary import prepare,evaluate as binary_evaluate
from loudness_latch_increment_reference import IncrementNetwork
from loudness_latch_bdf_reference import BdfNetwork

VERSION="increment-pair/compensated-static-J66/v1"


class CompensatedIncrementNetwork(IncrementNetwork):
    def __init__(self,r61,parameters):
        super().__init__(r61,parameters)
        self.static_graph=prepare(graph(self.joint.values),"compensated-reciprocal")

    def increment_evaluator(self,key,old,dt_s):
        original=super().increment_evaluator(key,old,dt_s)
        cap_j=np.zeros((self.joint.n,self.joint.n))
        for left,right,_,c,resistance in self.branches:
            g=1/(dt_s/c+resistance);cap_j[left,left]+=g
            if right is not None:
                cap_j[right,right]+=g;cap_j[left,right]-=g;cap_j[right,left]-=g
        def evaluate(delta,jacobian=True,use_fd=False):
            # Calling the original closure with False preserves its residual bits.
            # Its explicit full-residual FD diagnostic also remains available.
            if use_fd:return original(delta,jacobian=jacobian,use_fd=True)
            r,_=original(delta,jacobian=False)
            if not jacobian:return r,None
            x=np.array([math.fsum((a,b,d)) for a,b,d in zip(old.joint.node_v,old.node_low_v,delta)])
            _,audio_j=binary_evaluate(self.static_graph,x[:66])
            _,contour_j=self.joint.contour.evaluate(list(x[66:]),key,jacobian=True)
            j=np.zeros_like(cap_j);j[:66,:66]=audio_j;j[66:,66:]=contour_j
            j[32,self.joint.out]=-1/68000;j[self.joint.out,32]=-1/68000
            j+=cap_j+self.latch.evaluate(x,old.latch,dt_s)["capacitance_f"]/dt_s
            return r,j
        return evaluate


class CompensatedBdfNetwork(BdfNetwork):
    def __init__(self,r61,parameters):
        self.network=CompensatedIncrementNetwork(r61,parameters)
