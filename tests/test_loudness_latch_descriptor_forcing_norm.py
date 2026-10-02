from fractions import Fraction as F
import gzip,json,hashlib
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_descriptor_forcing_budget as law
import loudness_latch_bdf_static_precision_descriptor_forcing_norm as producer
from loudness_latch_bdf_doubling_survey import canonical


def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()


class ForcingNorm(unittest.TestCase):
    def test_disjoint_forcing_counterexample_and_column_bound(self):
        # f1=2 on [0,1/2], f2=2 on [1/2,1]: each row L1=1, norm L1=2.
        x=[[F(1),0,0,0],[0,F(1),0,0],[-F(1),0,0,0],[0,-F(1),0,0]]
        errors=[[F(0)]*4 for _ in range(4)]
        corrected=law.frozen_budget(x,errors,2,[F(1),F(1)],[0,0],[2,2],[0,0],1)
        row_integrals=[F(2)*F(1,2),F(2)*F(1,2)]
        norm_integral=F(2)*F(1,2)+F(2)*F(1,2)
        self.assertEqual(F(corrected['previous_row_integral_max_v']),max(row_integrals))
        self.assertEqual(F(corrected['integrated_forcing_norm_upper_v']),norm_integral)
        self.assertGreater(norm_integral,max(row_integrals))
        self.assertEqual(F(corrected['zero_anchor_forced_memory_upper_v']),2)
        self.assertFalse(corrected['row_integral_max_is_norm_integral_bound'])
        self.assertFalse(corrected['prior_uniform_budget_admitted'])
        with self.assertRaisesRegex(ValueError,'nonnegative'):law.forcing_norm_budget([[1,0],[0,1]],1,[-1],[0])
        with self.assertRaisesRegex(ValueError,'complete'):law.forcing_norm_budget([[1,0],[0,1]],1,[],[0])

    def test_single_rc_column_budget_independently(self):
        g,c,r=F(2),F(1,4),F(3);det=c*(1+g*r)
        inverse=[[r*c/det,-c/det],[1/det,g/det]];errors=[[F(0)]*2 for _ in range(2)]
        dt=F(1,8);rr=F(1,1000);dd=F(1,500)
        result=law.frozen_budget(inverse,errors,1,[dt*rr],[dt*dd],[rr],[dd],dt)
        expected=dt*(rr+g*dd)/det
        self.assertEqual(F(result['integrated_forcing_norm_upper_v']),expected)
        self.assertEqual(F(result['previous_row_integral_max_v']),expected)
        self.assertEqual(F(result['zero_anchor_forced_memory_upper_v']),expected)
        self.assertEqual(F(result['anchor_gain_upper']),1)

    def test_eight_corrected_budgets_inherited_certificates_and_storage(self):
        report=read(producer.OUTPUT);prior=read(producer.prior.OUTPUT)
        self.assertEqual(len(report['cases']),8);self.assertFalse(report['prior_uniform_budgets_valid'])
        for a,b in zip(prior['cases'],report['cases']):
            self.assertIsNone(b['failure']);self.assertEqual(a['inverse_certificate'],b['inverse_certificate'])
            self.assertEqual(a['inverse_binary'],b['inverse_binary']);self.assertEqual(a['forcing_inputs'],b['forcing_inputs'])
            cert=b['inverse_certificate'];q=F(cert['contraction_upper'])
            scales=list(map(F,cert['column_scales']));peaks=list(map(F,cert['error_column_peaks']))
            errors=[[q/(1-q)*p/s for p in peaks] for s in scales];v=b['forcing_inputs']
            replay=law.frozen_budget(b['inverse_binary'],errors,94,*[list(map(F,v[k])) for k in (
                'nodal_l1_c','constraint_l1_v_s','nodal_point_a','constraint_point_v')],F(b['duration_s']))
            self.assertEqual(replay,b['frozen_budget'])
            # Independent order: accumulate each forcing column after taking row maximum.
            total=F(0)
            for j,amount in enumerate(map(F,v['nodal_l1_c']+v['constraint_l1_v_s'])):
                peak=max(abs(F(b['inverse_binary'][94+i][j]))+errors[94+i][j] for i in range(25))
                total+=peak*amount
            self.assertEqual(F(replay['integrated_forcing_norm_upper_v']),total)
            self.assertGreaterEqual(total,F(replay['previous_row_integral_max_v']))
            self.assertGreaterEqual(F(replay['zero_anchor_forced_memory_upper_v']),F(a['frozen_budget']['zero_anchor_forced_memory_upper_v']))
            for field in ('logarithmic_norm_upper_per_s','growth_exponent_upper','anchor_gain_upper','node_from_memory_gain_upper','node_direct_forcing_upper_v'):
                self.assertEqual(replay[field],a['frozen_budget'][field])
            self.assertFalse(b['backward_gate_passed']);self.assertIn('max_i integral',b['prior_uniform_budget_rejected_reason'])
        storage=json.loads(producer.SUMMARY.read_text())['storage'];raw=producer.OUTPUT.read_bytes()
        self.assertEqual(len(raw),storage['bytes']);self.assertEqual(sha(raw),storage['compressed_sha256'])
        self.assertEqual(gzip.decompress(raw),canonical(report));self.assertEqual(sha(canonical(report)),storage['canonical_json_sha256'])
        for p,h in report['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        for field in ('rounded_inverse_numerically_admitted','actual_time_varying_propagation_bound','full_path_coverage',
                      'temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted','deadline_admitted'):
            self.assertFalse(report[field],field)
        self.assertEqual(report['new_exact_linear_systems'],0);self.assertEqual(report['new_nonlinear_circuit_solves'],0)


if __name__=='__main__':unittest.main()
