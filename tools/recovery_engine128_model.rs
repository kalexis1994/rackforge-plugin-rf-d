//! Column order of the odd Newton correction, with independent rows in SIMD.
use std::arch::wasm32::{
    f64x2, f64x2_abs, f64x2_extract_lane, f64x2_le, f64x2_mul, f64x2_splat, f64x2_sub,
    i64x2_all_true, v128, v128_load,
};

use super::data;

const fn odd_columns() -> [[[f64; 6]; 6]; 3] {
    let mut coefficients = [[[0.; 6]; 6]; 3];
    let mut index = 0;
    while index < 3 {
        let mut column = 0;
        while column < 6 {
            let mut row = 0;
            while row < 6 {
                coefficients[index][column][row] = data::P[index][2 * row + 1][2 * column];
                row += 1;
            }
            column += 1;
        }
        index += 1;
    }
    coefficients
}

const ODD: [[[f64; 6]; 6]; 3] = odd_columns();

#[inline]
pub fn update(index: usize, z: &mut [f64; 12], residual: &[f64; 12], slope: &[f64; 12], even: &[f64; 6]) {
    let mut rows: [v128; 3] = std::array::from_fn(|pair| f64x2(residual[4 * pair + 1], residual[4 * pair + 3]));
    for column in 0..6 {
        let slope = f64x2_splat(slope[2 * column]);
        let even = f64x2_splat(even[column]);
        for (pair, row) in rows.iter_mut().enumerate() {
            // The transposed column contains two adjacent coefficients per pair.
            let coefficient = unsafe { v128_load(ODD[index][column].as_ptr().add(2 * pair).cast()) };
            let scaled = f64x2_mul(coefficient, slope);
            *row = f64x2_sub(*row, f64x2_mul(scaled, even));
        }
    }
    for (pair, row) in rows.into_iter().enumerate() {
        z[4 * pair] -= even[2 * pair];
        z[4 * pair + 1] -= f64x2_extract_lane::<0>(row);
        z[4 * pair + 2] -= even[2 * pair + 1];
        z[4 * pair + 3] -= f64x2_extract_lane::<1>(row);
    }
}

#[inline]
pub fn finite(q: &[f64; 18]) -> bool {
    for pair in (0..18).step_by(2) {
        let values = unsafe { v128_load(q.as_ptr().add(pair).cast()) };
        if !i64x2_all_true(f64x2_le(f64x2_abs(values), f64x2_splat(f64::MAX))) {
            return false;
        }
    }
    true
}
