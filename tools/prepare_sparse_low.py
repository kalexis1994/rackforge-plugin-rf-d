"""Accumulate analytic J*LOW at devices in both modes, without dense dot loops."""
from refine_hybrid_stamp import once
def transform(audio,chain,contour,volume,filter):
    audio=once(audio,'let current=if FULL{current}else{current+g*(self.low(left)-self.low(right))};','let current=current+g*(self.low(left)-self.low(right));')
    audio=once(audio,'}else{let mut v=0.;for col in 0..3{v+=slopes[row][col]*self.low(terminals[col]);}self.r[i]+=v;}', '}\n                let mut v=0.;for col in 0..3{v+=slopes[row][col]*self.low(terminals[col]);}self.r[i]+=v;')
    audio=once(audio,'if !FULL{s.r[49]+=if ob.r21_lower_ohm==5000.{low[49]-low[48]}else{low[49]};}','s.r[49]+=if ob.r21_lower_ohm==5000.{low[49]-low[48]}else{low[49]};')
    chain=once(chain,'let mut dc=[0.;N];dc[..66].copy_from_slice(&r);dc[BUS]=port.current_a[5];','let mut dc=[0.;N];dc[..66].copy_from_slice(&r);dc[BUS]=port.current_a[5];')
    chain=once(chain,'let y=p.mixer.admittance_s();jac[BUS][BUS]=y[5][5];','let y=p.mixer.admittance_s();jac[BUS][BUS]=y[5][5];dc[BUS]+=y[5][5]*now.low[BUS];')
    chain=once(chain,'let i=g*(now.high[22]-now.high[C10_LEFT]);','let i=g*(now.high[22]-now.high[C10_LEFT])+g*(now.low[22]-now.low[C10_LEFT]);')
    chain=once(chain,'dc[C10_LEFT]=now.high[C10_LEFT]-now.high[22];','dc[C10_LEFT]=now.high[C10_LEFT]-now.high[22]+(now.low[C10_LEFT]-now.low[22]);')
    chain=once(chain,'dc[C10_LEFT]=now.high[C10_LEFT]-now.high[7];','dc[C10_LEFT]=now.high[C10_LEFT]-now.high[7]+(now.low[C10_LEFT]-now.low[7]);')
    chain=once(chain,' for a in 0..N {if FULL||a==22||a==C10_LEFT||a==BUS{dc[a]+=(0..N).map(|b|jac[a][b]*now.low[b]).sum::<f64>();}}',' // Every DC incidence already includes its analytic LOW direction.\n')
    old='if k<N{s.dc[k]+=i;if FULL{for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}}}else{s.dc[k]+=d.iter().map(|&(j,g)|if j<N{g*s.low[j]}else{0.}).sum::<f64>();}}'
    new='if k<N{s.dc[k]+=i;s.dc[k]+=d.iter().map(|&(j,g)|if j<N{g*s.low[j]}else{0.}).sum::<f64>();if FULL{for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}}}}'
    volume=once(volume,old,new)
    filter=once(filter,'let i=if FULL{i}else{i+d.iter().map(|&(j,g)|g*if j<N{s.low[j]}else{s.port_low[j-N]}).sum::<f64>()};','let i=i+d.iter().map(|&(j,g)|g*if j<N{s.low[j]}else{s.port_low[j-N]}).sum::<f64>();')
    contour=once(contour,'if k<N{s.dc[k]+=i;if FULL{for &(j,g)in d{if j<N{s.j[k][j]+=g;}}}else{s.dc[k]+=d.iter().map(|&(j,g)|if j<N{g*s.now.low[j]}else{0.}).sum::<f64>();}}','if k<N{s.dc[k]+=i;s.dc[k]+=d.iter().map(|&(j,g)|if j<N{g*s.now.low[j]}else{0.}).sum::<f64>();if FULL{for &(j,g)in d{if j<N{s.j[k][j]+=g;}}}}')
    contour=once(contour,'    if FULL {for a in 0..N {\n        s.dc[a] += (0..N).map(|b| s.j[a][b] * x.low[b]).sum::<f64>();\n    }}','    // LOW has been accounted at the original device/port incidences.\n')
    return audio,chain,contour,volume,filter
