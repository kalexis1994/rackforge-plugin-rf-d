//! Independent rows in SIMD lanes. Each row keeps its scalar column order.
use std::arch::wasm32::{f64x2_add, f64x2_mul, f64x2_splat, f64x2_sub, v128, v128_load, v128_store};

use super::data;

const fn transpose<const ROWS: usize, const COLS: usize>(
    matrix: &[[[f64; COLS]; ROWS]; 3],
) -> [[[f64; ROWS]; COLS]; 3] {
    let mut result = [[[0.0; ROWS]; COLS]; 3];
    let mut model = 0;
    while model < 3 {
        let mut row = 0;
        while row < ROWS {
            let mut column = 0;
            while column < COLS {
                result[model][column][row] = matrix[model][row][column];
                column += 1;
            }
            row += 1;
        }
        model += 1;
    }
    result
}

pub const F: [[[f64; 18]; 18]; 3] = transpose(&data::F);
pub const N0: [[[f64; 18]; 12]; 3] = transpose(&data::N0);
pub const N1: [[[f64; 18]; 12]; 3] = transpose(&data::N1);
pub const ZH: [[[f64; 12]; 18]; 3] = transpose(&data::ZH);
pub const P: [[[f64; 12]; 12]; 3] = transpose(&data::P);

pub fn accumulate<const ROWS: usize, const COLS: usize, const SUBTRACT: bool>(
    output: &mut [f64; ROWS],
    matrix: &[[f64; ROWS]; COLS],
    input: &[f64; COLS],
) {
    const { assert!(ROWS % 2 == 0) };
    for row in (0..ROWS).step_by(2) {
        // Every load/store covers two adjacent f64 lanes within the array.
        // The Wasm intrinsics permit an unaligned address.
        let destination = unsafe { output.as_mut_ptr().add(row).cast::<v128>() };
        let mut lanes = unsafe { v128_load(destination) };
        for (column, &value) in matrix.iter().zip(input) {
            let coefficients = unsafe { v128_load(column.as_ptr().add(row).cast()) };
            let product = f64x2_mul(coefficients, f64x2_splat(value));
            lanes = if SUBTRACT {
                f64x2_sub(lanes, product)
            } else {
                f64x2_add(lanes, product)
            };
        }
        unsafe { v128_store(destination, lanes) };
    }
}
