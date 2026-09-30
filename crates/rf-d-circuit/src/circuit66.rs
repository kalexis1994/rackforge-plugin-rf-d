//! Experimental simultaneous 66-node circuit, analytic Jacobian and fixed arrays.
//! Topology: SVC-9 Fig.9-11 p.13, Fig.9-8 p.10, Fig.9-17 p.19 (PDF pages).
//! Same conditional device hypotheses and implicit Euler as the nested oracle.

use crate::cutoff_ladder_output;
pub use crate::cutoff_ladder_output::{Boundary, Parameters};
use crate::ladder_recovery_output::StepResult;
use crate::output::{main_load, MainLoad};
use crate::output_conversion::{max_abs, solve_linear_sparse, Parameters as ConversionParameters};
use crate::vca2_output::Parameters as Bjt;
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

const N: usize = 66;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;

// Numerical row/column numbering only, from the nominal symmetric graph at
// sample 1023 of the deadline probe. C10's edge is included even when open.
// Every future coefficient is stamped; this is not a sparsity/drop mask.
#[cfg(not(feature = "solver-natural-order"))]
const ORDER: [usize; N] = [
    23, 36, 35, 61, 17, 19, 22, 24, 29, 32, 28, 41, 40, 45, 43, 47, 48, 49, 50, 52, 53, 55, 54, 56,
    58, 57, 59, 60, 51, 46, 44, 62, 64, 63, 65, 0, 4, 16, 18, 20, 42, 39, 5, 6, 7, 8, 11, 12, 3, 9,
    13, 2, 1, 10, 14, 15, 21, 25, 27, 26, 30, 31, 33, 34, 37, 38,
];
#[cfg(feature = "solver-natural-order")]
const ORDER: [usize; N] = {
    let mut result = [0; N];
    let mut i = 0;
    while i < N {
        result[i] = i;
        i += 1;
    }
    result
};
const POSITION: [usize; N] = {
    let mut result = [0; N];
    let mut i = 0;
    while i < N {
        result[ORDER[i]] = i;
        i += 1;
    }
    result
};

