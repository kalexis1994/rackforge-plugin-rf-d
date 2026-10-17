use rf_d_circuit::StepError;
pub(crate) fn max_abs<const M: usize>(x: &[f64; M]) -> f64 {
    x.iter().fold(0.0_f64, |a, v| a.max(v.abs()))
}
pub(crate) fn solve_linear_sparse<const M: usize>(
    j: [[f64; M]; M],
    rhs: [f64; M],
) -> Result<[f64; M], StepError> {
    solve_linear_internal::<M, true>(j, rhs)
}

fn solve_linear_internal<const M: usize, const SKIP_ZERO: bool>(
    mut j: [[f64; M]; M],
    mut rhs: [f64; M],
) -> Result<[f64; M], StepError> {
    let mut scale = [0.0; M];
    for i in 0..M {
        scale[i] = max_abs(&j[i]);
        if scale[i] == 0.0 {
            return Err(StepError::SingularJacobian);
        }
    }
    for col in 0..M {
        let mut pivot = col;
        let mut best = 0.0;
        for row in col..M {
            if SKIP_ZERO && j[row][col] == 0.0 {
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
            if SKIP_ZERO && j[row][col] == 0.0 {
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

