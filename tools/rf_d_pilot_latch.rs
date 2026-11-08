//! Charge-conserving Q25/Q15 core with five explicit surrounding circuit voltages.
use crate::{
    latch_charge::{terminal, VT},
    reduced_lu::{maximum, Lu},
    StepError,
};

pub const CORE: [usize; 5] = [23, 25, 26, 27, 28];
pub const BOUNDARY: [usize; 5] = [17, 6, 9, 4, 24];
const C4: f64 = 10e-9;
const B: [[f64; 2]; 2] = [[1.5, 0.5], [-4.5, 2.5]];

#[derive(Clone, Copy)]
pub struct State(pub [f64; 5]);

impl State {
    pub fn order(self) -> bool {
        self.0[2] >= self.0[4]
    }
}

pub struct Stamp {
    pub dc: [f64; 5],
    pub charge_c: [f64; 5],
    conductance: [[f64; 5]; 5],
    capacitance: [[f64; 5]; 5],
}

impl Stamp {
    fn resistor(&mut self, row: usize, other: Option<usize>, difference: f64, ohm: f64) {
        let g = 1. / ohm;
        self.dc[row] += difference * g;
        self.conductance[row][row] += g;
        if let Some(j) = other {
            self.dc[j] -= difference * g;
            self.conductance[row][j] -= g;
            self.conductance[j][row] -= g;
            self.conductance[j][j] += g;
        }
    }
}

fn junction(v: f64, is_a: f64, scale: f64) -> Result<(f64, f64), StepError> {
    let z = v / scale;
    if !z.is_finite() || z > 45. {
        return Err(StepError::ExponentialDomain);
    }
    Ok((is_a * z.exp_m1(), is_a * z.exp() / scale))
}

// Series R36/CR8. Solving for diode voltage gives a monotone scalar KCL.
fn cr8_series(delta_v: f64) -> Result<(f64, f64), StepError> {
    let scale = 1.5 * VT;
    let ratio = 10_000. * 1e-8 / scale;
    let source = delta_v / scale;
    let mut exponent = if source > 0. {
        source.min((source / ratio).ln_1p())
    } else {
        source
    };
    for _ in 0..12 {
        let (i, g) = junction(exponent * scale, 1e-8, scale)?;
        let residual = exponent + 10_000. * i / scale - source;
        if residual.abs() <= 2e-13 {
            return Ok((i, g / (1. + 10_000. * g)));
        }
        exponent -= residual / (1. + 10_000. * g);
    }
    Err(StepError::IterationBudget)
}

