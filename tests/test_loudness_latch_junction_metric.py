from fractions import Fraction as F
from itertools import product
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_junction_metric as law
import loudness_latch_bdf_static_precision_junction_metric as producer
from loudness_latch_cell_propagation import structured_inverse
from loudness_latch_spectral_junction import spectral_bound,ldlt
from loudness_latch_bdf_doubling_survey import canonical

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def diagonal(v):return [[F(x) if i==j else F(0) for j in range(4)] for i,x in enumerate(v)]
def point(a):return [[(F(v),F(v)) for v in row] for row in a]
def quadratic(p,v):return sum((F(v[i])*p[i][j]*v[j] for i in range(len(v)) for j in range(len(v))),F(0))
def nonnormal():
    a=diagonal([-1,-1,-2,-3]);a[0][1]=F(4);return a

class JunctionMetric(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_candidate_equation_quantization_inverse_and_guards(self):
        a=nonnormal();m=law.candidate([point(a)]);self.assertTrue(m['accepted'])
        c=[[F(v) for v in row] for row in m['normalized_center']];raw=[[F(v) for v in row] for row in m['raw_solution']]
        for i in range(4):
            for j in range(4):self.assertEqual(sum((c[k][i]*raw[k][j]+raw[i][k]*c[k][j] for k in range(4)),F(0)),-F(i==j))
        trace=sum(raw[i][i] for i in range(4));p=[[F(v) for v in row] for row in m['metric']];pi=[[F(v) for v in row] for row in m['inverse_metric']]
        self.assertEqual(p,[[law.nearest(4*v/trace) for v in row] for row in raw]);self.assertTrue(ldlt(p)['positive_definite'])
        for i in range(4):
            for j in range(4):self.assertEqual(sum((p[i][k]*pi[k][j] for k in range(4)),F(0)),F(i==j))
        self.assertEqual(law.nearest(F(1,2*(1<<40))),0);self.assertEqual(law.nearest(F(3,2*(1<<40))),F(2,1<<40))
        self.assertFalse(law.candidate([point(diagonal([0,-1,-2,-3]))])['accepted'])
        self.assertFalse(law.candidate([point(diagonal([1,-1,-2,-3]))])['accepted'])
        with self.assertRaises(ValueError):law.solve([[0]],[1])
        with self.assertRaises(ValueError):law.candidate([])
        with self.assertRaises(ValueError):law.quadratic_upper([[F(1)]],[])
        with self.assertRaises(ValueError):law.quadratic_upper([[F(-1)]],[(F(1),F(1))])

    def test_generalized_rate_full_interval_certificate_at_vertices(self):
        a=nonnormal();m=law.candidate([point(a)]);r=law.rate(m,point(a))
        self.assertLess(F(r['mu_metric_upper_per_s']),0)
        symmetric=point([[(a[i][j]+a[j][i])/2 for j in range(4)] for i in range(4)])
        self.assertGreater(F(spectral_bound(symmetric)['lambda_lower_per_s']),0)
        b=point(a);positions=[(i,j) for i in range(2) for j in range(2)]
        for i,j in positions:b[i][j]=(a[i][j]-F(1,100),a[i][j]+F(1,100))
        m=law.candidate([b]);r=law.rate(m,b);self.assertLess(F(r['mu_metric_upper_per_s']),0)
        p=[[F(v) for v in row] for row in m['metric']];alpha=F(r['mu_metric_upper_per_s'])
        for ends in product((0,1),repeat=4):
            v=[row[:] for row in a]
            for (i,j),end in zip(positions,ends):v[i][j]=b[i][j][end]
            s=[[(sum((p[i][k]*v[k][j]+v[k][i]*p[k][j] for k in range(4)),F(0)))/2 for j in range(4)] for i in range(4)]
            self.assertTrue(ldlt([[alpha*p[i][j]-s[i][j] for j in range(4)] for i in range(4)])['positive_definite'])
        self.assertFalse(r['lower_is_actual_log_norm_bound']);self.assertTrue(r['metric_constant_within_interval'])

    def test_signed_quadratic_boxes_dual_and_anchor_at_all_vertices(self):
        p=diagonal([2,2,3,4]);p[0][1]=p[1][0]=F(-1);pi=law.invert(p)
        v=[(F(-2),F(1)),(F(-1),F(3)),(F(-1),F(2)),(F(0),F(1))]
        bound=law.quadratic_upper(p,v)
        for ends in product((0,1),repeat=4):
            x=[v[i][ends[i]] for i in range(4)];self.assertGreaterEqual(bound**2,quadratic(p,x))
            y=[F(i-2) for i in range(4)]
            self.assertLessEqual(sum((u*w for u,w in zip(x,y)),F(0))**2,quadratic(p,x)*quadratic(pi,y))
        self.assertEqual(law.square((F(-2),F(1))),(F(0),F(4)))
        self.assertEqual(law.quadratic_upper(p,[(F(0),F(0))]*4),0)
        m=law.candidate([point(nonnormal())]);p=[[F(v) for v in row] for row in m['metric']];a=F(m['anchor_normalization_upper'])
        vertex_values=[quadratic(p,s) for s in product((-1,1),repeat=4)]
        self.assertEqual(list(map(F,m['anchor_vertex_quadratics'])),vertex_values);self.assertGreaterEqual(4*a*a,max(vertex_values))
        # Convexity gives the cube maximum at these vertices, preserving the infinity anchor.
        for x in ([F(1,2)]*4,[F(-1),F(1,3),F(0),F(1)]):self.assertLessEqual(quadratic(p,x),4*a*a)

    def test_complete_sending_receiving_forcing_and_nodal_conversions(self):
        inverse=[[(F(0),F(0)) for _ in range(119)] for _ in range(119)]
        def setv(i,j,v):inverse[i][j]=(F(v),F(v))
        setv(115,0,1);setv(116,0,2);setv(115,111,3);setv(116,111,4)
        setv(111,115,3);setv(111,116,4);setv(0,115,-3);setv(0,116,4)
        for i in range(115,119):setv(i,i,2)
        old=dict(comparison_per_s=[['0']*6 for _ in range(6)],block_forcing_l1_v=['0']*6,nodal_block_gains=[['0']*6 for _ in range(94)],nodal_direct_v=['0']*94)
        forcing=dict(nodal_l1_c=['3']+['0']*93,constraint_l1_v_s=['0']*25)
        metric=dict(metric=law.pack(diagonal([1]*4)),inverse_metric=law.pack(diagonal([1]*4)),anchor_normalization_upper='1',metric_norm='manufactured RMS')
        out=law.metrics(inverse,[F(1)]*25,forcing,old,metric,dict(mu_metric_upper_per_s='-2'))
        self.assertEqual(F(out['comparison_per_s'][1][5]),10);self.assertEqual(F(out['comparison_per_s'][5][1]),F(5,2))
        self.assertEqual(F(out['nodal_block_gains'][0][5]),10)
        self.assertEqual(F(out['block_forcing_l1_v'][5]),3*law.sqrt_bounds(F(5))[1]/2)
        self.assertEqual(out['nodal_direct_v'],old['nodal_direct_v']);self.assertEqual(F(out['comparison_per_s'][5][5]),-2)
        for i in range(5):
            self.assertEqual(out['block_forcing_l1_v'][i],old['block_forcing_l1_v'][i])
            for j in range(5):self.assertEqual(out['comparison_per_s'][i][j],old['comparison_per_s'][i][j])

    def test_switched_stable_family_rejected_without_alternate_metric(self):
        a=nonnormal();b=[row[:] for row in a];b[0][1]=0;b[1][0]=4
        for v in (a,b):self.assertTrue(law.box.analyze(point(v))['routh_certificate']['all_frozen_matrices_hurwitz'])
        m=law.candidate([point(a),point(b)]);self.assertFalse(m['accepted'])
        self.assertIn('not positive definite',m['rejection'])
        # Failure of this candidate alone is not a proof of nonexistence of all common metrics.
        self.assertEqual(m['numerical_metric_systems'],1);self.assertEqual(m['circuit_inverse_systems'],0)

    def test_all_candidates_cells_conversions_and_propagations_replay(self):
        modal=read(producer.prior.OUTPUT);weighted=read(producer.prior.weighted.OUTPUT);rms=read(producer.prior.prior.prior.OUTPUT);spectral=read(producer.prior.prior.OUTPUT)
        for c in self.report['cases']:
            old=modal['cases'][c['source_modal_case_index']];generators=[v['result']['generator_intervals_per_s'] for v in old['cells']]
            m=law.candidate(generators);self.assertEqual(m,c['metric_candidate']);self.assertEqual(c['support_sha256'],old['support_sha256']);self.assertEqual(c['weights'],old['weights'])
            self.assertTrue(c['binary_backward_gate_still_rejected'])
            baseline=spectral['cases'][old['source_spectral_case_index']]['propagation'];self.assertEqual(c['prior_spectral_propagation'],baseline)
            if not m['accepted']:
                self.assertEqual(c['cells'],[]);self.assertIsNone(c['propagation']);self.assertIsNone(c['peak_node_budget_nonincreasing']);continue
            source=weighted['cases'][old['source_weighted_case_index']];previous=rms['cases'][old['source_spectral_case_index']];q=max(F(v['contraction_upper']) for v in source['ideal_temporal_cover']);cells=[]
            self.assertEqual(len(c['cells']),8)
            for record in c['cells']:
                i=record['source_cell_index'];rate=law.rate(m,generators[i]);self.assertEqual(rate,record['rate_certificate']);self.assertTrue(rate['final_upper_ldlt']['positive_definite'])
                inverse,cert=structured_inverse(source['inverse_binary'],source['inverse_certificate']['column_scales'],source['ideal_temporal_cover'][i],q)
                self.assertEqual(cert,previous['cells'][i]['inverse_certificate']);forcing=previous['cells'][i]['forcing_inputs']
                metrics=law.metrics(inverse,source['weights'],forcing,previous['cells'][i]['metrics'],m,rate);self.assertEqual(metrics,record['metrics'])
                original=previous['cells'][i]['metrics']
                self.assertEqual(metrics['nodal_direct_v'],original['nodal_direct_v'])
                for row,oldrow in zip(metrics['nodal_block_gains'],original['nodal_block_gains']):self.assertEqual(row[:5],oldrow[:5])
                self.assertEqual(metrics['block_forcing_l1_v'][:5],original['block_forcing_l1_v'][:5])
                for row,oldrow in zip(metrics['comparison_per_s'][:5],original['comparison_per_s'][:5]):self.assertEqual(row[:5],oldrow[:5])
                cells.append(dict(forcing_inputs=forcing,metrics=metrics))
            self.assertEqual(law.propagate(cells),c['propagation'])
            self.assertEqual(c['all_internal_cells_contracting'],all(v['rate_certificate']['internal_time_varying_contraction_certified'] for v in c['cells']))
            self.assertEqual(c['peak_node_budget_nonincreasing'],F(c['propagation']['peak_zero_anchor_node_upper_v'])<=F(baseline['peak_zero_anchor_node_upper_v']))

    def test_storage_sources_destinations_and_tangent_only_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();s=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-junction-metric/v1');self.assertEqual(len(r['cases']),8)
        self.assertEqual(len(raw),s['bytes']);self.assertEqual(sha(raw),s['compressed_sha256']);self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),s['canonical_json_sha256'])
        for p,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        self.assertTrue(r['norm_changed']);self.assertTrue(r['metric_constant_within_each_interval']);self.assertEqual(r['initial_anchor_reference'],'common weighted infinity')
        self.assertEqual(r['metric_systems_attempted'],8);self.assertEqual(r['circuit_inverse_systems'],0);self.assertEqual(r['new_nonlinear_circuit_solves'],0)
        for key in ('metric_common_across_all_intervals','weights_changed','block_partition_changed','comparison_variants_intersected','complete_coupled_contraction_certified',
                    'nonlinear_remainder_bound','initial_error_known','actual_dae_error_bound','full_path_coverage','temporal_error_bound_admitted',
                    'physical_trajectory_bound','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):
            self.assertFalse(r[key],key)

if __name__=='__main__':unittest.main()
