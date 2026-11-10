//! Compare the local Radau defect and resolve a switch on the eight-tick grid.
use super::{voltage, Accepted, Failure, History, LOAD};

#[derive(Clone, Copy)]
pub(super) struct Tolerances {
    voltage: f64,
    latch: f64,
    relative: f64,
    current: f64,
    phase: f64,
}

pub(super) const STRICT: Tolerances = Tolerances {
    voltage: 2e-9,
    latch: 2e-9,
    relative: 2e-10,
    current: 2e-11,
    phase: 1e-11,
};
// Local step defect for the pilot. The complete independent reserves
// still gate currents, J7, node voltages and the exact switch bracket.
pub(super) const PORTS: Tolerances = Tolerances {
    voltage: 5e-7,
    latch: 5e-7,
    relative: 0.,
    current: 5e-11,
    phase: 1e-8,
};

pub(super) const LATCH: Tolerances = Tolerances {
    latch: 2e-8,
    ..PORTS
};

fn currents(state: History) -> [f64; 2] {
    let [base, tail] = LOAD.map(|k| voltage(state.audio, k));
    state.contour.returns.currents(base, tail)
}

fn defect(coarse: &Accepted, fine: &Accepted, tolerance: Tolerances) -> f64 {
    let scale = |v: f64| tolerance.voltage + tolerance.relative * v.abs();
    let distance = |a: f64, b: f64| (a - b).abs() / scale(b);
    let (a, b) = (coarse.end, fine.end);
    let phase = (a.phase - b.phase).abs();
    let mut error = phase.min(1. - phase) / tolerance.phase;
    for (x, y) in a.contour.latch.0.into_iter().zip(b.contour.latch.0) {
        error = error.max((x - y).abs() / (tolerance.latch + tolerance.relative * y.abs()));
    }
    for (x, y) in a.contour.timers.into_iter().zip(b.contour.timers) {
        error = error.max(distance(x, y));
    }
    for (x, y) in a
        .contour
        .returns
        .volume
        .into_iter()
        .zip(b.contour.returns.volume)
    {
        error = error.max(distance(x, y));
    }
    for i in 0..super::SIZE {
        let k = super::local(i);
        let diff = (a.audio.high[k] - b.audio.high[k]) + (a.audio.low[k] - b.audio.low[k]);
        error = error.max(diff.abs() / scale(b.audio.high[k]));
    }
    for (x, y) in currents(a).into_iter().zip(currents(b)) {
        error = error.max((x - y).abs() / tolerance.current);
    }
    error
}

fn switch(old: History, step: &Accepted) -> bool {
    let before = old.contour.latch.order();
    step.result
        .contour
        .iter()
        .any(|stage| stage.latch.order() != before)
}

#[derive(Default)]
pub(super) struct Stats {
    pub solve: usize,
    pub defect: usize,
    pub switch: usize,
    pub worst: f64,
}

pub(super) fn advance(
    old: History,
    step: impl Fn(History, usize) -> Result<Accepted, Failure>,
    proposal: &mut usize,
    max_span: usize,
    stats: &mut Stats,
    tolerance: Tolerances,
) -> Result<[Option<Accepted>; 2], Failure> {
    loop {
        let span = *proposal;
        if span == 1 {
            let result = step(old, span)?;
            *proposal = 2.min(max_span);
            return Ok([Some(result), None]);
        }
        let half = span / 2;
        let trial = (|| {
            let coarse = step(old, span)?;
            let left = step(old, half)?;
            let right = step(left.end, half)?;
            Ok::<_, Failure>((coarse, left, right))
        })();
        match trial {
            Ok((coarse, left, right)) => {
                let error = defect(&coarse, &right, tolerance);
                // The stage signs also guard switches that could be hidden
                // by comparing endpoints alone.
                let crossing =
                    switch(old, &coarse) || switch(old, &left) || switch(left.end, &right);
                if crossing && half > 1 {
                    stats.switch += 1;
                } else if error <= 1. {
                    stats.worst = stats.worst.max(error);
                    if error < 0.0625 && !crossing {
                        *proposal = (2 * span).min(max_span);
                    }
                    return Ok([Some(left), Some(right)]);
                } else {
                    stats.defect += 1;
                }
            }
            Err(_) => stats.solve += 1,
        }
        *proposal = half;
    }
}
