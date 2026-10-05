from pathlib import Path
from fractions import Fraction as F
from copy import deepcopy
import gzip,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_curved_reference as producer
from loudness_latch_bdf_doubling_survey import canonical
law=producer.law;curve=producer.curve;poly=curve.poly;iv=law.action.iv
sha=lambda raw:hashlib.sha256(raw).hexdigest()


class CurvedReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
        cls.report=producer.read(producer.OUTPUT);cls.source=producer.read(producer.signed.OUTPUT)
        cls.history=producer.read(producer.signed.prior.prior.OUTPUT)
        cls.previous,cls.metric,cls.left=producer.support(cls.source,cls.history)
        cls.network=producer.constructor.CompensatedBdfNetwork(200,producer.constructor.model_parameters(1,'finite_transit'))
        cls.graph=producer.read(producer.graph_source.OUTPUT)['graph'];startup=producer.read(producer.startup_source.OUTPUT)
        a,b=[producer.startup_source.unpack(cls.network,startup['rows'][k]['history']) for k in (6,7)]
        cls.affine=law.real.prepare(cls.network,a,b)
        cls.curved,cls.bubble=curve.candidate(cls.network,cls.affine,cls.report['candidate_inverse_binary'],cls.report['candidate_rhs']['polynomials'])
        cls.references=[cls.affine,cls.curved]
    @classmethod
    def tearDownClass(cls):sys.set_int_max_str_digits(cls.limit)

    def test_exact_quadratic_solution_physical_time_sign_and_rc_counterexample(self):
        source=self.affine|dict(x=[(F(0),F(0))]*94,y_linear=[(F(0),F(0))]*21,h=F(2))
        source=curve.rebuild(self.network,source,source['x'],source['y_linear'])
        inverse=[[int(i==j) for j in range(119)] for i in range(119)]
        inverse[78][114]=-1;inverse[22][114]=3
        rhs=[['0']]*119;rhs[114]=['-1','2']
        result,b=curve.candidate(self.network,source,inverse,rhs)
        self.assertEqual(b['amplitude_v_s'],'1');self.assertEqual(b['bubble_v'],['0','2','-2'])
        for u in (F(0),F(1,4),F(1,2),F(3,4),F(1)):
            p=2*u*(1-u);yp=poly.evaluate(poly.differentiate(result['y_linear'][20]),u)/2
            self.assertEqual(yp,1-2*u);self.assertEqual(poly.evaluate(result['y_linear'][20],u),p)
            self.assertEqual(poly.evaluate(result['x'][78],u),p);self.assertEqual(poly.evaluate(result['x'][22],u),-3*p)
        # A changed RC memory must pay tau*y'_t even though the bubble vanishes at both endpoints.
        y=list(result['y_linear']);y[17]=(F(0),F(2),-F(2));rc=curve.rebuild(self.network,source,result['x'],y)
        port=law.real.event.ports(self.network)[17]
        for u in (F(0),F(1,4),F(1)):
            voltage=-port['fixed']+sum((a*poly.evaluate(rc['x'][i],u) for i,a in port['a'].items()),F(0))
            expected=poly.evaluate(y[17],u)-voltage+port['tau']*poly.evaluate(poly.differentiate(y[17]),u)/2
            self.assertEqual(poly.evaluate(rc['equations'][17],u),expected)
        self.assertNotEqual(poly.evaluate(rc['equations'][17],0),poly.evaluate(result['equations'][17],0))
        with self.assertRaises(ValueError):curve.candidate(self.network,source,inverse[:118],rhs)
        with self.assertRaises(ValueError):curve.candidate(self.network,source|dict(h=0),inverse,rhs)

    def test_reference_interfaces_charge_constraints_and_source_guards(self):
        self.assertEqual(self.bubble,self.report['bubble'])
        ports=law.real.event.ports(self.network)
        for prepared,record in zip(self.references,self.report['records']):
            self.assertEqual(producer.serial(prepared),record['prepared'])
            self.assertEqual(law.real.continuity(self.network,self.left,prepared,F(self.source['end_s']),F(prepared['start_s'])),record['interface'])
            self.assertEqual(record['incoming_block_error_upper_v'],law.transfer(self.previous))
            for k,(yp,branch,port) in enumerate(zip(prepared['y_linear'],self.network.network.branches,ports)):
                self.assertEqual(prepared['q'][k],poly.scale(yp,F(branch[3])))
                for u in (F(0),F(1,3),F(1)):
                    voltage=-port['fixed']+sum((a*poly.evaluate(prepared['x'][i],u) for i,a in port['a'].items()),F(0))
                    self.assertEqual(poly.evaluate(prepared['equations'][k],u),poly.evaluate(yp,u)-voltage+port['tau']*poly.evaluate(poly.differentiate(yp),u)/prepared['h'])
            for junction,port in zip(prepared['junctions'],ports[21:]):
                v=port['fixed'],
                for i,a in port['a'].items():v=poly.add(v,poly.scale(prepared['x'][i],a))
                self.assertEqual(junction,(v,port['dep'],port['transit'],port['emission']))
        for u in (F(0),F(1)):
            for field in ('x','q','y_linear'):
                self.assertEqual([poly.evaluate(p,u) for p in self.affine[field]],[poly.evaluate(p,u) for p in self.curved[field]])
            self.assertEqual([poly.evaluate(j[0],u) for j in self.affine['junctions']],[poly.evaluate(j[0],u) for j in self.curved['junctions']])
        bad=deepcopy(self.source);bad['final_certified_result']['actual_outgoing_memory_restored']=False
        with self.assertRaises(ValueError):producer.support(bad,self.history)
        with self.assertRaises(ValueError):producer.support(self.source|dict(accepted_intervals_total=8),self.history)

    def test_full_residual_replay_degree_and_decimal_queries_enclosed(self):
        candidate=law.action.rhs(self.network,self.graph,self.affine,F(0),F(1))
        self.assertEqual(candidate,self.report['candidate_rhs']);degrees=[]
        for prepared,record in zip(self.references,self.report['records']):
            for base,rhs in zip(record['base_cells'],record['rhs']):
                a,b=F(base['left']),F(base['right']);actual=law.action.rhs(self.network,self.graph,prepared,a,b)
                self.assertEqual(actual,rhs);self.assertEqual(len(rhs['polynomials']),119)
                degrees.append(max(len(p)-1 for p in rhs['polynomials']))
                # Each queried current lies inside the full polynomial + independent constitutive remainder.
                for z in (F(0),F(1,2),F(1)):
                    query=law.real.tube.query(self.network,self.graph,prepared,a+(b-a)*z,100)
                    sub=rhs['subcells'][min(int(z*8),7)]
                    for i,truth in enumerate(query['kcl_a']+query['constraint_v']):
                        value=poly.evaluate(tuple(map(F,rhs['polynomials'][i])),z);error=F(sub['rhs_remainder_upper'][i])
                        # Decimal100 observer rounding is separate from the rational certificate.
                        display=F(1,10**90)*(1+abs(value))
                        self.assertLessEqual(value-error-display,F(truth));self.assertLessEqual(F(truth),value+error+display)
            for row in record['queries']:
                self.assertEqual(law.real.tube.query(self.network,self.graph,prepared,F(row['u']),100),row['decimal100'])
                self.assertLessEqual(abs(F(row['decimal100']['dynamic_conservation_error_a'])),F(1,10**90))
        self.assertEqual(max(degrees),12)
        self.assertNotEqual(self.report['records'][0]['rhs'],self.report['records'][1]['rhs'])

    def test_all_new_tubes_inverses_rates_actions_and_metrics_replay(self):
        r=self.report;counts=[0,0,0];scales=list(map(F,r['descriptor_scales']));gains=law.real.tube.gains(self.network,self.graph)
        for prepared,record in zip(self.references,r['records']):
            for base,rhs in zip(record['base_cells'],record['rhs']):
                residual,forcing=law.real.tube.forcing(self.network,self.graph,prepared,F(base['left']),F(base['right']))
                self.assertEqual(producer.serial(residual),base['residual_bounds']);self.assertEqual(forcing,base['forcing_inputs'])
                constant,terms=law.real.tube.weighted.compile_terms(self.network,self.graph,prepared,base['inverse_binary'],scales)
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

    def test_all_closures_and_ordered_certified_transport(self):
        r=self.report;selected=None
        for i,record in enumerate(r['records']):
            for j,t in enumerate(record['trials']):
                if t['cells']:
                    self.assertEqual(law.blocks.close(t['cells'],law.transfer(self.previous),F(t['radius_v']),F(self.previous['peak_node_error_upper_v'])),t['result'])
                if selected is None and t['result']['accepted']:selected=[i,j]
            self.assertEqual(law.select(record['trials']),record['selected_trial_index'])
        self.assertEqual(selected,r['selected_variant_trial'])
        if selected is None:
            self.assertEqual(r['final_certified_result'],self.previous);self.assertEqual(r['first_gap_index'],7)
            self.assertEqual(r['accepted_intervals_total'],7);self.assertEqual(r['continuous_actual_error_certified_duration_s'],self.source['end_s'])
        else:
            final,end=law.admit(self.previous,F(self.source['end_s']),r['records'][selected[0]])
            self.assertEqual(final,r['final_certified_result']);self.assertEqual(str(end),r['continuous_actual_error_certified_duration_s'])
            self.assertEqual(len(law.transfer(final)),22);self.assertEqual(r['accepted_intervals_total'],8);self.assertIsNone(r['first_gap_index'])

    def test_storage_inputs_counts_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256']);self.assertEqual(len(raw),storage['bytes'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertEqual(r['new_preconditioners'],17);self.assertEqual(r['variant_order'],list(producer.VARIANTS));self.assertEqual(r['radius_order'],list(map(str,producer.RADII)))
        self.assertEqual(r['metric_sha256'],self.source['metric_sha256']);self.assertEqual(r['source_certified_result_sha256'],law.digest(self.previous));self.assertEqual(r['integer_text_limit_during'],0)
        self.assertEqual(r['new_nonlinear_solves'],0);self.assertEqual(r['new_metric_systems'],0)
        for key in ('junction_norm_changed','clock_translation','dc_anchor_reset','original_integrator_modified','prior_reports_modified','numerical_gates_changed','small_currents_dropped','circuit_regularized','independent_remainders_cancelled','full_path_coverage','global_1mv_gate_closed','physical_trajectory_bound','audio_admitted','deadline_admitted'):self.assertFalse(r[key])
        self.assertTrue(r['reference_changed']);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)

if __name__=='__main__':unittest.main()
