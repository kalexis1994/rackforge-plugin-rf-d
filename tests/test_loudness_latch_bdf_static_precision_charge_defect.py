import gzip,hashlib,json,sys,unittest
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_charge_defect as law
import loudness_latch_bdf_static_precision_charge_defect as experiment
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters
from circuit66_decimal_static import lift

def fraction(value):return F(value['numerator'],value['denominator'])


class ChargeDefect(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.parameters=model_parameters(1,'finite_transit')

    def test_exact_polynomial_identities_independent_cardinal_weights_and_kernel_bound(self):
        self.assertEqual(len(self.report['polynomial_cases']),72)
        for row in self.report['polynomial_cases']:
            h=fraction(row['h_s']);k=fraction(row['k_s']);degree=row['degree']
            weights=law.lagrange_weights((F(0),-h,-h-k));self.assertEqual(weights,law.weights(h,k))
            self.assertEqual(sum(weights),0)
            q=[F(0)]*degree+[F(1)];qprime=law.derivative(q,1)
            direct=sum((w*law.polynomial(t,q) for w,t in zip(weights,(F(0),-h,-h-k))),F(0))-law.polynomial(F(0),qprime)
            self.assertEqual(direct,fraction(row['direct']));self.assertEqual(direct,fraction(row['integral']))
            self.assertTrue(row['exact_identity']);self.assertTrue(row['bound_passed'])
            self.assertLessEqual(abs(direct),fraction(row['bound']))
            if degree<=2:self.assertEqual(direct,0)
            if degree==3:self.assertEqual(direct,-h*(h+k))
            self.assertEqual(law.peano_polynomial(h,k,[F(0),F(0),F(0),F(1,6)]),-h*(h+k)/6)
            for j in range(65):self.assertLessEqual(law.kernel(h,k,-(h+k)*j/64),0)
            offset=F(12345,7)
            shifted=list(q);shifted[0]+=offset
            shifted_direct=sum((w*law.polynomial(t,shifted) for w,t in zip(weights,(F(0),-h,-h-k))),F(0))-law.polynomial(F(0),law.derivative(shifted,1))
            self.assertEqual(shifted_direct,direct)

    def test_exact_be_startup_and_nonzero_cubic_defect(self):
        self.assertEqual(len(self.report['be_cases']),18)
        for row in self.report['be_cases']:
            h=fraction(row['h_s']);degree=row['degree'];q=[F(0)]*degree+[F(1)]
            weights=law.lagrange_weights((F(0),-h))
            direct=sum((w*law.polynomial(t,q) for w,t in zip(weights,(F(0),-h))),F(0))-law.polynomial(F(0),law.derivative(q,1))
            self.assertEqual(direct,fraction(row['direct']));self.assertEqual(direct,fraction(row['integral']))
            if degree<=1:self.assertEqual(direct,0)
            if degree==2:self.assertEqual(direct,-h)

    def test_rc_owned_history_exact_forcing_and_missing_publication_counterexample(self):
        self.assertEqual(len(self.report['rc_cases']),8);count=0;nonzero=0
        for case in self.report['rc_cases']:
            poly=[fraction(v) for v in case['voltage_polynomial']];cap=fraction(case['capacitance_f']);resistance=fraction(case['resistance_ohm'])
            old=poly[0];older=law.polynomial(-F(1,100000),poly);eold=F(0);eolder=F(0);time=F(0)
            for row in case['rows']:
                h=fraction(row['h_s']);k=fraction(row['previous_h_s']);t=fraction(row['time_s'])
                self.assertEqual(t,time+h)
                # Derive weights independently from actual timestamps.
                times=(t,time) if row['method']=='BE' else (t,time,time-k)
                w=law.lagrange_weights(times);dt=1/w[0];gamma=F(0) if row['method']=='BE' else w[2]/w[0]
                exact=law.polynomial(t,poly);velocity=law.polynomial(t,law.derivative(poly,1))
                tau=sum((weight*cap*law.polynomial(x,poly) for weight,x in zip(w,times)),F(0))-cap*velocity
                beta=dt/(dt+cap*resistance);source=exact+resistance*cap*velocity
                virtual=old+gamma*(old-older);published=beta*source+(1-beta)*virtual
                predicted=(1-beta)*(eold+gamma*(eold-eolder))+resistance*beta*tau
                self.assertEqual(published,fraction(row['published_v']));self.assertEqual(exact-published,predicted)
                self.assertEqual(predicted,fraction(row['predicted_error_v']));self.assertEqual(tau,fraction(row['tau_a']))
                self.assertEqual(beta*tau,fraction(row['residual_forcing_a']))
                self.assertEqual(resistance*beta*tau,fraction(row['publication_forcing_v']))
                self.assertTrue(row['exact_error_identity'])
                if resistance==0:self.assertEqual(predicted,0);self.assertEqual(beta,1)
                elif predicted:
                    self.assertNotEqual(predicted,fraction(row['error_without_forcing_v']));nonzero+=1
                # Local exact-history current/publication identities, separate from numerical incoming memory.
                exact_virtual=law.polynomial(time,poly)
                if row['method']!='BE':exact_virtual+=gamma*(law.polynomial(time,poly)-law.polynomial(time-k,poly))
                coarse_current=(source-exact_virtual)/(dt/cap+resistance)
                self.assertEqual(coarse_current-cap*velocity,beta*tau)
                coarse_publication=exact_virtual+dt*coarse_current/cap
                self.assertEqual(exact-coarse_publication,resistance*beta*tau)
                time=t;older,old=old,published;eolder,eold=eold,predicted;count+=1
        self.assertEqual(count,512);self.assertGreater(nonzero,0)

    def test_nonlinear_profiles_chain_rule_precision_all_quadrature_levels_and_conservation(self):
        self.assertEqual(len(self.report['nonlinear_profiles']),32)
        for profile in self.report['nonlinear_profiles']:
            junction=profile['junction'];bias=profile['bias_v'];h=fraction(profile['h_s']);k=fraction(profile['k_s'])
            direct=law.nonlinear_defect(self.parameters,junction,bias,h,k,80)
            direct100=law.nonlinear_defect(self.parameters,junction,bias,h,k,100)
            self.assertEqual(str(direct),profile['defect80_a']);self.assertEqual(str(direct100),profile['defect100_a'])
            self.assertEqual(law.precision_metric(direct,direct100),profile['precision']);self.assertTrue(profile['precision']['passed'])
            self.assertEqual([v['count'] for v in profile['levels']],[32,64,128,256])
            for level in profile['levels']:
                self.assertEqual(law.precision_metric(direct,D(level['integral_a'])),level['comparison'])
            self.assertEqual(all(level['comparison']['passed'] for level in profile['levels'][-2:]),profile['declared_final_quadratures_passed'])
            self.assertTrue(profile['declared_final_quadratures_passed'])
            # Independent FD of Q'': compute it from Q'(v) and Q''(v) along the known voltage, not Q''' helper.
            with localcontext() as ctx:
                ctx.prec=80;epsilon=D('1e-10');t=-law.decimal_fraction(h)/2
                dep=self.parameters.depletion_be if junction=='be' else self.parameters.depletion_bc
                transit=self.parameters.transit_forward_s if junction=='be' else self.parameters.transit_reverse_s
                scale=self.parameters.emission_be_v if junction=='be' else self.parameters.emission_bc_v
                def time_second(time):
                    voltage=lift(bias)+100*time+20000*time*time+10000000*time**3
                    _,c,c2=law.junction_values(dep,transit,self.parameters.saturation_a,scale,voltage)
                    velocity=100+40000*time+30000000*time*time;acceleration=40000+60000000*time
                    return c2*velocity**2+c*acceleration
                fd=(time_second(t+epsilon)-time_second(t-epsilon))/(2*epsilon)
                analytic=law.charge_profile(self.parameters,junction,bias,t)['third_c_per_s3']
                self.assertTrue(law.precision_metric(analytic,fd)['passed'])
                # Oriented two-junction terminal incidence is conservative, including negative current.
                be=F(direct);bc=-be/7
                self.assertEqual((be+bc)-bc-be,0)
        # Replay the final quadrature independently for one profile in each branch and region.
        for index in (0,8,16,24):
            p=self.report['nonlinear_profiles'][index];level=p['levels'][-1]
            value=law.nonlinear_integral(self.parameters,p['junction'],p['bias_v'],fraction(p['h_s']),fraction(p['k_s']),256,100)
            self.assertEqual(str(value),level['integral100_a'])

    def test_domains_reject_crossing_invalid_times_and_invalid_quadrature(self):
        with self.assertRaises(ValueError):law.weights(F(3),F(1))
        with self.assertRaises(ValueError):law.weights(F(0),F(1))
        with self.assertRaises(ValueError):law.lagrange_weights((F(0),F(0)))
        with self.assertRaises(ValueError):law.kernel(F(1),F(1),F(-3))
        with self.assertRaises(ValueError):law.nonlinear_integral(self.parameters,'be',.12,F(1,10000),F(1,10000),3)
        with self.assertRaisesRegex(ValueError,'knee'):
            law.nonlinear_defect(self.parameters,'be',.31,F(1,10000),F(1,10000))
        with self.assertRaises(ValueError):law.series_terms(F(1),F(1),F(1),F(-1))

    def test_storage_source_hashes_and_scope(self):
        summary=json.loads(experiment.SUMMARY.read_bytes());storage=summary['storage'];sha=lambda b:hashlib.sha256(b).hexdigest()
        self.assertEqual(len(self.raw),storage['bytes']);self.assertEqual(sha(self.raw),storage['compressed_sha256'])
        self.assertEqual(sha(canonical(self.report)),storage['canonical_json_sha256'])
        self.assertEqual(gzip.decompress(self.raw),canonical(self.report))
        for name,h in self.report['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h)
        self.assertEqual(self.report['new_nonlinear_solves'],0)
        for key in ('circuit_temporal_defect_known','temporal_error_bound_admitted','integrator_changed',
                    'physical_switching_admitted','audio_admitted','deadline_admitted'):self.assertFalse(self.report[key])


if __name__=='__main__':unittest.main()
