//! Loaded volume latch, attack/decay switches and shared Q20/Q12 trigger.
use crate::{
    latch_charge::{terminal, VT},
    reduced_lu::{maximum, Lu},
    StepError,
};

pub const N: usize = 19;
pub const CORE: [usize; N] = [
    6, 7, 8, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 53,
];
pub const PORTS: [usize; 6] = [4, 5, 14, 41, 48, 52];
const P: usize = PORTS.len();
const SUPPLY: usize = N + P;
const MINUS: usize = SUPPLY + 1;
const GROUND: usize = SUPPLY + 2;
const KEY: usize = SUPPLY + 3;
const PINS: usize = KEY + 1;
const B: [[f64; 2]; 2] = [[1.5, 0.5], [-4.5, 2.5]];

const fn pin(node: usize) -> usize {
    let mut i = 0;
    while i < N {
        if CORE[i] == node {
            return i;
        }
        i += 1;
    }
    let mut i = 0;
    while i < P {
        if PORTS[i] == node {
            return N + i;
        }
        i += 1;
    }
    panic!("unknown trigger pin");
}

const R: [(usize, usize, f64); 21] = [
    (SUPPLY, pin(17), 3300.),
    (SUPPLY, pin(18), 3300.),
    (SUPPLY, pin(17), 10_000.), // Filter board load
    (SUPPLY, pin(18), 10_000.), // Filter board load
    (pin(18), pin(19), 10_000.),
    (pin(20), pin(21), 47_000.),
    (pin(21), pin(22), 100_000.),
    (pin(17), pin(23), 10_000.),
    (pin(17), pin(52), 10_000.),
    (pin(18), pin(24), 10_000.),
    (pin(18), pin(53), 10_000.),
    (pin(25), pin(28), 10_000.),
    (SUPPLY, pin(28), 10_000.),
    (pin(6), pin(26), 3300.),
    (SUPPLY, pin(6), 560.),
    (pin(7), pin(8), 100.),
    (pin(8), pin(5), 1000.),
    (pin(11), pin(5), 10_000.),
    (pin(26), pin(27), 33_000.),
    (pin(9), MINUS, 10_000.),
    (pin(9), pin(10), 4700.),
];
const TRANSISTORS: [(usize, usize, usize, f64); 7] = [
    (pin(19), pin(17), GROUND, 1.),
    (pin(20), pin(18), GROUND, 1.),
    (pin(25), pin(26), GROUND, 1.),
    (pin(27), pin(28), GROUND, 1.),
    (pin(6), pin(7), SUPPLY, -1.),
    (pin(26), SUPPLY, pin(9), 1.),
    (pin(10), pin(11), pin(14), 1.),
];
const DIODES: [(usize, usize, f64); 6] = [
    (KEY, pin(22), 1e-8),
    (pin(24), pin(27), 1e-8),
    (pin(53), pin(41), 1e-8),
    (pin(4), pin(27), 1e-8),
    (pin(14), pin(17), 1e-12),
    (pin(48), pin(17), 1e-12),
];
const CHARGED: [(usize, usize); 4] = [
    (pin(19), pin(17)),
    (pin(20), pin(18)),
    (pin(25), pin(26)),
    (pin(27), pin(28)),
];

#[derive(Clone, Copy)]
pub struct State(pub [f64; N]);

impl State {
    pub fn order(self) -> bool {
        self.0[pin(26)] >= self.0[pin(28)]
    }
}

#[derive(Clone, Copy)]
pub struct Boundary {
    pub volts: [f64; P],
    pub key: f64,
    pub short: bool,
}

pub struct Stamp {
    pub dc: [f64; PINS],
    pub charge_c: [f64; N],
    conductance: [[f64; N]; N],
    capacitance: [[f64; N]; N],
}

impl Stamp {
    fn row<const FULL: bool>(&mut self, row: usize, current: f64, terms: &[(usize, f64)]) {
        self.dc[row] += current;
        if FULL && row < N {
            for &(col, value) in terms {
                if col < N {
                    self.conductance[row][col] += value;
                }
            }
        }
    }

    fn branch<const FULL: bool>(&mut self, a: usize, b: usize, i: f64, g: f64) {
        self.row::<FULL>(a, i, &[(a, g), (b, -g)]);
        self.row::<FULL>(b, -i, &[(a, -g), (b, g)]);
    }

