"""Stage-contiguous Radau matrix, preserving each scalar expression."""
from prepare_dual_chain import ROOT
from prepare_hybrid_stamp import once

def candidate():
    voice=(ROOT/'crates/rf-d-circuit/src/prepared_hybrid_voice.rs').read_text(encoding='utf8')
    a=voice.index('    let jacobian = ');b=voice.index('    let system = ',a)
    old=voice[a:b]
    new='''    let jacobian = |s:&[Parts;2]|->[[f64;M];M]{
        let mut j=[[0.;M];M];
        for i in 0..2{for jj in 0..2{
            let stage=&s[jj];let weight=B[i][jj];
            for a in 0..N{let row=&mut j[i*N+a];
                let mass=&stage.mass[a];let dc=&stage.j[a];
                for b in 0..N{row[jj*N+b]=weight*mass[b]+if i==jj{dc[b]}else{0.};}
            }
        }}j
    };
'''
    voice=once(voice,old,new)
    probe=(ROOT/'tools/hybrid_linear_probe.rs').read_text(encoding='utf8')
    probe=once(probe,'profiled_hybrid_voice.rs','stage_hybrid_voice.rs')
    local=(ROOT/'tools/hybrid_schur_local.rs').read_text(encoding='utf8')
    local=once(local,'hybrid_nominal_voice.rs','stage_hybrid_voice.rs')
    local=local.replace('let a=parts(p,','let a=parts::<true>(p,').replace('let b=parts(p,','let b=parts::<true>(p,')
    marker='        let mut rhses=[[0.;M];8];'
    test='''        let mut contiguous=[[0.;M];M];
        for i in 0..2{for jj in 0..2{let stage=&s[jj];let weight=B[i][jj];
            for a in 0..N{let row=&mut contiguous[i*N+a];let mass=&stage.mass[a];let dc=&stage.j[a];
                for b in 0..N{row[jj*N+b]=weight*mass[b]+if i==jj{dc[b]}else{0.};}
            }
        }}
        for i in 0..M{for k in 0..M{assert_eq!(j[i][k].to_bits(),contiguous[i][k].to_bits());}}
        let valid=w.solve(&j,r.map(|v|-v)).unwrap();
        let mut corrupt=j;corrupt[54][54]=f64::NAN;
        assert!(w.solve(&corrupt,r.map(|v|-v)).is_err());
        assert_eq!(w.solve(&j,r.map(|v|-v)).unwrap(),valid);
'''
    local=once(local,marker,test+marker)
    return {'crates/rf-d-circuit/src/stage_hybrid_voice.rs':voice,'tools/hybrid_stage_probe.rs':probe,'tools/hybrid_stage_local.rs':local}

if __name__=="__main__":
    for n,s in candidate().items():
        p=ROOT/n;assert not p.exists();p.write_text(s,encoding="utf8",newline="\n")
