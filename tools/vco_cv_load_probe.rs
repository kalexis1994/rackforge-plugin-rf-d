pub use rf_d_circuit::{vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton,vco1_startup};
#[path="vco_cv_load_linear.rs"]mod output_conversion;
#[path="vco_cv_load_fine.rs"]mod fine;
#[path="vco_cv_load_radau.rs"]mod radau;
use vco1_stamp::{Controls,N};use fine::State;use std::io::{Write,BufWriter};
const TICK:f64=125e-9/65536.;
fn controls(i:usize)->Controls{let mut c=Controls::default();c.r8_fraction=0.2613404652606161;c.r11_ohm=521.3126579373712;c.cv_v[2]=[-3.1,-2.1,-1.1,-0.1][i/3];c.mixer_v=[-0.125,0.,0.125][i%3];c}
fn state(out:&mut impl Write,s:State)->std::io::Result<()>{for x in s.high.into_iter().chain(s.low){write!(out,",{x:.17e}")?;}Ok(())}
fn roots()->Result<(),Box<dyn std::error::Error>>{
    let mut out=BufWriter::new(std::io::stdout().lock());
    for i in 0..12{let c=controls(i);let seed=vco1_startup::seed(c).map_err(|e|format!("seed {i}: {e:?}"))?;write!(out,"SEED,{i}")?;state(&mut out,State::from_nodes(seed))?;writeln!(out)?;let initial=vco1_startup::startup(c).map_err(|e|format!("startup {i}: {e:?}"))?;assert!(initial.residual_ratio<=1.&&initial.correction_ratio<=1.);write!(out,"DC,{i},{:.17e},{:.17e},{:.17e}",initial.startup_current_a.unwrap(),initial.residual_ratio,initial.correction_ratio)?;state(&mut out,State::from_nodes(initial.nodes))?;writeln!(out)?;
        if [0,2,9,11].contains(&i){let old=State::from_nodes(initial.nodes);for ticks in [4_u64,32]{let p=radau::step(c,old,ticks as f64*TICK).map_err(|e|format!("local {i}/{ticks}: {e:?}"))?;for(k,s)in [p.stage,p.endpoint].into_iter().enumerate(){write!(out,"LOCAL,{i},{ticks},{k},{:.17e},{:.17e}",s.residual_ratio,s.correction_ratio)?;state(&mut out,s.candidate)?;writeln!(out)?;}}}
    }out.flush()?;Ok(())
}
fn currents(p:&radau::Pair,old:State,h:f64)->Result<[f64;3],vco1_stamp::Error>{let a=p.stage.candidate;let b=p.endpoint.candidate;let fa=fine::observed_currents(a,a,h)?;let ea=fine::observed_currents(a,old,h)?;let fb=fine::observed_currents(b,b,h)?;let eb=fine::observed_currents(b,old,h)?;Ok(std::array::from_fn(|k|fb[k]+radau::B[1][0]*(ea[k]-fa[k])+radau::B[1][1]*(eb[k]-fb[k])))}
fn emit(out:&mut impl Write,time:u64,p:&radau::Pair,old:State,h:f64)->Result<(),Box<dyn std::error::Error>>{
    let s=p.endpoint.candidate;for k in 0..N{assert_eq!(fine::two_sum(s.high[k],s.low[k]),(s.high[k],s.low[k]));}let cur=currents(p,old,h).map_err(|e|format!("currents: {e:?}"))?;
    out.write_all(&(time as f64*TICK).to_le_bytes())?;for k in [43,48,46,54,44,15,35,7,10,21,4,3,39,20]{out.write_all(&(s.high[k]+s.low[k]).to_le_bytes())?;}for x in &cur[..2]{out.write_all(&x.to_le_bytes())?;}Ok(())
}
fn walk(maximum:u32)->Result<(),Box<dyn std::error::Error>>{
    if ![65536,131072].contains(&maximum){return Err("maximum half ticks".into());}let c=controls(5);let initial=vco1_startup::startup(c).map_err(|e|format!("startup: {e:?}"))?;let mut old=State::from_nodes(initial.nodes);let mut err=BufWriter::new(std::io::stderr());write!(err,"INITIAL")?;state(&mut err,old)?;writeln!(err)?;err.flush()?;
    let(mut time,mut steps,mut proposal)=(0_u64,0_u64,2*maximum);let end=15728640000_u64; // 30 ms in the admitted clock.
    let mut out=BufWriter::with_capacity(65536,std::io::stdout().lock());let mut maxima=[0_f64;3];let mut min_ticks=u32::MAX;
    while time<end{
        if steps>=800000{return Err("endpoint budget".into());}let mut ticks=proposal;while ticks as u64>end-time{ticks/=2;}
        let mut accepted=None;let mut reason=String::new();
        for attempts in 1..=20{
            let trial=(||{let full=radau::step(c,old,ticks as f64*TICK)?;let mid=radau::step(c,old,(ticks/2)as f64*TICK)?;let last=radau::step(c,mid.endpoint.candidate,(ticks/2)as f64*TICK)?;let d=full.endpoint.candidate.difference(last.endpoint.candidate);let error=(0..N).fold(0_f64,|a,k|a.max(d[k].abs()/if k<98{2e-6}else{2e-9}));Ok::<_,vco1_newton::Error>((mid,last,error))})();
            match trial{Ok((mid,last,error))=>{if error<=1.{accepted=Some((mid,last,error,attempts));break;}reason=format!("LTE {error}");},Err(e)=>reason=format!("{e:?}")}
            if ticks<=8{out.flush()?;return Err(format!("time={time},ticks={ticks},{reason}").into());}ticks/=2;
        }
        let(mid,last,error,attempts)=accepted.ok_or(format!("attempt budget {reason}"))?;proposal=if error<=0.25{(ticks*2).min(2*maximum)}else{ticks};
        for p in [&mid,&last]{for v in [&p.stage,&p.endpoint]{maxima[0]=maxima[0].max(v.residual_ratio);maxima[1]=maxima[1].max(v.correction_ratio);}maxima[2]=maxima[2].max(error);}
        if steps==0||time<100000&&time+ticks as u64>=100000{write!(err,"INTERVAL,{time},{}",ticks/2)?;state(&mut err,old)?;state(&mut err,mid.stage.candidate)?;state(&mut err,mid.endpoint.candidate)?;writeln!(err)?;err.flush()?;}
        time+=(ticks/2)as u64;emit(&mut out,time,&mid,old,(ticks/2)as f64*TICK)?;time+=(ticks/2)as u64;emit(&mut out,time,&last,mid.endpoint.candidate,(ticks/2)as f64*TICK)?;old=last.endpoint.candidate;steps+=2;min_ticks=min_ticks.min(ticks/2);
        if steps%10000==0{writeln!(err,"PROGRESS,{maximum},{steps},{time}")?;err.flush()?;}
        let _=attempts;
    }
    out.flush()?;writeln!(err,"COMPLETE,{maximum},{steps},{time},{min_ticks},{:.17e},{:.17e},{:.17e}",maxima[0],maxima[1],maxima[2])?;write!(err,"FINAL")?;state(&mut err,old)?;writeln!(err)?;err.flush()?;Ok(())
}
fn run()->Result<(),Box<dyn std::error::Error>>{let a:Vec<_>=std::env::args().collect();if a.len()!=2{return Err("roots or maximum_half_ticks".into());}if a[1]=="roots"{roots()}else{walk(a[1].parse()?)}}
fn main(){if let Err(e)=run(){eprintln!("ERROR,{e}");std::process::exit(2);}}
