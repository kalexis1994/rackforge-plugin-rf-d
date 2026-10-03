from fractions import Fraction as F
import gzip,json,hashlib
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_cell_propagation as law
import loudness_latch_bdf_static_precision_cell_propagation as producer
from loudness_latch_bdf_doubling_survey import canonical

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def scalar_cell(left,right,mu,b):
    return dict(forcing_inputs=dict(left=str(left),right=str(right),duration_s=str(F(right)-F(left))),
        metrics=dict(logarithmic_norm_upper_per_s=str(mu),integrated_forcing_norm_upper_v=str(b),
            node_from_weighted_memory_gain_upper='1',node_direct_forcing_upper_v='0'))

class CellPropagation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_integer_dot_products_match_independent_fraction_arithmetic(self):
        a=[[(F(-1,8),F(1,4)),(F(1,16),F(3,8))],[(F(-1,2),F(-1,4)),(F(0),F(1,8))]]
        b=[[F(2),F(-1,8)],[F(-1,4),F(0)]];out=law.interval_dyadic_product(a,b)
        for i in range(2):
            for j in range(2):
                products=[tuple(sorted((a[i][k][0]*b[k][j],a[i][k][1]*b[k][j]))) for k in range(2)]
                self.assertEqual(out[i][j],tuple(sum((v[t] for v in products),F(0)) for t in (0,1)))
        with self.assertRaisesRegex(ValueError,'dyadic'):law.interval_dyadic_product([[(F(1,3),F(1,3))]],[[1]])
        with self.assertRaisesRegex(ValueError,'square'):law.interval_dyadic_product(a,[[1]])
        with self.assertRaisesRegex(ValueError,'ordered'):law.interval_dyadic_product([[(1,0)]],[[1]])

    def test_rational_inverse_first_signed_term_row_tail_and_guards(self):
        e=[[F(1,8),F(1,16)],[-F(1,16),-F(1,8)]];q=F(3,16)
        cover=dict(preconditioned_defect_intervals=[[(v,v) for v in row] for row in e],contraction_upper=str(q))
        x=[[1,0],[0,1]];d=[F(2),F(1,2)];out,cert=law.structured_inverse(x,d,cover,F(1,4))
        # A=D*X*H*D^-1=I-E. Invert the exact 2x2 A, then H^-1=D^-1*A^-1*D.
        a,b,c,z=1-e[0][0],-e[0][1],-e[1][0],1-e[1][1];det=a*z-b*c
        exact=[[z/det,-b/det],[-c/det,a/det]]
        for i in range(2):
            for j in range(2):
                value=exact[i][j]*d[j]/d[i];lo,hi=out[i][j]
                self.assertLessEqual(lo,value);self.assertLessEqual(value,hi)
                peak=d[j];tail=q*q/(1-q)*peak
                raw=(F(x[i][j])+e[i][j]*d[j]/d[i]-tail/d[i],F(x[i][j])+e[i][j]*d[j]/d[i]+tail/d[i])
                parent=F(1,4)/(1-F(1,4))*peak/d[i];row=q/(1-q)*peak/d[i]
                self.assertEqual(out[i][j],(max(raw[0],F(x[i][j])-row,F(x[i][j])-parent),min(raw[1],F(x[i][j])+row,F(x[i][j])+parent)))
        self.assertEqual(cert['strictly_narrower_entries'],4)
        with self.assertRaisesRegex(ValueError,'positive'):law.structured_inverse(x,[0,1],cover,q)
        with self.assertRaisesRegex(ValueError,'contracted'):law.structured_inverse(x,d,cover,q/2)
        with self.assertRaisesRegex(ValueError,'contracted'):law.structured_inverse(x,d,cover|dict(contraction_upper='1'),1)

    def test_signed_contraction_late_forcing_and_disjoint_cells(self):
        # Exact sign: old error contracts, but L1 forcing may occur at the end.
        out=law.propagate([scalar_cell(0,1,-1,1)])
        self.assertLess(F(out['endpoint_weighted_anchor_gain_upper']),1)
        self.assertEqual(F(out['peak_node_from_weighted_anchor_gain_upper']),1)
        self.assertEqual(F(out['endpoint_zero_anchor_memory_upper_v']),1)
        self.assertEqual(F(out['peak_zero_anchor_node_upper_v']),1)
        first=law.propagate([scalar_cell(0,F(1,2),-1,1),scalar_cell(F(1,2),1,-1,0)])
        late=law.propagate([scalar_cell(0,F(1,2),-1,0),scalar_cell(F(1,2),1,-1,1)])
        self.assertLess(F(first['endpoint_zero_anchor_memory_upper_v']),F(late['endpoint_zero_anchor_memory_upper_v']))
        self.assertEqual(F(first['peak_zero_anchor_node_upper_v']),1)
        # A forcing pulse on [1-epsilon,1] tends to 1, defeating exp(-1)*L1.
        eps=F(1,1024);lower=1-eps/2
        self.assertGreater(lower,F(out['endpoint_weighted_anchor_gain_upper']))
        for cells in ([],[scalar_cell(0,F(1,2),0,0)],[scalar_cell(F(1,2),1,0,0)],
                      [scalar_cell(0,F(3,4),0,0),scalar_cell(F(1,2),1,0,0)],
                      [scalar_cell(0,1,4097,0)],[scalar_cell(0,1,0,-1)]):
            with self.assertRaises(ValueError):law.propagate(cells)

    def test_residual_partition_rejects_gaps_and_preserves_signed_polynomials(self):
        parent=dict(cells_a=[[('-2','3'),('-1','1')]]*2)
        rate=dict(active_nodes=[0],segments=[dict(left='0',right='1/4',active_a=[('-1','2')]),
            dict(left='1/4',right='1',active_a=[('-1/2','1/2')])])
        out=law.residual_cells(parent,rate,[(F(-1),F(2))],2,count=2)
        self.assertEqual(list(map(F,out[0]['nodal_l1_c'])),[F(5,4),F(1)])
        self.assertEqual(list(map(F,out[1]['nodal_l1_c'])),[F(1,2),F(1)])
        self.assertEqual(list(map(F,out[0]['constraint_point_v'])),[F(1),F(0),F(0),F(0),F(0)])
        for bad in (rate|dict(segments=rate['segments'][:1]),rate|dict(segments=rate['segments']+[rate['segments'][0]])):
            with self.assertRaisesRegex(ValueError,'gap or overlap'):law.residual_cells(parent,bad,[(F(0),)],2,count=2)

    def test_all_64_inverse_certificates_forcing_and_budget_replays(self):
        old=read(producer.prior.OUTPUT);boxes=producer.rows(producer.rectangular.OUTPUT);rates=producer.rows(producer.correlated.OUTPUT)
        dense=producer.prior.dense
        refs={(w['name'],l['reference']['subdivisions']):l['reference'] for w in read(dense.previous.proxy.REFERENCE)['windows'] for l in w['levels']}
        network=dense.CompensatedBdfNetwork(200,dense.model_parameters(1,'finite_transit'))
        for case in self.report['cases']:
            prior=old['cases'][case['source_case_index']];key=(case['window'],case['subdivisions'],case['index'])
            prepared=dense.prepare(network,refs[key[:2]],key[2]);self.assertEqual(prepared['support_sha256'],case['support_sha256'])
            self.assertEqual(case['weights'],prior['weights']);self.assertEqual(case['prior_weighted_temporal_budget'],prior['weighted_temporal_budget'])
            forcing=law.residual_cells(boxes[key]['result'],rates[key]['result'],prepared['equations'],prepared['h'])
            q=max(F(v['contraction_upper']) for v in prior['ideal_temporal_cover']);replayed=[]
            for i,(cell,cover) in enumerate(zip(case['cells'],prior['ideal_temporal_cover'])):
                inverse,cert=law.structured_inverse(prior['inverse_binary'],prior['inverse_certificate']['column_scales'],cover,q)
                self.assertEqual(cert,cell['inverse_certificate']);self.assertEqual(forcing[i],cell['forcing_inputs'])
                metric=law.metrics(inverse,94,case['weights'],forcing[i]);self.assertEqual(metric,cell['metrics'])
                replayed.append(dict(forcing_inputs=forcing[i],metrics=metric))
            self.assertEqual(len(replayed),8);self.assertEqual(law.propagate(replayed),case['propagation'])
            for k,values in case['recombined_l1'].items():
                for j,v in enumerate(values):
                    self.assertEqual(F(v),sum((F(f[k][j]) for f in forcing),F(0)))
                    self.assertLessEqual(F(v),F(prior['forcing_inputs'][k][j]))
            self.assertTrue(case['binary_backward_gate_still_rejected']);self.assertTrue(case['recombined_l1_nonincreasing'])
            self.assertEqual(case['peak_node_budget_nonincreasing'],F(case['propagation']['peak_zero_anchor_node_upper_v'])<=F(prior['weighted_temporal_budget']['zero_anchor_forced_node_upper_v']))

    def test_asymmetric_metrics_independent_row_and_column_formula(self):
        a=[[(F(3),F(4)),(F(-2),F(-1))],[(F(-5),F(-4)),(F(2),F(3))]]
        f=dict(nodal_l1_c=['1/2'],constraint_l1_v_s=['1/4'],nodal_point_a=['1'],constraint_point_v=['2'])
        m=law.metrics(a,1,[2],f)
        self.assertEqual(list(map(F,m.values())),[F(-2),F(13,2),F(1),F(8)])
        with self.assertRaisesRegex(ValueError,'positive'):law.metrics(a,1,[0],f)
        with self.assertRaisesRegex(ValueError,'nonnegative'):law.metrics(a,1,[2],f|dict(nodal_l1_c=['-1']))

    def test_storage_sources_and_unadmitted_scope(self):
        report=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text())['storage']
        self.assertEqual(report['schema'],'rf-d/bdf-static-cell-propagation/v1');self.assertEqual(len(report['cases']),8)
        self.assertEqual(len(raw),storage['bytes']);self.assertEqual(sha(raw),storage['compressed_sha256'])
        self.assertEqual(gzip.decompress(raw),canonical(report));self.assertEqual(sha(canonical(report)),storage['canonical_json_sha256'])
        for p,h in report['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        for flag in ('weights_changed','actual_dae_error_bound','initial_error_known','full_path_coverage','nonlinear_remainder_bound',
                     'temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(report[flag],flag)
        self.assertEqual(report['new_exact_linear_systems'],0);self.assertEqual(report['new_nonlinear_circuit_solves'],0)

if __name__=='__main__':unittest.main()
