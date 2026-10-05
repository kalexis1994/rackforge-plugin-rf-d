from pathlib import Path
from fractions import Fraction as F
from dataclasses import replace
from decimal import localcontext
from unittest.mock import patch
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_shared_continuation as producer
prior=producer.prior;law=producer.law;poly=law.real.poly
sha=lambda raw:hashlib.sha256(raw).hexdigest()


class SharedCovers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
        cls.manifest=producer.read(producer.OUTPUT);cls.source_report=producer.read(producer.shared.OUTPUT)
        control=producer.read(prior.OUTPUT);cls.left_record=prior.load_record(control['records'][-1])
        cls.source,cls.metric,cls.left,cls.source_end=producer.source(cls.source_report,cls.left_record)
        cls.network=prior.constructor.CompensatedBdfNetwork(200,prior.constructor.model_parameters(1,'finite_transit'))
        cls.graph=producer.read(prior.graph_source.OUTPUT)['graph'];cls.startup=producer.read(prior.startup_source.OUTPUT)
        cls.templates=[producer.load_artifact(row['storage'],'template',row['interval_index']) for row in cls.manifest['templates']]
        cls.items=[producer.unpack_template(cls.network,cls.startup,t,row['storage']) for t,row in zip(cls.templates,cls.manifest['templates'])]
        branches=[]
        for v in cls.manifest['variants']:
            branches.append(v|dict(blocks=[producer.load_artifact(b['storage'],'block',b['block_index'],v['width'])['block'] for b in v['blocks']],
                records=[producer.load_artifact(rec['storage'],'interval',rec['interval_index'],v['width'])['record'] for rec in v['records']]))
        cls.report=cls.manifest|dict(variants=branches)
    @classmethod
    def tearDownClass(cls):sys.set_int_max_str_digits(cls.limit)

    def test_union_full_polynomials_and_piecewise_laws(self):
        c=[[(F(1),F(1))]]
        t=dict(ref='synthetic',kind='exponential',factor=F(1),coefficients=[(0,0,F(1))],power=(F(0),F(0)))
        _,terms,ledger=producer.shared.merge_terms([(c,[t]),(c,[t|dict(power=(F(0),F(4),F(-4)))])])
        self.assertEqual(terms[0]['power'],(F(0),F(2))) # Bernstein includes interior, endpoints both zero.
        self.assertEqual(ledger['reference_ranges'][1][0]['upper'],'2')
        def contained(power):
            bounds=poly.bernstein(power,F(0),F(1));lo,span=terms[0]['power']
            return min(bounds)>=lo and max(bounds)<=lo+span
        self.assertTrue(contained(t['power']));self.assertFalse(contained((F(3),)))
        self.assertFalse(contained((F(0),F(12),F(-12))))
        with self.assertRaises(ValueError):producer.shared.merge_terms([])
        with self.assertRaises(ValueError):producer.shared.merge_terms([(c,[t]),(c,[t|dict(factor=F(2))])])
        with self.assertRaises(ValueError):producer.shared.merge_terms([(c,[t]),([[(F(0),F(0))]],[t])])
        p=self.network.network.latch.device.parameters;dep=p.depletion_be
        cap=dict(ref='cap',kind='capacitance',power=(F(-1,10),F(4,5)),coefficients=[(0,0,F(1))],
            depletion=dep,transit=p.transit_forward_s,saturation=p.saturation_a,emission=p.emission_be_v)
        _,merged,_=producer.shared.merge_terms([(c,[cap])]);rho=F(1,10**6)
        cover=law.real.tube.inflated_cover(c,merged,{'cap':F(1)},F(0),F(1),rho)
        a,b=map(F,cover['coefficient_domains'][0]['coefficient_interval'])
        knee=F(dep.forward_fraction*dep.potential_v)
        for v in (F(-1,10)-rho,knee-F(1,10**8),knee,knee+F(1,10**8),F(7,10)+rho):
            _,interval=law.real.tube.iv.junction_bounds(dep,cap['transit'],cap['saturation'],cap['emission'],v)
            self.assertLessEqual(a,interval[0]);self.assertLessEqual(interval[1],b)
        with self.assertRaises(ValueError):producer.shared.merge_terms([(c,[cap]),(c,[cap|dict(depletion=replace(dep,forward_fraction=.3))])])
        with self.assertRaises(ValueError):law.real.tube.inflated_cover(c,[t|dict(power=(F(46),))],{'synthetic':F(1)},F(0),F(1),rho)

    def test_new_templates_rhs_junctions_queries_and_physical_clocks(self):
        for item,template,row in zip(self.items,self.templates,self.manifest['templates']):
            self.assertEqual(item['source_storage'],row['storage']);self.assertEqual(template['source_sha256'],self.manifest['producer_source_sha256'])
            self.assertEqual(item['prepared_sha256'],law.digest(producer.serial(item['prepared'])))
            k=item['interval_index'];a,b=[prior.startup_source.unpack(self.network,self.startup['rows'][j]['history']) for j in (k-1,k)]
            affine=law.real.prepare(self.network,a,b);h=F(b.time_s)-F(a.time_s)
            self.assertEqual(law.action.rhs(self.network,self.graph,affine,F(0),F(1)),template['candidate_rhs'])
            with localcontext() as ctx:
                ctx.prec=100
                matrix,_=prior.descriptor(self.network,self.graph,[law.real.event.decimal(poly.evaluate(v,F(1,2))) for v in affine['x']],100)
            self.assertEqual(producer.np.linalg.inv(producer.np.array(matrix,dtype=float)).tolist(),template['candidate_inverse_binary'])
            self.assertEqual(item['prepared']['h'],h)
            for u in (F(0),F(1)):
                for field in ('x','q','y_linear'):
                    self.assertEqual([poly.evaluate(p,u) for p in affine[field]],[poly.evaluate(p,u) for p in item['prepared'][field]])
            for j,(rhs,forcing) in enumerate(zip(item['rhs'],item['forcing'])):
                lo,hi=F(j,8),F(j+1,8)
                self.assertEqual(law.action.rhs(self.network,self.graph,item['prepared'],lo,hi),rhs)
                residual,replayed=law.real.tube.forcing(self.network,self.graph,item['prepared'],lo,hi)
                self.assertEqual(replayed,forcing);self.assertEqual(producer.serial(residual),template['residual_bounds'][j]);self.assertEqual(F(rhs['duration_s']),h/8)
                self.assertEqual(len(rhs['polynomials']),119);self.assertEqual(max(len(p)-1 for p in rhs['polynomials']),12)
                for z in (F(0),F(1,2),F(1)):
                    query=law.real.tube.query(self.network,self.graph,item['prepared'],lo+(hi-lo)*z,100)
                    remainder=rhs['subcells'][min(int(z*8),7)]['rhs_remainder_upper']
                    for i,truth in enumerate(query['kcl_a']+query['constraint_v']):
                        value=poly.evaluate(tuple(map(F,rhs['polynomials'][i])),z);error=F(remainder[i])
                        display=F(1,10**90)*(1+abs(value))
                        self.assertLessEqual(value-error-display,F(truth));self.assertLessEqual(F(truth),value+error+display)
            for query in template['queries']:
                self.assertEqual(law.real.tube.query(self.network,self.graph,item['prepared'],F(query['u']),100),query['decimal100'])
                self.assertLessEqual(abs(F(query['decimal100']['dynamic_conservation_error_a'])),F(1,10**90))
            self.assertTrue(template['conditional_reference_only']);self.assertFalse(template['actual_dae_error_bound'])
        self.assertEqual([i['interval_index'] for i in self.items],list(range(16,24)))

    def test_all_shared_covers_inverses_rates_and_new_actions(self):
        r=self.report;scales=list(map(F,r['descriptor_scales']));gains=law.real.tube.gains(self.network,self.graph);total=dict(preconditioners=0,inverses=0,rate_queries=0,actions=0)
        for variant in r['variants']:
            counts=dict(preconditioners=len(variant['blocks']),inverses=0,rate_queries=0,actions=0);inverses={}
            for block in variant['blocks']:
                items=[i for i in self.items if i['interval_index'] in block['support_indices']]
                self.assertEqual(block['reference_sha256'],[i['prepared_sha256'] for i in items])
                self.assertEqual(block['representative_index'],items[(len(items)-1)//2]['interval_index']);self.assertEqual(block['representative_u'],'1/2')
                with localcontext() as ctx:
                    ctx.prec=100
                    representative=items[(len(items)-1)//2]['prepared']
                    matrix,_=prior.descriptor(self.network,self.graph,[law.real.event.decimal(poly.evaluate(v,F(1,2))) for v in representative['x']],100)
                binary=producer.np.array(matrix,dtype=float)
                self.assertEqual(law.digest(binary.tolist()),block['descriptor_binary_sha256'])
                self.assertEqual(producer.np.linalg.inv(binary).tolist(),block['candidate_inverse_binary'])
                compiled=[law.real.tube.weighted.compile_terms(self.network,self.graph,i['prepared'],block['candidate_inverse_binary'],scales) for i in items]
                c,t,ledger=producer.shared.merge_terms(compiled);self.assertEqual(ledger,block['ledger'])
                cover=law.real.tube.inflated_cover(c,t,gains,F(0),F(1),F(block['radius_v']));self.assertEqual(cover,block['cover'])
                self.assertEqual(cover['strict_contraction'],block['inverse_certified'])
                if not block['inverse_certified']:continue
                inverse,proof=law.real.tube.cells.structured_inverse(block['candidate_inverse_binary'],scales,cover,F(cover['contraction_upper']))
                self.assertEqual(proof,block['inverse_certificate']);self.assertEqual(law.digest(law.real.tube.cells.packed_matrix(inverse)),block['inverse_intervals_sha256'])
                _,rates=law.cell_metrics(inverse,r['weights'],items[0]['forcing'][0],self.metric,r['congruence'],r['balance'])
                self.assertEqual(rates,block['rate_certificate']);inverses[block['block_index']]=inverse
                counts['inverses']+=1;counts['rate_queries']+=sum(len(v['probes']) for v in rates.values())
            for record in variant['records']:
                item=self.items[record['interval_index']-16]
                for trial in record['trials']:
                    if not trial['cells']:continue
                    block=variant['blocks'][trial['block_index']];inverse=inverses[trial['block_index']]
                    for cell,forcing,rhs in zip(trial['cells'],item['forcing'],item['rhs']):
                        self.assertEqual(cell['block_index'],block['block_index']);self.assertEqual(cell['rhs_sha256'],law.digest(rhs));self.assertEqual(cell['forcing_inputs'],forcing)
                        original=law.fine.fine_metrics(inverse,r['weights'],forcing,self.metric,block['rate_certificate']['balanced']['mu_metric_upper_per_s'])
                        self.assertEqual(original,cell['original_metrics'])
                        action=law.action.budgets(block['candidate_inverse_binary'],scales,block['cover'],rhs,r['weights'],self.metric)
                        self.assertEqual(action,cell['action']);counts['actions']+=len(action['subcells'])
                        self.assertEqual(law.action.refine_metrics(original,action,True),cell['metrics'])
                    self.assertEqual(len(trial['cells']),8)
            self.assertEqual(counts,variant['cost'])
            for key in total:total[key]+=counts[key]
        self.assertEqual(total,r['total_cost'])

    def test_transport_strict_closures_first_gap_and_variant_order(self):
        r=self.report;selected=None
        for n,variant in enumerate(r['variants']):
            self.assertIsNone(selected);self.assertEqual(variant['width'],producer.WIDTHS[n])
            previous=self.source;left=self.left;end=F(r['initial_certified_end_s']);accepted=0;gap=False
            for offset,record in enumerate(variant['records']):
                self.assertFalse(gap);self.assertEqual(record['interval_index'],16+offset);item=self.items[offset]
                self.assertEqual(record['incoming_certified_result_sha256'],law.digest(previous));self.assertEqual(record['incoming_block_error_upper_v'],law.transfer(previous))
                self.assertEqual(record['incoming_metric_sha256'],r['metric_sha256']);self.assertEqual(record['prepared_sha256'],item['prepared_sha256'])
                self.assertEqual(record['interface'],law.real.continuity(self.network,left,item['prepared'],end,F(item['start_s'])))
                for trial in record['trials']:
                    if trial['cells']:
                        self.assertEqual(law.blocks.close(trial['cells'],law.transfer(previous),F(trial['radius_v']),F(previous['peak_node_error_upper_v'])),trial['result'])
                    else:self.assertFalse(trial['result']['accepted'])
                self.assertEqual(law.select(record['trials']),record['selected_trial_index'])
                with self.assertRaises(ValueError):law.admit(previous,end,record|dict(start_s='0'))
                with self.assertRaises(ValueError):law.admit(previous,end,record|dict(incoming_certified_result_sha256='wrong'))
                admitted=law.admit(previous,end,record)
                if admitted is None:gap=True
                else:previous,end=admitted;left=item['prepared'];accepted+=1
            self.assertEqual(previous,variant['final_certified_result']);self.assertEqual(str(end),variant['continuous_actual_error_certified_duration_s'])
            self.assertEqual(accepted,variant['accepted_additional_intervals']);self.assertEqual(16+accepted,variant['accepted_intervals_total'])
            self.assertEqual(variant['first_gap_index'],variant['records'][-1]['interval_index'] if gap else None)
            self.assertEqual(variant['complete_new_bank'],accepted==8);self.assertEqual(variant['stop_reason'],'first_gap' if gap else 'declared_limit')
            if accepted==8:selected=n
        self.assertEqual(max(range(len(r['variants'])),key=lambda n:r['variants'][n]['accepted_additional_intervals']),r['selected_variant_index'])

    def test_changed_duration_rejected_before_forcing_application(self):
        item=self.items[0];bad=item|dict(rhs=[item['rhs'][0]|dict(duration_s='1'),*item['rhs'][1:]])
        dummy=dict(support_indices=[16],block_index=0,rate_certificate={'synthetic':dict(probes=[])})
        with patch.object(producer.shared,'make_block',return_value=(dummy,[[]])):
            with self.assertRaisesRegex(ValueError,'physical duration'):
                producer.measure_variant(self.network,self.graph,[bad],self.source,self.metric,self.left,F(self.report['initial_certified_end_s']),self.report['weights'],self.report['descriptor_scales'],self.report['congruence'],self.report['balance'],8)
        with self.assertRaises(ValueError):producer.measure_variant(None,None,[],None,None,None,None,None,None,None,None,3)

    def test_manifest_storage_lineage_counters_and_scope(self):
        r=self.manifest;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(gzip.decompress(raw),producer.canonical(r));self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(producer.canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['width_order'],list(producer.WIDTHS));self.assertEqual(r['radius_order'],list(map(str,producer.RADII)))
        self.assertEqual(r['source_certified_result_sha256'],law.digest(self.source));self.assertEqual(F(r['initial_certified_end_s']),self.source_end)
        self.assertEqual(r['source_accepted_intervals'],16);self.assertEqual(r['new_reference_preconditioners'],8)
        self.assertEqual(r['metric_sha256'],self.source_report['metric_sha256']);self.assertEqual(r['fixed_metric'],self.source_report['fixed_metric'])
        selected=r['variants'][r['selected_variant_index']]
        for field in ('accepted_additional_intervals','accepted_intervals_total','continuous_actual_error_certified_duration_s','final_certified_result','first_gap_index','stop_reason'):
            self.assertEqual(r[field],selected[field])
        self.assertEqual(r['new_nonlinear_solves'],0);self.assertEqual(r['new_metric_systems'],0);self.assertEqual(r['integer_text_limit_during'],0)
        for key in ('source_bound_reset','clock_translation','junction_norm_changed','prior_reports_modified','original_integrator_modified','numerical_gates_changed','independent_remainders_cancelled','partial_artifacts_admitted','global_1mv_gate_closed','full_path_coverage','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[key])
        for key in ('conditional_templates_do_not_admit_time','complete_artifact_manifest','real_history_only','actual_individual_memory_transport'):self.assertTrue(r[key])
        with self.assertRaises(ValueError):producer.generate()
        with self.assertRaises(ValueError):producer.save(r)

    def test_artifacts_and_source_reject_changed_destinations_bytes_or_identity(self):
        row=self.manifest['templates'][0];storage=row['storage'];template=self.templates[0]
        with self.assertRaises(ValueError):producer.load_artifact(storage|dict(path='../elsewhere.json.gz'),'template',16)
        with self.assertRaises(ValueError):producer.load_artifact(storage|dict(compressed_sha256='wrong'),'template',16)
        with self.assertRaises(ValueError):producer.load_artifact(storage|dict(canonical_json_sha256='wrong'),'template',16)
        with patch.object(Path,'read_bytes',return_value=b'changed'):
            with self.assertRaises(ValueError):producer.load_artifact(storage,'template',16)
        with self.assertRaises(ValueError):producer.unpack_template(self.network,self.startup,template|dict(prepared_sha256='wrong'),storage)
        with self.assertRaises(ValueError):producer.unpack_template(self.network,self.startup,template|dict(start_s='0'),storage)
        for args in (('template',15),('template',24),('template',True),('block',0,True),('block',1,8),('interval',16,3)):
            with self.assertRaises(ValueError):producer.artifact_path(*args)
        with self.assertRaises(ValueError):producer.source(self.source_report|dict(selected_variant_index=1),self.left_record)
        with self.assertRaises(ValueError):producer.source(self.source_report,self.left_record|dict(end_s='0'))
        for v in self.manifest['variants']:
            for kind,rows in (('block',v['blocks']),('interval',v['records'])):
                for row in rows:
                    k=row['block_index'] if kind=='block' else row['interval_index']
                    data=producer.load_artifact(row['storage'],kind,k,v['width'])
                    for name,h in data['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
                    if kind=='interval':
                        rec=data['record'];self.assertEqual(rec['selected_trial_index'],row['selected_trial_index'])
                        self.assertEqual(rec['start_s'],row['start_s']);self.assertEqual(rec['end_s'],row['end_s'])
                        self.assertEqual(rec['prepared_sha256'],row['prepared_sha256'])
                        self.assertEqual(row['trials'],[dict(radius_v=t['radius_v'],block_index=t['block_index'],result={k:value for k,value in t['result'].items() if k!='propagation'}) for t in rec['trials']])

if __name__=='__main__':unittest.main()
