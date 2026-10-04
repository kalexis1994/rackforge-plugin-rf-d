from pathlib import Path
from fractions import Fraction as F
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_large_closure as producer
from loudness_latch_bdf_doubling_survey import canonical
law=producer.prior.law
sha=lambda raw:hashlib.sha256(raw).hexdigest()


class LargeClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
        cls.report=producer.read(producer.OUTPUT);cls.source=producer.read(producer.prior.OUTPUT)
    @classmethod
    def tearDownClass(cls):sys.set_int_max_str_digits(cls.old_limit)

    def test_both_complete_archived_closures_replay_with_exact_policy(self):
        targets=producer.supports(self.source);self.assertEqual(len(targets),2)
        for row,(rec,i,t) in zip(self.report['records'],targets):
            self.assertEqual(row['interval_index'],rec['interval_index']);self.assertEqual(row['trial_index'],i)
            self.assertEqual(row['source_cells_sha256'],law.digest(t['cells']));self.assertEqual(row['source_failed_result'],t['result'])
            self.assertEqual(row['incoming_block_error_upper_v'],rec['incoming_block_error_upper_v'])
            self.assertEqual(row['incoming_certified_result_sha256'],rec['incoming_certified_result_sha256'])
            self.assertEqual(law.blocks.close(t['cells'],rec['incoming_block_error_upper_v'],F(t['radius_v']),F(rec['incoming_node_error_upper_v'])),row['result'])
            self.assertIn('peak_node_error_upper_v',row['result']);self.assertFalse(row['result']['accepted'])
            self.assertEqual(row['result']['reason'],'comparison bound escapes assumed potential tube')
            self.assertEqual(len(row['result']['propagation']['trace']),8)
        self.assertEqual(self.report['source_prefix_result_sha256'],law.digest(self.source['final_certified_result']))
        self.assertEqual(self.report['accepted_intervals_total'],6);self.assertEqual(self.report['first_gap_index'],6)
        self.assertEqual(self.report['continuous_actual_error_certified_duration_s'],self.source['continuous_actual_error_certified_duration_s'])

    def test_known_growth_over_five_thousand_digits_within_kernel_domain(self):
        cells=[]
        for k in range(4):
            cells.append(dict(inverse_certified=True,forcing_inputs=dict(left=str(F(k,4)),right=str(F(k+1,4)),duration_s='1'),metrics=dict(
                comparison_per_s=[['3000']],block_forcing_l1_v=['0'],nodal_block_gains=[['1']],nodal_direct_v=['0'])))
        result=law.blocks.close(cells,['1'],2,1);peak=F(result['peak_node_error_upper_v'])
        self.assertGreater(peak,10**5000);self.assertFalse(result['accepted'])
        # Independent 64-term outward exponential, vs 32-term positive semigroup kernels.
        lower=law.blocks.blocks.exp_bounds(3000)[0]**4
        self.assertGreaterEqual(peak,lower);self.assertGreater(len(str(peak.numerator)),5000)
        self.assertEqual(json.loads(canonical(result)),result)
        for row in result['propagation']['trace']:self.assertLessEqual(F(row['kernel_certificate']['small_shifted_norm_upper']),1)

    def test_support_guards_preserve_identified_failures_and_prefix(self):
        with self.assertRaises(ValueError):producer.supports(self.source|dict(first_gap_index=7))
        from copy import deepcopy
        bad=deepcopy(self.source);bad['records'][1]['trials'][2]['result']['reason']='different failure'
        with self.assertRaises(ValueError):producer.supports(bad)
        bad=deepcopy(self.source);bad['records'][1]['trials'][2]['cells'].pop()
        with self.assertRaises(ValueError):producer.supports(bad)

    def test_storage_sources_costs_and_unchanged_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-large-closure/v1');self.assertEqual(r['integer_text_limit_before'],4300);self.assertEqual(r['integer_text_limit_during'],0)
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['new_closures'],2)
        for key in ('new_preconditioners','new_inverse_enclosures','new_rate_ldlt_queries','new_action_subcell_certificates','new_nonlinear_solves'):self.assertEqual(r[key],0)
        for key in ('source_selections_rewritten','source_reports_modified','numerical_gates_changed','circuit_changed','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[key])
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)

if __name__=='__main__':unittest.main()
