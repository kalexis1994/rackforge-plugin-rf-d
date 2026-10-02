import gzip,hashlib,json,sys,unittest
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_continuous_charge as experiment
import loudness_latch_bdf_charge_defect as law
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import lift
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from bjt_charge_ngspice_probes import model_parameters


def fraction(record):return F(record['numerator'],record['denominator'])


def independent_static(g,x):
    """Device terminal currents assembled independently of the primary evaluator."""
    out=[D(0)]*94;boundary=D(0)
    def v(i):return x[i] if isinstance(i,int) else lift(g['fixed'][i])
    def add(i,current):
        nonlocal boundary
        if isinstance(i,int):out[i]+=current
        else:boundary+=current
    for r in g['resistors']+g['conductances']:
        current=(v(r['left'])-v(r['right']))*(1/lift(r['ohm']) if 'ohm' in r else lift(r['siemens']))
        add(r['left'],current);add(r['right'],-current)
    for q in g['bjts']:
        b,c,e=q['base'],q['collector'],q['emitter'];s=q['polarity']
        forward=lift(q['is_a'])*((s*(v(b)-v(e))/lift(q['vt'])).exp()-1)
        reverse=lift(q['is_a'])*((s*(v(b)-v(c))/lift(q['vt'])).exp()-1)
        # Separate forward/reverse terminal triplets, rather than reused KCL.
        bf=lift(q['beta_forward']);br=lift(q['beta_reverse'])
        for i,current in ((b,s*forward/bf),(c,s*forward),(e,-s*forward*(1+1/bf)),
                          (b,s*reverse/br),(c,-s*reverse*(1+1/br)),(e,s*reverse)):
            add(i,current)
    for q in g['diodes']:
        current=lift(q['is_a'])*(((v(q['anode'])-v(q['cathode']))/(lift(q['ideality'])*lift(q['vt']))).exp()-1)
        add(q['anode'],current);add(q['cathode'],-current)
    return out,boundary


