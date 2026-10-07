//! Nominal NJF E402 half, NG-46 pp.152-154, B=1 at TEMP=TNOM=25 C.
//! Domain, uncertainty and source derivation: docs/VCO_JFET_NOMINAL_PROTOCOLO.md.
use crate::junction_charge::{Parameters as Depletion, Error as ChargeError};

pub const THERMAL_VOLTAGE_V: f64 = (1.38064852e-23 / 1.6021766208e-19) * 298.15;
const THRESHOLD_V: f64 = -2.5;
const BETA_A_V2: f64 = 0.0003018867924528302;
const LAMBDA_PER_V: f64 = 0.003;
const IS_A: f64 = 1e-14;
const GMIN_S: f64 = 1e-12;
const DEPLETION: [Depletion; 2] = [
    Depletion { zero_bias_capacitance_f: 3.3e-12, potential_v: 1.0, grading: 0.5, forward_fraction: 0.5 },
    Depletion { zero_bias_capacitance_f: 5.4990908339470075e-12, potential_v: 1.0, grading: 0.5, forward_fraction: 0.5 },
];
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error { InvalidInput, JunctionDomain, ChannelDomain, NonFiniteResult }
impl From<ChargeError> for Error {
    fn from(_: ChargeError) -> Self { Self::NonFiniteResult }
}
/// Physical terminal arrays/matrices always use [drain, gate, source].
#[derive(Clone, Copy, Debug)]
pub struct OperatingPoint {
    pub current_a: [f64; 3],
    pub jacobian_s: [[f64; 3]; 3],
    pub terminal_charge_c: [f64; 3],
    pub charge_jacobian_f: [[f64; 3]; 3],
    pub junction_charge_c: [f64; 2], // [GS, GD], never swapped in inverse mode.
    pub channel_current_a: f64, // Drain to source, excludes gate currents.
}
#[derive(Clone, Copy, Debug)]
pub struct Companion {
    pub candidate: OperatingPoint,
    pub delta_charge_c: [f64; 2], // [GS, GD]
    pub current_a: [f64; 3],
    pub jacobian_s: [[f64; 3]; 3],
}
fn junctions(node: [f64; 3]) -> Result<[f64; 2], Error> {
    if node.iter().any(|v| !v.is_finite() || !(-40.0..=40.0).contains(v)) {
        return Err(Error::InvalidInput);
    }
    let v = [node[1]-node[2], node[1]-node[0]];
    if v.iter().any(|u| !(-40.0..=0.9).contains(u)) { return Err(Error::JunctionDomain); }
    if !(-40.0..=40.0).contains(&(v[0]-v[1])) { return Err(Error::ChannelDomain); }
    Ok(v)
}
fn gate(v: f64) -> (f64, f64) {
    let vt = THERMAL_VOLTAGE_V;
    let (i, g) = if v >= -3.0*vt {
        (IS_A*(v/vt).exp_m1(), IS_A*(v/vt).exp()/vt)
    } else {
        let ratio = 3.0*vt/(v*std::f64::consts::E);
        let arg = ratio*ratio*ratio;
        (-IS_A*(1.0+arg), IS_A*3.0*arg/v)
    };
    (i+GMIN_S*v, g+GMIN_S)
}
// Returns I(D->S), dI/dVGS and dI/dVGD for the normalized channel.
fn channel(v: [f64; 2]) -> (f64, f64, f64) {
    let ds = v[0]-v[1];
    let forward = ds >= 0.0;
    let h = ds.abs();
    let u = (if forward { v[0] } else { v[1] })-THRESHOLD_V;
    if u <= 0.0 { return (0.0, 0.0, 0.0); }
    let beta = BETA_A_V2*(1.0+LAMBDA_PER_V*h);
    let (shape, gm, gh) = if h <= u {
        let shape = h*(2.0*u-h);
        (shape, 2.0*beta*h, 2.0*beta*(u-h)+BETA_A_V2*LAMBDA_PER_V*shape)
    } else {
        let shape = u*u;
        (shape, 2.0*beta*u, BETA_A_V2*LAMBDA_PER_V*shape)
    };
    if forward { (beta*shape, gm+gh, -gh) }
    else { (-beta*shape, gh, -gm-gh) }
}
fn row(gs: f64, gd: f64) -> [f64; 3] { [-gd, gs+gd, -gs] }
fn capacitive_matrix(c: [f64; 2]) -> [[f64; 3]; 3] {
    [row(0.0, -c[1]), row(c[0], c[1]), row(-c[0], 0.0)]
}
pub fn evaluate(node: [f64; 3]) -> Result<OperatingPoint, Error> {
    let v = junctions(node)?;
    let (igs, ggs) = gate(v[0]); let (igd, ggd) = gate(v[1]);
    let (ich, dgs, dgd) = channel(v);
    let mut q = [0.0; 2]; let mut cap = [0.0; 2];
    for k in 0..2 {
        let branch = DEPLETION[k].charge(v[k])?;
        q[k] = branch.charge_c; cap[k] = branch.capacitance_f;
    }
    let result = OperatingPoint {
        current_a: [ich-igd, igs+igd, -ich-igs],
        jacobian_s: [row(dgs, dgd-ggd), row(ggs, ggd), row(-dgs-ggs, -dgd)],
        terminal_charge_c: [-q[1], q[0]+q[1], -q[0]],
        charge_jacobian_f: capacitive_matrix(cap), junction_charge_c: q, channel_current_a: ich,
    };
    if !result.current_a.iter().chain(result.terminal_charge_c.iter())
        .chain(result.junction_charge_c.iter()).chain(result.jacobian_s.iter().flatten())
        .chain(result.charge_jacobian_f.iter().flatten()).chain([ich].iter()).all(|x| x.is_finite()) {
        return Err(Error::NonFiniteResult);
    }
    Ok(result)
}
/// Provisional Euler stamp, with accepted incoming junction history fixed.
pub fn companion(node: [f64; 3], previous: [f64; 3], dt_s: f64) -> Result<Companion, Error> {
    if !dt_s.is_finite() || !(125e-9..=1e-3).contains(&dt_s) { return Err(Error::InvalidInput); }
    let now = junctions(node)?; let old = junctions(previous)?;
    let candidate = evaluate(node)?;
    let mut delta = [0.0; 2];
    for k in 0..2 { delta[k] = DEPLETION[k].charge_increment(old[k], now[k])?; }
    let igs = delta[0]/dt_s; let igd = delta[1]/dt_s;
    let current = [candidate.current_a[0]-igd, candidate.current_a[1]+igs+igd, candidate.current_a[2]-igs];
    let jacobian = std::array::from_fn(|i| std::array::from_fn(|j|
        candidate.jacobian_s[i][j]+candidate.charge_jacobian_f[i][j]/dt_s));
    if !current.iter().chain(delta.iter()).chain(jacobian.iter().flatten()).all(|x| x.is_finite()) {
        return Err(Error::NonFiniteResult);
    }
    Ok(Companion { candidate, delta_charge_c: delta, current_a: current, jacobian_s: jacobian })
}
