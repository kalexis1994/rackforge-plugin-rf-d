pub use rf_d_circuit::{junction_charge,StepError};
#[path="../crates/rf-d-circuit/src/active_nominal_voice.rs"]mod circuit;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use circuit::*;
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer};
use std::{fs,io::{Write,BufWriter},time::Instant,alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter {
    unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}
    unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}
    unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}
}
#[global_allocator] static ALLOCATOR:Counter=Counter;
const US:u64=524288;const TICK:f64=125e-9/65536.;
fn scene()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn vals(w:&mut impl Write,a:impl IntoIterator<Item=f64>){for v in a{write!(w,",{v:.17e}").unwrap();}}
fn state(w:&mut impl Write,s:State){vals(w,s.high.into_iter().chain(s.low));}
fn grid(w:&mut impl Write,t:u64,s:State){write!(w,"GRID,{t}").unwrap();vals(w,[s.high[115]+s.low[115],s.high[5]+s.low[5],s.high[38]+s.low[38],s.high[116]+s.low[116]]);vals(w,currents(s));writeln!(w).unwrap();}
fn root(w:&mut impl Write,old:State,q:&Pair,c:Controls,t:f64,h:f64){
    write!(w,"ROOT,{t:.17e},{h:.17e},{}",c.key).unwrap();state(w,old);
    for s in q.delta.into_iter().chain(q.stages){state(w,s);}vals(w,[q.residual_a,q.correction_v]);writeln!(w).unwrap();
}
type Workspace=circuit::Workspace;
fn step(w:&mut Workspace,p:Parameters,s:&mut State,c:Controls,h:f64)->Result<Accepted,StepError>{
    circuit::advance(w,p,s,c,h)
}
fn main()->Result<(),String>{
    let mut workspace=Workspace::new();
    let args:Vec<_>=std::env::args().collect();let bytes=fs::read(&args[1]).map_err(|e|e.to_string())?;
    if bytes.len()!=16*N{return Err("seed".into());}
    let all:[f64;M]=std::array::from_fn(|k|f64::from_le_bytes(bytes[8*k..8*k+8].try_into().unwrap()));
    let mut s=State{high:std::array::from_fn(|k|all[k]),low:std::array::from_fn(|k|all[N+k]),optional:false};assert!(s.valid());
    let maximum:u64=args[2].parse().unwrap();assert!([64*US,32*US].contains(&maximum));
    let p=scene();let mut w=BufWriter::new(std::io::stdout());let mut ticks=40000*US;
    let mut p0=p;p0.time=ticks as f64*TICK;let c0=Controls{key:10.,short:false,optional:false};let saved=s;
    for bad in [f64::NAN,0.,-1.,0.002]{assert!(step(&mut workspace,p0,&mut s,c0,bad).is_err());assert_eq!(s,saved);}
    assert!(step(&mut workspace,p0,&mut s,Controls{optional:true,..c0},maximum as f64*TICK).is_err());assert_eq!(s,saved);
    grid(&mut w,ticks,s);let mut next_grid=ticks+125*US;let mut proposal=maximum;let mut steps=0;let mut roots=0;let mut replays=0;
    let mut elapsed=0.;let mut heap=0;let mut max_r=0_f64;let mut max_corr=0_f64;let mut max_error=0_f64;let mut min_h=1_f64;
    while ticks<100000*US {
        let event=if ticks<75000*US{75000*US}else{100000*US};let edge=event.min(next_grid);let remain=edge-ticks;
        let span=proposal.min(1_u64<<(63-remain.leading_zeros()));let time=ticks as f64*TICK;let mut p=p;p.time=time;
        let c=Controls{key:if ticks<75000*US{10.}else{0.},short:false,optional:false};let old=s;let old_ticks=ticks;
        let count=ALLOCS.load(Ordering::Relaxed);let start=Instant::now();let result=step(&mut workspace,p,&mut s,c,span as f64*TICK);
        elapsed+=start.elapsed().as_secs_f64();heap+=ALLOCS.load(Ordering::Relaxed)-count;
        let q=match result{Ok(q)=>q,Err(e)=>{write!(w,"FAILED,{ticks},{span}").unwrap();state(&mut w,old);writeln!(w).unwrap();w.flush().unwrap();return Err(format!("TRANSIENT ticks={ticks} error={e:?}"));}};
        let actual=(q.h/TICK).round() as u64;assert_eq!(q.h.to_bits(),(actual as f64*TICK).to_bits());assert!(actual>0&&actual<=span);
        ticks+=actual;steps+=1;min_h=min_h.min(q.h);max_error=max_error.max(q.error);
        for z in [&q.coarse,&q.fine[0],&q.fine[1]]{max_r=max_r.max(z.residual_a);max_corr=max_corr.max(z.correction_v);}
        if steps==1||ticks==75000*US||old_ticks==75000*US||ticks==100000*US {
            let mut retry=old;let qq=step(&mut workspace,p,&mut retry,c,span as f64*TICK).unwrap();assert_eq!(s,retry);assert_eq!(q.h.to_bits(),qq.h.to_bits());assert_eq!(q.error.to_bits(),qq.error.to_bits());replays+=1;
            root(&mut w,old,&q.coarse,c,time,q.h);root(&mut w,old,&q.fine[0],c,time,q.h/2.);
            root(&mut w,q.fine[0].stages[1],&q.fine[1],c,time+q.h/2.,q.h/2.);roots+=3;
        }
        proposal=if q.error<0.05{(2*actual).min(maximum)}else{actual};
        if ticks==next_grid{grid(&mut w,ticks,s);next_grid+=125*US;}
    }
    {let z=workspace.statistics;write!(w,"SOLVER,{},{},{}",z.solves,z.refinements,z.max_nonzeros).unwrap();vals(&mut w,[z.max_initial_backward,z.max_final_backward]);writeln!(w).unwrap();}
    #[cfg(timings)] {write!(w,"PROFILE").unwrap();for n in workspace.profile{write!(w,",{n}").unwrap();}writeln!(w).unwrap();}
    assert_eq!(heap,0);write!(w,"FINAL,{ticks},{steps},{roots},{replays},5,{heap}").unwrap();vals(&mut w,[elapsed,min_h,max_r,max_corr,max_error]);state(&mut w,s);writeln!(w).unwrap();w.flush().unwrap();Ok(())
}
