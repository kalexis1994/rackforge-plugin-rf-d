from decimal import Decimal as D,localcontext
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from circuit66_decimal_static import evaluate,graph,lift
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack,publication_check
from loudness_latch_bdf_memory_transfer import perturb_history,node_difference
from loudness_latch_bdf_static_precision import OUTPUT,SUMMARY,WINDOWS,OLD_FD,floats,decimal_fd,derivative_metrics
from loudness_latch_bdf_fd_sensitivity import map_metrics
from loudness_latch_bdf_rational_solve import solve
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_doubling_survey import canonical


class StaticPrecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.old=json.loads(gzip.decompress(WINDOWS.read_bytes()))
        cls.fd_old=json.loads(gzip.decompress(OLD_FD.read_bytes()))
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_bjt_terminal_conservation_polarity_and_decimal_derivative(self):
        q=dict(ref="Q",base=0,collector=1,emitter=2,polarity=1,is_a=1e-14,vt=.0257,
               beta_forward=100,beta_reverse=5)
        g=dict(node_count=3,fixed={},resistors=[],conductances=[],bjts=[q],diodes=[])
        x=[.72,.1,0.]
        r,j=evaluate(g,x)
        with localcontext() as ctx:
            ctx.prec=80
            self.assertLess(abs(sum(r,D(0))),D("1e-70"))
            for col in range(3):self.assertLess(abs(sum((row[col] for row in j),D(0))),D("1e-70"))
        rf,jf=evaluate(g|dict(bjts=[q|dict(polarity=-1)]),[-v for v in x])
        self.assertEqual(rf,[v.copy_negate() for v in r])
        self.assertEqual(j,jf)
        self.assertTrue(derivative_metrics(j,decimal_fd(g,x,1e-7))["passed"])
        with self.assertRaisesRegex(ValueError,"complete nodes"):evaluate(g,x[:2])
        with self.assertRaisesRegex(ValueError,"exponential domain"):evaluate(g,[2.,0.,0.])

    def test_four_independent_static_transcriptions_and_precision_replay(self):
        self.assertEqual(canonical(graph(self.network.network.joint.values)),canonical(self.report["graph"]))
        for case,old in zip(self.report["cases"],self.old["windows"]):
            self.assertEqual(case["window"],old["name"])
            self.assertEqual(canonical(case["initial"]),canonical(old["initial"]))
            self.assertEqual(canonical(case["reference_step"]),canonical(old["reference"][0]))
            x=case["node_candidate_v"]
            r,j=evaluate(self.report["graph"],x[:66]);r100,j100=evaluate(self.report["graph"],x[:66],100)
            self.assertEqual([str(v) for v in r],case["decimal80_audio_static_residual_a"])
            self.assertEqual([[str(v) for v in row] for row in j],case["decimal80_audio_static_jacobian_s"])
            raw,_=self.network.network.joint.dc(x[:66]);out=np.array([-v if i<48 else v for i,v in enumerate(raw)])
            self.assertLess(float(np.max(abs(out-np.array([float(v) for v in r])))),1e-11)
            self.assertTrue(case["static_residual_gate_passed"])
            self.assertEqual(case["decimal80_100_rounded_residual_equal"],np.array_equal([float(v) for v in r],[float(v) for v in r100]))
            self.assertEqual(case["decimal80_100_rounded_jacobian_equal"],np.array_equal(floats(j),floats(j100)))

    def test_all_twenty_eight_maps_and_decimal_fd_gates(self):
        count=0
        for case,old,old_fd in zip(self.report["cases"],self.old["windows"],self.fd_old["cases"]):
            b=np.array(case["memory_rhs_s"]);ax=np.array(case["analytic"]["node_map"])
            analytic=[[D(v) for v in row] for row in case["decimal80_audio_static_jacobian_s"]]
            np.testing.assert_array_equal(case["decimal100"]["node_map"],ax)
            self.assertEqual(case["decimal80_100_map"],map_metrics(ax,np.array(case["decimal100"]["node_map"])))
            self.assertEqual(case["original_mixed_map"],map_metrics(ax,np.array(old["operators"][0]["node_map"])))
            original=next(r for r in old_fd["rows"] if r["step_v"]==1e-6 and r["mode"]=="full-residual-FD")
            self.assertEqual(case["original_full_fd_map"],map_metrics(ax,np.array(original["node_map"])))
            for row in [case["analytic"],case["decimal100"],*case["fd"]]:
                count+=1;self.assertTrue(row["passed"]);self.assertNotIn("error",row)
                j=np.array(row["jacobian_s"]);x=np.array(row["node_map"])
                _,errors=backward_errors(j,b,x)
                self.assertEqual(errors,row["backward_errors"]);self.assertLess(max(errors.values()),1e-10)
                self.assertTrue(row["exact_solve"]["exact_rational_residual_zero"])
                if "step_v" in row:
                    fd=[[D(v) for v in r] for r in row["decimal80_audio_fd_jacobian_s"]]
                    self.assertEqual(derivative_metrics(analytic,fd),row["derivative_comparison"])
                    metrics=map_metrics(ax,x);self.assertEqual(metrics,row["map_comparison"])
                    self.assertEqual(row["map_gate_passed"],metrics["node_map_max_scaled_difference"]<1e-8)
                if "step_v" not in row or row["step_v"]==1e-6:
                    exact,audit=solve(j,b);np.testing.assert_array_equal(exact,x);self.assertEqual(audit,row["exact_solve"])
            jf=decimal_fd(self.report["graph"],case["node_candidate_v"][:66],1e-6)
            row=next(r for r in case["fd"] if r["step_v"]==1e-6)
            self.assertEqual([[str(v) for v in r] for r in jf],row["decimal80_audio_fd_jacobian_s"])
        self.assertEqual(count,28)

    def test_forty_eight_hypothetical_publications_and_selected_nonlinear_replay(self):
        count=0
        for case,old in zip(self.report["cases"],self.old["windows"]):
            history=unpack(self.network,case["initial"]);base=unpack(self.network,case["reference_step"]["history"])
            gamma=old["operators"][0]["coefficients"]["gamma"]
            self.assertEqual([(d["memory"],d["amplitude_v"]) for d in case["directions"]],
                [(i,a) for i in (7,10,18) for a in (1e-6,.5e-6)])
            for direction in case["directions"]:
                kick=np.zeros(25);kick[direction["memory"]]=direction["amplitude_v"]
                actual=[]
                for sample in direction["cases"]:
                    count+=1;self.assertTrue(sample["complete"]);self.assertFalse(sample["published"])
                    injected=perturb_history(self.network,history,sample["sign"]*kick,np.zeros(25))
                    self.assertEqual(injected,unpack(self.network,sample["initial"]))
                    new=unpack(self.network,sample["history"]);h=case["reference_step"]["diagnostics"]["actual_dt_s"]
                    check=publication_check(self.network,injected,new,h,sample["diagnostics"])
                    self.assertEqual(canonical(check),canonical(sample["publication"]))
                    self.assertLess(check["max_published_kcl_a"],1e-11)
                    self.assertLess(check["max_branch_equation_error_v"],1e-14)
                    np.testing.assert_array_equal(node_difference(new.current,base.current),sample["node_difference_v"])
                    actual.append(np.array(sample["node_difference_v"]))
                    if direction["memory"]==10 and sample["sign"]==1:
                        replay,diag=self.network.advance(injected,10.,h)
                        self.assertEqual(replay,new);self.assertEqual(canonical(diag),canonical(sample["diagnostics"]))
                central=(actual[0]-actual[1])/2
                for name,x in (("decimal-analytic",case["analytic"]["node_map"]),("original-mixed",old["operators"][0]["node_map"])):
                    predicted=np.array(x)@((1+gamma)*kick)
                    metric=float(np.max(abs(central-predicted)/(1e-8+1e-3*abs(predicted))))
                    observed=direction["comparisons"][name]
                    np.testing.assert_array_equal(observed["central_v"],central)
                    np.testing.assert_array_equal(observed["prediction_v"],predicted)
                    self.assertEqual(observed["maximum_scaled_error"],metric)
                    self.assertEqual(observed["passed"],metric<1)
        self.assertEqual(count,48)

    def test_storage_frozen_sources_and_scope(self):
        raw=OUTPUT.read_bytes();summary=json.loads(SUMMARY.read_text(encoding="utf-8"));s=summary["storage"]
        self.assertEqual(s["bytes"],len(raw));self.assertEqual(s["compressed_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(s["canonical_json_sha256"],hashlib.sha256(canonical(self.report)).hexdigest())
        self.assertEqual(gzip.decompress(raw),canonical(self.report))
        for name,sha in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha,name)
        self.assertEqual(self.report["producer_source_utf8"],(ROOT/"tools/loudness_latch_bdf_static_precision.py").read_text(encoding="utf-8"))
        self.assertEqual(self.report["decimal_evaluator_source_utf8"],(ROOT/"tools/circuit66_decimal_static.py").read_text(encoding="utf-8"))
        self.assertTrue(self.report["independent_static_transcription"])
        self.assertTrue(self.report["diagnostic_only"])
        for key in ("independent_full_spatial_oracle","original_reset_fd_gate_closed","previous_reports_modified",
            "new_step_selected","original_solver_modified","temporal_error_bound_admitted","physical_switching_admitted",
            "temporal_refinement_admitted","audio_admitted"):
            self.assertFalse(self.report[key])


if __name__=="__main__":unittest.main()
