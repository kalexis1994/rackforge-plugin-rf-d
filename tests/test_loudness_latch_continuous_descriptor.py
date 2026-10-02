from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import gzip,json,hashlib
from pathlib import Path
import sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_continuous_descriptor as law
import loudness_latch_bdf_static_precision_descriptor_certificate as producer
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_bdf_rational_solve import solve as exact_solve
import loudness_latch_bdf_static_precision_dense_charge as dense


def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(raw):return hashlib.sha256(raw).hexdigest()


class ContinuousDescriptor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_manufactured_rc_operator_and_continuous_budget(self):
        g,c,r=F(2),F(1,4),F(3);h=[[g,c],[-F(1),r*c]]
        x,_=exact_solve(h,np.eye(2));errors,cert=law.inverse_certificate(h,x.tolist(),[1,1])
        det=c*(1+g*r);reference=[[r*c/det,-c/det],[1/det,g/det]]
        for i in range(2):
            for j in range(2):self.assertLessEqual(abs(reference[i][j]-F(float(x[i,j]))),errors[i][j])
        self.assertLess(F(cert['contraction_upper']),F(1,10**10))
        dt=F(1,8);rr=F(1,1000);dd=F(1,500);anchor=F(1,100)
        budget=law.frozen_budget(x.tolist(),errors,1,[dt*rr],[dt*dd],[rr],[dd],dt)
        self.assertLess(F(budget['logarithmic_norm_upper_per_s']),0)
        with localcontext() as ctx:
            ctx.prec=120
            dec=lambda v:D(v.numerator)/D(v.denominator)
            b=-g/det;forcing=-rr/det-g*dd/det
            y=dec(anchor)*(dec(b*dt)).exp()+dec(forcing/b)*((dec(b*dt)).exp()-1)
            voltage=(y+dec(dd-r*rr))/dec(1+g*r)
            memory_upper=F(budget['anchor_gain_upper'])*anchor+F(budget['zero_anchor_forced_memory_upper_v'])
            node_upper=F(budget['node_from_memory_gain_upper'])*F(budget['anchor_gain_upper'])*anchor+F(budget['zero_anchor_forced_node_upper_v'])
            self.assertLess(abs(y),dec(memory_upper));self.assertLess(abs(voltage),dec(node_upper))

    def test_manufactured_nonlinear_error_signs(self):
        # Exact two states, arbitrary reconstructed charge/rate and nonzero d.
        vr=F(1,3);ev=F(1,7);ve=vr+ev;scale=F(1,8)
        current=lambda v:v**3+2*v
        charge=lambda v:v*v+3*v
        jac=3*vr*vr+2;cap=2*vr+3
        yr=charge(vr)/scale+F(1,11);ye=charge(ve)/scale
        rate_r=F(1,13);rate_e=-current(ve)/scale
        ey=ye-yr;erate=rate_e-rate_r;residual=current(vr)+scale*rate_r
        defect=yr-charge(vr)/scale
        ni=current(ve)-current(vr)-jac*ev;nq=charge(ve)-charge(vr)-cap*ev
        self.assertEqual(jac*ev+scale*erate,-residual-ni)
        self.assertEqual(-cap/scale*ev,-ey-defect+nq/scale)
        self.assertNotEqual(defect,0);self.assertNotEqual(ni,0);self.assertNotEqual(nq,0)

    def test_neumann_enclosure_and_guards(self):
        h=[[F(1),F(0)],[F(0),F(1)]];x=[[F(99,100),F(0)],[F(0),F(99,100)]]
        errors,cert=law.inverse_certificate(h,x,[F(2),F(3)])
        self.assertEqual(F(cert['contraction_upper']),F(1,100))
        for i in range(2):
            for j in range(2):self.assertLessEqual(abs(F(i==j)-x[i][j]),errors[i][j])
        with self.assertRaisesRegex(ValueError,'contraction'):law.inverse_certificate(h,[[0,0],[0,0]],[1,1])
        with self.assertRaisesRegex(ValueError,'positive scales'):law.inverse_certificate(h,x,[0,1])
        with self.assertRaisesRegex(ValueError,'complete'):law.inverse_certificate(h,[[0]],[1,1])
        with self.assertRaisesRegex(ValueError,'positive duration'):law.frozen_budget(h,[[F(0)]*2]*2,1,[0],[0],[0],[0],0)
        # A frozen expansive scalar exceeds the declared exponential domain.
        budget=law.frozen_budget([[1,0],[0,-5000]],[[F(0)]*2]*2,1,[0],[0],[0],[0],1)
        self.assertFalse(budget['growth_supported'])
        self.assertNotIn('anchor_gain_upper',budget)

    def test_all_eight_continuous_stamps_and_history_replay(self):
        network=dense.CompensatedBdfNetwork(200,dense.model_parameters(1,'finite_transit'));g=dense.curvature.graph(network,10.)
        source=read(dense.previous.proxy.REFERENCE)['windows']
        refs={(w['name'],l['reference']['subdivisions']):l['reference'] for w in source for l in w['levels']}
        for case in self.report['cases']:
            prepared=dense.prepare(network,refs[case['window'],case['subdivisions']],31)
            self.assertEqual(prepared['support_sha256'],case['support_sha256'])
            with localcontext() as ctx:
                ctx.prec=120;x=[dense.law.decimal_fraction(dense.poly.evaluate(p,F(1,2))) for p in prepared['x']]
            self.assertEqual(list(map(str,x)),case['node_query_v'])
            h,meta=law.descriptor(network,g,x,100)
            self.assertEqual([[float(v) for v in row] for row in h],case['descriptor_binary'])
            self.assertEqual(meta,case['metadata']);self.assertTrue(case['decimal80_100_rounded_descriptor_equal'])
            self.assertEqual(law.exact_rank(np.array(meta['incidence_columns']).T.tolist())['rank'],25)
            # Ideal linear constraints and physical series branch are explicit.
            self.assertEqual(F(meta['rc_time_constants_s'][17]),F(network.network.branches[17][3])*F(25500))
            self.assertEqual(sum(F(v)!=0 for v in meta['rc_time_constants_s']),1)
            for k,(left,right,_,cap,resistance) in enumerate(network.network.branches):
                for i in range(94):
                    a=F(i==left)-F(i==right)
                    self.assertEqual(h[94+k][i],-D(a.numerator)/D(a.denominator))
                    self.assertEqual(h[i][94+k],D.from_float(cap)*int(a))
            forcing=case['forcing_inputs']
            expected=[str(max(map(abs,dense.poly.bernstein(p)))) for p in prepared['equations']]+['0']*4
            self.assertEqual(forcing['constraint_point_v'],expected)

    def test_all_certificates_budgets_and_rejected_binary_witnesses(self):
        self.assertEqual(len(self.report['cases']),8)
        for c in self.report['cases']:
            self.assertIsNone(c['failure']);self.assertFalse(c['backward_gate_passed'])
            self.assertTrue(c['exact_solve']['exact_rational_residual_zero'])
            self.assertGreater(c['backward_errors']['binary_componentwise_backward_error'],1e-10)
            self.assertLess(c['backward_errors']['decimal80_componentwise_backward_error'],1e-10)
            h=c['descriptor_binary'];x=c['inverse_binary'];cert=c['inverse_certificate']
            errors,replay=law.inverse_certificate(h,x,cert['column_scales'])
            self.assertEqual(replay,cert);self.assertLess(F(cert['contraction_upper']),F(1,10**10))
            v=c['forcing_inputs']
            budget=law.frozen_budget(x,errors,94,*[list(map(F,v[k])) for k in (
                'nodal_l1_c','constraint_l1_v_s','nodal_point_a','constraint_point_v')],F(c['duration_s']))
            self.assertEqual(budget,c['frozen_budget']);self.assertTrue(budget['growth_supported'])
            witness=producer.backward_witness(np.array(h),np.array(x))
            self.assertEqual(witness,c['binary_backward_witness'])
            self.assertLess(F(witness['exact_componentwise_ratio']),F(1,10**10))
            self.assertGreater(witness['binary_ratio'],1e-10)
            self.assertFalse(budget['initial_memory_error_known'])
            self.assertFalse(budget['time_varying_operator_bound']);self.assertFalse(budget['nonlinear_remainder_bound'])

    def test_frozen_inputs_canonical_storage_and_scope(self):
        report=self.report
        self.assertEqual(report['schema'],'rf-d/bdf-static-descriptor-certificate/v1')
        for p,h in report['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        storage=json.loads(producer.SUMMARY.read_text())['storage'];raw=producer.OUTPUT.read_bytes()
        self.assertEqual(len(raw),storage['bytes']);self.assertEqual(sha(raw),storage['compressed_sha256'])
        self.assertEqual(gzip.decompress(raw),canonical(report));self.assertEqual(sha(canonical(report)),storage['canonical_json_sha256'])
        self.assertFalse(report['rounded_inverse_numerically_admitted']);self.assertTrue(report['rejected_binary_gate_preserved'])
        self.assertEqual(report['new_exact_linear_systems'],0);self.assertEqual(report['new_nonlinear_circuit_solves'],0)
        for key in ('actual_time_varying_propagation_bound','full_path_coverage','temporal_error_bound_admitted',
                    'physical_trajectory_bound','audio_admitted','deadline_admitted','coefficient_matrix_changed','numerical_gates_changed'):
            self.assertFalse(report[key],key)
        floating=read(producer.prior.prior.OUTPUT);exact=read(producer.prior.OUTPUT)
        self.assertEqual(len(floating['cases']),8);self.assertEqual(len(exact['cases']),8)
        for a,b,c in zip(floating['cases'],exact['cases'],report['cases']):
            self.assertIsNotNone(a['failure']);self.assertIsNotNone(b['failure'])
            self.assertEqual(c['prior_failure'],a['failure']);self.assertEqual(c['rounded_inverse_failure'],b['failure'])
            self.assertEqual(a['descriptor_binary'],b['descriptor_binary']);self.assertEqual(b['descriptor_binary'],c['descriptor_binary'])


if __name__=='__main__':unittest.main()
