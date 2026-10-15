//! Reviewed Q22/Q21 complementary feedback pair -> Amount -> Q26/Q28.
//! Conditional nine-node port, not a complete contour. See CONTORNO_FILTRO_PUERTO_PROTOCOLO.
//! Capacitor recipe is fixed across a trajectory; controls may change with charge preserved.
use crate::StepError;
pub const N: usize = 9;
pub const P: usize = 8;
pub const NODES: [&str; N] = [
    "Q22_B",
    "Q22_C_Q21_B",
    "Q21_E",
    "FILTER_OUT",
    "FEEDBACK",
    "Q26_B",
    "Q26_E_Q28_B",
    "Q26_C",
    "Q28_C",
];
pub const PORTS: [&str; P] = [
    "TIMING_C5",
    "RESET_Q4",
    "TAIL",
    "SUPPLY",
    "MINUS10",
    "CUTOFF_TH",
    "RANGE_TH",
    "GROUND",
];
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Parameters {
    pub amount: f64,
    pub cutoff: f64,
    pub range: f64,
    pub scale_ohm: f64,
    pub c11_f: f64,
}
impl Default for Parameters {
    fn default() -> Self {
        Self {
            amount: 0.5,
            cutoff: 0.5,
            range: 0.1,
            scale_ohm: 250.,
            c11_f: 0.,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub node_v: [f64; N],
    pub capacitor_v: [f64; 2],
    pub c11_f: f64,
}
impl State {
    pub fn from_nodes(node_v: [f64; N], ground: f64, c11_f: f64) -> Self {
        Self {
            node_v,
            capacitor_v: [node_v[1] - node_v[2], node_v[5] - ground],
            c11_f,
        }
    }
}
pub struct Stamp<const FULL:bool> {
    low:[f64;N],port_low:[f64;P],
    pub residual: [f64; N],
    pub jacobian: [[f64; N]; N],
    pub port_current: [f64; P],
    pub node_port: [[f64; P]; N],
    pub port_node: [[f64; N]; P],
    pub port_port: [[f64; P]; P],
}
pub struct Response {
    pub next_state: State,
    pub port_current: [f64; P],
    pub port_jacobian: [[f64; P]; P],
    pub iterations: usize,
    pub residual_a: f64,
    pub correction_v: f64,
}
pub fn boundary(timing: f64, reset: f64, tail: f64, p: Parameters) -> [f64; P] {
    [
        timing,
        reset,
        tail,
        9.3,
        -10.,
        -10. + 20. * p.cutoff,
        10. * p.range,
        0.,
    ]
}
pub fn amount_matrix(a: f64) -> Result<[[f64; 2]; 2], StepError> {
    if !a.is_finite() || !(0. ..=1.).contains(&a) {
        return Err(StepError::InvalidInput);
    }
    let ru = (1. - a) * 50000.;
    let rl = a * 50000.;
    let d = 47000. * 50000. + ru * rl;
    Ok([[(47000. + rl) / d, -rl / d], [-rl / d, 50000. / d]])
}
fn valid(p: Parameters, b: [f64; P], x: [f64; N]) -> bool {
    [p.amount, p.cutoff, p.range]
        .iter()
        .all(|v| v.is_finite() && (0. ..=1.).contains(v))
        && p.scale_ohm.is_finite()
        && (0. ..=500.).contains(&p.scale_ohm)
        && [0., 47e-12].contains(&p.c11_f)
        && b.iter().chain(x.iter()).all(|v| v.is_finite())
}
fn maximum<const M: usize>(x: [f64; M]) -> f64 {
    x.into_iter().fold(0., |a, v| a.max(v.abs()))
}
fn row<const FULL:bool>(s: &mut Stamp<FULL>, k: usize, i: f64, d: &[(usize, f64)]) {
    let i=i+d.iter().map(|&(j,g)|g*if j<N{s.low[j]}else{s.port_low[j-N]}).sum::<f64>();
    if k<N{s.residual[k]+=i;if FULL{for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}else{s.node_port[k][j-N]+=g;}}}}
    else{s.port_current[k-N]+=i;if FULL{for &(j,g)in d{if j<N{s.port_node[k-N][j]+=g;}else{s.port_port[k-N][j-N]+=g;}}}}
}

