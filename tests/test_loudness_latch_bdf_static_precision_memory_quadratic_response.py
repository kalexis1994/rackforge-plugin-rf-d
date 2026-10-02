import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import loudness_latch_bdf_static_precision_memory_quadratic_response as experiment
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_memory_transfer import propagate,perturb_history,node_difference,memory_difference
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters


class QuadraticResponse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(experiment.OUTPUT.read_bytes()))
        cls.coefficients=json.loads(gzip.decompress(experiment.COEFFICIENTS.read_bytes()))
        source=json.loads(gzip.decompress(experiment.SOURCE.read_bytes()))
        cls.source=[{k:v for k,v in w.items() if k!="experiments"} for w in source["windows"]]
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_reserved_levels_frozen_coefficients_directions_and_initial_histories(self):
        self.assertEqual(self.report["amplitudes"],self.coefficients["reserved_response_amplitudes"])
        self.assertEqual(self.report["amplitudes"],[.75,.375,.1875]);count=0
        for w,coef,base in zip(self.report["windows"],self.coefficients["windows"],self.source):
            self.assertEqual(w["name"],coef["name"]);self.assertEqual(w["name"],base["name"])
            self.assertEqual(canonical(w["initial"]),canonical(base["initial"]))
            initial=unpack(self.network,w["initial"])
            for e,definition in zip(w["experiments"],coef["definitions"]):
                self.assertEqual(e["definition"],definition)
                self.assertEqual([l["amplitude"] for l in e["levels"]],[.75,.375,.1875])
                for level in e["levels"]:
                    self.assertEqual([c["sign"] for c in level["cases"]],[1,-1])
                    for case in level["cases"]:
                        scale=case["sign"]*level["amplitude"]
                        injected=perturb_history(self.network,initial,scale*np.array(definition["current_direction_v"]),scale*np.array(definition["previous_direction_v"]))
                        self.assertEqual(canonical(pack(injected)),canonical(case["initial"]))
                        self.assertEqual(injected.current.joint.node_v,initial.current.joint.node_v);count+=1
        self.assertEqual(count,144)

    def test_every_real_publication_linear_quadratic_and_even_prediction_and_gates(self):
        count=0;levels=0
        for w,coef,base in zip(self.report["windows"],self.coefficients["windows"],self.source):
            ops=[dict(o,node_map=np.array(o["node_map"]),memory_map=np.array(o["memory_map"])) for o in base["operators"]]
            for k,e in enumerate(w["experiments"]):
                definition=e["definition"]
                for level in e["levels"]:
                    amplitude=level["amplitude"]
                    for case in level["cases"]:
                        scale=case["sign"]*amplitude;pc=scale*np.array(definition["current_direction_v"]);pp=scale*np.array(definition["previous_direction_v"])
                        old=unpack(self.network,case["initial"])
                        for row,ref,op,cr in zip(case["steps"],base["reference"],ops,coef["rows"]):
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
                            for name,linear in (("node",pn),("memory",pm)):
                                even=amplitude*amplitude/2*np.array(cr[name+"_second_v"])[:,k]
                                np.testing.assert_array_equal(even,row["quadratic_even_"+name+"_prediction_v"])
                                np.testing.assert_array_equal(linear+even,row["quadratic_"+name+"_prediction_v"])
                            old=new;pp,pc=pc,pm;count+=1
                        self.assertEqual(canonical(pack(old)),canonical(case["final"]))
                        self.assertEqual(case["complete"],len(case["steps"])==64)
                        if case["stop"] is not None:self.assertEqual(canonical(case["stop"]["incoming"]),canonical(pack(old)))
                    self.assertEqual(canonical(experiment.central_metrics(*level["cases"])),canonical(level["linear_central"]))
                    self.assertEqual(canonical(experiment.response_metrics(level["cases"])),canonical(level["linear_individual"]))
                    self.assertEqual(canonical(experiment.comparisons(level["cases"])),canonical(level["quadratic"]))
                    for plus,minus in zip(*[c["steps"] for c in level["cases"]]):
                        for name in ("node","memory"):
                            even=np.array(plus["quadratic_even_"+name+"_prediction_v"])
                            np.testing.assert_array_equal(even,minus["quadratic_even_"+name+"_prediction_v"])
                            p=np.array(plus["quadratic_"+name+"_prediction_v"]);m=np.array(minus["quadratic_"+name+"_prediction_v"])
                            np.testing.assert_allclose((p+m)/2,even,rtol=1e-11,atol=1e-18)
                    levels+=1
        self.assertEqual(levels,72)
        self.assertEqual(count,sum(len(c["steps"]) for w in self.report["windows"] for e in w["experiments"] for l in e["levels"] for c in l["cases"]))

    def test_96_fresh_replays_and_failed_budget_preserve_memory(self):
        count=0
        for w,base in zip(self.report["windows"],self.source):
            for e in w["experiments"]:
                for case in e["levels"][0]["cases"]:
                    for i in sorted({0,len(case["steps"])-1}):
                        if i<0:continue
                        old=unpack(self.network,case["initial"] if i==0 else case["steps"][i-1]["history"])
                        row=case["steps"][i];snapshot=state_hash(old)
                        new,d=self.network.advance(old,10.,row["diagnostics"]["actual_dt_s"])
                        self.assertEqual(canonical(pack(new)),canonical(row["history"]))
                        self.assertEqual(canonical(d),canonical(row["diagnostics"]));self.assertEqual(snapshot,state_hash(old));count+=1
            old=unpack(self.network,w["initial"]);snapshot=state_hash(old)
            with self.assertRaises(ValueError):self.network.advance(old,10.,base["reference"][0]["diagnostics"]["actual_dt_s"],iterations=0)
            self.assertEqual(snapshot,state_hash(old))
        self.assertEqual(count,96)

    def test_storage_sha_individual_and_even_counts_and_unpromoted_scope(self):
        r=self.report;raw=experiment.OUTPUT.read_bytes();summary=json.loads(experiment.SUMMARY.read_text())
        s=summary["storage"];self.assertEqual(len(raw),s["bytes"]);self.assertEqual(hashlib.sha256(raw).hexdigest(),s["compressed_sha256"])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(hashlib.sha256(canonical(r)).hexdigest(),s["canonical_json_sha256"])
        for name,sha in r["source_sha256"].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha,name)
        self.assertEqual(r["absolute_response_gate_v"],1e-8);self.assertEqual(r["relative_response_gate"],1e-3)
        self.assertEqual(r["new_coefficient_solves"],0);self.assertEqual(r["history_reset_count"],0)
        self.assertTrue(r["reserved_amplitudes_preserved"]);self.assertTrue(r["diagnostic_only"])
        for key in ("coefficients_fitted_to_responses","initial_memory_injections_are_accepted_states","local_adaptive_error_gate_applied",
            "previous_failures_modified","global_nonlinear_remainder_bound_admitted","temporal_error_bound_admitted",
            "physical_switching_admitted","audio_admitted","deadline_admitted"):self.assertFalse(r[key])
        for w,small in zip(r["windows"],summary["windows"]):
            self.assertEqual(small["nonlinear_cases"],36)
            self.assertEqual(small["linear_individual_passes"],sum(l["linear_individual"]["passed"] for e in w["experiments"] for l in e["levels"]))
            self.assertEqual(small["quadratic_individual_passes"],sum(l["quadratic"]["individual_passed"] for e in w["experiments"] for l in e["levels"]))
            self.assertEqual(small["quadratic_even_passes"],sum(l["quadratic"]["even_passed"] for e in w["experiments"] for l in e["levels"]))


if __name__=="__main__":unittest.main()
