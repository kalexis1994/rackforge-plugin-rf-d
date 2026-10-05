import copy,gzip,hashlib,json,sys,unittest
from dataclasses import FrozenInstanceError,replace
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.set_int_max_str_digits(0)
import loudness_latch_prepared_action_benchmark as bench
p=bench.prepared;ref=p.reference;canonical=bench.canonical


class PreparedAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=bench.source.read(bench.source.OUTPUT);cls.variant,cls.block=bench.bank(cls.manifest)
        cls.x=cls.block['candidate_inverse_binary'];cls.d=cls.manifest['descriptor_scales'];cls.cover=cls.block['cover']
        cls.state=p.prepare(cls.x,cls.d,cls.cover);cls.report=bench.source.read(bench.OUTPUT)
        cls.first=next(bench.cases(cls.manifest))

    def budget(self,rhs,state=None):
        return p.budgets(state or self.state,self.x,self.d,self.cover,rhs,self.manifest['weights'],self.manifest['fixed_metric'])

    def test_full_64_cell_certificates_replay_all_canonical_bytes(self):
        self.assertEqual(len(self.report['rows']),64)
        for row,(k,j,rs,ts,rhs,golden) in zip(self.report['rows'],bench.cases(self.manifest)):
            with self.subTest(interval=k,cell=j):
                result=self.budget(rhs);raw=canonical(result);archived=canonical(golden)
                self.assertEqual(raw,archived)
                self.assertEqual(row['interval_index'],k);self.assertEqual(row['cell_index'],j)
                self.assertEqual(row['record_storage'],rs);self.assertEqual(row['template_storage'],ts)
                self.assertEqual(row['rhs_sha256'],bench.source.law.digest(rhs))
                for label in ('reference','prepared','archived'):
                    self.assertEqual(row['certificate_sha256'][label],hashlib.sha256(raw).hexdigest())
                    self.assertEqual(row['canonical_bytes'][label],len(raw))
                self.assertTrue(row['complete_bytes_identical']);self.assertEqual(len(result['subcells']),8)
                for cert in result['subcells']:
                    self.assertEqual(len(cert['action_intervals']),119)
                    self.assertFalse(cert['independent_remainders_cancelled'])

    def test_timing_ledger_is_balanced_and_setup_is_not_hidden(self):
        r=self.report;self.assertEqual(r['aggregates'],bench.aggregates(r['rows'],r['setup']))
        self.assertEqual([row['order'] for row in r['rows']],['AB','BA']*32)
        self.assertEqual(r['rounds'],1);self.assertEqual(r['preparation_count'],1)
        for key in ('reference_budget_calls','prepared_budget_calls'):self.assertEqual(r[key],64)
        for key in ('reference_action_subcells','prepared_action_subcells'):self.assertEqual(r[key],512)
        self.assertGreater(r['setup']['wall_ns'],0)
        for row in r['rows']:
            for label in ('reference','prepared'):
                for clock in ('wall_ns','cpu_ns'):self.assertGreater(row['timings'][label][clock],0)
        self.assertEqual(r['prepared_input_sha256'],self.state.input_sha256)
        self.assertEqual(r['prepared_state_sha256'],self.state.state_sha256)

    def test_immutable_snapshot_keeps_signed_cancellation_and_independent_rest(self):
        x=[['1','-1'],['1/2','1/2']];d=['1','2']
        cover={'preconditioned_defect_intervals':[[['0','0'],['-1/8','1/8']],[['0','0'],['0','0']]],
            'contraction_upper':'1/8','strict_contraction':True,'radius_v':'1/1000000'}
        state=p.prepare(x,d,cover);polys=[['1','-2','1'],['1','-2','1']]
        compiled=ref.compile_polynomials(x,d,polys)
        self.assertEqual(p._compile(state,polys),compiled);self.assertEqual(compiled[0],(F(0),))
        actual=p.enclose(state,x,d,cover,compiled,['1/100','1/50'],F(1,8),F(7,8))
        expected=ref.enclose(x,d,cover,compiled,['1/100','1/50'],F(1,8),F(7,8))
        self.assertEqual(canonical(actual),canonical(expected))
        self.assertEqual(F(actual['preconditioned_remainder_upper'][0]),F(3,100))
        original_digest=state.state_sha256;x[0][0]='9';d[0]='3';cover['preconditioned_defect_intervals'][0][1][0]='-1/7'
        self.assertEqual(p.state_digest(state),original_digest);self.assertEqual(state.x[0][0],1)
        with self.assertRaises(FrozenInstanceError):state.n=3
        with self.assertRaises(TypeError):state.x[0][0]=F(9)

    def test_context_and_prepared_integrity_changes_are_rejected(self):
        for name in ('x','d','cover'):
            x=copy.deepcopy(self.x);d=copy.deepcopy(self.d);cover=copy.deepcopy(self.cover)
            if name=='x':x[0][0]+=1
            elif name=='d':d[0]='2'
            else:cover['radius_v']='1/2000000'
            with self.assertRaisesRegex(ValueError,'input identity'):p.verify(self.state,x,d,cover)
        cover=copy.deepcopy(self.cover);cover['new_domain_annotation']='different'
        with self.assertRaisesRegex(ValueError,'input identity'):p.verify(self.state,self.x,self.d,cover)
        for forged in (replace(self.state,n=118),replace(self.state,q=F(0)),replace(self.state,tail_factors=self.state.coarse_factors)):
            with self.assertRaisesRegex(ValueError,'state identity'):p.verify(forged,self.x,self.d,self.cover)
        with self.assertRaisesRegex(ValueError,'immutable preparation'):p.verify({},self.x,self.d,self.cover)

    def test_factory_rejects_invalid_dimensions_scales_intervals_and_contraction(self):
        cover={'preconditioned_defect_intervals':[[['0','0']]],'contraction_upper':'0','strict_contraction':True}
        bad=[([],[],cover),([['1','0']],['1'],cover),([['1']],['0'],cover),
            ([['1']],['1'],cover|{'contraction_upper':'1/8'}),
            ([['1']],['1'],cover|{'strict_contraction':False}),
            ([['1']],['1'],cover|{'preconditioned_defect_intervals':[[['1','0']]]}),
            ([['1']],['1'],cover|{'preconditioned_defect_intervals':[[['1','1']]],'contraction_upper':'1'})]
        for args in bad:
            with self.subTest(args=args),self.assertRaises(ValueError):p.prepare(*args)
        state=p.prepare([['1']],['1'],cover)
        for remainder,left,right in ((['-1'],0,1),([],0,1),(['0'],1,0),(['0'],-1,1),(['0'],0,2)):
            with self.assertRaises(ValueError):p.enclose(state,[['1']],['1'],cover,[(F(0),)],remainder,left,right)
        with self.assertRaisesRegex(ValueError,'119-equation'):p.budgets(state,[['1']],['1'],cover,{},[],{})

    def test_rhs_is_recomputed_and_invalid_supports_are_rejected(self):
        rhs=copy.deepcopy(self.first[4]);rhs['duration_s']=str(F(rhs['duration_s'])/2)
        result=self.budget(rhs);expected=ref.budgets(self.x,self.d,self.cover,rhs,self.manifest['weights'],self.manifest['fixed_metric'])
        self.assertEqual(canonical(result),canonical(expected));self.assertNotEqual(canonical(result),canonical(self.first[5]))
        rhs2=copy.deepcopy(self.first[4]);rhs2['polynomials'][0][0]=str(F(rhs2['polynomials'][0][0])+F(1,10**20))
        self.assertEqual(canonical(self.budget(rhs2)),canonical(ref.budgets(self.x,self.d,self.cover,rhs2,self.manifest['weights'],self.manifest['fixed_metric'])))
        for kind in ('duration','dimension','empty_poly','partition','remainder','count'):
            bad=copy.deepcopy(self.first[4])
            if kind=='duration':bad['duration_s']='0'
            elif kind=='dimension':bad['polynomials'].pop()
            elif kind=='empty_poly':bad['polynomials'][0]=[]
            elif kind=='partition':bad['subcells'][0]['left']='1/16'
            elif kind=='remainder':bad['subcells'][0]['rhs_remainder_upper'][0]='-1'
            else:bad['subcells'].pop()
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.budget(bad)

    def test_storage_frozen_sources_and_scope_have_no_new_time_admission(self):
        r=self.report;self.assertTrue(r['accepted']);self.assertTrue(r['inputs_unchanged']);self.assertEqual(r['failures'],[])
        self.assertEqual(r['mismatch_artifacts'],[]);self.assertEqual(r['integer_text_limit_during'],0)
        self.assertEqual(r['source_sha256_before'],r['source_sha256_after'])
        self.assertEqual(r['accepted_intervals_total'],24)
        self.assertEqual(r['continuous_actual_error_certified_duration_s'],self.manifest['continuous_actual_error_certified_duration_s'])
        for flag in ('time_coverage_extended','prior_reports_modified','numerical_gates_changed','reference_helper_changed',
            'global_1mv_gate_closed','audio_admitted','native_implementation_admitted','deadline_proven'):self.assertFalse(r[flag])
        for key in ('new_nonlinear_solves','new_inverse_enclosures','new_rate_ldlt_queries'):self.assertEqual(r[key],0)
        for name,sha in r['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha)
        summary=json.loads(bench.SUMMARY.read_text(encoding='utf-8'));storage=summary.pop('storage');self.assertEqual(summary,r)
        raw=bench.OUTPUT.read_bytes();self.assertEqual(len(raw),storage['bytes'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),storage['compressed_sha256'])
        self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(hashlib.sha256(canonical(r)).hexdigest(),storage['canonical_json_sha256'])


if __name__=='__main__':unittest.main()
