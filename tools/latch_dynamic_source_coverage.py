"""Domain comparisons of manufacturer experiments against frozen model biases."""
import hashlib
import json
import math
from pathlib import Path
from loudness_lab_metadata import environment

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/"evidence/latch_dynamic_source_coverage.json"


def generate():
    ledger = json.loads((ROOT/"evidence/latch_charge_source_ledger.json").read_text())
    domain = json.loads((ROOT/"evidence/loudness_junction_domain_audit.json").read_text())
    pn = next(s for s in ledger["sources"] if s["id"]=="DS-PN100A-F08")
    lo,hi = pn["switching_curve"]["collector_current_domain_a"]
    rows = []
    for p in domain["cases"]:
        ic,ib = p["outgoing_current_a"]["collector"],p["outgoing_current_a"]["base"]
        # 1nA/1nV are comparison precision only, not physical acceptance ranges.
        ft_ic = math.isclose(ic,pn["ft"]["conditions"]["collector_current_a"],abs_tol=1e-9,rel_tol=0)
        ft_vce = math.isclose(p["vce_v"],pn["ft"]["conditions"]["vce_v"],abs_tol=1e-9,rel_tol=0)
        rows.append(dict(root=p["root"],ref=p["ref"],r61_ohm=p["r61_ohm"],collector_current_a=ic,
            snapshot_ic_over_ib=ic/ib if ib != 0 else None,vce_v=p["vce_v"],vcb_v=p["vcb_v"],
            switching_current_inside_curve_domain=lo<=ic<=hi,
            switching_driver_waveform_identified=False,
            ft_current_matches=ft_ic,ft_vce_matches=ft_vce,
            ft_bias_matches=ft_ic and ft_vce,case_temperature_identified=False,
            cobo_bias_matches=math.isclose(p["vcb_v"],pn["cob"]["conditions"]["vcb_v"],abs_tol=1e-9,rel_tol=0),
            dynamic_parameters_identified=False))
    paths = [ROOT/"tools/latch_dynamic_source_coverage.py",ROOT/"evidence/latch_charge_source_ledger.json",
             ROOT/"evidence/loudness_junction_domain_audit.json"]
    return dict(schema="rf-d/latch-dynamic-source-coverage/v1",cases=rows,environment=environment(),
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        experiment_source="DS-PN100A-F08",physical_lot_identified=False,selected_parameter_set=None,
        audio_admitted=False,transit_time_from_ft_assigned=False,storage_time_as_transit_assigned=False)


if __name__ == "__main__":
    r = generate()
    OUTPUT.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(cases=len(r["cases"]),
        switching_current_inside=sum(c["switching_current_inside_curve_domain"] for c in r["cases"]),
        ft_bias_matches=sum(c["ft_bias_matches"] for c in r["cases"]),
        cobo_bias_matches=sum(c["cobo_bias_matches"] for c in r["cases"]))))
