import gzip,hashlib,json,sys,unittest
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from math import factorial
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_charge_enclosure as bound
import loudness_latch_bdf_static_precision_charge_enclosure as experiment
import loudness_latch_dense_charge as poly
import loudness_latch_charge_balance as balance
from loudness_latch_bdf_doubling_survey import canonical


def decimal(x):return D(x.numerator)/D(x.denominator)


class RationalEnclosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.source=json.loads(gzip.decompress(experiment.old.old.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
        cls.prior=json.loads(gzip.decompress(experiment.old.OUTPUT.read_bytes()))
        cls.network=experiment.old.CompensatedBdfNetwork(200,experiment.old.model_parameters(1,'finite_transit'))
        cls.graph=experiment.old.curvature.graph(cls.network,10.)

    def test_exponential_independent_rational_series_and_extremes(self):
        for x in (F(0),F(1),F(3,7)):
            lo,hi=bound.exp_bounds(x);s=sum((x**k/F(factorial(k)) for k in range(151)),F(0))
            tail=2*x**151/F(factorial(151));self.assertLessEqual(lo,s);self.assertGreaterEqual(hi,s+tail)
            if x:
                a,b=bound.exp_bounds(-x);self.assertLessEqual(a,1/(s+tail));self.assertGreaterEqual(b,1/s)
        with localcontext() as ctx:
            ctx.prec=200
            for x in (-4096,-256,-45,45,256,4096):
                a,b=bound.exp_bounds(F(x));w=F(D(x).exp())
                self.assertLessEqual(a,w);self.assertGreaterEqual(b,w)
        with self.assertRaises(ValueError):bound.exp_bounds(4097)
        for x in (F(1,3),F(-1,3)):
            self.assertLessEqual(bound.down(x),x);self.assertGreaterEqual(bound.up(x),x)

    def test_affine_closed_form_and_independent_uncentered_cubic_series(self):
        with localcontext() as ctx:
            ctx.prec=200
            for p,left,right in (((F(1,7),),F(0),F(1)),((F(1,7),F(1,100000)),F(-3),F(1)),
                                 ((F(-2),F(-1,100)),F(0),F(1))):
                (a,b),_=bound.exponential_integral(p,left,right)
                if len(p)==1:w=(decimal(p[0])).exp()*decimal(right-left)
                else:w=((decimal(p[0]+p[1]*right)).exp()-(decimal(p[0]+p[1]*left)).exp())/decimal(p[1])
                self.assertLessEqual(a,F(w));self.assertGreaterEqual(b,F(w))
        p=(F(1,10),F(1,50),F(3,100),F(1,25));power=(F(1),);s=F(0)
        for k in range(61):
            s+=balance.integral(power,F(0),F(1))/factorial(k);power=poly.multiply(power,p)
        maximum=sum(p);tail=bound.exp_bounds(maximum)[1]*maximum**61/factorial(61)
        (a,b),d=bound.exponential_integral(p)
        self.assertLessEqual(a,s);self.assertGreaterEqual(b,s+tail);self.assertEqual(d['degree'],12)
        with self.assertRaises(ValueError):bound.exponential_integral(p,F(1),F(0))

    def test_terminal_stamps_polarities_and_fixed_boundary(self):
        for polarity in (1,-1):
            g=dict(fixed={'GND':0.},resistors=[dict(left=0,right='GND',ohm=3.)],conductances=[],
                   bjts=[dict(ref='Q',base=0,collector=1,emitter='GND',polarity=polarity,
                              is_a=1e-14,vt=.025,beta_forward=100.,beta_reverse=5.)],diodes=[])
            x=[(F(1,100),),(F(1,200),)];intervals,terms=bound.static_integral(g,x,F(1,1000))
            self.assertEqual(len(terms),2)
            with localcontext() as ctx:
                ctx.prec=200;s=D(polarity);sat=D.from_float(1e-14);vt=D.from_float(.025)
                forward=sat*((s*decimal(x[0][0])/vt).exp()-1)
                reverse=sat*((s*decimal(x[0][0]-x[1][0])/vt).exp()-1)
                currents=[decimal(x[0][0])/3+s*(forward/100+reverse/5),s*(forward-D('1.2')*reverse)]
                for (a,b),v in zip(intervals,currents):self.assertLessEqual(a,F(v/1000));self.assertGreaterEqual(b,F(v/1000))
        bad=g|dict(diodes=[dict(ref='D',anode=0,cathode='GND',is_a=1e-14,ideality=1.,vt=.0001)])
        with self.assertRaises(ValueError):bound.static_integral(bad,x,F(1))

    def test_all_balances_enclosures_and_selected_replays(self):
        count=0;classes={'below':0,'above':0,'unresolved':0}
        for w,source,pw in zip(self.report['windows'],self.source,self.prior['windows']):
            self.assertEqual(w['name'],pw['name'])
            for level,original,pl in zip(w['levels'],source['levels'],pw['levels']):
                for row,pr in zip(level['rows'],pl['rows']):
                    r=row['result'];self.assertEqual(row['support_sha256'],pr['support_sha256'])
                    self.assertEqual(len(r['terms']),84);self.assertTrue(r['all_gauss16_error_bounds_passed'])
                    duration=F(r['duration_s']);self.assertGreater(duration,0)
                    for static,bal,mean,l1,c in zip(r['static_integral_c'],r['polynomial_balance_c'],r['polynomial_mean_a'],r['nodal_l1_residual_lower_c'],r['gauss16_contrast']):
                        a,b=map(F,static);ba,bb=map(F,bal);ma,mb=map(F,mean)
                        self.assertLessEqual(a,b);self.assertEqual(bb-ba,b-a);self.assertEqual((ma,mb),(ba/duration,bb/duration))
                        self.assertEqual(F(l1),F(0) if ba<=0<=bb else min(abs(ba),abs(bb)))
                        self.assertTrue(c['passed']);self.assertLessEqual(F(c['absolute_error_upper_c']),F(c['gate_c']))
                    classes[r['mean_classification_10pa']]+=1;count+=1
                # One full exact re-evaluation per level; do not repeat the entire corpus.
                prepared=experiment.old.old.dense.prepare(self.network,original['reference'],31)
                r=experiment.point(self.network,self.graph,prepared,F(0),F(1),pl['rows'][29]['result'])
                self.assertEqual(r,level['rows'][29]['result'])
                dyn,boundary=bound.dynamic_charge(self.network,prepared['q'],F(0),F(1))
                self.assertEqual(sum(dyn)+boundary,0)
        self.assertEqual(count,496);self.assertEqual(classes,{'below':105,'above':391,'unresolved':0})
        self.assertEqual(len(self.report['mixed_supports']),1)
        self.assertTrue(self.report['mixed_supports'][0]['result']['all_gauss16_error_bounds_passed'])

    def test_storage_frozen_sources_and_scope(self):
        self.assertGreater(F(1e-30),F(D('1e-30')));self.assertGreater(F(1e-8),F(D('1e-8')))
        storage=json.loads(experiment.SUMMARY.read_text())['storage']
        self.assertEqual(len(self.raw),storage['bytes']);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),storage['compressed_sha256'])
        self.assertEqual(gzip.decompress(self.raw),canonical(self.report));self.assertEqual(hashlib.sha256(canonical(self.report)).hexdigest(),storage['canonical_json_sha256'])
        for name,expected in self.report['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        self.assertEqual(self.report['new_nonlinear_circuit_solves'],0);self.assertTrue(self.report['ideal_reconstructed_integral_enclosed'])
        for key in ('constitutive_memory_residual_enclosed','full_path_coverage','temporal_error_bound_admitted','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(self.report[key])
