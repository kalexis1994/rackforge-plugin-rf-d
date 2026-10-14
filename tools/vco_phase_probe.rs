pub use rf_d_circuit::{junction_charge,vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton,block_decay_voice};
#[path="../crates/rf-d-circuit/src/vco_nominal_phase.rs"] mod phase;
#[path="assembly_vco_helper.rs"] mod fine;
use std::{io::{self,BufRead},alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering},hint::black_box,time::Instant};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter {
    unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}
    unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}
    unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}
}
#[global_allocator] static ALLOCATOR:Counter=Counter;
fn print_values(tag:&str,all:impl IntoIterator<Item=f64>){print!("{tag}");for v in all{print!(",{v:.17e}");}println!();}
fn port(p:phase::output::Port)->impl Iterator<Item=f64>{p.current_a.into_iter().chain(p.admittance_s.into_iter().flatten()).chain([p.saw_v,p.tap_v,p.cursor_v,p.dissipated_w])}
fn tangent(values:&[f64],h:f64)->(f64,f64) {
    const N:usize=134;const M:usize=268;
    let get=|k:usize|if k==108{0.}else{values[if k<108{k}else{k-1}]};
    let low=|k:usize|if k==108{0.}else{values[250+if k<108{k}else{k-1}]};
    let old=fine::State{high:std::array::from_fn(get),low:std::array::from_fn(low)};
    let dc=vco1_stamp::linearize(old.high,vco1_stamp::Controls::default(),vco1_stamp::Mode::Dc).unwrap();
    let full=fine::linearize_compensated(old,fine::State::from_nodes([0.;N]),vco1_stamp::Controls::default(),h).unwrap();
    let b=rf_d_circuit::vco1_radau::B;
    let j:[[f64;M];M]=std::array::from_fn(|i|std::array::from_fn(|k|
        b[i/N][k/N]*(full.jacobian[i%N][k%N]-dc.jacobian[i%N][k%N])+if i/N==k/N{dc.jacobian[i%N][k%N]}else{0.}));
    let mut rhs=[0.;M];rhs[108]=1.;rhs[N+108]=1.;
    let mut d=rf_d_circuit::block_decay_voice::solve_linear_sparse(j,rhs).unwrap();
    let mut low=[0.;M];
    for iteration in 0..=3 {
        let mut residual=[0.;M];let mut backward=0_f64;
        for i in 0..M {
            let mut high=-rhs[i];let mut tail=0.;let mut scale=rhs[i].abs();
            for k in 0..M {
                let product=j[i][k]*d[k];let(a,b)=fine::two_sum(high,product);high=a;
                tail+=b+j[i][k].mul_add(d[k],-product)+j[i][k]*low[k];
                scale+=j[i][k].abs()*(d[k].abs()+low[k].abs()+if k%N>=98{2e-12}else{2e-9});
            }
            residual[i]=high+tail;backward=backward.max(residual[i].abs()/scale.max(1e-300));
        }
        if backward<=1e-10||iteration==3{return (-(d[N+108]+low[N+108]),backward);}
        let correction=rf_d_circuit::block_decay_voice::solve_linear_sparse(j,residual.map(|v|-v)).unwrap();
        for k in 0..M {let(h,l)=fine::two_sum(d[k],correction[k]);let(h,l)=fine::two_sum(h,l+low[k]);d[k]=h;low[k]=l;}
    }
    unreachable!()
}
fn main() {
    for line in io::stdin().lock().lines() {
        let line=line.unwrap();let mut tokens=line.split(',');let tag=tokens.next().unwrap();
        let v:Vec<f64>=tokens.map(|x|x.parse().unwrap()).collect();
        match tag {
            "TIME"=>{let p=phase::observe(v[0],v[1]).unwrap();print_values("TIME",port(p));},
            "PORT"=>{let p=phase::output::evaluate(v[0],[v[1],v[2],v[3],v[4]]).unwrap();print_values("PORT",port(p));},
            "TANGENT"=>{let(y,r)=tangent(&v[1..],v[0]);print_values("TANGENT",[y,r]);},
            "BENCH"=>{
                for rate in [48000.,96000.,192000.] {
                    let mut s=phase::State::at_time(0.04).unwrap();let start=Instant::now();let before=ALLOCS.load(Ordering::Relaxed);
                    for k in 0..1_000_000 {black_box(s.process(black_box(rate),black_box(0.7+0.2*(k%51) as f64/50.)).unwrap());}
                    let allocations=ALLOCS.load(Ordering::Relaxed)-before;let seconds=start.elapsed().as_secs_f64();
                    let expected=phase::State::at_time(0.04+1_000_000_f64/rate).unwrap();
                    let error=(s.phase()-expected.phase()).abs().min(1.-(s.phase()-expected.phase()).abs());
                    assert_eq!(allocations,0);assert!(error<1e-10);print_values("BENCH",[rate,seconds,allocations as f64,error]);
                }
                let mut s=phase::State::at_time(0.04).unwrap();let saved=s;
                for (rate,bus) in [(f64::NAN,0.),(44100.,0.),(300000.,0.),(48000.,f64::NAN),(48000.,f64::INFINITY),(48000.,2.1),(48000.,-2.1)] {
                    assert!(s.process(rate,bus).is_err());assert_eq!(s,saved);
                }
                assert!(phase::State::at_time(f64::NAN).is_err());
                for k in 0..200 {
                    let mut edge=phase::State::at_time(phase::profile::EPOCH_S+(0.992+k as f64*1e-5)/phase::profile::FREQUENCY_HZ).unwrap();
                    let rate=phase::profile::FREQUENCY_HZ/(1.-edge.phase());
                    edge.process(rate,0.8).unwrap();assert!((0. ..1.).contains(&edge.phase()));
                }
                let p=s.process(48000.,0.8).unwrap();let mut fresh=saved;assert_eq!(p,fresh.process(48000.,0.8).unwrap());assert_eq!(s,fresh);
                println!("DOMAIN,7,exact_retry=true");
            },
            _=>panic!("unknown mode"),
        }
    }
}
