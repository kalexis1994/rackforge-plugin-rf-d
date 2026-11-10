//! C7-clocked negative timer carry across one KEY edge.
use crate::{
    carry::{cell_attack, continuous_step, project, weights},
    clock::PERIOD_S,
    latch_charge::VT,
    timer::RESISTANCE_OHM,
};

pub const POINTS: usize = 65;
pub const NODES: usize = 10;
const CAP_C7: f64 = 100e-9;
const R55: f64 = 47_000.;
const R60_TRIGGER: f64 = 100_000.;
const DIODE_SCALE: f64 = 1.5 * VT;
const DIODE_IS_A: f64 = 1e-8;
type Nodes = [f64; NODES];

#[derive(Clone, Copy)]
pub struct Knot {
    pub progress: f64,
    pub nominal: Nodes,
    pub linear: [Nodes; 2],
    pub quadratic: [Nodes; 2],
}

pub struct Profile {
    pub direction: f64,
    pub nominal_timers: [f64; 2],
    pub knots: [Knot; POINTS],
}

pub struct Carry {
    time: [f64; POINTS],
    cap: [f64; POINTS],
    nodes: [Nodes; POINTS],
    relative: [f64; POINTS - 1],
    key: f64,
    slot: usize,
    timers: [f64; 2],
    full: [f64; 2],
}

pub struct Sample {
    pub timers: [f64; 2],
    pub c7: f64,
    pub key_port: f64,
    pub filter_sum: f64,
    pub currents: [[f64; 3]; 2],
}

fn key_side(capacitor: f64, key: f64) -> f64 {
    let ratio = R60_TRIGGER * DIODE_IS_A / DIODE_SCALE;
    let source = (key - capacitor) / DIODE_SCALE;
    let mut exponent = if source > 0. {
        (source / ratio).ln_1p()
    } else {
        source + ratio
    };
    for _ in 0..8 {
        let residual = exponent + ratio * exponent.exp_m1() - source;
        exponent -= residual / (1. + ratio * exponent.exp());
    }
    key - DIODE_SCALE * exponent
}

fn latch(nodes: Nodes) -> [f64; 2] {
    [nodes[1], nodes[2]]
}

fn ports(nodes: Nodes) -> [[f64; 2]; 2] {
    [[nodes[5], nodes[6]], [nodes[7], nodes[8]]]
}

impl Profile {
    /// Initial values are C2, C5, C7 and the two collector pairs.
    pub fn start(&self, initial: [f64; 7], key: f64) -> Option<Carry> {
        let [c2, c5, c7, v_left, v_right, f_left, f_right] = initial;
        if !(v_left > v_right && f_left > f_right && (0. ..=10.).contains(&key)) {
            return None;
        }
        let timers = [c2, c5];
        let load: [f64; 2] = std::array::from_fn(|i| (timers[i] - self.nominal_timers[i]) / 0.01);
        if !load.iter().all(|v| (-1. ..=1.).contains(v)) {
            return None;
        }
        let nodes = self.knots.map(|row| {
            std::array::from_fn(|k| {
                row.nominal[k]
                    + (load[0] * row.linear[0][k] + load[1] * row.linear[1][k])
                    + (load[0] * load[0] * row.quadratic[0][k]
                        + load[1] * load[1] * row.quadratic[1][k])
            })
        });
        if !nodes.iter().all(|x: &Nodes| x[1] > x[3] && x[2] > x[4]) {
            return None;
        }
        let cap = self.knots.map(|row| c7 + self.direction * row.progress);
        let speed: [f64; POINTS] = std::array::from_fn(|i| {
            let v = cap[i];
            self.direction / CAP_C7
                * ((nodes[i][0] - v) / R55 + (key_side(v, key) - v) / R60_TRIGGER)
        });
        if !speed.iter().all(|&v| v.is_finite() && v > 0.) {
            return None;
        }
        let relative = std::array::from_fn(|i| (speed[i + 1] - speed[i]) / speed[i]);
        let mut time = [0.; POINTS];
        for i in 0..POINTS - 1 {
            let r = relative[i];
            let scale = if r == 0. { 1. } else { r.ln_1p() / r };
            let distance = self.knots[i + 1].progress - self.knots[i].progress;
            time[i + 1] = time[i] + distance / speed[i] * scale;
        }
        Some(Carry {
            time,
            cap,
            nodes,
            relative,
            key,
            slot: 0,
            timers,
            full: weights(PERIOD_S).0,
        })
    }
}

impl Carry {
    fn sample(&self, time: f64) -> Option<(usize, f64, Nodes)> {
        let right = self.time.partition_point(|&v| v <= time);
        if right == 0 || right == POINTS {
            return None;
        }
        let left = right - 1;
        let u = (time - self.time[left]) / (self.time[right] - self.time[left]);
        let r = self.relative[left];
        let f = if r == 0. {
            u
        } else {
            (r.ln_1p() * u).exp_m1() / r
        };
        let cap = self.cap[left] + f * (self.cap[right] - self.cap[left]);
        let nodes = std::array::from_fn(|k| {
            self.nodes[left][k] + f * (self.nodes[right][k] - self.nodes[left][k])
        });
        Some((left, cap, nodes))
    }

    pub fn stage_filter_sum(&self) -> Option<f64> {
        let time = self.slot as f64 * PERIOD_S + PERIOD_S / 3.;
        let (_, _, nodes) = self.sample(time)?;
        Some(nodes[9])
    }

    pub fn observe(&self) -> Option<Sample> {
        let (_, c7, nodes) = self.sample(self.slot as f64 * PERIOD_S)?;
        let attack = cell_attack(latch(nodes), self.timers)?;
        let passive = ports(nodes);
        let currents = std::array::from_fn(|i| {
            [
                attack[i],
                (passive[i][0] - self.timers[i]) / RESISTANCE_OHM[i][1],
                (passive[i][1] - self.timers[i]) / RESISTANCE_OHM[i][2],
            ]
        });
        Some(Sample {
            timers: self.timers,
            c7,
            key_port: key_side(c7, self.key),
            filter_sum: nodes[9],
            currents,
        })
    }

    pub fn advance(&mut self) -> Option<()> {
        let start = self.slot as f64 * PERIOD_S;
        let end = (self.slot + 1) as f64 * PERIOD_S;
        let (first, _, left) = self.sample(start)?;
        let (last, _, right) = self.sample(end)?;
        let mut passive = [[0.; 2]; 2];
        for i in first..=last {
            let a = self.time[i];
            let b = self.time[i + 1];
            let begin = a.max(start);
            let stop = b.min(end);
            let at = |time: f64| {
                let f = (time - a) / (b - a);
                ports(std::array::from_fn(|k| {
                    self.nodes[i][k] + f * (self.nodes[i + 1][k] - self.nodes[i][k])
                }))
            };
            project(
                &mut passive,
                at(begin),
                at(stop),
                begin - start,
                stop - start,
                self.full,
            );
        }
        let attack = cell_attack(latch(left), self.timers)?;
        self.timers = continuous_step(self.timers, attack, latch(right), PERIOD_S, passive)?;
        self.slot += 1;
        Some(())
    }
}
