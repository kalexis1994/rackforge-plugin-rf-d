"""Independent finite-difference fixtures for Q26/Q28/C18 and panel reduction."""
import json
from pathlib import Path
from cutoff_ebers_moll_reference import NODES, panel_equivalent, solve_dc, step

OUTPUT = Path(__file__).resolve().parents[1]/"evidence"/"cutoff_native_vectors.json"


def generate_vectors():
    cases = []
    for name, temperature, bf26, bf28, initial_tail in (
            ("nominal_active", 298.15, 100, 100, 2.0),
            ("cool_loaded", 285, 80, 160, 0.02),
            ("warm_asymmetric", 315, 150, 70, 9.4)):
        q26 = dict(is_a=1e-14, beta_forward=bf26, beta_reverse=5,
                   temperature_k=temperature)
        q28 = dict(is_a=1e-14, beta_forward=bf28, beta_reverse=5,
                   temperature_k=temperature)
        panel = dict(cutoff_fraction_from_neg10=0.5, scale_active_ohm=250,
                     contour_pin16_v=0, external_control_v=None,
                     external_source_ohm=0, filter_mod_on=False,
                     modulation_source_v=None, modulation_source_ohm=0,
                     keyboard_1_3_on=False, keyboard_2_3_on=False,
                     keyboard_cv_v=None, keyboard_source_ohm=0)
        state = solve_dc(panel=panel, range_fraction=0.1, tail_v=initial_tail,
                         q26=q26, q28=q28)
        initial = state
        rows = []
        for index in range(24):
            b = dict(panel)
            b["cutoff_fraction_from_neg10"] = 0.5 + (0.08 if index >= 3 else 0)
            b["contour_pin16_v"] = 0.08 if index >= 6 else 0
            if index >= 9:
                b.update(keyboard_1_3_on=True, keyboard_2_3_on=True,
                         keyboard_cv_v=1.0, keyboard_source_ohm=1200)
            if index >= 12:
                b.update(filter_mod_on=True, modulation_source_v=-0.3,
                         modulation_source_ohm=2000)
            if index >= 15:
                b.update(external_control_v=0.2, external_source_ohm=10000)
            tail = initial_tail if index < 18 else (0.02 if index < 21 else 2.0)
            fraction = 0.1 if index < 8 else 0.15
            state = step(previous=state, panel=b, range_fraction=fraction,
                         tail_v=tail, dt_s=1/48000, q26=q26, q28=q28)
            pv, pg = panel_equivalent(b)
            rows.append(dict(panel=b, range_fraction=fraction, tail_v=tail,
                             panel_v=pv, panel_g=pg, **state))
        cases.append(dict(name=name, q26=q26, q28=q28,
                          initial_panel=panel, initial_tail_v=initial_tail,
                          initial_range_fraction=0.1, initial=initial, rows=rows))
    return dict(schema="rf-d/cutoff-native-vectors/v1", node_order=list(NODES),
                sources=["SVC-9 Fig. 9-11 PDF p. 13", "SVC-9 Fig. 9-17 PDF p. 19",
                         "SVC-9 Table 7-8 PDF pp. 30-31"],
                method="four-node finite-difference Newton; implicit Euler C18",
                dt_s=1/48000, cases=cases)


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(generate_vectors(), indent=2)+"\n", encoding="utf-8")
