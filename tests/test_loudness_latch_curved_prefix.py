from pathlib import Path
from fractions import Fraction as F
from unittest.mock import patch
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_curved_prefix as producer
law=producer.law;curve=producer.curve;poly=curve.poly
sha=lambda raw:hashlib.sha256(raw).hexdigest()


class CurvedPrefix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
        cls.report=producer.read(producer.OUTPUT);cls.source_report=producer.read(producer.ancestor.OUTPUT)
        cls.previous,cls.metric,cls.left=producer.source(cls.source_report)
        cls.network=producer.constructor.CompensatedBdfNetwork(200,producer.constructor.model_parameters(1,'finite_transit'))
        cls.startup=producer.read(producer.startup_source.OUTPUT);cls.graph=producer.read(producer.graph_source.OUTPUT)['graph']
    @classmethod
    def tearDownClass(cls):sys.set_int_max_str_digits(cls.limit)

    def references(self,record):
        k=record['interval_index']
        a,b=[producer.startup_source.unpack(self.network,self.startup['rows'][j]['history']) for j in (k-1,k)]
        affine=law.real.prepare(self.network,a,b)
        curved,bubble=curve.candidate(self.network,affine,record['candidate_inverse_binary'],record['candidate_rhs']['polynomials'])
        self.assertEqual(bubble,record['bubble']);self.assertEqual(producer.serial(curved),record['prepared'])
        return affine,curved

    def test_exact_quadratic_with_variable_physical_supports_and_rc(self):
        inverse=[[int(i==j) for j in range(119)] for i in range(119)]
        inverse[78][114]=-1;inverse[22][114]=3
        ports=law.real.event.ports(self.network)
        for h in (F(1,8),F(3,16),F(5,32)):
            for sign in (-1,1):
                base=dict(start_s='0',end_s=str(h),h=h,x=[(F(0),F(0))]*94,y_linear=[(F(0),F(0))]*21)
                affine=curve.rebuild(self.network,base,base['x'],base['y_linear'])
                rhs=[['0']]*119;rhs[114]=list(map(str,[-sign,2*sign]))
                reference,bubble=curve.candidate(self.network,affine,inverse,rhs)
                self.assertEqual(F(bubble['amplitude_v_s']),sign)
                for u in (F(0),F(1,4),F(1,2),F(3,4),F(1)):
                    exact=sign*h*u*(1-u)
                    self.assertEqual(poly.evaluate(reference['y_linear'][20],u),exact)
                    self.assertEqual(poly.evaluate(reference['x'][78],u),exact)
                    self.assertEqual(poly.evaluate(poly.differentiate(reference['y_linear'][20]),u)/h,sign*(1-2*u))
                # An endpoint-preserving RC memory still has a nonzero endpoint derivative.
                y=list(reference['y_linear']);y[17]=tuple(map(F,bubble['bubble_v']))
                rc=curve.rebuild(self.network,base,reference['x'],y);port=ports[17]
                for u in (F(0),F(1,3),F(1)):
                    voltage=-port['fixed']+sum((a*poly.evaluate(rc['x'][i],u) for i,a in port['a'].items()),F(0))
                    expected=poly.evaluate(y[17],u)-voltage+port['tau']*poly.evaluate(poly.differentiate(y[17]),u)/h
                    self.assertEqual(poly.evaluate(rc['equations'][17],u),expected)
                self.assertNotEqual(poly.evaluate(rc['equations'][17],0),poly.evaluate(reference['equations'][17],0))

    def test_real_interfaces_constraints_junctions_and_lineage(self):
        previous=self.previous;left=self.left;end=F(self.source_report['continuous_actual_error_certified_duration_s'])
        ports=law.real.event.ports(self.network)
        for row in self.report['records']:
            record=producer.load_record(row);affine,reference=self.references(record)
            self.assertEqual(law.real.continuity(self.network,left,reference,end,F(record['start_s'])),record['interface'])
            self.assertEqual(record['incoming_certified_result_sha256'],law.digest(previous))
            self.assertEqual(record['incoming_block_error_upper_v'],law.transfer(previous))
            self.assertEqual(record['incoming_metric_sha256'],self.report['metric_sha256'])
            self.assertEqual(record['source_sha256'],self.report['producer_source_sha256'])
            for k,(y,branch,port) in enumerate(zip(reference['y_linear'],self.network.network.branches,ports)):
                self.assertEqual(reference['q'][k],poly.scale(y,F(branch[3])))
                for u in (F(0),F(1,3),F(1)):
                    voltage=-port['fixed']+sum((a*poly.evaluate(reference['x'][i],u) for i,a in port['a'].items()),F(0))
                    self.assertEqual(poly.evaluate(reference['equations'][k],u),poly.evaluate(y,u)-voltage+port['tau']*poly.evaluate(poly.differentiate(y),u)/reference['h'])
            for junction,port in zip(reference['junctions'],ports[21:]):
                voltage=(port['fixed'],)
                for i,a in port['a'].items():voltage=poly.add(voltage,poly.scale(reference['x'][i],a))
                self.assertEqual(junction,(voltage,port['dep'],port['transit'],port['emission']))
            for u in (F(0),F(1)):
                for field in ('x','q','y_linear'):
                    self.assertEqual([poly.evaluate(p,u) for p in affine[field]],[poly.evaluate(p,u) for p in reference[field]])
            admitted=law.admit(previous,end,record)
            if admitted is None:break
            previous,end=admitted;left=reference
        with self.assertRaises(ValueError):producer.source(self.source_report|dict(selected_variant_trial=[0,1]))
        with self.assertRaises(ValueError):producer.source(self.source_report|dict(continuous_actual_error_certified_duration_s='0'))
        with self.assertRaises(ValueError):producer.source(self.source_report|dict(final_certified_result=self.previous|dict(accepted=False)))

    def test_full_residual_and_decimal_observers_for_every_support(self):
        for row in self.report['records']:
            record=producer.load_record(row);affine,reference=self.references(record)
            self.assertEqual(law.action.rhs(self.network,self.graph,affine,F(0),F(1)),record['candidate_rhs'])
            for base,rhs in zip(record['base_cells'],record['rhs']):
                a,b=F(base['left']),F(base['right'])
                self.assertEqual(law.action.rhs(self.network,self.graph,reference,a,b),rhs)
                self.assertEqual(len(rhs['polynomials']),119);self.assertEqual(max(len(p)-1 for p in rhs['polynomials']),12)
                for z in (F(0),F(1,2),F(1)):
                    query=law.real.tube.query(self.network,self.graph,reference,a+(b-a)*z,100)
                    sub=rhs['subcells'][min(int(z*8),7)]
                    for i,truth in enumerate(query['kcl_a']+query['constraint_v']):
                        value=poly.evaluate(tuple(map(F,rhs['polynomials'][i])),z);error=F(sub['rhs_remainder_upper'][i])
                        display=F(1,10**90)*(1+abs(value))
                        self.assertLessEqual(value-error-display,F(truth));self.assertLessEqual(F(truth),value+error+display)
            for query in record['queries']:
                self.assertEqual(law.real.tube.query(self.network,self.graph,reference,F(query['u']),100),query['decimal100'])
                self.assertLessEqual(abs(F(query['decimal100']['dynamic_conservation_error_a'])),F(1,10**90))

    def test_all_future_tubes_inverses_rates_actions_and_metrics_replay(self):
        r=self.report;counts=[0,0,0];scales=list(map(F,r['descriptor_scales']));gains=law.real.tube.gains(self.network,self.graph)
        for row in r['records']:
            record=producer.load_record(row);_,reference=self.references(record)
            for base,rhs in zip(record['base_cells'],record['rhs']):
                residual,forcing=law.real.tube.forcing(self.network,self.graph,reference,F(base['left']),F(base['right']))
                self.assertEqual(producer.serial(residual),base['residual_bounds']);self.assertEqual(forcing,base['forcing_inputs'])
                constant,terms=law.real.tube.weighted.compile_terms(self.network,self.graph,reference,base['inverse_binary'],scales)
                for trial in record['trials']:
                    if not trial['covers']:continue
                    c=trial['covers'][base['index']]
                    cover=law.real.tube.inflated_cover(constant,terms,gains,F(base['left']),F(base['right']),F(trial['radius_v']))
                    self.assertEqual(cover,c['cover'])
                    if not c['inverse_certified']:continue
                    inverse,proof=law.real.tube.cells.structured_inverse(base['inverse_binary'],scales,cover,F(cover['contraction_upper']))
                    self.assertEqual(proof,c['inverse_certificate']);self.assertEqual(law.digest(law.real.tube.cells.packed_matrix(inverse)),c['inverse_intervals_sha256']);counts[0]+=1
                    if not trial['cells']:continue
                    cell=trial['cells'][base['index']]
                    metrics,rates=law.cell_metrics(inverse,r['weights'],forcing,self.metric,r['congruence'],r['balance'])
                    self.assertEqual(metrics,cell['original_metrics']);self.assertEqual(rates,cell['rate_certificate'])
                    counts[1]+=sum(len(v['probes']) for v in rates.values())
                    action=law.action.budgets(base['inverse_binary'],scales,cover,rhs,r['weights'],self.metric)
                    self.assertEqual(action,cell['action']);counts[2]+=len(action['subcells'])
                    self.assertEqual(law.action.refine_metrics(metrics,action,True),cell['metrics'])
        self.assertEqual(counts,[r['new_inverse_enclosures'],r['new_rate_ldlt_queries'],r['new_action_subcell_certificates']])

    def test_every_closure_transport_and_first_gap_or_limit(self):
        r=self.report;previous=self.previous;end=F(r['initial_certified_end_s']);accepted=0;gap=False
        for offset,row in enumerate(r['records']):
            self.assertFalse(gap);record=producer.load_record(row)
            self.assertEqual(record['interval_index'],producer.START_INDEX+offset)
            for trial in record['trials']:
                if trial['cells']:
                    self.assertEqual(law.blocks.close(trial['cells'],law.transfer(previous),F(trial['radius_v']),F(previous['peak_node_error_upper_v'])),trial['result'])
                else:
                    self.assertFalse(trial['result']['accepted'])
            self.assertEqual(law.select(record['trials']),row['selected_trial_index'])
            self.assertEqual(row['trials'],[dict(radius_v=t['radius_v'],inverse_certified_cells=sum(c['inverse_certified'] for c in t['covers']),result={k:v for k,v in t['result'].items() if k!='propagation'}) for t in record['trials']])
            with self.assertRaises(ValueError):law.admit(previous,end,record|dict(start_s='0'))
            with self.assertRaises(ValueError):law.admit(previous,end,record|dict(incoming_certified_result_sha256='wrong'))
            admitted=law.admit(previous,end,record)
            if admitted is None:gap=True
            else:previous,end=admitted;accepted+=1
        self.assertEqual(previous,r['final_certified_result']);self.assertEqual(str(end),r['continuous_actual_error_certified_duration_s'])
        self.assertEqual(accepted,r['accepted_additional_intervals']);self.assertEqual(8+accepted,r['accepted_intervals_total'])
        self.assertEqual(r['first_gap_index'],r['records'][-1]['interval_index'] if gap else None)
        self.assertEqual(r['stop_reason'],'first_gap' if gap else 'declared_limit')
        if not gap:self.assertEqual(len(r['records']),producer.ADDITIONAL_LIMIT)
        self.assertEqual(len(law.transfer(previous)),22)

    def test_storage_identity_rejects_changes_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(gzip.decompress(raw),producer.canonical(r));self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(producer.canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        row=r['records'][0];producer.load_record(row)
        with self.assertRaises(ValueError):producer.load_record(row|dict(storage=row['storage']|dict(path='../other.json.gz')))
        with self.assertRaises(ValueError):producer.load_record(row|dict(storage=row['storage']|dict(compressed_sha256='wrong')))
        with self.assertRaises(ValueError):producer.load_record(row|dict(storage=row['storage']|dict(canonical_json_sha256='wrong')))
        with self.assertRaises(ValueError):producer.load_record(row|dict(end_s='0'))
        with patch.object(Path,'read_bytes',return_value=b'altered'):
            with self.assertRaises(ValueError):producer.load_record(row)
        with self.assertRaises(ValueError):producer.generate()
        with self.assertRaises(ValueError):producer.save(r)
        for bad in (7,16,True,'8'):
            with self.assertRaises(ValueError):producer.interval_output(bad)
        self.assertEqual(r['new_preconditioners'],9*len(r['records']))
        self.assertEqual(r['radius_order'],list(map(str,producer.RADII)));self.assertEqual(r['additional_limit'],8)
        self.assertEqual(r['metric_sha256'],self.source_report['metric_sha256']);self.assertEqual(r['source_certified_result_sha256'],law.digest(self.previous))
        self.assertEqual(r['new_nonlinear_solves'],0);self.assertEqual(r['new_metric_systems'],0);self.assertEqual(r['integer_text_limit_during'],0)
        for key in ('junction_norm_changed','clock_translation','dc_anchor_reset','original_integrator_modified','prior_reports_modified','numerical_gates_changed','small_currents_dropped','circuit_regularized','independent_remainders_cancelled','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted','partial_supports_admitted'):self.assertFalse(r[key])
        self.assertTrue(r['complete_prefix_manifest']);self.assertTrue(r['endpoint_preserving_references'])

if __name__=='__main__':unittest.main()
