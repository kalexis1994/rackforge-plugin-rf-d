//! Exact f64 SIMD across independent laws, elimination columns and readout nodes.
use std::arch::wasm32::*;

use super::{broadcast, data, Error};

const SERIES: [f64; 11] = [
    1. / 2., 1. / 6., 1. / 24., 1. / 120., 1. / 720., 1. / 5040.,
    1. / 40320., 1. / 362880., 1. / 3628800., 1. / 39916800., 1. / 479001600.,
];

#[inline]
pub fn law(index: usize, z: [f64; 12]) -> Result<([f64; 12], [f64; 12]), Error> {
    let mut current = [0.; 12];
    let mut slope = [0.; 12];
    for lane in (0..12).step_by(2) {
        // All four arrays have room for both lanes. Wasm permits unaligned accesses.
        let input = unsafe { v128_load(z.as_ptr().add(lane).cast()) };
        let magnitude = f64x2_abs(input);
        if !i64x2_all_true(f64x2_le(magnitude, f64x2_splat(40.))) {
            return Err(Error::Domain);
        }
        let mut polynomial = f64x2_splat(SERIES[10]);
        for &coefficient in SERIES[..10].iter().rev() {
            polynomial = f64x2_add(f64x2_splat(coefficient), f64x2_mul(input, polynomial));
        }
        let mut defect = f64x2_mul(f64x2_mul(input, input), polynomial);
        let mut em1 = f64x2_add(input, defect);
        let large = i64x2_bitmask(f64x2_ge(magnitude, f64x2_splat(0.125)));
        if large & 1 != 0 {
            let x = f64x2_extract_lane::<0>(input);
            let exp = x.exp_m1();
            defect = f64x2_replace_lane::<0>(defect, exp - x);
            em1 = f64x2_replace_lane::<0>(em1, exp);
        }
        if large & 2 != 0 {
            let x = f64x2_extract_lane::<1>(input);
            let exp = x.exp_m1();
            defect = f64x2_replace_lane::<1>(defect, exp - x);
            em1 = f64x2_replace_lane::<1>(em1, exp);
        }
        let scale = unsafe { v128_load(data::IEXP[index].as_ptr().add(lane).cast()) };
        unsafe {
            v128_store(current.as_mut_ptr().add(lane).cast(), f64x2_mul(scale, defect));
            v128_store(slope.as_mut_ptr().add(lane).cast(), f64x2_mul(scale, em1));
        }
    }
    Ok((current, slope))
}

#[inline(always)]
fn eliminate<const K: usize>(a: &mut [[f64; 6]; 6], b: &mut [f64; 6]) -> Result<(), Error> {
    let mut pivot = K;
    for row in K + 1..6 {
        if a[row][K].abs() > a[pivot][K].abs() {
            pivot = row;
        }
    }
    if a[pivot][K].abs() < 1e-28 {
        return Err(Error::Singular);
    }
    if pivot != K {
        a.swap(K, pivot);
        b.swap(K, pivot);
    }
    let pivot_row = a[K];
    for row in K + 1..6 {
        let factor = a[row][K] / pivot_row[K];
        a[row][K] = 0.;
        let mut col = K + 1;
        while col + 1 < 6 {
            // Each lane performs the original subtraction on one trailing column.
            unsafe {
                let dest = a[row].as_mut_ptr().add(col).cast();
                let coefficients = v128_load(pivot_row.as_ptr().add(col).cast());
                let product = f64x2_mul(f64x2_splat(factor), coefficients);
                v128_store(dest, f64x2_sub(v128_load(dest), product));
            }
            col += 2;
        }
        if col < 6 {
            a[row][col] -= factor * pivot_row[col];
        }
        b[row] -= factor * b[K];
    }
    Ok(())
}

#[inline]
pub fn solve(mut a: [[f64; 6]; 6], mut b: [f64; 6]) -> Result<[f64; 6], Error> {
    eliminate::<0>(&mut a, &mut b)?;
    eliminate::<1>(&mut a, &mut b)?;
    eliminate::<2>(&mut a, &mut b)?;
    eliminate::<3>(&mut a, &mut b)?;
    eliminate::<4>(&mut a, &mut b)?;
    eliminate::<5>(&mut a, &mut b)?;
    let mut x = [0.; 6];
    for k in (0..6).rev() {
        let mut value = b[k];
        for j in k + 1..6 {
            value -= a[k][j] * x[j];
        }
        x[k] = value / a[k][k];
    }
    Ok(x)
}

const PORTS: [usize; 4] = [66, 6, 61, 61];

const fn port_columns<const COLS: usize>(matrix: &[[[f64; COLS]; 68]; 3]) -> [[[f64; 4]; COLS]; 3] {
    let mut output = [[[0.; 4]; COLS]; 3];
    let mut index = 0;
    while index < 3 {
        let mut column = 0;
        while column < COLS {
            let mut row = 0;
            while row < 4 {
                output[index][column][row] = matrix[index][PORTS[row]][column];
                row += 1;
            }
            column += 1;
        }
        index += 1;
    }
    output
}

const XQ: [[[f64; 4]; 18]; 3] = port_columns(&data::XQ);
const XD: [[[f64; 4]; 12]; 3] = port_columns(&data::XD);

#[inline]
pub fn ports(index: usize, input: f64, history: &[f64; 18], defects: &[f64; 12]) -> [f64; 4] {
    let mut volts = PORTS.map(|node| data::XU[index][node] * input);
    broadcast::accumulate::<4, 18, 2, false>(&mut volts, &XQ[index], history);
    broadcast::accumulate::<4, 12, 2, true>(&mut volts, &XD[index], defects);
    std::array::from_fn(|i| data::DC[index][PORTS[i]] + volts[i])
}
