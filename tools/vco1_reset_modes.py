"""Frozen local descriptor modes; shift reconstruction and Decimal100 residuals."""
import argparse,json,sys,time
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
import vco1_increment_circuit as circuit
from vco1_newton_reference import ROOT,sha

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 out=ROOT/f'evidence/voice_vco1_reset_modes{a:02d}.json'
 if out.exists():raise ValueError('preserve descriptor attempt')
 parent=json.loads((ROOT/'evidence/voice_vco1_sdirk_probe01.json').read_text());names=set(parent['source_sha256'])|{'tools/vco1_reset_modes.py','docs/VCO1_POLOS_RESET_PROTOCOLO.md','docs/VCO1_POLOS_RESET_NORMALIZACION.md','evidence/voice_vco1_reset_modes01.json','evidence/voice_vco1_sdirk_probe01.json'};before={n:sha(ROOT/n) for n in names};sdirk=np.memmap(ROOT/parent['coverage']['path'],dtype='<f8').reshape(-1,542);grid=json.loads((ROOT/'evidence/voice_vco1_reset_grid02.json').read_text());euler=np.memmap(ROOT/grid['failed_export']['path'],dtype='<f8').reshape(-1,274);first=list(map(float,(ROOT/'evidence/voice_vco1_increment_floor_history01.txt').read_text().split()));histories=[first,euler[-1,6:].tolist(),sdirk[-1,6:274].tolist()];c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)];inv=circuit.inventory(circuit.scenario(c));scales=np.r_[np.ones(98),np.full(36,.001)];private={parent['coverage']['path']:parent['coverage']['sha256'],grid['failed_export']['path']:grid['failed_export']['sha256'],circuit.op.MODEL:sha(ROOT/circuit.op.MODEL)}
 r=dict(passed=False,schema='rf-d/local-descriptor-reset-modes/v1',source_sha256=before,private_input_sha256=private,numpy_version=np.__version__,python_version=sys.version,python_sha256=sha(Path(sys.executable)),scenes=[],unchanged_replays=[],new_spice_processes=0,new_audio=False,production_kernel_changed=False,nominal_isolated_l3_over_rl3_s=1e-15,not_an_eigenvalue_enclosure=True,residual_normalization='equilibrated pencil row norm times scaled vector infinity norm',different_criterion_from_attempt01=True)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save();start=time.perf_counter()
 with localcontext() as ctx:
  ctx.prec=100
  for scene,values in enumerate(histories):
   x=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(values[:134],values[134:])];f,g,ground=circuit.reference_decimal(x,x,0.,c);dt=1e-12;ff,j,gg=circuit.reference_decimal(x,x,dt,c);m=[[(a-b)*Decimal.from_float(dt) for a,b in zip(ja,ga)] for ja,ga in zip(j,g)];gf=np.array(g,dtype=float);mf=np.array(m,dtype=float);row=dict(scene=scene,previous_high=values[:134],previous_low=values[134:],dc_jacobian_decimal=[[str(v) for v in a] for a in g],charge_jacobian_decimal=[[str(v) for v in a] for a in m],shifts=[],matches=[]);r['scenes'].append(row);save()
   for dt in (1e-15,1e-12,1e-9):
    a=(gf+mf/dt)*scales[None,:];b=(mf/dt)*scales[None,:];rowscale=np.max(np.abs(a),axis=1);transition=np.linalg.solve(a/rowscale[:,None],b/rowscale[:,None]);mu,vectors=np.linalg.eig(transition);shift=dict(dt_s=dt,condition=float(np.linalg.cond(a/rowscale[:,None])),candidates=[]);row['shifts'].append(shift)
    for k,value in enumerate(mu):
     if abs(value)<1e-10:continue
     lam=(1-1/value)/dt
     if not np.isfinite(lam):continue
     vector=vectors[:,k]*scales;lr,li=Decimal.from_float(float(lam.real)),Decimal.from_float(float(lam.imag));vr=[Decimal.from_float(float(v.real)) for v in vector];vi=[Decimal.from_float(float(v.imag)) for v in vector];maxres=Decimal(0);componentwise=Decimal(0);vmax=Decimal.from_float(float(np.max(np.abs(vectors[:,k].real)+np.abs(vectors[:,k].imag))))
     for gr,mr in zip(g,m):
      real=sum((q+lr*z)*v-li*z*w for q,z,v,w in zip(gr,mr,vr,vi));imag=sum((q+lr*z)*w+li*z*v for q,z,v,w in zip(gr,mr,vr,vi));den=sum((abs(q)+(abs(lr)+abs(li))*abs(z))*(abs(v)+abs(w)) for q,z,v,w in zip(gr,mr,vr,vi))
      if den:componentwise=max(componentwise,(abs(real)+abs(imag))/den)
      norm=sum((abs(q)+(abs(lr)+abs(li))*abs(z))*Decimal.from_float(float(scale)) for q,z,scale in zip(gr,mr,scales))*vmax
      if norm:maxres=max(maxres,(abs(real)+abs(imag))/norm)
     if maxres>Decimal.from_float(1e-8):continue
     dominant=int(np.argmax(np.abs(vectors[:,k])));shift['candidates'].append(dict(lambda_real_s=float(lam.real),lambda_imag_s=float(lam.imag),relative_pencil_residual=float(maxres),old_componentwise_residual=float(componentwise),dominant_index=dominant,dominant_name=inv['names'][dominant],vector_real=list(map(float,vector.real)),vector_imag=list(map(float,vector.imag))))
    print('Modes scene',scene,'dt',dt,'candidates',len(shift['candidates']),flush=True);save()
   for candidate in row['shifts'][1]['candidates']:
    lam=complex(candidate['lambda_real_s'],candidate['lambda_imag_s']);mates=[]
    for shift in (row['shifts'][0],row['shifts'][2]):
     if not shift['candidates']:break
     mate=min(shift['candidates'],key=lambda v:abs(complex(v['lambda_real_s'],v['lambda_imag_s'])-lam));distance=abs(complex(mate['lambda_real_s'],mate['lambda_imag_s'])-lam)/max(abs(lam),1.)
     if distance>1e-3:break
     mates.append(dict(dt_s=shift['dt_s'],relative_distance=distance))
    if len(mates)==2:row['matches'].append(dict(lambda_real_s=lam.real,lambda_imag_s=lam.imag,relative_pencil_residual=candidate['relative_pencil_residual'],dominant_index=candidate['dominant_index'],dominant_name=candidate['dominant_name'],other_shifts=mates))
   row['matches'].sort(key=lambda v:abs(complex(v['lambda_real_s'],v['lambda_imag_s'])),reverse=True);print('Matched scene',scene,len(row['matches']),'fastest',row['matches'][:2],flush=True);save()
 original=json.loads((ROOT/'evidence/voice_vco1_reset_modes01.json').read_text());r['descriptor_identical_to_attempt01']=all(a['dc_jacobian_decimal']==b['dc_jacobian_decimal'] and a['charge_jacobian_decimal']==b['charge_jacobian_decimal'] for a,b in zip(r['scenes'],original['scenes']))
 r.update(passed=r['descriptor_identical_to_attempt01'],source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start);r['passed']=r['passed'] and before==r['source_sha256_after'] and private==r['private_input_sha256_after'];save();print('Local descriptor analysis',r['passed'],flush=True)
if __name__=='__main__':main()
