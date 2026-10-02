import gzip,hashlib,json,sys,unittest
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_bdf_static_precision_charge_proxy as experiment
import loudness_latch_bdf_charge_defect as law
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_directional_curvature import metrics
from bjt_charge_ngspice_probes import model_parameters

def fraction(value):return F(value['numerator'],value['denominator'])

def exact_charges(network,state):
    return [F(cap)*(F(a)+F(b)) for (_,_,_,cap,_),(a,b) in zip(network.network.branches,state.capacitor_pairs_v)]+[
        F(q) for device in state.latch.devices for q in (device.be_c,device.bc_c)]

def weighted(weights,values):
    return [sum((w*v[j] for w,v in zip(weights,values)),F(0)) for j in range(25)]


class ChargeProxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=experiment.OUTPUT.read_bytes();cls.report=json.loads(gzip.decompress(cls.raw))
        cls.base=json.loads(gzip.decompress(experiment.BASE.read_bytes()))['windows']
        cls.references=json.loads(gzip.decompress(experiment.REFERENCE.read_bytes()))['windows']
        cls.network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))

    def test_all_operator_moments_actual_clocks_binary_origin_and_sample_coverage(self):
        count=0
        for w,base,source in zip(self.report['windows'],self.base,self.references):
            self.assertEqual(w['name'],base['name']);self.assertEqual(w['name'],source['name'])
            for level,original in zip(w['levels'],source['levels']):
                self.assertEqual(level['subdivisions'],original['reference']['subdivisions'])
                self.assertEqual(level['skipped_indices'],[0,1]);self.assertEqual([r['index'] for r in level['rows']],list(range(2,64)))
                ref=original['reference']
                for row in level['rows']:
                    index=row['index'];fi=ref['samples'][index]['fine_step_index']
                    ct=[fraction(v) for v in row['clock_times_s']];ft=[fraction(v) for v in row['fine_times_s']]
                    self.assertEqual(ct,[F(ref['samples'][j]['history']['time_s']) for j in (index,index-1,index-2)])
                    self.assertEqual(ft,[F(ref['steps'][j]['history']['time_s']) for j in range(fi,fi-4,-1)])
                    for name,times in (('clock',ct),('fine_cubic',ft),('fine_quadratic',ft[:3])):
                        weights=[fraction(v) for v in row['operators'][name]]
                        for degree in range(len(times)):
                            derivative=F(0) if degree==0 else degree*times[0]**(degree-1)
                            self.assertEqual(sum((w*t**degree for w,t in zip(weights,times)),F(0)),derivative)
                    step=base['reference'][index];h=F(step['diagnostics']['actual_dt_s']);k=F(base['reference'][index-1]['diagnostics']['actual_dt_s'])
                    self.assertEqual([fraction(v) for v in row['operators']['command']],list(law.weights(h,k)))
                    a0=F(step['diagnostics']['coefficients']['a0']);a2=F(step['diagnostics']['coefficients']['a2'])
                    self.assertEqual([fraction(v) for v in row['operators']['binary']],[a0/h,-(a0+a2)/h,a2/h])
                    for weights in row['operators'].values():self.assertEqual(sum(fraction(v) for v in weights),0)
                    self.assertEqual(fraction(row['clock_ratio']),(ct[0]-ct[1])/(ct[1]-ct[2]))
                    self.assertEqual(row['clock_ratio_exceeds_solver_domain'],fraction(row['clock_ratio'])>2)
                    self.assertEqual(fraction(row['command_ratio']),h/k);self.assertLessEqual(h/k,2)
                    self.assertEqual(fraction(row['ideal_effective_dt_s']),h/a0)
                    # Cubic derivative is exact at these clocks; the coarse defect has the kernel mass sign.
                    cw=[fraction(v) for v in row['operators']['clock']];fw=[fraction(v) for v in row['operators']['fine_cubic']]
                    defect=sum((a*t**3 for a,t in zip(cw,ct)),F(0))-sum((a*t**3 for a,t in zip(fw,ft)),F(0))
                    self.assertEqual(defect,-(ct[0]-ct[1])*(ct[0]-ct[2]));count+=1
        self.assertEqual(count,496)

    def test_every_decimal80_100_reproduction_decomposition_and_conservation(self):
        count=0
        for w,base,source in zip(self.report['windows'],self.base,self.references):
            for level,original in zip(w['levels'],source['levels']):
                for row in level['rows']:
                    a=experiment.evaluate_point(self.network,base,original['reference'],row['index'],80)
                    high=experiment.evaluate_point(self.network,base,original['reference'],row['index'],100)
                    self.assertEqual({k:[str(v) for v in vector] for k,vector in a['vectors'].items()},row['vectors'])
                    for key,vector in a['vectors'].items():
                        m=metrics(vector,high['vectors'][key]);self.assertEqual(m,row['precision'][key]);self.assertTrue(m['passed'])
                    self.assertEqual(a['decomposition'],row['decomposition']);self.assertTrue(row['decomposition']['passed'])
                    self.assertEqual(str(a['effective_dt_difference_s']),row['effective_dt_difference_s'])
                    self.assertEqual([str(v) for v in a['beta']],row['beta'])
                    self.assertLess(abs(a['vectors']['conservation_error_a'][0]),D('1e-30'))
                    self.assertTrue(row['conservation_gate_passed']);count+=1
        self.assertEqual(count,496)

    def test_24_independent_rational_charge_and_rc_incidence_replays(self):
        count=0
        for w,base,source in zip(self.report['windows'],self.base,self.references):
            for level,original in zip(w['levels'],source['levels']):
                ref=original['reference']
                for index in (2,31,63):
                    row=level['rows'][index-2];fi=ref['samples'][index]['fine_step_index']
                    ops={name:[fraction(v) for v in v] for name,v in row['operators'].items()}
                    qc=[exact_charges(self.network,unpack(self.network,ref['samples'][j]['history']).current) for j in (index,index-1,index-2)]
                    qf=[exact_charges(self.network,unpack(self.network,ref['steps'][j]['history']).current) for j in range(fi,fi-4,-1)]
                    dc=weighted(ops['fine_cubic'],qf);clock=weighted(ops['clock'],qc)
                    command=weighted(ops['command'],qc);binary=weighted(ops['binary'],qc)
                    vectors=dict(clock_defect_proxy_a=[a-b for a,b in zip(clock,dc)],
                        command_clock_term_a=[a-b for a,b in zip(command,clock)],
                        coefficient_term_a=[a-b for a,b in zip(binary,command)],
                        binary_defect_proxy_a=[a-b for a,b in zip(binary,dc)])
                    tau=vectors['binary_defect_proxy_a'];nodal=[F(0)]*94;pub=[F(0)]*25;boundary=F(0)
                    def stamp(left,right,current):
                        nonlocal boundary
                        if left is not None:nodal[left]+=current
                        else:boundary+=current
                        if right is not None:nodal[right]-=current
                        else:boundary-=current
                    dt=fraction(row['ideal_effective_dt_s'])
                    for j,(left,right,_,cap,resistance) in enumerate(self.network.network.branches):
                        beta=dt/(dt+F(cap)*F(resistance));stamp(left,right,beta*tau[j]);pub[j]=F(resistance)*beta*tau[j]
                    p=self.network.network.latch.device.parameters
                    for j,terminals in enumerate(self.network.network.latch.terminals):
                        b,c,e=[i for i,_ in terminals];stamp(b,e,p.polarity*tau[21+2*j]);stamp(b,c,p.polarity*tau[22+2*j])
                    self.assertEqual(sum(nodal)+boundary,0)
                    self.assertTrue(all(value==0 for j,value in enumerate(pub) if j!=17))
                    vectors.update(nodal_residual_proxy_a=nodal,publication_proxy_v=pub,fixed_boundary_sum_a=[boundary])
                    with localcontext() as ctx:
                        ctx.prec=100
                        for name,value in vectors.items():
                            exact=[law.decimal_fraction(v) for v in value];stored=[D(v) for v in row['vectors'][name]]
                            self.assertTrue(metrics(exact,stored)['passed'],name)
                    # Origin cancellation holds exactly, including both rounded-coefficient operators.
                    offset=F(1,1000000);shifted=[[value+offset for value in vector] for vector in qc]
                    self.assertEqual(weighted(ops['binary'],shifted),binary);count+=1
        self.assertEqual(count,24)

    def test_storage_scope_and_all_4_minus_2_differences(self):
        sha=lambda b:hashlib.sha256(b).hexdigest();summary=json.loads(experiment.SUMMARY.read_bytes())
        self.assertEqual(len(self.raw),summary['storage']['bytes']);self.assertEqual(sha(self.raw),summary['storage']['compressed_sha256'])
        self.assertEqual(sha(canonical(self.report)),summary['storage']['canonical_json_sha256'])
        for name,h in self.report['source_sha256'].items():self.assertEqual(sha((ROOT/name).read_bytes()),h)
        with localcontext() as ctx:
            ctx.prec=80
            for w in self.report['windows']:
                for difference,a,b in zip(w['proxy_4_minus_2'],w['levels'][0]['rows'],w['levels'][1]['rows']):
                    self.assertEqual(difference['index'],a['index']);self.assertEqual(a['time_s'],b['time_s'])
                    values=[str(D(y)-D(x)) for x,y in zip(a['vectors']['binary_defect_proxy_a'],b['vectors']['binary_defect_proxy_a'])]
                    self.assertEqual(values,difference['binary_proxy_4_minus_2_a'])
        self.assertEqual(self.report['new_nonlinear_solves'],0)
        for key in ('prior_reports_modified','integrator_changed','exact_temporal_defect_known','independent_error_estimator',
                    'temporal_error_bound_admitted','physical_switching_admitted','audio_admitted','deadline_admitted'):
            self.assertFalse(self.report[key])


if __name__=='__main__':unittest.main()
