import gzip,hashlib,json,sys,unittest
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_correlated_enclosure as bound
import loudness_latch_bdf_static_precision_correlated_enclosure as experiment
import loudness_latch_dense_charge as poly
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import evaluate as static_values
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_doubling_survey import canonical


def decimal(x):return D(x.numerator)/D(x.denominator)


class CorrelatedBounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.prior=json.loads(gzip.decompress(experiment.old.OUTPUT.read_bytes()))
        cls.source=json.loads(gzip.decompress(experiment.old.old.old.old.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
        cls.network=experiment.old.old.old.CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))
        cls.graph=curvature.graph(cls.network,10.)

    def test_capacitance_series_both_pieces_m0_m1_and_rates(self):
        p=model_parameters(1,'finite_transit');dep=p.depletion_be;knee=F(dep.forward_fraction*dep.potential_v)
        with localcontext() as ctx:
            ctx.prec=200
            for m in (0.,.5,1.):
                d=replace(dep,grading=m)
                for below,v in ((True,(F(1,10),F(1,100),F(1,2000),F(1,10000))),
                                (False,(knee+F(1,10),F(1,100),F(1,2000),F(1,10000)))):
                    cp,error,diag=bound.capacitance_polynomial(v,d,p.transit_forward_s,p.saturation_a,p.emission_be_v,F(0),F(1),below)
                    self.assertGreaterEqual(error,0);self.assertEqual(diag['below'],below);self.assertLessEqual(len(cp),19)
                    for u in (F(0),F(1,4),F(1,2),F(1)):
                        value=poly.evaluate(v,u);_,cap,_=curvature.junction_values(d,p.transit_forward_s,p.saturation_a,p.emission_be_v,decimal(value))
                        self.assertLessEqual(abs(poly.evaluate(cp,u)-F(cap)),error)
                        velocity=poly.evaluate(poly.differentiate(v),u)/F(3,1000)
                        self.assertLessEqual(abs(poly.evaluate(cp,u)*velocity-F(cap)*velocity),error*abs(velocity))
            # Rational M=1/T=0 oracle independent of log and exp; exact linear M=0 rate cancels Qpol'.
            v=(F(1,10),F(1,100),F(1,1000));d=replace(dep,grading=1.)
            cp,error,_=bound.capacitance_polynomial(v,d,0.,p.saturation_a,p.emission_be_v,F(0),F(1),True)
            for u in (F(0),F(1,2),F(1)):
                exact=F(dep.cj0_f)/(1-poly.evaluate(v,u)/F(dep.potential_v))
                self.assertLessEqual(abs(poly.evaluate(cp,u)-exact),error)
            d=replace(dep,grading=0.);cp,error,_=bound.capacitance_polynomial(v,d,0.,p.saturation_a,p.emission_be_v,F(0),F(1),True)
            velocity=poly.differentiate(v);difference=poly.add(poly.multiply(cp,velocity),poly.scale(velocity,-F(dep.cj0_f)))
            enclosure=bound.old.polynomial_range(difference);limit=error*max(map(abs,poly.bernstein(velocity)))
            self.assertLessEqual(enclosure[0]-limit,0);self.assertGreaterEqual(enclosure[1]+limit,0)
        with self.assertRaises(ValueError):bound.intersect((F(0),F(1)),(F(2),F(3)))
        with self.assertRaises(ValueError):bound.capacitance_polynomial((F(2),),dep,0.,p.saturation_a,p.emission_be_v,F(0),F(1),True)

    def test_restricted_graph_independent_full_currents_on_active_nodes(self):
        active=bound.active_nodes(self.network);filtered=bound.restricted_graph(self.graph,active)
        for rows,fields in (('resistors',('left','right')),('conductances',('left','right')),('bjts',('base','collector','emitter')),('diodes',('anode','cathode'))):
            expected=[r for r in self.graph[rows] if any(r[k] in active for k in fields)]
            self.assertEqual(filtered[rows],expected)
        for w in self.source:
            for level in w['levels']:
                prepared=experiment.old.old.old.old.dense.prepare(self.network,level['reference'],31)
                with localcontext() as ctx:
                    ctx.prec=120;x=[decimal(poly.evaluate(p,F(1,2))) for p in prepared['x']]
                    full=static_values(self.graph,x,120,jacobian=False)[0];query=static_values(filtered,x,120,jacobian=False)[0]
                    for j in active:self.assertEqual(full[j],query[j])

    def test_all_496_covers_intersections_l1_and_eight_replays(self):
        count=0
        for w,source,pw in zip(self.report['windows'],self.source,self.prior['windows']):
            for level,original,pl in zip(w['levels'],source['levels'],pw['levels']):
                for row,pr in zip(level['rows'],pl['rows']):
                    r=row['result'];prior=pr['result'];active=r['active_nodes'];self.assertEqual(row['support_sha256'],pr['support_sha256'])
                    self.assertEqual(active,bound.active_nodes(self.network));self.assertTrue(r['bounds_nonincreasing']);self.assertTrue(r['l1_lower_upper_consistent'])
                    self.assertEqual(F(r['segments'][0]['left']),0);self.assertEqual(F(r['segments'][-1]['right']),1)
                    sums={j:F(0) for j in active};points={j:F(0) for j in active};last=F(0)
                    for segment in r['segments']:
                        a,b=F(segment['left']),F(segment['right']);self.assertEqual(a,last);self.assertGreater(b,a);last=b
                        for j,raw,final in zip(active,segment['raw_active_a'],segment['active_a']):
                            raw=tuple(map(F,raw));final=tuple(map(F,final));inherited=tuple(map(F,prior['cells_a'][segment['old_cell']][j]))
                            self.assertEqual(final,bound.intersect(raw,inherited));sums[j]+=F(prior['duration_s'])*(b-a)*bound.old.magnitude(final);points[j]=max(points[j],bound.old.magnitude(final))
                    for j in range(94):
                        upper=F(r['constitutive_l1_upper_c'][j]);point=F(r['constitutive_pointwise_upper_a'][j])
                        self.assertLessEqual(F(prior['constitutive_l1_lower_c'][j]),upper);self.assertLessEqual(upper,F(prior['constitutive_l1_upper_c'][j]));self.assertLessEqual(point,F(prior['constitutive_pointwise_upper_a'][j]))
                        if j in active:self.assertEqual(upper,bound.old.base.up(sums[j]));self.assertEqual(point,bound.old.base.up(points[j]))
                        else:self.assertEqual(r['constitutive_l1_upper_c'][j],prior['constitutive_l1_upper_c'][j]);self.assertEqual(r['constitutive_pointwise_upper_a'][j],prior['constitutive_pointwise_upper_a'][j])
                    self.assertEqual(r['whole_interval_below_10pa'],max(map(F,r['constitutive_pointwise_upper_a']))<F(1e-11));count+=1
                prepared=experiment.old.old.old.old.dense.prepare(self.network,original['reference'],31)
                actual=experiment.old.old.packed(bound.correlated_bounds(self.network,self.graph,prepared,F(0),F(1),pl['rows'][29]['result']))
                self.assertEqual(actual,level['rows'][29]['result'])
        self.assertEqual(count,496)

    def test_24_interior_witnesses_and_mixed_bracket(self):
        witnesses=0
        for w,source in zip(self.report['windows'],self.source):
            for level,original in zip(w['levels'],source['levels']):
                prepared=experiment.old.old.old.old.dense.prepare(self.network,original['reference'],31);r=level['rows'][29]['result']
                for z in (F(1,4),F(1,2),F(3,4)):
                    actual=experiment.old.old.old.old.dense.query(self.network,self.graph,prepared,z,120)['vectors']['continuous_chain_kcl_a']
                    seg=next(s for s in r['segments'] if F(s['left'])<=z<=F(s['right']))
                    for j,ab in zip(r['active_nodes'],seg['active_a']):
                        a,b=map(F,ab);self.assertLessEqual(a,F(actual[j]));self.assertGreaterEqual(b,F(actual[j]))
                    witnesses+=1
        self.assertEqual(witnesses,24);self.assertEqual(len(self.report['mixed_supports']),1)
        m=self.report['mixed_supports'][0];r=m['result'];self.assertEqual(r['smooth_pieces'],2);self.assertEqual(r['bridges'],1)
        source=next(w for w in self.source if w['name']==m['window']);ref=next(l['reference'] for l in source['levels'] if l['reference']['subdivisions']==m['subdivisions'])
        prepared=experiment.old.old.old.old.dense.prepare(self.network,ref,m['index']);left=prepared['u'][-1];width=1-left
        bridge=next(s for s in r['segments'] if s['kind']=='bridge-rectangle');z=(F(bridge['left'])+F(bridge['right']))/2
        actual=experiment.old.old.old.old.dense.query(self.network,self.graph,prepared,left+width*z,120)['vectors']['continuous_chain_kcl_a']
        for j,ab in zip(r['active_nodes'],bridge['active_a']):
            a,b=map(F,ab);self.assertLessEqual(a,F(actual[j]));self.assertGreaterEqual(b,F(actual[j]))
        with self.assertRaises(ValueError):bound.balance.partition(prepared|dict(knees=[(F(0),)]*4),F(0),F(1))

    def test_storage_sources_and_scope(self):
        s=json.loads(experiment.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(len(self.raw),s['bytes']);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),s['compressed_sha256'])
        self.assertEqual(gzip.decompress(self.raw),canonical(self.report));self.assertEqual(hashlib.sha256(canonical(self.report)).hexdigest(),s['canonical_json_sha256'])
        for name,expected in self.report['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        self.assertEqual(self.report['schema'],'rf-d/bdf-static-correlated-enclosure/v1');self.assertEqual(self.report['new_nonlinear_circuit_solves'],0);self.assertTrue(self.report['inherited_signed_balances_unchanged'])
        for key in ('prior_reports_modified','numerical_gates_changed','full_path_coverage','physical_trajectory_bound','temporal_error_bound_admitted','audio_admitted','deadline_admitted'):self.assertFalse(self.report[key])
