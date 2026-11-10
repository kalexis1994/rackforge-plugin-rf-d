//! Bounded collector-charge predictor and attack-tail integral at 96 kHz.
use crate::{
    attack::AttackCell,
    latch_charge::{BC, VT},
};

pub const POINTS: usize = 25;
const PANEL: usize = 8;
const PERIOD_S: f64 = 1. / 96_000.;
const TIMER_RATE: f64 = (1. / 10_000. + 1. / 10_000.) / 10e-6;
const TAIL_END_V: f64 = 8.;

#[derive(Clone, Copy)]
pub struct Point {
    pub collector: f64,
    // Q25 base, Q15 base, Q17 emitter, C2, Q15 collector.
    pub neighbors: [f64; 5],
}

impl Point {
    fn at(self, end: Self, fraction: f64) -> Self {
        Self {
            collector: self.collector + fraction * (end.collector - self.collector),
            neighbors: std::array::from_fn(|i| {
                self.neighbors[i] + fraction * (end.neighbors[i] - self.neighbors[i])
            }),
        }
    }

    fn difference(self) -> f64 {
        self.collector - self.neighbors[4]
    }
}

pub struct Profile {
    pub rising: [Point; POINTS],
    pub tail: [[f64; 4]; POINTS],
}

pub struct Event {
    pub time_s: f64,
    pub point: Point,
    pub tail_correction_a: f64,
}

fn density(point: Point, base_slope: f64) -> Option<(f64, f64)> {
    let c = point.collector;
    let [base, neighbor, emitter, timer, _] = point.neighbors;
    let attack = AttackCell::Volume.evaluate(c, timer)?;
    let vbc = base - c;
    let forward = 1e-14 * (base / VT).exp_m1();
    let reverse = 1e-14 * (vbc / VT).exp_m1();
    let decay_base =
        1e-14 * ((c - emitter) / VT).exp_m1() / 100. + 1e-14 * ((c - 9.3) / VT).exp_m1() / 5.;
    let dc = -attack.into_latch_a + (c - neighbor) / 33_000. + forward - 1.2 * reverse + decay_base;
    let cap = BC.charge(vbc).ok()?.capacitance_f + 3e-9 * 1e-14 * (vbc / VT).exp() / VT;
    let seconds_per_v = -cap * (1. - base_slope) / dc;
    (seconds_per_v.is_finite() && seconds_per_v > 0.)
        .then_some((seconds_per_v, attack.into_timer_a))
}

fn segment(from: Point, to: Point, mut visit: impl FnMut(f64, f64) -> Option<()>) -> Option<()> {
    let width = to.collector - from.collector;
    if !(width > 0.) {
        return None;
    }
    let slope = (to.neighbors[0] - from.neighbors[0]) / width;
    for i in 0..PANEL {
        let at = from.at(to, (i as f64 + 0.5) / PANEL as f64);
        let (density, current) = density(at, slope)?;
        visit(density * width / PANEL as f64, current)?;
    }
    Some(())
}

impl Profile {
    /// The observation is inside the current 96 kHz interval. The post
    /// drive is specified at its end, with slope per interval in amperes.
    pub fn advance(&self, observed: Point, guard_time_s: f64, post: [f64; 2]) -> Option<Event> {
        let (crossing, time_s) = self.crossing(observed, guard_time_s)?;
        let tail_correction_a = self.tail(crossing, time_s, post)?;
        Some(Event {
            time_s,
            point: crossing,
            tail_correction_a,
        })
    }

    fn crossing(&self, observed: Point, guard_time_s: f64) -> Option<(Point, f64)> {
        if !(0. ..PERIOD_S).contains(&guard_time_s)
            || observed.difference() >= 0.
            || observed.collector < self.rising[0].collector
        {
            return None;
        }
        let next = self
            .rising
            .iter()
            .position(|knot| knot.collector > observed.collector)?;
        if next == 0 {
            return None;
        }
        let [a, b] = [self.rising[next - 1], self.rising[next]];
        let nominal = a.at(
            b,
            (observed.collector - a.collector) / (b.collector - a.collector),
        );
        let offset: [f64; 5] =
            std::array::from_fn(|i| observed.neighbors[i] - nominal.neighbors[i]);
        let mut from = observed;
        let mut time = guard_time_s;
        for mut to in self.rising[next..].iter().copied() {
            to.neighbors = std::array::from_fn(|i| to.neighbors[i] + offset[i]);
            let crosses = to.difference() >= 0.;
            if crosses {
                let difference = from.difference();
                to = from.at(to, -difference / (to.difference() - difference));
            }
            segment(from, to, |dt, _| {
                time += dt;
                Some(())
            })?;
            if crosses {
                return (time < PERIOD_S).then_some((to, time));
            }
            from = to;
        }
        None
    }

    fn tail(&self, crossing: Point, time_s: f64, post: [f64; 2]) -> Option<f64> {
        let [post_a, post_slope_a] = post;
        let delta = (TAIL_END_V - crossing.collector) / (POINTS - 1) as f64;
        let point = |i: usize| Point {
            collector: crossing.collector + i as f64 * delta,
            neighbors: std::array::from_fn(|k| {
                if k < 4 {
                    crossing.neighbors[k] + (self.tail[i][k] - self.tail[0][k])
                } else {
                    crossing.neighbors[k]
                }
            }),
        };
        let mut time = time_s;
        let mut area = 0.;
        for i in 0..POINTS - 1 {
            segment(point(i), point(i + 1), |dt, current| {
                let at = time + 0.5 * dt;
                if !(0. ..=PERIOD_S).contains(&at) {
                    return None;
                }
                let baseline = post_a + post_slope_a * (at / PERIOD_S - 1.);
                area += (current - baseline) * (TIMER_RATE * (at - PERIOD_S)).exp() * dt;
                time += dt;
                Some(())
            })?;
        }
        Some(area * TIMER_RATE / -(-TIMER_RATE * PERIOD_S).exp_m1())
    }
}
