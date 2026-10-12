"""Archive-based DC/AC control diagnostic. Independent KCL, shared complex solver."""
import argparse,copy,json,os,shutil,struct,subprocess,time,traceback,sys
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from cutoff_j7_vectors import setup
from circuit66_dc_vectors import dc_evaluator
from chain_charge_reference import mass

def compare(a,b,floor,relative,label):
 ratios=abs(a-b)/(floor+relative*abs(b));ratio=float(np.max(ratios));require(ratio<=1,label+' '+str(ratio));return ratio
def audit(matrix_path,archived,frequency):
 raw=matrix_path.read_bytes();require(raw[:8]==b'RFCUTO01' and len(raw)==8+3*(1+68+68+2*68*68)*8,'full native matrix codec');data=np.frombuffer(raw,dtype='<f8',offset=8).reshape(3,-1);require(np.isfinite(data).all(),'finite matrices');values=setup(200);cm=mass();keep=np.array([i for i in range(68) if i!=66]);result=[]
 for row,name,knob in zip(data,['cutoff_min','centre','cutoff_max'],[0.,.5,1.]):
  case=next(c for c in archived['cases'] if c['name']==name and c['r61_ohm']==200);root=np.array([*case['node_v'],0.,case['node_v'][22]]);require(row[0]==knob and np.array_equal(row[1:69].view('<u8'),root.view('<u8')),'archived DC bytes');native_dc=row[69:137];ng=row[137:4761].reshape(68,68);nc=row[4761:].reshape(68,68);require(np.max(abs(native_dc))<=2e-11,'native archived DC gate');c_ratio=compare(nc,cm,1e-16,0.,'incidence mass')
  controls=copy.deepcopy(values[4]);controls['panel']['cutoff_fraction_from_neg10']=knob;core=dc_evaluator(values,controls)
  def dc(x):
   r=np.zeros(68);r[:66]=core(x[:66].tolist())[0];r[:48]*=-1.;i=(x[22]-x[67])/25500.;r[22]+=i;r[67]=-i;return r
  require(np.max(abs(dc(root)))<=2e-11,'independent archived DC gate');derivatives=[];responses=[]
  for epsilon in [1e-6,2e-6]:
   g=np.empty((68,68))
   for k in range(68):
    a=root.copy();b=root.copy();a[k]+=epsilon;b[k]-=epsilon;g[:,k]=(dc(a)-dc(b))/(2*epsilon)
   derivatives.append(dict(epsilon_v=epsilon,matrix_ratio=compare(ng,g,1e-10,1e-4,'DC derivative')))
   for harmonic in [1,2,4,8]:
    f=frequency*harmonic;s=2j*np.pi*f;operators=[ng+s*nc,g+s*cm];states=[];admittances=[];residuals=[]
    for m in operators:
     v=np.ones(68,dtype=complex);v[keep]=np.linalg.solve(m[np.ix_(keep,keep)],-m[keep,66]);residual=float(np.max(abs((m@v)[keep])));require(residual<=1e-11,'complex KCL');states.append(v);admittances.append((m@v)[66]);residuals.append(residual)
    ratio=compare(states[0],states[1],1e-10,5e-4,'AC voltage');yr=compare(np.array(admittances[:1]),np.array(admittances[1:]),1e-10,5e-4,'input admittance');j7=states[0][61];cap_currents= s*nc@states[0]
    responses.append(dict(epsilon_v=epsilon,harmonic=harmonic,frequency_hz=f,j7_v_per_bus_v=[float(j7.real),float(j7.imag)],j7_magnitude_v_per_bus_v=float(abs(j7)),input_admittance_s=[float(admittances[0].real),float(admittances[0].imag)],voltage_comparison_ratio=ratio,admittance_comparison_ratio=yr,residuals_a_per_bus_v=residuals,maximum_capacitor_nodal_current_a_per_bus_v=float(np.max(abs(cap_currents)))))
  result.append(dict(name=name,cutoff_fraction=knob,tail_current_a=case['tail_current_a'],native_dc_max_a=float(np.max(abs(native_dc))),mass_matrix_ratio=c_ratio,derivatives=derivatives,responses=responses))
 return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args();out=ROOT/f'evidence/voice_cutoff_opening{args.attempt:02d}.json';work=ROOT/f'references-local/cutoff-opening{args.attempt:02d}';require(not out.exists() and not work.exists(),'exclusive probe');old=json.loads((ROOT/'evidence/voice_dynamic_direction_tests01.json').read_text(encoding='utf8'));archive_name='evidence/circuit66_dc_vectors.json';archive=json.loads((ROOT/archive_name).read_text(encoding='utf8'));require(sha(ROOT/archive_name)==old['source_sha256'][archive_name],'archived DC identity');lib='references-local/joint-startup01/librf_d_circuit.rlib';require(sha(ROOT/lib)==old['private_input_sha256'][lib],'library identity');compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler identity');frequency=1/json.loads((ROOT/'evidence/voice_dynamic_direction_reference01.json').read_text(encoding='utf8'))['candidate']['period_s']
 names={'tools/probe_cutoff_opening.py','tools/cutoff_opening_runner.rs','docs/VOZ_APERTURA_CUTOFF_PROTOCOLO.md',archive_name,'evidence/voice_dynamic_direction_reference01.json','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs'}
 for module in list(sys.modules.values()):
  f=getattr(module,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/cutoff-opening/v1',passed=False,source_sha256=before,private_used_sha256={lib:sha(ROOT/lib)},compiler=compiler,commands=[],frequency_hz=frequency,rows=[],reserve_bytes=1024**3,estimated_output_bytes=8*1024**2,initial_free_bytes=shutil.disk_usage(ROOT).free,new_library_compile=False,new_trajectories=0,new_roots=0,new_audio=False,new_spice_processes=0,ideal_bus_small_signal=True,shared_complex_solver=True,physical_fidelity=False,real_time=False);start=time.perf_counter()
 def save():out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
 try:
  require(r['initial_free_bytes']>=r['reserve_bytes']+r['estimated_output_bytes'],'disk reserve');work.mkdir();inp=work/'inputs.bin'
  with inp.open('xb') as file:
   file.write(b'RFCUTI01')
   for name,knob in [('cutoff_min',0.),('centre',.5),('cutoff_max',1.)]:
    c=next(c for c in archive['cases'] if c['name']==name and c['r61_ohm']==200);file.write(struct.pack('<69d',knob,*c['node_v'],0.,c['node_v'][22]))
  r['initial_input_sha256']=sha(inp);exe=work/'run.exe';matrix=work/'matrices.bin';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432'
  for cmd in [[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/cutoff_opening_runner.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)],[str(exe),str(inp),str(matrix)]]:
   t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);r['commands'].append(dict(command=cmd,exit_code=p.returncode,wall_s=time.perf_counter()-t,stdout=p.stdout,stderr=p.stderr));save();require(p.returncode==0,'native command')
  t=time.perf_counter();r['rows']=audit(matrix,archive,frequency);r['reference_wall_s']=time.perf_counter()-t;require(r['reference_wall_s']<=120 and time.perf_counter()-start<=480,'probe budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
  if (work/'matrices.bin').exists():
   try:audit(work/'matrices.bin',archive,frequency);r['replay']='unexpected pass'
   except Exception:r['replay']=traceback.format_exc()
  elif r['commands']:
   cmd=r['commands'][-1]['command'];p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);r['replay']=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
 r['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==r['source_sha256_after'],'unchanged probe sources');r['private_used_sha256_after']={n:sha(ROOT/n) for n in r['private_used_sha256']};require(r['private_used_sha256']==r['private_used_sha256_after'],'unchanged library');r['wall_s']=time.perf_counter()-start;r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()];r['final_free_bytes']=shutil.disk_usage(ROOT).free;save();print('CUTOFF_OPENING',r['passed'],r.get('failure',''),[(x['cutoff_fraction'],x['responses'][0]['j7_magnitude_v_per_bus_v']) for x in r['rows']],flush=True)
if __name__=='__main__':main()
