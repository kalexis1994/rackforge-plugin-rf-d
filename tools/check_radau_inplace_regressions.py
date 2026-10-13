"""Full stamp identity, rejection order, scratch recovery and reference swapping."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
from schur_refined_native import experiment
MAIN='''macro_rules! setup{($name:ident,$m:ident)=>{fn $name(c:&Case)->($m::Parameters,$m::State,[$m::State;2]){
 let(mut a,b,d)=lab::lab_parameters();a.r61_ohm=200.;let mut chain=Chain{circuit:a,conversion:b,headphone:d,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};chain.boundary.panel.cutoff_fraction_from_neg10=1.;let mut p=$m::Parameters::new(Controls::default(),chain,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap();p.final_decay=c.on;p.keyboard=[0.,10.,0.][c.phase];p.short=c.phase==1;
 let state=|s:usize|$m::State{high:std::array::from_fn(|k|c.states[s][k]),low:std::array::from_fn(|k|c.states[s][k+229])};(p,state(0),[state(1),state(2)])
}}}
setup!(base_input,reference);setup!(input,reuse);
fn equal(a:&reference::Stamp,b:&reuse::Stamp){
 for i in 0..458{assert_eq!(a.residual[i].to_bits(),b.residual[i].to_bits(),"residual {i}");for k in 0..458{assert_eq!(a.jacobian[i][k].to_bits(),b.jacobian[i][k].to_bits(),"matrix {i},{k}");}}
 for i in 0..2{assert_eq!(a.candidates[i].high.map(f64::to_bits),b.candidates[i].high.map(f64::to_bits));assert_eq!(a.candidates[i].low.map(f64::to_bits),b.candidates[i].low.map(f64::to_bits));}
}
#[inline(never)]fn complete(c:&Case){let(p,o,d)=base_input(c);let a=reference::linearize(p,o,d,c.h).unwrap();let(p,o,d)=input(c);let mut b=reuse::Stamp::blank();b.initialize(p,o,d,c.h).unwrap();equal(&a,&b);let facade=reuse::linearize(p,o,d,c.h).unwrap();equal(&a,&facade);}
#[inline(never)]fn reinitialize(a:&Case,b:&Case){
 let mut s=reuse::Stamp::blank();for c in [a,b,a]{let(p,o,d)=input(c);s.initialize(p,o,d,c.h).unwrap();let(p,o,d)=base_input(c);equal(&reference::linearize(p,o,d,c.h).unwrap(),&s);}println!("ASSEMBLY,reinitialize_A_B_A");
 s.residual.fill(f64::NAN);for row in &mut s.jacobian{row.fill(f64::NAN);}for c in &mut s.candidates{c.high.fill(f64::NAN);c.low.fill(f64::NAN);}let(p,o,d)=input(a);s.initialize(p,o,d,a.h).unwrap();let(p,o,d)=base_input(a);equal(&reference::linearize(p,o,d,a.h).unwrap(),&s);println!("ASSEMBLY,poisoned_destination_replaced");
}
#[inline(never)]fn rejection(c:&Case,kind:usize){
 let(p,o,d)=input(c);let mut s=reuse::Stamp::blank();s.initialize(p,o,d,c.h).unwrap();let(pa,oa,da)=base_input(c);let original=reference::linearize(pa,oa,da,c.h).unwrap();
 let(mut p,mut d,mut h)=(p,d,c.h);let(mut pa,mut da,mut ha)=(pa,da,c.h);
 let label=match kind{0=>{h=0.;ha=0.;"zero_dt"},1=>{h=-c.h;ha=-c.h;"negative_dt"},2=>{h=f64::NAN;ha=f64::NAN;"nan_dt"},3=>{p.keyboard=11.;pa.keyboard=11.;"invalid_keyboard"},4=>{d[0].high[225]=1e6;da[0].high[225]=1e6;assert!(reference::parts(pa,oa,da[0],ha).is_err());assert!(reference::parts(pa,oa,da[1],ha).is_ok());"first_stage_error"},_=>{d[1].high[225]=1e6;da[1].high[225]=1e6;assert!(reference::parts(pa,oa,da[0],ha).is_ok());assert!(reference::parts(pa,oa,da[1],ha).is_err());"second_stage_error"}};
 let expected=reference::linearize(pa,oa,da,ha).err().unwrap();let actual=s.initialize(p,o,d,h).err().unwrap();assert_eq!(format!("{expected:?}"),format!("{actual:?}"));equal(&original,&s);let(p,o,d)=input(c);s.initialize(p,o,d,c.h).unwrap();equal(&original,&s);println!("ASSEMBLY,{label},atomic_and_recovered");
}
#[inline(never)]fn references(a:&Case,b:&Case){
 let mut first=reuse::Stamp::blank();let mut second=reuse::Stamp::blank();let(mut current,mut trial)=(&mut first,&mut second);let current_pointer=current as *mut _ as usize;let trial_pointer=trial as *mut _ as usize;
 let(p,o,d)=input(a);current.initialize(p,o,d,a.h).unwrap();let(mut p,o,d)=input(b);p.keyboard=f64::NAN;assert!(trial.initialize(p,o,d,b.h).is_err());let(p,o,d)=base_input(a);equal(&reference::linearize(p,o,d,a.h).unwrap(),current);assert_eq!(current as *mut _ as usize,current_pointer);println!("ASSEMBLY,rejected_trial_preserves_current");
 let(p,o,d)=input(b);trial.initialize(p,o,d,b.h).unwrap();std::mem::swap(&mut current,&mut trial);assert_eq!(current as *mut _ as usize,trial_pointer);assert_eq!(trial as *mut _ as usize,current_pointer);let(p,o,d)=base_input(b);equal(&reference::linearize(p,o,d,b.h).unwrap(),current);let(p,o,d)=base_input(a);equal(&reference::linearize(p,o,d,a.h).unwrap(),trial);println!("ASSEMBLY,accepted_reference_swap");
}
fn main(){let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),84);for c in &cs{complete(c);}println!("ASSEMBLY,84_complete_stamps_and_facade");reinitialize(&cs[0],&cs[83]);for k in 0..6{rejection(&cs[0],k);}references(&cs[0],&cs[83]);println!("ASSEMBLY_PASSED,11,84,17620176,38472,76944");}
'''

def validate(work,q):
    lines=q['stdout'].splitlines();require(lines[-1]=='ASSEMBLY_PASSED,11,84,17620176,38472,76944' and len([x for x in lines if x.startswith('ASSEMBLY,')])==11,'complete assembly/recovery scope')
    return dict(regressions=11,complete_stamps=84,jacobian_bit_coordinates=84*458*458,residual_bit_coordinates=84*458,candidate_high_low_bit_coordinates=84*2*458,compatible_facade_identical=True,first_and_second_stage_error_order_preserved=True,successful_and_failed_workspace_reuse=True,reference_swapping_verified=True,full_trajectory_admitted=False)

def main():
    text=(ROOT/'tools/radau_inplace_bench.rs').read_text(encoding='utf8').split('fn main(){')[0]
    for n in ['joint_lu_extent_kernel.rs','joint_schur_chain_kernel.rs','joint_radau_inplace_kernel.rs']:text=text.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=text.replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix())
    experiment('radauinplacestructure01',text+MAIN,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin'],['tools/check_radau_inplace_regressions.py','tools/radau_inplace_bench.rs','tools/joint_radau_inplace_kernel.rs','tools/joint_schur_chain_kernel.rs','tools/dynamic_schur_chain_solver.rs','docs/RADAU_EN_SITIO_PROTOCOLO.md'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate,replay=True,timeout=120)
if __name__=='__main__':main()
