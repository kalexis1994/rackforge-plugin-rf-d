import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import loudness_latch_bdf_static_precision_memory_extrema as experiment
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_memory_transfer import perturb_history,propagate,node_difference,memory_difference
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters


class Extrema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(experiment.OUTPUT.read_bytes()))
        data=json.loads(gzip.decompress(experiment.SOURCE.read_bytes()))
        cls.source=[{k:v for k,v in w.items() if k!="experiments"} for w in data["windows"]]
        cls.basis=json.loads(gzip.decompress(experiment.BASIS.read_bytes()))["windows"]
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_frozen_selection_normalization_peak_witness_and_initial_injections(self):
        self.assertEqual(len(self.report["windows"]),4);count=0
        for w,base,basis in zip(self.report["windows"],self.source,self.basis):
            self.assertEqual(w["name"],base["name"]);self.assertEqual(w["name"],basis["name"])
            self.assertEqual(canonical(w["initial"]),canonical(base["initial"]))
            self.assertEqual(w["reference_end_s"],base["end_s"])
            initial=unpack(self.network,w["initial"])
            selected=experiment.directions(self.network,basis)
            self.assertEqual(len(w["experiments"]),6)
            for e,d in zip(w["experiments"],selected):
                self.assertEqual(e["direction"],d["name"]);self.assertEqual(e["selection"],d["selection"])
                v=np.array(e["unit_direction"]);np.testing.assert_array_equal(v,d["unit_direction"])
                self.assertAlmostEqual(np.linalg.norm(v),1.,places=12)
                current=np.array(e["current_direction_v"]);previous=np.array(e["previous_direction_v"])
                np.testing.assert_array_equal(current,experiment.KICK_V*v[:25])
                np.testing.assert_array_equal(previous,experiment.KICK_V*v[25:])
                if e["selection"] is not None:
                    i=e["selection"]["index"];row=basis["rows"][i]
                    if e["direction"]=="maximum-node_basis":matrix=np.array(row["cumulative_node_matrix"])
                    elif e["direction"]=="maximum-memory_basis":matrix=np.array(row["cumulative_memory_matrix"])
                    else:
                        prior_matrix=np.hstack((np.eye(25),np.zeros((25,25)))) if i==0 else np.array(basis["rows"][i-1]["cumulative_memory_matrix"])
                        matrix=np.vstack((np.array(row["cumulative_memory_matrix"]),prior_matrix))
                    self.assertAlmostEqual(np.linalg.norm(matrix@v)/e["selection"]["spectral_norm"],1.,places=11)
                self.assertEqual([l["amplitude"] for l in e["levels"]],[1.,.5,.25])
                for level in e["levels"]:
                    self.assertEqual([c["sign"] for c in level["cases"]],[1,-1])
                    for case in level["cases"]:
                        scale=level["amplitude"]*case["sign"]
                        injected=perturb_history(self.network,initial,scale*current,scale*previous)
                        self.assertEqual(canonical(pack(injected)),canonical(case["initial"]))
                        self.assertEqual(injected.current.joint.node_v,initial.current.joint.node_v)
                        self.assertEqual(injected.current.node_low_v,initial.current.node_low_v)
                        self.assertEqual(injected.previous.joint.node_v,initial.previous.joint.node_v)
                        self.assertEqual(injected.previous.node_low_v,initial.previous.node_low_v);count+=1
        self.assertEqual(count,144)

    def test_every_history_publication_prediction_and_individual_central_bias_metrics(self):
        count=0;comparisons=0
        for w,base in zip(self.report["windows"],self.source):
            operators=[dict(op,node_map=np.array(op["node_map"]),memory_map=np.array(op["memory_map"])) for op in base["operators"]]
            for e in w["experiments"]:
                for level in e["levels"]:
                    for case in level["cases"]:
                        old=unpack(self.network,case["initial"]);scale=case["sign"]*level["amplitude"]
                        pc=scale*np.array(e["current_direction_v"]);pp=scale*np.array(e["previous_direction_v"])
                        for row,reference,op in zip(case["steps"],base["reference"],operators):
                            self.assertEqual(state_hash(old),row["previous_history_sha256"])
                            new=unpack(self.network,row["history"]);ref=unpack(self.network,reference["history"])
                            h=reference["diagnostics"]["actual_dt_s"]
                            self.assertEqual(h,row["diagnostics"]["actual_dt_s"])
                            self.assertEqual(new.previous,old.current);self.assertEqual(new.time_s,ref.time_s)
                            pub=publication_check(self.network,old,new,h,row["diagnostics"])
                            self.assertEqual(canonical(pub),canonical(row["publication"]))
                            self.assertTrue(pub["round_trip_exact"]);self.assertLess(pub["max_published_kcl_a"],1e-11)
                            self.assertLess(pub["max_branch_equation_error_v"],1e-14)
                            self.assertLess(row["diagnostics"]["max_kcl_a"],1e-11);self.assertLess(row["diagnostics"]["correction_v"],1e-8)
                            pn,pm=propagate(op,pc,pp)
                            np.testing.assert_array_equal(pn,row["predicted_node_difference_v"])
                            np.testing.assert_array_equal(pm,row["predicted_memory_difference_v"])
                            np.testing.assert_array_equal(node_difference(new.current,ref.current),row["node_difference_v"])
                            np.testing.assert_array_equal(memory_difference(new.current,ref.current),row["memory_difference_v"])
                            old=new;pp,pc=pc,pm;count+=1
                        self.assertEqual(canonical(pack(old)),canonical(case["final"]))
                        self.assertEqual(case["complete"],len(case["steps"])==64)
                        if case["stop"] is not None:self.assertEqual(canonical(case["stop"]["incoming"]),canonical(pack(old)))
                        self.assertFalse(case["local_adaptive_error_gate_applied"]);self.assertFalse(case["published"])
                    self.assertEqual(canonical(experiment.central_metrics(*level["cases"])),canonical(level["central_comparison"]))
                    self.assertEqual(canonical(experiment.response_metrics(level["cases"])),canonical(level["one_sided_comparison"]))
                    # An independent parity identity verifies the shared baseline
                    # and sign orientation, regardless of whether a gate passes.
                    for plus,minus,row in zip(*[c["steps"] for c in level["cases"]],level["one_sided_comparison"]["rows"]):
                        for name in ("node","memory"):
                            p=np.array(plus[name+"_difference_v"]);m=np.array(minus[name+"_difference_v"])
                            even=np.array(row["even_"+name+"_response_v"]);odd=(p-m)/2
                            np.testing.assert_allclose(even+odd,p,rtol=1e-12,atol=1e-18)
                    comparisons+=1
        self.assertEqual(comparisons,72)
        self.assertEqual(count,sum(len(c["steps"]) for w in self.report["windows"] for e in w["experiments"] for l in e["levels"] for c in l["cases"]))

    def test_selected_fresh_nonlinear_replays_and_immutable_budget_failures(self):
        count=0
        for w,base in zip(self.report["windows"],self.source):
            for e in w["experiments"]:
                for sign_case in e["levels"][0]["cases"]:
                    for i in sorted({0,len(sign_case["steps"])-1}):
                        if i<0:continue
                        old=unpack(self.network,sign_case["initial"] if i==0 else sign_case["steps"][i-1]["history"])
                        row=sign_case["steps"][i];snapshot=state_hash(old)
                        new,d=self.network.advance(old,10.,row["diagnostics"]["actual_dt_s"])
                        self.assertEqual(canonical(pack(new)),canonical(row["history"]))
                        self.assertEqual(canonical(d),canonical(row["diagnostics"]))
                        self.assertEqual(state_hash(old),snapshot);count+=1
            old=unpack(self.network,w["initial"]);snapshot=state_hash(old)
            with self.assertRaises(ValueError):self.network.advance(old,10.,base["reference"][0]["diagnostics"]["actual_dt_s"],iterations=0)
            self.assertEqual(snapshot,state_hash(old))
        self.assertEqual(count,96)

    def test_exact_storage_inputs_gate_counts_and_unpromoted_scope(self):
        r=self.report;raw=experiment.OUTPUT.read_bytes()
        summary=json.loads(experiment.SUMMARY.read_text(encoding="utf-8"));s=summary["storage"]
        self.assertEqual(len(raw),s["bytes"]);self.assertEqual(hashlib.sha256(raw).hexdigest(),s["compressed_sha256"])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(hashlib.sha256(canonical(r)).hexdigest(),s["canonical_json_sha256"])
        for path,expected in r["source_sha256"].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected,path)
        self.assertEqual(r["kick_double_history_euclidean_v"],1e-6);self.assertEqual(r["amplitudes"],[1.,.5,.25])
        self.assertEqual(r["absolute_linearization_gate_v"],1e-8);self.assertEqual(r["relative_linearization_gate"],1e-3)
        self.assertEqual(r["history_reset_count"],0);self.assertEqual(r["new_spatial_map_solves"],0)
        self.assertTrue(r["diagnostic_only"]);self.assertTrue(r["reference_clock_preserved"])
        for key in ("initial_memory_injections_are_accepted_states","local_adaptive_error_gate_applied",
            "full_nonlinear_direction_validation","temporal_error_bound_admitted","temporal_refinement_admitted",
            "physical_switching_admitted","audio_admitted","deadline_admitted"):self.assertFalse(r[key])
        for w,small in zip(r["windows"],summary["windows"]):
            self.assertEqual(small["nonlinear_cases"],36)
            self.assertEqual(small["central_passes"],sum(l["central_comparison"]["passed"] for e in w["experiments"] for l in e["levels"]))
            self.assertEqual(small["one_sided_passes"],sum(l["one_sided_comparison"]["passed"] for e in w["experiments"] for l in e["levels"]))


if __name__=="__main__":unittest.main()
