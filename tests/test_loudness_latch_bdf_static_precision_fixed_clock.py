import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_latch_bdf_static_precision_fixed_clock import OUTPUT,SUMMARY,SOURCE,schedule,STEP_COUNT,SOURCE_SHA256
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork,VERSION
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_memory_transfer import node_difference,memory_difference
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters


class FixedClock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.case=json.loads(gzip.decompress(SOURCE.read_bytes()))["case"]
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))
        cls.clock=schedule(cls.network,cls.case)

    def test_complete_source_clock_and_fresh_dc_identity(self):
        r=self.report
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(),SOURCE_SHA256)
        self.assertEqual(len(self.clock),STEP_COUNT)
        self.assertEqual(len(r["reference_clock"]),STEP_COUNT)
        self.assertEqual(canonical([{k:v for k,v in s.items() if k!="step"} for s in self.clock]),canonical(r["reference_clock"]))
        fresh,d=self.network.initial_history()
        self.assertEqual(canonical(pack(fresh)),canonical(r["initial"]))
        self.assertEqual(canonical(d),canonical(r["dc_diagnostics"]))
        matched=canonical(pack(fresh))==canonical(self.case["initial"])
        self.assertEqual(matched,r["fresh_dc_matches_reference"])
        self.assertTrue(matched);self.assertTrue(r["reference_lineage_verified"])
        self.assertEqual(r["reference_rejected_trials_not_executed"],49)
        self.assertEqual(self.clock[0]["step"]["diagnostics"]["method"],"backward-euler-startup")
        self.assertTrue(all(s["step"]["diagnostics"]["method"]=="variable-bdf2-charge/v1" for s in self.clock[1:]))

    def test_every_candidate_publication_lineage_and_comparison(self):
        old=unpack(self.network,self.report["initial"]);valid=0
        for row,slot in zip(self.report["rows"],self.clock):
            self.assertEqual(state_hash(old),row["previous_history_sha256"])
            new=unpack(self.network,row["history"]);reference=unpack(self.network,slot["step"]["history"])
            pub=publication_check(self.network,old,new,slot["dt_s"],row["diagnostics"])
            self.assertEqual(canonical(pub),canonical(row["publication"]))
            passed=bool(pub["round_trip_exact"] and pub["max_published_kcl_a"]<1e-11 and pub["max_branch_equation_error_v"]<1e-14)
            self.assertEqual(passed,row["publication_passed"])
            self.assertLess(row["diagnostics"]["max_kcl_a"],1e-11)
            self.assertLess(row["diagnostics"]["correction_v"],1e-8)
            self.assertEqual(new.previous,old.current);self.assertEqual(new.previous_key_v,old.key_v)
            self.assertEqual(new.time_s,slot["time_s"]);self.assertTrue(row["reference_time_equal"])
            self.assertEqual(row["diagnostics"]["actual_dt_s"],slot["dt_s"])
            nodes=node_difference(new.current,reference.current);memory=memory_difference(new.current,reference.current)
            np.testing.assert_array_equal(nodes,row["node_difference_v"])
            np.testing.assert_array_equal(memory,row["memory_difference_v"])
            self.assertEqual(float(np.max(abs(nodes))),row["max_node_difference_v"])
            self.assertEqual(float(np.max(abs(memory))),row["max_memory_coordinate_difference_v"])
            self.assertEqual(bool(np.max(abs(nodes))<1e-8),row["node_gate_passed"])
            self.assertEqual(bool(np.max(abs(memory))<1e-8),row["memory_gate_passed"])
            self.assertFalse(row["published"])
            if not passed:break
            old=new;valid+=1
        self.assertEqual(valid,self.report["valid_intervals"])
        self.assertEqual(canonical(pack(old)),canonical(self.report["final"]))
        self.assertEqual(self.report["solved_intervals"],len(self.report["rows"]))
        if self.report["stop"] is not None:
            self.assertEqual(canonical(self.report["stop"]["incoming"]),canonical(pack(old)))

    def test_selected_fresh_replays_and_failed_step_preserve_history(self):
        rows=self.report["rows"];indices={0,len(rows)-1}
        for limit in (.0023,.0024222,.00244205,.0025):
            selected=next((i for i,r in enumerate(rows) if r["history"]["time_s"]>=limit),None)
            if selected is not None:indices.add(selected)
        self.assertGreaterEqual(len(indices),2)
        for i in sorted(indices):
            row=rows[i];incoming=self.report["initial"] if i==0 else rows[i-1]["history"]
            old=unpack(self.network,incoming);before=state_hash(old)
            new,d=self.network.advance(old,10.,self.clock[i]["dt_s"])
            self.assertEqual(canonical(pack(new)),canonical(row["history"]))
            self.assertEqual(canonical(d),canonical(row["diagnostics"]))
            self.assertEqual(before,state_hash(old))
        if self.report["stop"] is not None and self.report["stop"]["reason"]=="solve-or-check-failed":
            stop=self.report["stop"];old=unpack(self.network,stop["incoming"]);before=state_hash(old)
            with self.assertRaises((ValueError,np.linalg.LinAlgError,OverflowError)):
                self.network.advance(old,10.,stop["dt_s"])
            self.assertEqual(before,state_hash(old))
        old=unpack(self.network,self.report["initial"]);before=state_hash(old)
        with self.assertRaisesRegex(ValueError,"positive integer offline budgets"):
            self.network.advance(old,10.,self.clock[0]["dt_s"],iterations=0)
        self.assertEqual(before,state_hash(old))

    def test_storage_summary_outcomes_and_no_temporal_promotion(self):
        r=self.report;raw=OUTPUT.read_bytes();s=json.loads(SUMMARY.read_bytes());storage=s["storage"]
        self.assertEqual(len(raw),storage["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),storage["compressed_sha256"])
        self.assertEqual(gzip.decompress(raw),canonical(r))
        self.assertEqual(hashlib.sha256(canonical(r)).hexdigest(),storage["canonical_json_sha256"])
        for name,expected in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        self.assertEqual(r["candidate_version"],VERSION);self.assertEqual(r["planned_intervals"],6486)
        complete=len(r["rows"])==6486 and r["stop"] is None and r["final"]["time_s"]==.003
        self.assertEqual(r["complete"],complete)
        equivalent=complete and all(row["node_gate_passed"] and row["memory_gate_passed"] for row in r["rows"])
        self.assertEqual(r["fixed_clock_equivalence_passed"],equivalent)
        self.assertEqual(s["node_comparison_failures"],sum(not row["node_gate_passed"] for row in r["rows"]))
        self.assertEqual(s["memory_comparison_failures"],sum(not row["memory_gate_passed"] for row in r["rows"]))
        self.assertEqual(s["max_node_difference_v"],max(row["max_node_difference_v"] for row in r["rows"]))
        self.assertEqual(s["max_memory_coordinate_difference_v"],max(row["max_memory_coordinate_difference_v"] for row in r["rows"]))
        self.assertEqual(r["history_reset_count"],0);self.assertTrue(r["diagnostic_only"])
        for key in ("trajectory_retimed","adaptive_controller_applied","original_solver_modified",
                    "original_reset_fd_gate_closed","previous_reports_modified","independent_full_spatial_oracle",
                    "physical_switching_admitted","temporal_error_bound_admitted","temporal_refinement_admitted",
                    "audio_admitted","deadline_admitted"):self.assertFalse(r[key])


if __name__=="__main__":unittest.main()
