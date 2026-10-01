import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_survey import state_hash,trace,comparison
from loudness_latch_bdf_doubling_survey import OUTPUTS,canonical,case_summary
from loudness_latch_bdf_growth_dc import OUTPUT,SUMMARY,NAME,POLICY,GROWTH_ERROR_THRESHOLD,END_S
from loudness_latch_bdf_doubling import trial
from loudness_latch_bdf_time import trial as startup_trial
from loudness_latch_time_reference import frozen_rate


class GrowthDC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.case=cls.payload["case"]
        cls.summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_same_dc_and_policy_only_growth_threshold_changes(self):
        c=self.case
        self.assertEqual(c["name"],NAME);self.assertEqual(c["policy"],vars(POLICY))
        self.assertEqual(c["growth_error_threshold"],.125)
        reference=json.loads(gzip.decompress(OUTPUTS[1].read_bytes()))["case"]
        self.assertEqual(c["initial"],reference["initial"])
        self.assertEqual(c["dc_diagnostics"],reference["dc_diagnostics"])
        self.assertEqual(c["policy"],reference["policy"])
        self.assertEqual(c["initial"]["time_s"],0.);self.assertIsNone(c["initial"]["previous"])
        startup=[r for r in c["accepted"] if r["diagnostics"]["startup"]]
        self.assertEqual(len(startup),1);self.assertIs(startup[0],c["accepted"][0])
        self.assertEqual(startup[0],reference["accepted"][0])
        self.assertEqual(len(startup[0]["steps"]),2)
        self.assertEqual(startup[0]["steps"][0]["diagnostics"]["method"],"backward-euler-startup")
        self.assertEqual(c["complete"],c["final_time_s"]==END_S)
        self.assertTrue(c["complete"]);self.assertIsNone(c["stop"])
        self.assertEqual(c["attempts"],len(c["accepted"])+len(c["rejected"]))
        self.assertLessEqual(c["attempts"],POLICY.maximum_attempts)
        self.assertEqual(c["history_reset_count"],0);self.assertIsNone(c["selected_alternative"])

    def verify_interval(self,old,s):
        new=unpack(self.network,s["history"]);d=s["diagnostics"];h=d["actual_dt_s"]
        self.assertGreaterEqual(h,POLICY.minimum_step_s)
        self.assertEqual(new.time_s,old.time_s+h)
        self.assertEqual(new.previous,old.current);self.assertEqual(new.previous_dt_s,h)
        if old.previous is not None:
            self.assertEqual(d["method"],"variable-bdf2-charge/v1")
            self.assertLessEqual(h/old.previous_dt_s,2.)
        check=publication_check(self.network,old,new,h,d)
        self.assertEqual(check,s["publication"]);self.assertTrue(check["round_trip_exact"])
        self.assertLess(check["max_published_kcl_a"],1e-11)
        self.assertLess(check["max_branch_equation_error_v"],1e-14)
        return new

    def test_all_main_shadow_and_rejected_half_intervals_conserve_real_charge(self):
        c=self.case;n=self.network;old=unpack(n,c["initial"])
        histories={old.time_s:c["initial"]}
        for row in c["accepted"]:
            self.assertEqual(row["start_s"],old.time_s)
            self.assertEqual(row["previous_history_sha256"],state_hash(old))
            anchor=old
            for s in row["steps"]:old=self.verify_interval(old,s)
            histories[old.time_s]=row["steps"][-1]["history"]
            d=row["diagnostics"]
            if not d["startup"]:
                self.assertEqual(len(row["steps"]),1)
                self.assertEqual(d["published_candidate"],"full-step")
                self.assertFalse(d["richardson_factor_applied"])
                self.assertEqual(d["full_publication"],row["steps"][0]["publication"])
                shadow=anchor
                self.assertEqual(len(d["shadow_half_steps"]),2)
                for s in d["shadow_half_steps"]:
                    self.assertFalse(s["published"]);shadow=self.verify_interval(shadow,s)
                self.assertEqual(shadow.time_s,old.time_s)
        self.assertEqual(canonical(pack(old)),canonical(c["final"]))
        for row in c["rejected"]:
            old=unpack(n,histories[row["time_s"]]);shadow=old
            self.assertEqual(state_hash(old),row["previous_history_sha256"])
            for s in row["diagnostics"].get("shadow_half_steps",[]):
                self.assertFalse(s["published"]);shadow=self.verify_interval(shadow,s)
            self.assertEqual(state_hash(old),row["previous_history_sha256"])

    def test_all_growth_proposals_and_halvings_follow_declared_protocol(self):
        c=self.case;h=POLICY.maximum_step_s;old=unpack(self.network,c["initial"])
        rejects={}
        for r in c["rejected"]:rejects.setdefault(r["time_s"],[]).append(r)
        for row in c["accepted"]:
            proposed=min(h,END_S-old.time_s)
            if old.previous is not None:proposed=min(proposed,2*old.previous_dt_s)
            for r in rejects.pop(old.time_s,[]):
                self.assertEqual(r["dt_s"],proposed)
                self.assertEqual(r["previous_history_sha256"],state_hash(old))
                proposed/=2
            self.assertEqual(row["dt_s"],proposed)
            d=row["diagnostics"]
            self.assertLessEqual(max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"]),1.)
            self.assertLessEqual(d["junction_increment_v"],POLICY.junction_increment_v)
            self.assertLessEqual(d["positive_mode_step_product"],POLICY.positive_mode_step_product)
            self.assertEqual(len(d["frozen_positive_rates_per_s"]),3 if d["startup"] else 4)
            old=unpack(self.network,row["steps"][-1]["history"]);h=proposed
            if (max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"])<GROWTH_ERROR_THRESHOLD
                    and d["junction_increment_v"]<POLICY.junction_increment_v/2
                    and d["positive_mode_step_product"]<POLICY.positive_mode_step_product/2):
                h=min(2*h,POLICY.maximum_step_s,2*old.previous_dt_s)
        self.assertEqual(rejects,{})

    def test_selected_accepted_and_rejected_trials_replay_exactly(self):
        c=self.case;n=self.network;rows=c["accepted"]
        states={c["initial"]["time_s"]:c["initial"]}
        states.update({r["steps"][-1]["history"]["time_s"]:r["steps"][-1]["history"] for r in rows})
        selected=[rows[k] for k in {0,1,len(rows)//2,len(rows)-1,min(range(len(rows)),key=lambda k:rows[k]["dt_s"])}]
        rejects=c["rejected"]
        selected.extend(rejects[k] for k in {0,len(rejects)//2,len(rejects)-1} if rejects)
        for r in selected:
            time=r.get("start_s",r.get("time_s"));old=unpack(n,states[time]);snapshot=state_hash(old)
            rate=frozen_rate(n.network,old.current,old.key_v)
            result,d,_=(startup_trial if old.previous is None else trial)(n,old,10.,r["dt_s"],POLICY,rate)
            self.assertEqual(state_hash(old),snapshot)
            self.assertEqual(canonical(dict(d,startup=old.previous is None)),canonical(r["diagnostics"]))
            if "steps" in r:
                self.assertIsNotNone(result)
                self.assertEqual(canonical([dict(history=pack(v),diagnostics=diag) for v,diag in result]),
                                 canonical([{k:v for k,v in s.items() if k!="publication"} for s in r["steps"]]))
            else:self.assertIsNone(result)

    def test_fixed_tolerance_comparisons_do_not_promote_refinement(self):
        s=self.summary;c=self.case
        for path,stored in zip(OUTPUTS,s["comparisons"]):
            reference=json.loads(gzip.decompress(path.read_bytes()))["case"]
            actual=comparison(trace(reference),trace(c),reference["complete"] and c["complete"])
            self.assertEqual(actual,{k:v for k,v in stored.items() if k not in ("reference","diagnostic_only")})
            self.assertTrue(stored["diagnostic_only"])
        self.assertEqual(s["maximum_difference_gate_v"],1e-3)
        for key in ("previous_reports_modified","trajectory_retimed","independent_spatial_oracle",
                    "temporal_refinement_admitted","temporal_error_bound_admitted","physical_charge_identified",
                    "physical_switching_admitted","audio_admitted"):
            self.assertFalse(s[key])
        self.assertTrue(s["diagnostic_only"]);self.assertIsNone(s["selected"])

    def test_storage_summary_and_unchanged_inputs(self):
        p=self.payload;s=self.summary;raw=gzip.decompress(OUTPUT.read_bytes());saved=s["case"]
        self.assertEqual(canonical(p),raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),saved["storage"]["canonical_json_sha256"])
        self.assertEqual(hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),saved["storage"]["compressed_sha256"])
        self.assertEqual(case_summary(self.case),{k:v for k,v in saved.items()
            if k not in ("storage","attempts","growth_error_threshold","offline_integration_wall_s")})
        self.assertEqual(p["source_sha256"],s["source_sha256"])
        for source,h in p["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),h)


if __name__=="__main__":unittest.main()
