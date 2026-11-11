//! Four independent rows share each input value while retaining column order.
use super::{map, CHARGES, JUNCTIONS};

pub(super) struct Matrix<const R: usize, const C: usize, const G: usize> {
    groups: [[[f64; 4]; C]; G],
}

impl<const R: usize, const C: usize, const G: usize> Matrix<R, C, G> {
    const fn new(rows: &[[f64; C]; R]) -> Self {
        assert!(G == (R + 3) / 4);
        let mut groups = [[[0.; 4]; C]; G];
        let mut row = 0;
        while row < R {
            let mut column = 0;
            while column < C {
                groups[row / 4][column][row % 4] = rows[row][column];
                column += 1;
            }
            row += 1;
        }
        Self { groups }
    }
}

const CHARGE_GROUPS: usize = (CHARGES + 3) / 4;
const JUNCTION_GROUPS: usize = (JUNCTIONS + 3) / 4;
pub(super) const F: Matrix<CHARGES, CHARGES, CHARGE_GROUPS> = Matrix::new(&map::F);
pub(super) const N0: Matrix<CHARGES, JUNCTIONS, CHARGE_GROUPS> = Matrix::new(&map::N0);
pub(super) const N1: Matrix<CHARGES, JUNCTIONS, CHARGE_GROUPS> = Matrix::new(&map::N1);
pub(super) const P: Matrix<JUNCTIONS, JUNCTIONS, JUNCTION_GROUPS> = Matrix::new(&map::P);
pub(super) const ZH: Matrix<JUNCTIONS, CHARGES, JUNCTION_GROUPS> = Matrix::new(&map::ZH);
const XQ: Matrix<6, CHARGES, 2> = Matrix::new(&map::XQ);
const XU: Matrix<6, 3, 2> = Matrix::new(&map::XU);
const XD: Matrix<6, JUNCTIONS, 2> = Matrix::new(&map::XD);

pub(super) fn readout(
    base: &[f64; CHARGES],
    input: &[f64; 3],
    defects: &[f64; JUNCTIONS],
) -> [f64; 6] {
    let charge = product(&XQ, base);
    let source = product(&XU, input);
    let correction = product(&XD, defects);
    std::array::from_fn(|row| map::DC[row] + charge[row] + source[row] - correction[row])
}

#[inline]
pub(super) fn product<const R: usize, const C: usize, const G: usize>(
    matrix: &Matrix<R, C, G>,
    input: &[f64; C],
) -> [f64; R] {
    let mut rows = [[-0.; 4]; G];
    for (output, coefficients) in rows.iter_mut().zip(&matrix.groups) {
        for (column, &value) in coefficients.iter().zip(input) {
            for lane in 0..4 {
                output[lane] += column[lane] * value;
            }
        }
    }
    std::array::from_fn(|row| rows[row / 4][row % 4])
}
