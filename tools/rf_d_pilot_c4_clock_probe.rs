//! Native carry from one initial state and isolated cost of the event path.
#[path = "rf_d_pilot_attack_cell.rs"]
mod attack;
#[path = "rf_d_pilot_c4_clock.rs"]
mod clock;
#[path = "rf_d_pilot_crossing.rs"]
mod crossing;
#[path = "latch_charge_driver.rs"]
mod latch_charge;
#[path = "rf_d_pilot_precursor.rs"]
mod precursor;

use std::{
    error::Error,
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};

const RATE: f64 = 96_000.;
const C2_RATE_PER_S: f64 = (1. / 10_000. + 1. / 10_000.) / 10e-6;

fn render(
    family: &clock::Family,
    profile: &crossing::Profile,
    initial: [f64; clock::STATE],
    mut emit: impl FnMut([f64; clock::STATE]),
) -> Option<[f64; 4]> {
    let mut clock = family.start(initial)?;
    let current = |state: [f64; clock::STATE]| {
        attack::AttackCell::Volume
            .evaluate(state[0], state[6])
            .map(|p| p.into_timer_a)
    };
    let mut previous_a = None;
    let mut left_a = current(initial)?;
    let mut initial = initial;
    initial[1] -= initial[2];
    emit(initial);
    for slot in 0..64 {
        match clock.advance()? {
            clock::Step::Boundary(state) => {
                previous_a = Some(left_a);
                left_a = current(state)?;
                emit(state);
            }
            clock::Step::Guard(point, time_s) => {
                let previous_a = previous_a?;
                let event = profile.advance(point, time_s, [0., 0.])?;
                let x = C2_RATE_PER_S / RATE;
                let fraction = event.time_s * RATE;
                let moved = -(-x).exp_m1();
                let xt = x * fraction;
                let m0 = xt.exp_m1() * (-x).exp() / moved;
                let m1 = (xt * xt.exp() - xt.exp_m1()) * (-x).exp() / (x * moved);
                let average = m0 * left_a + m1 * (left_a - previous_a) + event.tail_correction_a;
                return Some([slot as f64, time_s, event.time_s, average]);
            }
        }
    }
    None
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    let length = (crossing::POINTS * 10 + clock::POINTS * clock::STATE * 5 + clock::STATE) * 8;
    assert_eq!(raw.len(), length);
    let mut values = raw
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()));
    let mut next = || values.next().unwrap();
    let event = crossing::Profile {
        rising: std::array::from_fn(|_| crossing::Point {
            collector: next(),
            neighbors: std::array::from_fn(|_| next()),
        }),
        tail: std::array::from_fn(|_| std::array::from_fn(|_| next())),
    };
    let guard = clock::Family::uniform(std::array::from_fn(|_| clock::Knot {
        nominal: std::array::from_fn(|_| next()),
        linear: std::array::from_fn(|_| std::array::from_fn(|_| next())),
        quadratic: std::array::from_fn(|_| std::array::from_fn(|_| next())),
    }));
    let initial = std::array::from_fn(|_| next());
    if std::env::args().nth(1).as_deref() == Some("bench") {
        const PASSES: usize = 2_000;
        let mut times = [0; PASSES];
        for elapsed in &mut times {
            let begin = Instant::now();
            black_box(
                render(&guard, &event, black_box(initial), |_| {}).expect("event outside domain"),
            );
            *elapsed = begin.elapsed().as_nanos();
        }
        times.sort_unstable();
        println!(
            "{PASSES},{},{},{}",
            times[PASSES / 2],
            times[PASSES * 99 / 100],
            times[PASSES - 1]
        );
    } else {
        let mut states = Vec::new();
        if let Some(event) = render(&guard, &event, initial, |state| states.push(state)) {
            let mut out = std::io::stdout().lock();
            for value in event.into_iter().chain(states.into_iter().flatten()) {
                out.write_all(&value.to_le_bytes())?;
            }
        }
    }
    Ok(())
}
