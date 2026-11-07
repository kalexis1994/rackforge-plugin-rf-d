//! Column-major storage for the even Newton solve. Every row keeps its pivot order.
use std::arch::wasm32::{f64x2_div, f64x2_mul, f64x2_splat, f64x2_sub, v128_load, v128_store};

use super::{data, Error};

const fn even_columns() -> [[[f64; 6]; 6]; 3] {
    let mut result = [[[0.; 6]; 6]; 3];
    let mut index = 0;
    while index < 3 {
        let mut column = 0;
        while column < 6 {
            let mut row = 0;
            while row < 6 {
                result[index][column][row] = data::P[index][2 * row][2 * column];
                row += 1;
            }
            column += 1;
        }
        index += 1;
    }
    result
}

const EVEN: [[[f64; 6]; 6]; 3] = even_columns();

#[inline(always)]
fn eliminate<const K: usize>(a: &mut [[f64; 6]; 6], b: &mut [f64; 6]) -> Result<(), Error> {
    let mut pivot = K;
    for row in K + 1..6 {
        if a[K][row].abs() > a[K][pivot].abs() {
            pivot = row;
        }
    }
    if a[K][pivot].abs() < 1e-28 {
        return Err(Error::Singular);
    }
    if pivot != K {
        for column in a.iter_mut() {
            column.swap(K, pivot);
        }
        b.swap(K, pivot);
    }
    let diagonal = a[K][K];
    let pivot_rhs = b[K];
    let mut row = K + 1;
    while row + 1 < 6 {
        // Each pointer covers exactly two valid adjacent rows.
        unsafe {
            let factors = f64x2_div(v128_load(a[K].as_ptr().add(row).cast()), f64x2_splat(diagonal));
            for column in &mut a[K + 1..] {
                let pivot_value = column[K];
                let destination = column.as_mut_ptr().add(row).cast();
                let update = f64x2_mul(factors, f64x2_splat(pivot_value));
                v128_store(destination, f64x2_sub(v128_load(destination), update));
            }
            let rhs = b.as_mut_ptr().add(row).cast();
            v128_store(rhs, f64x2_sub(v128_load(rhs), f64x2_mul(factors, f64x2_splat(pivot_rhs))));
        }
        a[K][row] = 0.;
        a[K][row + 1] = 0.;
        row += 2;
    }
    if row < 6 {
        let factor = a[K][row] / diagonal;
        a[K][row] = 0.;
        for column in &mut a[K + 1..] {
            column[row] -= factor * column[K];
        }
        b[row] -= factor * b[K];
    }
    Ok(())
}

#[inline]
pub fn solve(index: usize, slope: &[f64; 12], residual: &[f64; 12]) -> Result<[f64; 6], Error> {
    let mut a = std::array::from_fn(|column| {
        let values = &EVEN[index][column];
        let multiplier = f64x2_splat(slope[2 * column]);
        let mut result = [0.; 6];
        for row in (0..6).step_by(2) {
            unsafe {
                let pair = v128_load(values.as_ptr().add(row).cast());
                v128_store(result.as_mut_ptr().add(row).cast(), f64x2_mul(pair, multiplier));
            }
        }
        result[column] = 1. + result[column];
        result
    });
    let mut b = std::array::from_fn(|row| residual[2 * row]);
    eliminate::<0>(&mut a, &mut b)?;
    eliminate::<1>(&mut a, &mut b)?;
    eliminate::<2>(&mut a, &mut b)?;
    eliminate::<3>(&mut a, &mut b)?;
    eliminate::<4>(&mut a, &mut b)?;
    eliminate::<5>(&mut a, &mut b)?;
    let mut x = [0.; 6];
    for row in (0..6).rev() {
        let mut value = b[row];
        for column in row + 1..6 {
            value -= a[column][row] * x[column];
        }
        x[row] = value / a[row][row];
    }
    Ok(x)
}
