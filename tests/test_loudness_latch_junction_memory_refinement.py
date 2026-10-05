from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
from unittest.mock import patch
import gzip,hashlib,json,sys,subprocess,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_junction_memory_refinement as p
law=p.law;prior=p.prior;poly=law.real.poly
sha=lambda raw:hashlib.sha256(raw).hexdigest()


class JunctionMemoryRefinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
        cls.r=p.read(p.OUTPUT);cls.old=p.read(p.ancestor.OUTPUT)
        cls.source_record=p.ancestor.load_artifact(cls.old['variants'][0]['records'][0]['storage'],'interval',32,8)['record']
        cls.left_template=p.ancestor.load_artifact(cls.old['templates'][0]['storage'],'template',32)
        cls.template=p.ancestor.load_artifact(cls.old['templates'][1]['storage'],'template',33)
        cls.block=p.ancestor.load_artifact(cls.r['source_block_storage'],'block',1,1)['block']
        cls.previous,cls.metric,cls.left,cls.end=p.source(cls.old,cls.source_record,cls.left_template,cls.template,cls.block)
        cls.network=prior.constructor.CompensatedBdfNetwork(200,prior.constructor.model_parameters(1,'finite_transit'))
        cls.graph=p.read(prior.graph_source.OUTPUT)['graph'];cls.startup=p.read(prior.startup_source.OUTPUT)
        cls.item=p.ancestor.unpack_template(cls.network,cls.startup,cls.template,cls.old['templates'][1]['storage'])
        cls.weights=list(map(F,cls.r['weights']));cls.scales=list(map(F,cls.r['descriptor_scales']))
        cls.inverse=p.reconstruct_inverse(cls.network,cls.graph,cls.item,cls.block,cls.scales)
        cls.context=p.ancestor.prepared_action.prepare(cls.block['candidate_inverse_binary'],cls.scales,cls.block['cover'])
        cls.branches=[]
        for row in cls.r['variants']:
            n=row['partition'];data=[p.load_artifact(c['storage'],'cell',n,c['index']) for c in row['cells']]
            support=p.load_artifact(row['storage'],'support',n);record=support['record']
            record=record|dict(trials=[record['trials'][0]|dict(cells=[d['cell'] for d in data])])
            cls.branches.append(dict(row=row,data=data,support=support,record=record))
    @classmethod
    def tearDownClass(cls):sys.set_int_max_str_digits(cls.limit)

    def test_source_curve_domain_inverse_and_three_rates_reused_by_identity(self):
        r=self.r;b=self.block
        self.assertEqual(r['source_certified_result_sha256'],law.digest(self.previous));self.assertEqual(r['source_selected_variant_index'],0)
        self.assertEqual(r['source_interval_index'],32);self.assertEqual(r['source_accepted_intervals'],33)
        self.assertEqual(r['metric_sha256'],self.old['metric_sha256']);self.assertEqual(r['fixed_metric'],self.old['fixed_metric'])
        self.assertEqual(r['prepared_sha256'],self.template['prepared_sha256']);self.assertEqual(r['groups'],self.old['groups'])
        self.assertEqual(b['support_indices'],[33]);self.assertEqual(b['reference_sha256'],[r['prepared_sha256']])
        self.assertEqual(b['action_preparation'],dict(input_sha256=self.context.input_sha256,state_sha256=self.context.state_sha256,n=119))
        self.assertLess(F(b['cover']['contraction_upper']),1)
        with localcontext() as ctx:
            ctx.prec=100
            matrix,_=prior.descriptor(self.network,self.graph,[law.real.event.decimal(poly.evaluate(v,F(1,2))) for v in self.item['prepared']['x']],100)
        binary=p.ancestor.np.array(matrix,dtype=float)
        self.assertEqual(law.digest(binary.tolist()),b['descriptor_binary_sha256'])
        self.assertEqual(p.ancestor.np.linalg.inv(binary).tolist(),b['candidate_inverse_binary'])
        basis=law.blocks.directed.basis(self.metric);balance=law.blocks.balanced.balance(basis)
        _,rates=law.cell_metrics(self.inverse,self.weights,self.template['forcing'][0],self.metric,basis,balance)
        self.assertEqual(rates,b['rate_certificate']);self.assertEqual(sum(len(v['probes']) for v in rates.values()),99)
        historical=p.ancestor.load_artifact(self.old['variants'][3]['records'][1]['storage'],'interval',33,1)['record']
        self.assertEqual(r['historical_control_incoming_sha256'],historical['incoming_certified_result_sha256'])
        self.assertFalse(r['same_historical_control_incoming']);self.assertNotEqual(law.transfer(self.previous),historical['incoming_block_error_upper_v'])
        self.assertEqual(p.serial(self.item['prepared']),self.template['prepared'])

    def test_every_fine_rhs_remainder_query_and_physical_duration(self):
        for branch in self.branches:
            n=branch['row']['partition']
            for k,data in enumerate(branch['data']):
                lo,hi=F(k,n),F(k+1,n);prepared=self.item['prepared']
                self.assertEqual(data['source_sha256'],self.r['producer_source_sha256']);self.assertEqual(data['prepared_sha256'],self.r['prepared_sha256'])
                rhs=law.action.rhs(self.network,self.graph,prepared,lo,hi);residual,forcing=law.real.tube.forcing(self.network,self.graph,prepared,lo,hi)
                self.assertEqual(rhs,data['rhs']);self.assertEqual(forcing,data['cell']['forcing_inputs']);self.assertEqual(p.serial(residual),data['residual_bounds'])
                p.check_duration(forcing,rhs,prepared,n,k);self.assertEqual(F(rhs['duration_s']),prepared['h']/n)
                self.assertEqual((data['left'],data['right']),(str(lo),str(hi)));self.assertEqual(rhs['omitted_rhs_components'],0)
                self.assertEqual(len(rhs['polynomials']),119);self.assertEqual(len(rhs['subcells']),8)
                for query in data['queries']:
                    u=F(query['u']);actual=lo+(hi-lo)*u
                    self.assertEqual(F(query['absolute_u']),actual)
                    truth=law.real.tube.query(self.network,self.graph,prepared,actual,100);self.assertEqual(truth,query['decimal100'])
                    remainder=rhs['subcells'][min(int(u*8),7)]['rhs_remainder_upper']
                    for i,value in enumerate(truth['kcl_a']+truth['constraint_v']):
                        nominal=poly.evaluate(tuple(map(F,rhs['polynomials'][i])),u);error=F(remainder[i]);display=F(1,10**90)*(1+abs(nominal))
                        self.assertLessEqual(nominal-error-display,F(value));self.assertLessEqual(F(value),nominal+error+display)
                    self.assertLessEqual(abs(F(truth['dynamic_conservation_error_a'])),F(1,10**90))
                if n==8:
                    self.assertEqual(rhs,self.template['rhs'][k]);self.assertEqual(forcing,self.template['forcing'][k]);self.assertEqual(data['residual_bounds'],self.template['residual_bounds'][k])
                print(json.dumps(dict(replayed_rhs_partition=n,cell=k,decimal100_and_physical_clock=True)),flush=True)

    def test_all_actions_match_complete_original_prepared_and_archived_bytes(self):
        historical=p.ancestor.load_artifact(self.old['variants'][3]['records'][1]['storage'],'interval',33,1)['record'];count=0
        for branch in self.branches:
            n=branch['row']['partition']
            for k,data in enumerate(branch['data']):
                cell=data['cell'];rhs=data['rhs']
                control=law.action.budgets(self.block['candidate_inverse_binary'],self.scales,self.block['cover'],rhs,self.weights,self.metric)
                replay=p.ancestor.prepared_action.budgets(self.context,self.block['candidate_inverse_binary'],self.scales,self.block['cover'],rhs,self.weights,self.metric)
                self.assertEqual(p.canonical(control),p.canonical(replay));self.assertEqual(p.canonical(control),p.canonical(cell['action']))
                original=law.fine.fine_metrics(self.inverse,self.weights,cell['forcing_inputs'],self.metric,self.block['rate_certificate']['balanced']['mu_metric_upper_per_s'])
                self.assertEqual(original,cell['original_metrics']);self.assertEqual(law.action.refine_metrics(original,control,True),cell['metrics'])
                self.assertEqual(cell['rhs_sha256'],law.digest(rhs));self.assertEqual(cell['action_context_sha256'],self.context.input_sha256);self.assertEqual(cell['action_state_sha256'],self.context.state_sha256)
                if n==8:
                    self.assertEqual(p.canonical(control),p.canonical(historical['trials'][1]['cells'][k]['action']))
                    self.assertEqual(cell['metrics'],historical['trials'][1]['cells'][k]['metrics'])
                self.assertFalse(control['new_trajectory_solve']);self.assertTrue(control['action_enclosed'])
                self.assertTrue(all(not s['independent_remainders_cancelled'] for s in control['subcells']));count+=1
                print(json.dumps(dict(replayed_action_partition=n,cell=k,complete_certificate_bytes_equal=True)),flush=True)
        self.assertEqual(count,self.r['new_budget_calls']);self.assertEqual(count*8,self.r['new_action_subcell_certificates'])

    def test_actual_transport_closures_and_exact_nodal_memory_assembly(self):
        selected=None;final=self.previous;end=self.end
        for j,branch in enumerate(self.branches):
            self.assertIsNone(selected);record=branch['record'];row=branch['row'];n=row['partition']
            self.assertEqual(n,p.PARTITIONS[j]);self.assertEqual(record['incoming_certified_result_sha256'],law.digest(self.previous))
            self.assertEqual(record['incoming_block_error_upper_v'],law.transfer(self.previous));self.assertEqual(record['incoming_metric_sha256'],self.r['metric_sha256'])
            self.assertEqual(record['interface'],law.real.continuity(self.network,self.left,self.item['prepared'],self.end,F(record['start_s'])))
            result=law.blocks.close(record['trials'][0]['cells'],law.transfer(self.previous),p.RADIUS,F(self.previous['peak_node_error_upper_v']))
            self.assertEqual(p.canonical(result),p.canonical(record['trials'][0]['result']));self.assertEqual(law.digest(result),row['full_result_sha256'])
            self.assertEqual(p.diagnostic(record),branch['support']['diagnostic'])
            for cell,trace,diag in zip(record['trials'][0]['cells'],result['propagation']['trace'],branch['support']['diagnostic']['rows']):
                self.assertEqual(F(diag['node66_anchor_v']),sum(map(F,diag['node66_anchor_terms_v']),F(0)))
                self.assertEqual(F(diag['node66_forced_v']),sum(map(F,diag['node66_forced_terms_v']),F(0))+F(diag['node66_direct_v']))
                self.assertEqual(len(diag['node66_anchor_terms_v']),22);self.assertEqual(len(diag['node66_forced_terms_v']),22)
                self.assertEqual(F(trace['left']),F(cell['index'],n));self.assertEqual(F(trace['right']),F(cell['index']+1,n))
            self.assertEqual(law.select(record['trials']),record['selected_trial_index'])
            admitted=law.admit(self.previous,self.end,record)
            if admitted is not None:
                selected=j;final,end=admitted;self.assertLess(F(result['peak_node_error_upper_v']),p.RADIUS)
            else:
                self.assertFalse(result['actual_dae_error_bound'])
                with self.assertRaises(ValueError):law.transfer(result)
            print(json.dumps(dict(replayed_closure_partition=n,accepted=admitted is not None,local_peak_v=float(F(row['local_peak_v'])))),flush=True)
        self.assertEqual(selected,self.r['selected_variant_index']);self.assertEqual(p.canonical(final),p.canonical(self.r['final_certified_result']))
        self.assertEqual(str(end),self.r['continuous_actual_error_certified_duration_s']);self.assertEqual(self.r['accepted_intervals_total'],33+(selected is not None))
        self.assertEqual(self.r['first_gap_index'],33 if selected is None else None)
        self.assertEqual(self.r['stop_reason'],'all_partitions_rejected' if selected is None else 'declared_first_closure')
        self.assertFalse(self.branches[0]['row']['accepted'])

    def test_zero_generator_exact_total_forcing_survives_outer_partition(self):
        anchor=F(1,2**24);total=F(1,2**23)
        for n in p.PARTITIONS:
            cells=[dict(index=k,inverse_certified=True,forcing_inputs=dict(left=str(F(k,n)),right=str(F(k+1,n)),duration_s=str(F(1,n))),
                metrics=dict(comparison_per_s=[['0']],block_forcing_l1_v=[str(total/n)],nodal_block_gains=[['1']],nodal_direct_v=['0'])) for k in range(n)]
            result=law.blocks.close(cells,[str(anchor)],p.RADIUS,anchor)
            self.assertTrue(result['accepted']);self.assertEqual(F(result['peak_node_error_upper_v']),anchor+total)
            self.assertEqual(F(result['propagation']['endpoint_anchor_v'][0]),anchor);self.assertEqual(F(result['propagation']['endpoint_forced_v'][0]),total)
            bad=cells[1:]
            self.assertFalse(law.blocks.close(bad,[str(anchor)],p.RADIUS,anchor)['accepted'])

    def test_negative_duration_identity_provider_and_incoming_rejected(self):
        data=self.branches[0]['data'][0];forcing=data['cell']['forcing_inputs'];rhs=data['rhs'];prepared=self.item['prepared']
        with self.assertRaisesRegex(ValueError,'physical cell clock'):p.check_duration(forcing,rhs|dict(duration_s='1'),prepared,8,0)
        with self.assertRaisesRegex(ValueError,'physical cell clock'):p.check_duration(forcing|dict(left='1/8'),rhs,prepared,8,0)
        with self.assertRaisesRegex(ValueError,'complete RHS'):p.check_duration(forcing,rhs|dict(subcells=rhs['subcells'][:-1]),prepared,8,0)
        with patch.object(law.real.tube,'forcing',return_value=(None,forcing)),patch.object(law.action,'rhs',return_value=rhs|dict(duration_s='1')):
            provider=unittest.mock.Mock()
            with self.assertRaisesRegex(ValueError,'physical cell clock'):p.build_cell(self.network,self.graph,prepared,self.inverse,self.block,self.weights,self.scales,self.metric,self.context,provider,8,0,{})
            provider.budgets.assert_not_called()
        with self.assertRaisesRegex(ValueError,'action provider'):p.build_cell(None,None,None,None,None,None,None,None,None,None,8,0,{})
        with self.assertRaises(ValueError):p.source(self.old|dict(selected_variant_index=3),self.source_record,self.left_template,self.template,self.block)
        with self.assertRaises(ValueError):p.source(self.old,self.source_record|dict(selected_trial_index=None),self.left_template,self.template,self.block)
        with self.assertRaises(ValueError):p.source(self.old,self.source_record,self.left_template,self.template,self.block|dict(radius_v='1/100000'))
        with self.assertRaises(ValueError):p.source(self.old,self.source_record,self.left_template,self.template|dict(start_s='0'),self.block)
        with self.assertRaises(ValueError):p.reconstruct_inverse(self.network,self.graph,self.item,self.block|dict(inverse_intervals_sha256='wrong'),self.scales)
        with self.assertRaisesRegex(ValueError,'input identity'):p.ancestor.prepared_action.verify(self.context,self.block['candidate_inverse_binary'],self.scales,self.block['cover']|dict(changed=True))
        for args in (('cell',True,0),('cell',8,True),('cell',8,8),('cell',4,0),('support',8,0),('invalid',8)):
            with self.assertRaises(ValueError):p.artifact_path(*args)
        storage=self.branches[0]['row']['cells'][0]['storage']
        for field in ('path','compressed_sha256','canonical_json_sha256'):
            with self.assertRaises(ValueError):p.load_artifact(storage|{field:'wrong'},'cell',8,0)
        with self.assertRaises(ValueError):p.load_artifact(storage,'cell',8,1)

    def test_full_manifest_artifacts_counters_and_scope(self):
        r=self.r;raw=p.OUTPUT.read_bytes();summary=json.loads(p.SUMMARY.read_text(encoding='utf-8'));storage=summary['storage']
        self.assertEqual(gzip.decompress(raw),p.canonical(r));self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(p.canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        self.assertEqual(r['partition_order'],list(p.PARTITIONS));self.assertEqual(F(r['radius_v']),p.RADIUS)
        self.assertEqual(r['new_budget_calls'],sum(v['partition'] for v in r['variants']));self.assertEqual(r['new_action_subcell_certificates'],r['new_budget_calls']*8)
        self.assertEqual(r['new_prepared_contexts'],1);self.assertEqual(r['reused_inverse_enclosures'],1);self.assertEqual(r['inverse_reconstructions'],1)
        self.assertEqual(r['reused_rate_certificates'],1);self.assertEqual(r['reused_rate_queries'],99)
        for key in ('new_nonlinear_solves','new_preconditioners','new_inverse_certificates','new_rate_queries','new_metric_systems'):self.assertEqual(r[key],0)
        for key in ('reference_changed','incoming_reset','clock_translation','junction_norm_changed','prior_reports_modified','original_integrator_modified','numerical_gates_changed','independent_remainders_cancelled','partial_artifacts_admitted','global_1mv_gate_closed','full_path_coverage','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[key])
        self.assertEqual(r['integer_text_limit_during'],0)
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        for branch in self.branches:
            support=branch['support'];self.assertEqual(support['full_result_sha256'],branch['row']['full_result_sha256'])
            self.assertEqual(support['record']['trials'][0]['cells'],branch['row']['cells'])
            for name,h in support['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        with self.assertRaises(ValueError):p.generate()
        with self.assertRaises(ValueError):p.save(r)

    def test_launch_recovers_exact_frozen_source_and_all_output(self):
        launch=json.loads(p.LAUNCH.read_text(encoding='utf-8'));name=Path(p.__file__).resolve().relative_to(ROOT).as_posix()
        self.assertEqual(launch['schema'],p.SCHEMA+'-launch/v1');self.assertEqual(launch['exit_code'],0);self.assertEqual(launch['stderr'],'')
        self.assertTrue(launch['measurement_published']);self.assertTrue(launch['inputs_unchanged']);self.assertEqual(launch['command'][1],'-B')
        self.assertEqual(Path(launch['command'][2]),Path(p.__file__).resolve());self.assertEqual(launch['source_sha256_before'],launch['source_sha256_after'])
        self.assertEqual(launch['source_sha256'],self.r['producer_source_sha256']);raw=launch['producer_source_utf8'].encode('utf-8')
        self.assertEqual(sha(raw),launch['source_sha256'][name]);self.assertEqual(subprocess.check_output(['git','show',launch['environment']['git_head']+':'+name]),raw)
        rows=[json.loads(line) for line in launch['stdout'].splitlines()]
        self.assertEqual([(row['partition'],row['cell']) for row in rows if 'cell' in row],[(v['partition'],k) for v in self.r['variants'] for k in range(v['partition'])])
        self.assertEqual([row['partition'] for row in rows if 'accepted' in row],[v['partition'] for v in self.r['variants']])


if __name__=='__main__':unittest.main()
