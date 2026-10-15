pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/j7_audio_readout.rs"]mod readout;
use readout::startup;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use startup::*;
use std::{io::{Write,BufWriter},time::Instant,alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
const US:u64=524288;const TICK:f64=125e-9/65536.;
fn chain()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn seed(mode:usize)->Result<State,StepError>{startup::numerical_guess(chain(),mode)}
fn vals(w:&mut impl Write,a:impl IntoIterator<Item=f64>){for v in a{write!(w,",{v:0.17e}").unwrap();}}
fn state(w:&mut impl Write,s:State){vals(w,s.high.into_iter().chain(s.low));}
fn root(w:&mut impl Write,old:State,p:&Pair,c:Controls,t:f64,h:f64){write!(w,"ROOT,{t:0.17e},{h:0.17e},{}",c.key).unwrap();state(w,old);for s in p.delta.into_iter().chain(p.stages){state(w,s);}vals(w,[p.residual_a,p.correction_v]);writeln!(w).unwrap();}
fn grid(w:&mut impl Write,t:u64,s:State){write!(w,"GRID,{t}").unwrap();vals(w,[s.high[115]+s.low[115],s.high[5]+s.low[5],s.high[38]+s.low[38],s.high[116]+s.low[116]]);vals(w,voice::currents(s));writeln!(w).unwrap();}
fn main()->Result<(),String>{
    let args:Vec<_>=std::env::args().collect();let maximum:u64=args[1].parse().unwrap();assert!([32*US,8*US,4*US,2*US,US].contains(&maximum));let p=Parameters::new(chain()).unwrap();let mut out=BufWriter::new(std::io::stdout());let mut initial=None;
    for mode in 0..2{let guess=seed(mode).map_err(|e|format!("BLOCK_SEED:{e:?}"))?;write!(out,"SEED,{mode}").unwrap();state(&mut out,guess);writeln!(out).unwrap();out.flush().unwrap();
        let r=(if mode==0{startup::cold_start(chain())}else{initialize(p,guess,100)}).map_err(|e|format!("DC mode={mode}:{e:?}"))?;write!(out,"DC,{mode},{}",r.iterations).unwrap();vals(&mut out,[r.residual_a,r.correction_v]);state(&mut out,r.state);writeln!(out).unwrap();out.flush().unwrap();
        if let Some(a)=initial{let a:State=a;assert!((0..N).all(|k|((a.high[k]-r.state.high[k])+(a.low[k]-r.state.low[k])).abs()<=1e-6));}else{initial=Some(r.state);}
    }
    let mut s=initial.unwrap();let mut audio=readout::Buffer::<4801>::new(s).unwrap();let mut readout_rejections=0;let mut readout_replays=0;let mut workspace=Workspace::new();let c0=Controls::default();let saved=s;
    for bad in[f64::NAN,0.,-1.,0.002]{assert!(voice::advance(&mut workspace,p,&mut s,c0,bad).is_err());assert_eq!(s,saved);}assert!(voice::advance(&mut workspace,p,&mut s,Controls{optional:true,..c0},1e-6).is_err());assert_eq!(s,saved);
    let mut ticks=0_u64;let mut proposal=maximum;let mut next_grid=125*US;let mut steps=0;let mut roots=0;let mut replays=0;let mut elapsed=0.;let mut heap=0;let mut max_r=0_f64;let mut max_c=0_f64;let mut max_e=0_f64;let mut min_h=1_f64;grid(&mut out,0,s);
    while ticks<100000*US{let event=if ticks<1000*US{1000*US}else if ticks<75000*US{75000*US}else{100000*US};let edge=event.min(next_grid);let remain=edge-ticks;let span=proposal.min(1_u64<<(63-remain.leading_zeros()));let mut p=p;p.time=ticks as f64*TICK;
        let c=Controls{key:if(1000*US..75000*US).contains(&ticks){10.}else{0.},short:false,optional:false};let old=s;let old_ticks=ticks;let allocations=ALLOCS.load(Ordering::Relaxed);let clock=Instant::now();let result=voice::advance(&mut workspace,p,&mut s,c,span as f64*TICK);elapsed+=clock.elapsed().as_secs_f64();heap+=ALLOCS.load(Ordering::Relaxed)-allocations;
        let q=match result{Ok(q)=>q,Err(e)=>{write!(out,"FAILED,{ticks},{span}").unwrap();state(&mut out,old);writeln!(out).unwrap();out.flush().unwrap();return Err(format!("TRANSIENT ticks={ticks}:{e:?}"));}};
        let actual=(q.h/TICK).round()as u64;assert!(actual>0&&actual<=span);assert_eq!(q.h.to_bits(),(actual as f64*TICK).to_bits());let before=audio.clone();let read_alloc=ALLOCS.load(Ordering::Relaxed);
        if steps%1500==0{assert!(audio.append(old,&q,old_ticks+1,actual).is_err());assert_eq!(audio.samples(),before.samples());assert_eq!(audio.through_ticks(),before.through_ticks());readout_rejections+=1;}
        audio.append(old,&q,old_ticks,actual).unwrap();assert_eq!(s,q.fine[1].stages[1]);
        if steps%1500==0{let mut retry=before;retry.append(old,&q,old_ticks,actual).unwrap();assert_eq!(audio.samples(),retry.samples());assert_eq!(audio.through_ticks(),retry.through_ticks());readout_replays+=1;}
        assert_eq!(ALLOCS.load(Ordering::Relaxed),read_alloc);
        ticks+=actual;steps+=1;min_h=min_h.min(q.h);max_e=max_e.max(q.error);for pair in [&q.coarse,&q.fine[0],&q.fine[1]]{max_r=max_r.max(pair.residual_a);max_c=max_c.max(pair.correction_v);}
        if steps==1||ticks==1000*US||old_ticks==1000*US||ticks==75000*US||old_ticks==75000*US||ticks==100000*US{let mut retry=old;let qq=voice::advance(&mut workspace,p,&mut retry,c,span as f64*TICK).unwrap();assert_eq!(s,retry);assert_eq!(q.h.to_bits(),qq.h.to_bits());assert_eq!(q.error.to_bits(),qq.error.to_bits());replays+=1;root(&mut out,old,&q.coarse,c,p.time,q.h);root(&mut out,old,&q.fine[0],c,p.time,q.h/2.);root(&mut out,q.fine[0].stages[1],&q.fine[1],c,p.time+q.h/2.,q.h/2.);roots+=3;}
        if ticks==1000*US||ticks==75000*US{assert_eq!(audio.samples()[(ticks/(1000*US)*48)as usize].to_bits(),(s.high[115]+s.low[115]).to_bits());write!(out,"EVENT,{ticks},{}",if ticks==1000*US{10}else{0}).unwrap();state(&mut out,s);writeln!(out).unwrap();}
        proposal=if q.error<0.05{(2*actual).min(maximum)}else{actual};if ticks==next_grid{grid(&mut out,ticks,s);next_grid+=125*US;}
    }
    assert_eq!(heap,0);assert_eq!(audio.samples().len(),4801);assert_eq!(audio.samples()[4800].to_bits(),(s.high[115]+s.low[115]).to_bits());
    for (n,v) in audio.samples().iter().enumerate(){writeln!(out,"AUDIO,{n},{v:0.17e}").unwrap();}
    writeln!(out,"READOUT,{readout_rejections},{readout_replays},0,{}",audio.through_ticks()).unwrap();
    write!(out,"FINAL,{ticks},{steps},{roots},{replays},5,{heap}").unwrap();vals(&mut out,[elapsed,min_h,max_r,max_c,max_e]);state(&mut out,s);writeln!(out).unwrap();out.flush().unwrap();Ok(())
}
