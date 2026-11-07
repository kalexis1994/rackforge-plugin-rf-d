pub use rf_d_circuit::{junction_charge, StepError};
#[cfg(baseline)]
#[path = "recovery_port_fast_kernel.rs"]
mod core;
#[cfg(joint)]
#[path = "recovery_cost_joint_kernel.rs"]
mod core;
#[cfg(predict)]
#[path = "recovery_cost_predict_kernel.rs"]
mod core;
#[cfg(specialized)]
#[path = "recovery_cost_static_kernel.rs"]
mod core;
#[cfg(expfoh)]
#[path = "recovery_cost_exp_kernel.rs"]
mod core;
#[cfg(not(splitfir))]
#[path = "../crates/rf-d-circuit/src/j7_stream_output.rs"]
mod stream;
#[cfg(splitfir)]
#[path = "recovery_cost_split_fir.rs"]
mod stream;
#[cfg(splitfir)]
#[path = "../crates/rf-d-circuit/src/j7_stream_output.rs"]
mod old_stream;
use std::{
    alloc::{GlobalAlloc, Layout, System},
    io::{BufWriter, Read, Write},
    sync::atomic::{AtomicUsize, Ordering},
    time::Instant,
};
struct Counter;
static ALLOCS: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        ALLOCS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.alloc(l) }
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) { unsafe { System.dealloc(p, l) } }
    unsafe fn realloc(&self, p: *mut u8, l: Layout, n: usize) -> *mut u8 {
        ALLOCS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.realloc(p, l, n) }
    }
}
#[global_allocator]
static ALLOCATOR: Counter = Counter;
fn input(k: usize, stress: bool) -> f64 {
    if stress {
        match (k / 97) % 4 {
            0 => 0.13,
            1 => -0.13,
            2 => 0.13 * (2. * (k % 97) as f64 / 96. - 1.),
            _ => 0.,
        }
    } else {
        let t = k as f64 / 384000.;
        0.1 * ((std::f64::consts::TAU * 137. * t).sin()
            + 0.3 * (std::f64::consts::TAU * 1103. * t).sin())
    }
}
fn same(a: core::State, b: core::State) -> bool {
    a.index == b.index && a.q.into_iter().chain(a.history).chain(a.defects)
        .chain([a.input]).zip(b.q.into_iter().chain(b.history).chain(b.defects).chain([b.input]))
        .all(|(a, b)| a.to_bits() == b.to_bits())
}
fn rejections(mut s: core::State) {
    s.q[0] = -0.; s.input = -0.;
    let before = ALLOCS.load(Ordering::Relaxed);
    for u in [f64::NAN, f64::INFINITY, 0.130001] {
        let mut x = s;
        assert!(core::step(&mut x, u).is_err()); assert!(same(x, s));
        let mut control = s;
        core::step(&mut x, 0.).unwrap(); core::step(&mut control, 0.).unwrap();
        assert!(same(x, control));
    }
    for budget in [0, 1] {
        let mut x = s;
        assert!(core::step_with_budget(&mut x, 0.13, budget).is_err()); assert!(same(x, s));
        let mut control = s;
        core::step(&mut x, 0.).unwrap(); core::step(&mut control, 0.).unwrap();
        assert!(same(x, control));
    }
    for corrupt in [0, 1] {
        let mut x = s;
        if corrupt == 0 { x.index = 3; } else { x.q[3] = f64::NAN; }
        let saved = x;
        assert!(core::step(&mut x, 0.).is_err()); assert!(same(x, saved));
    }
    assert_eq!(before, ALLOCS.load(Ordering::Relaxed));
}
fn vectors(stress: bool) -> Result<(), Box<dyn std::error::Error>> {
    let mut out = BufWriter::new(std::io::stdout().lock());
    for index in 0..3 {
        let mut s = core::State::dc(index).unwrap(); rejections(s);
        for k in 0..1537 {
            let u = if k == 0 { 0. } else { input(k, stress) };
            let before = ALLOCS.load(Ordering::Relaxed);
            let ports = core::step(&mut s, u).unwrap(); let x = core::nodes(s);
            assert_eq!(before, ALLOCS.load(Ordering::Relaxed));
            for v in [index as f64, k as f64 / 384000., u, ports.bus_v, ports.base_v, ports.j7_v, ports.panel_a]
                .into_iter().chain(s.q).chain(x) { out.write_all(&v.to_le_bytes())?; }
        }
        rejections(s);
    }
    out.flush()?; Ok(())
}
#[cfg(not(baseline))]
fn laws() -> Result<(), Box<dyn std::error::Error>> {
    let mut bytes = Vec::new(); std::io::stdin().read_to_end(&mut bytes)?;
    assert_eq!(bytes.len() % 8, 0);
    let mut out = BufWriter::new(std::io::stdout().lock());
    for index in 0..3 { for chunk in bytes.chunks_exact(8) {
        let z = f64::from_le_bytes(chunk.try_into().unwrap());
        let before = ALLOCS.load(Ordering::Relaxed);
        let (n, s) = core::law(index, [z; 12]).unwrap();
        assert_eq!(before, ALLOCS.load(Ordering::Relaxed));
        for v in [index as f64, z].into_iter().chain(n).chain(s) { out.write_all(&v.to_le_bytes())?; }
    }}
    out.flush()?; Ok(())
}
#[cfg(joint)]
fn stages() -> Result<(), Box<dyn std::error::Error>> {
    let mut out = BufWriter::new(std::io::stdout().lock());
    for index in 0..3 { for k in 0..16 {
        let q = std::array::from_fn(|j| ((j as f64)*0.73+(k as f64)*0.2).sin()*1e-5);
        let u = 0.1 * ((k as f64) * 0.7).sin();
        let before = ALLOCS.load(Ordering::Relaxed);
        let (next, n, z, iterations, residual) = core::stage(index, q, u, 12).unwrap();
        assert_eq!(before, ALLOCS.load(Ordering::Relaxed));
        for v in [index as f64, k as f64, u, iterations as f64, residual].into_iter()
            .chain(q).chain(next).chain(n).chain(z) { out.write_all(&v.to_le_bytes())?; }
    }}
    out.flush()?; Ok(())
}
#[cfg(any(predict,specialized))]
fn stages() -> Result<(), Box<dyn std::error::Error>> {
    let mut out = BufWriter::new(std::io::stdout().lock());
    let gamma = 1.-1./2_f64.sqrt();
    for index in 0..3 { for k in 0..16 {
        let q: [f64;18] = std::array::from_fn(|j| ((j as f64)*0.73+(k as f64)*0.2).sin()*1e-5);
        let u = 0.1 * ((k as f64) * 0.7).sin();
        let before = ALLOCS.load(Ordering::Relaxed);
        let first = core::stage_seed(index, q, gamma*u, 12, [0.;12]).unwrap();
        let history = std::array::from_fn(|j| q[j]+(1.-gamma)/gamma*(first.0[j]-q[j]));
        let second = core::stage_seed(index, history, u, 12, first.1).unwrap();
        assert_eq!(before, ALLOCS.load(Ordering::Relaxed));
        for (stage,old,voltage,result) in [(0,q,gamma*u,first),(1,history,u,second)] {
            for v in [index as f64,(2*k+stage) as f64,voltage,result.3 as f64,result.4].into_iter()
                .chain(old).chain(result.0).chain(result.1).chain(result.2) {out.write_all(&v.to_le_bytes())?;}
        }
    }}
    out.flush()?; Ok(())
}
#[cfg(expfoh)]
fn stages() -> Result<(), Box<dyn std::error::Error>> {
    let mut out = BufWriter::new(std::io::stdout().lock());
    for index in 0..3 {
        let mut s=core::State::dc(index).unwrap();
        for k in 0..1537 {
            let old=s; let u=input(k,false);
            let before=ALLOCS.load(Ordering::Relaxed);
            let(_,z,it,res)=core::inspect(&mut s,u,12).unwrap();
            assert_eq!(before,ALLOCS.load(Ordering::Relaxed));
            if k%96==0 && k<1536 {
                for v in [index as f64,k as f64,old.input,u,it as f64,res].into_iter().chain(old.q)
                    .chain(old.defects).chain(s.q).chain(s.defects).chain(z).chain(core::nodes(s)) {
                    out.write_all(&v.to_le_bytes())?;
                }
            }
        }
    }
    out.flush()?;Ok(())
}
#[cfg(splitfir)]
fn fircheck() -> Result<(),Box<dyn std::error::Error>> {
    let mut total=0;
    for scene in 0..4 {
        let mut s=core::State::dc(scene.min(2)).unwrap();
        let initial=if scene==3 {0.25} else {core::nodes(s)[61]};
        let mut fast=stream::Decimator::new(initial).unwrap();
        let mut old=old_stream::Decimator::new(initial).unwrap();
        let mut a=[stream::Frame::EMPTY;128];let mut b=[old_stream::Frame::EMPTY;128];
        let mut input_buffer=[0.;1024];let mut at=0;
        let saved=fast.clone(); let slots=a;
        assert!(fast.push(&[f64::NAN],&mut a).is_err());assert!(fast==saved);assert_eq!(a,slots);
        for size in [17,383,389,1024,64,1,769,512].into_iter().cycle().take(48) {
            for k in 0..size {let j=at+k;input_buffer[k]=if scene==3{if j==1{1.25}else{0.25}}else{core::step(&mut s,input(j,false)).unwrap().j7_v};}
            let before=ALLOCS.load(Ordering::Relaxed);
            let n=fast.push(&input_buffer[..size],&mut a).unwrap();let m=old.push(&input_buffer[..size],&mut b).unwrap();
            assert_eq!(before,ALLOCS.load(Ordering::Relaxed));assert_eq!(n,m);
            assert_eq!((fast.consumed(),fast.produced()),(old.consumed(),old.produced()));
            for j in 0..n {assert_eq!((a[j].source_index,a[j].ready_input_index,a[j].voltage_v.to_bits()),(b[j].source_index,b[j].ready_input_index,b[j].voltage_v.to_bits()));}
            at+=size;total+=n;
        }
    }
    println!("FIR_EXACT,{total},4,48"); Ok(())
}
fn bench(blocks: usize) -> Result<(), Box<dyn std::error::Error>> {
    let mut s = core::State::dc(1).unwrap();
    let mut fir = stream::Decimator::new(core::nodes(s)[61]).unwrap();
    let mut inputs = [0.; 1024]; let mut raw = [0.; 1024];
    let mut frames = [stream::Frame::EMPTY; 128];
    let mut out = BufWriter::new(std::io::stdout().lock()); let mut checksum = 0.;
    for block in 0..blocks {
        for k in 0..1024 { inputs[k] = input(block*1024+k, false); }
        let before = ALLOCS.load(Ordering::Relaxed); let clock = Instant::now();
        for k in 0..1024 { raw[k] = core::step(&mut s, inputs[k]).unwrap().j7_v; }
        let n = fir.push(&raw, &mut frames).unwrap();
        let elapsed = clock.elapsed().as_secs_f64(); let heap = ALLOCS.load(Ordering::Relaxed)-before;
        assert_eq!(heap, 0);
        for frame in &frames[..n] { checksum += std::hint::black_box(frame.voltage_v); }
        writeln!(out, "BLOCK,{block},{elapsed:.17e},{heap},{n}")?;
    }
    writeln!(out, "COMPLETE,{checksum:.17e}")?; out.flush()?; Ok(())
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    match std::env::args().nth(1).as_deref() {
        Some("vectors") => vectors(false), Some("stress") => vectors(true),
        #[cfg(not(baseline))] Some("laws") => laws(),
        #[cfg(not(baseline))] Some("stages") => stages(),
        #[cfg(splitfir)] Some("fircheck") => fircheck(),
        Some("long") => bench(4800), _ => bench(1200),
    }
}
