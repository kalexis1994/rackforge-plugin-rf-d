import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_charge_reference import ChargedNetwork
from loudness_latch_time_probes import unpack,state_hash,POLICIES
from loudness_latch_rejection_audit import coordinate_floor,gauge_difference_error,diagnose,origin_scaled_error


class RejectionDiagnosis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/"evidence/loudness_latch_rejection_audit.json").read_text())

    def test_actual_second_half_fails_with_the_same_unmodified_history(self):
        r=self.report["replay"];network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
        old=unpack(network,r["previous"],10.0);snapshot=copy.deepcopy(old)
        half,_=network.step(old,10.0,r["macro_dt_s"]/2)
        with self.assertRaises(ValueError):network.step(half,10.0,r["macro_dt_s"]/2)
        for use_fd,key in ((False,"hybrid"),(True,"full_fd")):
            audit=diagnose(network,half,r["macro_dt_s"]/2,use_fd=use_fd)
            self.assertEqual(audit["status"],"line-search-rejected")
            self.assertEqual(audit["final_node_v"],r[key]["final_node_v"])
            last=audit["iterations"][-1]
            self.assertGreater(last["max_kcl_a"],1e-11)
            self.assertLess(last["correction_v"],1e-8)
            self.assertEqual(last["limiting_row"],92)
            self.assertEqual(len(last["trials"]),24)
            self.assertFalse(any(t["accepted"] for t in last["trials"]))
        self.assertEqual(old,snapshot)
        self.assertEqual(state_hash(old),r["previous_state_sha256"])

    def test_next_float_timing_coordinates_cannot_close_the_recorded_residual(self):
        r=self.report["replay"];network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
        half=unpack(network,r["half_state"],10.0)
        for key in ("hybrid","full_fd"):
            floor=coordinate_floor(network,half,r[key])
            self.assertEqual(floor,r[key]["coordinate_floor"])
            self.assertFalse(floor["timing_coordinate_changes"])
            self.assertGreater(abs(floor["timing_kcl_a"]),1e-11)
            for neighbor in floor["nearest_representable_neighbors"]:
                self.assertGreater(abs(neighbor["timing_kcl_a"]),1e-11)

    def test_charge_origin_changes_the_error_decision_but_not_the_increment(self):
        for s in self.report["charge_origin_shadows"]:
            p=POLICIES[s["policy_index"]]
            a=np.array(s["full_charge_c"]);b=np.array(s["fine_charge_c"])
            self.assertGreater(s["offsets"][1]["charge_error_ratio"],1)
            for row in s["offsets"]:
                offset=row["offset_c"]
                ratio=origin_scaled_error(a,b,offset,p.charge_abs_c,p.charge_relative)
                self.assertEqual(ratio,row["charge_error_ratio"])
                self.assertLess(gauge_difference_error(a,b,offset,s["dt_s"]),1e-50)
                if offset:self.assertLess(ratio,1)
            self.assertTrue(s["original_rejection_retained"])
            self.assertFalse(s["published_shadow"])

    def test_audit_sources_original_gates_and_scope_are_preserved(self):
        for path,h in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        self.assertTrue(self.report["gates_unchanged"])
        self.assertFalse(self.report["original_report_modified"])
        for flag in ("physical_switching_admitted","temporal_refinement_admitted","audio_admitted"):
            self.assertFalse(self.report[flag])
        self.assertIsNone(self.report["selected"])


if __name__=="__main__":unittest.main()
