from fractions import Fraction as F
from itertools import product,combinations
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_junction_balanced as law
import loudness_latch_bdf_static_precision_junction_balanced as producer
from loudness_latch_spectral_junction import ldlt
from loudness_latch_bdf_doubling_survey import canonical

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def point(a):return [[(F(v),F(v)) for v in row] for row in a]
def diagonal(values):return [[F(v) if i==j else F(0) for j in range(4)] for i,v in enumerate(values)]
def exact_det(a):
    # Independent pivoted elimination; PSD requires every principal minor, including zeros.
    a=[[F(v) for v in row] for row in a];n=len(a);out=F(1)
    for k in range(n):
        pivot=next((i for i in range(k,n) if a[i][k]),None)
        if pivot is None:return F(0)
        if pivot!=k:a[k],a[pivot]=a[pivot],a[k];out=-out
        p=a[k][k];out*=p
        for i in range(k+1,n):
            ratio=a[i][k]/p
            for j in range(k+1,n):a[i][j]-=ratio*a[k][j]
    return out

class JunctionBalanced(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_fixed_outward_roots_scale_invariance_and_domain_guards(self):
        d=[F(1,10000),F(3,7),F(100),F(987654321)]
        prepared=dict(diagonal=list(map(str,d)),time_scale_per_s='1');fixed=law.balance(prepared)
        for v,bracket,weight in zip(d,fixed['reciprocal_sqrt_brackets'],fixed['weights']):
            lo,hi=map(F,bracket);g=F(weight)
            self.assertLessEqual(lo*lo,1/v);self.assertGreaterEqual(hi*hi,1/v)
            self.assertGreaterEqual(g,hi);self.assertLess(g-hi,F(1,1<<40));self.assertEqual((g*(1<<40)).denominator,1)
        self.assertEqual(fixed['basis_sha256'],law.box.digest(prepared));self.assertEqual(fixed,law.balance(prepared))
        for bad in (['0','1','1','1'],['-1','1','1','1'],['1']):
            with self.assertRaises(ValueError):law.balance(prepared|dict(diagonal=bad))
        c=diagonal([-1]*4);q=[[F(i+j+1,100) for j in range(4)] for i in range(4)];g=[F(1),F(1,8),F(8),F(2)]
        self.assertEqual(law.majorant(c,q,g),law.majorant(c,q,[7*v for v in g]))
        for bad in ([],[F(0),*g[1:]],[F(-1),*g[1:]]):
            with self.assertRaises(ValueError):law.majorant(c,q,bad)
        for bad in ([],[[F(-1) if i==j else q[i][j] for j in range(4)] for i in range(4)],
                    [[q[i][j]+F(i==0 and j==1) for j in range(4)] for i in range(4)]):
            with self.assertRaises(ValueError):law.majorant(c,bad,g)
        with self.assertRaises(ValueError):law.majorant([[F(i==0 and j==1) for j in range(4)] for i in range(4)],q,g)

    def test_weighted_majorant_psd_at_all_1024_symmetric_vertices(self):
        q=[[F(i+j+1,100) for j in range(4)] for i in range(4)];g=[F(1),F(1,8),F(8),F(2)]
        rows,u=law.majorant(diagonal([0]*4),q,g);positions=[(i,j) for i in range(4) for j in range(i,4)];count=0
        for signs in product((-1,1),repeat=10):
            delta=diagonal([0]*4)
            for (i,j),sign in zip(positions,signs):delta[i][j]=delta[j][i]=sign*q[i][j]
            difference=[[u[i][j]-delta[i][j] for j in range(4)] for i in range(4)]
            for k in range(1,5):
                for idx in combinations(range(4),k):self.assertGreaterEqual(exact_det([[difference[i][j] for j in idx] for i in idx]),0)
            count+=1
        self.assertEqual(count,1024);self.assertNotEqual(rows,[sum(row,F(0)) for row in q])

    def test_disparate_diagonal_family_certifies_contraction_and_all_vertices(self):
        p=diagonal([1,100,1,1]);metric=dict(accepted=True,metric=law.prior.prior.pack(p),inverse_metric=law.prior.prior.pack(law.prior.prior.invert(p)),rounded_pd_proof=ldlt(p),time_scale_per_s='1')
        b=point(diagonal([-3]*4));b[0][1]=(F(-10),F(10));b[1][0]=(F(-1,10),F(1,10))
        isotropic=law.prior.prior.rate(metric,b);directed=law.prior.rate(metric,b,isotropic);prepared=law.prior.basis(metric)
        cert=law.rate(prepared,directed);alpha=F(cert['mu_metric_upper_per_s'])
        self.assertGreater(F(directed['mu_metric_upper_per_s']),0);self.assertLess(alpha,0)
        self.assertTrue(cert['internal_time_varying_contraction_certified']);self.assertTrue(cert['strictly_narrower'])
        for ends in product((0,1),repeat=2):
            v=diagonal([-3]*4);v[0][1]=b[0][1][ends[0]];v[1][0]=b[1][0][ends[1]]
            pb=law.prior.multiply(p,v);s=[[(pb[i][j]+pb[j][i])/2 for j in range(4)] for i in range(4)]
            self.assertTrue(ldlt([[alpha*p[i][j]-s[i][j] for j in range(4)] for i in range(4)])['positive_definite'])
        self.assertFalse(cert['lower_is_actual_log_norm_bound']);self.assertTrue(cert['same_metric_intersection'])
        for change in (dict(metric_changed=True),dict(same_metric_intersection=False),dict(final_raw_upper_ldlt=dict(positive_definite=False))):
            with self.assertRaises(ValueError):law.rate(prepared,directed|change)
        with self.assertRaises(ValueError):law.rate(prepared,directed,law.balance(prepared)|dict(basis_sha256='wrong'))
        with self.assertRaises(ValueError):law.rate(prepared|dict(time_scale_per_s='0'),directed)

    def test_all_48_certificates_and_1584_exact_queries_replay(self):
        old=read(producer.prior.OUTPUT);queries=0
        for c in self.report['cases']:
            previous=old['cases'][c['source_directed_case_index']]
            self.assertEqual(c['metric_candidate_sha256'],previous['metric_candidate_sha256']);self.assertEqual(c['metric_accepted'],previous['metric_accepted'])
            if not c['metric_accepted']:
                self.assertIsNone(c['balance']);self.assertEqual(c['cells'],[]);continue
            prepared=previous['basis'];self.assertEqual(c['balance'],law.balance(prepared))
            self.assertEqual(len(c['cells']),8)
            for record in c['cells']:
                previous_cert=previous['cells'][record['source_cell_index']]['rate_certificate'];cert=record['rate_certificate']
                self.assertEqual(cert,law.rate(prepared,previous_cert,c['balance']))
                self.assertEqual(cert['center_radius_sha256'],law.box.digest(dict(center=previous_cert['center'],radius=previous_cert['radius'])))
                self.assertEqual(cert['balance_sha256'],law.box.digest(c['balance']))
                d=list(map(F,prepared['diagonal']));u=[[F(v) for v in row] for row in cert['surrogate_upper']];lo=F(cert['seed_lower_normalized']);hi=F(cert['seed_upper_normalized'])
                for index,probe in enumerate(cert['probes']):
                    alpha=hi if index==0 else (lo+hi)/2;self.assertEqual(alpha,F(probe['alpha_normalized']))
                    proof=ldlt([[alpha*d[j]*F(j==k)-u[j][k] for k in range(4)] for j in range(4)])
                    self.assertEqual(proof['positive_definite'],probe['positive_definite']);self.assertEqual(proof['failed_at'],probe['failed_at']);self.assertEqual(law.box.digest(proof['pivots']),probe['pivot_sha256'])
                    if index:
                        if proof['positive_definite']:hi=alpha
                        else:lo=alpha
                self.assertEqual(hi,F(cert['raw_upper_normalized']));self.assertEqual(lo,F(cert['surrogate_lower_normalized']))
                self.assertEqual(cert['final_raw_upper_ldlt'],ldlt([[hi*d[j]*F(j==k)-u[j][k] for k in range(4)] for j in range(4)]))
                self.assertTrue(cert['final_raw_upper_ldlt']['positive_definite'])
                self.assertEqual(F(cert['raw_mu_metric_upper_per_s']),hi*F(prepared['time_scale_per_s']))
                self.assertEqual(F(cert['mu_metric_upper_per_s']),min(hi*F(prepared['time_scale_per_s']),F(previous_cert['mu_metric_upper_per_s'])))
                queries+=len(cert['probes'])
        self.assertEqual(queries,1584);self.assertEqual(queries,self.report['exact_rate_ldlt_queries'])

    def test_unchanged_conversions_forcing_anchor_and_all_propagations(self):
        old=read(producer.prior.OUTPUT);metric=read(producer.prior.prior.OUTPUT);modal=read(producer.prior.prior.prior.OUTPUT);rms=read(producer.prior.prior.prior.prior.prior.OUTPUT)
        for c in self.report['cases']:
            previous=old['cases'][c['source_directed_case_index']];self.assertEqual(c['support_sha256'],previous['support_sha256']);self.assertEqual(c['weights'],previous['weights']);self.assertTrue(c['binary_backward_gate_still_rejected'])
            if not c['metric_accepted']:
                self.assertIsNone(c['propagation']);self.assertIsNone(c['peak_node_budget_nonincreasing']);continue
            fixed=metric['cases'][previous['source_metric_case_index']];source=modal['cases'][fixed['source_modal_case_index']];cells=[]
            for record in c['cells']:
                i=record['source_cell_index'];original=fixed['cells'][i]['metrics'];metrics=law.refine_metrics(original,record['rate_certificate'])
                self.assertEqual(metrics['comparison_per_s'],record['comparison_per_s'])
                for key,value in original.items():
                    if key!='comparison_per_s':self.assertEqual(metrics[key],value)
                for j in range(6):
                    for k in range(6):
                        if (j,k)!=(5,5):self.assertEqual(metrics['comparison_per_s'][j][k],previous['cells'][i]['comparison_per_s'][j][k])
                forcing=rms['cases'][source['source_spectral_case_index']]['cells'][i]['forcing_inputs'];cells.append(dict(forcing_inputs=forcing,metrics=metrics))
            self.assertEqual(producer.prior.prior.law.propagate(cells),c['propagation'])
            self.assertEqual(c['peak_node_budget_nonincreasing'],F(c['propagation']['peak_zero_anchor_node_upper_v'])<=F(previous['propagation']['peak_zero_anchor_node_upper_v']))
            self.assertEqual(c['all_internal_cells_contracting'],all(v['rate_certificate']['internal_time_varying_contraction_certified'] for v in c['cells']))

    def test_storage_sources_destinations_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();s=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-junction-balanced/v1');self.assertEqual(len(r['cases']),8)
        self.assertEqual(len(raw),s['bytes']);self.assertEqual(sha(raw),s['compressed_sha256']);self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),s['canonical_json_sha256'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        for flag in ('only_junction_diagonal_changed','prior_metric_components_reused_by_reference','proof_weights_constant_within_each_interval'):self.assertTrue(r[flag])
        self.assertEqual(r['initial_anchor_reference'],'common weighted infinity');self.assertEqual(r['balance_bits'],40)
        for flag in ('metric_changed','norm_changed','anchor_changed','proof_weights_fitted_to_results','weights_changed','block_partition_changed','metric_common_across_all_intervals',
                     'complete_coupled_contraction_certified','nonlinear_remainder_bound','initial_error_known','actual_dae_error_bound',
                     'full_path_coverage','temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(r[flag],flag)
        self.assertEqual(r['new_metric_candidates'],0);self.assertEqual(r['new_circuit_inverse_systems'],0);self.assertEqual(r['new_nonlinear_circuit_solves'],0)

if __name__=='__main__':unittest.main()