    fn capacitor(&mut self, a: usize, b: usize, change: &[f64; N], c: f64) {
        let q = c * (change[a] - change.get(b).copied().unwrap_or(0.));
        self.charge_c[a] += q;
        self.capacitance[a][a] += c;
        if b < N {
            self.charge_c[b] -= q;
            self.capacitance[a][b] -= c;
            self.capacitance[b][a] -= c;
            self.capacitance[b][b] += c;
        }
    }
}

fn junction(z: f64, is_a: f64, scale: f64) -> Result<(f64, f64), StepError> {
    if !z.is_finite() || z > 45. {
        return Err(StepError::ExponentialDomain);
    }
    Ok((is_a * z.exp_m1(), is_a * z.exp() / scale))
}

pub fn stamp<const FULL: bool>(
    old: State,
    change: [f64; N],
    u: Boundary,
) -> Result<Stamp, StepError> {
    let x: [f64; PINS] = std::array::from_fn(|i| match i {
        0..N => old.0[i] + change[i],
        N..SUPPLY => u.volts[i - N],
        SUPPLY => 9.3,
        MINUS => -10.,
        GROUND => 0.,
        _ => u.key,
    });
    let mut s = Stamp {
        dc: [0.; PINS],
        charge_c: [0.; N],
        conductance: [[0.; N]; N],
        capacitance: [[0.; N]; N],
    };
    for (a, b, ohm) in R {
        s.branch::<FULL>(a, b, (x[a] - x[b]) / ohm, 1. / ohm);
    }
    if u.short {
        s.branch::<FULL>(pin(18), GROUND, x[pin(18)] / 220., 1. / 220.);
    }
    for (a, b, is_a) in DIODES {
        let scale = 1.5 * VT;
        let (i, g) = junction((x[a] - x[b]) / scale, is_a, scale)?;
        s.branch::<FULL>(a, b, i, g);
    }
    for (b, c, e, sign) in TRANSISTORS {
        let (f, gf) = junction(sign * (x[b] - x[e]) / VT, 1e-14, VT)?;
        let (r, gr) = junction(sign * (x[b] - x[c]) / VT, 1e-14, VT)?;
        let ib = sign * (f / 100. + r / 5.);
        let ic = sign * (f - 1.2 * r);
        s.row::<FULL>(
            b,
            ib,
            &[(b, gf / 100. + gr / 5.), (e, -gf / 100.), (c, -gr / 5.)],
        );
        s.row::<FULL>(c, ic, &[(b, gf - 1.2 * gr), (e, -gf), (c, 1.2 * gr)]);
        s.row::<FULL>(
            e,
            -ib - ic,
            &[(b, -gf - gf / 100. + gr), (e, gf + gf / 100.), (c, -gr)],
        );
    }
    s.capacitor(pin(21), GROUND, &change, 1e-7);
    s.capacitor(pin(23), pin(25), &change, 1e-8);
    for (b, c) in CHARGED {
        let pair = [b, c];
        let (q, m) = terminal(pair.map(|i| (old.0[i], 0.)), pair.map(|i| (x[i], 0.)))?;
        for i in 0..2 {
            s.charge_c[pair[i]] += q[i];
            if FULL {
                for j in 0..2 {
                    s.capacitance[pair[i]][pair[j]] += m[i][j];
                }
            }
        }
    }
    if s.dc.iter().chain(&s.charge_c).any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok(s)
}

fn evaluate<const FULL: bool>(
    old: State,
    delta: [f64; 2 * N],
    u: [Boundary; 2],
    h: f64,
) -> Result<([Stamp; 2], [f64; 2 * N]), StepError> {
    let s = [
        stamp::<FULL>(old, delta[..N].try_into().unwrap(), u[0])?,
        stamp::<FULL>(old, delta[N..].try_into().unwrap(), u[1])?,
    ];
    let r = std::array::from_fn(|k| {
        let (i, a) = (k / N, k % N);
        s[i].dc[a] + (B[i][0] * s[0].charge_c[a] + B[i][1] * s[1].charge_c[a]) / h
    });
    Ok((s, r))
}

