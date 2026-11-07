//! Explicit SIMD locals for the fixed row counts used by the recovery maps.
use std::arch::wasm32::{f64x2_add, f64x2_mul, f64x2_splat, f64x2_sub, v128_load, v128_store};

// The dispatch checks the row count. Each load and store covers one in-bounds pair.
macro_rules! accumulate_pairs {
    ($name:ident, $($sum:ident @ $offset:literal),+) => {
        #[inline]
        fn $name<const ROWS: usize, const COLS: usize, const SUBTRACT: bool>(
            output: &mut [f64; ROWS],
            matrix: &[[f64; ROWS]; COLS],
            input: &[f64; COLS],
        ) {
            $(let mut $sum = unsafe { v128_load(output.as_ptr().add($offset).cast()) };)+
            for (column, &value) in matrix.iter().zip(input) {
                let broadcast = f64x2_splat(value);
                $(
                    let coefficient = unsafe { v128_load(column.as_ptr().add($offset).cast()) };
                    let product = f64x2_mul(coefficient, broadcast);
                    $sum = if SUBTRACT { f64x2_sub($sum, product) } else { f64x2_add($sum, product) };
                )+
            }
            $(unsafe { v128_store(output.as_mut_ptr().add($offset).cast(), $sum) };)+
        }
    };
}

accumulate_pairs!(two, a @ 0, b @ 2);
accumulate_pairs!(six, a @ 0, b @ 2, c @ 4, d @ 6, e @ 8, f @ 10);
accumulate_pairs!(nine, a @ 0, b @ 2, c @ 4, d @ 6, e @ 8, f @ 10, g @ 12, h @ 14, i @ 16);

#[inline]
pub fn accumulate<const ROWS: usize, const COLS: usize, const PAIRS: usize, const SUBTRACT: bool>(
    output: &mut [f64; ROWS],
    matrix: &[[f64; ROWS]; COLS],
    input: &[f64; COLS],
) {
    const { assert!(ROWS == 2 * PAIRS) };
    match PAIRS {
        2 => two::<ROWS, COLS, SUBTRACT>(output, matrix, input),
        6 => six::<ROWS, COLS, SUBTRACT>(output, matrix, input),
        9 => nine::<ROWS, COLS, SUBTRACT>(output, matrix, input),
        _ => unreachable!("unsupported SIMD row count"),
    }
}