fn natural_jacobian(j: &[[f64; N]; N]) -> [[f64; N]; N] {
    std::array::from_fn(|i| std::array::from_fn(|k| j[POSITION[i]][POSITION[k]]))
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    /// Same order as the independent Python 66-node oracle.
    pub node_v: [f64; N],
    pub previous_node_v: [f64; N],
    /// Four ladder cells, C24, C27, C5, C1, C9, C6, VCA C15,
    /// C4, C2, C19, amp C15, C21, C18. Left minus right, V.
    pub capacitor_v: [f64; 17],
    pub c10_capacitor_v: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Result66 {
    pub output: StepResult,
    pub residual_evaluations: usize,
}

#[derive(Clone, Copy)]
enum Terminal {
    Node(usize),
    Fixed(f64),
}
use Terminal::{Fixed, Node};
impl Terminal {
    fn value(self, x: &[f64; N]) -> f64 {
        match self {
            Node(i) => x[i],
            Fixed(v) => v,
        }
    }
}

struct Stamp<'a> {
    x: &'a [f64; N],
    r: [f64; N],
    j: [[f64; N]; N],
}
impl<'a> Stamp<'a> {
    fn branch(&mut self, left: Terminal, right: Terminal, current: f64, g: f64) {
        for (terminal, sign) in [(left, 1.0), (right, -1.0)] {
            if let Node(i) = terminal {
                self.r[i] += sign * current;
                for (other, slope) in [(left, g), (right, -g)] {
                    if let Node(k) = other {
                        self.j[POSITION[i]][POSITION[k]] += sign * slope;
                    }
                }
            }
        }
    }
    fn resistor(&mut self, left: Terminal, right: Terminal, ohm: f64) {
        let g = 1.0 / ohm;
        self.branch(
            left,
            right,
            (left.value(self.x) - right.value(self.x)) * g,
            g,
        );
    }
    fn capacitor(&mut self, left: Terminal, right: Terminal, farad: f64, old: f64, dt: f64) {
        let g = farad / dt;
        self.branch(
            left,
            right,
            g * (left.value(self.x) - right.value(self.x) - old),
            g,
        );
    }
    fn transistor(
        &mut self,
        base: Terminal,
        collector: Terminal,
        emitter: Terminal,
        polarity: f64,
        p: Bjt,
    ) -> Result<(), StepError> {
        let vt = K_B * p.temperature_k / Q_E;
        let be = polarity * (base.value(self.x) - emitter.value(self.x)) / vt;
        let bc = polarity * (base.value(self.x) - collector.value(self.x)) / vt;
        if !be.is_finite() || !bc.is_finite() || be.max(bc) > 45.0 {
            return Err(StepError::ExponentialDomain);
        }
        let f = p.transistor_is_a * be.exp_m1();
        let rev = p.transistor_is_a * bc.exp_m1();
        let gf = p.transistor_is_a * be.exp() / vt;
        let gr = p.transistor_is_a * bc.exp() / vt;
        let ib = f / p.beta_forward + rev / p.beta_reverse;
        let ic = f - (1.0 + 1.0 / p.beta_reverse) * rev;
        let db = [
            gf / p.beta_forward + gr / p.beta_reverse,
            -gr / p.beta_reverse,
            -gf / p.beta_forward,
        ];
        let dc = [
            gf - (1.0 + 1.0 / p.beta_reverse) * gr,
            (1.0 + 1.0 / p.beta_reverse) * gr,
            -gf,
        ];
        let slopes = [db, dc, std::array::from_fn(|i| -db[i] - dc[i])];
        let terminals = [base, collector, emitter];
        for row in 0..3 {
            if let Node(i) = terminals[row] {
                self.r[i] += polarity * [ib, ic, -ib - ic][row];
                for col in 0..3 {
                    if let Node(k) = terminals[col] {
                        self.j[POSITION[i]][POSITION[k]] += slopes[row][col];
                    }
                }
            }
        }
        Ok(())
    }
    fn diode(
        &mut self,
        anode: Terminal,
        cathode: Terminal,
        is_a: f64,
        ideality: f64,
        temperature: f64,
    ) -> Result<(), StepError> {
        let nvt = ideality * K_B * temperature / Q_E;
        let exponent = (anode.value(self.x) - cathode.value(self.x)) / nvt;
        if !exponent.is_finite() || exponent > 45.0 {
            return Err(StepError::ExponentialDomain);
        }
        self.branch(
            anode,
            cathode,
            is_a * exponent.exp_m1(),
            is_a * exponent.exp() / nvt,
        );
        Ok(())
    }
}

fn capacitors(b: Boundary) -> [(Terminal, Terminal, f64); 17] {
    [
        (Node(8), Node(12), 68e-9),
        (Node(9), Node(13), 68e-9),
        (Node(10), Node(14), 68e-9),
        (Node(11), Node(15), 68e-9),
        (Node(4), Fixed(0.0), 220e-6),
        (Node(6), Fixed(b.bus_v), 10e-6),
        (Node(16), Node(11), 0.22e-6),
        (Node(17), Node(15), 0.22e-6),
        (Node(23), Fixed(0.0), 100e-6),
        (Node(24), Node(25), 0.33e-6),
        (Node(26), Fixed(0.0), 220e-6),
        (Node(40), Fixed(b.recovery.vca.second.output.plus_v), 220e-6),
        (Node(46), Node(47), 10e-6),
        (Node(49), Node(50), 2.5e-6),
        (Node(57), Node(58), 220e-12),
        (Node(60), Node(61), 400e-6),
        (Node(62), Fixed(0.0), 100e-12),
    ]
}

