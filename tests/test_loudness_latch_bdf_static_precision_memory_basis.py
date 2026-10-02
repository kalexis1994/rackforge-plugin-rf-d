import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import loudness_latch_bdf_static_precision_memory_basis as experiment
from loudness_latch_bdf_doubling_survey import canonical


class MemoryBasis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(experiment.OUTPUT.read_bytes()))
        cls.source=json.loads(gzip.decompress(experiment.SOURCE.read_bytes()))

    def test_complete_basis_recurrence_singular_values_and_peak_directions(self):
        count=0
        for w,base in zip(self.report["windows"],self.source["windows"]):
            self.assertEqual(w["name"],base["name"])
            current,previous=experiment.basis()
            np.testing.assert_array_equal(current,self.report["initial_current_basis"])
            np.testing.assert_array_equal(previous,self.report["initial_previous_basis"])
            for r,op,ref in zip(w["rows"],base["operators"],base["reference"]):
                gamma=op["coefficients"]["gamma"];virtual=(1+gamma)*current-gamma*previous
                nodes=np.array(op["node_map"])@virtual;memory=np.array(op["memory_map"])@virtual
                np.testing.assert_array_equal(nodes,r["cumulative_node_matrix"])
                np.testing.assert_array_equal(memory,r["cumulative_memory_matrix"])
                self.assertEqual(r["time_s"],ref["history"]["time_s"])
                for name,matrix in (("node_basis",nodes),("memory_basis",memory),("double_history_basis",np.vstack((memory,current)))):
                    stored=r[name];v=np.array(stored["maximum_right_direction"])
                    self.assertGreaterEqual(v[int(np.argmax(abs(v)))],0)
                    self.assertAlmostEqual(np.linalg.norm(v),1.,places=12)
                    # Reproduce the declared SVD route; values-only dispatch uses
                    # a different LAPACK path. Keep the independent norm witness.
                    _,s,_=np.linalg.svd(matrix,full_matrices=False)
                    np.testing.assert_array_equal(s,stored["singular_values"])
                    self.assertAlmostEqual(np.linalg.norm(matrix@v)/stored["spectral_norm"],1.,places=11)
                previous,current=current,memory;count+=1
            self.assertEqual(w["complete"],len(w["rows"])==64)
        self.assertEqual(count,256)

    def test_decimal80_and_100_entire_recurrence_digests_and_product_gates(self):
        count=0
        for w,base in zip(self.report["windows"],self.source["windows"]):
            current,previous=experiment.basis()
            precise={p:(experiment.lift(current),experiment.lift(previous)) for p in (80,100)}
            for row,op in zip(w["rows"],base["operators"]):
                results={p:experiment.precise_step(op,*precise[p],p) for p in (80,100)}
                for p,(n,m) in results.items():
                    self.assertEqual(experiment.digest(n),row[f"decimal{p}_node_sha256"])
                    self.assertEqual(experiment.digest(m),row[f"decimal{p}_memory_sha256"])
                n80,m80=[experiment.rounded(v) for v in results[80]]
                n100,m100=[experiment.rounded(v) for v in results[100]]
                np.testing.assert_array_equal(n80,row["decimal80_rounded_node_matrix"])
                np.testing.assert_array_equal(m80,row["decimal80_rounded_memory_matrix"])
                self.assertEqual(np.array_equal(n80,n100),row["decimal80_100_rounded_nodes_equal"])
                self.assertEqual(np.array_equal(m80,m100),row["decimal80_100_rounded_memory_equal"])
                nm=experiment.metrics(n80,np.array(row["cumulative_node_matrix"]))
                mm=experiment.metrics(m80,np.array(row["cumulative_memory_matrix"]))
                self.assertEqual(nm,row["node_rounding_comparison"]);self.assertEqual(mm,row["memory_rounding_comparison"])
                passed=nm["passed"] and mm["passed"] and np.array_equal(n80,n100) and np.array_equal(m80,m100)
                self.assertEqual(bool(passed),row["product_gate_passed"])
                for p in (80,100):precise[p]=(results[p][1],precise[p][0])
                count+=1
        self.assertEqual(count,256)

    def test_current_previous_orientation_against_all_archived_direction_predictions(self):
        count=0
        for w,base in zip(self.report["windows"],self.source["windows"]):
            for e in base["experiments"]:
                direction=np.concatenate((e["current_direction_v"],e["previous_direction_v"]))
                for level in e["levels"]:
                    for case in level["cases"]:
                        injection=case["sign"]*level["amplitude"]*direction
                        for row,step in zip(w["rows"],case["steps"]):
                            for name in ("node","memory"):
                                from_basis=np.array(row[f"cumulative_{name}_matrix"])@injection
                                direct=np.array(step[f"predicted_{name}_difference_v"])
                                self.assertLess(float(np.max(abs(from_basis-direct)/(1+abs(direct)))),experiment.GATE)
                            count+=1
        self.assertEqual(count,8192)

    def test_storage_sources_summary_peaks_and_linear_only_scope(self):
        r=self.report;raw=experiment.OUTPUT.read_bytes()
        summary=json.loads(experiment.SUMMARY.read_text(encoding="utf-8"));s=summary["storage"]
        self.assertEqual(len(raw),s["bytes"]);self.assertEqual(hashlib.sha256(raw).hexdigest(),s["compressed_sha256"])
        self.assertEqual(gzip.decompress(raw),canonical(r))
        self.assertEqual(hashlib.sha256(canonical(r)).hexdigest(),s["canonical_json_sha256"])
        for path,expected in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected,path)
        self.assertEqual(r["precisions"],[80,100]);self.assertEqual(r["input_dimension"],50)
        self.assertEqual(r["product_scaled_gate"],1e-8);self.assertEqual(r["new_nonlinear_solves"],0)
        self.assertEqual(r["new_spatial_solves"],0);self.assertTrue(r["diagnostic_only"])
        self.assertTrue(r["operator_coefficients_lifted_exactly_from_binary64"])
        for key in ("unit_basis_is_finite_physical_injection","full_nonlinear_direction_validation",
            "global_temporal_error_bound_admitted","physical_switching_admitted","audio_admitted","deadline_admitted"):
            self.assertFalse(r[key])
        for w,small in zip(r["windows"],summary["windows"]):
            self.assertEqual(small["product_passes"],sum(row["product_gate_passed"] for row in w["rows"]))
            for name in ("node_basis","memory_basis","double_history_basis"):
                i=max(range(len(w["rows"])),key=lambda i:w["rows"][i][name]["spectral_norm"])
                self.assertEqual(small["peaks"][name]["index"],i)
                self.assertEqual(small["peaks"][name]["time_s"],w["rows"][i]["time_s"])
                self.assertEqual(small["peaks"][name]["spectral_norm"],w["rows"][i][name]["spectral_norm"])


if __name__=="__main__":unittest.main()
