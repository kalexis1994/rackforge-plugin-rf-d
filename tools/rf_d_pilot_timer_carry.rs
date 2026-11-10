//! C2/C5 charge update on the loaded positive C4 path.
use crate::{
    attack::AttackCell,
    clock::{Clock, Family, Step, PERIOD_S},
    crossing,
    timer::{CurrentStep, CAPACITANCE_F, RESISTANCE_OHM},
};

pub const STATE: usize = 15;
pub const POINTS: usize = 161;
pub const POST_POINTS: usize = 33;
const RATES: [f64; 2] = [
    (1. / RESISTANCE_OHM[0][1] + 1. / RESISTANCE_OHM[0][2]) / CAPACITANCE_F,
    (1. / RESISTANCE_OHM[1][1] + 1. / RESISTANCE_OHM[1][2]) / CAPACITANCE_F,
];

type Ports = [[f64; 2]; 2];
type State = [f64; STATE];

#[derive(Clone, Copy)]
pub struct PostKnot {
    pub time: f64,
    pub nominal: Ports,
    pub linear: [Ports; 2],
    pub quadratic: [Ports; 2],
    pub sum: [f64; 5],
}

pub struct PostProfile(pub [PostKnot; POST_POINTS]);

#[derive(Clone, Copy)]
pub struct Carry<'a> {
    clock: Clock<'a, STATE, POINTS>,
    timers: [f64; 2],
    attack: [f64; 2],
    previous_attack: Option<[f64; 2]>,
    slope: Ports,
    full: [f64; 2],
    finished: bool,
}

pub enum Sample {
    Boundary,
    Event {
        seconds: f64,
        timers: [f64; 2],
        filter_sum: f64,
    },
}

pub(crate) fn weights(duration: f64) -> ([f64; 2], [f64; 2]) {
    let x = RATES.map(|rate| rate * duration);
    let moved = x.map(|v| -(-v).exp_m1());
    let w = std::array::from_fn(|i| {
        let v = x[i];
        v * (0.5 - v * (1. / 6. - v * (1. / 24. - v / 120.))) / moved[i]
    });
    (moved, w)
}

fn ports(state: &[f64; STATE]) -> Ports {
    [[state[10], state[11]], [state[12], state[13]]]
}

fn latch(state: &State) -> [f64; 2] {
    [state[0], state[9]]
}

pub(crate) fn cell_attack(latch: [f64; 2], timer: [f64; 2]) -> Option<[f64; 2]> {
    Some([
        AttackCell::Volume
            .evaluate(latch[0], timer[0])?
            .into_timer_a,
        AttackCell::Filter
            .evaluate(latch[1], timer[1])?
            .into_timer_a,
    ])
}

fn lerp(a: Ports, b: Ports, f: f64) -> Ports {
    std::array::from_fn(|i| std::array::from_fn(|k| a[i][k] + f * (b[i][k] - a[i][k])))
}

pub(crate) fn project(
    result: &mut Ports,
    from: Ports,
    to: Ports,
    begin: f64,
    end: f64,
    full: [f64; 2],
) {
    if end <= begin {
        return;
    }
    let (moved, w) = weights(end - begin);
    for i in 0..2 {
        let factor = moved[i] / full[i] * (-RATES[i] * (PERIOD_S - end)).exp();
        for k in 0..2 {
            result[i][k] += factor * (from[i][k] + w[i] * (to[i][k] - from[i][k]));
        }
    }
}

pub(crate) fn continuous_step(
    timer: [f64; 2],
    left_attack: [f64; 2],
    end: [f64; 2],
    duration: f64,
    passive: Ports,
) -> Option<[f64; 2]> {
    let (_, w) = weights(duration);
    let update = CurrentStep::new(duration);
    let mut predicted = update.advance(timer, left_attack, passive);
    for _ in 0..2 {
        let right_attack = cell_attack(end, predicted)?;
        let mean =
            std::array::from_fn(|i| left_attack[i] + w[i] * (right_attack[i] - left_attack[i]));
        predicted = update.advance(timer, mean, passive);
    }
    Some(predicted)
}

impl PostKnot {
    fn at(self, [a, b]: [f64; 2]) -> Ports {
        std::array::from_fn(|i| {
            std::array::from_fn(|k| {
                self.nominal[i][k]
                    + (a * self.linear[0][i][k] + b * self.linear[1][i][k])
                    + (a * a * self.quadratic[0][i][k] + b * b * self.quadratic[1][i][k])
            })
        })
    }
}

impl PostProfile {
    fn filter_sum(&self, duration: f64, [a, b]: [f64; 2]) -> Option<f64> {
        let i = self.0.partition_point(|row| row.time <= duration);
        if i == 0 || i == POST_POINTS {
            return None;
        }
        let left = self.0[i - 1];
        let right = self.0[i];
        let at = |row: PostKnot| {
            let [center, da, db, aa, bb] = row.sum;
            center + (a * da + b * db) + (a * a * aa + b * b * bb)
        };
        let u = (duration - left.time) / (right.time - left.time);
        Some(at(left) + u * (at(right) - at(left)))
    }