class ContinuousCharge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.source=json.loads(gzip.decompress(experiment.proxy.REFERENCE.read_bytes()))['windows']
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))
        cls.graph=curvature.graph(cls.network,10.)

    def test_all_496_replays_precision_algebra_and_continuous_observations(self):
        count=0;passes=0;knees=0
        for w,source in zip(self.report['windows'],self.source):
            self.assertEqual(w['name'],source['name'])
            for level,original in zip(w['levels'],source['levels']):
                self.assertEqual(level['subdivisions'],original['reference']['subdivisions'])
                self.assertEqual(level['skipped_indices'],[0,1])
                for row in level['rows']:
                    self.assertEqual(row['index'],count%62+2)
                    a=experiment.evaluate_point(self.network,self.graph,original['reference'],row['index'],80)
                    b=experiment.evaluate_point(self.network,self.graph,original['reference'],row['index'],100)
                    for key,v in a['vectors'].items():
                        self.assertEqual(list(map(str,v)),row['vectors'][key])
                        self.assertEqual(curvature.metrics(v,b['vectors'][key]),row['precision'][key])
                        self.assertTrue(row['precision'][key]['passed'])
                    self.assertEqual(a['algebra'],row['algebra'])
                    self.assertTrue(all(v['passed'] for v in row['algebra'].values()))
                    self.assertEqual(a['knee_crossings'],row['knee_crossings']);knees+=sum(row['knee_crossings'])
                    self.assertTrue(row['observed_lifted_fine_kcl_below_10pa'])
                    self.assertTrue(row['observed_continuous_branches_below_10fv'])
                    passes+=row['observed_continuous_kcl_below_10pa']
                    self.assertLess(max(map(abs,a['vectors']['dynamic_conservation_error_a'])),D('1e-30'))
                    self.assertEqual(a['fine_publication'],row['fine_publication'])
                    self.assertLess(row['fine_publication']['max_published_kcl_a'],1e-11)
                    count+=1
        self.assertEqual(count,496);self.assertEqual(passes,106);self.assertEqual(knees,1)

    def test_24_independent_exact_rate_incidence_and_series_equation_replays(self):
        count=0
        for w,source in zip(self.report['windows'],self.source):
            for level,original in zip(w['levels'],source['levels']):
                ref=original['reference']
                for index in (2,31,63):
                    row=level['rows'][index-2];fi=ref['samples'][index]['fine_step_index']
                    states=[unpack(self.network,ref['steps'][j]['history']).current for j in range(fi,fi-4,-1)]
                    qs=[[F(cap)*(F(a)+F(b)) for (_,_,_,cap,_),(a,b) in zip(self.network.network.branches,s.capacitor_pairs_v)]+
                        [F(v) for d in s.latch.devices for v in (d.be_c,d.bc_c)] for s in states]
                    xs=[[F(a)+F(b) for a,b in zip(s.joint.node_v,s.node_low_v)] for s in states]
                    tt=list(map(fraction,row['fine_times_s']));rates={}
                    for name,records in row['weights'].items():
                        weights=list(map(fraction,records));n=len(weights)
                        self.assertEqual(sum(weights,F(0)),0)
                        if name!='binary':
                            for degree in range(n):
                                self.assertEqual(sum((v*(t-tt[0])**degree for v,t in zip(weights,tt)),F(0)),F(degree==1))
                        rates[name]=[sum((v*q[k] for v,q in zip(weights,qs)),F(0)) for k in range(25)]
                        shifted=[sum((v*(q[k]+F(7,13)) for v,q in zip(weights,qs)),F(0)) for k in range(25)]
                        self.assertEqual(rates[name],shifted)
                    coeff=row['fine_coefficients'];h=F(row['fine_dt_s'])
                    direct=[(F(coeff['a0'])*(a-b)-F(coeff['a2'])*(b-c))/h for a,b,c in zip(*qs[:3])]
                    self.assertEqual(direct,rates['binary'])
                    delta=[a-b for a,b in zip(rates['cubic'],rates['binary'])]
                    nodal=[F(0)]*94;boundary=F(0)
                    for (a,b,_,_,_),q in zip(self.network.network.branches,delta[:21]):
                        nodal[a]+=q
                        if b is None:boundary-=q
                        else:nodal[b]-=q
                    s=self.network.network.latch.device.parameters.polarity
                    for j,terminals in enumerate(self.network.network.latch.terminals):
                        be,bc=delta[21+2*j:23+2*j]
                        for (node,_),q in zip(terminals,(s*(be+bc),-s*bc,-s*be)):
                            if node is None:boundary+=q
                            else:nodal[node]+=q
                    self.assertEqual(sum(nodal,F(0))+boundary,0)
                    with localcontext() as ctx:
                        ctx.prec=100
                        for name,key in (('cubic','charge_cubic_rate_a'),('quadratic','charge_quadratic_rate_a'),('binary','fine_binary_rate_a')):
                            self.assertTrue(curvature.metrics(list(map(law.decimal_fraction,rates[name])),list(map(D,row['vectors'][key])))['passed'])
                        self.assertTrue(curvature.metrics(list(map(law.decimal_fraction,nodal)),list(map(D,row['vectors']['kcl_derivative_delta_a'])))['passed'])
                        for name,key in (('cubic','continuous_branch_equation_v'),('binary','fine_binary_branch_equation_v')):
                            exact=[xs[0][a]-(F(fixed) if b is None else xs[0][b])-q/F(cap)-F(resistance)*rate
                                for (a,b,fixed,cap,resistance),q,rate in zip(self.network.network.branches,qs[0],rates[name])]
                            self.assertTrue(curvature.metrics(list(map(law.decimal_fraction,exact)),list(map(D,row['vectors'][key])))['passed'])
                        for j in range(21):
                            if j!=17:self.assertEqual(D(row['vectors']['branch_derivative_delta_v'][j]),0)
                    count+=1
        self.assertEqual(count,24)
        with self.assertRaises(ValueError):experiment.derivative((F(1),F(1)),[[D(1)],[D(2)]])
        with self.assertRaises(ValueError):experiment.incidence(self.network,[D(0)])

    def test_independent_device_currents_and_96_junction_capacitance_fd_checks(self):
        count=0
        with localcontext() as ctx:
            ctx.prec=100
            p=self.network.network.latch.device.parameters
            for w,source in zip(self.report['windows'],self.source):
                for level,original in zip(w['levels'],source['levels']):
                    ref=original['reference']
                    for index in (2,31,63):
                        row=level['rows'][index-2];state=unpack(self.network,ref['samples'][index]['history']).current
                        x=[lift(a)+lift(b) for a,b in zip(state.joint.node_v,state.node_low_v)]
                        static,boundary=independent_static(self.graph,x)
                        self.assertTrue(curvature.metrics(static,list(map(D,row['vectors']['static_kcl_a'])))['passed'])
                        self.assertLess(abs(sum(static,D(0))+boundary),D('1e-30'))
                        for terminals in self.network.network.latch.terminals:
                            vv=[x[j] if j is not None else lift(fixed) for j,fixed in terminals]
                            for other,dep,transit,scale in ((2,p.depletion_be,p.transit_forward_s,p.emission_be_v),
                                                        (1,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v)):
                                v=p.polarity*(vv[0]-vv[other]);knee=lift(dep.forward_fraction*dep.potential_v)
                                eps=min(D('1e-8'),abs(v-knee)/4)
                                self.assertGreater(eps,0)
                                _,c,_=curvature.junction_values(dep,transit,p.saturation_a,scale,v)
                                plus=curvature.junction_values(dep,transit,p.saturation_a,scale,v+eps)[0]
                                minus=curvature.junction_values(dep,transit,p.saturation_a,scale,v-eps)[0]
                                self.assertTrue(curvature.metrics([c],[(plus-minus)/(2*eps)])['passed']);count+=1
        self.assertEqual(count,96)

    def test_storage_sources_scope_and_248_cross_refinement_differences(self):
        summary=json.loads(experiment.SUMMARY.read_text());storage=summary['storage']
        self.assertEqual(len(self.raw),storage['bytes'])
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),storage['compressed_sha256'])
        self.assertEqual(hashlib.sha256(canonical(self.report)).hexdigest(),storage['canonical_json_sha256'])
        self.assertEqual(gzip.decompress(self.raw),canonical(self.report))
        self.assertEqual(len(experiment.PATHS),len(self.report['source_sha256']))
        for name,expected in self.report['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        with localcontext() as ctx:
            ctx.prec=80
            for w in self.report['windows']:
                for a,b,diff in zip(w['levels'][0]['rows'],w['levels'][1]['rows'],w['differences']):
                    self.assertEqual(a['time_s'],b['time_s']);self.assertEqual(a['time_s'],diff['time_s'])
                    self.assertEqual([str(D(v)-D(u)) for u,v in zip(a['vectors']['continuous_kcl_a'],b['vectors']['continuous_kcl_a'])],diff['continuous_kcl_4_minus_2_a'])
        self.assertEqual(self.report['new_nonlinear_solves'],0)
        self.assertTrue(self.report['diagnostic_only'])
        for k in ('prior_reports_modified','integrator_changed','exact_temporal_defect_known','independent_error_estimator',
                  'temporal_error_bound_admitted','physical_switching_admitted','audio_admitted','deadline_admitted'):
            self.assertFalse(self.report[k])


if __name__=='__main__':unittest.main()