const ALGEBRAIC: [usize; 4] = [pin(8), pin(22), pin(24), pin(53)];
const KEPT: [usize; N - ALGEBRAIC.len()] = [
    pin(6),
    pin(7),
    pin(9),
    pin(10),
    pin(11),
    pin(17),
    pin(18),
    pin(19),
    pin(20),
    pin(21),
    pin(23),
    pin(25),
    pin(26),
    pin(27),
    pin(28),
];
const K: usize = KEPT.len();

fn direction(s: &[Stamp; 2], r: [f64; 2 * N], h: f64) -> Result<[f64; 2 * N], StepError> {
    // These four algebraic rows have neither stored charge nor mutual
    // coupling. Their exact Schur contribution stays within each stage.
    let inv_diagonal: [[f64; 4]; 2] =
        std::array::from_fn(|j| ALGEBRAIC.map(|a| 1. / s[j].conductance[a][a]));
    if inv_diagonal
        .iter()
        .flatten()
        .any(|x| !x.is_finite() || *x <= 0.)
    {
        return Err(StepError::SingularJacobian);
    }
    let lift: [[[f64; 4]; K]; 2] = std::array::from_fn(|j| {
        KEPT.map(|a| {
            std::array::from_fn(|g| s[j].conductance[a][ALGEBRAIC[g]] * inv_diagonal[j][g])
        })
    });
    let jac: [[f64; 2 * K]; 2 * K] = std::array::from_fn(|i| {
        let (stage, row) = (i / K, KEPT[i % K]);
        std::array::from_fn(|j| {
            let (other, col) = (j / K, KEPT[j % K]);
            let mass = B[stage][other] * s[other].capacitance[row][col] / h;
            if stage != other {
                return mass;
            }
            let reaction: f64 = ALGEBRAIC
                .iter()
                .zip(&lift[stage][i % K])
                .map(|(&a, weight)| weight * s[stage].conductance[a][col])
                .sum();
            mass + s[stage].conductance[row][col] - reaction
        })
    });
    let rhs = std::array::from_fn(|i| {
        let stage = i / K;
        let load: f64 = ALGEBRAIC
            .iter()
            .zip(&lift[stage][i % K])
            .map(|(&a, weight)| weight * r[stage * N + a])
            .sum();
        -r[stage * N + KEPT[i % K]] + load
    });
    let solution = Lu::factor(jac)?.solve(rhs)?;
    let mut full = [0.; 2 * N];
    for stage in 0..2 {
        let base = stage * N;
        for (i, &a) in KEPT.iter().enumerate() {
            full[base + a] = solution[stage * K + i];
        }
        for (g, &a) in ALGEBRAIC.iter().enumerate() {
            let feedback: f64 = KEPT
                .iter()
                .map(|&b| s[stage].conductance[a][b] * full[base + b])
                .sum();
            full[base + a] = (-r[base + a] - feedback) * inv_diagonal[stage][g];
        }
    }
    if full.iter().any(|x| !x.is_finite()) {
        return Err(StepError::SingularJacobian);
    }
    Ok(full)
}

fn full_direction(s: &[Stamp; 2], r: [f64; 2 * N], h: f64) -> Result<[f64; 2 * N], StepError> {
    let jac = std::array::from_fn(|k| {
        std::array::from_fn(|l| {
            let (i, a) = (k / N, k % N);
            let (j, b) = (l / N, l % N);
            B[i][j] * s[j].capacitance[a][b] / h + if i == j { s[i].conductance[a][b] } else { 0. }
        })
    });
    Lu::factor(jac)?.solve(r.map(|v| -v))
}

pub fn audit_direction(
    old: State,
    candidates: [State; 2],
    u: [Boundary; 2],
    h: f64,
) -> Result<f64, StepError> {
    let delta = std::array::from_fn(|i| candidates[i / N].0[i % N] - old.0[i % N]);
    let (s, mut r) = evaluate::<true>(old, delta, u, h)?;
    for stamp in &s {
        for &a in &ALGEBRAIC {
            assert!((0..N).all(|b| stamp.capacitance[a][b] == 0. && stamp.capacitance[b][a] == 0.));
            assert!(ALGEBRAIC
                .iter()
                .all(|&b| a == b || stamp.conductance[a][b] == 0.));
        }
    }
    for (k, value) in r.iter_mut().enumerate() {
        *value += 1e-9 * (k as f64 + 0.5).sin();
    }
    let reduced = direction(&s, r, h)?;
    let full = full_direction(&s, r, h)?;
    Ok(reduced.iter().zip(full).fold(0_f64, |maximum, (&a, b)| {
        maximum.max((a - b).abs() / (2e-9 + 2e-8 * b.abs()))
    }))
}

