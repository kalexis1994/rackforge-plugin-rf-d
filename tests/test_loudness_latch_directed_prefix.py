from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
from copy import deepcopy
import gzip,hashlib,json,subprocess,sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_directed_prefix as producer
from loudness_latch_bdf_doubling_survey import canonical
law=producer.law
sha=lambda raw:hashlib.sha256(raw).hexdigest()


class FinePrefix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=producer.read(producer.OUTPUT);cls.source=producer.read(producer.prior.OUTPUT);cls.history=producer.read(producer.prior.prior.OUTPUT)
        cls.previous,cls.metric=law.source(cls.source,cls.history,producer.SOURCE_SELECTION)
        cls.startup=producer.read(producer.startup_source.OUTPUT)
        cls.network=producer.constructor.CompensatedBdfNetwork(200,producer.constructor.model_parameters(1,'finite_transit'))
        cls.graph=producer.read(producer.graph_source.OUTPUT)['graph'];cls.prepared=[];cls.inverses=[]
        scales=list(map(F,cls.report['descriptor_scales']))
        for rec in cls.report['records']:
            k=rec['interval_index'];a=producer.startup_source.unpack(cls.network,cls.startup['rows'][k-1]['history']);b=producer.startup_source.unpack(cls.network,cls.startup['rows'][k]['history'])
            cls.prepared.append(law.real.prepare(cls.network,a,b));families=[]
            for trial in rec['trials']:
                values=[]
                for base,row in zip(rec['base_cells'],trial['covers']):
                    if not row['inverse_certified']:continue
                    inv,cert=law.real.tube.cells.structured_inverse(base['inverse_binary'],scales,row['cover'],F(row['cover']['contraction_upper']))
                    if cert!=row['inverse_certificate']:raise AssertionError('inverse certificate differs')
                    if law.digest(law.real.tube.cells.packed_matrix(inv))!=row['inverse_intervals_sha256']:raise AssertionError('inverse enclosure hash differs')
                    values.append(inv)
                families.append(values)
            cls.inverses.append(families)

    def test_secondary_source_fixed_norm_and_individual_transport(self):
        r=self.report;self.assertEqual(r['source_trial_mode'],[1,1]);self.assertEqual(r['source_primary_trial_mode'],[1,0])
        self.assertEqual(r['source_certified_result_sha256'],law.digest(self.previous));self.assertEqual(r['fixed_metric'],self.metric)
        self.assertEqual(r['metric_sha256'],law.digest(self.metric));self.assertEqual(r['groups'],[list(g) for g in law.fine.GROUPS])
        incoming=law.transfer(self.previous);self.assertEqual(incoming,r['records'][0]['incoming_block_error_upper_v'])
        p=self.previous['propagation'];self.assertEqual(list(map(F,incoming)),[F(a)+F(b) for a,b in zip(p['endpoint_anchor_v'],p['endpoint_forced_v'])])
        self.assertGreater(len(set(incoming[:17])),1);self.assertEqual(r['congruence'],law.blocks.directed.basis(self.metric))
        self.assertEqual(r['balance'],law.blocks.balanced.balance(r['congruence']))

    def test_real_clocks_history_reconstruction_and_interfaces(self):
        left=self.history['records'][-1]['prepared'];end=F(self.source['end_s'])
        for rec,p in zip(self.report['records'],self.prepared):
            self.assertEqual(producer.serial(p),rec['prepared']);self.assertEqual(F(p['start_s']),end)
            self.assertEqual(p['h'],F(p['end_s'])-F(p['start_s']));self.assertEqual(law.real.continuity(self.network,left,p,end,F(p['start_s'])),rec['interface'])
            for u,k in ((F(0),rec['interval_index']-1),(F(1),rec['interval_index'])):
                h=producer.startup_source.unpack(self.network,self.startup['rows'][k]['history'])
                self.assertEqual([law.real.poly.evaluate(v,u) for v in p['x']],law.real.origin.state_values(h.current))
                self.assertEqual([law.real.poly.evaluate(v,u) for v in p['y_linear']],law.real.origin.charge_coordinates(self.network.network,h.current)[:21])
            bad=deepcopy(producer.serial(p));bad['x'][0][0]=str(F(bad['x'][0][0])+1)
            with self.assertRaises(ValueError):law.real.continuity(self.network,left,bad,end,F(p['start_s']))
            with self.assertRaises(ValueError):law.real.continuity(self.network,left,p,end+1,F(p['start_s']))
            left=p;end=F(p['end_s'])

    def test_every_mean_cover_residual_inverse_and_diagnostic_replays(self):
        scales=list(map(F,self.report['descriptor_scales']))
        for rec,p in zip(self.report['records'],self.prepared):
            gains=law.real.tube.gains(self.network,self.graph)
            for base in rec['base_cells']:
                a,b=F(base['left']),F(base['right']);residual,forcing=law.real.tube.forcing(self.network,self.graph,p,a,b)
                self.assertEqual(producer.serial(residual),base['residual_bounds']);self.assertEqual(forcing,base['forcing_inputs'])
                with localcontext() as ctx:
                    ctx.prec=100;x=[law.real.event.decimal(law.real.poly.evaluate(v,(a+b)/2)) for v in p['x']]
                    h,_=producer.descriptor(self.network,self.graph,x,100)
                self.assertEqual(law.digest(np.array(h,dtype=float).tolist()),base['descriptor_binary_sha256'])
                constant,terms=law.real.tube.weighted.compile_terms(self.network,self.graph,p,base['inverse_binary'],scales)
                for trial in rec['trials']:
                    if not trial['covers']:continue
                    row=trial['covers'][base['index']];cover=law.real.tube.inflated_cover(constant,terms,gains,a,b,F(trial['radius_v']))
                    self.assertEqual(cover,row['cover']);self.assertEqual(cover['strict_contraction'],row['inverse_certified'])
            for q in rec['queries']:self.assertEqual(law.real.tube.query(self.network,self.graph,p,F(q['u']),100),q['decimal100'])

    def test_every_new_rate_and_fine_conversion_replays_in_fixed_metric(self):
        r=self.report;queries=0
        for rec,families in zip(r['records'],self.inverses):
            self.assertEqual(rec['incoming_metric_sha256'],r['metric_sha256'])
            for trial,inverses in zip(rec['trials'],families):
                for row,inverse in zip(trial['cells'],inverses):
                    metrics,rate=law.cell_metrics(inverse,r['weights'],row['forcing_inputs'],self.metric,r['congruence'],r['balance'])
                    self.assertEqual(metrics,row['original_metrics']);self.assertEqual(rate,row['rate_certificate'])
                    self.assertEqual(F(metrics['comparison_per_s'][21][21]),F(rate['balanced']['mu_metric_upper_per_s']))
                    queries+=sum(len(v['probes']) for v in rate.values())
                    self.assertTrue(all(rate[key]['final_raw_upper_ldlt']['positive_definite'] for key in ('directed','balanced')))
                    self.assertTrue(rate['isotropic']['final_upper_ldlt']['positive_definite'])
        self.assertEqual(queries,r['new_rate_ldlt_queries'])

    def test_every_closure_selection_lineage_and_first_gap_replays(self):
        r=self.report;previous=self.previous;end=F(r['initial_certified_end_s']);accepted=0
        self.assertEqual(sys.get_int_max_str_digits(),4300)
        self.assertEqual(r['accepted_intervals_total'],6);self.assertEqual(r['first_gap_index'],6)
        self.assertEqual([rec['selected_trial_index'] for rec in r['records']],[1,1,None])
        self.assertEqual(sum('4300 digits' in (t['result']['reason'] or '') for rec in r['records'] for t in rec['trials']),2)
        for i,rec in enumerate(r['records']):
            self.assertEqual(rec['incoming_block_error_upper_v'],law.transfer(previous));origin=F(previous['peak_node_error_upper_v'])
            self.assertEqual(F(rec['incoming_node_error_upper_v']),origin)
            for t in rec['trials']:
                if origin>=F(t['radius_v']):self.assertEqual(t['covers'],[]);self.assertFalse(t['result']['accepted'])
                if t['cells']:self.assertEqual(law.blocks.close(t['cells'],law.transfer(previous),F(t['radius_v']),origin),t['result'])
                elif t['covers']:self.assertFalse(all(v['inverse_certified'] for v in t['covers']))
            self.assertEqual(law.select(rec['trials']),rec['selected_trial_index'])
            next_state=law.admit(previous,end,rec)
            if next_state is None:
                self.assertEqual(i,len(r['records'])-1);self.assertEqual(r['first_gap_index'],rec['interval_index']);break
            previous,end=next_state;accepted+=1
        self.assertEqual(r['accepted_additional_intervals'],accepted);self.assertEqual(r['accepted_intervals_total'],4+accepted)
        self.assertEqual(F(r['continuous_actual_error_certified_duration_s']),end);self.assertEqual(previous,r['final_certified_result'])
        if accepted==len(r['records']):self.assertIsNone(r['first_gap_index']);self.assertEqual(accepted,producer.ADDITIONAL_LIMIT)

    def test_known_nonlinear_sequence_changing_steps_and_direction_without_reset(self):
        def cell(h,forcing=None,matrix=None):
            matrix=matrix or [[F(-8,5) if i==j==0 else -F(i==j) for j in range(22)] for i in range(22)]
            return dict(inverse_certified=True,forcing_inputs=dict(left='0',right='1',duration_s=str(h)),metrics=dict(
                comparison_per_s=law.blocks.blocks.pack(matrix),block_forcing_l1_v=list(map(str,forcing or [h]+[F(0)]*21)),
                nodal_block_gains=[['1']+['0']*21],nodal_direct_v=['0']))
        # y'=-y^2, yhat=1, true error t/(1+t). On t<=.3, rate <=-1.6.
        incoming=['0']*22;t=F(0);origin=F(0);result=None
        for h in (F(1,20),F(1,10),F(3,20)):
            result=law.blocks.close([cell(h)],incoming,F(1,2),origin);self.assertTrue(result['accepted']);t+=h
            self.assertLessEqual(t/(1+t),F(result['peak_node_error_upper_v']))
            incoming=law.transfer(result);origin=F(result['peak_node_error_upper_v'])
            self.assertGreater(F(incoming[0]),0);self.assertEqual(incoming[1:],['0']*21)
        rejected=law.blocks.close([cell(F(1,20))],incoming,F(1,100),origin);self.assertFalse(rejected['accepted'])
        with self.assertRaises(ValueError):law.transfer(rejected)
        matrix=[[F(0) for _ in range(22)] for _ in range(22)];matrix[0][0]=-1;matrix[0][1]=10
        directed=cell(F(1,10),[F(0)]*22,matrix)
        first=law.blocks.close([directed],['1']+['0']*21,F(11,10),1);self.assertTrue(first['accepted'])
        memory=law.transfer(first);second=law.blocks.close([directed],memory,F(11,10),F(first['peak_node_error_upper_v']))
        self.assertTrue(second['accepted']);self.assertGreater(F(memory[0]),0);self.assertEqual(F(memory[1]),0)
        coarse=[str(max(map(F,memory[:17])))]*17+memory[17:]
        self.assertFalse(law.blocks.close([directed],coarse,F(11,10),F(first['peak_node_error_upper_v']))['accepted'])

    def test_source_transport_and_admission_reject_bad_identity_or_conditional_proof(self):
        failed=json.loads((ROOT/'evidence/loudness_latch_bdf_static_precision_fine_prefix_measurement_attempt.json').read_text(encoding='utf-8'))
        self.assertEqual(failed['schema'],'rf-d/fine-prefix-measurement-attempt/v1')
        self.assertTrue(failed['numerical_measurement_started']);self.assertFalse(failed['full_report_saved'])
        self.assertEqual(sha(failed['failed_producer_source_utf8'].encode()),failed['failed_producer_sha256'])
        self.assertEqual(sha(subprocess.check_output(['git','show',failed['git_head']+':'+failed['failed_producer_path']],cwd=ROOT)),failed['failed_producer_sha256'])
        self.assertNotEqual(sha((ROOT/failed['failed_producer_path']).read_bytes()),failed['failed_producer_sha256'])
        self.assertIn('OverflowError',failed['reason']);self.assertTrue(failed['partial_acceptance_not_published'])
        self.assertEqual(producer.diagnostic_bound({}),None)
        self.assertEqual(producer.diagnostic_bound(dict(peak_node_error_upper_v='1/2')),0.5)
        self.assertIn('exact rational retained',producer.diagnostic_bound(dict(peak_node_error_upper_v=str(10**1000))))
        with self.assertRaises(ValueError):law.source(self.source,self.history,[1,0])
        for change in (dict(end_s='1'),dict(continuous_actual_error_certified_duration_s='1'),dict(source_certified_result_sha256='wrong'),dict(weights=['1']*25)):
            with self.assertRaises(ValueError):law.source(self.source|change,self.history,[1,1])
        with self.assertRaises(ValueError):law.source(self.source|dict(fixed_metric_sha256='wrong'),self.history,[1,1])
        bad=deepcopy(self.source);bad['trials'][1]['modes'][1]['result']['actual_dae_error_bound']=False
        with self.assertRaises(ValueError):law.source(bad,self.history,[1,1])
        with self.assertRaises(ValueError):law.transfer(self.previous|dict(accepted=False))
        bad=deepcopy(self.previous);bad['propagation']['endpoint_forced_v'][0]='-1'
        with self.assertRaises(ValueError):law.transfer(bad)
        bad=deepcopy(self.previous);bad['propagation']['endpoint_anchor_v'].pop()
        with self.assertRaises(ValueError):law.transfer(bad)
        rec=self.report['records'][0];end=F(self.report['initial_certified_end_s'])
        for change in (dict(start_s=str(end+1)),dict(end_s=str(end)),dict(incoming_certified_result_sha256='wrong'),dict(selected_trial_index=99)):
            with self.assertRaises(ValueError):law.admit(self.previous,end,rec|change)
        bad=deepcopy(rec);bad['interface']['charge_reset']=True
        with self.assertRaises(ValueError):law.admit(self.previous,end,bad)
        with self.assertRaises(ValueError):law.select([dict(result=dict(accepted=True,actual_dae_error_bound=False))])
        self.assertIsNone(law.select([dict(result=dict(accepted=False,actual_dae_error_bound=False))]))

    def test_all_rhs_actions_remainders_and_same_term_metrics_replay(self):
        r=self.report;count=0;scales=list(map(F,r['descriptor_scales']))
        for rec,p in zip(r['records'],self.prepared):
            self.assertEqual(len(rec['rhs']),8)
            for base,rhs in zip(rec['base_cells'],rec['rhs']):
                self.assertEqual(law.action.rhs(self.network,self.graph,p,F(base['left']),F(base['right'])),rhs)
                self.assertEqual(len(rhs['polynomials']),119);self.assertEqual(rhs['omitted_rhs_components'],0)
                for sub in rhs['subcells']:
                    for i,ab in enumerate(sub['constitutive_correction_intervals']):
                        self.assertGreaterEqual(F(sub['rhs_remainder_upper'][i]),F(sub['nodal_uniform_remainder_a'][i])+max(map(abs,map(F,ab))))
                    self.assertEqual(sub['rhs_remainder_upper'][94:],['0']*25)
            for t in rec['trials']:
                for row,base,cover,rhs in zip(t['cells'],rec['base_cells'],t['covers'],rec['rhs']):
                    expected=law.action.budgets(base['inverse_binary'],scales,cover['cover'],rhs,r['weights'],self.metric)
                    self.assertEqual(expected,row['action']);count+=len(expected['subcells'])
                    self.assertEqual(law.action.refine_metrics(row['original_metrics'],expected,True),row['metrics'])
                    for key in ('comparison_per_s','nodal_block_gains'):self.assertEqual(row['metrics'][key],row['original_metrics'][key])
        self.assertEqual(count,r['new_action_subcell_certificates'])

    def test_variable_descriptor_actions_remainders_and_changing_step_sequence(self):
        # H(t)=diag(1+t/10,1+t/20), b(t)=H(t)*[1,1]. Exact H^-1 b=[1,1].
        # Full independent residual errors are retained; y'=-y+1 has y=1-exp(-t).
        from test_loudness_latch_residual_action import cover
        incoming=['0']*22;origin=F(0);t=F(0);norms=[]
        for h in (F(1,20),F(1,10),F(3,20)):
            mids=[1+(t+h/2)/d for d in (10,20)]
            x=[[F(i==j)/mids[i] for j in range(2)] for i in range(2)]
            b=[(1+t/d,h/d) for d in (10,20)];epsilon=F(1,10**6)
            defect=[[(1-(1+(t+h)/d)/mids[i],1-(1+t/d)/mids[i]) if i==j else F(0) for j in range(2)] for i,d in enumerate((10,20))]
            compiled=law.action.compile_polynomials(x,[1,2],b)
            action=law.action.enclose(x,[1,2],cover(defect),compiled,[epsilon,epsilon],0,1)
            for u in (F(0),F(1,2),F(1)):
                for i,d in enumerate((10,20)):
                    for sign in (-1,1):
                        actual=1+sign*epsilon/(1+(t+h*u)/d)
                        self.assertLessEqual(F(action['action_intervals'][i][0]),actual)
                        self.assertLessEqual(actual,F(action['action_intervals'][i][1]))
            upper=max(map(abs,map(F,action['action_intervals'][0])))
            matrix=[[-F(i==j) for j in range(22)] for i in range(22)]
            cell=dict(inverse_certified=True,forcing_inputs=dict(left='0',right='1',duration_s=str(h)),metrics=dict(
                comparison_per_s=law.blocks.blocks.pack(matrix),block_forcing_l1_v=[str(h*upper)]+['0']*21,
                nodal_block_gains=[['1']+['0']*21],nodal_direct_v=['0']))
            result=law.blocks.close([cell],incoming,F(1,2),origin);self.assertTrue(result['accepted']);t+=h
            truth=1-law.blocks.blocks.exp_bounds(-t)[0]
            self.assertLessEqual(truth,F(result['peak_node_error_upper_v']))
            incoming=law.transfer(result);origin=F(result['peak_node_error_upper_v']);norms.append(incoming[0])
            self.assertEqual(incoming[1:],['0']*21)
        self.assertGreater(F(norms[-1]),F(norms[0]))

    def test_storage_sources_cost_counts_destinations_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-directed-prefix/v1');self.assertEqual(gzip.decompress(raw),canonical(r))
        self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['new_preconditioners'],8*len(r['records']));self.assertEqual(r['new_nonlinear_solves'],0);self.assertEqual(r['new_metric_systems'],0)
        self.assertEqual(r['new_inverse_enclosures'],sum(c['inverse_certified'] for rec in r['records'] for t in rec['trials'] for c in t['covers']))
        self.assertEqual(r['attempted_additional_intervals'],len(r['records']));self.assertLessEqual(len(r['records']),producer.ADDITIONAL_LIMIT)
        self.assertEqual(r['radius_order'],list(map(str,producer.RADII)));self.assertEqual(F(r['initial_certified_end_s']),F(self.source['end_s']))
        self.assertEqual(r['attempted_end_s'],r['records'][-1]['end_s'])
        for field in ('real_history_only','individual_memory_transport'):self.assertTrue(r[field])
        for field in ('junction_norm_changed','clock_translation','dc_anchor_reset','original_integrator_modified','prior_reports_modified','numerical_gates_changed','source_primary_selection_rewritten','small_currents_dropped','circuit_regularized','independent_remainders_cancelled','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[field])
        self.assertEqual(r['start_interval_index'],4);self.assertEqual(r['mode'],'direct_and_memory')
        self.assertEqual(r['new_action_subcell_certificates'],sum(len(c['action']['subcells']) for rec in r['records'] for t in rec['trials'] for c in t['cells']))
        self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)

if __name__=='__main__':unittest.main()
