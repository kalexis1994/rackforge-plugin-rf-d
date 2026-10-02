import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import loudness_latch_bdf_static_precision_memory_long as experiment
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_memory_transfer import (transfer,propagate,stamps,perturb_history,
    node_difference,memory_difference)
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters


class LongMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(experiment.OUTPUT.read_bytes()))
        cls.clock=json.loads(gzip.decompress(experiment.CLOCK.read_bytes()))
        cls.original=json.loads(gzip.decompress(experiment.SOURCE.read_bytes()))["case"]
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_declared_anchors_reference_clock_and_directions(self):
        self.assertEqual(len(self.report["windows"]),4)
        for w,(name,limit) in zip(self.report["windows"],experiment.WINDOWS):
            self.assertEqual(w["name"],name);self.assertEqual(w["anchor_limit_s"],limit)
            ai=max(i for i,r in enumerate(self.original["accepted"]) if r["steps"][-1]["history"]["time_s"]<=limit)
            ci=max(i for i,r in enumerate(self.clock["reference_clock"]) if r["trial_index"]==ai)
            self.assertEqual(ai,w["E4G8_accepted_anchor_index"])
            self.assertEqual(ci,w["compensated_clock_anchor_index"])
            self.assertEqual(canonical(w["initial"]),canonical(self.clock["rows"][ci]["history"]))
            self.assertEqual(canonical(w["reference"]),canonical(self.clock["rows"][ci+1:ci+1+len(w["reference"])]))
            self.assertEqual(w["reference_complete"],len(w["reference"])==64)
            initial=unpack(self.network,w["initial"])
            ds=experiment.directions(self.network,initial,self.original["accepted"][ai])
            self.assertEqual(len(w["experiments"]),8)
            for e,(direction,current,previous) in zip(w["experiments"],ds):
                self.assertEqual(e["direction"],direction)
                np.testing.assert_array_equal(current,e["current_direction_v"])
                np.testing.assert_array_equal(previous,e["previous_direction_v"])
            old=initial
            for s in w["reference"]:
                self.assertEqual(state_hash(old),s["previous_history_sha256"])
                new=unpack(self.network,s["history"])
                pub=publication_check(self.network,old,new,s["diagnostics"]["actual_dt_s"],s["diagnostics"])
                self.assertEqual(canonical(pub),canonical(s["publication"]))
                self.assertEqual(new.previous,old.current);old=new
            self.assertEqual(old.time_s,w["end_s"])

    def test_maps_backward_gates_and_four_independent_rational_replays(self):
        count=0;audits=0
        for w in self.report["windows"]:
            old=unpack(self.network,w["initial"])
            for i,(s,stored) in enumerate(zip(w["reference"],w["operators"])):
                new=unpack(self.network,s["history"])
                virtual,c=self.network.effective_history(old,s["diagnostics"]["actual_dt_s"])
                _,j=self.network.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(np.array(s["diagnostics"]["increment_v"]))
                b,p,d=stamps(self.network,new,c["effective_dt_s"])
                x=np.array(stored["node_map"]);t=np.array(stored["memory_map"])
                _,errors=backward_errors(j,b,x)
                self.assertEqual(errors["binary_componentwise_backward_error"],stored["linear_solve"]["binary_componentwise_backward_error"])
                self.assertEqual(errors["decimal80_componentwise_backward_error"],stored["linear_solve"]["decimal80_componentwise_backward_error"])
                self.assertLess(max(errors.values()),1e-10)
                np.testing.assert_array_equal(p@x+d,t);self.assertEqual(c,stored["coefficients"])
                if i in experiment.AUDIT_INDICES:
                    replay=transfer(self.network,old,new,s["diagnostics"])
                    self.assertEqual(canonical(experiment.serial(replay)),canonical(stored))
                    a=next(a["audit"] for a in w["audits"] if a["index"]==i)
                    if a["passed"]:
                        ax=np.array(a["node_map"]);at=np.array(a["memory_map"])
                        np.testing.assert_array_equal(np.array(a["publication_gradient"])@ax+np.array(a["direct_memory"]),at)
                        self.assertEqual(float(np.max(abs(ax-x)/(1+abs(ax)))),a["maximum_scaled_node_map_difference"])
                        self.assertEqual(float(np.max(abs(at-t)/(1+abs(at)))),a["maximum_scaled_memory_map_difference"])
                        self.assertTrue(a["exact_solve"]["exact_rational_residual_zero"])
                        self.assertLess(max(a["backward_errors"].values()),1e-10)
                    passed=bool(a["passed"] and a["decimal80_100_rounded_jacobian_equal"]
                        and a["maximum_scaled_node_map_difference"]<1e-8 and a["maximum_scaled_memory_map_difference"]<1e-8)
                    self.assertEqual(passed,a["map_gate_passed"]);audits+=1
                    if i==31:
                        fresh=experiment.audit_map(self.network,old,s,replay)
                        self.assertEqual(canonical(fresh),canonical(a))
                old=new;count+=1
        self.assertEqual(count,256);self.assertEqual(audits,12)

    def test_every_nonlinear_history_publication_tangent_and_central_gate(self):
        cases=0;steps=0;contrasts=0
        for w in self.report["windows"]:
            initial=unpack(self.network,w["initial"])
            ops=[dict(o,node_map=np.array(o["node_map"]),memory_map=np.array(o["memory_map"])) for o in w["operators"]]
            for e in w["experiments"]:
                current=np.array(e["current_direction_v"]);previous=np.array(e["previous_direction_v"])
                self.assertEqual([l["amplitude"] for l in e["levels"]],[1.,.5])
                for l in e["levels"]:
                    self.assertEqual([c["sign"] for c in l["cases"]],[1,-1])
                    for case in l["cases"]:
                        scale=case["sign"]*l["amplitude"];pc=scale*current;pp=scale*previous
                        old=perturb_history(self.network,initial,pc,pp)
                        self.assertEqual(canonical(pack(old)),canonical(case["initial"]));cases+=1
                        for s,base,op in zip(case["steps"],w["reference"],ops):
                            self.assertEqual(state_hash(old),s["previous_history_sha256"])
                            h=base["diagnostics"]["actual_dt_s"]
                            new=unpack(self.network,s["history"]);ref=unpack(self.network,base["history"])
                            self.assertEqual(h,s["diagnostics"]["actual_dt_s"])
                            self.assertEqual(new.time_s,ref.time_s);self.assertEqual(new.previous,old.current)
                            pub=publication_check(self.network,old,new,h,s["diagnostics"])
                            self.assertEqual(canonical(pub),canonical(s["publication"]))
                            self.assertTrue(pub["round_trip_exact"]);self.assertLess(pub["max_published_kcl_a"],1e-11)
                            self.assertLess(pub["max_branch_equation_error_v"],1e-14)
                            self.assertLess(s["diagnostics"]["max_kcl_a"],1e-11)
                            self.assertLess(s["diagnostics"]["correction_v"],1e-8)
                            pn,pm=propagate(op,pc,pp)
                            np.testing.assert_array_equal(pn,s["predicted_node_difference_v"])
                            np.testing.assert_array_equal(pm,s["predicted_memory_difference_v"])
                            np.testing.assert_array_equal(node_difference(new.current,ref.current),s["node_difference_v"])
                            np.testing.assert_array_equal(memory_difference(new.current,ref.current),s["memory_difference_v"])
                            self.assertFalse(s["published"]);old=new;pp,pc=pc,pm;steps+=1
                        self.assertEqual(canonical(pack(old)),canonical(case["final"]))
                        self.assertEqual(case["complete"],len(case["steps"])==64)
                        if case["stop"] is not None:
                            self.assertEqual(canonical(case["stop"]["incoming"]),canonical(pack(old)))
                        self.assertFalse(case["local_adaptive_error_gate_applied"])
                    central=experiment.central_metrics(*l["cases"])
                    self.assertEqual(canonical(central),canonical(l["central_comparison"]));contrasts+=1
        self.assertEqual(cases,128);self.assertEqual(contrasts,64)
        self.assertEqual(steps,sum(len(c["steps"]) for w in self.report["windows"] for e in w["experiments"] for l in e["levels"] for c in l["cases"]))

    def test_selected_fresh_nonlinear_replays_and_immutable_failed_budget(self):
        count=0
        for w in self.report["windows"]:
            for e in w["experiments"]:
                case=e["levels"][0]["cases"][0]
                for i in sorted({0,len(case["steps"])-1}):
                    if i<0:continue
                    old=unpack(self.network,case["initial"] if i==0 else case["steps"][i-1]["history"])
                    row=case["steps"][i];snapshot=state_hash(old);h=row["diagnostics"]["actual_dt_s"]
                    new,diag=self.network.advance(old,10.,h)
                    self.assertEqual(canonical(pack(new)),canonical(row["history"]))
                    self.assertEqual(canonical(diag),canonical(row["diagnostics"]))
                    self.assertEqual(snapshot,state_hash(old));count+=1
            old=unpack(self.network,w["initial"]);snapshot=state_hash(old)
            with self.assertRaises(ValueError):
                self.network.advance(old,10.,w["reference"][0]["diagnostics"]["actual_dt_s"],iterations=0)
            self.assertEqual(snapshot,state_hash(old))
        self.assertEqual(count,64)

    def test_storage_inputs_summary_and_unpromoted_scope(self):
        r=self.report;raw=experiment.OUTPUT.read_bytes()
        summary=json.loads(experiment.SUMMARY.read_text(encoding="utf-8"));s=summary["storage"]
        self.assertEqual(len(raw),s["bytes"]);self.assertEqual(hashlib.sha256(raw).hexdigest(),s["compressed_sha256"])
        self.assertEqual(gzip.decompress(raw),canonical(r))
        self.assertEqual(hashlib.sha256(canonical(r)).hexdigest(),s["canonical_json_sha256"])
        for path,expected in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected,path)
        self.assertEqual(r["audit_indices"],[0,31,63]);self.assertEqual(r["intervals_per_window"],64)
        self.assertEqual(r["kick_coordinate_v"],1e-6);self.assertEqual(r["charge_coordinate_scale_c_per_v"],1e-12)
        self.assertEqual(r["absolute_linearization_gate_v"],1e-8);self.assertEqual(r["relative_linearization_gate"],1e-3)
        self.assertEqual(r["history_reset_count"],0);self.assertTrue(r["diagnostic_only"])
        self.assertTrue(r["reference_clock_preserved"]);self.assertTrue(r["inherited_residual"])
        for key in ("fresh_dc_new","initial_memory_injections_are_accepted_states","local_adaptive_error_gate_applied",
            "independent_full_spatial_oracle","temporal_error_bound_admitted","temporal_refinement_admitted",
            "physical_switching_admitted","audio_admitted","deadline_admitted"):
            self.assertFalse(r[key])
        for w,small in zip(r["windows"],summary["windows"]):
            self.assertEqual(small["nonlinear_cases"],32)
            self.assertEqual(small["nonlinear_complete"],sum(c["complete"] for e in w["experiments"] for l in e["levels"] for c in l["cases"]))
            self.assertEqual(small["central_passes"],sum(l["central_comparison"]["passed"] for e in w["experiments"] for l in e["levels"]))


if __name__=="__main__":unittest.main()
