//! Native replay and cost of the timer pair, with the loads supplied by the lab.
#[path = "rf_d_pilot_timer_rc.rs"]
mod timer;

use std::{
    error::Error,
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};
use timer::Step;

const TICK_S: f64 = 1. / (48_000. * 4096.);
const PERIOD: usize = 2048;
const BLOCK: usize = 128 * 2;
const PASSES: usize = 2000;

fn main() -> Result<(), Box<dyn Error>> {
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    assert_eq!(raw.len() % 8, 0);
    let mut values = raw
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()));
    let mut value = || values.next().expect("truncated input");
    let mut state = [value(), value()];
    let mut ports = || std::array::from_fn(|_| std::array::from_fn(|_| value()));
    let initial = ports();
    let rows: Vec<_> = (0..(raw.len() / 8 - 8) / 7)
        .map(|_| {
            (
                value(),
                std::array::from_fn(|_| std::array::from_fn(|_| value())),
            )
        })
        .collect();
    assert_eq!(raw.len() / 8, 8 + 7 * rows.len());
    let step = Step::new(PERIOD as f64 * TICK_S);
    let mode = std::env::args().nth(1);
    if mode.as_deref() == Some("bench-held") {
        assert_eq!(rows.len(), BLOCK);
        assert!(rows.iter().all(|(ticks, _)| *ticks == PERIOD as f64));
        let mut times = Vec::with_capacity(PASSES);
        for pass in 0..=PASSES {
            let mut next = black_box(state);
            let begin = Instant::now();
            for &(_, right) in black_box(&rows) {
                next = step.advance_held(next, right);
            }
            black_box(next);
            let elapsed = begin.elapsed().as_nanos();
            if pass > 0 {
                times.push(elapsed);
            }
        }
        times.sort_unstable();
        println!(
            "{},{},{},{}",
            PASSES,
            times[PASSES / 2],
            times[PASSES * 99 / 100],
            times[PASSES - 1]
        );
    } else {
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        let mut left = initial;
        for (ticks, right) in rows {
            assert!(ticks.is_finite() && ticks > 0.);
            let update = if ticks == PERIOD as f64 {
                step
            } else {
                Step::new(ticks * TICK_S)
            };
            state = if mode.as_deref() == Some("held") {
                update.advance_held(state, right)
            } else {
                update.advance(state, left, right)
            };
            for v in state {
                out.write_all(&v.to_le_bytes())?;
            }
            left = right;
        }
        out.flush()?;
    }
    Ok(())
}
