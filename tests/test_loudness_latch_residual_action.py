from pathlib import Path
from fractions import Fraction as F
from copy import deepcopy
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_residual_action as producer
from loudness_latch_bdf_doubling_survey import canonical
law=producer.law
sha=lambda b:hashlib.sha256(b).hexdigest()


def cover(matrix):
    intervals=[[(F(v),F(v)) if not isinstance(v,tuple) else v for v in row] for row in matrix]
    q=max(sum((max(map(abs,v)) for v in row),F(0)) for row in intervals)
    return dict(preconditioned_defect_intervals=[[[str(a),str(b)] for a,b in row] for row in intervals],contraction_upper=str(q),strict_contraction=q<1)


class ResidualAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=producer.read(producer.OUTPUT);cls.source=producer.read(producer.prior.OUTPUT);cls.previous,cls.rec=producer.support(cls.source)
        cls.network=producer.prior.constructor.CompensatedBdfNetwork(200,producer.prior.constructor.model_parameters(1,'finite_transit'))
        startup=producer.read(producer.prior.startup_source.OUTPUT);cls.graph=producer.read(producer.prior.graph_source.OUTPUT)['graph'];k=cls.rec['interval_index']
        a=producer.prior.startup_source.unpack(cls.network,startup['rows'][k-1]['history']);b=producer.prior.startup_source.unpack(cls.network,startup['rows'][k]['history'])
        cls.prepared=law.prior.real.prepare(cls.network,a,b)

    def test_sensitive_common_mode_directed_rhs_and_no_cancellation_control(self):
        m=F(2**20);x=[[m+1,m],[m,m+1]];c=cover([[0,0],[0,0]])
        # Exact H=X^-1: antisymmetric RHS has unit response despite huge column magnitudes.
        h=[[v/(2*m+1) for v in row] for row in ((m+1,-m),(-m,m+1))]
        for rhs,truth in (([(F(1),),(-F(1),)],[F(1),-F(1)]),([(F(1),),(F(1),)],[2*m+1,2*m+1])):
            compiled=law.compile_polynomials(x,[1,1],rhs);r=law.enclose(x,[1,1],c,compiled,[0,0],0,1)
            self.assertEqual([tuple(map(F,v)) for v in r['action_intervals']],[(v,v) for v in truth])
            self.assertEqual([sum((h[i][j]*truth[j] for j in range(2)),F(0)) for i in range(2)],[p[0] for p in rhs])
        with self.assertRaises(ValueError):law.compile_polynomials(x,[1],[(1,),(-1,)])
        with self.assertRaises(ValueError):law.compile_polynomials(x,[1,0],[(1,),(-1,)])

    def test_uncertain_matrix_neumann_tail_and_independent_remainders(self):
        x=[[F(1),F(0)],[F(0),F(1)]];rhs=[(F(1),),(-F(1),)];compiled=law.compile_polynomials(x,[1,1],rhs)
        c=cover([[(F(1,20),F(1,10)),0],[0,(F(1,20),F(1,10))]])
        r=law.enclose(x,[1,1],c,compiled,[0,0],0,1);bounds=[tuple(map(F,v)) for v in r['action_intervals']]
        for e0 in (F(1,20),F(1,10)):
            for e1 in (F(1,20),F(1,10)):
                for (lo,hi),actual in zip(bounds,(1/(1-e0),-1/(1-e1))):self.assertLessEqual(lo,actual);self.assertLessEqual(actual,hi)
        self.assertGreater(F(r['tail_upper'][0]),0)
        c=cover([[0,F(1,5)],[F(1,5),0]]);r=law.enclose(x,[1,1],c,compiled,[0,0],0,1)
        for (lo,hi),v in zip(map(lambda ab:tuple(map(F,ab)),r['action_intervals']),(F(5,6),-F(5,6))):self.assertLessEqual(lo,v);self.assertLessEqual(v,hi)
        m=F(2**20);x=[[m+1,m],[m,m+1]];compiled=law.compile_polynomials(x,[1,1],rhs);epsilon=F(1,10**6)
        r=law.enclose(x,[1,1],cover([[0,0],[0,0]]),compiled,[epsilon,epsilon],0,1)
        for a in (-epsilon,epsilon):
            for b in (-epsilon,epsilon):
                actual=[1+(m+1)*a+m*b,-1+m*a+(m+1)*b]
                for ab,v in zip(r['action_intervals'],actual):self.assertLessEqual(F(ab[0]),v);self.assertLessEqual(v,F(ab[1]))
        self.assertGreater(F(r['action_intervals'][0][1]),3);self.assertFalse(r['independent_remainders_cancelled'])
        with self.assertRaises(ValueError):law.enclose(x,[1,1],cover([[1,0],[0,0]]),compiled,[0,0],0,1)
        with self.assertRaises(ValueError):law.enclose(x,[1,1],cover([[0,0],[0,0]]),compiled,[-1,0],0,1)
        with self.assertRaises(ValueError):law.enclose(x,[1,1],cover([[0,0],[0,0]]),compiled,[0,0],1,0)

    def test_signed_time_polynomial_and_integrated_exact_solution(self):
        m=F(2**16);x=[[m+1,m],[m,m+1]];rhs=[(F(0),F(1),-F(1)),(F(0),-F(1),F(1))];c=cover([[0,0],[0,0]])
        compiled=law.compile_polynomials(x,[1,2],rhs);total=F(0)
        for k in range(8):
            a,b=F(k,8),F(k+1,8);r=law.enclose(x,[1,2],c,compiled,[0,0],a,b)
            for j in range(5):
                u=a+(b-a)*F(j,4);truth=u*(1-u)
                for ab,v in zip(r['action_intervals'],(truth,-truth)):self.assertLessEqual(F(ab[0]),v);self.assertLessEqual(v,F(ab[1]))
            total+=(b-a)*max(map(abs,map(F,r['action_intervals'][0])))
        self.assertGreaterEqual(total,F(1,6));self.assertLess(total,F(1,5))

    def test_full_coordinate_conversion_and_same_term_intersections(self):
        x=[[F(i==j) for j in range(119)] for i in range(119)];p=[['0'] for _ in range(119)];p[0]=['1'];p[94]=['2'];p[115]=['3']
        source=dict(polynomials=p,duration_s='1/10',subcells=[dict(left=str(F(k,8)),right=str(F(k+1,8)),rhs_remainder_upper=['0']*119) for k in range(8)])
        metric=dict(accepted=True,metric=[[str(int(i==j)) for j in range(4)] for i in range(4)],anchor_normalization_upper='1')
        r=law.budgets(x,[1]*119,cover([[0]*119 for _ in range(119)]),source,[1]*25,metric)
        self.assertEqual(F(r['nodal_direct_upper_v'][0]),1)
        for i,truth in ((0,F(1,5)),(21,F(3,20))):
            self.assertLessEqual(truth,F(r['block_forcing_l1_upper_v'][i]));self.assertLess(F(r['block_forcing_l1_upper_v'][i])-truth,F(1,10**70))
        old=dict(nodal_direct_v=['2']*94,block_forcing_l1_v=['1']*22,comparison_per_s=[['1']],nodal_block_gains=[['1']])
        direct=law.refine_metrics(old,r,False);both=law.refine_metrics(old,r,True)
        self.assertEqual(direct['block_forcing_l1_v'],old['block_forcing_l1_v']);self.assertEqual(both['block_forcing_l1_v'][0],r['block_forcing_l1_upper_v'][0])
        self.assertEqual(both['block_forcing_l1_v'][21],r['block_forcing_l1_upper_v'][21]);self.assertEqual(direct['comparison_per_s'],old['comparison_per_s'])
        with self.assertRaises(ValueError):law.refine_metrics(old,r|dict(action_enclosed=False),True)
        bad=deepcopy(source);bad['subcells'][1]['left']='0'
        with self.assertRaises(ValueError):law.budgets(x,[1]*119,cover([[0]*119 for _ in range(119)]),bad,[1]*25,metric)

    def test_all_full_rhs_polynomials_and_constitutive_remainders_replay(self):
        self.assertEqual(producer.prior.serial(self.prepared),self.rec['prepared'])
        for base,rhs in zip(self.rec['base_cells'],self.report['rhs']):
            self.assertEqual(law.rhs(self.network,self.graph,self.prepared,F(base['left']),F(base['right'])),rhs)
            residual,errors,_=law.iv.polynomial_residual(self.network,self.graph,self.prepared,F(base['left']),F(base['right']))
            self.assertEqual([list(map(str,p)) for p in residual],rhs['polynomials'][:94])
            self.assertEqual(list(map(F,base['residual_bounds']['polynomial_uniform_remainder_a'])),errors)
            self.assertEqual(len(rhs['polynomials']),119);self.assertEqual(rhs['omitted_rhs_components'],0)
            for sub in rhs['subcells']:
                self.assertEqual(list(map(F,sub['nodal_uniform_remainder_a'])),errors)
                for i,c in enumerate(sub['constitutive_correction_intervals']):self.assertGreaterEqual(F(sub['rhs_remainder_upper'][i]),errors[i]+max(map(abs,map(F,c))))
                self.assertEqual(sub['rhs_remainder_upper'][94:],['0']*25)

    def test_all_128_actions_inverses_rates_and_refined_metrics_replay(self):
        r=self.report;count=0;scales=list(map(F,r['descriptor_scales']))
        for t,old in zip(r['trials'],self.rec['trials']):
            for row,base,c,original,rhs in zip(t['cells'],self.rec['base_cells'],old['covers'],old['cells'],r['rhs']):
                inverse,digest=producer.prior.prior.inverse(base,c,scales)
                self.assertEqual(digest,row['inverse_intervals_sha256']);self.assertEqual(law.prior.digest(c),row['source_cover_sha256'])
                self.assertEqual(law.prior.digest(original['rate_certificate']),row['source_rate_sha256'])
                self.assertEqual(law.budgets(base['inverse_binary'],scales,c['cover'],rhs,r['weights'],self.source['fixed_metric']),row['action'])
                count+=len(row['action']['subcells'])
            for mode in t['modes']:
                for row,action,original in zip(mode.get('cells',[]),t['cells'],old['cells']):
                    expected=law.refine_metrics(original['metrics'],action['action'],mode['mode']=='direct_and_memory');self.assertEqual(row['metrics'],expected)
                    for k in ('comparison_per_s','nodal_block_gains'):self.assertEqual(expected[k],original['metrics'][k])
                    self.assertTrue(all(F(a)<=F(b) for a,b in zip(expected['nodal_direct_v'],original['metrics']['nodal_direct_v'])))
        self.assertEqual(count,r['action_subcell_certificates']);self.assertEqual(count,128)

    def test_every_strict_closure_order_selection_and_actual_prefix(self):
        r=self.report;selected=None;incoming=law.prior.transfer(self.previous);origin=F(self.previous['peak_node_error_upper_v'])
        self.assertEqual(r['source_certified_result_sha256'],law.prior.digest(self.previous));self.assertEqual(r['incoming_block_error_upper_v'],incoming)
        for i,t in enumerate(r['trials']):
            for j,m in enumerate(t['modes']):
                if m.get('cells'):self.assertEqual(law.prior.blocks.close(m['cells'],incoming,F(t['radius_v']),origin),m['result'])
                else:self.assertFalse(m['result']['accepted'])
                if m['result']['accepted'] and selected is None:selected=[i,j]
        self.assertEqual(r['primary_trial_mode'],selected)
        if selected is not None:
            final=r['trials'][selected[0]]['modes'][selected[1]]['result'];self.assertTrue(final['actual_dae_error_bound'])
            self.assertEqual(len(law.prior.transfer(final)),22);self.assertEqual(r['final_certified_result'],final);self.assertEqual(r['accepted_intervals_total'],4)
            self.assertEqual(r['continuous_actual_error_certified_duration_s'],self.rec['end_s']);self.assertIsNone(r['first_gap_index'])
        else:
            self.assertEqual(r['final_certified_result'],self.previous);self.assertEqual(r['accepted_intervals_total'],3);self.assertEqual(r['first_gap_index'],3)
        self.assertEqual(r['fourth_interval_nonlinear_error_proven'],selected is not None);self.assertEqual(r['interface'],self.rec['interface'])
        with self.assertRaises(ValueError):producer.support(self.source|dict(first_gap_index=4))
        bad=deepcopy(self.source);bad['final_certified_result']['actual_dae_error_bound']=False
        with self.assertRaises(ValueError):producer.support(bad)

    def test_storage_sources_reuse_costs_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-residual-action/v1');self.assertEqual(gzip.decompress(raw),canonical(r))
        self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['reused_inverse_enclosures'],16);self.assertEqual(r['reused_rate_certificates'],16)
        self.assertEqual(r['mode_order'],list(producer.MODES));self.assertEqual(r['radius_order'],self.source['radius_order'])
        self.assertEqual(r['fixed_metric_sha256'],self.source['metric_sha256'])
        for field in ('new_nonlinear_solves','new_preconditioners','new_metric_systems','new_rate_ldlt_queries'):self.assertEqual(r[field],0)
        for flag in ('trajectory_changed','junction_norm_changed','dc_anchor_reset','original_integrator_modified','prior_reports_modified','numerical_gates_changed','small_currents_dropped','circuit_regularized','independent_remainders_cancelled','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[flag])
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)

if __name__=='__main__':unittest.main()
