from fractions import Fraction as F
from itertools import product
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_spectral_junction as law
import loudness_latch_bdf_static_precision_junction_spectral as producer
from loudness_latch_bdf_doubling_survey import canonical

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def box(a,radius=F(0)):return [[(v-radius,v+radius) for v in row] for row in a]
def known_center():
    q=[[F(v,2) for v in row] for row in ((1,1,1,1),(1,-1,1,-1),(1,1,-1,-1),(1,-1,-1,1))]
    eigen=[F(-9),F(-4),F(1),F(2)]
    return [[sum((q[i][k]*eigen[k]*q[j][k] for k in range(4)),F(0)) for j in range(4)] for i in range(4)]

class SpectralJunction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_exact_ldlt_reconstruction_nonpositive_pivots_and_guards(self):
        lower=[[F(1),F(0),F(0)],[F(1,2),F(1),F(0)],[-F(1,3),F(2,5),F(1)]];d=[F(2),F(3),F(5)]
        a=[[sum((lower[i][k]*d[k]*lower[j][k] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]
        proof=law.ldlt(a);self.assertTrue(proof['positive_definite']);self.assertEqual(proof['lower'],law.pack(lower));self.assertEqual(list(map(F,proof['pivots'])),d)
        for a,failed,pivot in (([[0,1],[1,0]],0,0),([[1,2],[2,1]],1,-3),([[1,1],[1,1]],1,0)):
            proof=law.ldlt(a);self.assertFalse(proof['positive_definite']);self.assertEqual(proof['failed_at'],failed);self.assertEqual(F(proof['pivots'][-1]),pivot)
        for a in ([],[[1,0]],[[1,2],[0,1]]):
            with self.assertRaises(ValueError):law.ldlt(a)
        with self.assertRaises(ValueError):law.spectral_bound([[(1,0)]])
        with self.assertRaises(ValueError):law.spectral_bound([[(0,0),(1,1)],[(0,0),(0,0)]])

    def test_known_eigenvalues_singular_probe_and_same_norm_intersection(self):
        a=known_center();certificate=law.spectral_bound(box(a))
        self.assertLessEqual(F(certificate['center_lambda_lower_per_s']),2)
        self.assertGreater(F(certificate['center_lambda_upper_per_s']),2)
        self.assertLess(F(certificate['lambda_upper_per_s']),4)
        self.assertTrue(certificate['strictly_narrower']);self.assertEqual(certificate['bisections'],32)
        self.assertEqual(len(certificate['probes']),33)
        for value,expected in ((F(1),False),(F(2),False),(F(3),True)):
            self.assertEqual(law.ldlt(law.shifted(a,value))['positive_definite'],expected)
        # On a diagonal matrix the spectral raw upper is strict; declared same-norm Gershgorin gives the exact value.
        c=law.spectral_bound(box([[F(-1),F(0)],[F(0),F(-2)]]))
        self.assertEqual(F(c['lambda_upper_per_s']),-1);self.assertGreater(F(c['raw_lambda_upper_per_s']),-1)
        self.assertTrue(c['same_norm_gershgorin_intersection'])

    def test_full_interval_perturbation_at_all_1024_symmetric_vertices(self):
        a=known_center();r=F(1,100);c=law.spectral_bound(box(a,r));self.assertEqual(F(c['radius_norm_upper_per_s']),4*r)
        upper=F(c['raw_lambda_upper_per_s']);lower=F(c['lambda_lower_per_s']);positions=[(i,j) for i in range(4) for j in range(i,4)]
        for signs in product((-1,1),repeat=10):
            vertex=[row[:] for row in a]
            for (i,j),sign in zip(positions,signs):vertex[i][j]=vertex[j][i]=a[i][j]+sign*r
            self.assertTrue(law.ldlt(law.shifted(vertex,upper))['positive_definite'])
            self.assertFalse(law.ldlt(law.shifted(vertex,lower))['positive_definite'])
        zero=[[F(0)]*2 for _ in range(2)];c=law.spectral_bound(box(zero,F(1)))
        # The center alone has lambda_max=0; all-ones is an admissible vertex with lambda_max=2.
        self.assertGreaterEqual(F(c['lambda_upper_per_s']),2);self.assertFalse(c['center_only_bound'])

    def test_all_64_certificates_2112_probes_and_unchanged_rms_components(self):
        old=read(producer.prior.OUTPUT);count=0
        for c in self.report['cases']:
            previous=old['cases'][c['source_case_index']];self.assertEqual(c['support_sha256'],previous['support_sha256']);self.assertEqual(c['weights'],previous['weights'])
            self.assertEqual(c['prior_rms_peak_zero_anchor_node_upper_v'],previous['propagation']['peak_zero_anchor_node_upper_v']);cells=[]
            self.assertEqual(len(c['cells']),8)
            for record in c['cells']:
                prior_cell=previous['cells'][record['source_cell_index']];m,certificate=law.refine_metrics(prior_cell['metrics'])
                self.assertEqual(certificate,record['spectral_certificate']);self.assertEqual(m['comparison_per_s'],record['comparison_per_s'])
                self.assertEqual(certificate['final_center_upper_ldlt'],law.ldlt(law.shifted([[F(v) for v in row] for row in certificate['center']],F(certificate['center_lambda_upper_per_s']))))
                self.assertTrue(certificate['final_center_upper_ldlt']['positive_definite'])
                self.assertLessEqual(F(certificate['lambda_upper_per_s']),F(prior_cell['metrics']['junction_mu2_gershgorin_upper_per_s']))
                for key,value in prior_cell['metrics'].items():
                    if key!='comparison_per_s':self.assertEqual(m[key],value)
                for i in range(6):
                    for j in range(6):
                        if (i,j)!=(5,5):self.assertEqual(m['comparison_per_s'][i][j],prior_cell['metrics']['comparison_per_s'][i][j])
                count+=len(certificate['probes']);cells.append(dict(forcing_inputs=prior_cell['forcing_inputs'],metrics=m))
            self.assertEqual(producer.prior.law.propagate(cells),c['propagation'])
            self.assertEqual(c['peak_node_budget_nonincreasing'],F(c['propagation']['peak_zero_anchor_node_upper_v'])<=F(previous['propagation']['peak_zero_anchor_node_upper_v']))
            self.assertTrue(c['binary_backward_gate_still_rejected'])
        self.assertEqual(count,2112);self.assertEqual(count,self.report['exact_ldlt_probes'])

    def test_storage_sources_and_proof_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();s=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-junction-spectral/v1');self.assertEqual(len(r['cases']),8)
        self.assertEqual(sha(raw),s['compressed_sha256']);self.assertEqual(len(raw),s['bytes'])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),s['canonical_json_sha256'])
        for p,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        self.assertTrue(r['only_junction_diagonal_changed']);self.assertTrue(r['prior_metric_components_reused_by_reference'])
        self.assertEqual(r['initial_anchor_reference'],'common weighted infinity')
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        for flag in ('norm_changed','weights_changed','block_partition_changed','actual_dae_error_bound','initial_error_known','full_path_coverage',
                     'nonlinear_remainder_bound','temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted','deadline_admitted',
                     'numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(r[flag],flag)
        self.assertEqual(r['new_exact_linear_systems'],0);self.assertEqual(r['new_nonlinear_circuit_solves'],0)

if __name__=='__main__':unittest.main()
