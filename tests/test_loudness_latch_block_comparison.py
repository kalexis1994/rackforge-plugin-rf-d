from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_block_comparison as law
import loudness_latch_bdf_static_precision_block_comparison as producer
from loudness_latch_bdf_doubling_survey import canonical

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def decimal(v):v=F(v);return D(v.numerator)/D(v.denominator)
def scalar(left,right,mu,b):
    return dict(forcing_inputs=dict(left=str(left),right=str(right),duration_s=str(F(right)-F(left))),
        metrics=dict(comparison_per_s=[[str(mu)]],block_forcing_l1_v=[str(b)],nodal_block_gains=[['1']],nodal_direct_v=['0']))

class BlockComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_triangular_semigroup_and_peak_against_analytic_solution(self):
        # exp([[-1,2],[0,-2]]t) off-diagonal=2*(exp(-t)-exp(-2t)).
        for h in (F(1,8),F(1),F(4)):
            end,peak,cert=law.kernels([[-1,2],[0,-2]],h)
            with localcontext() as ctx:
                ctx.prec=180;t=decimal(h);a=(-t).exp();b=(-2*t).exp()
                actual=[[a,2*(a-b)],[D(0),b]]
                for i in range(2):
                    for j in range(2):self.assertGreaterEqual(decimal(end[i][j]),actual[i][j])
                # Independent 33 point witnesses exercise the interior, not the proof.
                for k in range(33):
                    t=decimal(h)*k/32;a=(-t).exp();b=(-2*t).exp()
                    for i,j,v in ((0,0,a),(0,1,2*(a-b)),(1,0,D(0)),(1,1,b)):
                        self.assertGreaterEqual(decimal(peak[i][j]),v)
            if h>=1:self.assertGreaterEqual(peak[0][1],F(1,2)) # exact maximum at log(2).
            self.assertEqual(end[1][0],0);self.assertEqual(peak[1][0],0)
            self.assertEqual(cert['endpoint_sha256'],law.digest(end));self.assertEqual(cert['peak_sha256'],law.digest(peak))
        a=[[F(1,2),F(1,4)],[F(0),F(1,8)]];b=[[F(1,4),F(0)],[F(1,2),F(1,4)]]
        expected=[[sum((a[i][k]*b[k][j] for k in range(2)),F(0)) for j in range(2)] for i in range(2)]
        self.assertEqual(law.multiply(a,b),expected)

    def test_zero_positive_exponential_and_declared_domains(self):
        end,peak,cert=law.kernels([[0,0],[0,0]],1)
        self.assertEqual(end,law.identity(2));self.assertEqual(peak,law.identity(2))
        self.assertEqual(F(cert['small_endpoint_tail_upper']),0)
        for m,h in (([[0,-1],[0,0]],1),([[-4097]],1),([[1]],0),([[1,0]],1)):
            with self.assertRaises(ValueError):law.kernels(m,h)
        with self.assertRaisesRegex(ValueError,'domain'):law.positive_exponential([[F(2)]])
        with self.assertRaisesRegex(ValueError,'positive'):law.multiply([[F(-1)]],[[F(1)]])

    def test_block_rows_columns_and_disjoint_forcing_independently(self):
        x=[[3,1,2,4],[-1,2,-8,-3],[-2,F(-1,2),1,-4],[-3,-1,-2,5]]
        inv=[[(F(v),F(v)) for v in row] for row in x]
        f=dict(nodal_l1_c=['1/2'],constraint_l1_v_s=['1/4']*3,nodal_point_a=['1'],constraint_point_v=['1']*3)
        m=law.block_metrics(inv,1,[1,4,2],f,blocks=((0,1),(2,)))
        self.assertEqual(m['comparison_per_s'],[['1','8'],['3','-5']])
        self.assertEqual(list(map(F,m['block_forcing_l1_v'])),[F(21,2),F(7)])
        self.assertEqual(m['nodal_block_gains'],[['3/2','2']]);self.assertEqual(m['nodal_direct_v'],['10'])
        for groups in (((0,1),(1,2)),((0,),()),((0,1),)):
            with self.assertRaises(ValueError):law.block_metrics(inv,1,[1,4,2],f,blocks=groups)
        with self.assertRaises(ValueError):law.block_metrics(inv,1,[1,0,2],f,blocks=((0,1),(2,)))
        # Disjoint supports in two rows each have integral 1, integral max is 2.
        x=[[0]*4,[0]*4,[1,0,0,0],[0,1,0,0]];inv=[[(F(v),F(v)) for v in row] for row in x]
        f=dict(nodal_l1_c=['1','1'],constraint_l1_v_s=['0','0'],nodal_point_a=['2','2'],constraint_point_v=['0','0'])
        self.assertEqual(law.block_metrics(inv,2,[1,1],f,blocks=((0,1),))['block_forcing_l1_v'],['2'])

    def test_contraction_late_forcing_and_contiguous_composition(self):
        out=law.propagate([scalar(0,1,-1,1)])
        self.assertLess(F(out['endpoint_block_anchor'][0]),1)
        self.assertEqual(out['peak_node_anchor_gain_upper'],'1');self.assertEqual(out['peak_zero_anchor_node_upper_v'],'1')
        self.assertEqual(out['endpoint_block_forced_v'],['1'])
        early=law.propagate([scalar(0,F(1,2),-1,1),scalar(F(1,2),1,-1,0)])
        late=law.propagate([scalar(0,F(1,2),-1,0),scalar(F(1,2),1,-1,1)])
        self.assertLess(F(early['endpoint_block_forced_v'][0]),F(late['endpoint_block_forced_v'][0]))
        for cells in ([],[scalar(0,F(1,2),0,0)],[scalar(F(1,2),1,0,0)],
                      [scalar(0,F(3,4),0,0),scalar(F(1,2),1,0,0)],[scalar(0,1,0,-1)]):
            with self.assertRaises(ValueError):law.propagate(cells)

    def test_all_64_block_metrics_kernels_and_propagation_replay(self):
        previous=read(producer.prior.OUTPUT);weighted=read(producer.prior.prior.OUTPUT)
        self.assertEqual(self.report['blocks'],[list(v) for v in law.BLOCKS])
        self.assertEqual(self.report['block_names'],list(law.NAMES))
        for c,old in zip(self.report['cases'],previous['cases']):
            w=weighted['cases'][c['source_case_index']];q=max(F(v['contraction_upper']) for v in w['ideal_temporal_cover']);cells=[]
            self.assertEqual(c['support_sha256'],old['support_sha256']);self.assertEqual(c['weights'],old['weights'])
            self.assertEqual(c['prior_scalar_propagation'],old['propagation']);self.assertEqual(len(c['cells']),8)
            for cover,cell,prior_cell in zip(w['ideal_temporal_cover'],c['cells'],old['cells']):
                inv,cert=producer.prior.law.structured_inverse(w['inverse_binary'],w['inverse_certificate']['column_scales'],cover,q)
                self.assertEqual(cert,cell['inverse_certificate']);self.assertEqual(cert,prior_cell['inverse_certificate'])
                self.assertEqual(cell['forcing_inputs'],prior_cell['forcing_inputs'])
                metrics=law.block_metrics(inv,94,c['weights'],cell['forcing_inputs']);self.assertEqual(metrics,cell['metrics'])
                cells.append(dict(forcing_inputs=cell['forcing_inputs'],metrics=metrics))
            self.assertEqual(law.propagate(cells),c['propagation'])
            self.assertTrue(c['binary_backward_gate_still_rejected'])
            self.assertEqual(c['peak_node_budget_nonincreasing'],F(c['propagation']['peak_zero_anchor_node_upper_v'])<=F(old['propagation']['peak_zero_anchor_node_upper_v']))

    def test_storage_sources_scope_and_destination_contract(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text())['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-block-comparison/v1');self.assertEqual(len(r['cases']),8)
        self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(len(raw),storage['bytes'])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256'])
        for p,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY)
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        self.assertEqual(storage['path'],producer.OUTPUT.relative_to(ROOT).as_posix())
        for flag in ('weights_changed','block_partition_fitted','actual_dae_error_bound','initial_error_known','full_path_coverage',
                     'nonlinear_remainder_bound','temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted',
                     'deadline_admitted','numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(r[flag],flag)
        self.assertEqual(r['new_exact_linear_systems'],0);self.assertEqual(r['new_nonlinear_circuit_solves'],0)

if __name__=='__main__':unittest.main()
