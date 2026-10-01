import copy
from fractions import Fraction as F
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_survey import state_hash,trace,comparison
from loudness_latch_bdf_doubling_survey import OUTPUTS,SUMMARY,NAMES,POLICIES,END_S,canonical,case_summary,STRICT
from loudness_latch_bdf_doubling import trial
from loudness_latch_bdf_time import trial as startup_trial
from loudness_latch_time_reference import frozen_rate
from loudness_latch_increment_time import error,nodes,junctions,differences


class DoublingSurvey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads(SUMMARY.read_text())
        cls.payloads=[json.loads(gzip.decompress(p.read_bytes())) for p in OUTPUTS]
        cls.cases=[r["case"] for r in cls.payloads]
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_growth_quarter_heuristic_can_reject_next_cubic_trial_with_published_memory(self):
        def advance(t,current,previous,k,h):
            r=h/k;a0=(1+2*r)/(1+r);a1=-(1+r);a2=r*r/(1+r)
            return (h*3*(t+h)**2-a1*current-a2*previous)/a0
        def doubling(t,current,previous,k,h):
            full=advance(t,current,previous,k,h)
            middle=advance(t,current,previous,k,h/2)
            fine=advance(t+h/2,middle,current,h/2,h/2)
            return full,full-fine
        # Exact incoming y=t^3 at 0,-1/2; publish the full candidate.
        full,first=doubling(F(0),F(0),F(-1,8),F(1,2),F(1))
        self.assertEqual(full,F(19,10));self.assertEqual(first,F(23,45))
        # Preserve that numerical current and previous=0, then double h.
        _,second=doubling(F(1),full,F(0),F(1),F(2))
        self.assertEqual(second,F(992,225))
        absolute_gate=5*first
        self.assertEqual(first/absolute_gate,F(1,5));self.assertLess(first/absolute_gate,F(1,4))
        self.assertEqual(second/absolute_gate,F(992,575));self.assertGreater(second/absolute_gate,1)

    def test_predeclared_policies_coverage_and_single_startup(self):
        self.assertEqual(self.cases[0]["initial"],self.cases[1]["initial"])
        for name,p,c in zip(NAMES,POLICIES,self.cases):
            self.assertEqual(c["name"],name);self.assertEqual(c["policy"],vars(p))
            self.assertEqual(c["complete"],c["final_time_s"]>=END_S)
            if c["complete"]:self.assertEqual(c["final_time_s"],END_S)
            self.assertLessEqual(c["attempts"],p.maximum_attempts)
            self.assertEqual(c["attempts"],len(c["accepted"])+len(c["rejected"]))
            self.assertEqual(c["published_intervals"],sum(len(a["steps"]) for a in c["accepted"]))
            startup=[a for a in c["accepted"] if a["diagnostics"]["startup"]]
            self.assertEqual(len(startup),1);self.assertIs(startup[0],c["accepted"][0])
            self.assertEqual(len(startup[0]["steps"]),2)
            self.assertEqual(startup[0]["steps"][0]["diagnostics"]["method"],"backward-euler-startup")
            self.assertEqual(c["history_reset_count"],0);self.assertIsNone(c["selected_alternative"])
            self.assertEqual(c["initial"]["time_s"],0.);self.assertIsNone(c["initial"]["previous"])

    def test_every_main_and_shadow_interval_closes_real_charge_with_atomic_lineage(self):
        n=self.network
        for p,c in zip(POLICIES,self.cases):
            old=unpack(n,c["initial"])
            for row in c["accepted"]:
                self.assertEqual(row["start_s"],old.time_s)
                self.assertEqual(row["previous_history_sha256"],state_hash(old))
                incoming=old
                for s in row["steps"]:
                    old=self.verify_interval(incoming,s,p);incoming=old
                d=row["diagnostics"]
                if not d["startup"]:
                    self.assertEqual(len(row["steps"]),1)
                    self.assertEqual(d["published_candidate"],"full-step")
                    self.assertFalse(d["richardson_factor_applied"])
                    anchor=unpack(n,c["initial"] if row is c["accepted"][0] else previous_pack)
                    shadow=anchor
                    for s in d["shadow_half_steps"]:
                        self.assertFalse(s["published"])
                        shadow=self.verify_interval(shadow,s,p)
                    self.assertEqual(shadow.time_s,old.time_s)
                    self.assertEqual(d["full_publication"],row["steps"][0]["publication"])
                    self.assertEqual(old.previous,anchor.current)
                previous_pack=row["steps"][-1]["history"]
            self.assertEqual(canonical(pack(old)),canonical(c["final"]))

    def verify_interval(self,old,s,p):
        n=self.network;new=unpack(n,s["history"]);d=s["diagnostics"];h=d["actual_dt_s"]
        self.assertGreaterEqual(h,p.minimum_step_s)
        self.assertEqual(new.previous,old.current);self.assertEqual(new.previous_dt_s,h)
        self.assertEqual(new.time_s,old.time_s+h)
        check=publication_check(n,old,new,h,d)
        self.assertEqual(check,s["publication"])
        self.assertTrue(check["round_trip_exact"])
        self.assertLess(check["max_published_kcl_a"],1e-11)
        self.assertLess(check["max_branch_equation_error_v"],1e-14)
        if old.previous is not None:
            self.assertEqual(d["method"],"variable-bdf2-charge/v1")
            virtual,coeff=n.effective_history(old,h)
            self.assertLessEqual(coeff["ratio"],2.)
            delta=np.array(d["increment_v"])
            self.assertEqual(n.network.publish(delta,10.,virtual,coeff["effective_dt_s"]),new.current)
        return new

    def test_local_decisions_and_rejections_keep_incoming_memory(self):
        n=self.network
        for p,c in zip(POLICIES,self.cases):
            states={c["initial"]["time_s"]:state_hash(unpack(n,c["initial"]))}
            histories={c["initial"]["time_s"]:c["initial"]}
            previous=unpack(n,c["initial"])
            for row in c["accepted"]:
                d=row["diagnostics"];new=unpack(n,row["steps"][-1]["history"])
                self.assertLessEqual(max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"]),1.)
                self.assertLessEqual(d["junction_increment_v"],p.junction_increment_v)
                self.assertLessEqual(d["positive_mode_step_product"],p.positive_mode_step_product)
                if not d["startup"]:
                    fine=unpack(n,d["shadow_half_steps"][-1]["history"])
                    self.assertEqual(error(nodes(new.current),nodes(fine.current),p.voltage_abs_v,p.voltage_relative),d["voltage_error_ratio"])
                    self.assertEqual(error(junctions(n.network,new.current),junctions(n.network,fine.current),p.junction_abs_v,p.junction_relative),d["junction_voltage_error_ratio"])
                    self.assertEqual(float(np.max(np.abs(differences(junctions(n.network,new.current),junctions(n.network,previous.current))))),d["junction_increment_v"])
                states[new.time_s]=state_hash(new);histories[new.time_s]=row["steps"][-1]["history"];previous=new
            for row in c["rejected"]:
                self.assertEqual(states[row["time_s"]],row["previous_history_sha256"])
                old=unpack(n,histories[row["time_s"]]);shadow=old
                for s in row["diagnostics"].get("shadow_half_steps",[]):
                    self.assertFalse(s["published"]);shadow=self.verify_interval(shadow,s,p)
                self.assertEqual(state_hash(old),row["previous_history_sha256"])
            rejects=c["rejected"]
            for k in {0,len(rejects)//2,len(rejects)-1}:
                row=rejects[k];old=unpack(n,histories[row["time_s"]]);snapshot=copy.deepcopy(old)
                rate=frozen_rate(n.network,old.current,old.key_v)
                result,diag,_=(startup_trial if old.previous is None else trial)(n,old,10.,row["dt_s"],p,rate)
                self.assertIsNone(result);self.assertEqual(old,snapshot)
                self.assertEqual(canonical(dict(diag,startup=old.previous is None)),canonical(row["diagnostics"]))

    def test_selected_trials_replay_startup_normal_and_smallest_without_reset(self):
        n=self.network
        for p,c in zip(POLICIES,self.cases):
            rows=c["accepted"]
            indices={0,1,len(rows)//2,len(rows)-1,min(range(len(rows)),key=lambda k:rows[k]["dt_s"])}
            for k in indices:
                row=rows[k];old=unpack(n,c["initial"] if k==0 else rows[k-1]["steps"][-1]["history"])
                snapshot=copy.deepcopy(old);rate=frozen_rate(n.network,old.current,old.key_v)
                result,d,_=(startup_trial if old.previous is None else trial)(n,old,10.,row["dt_s"],p,rate)
                self.assertEqual(old,snapshot);self.assertIsNotNone(result)
                for (candidate,diag),s in zip(result,row["steps"]):
                    self.assertEqual(candidate,unpack(n,s["history"]));self.assertEqual(diag,s["diagnostics"])
                for field in ("voltage_error_ratio","junction_voltage_error_ratio","junction_increment_v","positive_mode_step_product"):
                    self.assertAlmostEqual(d[field],row["diagnostics"][field],places=12)

    def test_global_comparisons_keep_original_gate_and_scope(self):
        s=self.summary;complete=all(c["complete"] for c in self.cases)
        self.assertEqual(comparison(*(trace(c) for c in self.cases),complete),s["refinement"])
        strict=json.loads(gzip.decompress(STRICT.read_bytes()))["case"]
        self.assertEqual([comparison(trace(c),trace(strict),c["complete"] and strict["complete"]) for c in self.cases],s["C3_cross_comparisons"])
        self.assertEqual(s["maximum_difference_gate_v"],1e-3)
        self.assertEqual(s["temporal_refinement_admitted"],s["refinement"]["passed"])
        for key in ("previous_reports_modified","trajectory_retimed","independent_spatial_oracle",
                    "temporal_error_bound_admitted","physical_switching_admitted","physical_charge_identified","audio_admitted"):
            self.assertFalse(s[key])

    def test_lossless_storage_source_binding_and_summary(self):
        for path,payload,summary in zip(OUTPUTS,self.payloads,self.summary["cases"]):
            raw=gzip.decompress(path.read_bytes());storage=summary["storage"]
            self.assertEqual(canonical(payload),raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),storage["canonical_json_sha256"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),storage["compressed_sha256"])
            self.assertEqual(case_summary(payload["case"]),{k:v for k,v in summary.items() if k!="storage"})
            self.assertEqual(payload["source_sha256"],self.summary["source_sha256"])
            for source,h in payload["source_sha256"].items():
                self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),h)


if __name__=="__main__":unittest.main()
