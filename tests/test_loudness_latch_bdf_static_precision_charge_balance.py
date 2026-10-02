import gzip,hashlib,json,sys,unittest
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_charge_balance as experiment
import loudness_latch_charge_balance as balance
import loudness_latch_dense_charge as poly
import loudness_latch_bdf_charge_defect as law
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import lift,evaluate as static_values
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from bjt_charge_ngspice_probes import model_parameters


def f(record):return F(record['numerator'],record['denominator'])


def gauss4(function,left,right,h=F(1)):
    # Algebraic nodes/weights prepared in the caller's Decimal context.
    s=(D(6)/5).sqrt();r=D(30).sqrt();half=law.decimal_fraction((right-left)/2)
    mid=law.decimal_fraction((right+left)/2);nodes=(((3-2*s)/7).sqrt(),(18+r)/36),(((3+2*s)/7).sqrt(),(18-r)/36)
    samples=[]
    for z,w in nodes:
        for sign in (-1,1):samples.append((w,function(mid+sign*half*z)))
    return [half*law.decimal_fraction(h)*sum((w*v[j] for w,v in samples),D(0)) for j in range(len(samples[0][1]))]


class ChargeBalance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.source=json.loads(gzip.decompress(experiment.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))
        cls.graph=curvature.graph(cls.network,10.)

    def test_exact_polynomial_integral_simpson_and_gauss_moments(self):
        with localcontext() as ctx:
            ctx.prec=100
            for left,right in ((F(0),F(1)),(F(-2),F(1)),(F(1,7),F(9,7))):
                for degree in range(8):
                    exact=(right**(degree+1)-left**(degree+1))/F(degree+1)
                    p=tuple(F(i==degree) for i in range(degree+1))
                    self.assertEqual(balance.integral(p,left,right),exact)
                    result=gauss4(lambda u:[D(1) if degree==0 else u**degree],left,right)[0]
                    self.assertLess(abs(result-law.decimal_fraction(exact)),D('1e-90'))
                    if degree<=3:
                        values=[[D(1) if degree==0 else law.decimal_fraction(left+(right-left)*F(i,64))**degree] for i in range(65)]
                        for count in balance.COUNTS:
                            self.assertLess(abs(balance.simpson(values,left,right,count)[0]-law.decimal_fraction(exact)),D('1e-90'))
            with self.assertRaises(ValueError):balance.integral((F(1),),F(1),F(0))
            with self.assertRaises(ValueError):balance.simpson([[D(1)]]*65,F(0),F(1),3)

    def test_continuous_knee_manufactured_crossing_bridge_and_coincidence_rejection(self):
        prepared=experiment.dense.prepare(self.network,self.source[0]['levels'][0]['reference'],2)
        p=self.network.network.latch.device.parameters
        with localcontext() as ctx:
            ctx.prec=100
            for dep,transit,scale in ((p.depletion_be,p.transit_forward_s,p.emission_be_v),(p.depletion_bc,p.transit_reverse_s,p.emission_bc_v)):
                knee=lift(dep.forward_fraction*dep.potential_v);potential=lift(dep.potential_v);m=lift(dep.grading)
                log=(1-knee/potential).ln();power=1-m
                qdep=lift(dep.cj0_f)*potential*(1-(power*log).exp())/power
                cap=lift(dep.cj0_f)*(-m*log).exp();ex=(knee/lift(scale)).exp()
                expected=qdep+lift(transit)*lift(p.saturation_a)*(ex-1)
                expected_c=cap+lift(transit)*lift(p.saturation_a)*ex/lift(scale)
                q,c,_=curvature.junction_values(dep,transit,p.saturation_a,scale,knee)
                self.assertTrue(curvature.metrics([expected,expected_c],[q,c])['passed'])
            for root in (F(1,2),F(1,3)):
                junctions=[];knees=[]
                for _,dep,transit,scale in prepared['junctions']:
                    vp=(F(dep.forward_fraction*dep.potential_v)-F(1,1000)*root,F(1,1000))
                    junctions.append((vp,dep,transit,scale));knees.append((-F(1,1000)*root,F(1,1000)))
                fake=prepared|dict(junctions=junctions,knees=knees)
                result=balance.integrate(self.network,self.graph,fake,F(0),F(1),100)
                self.assertEqual(len(result['partition']['smooth']),2)
                self.assertEqual(len(result['partition']['bridges']),int(root==F(1,3)))
                for row in result['levels']:self.assertTrue(row['chain_endpoint_gate']['passed'])
                if root==F(1,3):
                    a,b=result['partition']['bridges'][0];self.assertLess(a,root);self.assertLess(root,b)
                    q0=balance.constitutive(fake,a,p);q1=balance.constitutive(fake,b,p)
                    self.assertEqual(result['bridge_c'],[v-u for u,v in zip(q0,q1)])
            with self.assertRaisesRegex(ValueError,'coincident knee'):
                balance.partition(prepared|dict(knees=((F(0),),)*4),F(0),F(1))
            invalid=prepared|dict(junctions=tuple(((F(100),),dep,transit,scale) for _,dep,transit,scale in prepared['junctions']))
            self.assertFalse(balance.domain_certificate(self.network,self.graph,invalid,F(0),F(1))['passed'])

    def test_all_496_balances_exact_endpoint_incidence_and_piece_coverage(self):
        count=0;common_passes=0
        with localcontext() as ctx:
            ctx.prec=100
            for w,source in zip(self.report['windows'],self.source):
                for level,original in zip(w['levels'],source['levels']):
                    for row in level['rows']:
                        r=row['result'];self.assertIsNone(r['failure']);self.assertTrue(r['domain']['passed'])
                        prepared=experiment.dense.prepare(self.network,original['reference'],row['index'])
                        delta=[law.decimal_fraction(poly.evaluate(p,F(1))-poly.evaluate(p,F(0))) for p in prepared['q']]
                        self.assertTrue(curvature.metrics(delta,list(map(D,r['common']['delta_poly_c'])))['passed'])
                        self.assertEqual(prepared['support_sha256'],row['support_sha256'])
                        self.assertEqual(r['partition']['bridges'],[]);self.assertEqual(len(r['partition']['smooth']),1)
                        dp,bp=experiment.dense.previous.incidence(self.network,list(map(D,r['common']['delta_poly_c'])))
                        dc,bc=experiment.dense.previous.incidence(self.network,list(map(D,r['common']['delta_constitutive_c'])))
                        self.assertTrue(curvature.metrics(dp,list(map(D,r['common']['dynamic_polynomial_c'])))['passed'])
                        self.assertTrue(curvature.metrics(dc,list(map(D,r['common']['dynamic_constitutive_c'])))['passed'])
                        self.assertLess(abs(sum(dp,D(0))+bp),D('1e-30'));self.assertLess(abs(sum(dc,D(0))+bc),D('1e-30'))
                        self.assertTrue(all(m['passed'] for m in r['common_precision'].values()));common_passes+=1
                        for l in r['levels']:
                            self.assertTrue(all(m['passed'] for m in l['precision'].values()));self.assertTrue(l['identity']['passed'])
                            static=list(map(D,l['vectors']['static_integral_c']))
                            self.assertTrue(curvature.metrics([a+b for a,b in zip(static,dp)],list(map(D,l['vectors']['polynomial_balance_c'])))['passed'])
                            self.assertTrue(curvature.metrics([a+b for a,b in zip(static,dc)],list(map(D,l['vectors']['constitutive_balance_c'])))['passed'])
                            self.assertEqual(l['static_vs_64'],curvature.metrics(list(map(D,r['levels'][-1]['vectors']['static_integral_c'])),static))
                        self.assertEqual(r['final_quadrature_gate'],r['levels'][-2]['static_vs_64']['passed'] and r['levels'][-2]['chain_endpoint_gate']['passed'] and r['levels'][-1]['chain_endpoint_gate']['passed'])
                        count+=1
            self.assertEqual(len(self.report['mixed_supports']),1)
            r=self.report['mixed_supports'][0]['result'];self.assertIsNone(r['failure'])
            self.assertEqual(len(r['partition']['smooth']),2);self.assertEqual(len(r['partition']['bridges']),1)
            self.assertTrue(all(v['passed'] for v in r['common_precision'].values()))
        self.assertEqual(count,496);self.assertEqual(common_passes,496)

    def test_24_independent_gauss_negative_controls_and_selected_precision_replays(self):
        count=0;failures=[]
        with localcontext() as ctx:
            ctx.prec=100
            for w,source in zip(self.report['windows'],self.source):
                for level,original in zip(w['levels'],source['levels']):
                    for index in (2,31,63):
                        r=level['rows'][index-2]['result'];prepared=experiment.dense.prepare(self.network,original['reference'],index)
                        xp=[tuple(map(law.decimal_fraction,p)) for p in prepared['x']]
                        def integrand(u):
                            x=[]
                            for p in xp:
                                v=D(0)
                                for a in reversed(p):v=v*u+a
                                x.append(v)
                            return static_values(self.graph,x,100,jacobian=False)[0]
                        independent=gauss4(integrand,F(0),F(1),prepared['h'])
                        m=curvature.metrics(independent,list(map(D,r['levels'][-1]['vectors']['static_integral_c'])))
                        if not m['passed']:failures.append(dict(window=w['name'],subdivisions=level['subdivisions'],index=index,comparison=m))
                        # Replay only the selected constitutive/precision cases, not all grids.
                        a=balance.integrate(self.network,self.graph,prepared,F(0),F(1),80)
                        b=balance.integrate(self.network,self.graph,prepared,F(0),F(1),100)
                        for archived,lo,hi in zip(r['levels'],a['levels'],b['levels']):
                            self.assertEqual(list(map(str,lo['static_integral_c'])),archived['vectors']['static_integral_c'])
                            self.assertTrue(curvature.metrics(lo['static_integral_c'],hi['static_integral_c'])['passed'])
                            self.assertEqual(lo['chain_endpoint_gate'],archived['chain_endpoint_gate'])
                        count+=1
        self.assertEqual(count,24)
        self.assertTrue(any(v["window"]=="prefix" and v["subdivisions"]==2 and v["index"]==2 for v in failures))
        print(json.dumps(dict(gauss4_simpson64_negative_controls=failures)),flush=True)

    def test_storage_sources_and_no_integrated_voltage_bound_promotion(self):
        summary=json.loads(experiment.SUMMARY.read_text());s=summary['storage']
        self.assertEqual(len(self.raw),s['bytes']);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),s['compressed_sha256'])
        self.assertEqual(hashlib.sha256(canonical(self.report)).hexdigest(),s['canonical_json_sha256'])
        self.assertEqual(gzip.decompress(self.raw),canonical(self.report))
        for name,expected in self.report['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        self.assertEqual(self.report['quadrature_counts'],[8,16,32,64]);self.assertEqual(self.report['final_quadrature_counts'],[32,64])
        self.assertEqual(self.report['new_nonlinear_solves'],0);self.assertTrue(self.report['bridge_is_constitutive_endpoint_difference'])
        for key in ('prior_reports_modified','integrator_changed','physical_trajectory_bound','exact_temporal_defect_known',
                    'independent_error_estimator','temporal_error_bound_admitted','physical_switching_admitted','audio_admitted','deadline_admitted'):
            self.assertFalse(self.report[key])


if __name__=='__main__':unittest.main()
