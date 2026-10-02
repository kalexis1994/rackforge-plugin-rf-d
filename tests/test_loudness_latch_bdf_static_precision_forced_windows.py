import gzip,hashlib,json,sys,unittest
from fractions import Fraction as F
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_forced_windows as experiment
import loudness_latch_bdf_forcing as force
import loudness_latch_directional_curvature as curvature
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters


def scalar_witness(r,h,t,current,previous,lam):
    k=h/r
    # Independent Lagrange derivative weights at the destination.
    times=(t+h,t,t-k)
    weights=[]
    for i,ti in enumerate(times):
        other=[j for j in range(3) if j!=i]
        weights.append(sum((times[0]-times[j] for j in other),F(0))/
                       ((ti-times[other[0]])*(ti-times[other[1]])))
    a,b,c=weights;dest=t+h;rhs=3*dest**2-lam*dest**3
    numerical=(rhs-b*current-c*previous)/(a-lam)
    exact=dest**3
    # Residual difference at the exact solution is the genuine polynomial defect.
    defect=a*exact+b*t**3+c*(t-k)**3-3*dest**2
    ec=t**3-current;ep=(t-k)**3-previous
    predicted=(-b*ec-c*ep+defect)/(a-lam)
    return exact-numerical,predicted,defect


class ForcedInitial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.base=json.loads(gzip.decompress(experiment.SOURCE.read_bytes()))['windows']
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))

    def test_every_accepted_fine_step_and_both_blocked_clock_attempts(self):
        count=0;clock_stops=0
        for w,base in zip(self.report['windows'],self.base):
            for level in w['levels']:
                ref=level['reference'];old=unpack(self.network,ref['initial'])
                for step in ref['steps']:
                    self.assertEqual(state_hash(old),step['previous_history_sha256'])
                    new=unpack(self.network,step['history']);h=step['diagnostics']['actual_dt_s']
                    self.assertEqual(new.time_s,step['destination_s']);self.assertEqual(new.previous,old.current)
                    pub=publication_check(self.network,old,new,h,step['diagnostics'])
                    self.assertEqual(canonical(pub),canonical(step['publication']))
                    self.assertTrue(pub['round_trip_exact']);self.assertLess(pub['max_published_kcl_a'],1e-11)
                    self.assertLess(pub['max_branch_equation_error_v'],1e-14)
                    self.assertLess(step['diagnostics']['correction_v'],1e-8)
                    self.assertGreaterEqual(h,1e-12);self.assertLessEqual(step['diagnostics']['coefficients']['ratio'],2)
                    old=new;count+=1
                self.assertEqual(canonical(pack(old)),canonical(ref['final']))
                if ref['stop']:
                    stop=ref['stop'];snapshot=state_hash(old)
                    self.assertEqual(canonical(pack(old)),canonical(stop['incoming']))
                    self.assertGreater(stop['dt_s']/old.previous_dt_s,2)
                    with self.assertRaisesRegex(ValueError,'growth at most two'):
                        self.network.advance(old,10.,stop['dt_s'])
                    self.assertEqual(state_hash(old),snapshot);clock_stops+=1
                for sample in ref['samples']:
                    self.assertEqual(canonical(sample['history']),canonical(ref['steps'][sample['fine_step_index']]['history']))
                    self.assertEqual(sample['history']['time_s'],base['reference'][sample['base_index']]['history']['time_s'])
        self.assertEqual(count,1276);self.assertEqual(clock_stops,2)

    def test_first_last_fresh_replays_and_rhs_format_failures_preserved(self):
        for w,base in zip(self.report['windows'],self.base):
            for level in w['levels']:
                steps=level['reference']['steps']
                for index in (0,len(steps)-1):
                    old=unpack(self.network,level['reference']['initial'] if index==0 else steps[index-1]['history'])
                    new,diag=self.network.advance(old,10.,steps[index]['diagnostics']['actual_dt_s'])
                    self.assertEqual(canonical(pack(new)),canonical(steps[index]['history']))
                    self.assertEqual(canonical(diag),canonical(steps[index]['diagnostics']))
                forced=level['forced'];self.assertEqual(forced['rows'],[]);self.assertFalse(forced['complete'])
                self.assertEqual(forced['stop']['error'],'square matrix and complete RHS columns required')
                self.assertEqual(np.array(forced['stop']['rhs_first_a']).shape,(94,))
                self.assertIsNone(forced['stop']['first_solve']);self.assertIsNone(forced['stop']['rhs_second_a'])

    def test_first_forcing_reproduces_with_independent_precision_and_zero_identity(self):
        g=curvature.graph(self.network)
        for w,base in zip(self.report['windows'],self.base):
            initial=unpack(self.network,base['initial'])
            new=unpack(self.network,base['reference'][0]['history'])
            dt=base['reference'][0]['diagnostics']['coefficients']['effective_dt_s']
            gamma=base['reference'][0]['diagnostics']['coefficients']['gamma']
            zero_virtual=force.virtual(force.difference(initial.current,initial.current)['memory_v'],
                                       force.difference(initial.previous,initial.previous)['memory_v'],gamma)
            for level in w['levels']:
                ref=unpack(self.network,level['reference']['samples'][0]['history']).current
                f=force.forcing(self.network,g,new,ref,zero_virtual,dt,80)
                self.assertEqual(force.serial(f),level['forced']['stop']['forcing'])
                other=force.forcing(self.network,g,new,ref,zero_virtual,dt,100)
                for key in ('residual_a','publication_offset_v'):self.assertTrue(curvature.metrics(f[key],other[key])['passed'])
            zero=force.forcing(self.network,g,new,new.current,[0.]*25,dt,80)
            self.assertTrue(all(v==0 for vector in zero.values() for v in vector))

    def test_exact_forcing_sign_series_rc_and_storage_identities(self):
        for r in (F(1,4),F(1,2),F(1),F(2)):
            for lam in (F(-3),F(0),F(1,7)):
                actual,pred,defect=scalar_witness(r,F(1,10),F(2,5),F(3,100),F(-1,20),lam)
                self.assertEqual(actual,pred);self.assertNotEqual(defect,0)
                self.assertNotEqual(actual,pred-defect/((1+2*r)/((1+r)*F(1,10))-lam))
        dt=F(1,1000);cap=F(1,100000);resistance=F(25500)
        beta=dt/(dt+cap*resistance);dv=F(1,10);virtual=F(-1,20);offset=F(1,1000000)
        published=beta*dv+(1-beta)*virtual+offset
        self.assertEqual(published-(beta*dv+(1-beta)*virtual),offset)
        self.assertNotEqual(published,dv+offset)
        summary=json.loads(experiment.SUMMARY.read_bytes());storage=summary['storage']
        sha=lambda raw:hashlib.sha256(raw).hexdigest()
        self.assertEqual(len(self.raw),storage['bytes']);self.assertEqual(sha(self.raw),storage['compressed_sha256'])
        self.assertEqual(sha(canonical(self.report)),storage['canonical_json_sha256'])
        for name,value in self.report['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),value)
        for key in ('independent_error_estimator','reference_defects_are_exact_temporal_defects','temporal_error_bound_admitted',
                    'temporal_refinement_admitted','integrator_changed','audio_admitted','deadline_admitted'):
            self.assertFalse(self.report[key])


if __name__=='__main__':unittest.main()
