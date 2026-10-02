import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import loudness_latch_bdf_static_precision_adaptive as producer
from loudness_latch_bdf_static_precision_adaptive import OUTPUT,SUMMARY,SOURCE,FIXED,POLICY,driver_audit,published,clock,decisions
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_memory_transfer import node_difference,memory_difference
from loudness_latch_bdf_survey import state_hash,trace,comparison
from loudness_latch_bdf_doubling_survey import canonical,case_summary,OUTPUTS
from loudness_latch_time_reference import frozen_rate
from bjt_charge_ngspice_probes import model_parameters


class AdaptiveCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.case=cls.report["case"];cls.steps=published(cls.case)
        reference=json.loads(gzip.decompress(SOURCE.read_bytes()))["case"]
        cls.reference_initial=reference["initial"];cls.reference_policy=reference["policy"]
        cls.reference_decisions=decisions(reference);cls.reference_steps=published(reference)
        cls.reference_clock=clock(cls.reference_steps)
        del reference
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_driver_ast_single_substitution_and_original_controller_functions(self):
        audit=driver_audit()
        self.assertEqual(canonical(audit),canonical(self.report["driver_audit"]))
        self.assertEqual(audit["network_constructor_substitutions"],1)
        self.assertTrue(audit["normalized_ast_equal"])
        for name in ("POLICY","startup_trial","trial","frozen_rate","publication_check"):
            self.assertIs(getattr(producer,name),getattr(producer.original_driver,name))
        self.assertEqual(self.case["policy"],self.reference_policy)
        self.assertEqual(self.case["growth_error_threshold"],.125)
        self.assertEqual(canonical(self.case["initial"]),canonical(self.reference_initial))

    def test_all_published_and_provisional_histories_and_direct_charge_publication(self):
        old=unpack(self.network,self.case["initial"]);published_count=0;shadow_count=0
        for accepted in self.case["accepted"]:
            snapshot=state_hash(old)
            self.assertEqual(snapshot,accepted["previous_history_sha256"])
            self.assertEqual(accepted["start_s"],old.time_s)
            d=accepted["diagnostics"]
            self.assertLessEqual(max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"]),1)
            self.assertLessEqual(d["junction_increment_v"],POLICY.junction_increment_v)
            self.assertLessEqual(d["positive_mode_step_product"],POLICY.positive_mode_step_product)
            previous=old
            for shadow in d.get("shadow_half_steps",[]):
                new=unpack(self.network,shadow["history"]);diag=shadow["diagnostics"]
                check=publication_check(self.network,previous,new,diag["actual_dt_s"],diag)
                self.assertEqual(canonical(check),canonical(shadow["publication"]))
                self.assertTrue(check["round_trip_exact"]);self.assertLess(check["max_published_kcl_a"],1e-11)
                self.assertLess(check["max_branch_equation_error_v"],1e-14)
                self.assertEqual(new.previous,previous.current);self.assertFalse(shadow["published"])
                self.assertLess(diag["correction_v"],1e-8);shadow_count+=1;previous=new
            previous=old
            for step in accepted["steps"]:
                new=unpack(self.network,step["history"]);diag=step["diagnostics"]
                check=publication_check(self.network,previous,new,diag["actual_dt_s"],diag)
                self.assertEqual(canonical(check),canonical(step["publication"]))
                self.assertTrue(check["round_trip_exact"]);self.assertLess(check["max_published_kcl_a"],1e-11)
                self.assertLess(check["max_branch_equation_error_v"],1e-14)
                self.assertLess(diag["max_kcl_a"],1e-11);self.assertLess(diag["correction_v"],1e-8)
                self.assertEqual(new.previous,previous.current)
                self.assertEqual(new.time_s,previous.time_s+diag["actual_dt_s"])
                published_count+=1;previous=new
            self.assertEqual(snapshot,state_hash(old));old=previous
        self.assertEqual(canonical(pack(old)),canonical(self.case["final"]))
        self.assertEqual(published_count,self.case["published_intervals"])
        self.assertEqual(self.case["attempts"],len(self.case["accepted"])+len(self.case["rejected"]))
        summary=case_summary(self.case)
        self.assertEqual(shadow_count,summary["provisional_accepted_half_intervals"])

    def test_controller_decisions_coordinate_contrasts_and_fixed_clock_states(self):
        c=self.report["contrast"];same=clock(self.steps)==self.reference_clock
        self.assertEqual(c["candidate_clock"],clock(self.steps));self.assertEqual(c["reference_clock"],self.reference_clock)
        self.assertEqual(c["published_clocks_equal"],same)
        self.assertEqual(c["candidate_decisions"],decisions(self.case))
        self.assertEqual(c["reference_decisions"],self.reference_decisions)
        self.assertEqual(c["controller_decisions_equal"],decisions(self.case)==self.reference_decisions)
        if same:
            self.assertEqual(len(c["rows"]),len(self.steps))
            for row,step,ref in zip(c["rows"],self.steps,self.reference_steps):
                a=unpack(self.network,step["history"]);b=unpack(self.network,ref["history"])
                nodes=node_difference(a.current,b.current);memory=memory_difference(a.current,b.current)
                np.testing.assert_array_equal(nodes,row["node_difference_v"])
                np.testing.assert_array_equal(memory,row["memory_difference_v"])
                self.assertEqual(float(np.max(abs(nodes))),row["max_node_difference_v"])
                self.assertEqual(float(np.max(abs(memory))),row["max_memory_coordinate_difference_v"])
                self.assertEqual(bool(np.max(abs(nodes))<1e-8),row["node_gate_passed"])
                self.assertEqual(bool(np.max(abs(memory))<1e-8),row["memory_gate_passed"])
        else:self.assertEqual(c["rows"],[])
        fixed=json.loads(gzip.decompress(FIXED.read_bytes()))
        fixed_steps=[dict(history=r["history"],diagnostics=r["diagnostics"]) for r in fixed["rows"]]
        if clock(self.steps)==clock(fixed_steps):
            identical=all(canonical(s["history"])==canonical(f["history"]) for s,f in zip(self.steps,fixed_steps))
            self.assertEqual(c["fixed_clock_states_identical"],identical)
        else:self.assertIsNone(c["fixed_clock_states_identical"])
        expected=bool(self.case["complete"] and c["initial_equal"] and same and c["controller_decisions_equal"]
            and all(r["node_gate_passed"] and r["memory_gate_passed"] for r in c["rows"]))
        self.assertEqual(self.report["controller_equivalence_passed"],expected)

    def test_selected_accepted_and_rejected_trial_replays_keep_incoming_state(self):
        accepted=self.case["accepted"];indices={0,len(accepted)-1}
        for limit in (.0023,.0024222,.00244205,.0025):
            i=next((i for i,a in enumerate(accepted) if a["steps"][-1]["history"]["time_s"]>=limit),None)
            if i is not None:indices.add(i)
        for i in sorted(indices):
            row=accepted[i];old=unpack(self.network,self.case["initial"] if i==0 else accepted[i-1]["steps"][-1]["history"])
            before=state_hash(old);rate=row["diagnostics"]["frozen_positive_rates_per_s"][0]
            fn=producer.startup_trial if old.previous is None else producer.trial
            result,diag,_=fn(self.network,old,10.,row["dt_s"],POLICY,rate)
            self.assertIsNotNone(result)
            self.assertEqual(canonical(dict(diag,startup=old.previous is None)),canonical(row["diagnostics"]))
            self.assertEqual(canonical([pack(h) for h,d in result]),canonical([s["history"] for s in row["steps"]]))
            self.assertEqual(before,state_hash(old))
        histories={state_hash(unpack(self.network,self.case["initial"])):self.case["initial"]}
        for step in self.steps:histories[state_hash(unpack(self.network,step["history"]))]=step["history"]
        reasons=set()
        for row in self.case["rejected"]:
            reason=row["diagnostics"]["reason"]
            if reason in reasons:continue
            reasons.add(reason);old=unpack(self.network,histories[row["previous_history_sha256"]]);before=state_hash(old)
            rate=frozen_rate(self.network.network,old.current,old.key_v)
            fn=producer.startup_trial if old.previous is None else producer.trial
            try:
                result,diag,_=fn(self.network,old,10.,row["dt_s"],POLICY,rate)
                self.assertIsNone(result);self.assertEqual(diag["reason"],reason)
            except (ValueError,OverflowError,np.linalg.LinAlgError):self.assertEqual(reason,"solve-rejected")
            self.assertEqual(before,state_hash(old))

    def test_storage_summary_temporal_comparisons_and_scope(self):
        r=self.report;raw=OUTPUT.read_bytes();summary=json.loads(SUMMARY.read_bytes());s=summary["storage"]
        self.assertEqual(s["bytes"],len(raw));self.assertEqual(s["compressed_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(gzip.decompress(raw),canonical(r))
        self.assertEqual(s["canonical_json_sha256"],hashlib.sha256(canonical(r)).hexdigest())
        for name,expected in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        for row,path in zip(r["temporal_comparisons"],OUTPUTS):
            reference=json.loads(gzip.decompress(path.read_bytes()))["case"]
            result=comparison(trace(reference),trace(self.case),reference["complete"] and self.case["complete"])
            self.assertEqual(canonical(result),canonical({k:v for k,v in row.items() if k not in ("reference","diagnostic_only")}))
        self.assertTrue(r["adaptive_controller_applied"]);self.assertTrue(r["modal_guard_uses_original_shared_derivative"])
        self.assertEqual(self.case["history_reset_count"],0);self.assertIsNone(self.case["selected_alternative"])
        self.assertTrue(r["diagnostic_only"])
        for k in ("original_controller_policy_modified","original_solver_modified","previous_reports_modified",
                  "trajectory_retimed","temporal_refinement_admitted","temporal_error_bound_admitted",
                  "independent_full_spatial_oracle","physical_switching_admitted","audio_admitted","deadline_admitted"):
            self.assertFalse(r[k])


if __name__=="__main__":unittest.main()
