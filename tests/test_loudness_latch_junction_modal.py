from fractions import Fraction as F
from itertools import product
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_junction_modal as law
import loudness_latch_bdf_static_precision_junction_modal as producer
from loudness_latch_cell_propagation import structured_inverse
from loudness_latch_spectral_junction import spectral_bound
from loudness_latch_charge_enclosure import exp_bounds
from loudness_latch_bdf_doubling_survey import canonical

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def point(a):return [[(F(v),F(v)) for v in row] for row in a]
def diagonal(values):return [[F(v) if i==j else F(0) for j in range(4)] for i,v in enumerate(values)]
def factors(roots):
    c=[F(1)]
    for r in roots:
        out=[F(0)]*(len(c)+1)
        for i,v in enumerate(c):out[i]+=v;out[i+1]-=F(r)*v
        c=out
    return c
def exact_det(a):
    # Independent row-pivoted elimination, not principal-minor/permutation code.
    a=[[F(v) for v in row] for row in a];out=F(1);n=len(a)
    for k in range(n):
        pivot=next((i for i in range(k,n) if a[i][k]),None)
        if pivot is None:return F(0)
        if pivot!=k:a[k],a[pivot]=a[pivot],a[k];out=-out
        p=a[k][k];out*=p
        for i in range(k+1,n):
            ratio=a[i][k]/p
            for j in range(k+1,n):a[i][j]-=ratio*a[k][j]
    return out

