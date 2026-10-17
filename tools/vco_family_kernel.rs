//! Stationary calibrated CV/BUS family; SVC-204D/SVC-9 pp.5/19.
//! Laboratory candidate only. Fixed trims/topology, no dynamic CV admission.
use crate::data::{COEFFICIENTS, LOG_FREQUENCY};
pub const CV: [f64; 4] = [-3.1, -2.1, -1.1, -0.1];
pub const OUTPUTS: usize = 19;
const RESISTANCE: [f64; 6] = [150000., 560000., 51100., 51100., 51100., 15000.];
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct InvalidDomain;
#[derive(Debug, Clone, Copy)]
pub struct Query {
    pub values: [f64; OUTPUTS],
    pub dcv: [f64; OUTPUTS],
    pub dbus: [f64; OUTPUTS],
}
pub fn evaluate(cv: f64, bus: f64, phase: f64) -> Result<Query, InvalidDomain> {
    if !cv.is_finite() || !bus.is_finite() || !phase.is_finite()
        || !(CV[0]..=CV[3]).contains(&cv) || !(-0.125..=0.125).contains(&bus)
        || !(0. ..=1.).contains(&phase) { return Err(InvalidDomain); }
    let mut w = [0.; 4]; let mut dw = [0.; 4];
    for i in 0..4 {
        let mut den = 1.; let mut num = 1.;
        for j in 0..4 { if j != i { den *= CV[i] - CV[j]; num *= cv - CV[j]; } }
        w[i] = num / den;
        for k in 0..4 { if k != i {
            let mut p = 1.;
            for j in 0..4 { if j != i && j != k { p *= cv - CV[j]; } }
            dw[i] += p / den;
        } }
    }
    let u = (bus + 0.125) / 0.25; let b = [1. - u, u]; let db = [-4., 4.];
    let mut log = [0.; 3]; let mut voltage = [[0.; 7]; 3];
    for i in 0..4 { for j in 0..2 {
        let weights = [w[i]*b[j], dw[i]*b[j], w[i]*db[j]];
        for axis in 0..3 { log[axis] += weights[axis]*LOG_FREQUENCY[i][j]; }
        for n in 0..=64 {
            let angle = std::f64::consts::TAU * n as f64 * phase;
            let (s, c) = angle.sin_cos(); let scale = if n == 0 { 1. } else { 2. };
            for channel in 0..7 {
                let x = COEFFICIENTS[i][j][channel][n];
                let v = scale*(x[0]*c - x[1]*s);
                for axis in 0..3 { voltage[axis][channel] += weights[axis]*v; }
            }
        }
    } }
    let f = log[0].exp2(); let mut all = [[0.; OUTPUTS]; 3];
    for axis in 0..3 {
        all[axis][0] = if axis == 0 { f } else { f*std::f64::consts::LN_2*log[axis] };
        all[axis][1..8].copy_from_slice(&voltage[axis]);
        let boundary = if axis == 0 { bus } else if axis == 2 { 1. } else { 0. };
        let saw = voltage[axis][0]; let sum = voltage[axis][3];
        let cursor = (saw/12500. + boundary/33000.)/(2./12500. + 1./33000.);
        all[axis][8] = cursor;
        all[axis][9] = (saw - cursor)/12500.;
        all[axis][10] = -cursor/12500.;
        all[axis][11] = (boundary - cursor)/33000.;
        for k in 0..6 {
            let control = if axis == 0 { if k == 2 { cv } else { -2.1 } }
                else if axis == 1 && k == 2 { 1. } else { 0. };
            all[axis][12+k] = (control-sum)/RESISTANCE[k];
        }
        all[axis][18] = if axis == 0 {
            (saw-cursor).powi(2)/12500. + cursor.powi(2)/12500.
                + (bus-cursor).powi(2)/33000.
        } else {
            let s0 = voltage[0][0]; let w0 = all[0][8];
            2.*((s0-w0)*(saw-cursor)/12500.+w0*cursor/12500.
                +(bus-w0)*(boundary-cursor)/33000.)
        };
    }
    Ok(Query { values: all[0], dcv: all[1], dbus: all[2] })
}
