from fractions import Fraction as F
from itertools import product,combinations
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_junction_directed as law
import loudness_latch_bdf_static_precision_junction_directed as producer
from loudness_latch_spectral_junction import ldlt
from loudness_latch_bdf_doubling_survey import canonical

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def point(a):return [[(F(v),F(v)) for v in row] for row in a]
def diagonal(values):return [[F(v) if i==j else F(0) for j in range(4)] for i,v in enumerate(values)]
def quadratic(a,x):return sum((F(x[i])*a[i][j]*x[j] for i in range(len(x)) for j in range(len(x))),F(0))
def exact_det(a):
    # Independent pivoted elimination for all principal minors, including zeros.
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

class JunctionDirected(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_exact_congruence_norm_compiled_cancellation_and_guards(self):
        l=diagonal([1]*4);l[1][0]=F(1);p=law.multiply(l,law.transpose(l))
        metric=dict(accepted=True,metric=law.prior.pack(p),rounded_pd_proof=ldlt(p),time_scale_per_s='1')
        basis=law.basis(metric);r=[[F(v) for v in row] for row in basis['inverse_lower']];d=list(map(F,basis['diagonal']))
        self.assertEqual(law.multiply(l,r),diagonal([1]*4));self.assertEqual(law.multiply(law.multiply(r,p),law.transpose(r)),diagonal(d))
        x=[F(1,3),F(-2),F(4,5),F(1)];y=[sum((l[k][i]*x[k] for k in range(4)),F(0)) for i in range(4)]
        self.assertEqual(quadratic(p,x),quadratic(diagonal(d),y))
        b=point(diagonal([-1,-2,-3,-4]));b[1][0]=(F(-10),F(10));out=law.enclosure(basis,b)
        t=[[tuple(map(F,v)) for v in row] for row in out['transformed_symmetric_intervals']]
        self.assertEqual(t[0][1][0],t[0][1][1]) # Its compiled coefficient of B[1,0] is exactly zero.
        for end in (F(-10),F(0),F(10)):
            v=diagonal([-1,-2,-3,-4]);v[1][0]=end
            pb=law.multiply(p,v);s=[[(pb[i][j]+pb[j][i])/2 for j in range(4)] for i in range(4)]
            exact=law.multiply(law.multiply(r,s),law.transpose(r))
            for i in range(4):
                for j in range(4):self.assertLessEqual(t[i][j][0],exact[i][j]);self.assertGreaterEqual(t[i][j][1],exact[i][j])
        with self.assertRaises(ValueError):law.basis(metric|dict(accepted=False))
        bad=metric|dict(rounded_pd_proof=dict(metric['rounded_pd_proof'],pivots=['0']))
        with self.assertRaises(ValueError):law.basis(bad)
        with self.assertRaises(ValueError):law.enclosure(basis,[])
        complete=law.prior.candidate([point(diagonal([-1,-2,-3,-4]))]);old=law.prior.rate(complete,point(diagonal([-1,-2,-3,-4])))
        with self.assertRaises(ValueError):law.rate(complete,point(diagonal([-1,-2,-3,-4])),old,basis)

    def test_directed_majorant_psd_at_all_1024_symmetric_vertices(self):
        radius=[[F(i+j+1,100) for j in range(4)] for i in range(4)];rows=[sum(v,F(0)) for v in radius]
        positions=[(i,j) for i in range(4) for j in range(i,4)];count=0
        for signs in product((-1,1),repeat=10):
            delta=[[F(0) for _ in range(4)] for _ in range(4)]
            for (i,j),sign in zip(positions,signs):delta[i][j]=delta[j][i]=sign*radius[i][j]
            difference=[[rows[i]*F(i==j)-delta[i][j] for j in range(4)] for i in range(4)]
            for k in range(1,5):
                for idx in combinations(range(4),k):self.assertGreaterEqual(exact_det([[difference[i][j] for j in idx] for i in idx]),0)
            count+=1
        self.assertEqual(count,1024);self.assertNotEqual(rows[0],rows[-1])

    def test_rate_uncertainty_vertices_same_metric_intersection_and_units(self):
        a=diagonal([-1,-1,-2,-3]);a[0][1]=F(4);b=point(a);positions=[(i,j) for i in range(2) for j in range(2)]
        for i,j in positions:b[i][j]=(a[i][j]-F(1,100),a[i][j]+F(1,100))
        m=law.prior.candidate([b]);old=law.prior.rate(m,b);cert=law.rate(m,b,old)
        self.assertLess(F(cert['mu_metric_upper_per_s']),0);self.assertEqual(F(cert['mu_metric_upper_per_s']),min(F(cert['raw_mu_metric_upper_per_s']),F(old['mu_metric_upper_per_s'])))
        p=[[F(v) for v in row] for row in m['metric']];alpha=F(cert['raw_mu_metric_upper_per_s'])
        for ends in product((0,1),repeat=4):
            v=[row[:] for row in a]
            for (i,j),end in zip(positions,ends):v[i][j]=b[i][j][end]
            pb=law.multiply(p,v);s=[[(pb[i][j]+pb[j][i])/2 for j in range(4)] for i in range(4)]
            self.assertTrue(ldlt([[alpha*p[i][j]-s[i][j] for j in range(4)] for i in range(4)])['positive_definite'])
        self.assertFalse(cert['lower_is_actual_log_norm_bound']);self.assertTrue(cert['same_metric_intersection'])
        with self.assertRaises(ValueError):law.rate(m,b,old|dict(metric_constant_within_interval=False))
        with self.assertRaises(ValueError):law.rate(m,b,old,law.basis(m)|dict(time_scale_per_s='0'))

    def test_all_48_certificates_and_1584_queries_replay(self):
        old=read(producer.prior.OUTPUT);modal=read(producer.prior.prior.OUTPUT);queries=0
        for c in self.report['cases']:
            previous=old['cases'][c['source_metric_case_index']];fixed=previous['metric_candidate']
            self.assertEqual(c['metric_candidate_sha256'],law.box.digest(fixed));self.assertEqual(c['metric_accepted'],fixed['accepted'])
            if not fixed['accepted']:
                self.assertIsNone(c['basis']);self.assertEqual(c['cells'],[]);continue
            prepared=law.basis(fixed);self.assertEqual(prepared,c['basis']);source=modal['cases'][previous['source_modal_case_index']]
            self.assertEqual(len(c['cells']),8)
            for record in c['cells']:
                i=record['source_cell_index'];generator=source['cells'][i]['result']['generator_intervals_per_s']
                cert=law.rate(fixed,generator,previous['cells'][i]['rate_certificate'],prepared);self.assertEqual(cert,record['rate_certificate'])
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
                self.assertTrue(cert['final_raw_upper_ldlt']['positive_definite']);queries+=len(cert['probes'])
        self.assertEqual(queries,1584);self.assertEqual(queries,self.report['exact_rate_ldlt_queries'])

    def test_unchanged_conversions_forcing_anchor_and_all_propagations(self):
        old=read(producer.prior.OUTPUT);modal=read(producer.prior.prior.OUTPUT);rms=read(producer.prior.prior.prior.prior.OUTPUT)
        for c in self.report['cases']:
            previous=old['cases'][c['source_metric_case_index']];self.assertEqual(c['support_sha256'],previous['support_sha256']);self.assertEqual(c['weights'],previous['weights']);self.assertTrue(c['binary_backward_gate_still_rejected'])
            if not c['metric_accepted']:
                self.assertIsNone(c['propagation']);self.assertIsNone(c['peak_node_budget_nonincreasing']);continue
            source=modal['cases'][previous['source_modal_case_index']];cells=[]
            for record in c['cells']:
                i=record['source_cell_index'];original=previous['cells'][i]['metrics'];metrics=law.refine_metrics(original,record['rate_certificate'])
                self.assertEqual(metrics['comparison_per_s'],record['comparison_per_s'])
                for key,value in original.items():
                    if key!='comparison_per_s':self.assertEqual(metrics[key],value)
                for j in range(6):
                    for k in range(6):
                        if (j,k)!=(5,5):self.assertEqual(metrics['comparison_per_s'][j][k],original['comparison_per_s'][j][k])
                forcing=rms['cases'][source['source_spectral_case_index']]['cells'][i]['forcing_inputs'];cells.append(dict(forcing_inputs=forcing,metrics=metrics))
            self.assertEqual(producer.prior.law.propagate(cells),c['propagation'])
            self.assertEqual(c['peak_node_budget_nonincreasing'],F(c['propagation']['peak_zero_anchor_node_upper_v'])<=F(previous['propagation']['peak_zero_anchor_node_upper_v']))
            self.assertEqual(c['all_internal_cells_contracting'],all(v['rate_certificate']['internal_time_varying_contraction_certified'] for v in c['cells']))

    def test_storage_sources_destinations_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();s=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-junction-directed/v1');self.assertEqual(len(r['cases']),8)
        self.assertEqual(len(raw),s['bytes']);self.assertEqual(sha(raw),s['compressed_sha256']);self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),s['canonical_json_sha256'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        self.assertTrue(r['only_junction_diagonal_changed']);self.assertTrue(r['prior_metric_components_reused_by_reference']);self.assertEqual(r['initial_anchor_reference'],'common weighted infinity')
        for flag in ('metric_changed','norm_changed','weights_changed','block_partition_changed','metric_common_across_all_intervals',
                     'complete_coupled_contraction_certified','nonlinear_remainder_bound','initial_error_known','actual_dae_error_bound',
                     'full_path_coverage','temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(r[flag],flag)
        self.assertEqual(r['new_metric_candidates'],0);self.assertEqual(r['new_circuit_inverse_systems'],0);self.assertEqual(r['new_nonlinear_circuit_solves'],0)

if __name__=='__main__':unittest.main()
