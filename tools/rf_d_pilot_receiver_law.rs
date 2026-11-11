//! Evaluate four independent small-signal junction laws in the same Horner order.
use super::{map, Error, JUNCTIONS};
use crate::pilot_law::{defect_at, REMAINDER_COEFFICIENTS};
use std::arch::x86_64::*;

#[inline]
fn polynomial(
    x: &[f64; 4],
    weights: &[f64; 4],
    defects: &mut [f64; 4],
    slopes: &mut [f64; 4],
) {
    // SAFETY: AVX is enabled and every unaligned load and store spans four doubles.
    unsafe {
        let x = _mm256_loadu_pd(x.as_ptr());
        let weights = _mm256_loadu_pd(weights.as_ptr());
        let (&last, coefficients) = REMAINDER_COEFFICIENTS.split_last().unwrap();
        let mut p = _mm256_set1_pd(last);
        for &c in coefficients.iter().rev() {
            p = _mm256_add_pd(_mm256_set1_pd(c), _mm256_mul_pd(x, p));
        }
        let defect = _mm256_mul_pd(_mm256_mul_pd(x, x), p);
        let em1 = _mm256_add_pd(x, defect);
        _mm256_storeu_pd(defects.as_mut_ptr(), _mm256_mul_pd(weights, defect));
        _mm256_storeu_pd(slopes.as_mut_ptr(), _mm256_mul_pd(weights, em1));
    }
}

pub(super) fn law(z: [f64; JUNCTIONS]) -> Result<([f64; JUNCTIONS], [f64; JUNCTIONS]), Error> {
    let mut defects = [0.; JUNCTIONS];
    let mut slopes = [0.; JUNCTIONS];
    let (groups, tail) = z.as_chunks::<4>();
    let (weights, tail_weights) = map::IEXP.as_chunks::<4>();
    let (defect_groups, tail_defects) = defects.as_chunks_mut::<4>();
    let (slope_groups, tail_slopes) = slopes.as_chunks_mut::<4>();
    for i in 0..groups.len() {
        let x = &groups[i];
        if x.iter().all(|&v| v.abs() < 0.125) {
            polynomial(x, &weights[i], &mut defect_groups[i], &mut slope_groups[i]);
        } else {
            for lane in 0..4 {
                (defect_groups[i][lane], slope_groups[i][lane]) =
                    defect_at(x[lane], weights[i][lane])?;
            }
        }
    }
    for i in 0..tail.len() {
        (tail_defects[i], tail_slopes[i]) = defect_at(tail[i], tail_weights[i])?;
    }
    Ok((defects, slopes))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn retains_scalar_bits_and_domain() {
        let near = f64::from_bits(0.125_f64.to_bits() - 1);
        let values = [0., -0., f64::MIN_POSITIVE, -near, near, 0.125, -0.125, 40., -40.];
        for offset in 0..values.len() {
            let z = std::array::from_fn(|i| values[(i + offset) % values.len()]);
            let (defects, slopes) = law(z).unwrap();
            let (scalar_defects, scalar_slopes) = crate::pilot_law::law(z).unwrap();
            assert_eq!(defects.map(f64::to_bits), scalar_defects.map(f64::to_bits));
            assert_eq!(slopes.map(f64::to_bits), scalar_slopes.map(f64::to_bits));
        }
        for invalid in [f64::NAN, f64::INFINITY, -41., 41.] {
            for index in [0, JUNCTIONS - 1] {
                let mut z = [0.; JUNCTIONS];
                z[index] = invalid;
                assert!(matches!(law(z), Err(Error::Domain)));
            }
        }
    }
}
