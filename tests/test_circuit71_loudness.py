"""Joint oracle histories and R59 signs, independent of the native solve."""
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from circuit71_loudness_vectors import evaluator, memory, metrics, solve
from cutoff_j7_vectors import setup


class JointLoudnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/"evidence/circuit71_loudness_vectors.json").read_text())

    def test_every_accepted_step_retains_the_original_eighteen_histories(self):
        for case in self.fixture["cases"]:
            values=setup(case["r61_ohm"])
            old=case["transient_initial"]
            for row in case["rows"]:
                x=row["node_v"]
                residual=evaluator(values,row["c2_v"],row["reset_base_v"],old=old,bus=row["bus_v"])(x)
                self.assertLess(max(map(abs,residual)),1e-11)
                new=memory(x,row["bus_v"],old)
                self.assertEqual(new["capacitor_v"],row["capacitor_v"])
                self.assertEqual(new["c10_v"],row["c10_v"])
                self.assertEqual(metrics(x,row["c2_v"],row["reset_base_v"]),row["metrics"])
                old=new
            rejected=[r["sample"] for r in case["rows"] if r["direct_error"]]
            self.assertEqual(len(rejected),1)
            self.assertTrue(set(rejected).issubset({8,24,40,48}))

    def test_coupling_derivatives_and_unclamped_electrical_domain(self):
        case=self.fixture["cases"][0]
        values=setup(case["r61_ohm"])
        for row in (case["dc_rows"][1],case["dc_rows"][3]):
            x=row["node_v"]
            evaluate=evaluator(values,row["c2_v"],case["reset_base_v"])
            # Row32 is incoming current; row69 is outgoing current. Their
            # independently stamped off-diagonals have opposite signs.
            for col,node,expected in ((69,32,1/68000),(32,69,-1/68000)):
                plus=x.copy(); minus=x.copy()
                plus[col]+=1e-5; minus[col]-=1e-5
                derivative=(evaluate(plus)[node]-evaluate(minus)[node])/2e-5
                self.assertAlmostEqual(derivative,expected,delta=1e-12)
        self.assertLess(case["dc_rows"][1]["node_v"][69],0.0)
        self.assertGreater(case["dc_rows"][3]["node_v"][69],2.0)

    def test_displaced_complete_dc_seed_reproduces_the_fd_root(self):
        case=self.fixture["cases"][0]
        row=case["dc_rows"][1]
        evaluate=evaluator(setup(case["r61_ohm"]),0.0,case["reset_base_v"])
        x,diag=solve([v+0.001 for v in row["node_v"]],evaluate)
        self.assertLess(max(abs(a-b) for a,b in zip(x,row["node_v"])),1e-6)
        self.assertLess(diag["correction_v"],1e-8)


if __name__=="__main__": unittest.main()
