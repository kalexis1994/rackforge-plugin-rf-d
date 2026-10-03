from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_junction_rms as law
import loudness_latch_bdf_static_precision_junction_rms as producer
from loudness_latch_bdf_doubling_survey import canonical

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def manufactured():
    # Four-dimensional generator embedded in the descriptor inverse layout.
    a=[[(F(0),F(0)) for _ in range(26)] for _ in range(26)]
    for i,v in enumerate((1,1,2,3)):a[22+i][22+i]=(F(v),F(v))
    a[22][23]=(F(-8),F(-8));a[23][22]=(F(8),F(8))
    for k,v in enumerate((3,4,0,0)):
        a[0][22+k]=(F(v),F(v));a[18][22+k]=(F(v),F(v))
        a[22+k][18]=(F(v),F(v));a[22+k][0]=(F(v),F(v))
    f=dict(nodal_l1_c=['1'],constraint_l1_v_s=['0']*25,nodal_point_a=['1'],constraint_point_v=['0']*25)
    return a,f

class JunctionRMS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_isqrt_rational_bounds_and_decimal_witnesses(self):
        for x in (F(0),F(1),F(2),F(3),F(25),F(1,3),F(1,4),F(2)**-600,F(2)**700):
            lo,hi=law.sqrt_bounds(x);self.assertLessEqual(lo*lo,x);self.assertLessEqual(x,hi*hi)
            self.assertLessEqual(hi-lo,F(1,law.UNIT))
            self.assertEqual(lo==hi,lo*lo==x)
            with localcontext() as ctx:
                ctx.prec=300;actual=(D(x.numerator)/D(x.denominator)).sqrt()
                self.assertLessEqual(D(lo.numerator)/D(lo.denominator),actual)
                self.assertLessEqual(actual,D(hi.numerator)/D(hi.denominator))
        self.assertEqual(law.norm2_upper([3,4]),5)
        with self.assertRaisesRegex(ValueError,'nonnegative'):law.sqrt_bounds(-1)

    def test_signed_rotation_intervals_and_every_norm_conversion(self):
        inverse,f=manufactured();m=law.block_metrics(inverse,1,[1]*25,f)
        self.assertEqual(F(m['junction_mu2_gershgorin_upper_per_s']),-1)
        self.assertEqual(F(m['prior_junction_mu_infinity_upper_per_s']),7)
        self.assertEqual(m['junction_symmetric_intervals'][0][1],['0','0'])
        # Receiving junction RMS, sending infinity C10; opposite direction differs.
        self.assertEqual(F(m['comparison_per_s'][5][1]),F(5,2))
        self.assertEqual(F(m['comparison_per_s'][1][5]),10)
        self.assertEqual(F(m['block_forcing_l1_v'][5]),F(5,2))
        self.assertEqual(F(m['nodal_block_gains'][0][5]),10)
        old=law.prior.block_metrics(inverse,1,[1]*25,f)
        self.assertGreater(F(m['nodal_block_gains'][0][5]),F(old['nodal_block_gains'][0][5]))
        for i in range(5):
            self.assertEqual(m['block_forcing_l1_v'][i],old['block_forcing_l1_v'][i])
            self.assertEqual(m['nodal_block_gains'][0][i],old['nodal_block_gains'][0][i])
            for j in range(5):self.assertEqual(m['comparison_per_s'][i][j],old['comparison_per_s'][i][j])
        inverse[22][23]=(F(-81,10),F(-79,10));inverse[23][22]=(F(78,10),F(82,10))
        m=law.block_metrics(inverse,1,[1]*25,f)
        self.assertEqual(m['junction_symmetric_intervals'][0][1],['-3/20','3/20'])
        self.assertEqual(F(m['junction_mu2_gershgorin_upper_per_s']),F(-17,20))
        with self.assertRaises(ValueError):law.block_metrics(inverse,1,[0]*25,f)

    def test_anchor_equivalence_and_column_l1_with_disjoint_support(self):
        for values in ((1,1,1,1),(1,0,0,0),(3,-4,0,0)):
            squared=sum((F(v)**2 for v in values),F(0))/4;inf=max(map(abs,values))
            self.assertLessEqual(squared,inf**2);self.assertLessEqual(inf**2,4*squared)
        inverse,f=manufactured()
        inverse[22][0]=(F(1),F(1));inverse[23][0]=(F(0),F(0))
        inverse[22][1]=(F(0),F(0));inverse[23][1]=(F(1),F(1))
        f['constraint_l1_v_s'][0]='1'
        m=law.block_metrics(inverse,1,[1]*25,f)
        self.assertEqual(F(m['block_forcing_l1_v'][5]),1)
        # Two disjoint unit integrals have RMS norm integral 1; norm of integrals sqrt(2)/2 is smaller.
        self.assertLess(law.norm2_upper([1,1])/2,F(m['block_forcing_l1_v'][5]))
        e,p,_=law.prior.kernels([[-1]],1)
        self.assertLess(e[0][0],1);self.assertEqual(p[0][0],1)

    def test_all_64_metrics_symmetric_parts_and_propagation_replay(self):
        old=read(producer.prior.OUTPUT);weighted=read(producer.weighted.OUTPUT)
        for c,previous in zip(self.report['cases'],old['cases']):
            w=weighted['cases'][c['source_case_index']];q=max(F(v['contraction_upper']) for v in w['ideal_temporal_cover']);cells=[]
            self.assertEqual(c['support_sha256'],previous['support_sha256']);self.assertEqual(c['weights'],previous['weights'])
            self.assertEqual(c['prior_infinity_block_propagation'],previous['propagation']);self.assertEqual(len(c['cells']),8)
            for cover,cell,prior_cell in zip(w['ideal_temporal_cover'],c['cells'],previous['cells']):
                inv,cert=producer.structured_inverse(w['inverse_binary'],w['inverse_certificate']['column_scales'],cover,q)
                self.assertEqual(cert,cell['inverse_certificate']);self.assertEqual(cert,prior_cell['inverse_certificate'])
                self.assertEqual(cell['forcing_inputs'],prior_cell['forcing_inputs'])
                metric=law.block_metrics(inv,94,c['weights'],cell['forcing_inputs']);self.assertEqual(metric,cell['metrics'])
                s=metric['junction_symmetric_intervals']
                for i in range(4):
                    for j in range(4):self.assertEqual(s[i][j],s[j][i])
                cells.append(dict(forcing_inputs=cell['forcing_inputs'],metrics=metric))
            self.assertEqual(law.propagate(cells),c['propagation'])
            self.assertTrue(c['binary_backward_gate_still_rejected'])
            self.assertEqual(c['peak_node_budget_nonincreasing'],F(c['propagation']['peak_zero_anchor_node_upper_v'])<=F(previous['propagation']['peak_zero_anchor_node_upper_v']))

    def test_storage_sources_common_anchor_and_unadmitted_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();s=json.loads(producer.SUMMARY.read_text())['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-junction-rms/v1');self.assertEqual(len(r['cases']),8)
        self.assertEqual(sha(raw),s['compressed_sha256']);self.assertEqual(len(raw),s['bytes'])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),s['canonical_json_sha256'])
        for p,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        self.assertEqual(r['initial_anchor_reference'],'common weighted infinity');self.assertTrue(r['junction_norm_changed'])
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        for flag in ('weights_changed','block_partition_changed','block_partition_fitted','actual_dae_error_bound','initial_error_known',
                     'full_path_coverage','nonlinear_remainder_bound','temporal_error_bound_admitted','physical_trajectory_bound',
                     'audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(r[flag],flag)
        self.assertEqual(r['new_exact_linear_systems'],0);self.assertEqual(r['new_nonlinear_circuit_solves'],0)

if __name__=='__main__':unittest.main()