    fn project(&self, passive: &mut Ports, cross: f64, full: [f64; 2], load: [f64; 2]) {
        let duration = PERIOD_S - cross;
        let mut last = self.0[0];
        let mut from = last.at(load);
        for &next in &self.0[1..] {
            let to = next.at(load);
            if next.time >= duration {
                let fraction = (duration - last.time) / (next.time - last.time);
                project(
                    passive,
                    from,
                    lerp(from, to, fraction),
                    cross + last.time,
                    PERIOD_S,
                    full,
                );
                break;
            }
            project(
                passive,
                from,
                to,
                cross + last.time,
                cross + next.time,
                full,
            );
            last = next;
            from = to;
        }
    }
}

impl<'a> Carry<'a> {
    pub fn start(family: &'a Family<STATE, POINTS>, initial: State) -> Option<Self> {
        let clock = family.start(initial)?;
        let timers = [initial[6], initial[8]];
        Some(Self {
            clock,
            timers,
            attack: cell_attack(latch(&initial), timers)?,
            previous_attack: None,
            slope: [[0.; 2]; 2],
            full: weights(PERIOD_S).0,
            finished: false,
        })
    }

    pub fn filter_sum(&self) -> f64 {
        self.clock.state()[14]
    }

    /// The two voltages, followed by attack, decay and follower current per timer.
    pub fn observe(&self) -> Option<([f64; 2], [[f64; 3]; 2])> {
        if self.finished {
            return None;
        }
        let passive = ports(&self.clock.state());
        let currents = std::array::from_fn(|i| {
            [
                self.attack[i],
                (passive[i][0] - self.timers[i]) / RESISTANCE_OHM[i][1],
                (passive[i][1] - self.timers[i]) / RESISTANCE_OHM[i][2],
            ]
        });
        Some((self.timers, currents))
    }

    pub fn advance(&mut self, profile: &crossing::Profile, post: &PostProfile) -> Option<Sample> {
        let mut next = *self;
        let result = next.interval(profile, post)?;
        *self = next;
        Some(result)
    }

    fn interval(&mut self, profile: &crossing::Profile, post: &PostProfile) -> Option<Sample> {
        let mut passive = [[0.; 2]; 2];
        let full = self.full;
        let mut slope = self.slope;
        let step = self.clock.advance_projected(|start, end, from, to| {
            let from = ports(from);
            let to = ports(to);
            project(&mut passive, from, to, start, end, full);
            if end > start {
                slope = std::array::from_fn(|i| {
                    std::array::from_fn(|k| (to[i][k] - from[i][k]) / (end - start))
                });
            }
        })?;
        self.slope = slope;
        match step {
            Step::Boundary(state) => {
                self.timers =
                    continuous_step(self.timers, self.attack, latch(&state), PERIOD_S, passive)?;
                self.previous_attack = Some(self.attack);
                self.attack = cell_attack(latch(&state), self.timers)?;
                Some(Sample::Boundary)
            }
            Step::Guard(mut point, guard_s) => {
                let previous = self.previous_attack?;
                let guard = self.clock.state();
                if guard_s > 0. {
                    let moved = weights(guard_s).0;
                    let guard_ports = std::array::from_fn(|i| {
                        let factor = full[i] / moved[i] * (RATES[i] * (PERIOD_S - guard_s)).exp();
                        passive[i].map(|v| v * factor)
                    });
                    point.neighbors[3] = continuous_step(
                        self.timers,
                        self.attack,
                        latch(&guard),
                        guard_s,
                        guard_ports,
                    )?[0];
                } else {
                    point.neighbors[3] = self.timers[0];
                }
                let event = profile.advance(point, guard_s, [0., 0.])?;
                let cross = event.time_s;
                let x = RATES[0] * PERIOD_S;
                let xt = RATES[0] * cross;
                let m0 = xt.exp_m1() * (-x).exp() / full[0];
                let m1 = (xt * xt.exp() - xt.exp_m1()) * (-x).exp() / (x * full[0]);
                let mean = [
                    m0 * self.attack[0]
                        + m1 * (self.attack[0] - previous[0])
                        + event.tail_correction_a,
                    self.attack[1],
                ];
                let from = ports(&guard);
                let end = std::array::from_fn(|i| {
                    std::array::from_fn(|k| from[i][k] + (cross - guard_s) * self.slope[i][k])
                });
                project(&mut passive, from, end, guard_s, cross, full);
                let load = self.clock.load_weights();
                post.project(&mut passive, cross, full, load);
                let filter_sum = post.filter_sum(PERIOD_S - cross, load)?;
                self.timers = CurrentStep::new(PERIOD_S).advance(self.timers, mean, passive);
                self.finished = true;
                Some(Sample::Event {
                    seconds: cross,
                    timers: self.timers,
                    filter_sum,
                })
            }
        }
    }
}
