from pathlib import Path
from fractions import Fraction as F
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_coordinate_memory as producer
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_charge_enclosure import exp_bounds
law=producer.law
sha=lambda b:hashlib.sha256(b).hexdigest()

class CoordinateMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=producer.read(producer.OUTPUT);cls.first=producer.read(producer.startup_blocks.OUTPUT)
        cls.tube=producer.read(producer.startup_tube.OUTPUT);cls.prefix=producer.read(producer.prior.OUTPUT)
        chosen=cls.first['primary_trial_mode'];cls.metric=cls.first['trials'][chosen[0]]['metric'];cls.previous=cls.first['trials'][chosen[0]]['modes'][chosen[1]]
        cls.first_inverses=[];cls.second_inverses=[];scales=list(map(F,cls.tube['descriptor_scales']))
        for base,row in zip(cls.tube['base_cells'],cls.tube['trials'][chosen[0]]['cells']):cls.first_inverses.append(producer.inverse(base,row,scales))
        for trial in cls.prefix['records'][0]['trials']:
            cls.second_inverses.append([producer.inverse(base,row,scales) for base,row in zip(cls.prefix['records'][0]['base_cells'],trial['covers'])])

    def test_every_reused_inverse_and_rate_identity_is_bound(self):
        r=self.report;self.assertEqual(r['reused_inverse_enclosures'],24)
        for row,(inverse,digest),old in zip(r['first_cells'],self.first_inverses,self.previous['cells']):
            self.assertEqual(digest,row['inverse_intervals_sha256']);self.assertEqual(sha(canonical(old['rate_certificate'])),row['source_rate_sha256'])
            self.assertEqual(row['metrics']['junction_mu_reused_per_s'],old['rate_certificate']['balanced']['mu_metric_upper_per_s'])
        for trial,original,inverses in zip(r['trials'],self.prefix['records'][0]['trials'],self.second_inverses):
            if not trial['cells']:continue
            retained=original['modes'][0];self.assertEqual(retained['metric'],self.metric);self.assertTrue(retained['bridge']['identical_norm'])
            for row,old,(inverse,digest) in zip(trial['cells'],retained['cells'],inverses):
                self.assertEqual(digest,row['inverse_intervals_sha256']);self.assertEqual(sha(canonical(old['rate_certificate'])),row['source_rate_sha256'])
                self.assertEqual(row['metrics']['junction_mu_reused_per_s'],old['rate_certificate']['balanced']['mu_metric_upper_per_s'])
        p=[[F(v) for v in row] for row in self.metric['metric']];pi=[[F(v) for v in row] for row in self.metric['inverse_metric']]
        self.assertEqual([[sum((p[i][k]*pi[k][j] for k in range(4)),F(0)) for j in range(4)] for i in range(4)],[[F(i==j) for j in range(4)] for i in range(4)])

    def test_all_fine_comparison_forcing_and_output_metrics_replay(self):
        weights=self.report['weights']
        for row,(inverse,_) in zip(self.report['first_cells'],self.first_inverses):
            self.assertEqual(law.fine_metrics(inverse,weights,row['forcing_inputs'],self.metric,row['metrics']['junction_mu_reused_per_s']),row['metrics'])
        for trial,inverses in zip(self.report['trials'],self.second_inverses):
            for row,(inverse,_) in zip(trial['cells'],inverses):
                self.assertEqual(law.fine_metrics(inverse,weights,row['forcing_inputs'],self.metric,row['metrics']['junction_mu_reused_per_s']),row['metrics'])
                m=list(map(lambda r:list(map(F,r)),row['metrics']['comparison_per_s']))
                self.assertEqual(len(m),22);self.assertTrue(all(m[i][j]>=0 for i in range(22) for j in range(22) if i!=j))
        self.assertEqual(self.report['groups'],[list(g) for g in law.GROUPS])

    def test_168_scalar_refinements_and_known_profile_intersections_replay(self):
        r=self.report;initial=[v['weighted_error_upper_v'] for v in self.first['initial_memory']['rows'][:21]]
        expected=law.refine(initial,self.previous['result'],r['first_cells']);self.assertEqual(expected,r['refinement'])
        self.assertEqual(sum(len(c['rows']) for c in expected['trace']),168)
        for cell in expected['trace']:
            for row in cell['rows']:
                q=row['scalar'];self.assertLessEqual(F(q['endpoint_upper_v']),F(q['raw_endpoint_upper_v']));self.assertLessEqual(F(q['endpoint_upper_v']),F(q['previous_endpoint_upper_v']))
                self.assertEqual(q['same_coordinate_intersection'],True)
        for refined,coarse in zip(expected['refined_outgoing_v'],expected['coarse_outgoing_v']):self.assertLessEqual(F(refined),F(coarse))
        self.assertEqual(expected['refined_outgoing_v'][21],expected['coarse_outgoing_v'][21])
        with self.assertRaises(ValueError):law.lift(self.previous['result']|dict(accepted=False))
        with self.assertRaises(ValueError):law.refine(initial[:-1],self.previous['result'],r['first_cells'])

    def test_scalar_known_linear_solution_signed_diagonal_and_rounding(self):
        result=law.scalar_refine(1,-2,F(3,5),F(7,5),F(1,10))
        # e'=-2e+6, e(0)=1, e(.1)=3-2exp(-.2); outer exact rational exponential enclosure.
        truth_upper=3-2*exp_bounds(-F(1,5))[0]
        self.assertLessEqual(truth_upper,F(result['endpoint_upper_v']));self.assertEqual(F(result['endpoint_upper_v']),F(7,5))
        self.assertGreaterEqual(F(result['raw_endpoint_upper_v']),F(7,5))
        exact=law.scalar_refine(1,0,F(1,10),F(11,10),F(1,10));self.assertEqual(F(exact['endpoint_upper_v']),F(11,10))
        with self.assertRaises(ValueError):law.scalar_refine(-1,0,0,1,1)
        with self.assertRaises(ValueError):law.scalar_refine(0,0,0,1,0)

    def test_manufactured_dual_norms_couplings_forcing_and_output(self):
        inverse=[[(F(0),F(0)) for _ in range(119)] for _ in range(119)]
        def put(i,j,v):inverse[i][j]=(F(v),F(v))
        put(94,94,2);put(94,95,-3);put(94,115,-2);put(115,94,-4);put(115,116,-1000);put(116,115,1000)
        put(94,0,F(1,2));put(115,0,-4);put(0,115,-3);put(0,94,-5);put(0,0,2)
        metric=dict(accepted=True,metric=[[str(int(i==j)) for j in range(4)] for i in range(4)],inverse_metric=[[str(int(i==j)) for j in range(4)] for i in range(4)],anchor_normalization_upper='1',metric_norm='weighted RMS')
        forcing=dict(nodal_l1_c=['1/10']+['0']*93,constraint_l1_v_s=['0']*25,nodal_point_a=['1/20']+['0']*93,constraint_point_v=['0']*25)
        r=law.fine_metrics(inverse,[1]*25,forcing,metric,0)
        self.assertEqual(list(map(F,r['comparison_per_s'][0][:2])),[F(-2),F(3)])
        self.assertEqual(F(r['comparison_per_s'][0][21]),4);self.assertEqual(F(r['comparison_per_s'][21][0]),2);self.assertEqual(F(r['comparison_per_s'][21][21]),0)
        self.assertEqual(F(r['block_forcing_l1_v'][0]),F(1,20));self.assertEqual(F(r['block_forcing_l1_v'][21]),F(1,5))
        self.assertEqual(F(r['nodal_block_gains'][0][0]),5);self.assertEqual(F(r['nodal_block_gains'][0][21]),6);self.assertEqual(F(r['nodal_direct_v'][0]),F(1,10))
        with self.assertRaises(ValueError):law.fine_metrics(inverse,[1]*24,forcing,metric,0)
        with self.assertRaises(ValueError):law.fine_metrics(inverse,[1]*25,forcing,metric|dict(accepted=False),0)

    def test_nonlinear_truth_anisotropic_direction_and_late_forcing(self):
        def cell(matrix,forcing,gain):
            return dict(inverse_certified=True,forcing_inputs=dict(left='0',right='1',duration_s='1/10'),metrics=dict(comparison_per_s=law.blocks.pack(matrix),block_forcing_l1_v=list(map(str,forcing)),nodal_block_gains=[list(map(str,gain))],nodal_direct_v=['0']))
        matrix=[[F(-8,5) if i==j==0 else -F(i==j) for j in range(22)] for i in range(22)]
        first=law.scalar_refine(0,-F(8,5),F(1,10),F(1,10),F(1,10))
        c=cell(matrix,[F(1,10)]+[F(0)]*21,[F(1)]+[F(0)]*21);incoming=[first['endpoint_upper_v']]+['0']*21
        result=law.prior.close([c],incoming,F(1,4),F(1,10));self.assertTrue(result['accepted']);self.assertLessEqual(F(1,6),F(result['peak_node_error_upper_v']))
        self.assertFalse(law.prior.close([c],incoming,F(1,20),F(1,10))['accepted'])
        matrix=[[F(0) for _ in range(22)] for _ in range(22)];matrix[0][0]=-1;matrix[0][1]=10
        c=cell(matrix,[F(0)]*22,[F(1)]+[F(0)]*21)
        self.assertTrue(law.prior.close([c],['1','0']+['0']*20,F(11,10),1)['accepted'])
        self.assertFalse(law.prior.close([c],['1','1']+['0']*20,F(11,10),1)['accepted'])
        late=cell([[-F(i==j) for j in range(22)] for i in range(22)],[F(1,5)]+[F(0)]*21,[F(1)]+[F(0)]*21)
        self.assertGreaterEqual(F(law.prior.propagate([late],['0']*22)['peak_node_error_upper_v']),F(1,5))

    def test_every_fine_propagation_closure_and_ordered_selection_replays(self):
        r=self.report;selected=None;origin=F(self.previous['result']['peak_node_error_upper_v'])
        for i,trial in enumerate(r['trials']):
            if not trial['cells']:
                self.assertGreaterEqual(origin,F(trial['radius_v']));continue
            for j,mode in enumerate(trial['modes']):
                expected=law.prior.close(trial['cells'],mode['initial_block_error_upper_v'],F(trial['radius_v']),origin)
                self.assertEqual(expected,mode['result']);self.assertEqual(expected['accepted'],F(expected['peak_node_error_upper_v'])<F(trial['radius_v']))
                if expected['accepted'] and selected is None:selected=[i,j]
        self.assertEqual(r['primary_trial_mode'],selected);self.assertEqual(r['second_interval_nonlinear_error_proven'],selected is not None)
        self.assertEqual(r['continuous_actual_error_certified_duration_s'],r['second_end_s'] if selected else self.first['duration_s'])
        self.assertEqual(r['second_interface'],self.prefix['records'][0]['interface'])

    def test_storage_sources_scope_and_destinations(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-coordinate-memory/v1');self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        for field in ('new_nonlinear_solves','new_preconditioners','new_metric_systems','new_rate_ldlt_queries'):self.assertEqual(r[field],0)
        for flag in ('reconstruction_changed','junction_norm_changed','dc_anchor_reset','original_integrator_modified','prior_reports_modified','numerical_gates_changed','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[flag])
        self.assertTrue(r['outgoing_memory_refinement_proven']);self.assertEqual(r['mode_order'],list(producer.MODES))
        self.assertEqual(r['metric_sha256'],sha(canonical(self.metric)))
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)

if __name__=='__main__':unittest.main()
