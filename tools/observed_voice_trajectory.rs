pub use rf_d_circuit::{junction_charge,StepError,vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton,block_decay_voice};
#[path="../crates/rf-d-circuit/src/observed_voice.rs"] mod voice;
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use voice::*;
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer};
use std::{fs,io::{Write,BufWriter},time::Instant};
fn scene()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn vals(w:&mut impl Write,x:impl IntoIterator<Item=f64>){for v in x{write!(w,",{v:.17e}").unwrap();}}
fn state(w:&mut impl Write,s:State){vals(w,s.high.into_iter().chain(s.low));}
fn root(w:&mut impl Write,old:State,q:&Pair,p:Parameters,h:f64){write!(w,"ROOT,{h:.17e},{}",p.key).unwrap();for s in [old,q.delta[0],q.delta[1],q.stages[0],q.stages[1]]{state(w,s);}vals(w,[q.residual_ratio,q.correction_ratio,bus_balance(q,h)]);writeln!(w).unwrap();}
fn main()->Result<(),String>{
    let args:Vec<_>=std::env::args().collect();let bytes=fs::read(&args[1]).map_err(|e|e.to_string())?;if bytes.len()!=8*118{return Err("seed".into());}
    let dual:[f64;118]=std::array::from_fn(|k|f64::from_le_bytes(bytes[8*k..8*k+8].try_into().unwrap()));let vco=rf_d_circuit::vco1_startup::startup(rf_d_circuit::vco1_stamp::Controls::default()).map_err(|e|format!("seed VCO:{e:?}"))?.nodes;
    let mut seed=State::new([0.;N]);for k in 0..134{if let Some(i)=vi(k){seed.high[i]=vco[k];}}for k in 0..118{if k!=116{seed.high[di(k)]=dual[k];}}
    let maximum:u32=args[2].parse().unwrap();let duration:u64=args[4].parse().unwrap();let gate_end:u64=args[5].parse().unwrap();let started=Instant::now();let p=scene();let init=initial(p,seed).map_err(|e|format!("DC:{e:?}"))?;let mut s=init.state;
    let mut w=BufWriter::new(std::io::stdout());write!(w,"DC,{},",init.iterations).unwrap();write!(w,"{:.17e},{:.17e},{:.17e}",init.forcing_a,init.residual_ratio,init.correction_ratio).unwrap();state(&mut w,s);writeln!(w).unwrap();
    let mut workspace=Workspace::new();let initial_state=s;
    for ticks in [0,3,1<<30]{assert!(advance(&mut workspace,p,&mut s,ticks).is_err());assert_eq!(s,initial_state);}
    let mut invalid=p;invalid.key=f64::NAN;assert!(advance(&mut workspace,invalid,&mut s,8).is_err());assert_eq!(s,initial_state);
    let mut ticks=0_u64;let max=2*maximum;let mut proposal=max;let mut steps=0;let mut roots=0;let mut bus=0_f64;
    let unit=524288_u64;let end=duration*unit;let mut grid=125*unit;
    while ticks<end{
        let event=[1000,gate_end,duration].into_iter().map(|v|v*unit).find(|&t|t>ticks).unwrap();let target=grid.min(event);let remaining=target-ticks;
        let span=proposal.min(1_u32<<(63-remaining.leading_zeros()));let mut p=p;p.key=if ticks>=1000*unit&&ticks<gate_end*unit{10.}else{0.};let old=s;
        let q=advance(&mut workspace,p,&mut s,span).map_err(|e|format!("TRANSIENT ticks={ticks} steps={steps} error={e:?}"))?;let elapsed=q.full_ticks;ticks+=u64::from(elapsed);steps+=1;
        bus=bus.max(bus_balance(&q.fine[0],elapsed as f64*rf_d_circuit::vco1_engine::TICK_S/2.).abs()).max(bus_balance(&q.fine[1],elapsed as f64*rf_d_circuit::vco1_engine::TICK_S/2.).abs());
        if steps==1 || ticks==event || ticks==end{
            let h=elapsed as f64*rf_d_circuit::vco1_engine::TICK_S;root(&mut w,old,&q.coarse,p,h);root(&mut w,old,&q.fine[0],p,h/2.);root(&mut w,q.fine[0].stages[1],&q.fine[1],p,h/2.);roots+=3;
            if steps==1{
                let a=parts(p,old,q.coarse.delta[0],h).unwrap();let b=parts(p,old,q.coarse.delta[1],h).unwrap();let j:[[f64;M];M]=std::array::from_fn(|k|std::array::from_fn(|l|B[k/N][l/N]*if l/N==0{a.mass_over_h[k%N][l%N]}else{b.mass_over_h[k%N][l%N]}+if k/N==l/N{if k/N==0{a.dc_jacobian[k%N][l%N]}else{b.dc_jacobian[k%N][l%N]}}else{0.}));
                let rhs:[f64;M]=std::array::from_fn(|k|-(if k/N==0{a.dc[k%N]}else{b.dc[k%N]}+B[k/N][0]*a.charge_over_h[k%N]+B[k/N][1]*b.charge_over_h[k%N]));
                let observed=solver::Workspace::new().solve_observed(&j,rhs).unwrap();let mut binary=fs::File::create(&args[3]).unwrap();for v in j.into_iter().flatten().chain(rhs).chain(observed.correction){binary.write_all(&v.to_le_bytes()).unwrap();}writeln!(w,"LINEAR,{},{:.17e},{:.17e}",observed.refinements,observed.initial_backward,observed.final_backward).unwrap();
            }
        }
        proposal=if q.error<0.05{(2*elapsed).min(max)}else{elapsed};
        if ticks==grid{write!(w,"GRID,{ticks}").unwrap();state(&mut w,s);vals(&mut w,loads(s));writeln!(w).unwrap();grid+=125*unit;}
    }
    assert!(bus<=2e-11);write!(w,"FINAL,{ticks},{steps},{roots},4").unwrap();vals(&mut w,[started.elapsed().as_secs_f64(),bus]);state(&mut w,s);writeln!(w).unwrap();w.flush().unwrap();Ok(())
}
