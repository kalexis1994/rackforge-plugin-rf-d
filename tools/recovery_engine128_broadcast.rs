//! Broadcast one column value to all pairs before advancing the scalar order.
use std::arch::wasm32::{f64x2_add, f64x2_mul, f64x2_splat, f64x2_sub, v128, v128_load, v128_store};

pub fn accumulate<const ROWS: usize, const COLS: usize, const PAIRS: usize, const SUBTRACT: bool>(
    output: &mut [f64; ROWS],
    matrix: &[[f64; ROWS]; COLS],
    input: &[f64; COLS],
) {
    const { assert!(ROWS == PAIRS * 2) };
    // Each pointer covers an in-bounds pair. Wasm permits unaligned accesses.
    let mut lanes: [v128; PAIRS] = std::array::from_fn(|pair| unsafe {
        v128_load(output.as_ptr().add(2 * pair).cast())
    });
    for (column, &value) in matrix.iter().zip(input) {
        let broadcast = f64x2_splat(value);
        for (pair, accumulator) in lanes.iter_mut().enumerate() {
            let coefficients = unsafe { v128_load(column.as_ptr().add(2 * pair).cast()) };
            let product = f64x2_mul(coefficients, broadcast);
            *accumulator = if SUBTRACT {
                f64x2_sub(*accumulator, product)
            } else {
                f64x2_add(*accumulator, product)
            };
        }
    }
    for (pair, accumulator) in lanes.into_iter().enumerate() {
        unsafe { v128_store(output.as_mut_ptr().add(2 * pair).cast(), accumulator) };
    }
}
