"""Independent 16-node finite-difference oracle for native ladder stamping.

Recovery, VCAs and C10 are disconnected in these laboratory vectors. The
separate native end-to-end test checks coupling and transactional behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import (
    DEVICE_NODES, NODE_NAMES, conditional_ladder_ebers_moll_dc)
from filter_ladder_nonlinear_transient_reference import nonlinear_step


OUTPUT = Path(__file__).resolve().parents[1] / "evidence" / "ladder_native_vectors.json"


def generate_vectors() -> dict:
    cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250,
                                    contour_pin16_v=0),
                  range_fraction_from_ground=0.1,
                  is26_a=1e-14, is28_a=1e-14,
                  beta26=100, beta28=100, temperature_k=298.15)
    scenarios = []
    for r61 in (200, 200000):
        dc = conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)
        x = tuple(dc["nodes_v"][name] for name in NODE_NAMES)
        initial = x
        previous_bus = 0.0
        rows = []
        for index, bus in enumerate((0, 0.001, 0.001, -0.001, -0.001,
                                     0.01, 0.01, 0.0, -0.01, 0.0)):
            result = nonlinear_step(
                dc_solution=dc, dt_s=1/48000,
                previous_node_v=x, previous_bus_v=previous_bus,
                bus_v=bus)
            x = result["node_v"]
            rows.append(dict(index=index, bus_v=bus, node_v=list(x),
                             board_input_current_a=result["board_input_current_a"],
                             max_kcl_residual_a=result["max_charge_kcl_residual_a"]))
            previous_bus = bus
        scenarios.append(dict(r61_ohm=r61,
                              r30_ohm=dc["network_parameters"]["r30"],
                              tail_current_a=dc["tail_current_a"],
                              initial_node_v=list(initial), rows=rows))
    return dict(schema="rf-d/ladder-native-vectors/v1",
                source=["SVC-9 Fig. 9-11 PDF p. 13",
                        "SVC-9 Table 7-8 PDF pp. 30-31"],
                method="16-node finite-difference Newton, implicit Euler",
                units=dict(voltage="V", current="A", resistance="ohm",
                           time="s", capacitance="F"),
                node_order=list(NODE_NAMES), dt_s=1/48000,
                bjt=dict(is_a=1e-14, beta_forward=100,
                         beta_reverse=5, temperature_k=298.15),
                scenarios=scenarios)


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(generate_vectors(), indent=2) + "\n",
                      encoding="utf-8")
