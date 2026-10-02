import gzip,hashlib,json,sys,unittest
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from math import comb
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_dense_charge as experiment
import loudness_latch_dense_charge as poly
import loudness_latch_bdf_charge_defect as law
import loudness_latch_directional_curvature as curvature
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack
from bjt_charge_ngspice_probes import model_parameters


def f(value):return F(value['numerator'],value['denominator'])


def independent_newton(times,values,u):
    """Divided differences with nested derivative, no cardinal polynomial helper."""
    dd=list(values);coeff=[dd[0]]
    for order in range(1,len(times)):
        dd=[(dd[j+1]-dd[j])/(times[j+order]-times[j]) for j in range(len(dd)-1)]
        coeff.append(dd[0])
    value=coeff[-1];slope=F(0)
    for j in range(len(coeff)-2,-1,-1):
        slope=slope*(u-times[j])+value;value=value*(u-times[j])+coeff[j]
    return value,slope


class DenseCharge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.source=json.loads(gzip.decompress(experiment.previous.proxy.REFERENCE.read_bytes()))['windows']
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))
        cls.graph=curvature.graph(cls.network,10.)

    def test_exact_polynomial_basis_bernstein_subdivision_and_hidden_roots(self):
        times=(F(1),F(0),F(-1),F(-3));basis=poly.cardinal_basis(times)
        for i,p in enumerate(basis):
            self.assertEqual([poly.evaluate(p,t) for t in times],[F(i==j) for j in range(4)])
        for degree in range(4):
            result=poly.interpolate(basis,[[t**degree] for t in times])[0]
            self.assertEqual(result,tuple(F(i==degree) for i in range(4)))
        for degree in range(6):
            a=tuple(F((i+1)*(-1)**i,7) for i in range(degree+1))
            for left,right in ((F(0),F(1)),(F(-3),F(1)),(F(1,7),F(9,7))):
                b=poly.bernstein(a,left,right)
                first,second=poly.bisect_bernstein(b)
                for j in range(9):
                    u=F(j,8);value=sum((v*comb(degree,i)*u**i*(1-u)**(degree-i) for i,v in enumerate(b)),F(0))
                    self.assertEqual(value,poly.evaluate(a,left+(right-left)*u))
                    self.assertLessEqual(min(b),value);self.assertLessEqual(value,max(b))
                    for sub,offset in ((first,F(0)),(second,F(1,2))):
                        v=sum((z*comb(degree,i)*u**i*(1-u)**(degree-i) for i,z in enumerate(sub)),F(0))
                        self.assertEqual(v,poly.evaluate(a,left+(right-left)*(offset+u/2)))
        cases=(
            (poly.multiply((-F(1,3),F(1)),(-F(2,3),F(1))),(F(1,3),F(2,3))),
            (poly.multiply((-F(1,3),F(1)),(-F(1,3),F(1))),(F(1,3),)),
            ((F(-1,2),F(1)),(F(1,2),)),((F(0),F(-1),F(1)),(F(0),F(1))))
        for a,roots in cases:
            covered=poly.isolate_zero(a,depth=40)
            self.assertFalse(covered['coincident'])
            for root in roots:
                self.assertTrue(root in covered['exact_points'] or any(b['left']<=root<=b['right'] for b in covered['brackets']))
            for b in covered['brackets']:
                self.assertEqual(b['right']-b['left'],F(1,2**40))
                self.assertLess(min(b['bernstein']),0);self.assertGreater(max(b['bernstein']),0)
                self.assertEqual(b['opposite_endpoint_signs'],poly.evaluate(a,b['left'])*poly.evaluate(a,b['right'])<0)
        hidden=poly.isolate_zero(cases[0][0]);self.assertEqual(sum(b['opposite_endpoint_signs'] for b in hidden['brackets']),2)
        tangent=poly.isolate_zero(cases[1][0]);self.assertTrue(tangent['brackets']);self.assertFalse(any(b['opposite_endpoint_signs'] for b in tangent['brackets']))
        self.assertTrue(poly.isolate_zero((F(0),F(0)))['coincident'])
        self.assertFalse(poly.isolate_zero((F(2),))['brackets'])
        with self.assertRaises(ValueError):poly.cardinal_basis((F(0),F(0)))
        with self.assertRaises(ValueError):poly.bernstein((F(1),),F(1),F(0))
        with self.assertRaises(ValueError):poly.isolate_zero((F(1),),depth=41)
        with self.assertRaises(ValueError):poly.interpolate(basis,[[F(1)]])

    def test_all_496_exact_constraint_and_knee_certificates(self):
        count=0;crossings=0;last_piece=0
        for w,source in zip(self.report['windows'],self.source):
            self.assertEqual(w['name'],source['name'])
            for level,original in zip(w['levels'],source['levels']):
                for row in level['rows']:
                    prepared=experiment.prepare(self.network,original['reference'],row['index'])
                    self.assertEqual(experiment.serialize(experiment.certificate(prepared)),row['certificate'])
                    self.assertEqual(prepared['support_sha256'],row['support_sha256'])
                    self.assertEqual(experiment.serialize(prepared['times']),row['support_times_s'])
                    self.assertEqual(experiment.serialize(prepared['u']),row['normalized_support'])
                    for b in row['certificate']['branches']:
                        power=tuple(map(f,b['power']));bern=tuple(map(f,b['bernstein']))
                        self.assertEqual(f(b['lower']),min(bern));self.assertEqual(f(b['upper']),max(bern))
                        self.assertEqual(f(b['absolute_upper_v']),max(map(abs,bern)))
                        self.assertTrue(b['whole_interpolant_below_10fv'])
                        for u in (F(0),F(1,5),F(1,2),F(4,5),F(1)):
                            v=sum((z*comb(3,i)*u**i*(1-u)**(3-i) for i,z in enumerate(bern)),F(0))
                            self.assertEqual(v,poly.evaluate(power,u));self.assertLessEqual(min(bern),v);self.assertLessEqual(v,max(bern))
                    for knee in row['certificate']['knees']:
                        power=tuple(map(f,knee['power']))
                        last_piece+=knee['intervals'][0]['strict_same_piece']
                        for domain in knee['intervals']:
                            self.assertFalse(domain['zero_cover']['coincident'])
                            for b in domain['zero_cover']['brackets']:
                                left,right=f(b['left']),f(b['right'])
                                self.assertEqual(right-left,(f(domain['right'])-f(domain['left']))/2**40)
                                self.assertTrue(b['opposite_endpoint_signs'])
                                self.assertLess(poly.evaluate(power,left)*poly.evaluate(power,right),0);crossings+=1
                    count+=1
        self.assertEqual(count,496);self.assertEqual(last_piece,1984);self.assertEqual(crossings,1)

    def test_all_1488_interior_replays_precision_conservation_and_endpoint_gates(self):
        count=0;passes=0
        for w,source in zip(self.report['windows'],self.source):
            for level,original in zip(w['levels'],source['levels']):
                for row in level['rows']:
                    prepared=experiment.prepare(self.network,original['reference'],row['index'])
                    self.assertTrue(all(m['passed'] for m in row['endpoint_replay'].values()))
                    self.assertEqual(len(row['queries']),3)
                    for q,u in zip(row['queries'],experiment.FRACTIONS):
                        self.assertIsNone(q['failure']);self.assertEqual(f(q['u']),u)
                        self.assertEqual(f(q['time_s']),prepared['times'][1]+u*prepared['h'])
                        a=experiment.query(self.network,self.graph,prepared,u,80)
                        b=experiment.query(self.network,self.graph,prepared,u,100)
                        for name,v in a['vectors'].items():
                            self.assertEqual(list(map(str,v)),q['vectors'][name])
                            self.assertEqual(curvature.metrics(v,b['vectors'][name]),q['precision'][name])
                            self.assertTrue(q['precision'][name]['passed'])
                        self.assertEqual(q['knee_below'],a['knee_below']);self.assertEqual(q['algebra'],a['algebra'])
                        self.assertTrue(all(m['passed'] for m in q['algebra'].values()))
                        self.assertLess(max(map(abs,a['vectors']['dynamic_conservation_error_a'])),D('1e-30'))
                        self.assertTrue(q['observed_branches_below_10fv']);passes+=q['observed_kcl_below_10pa'];count+=1
        self.assertEqual(count,1488);self.assertEqual(passes,315)

    def test_24_newton_reconstructions_72_exact_rate_replays_and_288_chain_fd_checks(self):
        count=0;checks=0
        with localcontext() as ctx:
            ctx.prec=100;p=self.network.network.latch.device.parameters
            for w,source in zip(self.report['windows'],self.source):
                for level,original in zip(w['levels'],source['levels']):
                    ref=original['reference']
                    for index in (2,31,63):
                        row=level['rows'][index-2];fi=ref['samples'][index]['fine_step_index']
                        states=[unpack(self.network,ref['steps'][j]['history']).current for j in range(fi,fi-4,-1)]
                        times=list(map(f,row['normalized_support']));h=f(row['support_times_s'][0])-f(row['support_times_s'][1])
                        xs=[[F(a)+F(b) for a,b in zip(s.joint.node_v,s.node_low_v)] for s in states]
                        qs=[[F(cap)*(F(a)+F(b)) for (_,_,_,cap,_),(a,b) in zip(self.network.network.branches,s.capacitor_pairs_v)]+
                            [F(v) for d in s.latch.devices for v in (d.be_c,d.bc_c)] for s in states]
                        for q,u in zip(row['queries'],experiment.FRACTIONS):
                            x=[independent_newton(times,[v[j] for v in xs],u)[0] for j in range(94)]
                            charge=[independent_newton(times,[v[j] for v in qs],u) for j in range(25)]
                            self.assertTrue(curvature.metrics([law.decimal_fraction(d/h) for _,d in charge],list(map(D,q['vectors']['charge_rate_a'])))['passed'])
                            exact=[x[a]-(F(fixed) if b is None else x[b])-value/F(cap)-F(resistance)*slope/h
                                for (a,b,fixed,cap,resistance),(value,slope) in zip(self.network.network.branches,charge)]
                            self.assertTrue(curvature.metrics(list(map(law.decimal_fraction,exact)),list(map(D,q['vectors']['branch_equation_v'])))['passed'])
                            for i,terminals in enumerate(self.network.network.latch.terminals):
                                for j,(other,dep,transit,scale) in enumerate(((2,p.depletion_be,p.transit_forward_s,p.emission_be_v),
                                    (1,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v))):
                                    def junction(at):
                                        vv=[independent_newton(times,[z[node] for z in xs],at)[0] if node is not None else F(fixed) for node,fixed in terminals]
                                        v=law.decimal_fraction(p.polarity*(vv[0]-vv[other]))
                                        return curvature.junction_values(dep,transit,p.saturation_a,scale,v)[0],v<law.decimal_fraction(F(dep.forward_fraction*dep.potential_v))
                                    eps=F(1,10**8);plus,sp=junction(u+eps);minus,sm=junction(u-eps)
                                    self.assertEqual(sp,sm)
                                    fd=(plus-minus)/(2*law.decimal_fraction(eps*h))
                                    self.assertTrue(curvature.metrics([D(q['vectors']['nonlinear_chain_rate_a'][2*i+j])],[fd])['passed']);checks+=1
                            count+=1
        self.assertEqual(count,72);self.assertEqual(checks,288)

    def test_storage_sources_and_no_physical_bound_promotion(self):
        summary=json.loads(experiment.SUMMARY.read_text());s=summary['storage']
        self.assertEqual(len(self.raw),s['bytes']);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),s['compressed_sha256'])
        self.assertEqual(hashlib.sha256(canonical(self.report)).hexdigest(),s['canonical_json_sha256'])
        self.assertEqual(gzip.decompress(self.raw),canonical(self.report))
        for name,expected in self.report['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        self.assertEqual(self.report['root_cover_depth'],40);self.assertEqual(self.report['new_nonlinear_solves'],0)
        self.assertTrue(self.report['diagnostic_only']);self.assertTrue(self.report['exact_polynomial_constraints'])
        for key in ('prior_reports_modified','integrator_changed','physical_trajectory_bound','exact_temporal_defect_known',
                    'independent_error_estimator','temporal_error_bound_admitted','physical_switching_admitted','audio_admitted','deadline_admitted'):
            self.assertFalse(self.report[key])


if __name__=='__main__':unittest.main()
