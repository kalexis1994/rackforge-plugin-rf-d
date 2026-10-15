"""Derive residual/DC Jacobian modes without changing any device law."""
from prepare_dual_chain import ROOT
from refine_hybrid_stamp import once
def volume_source():
    s=(ROOT/'crates/rf-d-circuit/src/conditioned_voice_contour.rs').read_text(encoding='utf8')
    s=once(s,'pub struct Stamp{','pub struct Stamp<const FULL:bool>{low:[f64;N],')
    for name in ['row','r','diode','bjt']:s=once(s,'fn '+name+'(', 'fn '+name+'<const FULL:bool>(')
    s=s.replace('s:&mut Stamp','s:&mut Stamp<FULL>')
    s=once(s,'pub fn linearize(x:[f64;N],','pub fn linearize<const FULL:bool>(x:[f64;N],low:[f64;N],')
    s=once(s,'Result<Stamp,StepError>','Result<Stamp<FULL>,StepError>')
    s=once(s,'let mut s=Stamp{dc:', 'let mut s=Stamp::<FULL>{low,dc:')
    old='if k<N{s.dc[k]+=i;for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}}}'
    new='if k<N{s.dc[k]+=i;if FULL{for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}}}else{s.dc[k]+=d.iter().map(|&(j,g)|if j<N{g*s.low[j]}else{0.}).sum::<f64>();}}'
    return once(s,old,new)
def filter_source():
    s=(ROOT/'crates/rf-d-circuit/src/filter_contour_port.rs').read_text(encoding='utf8');s=s[:s.index('fn solve_linear(')]
    s=once(s,'pub struct Stamp {', 'pub struct Stamp<const FULL:bool> {\n    low:[f64;N],port_low:[f64;P],')
    for name in ['row','branch','transistor']:s=once(s,'fn '+name+'(', 'fn '+name+'<const FULL:bool>(')
    s=s.replace('s: &mut Stamp','s: &mut Stamp<FULL>')
    a=s.index('    if k < N {',s.index('fn row<'));b=s.index('\nfn value(',a)
    s=s[:a]+'''    let i=if FULL{i}else{i+d.iter().map(|&(j,g)|g*if j<N{s.low[j]}else{s.port_low[j-N]}).sum::<f64>()};
    if k<N{s.residual[k]+=i;if FULL{for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}else{s.node_port[k][j-N]+=g;}}}}
    else{s.port_current[k-N]+=i;if FULL{for &(j,g)in d{if j<N{s.port_node[k-N][j]+=g;}else{s.port_port[k-N][j-N]+=g;}}}}
}
'''+s[b:]
    s=once(s,'pub fn linearize(', 'pub fn linearize<const FULL:bool>(')
    a=s.index('pub fn linearize<');sig=s[a:s.index('    if !valid',a)]
    # Preserve all high-voltage/history parameters and add their LOW directions.
    sig2=once(sig,'    p: Parameters,', '    p: Parameters,\n    low:[f64;N],port_low:[f64;P],').replace('Result<Stamp, StepError>','Result<Stamp<FULL>, StepError>')
    s=once(s,sig,sig2);s=once(s,'    let mut s = Stamp {','    let mut s = Stamp::<FULL> {\n        low,port_low,')
    return s
def contour_source():
    s=(ROOT/'crates/rf-d-circuit/src/dual_contour_loaded.rs').read_text(encoding='utf8');s=s[:s.index('pub fn gaussian<')]
    s=s.replace('filter_contour_port.rs','prepared_filter_residual.rs').replace('conditioned_voice_contour.rs','prepared_volume_residual.rs')
    s=once(s,'pub struct Parts {','pub struct Parts<const FULL:bool> {')
    for name in ['row','resistor','bjt','diode','empty']:s=once(s,'fn '+name+'(', 'fn '+name+'<const FULL:bool>(')
    s=s.replace('s: &mut Parts','s: &mut Parts<FULL>').replace('-> Parts {','-> Parts<FULL> {').replace('        Parts {','        Parts::<FULL> {').replace('    Parts {','    Parts::<FULL> {')
    for name in ['dc','parts']:s=once(s,'pub fn '+name+'(', 'pub fn '+name+'<const FULL:bool>(')
    s=s.replace('Result<Parts, StepError>','Result<Parts<FULL>, StepError>')
    a=s.index('    if k < N {',s.index('fn row<'));b=s.index('\nfn resistor<',a)
    s=s[:a]+'''    if k<N{s.dc[k]+=i;if FULL{for &(j,g)in d{if j<N{s.j[k][j]+=g;}}}else{s.dc[k]+=d.iter().map(|&(j,g)|if j<N{g*s.now.low[j]}else{0.}).sum::<f64>();}}
    else{s.ports[k-N]+=i;}
}
'''+s[b:]
    s=once(s,'volume::linearize(', 'volume::linearize::<FULL>(')
    s=once(s,'        c.key,\n        true,','        std::array::from_fn(|k| if k < 29 { x.low[k] } else { x.low[54] }),\n        c.key,\n        true,')
    s=once(s,'        for b in 0..30 {','        if FULL {for b in 0..30 {')
    s=once(s,'s.j[i][j] = vol.jacobian[a][b];\n        }','s.j[i][j] = vol.jacobian[a][b];\n        }}')
    s=once(s,'filter::linearize(', 'filter::linearize::<FULL>(')
    s=once(s,'        fp,\n        map.map', '        fp,\n        std::array::from_fn(|k|x.low[k+29]),map.map(|k|if k<N{x.low[k]}else{0.}),\n        map.map')
    s=once(s,'        for b in 0..9 {\n            s.j[r]', '        if FULL {for b in 0..9 {\n            s.j[r]')
    s=once(s,'s.j[r][map[p]] += f.node_port[a][p];\n            }\n        }','s.j[r][map[p]] += f.node_port[a][p];\n            }\n        }}')
    s=once(s,'            for b in 0..9 {','            if FULL {for b in 0..9 {')
    s=once(s,'s.j[a][map[q]] += f.port_port[p][q];\n                }\n            }','s.j[a][map[q]] += f.port_port[p][q];\n                }\n            }}')
    s=once(s,'    for a in 0..N {\n        s.dc[a] += (0..N).map(|b| s.j[a][b] * x.low[b]).sum::<f64>();\n    }','    if FULL {for a in 0..N {\n        s.dc[a] += (0..N).map(|b| s.j[a][b] * x.low[b]).sum::<f64>();\n    }}')
    s=once(s,'                s.mass[i][a] += sign * cf / h;','                if FULL {s.mass[i][a] += sign * cf / h;')
    s=once(s,'s.mass[i][b] -= sign * cf / h;\n                }','s.mass[i][b] -= sign * cf / h;\n                }}')
    s=once(s,'            for (k, jj) in [b, col].into_iter().enumerate() {','            if FULL {for (k, jj) in [b, col].into_iter().enumerate() {')
    s=once(s,'s.mass[i][jj] += j[a][k] / h;\n            }','s.mass[i][jj] += j[a][k] / h;\n            }}')
    return s
def derive():
    return {'crates/rf-d-circuit/src/prepared_volume_residual.rs':volume_source(),'crates/rf-d-circuit/src/prepared_filter_residual.rs':filter_source(),'crates/rf-d-circuit/src/prepared_contour_residual.rs':contour_source()}