pub fn step(
    old: State,
    u: [Boundary; 2],
    h: f64,
    previous: Boundary,
    previous_change: [f64; N],
) -> Result<[State; 2], StepError> {
    if !h.is_finite() || h <= 0. || u.iter().any(|s| !(0. ..=10.).contains(&s.key)) {
        return Err(StepError::InvalidInput);
    }
    let seed = std::array::from_fn(|i| [1. / 3., 1.][i / N] * previous_change[i % N]);
    solve(old, u, h, seed)
        .or_else(|_| solve(old, u, h, [0.; 2 * N]))
        .or_else(|_| refined_seed(old, previous, u, h))
}

fn quadratic(t: f64) -> [f64; 3] {
    [
        3. * (t - 1. / 3.) * (t - 1.),
        -4.5 * t * (t - 1.),
        1.5 * t * (t - 1. / 3.),
    ]
}

fn refined_seed(
    old: State,
    previous: Boundary,
    u: [Boundary; 2],
    h: f64,
) -> Result<[State; 2], StepError> {
    // Substeps propose a seed only. The original Radau equations still
    // decide whether to publish either of the two original stage states.
    let at = |t| {
        let [a, b, c] = quadratic(t);
        Boundary {
            volts: std::array::from_fn(|i| {
                a * previous.volts[i] + b * u[0].volts[i] + c * u[1].volts[i]
            }),
            ..u[1]
        }
    };
    let first = solve(old, [at(1. / 6.), at(0.5)], h / 2., [0.; 2 * N])?;
    let second = solve(first[1], [at(2. / 3.), u[1]], h / 2., [0.; 2 * N])?;
    let [a, b, c] = quadratic(2. / 3.);
    let seed = std::array::from_fn(|i| {
        if i < N {
            (a - 1.) * old.0[i] + b * first[0].0[i] + c * first[1].0[i]
        } else {
            second[1].0[i - N] - old.0[i - N]
        }
    });
    solve(old, u, h, seed)
}

pub fn trial_diagnostic(
    old: State,
    candidate: [State; 2],
    u: [Boundary; 2],
    h: f64,
) -> Result<(f64, f64), StepError> {
    let change = std::array::from_fn(|i| candidate[i / N].0[i % N] - old.0[i % N]);
    let (stamp, residual) = evaluate::<true>(old, change, u, h)?;
    let correction = direction(&stamp, residual, h)?;
    Ok((maximum(&residual), maximum(&correction)))
}

fn solve(
    old: State,
    u: [Boundary; 2],
    h: f64,
    mut delta: [f64; 2 * N],
) -> Result<[State; 2], StepError> {
    for j in 0..2 {
        let k = pin(22);
        if u[j].key - old.0[k] > 0.5 {
            delta[j * N + k] = u[j].key - 0.5 - old.0[k];
        }
    }
    for _ in 0..80 {
        let (s, r) = evaluate::<true>(old, delta, u, h)?;
        let correction = direction(&s, r, h)?;
        let norm = maximum(&r);
        if norm <= 1e-12 && maximum(&correction) <= 2e-9 {
            return Ok(std::array::from_fn(|j| {
                State(std::array::from_fn(|i| old.0[i] + delta[j * N + i]))
            }));
        }
        let mut next = None;
        let mut alpha = 1.;
        for _ in 0..24 {
            let trial = std::array::from_fn(|i| delta[i] + alpha * correction[i]);
            let improves = if norm <= 1e-12 {
                if let Ok((s, r)) = evaluate::<true>(old, trial, u, h) {
                    maximum(&r) <= 1e-12 && maximum(&direction(&s, r, h)?) < maximum(&correction)
                } else {
                    false
                }
            } else {
                evaluate::<false>(old, trial, u, h).is_ok_and(|(_, r)| maximum(&r) < norm)
            };
            if improves {
                next = Some(trial);
                break;
            }
            alpha *= 0.5;
        }
        delta = next.ok_or(StepError::NoDecrease)?;
    }
    Err(StepError::IterationBudget)
}