pub fn stamp(
    old: State,
    new: State,
    boundary: [f64; 5],
    series_cr8: bool,
) -> Result<Stamp, StepError> {
    let x = new.0;
    let [reset, attack_base, decay_emitter, cr6, cr8] = boundary;
    let mut s = Stamp {
        dc: [0.; 5],
        charge_c: [0.; 5],
        conductance: [[0.; 5]; 5],
        capacitance: [[0.; 5]; 5],
    };
    s.resistor(0, None, x[0] - reset, 10_000.);
    s.resistor(1, Some(4), x[1] - x[4], 10_000.);
    s.resistor(2, None, x[2] - attack_base, 3_300.);
    s.resistor(2, Some(3), x[2] - x[3], 33_000.);
    s.resistor(4, None, x[4] - 9.3, 10_000.);
    // Q17 base loads the Q25 collector. Its other terminals are explicit.
    let (f, gf) = junction(x[2] - decay_emitter, 1e-14, VT)?;
    let (r, gr) = junction(x[2] - 9.3, 1e-14, VT)?;
    s.dc[2] += f / 100. + r / 5.;
    s.conductance[2][2] += gf / 100. + gr / 5.;
    let cr8 = if series_cr8 {
        cr8_series(cr8 - x[3])?
    } else {
        junction(cr8 - x[3], 1e-8, 1.5 * VT)?
    };
    for (i, g) in [junction(cr6 - x[3], 1e-8, 1.5 * VT)?, cr8] {
        s.dc[3] -= i;
        s.conductance[3][3] += g;
    }
    // Both plates of C4 share a single oriented charge increment.
    let q4 = C4 * ((x[0] - old.0[0]) - (x[1] - old.0[1]));
    s.charge_c[0] += q4;
    s.charge_c[1] -= q4;
    s.capacitance[0][0] += C4;
    s.capacitance[0][1] -= C4;
    s.capacitance[1][0] -= C4;
    s.capacitance[1][1] += C4;
    for [b, c] in [[1, 2], [3, 4]] {
        let (f, gf) = junction(x[b], 1e-14, VT)?;
        let (r, gr) = junction(x[b] - x[c], 1e-14, VT)?;
        s.dc[b] += f / 100. + r / 5.;
        s.dc[c] += f - 1.2 * r;
        s.conductance[b][b] += gf / 100. + gr / 5.;
        s.conductance[b][c] -= gr / 5.;
        s.conductance[c][b] += gf - 1.2 * gr;
        s.conductance[c][c] += 1.2 * gr;
        let pair = [b, c];
        let (charge, mass) = terminal(pair.map(|i| (old.0[i], 0.)), pair.map(|i| (x[i], 0.)))?;
        for i in 0..2 {
            s.charge_c[pair[i]] += charge[i];
            for j in 0..2 {
                s.capacitance[pair[i]][pair[j]] += mass[i][j];
            }
        }
    }
    if s.dc.iter().chain(&s.charge_c).any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok(s)
}

fn evaluate(
    old: State,
    delta: [f64; 10],
    boundary: [[f64; 5]; 2],
    h: f64,
    series_cr8: bool,
) -> Result<([State; 2], [Stamp; 2], [f64; 10]), StepError> {
    let x = std::array::from_fn(|i| State(std::array::from_fn(|k| old.0[k] + delta[5 * i + k])));
    let stage = [
        stamp(old, x[0], boundary[0], series_cr8)?,
        stamp(old, x[1], boundary[1], series_cr8)?,
    ];
    let residual = std::array::from_fn(|k| {
        let (i, r) = (k / 5, k % 5);
        stage[i].dc[r] + (B[i][0] * stage[0].charge_c[r] + B[i][1] * stage[1].charge_c[r]) / h
    });
    Ok((x, stage, residual))
}

pub fn step(
    old: State,
    boundary: [[f64; 5]; 2],
    h: f64,
    series_cr8: bool,
) -> Result<[State; 2], StepError> {
    if !h.is_finite() || h <= 0. || boundary.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::InvalidInput);
    }
    let mut delta = [0.; 10];
    for _ in 0..24 {
        let (x, stage, residual) = evaluate(old, delta, boundary, h, series_cr8)?;
        let jacobian = std::array::from_fn(|k| {
            std::array::from_fn(|l| {
                let (i, r) = (k / 5, k % 5);
                let (j, c) = (l / 5, l % 5);
                B[i][j] * stage[j].capacitance[r][c] / h
                    + if i == j {
                        stage[i].conductance[r][c]
                    } else {
                        0.
                    }
            })
        });
        let correction = Lu::factor(jacobian)?.solve(residual.map(|v| -v))?;
        let norm = maximum(&residual);
        if norm <= 1e-12 && maximum(&correction) <= 2e-9 {
            return Ok(x);
        }
        let mut improved = false;
        let mut scale = 1.;
        for _ in 0..24 {
            let trial = std::array::from_fn(|i| delta[i] + scale * correction[i]);
            if evaluate(old, trial, boundary, h, series_cr8)
                .is_ok_and(|(_, _, r)| maximum(&r) < norm.max(1e-12))
            {
                delta = trial;
                improved = true;
                break;
            }
            scale *= 0.5;
        }
        if !improved {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}
