"""Four-node Q26/Q28 and C18 reference with both BJT junctions.

SVC-9 Figs. 9-11/9-17, Table 7-8. Panel/RANGE sources and device parameters
are imposed; the returned TAIL load can be coupled to a ladder solver.
"""
from __future__ import annotations

import math
from filter_cutoff_panel_reference import conditional_panel_q26_base
from output_conversion_c4_vectors import _newton
from semiconductor_ideal import thermal_voltage_v

NODES = ("CONTROL_BASE", "SHARED_Q26E_Q28B", "Q26_COLLECTOR", "Q28_COLLECTOR")
C18_F = 100e-12
R60_OHM = 680.0


def panel_equivalent(panel: dict) -> tuple[float, float]:
    passive = conditional_panel_q26_base(**panel, q26_base_current_a=0)
    return passive["q26_base_v"], passive["node_conductance_s"]


def evaluate(x, *, panel_v, panel_g, range_fraction, tail_v,
             q26, q28, previous_base_v=None, dt_s=None):
    """Outgoing nodal KCL, A. PNP polarity applies to terminal currents."""
    if (len(x) != 4 or not all(math.isfinite(v) for v in x)
            or not math.isfinite(tail_v) or not 0 <= range_fraction <= 1
            or (previous_base_v is None) != (dt_s is None)):
        raise ValueError("finite four-node state and valid boundaries required")
    rsource = 68000 + 10000 * range_fraction * (1-range_fraction)
    r = [(x[0]-panel_v)*panel_g,
         (x[1]-10*range_fraction)/rsource,
         (x[2]+10)/330,
         (x[3]-tail_v)/680]
    devices = {}
    for name, base, collector, emitter, polarity, p in (
            ("Q26", 0, 2, 1, -1, q26), ("Q28", 1, 3, None, 1, q28)):
        vt = thermal_voltage_v(p["temperature_k"])
        ve = 0 if emitter is None else x[emitter]
        be = polarity*(x[base]-ve)/vt
        bc = polarity*(x[base]-x[collector])/vt
        if max(be, bc) > 45:
            raise ValueError("BJT exponential domain exceeded")
        f = p["is_a"]*math.expm1(be)
        reverse = p["is_a"]*math.expm1(bc)
        ib = f/p["beta_forward"] + reverse/p["beta_reverse"]
        ic = f-(1+1/p["beta_reverse"])*reverse
        r[base] += polarity*ib
        r[collector] += polarity*ic
        if emitter is not None:
            r[emitter] -= polarity*(ib+ic)
        devices[name] = dict(base_a=polarity*ib, collector_a=polarity*ic,
                             emitter_a=-polarity*(ib+ic), v_bc_v=polarity*(x[base]-x[collector]))
    if dt_s is not None:
        if not math.isfinite(dt_s) or dt_s <= 0:
            raise ValueError("positive finite step required")
        r[0] += C18_F/dt_s*(x[0]-previous_base_v)
    return r, devices


def solve_dc(*, panel, range_fraction, tail_v, q26, q28):
    pv, pg = panel_equivalent(panel)
    seed = [pv, 0.52, -9.998, tail_v-680*7e-6]
    x, devices, error = _newton(seed, lambda y: evaluate(
        y, panel_v=pv, panel_g=pg, range_fraction=range_fraction,
        tail_v=tail_v, q26=q26, q28=q28), "cutoff-em/dc")
    return dict(node_v=x, c18_v=x[0], current_a=(tail_v-x[3])/680,
                max_kcl_residual_a=error, devices=devices)


def step(*, previous, panel, range_fraction, tail_v, dt_s, q26, q28):
    pv, pg = panel_equivalent(panel)
    x, devices, error = _newton(list(previous["node_v"]), lambda y: evaluate(
        y, panel_v=pv, panel_g=pg, range_fraction=range_fraction,
        tail_v=tail_v, q26=q26, q28=q28,
        previous_base_v=previous["c18_v"], dt_s=dt_s), "cutoff-em/step")
    return dict(node_v=x, c18_v=x[0], current_a=(tail_v-x[3])/680,
                max_kcl_residual_a=error, devices=devices)
