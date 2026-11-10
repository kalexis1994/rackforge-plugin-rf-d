//! Native equivalence and isolated 128-frame cost of the C4 guard and event.
#[path = "rf_d_pilot_attack_cell.rs"]
mod attack;
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

fn render(
    observations: &[(f64, [f64; 8])],
    guard: &precursor::Profile,
    event: &crossing::Profile,
    mut emit: impl FnMut(usize, f64, crossing::Event),
) {
    for (i, &(collector, state)) in black_box(observations).iter().enumerate() {
        if let Some((point, guard_s)) = guard.advance(collector, state) {
            if let Some(result) = event.advance(point, guard_s, [0., 0.]) {
                emit(i, guard_s, result);
            }
        }
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    let header = (crossing::POINTS * 10 + precursor::POINTS * 41) * 8;
    assert!(raw.len() >= header && (raw.len() - header) % 72 == 0);
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
    let guard = precursor::Profile(std::array::from_fn(|_| precursor::Knot {
        collector: next(),
        nominal: std::array::from_fn(|_| next()),
        linear: std::array::from_fn(|_| std::array::from_fn(|_| next())),
        quadratic: std::array::from_fn(|_| std::array::from_fn(|_| next())),
    }));
    let observations: Vec<_> = (0..(raw.len() - header) / 72)
        .map(|_| (next(), std::array::from_fn(|_| next())))
        .collect();
    if std::env::args().nth(1).as_deref() == Some("bench") {
        const PASSES: usize = 2_000;
        assert_eq!(observations.len(), 256);
        let mut times = [0; PASSES];
        for elapsed in &mut times {
            let begin = Instant::now();
            render(&observations, &guard, &event, |_, guard_s, result| {
                black_box((guard_s, result));
            });
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
        let mut rows = Vec::new();
        render(&observations, &guard, &event, |index, guard_s, result| {
            rows.push([
                index as f64,
                guard_s,
                result.time_s,
                result.tail_correction_a,
            ]);
        });
        let mut out = std::io::stdout().lock();
        for value in rows.into_iter().flatten() {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    Ok(())
}
