from pathlib import Path
from fractions import Fraction as F
from copy import deepcopy
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_signed_memory as producer
from loudness_latch_bdf_doubling_survey import canonical
law=producer.law
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def fixture(forcing=(F(1),-F(2)),diagonal=(F(0),F(0)),epsilon=F(0),weights=None):
    inv=[[(F(i==j),F(i==j)) for j in range(119)] for i in range(119)]
    inv[0][0]=(F(0),F(0));inv[0][114]=(F(1),F(1));inv[114][0]=(F(1),F(1));inv[114][114]=diagonal
    w=weights or [F(1)]*25
    matrix=[[-F(i==j) for j in range(22)] for i in range(22)];matrix[20][20]=-diagonal[0]
    compiled=[['0'] for _ in range(119)];compiled[114]=list(map(str,[-F(v) for v in forcing]));sub=[]
    for k in range(8):
        rest=['0']*119;rest[114]=str(epsilon)
        sub.append(dict(left=str(F(k,8)),right=str(F(k+1,8)),preconditioned_remainder_upper=rest,
            first_correction_intervals=[['0','0'] for _ in range(119)],tail_upper=['0']*119,row_defect_upper=['0']*119,
            contraction_upper='0',preconditioned_peak_upper=str(sum(map(abs,forcing))+epsilon),mean_descriptor_uncertainty_included=True,independent_remainders_cancelled=False))
    metric=dict(accepted=True,metric=[[str(int(i==j)) for j in range(4)] for i in range(4)],anchor_normalization_upper='1')
    gains=[['0']*22 for _ in range(94)];gains[0][20]=str(1/F(w[20]));b=['0']*22;b[20]='1'
    original=dict(index=0,inverse_certified=True,forcing_inputs=dict(left='0',right='1',duration_s='1'),metrics=dict(
        comparison_per_s=law.prior.blocks.blocks.pack(matrix),block_forcing_l1_v=b,nodal_block_gains=gains,nodal_direct_v=['0']*94),
        action=dict(action_enclosed=True,point_and_l1=True,compiled_preconditioned_polynomials=compiled,subcells=sub))
    return original,inv,[F(1)]*119,w,metric


class SignedMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
        cls.report=producer.read(producer.OUTPUT);cls.source=producer.read(producer.prior.prior.OUTPUT);cls.large=producer.read(producer.prior.OUTPUT)
        cls.previous,cls.rec,cls.ten=producer.support(cls.source,cls.large);cls.inverses=[]
        scales=list(map(F,cls.report['descriptor_scales']))
        for t in cls.rec['trials']:
            invs=[]
            for base,c in zip(cls.rec['base_cells'],t['covers']):
                inv,cert=law.prior.real.tube.cells.structured_inverse(base['inverse_binary'],scales,c['cover'],F(c['cover']['contraction_upper']))
                if cert!=c['inverse_certificate']:raise AssertionError('same inverse certificate required')
                if law.prior.digest(law.prior.real.tube.cells.packed_matrix(inv))!=c['inverse_intervals_sha256']:raise AssertionError('same inverse hash required')
                invs.append(inv)
            cls.inverses.append(invs)
    @classmethod
    def tearDownClass(cls):sys.set_int_max_str_digits(cls.limit)

    def test_exact_primitive_uses_physical_duration_and_continuous_endpoint(self):
        p=law.primitive([1,-2],2,3);self.assertEqual(p,(F(3),F(2),-F(2)))
        self.assertEqual(law.poly.scale(law.poly.differentiate(p),F(1,2)),(F(1),-F(2)))
        q=law.primitive([2],F(1,4),law.poly.evaluate(p,1));self.assertEqual(q[0],3);self.assertEqual(q[1],F(1,2))
        with self.assertRaises(ValueError):law.primitive([1],0,0)
        with self.assertRaises(ValueError):law.primitive([],1,0)

    def test_affine_sign_change_exact_solution_and_no_cancellation_control(self):
        old,inv,d,w,metric=fixture();row=law.shifted_cell(old,inv,d,w,metric,0)
        result=law.close([row],['0']*22,F(1,3),0);self.assertTrue(result['accepted'])
        self.assertEqual(F(result['peak_node_error_upper_v']),F(1,4));self.assertEqual(law.prior.transfer(result),['0']*22)
        self.assertEqual(row['shift']['endpoint_v'],'0');self.assertEqual(row['shift']['memory_peak_added_v'][20],'1/4')
        for sub in row['shift']['subcells']:
            a,b=F(sub['left']),F(sub['right'])
            for k in range(9):
                u=a+(b-a)*F(k,8);truth=u-u*u;lo,hi=map(F,sub['particular_interval_v'])
                self.assertLessEqual(lo,truth);self.assertLessEqual(truth,hi)
        self.assertFalse(law.prior.blocks.close([old],['0']*22,F(1,3),0)['accepted'])
        old,inv,d,w,metric=fixture((F(1),));row=law.shifted_cell(old,inv,d,w,metric,0)
        control=law.close([row],['0']*22,F(1,3),0);self.assertFalse(control['accepted'])
        self.assertEqual(F(control['propagation']['endpoint_forced_v'][20]),1)

    def test_variable_uncertain_generator_independent_remainder_and_bp_counterexample(self):
        eps=F(1,10**6);old,inv,d,w,metric=fixture((F(1),),(-F(2),-F(1)),eps)
        row=law.shifted_cell(old,inv,d,w,metric,0);result=law.close([row],['0']*22,10,0)
        self.assertTrue(result['accepted']);self.assertGreater(F(row['shift']['shifted_coupling_l1_upper_v'][20]),1)
        self.assertGreaterEqual(F(row['shift']['action_difference_l1_upper_v']),eps)
        # B(t)=2/(1+t), f=1+epsilon has exact y=(1+epsilon)*(t+t^2).
        for sign in (-1,1):
            for u in (F(0),F(1,4),F(1,2),F(3,4),F(1)):
                y=(1+sign*eps)*(u+u*u);b=2/(1+u);yp=(1+sign*eps)*(1+2*u)
                self.assertEqual(yp,b*y+1+sign*eps)
                self.assertLessEqual(y,F(result['peak_node_error_upper_v']))
            self.assertLessEqual((1+sign*eps)*2,F(result['propagation']['endpoint_forced_v'][20]))
        bad=deepcopy(row);bad['metrics']['block_forcing_l1_v']=['0']*22
        unsafe=law.close([bad],['0']*22,F(3,2),0)
        self.assertTrue(unsafe['accepted']);self.assertLess(F(unsafe['peak_node_error_upper_v']),2)
        # This demonstrates the failure caused by dropping Bp, not an admitted certificate.
        bad=deepcopy(row);bad['shift']['uncertain_generator_times_particular_included']=False
        with self.assertRaises(ValueError):law.close([bad],['0']*22,10,0)

    def test_all_couplings_weights_and_quadratic_conversion_are_paid(self):
        w=[F(1)]*25;w[3]=2;w[20]=2
        old,inv,d,w,metric=fixture((F(1),),(F(0),F(0)),weights=w)
        inv[97][114]=(F(3),F(3));inv[115][114]=(F(1),F(1));inv[116][114]=(F(2),F(2))
        row=law.shifted_cell(old,inv,d,w,metric,0);coupling=list(map(F,row['shift']['shifted_coupling_l1_upper_v']))
        self.assertGreaterEqual(coupling[3],3);self.assertGreaterEqual(coupling[21],law.prior.blocks.quadratic.sqrt_bounds(5)[0]/4)
        self.assertEqual(F(row['shift']['memory_endpoint_added_v'][20]),2)
        self.assertEqual(F(row['shift']['nodal_particular_upper_v'][0]),1)
        self.assertEqual(old['metrics']['block_forcing_l1_v'][3],'0')

    def test_action_difference_retains_error_defect_and_tail_without_false_cancellation(self):
        cert=fixture()[0]['action']['subcells'][0];cert=deepcopy(cert)
        cert['preconditioned_remainder_upper'][114]='6';cert['first_correction_intervals'][114]=['-4','5'];cert['tail_upper'][114]='1'
        cert['row_defect_upper'][114]='1/10';cert['contraction_upper']='1/5';cert['preconditioned_peak_upper']='10'
        self.assertEqual(law.action_difference(cert,114,2),F(29,8))
        cert['independent_remainders_cancelled']=True
        with self.assertRaises(ValueError):law.action_difference(cert,114,2)
        with self.assertRaises(ValueError):law.action_difference(cert,114,0)

    def test_all_archived_inverses_profiles_compensations_and_source_identities_replay(self):
        r=self.report;count=0;scales=list(map(F,r['descriptor_scales']))
        for t,old,invs in zip(r['trials'],self.rec['trials'],self.inverses):
            p=F(0)
            for row,original,inv,c,cert in zip(t['modes'][1].get('cells',[]),old['cells'],invs,old['covers'],t['certificates']):
                self.assertEqual(law.shifted_cell(original,inv,scales,r['weights'],self.source['fixed_metric'],p),row)
                p=F(row['shift']['endpoint_v']);count+=len(row['shift']['subcells'])
                self.assertEqual(cert['inverse_intervals_sha256'],c['inverse_intervals_sha256'])
                self.assertEqual(cert['source_cover_sha256'],law.prior.digest(c));self.assertEqual(cert['source_rate_sha256'],law.prior.digest(original['rate_certificate']))
                self.assertEqual(cert['source_action_sha256'],law.prior.digest(original['action']))
                for key in ('comparison_per_s','nodal_block_gains','norm_policy'):self.assertEqual(row['metrics'][key],original['metrics'][key])
        self.assertEqual(count,128);self.assertEqual(count,r['new_shift_subcell_certificates'])
        self.assertEqual(r['incoming_block_error_upper_v'],law.prior.transfer(self.previous));self.assertEqual(r['interface'],self.rec['interface'])
        self.assertEqual(r['metric_sha256'],self.source['metric_sha256']);self.assertEqual(r['source_certified_result_sha256'],law.prior.digest(self.previous))
        with self.assertRaises(ValueError):producer.support(self.source|dict(first_gap_index=7),self.large)
        bad=deepcopy(self.source);bad['final_certified_result']['actual_dae_error_bound']=False
        with self.assertRaises(ValueError):producer.support(bad,self.large)

    def test_all_closures_order_actual_memory_restoration_and_seventh_prefix(self):
        r=self.report;selected=None
        for i,t in enumerate(r['trials']):
            baseline=self.ten if i==2 else self.rec['trials'][i]['result'];self.assertEqual(t['modes'][0]['result'],baseline)
            m=t['modes'][1]
            if m.get('cells'):
                result=law.close(m['cells'],r['incoming_block_error_upper_v'],F(t['radius_v']),F(r['incoming_node_error_upper_v']))
                self.assertEqual(result,m['result']);p=result['propagation'];last=F(0)
                for cell,trace in zip(m['cells'],p['trace']):
                    s=cell['shift'];self.assertEqual(F(s['initial_v']),last);last=F(s['endpoint_v'])
                    self.assertEqual(trace['kernels_act_on'],'z=e-p')
                    for a,b,v in zip(trace['shifted_endpoint_forced_v'],s['memory_endpoint_added_v'],trace['endpoint_forced_v']):self.assertGreaterEqual(F(v),F(a)+F(b))
                self.assertEqual(p['endpoint_forced_v'],p['trace'][-1]['endpoint_forced_v'])
            else:self.assertFalse(m['result']['accepted'])
            for j,mode in enumerate(t['modes']):
                if selected is None and mode['result']['accepted']:selected=[i,j]
        self.assertEqual(selected,[1,1]);self.assertEqual(r['primary_trial_mode'],selected);self.assertEqual(r['accepted_intervals_total'],7)
        self.assertEqual(r['final_certified_result'],r['trials'][1]['modes'][1]['result']);self.assertEqual(len(law.prior.transfer(r['final_certified_result'])),22)
        self.assertEqual(r['continuous_actual_error_certified_duration_s'],r['end_s']);self.assertIsNone(r['first_gap_index'])
        bad=deepcopy(r['trials'][1]['modes'][1]['cells']);bad[1]['shift']['initial_v']='1'
        with self.assertRaises(ValueError):law.close(bad,r['incoming_block_error_upper_v'],F(1,10**6),F(r['incoming_node_error_upper_v']))

    def test_storage_sources_counts_scope_and_destinations(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-signed-memory/v1');self.assertEqual(gzip.decompress(raw),canonical(r))
        self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['reused_inverse_enclosures'],16);self.assertEqual(r['reused_rate_certificates'],16);self.assertEqual(r['reused_action_subcell_certificates'],128)
        self.assertEqual(r['integer_text_limit_during'],0);self.assertEqual(r['mode_order'],list(producer.MODES));self.assertEqual(r['radius_order'],self.source['radius_order'])
        for key in ('new_nonlinear_solves','new_preconditioners','new_inverse_enclosures','new_metric_systems','new_rate_ldlt_queries'):self.assertEqual(r[key],0)
        for key in ('trajectory_changed','physical_reconstruction_changed','junction_norm_changed','dc_anchor_reset','prior_reports_modified','numerical_gates_changed','small_currents_dropped','circuit_regularized','independent_remainders_cancelled','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[key])
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)

if __name__=='__main__':unittest.main()