fn valid_bjt(p: Bjt) -> bool {
    [
        p.transistor_is_a,
        p.beta_forward,
        p.beta_reverse,
        p.temperature_k,
    ]
    .iter()
    .all(|v| v.is_finite() && *v > 0.0)
}
fn prepare(
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<(crate::cutoff::PanelEquivalent, MainLoad), StepError> {
    let cb = Bjt {
        transistor_is_a: conversion.transistor_is_a,
        beta_forward: conversion.beta_forward,
        beta_reverse: conversion.beta_reverse,
        temperature_k: conversion.temperature_k,
    };
    let hb = Bjt {
        transistor_is_a: headphone.transistor_is_a,
        beta_forward: headphone.beta_forward,
        beta_reverse: headphone.beta_reverse,
        temperature_k: headphone.temperature_k,
    };
    let vb = b.recovery.vca;
    let sb = vb.second;
    let ob = sb.output.output;
    if ![p.ladder_transistor, p.cutoff.q26, p.cutoff.q28, cb, hb]
        .into_iter()
        .all(valid_bjt)
        || !matches!(p.r61_ohm, 200.0 | 200_000.0)
        || !p.r30_ohm.is_finite()
        || !(330.0..=1330.0).contains(&p.r30_ohm)
        || !b.range_fraction_from_ground.is_finite()
        || !(0.0..=1.0).contains(&b.range_fraction_from_ground)
        || b.r14_ohm
            .is_some_and(|v| !v.is_finite() || !(0.0..=50_000.0).contains(&v))
        || ![
            b.bus_v,
            vb.loudness_v,
            sb.q21_base_v,
            sb.minus_v,
            sb.output.plus_v,
        ]
        .iter()
        .all(|v| v.is_finite())
        || sb.output.plus_v <= sb.minus_v
        || !vb.first_balance_left_ohm.is_finite()
        || !(0.0..=25.0).contains(&vb.first_balance_left_ohm)
        || !sb.second_balance_left_ohm.is_finite()
        || !(0.0..=100.0).contains(&sb.second_balance_left_ohm)
        || !ob.r21_lower_ohm.is_finite()
        || !(0.0..5000.0).contains(&ob.r21_lower_ohm)
        || ob.r21_lower_ohm == 0.0
        || ![headphone.diode_is_a, headphone.diode_ideality]
            .iter()
            .all(|v| v.is_finite() && *v > 0.0)
        || conversion.diode.is_some_and(|d| {
            !d.is_a.is_finite() || d.is_a <= 0.0 || !d.ideality.is_finite() || d.ideality <= 0.0
        })
        || ob.tip_load_ohm.is_some_and(|v| !v.is_finite() || v <= 0.0)
        || ob.ring_load_ohm.is_some_and(|v| !v.is_finite() || v <= 0.0)
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    Ok((crate::cutoff::reduce_panel(b.panel)?, main_load(ob)?))
}

fn evaluate(
    x: &[f64; N],
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    prepared: (crate::cutoff::PanelEquivalent, MainLoad),
    old: Option<&State>,
) -> Result<([f64; N], [[f64; N]; N], f64), StepError> {
    let mut s = Stamp {
        x,
        r: [0.0; N],
        j: [[0.0; N]; N],
    };
    let vb = b.recovery.vca;
    let sb = vb.second;
    let plus = sb.output.plus_v;
    let minus = sb.minus_v;
    // Ladder, Fig.9-11. Documentary R61 alternatives stay explicit.
    s.resistor(Node(0), Fixed(10.0), 220.0);
    for i in 0..4 {
        s.resistor(Node(i), Node(i + 1), 150.0);
    }
    s.resistor(Node(4), Fixed(0.0), p.r61_ohm);
    s.resistor(Node(4), Node(6), 470.0);
    s.resistor(Node(4), Node(7), p.r30_ohm);
    for (base, collector, emitter) in [
        (6, Node(8), 5),
        (3, Node(9), 8),
        (2, Node(10), 9),
        (1, Node(11), 10),
        (0, Fixed(10.0), 11),
        (7, Node(12), 5),
        (3, Node(13), 12),
        (2, Node(14), 13),
        (1, Node(15), 14),
        (0, Fixed(10.0), 15),
    ] {
        s.transistor(
            Node(base),
            collector,
            Node(emitter),
            1.0,
            p.ladder_transistor,
        )?;
    }
    // Q26/Q28 and the reduced panel. R60 closes TAIL electrically.
    let panel = prepared.0;
    s.branch(
        Node(62),
        Fixed(panel.voltage_v),
        (x[62] - panel.voltage_v) * panel.conductance_s,
        panel.conductance_s,
    );
    let a = b.range_fraction_from_ground;
    s.resistor(
        Node(63),
        Fixed(10.0 * a),
        68_000.0 + 10_000.0 * a * (1.0 - a),
    );
    s.resistor(Node(64), Fixed(-10.0), 330.0);
    s.resistor(Node(65), Node(5), 680.0);
    s.transistor(Node(62), Node(64), Node(63), -1.0, p.cutoff.q26)?;
    s.transistor(Node(63), Node(65), Fixed(0.0), 1.0, p.cutoff.q28)?;
    // Recovery Q8/Q6/Q7/Q5.
    for (node, fixed, ohm) in [
        (16, 0.0, 47000.0),
        (17, 0.0, 47000.0),
        (18, minus, 220000.0),
        (19, minus, 100000.0),
        (20, minus, 1000.0),
        (23, plus, 47.0),
    ] {
        s.resistor(Node(node), Fixed(fixed), ohm);
    }
    s.resistor(Node(21), Node(22), 1000.0);
    s.resistor(Node(22), Node(23), 180.0);
    for (base, collector, emitter) in [
        (16, Node(21), 18),
        (17, Fixed(plus), 19),
        (18, Node(21), 20),
        (19, Fixed(plus), 20),
    ] {
        s.transistor(
            Node(base),
            collector,
            Node(emitter),
            1.0,
            p.ladder_transistor,
        )?;
    }
    // First VCA, including the input and first balance.
    for (left, right, ohm) in [
        (21, 24, 82000.0),
        (25, 26, 820.0),
        (26, 33, 120.0),
        (27, 28, 1000.0),
        (30, 33, 100.0 + vb.first_balance_left_ohm),
        (31, 33, 125.0 - vb.first_balance_left_ohm),
    ] {
        s.resistor(Node(left), Node(right), ohm);
    }
    for (node, fixed, ohm) in [
        (26, 0.0, 510.0),
        (29, 0.0, 6800.0),
        (29, minus, 270000.0),
        (32, vb.loudness_v, 68000.0),
    ] {
        s.resistor(Node(node), Fixed(fixed), ohm);
    }
    for (base, collector, emitter) in [(25, 30, 27), (26, 31, 27), (32, 28, 29)] {
        s.transistor(
            Node(base),
            Node(collector),
            Node(emitter),
            1.0,
            p.ladder_transistor,
        )?;
    }
    // Second VCA and its supply through R13/R11.
    for (left, right, ohm) in [
        (34, 35, 470.0),
        (37, 39, 330.0 + sb.second_balance_left_ohm),
        (38, 39, 430.0 - sb.second_balance_left_ohm),
        (39, 33, 120.0),
    ] {
        s.resistor(Node(left), Node(right), ohm);
    }
    s.resistor(Node(36), Fixed(0.0), 3300.0);
    s.resistor(Node(36), Fixed(minus), 150000.0);
    s.transistor(Node(30), Node(37), Node(34), 1.0, p.ladder_transistor)?;
    s.transistor(Node(31), Node(38), Node(34), 1.0, p.ladder_transistor)?;
    s.transistor(
        Fixed(sb.q21_base_v),
        Node(35),
        Node(36),
        1.0,
        p.ladder_transistor,
    )?;
    // PNP conversion Q1/Q12/Q17.
    let cp = Bjt {
        transistor_is_a: conversion.transistor_is_a,
        beta_forward: conversion.beta_forward,
        beta_reverse: conversion.beta_reverse,
        temperature_k: conversion.temperature_k,
    };
    for (left, right, ohm) in [(40, 39, 150.0), (42, 43, 8.2), (42, 44, 8.2)] {
        s.resistor(Node(left), Node(right), ohm);
    }
    for (node, fixed, ohm) in [
        (40, plus, 120.0),
        (41, plus, 62.0),
        (45, 0.0, 680.0),
        (46, 0.0, 680.0),
    ] {
        s.resistor(Node(node), Fixed(fixed), ohm);
    }
    for (base, collector, emitter) in [(40, 42, 41), (37, 45, 43), (38, 46, 44)] {
        s.transistor(Node(base), Node(collector), Node(emitter), -1.0, cp)?;
    }
    if let Some(d) = conversion.diode {
        s.diode(Node(46), Fixed(plus), d.is_a, d.ideality, cp.temperature_k)?;
        s.diode(Fixed(0.0), Node(46), d.is_a, d.ideality, cp.temperature_k)?;
    } else if !(0.0..=plus).contains(&x[46]) {
        return Err(StepError::ExponentialDomain);
    }
    // Panel algebraic reduction, R77 and both R21 segments.
    let ob = sb.output.output;
    s.resistor(Node(47), Fixed(0.0), 1000.0 + prepared.1.equivalent_ohm);
    s.resistor(Node(47), Node(48), 1000.0);
    s.resistor(Node(48), Node(49), 5000.0 - ob.r21_lower_ohm);
    s.resistor(Node(49), Fixed(0.0), ob.r21_lower_ohm);
    // Board 3 circuit 11, Fig.9-8. Separate device parameters and ±20 V supply.
    for (node, fixed, ohm) in [
        (50, -10.0, 6200.0),
        (50, 0.0, 24000.0),
        (55, -20.0, 10.0),
        (53, 0.0, 1200.0),
        (58, 0.0, 10.0),
        (61, 0.0, 390.0),
    ] {
        s.resistor(Node(node), Fixed(fixed), ohm);
    }
    for (left, right, ohm) in [
        (51, 54, 390.0),
        (56, 60, 4.7),
        (60, 59, 4.7),
        (53, 57, 390.0),
    ] {
        s.resistor(Node(left), Node(right), ohm);
    }
    for load in [ob.tip_load_ohm, ob.ring_load_ohm].into_iter().flatten() {
        s.resistor(Node(61), Fixed(0.0), load);
    }
    let hp = Bjt {
        transistor_is_a: headphone.transistor_is_a,
        beta_forward: headphone.beta_forward,
        beta_reverse: headphone.beta_reverse,
        temperature_k: headphone.temperature_k,
    };
    s.transistor(Node(50), Fixed(-20.0), Node(51), -1.0, hp)?;
    s.transistor(Node(54), Node(55), Node(56), -1.0, hp)?;
    s.transistor(Node(57), Node(58), Node(59), 1.0, hp)?;
    for (anode, cathode) in [(52, 51), (53, 52)] {
        s.diode(
            Node(anode),
            Node(cathode),
            headphone.diode_is_a,
            headphone.diode_ideality,
            hp.temperature_k,
        )?;
    }
    let mut i10 = 0.0;
    if let Some(old) = old {
        let dt = ob.dt_s;
        for (i, (left, right, farad)) in capacitors(b).into_iter().enumerate() {
            s.capacitor(left, right, farad, old.capacitor_v[i], dt);
        }
        if let Some(r14) = b.r14_ohm {
            let series = r14 + 1000.0 - (p.r30_ohm - 330.0);
            let gc = 10e-6 / dt;
            let y = gc / (1.0 + gc * series);
            i10 = y * (x[22] - x[7] - old.c10_capacitor_v);
            s.branch(Node(22), Node(7), i10, y);
        }
    }
    if s.r
        .iter()
        .chain(s.j.iter().flatten())
        .any(|v| !v.is_finite())
    {
        return Err(StepError::ExponentialDomain);
    }
    Ok((s.r, s.j, i10))
}

fn solve(
    mut x: [f64; N],
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    prepared: (crate::cutoff::PanelEquivalent, MainLoad),
    old: Option<&State>,
    budget: SolverBudget,
    evaluations: &mut usize,
) -> Result<([f64; N], usize, f64, f64, f64), StepError> {
    let mut cached = None;
    for iteration in 0..budget.iterations {
        let (r, j, i10) = match cached.take() {
            Some(v) => v,
            None => {
                *evaluations += 1;
                evaluate(&x, p, conversion, headphone, b, prepared, old)?
            }
        };
        let error = max_abs(&r);
        if error < 1e-11 {
            let control = std::array::from_fn::<_, 4, _>(|i| r[62 + i]);
            return Ok((x, iteration, error, i10, max_abs(&control)));
        }
        let ordered_direction = solve_linear_sparse(j, std::array::from_fn(|i| -r[ORDER[i]]))?;
        let direction: [f64; N] = std::array::from_fn(|i| ordered_direction[POSITION[i]]);
        let mut accepted = None;
        for power in 0..budget.line_search_halvings {
            let f = 0.5_f64.powi(power as i32);
            let candidate = std::array::from_fn(|i| x[i] + f * direction[i]);
            *evaluations += 1;
            if let Ok(next) = evaluate(&candidate, p, conversion, headphone, b, prepared, old) {
                if max_abs(&next.0) < error {
                    accepted = Some((candidate, next));
                    break;
                }
            }
        }
        if let Some((candidate, next)) = accepted {
            x = candidate;
            cached = Some(next);
        } else {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}

fn charges(x: &[f64; N], b: Boundary) -> [f64; 17] {
    capacitors(b).map(|(left, right, _)| left.value(x) - right.value(x))
}

/// Offline microbenchmark at one accepted operating point, not an audio deadline
/// claim. The feature keeps clocks and timing loops out of ordinary builds.
#[cfg(feature = "solver-profiling")]
pub fn profile_kernels(
    previous: &State,
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
) -> Result<(f64, f64, f64, [usize; N]), StepError> {
    use std::hint::black_box;
    use std::time::Instant;
    const REPEATS: usize = 8192;
    let prepared = prepare(p, conversion, headphone, b, SolverBudget::default())?;
    let (r, ordered_j, _) = evaluate(
        &previous.node_v,
        p,
        conversion,
        headphone,
        b,
        prepared,
        Some(previous),
    )?;
    let j = natural_jacobian(&ordered_j);
    // Both loops are warmed; copying the input matrix is included in solve cost.
    for _ in 0..256 {
        black_box(evaluate(
            black_box(&previous.node_v),
            p,
            conversion,
            headphone,
            b,
            prepared,
            Some(previous),
        )?);
        black_box(solve_linear_sparse(black_box(j), black_box(r))?);
    }
    let start = Instant::now();
    for _ in 0..REPEATS {
        black_box(evaluate(
            black_box(&previous.node_v),
            p,
            conversion,
            headphone,
            b,
            prepared,
            Some(previous),
        )?);
    }
    let stamp_us = start.elapsed().as_secs_f64() * 1e6 / REPEATS as f64;
    let start = Instant::now();
    for _ in 0..REPEATS {
        black_box(solve_linear_sparse(black_box(j), black_box(r))?);
    }
    let factor_us = start.elapsed().as_secs_f64() * 1e6 / REPEATS as f64;
    let mut graph = std::array::from_fn::<_, N, _>(|i| {
        std::array::from_fn::<_, N, _>(|k| i != k && (j[i][k] != 0.0 || j[k][i] != 0.0))
    });
    graph[7][22] = true;
    graph[22][7] = true;
    let mut removed = [false; N];
    let mut order = [0; N];
    for selected in &mut order {
        let node = (0..N)
            .filter(|i| !removed[*i])
            .min_by_key(|i| (0..N).filter(|k| !removed[*k] && graph[*i][*k]).count())
            .unwrap();
        *selected = node;
        for i in 0..N {
            if !removed[i] && graph[node][i] {
                for k in 0..N {
                    if !removed[k] && graph[node][k] && i != k {
                        graph[i][k] = true;
                    }
                }
            }
        }
        removed[node] = true;
    }
    // Permutation is outside the timed loop: measure the factorization alone.
    let matrix: [[f64; N]; N] =
        std::array::from_fn(|i| std::array::from_fn(|k| j[order[i]][order[k]]));
    let rhs = std::array::from_fn(|i| r[order[i]]);
    let start = Instant::now();
    for _ in 0..REPEATS {
        black_box(solve_linear_sparse(black_box(matrix), black_box(rhs))?);
    }
    let ordered_factor_us = start.elapsed().as_secs_f64() * 1e6 / REPEATS as f64;
    Ok((stamp_us, factor_us, ordered_factor_us, order))
}

/// Provisional KCL and analytic Jacobian for circuit diagnostics. All capacitor
/// histories come from `previous`; this never publishes a candidate state.
pub fn linearize(
    previous: &State,
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    candidate: &[f64; N],
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let prepared = prepare(p, conversion, headphone, b, SolverBudget::default())?;
    if previous
        .node_v
        .iter()
        .chain(previous.capacitor_v.iter())
        .any(|v| !v.is_finite())
        || !previous.c10_capacitor_v.is_finite()
        || candidate.iter().any(|v| !v.is_finite())
    {
        return Err(StepError::InvalidInput);
    }
    let (r, j, _) = evaluate(
        candidate,
        p,
        conversion,
        headphone,
        b,
        prepared,
        Some(previous),
    )?;
    Ok((r, natural_jacobian(&j)))
}

/// Uses the validated nested DC initializer as a seed, then closes every node
/// simultaneously with capacitors open. No seed is an audible parameter.
pub fn initial_state(
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    ladder_seed: [f64; 16],
) -> Result<State, StepError> {
    let budget = SolverBudget::default();
    let prepared = prepare(p, conversion, headphone, b, budget)?;
    let nested = cutoff_ladder_output::initial_state(p, conversion, headphone, b, ladder_seed)?;
    let mut x = [0.0; N];
    x[..16].copy_from_slice(&nested.chain.node_v);
    let r = &nested.chain.recovery;
    x[16..24].copy_from_slice(&r.node_v);
    x[24..34].copy_from_slice(&r.vca.node_v);
    x[34..40].copy_from_slice(&r.vca.second.node_v);
    let c = &r.vca.second.downstream;
    x[40..47].copy_from_slice(&c.node_v);
    x[47] = c.output.c2_right_v;
    x[49] = c.output.panel.r21_wiper_v;
    x[50..62].copy_from_slice(&c.output.panel.amp.node_v);
    x[62..].copy_from_slice(&nested.cutoff.node_v);
    let mut evaluations = 0;
    let solved = solve(
        x,
        p,
        conversion,
        headphone,
        b,
        prepared,
        None,
        budget,
        &mut evaluations,
    )?;
    Ok(State {
        node_v: solved.0,
        previous_node_v: solved.0,
        capacitor_v: charges(&solved.0, b),
        c10_capacitor_v: solved.0[22] - solved.0[7],
    })
}

/// Experimental global Newton step. Fixed capacitor histories, bounded
/// predictor fallback and publication only after all 66 KCL rows converge.
pub fn step(
    state: &mut State,
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<Result66, StepError> {
    let prepared = prepare(p, conversion, headphone, b, budget)?;
    if state
        .node_v
        .iter()
        .chain(state.previous_node_v.iter())
        .chain(state.capacitor_v.iter())
        .any(|v| !v.is_finite())
        || !state.c10_capacitor_v.is_finite()
    {
        return Err(StepError::InvalidInput);
    }
    let predicted = std::array::from_fn(|i| 2.0 * state.node_v[i] - state.previous_node_v[i]);
    if predicted.iter().any(|v| !v.is_finite()) {
        return Err(StepError::InvalidInput);
    }
    let mut evaluations = 0;
    let (solution, fallback) = match solve(
        predicted,
        p,
        conversion,
        headphone,
        b,
        prepared,
        Some(state),
        budget,
        &mut evaluations,
    ) {
        Ok(v) => (v, false),
        Err(_) => (
            solve(
                state.node_v,
                p,
                conversion,
                headphone,
                b,
                prepared,
                Some(state),
                budget,
                &mut evaluations,
            )?,
            true,
        ),
    };
    let x = solution.0;
    let ob = b.recovery.vca.second.output.output;
    let series = b.r14_ohm.unwrap_or(0.0) + 1000.0 - (p.r30_ohm - 330.0);
    let c10_v = if b.r14_ohm.is_some() {
        x[22] - x[7] - series * solution.3
    } else {
        state.c10_capacitor_v
    };
    let pin21 = x[47] * prepared.1.equivalent_ohm / (1000.0 + prepared.1.equivalent_ohm);
    let hi = pin21 * prepared.1.hi_to_pin21;
    let result = StepResult {
        j7_v: x[61],
        j4_hi_v: hi,
        j5_lo_v: hi * prepared.1.lo_to_hi,
        iterations: solution.1,
        recovery_port_evaluations: 0,
        predictor_fallback: fallback,
        max_ladder_kcl_residual_a: solution.2,
        max_cutoff_kcl_residual_a: solution.4,
        board_input_current_a: 10e-6 / ob.dt_s * (b.bus_v - x[6] + state.capacitor_v[5]),
        c5_c1_current_a: [
            0.22e-6 / ob.dt_s * (x[11] - x[16] + state.capacitor_v[6]),
            0.22e-6 / ob.dt_s * (x[15] - x[17] + state.capacitor_v[7]),
        ],
        c10_return_current_a: solution.3,
        c10_capacitor_v: c10_v,
        tail_current_a: (x[5] - x[65]) / 680.0,
    };
    *state = State {
        node_v: x,
        previous_node_v: state.node_v,
        capacitor_v: charges(&x, b),
        c10_capacitor_v: c10_v,
    };
    Ok(Result66 {
        output: result,
        residual_evaluations: evaluations,
    })
}
