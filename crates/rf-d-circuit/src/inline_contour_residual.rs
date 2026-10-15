//! Generated promotion of VCA_BASE=54 and TAIL=55 into simultaneous unknowns.
//! Source and exact substitutions: tools/prepare_dual_chain.py.
use crate::StepError;
#[path = "inline_filter_residual.rs"]
mod filter;
#[path = "conditioned_voice_latch.rs"]
mod latch_charge_driver;
#[path = "inline_volume_residual.rs"]
mod volume;
pub const N: usize = 56;
pub const M: usize = 2 * N;
pub const P: usize = 9;
pub const B: [[f64; 2]; 2] = [[1.5, 0.5], [-4.5, 2.5]];
pub const PORTS: [&str; P] = [
    "GROUND",
    "SUPPLY",
    "MINUS10",
    "PLUS10",
    "KEY",
    "VCA_BASE",
    "TAIL",
    "CUTOFF_TH",
    "RANGE_TH",
];
pub const TIMER: usize = 38;
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Controls {
    pub key: f64,
    pub short: bool,
    pub optional: bool,
}
impl Default for Controls {
    fn default() -> Self {
        Self {
            key: 0.,
            short: false,
            optional: false,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub high: [f64; N],
    pub low: [f64; N],
    pub optional: bool,
}
fn two_sum(a: f64, b: f64) -> (f64, f64) {
    let s = a + b;
    let v = s - a;
    (s, (a - (s - v)) + (b - v))
}
impl State {
    pub fn new(high: [f64; N], optional: bool) -> Self {
        Self {
            high,
            low: [0.; N],
            optional,
        }
    }
    pub fn advanced(self, d: [f64; N]) -> Self {
        let mut s = self;
        for k in 0..N {
            let (h, e) = two_sum(s.high[k], d[k]);
            let (l, f) = two_sum(s.low[k], e);
            let (h, l) = two_sum(h, l);
            (s.high[k], s.low[k]) = two_sum(h, l + f);
        }
        s
    }
    pub fn valid(self) -> bool {
        (0..N).all(|k| {
            self.high[k].is_finite()
                && self.low[k].is_finite()
                && self.high[k].abs() < 40.
                && two_sum(self.high[k], self.low[k]) == (self.high[k], self.low[k])
        })
    }
}
pub struct Parts<const FULL:bool> {
    pub dc: [f64; N],
    pub j: [[f64; N]; N],
    pub dq: [f64; N],
    pub mass: [[f64; N]; N],
    pub ports: [f64; P],
    pub charge_ports: [f64; P],
    pub now: State,
}
fn voltage(x: &[f64; N], c: Controls, k: usize) -> f64 {
    if k < N {
        x[k]
    } else {
        [0., 9.3, -10., 10., c.key, 0., 1.4, 0., 1.][k - N]
    }
}
fn row<const FULL:bool>(s: &mut Parts<FULL>, k: usize, i: f64, d: &[(usize, f64)]) {
    if k<N{s.dc[k]+=i;s.dc[k]+=d.iter().map(|&(j,g)|if j<N{g*s.now.low[j]}else{0.}).sum::<f64>();if FULL{for &(j,g)in d{if j<N{s.j[k][j]+=g;}}}}
    else{s.ports[k-N]+=i;}
}

fn resistor<const FULL:bool>(s: &mut Parts<FULL>, x: &[f64; N], c: Controls, a: usize, b: usize, g: f64) {
    let i = (voltage(x, c, a) - voltage(x, c, b)) * g;
    row(s, a, i, &[(a, g), (b, -g)]);
    row(s, b, -i, &[(a, -g), (b, g)]);
}
fn bjt<const FULL:bool>(
    s: &mut Parts<FULL>,
    x: &[f64; N],
    c: Controls,
    b: usize,
    col: usize,
    e: usize,
    sign: f64,
) -> Result<(), StepError> {
    let vt = latch_charge_driver::VT;
    let be = sign * (voltage(x, c, b) - voltage(x, c, e)) / vt;
    let bc = sign * (voltage(x, c, b) - voltage(x, c, col)) / vt;
    if be > 45. || bc > 45. {
        return Err(StepError::ExponentialDomain);
    }
    let f = 1e-14 * be.exp_m1();
    let r = 1e-14 * bc.exp_m1();
    let gf = 1e-14 * be.exp() / vt;
    let gr = 1e-14 * bc.exp() / vt;
    let ib = sign * (f / 100. + r / 5.);
    let ic = sign * (f - 1.2 * r);
    row(
        s,
        b,
        ib,
        &[(b, gf / 100. + gr / 5.), (e, -gf / 100.), (col, -gr / 5.)],
    );
    row(s, col, ic, &[(b, gf - 1.2 * gr), (e, -gf), (col, 1.2 * gr)]);
    row(
        s,
        e,
        -ib - ic,
        &[(b, -gf - gf / 100. + gr), (e, gf + gf / 100.), (col, -gr)],
    );
    Ok(())
}
fn diode<const FULL:bool>(
    s: &mut Parts<FULL>,
    x: &[f64; N],
    c: Controls,
    a: usize,
    b: usize,
    is: f64,
) -> Result<(), StepError> {
    let vt = 1.5 * latch_charge_driver::VT;
    let z = (voltage(x, c, a) - voltage(x, c, b)) / vt;
    if z > 45. {
        return Err(StepError::ExponentialDomain);
    }
    let i = is * z.exp_m1();
    let g = is * z.exp() / vt;
    row(s, a, i, &[(a, g), (b, -g)]);
    row(s, b, -i, &[(a, -g), (b, g)]);
    Ok(())
}
fn empty<const FULL:bool>(now: State) -> Parts<FULL> {
    Parts::<FULL> {
        dc: [0.; N],
        j: [[0.; N]; N],
        dq: [0.; N],
        mass: [[0.; N]; N],
        ports: [0.; P],
        charge_ports: [0.; P],
        now,
    }
}
#[inline(always)]
pub fn dc<const FULL:bool>(x: State, c: Controls) -> Result<Parts<FULL>, StepError> {
    if c.optional != x.optional || !c.key.is_finite() || !(0. ..=10.).contains(&c.key)
    {
        return Err(StepError::InvalidInput);
    }
    let mut s = empty(x);
    let v = x.high;
    let vol = volume::linearize::<FULL>(
        std::array::from_fn(|k| if k < 29 { v[k] } else { v[54] }),
        std::array::from_fn(|k| if k < 29 { x.low[k] } else { x.low[54] }),
        c.key,
        true,
        c.short,
    )?;
    for a in 0..30 {
        let i = if a < 29 { a } else { 54 };
        s.dc[i] = vol.dc[a];
        if FULL {for b in 0..30 {
            let j = if b < 29 { b } else { 54 };
            s.j[i][j] = vol.jacobian[a][b];
        }}
    }
    for k in 0..5 {
        s.ports[k] += vol.ports[k];
    }
    // Change only the electrical panel coordinates of the inherited volume graph.
    resistor(&mut s, &v, c, 8, 5, 1. / 1000. - 1. / 10000.);
    resistor(&mut s, &v, c, 11, 5, 1. / 10000. - 1. / 100000.);
    let fp = filter::Parameters {
        c11_f: if c.optional { 47e-12 } else { 0. },
        ..filter::Parameters::default()
    };
    let map = [38, 41, 55, N + 1, N + 2, N + 7, N + 8, N];
    let f = filter::linearize::<FULL>(
        fp,
        std::array::from_fn(|k|x.low[k+29]),map.map(|k|if k<N{x.low[k]}else{0.}),
        map.map(|k| voltage(&v, c, k)),
        std::array::from_fn(|k| v[k + 29]),
        None,
    )?;
    for a in 0..9 {
        let r = a + 29;
        s.dc[r] += f.residual[a];
        if FULL {for b in 0..9 {
            s.j[r][b + 29] += f.jacobian[a][b];
        }
        for p in 0..8 {
            if map[p] < N {
                s.j[r][map[p]] += f.node_port[a][p];
            }
        }}
    }
    for p in 0..8 {
        let a = map[p];
        if a < N {
            s.dc[a] += f.port_current[p];
            if FULL {for b in 0..9 {
                s.j[a][b + 29] += f.port_node[p][b];
            }
            for q in 0..8 {
                if map[q] < N {
                    s.j[a][map[q]] += f.port_port[p][q];
                }
            }}
        } else {
            s.ports[a - N] += f.port_current[p];
        }
    }
    for (a, b, r) in [
        (N + 1, 17, 10000.),
        (N + 1, 18, 10000.),
        (18, 53, 10000.),
        (17, 52, 10000.),
        (42, 39, 10000.),
        (N + 1, 42, 10000.),
        (40, 41, 33000.),
        (N + 1, 43, 560.),
        (43, 40, 3300.),
        (44, 38, 100.),
        (45, N + 2, 10000.),
        (45, 46, 4700.),
        (47, 38, 1000.),
        (N + 1, 48, 27000.),
        (51, 49, 4700.),
        (49, N + 2, 150000.),
        (50, N, 100.),
        (51, N, 2500.),
        (51, N + 3, 2500.),
    ] {
        resistor(&mut s, &v, c, a, b, 1. / r);
    }
    for (b, col, e, sign) in [
        (39, 40, N, 1.),
        (41, 42, N, 1.),
        (43, 44, N + 1, -1.),
        (40, N + 1, 45, 1.),
        (46, 47, 48, 1.),
        (49, 50, 48, -1.),
    ] {
        bjt(&mut s, &v, c, b, col, e, sign)?;
    }
    diode(&mut s, &v, c, 53, 41, 1e-8)?;
    diode(&mut s, &v, c, 48, 17, 1e-12)?;
    // First-order low correction preserves compensated state through static laws.
    // LOW has been accounted at the original device/port incidences.

    if s.dc
        .iter()
        .chain(s.j.iter().flatten())
        .chain(s.ports.iter())
        .any(|v| !v.is_finite())
    {
        return Err(StepError::ExponentialDomain);
    }
    Ok(s)
}
pub const CAPS: [(usize, usize, f64); 7] = [
    (5, N, 1e-5),
    (21, N, 1e-7),
    (23, 25, 1e-8),
    (38, N, 1e-5),
    (52, 39, 1e-8),
    (48, N, 1e-10),
    (34, N, 1e-10),
];
pub const LATCH: [(usize, usize); 6] = [(25, 26), (27, 28), (39, 40), (41, 42), (19, 17), (20, 18)];
#[inline(always)]
pub fn parts<const FULL:bool>(old: State, delta: State, c: Controls, h: f64, now:State) -> Result<Parts<FULL>, StepError> {
    // old/delta/now were checked in the full 118-node stage boundary.
    if !h.is_finite()||h<=0.{return Err(StepError::InvalidInput);}
    let mut s = dc(now, c)?;
    let mut cap = |a: usize, b: usize, cf: f64| {
        let get = |k| {
            if k < N {
                delta.high[k] + delta.low[k]
            } else {
                0.
            }
        };
        let q = cf * (get(a) - get(b)) / h;
        for (i, sign) in [(a, 1.), (b, -1.)] {
            if i < N {
                s.dq[i] += sign * q;
                if FULL {s.mass[i][a] += sign * cf / h;
                if b < N {
                    s.mass[i][b] -= sign * cf / h;
                }}
            } else {
                s.charge_ports[i - N] += sign * q;
            }
        }
    };
    for (a, b, cf) in CAPS {
        cap(a, b, cf);
    }
    if c.optional {
        cap(30, 31, 47e-12);
        cap(31, N + 1, 500e-12);
    }
    for (b, col) in LATCH {
        let (q, j) = latch_charge_driver::terminal(
            [(old.high[b], old.low[b]), (old.high[col], old.low[col])],
            [(now.high[b], now.low[b]), (now.high[col], now.low[col])],
        )?;
        for (a, i) in [b, col].into_iter().enumerate() {
            s.dq[i] += q[a] / h;
            if FULL {for (k, jj) in [b, col].into_iter().enumerate() {
                s.mass[i][jj] += j[a][k] / h;
            }}
        }
        s.charge_ports[0] -= (q[0] + q[1]) / h;
    }
    Ok(s)
}
