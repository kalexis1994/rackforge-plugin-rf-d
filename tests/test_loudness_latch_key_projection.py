from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_key_projection as producer
import loudness_latch_bdf_static_precision_key_scaled as scaled
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_bdf_checkout_audit import git_bytes
from test_loudness_latch_dc_anchor import independent_point_jacobian
law=producer.law
iv=law.iv
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()

class KeyProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=read(producer.OUTPUT);cls.scaled=read(scaled.OUTPUT)
        cls.network=producer.prior.CompensatedBdfNetwork(200,producer.prior.model_parameters(1,'finite_transit'))
        cls.center=list(map(F,cls.report['candidates'][cls.report['primary_candidate_index']]['values']))

    def test_decimal_pivoting_known_solution_and_input_guards(self):
        with localcontext() as ctx:
            ctx.prec=80
            self.assertEqual(law.linear_solve([[D(0),D(2)],[D(3),D(4)]],[D(4),D(11)]),[D(1),D(2)])
            for a,b in (([],[]),([[D(0)]],[D(1)]),([[D(1),D(0)]],[D(1)])):
                with self.assertRaises(ValueError):law.linear_solve(a,b)
        with self.assertRaises(ValueError):law.residual(self.network,self.report['graph'],[0]*118,[0]*25)
        with self.assertRaises(ValueError):law.compile_event(self.network,self.report['graph'],[0]*119,[0]*24,[])
        x=self.center.copy();x[77]=F(0)
        with self.assertRaisesRegex(ValueError,'exponential domain'):law.residual(self.network,self.report['graph'],x,self.report['targets_coordinate_v'])

    def test_descriptor_derivative_charge_stamps_and_series_resistance(self):
        r=self.report;ports=law.ports(self.network)
        with localcontext() as ctx:
            ctx.prec=80;res,h=law.residual(self.network,r['graph'],self.center,r['targets_coordinate_v'])
            # Directional central difference of the actual residual, including rate variables.
            direction=[F(((i*7)%11)-5,5) for i in range(119)];eps=F(1,10**8)
            plus,_=law.residual(self.network,r['graph'],[v+eps*d for v,d in zip(self.center,direction)],r['targets_coordinate_v'],jacobian=False)
            minus,_=law.residual(self.network,r['graph'],[v-eps*d for v,d in zip(self.center,direction)],r['targets_coordinate_v'],jacobian=False)
            for i in range(119):
                direct=sum((h[i][j]*law.decimal(d) for j,d in enumerate(direction)),D(0));fd=(plus[i]-minus[i])/(2*law.decimal(eps))
                self.assertLessEqual(abs(fd-direct),D('1e-10')*max(abs(direct),D('1e-12')))
            for p in ports[:21]:
                k=p['index'];row=94+k
                for j in range(94):self.assertEqual(h[row][j],law.decimal(-p['a'].get(j,0)))
                self.assertEqual(h[row][row],law.decimal(p['tau']))
            self.assertEqual(ports[17]['tau'],F(self.network.network.branches[17][3])*25500)
            self.assertGreater(ports[17]['tau'],0)
            self.assertTrue(all(p['tau']==0 for p in ports if p['index']!=17))
            # The four junction current stamps conserve terminal current exactly.
            self.assertTrue(all(sum(p['a'].values())==1 for p in ports[21::2])) # BE goes to fixed ground.
            self.assertTrue(all(sum(p['a'].values())==0 for p in ports[22::2]))
            for p in ports:
                for i,a in p['a'].items():self.assertEqual(h[i][94+p['index']],law.decimal(a*p['scale']))

    def test_two_seed_newton_trace_publication_and_restored_equations(self):
        r=self.report;self.assertEqual(r['primary_candidate_index'],0);self.assertEqual(len(r['candidates']),2)
        dc=read(producer.prior.OUTPUT)
        targets=[F(p['stored_charge_c'])/F(p['scale_c_per_v']) for p in dc['memory_enclosure']['rows']]
        self.assertEqual(targets,list(map(F,r['targets_coordinate_v'])))
        for c,seed in zip(r['candidates'],producer.SEEDS):
            self.assertTrue(c['converged']);self.assertFalse(c['clock_advanced']);self.assertEqual(c['precision'],80)
            self.assertEqual(F(c['seed_node77_v']),seed);self.assertEqual(F(c['seed_values'][77]),seed)
            self.assertEqual(c['seed_values'][94:],['0']*25)
            self.assertLessEqual(len(c['iterations']),64)
            for step in c['iterations'][:-1]:
                trials=step['trials'];self.assertLessEqual(len(trials),25);self.assertTrue(trials[-1]['accepted'])
                with localcontext() as ctx:
                    ctx.prec=80;merit=max(D(step['kcl_upper_a'])/D('1e-11'),D(step['coordinate_constraint_upper_v'])/D('1e-14'))
                    alpha=D(2)**(-trials[-1]['halvings']);self.assertLess(D(trials[-1]['merit']),(1-D('1e-4')*alpha)*merit)
                self.assertTrue(all(not t['accepted'] for t in trials[:-1]))
            for p in (80,100):
                residual,_=law.residual(self.network,r['graph'],c['values'],targets,p,False)
                self.assertLess(max(map(abs,residual[:94])),D('1e-35'));self.assertLess(max(map(abs,residual[94:])),D('1e-35'))
        self.assertLess(max(abs(F(a)-F(b))*w for a,b,w in zip(r['candidates'][0]['values'],r['candidates'][1]['values'],law.WEIGHTS)),F(1,10**25))
        event=json.loads(json.dumps(r['event']));self.assertEqual(event['schema'],'rf-d/clock-free-key-event/v1')
        self.assertEqual(event['time_s'],0);self.assertEqual((event['key_before_v'],event['key_after_v']),(0,10))
        self.assertIsNone(event['previous_history']);self.assertIsNone(event['previous_dt_s']);self.assertFalse(event['dc_state'])
        rp,_=law.residual(self.network,r['graph'],event['node_v']+event['charge_coordinate_rates_v_per_s'],event['charge_coordinates_v'],100,False)
        self.assertEqual(list(map(str,rp)),r['publication']['decimal100_residual']);self.assertTrue(r['publication']['gates_passed'])
        self.assertTrue(r['publication']['canonical_round_trip']);self.assertFalse(r['publication']['history_fabricated'])
        self.assertGreater(F(event['node_v'][77]),9)

    def test_first_scale_certificates_and_rejections_are_preserved(self):
        r=self.report;c=law.compile_event(self.network,r['graph'],self.center,r['targets_coordinate_v'],r['inverse_binary'])
        self.assertEqual(len(r['certificates']),4)
        for row,radius in zip(r['certificates'],producer.RADII):
            self.assertEqual(row['nominal'],law.certify(c,radius))
            self.assertEqual(row['dc_charge_box'],law.certify(c,radius,r['dc_charge_deviation_intervals_v']))
            self.assertFalse(row['dc_charge_box']['accepted'])
        self.assertEqual([v['nominal']['accepted'] for v in r['certificates']],[True,True,False,False])
        self.assertFalse(r['binary_algebra']['accepted']);self.assertEqual(r['binary_algebra']['gate'],1e-10)
        self.assertIn('backward gates',r['binary_algebra']['reason'])
        self.assertIsNone(r['primary_certificate_index']);self.assertFalse(r['post_key_initial_error_known'])

    def test_scaled_bank_full_replay_and_separate_unit_bounds(self):
        r=self.report;s=self.scaled;self.assertEqual(len(s['certificates']),12)
        for offset,w in enumerate(scaled.RATE_WEIGHTS):
            compiled=law.compile_event(self.network,r['graph'],self.center,r['targets_coordinate_v'],r['inverse_binary'],[F(1)]*94+[w]*25)
            for cert,radius in zip(s['certificates'][offset*4:offset*4+4],producer.RADII):
                self.assertEqual(cert,law.certify(compiled,radius,r['dc_charge_deviation_intervals_v'])|dict(rate_weight_s=str(w)))
                if cert['accepted']:
                    q=F(cert['contraction_upper']);self.assertLess(q,1)
                    self.assertTrue(all(F(v)<radius for v in cert['weighted_row_image_radius_v']))
                    self.assertEqual(F(cert['weighted_posterior_error_upper_v']),F(cert['weighted_eta_upper_v'])/(1-q))
                self.assertTrue(all(F(t['range'][1])<=45 for t in cert['exponent_ranges']))
        primary=next(i for i,c in enumerate(s['certificates']) if c['accepted']);self.assertEqual(primary,s['primary_certificate_index'])
        cert=s['certificates'][primary];bounds=s['bounds'];error=F(cert['weighted_posterior_error_upper_v'])
        self.assertEqual(F(bounds['node_error_upper_v']),error);self.assertEqual(F(bounds['rate_error_upper_v_per_s']),error/F(cert['rate_weight_s']))
        self.assertEqual(list(map(F,bounds['node77_interval_v'])),[self.center[77]-error,self.center[77]+error])
        self.assertEqual(bounds['laboratory_event_center_sha256'],law.dc.digest(r['event']))
        self.assertFalse(bounds['binary_integrator_publication_error_included'])

    def test_independent_interval_point_jacobian_and_decimal_residual_products(self):
        r=self.report;s=self.scaled;cert=s['certificates'][s['primary_certificate_index']];w=list(map(F,cert['weights']))
        compiled=law.compile_event(self.network,r['graph'],self.center,r['targets_coordinate_v'],r['inverse_binary'],w)
        # Assemble point J from outgoing-current derivatives, then independent mass/constitutive laws.
        j=independent_point_jacobian(r['graph'],self.center[:94]);j=[row+[(F(0),F(0))]*25 for row in j]+[[(F(0),F(0))]*119 for _ in range(25)]
        for p in law.ports(self.network):
            row=94+p['index'];v=sum((a*self.center[i] for i,a in p['a'].items()),F(0))
            v+=p['fixed'] if p['kind']=='junction' else -p['fixed']
            cap=(F(1),F(1)) if p['kind']=='linear' else iv.scale(iv.junction_bounds(p['dep'],p['transit'],p['sat'],p['emission'],v)[1],1/p['scale'])
            for i,a in p['a'].items():
                j[i][row]=(a*p['scale'],)*2;j[row][i]=iv.scale(cap,-a)
            j[row][row]=(p['tau'],)*2
        columns=[[(k,j[k][col]) for k in range(119) if j[k][col]!=(F(0),F(0))] for col in range(119)]
        for i in range(119):
            for col in range(119):
                value=(F(i==col),)*2
                for k,v in columns[col]:value=iv.sub(value,iv.scale(v,w[i]*F(r['inverse_binary'][i][k])/w[col]))
                lo,hi=map(F,cert['defect_intervals'][i][col]);self.assertLessEqual(lo,value[1]);self.assertGreaterEqual(hi,value[0])
        for precision in (80,100):
            with localcontext() as ctx:
                ctx.prec=precision;res,_=law.residual(self.network,r['graph'],self.center,r['targets_coordinate_v'],precision,False)
                for i,row in enumerate(r['inverse_binary']):
                    value=law.decimal(w[i])*sum((D.from_float(v)*res[k] for k,v in enumerate(row)),D(0))
                    lo,hi=compiled['preconditioned_residual'][i];self.assertLessEqual(lo,F(value));self.assertGreaterEqual(hi,F(value))

    def test_parameter_box_coverage_and_known_linear_parameterized_solution(self):
        dc=read(producer.prior.OUTPUT);r=self.report
        for row,target,uncertainty in zip(dc['memory_enclosure']['rows'],r['targets_coordinate_v'],r['dc_charge_deviation_intervals_v']):
            expected=[F(v)/F(row['scale_c_per_v'])-F(target) for v in row['ideal_charge_interval_c']]
            self.assertEqual(expected,list(map(F,uncertainty)))
        # 119 independent linear equations; row0 has x0+2*delta_y0=0.
        c=dict(constant_defect=[[(F(0),F(0))]*119 for _ in range(119)],terms=[],junctions=[],
            preconditioned_residual=[(F(0),F(0))]*119,charge_sensitivity=[[F(0)]*25 for _ in range(119)],weights=[F(1)]*119)
        c['charge_sensitivity'][0][0]=F(2);u=[(F(-1,100),F(1,50))]+[(F(0),F(0))]*24
        proof=law.certify(c,F(1,20),u);self.assertTrue(proof['accepted']);self.assertEqual(F(proof['weighted_posterior_error_upper_v']),F(1,25))
        self.assertFalse(law.certify(c,F(3,100),u)['accepted'])
        for radius,u in ((0,u),(1,[]),(1,[(1,-1)]*25)):
            with self.assertRaises(ValueError):law.certify(c,radius,u)

    def test_storage_sources_failed_import_and_open_scopes(self):
        for p,r in ((producer,self.report),(scaled,self.scaled)):
            storage=json.loads(p.SUMMARY.read_text(encoding='utf-8'))['storage'];raw=p.OUTPUT.read_bytes()
            self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(len(raw),storage['bytes'])
            self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256'])
            for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
            self.assertNotIn(p.OUTPUT,p.PATHS);self.assertNotIn(p.SUMMARY,p.PATHS);self.assertNotEqual(p.OUTPUT,p.SUMMARY)
            for flag in ('clock_advanced','initial_error_known','full_path_coverage','actual_dae_error_bound','physical_trajectory_bound','audio_admitted','deadline_admitted','numerical_gates_changed','prior_parameters_changed','prior_reports_modified'):self.assertFalse(r[flag],flag)
        s=self.scaled;self.assertTrue(s['laboratory_post_key_initial_error_known']);self.assertFalse(s['binary_integrator_initial_error_known'])
        self.assertEqual(s['new_nonlinear_solves'],0);self.assertEqual(s['new_preconditioners'],0)
        attempt=json.loads((ROOT/'evidence/loudness_latch_bdf_static_precision_key_launch_attempts.json').read_text(encoding='utf-8'))['attempts'][0]
        self.assertEqual(attempt['numerical_candidates_evaluated'],0);self.assertFalse(attempt['measurement_written']);self.assertEqual(attempt['exit_code'],1)
        self.assertEqual(attempt['source_sha256_before'],attempt['source_sha256_after'])
        for name,h in attempt['source_sha256_before'].items():self.assertEqual(sha(git_bytes(attempt['git_head'],name)),h)

if __name__=='__main__':unittest.main()
