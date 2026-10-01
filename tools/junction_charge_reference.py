"""Conditional two-terminal charge mathematics; no vintage defaults or BJT model.

NG-46 p138 eq7.4 supplies the depletion capacitance. Q is its integral,
referenced to Q(0)=0. Low-injection diffusion uses Q=transit*Is*expm1(v/scale).
No high injection, avalanche, charge partition, or recovery state is modeled.
"""
from dataclasses import dataclass
import math


def finite(*values):
    if not all(math.isfinite(v) for v in values):
        raise ValueError("finite charge arguments/results required")


@dataclass(frozen=True)
class Depletion:
    cj0_f: float
    potential_v: float
    grading: float
    forward_fraction: float

    def __post_init__(self):
        finite(*vars(self).values())
        if (self.cj0_f < 0 or self.potential_v <= 0 or not 0 <= self.grading <= 1
                or not 0 <= self.forward_fraction < 1):
            raise ValueError("Cj0>=0, potential>0, grading in [0,1], FC in [0,1) required")

    def _below_knee(self, voltage_v):
        log_ratio = math.log1p(-voltage_v/self.potential_v)
        p = 1-self.grading
        integral = -log_ratio if p == 0 else -math.expm1(p*log_ratio)/p
        q = self.cj0_f*self.potential_v*integral
        c = self.cj0_f*math.exp(-self.grading*log_ratio)
        return q, c

    def evaluate(self, voltage_v):
        finite(voltage_v)
        knee = self.forward_fraction*self.potential_v
        try:
            if voltage_v < knee:
                q, c = self._below_knee(voltage_v)
            else:
                qk, ck = self._below_knee(knee)
                slope = ck*self.grading/(self.potential_v*(1-self.forward_fraction))
                u = voltage_v-knee
                q, c = qk+ck*u+.5*slope*u*u, ck+slope*u
        except (OverflowError, ZeroDivisionError) as exc:
            raise ValueError("depletion arithmetic outside representable domain") from exc
        finite(q, c)
        return q, c


@dataclass(frozen=True)
class LowInjectionDiffusion:
    transit_s: float
    saturation_a: float
    emission_scale_v: float  # n*k*T/q supplied by caller; no assumed n or T

    def __post_init__(self):
        finite(*vars(self).values())
        if self.transit_s < 0 or self.saturation_a <= 0 or self.emission_scale_v <= 0:
            raise ValueError("transit>=0, Is>0 and emission scale>0 required")

    def evaluate(self, voltage_v):
        finite(voltage_v)
        x = voltage_v/self.emission_scale_v
        finite(x)
        if x > 45:
            raise ValueError("exponent exceeds laboratory numerical guard 45")
        q = self.transit_s*self.saturation_a*math.expm1(x)
        c = self.transit_s*self.saturation_a*math.exp(x)/self.emission_scale_v
        finite(q, c)
        return q, c


@dataclass(frozen=True)
class Junction:
    depletion: Depletion
    diffusion: LowInjectionDiffusion

    def evaluate(self, voltage_v):
        qd, cd = self.depletion.evaluate(voltage_v)
        qf, cf = self.diffusion.evaluate(voltage_v)
        q, c = qd+qf, cd+cf
        finite(q, c)
        return q, c


@dataclass(frozen=True)
class ChargeHistory:
    charge_c: float

    def __post_init__(self):
        finite(self.charge_c)


@dataclass(frozen=True)
class Companion:
    current_a: tuple[float, float]  # outgoing currents at positive, negative terminals
    jacobian_s: tuple[tuple[float, float], tuple[float, float]]
    candidate: ChargeHistory  # caller publishes only after whole circuit acceptance


def companion(junction, positive_v, negative_v, previous, dt_s):
    finite(positive_v, negative_v, dt_s)
    if dt_s <= 0 or not isinstance(previous, ChargeHistory):
        raise ValueError("positive dt and immutable charge history required")
    q, c = junction.evaluate(positive_v-negative_v)
    current, g = (q-previous.charge_c)/dt_s, c/dt_s
    finite(current, g)
    return Companion((current, -current), ((g, -g), (-g, g)), ChargeHistory(q))
