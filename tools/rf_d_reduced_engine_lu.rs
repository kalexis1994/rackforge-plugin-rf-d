//! Fixed-size, scaled-pivot elimination for the reduced voice.
use crate::StepError;

pub fn dot<const N: usize>(row: &[f64; N], input: &[f64; N]) -> f64 {
    row.iter().zip(input).map(|(a, b)| a * b).sum()
}

pub fn maximum(values: &[f64]) -> f64 {
    values.iter().fold(0_f64, |m, value| m.max(value.abs()))
}

pub struct Lu<const N: usize> {
    rows: [[f64; N]; N],
    order: [usize; N],
    end: [usize; N],
}

impl<const N: usize> Lu<N> {
    pub fn factor(mut rows: [[f64; N]; N]) -> Result<Self, StepError> {
        let mut order = std::array::from_fn(|i| i);
        let mut end = [N; N];
        let mut scales = rows.each_ref().map(|row| maximum(row));
        for col in 0..N {
            let mut best = 0.;
            let mut pivot = col;
            for row in col..N {
                let entry = rows[row][col];
                if entry == 0. {
                    continue;
                }
                let score = entry.abs() / scales[row];
                if score > best {
                    best = score;
                    pivot = row;
                }
            }
            if !best.is_finite() || best < 1e-12 {
                return Err(StepError::SingularJacobian);
            }
            rows.swap(col, pivot);
            order.swap(col, pivot);
            scales.swap(col, pivot);
            let (head, tail) = rows.split_at_mut(col + 1);
            let pivot_row = &head[col];
            let diagonal = pivot_row[col];
            let limit = pivot_row.iter().rposition(|x| *x != 0.).unwrap() + 1;
            end[col] = limit;
            for row in tail {
                if row[col] == 0. {
                    continue;
                }
                let ratio = row[col] / diagonal;
                row[col] = ratio;
                for j in col + 1..limit {
                    row[j] -= ratio * pivot_row[j];
                }
            }
        }
        Ok(Self { rows, order, end })
    }

    pub fn solve(&self, rhs: [f64; N]) -> Result<[f64; N], StepError> {
        let mut x = [0.; N];
        for i in 0..N {
            let mut value = rhs[self.order[i]];
            for j in 0..i {
                value -= self.rows[i][j] * x[j];
            }
            x[i] = value;
        }
        for i in (0..N).rev() {
            let mut value = x[i];
            for j in i + 1..self.end[i] {
                value -= self.rows[i][j] * x[j];
            }
            x[i] = value / self.rows[i][i];
        }
        if x.iter().any(|v| !v.is_finite()) {
            return Err(StepError::SingularJacobian);
        }
        Ok(x)
    }
}
