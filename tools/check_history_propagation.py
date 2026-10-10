"""Independent composed responses, complete fixed calendars and scaled own FD."""
import argparse,json,struct,sys,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_history_tangent import mass,stage_jacobian,ratio,COLS
from check_joint_reference import D
from joint_cycles_analysis import require,TICK,trace
from prepare_history_propagation import OBS

class Reader:
    def __init__(self,path):self.raw=np.memmap(path,dtype='u1',mode='r');self.offset=0
    def bytes(self,n):
        require(self.offset+n<=len(self.raw),'complete codec');a=self.raw[self.offset:self.offset+n].tobytes();self.offset+=n;return a
    def integer(self,kind):return struct.unpack('<'+kind,self.bytes(struct.calcsize('<'+kind)))[0]
    def floats(self,n):
        require(self.offset+8*n<=len(self.raw),'complete float record');a=np.frombuffer(self.raw,dtype='<f8',count=n,offset=self.offset);self.offset+=8*n;require(np.isfinite(a).all(),'finite record');return a
    def end(self):require(self.offset==len(self.raw),'no trailing codec bytes')

def previous_units():
    old=json.loads((ROOT/'evidence/voice_history_tangent_native05.json').read_text());name=next(o['path'] for o in old['outputs'] if o['path'].endswith('/history.bin'));r=Reader(ROOT/name)
    require(r.bytes(8)==b'RFJHIST2' and r.integer('I')==48,'old unit codec');out=[]
    for k in range(48):
        require(r.integer('I')==k,'old unit id');r.floats(1+40000+2*80000+1);columns=[]
        for col in COLS:
            require(r.integer('I')==col,'old unit column');r.floats(1);columns.append(r.floats(400).copy());r.floats(800)
        out.append(np.array(columns).T)
    r.end();return out,name

