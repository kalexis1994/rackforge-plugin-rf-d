fn flux(s:joint::State,slope:f64)->[f64;7]{
 let v=|k|s.high[k]+s.low[k];
 [v(205),slope,(v(208)-v(205))/10000.,(v(211)-v(205))/100000.,(v(205)-v(200))/10000.,v(226)-v(228),v(218)]
}
#[inline(never)]
fn initial_flux(p:joint::Parameters,s:joint::State)->Result<[f64;7],String>{
 let part=joint::parts(p,s,joint::State::from_nodes([0.;229]),joint::MIN_DT_S).map_err(|e|format!("incoming flux:{e:?}"))?;
 Ok(flux(s,-part.dc[205]/1e-5))
}
fn endpoint_flux(ep:&temporal::Endpoint,h:f64)->[f64;7]{
 let d=|i:usize|ep.pair.increments[i].high[205]+ep.pair.increments[i].low[205];
 flux(ep.pair.candidates[1],(-4.5*d(0)+2.5*d(1))/h)
}
fn write_flux(w:&mut impl Write,tick:u64,x:[f64;7])->Result<(),String>{
 if x.iter().any(|v|!v.is_finite()){return Err("nonfinite flux".into());}
 w.write_all(&tick.to_le_bytes()).map_err(|e|e.to_string())?;
 for v in x{w.write_all(&v.to_le_bytes()).map_err(|e|e.to_string())?;}Ok(())
}
