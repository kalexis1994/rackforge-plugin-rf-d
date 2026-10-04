from fractions import Fraction as F
from itertools import product
from pathlib import Path
import copy,gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_coverage_bridge as law
import loudness_latch_bdf_static_precision_coverage_bridge as producer
from loudness_latch_spectral_junction import ldlt
from loudness_latch_bdf_doubling_survey import canonical
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(b):return hashlib.sha256(b).hexdigest()
def diag(values):return [[F(v) if i==j else F(0) for j in range(4)] for i,v in enumerate(values)]
def quadratic(g,x):return sum((F(x[i])*F(g[i][j])*F(x[j]) for i in range(4) for j in range(4)),F(0))

class CoverageBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_exact_union_complement_contact_overlap_and_domain(self):
        spans=[(F(1,4),F(1,2)),(F(1,3),F(3,4)),(F(3,4),F(7,8)),(F(1,4),F(1,2))]
        c=law.coverage(spans,0,1);self.assertEqual(c['union_s'],[['1/4','7/8']]);self.assertEqual(c['gaps_s'],[['0','1/4'],['7/8','1']])
        self.assertEqual(F(c['covered_duration_s']),F(5,8));self.assertEqual(F(c['missing_duration_s']),F(3,8));self.assertGreater(F(c['raw_duration_s']),F(c['covered_duration_s']))
        self.assertEqual(c,law.coverage(list(reversed(spans)),0,1))
        complement=law.coverage(c['gaps_s'],0,1);self.assertEqual(complement['gaps_s'],c['union_s'])
        self.assertTrue(law.coverage([(0,1)],0,1)['complete']);self.assertEqual(law.coverage([],0,1)['gaps_s'],[['0','1']])
        self.assertNotEqual(F(.003),F(3,1000)) # Archived binary endpoint is lifted, not replaced by a decimal literal.
        for values,start,end in (([],1,0),([(0,0)],0,1),([(-1,1)],0,1),([(0,2)],0,1),([(1,0)],0,1)):
            with self.assertRaises(ValueError):law.coverage(values,start,end)

    def test_complete_history_lineage_and_tamper_guards(self):
        initial=dict(time_s=0.,current=dict(q=0),previous=None,key_v=0.,previous_key_v=None,previous_dt_s=None)
        old=initial;rows=[]
        for i in range(3):
            new=dict(time_s=old['time_s']+.125,current=dict(q=i+1),previous=old['current'],key_v=10.,previous_key_v=old['key_v'],previous_dt_s=.125)
            rows.append(dict(history=new,previous_history_sha256=law.digest(old),diagnostics=dict(actual_dt_s=.125)));old=new
        result=law.lineage(initial,rows);self.assertEqual(result['interval_count'],3);self.assertEqual(result['domain_s'],['0','3/8']);self.assertFalse(result['entry_error_bound_proven'])
        for change in ('sha','previous','dt','key','clock'):
            altered=copy.deepcopy(rows)
            if change=='sha':altered[1]['previous_history_sha256']='bad'
            elif change=='previous':altered[1]['history']['previous']['q']=99
            elif change=='dt':altered[1]['history']['previous_dt_s']=.25
            elif change=='key':altered[1]['history']['previous_key_v']=0.
            else:altered[1]['history']['time_s']+=.01
            with self.assertRaises(ValueError):law.lineage(initial,altered)
        with self.assertRaises(ValueError):law.lineage(initial,[])

    def test_known_norm_ratios_identity_full_block_gain_and_guards(self):
        p=diag([1,2,3,4]);candidate=dict(accepted=True,metric=law.metric.pack(p),anchor_normalization_upper='1')
        source=law.gram(candidate,['1']*25);dest=law.gram(candidate|dict(metric=law.metric.pack([[4*v for v in row] for row in p])),['1']*25)
        identity=law.bridge(source,source);self.assertTrue(identity['identity']);self.assertEqual(identity['junction_gain_upper'],'1');self.assertEqual(identity['probes'],[])
        forward=law.bridge(source,dest);back=law.bridge(dest,source)
        self.assertGreaterEqual(F(forward['junction_gain_upper']),2);self.assertLess(F(forward['junction_gain_upper'])-2,F(1,10**6))
        self.assertGreaterEqual(F(back['junction_gain_upper']),F(1,2));self.assertEqual(back['full_block_gain_upper'],'1')
        for signs in product((-1,1),repeat=4):
            x=[F(s*(i+1),7) for i,s in enumerate(signs)]
            self.assertLessEqual(quadratic(dest['gram'],x),F(forward['junction_gain_upper'])**2*quadratic(source['gram'],x))
        for bad,weights in ((candidate|dict(accepted=False),['1']*25),(candidate,['1']*24),(candidate,['2']+['1']*24),(candidate|dict(anchor_normalization_upper='0'),['1']*25)):
            with self.assertRaises(ValueError):law.gram(bad,weights)
        for bad in (dict(gram=[]),dict(gram=law.metric.pack(diag([-1,1,1,1]))),dict(gram=[['1','1','0','0'],['0','1','0','0'],['0','0','1','0'],['0','0','0','1']])):
            with self.assertRaises(ValueError):law.bridge(source,bad)

    def test_all_dc_refined_lineages_supports_and_coverage_reconstruct(self):
        r=self.report;fixed=read(producer.FIXED);fine=read(producer.FINE);long=read(producer.LONG);weighted=read(producer.WEIGHTED)
        self.assertEqual(law.lineage(fixed['initial'],fixed['rows']),r['dc_lineage']);self.assertEqual(r['dc_lineage']['interval_count'],6486)
        refs={(w['name'],l['reference']['subdivisions']):l['reference'] for w in fine['windows'] for l in w['levels']}
        total=0;bytime={F(v['history']['time_s']):v['history'] for v in fixed['rows']}
        for record in r['refined_lineages']:
            ref=refs[record['window'],record['subdivisions']];proof=law.lineage(ref['initial'],ref['steps']);self.assertEqual(proof,record['lineage']);total+=proof['interval_count']
            base=next(w for w in long['windows'] if w['name']==record['window']);ci=record['dc_anchor_row_index'];self.assertEqual(ci,base['compensated_clock_anchor_index'])
            self.assertEqual(canonical(ref['initial']),canonical(fixed['rows'][ci]['history']));self.assertEqual(record['dc_anchor_sha256'],law.digest(ref['initial']))
        self.assertEqual(total,1536)
        for c in r['cases']:
            source=weighted['cases'][c['source_case_index']];ref=refs[c['window'],c['subdivisions']];fi=ref['samples'][31]['fine_step_index']
            steps=[ref['steps'][j] for j in range(fi,fi-4,-1)];times=[F(v['history']['time_s']) for v in steps]
            self.assertEqual(c['support_sha256'],[law.digest(v['history']) for v in steps]);self.assertEqual(c['support_sha256'],source['support_sha256'])
            self.assertEqual(c['support_times_s'],list(map(str,times)));self.assertEqual(c['selected_interval_s'],list(map(str,[times[1],times[0]])));self.assertEqual(F(c['duration_s']),times[0]-times[1])
            # The report's endpoint match field means complete history identity, not equality of clocks.
            self.assertIn(times[0],bytime);self.assertEqual(c['selected_endpoint_matches_full_clock'],canonical(steps[0]['history'])==canonical(bytime[times[0]]));self.assertFalse(c['selected_endpoint_matches_full_clock'])
            self.assertEqual(c['quadratic_metric_accepted'],c['window']!='reset');self.assertFalse(c['actual_error_coverage'])
            if c['window']=='reset':self.assertEqual(c['frozen_rhp_counts'],[1]*8);self.assertIsNotNone(c['reset_strategy'])
            else:self.assertEqual(c['frozen_rhp_counts'],[0]*8)
        start,end=map(F,r['dc_lineage']['domain_s'])
        for inv in [*r['inventories'],dict(subdivisions=None,ideal_inverse_selected=r['combined_ideal_inverse_selected'],accepted_metric_selected=r['combined_accepted_metric_selected'])]:
            cases=[c for c in r['cases'] if inv['subdivisions'] is None or c['subdivisions']==inv['subdivisions']]
            for kind,selected in (('ideal_inverse_selected',cases),('accepted_metric_selected',[c for c in cases if c['quadratic_metric_accepted']])):
                self.assertEqual(inv[kind],law.coverage([c['selected_interval_s'] for c in selected],start,end));self.assertFalse(inv[kind]['complete'])
        self.assertEqual(len(r['combined_ideal_inverse_selected']['union_s']),4);self.assertEqual(len(r['combined_accepted_metric_selected']['union_s']),3)
        self.assertEqual(r['combined_ideal_inverse_selected']['covered_duration_s'],r['inventories'][0]['ideal_inverse_selected']['covered_duration_s'])

    def test_all_36_bridges_and_990_exact_queries_replay(self):
        r=self.report;source=read(producer.METRIC);norms=r['norms'];queries=0
        self.assertEqual(len(norms),6);self.assertEqual(len(r['bridges']),36);self.assertEqual({(b['source_norm_index'],b['destination_norm_index']) for b in r['bridges']},set(product(range(6),repeat=2)))
        for n in norms:
            c=source['cases'][n['case_index']];self.assertEqual(n['prepared'],law.gram(c['metric_candidate'],c['weights']))
            g=n['prepared']['gram'];inverse=n['prepared']['inverse_gram']
            for i in range(4):
                for j in range(4):self.assertEqual(sum(F(g[i][k])*F(inverse[k][j]) for k in range(4)),F(i==j))
        for b in r['bridges']:
            a=norms[b['source_norm_index']]['prepared'];d=norms[b['destination_norm_index']]['prepared'];cert=b['certificate'];self.assertEqual(cert,law.bridge(a,d))
            self.assertFalse(cert['actual_interface_verified']);self.assertFalse(cert['missing_region_propagation_proven'])
            if cert['identity']:self.assertEqual(b['source_norm_index'],b['destination_norm_index']);continue
            g=[[F(v) for v in row] for row in a['gram']];h=[[F(v) for v in row] for row in d['gram']];lo,hi=F(cert['seed_lower_squared']),F(cert['seed_upper_squared'])
            for index,probe in enumerate(cert['probes']):
                alpha=hi if not index else (lo+hi)/2;self.assertEqual(alpha,F(probe['alpha_squared']));proof=ldlt([[alpha*g[i][j]-h[i][j] for j in range(4)] for i in range(4)])
                self.assertEqual(proof['positive_definite'],probe['positive_definite']);self.assertEqual(proof['failed_at'],probe['failed_at']);self.assertEqual(law.digest(proof['pivots']),probe['pivot_sha256'])
                if index:
                    if proof['positive_definite']:hi=alpha
                    else:lo=alpha
            self.assertEqual(hi,F(cert['squared_upper']));self.assertEqual(lo,F(cert['auxiliary_lower_squared']));self.assertEqual(cert['final_upper_ldlt'],ldlt([[hi*g[i][j]-h[i][j] for j in range(4)] for i in range(4)]))
            root_lo,root_hi=map(F,cert['square_root_bracket']);self.assertLessEqual(root_lo**2,hi);self.assertGreaterEqual(root_hi**2,hi);self.assertEqual(root_hi,F(cert['junction_gain_upper']));self.assertEqual(max(F(1),root_hi),F(cert['full_block_gain_upper']))
            for x in ([F(1),F(-2),F(3,7),F(-5,11)],[F(0),F(1),F(0),F(0)]):self.assertLessEqual(quadratic(h,x),root_hi**2*quadratic(g,x))
            queries+=len(cert['probes'])
        self.assertEqual(queries,990);self.assertEqual(queries,r['exact_bridge_ldlt_queries'])

    def test_storage_source_identities_destinations_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();s=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-coverage-bridge/v1');self.assertEqual(len(r['cases']),8);self.assertEqual(r['continuous_actual_error_certified_duration_s'],'0')
        self.assertEqual(len(raw),s['bytes']);self.assertEqual(sha(raw),s['compressed_sha256']);self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),s['canonical_json_sha256'])
        for p,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        self.assertTrue(r['numerical_dc_lineage_verified'])
        for flag in ('metric_candidates_changed','weights_changed','norms_changed','initial_error_known','nonlinear_remainder_bound','actual_dae_error_bound',
                     'full_path_coverage','temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):self.assertFalse(r[flag],flag)
        self.assertEqual(r['new_circuit_inverse_systems'],0);self.assertEqual(r['new_nonlinear_circuit_solves'],0)

if __name__=='__main__':unittest.main()
