from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_latch_bdf_static_precision_windows import OUTPUT,SUMMARY,WINDOWS,candidate
from loudness_latch_bdf_static_precision import dynamic,derivative_metrics,floats
from circuit66_decimal_static import evaluate as decimal_evaluate
from circuit66_static_binary import prepare,evaluate,MODES
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_memory_transfer import stamps
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_fd_sensitivity import map_metrics
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_rational_solve import solve
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters


class StaticWindows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.source=json.loads(gzip.decompress(WINDOWS.read_bytes()))
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_sixty_four_candidates_history_chain_and_independent_derivatives(self):
        count=0
        for window,base in zip(self.report["windows"],self.source["windows"]):
            self.assertEqual(window["name"],base["name"])
            self.assertEqual(canonical(window["initial"]),canonical(base["initial"]))
            old=unpack(self.network,window["initial"])
            self.assertEqual(len(window["rows"]),16)
            for row,step in zip(window["rows"],base["reference"]):
                count+=1
                self.assertEqual(state_hash(old),row["previous_history_sha256"])
                _,c,x=candidate(old,step,self.network)
                np.testing.assert_array_equal(x,row["node_candidate_v"])
                self.assertEqual(c,row["coefficients"])
                self.assertEqual(row["actual_dt_s"],step["diagnostics"]["actual_dt_s"])
                r,j=decimal_evaluate(self.report["graph"],x[:66],80)
                r100,j100=decimal_evaluate(self.report["graph"],x[:66],100)
                self.assertEqual([str(v) for v in r],row["decimal80_audio_residual_a"])
                self.assertEqual([[str(v) for v in line] for line in j],row["decimal80_audio_jacobian_s"])
                self.assertEqual(np.array_equal([float(v) for v in r],[float(v) for v in r100]),row["decimal80_100_rounded_residual_equal"])
                self.assertEqual(np.array_equal(floats(j),floats(j100)),row["decimal80_100_rounded_jacobian_equal"])
                original,_=self.network.network.joint.evaluator(10.)(x,False)
                ar=original[:66].copy();ar[32]+=x[self.network.network.joint.out]/68000
                discrepancy=float(np.max(abs(ar-np.array([float(v) for v in r]))))
                self.assertEqual(discrepancy,row["original_static_discrepancy_a"])
                self.assertEqual(discrepancy<1e-11,row["original_static_gate_passed"])
                for result,g in zip(row["binary"],self.report["prepared_graphs"]):
                    br,bj=evaluate(g,x[:66])
                    np.testing.assert_array_equal(br,result["audio_residual_a"])
                    np.testing.assert_array_equal(bj,result["audio_jacobian_s"])
                    self.assertEqual(derivative_metrics(j,[[Decimal.from_float(float(v)) for v in line] for line in bj]),result["derivative_comparison"])
                old=unpack(self.network,step["history"])
        self.assertEqual(count,64)

    def test_all_256_combined_matrices_and_map_gates(self):
        count=0
        for w,base in zip(self.report["windows"],self.source["windows"]):
            old=unpack(self.network,w["initial"])
            for row,step,operator in zip(w["rows"],base["reference"],base["operators"]):
                new=unpack(self.network,step["history"]);virtual,c,x=candidate(old,step,self.network)
                _,sj=self.network.network.joint.evaluator(10.)(x)
                dyn=dynamic(self.network,virtual,x,c["effective_dt_s"])
                b,_,_=stamps(self.network,new,c["effective_dt_s"])
                np.testing.assert_array_equal(b,row["memory_rhs_s"])
                j80=floats([[Decimal(v) for v in line] for line in row["decimal80_audio_jacobian_s"]])
                _,j100=decimal_evaluate(self.report["graph"],x[:66],100)
                matrices=[j80,floats(j100)]+[np.array(v["audio_jacobian_s"]) for v in row["binary"]]
                solves=[row["analytic"],row["decimal100"]]+[v["solve"] for v in row["binary"]]
                for audio,s in zip(matrices,solves):
                    count+=1;combined=sj.copy();combined[:66,:66]=audio;combined+=dyn
                    np.testing.assert_array_equal(combined,s["jacobian_s"])
                    self.assertTrue(s["passed"])
                    _,errors=backward_errors(combined,b,np.array(s["node_map"]))
                    self.assertEqual(errors,s["backward_errors"])
                    self.assertLess(max(errors.values()),1e-10)
                ax=np.array(row["analytic"]["node_map"])
                self.assertEqual(map_metrics(ax,np.array(operator["node_map"])),row["original_mixed_map"])
                self.assertEqual(map_metrics(ax,np.array(row["decimal100"]["node_map"])),row["decimal80_100_map"])
                for result in row["binary"]:
                    metrics=map_metrics(ax,np.array(result["solve"]["node_map"]))
                    self.assertEqual(metrics,result["map_comparison"])
                    self.assertEqual(metrics["node_map_max_scaled_difference"]<1e-8,result["map_gate_passed"])
                old=new
        self.assertEqual(count,256)

    def test_eight_exact_rational_replays_and_prepared_graphs(self):
        for g,mode in zip(self.report["prepared_graphs"],MODES):
            self.assertEqual(canonical(prepare(self.report["graph"],mode)),canonical(g))
        count=0
        for w in self.report["windows"]:
            for row in (w["rows"][0],w["rows"][-1]):
                s=row["binary"][1]["solve"]
                x,audit=solve(np.array(s["jacobian_s"]),np.array(row["memory_rhs_s"]))
                np.testing.assert_array_equal(x,s["node_map"])
                self.assertEqual(audit,s["exact_solve"]);count+=1
        self.assertEqual(count,8)

    def test_canonical_sources_scope_and_prior_failure_preservation(self):
        raw=OUTPUT.read_bytes();storage=json.loads(SUMMARY.read_text(encoding="utf-8"))["storage"]
        self.assertEqual(len(raw),storage["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),storage["compressed_sha256"])
        self.assertEqual(gzip.decompress(raw),canonical(self.report))
        self.assertEqual(hashlib.sha256(canonical(self.report)).hexdigest(),storage["canonical_json_sha256"])
        for name,expected in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        self.assertEqual(self.report["intervals_per_window"],16)
        self.assertEqual(self.report["nonlinear_steps_new"],0)
        self.assertEqual(self.report["history_reset_count"],0)
        reset=next(w for w in self.report["windows"] if w["name"]=="reset")["rows"][0]
        self.assertFalse(reset["binary"][0]["map_gate_passed"])
        self.assertTrue(reset["binary"][1]["map_gate_passed"])
        self.assertTrue(self.report["diagnostic_only"])
        for key in ("original_solver_modified","trajectory_retimed","original_reset_fd_gate_closed",
                    "previous_reports_modified","independent_full_spatial_oracle","physical_switching_admitted",
                    "temporal_error_bound_admitted","temporal_refinement_admitted","audio_admitted","deadline_admitted"):
            self.assertFalse(self.report[key])


if __name__=="__main__":unittest.main()
