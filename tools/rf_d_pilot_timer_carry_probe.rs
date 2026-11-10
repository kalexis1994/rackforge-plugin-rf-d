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
#[cfg(pilot_native_handoff)]
use attack as attack_cell;
#[cfg(pilot_native_handoff)]
use latch_charge as latch_charge_driver;
#[cfg(pilot_native_handoff)]
pub use rf_d_circuit::StepError;
#[cfg(pilot_native_handoff)]
#[path = "rf_d_pilot_bistable_return.rs"]
mod bistable;
#[cfg(pilot_native_handoff)]
#[path = "rf_d_pilot_contour_ports.rs"]
mod contour_ports;
#[cfg(pilot_native_handoff)]
#[path = "rf_d_pilot_bistable_handoff.rs"]
mod handoff;
#[cfg(pilot_native_handoff)]
#[path = "rf_d_pilot_bistable_handoff_probe.rs"]
mod handoff_probe;
#[cfg(pilot_native_handoff)]
#[path = "rf_d_pilot_q15_return.rs"]
mod q15;
#[cfg(pilot_native_handoff)]
#[path = "rf_d_reduced_engine_lu.rs"]
mod reduced_lu;

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
    mut emit_cv: impl FnMut([f64; 3]),
) -> Option<[f64; 7]> {
    let mut voice = carry::Carry::start(family, initial)?;
    for slot in 0..64 {
        let (timers, currents) = voice.observe()?;
        emit(timers, currents, voice.filter_sum());
        let sample = voice.advance(profile, post)?;
        emit_cv(voice.cv_stages());
        match sample {
            carry::Sample::Boundary => (),
            carry::Sample::Event {
                seconds,
                timers,
                filter_sum,
            } => {
                let [c2_weight, c5_weight] = voice.load_weights();
                return Some([
                    slot as f64,
                    seconds,
                    timers[0],
                    timers[1],
                    filter_sum,
                    c2_weight,
                    c5_weight,
                ]);
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
        + carry::POST_POINTS * 31
        + carry::STATE)
        * 8;
    let mode = std::env::args().nth(1);
    #[cfg(pilot_native_handoff)]
    let native = matches!(
        mode.as_deref(),
        Some(
            "native-handoff"
                | "bench-native-handoff"
                | "native-handoff-c2"
                | "bench-native-handoff-c2"
        )
    );
    #[cfg(not(pilot_native_handoff))]
    let native = false;
    assert!(raw.len() == length || native && raw.len() > length && raw.len() % 8 == 0);
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
        readout: std::array::from_fn(|_| std::array::from_fn(|_| next())),
    }));
    let initial = std::array::from_fn(|_| next());
    #[cfg(pilot_native_handoff)]
    if native {
        return handoff_probe::run(
            values,
            || render(&family, &event, &post, initial, |_, _, _| {}, |_| {}),
            matches!(
                mode.as_deref(),
                Some("bench-native-handoff" | "bench-native-handoff-c2")
            ),
            matches!(
                mode.as_deref(),
                Some("native-handoff-c2" | "bench-native-handoff-c2")
            ),
        );
    }
    if mode.as_deref() == Some("bench") {
        const PASSES: usize = 2_000;
        let mut times = [0; PASSES];
        for elapsed in &mut times {
            let begin = Instant::now();
            black_box(
                render(
                    &family,
                    &event,
                    &post,
                    black_box(initial),
                    |_, _, _| {},
                    |_| {},
                )
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
        let mut cathodes = Vec::new();
        if let Some(event) = render(
            &family,
            &event,
            &post,
            initial,
            |timer, currents, sum| {
                states.extend(timer.into_iter().chain(currents.into_iter().flatten()));
                if with_returns {
                    states.push(sum);
                }
            },
            |row| cathodes.extend(row),
        ) {
            let mut out = std::io::stdout().lock();
            let header = if with_returns {
                &event[..5]
            } else {
                &event[..4]
            };
            let values = match mode.as_deref() {
                Some("cv-stages") => cathodes,
                Some("handoff") => event.to_vec(),
                _ => header.iter().copied().chain(states).collect(),
            };
            for value in values {
                out.write_all(&value.to_le_bytes())?;
            }
        }
    }
    Ok(())
}
