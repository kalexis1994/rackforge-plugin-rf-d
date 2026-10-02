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
import loudness_latch_bdf_static_precision_memory_quadratic as experiment
import loudness_latch_directional_curvature as curvature
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_static_precision_windows import candidate
from loudness_latch_bdf_memory_transfer import stamps
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_static_precision import solved
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters
from junction_charge_reference import Depletion


class Quadratic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(experiment.OUTPUT.read_bytes()))
        source=json.loads(gzip.decompress(experiment.SOURCE.read_bytes()))
        cls.source=[{k:v for k,v in w.items() if k!="experiments"} for w in source["windows"]]
        cls.definitions=[experiment.definitions(w) for w in json.loads(gzip.decompress(experiment.DIRECTIONS.read_bytes()))["windows"]]
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_full_static_graph_r59_and_frozen_direction_identity(self):
        g=curvature.graph(self.network)
        self.assertEqual(canonical(g),canonical(self.report["graph"]))
        self.assertEqual(g["node_count"],94)
        r59=next(r for r in g["resistors"] if r["ref"]=="R59-VCA1")
        self.assertEqual((r59["left"],r59["right"]),(32,self.network.network.joint.out))
        self.assertEqual(sum(r["ref"]=="R59-VCA1" for r in g["resistors"]),1)
        for w,defs in zip(self.report["windows"],self.definitions):
            self.assertEqual(w["definitions"],defs)
            self.assertEqual(len(w["rows"]),64)
            for row in w["rows"]:
                if "audit" not in row:continue
                x=np.array(row["node_candidate_v"])
                r,_=curvature.static_values(g,x,80,jacobian=False)
                old,_=self.network.network.joint.evaluator(10.)(x,False)
                error=float(np.max(abs(curvature.floats(r)-old)))
                self.assertEqual(error,row["audit"]["static_current_discrepancy_a"])
                self.assertEqual(error<1e-11,row["audit"]["static_current_gate_passed"])

    def test_all_first_second_recurrences_curvature_and_backward_gates(self):
        count=0
        for w,base in zip(self.report["windows"],self.source):
            current1=np.array([d["current_direction_v"] for d in w["definitions"]]).T
            previous1=np.array([d["previous_direction_v"] for d in w["definitions"]]).T
            current2=np.zeros_like(current1);previous2=current2.copy();old=unpack(self.network,w["initial"])
            for row,step,op in zip(w["rows"],base["reference"],base["operators"]):
                virtual,c,x=candidate(old,step,self.network);gamma=c["gamma"]
                v1=(1+gamma)*current1-gamma*previous1;v2=(1+gamma)*current2-gamma*previous2
                n1=np.array(op["node_map"])@v1;m1=np.array(op["memory_map"])@v1
                np.testing.assert_array_equal(n1,row["node_first_v"]);np.testing.assert_array_equal(m1,row["memory_first_v"])
                np.testing.assert_array_equal(x,row["node_candidate_v"]);self.assertEqual(c,row["coefficients"])
                new=unpack(self.network,step["history"]);b,p,d=stamps(self.network,new,c["effective_dt_s"])
                curves=[];publications=[]
                for k,term in enumerate(row["terms"]):
                    a=curvature.evaluate(self.network,self.report["graph"],x,n1[:,k],c["effective_dt_s"],80)
                    a100=curvature.evaluate(self.network,self.report["graph"],x,n1[:,k],c["effective_dt_s"],100)
                    self.assertEqual([str(v) for v in a["residual_a"]],term["residual_a"])
                    self.assertEqual([str(v) for v in a["publication_coordinate_v"]],term["publication_coordinate_v"])
                    for key in ("residual_a","publication_coordinate_v"):
                        self.assertEqual(curvature.metrics(a[key],a100[key]),term["precision_comparison"][key])
                    curves.append(curvature.floats(a["residual_a"]));publications.append(curvature.floats(a["publication_coordinate_v"]))
                rhs=b@v2-np.array(curves).T
                np.testing.assert_array_equal(rhs,row["rhs_second_a"])
                _,j=self.network.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(np.array(step["diagnostics"]["increment_v"]))
                n2=np.array(row["node_second_v"]);_,errors=backward_errors(j,rhs,n2)
                for key,value in errors.items():self.assertEqual(value,row["linear_solve"][key])
                self.assertLess(max(errors.values()),1e-10)
                m2=p@n2+d@v2+np.array(publications).T
                np.testing.assert_array_equal(m2,row["memory_second_v"])
                previous1,current1=current1,m1;previous2,current2=current2,m2;old=new;count+=1
        self.assertEqual(count,256)

    def test_216_fd_contrasts_and_four_exact_rational_replays(self):
        fd_count=0;rational_count=0
        for w in self.report["windows"]:
            for row in w["rows"]:
                if "audit" not in row:continue
                audit=row["audit"];x=np.array(row["node_candidate_v"]);n1=np.array(row["node_first_v"])
                dt=row["coefficients"]["effective_dt_s"]
                for k,fd in enumerate(audit["fd"]):
                    ref=curvature.evaluate(self.network,self.report["graph"],x,n1[:,k],dt,80)
                    for level in fd["levels"]:
                        value=curvature.finite_difference(self.network,self.report["graph"],x,n1[:,k],dt,level["epsilon"],80)
                        for key in ("residual_a","publication_coordinate_v"):
                            self.assertEqual(curvature.metrics(ref[key],value[key]),level["comparisons"][key])
                        fd_count+=1
                if row["index"]==31:
                    exact=audit["exact"]
                    fresh=solved(np.array(exact["jacobian_s"]),np.array(row["rhs_second_a"]))
                    for key in ("jacobian_s","node_map","exact_solve","backward_errors","passed"):
                        self.assertEqual(canonical(fresh[key]),canonical(exact[key]))
                    rational_count+=1
        self.assertEqual(fd_count,216);self.assertEqual(rational_count,4)

    def test_charge_piecewise_derivative_polarity_and_conservation_witnesses(self):
        p=model_parameters(1,"finite_transit")
        with localcontext() as ctx:
            ctx.prec=80
            for dep,t,scale in ((p.depletion_be,p.transit_forward_s,p.emission_be_v),(p.depletion_bc,p.transit_reverse_s,p.emission_bc_v),
                                (Depletion(7e-12,.75,1.,.4),0.,p.emission_be_v)):
                knee=dep.forward_fraction*dep.potential_v
                for v in (-.2,0.,knee-1e-3,knee+1e-3):
                    q,c,q2=curvature.junction_values(dep,t,p.saturation_a,scale,v)
                    h=D('1e-8');vf=D.from_float(v)
                    qp=curvature.junction_values(dep,t,p.saturation_a,scale,vf+h)[0]
                    qm=curvature.junction_values(dep,t,p.saturation_a,scale,vf-h)[0]
                    self.assertLess(abs((qp-qm)/(2*h)-c)/(D('1e-30')+D('1e-8')*abs(c)),1)
                    self.assertLess(abs((qp-2*q+qm)/(h*h)-q2)/(D('1e-30')+D('1e-8')*abs(q2)),1)
            g=dict(node_count=3,fixed={},resistors=[],conductances=[],diodes=[],bjts=[dict(
                ref="conditional",base=0,collector=1,emitter=2,polarity=1,is_a=1e-14,vt=p.emission_be_v,beta_forward=100.,beta_reverse=5.)])
            x=[.3,.1,0.];direction=[1e-6,-2e-6,0.]
            a=curvature.static_curvature(g,x,direction,80)
            self.assertLess(abs(sum(a)),D('1e-60'))
            g["bjts"][0]["polarity"]=-1
            mirrored=curvature.static_curvature(g,[-v for v in x],[-v for v in direction],80)
            self.assertEqual(mirrored,[-v for v in a])
            with self.assertRaises(ValueError):curvature.static_curvature(g,[-2.,0.,0.],direction,80)
        with self.assertRaises(ValueError):
            curvature.evaluate(self.network,self.report["graph"],[0.]*94,[0.]*94,1e-6)
        valid=self.report["windows"][0]["rows"][0]["node_candidate_v"]
        zero=curvature.evaluate(self.network,self.report["graph"],valid,[0.]*94,1e-6)
        self.assertEqual(zero["residual_a"],[D(0)]*94);self.assertEqual(zero["publication_coordinate_v"],[D(0)]*25)

    def test_storage_sources_reserved_levels_and_no_fitting(self):
        r=self.report;raw=experiment.OUTPUT.read_bytes();summary=json.loads(experiment.SUMMARY.read_text())
        storage=summary["storage"]
        self.assertEqual(len(raw),storage["bytes"]);self.assertEqual(hashlib.sha256(raw).hexdigest(),storage["compressed_sha256"])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(hashlib.sha256(canonical(r)).hexdigest(),storage["canonical_json_sha256"])
        for name,sha in r["source_sha256"].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha,name)
        self.assertEqual(r["reserved_response_amplitudes"],[.75,.375,.1875]);self.assertEqual(r["new_nonlinear_solves"],0)
        self.assertFalse(r["coefficients_fitted_to_responses"]);self.assertTrue(r["initial_second_variations_zero"])
        for key in ("temporal_error_bound_admitted","physical_switching_admitted","audio_admitted","deadline_admitted"):self.assertFalse(r[key])


if __name__=="__main__":unittest.main()
