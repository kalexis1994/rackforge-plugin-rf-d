"""Contiguous transfers of all child coefficients, keeping shared-row sums."""
from prepare_hybrid_stamp import once
def transform(g):
    old='for a in 0..56 {s.dc[a]=dual.dc[a];s.dq[a]=dual.dq[a];if FULL{for b in 0..56{let g=dual.j[a][b];let m=dual.mass[a][b];if !g.is_finite()||!m.is_finite(){return Err(StepError::ExponentialDomain);}s.j[a][b]=g;s.mass[a][b]=m;}}}'
    new='''for a in 0..56 {s.dc[a]=dual.dc[a];s.dq[a]=dual.dq[a];if FULL{
        let j=&dual.j[a];let mass=&dual.mass[a];
        if j.iter().chain(mass.iter()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
        s.j[a][..56].copy_from_slice(j);s.mass[a][..56].copy_from_slice(mass);
    }}'''
    g=once(g,old,new)
    old='if FULL{for b in 0..68 {let j=chain_index(b);let g=audio.dc_jacobian[a][b];let m=audio.mass_over_h[a][b];if g!=0.{s.j[i][j]+=g;if !s.j[i][j].is_finite(){return Err(StepError::ExponentialDomain);}}if m!=0.{s.mass[i][j]+=m;if !s.mass[i][j].is_finite(){return Err(StepError::ExponentialDomain);}}}}'
    new='''if FULL{
            let j=&audio.dc_jacobian[a];let mass=&audio.mass_over_h[a];
            if j.iter().chain(mass.iter()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
            if i<56{
                // Only physical overlap rows 54/55 add to a contour row.
                for b in 0..68{let k=chain_index(b);let g=j[b];let m=mass[b];
                    if g!=0.{s.j[i][k]+=g;if !s.j[i][k].is_finite(){return Err(StepError::ExponentialDomain);}}
                    if m!=0.{s.mass[i][k]+=m;if !s.mass[i][k].is_finite(){return Err(StepError::ExponentialDomain);}}
                }
            }else{
                // Complete permutation: every one of the 68 columns is read.
                // Adding +0 reproduces old accumulation into a +0 row,
                // including a source coefficient equal to negative zero.
                for (start,len,to) in [(0,5,56),(5,1,55),(6,26,61),(32,1,54),(33,29,87),(62,4,34),(66,2,116)]{
                    for (out,value) in s.j[i][to..to+len].iter_mut().zip(&j[start..start+len]){*out=0.+*value;}
                    for (out,value) in s.mass[i][to..to+len].iter_mut().zip(&mass[start..start+len]){*out=0.+*value;}
                }
            }
        }'''
    g=once(g,old,new)
    return g
