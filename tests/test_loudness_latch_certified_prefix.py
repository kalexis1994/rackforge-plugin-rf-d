from pathlib import Path
from fractions import Fraction as F
from copy import deepcopy
import gzip,hashlib,json,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_certified_prefix as producer
import loudness_latch_bdf_static_precision_dc_anchor as constructor
from loudness_latch_bdf_doubling_survey import canonical
law=producer.law
sha=lambda b:hashlib.sha256(b).hexdigest()

def fixture_metric(scale=1,normal=1):
    return dict(accepted=True,metric=[[str(F(scale)*(i==j)) for j in range(4)] for i in range(4)],anchor_normalization_upper=str(F(normal)/2))

class CertifiedPrefix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=producer.read(producer.OUTPUT);cls.source=producer.read(producer.prior.OUTPUT)
        cls.first=producer.read(producer.prior.prior.OUTPUT);cls.startup=producer.read(producer.prior.prior.prior.OUTPUT)
        cls.network=constructor.CompensatedBdfNetwork(200,constructor.model_parameters(1,'finite_transit'))
        cls.graph=producer.read(producer.prior.prior.prior.prior.prior.OUTPUT)['graph']
        cls.prepared=[];cls.inverses=[];scales=list(map(F,cls.report['descriptor_scales']))
        for rec in cls.report['records']:
            k=rec['interval_index'];initial=producer.prior.prior.prior.unpack(cls.network,cls.startup['rows'][k-1]['history']);end=producer.prior.prior.prior.unpack(cls.network,cls.startup['rows'][k]['history'])
            cls.prepared.append(law.prepare(cls.network,initial,end));families=[]
            for trial in rec['trials']:
                inverses=[]
                for base,row in zip(rec['base_cells'],trial['covers']):
                    if not row['inverse_certified']:continue
                    inverse,cert=law.tube.cells.structured_inverse(base['inverse_binary'],scales,row['cover'],F(row['cover']['contraction_upper']))
                    if cert!=row['inverse_certificate']:raise AssertionError('inverse certificate mismatch')
                    if sha(canonical(law.tube.cells.packed_matrix(inverse)))!=row['inverse_intervals_sha256']:raise AssertionError('inverse hash mismatch')
                    inverses.append(inverse)
                families.append(inverses)
            cls.inverses.append(families)

    def test_real_support_clocks_reconstruction_and_continuity(self):
        left=self.first['prepared'];last=F(self.source['duration_s'])
        for rec,p in zip(self.report['records'],self.prepared):
            self.assertEqual(producer.serial(p),rec['prepared']);self.assertEqual(F(p['start_s']),last);self.assertGreater(F(p['start_s']),0)
            self.assertEqual(p['h'],F(p['end_s'])-F(p['start_s']));self.assertEqual(law.continuity(self.network,left,p,last,F(p['start_s'])),rec['interface'])
            k=rec['interval_index']
            for u,row in ((F(0),self.startup['rows'][k-1]),(F(1),self.startup['rows'][k])):
                history=producer.prior.prior.prior.unpack(self.network,row['history'])
                self.assertEqual([law.poly.evaluate(v,u) for v in p['x']],law.origin.state_values(history.current))
                self.assertEqual([law.poly.evaluate(v,u) for v in p['y_linear']],law.origin.charge_coordinates(self.network.network,history.current)[:21])
            with self.assertRaises(ValueError):law.continuity(self.network,left,p,last+1,F(p['start_s']))
            bad=deepcopy(producer.serial(p));bad['x'][0][0]=str(F(bad['x'][0][0])+1)
            with self.assertRaises(ValueError):law.continuity(self.network,left,bad,last,F(p['start_s']))
            left=p;last=F(p['end_s'])
        a=producer.prior.prior.prior.unpack(self.network,self.startup['rows'][0]['history']);b=producer.prior.prior.prior.unpack(self.network,self.startup['rows'][1]['history'])
        with self.assertRaises(ValueError):law.prepare(self.network,b,a)

    def test_exact_bridge_identity_scaling_normalization_and_rejections(self):
        old=fixture_metric();self.assertEqual(law.bridge(old,old)['factor_upper'],'1')
        new=fixture_metric(4);cert=law.bridge(old,new);self.assertLessEqual(F(cert['alpha_lower']),4);self.assertGreater(F(cert['alpha_upper']),4)
        self.assertGreaterEqual(F(cert['factor_upper']),2);self.assertLess(F(cert['factor_upper']),F(2000001,1000000));self.assertEqual(len(cert['probes']),33)
        self.assertTrue(cert['final_upper_ldlt']['positive_definite'])
        norm=law.bridge(fixture_metric(1,2),fixture_metric(1,1));self.assertGreaterEqual(F(norm['factor_upper']),2)
        for probe in cert['probes']:
            a=F(probe['alpha']);q=law.blocks.quadratic.ldlt([[a*F(i==j)-4*F(i==j) for j in range(4)] for i in range(4)])
            self.assertEqual(q['positive_definite'],probe['positive_definite']);self.assertEqual(law.event.dc.digest(q['pivots']),probe['pivot_sha256'])
        with self.assertRaises(ValueError):law.bridge(old|dict(accepted=False),new)
        with self.assertRaises(ValueError):law.bridge(old,fixture_metric(-1))
        with self.assertRaises(ValueError):law.bridge(old,fixture_metric(1,0))

    def test_all_covers_residuals_queries_and_inverse_families_replay(self):
        scales=list(map(F,self.report['descriptor_scales']))
        for rec,p,families in zip(self.report['records'],self.prepared,self.inverses):
            gains=law.tube.gains(self.network,self.graph)
            for base in rec['base_cells']:
                left,right=F(base['left']),F(base['right']);residual,forcing=law.tube.forcing(self.network,self.graph,p,left,right)
                self.assertEqual(producer.serial(residual),base['residual_bounds']);self.assertEqual(forcing,base['forcing_inputs'])
                constant,terms=law.tube.weighted.compile_terms(self.network,self.graph,p,base['inverse_binary'],scales)
                for trial in rec['trials']:
                    if not trial['covers']:continue
                    actual=law.tube.inflated_cover(constant,terms,gains,left,right,F(trial['radius_v']))
                    self.assertEqual(actual,trial['covers'][base['index']]['cover'])
            for q in rec['queries']:self.assertEqual(q['decimal100'],law.tube.query(self.network,self.graph,p,F(q['u']),100))
            for trial,inverses in zip(rec['trials'],families):
                if len(inverses)==8:self.assertEqual(law.blocks.quadratic.candidate([law.blocks.generator(v,self.report['weights']) for v in inverses]),trial['new_metric'])

    def test_every_rate_metric_bridge_and_known_memory_transfer_replays(self):
        chosen=self.source['primary_trial_mode'];previous=self.source['trials'][chosen[0]]['modes'][chosen[1]]['result'];oldmetric=self.source['trials'][chosen[0]]['metric']
        for rec,families in zip(self.report['records'],self.inverses):
            self.assertEqual(law.event.dc.digest(previous),rec['incoming_certified_result_sha256']);self.assertEqual(law.event.dc.digest(oldmetric),rec['incoming_metric_sha256'])
            for trial,inverses in zip(rec['trials'],families):
                for mode in trial['modes']:
                    if not mode['cells']:continue
                    m=oldmetric if mode['mode']=='retained_quadratic' else trial['new_metric'];self.assertEqual(m,mode['metric'])
                    cert=law.bridge(oldmetric,m);self.assertEqual(cert,mode['bridge']);self.assertEqual(law.transfer(previous,cert),mode['initial_block_error_upper_v'])
                    basis=law.blocks.directed.basis(m);balance=law.blocks.balanced.balance(basis)
                    self.assertEqual(basis,mode['congruence']);self.assertEqual(balance,mode['balance'])
                    for row,inverse in zip(mode['cells'],inverses):
                        metrics,rate=law.blocks.cell_metrics(inverse,self.report['weights'],row['forcing_inputs'],'quadratic_balanced',m,basis,balance)
                        self.assertEqual(metrics,row['metrics']);self.assertEqual(rate,row['rate_certificate'])
            selected=rec['selected_trial_mode']
            if selected:
                mode=rec['trials'][selected[0]]['modes'][selected[1]];previous=mode['result'];oldmetric=mode['metric']

    def test_strict_closures_selection_and_first_gap_stop_chain(self):
        selected=self.source['primary_trial_mode'];previous=self.source['trials'][selected[0]]['modes'][selected[1]]['result'];metric=self.source['trials'][selected[0]]['metric']
        end=F(self.source['duration_s']);accepted=0
        for k,rec in enumerate(self.report['records']):
            self.assertEqual(F(rec['start_s']),end);origin=F(previous['peak_node_error_upper_v']);self.assertEqual(origin,F(rec['incoming_node_error_upper_v']))
            choice=None
            for i,trial in enumerate(rec['trials']):
                if origin>=F(trial['radius_v']):
                    self.assertEqual(trial['covers'],[]);self.assertTrue(all('incoming nodal bound' in m['result']['reason'] for m in trial['modes']))
                for j,mode in enumerate(trial['modes']):
                    if mode['cells']:
                        actual=law.blocks.close(mode['cells'],mode['initial_block_error_upper_v'],F(trial['radius_v']),origin);self.assertEqual(actual,mode['result'])
                    if mode['result']['accepted'] and choice is None:choice=[i,j]
            self.assertEqual(choice,rec['selected_trial_mode'])
            if choice is None:self.assertEqual(k,len(self.report['records'])-1);continue
            mode=rec['trials'][choice[0]]['modes'][choice[1]];previous=mode['result'];metric=mode['metric'];end=F(rec['end_s']);accepted+=1
        self.assertEqual(accepted,self.report['accepted_additional_intervals']);self.assertEqual(1+accepted,self.report['accepted_intervals_total'])
        self.assertEqual(end,F(self.report['continuous_actual_error_certified_duration_s']));self.assertEqual(previous,self.report['final_certified_result']);self.assertEqual(metric,self.report['final_certified_metric'])
        self.assertLessEqual(len(self.report['records']),producer.ADDITIONAL_LIMIT)

    def test_nonlinear_two_interval_truth_and_norm_bridge_without_dc_reset(self):
        # y'=-y², constant yhat=1; true errors at .1 and .2 are 1/11,1/6.
        def case(scale):
            return dict(inverse_certified=True,forcing_inputs=dict(left='0',right='1',duration_s='1/10'),
                metrics=dict(comparison_per_s=[[str(F(-8,5) if i==j==5 else -F(i==j)) for j in range(6)] for i in range(6)],
                    block_forcing_l1_v=['0']*5+[str(F(scale,10))],nodal_block_gains=[['0']*5+[str(1/F(scale))]],nodal_direct_v=['0']))
        first=law.blocks.close([case(1)],['0']*6,F(1,5),0);self.assertTrue(first['accepted']);self.assertLessEqual(F(1,11),F(first['peak_node_error_upper_v']))
        bridge=law.bridge(fixture_metric(),fixture_metric(4));incoming=law.transfer(first,bridge)
        self.assertGreater(F(incoming[5]),0);self.assertGreaterEqual(F(incoming[5]),2*F(first['propagation']['endpoint_forced_v'][5]))
        second=law.blocks.close([case(2)],incoming,F(1,4),F(first['peak_node_error_upper_v']));self.assertTrue(second['accepted']);self.assertLessEqual(F(1,6),F(second['peak_node_error_upper_v']))
        rejected=law.blocks.close([case(2)],incoming,F(1,20),F(first['peak_node_error_upper_v']));self.assertFalse(rejected['accepted'])
        with self.assertRaises(ValueError):law.transfer(rejected,bridge)

    def test_failed_launch_is_identified_before_numerical_work(self):
        path=ROOT/'evidence/loudness_latch_bdf_static_precision_certified_prefix_launch_attempt.json';r=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(r['schema'],'rf-d/certified-prefix-launch/v1');self.assertFalse(r['numerical_measurement_started'])
        self.assertEqual(sha(r['failed_producer_source_utf8'].encode()),r['failed_producer_sha256'])
        self.assertEqual(sha(subprocess.check_output(['git','show',r['git_head']+':'+r['failed_producer_path']],cwd=ROOT)),r['failed_producer_sha256'])
        self.assertNotEqual(sha((ROOT/r['failed_producer_path']).read_bytes()),r['failed_producer_sha256'])
        self.assertEqual(r['new_preconditioners'],0);self.assertEqual(r['metric_systems_attempted'],0);self.assertIn('AttributeError',r['reason'])

    def test_storage_sources_counts_destinations_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-certified-prefix/v1');self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['new_nonlinear_solves'],0);self.assertEqual(r['new_preconditioners'],8*len(r['records']));self.assertEqual(r['attempted_additional_intervals'],len(r['records']))
        self.assertEqual(r['radius_order'],list(map(str,producer.RADII)));self.assertEqual(r['mode_order'],list(producer.MODES))
        for flag in ('clock_translation','dc_anchor_reset','original_integrator_modified','prior_reports_modified','numerical_gates_changed','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[flag])
        self.assertTrue(r['metric_bridges_paid']);self.assertTrue(r['real_history_only'])
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)

if __name__=='__main__':unittest.main()
