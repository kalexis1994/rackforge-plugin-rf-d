from fractions import Fraction as F
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_anchor_budget as law
import loudness_latch_bdf_static_precision_anchor_budget as producer
from loudness_latch_bdf_doubling_survey import canonical
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(b):return hashlib.sha256(b).hexdigest()
def row(index,a,f):return dict(cell_index=0,node_row_index=index,anchor_gain=str(a),forced_upper_v=str(f))

class AnchorBudget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_known_affine_solutions_pairing_ties_and_degenerate_cases(self):
        rows=[row(0,1,F(3,4)),row(1,10,0)];paired=law.capacity(rows,1);separated=law.separated_capacity(rows,1)
        self.assertEqual(F(paired['anchor_upper_v']),F(1,10));self.assertEqual(F(separated['anchor_upper_v']),F(1,40))
        self.assertEqual(paired['binding_constraints'],[dict(cell_index=0,node_row_index=1)])
        tied=law.capacity([row(0,2,0),row(1,1,F(1,2)),row(2,0,1)],1)
        self.assertEqual(F(tied['anchor_upper_v']),F(1,2));self.assertEqual(len(tied['binding_constraints']),2)
        self.assertEqual(law.capacity([row(0,0,1)],1)['status'],'unbounded')
        zero=law.capacity([row(0,7,1)],1);self.assertEqual(zero['status'],'finite');self.assertEqual(F(zero['anchor_upper_v']),0)
        bad=law.capacity([row(0,0,F(11,10)),row(1,1,0)],1)
        self.assertEqual(bad['status'],'infeasible');self.assertIsNone(bad['anchor_upper_v']);self.assertEqual(bad['zero_anchor_violations'],[dict(cell_index=0,node_row_index=0)])
        previous=F(paired['anchor_upper_v'])
        for reserve in (F(1,10),F(1,5),F(1,4)):
            c=law.capacity(rows,1,reserve);a=F(c['anchor_upper_v']);self.assertLessEqual(a,previous);previous=a
            self.assertTrue(all(F(r['anchor_gain'])*a+F(r['forced_upper_v'])+reserve<=1 for r in rows))
        self.assertEqual(law.capacity(rows,1,F(1,3))['status'],'infeasible')

    def test_domain_and_identity_guards(self):
        valid=[row(0,1,0)]
        for threshold,reserve in ((0,0),(-1,0),(1,-1),(1,2)):
            with self.assertRaises(ValueError):law.capacity(valid,threshold,reserve)
        for rows in ([],[row(0,-1,0)],[row(0,1,-1)],valid+valid,
                     [valid[0]|dict(cell_index=-1)],[valid[0]|dict(node_row_index=True)],[valid[0]|dict(node_row_index=F(0))]):
            with self.assertRaises(ValueError):law.capacity(rows,1)
        with self.assertRaises(ValueError):law.separated_capacity([],1)

    def test_trace_conversion_independent_rational_products_and_guards(self):
        t=dict(left='0',right='1',peak_anchor=['2','3'],peak_forced_v=['1/10','1/5'],peak_node_anchor='6',peak_node_forced_v='2/5')
        m=dict(nodal_block_gains=[['1','0'],['0','2']],nodal_direct_v=['1/4','0'])
        rows=law.constraints([t],[m]);self.assertEqual(rows,[row(0,2,F(7,20)),row(1,6,F(2,5))])
        for trace,maps in (([],[]),([t],[]),([t|dict(left='1/2')],[m]),([t|dict(right='1/2')],[m]),
                           ([t|dict(peak_node_anchor='7')],[m]),([t|dict(peak_node_forced_v='1')],[m]),
                           ([t],[m|dict(nodal_direct_v=['-1','0'])]),([t],[m|dict(nodal_block_gains=[['1'],['0']])])):
            with self.assertRaises(ValueError):law.constraints(trace,maps)

    def test_all_4512_affine_pairs_conditional_capacities_and_binding_witnesses(self):
        source=read(producer.prior.OUTPUT);directed=read(producer.prior.prior.OUTPUT);metric=read(producer.prior.prior.prior.OUTPUT);total=0
        for c in self.report['cases']:
            old=source['cases'][c['source_balanced_case_index']]
            for key in ('support_sha256','weights','metric_candidate_sha256','metric_accepted'):self.assertEqual(c[key],old[key])
            if not c['metric_accepted']:
                self.assertEqual(c['affine_constraints'],[]);self.assertEqual(c['budgets'],[]);self.assertIsNone(c['propagation_sha256']);continue
            fixed=metric['cases'][directed['cases'][old['source_directed_case_index']]['source_metric_case_index']]
            maps=[v['metrics'] for v in fixed['cells']];rows=law.constraints(old['propagation']['trace'],maps)
            self.assertEqual(rows,c['affine_constraints']);self.assertEqual(len(rows),752);total+=len(rows)
            self.assertEqual(c['propagation_sha256'],producer.prior.law.box.digest(old['propagation']))
            # Independent dot products establish the paired coefficients from the frozen maps.
            for r in rows:
                t=old['propagation']['trace'][r['cell_index']];m=maps[r['cell_index']];n=r['node_row_index']
                a=sum(F(g)*F(v) for g,v in zip(m['nodal_block_gains'][n],t['peak_anchor']))
                f=F(m['nodal_direct_v'][n])+sum(F(g)*F(v) for g,v in zip(m['nodal_block_gains'][n],t['peak_forced_v']))
                self.assertEqual(a,F(r['anchor_gain']));self.assertEqual(f,F(r['forced_upper_v']))
            self.assertEqual(max(F(r['anchor_gain']) for r in rows),F(old['propagation']['peak_node_anchor_gain_upper']))
            self.assertEqual(max(F(r['forced_upper_v']) for r in rows),F(old['propagation']['peak_zero_anchor_node_upper_v']))
            prior=None
            for budget,reserve in zip(c['budgets'],producer.RESERVES):
                self.assertEqual(F(budget['reserve_v']),reserve);self.assertEqual(budget['paired'],law.capacity(rows,producer.THRESHOLD,reserve));self.assertEqual(budget['separated'],law.separated_capacity(rows,producer.THRESHOLD,reserve))
                result=budget['paired'];limit=F(result['anchor_upper_v']);self.assertTrue(budget['paired_nonworse']);self.assertGreaterEqual(limit,F(budget['separated']['anchor_upper_v']))
                constraints={(r['cell_index'],r['node_row_index']):r for r in rows};bindings=result['binding_constraints'];self.assertTrue(bindings)
                for r in rows:self.assertLessEqual(F(r['anchor_gain'])*limit+F(r['forced_upper_v'])+reserve,producer.THRESHOLD)
                for binding in bindings:
                    r=constraints[(binding['cell_index'],binding['node_row_index'])];a,f=F(r['anchor_gain']),F(r['forced_upper_v'])
                    self.assertGreater(a,0);self.assertEqual(a*limit+f+reserve,producer.THRESHOLD)
                    self.assertGreater(a*(limit+F(1,10**20))+f+reserve,producer.THRESHOLD)
                if prior is not None:self.assertLessEqual(limit,prior)
                prior=limit
        self.assertEqual(total,4512);self.assertEqual(total,self.report['affine_constraint_count'])

    def test_storage_sources_destinations_and_hypothetical_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();storage=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-anchor-budget/v1');self.assertEqual(len(r['cases']),8)
        self.assertEqual(r['nodal_gate_v'],'1/1000');self.assertEqual(r['hypothetical_reserves_v'],['0','1/4000','1/2000'])
        self.assertEqual(len(raw),storage['bytes']);self.assertEqual(sha(raw),storage['compressed_sha256']);self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),storage['canonical_json_sha256'])
        for name,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        self.assertTrue(r['conditional_sufficient_target_only']);self.assertTrue(r['exact_for_archived_affine_majorants']);self.assertEqual(r['initial_anchor_reference'],'common weighted infinity')
        for flag in ('nonlinear_reserve_proven','metric_changed','norm_changed','anchor_changed','weights_changed','block_partition_changed',
                     'initial_error_known','nonlinear_remainder_bound','actual_dae_error_bound','full_path_coverage','temporal_error_bound_admitted',
                     'physical_trajectory_bound','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):self.assertFalse(r[flag],flag)
        for flag in ('new_circuit_inverse_systems','new_nonlinear_circuit_solves','new_rate_certificates'):self.assertEqual(r[flag],0)

if __name__=='__main__':unittest.main()
