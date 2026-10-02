import gzip,hashlib,json,sys,unittest
from decimal import localcontext
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_forced_clock as experiment
import loudness_latch_bdf_forcing as force
import loudness_latch_directional_curvature as curvature
from loudness_latch_bdf_clock_plan import plan
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_static_precision_windows import candidate
from loudness_latch_bdf_static_precision import solved
from loudness_latch_bdf_memory_transfer import stamps,node_difference,memory_difference
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters
from test_loudness_latch_bdf_static_precision_forced_windows import scalar_witness


class ForcedClock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.base=json.loads(gzip.decompress(experiment.SOURCE.read_bytes()))['windows']
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))
        cls.graph=curvature.graph(cls.network)

    def test_every_fine_step_clock_publication_sampling_and_2_4_contrast(self):
        count=0
        for w,base in zip(self.report['windows'],self.base):
            self.assertEqual(w['name'],base['name'])
            for level in w['levels']:
                ref=level['reference'];old=unpack(self.network,ref['initial']);n=ref['subdivisions']
                self.assertEqual(canonical(ref['initial']),canonical(base['initial']))
                self.assertTrue(ref['complete']);self.assertIsNone(ref['stop']);self.assertEqual(len(ref['samples']),64)
                self.assertEqual(ref['attempted_intervals'],64*n)
                for index,base_step in enumerate(base['reference']):
                    schedule=plan(old,base_step['history']['time_s'],n)
                    for step,target in zip(ref['steps'][index*n:(index+1)*n],schedule):
                        self.assertEqual(state_hash(old),step['previous_history_sha256'])
                        new=unpack(self.network,step['history']);h=step['diagnostics']['actual_dt_s']
                        self.assertEqual(new.time_s,target);self.assertEqual(new.previous,old.current)
                        self.assertEqual(new.time_s-old.time_s,h)
                        self.assertEqual(h-base_step['diagnostics']['actual_dt_s']/n,step['dt_minus_nominal_s'])
                        pub=publication_check(self.network,old,new,h,step['diagnostics'])
                        self.assertEqual(canonical(pub),canonical(step['publication']))
                        self.assertTrue(pub['round_trip_exact']);self.assertLess(pub['max_published_kcl_a'],1e-11)
                        self.assertLess(pub['max_branch_equation_error_v'],1e-14)
                        self.assertLess(step['diagnostics']['correction_v'],1e-8)
                        self.assertGreaterEqual(h,1e-12);self.assertLessEqual(step['diagnostics']['coefficients']['ratio'],2)
                        old=new;count+=1
                    self.assertEqual(canonical(pack(old)),canonical(ref['samples'][index]['history']))
                self.assertEqual(canonical(pack(old)),canonical(ref['final']))
            for contrast,a,b in zip(w['refinement_4_minus_2'],w['levels'][0]['reference']['samples'],w['levels'][1]['reference']['samples']):
                x=unpack(self.network,a['history']).current;y=unpack(self.network,b['history']).current
                np.testing.assert_array_equal(node_difference(y,x),contrast['node_difference_4_minus_2_v'])
                np.testing.assert_array_equal(memory_difference(y,x),contrast['memory_difference_4_minus_2_v'])
        self.assertEqual(count,1536)

    def test_all_forcing_curvature_recurrences_publication_offsets_and_solve_gates(self):
        count=0;audits=0
        for w,base in zip(self.report['windows'],self.base):
            for level in w['levels']:
                forced=level['forced'];self.assertTrue(forced['complete']);self.assertIsNone(forced['stop'])
                old=unpack(self.network,base['initial']);last=old.current;prior=old.previous
                cur1=np.zeros(25);prev1=np.zeros(25);cur2=np.zeros(25);prev2=np.zeros(25)
                for row,step,sample in zip(forced['rows'],base['reference'],level['reference']['samples']):
                    new=unpack(self.network,step['history']);ref=unpack(self.network,sample['history']).current
                    virtual,c,_=candidate(old,step,self.network);dt=c['effective_dt_s'];gamma=c['gamma']
                    vref=force.virtual(force.difference(last,old.current)['memory_v'],force.difference(prior,old.previous)['memory_v'],gamma)
                    self.assertEqual([str(v) for v in vref],row['virtual_reference_difference_v'])
                    f=force.forcing(self.network,self.graph,new,ref,vref,dt,80)
                    f100=force.forcing(self.network,self.graph,new,ref,vref,dt,100)
                    self.assertEqual(force.serial(f),row['forcing'])
                    for key in ('residual_a','publication_offset_v'):
                        metric=curvature.metrics(f[key],f100[key])
                        self.assertEqual(metric,row['forcing_precision'][key]);self.assertTrue(metric['passed'])
                    v1=(1+gamma)*cur1-gamma*prev1;v2=(1+gamma)*cur2-gamma*prev2
                    _,j=self.network.network.increment_evaluator(10.,virtual,dt)(np.array(step['diagnostics']['increment_v']))
                    b,p,d=stamps(self.network,new,dt)
                    n1=np.array(row['node_first_v']);n2=np.array(row['node_second_v'])
                    h=curvature.evaluate(self.network,self.graph,force.nodes(new.current),n1,dt,80)
                    h100=curvature.evaluate(self.network,self.graph,force.nodes(new.current),n1,dt,100)
                    self.assertEqual(force.serial(h),row['curvature'])
                    for key in ('residual_a','publication_coordinate_v'):
                        metric=curvature.metrics(h[key],h100[key])
                        self.assertEqual(metric,row['curvature_precision'][key]);self.assertTrue(metric['passed'])
                    rhs1=b@v1+force.floats(f['residual_a']);rhs2=b@v2-curvature.floats(h['residual_a'])
                    np.testing.assert_array_equal(rhs1,row['rhs_first_a']);np.testing.assert_array_equal(rhs2,row['rhs_second_a'])
                    m1=p@n1+d@v1+force.floats(f['publication_offset_v'])
                    m2=p@n2+d@v2+curvature.floats(h['publication_coordinate_v'])
                    np.testing.assert_array_equal(m1,row['memory_first_v']);np.testing.assert_array_equal(m2,row['memory_second_v'])
                    for name,nvec,rhs in (('first',n1,rhs1),('second',n2,rhs2)):
                        _,error=backward_errors(j,rhs[:,None],nvec[:,None])
                        self.assertLess(max(error.values()),1e-10)
                        self.assertLess(max(row[name+'_solve'][k] for k in error),1e-10)
                    for order in ('linear','quadratic'):
                        for name,pred in (('node',n1 if order=='linear' else n1+n2/2),('memory',m1 if order=='linear' else m1+m2/2)):
                            np.testing.assert_array_equal(pred,row['predictions'][order+'_'+name+'_v'])
                            self.assertEqual(experiment.compare(force.floats(f[name+'_difference_v']),pred),row['comparisons'][order][name])
                    if 'exact_audit' in row:
                        a=row['exact_audit'];self.assertTrue(a['passed']);self.assertTrue(a['map_gate_passed'])
                        self.assertTrue(a['exact_solve']['exact_rational_residual_zero']);audits+=1
                        # Audit preprocessing too: H inputs were prepared in ambient Decimal28.
                        with localcontext() as ctx:
                            ctx.prec=80;lifted_nodes=force.nodes(new.current)
                        high=curvature.evaluate(self.network,self.graph,lifted_nodes,n1,dt,80)
                        for key in ('residual_a','publication_coordinate_v'):
                            self.assertTrue(curvature.metrics(high[key],h[key])['passed'])
                    old=new;prior,last=last,ref;prev1,cur1=cur1,m1;prev2,cur2=cur2,m2;count+=1
        self.assertEqual(count,512);self.assertEqual(audits,24)

    def test_selected_fresh_nonlinear_replays_and_rational_first_second_rhs(self):
        count=0
        for w,base in zip(self.report['windows'],self.base):
            for level in w['levels']:
                steps=level['reference']['steps']
                for i in (0,len(steps)//2,len(steps)-1):
                    old=unpack(self.network,level['reference']['initial'] if i==0 else steps[i-1]['history'])
                    snapshot=state_hash(old);new,diag=self.network.advance(old,10.,steps[i]['diagnostics']['actual_dt_s'])
                    self.assertEqual(canonical(pack(new)),canonical(steps[i]['history']))
                    self.assertEqual(canonical(diag),canonical(steps[i]['diagnostics']));self.assertEqual(state_hash(old),snapshot);count+=1
            row=w['levels'][0]['forced']['rows'][31];old=unpack(self.network,base['reference'][30]['history'])
            step=base['reference'][31];virtual,c,_=candidate(old,step,self.network)
            _,j=self.network.network.increment_evaluator(10.,virtual,c['effective_dt_s'])(np.array(step['diagnostics']['increment_v']))
            exact=solved(j,np.column_stack((row['rhs_first_a'],row['rhs_second_a'])))
            self.assertEqual(canonical(exact),canonical({k:v for k,v in row['exact_audit'].items()
                if k not in ('maximum_scaled_map_difference','map_gate_passed')}))
        self.assertEqual(count,24)

    def test_clock_edge_counterexamples_negative_domains_and_exact_forcing_sign(self):
        old_report=json.loads(gzip.decompress(experiment.FAILED_DATA.read_bytes()));fixed=0
        for w,base in zip(old_report['windows'],self.base):
            for level in w['levels']:
                stop=level['reference']['stop']
                if stop is None:continue
                old=unpack(self.network,stop['incoming']);target=base['reference'][stop['index']]['history']['time_s']
                endpoints=plan(old,target,level['reference']['subdivisions']);t=old.time_s;previous=old.previous_dt_s
                for endpoint in endpoints:
                    h=endpoint-t;self.assertLessEqual(h/previous,2);self.assertGreaterEqual(h,1e-12)
                    self.assertEqual(F.from_float(t)+F.from_float(h),F.from_float(endpoint));t=endpoint;previous=h
                self.assertEqual(t,target);fixed+=1
        self.assertEqual(fixed,2)
        old=SimpleNamespace(time_s=.0024,previous_dt_s=1e-8)
        for target,count in ((.0049,2),(.0024,2),(.002400000000000001,4),(.0028,2)):
            with self.assertRaises(ValueError):plan(old,target,count)
        for r in (F(1,4),F(1,2),F(1),F(2)):
            actual,pred,defect=scalar_witness(r,F(1,10),F(2,5),F(3,100),F(-1,20),F(-3))
            self.assertEqual(actual,pred);self.assertNotEqual(defect,0)

    def test_storage_sources_retained_failures_and_scope(self):
        sha=lambda raw:hashlib.sha256(raw).hexdigest();summary=json.loads(experiment.SUMMARY.read_bytes())
        self.assertEqual(len(self.raw),summary['storage']['bytes']);self.assertEqual(sha(self.raw),summary['storage']['compressed_sha256'])
        self.assertEqual(sha(canonical(self.report)),summary['storage']['canonical_json_sha256'])
        for name,value in self.report['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),value)
        self.assertEqual(self.report['subdivisions'],[2,4]);self.assertEqual(self.report['audit_indices'],[0,31,63])
        for key in ('independent_error_estimator','reference_defects_are_exact_temporal_defects','temporal_error_bound_admitted',
                    'temporal_refinement_admitted','integrator_changed','prior_failed_attempt_modified','audio_admitted','deadline_admitted'):
            self.assertFalse(self.report[key])


if __name__=='__main__':unittest.main()