def decoded(raw):return [D(raw[k])+D(raw[200+k]) for k in range(200)]
def bits(a,b):return np.array_equal(np.asarray(a).view('u8'),np.asarray(b).view('u8'))
def check(native):
    require(native['passed'],'passed native');inputs=json.loads((ROOT/'evidence/voice_history_propagation_inputs01.json').read_text());inp=Reader(ROOT/inputs['path']);require(inp.bytes(8)==b'RFJHPIN1' and inp.integer('I')==12 and inp.integer('I')==64,'input header')
    name=next(o['path'] for o in native['outputs'] if o['path'].endswith('/propagation.bin'));r=Reader(ROOT/name);require(r.bytes(8)==b'RFJHPRO1' and r.integer('I')==48,'output header');units,old_name=previous_units()
    for k in range(48):require(r.integer('I')==k and bits(r.floats(3600).reshape(400,9),units[k]),'batch identical admitted scalar '+str(k))
    require(r.integer('I')==12 and r.integer('I')==64,'window count');records=[];window_reports=[];output_gate=np.tile([1e-11 if 98<=k<133 else 1e-8 for k in range(200)],2);target=np.tile([1e-8 if 98<=k<133 else 1e-5 for k in range(200)],2);base=np.array([1e-10 if 98<=k<133 else 1e-5 for k in COLS]);deadline=time.perf_counter()+900;traces={}
    for wid,window in enumerate(inputs['windows']):
        require(time.perf_counter()<deadline,'reference budget');metadata=[inp.integer('I') for _ in range(3)];start=inp.integer('Q');initial=inp.floats(400);fixtures=[inp.floats(2000).reshape(5,400) for _ in range(2)]
        schedule=[(inp.integer('Q'),inp.integer('I'),inp.floats(7)) for _ in range(64)]
        require([r.integer('I') for _ in range(3)]==metadata==[wid,window['profile'],['first','reset1','reset2'].index(window['location'])],'window metadata');require(r.integer('Q')==start==window['start_ticks'],'start clock');epsilon=r.floats(9);require((epsilon>0).all(),'positive epsilon');old=initial;u=np.eye(200)[:,COLS];last=start;gain=np.ones(9);window_rows=[]
        if window['trace'] not in traces:traces[window['trace']]=trace(ROOT/window['trace'])
        saved_trace=traces[window['trace']][window['start_row']:window['start_row']+64]
        for n,(ticks,half,observed) in enumerate(schedule):
            require(time.perf_counter()<deadline,'reference budget');require(r.integer('Q')==ticks and r.integer('I')==half and ticks-last==half,'exact fixed calendar');last=ticks
            state=r.floats(2000).reshape(5,400);s=r.floats(3600).reshape(400,9);fd=r.floats(7200).reshape(9,2,400);require(bits(old,state[0]),'HIGH/LOW continuity');old=state[4]
            if n<2:require(bits(state,fixtures[n]),'selected increment and candidate seams')
            trace_observations=[float(saved_trace[n][field]) for field,_ in OBS];require(bits(observed,trace_observations),'frozen input trace identity');require(bits([state[4,k]+state[4,200+k] for _,k in OBS],observed),'all endpoint trace bits')
            case=(0,half*TICK,*[decoded(a) for a in state]);m=mass(case[2],case[1]);rhs=np.vstack([2*(m@u),-2*(m@u)]);independent=np.linalg.solve(stage_jacobian(case),rhs);u=independent[200:];require(np.count_nonzero(s[:,8])==np.count_nonzero(independent[:,8])==0,'exact propagated negative control')
            gain=np.maximum(gain,np.max(base[None,:]*np.abs(s)/target[:,None],axis=0));comparisons=[]
            for direction,col in enumerate(COLS):
                e=epsilon[direction];oracle=ratio(e*s[:,direction],e*independent[:,direction],output_gate,1e-4);require(oracle['max_ratio']<=1,'composed independent response '+str((wid,n,col,oracle)))
                finite=[]
                for scale,observed_fd in zip([1.,.5],fd[direction]):
                    result=ratio(scale*e*observed_fd,scale*e*s[:,direction],output_gate,1e-4);require(result['max_ratio']<=1,'own nonlinear histories '+str((wid,n,col,scale,result)));finite.append(result)
                comparisons.append(dict(column=col,independent=oracle,nonlinear_fd=finite))
            row=dict(window=wid,step=n,ticks=ticks,half_ticks=half,responses=comparisons);records.append(row);window_rows.append(row)
        expected=base/gain;require(np.all(np.abs(epsilon-expected)<=1e-15*expected),'whole-window epsilon policy');require(last==window['end_ticks'],'window endpoint')
        window_reports.append(dict(**window,epsilon=list(map(float,epsilon)),max_independent_ratio=max(a['independent']['max_ratio'] for b in window_rows for a in b['responses']),max_nonlinear_fd_ratio=max(c['max_ratio'] for b in window_rows for a in b['responses'] for c in a['nonlinear_fd'])))
        print('PROPAGATION_REFERENCE_WINDOW',wid,flush=True)
    inp.end();r.end();return dict(records=records,windows=window_reports,input_sha256={name:sha(ROOT/name),old_name:sha(ROOT/old_name),inputs['path']:sha(ROOT/inputs['path']),**inputs['private_used_sha256']},baseline_steps=768,response_directions=6912,response_stage_coordinates=2764800,perturbed_native_step_solves=27648,baseline_selected_bit_reproductions=24,baseline_trace_bit_reproductions=768,batched_scalar_bit_coordinates=172800,negative_controls=768,independent_roots=0,fixed_calendar_windows_admitted=True,adaptive_derivative_admitted=False,period_map_admitted=False,event_time_derivative_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)

def main():
    a=argparse.ArgumentParser();a.add_argument('--native',type=int,required=True);a.add_argument('--attempt',type=int,required=True);args=a.parse_args();name=f'evidence/voice_history_propagation_native{args.native:02d}.json';out=f'evidence/voice_history_propagation_reference{args.attempt:02d}.json';require(not (ROOT/out).exists(),'exclusive receipt');native=json.loads((ROOT/name).read_text());names={name,'evidence/voice_history_propagation_inputs01.json','docs/VOZ_PROPAGACION_HISTORIA_PROTOCOLO.md','evidence/voice_history_tangent_reference01.json','evidence/voice_history_tangent_native05.json','tools/check_history_propagation.py'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};report=dict(schema='rf-d/history-propagation-reference/v1',passed=False,source_sha256=before);started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;report.update(check(native))
        report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_history_propagation.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==report['source_sha256_after'],'unchanged reference source');report['wall_s']=time.perf_counter()-started;write(out,report);print('PROPAGATION_REFERENCE',report['passed'],report.get('failure',''),flush=True)
if __name__=='__main__':main()
