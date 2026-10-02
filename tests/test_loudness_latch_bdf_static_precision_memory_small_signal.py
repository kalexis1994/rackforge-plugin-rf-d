import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import loudness_latch_bdf_static_precision_memory_small_signal as experiment
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_memory_transfer import propagate,node_difference,memory_difference,perturb_history
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters


class SmallSignal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(experiment.OUTPUT.read_bytes()))
        source=json.loads(gzip.decompress(experiment.SOURCE.read_bytes()))
        cls.source=[{k:v for k,v in w.items() if k!="experiments"} for w in source["windows"]]
        extrema=json.loads(gzip.decompress(experiment.EXTREMA.read_bytes()))
        cls.extrema_attack=next(w for w in extrema["windows"] if w["name"]=="attack")
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))

    def cases_with_base(self):
        for control in self.report["controls"]:
            yield control["case"],self.source[control["source_window_index"]],np.zeros(25),np.zeros(25)
        base=self.source[self.report["attack"]["source_window_index"]]
        for e in self.report["attack"]["experiments"]:
            for level in e["levels"]:
                for case in level["cases"]:
                    scale=case["sign"]*level["amplitude"]
                    yield case,base,scale*np.array(e["current_direction_v"]),scale*np.array(e["previous_direction_v"])

    def test_zero_controls_frozen_directions_and_all_previous_failures_preserved(self):
        self.assertEqual(len(self.report["controls"]),4)
        for control in self.report["controls"]:
            base=self.source[control["source_window_index"]]
            self.assertEqual(control["name"],base["name"])
            comparison=experiment.zero_comparison(control["case"],base)
            self.assertEqual(canonical(comparison),canonical(control["comparison"]))
            for row,reference in zip(control["case"]["steps"],base["reference"]):
                self.assertEqual(row["predicted_node_difference_v"],[0.]*94)
                self.assertEqual(row["predicted_memory_difference_v"],[0.]*25)
                self.assertEqual(row["history"]["time_s"],reference["history"]["time_s"])
        attack=self.report["attack"];base=self.source[attack["source_window_index"]]
        self.assertEqual(base["name"],"attack");self.assertEqual(canonical(attack["initial"]),canonical(base["initial"]))
        self.assertEqual(len(attack["experiments"]),6)
        for e,old in zip(attack["experiments"],self.extrema_attack["experiments"]):
            for key in ("direction","selection","unit_direction","current_direction_v","previous_direction_v"):
                self.assertEqual(e[key],old[key])
            self.assertEqual([l["amplitude"] for l in e["levels"]],[1/8,1/16,1/32,1/64])
            for level in e["levels"]:
                self.assertEqual([c["sign"] for c in level["cases"]],[1,-1])
                self.assertEqual(canonical(experiment.central_metrics(*level["cases"])),canonical(level["central_comparison"]))
                self.assertEqual(canonical(experiment.response_metrics(level["cases"])),canonical(level["one_sided_comparison"]))
        old_levels=[l for e in self.extrema_attack["experiments"] for l in e["levels"]]
        self.assertEqual(len(old_levels),18)
        self.assertEqual(sum(l["one_sided_comparison"]["passed"] for l in old_levels),0)
        self.assertFalse(self.report["original_18_attack_one_sided_failures_resolved"])

    def test_all_real_history_publications_predictions_and_injection_identity(self):
        count=0;cases=0
        for case,base,current,previous in self.cases_with_base():
            initial=unpack(self.network,base["initial"])
            old=perturb_history(self.network,initial,current,previous);pc=current;pp=previous
            self.assertEqual(canonical(pack(old)),canonical(case["initial"]));cases+=1
            ops=experiment.operators(base)
            for row,ref,op in zip(case["steps"],base["reference"],ops):
                self.assertEqual(state_hash(old),row["previous_history_sha256"])
                new=unpack(self.network,row["history"]);reference=unpack(self.network,ref["history"])
                h=ref["diagnostics"]["actual_dt_s"]
                self.assertEqual(h,row["diagnostics"]["actual_dt_s"]);self.assertEqual(new.time_s,reference.time_s)
                self.assertEqual(new.previous,old.current)
                pub=publication_check(self.network,old,new,h,row["diagnostics"])
                self.assertEqual(canonical(pub),canonical(row["publication"]))
                self.assertTrue(pub["round_trip_exact"]);self.assertLess(pub["max_published_kcl_a"],1e-11)
                self.assertLess(pub["max_branch_equation_error_v"],1e-14)
                self.assertLess(row["diagnostics"]["max_kcl_a"],1e-11);self.assertLess(row["diagnostics"]["correction_v"],1e-8)
                pn,pm=propagate(op,pc,pp)
                np.testing.assert_array_equal(pn,row["predicted_node_difference_v"])
                np.testing.assert_array_equal(pm,row["predicted_memory_difference_v"])
                np.testing.assert_array_equal(node_difference(new.current,reference.current),row["node_difference_v"])
                np.testing.assert_array_equal(memory_difference(new.current,reference.current),row["memory_difference_v"])
                old=new;pp,pc=pc,pm;count+=1
            self.assertEqual(canonical(pack(old)),canonical(case["final"]))
            self.assertEqual(case["complete"],len(case["steps"])==64)
            if case["stop"] is not None:self.assertEqual(canonical(case["stop"]["incoming"]),canonical(pack(old)))
        self.assertEqual(cases,52)
        self.assertEqual(count,sum(len(c["steps"]) for c,_,_,_ in self.cases_with_base()))

    def test_104_selected_fresh_replays_and_failed_budget_leave_memory_unchanged(self):
        count=0
        for case,base,_,_ in self.cases_with_base():
            for i in sorted({0,len(case["steps"])-1}):
                if i<0:continue
                old=unpack(self.network,case["initial"] if i==0 else case["steps"][i-1]["history"])
                row=case["steps"][i];snapshot=state_hash(old)
                new,d=self.network.advance(old,10.,row["diagnostics"]["actual_dt_s"])
                self.assertEqual(canonical(pack(new)),canonical(row["history"]))
                self.assertEqual(canonical(d),canonical(row["diagnostics"]))
                self.assertEqual(snapshot,state_hash(old));count+=1
        self.assertEqual(count,104)
        for base in self.source:
            old=unpack(self.network,base["initial"]);snapshot=state_hash(old)
            with self.assertRaises(ValueError):self.network.advance(old,10.,base["reference"][0]["diagnostics"]["actual_dt_s"],iterations=0)
            self.assertEqual(snapshot,state_hash(old))

    def test_storage_source_sha_summary_counts_and_unpromoted_scope(self):
        r=self.report;raw=experiment.OUTPUT.read_bytes();summary=json.loads(experiment.SUMMARY.read_text())
        s=summary["storage"]
        self.assertEqual(len(raw),s["bytes"]);self.assertEqual(hashlib.sha256(raw).hexdigest(),s["compressed_sha256"])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(hashlib.sha256(canonical(r)).hexdigest(),s["canonical_json_sha256"])
        for path,sha in r["source_sha256"].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha,path)
        self.assertEqual(r["absolute_linearization_gate_v"],1e-8);self.assertEqual(r["relative_linearization_gate"],1e-3)
        self.assertTrue(r["diagnostic_only"])
        for key in ("original_18_attack_one_sided_failures_resolved","amplitude_selected_for_integrator",
            "initial_memory_injections_are_accepted_states","local_adaptive_error_gate_applied","nonlinear_ball_bound_admitted",
            "temporal_error_bound_admitted","temporal_refinement_admitted","physical_switching_admitted","audio_admitted","deadline_admitted"):
            self.assertFalse(r[key])
        self.assertEqual(summary["zero_intervals"],sum(len(c["case"]["steps"]) for c in r["controls"]))
        self.assertEqual(summary["attack_cases"],48)
        for e,small in zip(r["attack"]["experiments"],summary["attack_experiments"]):
            for level,slevel in zip(e["levels"],small["levels"]):
                self.assertEqual(level["central_comparison"]["passed"],slevel["central"]["passed"])
                self.assertEqual(level["one_sided_comparison"]["passed"],slevel["one_sided"]["passed"])


if __name__=="__main__":unittest.main()
