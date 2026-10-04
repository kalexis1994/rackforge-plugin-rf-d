from pathlib import Path
from fractions import Fraction as F
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_startup_blocks as producer
from loudness_latch_bdf_doubling_survey import canonical
law=producer.law
sha=lambda b:hashlib.sha256(b).hexdigest()

class StartupBlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=producer.read(producer.OUTPUT);cls.source=producer.read(producer.prior.OUTPUT)
        cls.startup=producer.read(producer.prior.prior.OUTPUT);cls.inverses=[]
        scales=list(map(F,cls.source['descriptor_scales']))
        for trial in cls.source['trials']:
            rows=[]
            for base,row in zip(cls.source['base_cells'],trial['cells']):
                inverse,cert=producer.prior.law.cells.structured_inverse(base['inverse_binary'],scales,row['cover'],F(row['cover']['contraction_upper']))
                if cert!=row['inverse_certificate']:raise AssertionError('source inverse certificate changed')
                rows.append((inverse,cert))
            cls.inverses.append(rows)

    def test_all_reused_inverse_hashes_generators_and_common_metrics(self):
        r=self.report;weights=list(map(F,r['weights']))
        self.assertEqual(r['blocks'],[list(v) for v in law.blocks.BLOCKS]);self.assertEqual(r['mode_order'],list(law.MODES))
        self.assertEqual(sum(len(rows) for rows in self.inverses),24)
        for trial,inverses in zip(r['trials'],self.inverses):
            family=[law.generator(inverse,weights) for inverse,_ in inverses]
            metric=law.quadratic.candidate(family);self.assertEqual(metric,trial['metric'])
            if metric['accepted']:
                prepared=law.directed.basis(metric);self.assertEqual(prepared,trial['congruence'])
                self.assertEqual(law.balanced.balance(prepared),trial['balance'])
            for mode in trial['modes']:
                for row,(inverse,cert) in zip(mode['cells'],inverses):
                    self.assertEqual(row['inverse_certificate'],cert)
                    self.assertEqual(row['inverse_intervals_sha256'],law.quadratic.box.digest(producer.prior.law.cells.packed_matrix(inverse)))
                    self.assertTrue(row['inverse_certified'])

    def test_every_metric_rate_and_conversion_replays(self):
        weights=list(map(F,self.report['weights']))
        for trial,inverses in zip(self.report['trials'],self.inverses):
            for mode in trial['modes']:
                for row,(inverse,_) in zip(mode['cells'],inverses):
                    metrics,rate=law.cell_metrics(inverse,weights,row['forcing_inputs'],mode['mode'],trial['metric'],trial['congruence'],trial['balance'])
                    self.assertEqual(metrics,row['metrics']);self.assertEqual(rate,row['rate_certificate'])
                    if rate:
                        self.assertLessEqual(F(rate['balanced']['mu_metric_upper_per_s']),F(rate['directed']['mu_metric_upper_per_s']))
                        self.assertLessEqual(F(rate['directed']['mu_metric_upper_per_s']),F(rate['isotropic']['mu_metric_upper_per_s']))
                        self.assertTrue(rate['balanced']['final_raw_upper_ldlt']['positive_definite'])

    def test_actual_block_anchors_replay_with_complete_norm_conversions(self):
        anchor=self.source['initial_memory'];bounds=[F(v['weighted_error_upper_v']) for v in anchor['rows']]
        for trial in self.report['trials']:
            for mode in trial['modes']:
                if not mode['cells']:continue
                initial=law.initial_vector(anchor,mode['mode'],trial['metric']);self.assertEqual(initial,mode['initial_block_error_upper_v'])
                for group,bound in zip(law.blocks.BLOCKS[:5],initial[:5]):self.assertEqual(F(bound),max(bounds[i] for i in group))
                if mode['mode']!='quadratic_balanced':self.assertLessEqual(F(initial[5]),max(bounds[21:]))
                else:
                    from itertools import product
                    p=[[F(v) for v in row] for row in trial['metric']['metric']]
                    normal=2*F(trial['metric']['anchor_normalization_upper'])
                    for signs in product((-1,1),repeat=4):
                        vector=[signs[k]*bounds[21+k] for k in range(4)]
                        square=sum((vector[i]*p[i][j]*vector[j] for i in range(4) for j in range(4)),F(0))
                        self.assertLessEqual(square, (F(initial[5])*normal)**2)
        with self.assertRaises(ValueError):law.initial_vector(anchor,'unknown')
        with self.assertRaises(ValueError):law.initial_vector(anchor|dict(rows=anchor['rows'][:-1]),'infinity')

    def test_all_vector_propagations_and_strict_closures_replay(self):
        r=self.report;selected=None;initial_node=F(self.startup['initial_bound']['node_error_upper_v'])
        for i,(trial,old) in enumerate(zip(r['trials'],self.source['trials'])):
            self.assertEqual(trial['radius_v'],old['radius_v']);self.assertEqual(trial['prior_scalar_result'],old['result'])
            for j,mode in enumerate(trial['modes']):
                if not mode['cells']:continue
                result=law.close(mode['cells'],mode['initial_block_error_upper_v'],trial['radius_v'],initial_node)
                self.assertEqual(result,mode['result']);peak=F(result['peak_node_error_upper_v'])
                self.assertEqual(result['accepted'],peak<F(trial['radius_v']))
                self.assertEqual(result['actual_dae_error_bound'],result['accepted'])
                if result['accepted'] and selected is None:selected=[i,j]
                for cell,trace in zip(mode['cells'],result['propagation']['trace']):
                    e,p,cert=law.blocks.kernels(cell['metrics']['comparison_per_s'],cell['forcing_inputs']['duration_s'])
                    self.assertEqual(law.blocks.pack(e),trace['endpoint_kernel']);self.assertEqual(law.blocks.pack(p),trace['peak_kernel']);self.assertEqual(cert,trace['kernel_certificate'])
        self.assertEqual(selected,r['primary_trial_mode'])
        self.assertEqual(r['first_interval_nonlinear_error_proven'],selected is not None)
        self.assertEqual(r['continuous_actual_error_certified_duration_s'],r['duration_s'] if selected else '0')

    def test_known_nonlinear_truth_sufficient_and_insufficient_tubes(self):
        # x=y, y'=-y², reconstruction one, h=0.1, |delta x|<0.2.
        case=dict(inverse_certified=True,forcing_inputs=dict(left='0',right='1',duration_s='1/10'),
            metrics=dict(comparison_per_s=[['-8/5']],block_forcing_l1_v=['1/10'],nodal_block_gains=[['1']],nodal_direct_v=['0']))
        result=law.close([case],['0'],F(1,5),0);self.assertTrue(result['accepted'])
        self.assertLessEqual(1-F(10,11),F(result['peak_node_error_upper_v']))
        self.assertFalse(law.close([case],['0'],F(1,20),0)['accepted'])
        self.assertFalse(law.close([case],['0'],F(1,5),F(1,5))['accepted'])

    def test_directional_anchor_and_late_forcing_are_not_uniform_or_endpoint_only(self):
        case=dict(inverse_certified=True,forcing_inputs=dict(left='0',right='1',duration_s='1/10'),
            metrics=dict(comparison_per_s=[['0','0'],['0','0']],block_forcing_l1_v=['0','0'],nodal_block_gains=[['0','1000']],nodal_direct_v=['0']))
        self.assertEqual(F(law.propagate([case],['1','0'])['peak_node_error_upper_v']),0)
        self.assertGreaterEqual(F(law.propagate([case],['1','1'])['peak_node_error_upper_v']),1000)
        late=dict(inverse_certified=True,forcing_inputs=case['forcing_inputs'],
            metrics=dict(comparison_per_s=[['-10']],block_forcing_l1_v=['1/5'],nodal_block_gains=[['1']],nodal_direct_v=['0']))
        self.assertGreaterEqual(F(law.propagate([late],['0'])['peak_node_error_upper_v']),F(1,5))
        self.assertFalse(law.close([case|dict(inverse_certified=False)],['0','0'],1,0)['accepted'])
        self.assertFalse(law.close([case|dict(forcing_inputs=dict(left='1/2',right='1',duration_s='1/10'))],['0','0'],1,0)['accepted'])
        with self.assertRaises(ValueError):law.propagate([case],['-1','0'])
        with self.assertRaises(ValueError):law.close([case],['0','0'],0,0)

    def test_signed_junction_rotation_preserves_rms_cancellation(self):
        inverse=[[(F(0),F(0)) for _ in range(119)] for _ in range(119)]
        inverse[115][116]=(F(-1000),)*2;inverse[116][115]=(F(1000),)*2
        zero=['0']*119;forcing=dict(nodal_l1_c=zero[:94],constraint_l1_v_s=zero[94:],nodal_point_a=zero[:94],constraint_point_v=zero[94:])
        old=law.blocks.block_metrics(inverse,94,[1]*25,forcing);rms=law.rms.block_metrics(inverse,94,[1]*25,forcing)
        self.assertEqual(F(old['comparison_per_s'][5][5]),1000);self.assertEqual(F(rms['comparison_per_s'][5][5]),0)
        self.assertTrue(all(lo=='0' and hi=='0' for row in rms['junction_symmetric_intervals'] for lo,hi in row))

    def test_storage_source_identities_and_limited_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-startup-blocks/v1');self.assertEqual(gzip.decompress(raw),canonical(r))
        self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['new_nonlinear_solves'],0);self.assertEqual(r['new_preconditioners'],0);self.assertEqual(r['metric_systems_attempted'],3)
        for flag in ('original_integrator_modified','prior_reports_modified','numerical_gates_changed','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[flag])
        self.assertTrue(r['fixed_candidate_bank']);self.assertTrue(r['metric_constant_whole_interval']);self.assertEqual(r['real_support_states'],2)
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS);self.assertNotEqual(producer.OUTPUT,producer.SUMMARY)

if __name__=='__main__':unittest.main()
