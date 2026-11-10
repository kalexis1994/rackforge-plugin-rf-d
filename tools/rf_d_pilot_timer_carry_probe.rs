//! Native comparison and isolated cost for C4/C2/C5 through the crossing.
#[path = "rf_d_pilot_attack_cell.rs"]
mod attack;
#[path = "rf_d_pilot_timer_carry.rs"]
mod carry;
#[path = "rf_d_pilot_c4_clock.rs"]
mod clock;
#[path = "rf_d_pilot_crossing.rs"]
mod crossing;
#[path = "latch_charge_driver.rs"]
mod latch_charge;
#[path = "rf_d_pilot_precursor.rs"]
mod precursor;
#[path = "rf_d_pilot_timer_rc.rs"]
mod timer;

use std::{
    error::Error,
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};

fn render(
    family: &clock::Family<{ carry::STATE }, { carry::POINTS }>,
    profile: &crossing::Profile,
    post: &carry::PostProfile,
    initial: [f64; carry::STATE],
    mut emit: impl FnMut([f64; 2], [[f64; 3]; 2], f64),
) -> Option<[f64; 5]> {
    let mut voice = carry::Carry::start(family, initial)?;
    for slot in 0..64 {
        let (timers, currents) = voice.observe()?;
        emit(timers, currents, voice.filter_sum());
        match voice.advance(profile, post)? {
            carry::Sample::Boundary => (),
            carry::Sample::Event {
                seconds,
                timers,
                filter_sum,
            } => {
                return Some([slot as f64, seconds, timers[0], timers[1], filter_sum]);
            }
        }
    }
    None
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    let length = (crossing::POINTS * 10
        + carry::POINTS * (carry::STATE * 5 + 1)
        + carry::POST_POINTS * 26
        + carry::STATE)
        * 8;
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
    let phase = std::array::from_fn(|_| next());
    let family = clock::Family {
        phase,
        knots: std::array::from_fn(|_| clock::Knot {
            nominal: std::array::from_fn(|_| next()),
            linear: std::array::from_fn(|_| std::array::from_fn(|_| next())),
            quadratic: std::array::from_fn(|_| std::array::from_fn(|_| next())),
        }),
    };
    let post = carry::PostProfile(std::array::from_fn(|_| carry::PostKnot {
        time: next(),
        nominal: std::array::from_fn(|_| std::array::from_fn(|_| next())),
        linear: std::array::from_fn(|_| std::array::from_fn(|_| std::array::from_fn(|_| next()))),
        quadratic: std::array::from_fn(|_| {
            std::array::from_fn(|_| std::array::from_fn(|_| next()))
        }),
        sum: std::array::from_fn(|_| next()),
    }));
    let initial = std::array::from_fn(|_| next());
    let mode = std::env::args().nth(1);
    if mode.as_deref() == Some("bench") {
        const PASSES: usize = 2_000;
        let mut times = [0; PASSES];
        for elapsed in &mut times {
            let begin = Instant::now();
            black_box(
                render(&family, &event, &post, black_box(initial), |_, _, _| {})
                    .expect("event outside domain"),
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
        let with_returns = mode.as_deref() == Some("returns");
        if let Some(event) = render(&family, &event, &post, initial, |timer, currents, sum| {
            states.extend(timer.into_iter().chain(currents.into_iter().flatten()));
            if with_returns {
                states.push(sum);
            }
        }) {
            let mut out = std::io::stdout().lock();
            let header = if with_returns {
                &event[..]
            } else {
                &event[..4]
            };
            for value in header.iter().copied().chain(states) {
                out.write_all(&value.to_le_bytes())?;
            }
        }
    }
    Ok(())
}
