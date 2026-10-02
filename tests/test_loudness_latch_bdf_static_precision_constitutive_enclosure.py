import gzip,hashlib,json,sys,unittest
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from dataclasses import replace
from types import SimpleNamespace as NS
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_constitutive_enclosure as bound
import loudness_latch_bdf_static_precision_constitutive_enclosure as experiment
import loudness_latch_dense_charge as poly
import loudness_latch_directional_curvature as curvature
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_doubling_survey import canonical


def decimal(x):return D(x.numerator)/D(x.denominator)


class ConstitutiveBounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.prior=json.loads(gzip.decompress(experiment.old.OUTPUT.read_bytes()))
        cls.gauss=json.loads(gzip.decompress(experiment.old.old.OUTPUT.read_bytes()))
        cls.source=json.loads(gzip.decompress(experiment.old.old.old.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
        cls.network=experiment.old.old.CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))
        cls.graph=curvature.graph(cls.network,10.)

    def test_log_rational_series_extremes_and_power_intervals(self):
        for x in (F(1),F(4,3),F(3,2)):
            z=(x-1)/(x+1);s=sum((2*z**(2*k+1)/(2*k+1) for k in range(151)),F(0))
            tail=2*z**303/(303*(1-z*z));a,b=bound.log_bounds(x)
            self.assertLessEqual(a,s);self.assertGreaterEqual(b,s+tail)
        with localcontext() as ctx:
            ctx.prec=200
            for x in (F(1,2**100),F(2**100),F(7,13),F(19,7)):
                a,b=bound.log_bounds(x);w=F(decimal(x).ln());self.assertLessEqual(a,w);self.assertGreaterEqual(b,w)
            for exponent in (F(-1),F(0),F(1,2),F(1)):
                a,b=bound.positive_power((F(3,2),F(7,4)),exponent)
                for x in (F(3,2),F(13,8),F(7,4)):
                    w=F((decimal(exponent)*decimal(x).ln()).exp());self.assertLessEqual(a,w);self.assertGreaterEqual(b,w)
        for x in (0,-1):
            with self.assertRaises(ValueError):bound.log_bounds(x)
        with self.assertRaises(ValueError):bound.log_bounds(F(2)**4097)
        with self.assertRaises(ValueError):bound.div((F(1),F(1)),(F(-1),F(1)))

    def test_junction_both_pieces_monotonicity_linear_and_m1(self):
        p=model_parameters(1,'finite_transit')
        with localcontext() as ctx:
            ctx.prec=200
            for dep,t,emission in ((p.depletion_be,p.transit_forward_s,p.emission_be_v),(p.depletion_bc,p.transit_reverse_s,p.emission_bc_v)):
                knee=F(dep.forward_fraction*dep.potential_v);previous=None
                for v in (F(-1,2),F(0),knee-F(1,2**100),knee,knee+F(1,2**100),knee+F(1,100)):
                    q,c=bound.junction_bounds(dep,t,p.saturation_a,emission,v)
                    oq,oc,_=curvature.junction_values(dep,t,p.saturation_a,emission,decimal(v))
                    for ab,w in ((q,oq),(c,oc)):
                        self.assertLessEqual(ab[0],F(w));self.assertGreaterEqual(ab[1],F(w))
                    if previous:self.assertLessEqual(previous[1],c[0])
                    previous=c
                # M=0, T=0 has an exact globally linear charge, including the continued branch.
                linear=replace(dep,grading=0.)
                for v in (F(-1),knee,knee+F(1,10)):
                    q,c=bound.junction_bounds(linear,0.,p.saturation_a,emission,v)
                    self.assertLessEqual(q[0],F(dep.cj0_f)*v);self.assertGreaterEqual(q[1],F(dep.cj0_f)*v)
                    self.assertLessEqual(c[0],F(dep.cj0_f));self.assertGreaterEqual(c[1],F(dep.cj0_f))
                special=replace(dep,grading=1.)
                for v in (F(-1,4),knee,knee+F(1,100)):
                    q,c=bound.junction_bounds(special,t,p.saturation_a,emission,v)
                    oq,oc,_=curvature.junction_values(special,t,p.saturation_a,emission,decimal(v))
                    self.assertLessEqual(q[0],F(oq));self.assertGreaterEqual(q[1],F(oq));self.assertLessEqual(c[0],F(oc));self.assertGreaterEqual(c[1],F(oc))
                with self.assertRaises(ValueError):bound.junction_bounds(replace(dep,grading=-1.),t,p.saturation_a,emission,F(0))
                with self.assertRaises(ValueError):bound.junction_bounds(dep,t,p.saturation_a,emission,46*F(emission))

    def test_polynomial_remainder_polarities_and_linear_cancellation(self):
        network=NS(network=NS(branches=[(0,None,0.,1.,0.)],latch=NS(device=NS(parameters=NS(polarity=1)),terminals=[])))
        for polarity in (1,-1):
            g=dict(fixed={'GND':0.},resistors=[dict(left=0,right='GND',ohm=2.)],conductances=[],
                   bjts=[dict(ref='Q',base=0,collector=1,emitter='GND',polarity=polarity,is_a=1e-14,vt=.025,beta_forward=100.,beta_reverse=5.)],diodes=[])
            prepared=dict(x=[(F(1,100),F(1,1000),F(1,2000),F(1,10000)),(F(1,200),F(-1,1000))],q=[(F(0),F(-1,200))]+[(F(0),)]*24,h=F(1))
            residual,errors,_=bound.polynomial_residual(network,g,prepared,F(0),F(1))
            with localcontext() as ctx:
                ctx.prec=200;s=D(polarity);sat=D.from_float(1e-14);vt=D.from_float(.025)
                for u in (F(0),F(1,4),F(1,2),F(1)):
                    vb=decimal(poly.evaluate(prepared['x'][0],u));vc=decimal(poly.evaluate(prepared['x'][1],u))
                    forward=sat*((s*vb/vt).exp()-1);reverse=sat*((s*(vb-vc)/vt).exp()-1)
                    values=(vb/2+s*(forward/100+reverse/5)-D('0.005'),s*(forward-D('1.2')*reverse))
                    for p,error,w in zip(residual,errors,values):self.assertLessEqual(abs(poly.evaluate(p,u)-F(w)),error)
            self.assertTrue(all(e>=0 for e in errors));self.assertEqual(max(map(len,residual)),19)
        # Interval charge stamping must include fixed terminals even with dependent enclosures.
        values=[(F(0),F(0))]*25;values[0]=(F(2),F(3));nodal,boundary=bound.charge_stamp(network,values)
        self.assertEqual(nodal[0],(F(2),F(3)));self.assertEqual(boundary,(F(-3),F(-2)))

    def test_all_bounds_eight_replays_and_24_decimal_interior_witnesses(self):
        count=0;classes={'below':0,'above':0,'unresolved':0};witnesses=0
        for w,source,pw,gw in zip(self.report['windows'],self.source,self.prior['windows'],self.gauss['windows']):
            for level,original,pl,gl in zip(w['levels'],source['levels'],pw['levels'],gw['levels']):
                for row,pr in zip(level['rows'],pl['rows']):
                    r=row['result'];self.assertEqual(row['support_sha256'],pr['support_sha256']);self.assertTrue(r['all_gauss16_error_bounds_passed']);self.assertTrue(r['l1_lower_upper_consistent'])
                    duration=F(r['duration_s']);self.assertEqual(len(r['cells_a']),8)
                    for j,(lo,hi,plo,phi) in enumerate(zip(r['constitutive_l1_lower_c'],r['constitutive_l1_upper_c'],r['polynomial_l1_lower_c'],r['polynomial_l1_upper_c'])):
                        self.assertLessEqual(F(lo),F(hi));self.assertLessEqual(F(plo),F(phi))
                        total=sum((bound.magnitude(tuple(map(F,cell[j]))) for cell in r['cells_a']),F(0))*duration/8
                        self.assertEqual(bound.base.up(total),F(hi))
                        self.assertEqual(bound.base.up(max(bound.magnitude(tuple(map(F,c[j]))) for c in r['cells_a'])),F(r['constitutive_pointwise_upper_a'][j]))
                    for balance,mean in zip(r['constitutive_balance_c'],r['constitutive_mean_a']):
                        a,b=map(F,balance);ma,mb=map(F,mean);self.assertLessEqual(ma,a/duration);self.assertGreaterEqual(mb,b/duration)
                    classes[r['mean_classification_10pa']]+=1;count+=1
                prepared=experiment.old.old.old.dense.prepare(self.network,original['reference'],31)
                r=experiment.point(self.network,self.graph,prepared,F(0),F(1),pl['rows'][29]['result'],gl['rows'][29]['result'])
                self.assertEqual(r,level['rows'][29]['result'])
                for u in (F(1,4),F(1,2),F(3,4)):
                    actual=experiment.old.old.old.dense.query(self.network,self.graph,prepared,u,120)['vectors']['continuous_chain_kcl_a']
                    for ab,witness in zip(r['cells_a'][int(8*u)],actual):
                        a,b=map(F,ab);self.assertLessEqual(a,F(witness));self.assertGreaterEqual(b,F(witness))
                    witnesses+=1
        self.assertEqual(count,496);self.assertEqual(witnesses,24);self.assertEqual(classes,{'below':105,'above':391,'unresolved':0})
        m=self.report['mixed_supports'][0]['result'];self.assertTrue(m['l1_lower_upper_consistent']);self.assertTrue(m['all_gauss16_error_bounds_passed'])

    def test_storage_sources_scope_and_schema(self):
        storage=json.loads(experiment.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(len(self.raw),storage['bytes']);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),storage['compressed_sha256'])
        self.assertEqual(gzip.decompress(self.raw),canonical(self.report));self.assertEqual(hashlib.sha256(canonical(self.report)).hexdigest(),storage['canonical_json_sha256'])
        for name,expected in self.report['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        self.assertEqual(self.report['schema'],'rf-d/bdf-static-constitutive-enclosure/v1');self.assertEqual(self.report['new_nonlinear_circuit_solves'],0)
        self.assertTrue(self.report['constitutive_reconstructed_balance_enclosed']);self.assertTrue(self.report['reconstructed_l1_upper_enclosed'])
        for key in ('full_path_coverage','physical_trajectory_bound','temporal_error_bound_admitted','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):self.assertFalse(self.report[key])
        self.assertGreater(F(1e-30),F(D('1e-30')));self.assertGreater(F(1e-8),F(D('1e-8')))
