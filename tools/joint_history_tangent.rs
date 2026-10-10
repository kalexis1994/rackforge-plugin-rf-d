//! Fixed-step laboratory sensitivity, absolute stage coordinates.
//! See VOZ_TANGENTE_HISTORIA_PROTOCOLO; not an adaptive/periodic derivative.
use rf_d_circuit::{joint_voice as j,StepError};
pub fn old_mass(p:j::Parameters,x:j::State,h:f64)->Result<[[f64;j::N];j::N],StepError> {
 Ok(j::parts(p,x,j::State::from_nodes([0.;j::N]),h)?.mass_over_h)
}
pub fn history(m:&[[f64;j::N];j::N],row:usize,col:usize)->f64 {
 -(j::B[row/j::N][0]+j::B[row/j::N][1])*m[row%j::N][col]
}
pub fn response(p:j::Parameters,x:j::State,d:[j::State;2],h:f64,m:&[[f64;j::N];j::N],col:usize)->Result<[f64;j::M],StepError> {
 let a=j::linearize(p,x,d,h)?;
 solve(a.jacobian,std::array::from_fn(|k|-history(m,k,col)))
}

fn solve<const M: usize>(
    mut j: [[f64; M]; M],
    mut rhs: [f64; M],
) -> Result<[f64; M], StepError> {
    let mut scale = [0.0; M];
    for i in 0..M {
        scale[i] = j[i].iter().fold(0_f64,|a,v|a.max(v.abs()));
        if scale[i] == 0.0 {
            return Err(StepError::SingularJacobian);
        }
    }
    for col in 0..M {
        let mut pivot = col;
        let mut best = 0.0;
        for row in col..M {
            if j[row][col] == 0.0 {
                continue;
            }
            let score = j[row][col].abs() / scale[row];
            if score > best {
                best = score;
                pivot = row;
            }
        }
        if best < 1e-12 {
            return Err(StepError::SingularJacobian);
        }
        j.swap(col, pivot);
        rhs.swap(col, pivot);
        scale.swap(col, pivot);
        let diagonal = j[col][col];
        for row in (col + 1)..M {
            if j[row][col] == 0.0 {
                continue;
            }
            let factor = j[row][col] / diagonal;
            j[row][col] = 0.0;
            #[allow(clippy::needless_range_loop)]
            for k in (col + 1)..M {
                j[row][k] -= factor * j[col][k];
            }
            rhs[row] -= factor * rhs[col];
        }
    }
    let mut out = [0.0; M];
    for row in (0..M).rev() {
        let mut value = rhs[row];
        for k in (row + 1)..M {
            value -= j[row][k] * out[k];
        }
        out[row] = value / j[row][row];
    }
    if out.iter().any(|v| !v.is_finite()) {
        return Err(StepError::SingularJacobian);
    }
    Ok(out)
}


