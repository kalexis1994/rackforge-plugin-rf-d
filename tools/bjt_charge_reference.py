"""Conservative intrinsic low-injection BJT subset; explicitly conditioned.

NG46 bjtload.c, tag ebdaf58: qb=1, XTF/PTF=0, XCJC=1, no internal
resistances, leakage, substrate, high injection or Early effects. Parameters
have no vintage defaults. Conserves terminal currents and accepted charge.
"""
from dataclasses import dataclass
from junction_charge_reference import Depletion, LowInjectionDiffusion, finite
import math


@dataclass(frozen=True)
class Parameters:
    polarity: int
    saturation_a: float
    beta_forward: float
    beta_reverse: float
    emission_be_v: float
    emission_bc_v: float
    depletion_be: Depletion
    depletion_bc: Depletion
    transit_forward_s: float
    transit_reverse_s: float

    def __post_init__(self):
        if type(self.polarity) is not int or self.polarity not in (-1,1):
            raise ValueError("polarity must be +1 NPN or -1 PNP")
        finite(self.saturation_a,self.beta_forward,self.beta_reverse,self.emission_be_v,self.emission_bc_v,
               self.transit_forward_s,self.transit_reverse_s)
        if min(self.saturation_a,self.beta_forward,self.beta_reverse,self.emission_be_v,self.emission_bc_v)<=0:
            raise ValueError("positive transport parameters required")
        if min(self.transit_forward_s,self.transit_reverse_s)<0:
            raise ValueError("nonnegative transit times required")
        if not isinstance(self.depletion_be,Depletion) or not isinstance(self.depletion_bc,Depletion):
            raise ValueError("explicit depletion laws required")


@dataclass(frozen=True)
class History:
    parameters: Parameters
    be_c: float  # oriented QBE, independent of NPN/PNP terminal sign
    bc_c: float

    def __post_init__(self):
        if not isinstance(self.parameters,Parameters):
            raise ValueError("charge history must identify its model parameters")
        finite(self.be_c,self.bc_c)


@dataclass(frozen=True)
class Evaluation:
    current_a: tuple  # outgoing B,C,E
    jacobian_s: tuple
    terminal_charge_c: tuple  # B,C,E, sum zero
    capacitance_f: tuple  # dQterminal/dVterminal
    candidate: History


class Device:
    def __init__(self,parameters):
        if not isinstance(parameters,Parameters):
            raise ValueError("explicit BJT parameters required")
        self.parameters = parameters

    def evaluate(self,voltages,previous=None,dt_s=None):
        if len(voltages)!=3:
            raise ValueError("three terminal voltages B,C,E required")
        finite(*voltages)
        p = self.parameters
        if previous is not None:
            if not isinstance(previous,History) or previous.parameters != p:
                raise ValueError("history parameter mismatch; reparameterization policy required")
            if dt_s is None:
                raise ValueError("transient history requires dt")
            finite(dt_s)
            if dt_s<=0:
                raise ValueError("positive transient dt required")
        elif dt_s is not None:
            raise ValueError("dt without charge history is ambiguous")
        vb,vc,ve = voltages
        vbe,vbc = p.polarity*(vb-ve),p.polarity*(vb-vc)
        xf,xr = vbe/p.emission_be_v,vbc/p.emission_bc_v
        finite(xf,xr)
        if max(xf,xr)>45:
            raise ValueError("BJT exponent outside laboratory numerical guard")
        f,r = p.saturation_a*math.expm1(xf),p.saturation_a*math.expm1(xr)
        gf,gr = p.saturation_a*math.exp(xf)/p.emission_be_v,p.saturation_a*math.exp(xr)/p.emission_bc_v
        ib = p.polarity*(f/p.beta_forward+r/p.beta_reverse)
        ic = p.polarity*(f-r*(1+1/p.beta_reverse))
        currents = [ib,ic,-ib-ic]
        gbf,gbr = gf/p.beta_forward,gr/p.beta_reverse
        j = [[gbf+gbr,-gbr,-gbf],
             [gf-gr*(1+1/p.beta_reverse),gr*(1+1/p.beta_reverse),-gf]]
        j.append([-j[0][col]-j[1][col] for col in range(3)])
        qbe,cbe = p.depletion_be.evaluate(vbe)
        qbc,cbc = p.depletion_bc.evaluate(vbc)
        qf,cf = LowInjectionDiffusion(p.transit_forward_s,p.saturation_a,p.emission_be_v).evaluate(vbe)
        qr,cr = LowInjectionDiffusion(p.transit_reverse_s,p.saturation_a,p.emission_bc_v).evaluate(vbc)
        qbe,cbe = qbe+qf,cbe+cf
        qbc,cbc = qbc+qr,cbc+cr
        charges = (p.polarity*(qbe+qbc),-p.polarity*qbc,-p.polarity*qbe)
        cap = ((cbe+cbc,-cbc,-cbe),(-cbc,cbc,0.0),(-cbe,0.0,cbe))
        if previous is not None:
            ibe,ibc = p.polarity*(qbe-previous.be_c)/dt_s,p.polarity*(qbc-previous.bc_c)/dt_s
            currents[0] += ibe+ibc
            currents[1] -= ibc
            currents[2] -= ibe
            for row in range(3):
                for col in range(3):
                    j[row][col] += cap[row][col]/dt_s
        finite(*currents,*charges,qbe,qbc,*(v for row in j for v in row),*(v for row in cap for v in row))
        return Evaluation(tuple(currents),tuple(tuple(row) for row in j),charges,cap,History(p,qbe,qbc))
