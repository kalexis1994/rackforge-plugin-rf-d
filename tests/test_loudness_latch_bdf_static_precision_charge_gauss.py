import gzip,hashlib,json,sys,unittest
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_charge_gauss as experiment
import loudness_latch_charge_gauss as gauss
import loudness_latch_bdf_charge_defect as law
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import evaluate as static_values
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from bjt_charge_ngspice_probes import model_parameters


class GaussBalance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.source=json.loads(gzip.decompress(experiment.old.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
        cls.prior=json.loads(gzip.decompress(experiment.old.OUTPUT.read_bytes()))
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))
        cls.graph=curvature.graph(cls.network,10.)

    def test_rules_both_precisions_moments_and_root_budgets(self):
        for precision in (80,100):
            for n in gauss.ORDERS:
                actual=gauss.rule(n,precision);archived=self.report['rules'][str(precision)][str(n)]
                self.assertEqual([[str(x),str(w)] for x,w in actual['points']],archived['points'])
                self.assertEqual(actual['moments'],archived['moments']);self.assertTrue(all(m['passed'] for m in actual['moments']))
                self.assertTrue(all(0<i<=32 for i in actual['iterations']))
                self.assertTrue(all(-1<x<1 and w>0 for x,w in actual['points']))
        with self.assertRaises(ValueError):gauss.rule(3,80)
        with self.assertRaises(ValueError):gauss.rule(8,28)

    def test_496_balance_identities_precision_and_mixed_bridge(self):
        count=0
        with localcontext() as ctx:
            ctx.prec=100
            for w,pw in zip(self.report['windows'],self.prior['windows']):
                self.assertEqual(w['name'],pw['name'])
                for level,pl in zip(w['levels'],pw['levels']):
                    for row,pr in zip(level['rows'],pl['rows']):
                        r=row['result'];self.assertEqual(row['index'],pr['index']);self.assertEqual(row['support_sha256'],pr['support_sha256'])
                        self.assertEqual(r['partition'],pr['result']['partition'])
                        self.assertTrue(r['final_quadrature_gate']);self.assertTrue(all(m['passed'] for m in r['common_precision'].values()))
                        dp=list(map(D,r['common']['dynamic_polynomial_c']));dc=list(map(D,r['common']['dynamic_constitutive_c']))
                        for l in r['levels']:
                            self.assertTrue(all(m['passed'] for m in l['precision'].values()));self.assertTrue(l['identity']['passed'])
                            self.assertTrue(l['chain_endpoint_gate']['passed'])
                            static=list(map(D,l['vectors']['static_integral_c']))
                            self.assertTrue(curvature.metrics([a+b for a,b in zip(static,dp)],list(map(D,l['vectors']['polynomial_balance_c'])))['passed'])
                            self.assertTrue(curvature.metrics([a+b for a,b in zip(static,dc)],list(map(D,l['vectors']['constitutive_balance_c'])))['passed'])
                        count+=1
            self.assertEqual(count,496);self.assertEqual(len(self.report['mixed_supports']),1)
            r=self.report['mixed_supports'][0]['result'];self.assertTrue(r['final_quadrature_gate'])
            self.assertEqual(len(r['partition']['smooth']),2);self.assertEqual(len(r['partition']['bridges']),1)
            self.assertTrue(all(m['passed'] for m in r['common_precision'].values()))

    def test_24_closed_form_gauss4_and_selected_full_precision_replays(self):
        rules={p:{n:gauss.rule(n,p) for n in gauss.ORDERS} for p in (80,100)};count=0
        with localcontext() as ctx:
            ctx.prec=100;s=(D(6)/5).sqrt();root30=D(30).sqrt()
            closed=((((3-2*s)/7).sqrt(),(18+root30)/36),(((3+2*s)/7).sqrt(),(18-root30)/36))
            for w,source in zip(self.report['windows'],self.source):
                for level,original in zip(w['levels'],source['levels']):
                    for index in (2,31,63):
                        prepared=experiment.old.dense.prepare(self.network,original['reference'],index);r=level['rows'][index-2]['result']
                        xp=[tuple(map(law.decimal_fraction,p)) for p in prepared['x']];samples=[]
                        for z,weight in closed:
                            for sign in (-1,1):
                                u=(1+sign*z)/2;x=[]
                                for p in xp:
                                    v=D(0)
                                    for a in reversed(p):v=v*u+a
                                    x.append(v)
                                samples.append((weight,static_values(self.graph,x,100,jacobian=False)[0]))
                        independent=[law.decimal_fraction(prepared['h'])/2*sum((w*v[j] for w,v in samples),D(0)) for j in range(94)]
                        self.assertTrue(curvature.metrics(independent,list(map(D,r['levels'][0]['vectors']['static_integral_c'])))['passed'])
                        a=gauss.integrate(self.network,self.graph,prepared,F(0),F(1),rules[80],80)
                        b=gauss.integrate(self.network,self.graph,prepared,F(0),F(1),rules[100],100)
                        for archived,lo,hi in zip(r['levels'],a['levels'],b['levels']):
                            self.assertEqual(list(map(str,lo['static_integral_c'])),archived['vectors']['static_integral_c'])
                            self.assertTrue(curvature.metrics(lo['static_integral_c'],hi['static_integral_c'])['passed'])
                            self.assertTrue(curvature.metrics(lo['chain_integral_c'],hi['chain_integral_c'])['passed'])
                        count+=1
        self.assertEqual(count,24)

    def test_storage_preserved_simpson_failures_and_scope(self):
        s=json.loads(experiment.SUMMARY.read_text())['storage']
        self.assertEqual(len(self.raw),s['bytes']);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),s['compressed_sha256'])
        self.assertEqual(hashlib.sha256(canonical(self.report)).hexdigest(),s['canonical_json_sha256'])
        self.assertEqual(gzip.decompress(self.raw),canonical(self.report))
        for name,expected in self.report['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        prior=[r['result'] for w in self.prior['windows'] for l in w['levels'] for r in l['rows']]
        self.assertEqual(sum(r['final_quadrature_gate'] for r in prior),125)
        receipt=json.loads((ROOT/'evidence/loudness_latch_bdf_static_precision_charge_balance_validation.json').read_text())
        self.assertEqual(len(receipt['attempts']),2);self.assertFalse(receipt['attempts'][0]['passed']);self.assertTrue(receipt['attempts'][1]['passed'])
        failed=receipt['attempts'][0]['suites'][0]
        self.assertEqual(hashlib.sha256(failed['failed_test_source_utf8'].encode()).hexdigest(),failed['test_sha256'])
        self.assertEqual(self.report['legendre_scalar_root_solves'],28);self.assertEqual(self.report['new_nonlinear_circuit_solves'],0)
        self.assertEqual(self.report['final_orders'],[8,16])
        for key in ('prior_reports_modified','integrator_changed','physical_trajectory_bound','exact_temporal_defect_known',
                    'independent_error_estimator','temporal_error_bound_admitted','physical_switching_admitted','audio_admitted','deadline_admitted'):
            self.assertFalse(self.report[key])


if __name__=='__main__':unittest.main()
