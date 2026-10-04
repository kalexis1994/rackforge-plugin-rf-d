from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from copy import deepcopy
import gzip,hashlib,json,math,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_post_key_startup as producer
from loudness_latch_bdf_probes import pack,unpack
from loudness_latch_bdf_reference import coefficients
from loudness_latch_bdf_doubling_survey import canonical
from circuit66_decimal_static import evaluate
law=producer.law
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(b):return hashlib.sha256(b).hexdigest()

class PostKeyStartup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=read(producer.OUTPUT);cls.fixed=read(producer.FIXED)
        dc=producer.prior.prior.prior
        cls.network=dc.CompensatedBdfNetwork(200,dc.model_parameters(1,'finite_transit'))
        cls.projection=read(producer.prior.prior.OUTPUT);cls.scaled=read(producer.prior.OUTPUT)

    def test_pair_conversion_known_rationals_and_all_publication_errors(self):
        for value in (F(0),F(1),F(-1,10),F(22,7),F(1,2**1074),F(2)**1000):
            pair,error=law.publish_pair(value);self.assertEqual(error,abs(sum(map(F,pair),F(0))-value))
            self.assertEqual(tuple(pair),law.pair(pair))
            if error:
                first=abs(F(pair[0])-value);self.assertLessEqual(error,first)
                self.assertLessEqual(error,F(math.ulp(pair[1]))/2)
        for bad in ('NaN','Infinity'):
            with self.assertRaises((ValueError,OverflowError)):law.publish_pair(bad)
        r=self.report;history=law.restore(self.network,r['origin']);event=self.projection['event']
        actual=law.state_values(history.current)
        nodes=[abs(v-F(c)) for v,c in zip(actual,event['node_v'])]
        rates=[abs(sum(map(F,p),F(0))-F(v)) for p,v in zip(r['origin']['auxiliary_rate_pairs_v_per_s'],event['charge_coordinate_rates_v_per_s'])]
        self.assertEqual(nodes,list(map(F,r['pair_publication_errors']['node_error_v'])))
        self.assertEqual(rates,list(map(F,r['pair_publication_errors']['rate_error_v_per_s'])))
        self.assertEqual(max(nodes),F(r['pair_publication_errors']['max_node_error_v']))
        self.assertEqual(max(rates),F(r['pair_publication_errors']['max_rate_error_v_per_s']))

    def test_origin_charge_conservation_complete_mirrors_and_json(self):
        r=self.report;pre=unpack(self.network,self.fixed['initial']);origin,errors=law.publish(self.network,pre,self.projection['event'])
        self.assertEqual(canonical(origin),canonical(r['origin']));self.assertEqual(errors,r['pair_publication_errors'])
        restored=law.restore(self.network,json.loads(json.dumps(origin)));self.assertEqual(canonical(pack(restored)),canonical(r['initial_history']))
        self.assertEqual(restored.current.capacitor_pairs_v,pre.current.capacitor_pairs_v)
        self.assertEqual(restored.current.latch,pre.current.latch)
        self.assertEqual(restored.current.joint.audio_capacitor_v,pre.current.joint.audio_capacitor_v)
        self.assertEqual(restored.current.joint.c10_v,pre.current.joint.c10_v)
        self.assertEqual(restored.current.joint.contour.capacitor_v,pre.current.joint.contour.capacitor_v)
        self.assertEqual(law.charge_coordinates(self.network.network,restored.current),list(map(F,self.projection['targets_coordinate_v'])))
        self.assertTrue(law.mirrors(self.network,restored.current,10.))
        self.assertEqual(restored.current.joint.contour.node_v['KEYBOARD_TRIGGER'],10.)
        self.assertIsNone(restored.previous);self.assertIsNone(restored.previous_dt_s);self.assertIsNone(restored.previous_key_v)
        self.assertEqual(restored.time_s,0.);self.assertEqual(restored.key_v,10.)
        self.assertNotEqual(canonical(pack(restored)),canonical(self.fixed['initial']))

    def test_origin_guards_reject_modified_provenance_history_and_rate_pairs(self):
        origin=self.report['origin'];pre=unpack(self.network,self.fixed['initial']);event=self.projection['event']
        for field,value in (('schema','unknown'),('role','dc'),('time_s',1),('dc_state',True),('fabricated_previous_history',True),('first_step_method','bdf2')):
            with self.assertRaises(ValueError):law.restore(self.network,origin|{field:value})
        for edit in ('clock','key','rates'):
            bad=deepcopy(origin)
            if edit=='clock':bad['history']['time_s']=1.
            if edit=='key':bad['history']['key_v']=9.
            if edit=='rates':bad['auxiliary_rate_pairs_v_per_s']=[]
            with self.assertRaises(ValueError):law.restore(self.network,bad)
        for field,value in (('pre_history_sha256','wrong'),('key_before_v',1),('time_s',1),('dc_state',True)):
            with self.assertRaises(ValueError):law.publish(self.network,pre,event|{field:value})
        bad=deepcopy(event);bad['charge_coordinates_v'][0]='1'
        with self.assertRaisesRegex(ValueError,'preserve'):law.publish(self.network,pre,bad)
        state=law.restore(self.network,origin).current
        state.joint.contour.node_v['KEYBOARD_TRIGGER']=0.
        with self.assertRaisesRegex(ValueError,'mirror'):law.mirrors(self.network,state,10.)

    def test_outward_event_checks_decimal_inclusion_and_initial_error_addition(self):
        r=self.report;check=law.event_check(self.network,self.projection['graph'],r['origin'])
        self.assertEqual(check,r['event_publication']);self.assertTrue(check['gates_passed']);self.assertTrue(check['domain_passed'])
        for value,interval in zip(check['decimal100_residual'],check['kcl_intervals_a']+check['constraint_intervals_v']):
            lo,hi=map(F,interval)
            # Linear exact rational equations may have zero interval width;
            # Decimal is diagnostic and can round in the last place.
            self.assertLessEqual(lo-F(1,10**90),F(value));self.assertGreaterEqual(hi+F(1,10**90),F(value))
        b=r['initial_bound'];e=r['pair_publication_errors'];s=self.scaled['bounds']
        self.assertEqual(F(b['node_error_upper_v']),F(s['node_error_upper_v'])+F(e['max_node_error_v']))
        self.assertEqual(F(b['auxiliary_rate_error_upper_v_per_s']),F(s['rate_error_upper_v_per_s'])+F(e['max_rate_error_v_per_s']))
        self.assertEqual(b['event_enclosure_sha256'],sha(producer.prior.OUTPUT.read_bytes()))
        dc=read(producer.prior.prior.prior.OUTPUT);self.assertEqual(b['initial_memory_weights'],dc['memory_enclosure']['weights'])
        self.assertTrue(b['initial_memory_box_unchanged']);self.assertTrue(r['post_key_published_initial_error_known'])
        self.assertLess(F(check['kcl_upper_a']),F(1,10**11));self.assertLess(F(check['constraint_upper_v']),F(1,10**14))

    def test_every_clock_history_startup_order_and_canonical_lineage(self):
        r=self.report;self.assertTrue(r['complete']);self.assertIsNone(r['stop']);self.assertEqual(len(r['rows']),512)
        self.assertEqual(r['clock'],self.fixed['reference_clock'][:producer.COUNT]);old=unpack(self.network,r['initial_history'])
        for i,(row,slot) in enumerate(zip(r['rows'],r['clock'])):
            self.assertEqual(row['index'],i);self.assertTrue(row['accepted']);self.assertEqual(row['dt_s'],slot['dt_s'])
            self.assertEqual(row['previous_history_sha256'],law.law.dc.digest(pack(old)))
            new=unpack(self.network,row['history']);self.assertEqual(new.time_s,old.time_s+row['dt_s']);self.assertEqual(new.time_s,slot['time_s'])
            self.assertEqual(new.previous_dt_s,row['dt_s']);self.assertEqual(canonical(pack(old)['current']),canonical(pack(new)['previous']))
            self.assertEqual(new.previous_key_v,10.);self.assertEqual(new.key_v,10.)
            expected='backward-euler-startup' if i==0 else 'variable-bdf2-charge/v1'
            self.assertEqual(row['diagnostics']['method'],expected);self.assertEqual(row['independent_discrete']['method'],expected)
            if i:self.assertEqual(row['diagnostics']['coefficients'],coefficients(row['dt_s'],old.previous_dt_s))
            self.assertTrue(law.mirrors(self.network,new.current,10.));old=new
        self.assertEqual(canonical(pack(old)),canonical(r['final']))
        self.assertEqual(r['accepted_intervals'],512)

    def test_all_independent_discrete_residuals_against_outgoing_current_graph(self):
        # Assemble charge currents directly, independently of the event residual adapter.
        r=self.report;old=unpack(self.network,r['initial_history']);g=self.projection['graph'];ports=law.law.ports(self.network)
        with localcontext() as ctx:
            ctx.prec=100
            for row in r['rows']:
                new=unpack(self.network,row['history']);h=row['dt_s'];x=law.state_values(new.current)
                y=law.charge_coordinates(self.network.network,new.current);y0=law.charge_coordinates(self.network.network,old.current)
                ym=y0 if old.previous is None else law.charge_coordinates(self.network.network,old.previous)
                c={'a0':1.,'a2':0.} if old.previous is None else coefficients(h,old.previous_dt_s)
                a0,a2=map(law.law.decimal,(c['a0'],c['a2']))
                rates=[(a0*(law.law.decimal(a)-law.law.decimal(b))-a2*(law.law.decimal(b)-law.law.decimal(z)))/law.law.decimal(h) for a,b,z in zip(y,y0,ym)]
                static,_=evaluate(g,[law.law.decimal(v) for v in x],100,False);linear=[]
                for p in ports:
                    k=p['index'];current=law.law.decimal(p['scale'])*rates[k]
                    for i,a in p['a'].items():static[i]+=law.law.decimal(a)*current
                    if p['kind']=='linear':
                        voltage=sum((law.law.decimal(a)*law.law.decimal(x[i]) for i,a in p['a'].items()),D(0))-law.law.decimal(p['fixed'])
                        linear.append(law.law.decimal(y[k])-voltage+law.law.decimal(p['tau'])*rates[k])
                direct=row['independent_discrete']
                self.assertLess(abs(max(map(abs,static))-D(direct['decimal100_kcl_upper_a'])),D('1e-80'))
                self.assertLess(abs(max(map(abs,linear))-D(direct['decimal100_linear_constraint_upper_v'])),D('1e-80'))
                self.assertTrue(direct['kcl_passed']);self.assertTrue(direct['linear_constraint_passed'])
                self.assertLess(max(map(abs,static)),D('1e-11'));self.assertLess(max(map(abs,linear)),D('1e-14'));old=new

    def test_publication_gates_and_endpoint_comparisons_preserve_all_coordinates(self):
        r=self.report
        for row in r['rows']:
            pub=row['publication'];diag=row['diagnostics'];self.assertLess(diag['max_kcl_a'],1e-11);self.assertLess(diag['correction_v'],1e-8)
            self.assertLess(pub['max_published_kcl_a'],1e-11);self.assertLess(pub['max_branch_equation_error_v'],1e-14)
            new=unpack(self.network,row['history']);reference=unpack(self.network,self.fixed['rows'][row['index']]['history'])
            expected=producer.comparison_row(new,reference)
            for k,v in expected.items():self.assertEqual(row[k],v,k)
            self.assertEqual(len(row['node_difference_v']),94);self.assertEqual(len(row['memory_difference_v']),25)
            self.assertTrue(row['reference_time_equal']);self.assertTrue(row['node_gate_passed']);self.assertTrue(row['memory_gate_passed'])
        self.assertEqual(r['reference_pre_key_history_sha256'],law.law.dc.digest(self.fixed['initial']))
        self.assertNotEqual(canonical(r['initial_history']),canonical(self.fixed['initial']))

    def test_storage_sources_destinations_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-post-key-startup/v1');self.assertEqual(sha(raw),storage['compressed_sha256'])
        self.assertEqual(len(raw),storage['bytes']);self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS);self.assertNotEqual(producer.OUTPUT,producer.SUMMARY)
        self.assertEqual(r['new_dc_solves'],0);self.assertEqual(r['new_event_solves'],0);self.assertEqual(r['continuous_actual_error_certified_duration_s'],'0')
        for flag in ('history_fabricated','previous_reports_modified','original_integrator_modified','prior_parameters_changed','numerical_gates_changed','trajectory_retimed','full_path_coverage','initial_error_known','actual_dae_error_bound','nonlinear_remainder_bound','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[flag],flag)

if __name__=='__main__':unittest.main()
