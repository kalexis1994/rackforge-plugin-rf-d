"""Change integration only, keeping full chain laws and H128 source fixed."""
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
def main():
    names=['tools/prepare_family_filter_sdirk.py','tools/family_filter_kernel.rs','tools/family_filter_probe.rs','tools/check_family_filter_native.py','tools/check_family_filter_reference.py','docs/FAMILIA_FILTRO_RESTRICCIONES.md'];sources=Sources(names)
    s=(ROOT/names[1]).read_text(encoding='utf8');s=s.replace('pub iterations:usize}','pub iterations:usize,pub stage:State}',1).replace('iterations:iteration});','iterations:iteration,stage:s.candidate});',1)
    old='r[k]=a.dc[k]+b.dc[k]+2.*a.charge_over_h[k]';assert s.count(old)==1;s=s.replace(old,'r[k]=a.dc[k]+a.charge_over_h[k]',1).replace('a.dc_jacobian[k][l]+2.*a.mass_over_h[k][l]','a.dc_jacobian[k][l]+a.mass_over_h[k][l]',1).replace('r[BUS]+=q.0+previous.0','r[BUS]+=q.0',1).replace('delta.value(PHASE)-h*0.5*(q.3+previous.3)','delta.value(PHASE)-h*q.3',1).replace('j[PHASE][BUS]=-h*0.5*q.4','j[PHASE][BUS]=-h*q.4',1)
    marker='pub fn process(';s=s[:s.index(marker)]+'''pub const GAMMA:f64=1.-std::f64::consts::FRAC_1_SQRT_2;
pub fn algebraic(p:Parameters,cv:f64,s:State)->Result<f64,StepError>{let a=chain_charge::linearize_compensated(p,[0.;5],s.chain(),Chain::from_nodes([0.;CN]),1e-6)?;Ok(a.dc[6]+a.dc[BUS]+current(cv,s)?)}
pub fn process(p:Parameters,cv:f64,s:&mut State,h:f64,budget:usize)->Result<Accepted,StepError>{
 let old=*s;let first=solve(p,cv,old,GAMMA*h,false,budget)?;
 let difference=first.state.advanced(old.high.map(|x|-x)).advanced(old.low.map(|x|-x));let alpha=(1.-GAMMA)/GAMMA;
 let virtual_history=old.advanced(difference.high.map(|x|alpha*x)).advanced(difference.low.map(|x|alpha*x));
 let mut last=solve(p,cv,virtual_history,GAMMA*h,false,budget)?;
 last.residual_ratio=last.residual_ratio.max(first.residual_ratio);last.correction_ratio=last.correction_ratio.max(first.correction_ratio);last.iterations+=first.iterations;last.stage=first.state;
 if algebraic(p,cv,last.state)?.abs()>1e-13||algebraic(p,cv,first.state)?.abs()>1e-13{return Err(StepError::NoDecrease);}
 *s=last.state;Ok(last)
}
'''
    outputs={'tools/family_filter_sdirk_kernel.rs':s}
    s=(ROOT/names[2]).read_text(encoding='utf8').replace('family_filter_kernel.rs','family_filter_sdirk_kernel.rs',1)
    old='let begin=CALLS.load(Ordering::Relaxed);';assert s.count(old)==1;s=s.replace(old,'let begin=CALLS.load(Ordering::Relaxed);let mut stage_board=0.;',1)
    old='s.value(5),s.value(65)]';assert s.count(old)==1;s=s.replace(old,'s.value(5),s.value(65),stage_board,if steps==0{0.}else{core::algebraic(p,cv,s).unwrap()}]',1)
    old='maxc=maxc.max(q.correction_ratio);steps+=1;';assert s.count(old)==1;s=s.replace(old,'maxc=maxc.max(q.correction_ratio);stage_board=-core::current(cv,q.stage).unwrap()-p.mixer.admittance_s()[5][5]*q.stage.value(BUS);steps+=1;',1);outputs['tools/family_filter_sdirk_probe.rs']=s
    s=(ROOT/names[3]).read_text(encoding='utf8')
    for a,b in [('family_filter_native01.json','family_filter_sdirk_native01.json'),('family_filter_windows01.xz','family_filter_sdirk_windows01.xz'),('check_family_filter_native.py','check_family_filter_sdirk_native.py'),('family_filter_probe.rs','family_filter_sdirk_probe.rs'),('family_filter_kernel.rs','family_filter_sdirk_kernel.rs'),('reshape(-1,9)','reshape(-1,11)')]:s=s.replace(a,b)
    outputs['tools/check_family_filter_sdirk_native.py']=s
    s=(ROOT/names[4]).read_text(encoding='utf8')
    for a,b in [('family_filter_native01.json','family_filter_sdirk_native01.json'),('family_filter_reference01.json','family_filter_sdirk_reference01.json'),('family_filter_reference_failure','family_filter_sdirk_reference_failure'),('check_family_filter_reference.py','check_family_filter_sdirk_reference.py'),('family_filter_tangent_probe.rs','family_filter_sdirk_tangent_probe.rs'),('family_filter_probe.rs','family_filter_sdirk_probe.rs'),('y=y+old_dc+2/h*(M@delta)','y=y+1/h*(M@delta)'),('delta[68]-h*.5*(old_f+freq)','delta[68]-h*freq')]:s=s.replace(a,b)
    outputs['tools/check_family_filter_sdirk_reference.py']=s
    for n,s in outputs.items():
        p=ROOT/n;assert not p.exists();p.write_text(s,encoding='utf8',newline='\n')
    sources.unchanged();write(ROOT/'evidence/family_filter_sdirk_derivation01.json',dict(passed=True,**sources.fields(),generated_sha256={n:sha(ROOT/n) for n in outputs},active_devices_unchanged=True,capacitor_values_unchanged=True,source_h128_unchanged=True,newton_gates_unchanged=True,method='stiffly accurate SDIRK2, BE substage solves'))
if __name__=='__main__':main()
