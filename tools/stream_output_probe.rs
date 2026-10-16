pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/j7_stream_output.rs"]mod stream;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use stream::{Frame,Decimator,Pipeline,startup::*};
use std::{io::{Write,BufWriter},alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
const US:u64=524288;const TICK:f64=125e-9/65536.;
fn read(path:&str)->Vec<f64>{std::fs::read(path).unwrap().chunks_exact(8).map(|b|f64::from_le_bytes(b.try_into().unwrap())).collect()}
fn equal(a:Frame,b:Frame){assert_eq!(a.source_index,b.source_index);assert_eq!(a.ready_input_index,b.ready_input_index);assert_eq!(a.voltage_v.to_bits(),b.voltage_v.to_bits());}
fn state_equal(a:State,b:State){assert_eq!(a.optional,b.optional);for k in 0..118{assert_eq!(a.high[k].to_bits(),b.high[k].to_bits());assert_eq!(a.low[k].to_bits(),b.low[k].to_bits());}}
fn check_frame(f:Frame,expected:&[f64]){assert_eq!(f.ready_input_index,8*f.source_index+384);assert_eq!(f.voltage_v.to_bits(),expected[f.source_index as usize].to_bits());}
fn replay(out:&mut impl Write,raw:&[f64],expected:&[f64],profile:usize){
    assert_eq!(raw.len(),115585);assert_eq!(expected.len(),14401);
    for mode in 0..3{
        let mut d=Decimator::new(raw[0]).unwrap();let mut pos=0;let mut blocks=0;let mut guards=0;let mut retries=0;let mut zeros=0;let mut heap=0;let mut values=[Frame::EMPTY;257];let mut other=values;let mut next_frame=0;
        while pos<raw.len(){
            let pattern:&[usize]=match mode{0=>&[1],1=>&[0,1,7,31,128,257,1024,2048],_=>&[127,128,129]};let mut len=pattern[blocks%pattern.len()].min(raw.len()-pos);
            for boundary in[384,385,76800,76801]{if pos<boundary{len=len.min(boundary-pos);}}
            let special=[0,384,385,76800,76801].contains(&pos);let saved=if special{Some(d.clone())}else{None};let n=ALLOCS.load(Ordering::Relaxed);
            if len==0{let old=d.clone();assert_eq!(d.push(&[],&mut values).unwrap(),0);assert!(d==old);zeros+=1;}
            else{
                let needed=if pos+len<=384{0}else{(pos+len-385)/8+1}-d.produced()as usize;
                if special&&needed>0{assert!(d.push(&raw[pos..pos+len],&mut[]).is_err());assert!(d==*saved.as_ref().unwrap());guards+=1;}
                let count=d.push(&raw[pos..pos+len],&mut values).unwrap();
                for &f in &values[..count]{assert_eq!(f.source_index,next_frame);check_frame(f,expected);next_frame+=1;}
                if let Some(mut branch)=saved{let count2=branch.push(&raw[pos..pos+len],&mut other).unwrap();assert_eq!(count,count2);for k in 0..count{equal(values[k],other[k]);}assert!(branch==d);d=branch.clone();retries+=1;}
            }
            heap+=ALLOCS.load(Ordering::Relaxed)-n;pos+=len;blocks+=1;
        }
        assert_eq!(d.consumed(),115585);assert_eq!(d.produced(),14401);assert_eq!(next_frame,14401);assert_eq!(heap,0);
        writeln!(out,"REPLAY,{profile},{mode},{blocks},{guards},{retries},{zeros},{heap},{},{}",d.consumed(),d.produced()).unwrap();
    }
}
fn chain()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn live(out:&mut impl Write,raw:&[f64],expected:&[f64]){
    let initial=stream::startup::cold_start(chain()).unwrap().state;let mut s=initial;let mut control=initial;let mut pipeline=Pipeline::new(initial).unwrap();let mut batch=stream::reference_readout::Buffer::<3841>::new(initial).unwrap();
    let mut w=Workspace::new();let mut w2=Workspace::new();let base=Parameters::new(chain()).unwrap();let mut ticks=0;let mut next_grid=125*US;let maximum=2*US;let mut proposal=maximum;let mut steps=0;let mut output=[Frame::EMPTY;433];let mut count=0;let mut guards=0;let mut capacity=0;let mut replays=0;let mut heap=0;let(mut max_r,mut max_c,mut max_e)=(0_f64,0_f64,0_f64);let mut minimum=1_f64;
    while ticks<10000*US{
        let event=if ticks<1000*US{1000*US}else{10000*US};let remain=event.min(next_grid)-ticks;let span=proposal.min(1_u64<<(63-remain.leading_zeros()));let mut p=base;p.time=ticks as f64*TICK;
        let c=Controls{key:if ticks>=1000*US{10.}else{0.},short:false,optional:false};let old=s;let mut frame=[Frame::EMPTY;1];let snapshot=pipeline.clone();let allocations=ALLOCS.load(Ordering::Relaxed);
        let q=voice::advance(&mut w,p,&mut s,c,span as f64*TICK).unwrap();let qc=voice::advance(&mut w2,p,&mut control,c,span as f64*TICK).unwrap();state_equal(s,control);assert_eq!(q.h.to_bits(),qc.h.to_bits());assert_eq!(q.error.to_bits(),qc.error.to_bits());
        for (a,b) in [&q.coarse,&q.fine[0],&q.fine[1]].into_iter().zip([&qc.coarse,&qc.fine[0],&qc.fine[1]]){for k in 0..2{state_equal(a.stages[k],b.stages[k]);state_equal(a.delta[k],b.delta[k]);}max_r=max_r.max(a.residual_a);max_c=max_c.max(a.correction_v);}
        let actual=(q.h/TICK).round()as u64;assert_eq!(q.h.to_bits(),(actual as f64*TICK).to_bits());
        if steps%1000==0{assert!(pipeline.append(old,&q,ticks+1,actual,&mut frame).is_err());assert!(pipeline==snapshot);assert_eq!(frame,[Frame::EMPTY;1]);guards+=1;}
        let last=((ticks+actual)as u128*384000/stream::reference_readout::TICKS_PER_SECOND as u128)as u64;
        let will=if last<384{0}else{(last-384)/8+1};
        if will>pipeline.produced()&&capacity<3{assert!(pipeline.append(old,&q,ticks,actual,&mut[]).is_err());assert!(pipeline==snapshot);capacity+=1;}
        let got=pipeline.append(old,&q,ticks,actual,&mut frame).unwrap();batch.append(old,&qc,ticks,actual).unwrap();
        if steps%1000==0{let mut retry=snapshot;let mut other=[Frame::EMPTY;1];let n=retry.append(old,&q,ticks,actual,&mut other).unwrap();assert_eq!(got,n);assert!(pipeline==retry);if got==1{equal(frame[0],other[0]);}replays+=1;}
        for f in frame.into_iter().take(got){check_frame(f,expected);assert_eq!(f.source_index,count as u64);output[count]=f;count+=1;}
        heap+=ALLOCS.load(Ordering::Relaxed)-allocations;ticks+=actual;steps+=1;minimum=minimum.min(q.h);max_e=max_e.max(q.error);assert_eq!(pipeline.through_ticks(),ticks);
        proposal=if q.error<0.05{(2*actual).min(maximum)}else{actual};if ticks==next_grid{next_grid+=125*US;}
    }
    assert_eq!(heap,0);assert_eq!(count,433);assert_eq!(pipeline.consumed(),3841);assert_eq!(pipeline.produced(),433);
    for(a,b)in batch.samples().iter().zip(raw){assert_eq!(a.to_bits(),b.to_bits());}
    let mut old=[0.;433];stream::reference_filter::convert(batch.samples(),&mut old,8).unwrap();for(k,f)in output.into_iter().enumerate(){assert_eq!(f.voltage_v.to_bits(),old[k].to_bits());}
    writeln!(out,"LIVE,{ticks},{steps},{count},{},{guards},{capacity},{replays},{heap},{minimum:.17e},{max_r:.17e},{max_c:.17e},{max_e:.17e}",pipeline.consumed()).unwrap();
    write!(out,"STATE").unwrap();for v in s.high.into_iter().chain(s.low){write!(out,",{v:.17e}").unwrap();}writeln!(out).unwrap();
}
fn main(){let args:Vec<_>=std::env::args().collect();let mut out=BufWriter::new(std::io::stdout());let a=read(&args[1]);let b=read(&args[2]);let c=read(&args[3]);let d=read(&args[4]);
    replay(&mut out,&a,&b,0);replay(&mut out,&c,&d,1);live(&mut out,&a,&b);
    writeln!(out,"SIZES,{},{},{}",std::mem::size_of::<Decimator>(),std::mem::size_of::<Pipeline>(),std::mem::size_of::<stream::reference_readout::Buffer<115585>>()).unwrap();out.flush().unwrap();
}
