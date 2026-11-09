//! Fixed-size, scaled-pivot elimination for the reduced voice.
use crate::StepError;

pub fn dot<const N: usize>(row: &[f64; N], input: &[f64; N]) -> f64 {
    row.iter().zip(input).map(|(a, b)| a * b).sum()
}

pub fn row_product<const K: usize>(row: &[f64], vectors: &[[f64; K]]) -> [f64; K] {
    let mut result = [0.; K];
    for (&weight, vector) in row.iter().zip(vectors) {
        for (sum, value) in result.iter_mut().zip(vector) {
            *sum += weight * value;
        }
    }
    result
}

pub fn maximum(values: &[f64]) -> f64 {
    values.iter().fold(0_f64, |m, value| m.max(value.abs()))
}

#[cfg(all(target_arch = "x86_64", target_feature = "avx"))]
fn pivot_scale(row: &[f64]) -> f64 {
    use std::arch::x86_64::*;

    let (groups, tail) = row.as_chunks::<4>();
    let mut lanes = [0.; 4];
    // SAFETY: AVX is enabled and every unaligned load and store spans four doubles.
    unsafe {
        let sign = _mm256_set1_pd(-0.0);
        let mut peak = _mm256_setzero_pd();
        for group in groups {
            let abs = _mm256_andnot_pd(sign, _mm256_loadu_pd(group.as_ptr()));
            // With the running peak as the second operand, a NaN input is ignored.
            peak = _mm256_max_pd(abs, peak);
        }
        _mm256_storeu_pd(lanes.as_mut_ptr(), peak);
    }
    maximum(&lanes).max(maximum(tail))
}

#[cfg(not(all(target_arch = "x86_64", target_feature = "avx")))]
use self::maximum as pivot_scale;

pub struct Lu<const N: usize> {
    rows: [[f64; N]; N],
    order: [usize; N],
    start: [usize; N],
    end: [usize; N],
}

impl<const N: usize> Lu<N> {
    pub fn factor(rows: [[f64; N]; N]) -> Result<Self, StepError> {
        Self::factor_prefix(rows, N)
    }

    pub fn factor_contour(rows: [[f64; N]; N]) -> Result<Self, StepError> {
        Self::factor_rows::<true>(rows, N, pivot_scale)
    }

    /// Factor only the leading square block. The suffix is ignored.
    #[inline]
    pub fn factor_prefix(rows: [[f64; N]; N], active: usize) -> Result<Self, StepError> {
        Self::factor_rows::<false>(rows, active, maximum)
    }

    #[inline]
    fn factor_rows<const INDEXED: bool>(
        mut rows: [[f64; N]; N],
        active: usize,
        scale: impl Fn(&[f64]) -> f64,
    ) -> Result<Self, StepError> {
        let mut order = std::array::from_fn(|i| i);
        let mut end = [active; N];
        let mut scales = [0.; N];
        let mut affected = [0; N];
        for i in 0..active {
            scales[i] = scale(&rows[i][..active]);
        }
        for col in 0..active {
            let mut best = 0.;
            let mut pivot = col;
            let mut count = 0;
            for row in col..active {
                let entry = rows[row][col];
                if entry == 0. {
                    continue;
                }
                if INDEXED {
                    affected[count] = row;
                    count += 1;
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
            let (head, tail) = rows[..active].split_at_mut(col + 1);
            let pivot_row = &head[col];
            let diagonal = pivot_row[col];
            let limit = pivot_row[..active].iter().rposition(|x| *x != 0.).unwrap() + 1;
            end[col] = limit;
            let eliminate = |row: &mut [f64; N]| {
                let ratio = row[col] / diagonal;
                row[col] = ratio;
                for j in col + 1..limit {
                    row[j] -= ratio * pivot_row[j];
                }
            };
            if INDEXED {
                for &source in &affected[..count] {
                    if source == pivot {
                        continue;
                    }
                    // The old first row now occupies the selected pivot's slot.
                    let row = if source == col { pivot } else { source };
                    eliminate(&mut tail[row - col - 1]);
                }
            } else {
                for row in tail {
                    if row[col] != 0. {
                        eliminate(row);
                    }
                }
            }
        }
        let mut start = [0; N];
        for i in 0..active {
            start[i] = rows[i][..i]
                .iter()
                .position(|value| *value != 0.)
                .unwrap_or(i);
        }
        Ok(Self {
            rows,
            order,
            start,
            end,
        })
    }

    pub fn solve(&self, rhs: [f64; N]) -> Result<[f64; N], StepError> {
        Ok(self
            .solve_batch(&rhs.map(|value| [value]))?
            .map(|[value]| value))
    }

    pub fn solve_batch<const K: usize>(
        &self,
        rhs: &[[f64; K]; N],
    ) -> Result<[[f64; K]; N], StepError> {
        self.solve_batch_prefix(rhs, N)
    }

    /// Solve the same leading block passed to factor_prefix.
    #[inline]
    pub fn solve_batch_prefix<const K: usize>(
        &self,
        rhs: &[[f64; K]; N],
        active: usize,
    ) -> Result<[[f64; K]; N], StepError> {
        let mut x = [[0.; K]; N];
        for i in 0..active {
            let mut value = rhs[self.order[i]];
            for j in self.start[i]..i {
                let weight = self.rows[i][j];
                for (v, x) in value.iter_mut().zip(x[j]) {
                    *v -= weight * x;
                }
            }
            x[i] = value;
        }
        for i in (0..active).rev() {
            let mut value = x[i];
            for j in i + 1..self.end[i] {
                let weight = self.rows[i][j];
                for (v, x) in value.iter_mut().zip(x[j]) {
                    *v -= weight * x;
                }
            }
            x[i] = value.map(|v| v / self.rows[i][i]);
        }
        if x.iter().flatten().any(|v| !v.is_finite()) {
            return Err(StepError::SingularJacobian);
        }
        Ok(x)
    }
}
