pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/nominal_offline_producer.rs"]mod producer;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use producer::{Producer,Pending,Stop,US,stream::{self,Frame,Pipeline,startup::*}};
use std::{io::{Write,BufWriter},alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
const TICK:f64=stream::reference_readout::TICK_S;
fn read(path:&str)->Vec<f64>{std::fs::read(path).unwrap().chunks_exact(8).map(|b|f64::from_le_bytes(b.try_into().unwrap())).collect()}
fn state(a:State,b:State){assert_eq!(a.optional,b.optional);for k in 0..118{assert_eq!(a.high[k].to_bits(),b.high[k].to_bits());assert_eq!(a.low[k].to_bits(),b.low[k].to_bits());}}
fn pair(a:&Pair,b:&Pair){for k in 0..2{state(a.delta[k],b.delta[k]);state(a.stages[k],b.stages[k]);}assert_eq!(a.residual_a.to_bits(),b.residual_a.to_bits());assert_eq!(a.correction_v.to_bits(),b.correction_v.to_bits());assert_eq!(a.iterations,b.iterations);}
fn accepted(a:&Accepted,b:&Accepted){pair(&a.coarse,&b.coarse);pair(&a.fine[0],&b.fine[0]);pair(&a.fine[1],&b.fine[1]);assert_eq!(a.h.to_bits(),b.h.to_bits());assert_eq!(a.error.to_bits(),b.error.to_bits());assert_eq!(a.attempts,b.attempts);}
fn pending(a:&Pending,b:&Pending){state(a.old,b.old);accepted(&a.accepted,&b.accepted);assert_eq!(a.start,b.start);assert_eq!(a.span,b.span);}
fn same(a:&Producer,b:&Producer){state(a.state(),b.state());assert_eq!(a.solved_ticks(),b.solved_ticks());assert_eq!(a.end_ticks(),b.end_ticks());assert_eq!(a.next_grid_ticks(),b.next_grid_ticks());assert_eq!(a.proposal_ticks(),b.proposal_ticks());assert_eq!(a.invocations(),b.invocations());assert_eq!(a.accepted_steps(),b.accepted_steps());assert!(a.output()==b.output());match(a.pending(),b.pending()){(Some(a),Some(b))=>pending(a,b),(None,None)=>(),_=>panic!("pending lost")}}
fn chain()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn check(values:&[Frame],expected:&[f64],count:&mut usize){for f in values{assert_eq!(f.source_index,*count as u64);assert_eq!(f.ready_input_index,8*f.source_index+384);assert_eq!(f.voltage_v.to_bits(),expected[*count].to_bits());*count+=1;}}
fn main(){
    let args:Vec<_>=std::env::args().collect();let raw=read(&args[1]);let expected=read(&args[2]);let final_state=read(&args[3]);let mut out=BufWriter::new(std::io::stdout());
    let initial=stream::startup::cold_start(chain()).unwrap().state;let base=Parameters::new(chain()).unwrap();
    let mut previous:Option<Producer>=None;
    for mode in 0..3{
        let mut p=Producer::from_initial(base,initial,10000*US).unwrap();let mut w=Workspace::new();let mut wc=Workspace::new();let mut control=initial;let mut control_pipe=Pipeline::new(initial).unwrap();let mut batch=stream::reference_readout::Buffer::<3841>::new(initial).unwrap();let mut ct=0;let mut cg=125*US;let mut proposal=2*US;let mut comparisons=0;
        let(mut calls,mut count,mut blocked,mut zero_calls,mut retries,mut heap)=(0,0,0,0,0,0);let(mut max_r,mut max_c,mut max_e)=(0_f64,0_f64,0_f64);let mut min_h=1_f64;let mut first_boundary=false;let mut across_key=false;let mut frames=[Frame::EMPTY;128];
        loop{
            let quota=match mode{0=>1,1=>[0,7,31,3,127][calls%5],_=>[1024,1,509,0,17][calls%5]};
            let capacity=match mode{0=>if count<2{0}else{1},1=>[0,1,3,0,17,2,64][calls%7],_=>[0,0,128,7,0,2][calls%6]};
            let n=ALLOCS.load(Ordering::Relaxed);
            let r=if mode==0{p.run(&mut w,quota,&mut frames[..capacity],|work,par,s,c,h|{
                let event=if ct<1000*US{1000*US}else{10000*US};let remain=event.min(cg)-ct;let span=proposal.min(1_u64<<(63-remain.leading_zeros()));assert_eq!(h.to_bits(),(span as f64*TICK).to_bits());assert_eq!(par.time.to_bits(),(ct as f64*TICK).to_bits());assert_eq!(c.key,if ct>=1000*US{10.}else{0.});
                let mut pc=base;pc.time=ct as f64*TICK;let old=control;let q=voice::advance(work,par,s,c,h)?;let qc=voice::advance(&mut wc,pc,&mut control,c,span as f64*TICK)?;state(*s,control);accepted(&q,&qc);
                let actual=(qc.h/TICK).round()as u64;let mut cf=[Frame::EMPTY;1];control_pipe.append(old,&qc,ct,actual,&mut cf).unwrap();batch.append(old,&qc,ct,actual).unwrap();ct+=actual;if ct==cg{cg+=125*US;}proposal=if qc.error<0.05{(2*actual).min(2*US)}else{actual};comparisons+=1;
                for a in [&q.coarse,&q.fine[0],&q.fine[1]]{max_r=max_r.max(a.residual_a);max_c=max_c.max(a.correction_v);}max_e=max_e.max(q.error);min_h=min_h.min(q.h);Ok(q)
            })}else{p.pump(&mut w,quota,&mut frames[..capacity])};
            assert!(r.invocations<=quota);assert!(r.written<=capacity);check(&frames[..r.written],&expected,&mut count);if quota==0{assert_eq!(r.invocations,0);zero_calls+=1;}
            if let Some(pending)=p.pending(){assert_eq!(p.output().through_ticks(),pending.start);assert_eq!(p.solved_ticks(),pending.start+pending.span);state(p.state(),pending.accepted.fine[1].stages[1]);}else{assert_eq!(p.output().through_ticks(),p.solved_ticks());}
            if mode==0{assert_eq!(p.solved_ticks(),ct);assert_eq!(p.accepted_steps(),comparisons);assert_eq!(p.proposal_ticks(),proposal);assert_eq!(p.next_grid_ticks(),cg);state(p.state(),control);if p.pending().is_none(){assert!(p.output()==&control_pipe);}}
            if r.stop==Stop::OutputFull{
                blocked+=1;let saved=p.clone();let before=p.invocations();let mut sentinel=[Frame{source_index:99,ready_input_index:99,voltage_v:7.};1];let original=sentinel;
                if p.solved_ticks()==1000*US{first_boundary=true;}if p.output().produced()==1&&p.solved_ticks()>1000*US{across_key=true;}
                for quota in [0,1000]{let z=p.pump(&mut w,quota,&mut sentinel[..0]);assert_eq!(sentinel,original);assert_eq!(z.stop,Stop::OutputFull);assert_eq!(z.invocations,0);assert_eq!(z.written,0);assert_eq!(z.published_steps,0);same(&p,&saved);}
                let z=p.pump(&mut w,0,&mut sentinel);assert_eq!(z.invocations,0);assert_eq!(z.written,1);assert_eq!(z.published_steps,1);assert!(p.pending().is_none());assert_eq!(p.invocations(),before);
                let mut branch=saved;let mut fresh=Workspace::new();let mut other=original;let y=branch.pump(&mut fresh,0,&mut other);assert_eq!(z,y);assert_eq!(sentinel,other);same(&p,&branch);p=branch;retries+=1;zero_calls+=1;check(&sentinel[..z.written],&expected,&mut count);
            }else{assert!(matches!(r.stop,Stop::WorkQuota|Stop::Complete));}
            heap+=ALLOCS.load(Ordering::Relaxed)-n;calls+=1;assert!(calls<20000);
            if p.solved_ticks()==10000*US&&p.pending().is_none(){break;}
        }
        assert_eq!(count,433);assert_eq!(p.invocations(),5170);assert_eq!(p.accepted_steps(),5170);assert_eq!(p.output().consumed(),3841);assert_eq!(p.output().produced(),433);assert_eq!(heap,0);
        if mode==0{assert!(first_boundary&&across_key);assert_eq!(comparisons,5170);assert!(max_r<=1e-12&&max_c<=2e-9&&max_e<=1.);for(a,b)in batch.samples().iter().zip(&raw){assert_eq!(a.to_bits(),b.to_bits());}assert!(p.output()==&control_pipe);}
        for(a,b)in p.state().high.into_iter().chain(p.state().low).zip(&final_state){assert_eq!(a.to_bits(),b.to_bits());}
        if let Some(last)=&previous{same(&p,last);}previous=Some(p.clone());
        let n=ALLOCS.load(Ordering::Relaxed);for quota in[0,1,usize::MAX]{let saved=p.clone();let z=p.pump(&mut w,quota,&mut[]);assert_eq!(z.stop,Stop::Complete);assert_eq!(z.invocations,0);assert_eq!(z.written,0);same(&p,&saved);}assert_eq!(ALLOCS.load(Ordering::Relaxed)-n,0);
        writeln!(out,"PROFILE,{mode},{calls},{count},{blocked},{zero_calls},{retries},{heap},{},{},{},{},{},{comparisons},{first_boundary},{across_key},{min_h:.17e},{max_r:.17e},{max_c:.17e},{max_e:.17e}",p.solved_ticks(),p.invocations(),p.accepted_steps(),p.output().consumed(),p.output().produced()).unwrap();
    }
    writeln!(out,"SIZES,{},{},{}",std::mem::size_of::<Producer>(),std::mem::size_of::<Pending>(),std::mem::size_of::<Workspace>()).unwrap();out.flush().unwrap();
}
