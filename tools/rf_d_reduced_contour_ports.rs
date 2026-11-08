//! Two-terminal contour/audio closure across two Radau stages.
pub const N: usize = 4;
pub type Matrix = [[f64; N]; N];
pub type Ports = [f64; N];

#[derive(Clone, Copy)]
pub struct Reaction {
    pub jacobian: Matrix,
    /// Current leaving the shared nodes at zero port increment.
    pub current_a: Ports,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Nonfinite,
    Singular,
}

/// The signs of the two reactions follow the same physical node KCL.
pub fn close(contour: Reaction, audio: Reaction) -> Result<Ports, Error> {
    let mut matrix: Matrix = std::array::from_fn(|i| {
        std::array::from_fn(|j| contour.jacobian[i][j] + audio.jacobian[i][j])
    });
    let mut rhs: Ports = std::array::from_fn(|i| -(contour.current_a[i] + audio.current_a[i]));
    if matrix.iter().flatten().chain(&rhs).any(|x| !x.is_finite()) {
        return Err(Error::Nonfinite);
    }
    let mut scales = matrix.map(|row| row.into_iter().map(f64::abs).fold(0., f64::max));
    if scales.contains(&0.) {
        return Err(Error::Singular);
    }
    for col in 0..N {
        let mut pivot = col;
        let mut best = 0.;
        for row in col..N {
            let magnitude = matrix[row][col].abs() / scales[row];
            if magnitude > best {
                best = magnitude;
                pivot = row;
            }
        }
        if best < 1e-12 {
            return Err(Error::Singular);
        }
        matrix.swap(col, pivot);
        rhs.swap(col, pivot);
        scales.swap(col, pivot);
        for row in col + 1..N {
            let factor = matrix[row][col] / matrix[col][col];
            for k in col + 1..N {
                matrix[row][k] -= factor * matrix[col][k];
            }
            rhs[row] -= factor * rhs[col];
        }
    }
    let mut solution = [0.; N];
    for row in (0..N).rev() {
        let mut value = rhs[row];
        for k in row + 1..N {
            value -= matrix[row][k] * solution[k];
        }
        solution[row] = value / matrix[row][row];
    }
    if solution.iter().any(|value| !value.is_finite()) {
        return Err(Error::Nonfinite);
    }
    Ok(solution)
}
