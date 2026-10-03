from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import gzip,json,hashlib,subprocess
from pathlib import Path
from types import SimpleNamespace as NS
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_weighted_descriptor as law
import loudness_latch_bdf_static_precision_weighted_descriptor as producer
import loudness_latch_bdf_static_precision_dense_charge as dense
from loudness_latch_continuous_descriptor import descriptor
from loudness_latch_bdf_doubling_survey import canonical


def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()


class WeightedDescriptor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_dyadic_weights_and_fixed_policy(self):
        for v in (F(1,3),F(7,8),F(3),F(2)**-1074,F(2)**1023,F(10)**-1000):
            w=law.dyadic_floor(v);self.assertLessEqual(w,v);self.assertLess(v,2*w)
            self.assertTrue(w.numerator&(w.numerator-1)==0)
            self.assertTrue(w.denominator&(w.denominator-1)==0)
        with self.assertRaisesRegex(ValueError,'positive'):law.dyadic_floor(0)
        for c in self.report['cases']:
            w=law.weights(c['descriptor_binary']);self.assertEqual(list(map(str,w)),c['weights'])
            self.assertEqual(w[:21],[F(1)]*21)
            for i in range(4):
                ratio=1/max(abs(F(v)) for v in c['descriptor_binary'][115+i][:94])
                self.assertLessEqual(w[21+i],ratio);self.assertLess(ratio,2*w[21+i])
        self.assertTrue(self.report['weights_constant_on_each_interval'])
        self.assertFalse(self.report['weights_fitted_to_response'])

    def test_similarity_log_norm_and_forcing_columns_independently(self):
        # B=[[-2,8],[1/2,-1]], W=diag(1,4): muinf(W B W^-1)=1.
        x=[[F(3),F(1),F(2)],[-F(1),F(2),-F(8)],[-F(2),-F(1,2),F(1)]]
        err=[[F(0)]*3 for _ in range(3)];w=[F(1),F(4)]
        rv=[F(1,1000)];dv=[F(3,1000),F(5,1000)]
        b=law.weighted_budget(x,err,1,w,rv,dv,rv,dv,F(1,10))
        self.assertEqual(F(b['logarithmic_norm_upper_per_s']),1)
        self.assertEqual(F(b['integrated_forcing_norm_upper_v']),8*rv[0]+2*dv[0]+8*dv[1])
        self.assertEqual(F(b['node_from_weighted_memory_gain_upper']),F(3,2))
        self.assertEqual(F(b['node_direct_forcing_upper_v']),3*rv[0]+dv[0]+2*dv[1])
        with localcontext() as ctx:
            ctx.prec=120
            gain=(D(1)/10).exp();upper=F(b['weighted_anchor_gain_upper'])
            self.assertGreaterEqual(D(upper.numerator)/D(upper.denominator),gain)
        self.assertEqual(F(b['node_from_unweighted_anchor_gain_upper']),F(3,2)*F(b['weighted_anchor_gain_upper'])*4)
        with self.assertRaisesRegex(ValueError,'positive'):law.weighted_budget(x,err,1,[0,4],rv,dv,rv,dv,1)
        with self.assertRaisesRegex(ValueError,'complete'):law.weighted_budget(x,err,1,w,[],dv,rv,dv,1)

    def test_varying_weight_counterexample_requires_connection_term(self):
        # y'=0, y=1, w(t)=1+t. Frozen B=0 cannot bound z(1)=2 by exp(0)=1.
        b=law.weighted_budget([[0,-1],[1,0]],[[F(0)]*2]*2,1,[1],[0],[0],[0],[0],1)
        self.assertEqual(F(b['weighted_anchor_gain_upper']),1)
        y=F(1);z_end=(1+F(1))*y
        self.assertGreater(z_end,F(b['weighted_anchor_gain_upper'])*y)
        for t in (F(0),F(1,2),F(1)):
            w=1+t;z=w*y;connection=1/w
            self.assertEqual(F(1),connection*z)
        self.assertTrue(self.report['weights_constant_on_each_interval'])

    def test_manufactured_ideal_temporal_descriptor(self):
        # One diode, resistor 2 ohm, capacitor 1/4 F: ideal g=.5+exp(v(t)).
        g=dict(node_count=1,fixed={'GND':0.},resistors=[dict(ref='R',left=0,right='GND',ohm=2.)],
               conductances=[],bjts=[],diodes=[dict(ref='D',anode=0,cathode='GND',is_a=1.,ideality=1.,vt=1.)])
        n=NS(network=NS(branches=[(0,None,0.,.25,0.)],latch=NS(terminals=[],device=NS(parameters=NS(polarity=1)))))
        p=dict(x=[(-F(1,100),F(1,50))],junctions=[]);x=[[F(0),-F(1)],[F(4),F(6)]]
        constant,terms=law.compile_terms(n,g,p,x,[1,1])
        _,cover=law.preconditioned_cover(constant,terms,F(0),F(1));self.assertTrue(cover['strict_contraction'])
        errors=law.temporal_inverse_errors(x,[1,1],[cover])
        with localcontext() as ctx:
            ctx.prec=160
            for t in (F(0),F(1,2),F(1)):
                v=-F(1,100)+t/50;conductance=D(1)/2+(D(v.numerator)/D(v.denominator)).exp()
                h=[[F(conductance),F(1,4)],[-F(1),F(0)]]
                actual=[[F(0),-F(1)],[F(4),4*F(conductance)]]
                for i in range(2):
                    for j in range(2):
                        e=F(i==j)-sum((x[i][k]*h[k][j] for k in range(2)),F(0))
                        lo,hi=map(F,cover['preconditioned_defect_intervals'][i][j]);self.assertLessEqual(lo,e);self.assertLessEqual(e,hi)
                        self.assertLessEqual(abs(actual[i][j]-x[i][j]),errors[i][j])
        p['x']=[(F(0),F(2))];const,terms=law.compile_terms(n,g,p,x,[1,1])
        _,bad=law.preconditioned_cover(const,terms,F(0),F(1));self.assertFalse(bad['strict_contraction'])
        with self.assertRaisesRegex(ValueError,'contracted'):law.temporal_inverse_errors(x,[1,1],[bad])

    def test_rank_one_stamps_against_full_decimal_matrices_24_queries(self):
        network=dense.CompensatedBdfNetwork(200,dense.model_parameters(1,'finite_transit'));g=dense.curvature.graph(network,10.)
        refs={(w['name'],l['reference']['subdivisions']):l['reference'] for w in read(dense.previous.proxy.REFERENCE)['windows'] for l in w['levels']}
        for c in self.report['cases']:
            prepared=dense.prepare(network,refs[c['window'],c['subdivisions']],31)
            self.assertEqual(prepared['support_sha256'],c['support_sha256'])
            inverse=[[F(v) for v in row] for row in c['inverse_binary']];scales=list(map(F,c['inverse_certificate']['column_scales']))
            for u,cell in ((F(0),0),(F(1,2),4),(F(1),7)):
                with localcontext() as ctx:
                    ctx.prec=160
                    x=[dense.law.decimal_fraction(dense.poly.evaluate(p,u)) for p in prepared['x']]
                h,_=descriptor(network,g,x,120);hf=[[F(v) for v in row] for row in h]
                # Decimal120 is a numerical witness, not an exact rational H.
                # A separate comparison budget protects exact structural zeros.
                # This margin is not used by the interval proof or circuit gates.
                coefficient_comparison_budget=F(1,10**100)*(1+max(abs(v) for row in hf for v in row))
                columns=[[(k,hf[k][j]) for k in range(119) if hf[k][j]] for j in range(119)]
                intervals=c['ideal_temporal_cover'][cell]['preconditioned_defect_intervals']
                for i in range(119):
                    for j in range(119):
                        e=(F(i==j)-sum((inverse[i][k]*v for k,v in columns[j]),F(0)))*scales[i]/scales[j]
                        a,b=map(F,intervals[i][j])
                        margin=coefficient_comparison_budget*scales[i]/scales[j]*sum(map(abs,inverse[i]),F(0))
                        self.assertLessEqual(a-margin,e,(c['window'],u,i,j));self.assertLessEqual(e,b+margin,(c['window'],u,i,j))

    def test_cover_contractions_budget_replays_and_selected_full_replays(self):
        network=dense.CompensatedBdfNetwork(200,dense.model_parameters(1,'finite_transit'));g=dense.curvature.graph(network,10.)
        refs={(w['name'],l['reference']['subdivisions']):l['reference'] for w in read(dense.previous.proxy.REFERENCE)['windows'] for l in w['levels']}
        for c in self.report['cases']:
            covers=c['ideal_temporal_cover'];self.assertEqual(len(covers),8)
            self.assertTrue(c['ideal_temporal_inverse_certified']);self.assertFalse(c['backward_gate_passed'])
            for i,cell in enumerate(covers):
                self.assertEqual(F(cell['left']),F(i,8));self.assertEqual(F(cell['right']),F(i+1,8))
                rows=[sum((max(abs(F(a)),abs(F(b))) for a,b in row),F(0)) for row in cell['preconditioned_defect_intervals']]
                self.assertEqual(list(map(str,rows)),cell['defect_row_upper']);self.assertEqual(max(rows),F(cell['contraction_upper']))
                self.assertLess(max(rows),1)
            cert=c['inverse_certificate'];q=F(cert['contraction_upper']);d=list(map(F,cert['column_scales']))
            frozen=[[q/(1-q)*F(p)/di for p in cert['error_column_peaks']] for di in d]
            temporal=law.temporal_inverse_errors(c['inverse_binary'],d,covers);v=c['forcing_inputs']
            args=[list(map(F,v[k])) for k in ('nodal_l1_c','constraint_l1_v_s','nodal_point_a','constraint_point_v')]
            for name,err,flag in (('weighted_frozen_budget',frozen,False),('weighted_temporal_budget',temporal,True)):
                replay=law.weighted_budget(c['inverse_binary'],err,94,list(map(F,c['weights'])),*args,F(c['duration_s']),time_varying=flag)
                self.assertEqual(replay,c[name]);self.assertTrue(replay['growth_supported'])
                self.assertFalse(replay['anchor_known']);self.assertFalse(replay['nonlinear_remainder_bound'])
            if (c['window'],c['subdivisions']) in (('attack',2),('reset',4)):
                p=dense.prepare(network,refs[c['window'],c['subdivisions']],31)
                const,terms=law.compile_terms(network,g,p,c['inverse_binary'],d)
                for i in (0,7):
                    _,replay=law.preconditioned_cover(const,terms,F(i,8),F(i+1,8));self.assertEqual(replay,covers[i])

    def test_storage_sources_scope_and_preserved_pre_measurement_parse_failures(self):
        report=self.report;storage=json.loads(producer.SUMMARY.read_text())['storage'];raw=producer.OUTPUT.read_bytes()
        self.assertEqual(report['schema'],'rf-d/bdf-static-weighted-descriptor/v1');self.assertEqual(len(report['cases']),8)
        self.assertEqual(len(raw),storage['bytes']);self.assertEqual(sha(raw),storage['compressed_sha256'])
        self.assertEqual(gzip.decompress(raw),canonical(report));self.assertEqual(sha(canonical(report)),storage['canonical_json_sha256'])
        for p,h in report['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        for suffix,source in (('parse_attempt','tools/loudness_latch_bdf_static_precision_weighted_descriptor.py'),
                              ('helper_parse_attempt','tools/loudness_latch_weighted_descriptor.py')):
            a=json.loads((ROOT/('evidence/loudness_latch_bdf_static_precision_weighted_descriptor_'+suffix+'.json')).read_text())
            self.assertEqual(sha(a['source_utf8'].encode()),a['source_sha256']);self.assertFalse(a['numerical_measurement_started'])
            self.assertNotEqual(a['exit_code'],0);self.assertIn('SyntaxError',a['stderr'])
            blob=subprocess.check_output(['git','show',a['git_head']+':'+source],cwd=ROOT)
            self.assertEqual(sha(blob),a['source_sha256']);self.assertNotEqual(sha((ROOT/source).read_bytes()),a['source_sha256'])
        for flag in ('actual_dae_error_bound','initial_error_known','full_path_coverage','nonlinear_remainder_bound',
                     'temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted','deadline_admitted','rounded_inverse_numerically_admitted'):
            self.assertFalse(report[flag],flag)
        self.assertTrue(report['ideal_descriptor_coefficients_enclosed'])
        self.assertEqual(report['new_exact_linear_systems'],0);self.assertEqual(report['new_nonlinear_circuit_solves'],0)


if __name__=='__main__':unittest.main()
