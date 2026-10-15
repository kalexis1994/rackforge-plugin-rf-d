pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/nominal_chain_startup.rs"]mod startup;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use startup::*;
use std::{io::{Write,BufWriter},time::Instant,alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
const US:u64=524288;const TICK:f64=125e-9/65536.;
fn chain()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn seed(mode:usize)->Result<State,StepError>{
    let p=chain();let audio=rf_d_circuit::circuit66::initial_state(p.circuit,p.conversion,p.headphone,p.boundary,lab::SEED)?;
    // Numerical off guesses, from loudness_contour_reference.initial_state and c5_trigger_reference.dc_seed.
    let vol=[0.1,-0.5,9.3,-1.,-3.6,0.7,9.2,0.,0.,8.,1.3,0.7,5.,4.,0.6,0.01,0.05,0.05,9.,0.7,0.,0.,0.,0.,0.9,0.,8.7,0.7,0.05];
    let filter=[0.3,8.75,9.25,0.,-2.,0.005,0.52,-9.998,1.39];
    let timer=[0.85,0.01,8.3,0.7,0.03,9.15,0.85,7.6,1.,0.85,0.7,4.8,0.001,5.,0.03,1.1];
    let mut x=[0.;N];x[..29].copy_from_slice(&vol);x[29..38].copy_from_slice(&filter);x[38..54].copy_from_slice(&timer);
    for k in 0..66{if(62..66).contains(&k){continue;}let i=match k{5=>55,32=>54,_=>56+k-(k>5)as usize-(k>32)as usize};x[i]=audio.node_v[k];}
    x[116]=0.;x[117]=audio.node_v[22];if mode==1{for k in 0..54{x[k]+=if k%2==0{0.005}else{-0.005};}}
    Ok(State::new(x,false))
}
fn vals(w:&mut impl Write,a:impl IntoIterator<Item=f64>){for v in a{write!(w,",{v:0.17e}").unwrap();}}
fn state(w:&mut impl Write,s:State){vals(w,s.high.into_iter().chain(s.low));}
fn root(w:&mut impl Write,old:State,p:&Pair,c:Controls,t:f64,h:f64){write!(w,"ROOT,{t:0.17e},{h:0.17e},{}",c.key).unwrap();state(w,old);for s in p.delta.into_iter().chain(p.stages){state(w,s);}vals(w,[p.residual_a,p.correction_v]);writeln!(w).unwrap();}
fn grid(w:&mut impl Write,t:u64,s:State){write!(w,"GRID,{t}").unwrap();vals(w,[s.high[115]+s.low[115],s.high[5]+s.low[5],s.high[38]+s.low[38],s.high[116]+s.low[116]]);vals(w,voice::currents(s));writeln!(w).unwrap();}
fn main()->Result<(),String>{
    let args:Vec<_>=std::env::args().collect();let maximum:u64=args[1].parse().unwrap();assert!([64*US,32*US].contains(&maximum));let p=Parameters::new(chain()).unwrap();let mut out=BufWriter::new(std::io::stdout());let mut initial=None;
    for mode in 0..2{let guess=seed(mode).map_err(|e|format!("BLOCK_SEED:{e:?}"))?;write!(out,"SEED,{mode}").unwrap();state(&mut out,guess);writeln!(out).unwrap();out.flush().unwrap();
        let r=initialize(p,guess,100).map_err(|e|format!("DC mode={mode}:{e:?}"))?;write!(out,"DC,{mode},{}",r.iterations).unwrap();vals(&mut out,[r.residual_a,r.correction_v]);state(&mut out,r.state);writeln!(out).unwrap();out.flush().unwrap();
        if let Some(a)=initial{let a:State=a;assert!((0..N).all(|k|((a.high[k]-r.state.high[k])+(a.low[k]-r.state.low[k])).abs()<=1e-6));}else{initial=Some(r.state);}
    }
    let mut s=initial.unwrap();let mut workspace=Workspace::new();let c0=Controls::default();let saved=s;
    for bad in[f64::NAN,0.,-1.,0.002]{assert!(historical_advance(&mut workspace,p,&mut s,c0,bad).is_err());assert_eq!(s,saved);}assert!(historical_advance(&mut workspace,p,&mut s,Controls{optional:true,..c0},1e-6).is_err());assert_eq!(s,saved);
    let mut ticks=0_u64;let mut proposal=maximum;let mut next_grid=125*US;let mut steps=0;let mut roots=0;let mut replays=0;let mut elapsed=0.;let mut heap=0;let mut max_r=0_f64;let mut max_c=0_f64;let mut max_e=0_f64;let mut min_h=1_f64;grid(&mut out,0,s);
    while ticks<100000*US{let event=if ticks<1000*US{1000*US}else if ticks<75000*US{75000*US}else{100000*US};let edge=event.min(next_grid);let remain=edge-ticks;let span=proposal.min(1_u64<<(63-remain.leading_zeros()));let mut p=p;p.time=ticks as f64*TICK;
        let c=Controls{key:if(1000*US..75000*US).contains(&ticks){10.}else{0.},short:false,optional:false};let old=s;let old_ticks=ticks;let allocations=ALLOCS.load(Ordering::Relaxed);let clock=Instant::now();let result=historical_advance(&mut workspace,p,&mut s,c,span as f64*TICK);elapsed+=clock.elapsed().as_secs_f64();heap+=ALLOCS.load(Ordering::Relaxed)-allocations;
        let q=match result{Ok(q)=>q,Err(e)=>{write!(out,"FAILED,{ticks},{span}").unwrap();state(&mut out,old);writeln!(out).unwrap();out.flush().unwrap();return Err(format!("TRANSIENT ticks={ticks}:{e:?}"));}};
        let actual=(q.h/TICK).round()as u64;assert!(actual>0&&actual<=span);assert_eq!(q.h.to_bits(),(actual as f64*TICK).to_bits());ticks+=actual;steps+=1;min_h=min_h.min(q.h);max_e=max_e.max(q.error);for pair in [&q.coarse,&q.fine[0],&q.fine[1]]{max_r=max_r.max(pair.residual_a);max_c=max_c.max(pair.correction_v);}
        if steps==1||ticks==1000*US||old_ticks==1000*US||ticks==75000*US||old_ticks==75000*US||ticks==100000*US{let mut retry=old;let qq=historical_advance(&mut workspace,p,&mut retry,c,span as f64*TICK).unwrap();assert_eq!(s,retry);assert_eq!(q.h.to_bits(),qq.h.to_bits());assert_eq!(q.error.to_bits(),qq.error.to_bits());replays+=1;root(&mut out,old,&q.coarse,c,p.time,q.h);root(&mut out,old,&q.fine[0],c,p.time,q.h/2.);root(&mut out,q.fine[0].stages[1],&q.fine[1],c,p.time+q.h/2.,q.h/2.);roots+=3;}
        if ticks==1000*US||ticks==75000*US{write!(out,"EVENT,{ticks},{}",if ticks==1000*US{10}else{0}).unwrap();state(&mut out,s);writeln!(out).unwrap();}
        proposal=if q.error<0.05{(2*actual).min(maximum)}else{actual};if ticks==next_grid{grid(&mut out,ticks,s);next_grid+=125*US;}
    }
    assert_eq!(heap,0);write!(out,"FINAL,{ticks},{steps},{roots},{replays},5,{heap}").unwrap();vals(&mut out,[elapsed,min_h,max_r,max_c,max_e]);state(&mut out,s);writeln!(out).unwrap();out.flush().unwrap();Ok(())
}

#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"]mod historical;
struct Workspace{workspace:historical::Workspace,p:historical::Parameters}
impl Workspace{fn new()->Self{Self{workspace:historical::Workspace::new(),p:historical::Parameters::new(chain()).unwrap()}}}
fn new_state(s:historical::State)->State{State{high:s.high,low:s.low,optional:s.optional}}
fn new_pair(p:historical::Pair)->Pair{Pair{delta:p.delta.map(new_state),stages:p.stages.map(new_state),residual_a:p.residual_a,correction_v:p.correction_v,iterations:p.iterations}}
fn historical_advance(w:&mut Workspace,p:Parameters,s:&mut State,c:Controls,h:f64)->Result<Accepted,StepError>{
    let mut state=historical::State{high:s.high,low:s.low,optional:s.optional};let mut pp=w.p;pp.time=p.time;let cc=historical::Controls{key:c.key,short:c.short,optional:c.optional};
    let q=historical::advance(&mut w.workspace,pp,&mut state,cc,h)?;
    *s=new_state(state);Ok(Accepted{coarse:new_pair(q.coarse),fine:q.fine.map(new_pair),h:q.h,error:q.error,attempts:q.attempts})
}
