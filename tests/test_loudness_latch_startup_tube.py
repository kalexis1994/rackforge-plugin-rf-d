from pathlib import Path
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_startup_tube as producer
from loudness_latch_bdf_doubling_survey import canonical
from test_loudness_latch_dc_anchor import independent_point_jacobian
law=producer.law
iv=law.iv
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(b):return hashlib.sha256(b).hexdigest()

class StartupTube(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=read(producer.OUTPUT);cls.startup=read(producer.prior.OUTPUT)
        constructor=producer.prior.prior.prior.prior
        cls.dc=read(constructor.OUTPUT);cls.network=constructor.CompensatedBdfNetwork(200,constructor.model_parameters(1,'finite_transit'))
        cls.g=read(producer.prior.prior.prior.OUTPUT)['graph']
        cls.initial=law.origin.restore(cls.network,cls.startup['origin']);cls.endpoint=producer.prior.unpack(cls.network,cls.startup['rows'][0]['history'])
        cls.prepared=law.prepare(cls.network,cls.initial,cls.endpoint)

    def test_two_real_endpoints_affine_memory_and_exact_rc_constraints(self):
        p=self.prepared;r=self.report
        self.assertEqual(list(map(str,p['support_sha256'])),r['prepared']['support_sha256'])
        self.assertEqual(p['h'],F(self.endpoint.time_s));self.assertEqual(p['h'],F(r['duration_s']))
        for u,state in ((F(0),self.initial.current),(F(1),self.endpoint.current)):
            self.assertEqual([law.poly.evaluate(v,u) for v in p['x']],law.origin.state_values(state))
            self.assertEqual([law.poly.evaluate(v,u) for v in p['y_linear']],law.origin.charge_coordinates(self.network.network,state)[:21])
        for port,yp,equation in zip(law.event.ports(self.network),p['y_linear'],p['equations']):
            for u in (F(0),F(1,3),F(1)):
                x=[law.poly.evaluate(v,u) for v in p['x']];v=sum((a*x[i] for i,a in port['a'].items()),F(0))-port['fixed']
                expected=law.poly.evaluate(yp,u)-v+port['tau']*law.poly.evaluate(law.poly.differentiate(yp),u)/p['h']
                self.assertEqual(law.poly.evaluate(equation,u),expected)
        self.assertEqual(p['q'][21:],[(F(0),)]*4);self.assertEqual(r['real_support_states'],2);self.assertFalse(p['fabricated_history'])
        with self.assertRaises(ValueError):law.prepare(self.network,self.endpoint,self.initial)

    def test_initial_charge_box_and_identity_norm_conversion(self):
        r=self.report;weights=list(map(F,r['weights']));anchor=law.initial_memory(self.network,self.prepared,self.dc,weights)
        self.assertEqual(anchor,r['initial_memory']);self.assertEqual(weights,list(map(F,self.dc['memory_enclosure']['weights'])))
        self.assertEqual(anchor['norm_conversion_factor'],'1');self.assertTrue(anchor['same_dc_norm'])
        self.assertTrue(anchor['constitutive_initial_mismatch_included'])
        for row in anchor['rows']:
            actual=tuple(map(F,row['actual_charge_interval_c']));reconstructed=tuple(map(F,row['reconstructed_initial_charge_interval_c']))
            difference=iv.sub(actual,reconstructed);self.assertEqual(list(map(str,difference)),row['charge_error_interval_c'])
            scale=F(self.dc['memory_enclosure']['rows'][row['index']]['scale_c_per_v'])
            self.assertEqual(F(row['coordinate_error_upper_v']),iv.magnitude(difference)/scale)
            self.assertEqual(F(row['weighted_error_upper_v']),weights[row['index']]*iv.magnitude(difference)/scale)
        self.assertEqual(F(anchor['error_upper_v']),max(F(v['weighted_error_upper_v']) for v in anchor['rows']))

    def test_decimal_queries_constitutive_rates_conservation_and_interval_bounds(self):
        r=self.report;p=self.prepared
        for q in r['queries']:
            u=F(q['u']);cell=min(7,int(u*8));bounds=r['base_cells'][cell]['residual_bounds']
            for precision,name in ((80,'decimal80'),(100,'decimal100')):
                actual=law.query(self.network,self.g,p,u,precision);self.assertEqual(actual,q[name])
                self.assertLess(abs(D(actual['dynamic_conservation_error_a'])),D('1e-70'))
                for i,(value,bound) in enumerate(zip(actual['kcl_a'],bounds['constitutive_pointwise_upper_a'])):
                    if i!=61:
                        self.assertLessEqual(abs(F(value)),F(bound));continue
                    # J7-load is a single linear shunt. Its enclosure is exact;
                    # a rounded Decimal product is a diagnostic, not an exact real.
                    shunts=[v for v in self.g['conductances'] if v['left']==61]
                    self.assertEqual(len(shunts),1);self.assertEqual(shunts[0]['right'],'GND')
                    self.assertFalse(any(61 in v.values() for name in ('resistors','bjts','diodes') for v in self.g[name]))
                    exact_v=law.poly.evaluate(p['x'][61],u);conductance=F(shunts[0]['siemens'])
                    contributions=[]
                    for port,qp in zip(law.event.ports(self.network)[:21],p['q'][:21]):
                        if 61 in port['a']:
                            contributions.append((port['a'][61],law.poly.evaluate(law.poly.differentiate(qp),u)/p['h']))
                    self.assertFalse(any(61 in port['a'] for port in law.event.ports(self.network)[21:]))
                    exact_current=conductance*exact_v+sum((a*rate for a,rate in contributions),F(0))
                    self.assertLessEqual(abs(exact_current),F(bound))
                    with localcontext() as ctx:
                        ctx.prec=precision;rounded_v=law.event.decimal(exact_v)
                        static=D.from_float(shunts[0]['siemens'])*rounded_v;dynamic=D(0)
                        # Independently replay this purely linear row; cancellation
                        # of larger currents need not round toward its exact bound.
                        for a,rate in contributions:dynamic+=law.event.decimal(a)*law.event.decimal(rate)
                        expected=static+dynamic
                    self.assertEqual(D(value),expected)
                for i,value in enumerate(actual['constraint_v'][:21]):
                    upper=F(r['base_cells'][cell]['forcing_inputs']['constraint_point_v'][i])
                    exact=law.poly.evaluate(p['equations'][i],u);self.assertLessEqual(abs(exact),upper)
                    with localcontext() as ctx:
                        ctx.prec=precision;self.assertEqual(D(value),law.event.decimal(exact))
            with localcontext() as ctx:
                ctx.prec=100;params=self.network.network.latch.device.parameters
                for j,(voltage,dep,t,em) in enumerate(p['junctions']):
                    v=law.event.decimal(law.poly.evaluate(voltage,u));slope=law.event.decimal(law.poly.evaluate(law.poly.differentiate(voltage),u)/p['h'])
                    _,cap,_=law.event.junction_values(dep,t,params.saturation_a,em,v)
                    self.assertEqual(D(q['decimal100']['charge_rate_a'][21+j]),cap*slope)
            self.assertEqual(q['decimal100']['constraint_v'][21:],['0']*4)

    def test_all_residual_cells_tube_covers_inverse_and_metric_replay(self):
        r=self.report;p=self.prepared;scales=list(map(F,r['descriptor_scales']));weights=list(map(F,r['weights']));gains=law.gains(self.network,self.g)
        for k,base in enumerate(r['base_cells']):
            left,right=F(base['left']),F(base['right']);residual,forcing=law.forcing(self.network,self.g,p,left,right)
            # Compare canonical rational string serialization to preserve JSON tuple/list types.
            def serial(v):
                if isinstance(v,F):return str(v)
                if isinstance(v,dict):return {k:serial(x) for k,x in v.items()}
                if isinstance(v,(tuple,list)):return [serial(x) for x in v]
                return v
            self.assertEqual(serial(residual),base['residual_bounds']);self.assertEqual(forcing,base['forcing_inputs'])
            constant,terms=law.weighted.compile_terms(self.network,self.g,p,base['inverse_binary'],scales)
            for trial,radius in zip(r['trials'],producer.RADII):
                row=trial['cells'][k];cover=law.inflated_cover(constant,terms,gains,left,right,radius)
                self.assertEqual(row['cover'],cover);self.assertTrue(cover['strict_contraction']);self.assertTrue(cover['includes_mean_descriptors'])
                inverse,certificate=law.cells.structured_inverse(base['inverse_binary'],scales,cover,F(cover['contraction_upper']))
                self.assertEqual(certificate,row['inverse_certificate']);self.assertEqual(law.cells.metrics(inverse,94,weights,forcing),row['metrics'])
                self.assertTrue(row['inverse_certified']);self.assertLess(F(cover['contraction_upper']),1)
                for domain in cover['coefficient_domains']:
                    if domain['kind']=='exponential':self.assertLessEqual(F(domain['upper']),45)
        with self.assertRaises(ValueError):law.inflated_cover(constant,terms,gains,0,1,0)
        with self.assertRaisesRegex(ValueError,'exponential domain'):law.inflated_cover(constant,terms,gains,0,1,10)

    def test_independent_interval_point_descriptor_inside_inflated_cover(self):
        r=self.report;p=self.prepared;base=r['base_cells'][0];row=r['trials'][0]['cells'][0];radius=F(r['trials'][0]['radius_v'])
        mid=(F(base['left'])+F(base['right']))/2
        # An independent corner lies in the prescribed potential tube, away from its center.
        x=[law.poly.evaluate(v,mid)+(radius if i%2 else -radius) for i,v in enumerate(p['x'])]
        j=independent_point_jacobian(self.g,x);j=[v+[(F(0),F(0))]*25 for v in j]+[[(F(0),F(0))]*119 for _ in range(25)]
        for port in law.event.ports(self.network):
            k=port['index'];index=94+k;v=sum((a*x[i] for i,a in port['a'].items()),F(0))
            v+=port['fixed'] if port['kind']=='junction' else -port['fixed']
            cap=(F(1),F(1)) if port['kind']=='linear' else iv.scale(iv.junction_bounds(port['dep'],port['transit'],port['sat'],port['emission'],v)[1],1/port['scale'])
            for i,a in port['a'].items():j[i][index]=(a*port['scale'],)*2;j[index][i]=iv.scale(cap,-a)
            j[index][index]=(port['tau'],)*2
        columns=[[(k,j[k][col]) for k in range(119) if j[k][col]!=(F(0),F(0))] for col in range(119)]
        d=list(map(F,r['descriptor_scales']));inverse=base['inverse_binary'];cover=row['cover']
        for i in range(119):
            for col in range(119):
                value=(F(i==col),)*2
                for k,v in columns[col]:value=iv.sub(value,iv.scale(v,d[i]*F(inverse[i][k])/d[col]))
                lo,hi=map(F,cover['preconditioned_defect_intervals'][i][col]);self.assertLessEqual(lo,value[1]);self.assertGreaterEqual(hi,value[0])

    def test_known_nonlinear_scalar_comparison_closes_and_insufficient_tube_rejects(self):
        # x=y, y'=-y²; constant reconstruction xhat=yhat=1 over h=1/10.
        # H^-1 gives node gain one, A=-2*x in [ -12/5, -8/5 ]; forcing=1.
        case=dict(inverse_certified=True,forcing_inputs=dict(left='0',right='1',duration_s='1/10'),
            metrics=dict(logarithmic_norm_upper_per_s='-8/5',integrated_forcing_norm_upper_v='1/10',
                node_from_weighted_memory_gain_upper='1',node_direct_forcing_upper_v='0'))
        result=law.close([case],0,F(1,5),0);self.assertTrue(result['accepted']);self.assertTrue(result['actual_dae_error_bound'])
        exact_error=F(1)-F(10,11);self.assertLessEqual(exact_error,F(result['peak_node_error_upper_v']))
        rejected=law.close([case],0,F(1,20),0);self.assertFalse(rejected['accepted']);self.assertFalse(rejected['actual_dae_error_bound'])
        self.assertIn('escapes',rejected['reason'])
        self.assertFalse(law.close([case|dict(inverse_certified=False)],0,1,0)['accepted'])
        self.assertFalse(law.close([case|dict(forcing_inputs=dict(left='1/2',right='1',duration_s='1/10'))],0,1,0)['accepted'])
        with self.assertRaises(ValueError):law.close([case],-1,1,0)

    def test_full_comparisons_reject_all_radii_without_promoting_conditional_bounds(self):
        r=self.report;self.assertIsNone(r['primary_trial_index']);self.assertEqual(len(r['trials']),3)
        for t in r['trials']:
            expected=law.close(t['cells'],F(r['initial_memory']['error_upper_v']),F(t['radius_v']),F(self.startup['initial_bound']['node_error_upper_v']))
            self.assertEqual(t['result'],expected);self.assertFalse(expected['accepted']);self.assertFalse(expected['actual_dae_error_bound'])
            self.assertGreaterEqual(F(expected['peak_node_error_upper_v']),F(t['radius_v']));self.assertIn('escapes',expected['reason'])
            self.assertTrue(all(c['inverse_certified'] for c in t['cells']))
        self.assertEqual(r['continuous_actual_error_certified_duration_s'],'0');self.assertFalse(r['first_interval_nonlinear_error_proven'])

    def test_storage_sources_scope_and_destinations(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();s=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-startup-tube/v1');self.assertEqual(sha(raw),s['compressed_sha256']);self.assertEqual(len(raw),s['bytes'])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),s['canonical_json_sha256'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS);self.assertNotEqual(producer.OUTPUT,producer.SUMMARY)
        self.assertEqual(r['new_nonlinear_solves'],0);self.assertEqual(r['new_preconditioners'],8)
        for flag in ('fabricated_history','original_integrator_modified','prior_reports_modified','numerical_gates_changed','first_interval_nonlinear_error_proven','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[flag],flag)
        self.assertTrue(r['constitutive_junction_path'])

if __name__=='__main__':unittest.main()