class JunctionModal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_interval_arithmetic_singular_and_domain_guards(self):
        self.assertEqual(law.mul((F(-2),F(3)),(F(-5),F(-1))),(F(-15),F(10)))
        self.assertEqual(law.div((F(1),F(2)),(F(-4),F(-2))),(F(-1),F(-1,4)))
        for d in ((F(-1),F(1)),(F(0),F(1)),(F(0),F(0))):
            with self.assertRaises(ValueError):law.div(law.ONE,d)
        for c in ((1,0,2,0,1),(1,1,1,1,1),(1,2,3,4,0)):
            r=law.routh([(F(v),F(v)) for v in c]);self.assertIsNone(r['right_half_plane_roots']);self.assertIsNotNone(r['blocked'])
        with self.assertRaises(ValueError):law.interval((1,0))
        with self.assertRaises(ValueError):law.characteristic([])
        with self.assertRaises(ValueError):law.routh([law.ONE]*4)
        with self.assertRaises(ValueError):law.routh([(F(2),F(2))]+[law.ONE]*4)
        with self.assertRaises(ValueError):law.generator(point(diagonal([-1,-2,-3,-4])),[1,1,0,1])

    def test_known_real_complex_roots_and_independent_polynomial_identity(self):
        for count in range(5):
            roots=[i+1 if i<count else -(i+1) for i in range(4)];a=point(diagonal(roots));c=law.characteristic(a)
            self.assertEqual(c,[(v,v) for v in factors(roots)])
            r=law.routh(c);self.assertEqual(r['right_half_plane_roots'],count);self.assertTrue(r['imaginary_axis_excluded'])
        # Two conjugate pairs: +1 +/-2i and -3 +/-4i. Companion keeps coefficients exact.
        coefficients=[1,4,18,-20,125]
        a=[[0,0,0,-125],[1,0,0,20],[0,1,0,-18],[0,0,1,-4]]
        c=law.characteristic(point(a));self.assertEqual(c,[(F(v),F(v)) for v in coefficients])
        self.assertEqual(law.routh(c)['right_half_plane_roots'],2)
        # Published Illinois quartic example, independent known RHP count.
        self.assertEqual(law.routh([(F(v),F(v)) for v in (1,4,1,2,3)])['right_half_plane_roots'],2)
        matrix=[[F((i+1)*(j+2)%7-3,3) for j in range(4)] for i in range(4)]
        c=law.characteristic(point(matrix))
        for z in (F(-3),F(0),F(1,2),F(7)):
            value=sum((c[k][0]*z**(4-k) for k in range(5)),F(0))
            self.assertEqual(value,exact_det([[z*(i==j)-matrix[i][j] for j in range(4)] for i in range(4)]))

    def test_stable_nonnormal_transient_and_switched_scope_counterexample(self):
        a=diagonal([-1,-1,-2,-3]);a[0][1]=F(4)
        self.assertEqual(law.analyze(point(a))['routh_certificate']['right_half_plane_roots'],0)
        s=[[(a[i][j]+a[j][i])/2 for j in range(4)] for i in range(4)]
        self.assertGreater(F(spectral_bound(point(s))['lambda_lower_per_s']),0)
        # Frozen exp(A t): exp(-t)*[[1,4t],[0,1]], direction e2 at t=1 grows.
        e=exp_bounds(F(-2));self.assertGreater(17*e[0],1)
        # Swap upper/lower triangular blocks each second. Both spectra are negative.
        swapped=[row[:] for row in a];swapped[0][1]=0;swapped[1][0]=4
        self.assertEqual(law.analyze(point(swapped))['routh_certificate']['right_half_plane_roots'],0)
        # One-period product is e^-2 [[1,4],[4,17]]; trace>2 and det=e^-4<1.
        # Its monic quadratic at 1 is negative, hence an eigenvalue >1.
        self.assertLess(1-18*e[0]+exp_bounds(F(-4))[1],0)
        self.assertFalse(law.analyze(point(a))['time_varying_stability_certified'])

    def test_interval_uncertainty_all_diagonal_vertices_and_center_only_failure(self):
        b=point(diagonal([-1,-2,-3,-4]))
        for i in range(4):b[i][i]=(b[i][i][0]-F(1,10),b[i][i][1]+F(1,10))
        c=law.characteristic(b);self.assertEqual(law.routh(c)['right_half_plane_roots'],0)
        for ends in product((0,1),repeat=4):
            vertex=diagonal([b[i][i][ends[i]] for i in range(4)]);coeff=law.characteristic(point(vertex))
            for enclosed,exact in zip(c,coeff):self.assertLessEqual(enclosed[0],exact[0]);self.assertGreaterEqual(enclosed[1],exact[1])
            self.assertEqual(law.routh(coeff)['right_half_plane_roots'],0)
        uncertain=point(diagonal([-1,-2,-3,-4]));uncertain[0][0]=(F(-3),F(1))
        result=law.analyze(uncertain);self.assertIsNone(result['routh_certificate']['right_half_plane_roots'])
        self.assertFalse(result['center_only_bound'])
        self.assertEqual(law.analyze(point(diagonal([1,-2,-3,-4])))['routh_certificate']['right_half_plane_roots'],1)

    def test_all_signed_cells_replay_and_full_neumann_slice_identity(self):
        source=read(producer.weighted.OUTPUT);rms=read(producer.prior.prior.OUTPUT);spectral=read(producer.prior.OUTPUT);counts=[]
        for c in self.report['cases']:
            old=source['cases'][c['source_weighted_case_index']];r=rms['cases'][c['source_spectral_case_index']];s=spectral['cases'][c['source_spectral_case_index']]
            self.assertEqual(c['support_sha256'],old['support_sha256']);self.assertEqual(c['weights'],old['weights'])
            q=max(F(v['contraction_upper']) for v in old['ideal_temporal_cover'])
            self.assertEqual(len(c['cells']),8);self.assertTrue(c['binary_backward_gate_still_rejected'])
            for record in c['cells']:
                i=record['source_cell_index'];cover=old['ideal_temporal_cover'][i]
                inverse=law.inverse_slice(old['inverse_binary'],old['inverse_certificate']['column_scales'],cover,q,range(115,119))
                if c['window']=='prefix' and c['subdivisions']==2 and i==0:
                    full,_=structured_inverse(old['inverse_binary'],old['inverse_certificate']['column_scales'],cover,q)
                    self.assertEqual(inverse,[[full[j][k] for k in range(115,119)] for j in range(115,119)])
                b=law.generator(inverse,old['weights'][21:]);self.assertEqual(law.analyze(b),record['result'])
                symmetric=[[law.mul(law.add(b[j][k],b[k][j]),(F(1,2),F(1,2))) for k in range(4)] for j in range(4)]
                self.assertEqual(law.pack(symmetric),r['cells'][i]['metrics']['junction_symmetric_intervals'])
                for endpoint in ('lower','upper'):self.assertEqual(record['mu2_'+endpoint+'_per_s'],s['cells'][i]['spectral_certificate']['lambda_'+endpoint+'_per_s'])
                counts.append(record['result']['routh_certificate']['right_half_plane_roots'])
        self.assertEqual(counts.count(0),48);self.assertEqual(counts.count(1),16);self.assertNotIn(None,counts)

    def test_storage_sources_destinations_and_frozen_only_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-junction-modal/v1');self.assertEqual(len(r['cases']),8)
        self.assertEqual(len(raw),storage['bytes']);self.assertEqual(sha(raw),storage['compressed_sha256'])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        self.assertTrue(r['isolated_frozen_generator_only']);self.assertTrue(r['all_interval_coefficients_enclosed'])
        for key in ('norm_changed','weights_changed','prior_propagation_modified','time_varying_stability_certified','complete_25_memory_modal_certificate',
                    'nonlinear_remainder_bound','initial_error_known','actual_dae_error_bound','full_path_coverage','physical_trajectory_bound',
                    'temporal_error_bound_admitted','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(r[key],key)
        self.assertEqual(r['new_exact_linear_systems'],0);self.assertEqual(r['new_nonlinear_circuit_solves'],0)
        for c in r['cases']:
            for cell in c['cells']:
                certificate=cell['result']['routh_certificate']
                self.assertEqual(certificate['positive_real_root_certified'],c['window']=='reset')
                self.assertEqual(certificate['all_frozen_matrices_hurwitz'],c['window']!='reset')

if __name__=='__main__':unittest.main()
