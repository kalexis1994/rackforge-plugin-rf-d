//! Nominal NG-46 BJT subset, NG-46 pp.138-145; fixed TEMP=TNOM=25 C.
//! See docs/VCO_BJT_NOMINAL_PROTOCOLO.md for card, domains and uncertainty.
use crate::junction_charge::{Parameters as Depletion, Error as ChargeError};

pub const THERMAL_VOLTAGE_V: f64 = (1.38064852e-23 / 1.6021766208e-19) * 298.15;
const IS_A: f64 = 1e-14;
const BF: f64 = 100.0;
const BR: f64 = 5.0;
const GMIN_S: f64 = 1e-12;
const TAU_S: [f64; 2] = [1e-9, 3e-9];
const DEPLETION: [Depletion; 2] = [
    Depletion { zero_bias_capacitance_f: 7e-12, potential_v: 0.75, grading: 0.5, forward_fraction: 0.4 },
    Depletion { zero_bias_capacitance_f: 3e-12, potential_v: 0.7, grading: 0.33, forward_fraction: 0.4 },
];
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Polarity { Npn, Pnp }
impl Polarity {
    fn sign(self) -> f64 { match self { Self::Npn => 1.0, Self::Pnp => -1.0 } }
    fn substrate_return(self) -> usize { match self { Self::Npn => 0, Self::Pnp => 1 } }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error { InvalidInput, JunctionDomain, NonFiniteResult }
impl From<ChargeError> for Error {
    fn from(_: ChargeError) -> Self { Self::NonFiniteResult }
}
/// All terminal arrays/matrices use [collector, base, emitter, substrate].
#[derive(Clone, Copy, Debug)]
pub struct OperatingPoint {
    pub current_a: [f64; 4],
    pub jacobian_s: [[f64; 4]; 4],
    pub terminal_charge_c: [f64; 4],
    pub charge_jacobian_f: [[f64; 4]; 4],
    pub oriented_junction_charge_c: [f64; 2],
}
#[derive(Clone, Copy, Debug)]
pub struct Companion {
    pub candidate: OperatingPoint,
    /// Normalized BE/BC increments; physical branches multiply by polarity.
    pub delta_charge_c: [f64; 2],
    pub current_a: [f64; 4],
    pub jacobian_s: [[f64; 4]; 4],
}
fn junctions(polarity: Polarity, node: [f64; 4]) -> Result<[f64; 2], Error> {
    if node.iter().any(|v| !v.is_finite() || !(-40.0..=40.0).contains(v)) {
        return Err(Error::InvalidInput);
    }
    let sign = polarity.sign();
    let v = [sign*(node[1]-node[2]), sign*(node[1]-node[0])];
    if v.iter().any(|u| !(-40.0..=0.9).contains(u)) { return Err(Error::JunctionDomain); }
    Ok(v)
}
fn diode(v: f64) -> (f64, f64) {
    let vt = THERMAL_VOLTAGE_V;
    if v >= -3.0*vt {
        let x = v/vt;
        (IS_A*x.exp_m1(), IS_A*x.exp()/vt)
    } else {
        let ratio = 3.0*vt/(v*std::f64::consts::E);
        let arg = ratio*ratio*ratio;
        (-IS_A*(1.0+arg), IS_A*3.0*arg/v)
    }
}
fn diode_increment(from: f64, to: f64) -> f64 {
    if from == to { return 0.0; }
    let (lo, hi, sign) = if to > from { (from, to, 1.0) } else { (to, from, -1.0) };
    let knee = -3.0*THERMAL_VOLTAGE_V;
    let low = |a: f64, b: f64| {
        let ratio = 3.0*THERMAL_VOLTAGE_V/(a*std::f64::consts::E);
        let z = (a-b)/b;
        -IS_A*ratio*ratio*ratio*z*(3.0+z*(3.0+z))
    };
    let high = |a: f64, b: f64| IS_A*(a/THERMAL_VOLTAGE_V).exp()
        *((b-a)/THERMAL_VOLTAGE_V).exp_m1();
    sign*if hi <= knee { low(lo, hi) }
        else if lo >= knee { high(lo, hi) }
        else { low(lo, knee)+high(knee, hi) }
}
fn terminal_row(be: f64, bc: f64) -> [f64; 4] { [-bc, be+bc, -be, 0.0] }
fn capacitive_matrix(c: [f64; 2]) -> [[f64; 4]; 4] {
    [terminal_row(0.0, -c[1]), terminal_row(c[0], c[1]),
     terminal_row(-c[0], 0.0), [0.0; 4]]
}
fn finite(values: &OperatingPoint) -> bool {
    values.current_a.iter().chain(values.terminal_charge_c.iter())
        .chain(values.oriented_junction_charge_c.iter())
        .chain(values.jacobian_s.iter().flatten())
        .chain(values.charge_jacobian_f.iter().flatten()).all(|v| v.is_finite())
}
pub fn evaluate(polarity: Polarity, node: [f64; 4]) -> Result<OperatingPoint, Error> {
    let v = junctions(polarity, node)?;
    let (f, gf) = diode(v[0]); let (r, gr) = diode(v[1]);
    let sign = polarity.sign();
    let ic = sign*(f-r-r/BR-GMIN_S*v[1]);
    let ib = sign*(f/BF+r/BR+GMIN_S*(v[0]+v[1]));
    let jc = terminal_row(gf, -gr*(1.0+1.0/BR)-GMIN_S);
    let jb = terminal_row(gf/BF+GMIN_S, gr/BR+GMIN_S);
    let mut result = OperatingPoint {
        current_a: [ic, ib, -ic-ib, 0.0],
        jacobian_s: [jc, jb, std::array::from_fn(|k| -jc[k]-jb[k]), [0.0; 4]],
        terminal_charge_c: [0.0; 4], charge_jacobian_f: [[0.0; 4]; 4],
        oriented_junction_charge_c: [0.0; 2],
    };
    // Default NG-46 substrate is vertical NPN / lateral PNP. ISS=CJS=0.
    let target = polarity.substrate_return();
    let substrate = GMIN_S*(node[target]-node[3]);
    result.current_a[target] += substrate; result.current_a[3] -= substrate;
    result.jacobian_s[target][target] += GMIN_S;
    result.jacobian_s[target][3] -= GMIN_S;
    result.jacobian_s[3][target] -= GMIN_S;
    result.jacobian_s[3][3] += GMIN_S;
    let mut cap = [0.0; 2];
    for k in 0..2 {
        let q = DEPLETION[k].charge(v[k])?; let (i, g) = diode(v[k]);
        result.oriented_junction_charge_c[k] = q.charge_c+TAU_S[k]*i;
        cap[k] = q.capacitance_f+TAU_S[k]*g;
    }
    let q = result.oriented_junction_charge_c;
    result.terminal_charge_c = [-sign*q[1], sign*(q[0]+q[1]), -sign*q[0], 0.0];
    result.charge_jacobian_f = capacitive_matrix(cap);
    if !finite(&result) { return Err(Error::NonFiniteResult); }
    Ok(result)
}
/// Provisional stamp only. The caller commits the entire circuit state.
pub fn companion(polarity: Polarity, node: [f64; 4], previous: [f64; 4], dt_s: f64)
    -> Result<Companion, Error> {
    if !dt_s.is_finite() || !(125e-9..=1e-3).contains(&dt_s) { return Err(Error::InvalidInput); }
    let now = junctions(polarity, node)?; let old = junctions(polarity, previous)?;
    let candidate = evaluate(polarity, node)?;
    let mut delta = [0.0; 2];
    for k in 0..2 {
        delta[k] = DEPLETION[k].charge_increment(old[k], now[k])?
            +TAU_S[k]*diode_increment(old[k], now[k]);
    }
    let sign = polarity.sign(); let ibe = sign*delta[0]/dt_s; let ibc = sign*delta[1]/dt_s;
    let current = [candidate.current_a[0]-ibc, candidate.current_a[1]+ibe+ibc,
                   candidate.current_a[2]-ibe, candidate.current_a[3]];
    let reactive = candidate.charge_jacobian_f;
    let jacobian = std::array::from_fn(|i| std::array::from_fn(|j|
        candidate.jacobian_s[i][j]+reactive[i][j]/dt_s));
    if !current.iter().chain(delta.iter()).chain(jacobian.iter().flatten()).all(|x| x.is_finite()) {
        return Err(Error::NonFiniteResult);
    }
    Ok(Companion { candidate, delta_charge_c: delta, current_a: current, jacobian_s: jacobian })
}
