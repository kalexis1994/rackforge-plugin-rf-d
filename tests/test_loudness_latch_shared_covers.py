from pathlib import Path
from fractions import Fraction as F
from dataclasses import replace
from decimal import localcontext
from unittest.mock import patch
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_shared_covers as producer
prior=producer.prior;law=producer.law;poly=law.real.poly
sha=lambda raw:hashlib.sha256(raw).hexdigest()


class SharedCovers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
        cls.report=producer.read(producer.OUTPUT);cls.control=producer.read(prior.OUTPUT);cls.eighth=producer.read(prior.ancestor.OUTPUT)
        cls.source,cls.metric,cls.left=prior.source(cls.eighth)
        cls.network=prior.constructor.CompensatedBdfNetwork(200,prior.constructor.model_parameters(1,'finite_transit'))
        cls.graph=producer.read(prior.graph_source.OUTPUT)['graph'];cls.startup=producer.read(prior.startup_source.OUTPUT)
        cls.items=producer.references(cls.network,cls.startup,cls.control)
    @classmethod
    def tearDownClass(cls):sys.set_int_max_str_digits(cls.limit)

    def test_union_full_polynomials_and_piecewise_laws(self):
        c=[[(F(1),F(1))]]
        t=dict(ref='synthetic',kind='exponential',factor=F(1),coefficients=[(0,0,F(1))],power=(F(0),F(0)))
        _,terms,ledger=producer.merge_terms([(c,[t]),(c,[t|dict(power=(F(0),F(4),F(-4)))])])
        self.assertEqual(terms[0]['power'],(F(0),F(2))) # Bernstein includes interior, endpoints both zero.
        self.assertEqual(ledger['reference_ranges'][1][0]['upper'],'2')
        def contained(power):
            bounds=poly.bernstein(power,F(0),F(1));lo,span=terms[0]['power']
            return min(bounds)>=lo and max(bounds)<=lo+span
        self.assertTrue(contained(t['power']));self.assertFalse(contained((F(3),)))
        self.assertFalse(contained((F(0),F(12),F(-12))))
        with self.assertRaises(ValueError):producer.merge_terms([])
        with self.assertRaises(ValueError):producer.merge_terms([(c,[t]),(c,[t|dict(factor=F(2))])])
        with self.assertRaises(ValueError):producer.merge_terms([(c,[t]),([[(F(0),F(0))]],[t])])
        p=self.network.network.latch.device.parameters;dep=p.depletion_be
        cap=dict(ref='cap',kind='capacitance',power=(F(-1,10),F(4,5)),coefficients=[(0,0,F(1))],
            depletion=dep,transit=p.transit_forward_s,saturation=p.saturation_a,emission=p.emission_be_v)
        _,merged,_=producer.merge_terms([(c,[cap])]);rho=F(1,10**6)
        cover=law.real.tube.inflated_cover(c,merged,{'cap':F(1)},F(0),F(1),rho)
        a,b=map(F,cover['coefficient_domains'][0]['coefficient_interval'])
        knee=F(dep.forward_fraction*dep.potential_v)
        for v in (F(-1,10)-rho,knee-F(1,10**8),knee,knee+F(1,10**8),F(7,10)+rho):
            _,interval=law.real.tube.iv.junction_bounds(dep,cap['transit'],cap['saturation'],cap['emission'],v)
            self.assertLessEqual(a,interval[0]);self.assertLessEqual(interval[1],b)
        with self.assertRaises(ValueError):producer.merge_terms([(c,[cap]),(c,[cap|dict(depletion=replace(dep,forward_fraction=.3))])])
        with self.assertRaises(ValueError):law.real.tube.inflated_cover(c,[t|dict(power=(F(46),))],{'synthetic':F(1)},F(0),F(1),rho)

    def test_immutable_references_rhs_and_physical_clocks(self):
        for item,row in zip(self.items,self.control['records']):
            self.assertEqual(item['source_storage'],row['storage'])
            self.assertEqual(item['prepared_sha256'],law.digest(producer.serial(item['prepared'])))
            h=F(item['end_s'])-F(item['start_s']);self.assertEqual(item['prepared']['h'],h)
            for k,(rhs,forcing) in enumerate(zip(item['rhs'],item['forcing'])):
                a,b=F(k,8),F(k+1,8)
                self.assertEqual(law.action.rhs(self.network,self.graph,item['prepared'],a,b),rhs)
                _,replayed=law.real.tube.forcing(self.network,self.graph,item['prepared'],a,b)
                self.assertEqual(replayed,forcing);self.assertEqual(F(rhs['duration_s']),h/8)
        self.assertEqual([i['interval_index'] for i in self.items],list(range(8,16)))
        with self.assertRaises(ValueError):producer.references(self.network,self.startup,self.control|dict(accepted_intervals_total=15))

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
                c,t,ledger=producer.merge_terms(compiled);self.assertEqual(ledger,block['ledger'])
                cover=law.real.tube.inflated_cover(c,t,gains,F(0),F(1),F(block['radius_v']));self.assertEqual(cover,block['cover'])
                self.assertEqual(cover['strict_contraction'],block['inverse_certified'])
                if not block['inverse_certified']:continue
                inverse,proof=law.real.tube.cells.structured_inverse(block['candidate_inverse_binary'],scales,cover,F(cover['contraction_upper']))
                self.assertEqual(proof,block['inverse_certificate']);self.assertEqual(law.digest(law.real.tube.cells.packed_matrix(inverse)),block['inverse_intervals_sha256'])
                _,rates=law.cell_metrics(inverse,r['weights'],items[0]['forcing'][0],self.metric,r['congruence'],r['balance'])
                self.assertEqual(rates,block['rate_certificate']);inverses[block['block_index']]=inverse
                counts['inverses']+=1;counts['rate_queries']+=sum(len(v['probes']) for v in rates.values())
            for record in variant['records']:
                item=self.items[record['interval_index']-8]
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
                self.assertFalse(gap);self.assertEqual(record['interval_index'],8+offset);item=self.items[offset]
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
            self.assertEqual(accepted,variant['accepted_additional_intervals']);self.assertEqual(8+accepted,variant['accepted_intervals_total'])
            self.assertEqual(variant['first_gap_index'],variant['records'][-1]['interval_index'] if gap else None)
            self.assertEqual(variant['complete_known_bank'],accepted==8);self.assertEqual(variant['stop_reason'],'first_gap' if gap else 'declared_limit')
            if accepted==8:selected=n
        self.assertEqual(selected,r['selected_variant_index'])

    def test_changed_duration_rejected_before_forcing_application(self):
        item=self.items[0];bad=item|dict(rhs=[item['rhs'][0]|dict(duration_s='1'),*item['rhs'][1:]])
        dummy=dict(support_indices=[8],block_index=0,rate_certificate={'synthetic':dict(probes=[])})
        with patch.object(producer,'make_block',return_value=(dummy,[[]])):
            with self.assertRaisesRegex(ValueError,'physical duration'):
                producer.measure_variant(self.network,self.graph,[bad],self.source,self.metric,self.left,F(self.report['initial_certified_end_s']),self.report['weights'],self.report['descriptor_scales'],self.report['congruence'],self.report['balance'],8)
        with self.assertRaises(ValueError):producer.measure_variant(None,None,[],None,None,None,None,None,None,None,None,3)

    def test_storage_frozen_lineage_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(gzip.decompress(raw),prior.canonical(r));self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(prior.canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['width_order'],list(producer.WIDTHS));self.assertEqual(r['radius_order'],list(map(str,producer.RADII)))
        self.assertEqual(r['source_certified_result_sha256'],law.digest(self.source));self.assertNotEqual(r['source_certified_result_sha256'],law.digest(self.control['final_certified_result']))
        self.assertEqual(r['control_manifest_sha256'],sha(prior.OUTPUT.read_bytes()));self.assertEqual(r['metric_sha256'],self.control['metric_sha256']);self.assertEqual(r['fixed_metric'],self.control['fixed_metric'])
        self.assertEqual(r['control_accepted_intervals'],16);self.assertEqual(r['control_end_s'],self.control['continuous_actual_error_certified_duration_s'])
        self.assertEqual(r['control_cost'],dict(preconditioners=72,inverses=64,rate_queries=6336,actions=512))
        self.assertEqual(r['new_nonlinear_solves'],0);self.assertEqual(r['new_metric_systems'],0);self.assertEqual(r['integer_text_limit_during'],0)
        for key in ('prior_reports_modified','reference_changed','rhs_changed','junction_norm_changed','clock_translation','independent_remainders_cancelled','numerical_gates_changed','original_integrator_modified','time_coverage_extended','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[key])
        for key in ('full_reference_ranges','whole_future_potential_tube','actual_individual_memory_transport','conditional_block_covers_include_unreached_supports'):self.assertTrue(r[key])
        with self.assertRaises(ValueError):producer.generate()
        with self.assertRaises(ValueError):producer.save(r)

if __name__=='__main__':unittest.main()
