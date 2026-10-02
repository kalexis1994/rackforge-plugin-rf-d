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
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_bdf_memory_transfer import stamps,transfer,propagate,memory_difference,node_difference,perturb_history
from loudness_latch_bdf_memory_windows import OUTPUT,SUMMARY,SOURCE,WINDOWS,STEP_COUNT,AMPLITUDES,central_metrics
from loudness_latch_bdf_fd_transfer_audit import OUTPUT as FD,SUMMARY as FD_SUMMARY
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_rational_solve import solve as rational_solve


class MemoryWindows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.fd=json.loads(gzip.decompress(FD.read_bytes()))
        cls.summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.fd_summary=json.loads(FD_SUMMARY.read_text(encoding="utf-8"))
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_declared_anchors_and_fixed_reference_clocks_replay_source(self):
        source=json.loads(gzip.decompress(SOURCE.read_bytes()))["case"]
        self.assertEqual(self.report["step_count"],16);self.assertEqual(self.report["C2_kick_v"],1e-6)
        self.assertEqual(self.report["amplitudes"],list(AMPLITUDES))
        for w,(name,limit) in zip(self.report["windows"],WINDOWS):
            index=max(k for k,r in enumerate(source["accepted"]) if r["steps"][-1]["history"]["time_s"]<=limit)
            self.assertEqual(w["name"],name);self.assertEqual(w["E4G8_accepted_anchor_index"],index)
            self.assertEqual(w["initial"],source["accepted"][index]["steps"][-1]["history"])
            self.assertFalse(w["initial_memory_injections_are_accepted_states"])
            self.assertEqual(len(w["reference"]),STEP_COUNT)
            for saved,row in zip(w["reference"],source["accepted"][index+1:index+1+STEP_COUNT]):
                self.assertEqual(saved["history"],row["steps"][0]["history"])
                self.assertEqual(saved["diagnostics"],row["steps"][0]["diagnostics"])
                self.assertEqual(saved["publication"],row["steps"][0]["publication"])

    def test_all_hypothetical_paths_and_published_charge_lineage(self):
        n=self.network;count=0
        for w in self.report["windows"]:
            base=[unpack(n,s["history"]) for s in w["reference"]]
            anchor=unpack(n,w["initial"])
            operators=[dict(op,node_map=np.array(op["node_map"]),memory_map=np.array(op["memory_map"])) for op in w["operators"]]
            for e in w["experiments"]:
                current=np.array(e["current_direction_v"]);previous=np.array(e["previous_direction_v"])
                for level in e["levels"]:
                    for c in level["cases"]:
                        amplitude=c["amplitude"];sign=c["sign"]
                        old=unpack(n,c["initial"])
                        self.assertEqual(canonical(pack(perturb_history(n,anchor,sign*amplitude*current,sign*amplitude*previous))),canonical(c["initial"]))
                        self.assertTrue(c["hypothetical_initial_memory"]);self.assertFalse(c["published"])
                        self.assertFalse(c["local_adaptive_error_gate_applied"])
                        self.assertTrue(c["complete"]);self.assertIsNone(c["stop"])
                        self.assertEqual(old.current.joint.node_v,anchor.current.joint.node_v)
                        pc=sign*amplitude*current;pp=sign*amplitude*previous
                        for s,reference,op in zip(c["steps"],base,operators):
                            new=unpack(n,s["history"]);d=s["diagnostics"];h=d["actual_dt_s"]
                            self.assertEqual(s["previous_history_sha256"],state_hash(old))
                            self.assertEqual(new.previous,old.current);self.assertEqual(new.time_s,reference.time_s)
                            self.assertGreaterEqual(h,1e-12);self.assertLessEqual(h/old.previous_dt_s,2.)
                            check=publication_check(n,old,new,h,d)
                            self.assertEqual(check,s["publication"])
                            self.assertLess(check["max_published_kcl_a"],1e-11)
                            self.assertLess(check["max_branch_equation_error_v"],1e-14);self.assertTrue(check["round_trip_exact"])
                            np.testing.assert_array_equal(node_difference(new.current,reference.current),s["node_difference_v"])
                            np.testing.assert_array_equal(memory_difference(new.current,reference.current),s["memory_difference_v"])
                            pn,pm=propagate(op,pc,pp)
                            np.testing.assert_array_equal(pn,s["predicted_node_difference_v"])
                            np.testing.assert_array_equal(pm,s["predicted_memory_difference_v"])
                            pp,pc=pc,pm;old=new;count+=1
                        self.assertEqual(canonical(pack(old)),canonical(c["final"]))
        self.assertEqual(count,1024)

    def test_every_mixed_map_obeys_real_stamps_and_both_backward_gates(self):
        n=self.network
        for w in self.report["windows"]:
            old=unpack(n,w["initial"])
            for s,op in zip(w["reference"],w["operators"]):
                new=unpack(n,s["history"]);d=s["diagnostics"]
                virtual,c=n.effective_history(old,d["actual_dt_s"])
                self.assertEqual(c,op["coefficients"])
                _,j=n.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(np.array(d["increment_v"]))
                b,p,direct=stamps(n,new,c["effective_dt_s"]);x=np.array(op["node_map"])
                _,errors=backward_errors(j,b,x)
                self.assertLess(max(errors.values()),1e-10)
                self.assertEqual(errors["binary_componentwise_backward_error"],op["linear_solve"]["binary_componentwise_backward_error"])
                np.testing.assert_array_equal(p@x+direct,op["memory_map"])
                # C10's memory, including its direct series term, is retained.
                beta=c["effective_dt_s"]/(c["effective_dt_s"]+.255)
                self.assertAlmostEqual(direct[17,17],1-beta,places=15)
                old=new

    def test_all_central_and_half_amplitude_comparisons_keep_declared_gates(self):
        r=self.report
        self.assertEqual(r["absolute_node_linearization_gate_v"],1e-8)
        self.assertEqual(r["relative_node_linearization_gate"],1e-3)
        count=0
        for w in r["windows"]:
            for e in w["experiments"]:
                for level in e["levels"]:
                    self.assertEqual(central_metrics(*level["cases"]),level["central_comparison"])
                    self.assertTrue(level["central_comparison"]["passed"]);count+=1
                full,half=[max(row["maximum_node_response_v"] for row in level["central_comparison"]["rows"]) for level in e["levels"]]
                self.assertLess(abs(half-full/2),1e-8+1e-3*abs(full/2))
        self.assertEqual(count,32)

    def test_selected_maps_and_nonlinear_windows_replay_without_history_edits(self):
        n=self.network
        for w in self.report["windows"]:
            old=unpack(n,w["initial"])
            for k in (0,len(w["reference"])-1):
                previous=old if k==0 else unpack(n,w["reference"][k-1]["history"])
                s=w["reference"][k];new=unpack(n,s["history"])
                op=transfer(n,previous,new,s["diagnostics"])
                np.testing.assert_array_equal(op["node_map"],w["operators"][k]["node_map"])
            case=w["experiments"][0]["levels"][1]["cases"][0]
            old=unpack(n,case["initial"])
            for s in case["steps"]:
                snapshot=state_hash(old);new,d=n.advance(old,10.,s["diagnostics"]["actual_dt_s"])
                self.assertEqual(state_hash(old),snapshot)
                self.assertEqual(new,unpack(n,s["history"]));self.assertEqual(d,s["diagnostics"]);old=new

    def test_exact_fd_audit_uses_unchanged_jacobian_and_retains_reset_failure(self):
        n=self.network
        for row,w in zip(self.fd["rows"],self.report["windows"]):
            old=unpack(n,row["old"]);s=row["reference_step"];new=unpack(n,s["history"])
            virtual,c=n.effective_history(old,s["diagnostics"]["actual_dt_s"])
            _,j=n.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(np.array(s["diagnostics"]["increment_v"]),use_fd=True)
            b,_,_=stamps(n,new,c["effective_dt_s"])
            np.testing.assert_array_equal(j,row["fd_jacobian_s"]);np.testing.assert_array_equal(b,row["memory_rhs_s"])
            exact,audit=rational_solve(j,b)
            np.testing.assert_array_equal(exact,row["node_map"]);self.assertEqual(audit,row["exact_solve"])
            _,errors=backward_errors(j,b,exact);self.assertEqual(errors,row["backward_errors"])
            self.assertLess(max(errors.values()),1e-10)
            mixed=np.array(w["operators"][0]["node_map"])
            difference=float(np.max(np.abs(mixed-exact)/(1+np.abs(mixed))))
            self.assertEqual(difference,row["node_map_max_scaled_difference"])
            self.assertEqual(row["passed"],difference<1e-8)
        reset=next(r for r in self.fd["rows"] if r["window"]=="reset")
        self.assertFalse(reset["passed"])
        self.assertTrue(self.fd["original_fd_failures_retained"])
        self.assertEqual(sum(r["passed"] for r in self.fd["rows"]),3)

    def test_canonical_storage_sources_failed_attempt_and_scope(self):
        for path,payload,summary in ((OUTPUT,self.report,self.summary),(FD,self.fd,self.fd_summary)):
            raw=gzip.decompress(path.read_bytes());storage=summary["storage"]
            self.assertEqual(canonical(payload),raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),storage["canonical_json_sha256"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),storage["compressed_sha256"])
            for name,h in payload["source_sha256"].items():
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),h)
            for key in ("previous_reports_modified","trajectory_retimed","temporal_error_bound_admitted","temporal_refinement_admitted","physical_switching_admitted","audio_admitted"):
                if key in payload:self.assertFalse(payload[key])
        failed=json.loads(gzip.decompress((ROOT/"evidence/loudness_latch_bdf_memory_windows_attempt1.json.gz").read_bytes()))
        for name,text in failed["producer_sources_utf8"].items():
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),failed["source_sha256"][name])
        self.assertGreater(failed["failed_operator"]["max_componentwise_backward_error"],failed["backward_gate"])


if __name__=="__main__":unittest.main()