fn value(x: [f64; N], b: [f64; P], k: usize) -> f64 {
    if k < N {
        x[k]
    } else {
        b[k - N]
    }
}
fn branch<const FULL:bool>(s: &mut Stamp<FULL>, x: [f64; N], b: [f64; P], a: usize, c: usize, g: f64) {
    let i = g * (value(x, b, a) - value(x, b, c));
    row(s, a, i, &[(a, g), (c, -g)]);
    row(s, c, -i, &[(a, -g), (c, g)])
}
fn transistor<const FULL:bool>(
    s: &mut Stamp<FULL>,
    x: [f64; N],
    b: [f64; P],
    base: usize,
    c: usize,
    e: usize,
    sign: f64,
) -> Result<(), StepError> {
    let vt = 1.380649e-23 * 298.15 / 1.602176634e-19;
    let be = sign * (value(x, b, base) - value(x, b, e)) / vt;
    let bc = sign * (value(x, b, base) - value(x, b, c)) / vt;
    if !be.is_finite() || !bc.is_finite() || be > 45. || bc > 45. {
        return Err(StepError::ExponentialDomain);
    }
    let f = 1e-14 * be.exp_m1();
    let r = 1e-14 * bc.exp_m1();
    let gf = 1e-14 * be.exp() / vt;
    let gr = 1e-14 * bc.exp() / vt;
    row(
        s,
        base,
        sign * (f / 100. + r / 5.),
        &[(base, gf / 100. + gr / 5.), (e, -gf / 100.), (c, -gr / 5.)],
    );
    row(
        s,
        c,
        sign * (f - 1.2 * r),
        &[(base, gf - 1.2 * gr), (e, -gf), (c, 1.2 * gr)],
    );
    row(
        s,
        e,
        -sign * (f / 100. + r / 5. + f - 1.2 * r),
        &[(base, -gf - gf / 100. + gr), (e, gf + gf / 100.), (c, -gr)],
    );
    Ok(())
}
pub fn linearize<const FULL:bool>(
    p: Parameters,
    low:[f64;N],port_low:[f64;P],
    b: [f64; P],
    x: [f64; N],
    history: Option<([f64; 2], f64)>,
) -> Result<Stamp<FULL>, StepError> {
    if !valid(p, b, x) {
        return Err(StepError::InvalidInput);
    }
    if let Some((old, h)) = history {
        if old.iter().any(|v| !v.is_finite()) || !h.is_finite() || h <= 0. {
            return Err(StepError::InvalidInput);
        }
    }
    let mut s = Stamp::<FULL> {
        low,port_low,
        residual: [0.; N],
        jacobian: [[0.; N]; N],
        port_current: [0.; P],
        node_port: [[0.; P]; N],
        port_node: [[0.; N]; P],
        port_port: [[0.; P]; P],
    };
    for (a, c, g) in [
        (0, N, 1. / 10000.),
        (2, N + 3, 1. / 560.),
        (3, 4, 1. / 5600.),
        (4, N + 4, 1. / 16900.),
        (
            5,
            N + 5,
            1. / (200000. + 5000. * p.cutoff * (1. - p.cutoff)),
        ),
        (
            5,
            N + 7,
            1. / (1800. + p.scale_ohm) + 1. / 100000. + 1. / 33000.,
        ),
        (6, N + 6, 1. / (68000. + 10000. * p.range * (1. - p.range))),
        (7, N + 4, 1. / 330.),
        (8, N + 2, 1. / 680.),
    ] {
        branch(&mut s, x, b, a, c, g)
    }
    let g = amount_matrix(p.amount)?;
    let u = [x[3] - b[7], x[5] - b[7]];
    let i = [
        g[0][0] * u[0] + g[0][1] * u[1],
        g[1][0] * u[0] + g[1][1] * u[1],
    ];
    for (k, a) in [3, 5].into_iter().enumerate() {
        row(
            &mut s,
            a,
            i[k],
            &[(3, g[k][0]), (5, g[k][1]), (N + 7, -g[k][0] - g[k][1])],
        );
    }
    row(
        &mut s,
        N + 7,
        -i[0] - i[1],
        &[
            (3, -g[0][0] - g[1][0]),
            (5, -g[0][1] - g[1][1]),
            (N + 7, g[0][0] + g[0][1] + g[1][0] + g[1][1]),
        ],
    );
    for (base, c, e, sign) in [
        (0, 1, 3, 1.),
        (1, 3, 2, -1.),
        (5, 7, 6, -1.),
        (6, 8, N + 7, 1.),
    ] {
        transistor(&mut s, x, b, base, c, e, sign)?;
    }
    let vt = 1.5 * 1.380649e-23 * 298.15 / 1.602176634e-19;
    let z = (x[4] - b[1]) / vt;
    if !z.is_finite() || z > 45. {
        return Err(StepError::ExponentialDomain);
    }
    let i = 1e-8 * z.exp_m1();
    let g = 1e-8 * z.exp() / vt;
    row(&mut s, 4, i, &[(4, g), (N + 1, -g)]);
    row(&mut s, N + 1, -i, &[(4, -g), (N + 1, g)]);
    if let Some((old, h)) = history {
        for (k, (a, c, cap)) in [(1, 2, p.c11_f), (5, N + 7, 100e-12)]
            .into_iter()
            .enumerate()
        {
            let g = cap / h;
            let i = g * (value(x, b, a) - value(x, b, c) - old[k]);
            row(&mut s, a, i, &[(a, g), (c, -g)]);
            row(&mut s, c, -i, &[(a, -g), (c, g)]);
        }
    }
    if s.residual
        .iter()
        .chain(s.port_current.iter())
        .chain(s.jacobian.iter().flatten())
        .chain(s.node_port.iter().flatten())
        .chain(s.port_node.iter().flatten())
        .chain(s.port_port.iter().flatten())
        .any(|v| !v.is_finite())
    {
        return Err(StepError::ExponentialDomain);
    }
    Ok(s)
}
