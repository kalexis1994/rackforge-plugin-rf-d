"""Bounded two-way coupling screen, with an independent monolithic control first."""
from dataclasses import replace
import gzip,json,math
from pathlib import Path
import numpy as np
import loudness_voice_circuit as c
import loudness_voice_probes as screen
import voice_port_relaxation as p
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT


def frequency(t,ramp):
    edges=vco.crossings(t,ramp,-2,True);edges=edges[edges>=.00201]
    if len(edges)<5:raise ValueError('reset train too short')
    return float(1/np.mean(np.diff(edges)))


def reference_contrast(vraw,braw):
    bank=json.loads(gzip.decompress((ROOT/'evidence/voice_circuit_klu_bank01.json.gz').read_bytes()))
    receipt=bank['cases']['nominal500']['receipt']
    path=ROOT/'references-local/voice-circuit'/bank['bank']/'nominal500.txt'
    if vco.sha(path)!=receipt['raw_export_sha256']:raise ValueError('monolithic control identity')
    reference=np.loadtxt(path,skiprows=1,ndmin=2)
    if abs(reference[-1,0]-vraw[-1,0])>1e-14 or not np.isfinite(reference).all():raise ValueError('reference horizon')
    t=np.union1d(reference[:,0],np.union1d(vraw[:,0],braw[:,0]));d={}
    t=t[t<=min(reference[-1,0],vraw[-1,0],braw[-1,0])]
    for name in ('v(mix_bus_board4_pin4)','v(f4_recover_collector)','v(f4_main_output)'):
        x=np.interp(t,reference[:,0],reference[:,voice.VECTORS.index(name)+1])
        y=np.interp(t,braw[:,0],braw[:,p.BOARD_VECTORS.index(name)+1]);d[name]=float(np.max(np.abs(x-y)))
    cents=abs(1200*math.log2(frequency(reference[:,0],reference[:,1])/frequency(vraw[:,0],vraw[:,1])))
    return dict(reference_export_sha256=vco.sha(path),max_trace_difference_v=d,frequency_cents=cents,
        passed=max(d.values())<=p.GATES['trace_v'] and cents<=p.GATES['frequency_cents'])


def solve(s,label,with_contour,work,exe,report,save,port_factory=p.factory):
    bt=np.array([0.,s.oscillator.duration_s]);bus=np.zeros(2);history=[]
    result=dict(iterations=history,passed=False);report['cases'][label]=result
    for k in range(p.GATES['max_iterations']):
        record=dict(iteration=k+1);history.append(record)
        try:
            fn,vectors=port_factory(s,'vco',bt,bus,with_contour)
            vraw,vr=voice.run(s,f'{label}-{k+1:02d}-vco',work,exe,netlist_factory=fn,vectors=vectors,timeout=120)
            record['vco_receipt']=vr;save()
            if 'non-increasing PWL' in (work/(vr['label']+'.log')).read_text(encoding='utf-8'):
                raise ValueError('serialized port clock rejected by ngspice')
            left=vraw[:,p.VCO_VECTORS.index('v(r6_wiper)')+1]
            fn,bvectors=port_factory(s,'board',vraw[:,0],left,with_contour)
            braw,br=voice.run(s,f'{label}-{k+1:02d}-board',work,exe,netlist_factory=fn,vectors=bvectors,timeout=120)
            record['board_receipt']=br
            if 'non-increasing PWL' in (work/(br['label']+'.log')).read_text(encoding='utf-8'):
                raise ValueError('serialized port clock rejected by ngspice')
            if any(r['source_sha256']!=r['source_sha256_after'] for r in (vr,br)):raise ValueError('source changed')
            record['closure']=p.closure(vraw,braw,bvectors);save()
            print(label,k+1,record['closure'],flush=True)
            if record['closure']['passed']:
                if with_contour:
                    raw=p.assemble(vraw,braw,bvectors,s);m=c.measurement(raw,s);result['measurements']=m
                    if max(m['timing_balance_max_c'],m['output_balance_max_c'])>p.GATES['charge_c']:raise ValueError('charge balance')
                else:
                    result['reference_contrast']=reference_contrast(vraw,braw)
                    if not result['reference_contrast']['passed']:raise ValueError('monolithic control contrast')
                result['passed']=True;save();return (vraw,braw,bvectors)
            bt=braw[:,0];bus=braw[:,1]
        except Exception as e:
            record['error']=str(e)
            for side in ('vco','board'):
                path=work/f'{label}-{k+1:02d}-{side}.json'
                if path.exists():record[side+'_receipt']=vco.read(path)
            save();return None
    result['error']='port closure exhausted frozen iteration budget';save();return None


def main(bank_name='port-relaxation03',port_factory=p.factory):
    work=ROOT/'references-local/voice-circuit'/bank_name
    output=ROOT/'evidence'/('voice_'+bank_name.replace('-','_')+'.json.gz')
    if work.exists() or output.exists():raise ValueError('preserve prior screen')
    report=dict(schema='rf-d/voice-port-screen/v1',bank=work.name,gates=p.GATES,cases={},comparisons={},passed=False,
                physical_fidelity=False,real_time=False,runner_sha256=vco.sha(Path(__file__)))
    def save():output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    control=c.Scenario()
    if solve(control,'fixed-contour-control',False,work,exe,report,save,port_factory) is None:
        report['validation_error']='monolithic control rejected; contour scenes not measured';save();return
    kept={};ss=screen.scenes()
    for label,s in ss.items():
        pair=solve(s,label,True,work,exe,report,save,port_factory)
        if pair is None:
            report['validation_error']='contour scene rejected; remaining scenes not measured';save();return
        kept[label]=p.assemble(*pair,s)
    try:
        for a,b in screen.PAIRS:report['comparisons'][a+'--'+b]=screen.contrast(kept[a],kept[b],ss[a],ss[b])
        report['passed']=True
    except Exception as e:report['validation_error']=str(e)
    save();print('partition screen',report['passed'],flush=True)


if __name__=='__main__':main()
