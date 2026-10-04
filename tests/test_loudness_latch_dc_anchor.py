from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from pathlib import Path
import gzip,json,hashlib,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_dc_anchor as law
import loudness_latch_bdf_static_precision_dc_anchor as producer
from loudness_latch_junction_rms import sqrt_bounds
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_directional_curvature import junction_values
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(v):return hashlib.sha256(v).hexdigest()
def decimal(v):v=F(v);return D(v.numerator)/D(v.denominator)
def empty_graph(n):return dict(node_count=n,fixed=dict(GND=0.),resistors=[],conductances=[],bjts=[],diodes=[])

class DcAnchor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=read(producer.OUTPUT)

    def test_known_linear_and_nonlinear_root_enclosures_and_rejections(self):
        # F(v)=2v-1, x=49/100 and X=1/2: exact root at 1/2.
        linear=law.prove([[(F(0),F(0))]],[(F(-1,100),F(-1,100))],F(1,50))
        self.assertTrue(linear['accepted']);self.assertEqual(F(linear['posterior_error_upper_v']),F(1,100))
        self.assertFalse(law.prove([[(F(0),F(0))]],[(F(-1,100),F(-1,100))],F(1,200))['accepted'])
        # F(v)=v²-2, x=7/5, X=5/14, r=1/10. Independent sqrt bracket witnesses the root.
        nonlinear=law.prove([[(F(-1,14),F(1,14))]],[(F(-1,70),F(-1,70))],F(1,10))
        self.assertTrue(nonlinear['accepted']);root=sqrt_bounds(2);error=F(nonlinear['posterior_error_upper_v'])
        self.assertGreaterEqual(F(7,5)+error,root[1]);self.assertLessEqual(F(7,5)-error,root[0])
        self.assertFalse(law.prove([[(F(-1),F(1))]],[(F(0),F(0))],F(1))['accepted'])
        for defect,residual,radius in (([],[],1),([[(0,0)]],[],1),([[(1,-1)]],[(0,0)],1),([[(0,0)]],[(0,0)],0)):
            with self.assertRaises(ValueError):law.prove(defect,residual,radius)

    def test_rank_one_preconditioning_current_conservation_and_compiled_cancellation(self):
        g=empty_graph(3);g['bjts']=[dict(ref='Q',base=0,collector=1,emitter=2,polarity=1,is_a=F(1,100),vt=F(1,10),beta_forward=2,beta_reverse=3)]
        inverse=[[F(1),F(1),F(1)],[F(2),F(-1),F(3)],[F(0),F(1),F(-1)]];compiled=law.compile_graph(g,[0,0,0],inverse)
        # The first preconditioner row sums all KCLs. Every nonlinear coefficient cancels exactly.
        self.assertFalse(any(i==0 for t in compiled['terms'] for i,j,c in t['coefficients']))
        gf=F(1,10);j=[[gf*(F(1,2)+F(1,3)),-gf/3,-gf/2],[-gf/3,gf*(1+F(1,3)),-gf],[-gf/2,-gf,gf*(1+F(1,2))]]
        self.assertTrue(all(sum(j[i][k] for i in range(3))==0 for k in range(3)))
        actual=[[compiled['constant_defect'][i][k][0] for k in range(3)] for i in range(3)]
        for t in compiled['terms']:
            for i,k,c in t['coefficients']:actual[i][k]-=c # exp(0)=1 exactly.
        for i in range(3):
            for k in range(3):self.assertEqual(actual[i][k],F(i==k)-sum(inverse[i][l]*j[l][k] for l in range(3)))
        point=law.static_point(g,[F(1,100),0,0]);total=(F(0),F(0))
        for v in point:total=law.iv.add(total,v)
        self.assertLessEqual(total[0],0);self.assertGreaterEqual(total[1],0)
        with self.assertRaises(ValueError):law.compile_graph(g,[0,0],inverse)
        with self.assertRaises(ValueError):law.compile_graph(g,[0,0,0],[])
        with self.assertRaises(ValueError):law.certify(compiled,0)
        with self.assertRaises(ValueError):law.certify(compiled,10)
        with self.assertRaises(ValueError):law.static_point(g,[10,0,0])

    def test_all_four_radii_replay_and_independent_decimal_products(self):
        r=self.report;center=list(map(F,r['center_node_v']));compiled=law.compile_graph(r['graph'],center,r['inverse_binary'])
        self.assertEqual(len(r['certificates']),4);self.assertEqual(r['primary_certificate_index'],0)
        for cert,radius in zip(r['certificates'],producer.RADII):
            self.assertEqual(cert,law.certify(compiled,radius));self.assertTrue(cert['accepted'])
            self.assertLess(F(cert['contraction_upper']),1);self.assertTrue(all(F(v)<radius for v in cert['row_image_radius_v']))
            self.assertLessEqual(F(cert['posterior_error_upper_v']),radius)
            self.assertEqual(F(cert['posterior_error_upper_v']),F(cert['eta_upper_v'])/(1-F(cert['contraction_upper'])))
        point=law.static_point(r['graph'],center)
        for precision in (80,100):
            with localcontext() as ctx:
                ctx.prec=precision;rd,jd=producer.evaluate(r['graph'],[decimal(v) for v in center],precision)
                for i in range(94):self.assertLessEqual(point[i][0],F(rd[i]));self.assertGreaterEqual(point[i][1],F(rd[i]))
                # Matrix product follows the independent outgoing-current Decimal graph, not compiled rank-one terms.
                for i,row in enumerate(r['inverse_binary']):
                    value=sum((D.from_float(v)*rd[k] for k,v in enumerate(row)),D(0));lo,hi=compiled['preconditioned_residual'][i]
                    self.assertLessEqual(lo,F(value));self.assertGreaterEqual(hi,F(value))
                cert=r['certificates'][0]
                for i in range(94):
                    for j in range(94):
                        value=D(i==j)-sum((D.from_float(r['inverse_binary'][i][k])*jd[k][j] for k in range(94)),D(0))
                        lo,hi=map(F,cert['defect_intervals'][i][j]);self.assertLessEqual(lo,F(value));self.assertGreaterEqual(hi,F(value))

    def test_all_25_memory_bounds_scales_and_initial_norm(self):
        r=self.report;frozen=read(producer.prior.FIXED);network=producer.CompensatedBdfNetwork(200,producer.model_parameters(1,'finite_transit'));state=producer.unpack(network,frozen['initial']).current
        error=F(r['certificates'][r['primary_certificate_index']]['posterior_error_upper_v']);center=list(map(F,r['center_node_v']));memory=r['memory_enclosure']
        self.assertEqual(memory,producer.memory_enclosure(network,state,center,error));self.assertEqual(len(memory['rows']),25)
        self.assertEqual(memory['weights'][:21],['1']*21)
        for row in memory['rows']:
            lo,hi=map(F,row['ideal_charge_interval_c']);stored=F(row['stored_charge_c']);scale=F(row['scale_c_per_v']);e=max(abs(lo-stored),abs(hi-stored))
            self.assertEqual(e,F(row['error_upper_c']));self.assertEqual(e/scale,F(row['coordinate_error_upper_v']));self.assertEqual(F(row['weighted_error_upper_v']),F(row['weight'])*e/scale)
            if row['kind']=='linear':
                a,b,fixed,cap,resistance=network.network.branches[row['index']];v=center[a]-(center[b] if b is not None else F(fixed));width=error*(2 if b is not None else 1)
                self.assertEqual((lo,hi),(F(cap)*(v-width),F(cap)*(v+width)));self.assertEqual(stored,F(cap)*sum(map(F,state.capacitor_pairs_v[row['index']]),F(0)))
            else:
                p=network.network.latch.device.parameters;be=row['other_terminal_index']==2;dep=p.depletion_be if be else p.depletion_bc;transit=p.transit_forward_s if be else p.transit_reverse_s;em=p.emission_be_v if be else p.emission_bc_v
                for voltage in row['voltage_interval_v']:
                    with localcontext() as ctx:
                        ctx.prec=100;q,cap,q2=junction_values(dep,transit,p.saturation_a,em,decimal(voltage))
                    self.assertLessEqual(lo,F(q));self.assertGreaterEqual(hi,F(q))
                upper=F(row['center_capacitance_interval_f'][1]);w=F(row['weight']);self.assertLessEqual(w,producer.SCALE/upper);self.assertLess(producer.SCALE/upper,2*w)
        self.assertEqual(F(memory['weighted_infinity_error_upper_v']),max(F(v['weighted_error_upper_v']) for v in memory['rows']))
        self.assertTrue(memory['dc_charge_error_bound_proven']);self.assertFalse(memory['post_key_charge_error_bound_proven'])

    def test_key_event_domain_obstruction_and_zero_mass_row(self):
        r=self.report;network=producer.CompensatedBdfNetwork(200,producer.model_parameters(1,'finite_transit'));error=F(r['certificates'][0]['posterior_error_upper_v']);event=r['event_audit']
        self.assertEqual(event,producer.event_audit(network,r['graph'],r['center_node_v'],error));self.assertEqual(event['node_row_index'],77)
        self.assertTrue(event['frozen_voltage_hypothesis_refuted']);self.assertFalse(event['frozen_voltage_hypothesis_admissible']);self.assertGreater(F(event['post_key_exponent_with_frozen_nodes'][0]),200)
        vt=F(event['device']['ideality'])*F(event['device']['vt']);minimum=F(event['minimum_post_event_node_v']);self.assertEqual((F(10)-minimum)/vt,45)
        self.assertEqual(F(event['minimum_upward_jump_for_domain_v']),minimum-F(event['pre_event_node_interval_v'][1]));self.assertGreater(F(event['minimum_upward_jump_for_domain_v']),8)
        self.assertEqual(event['modeled_memory_ports'],[]);self.assertTrue(event['modeled_mass_row_zero']);self.assertFalse(event['post_event_state_solved'])
        post=dict(r['graph'],fixed=r['graph']['fixed']|{'contour/KEYBOARD_TRIGGER':10.})
        with self.assertRaisesRegex(ValueError,'exponential domain'):law.static_point(post,r['center_node_v'])
        self.assertFalse(event['exponential_evaluated_outside_domain']);self.assertFalse(event['physical_parasitics_identified']);self.assertFalse(event['post_event_anchor_error_bound_proven'])

    def test_storage_sources_destinations_and_scope(self):
        r=self.report;raw=producer.OUTPUT.read_bytes();s=json.loads(producer.SUMMARY.read_text(encoding='utf-8'))['storage']
        self.assertEqual(r['schema'],'rf-d/bdf-static-dc-anchor/v1');self.assertEqual(len(raw),s['bytes']);self.assertEqual(sha(raw),s['compressed_sha256']);self.assertEqual(gzip.decompress(raw),canonical(r));self.assertEqual(sha(canonical(r)),s['canonical_json_sha256'])
        for p,h in r['source_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        self.assertNotEqual(producer.OUTPUT,producer.SUMMARY);self.assertNotIn(producer.OUTPUT,producer.PATHS);self.assertNotIn(producer.SUMMARY,producer.PATHS)
        self.assertTrue(r['dc_root_enclosure_proven']);self.assertTrue(r['dc_memory_error_bound_proven']);self.assertEqual(r['new_binary_preconditioners'],1);self.assertEqual(r['new_dc_nonlinear_solves'],0)
        for flag in ('post_key_initial_error_known','initial_error_known','binary_preconditioner_audio_admitted','prior_parameters_changed','prior_norms_changed',
                     'nonlinear_remainder_bound','actual_dae_error_bound','full_path_coverage','temporal_error_bound_admitted','physical_trajectory_bound','audio_admitted','deadline_admitted','numerical_gates_changed','prior_reports_modified'):self.assertFalse(r[flag],flag)

if __name__=='__main__':unittest.main()
