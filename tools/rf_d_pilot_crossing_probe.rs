//! Native contrast and isolated event cost for the collector predictor.
#[path = "rf_d_pilot_attack_cell.rs"]
mod attack;
#[path = "rf_d_pilot_crossing.rs"]
mod crossing;
#[path = "latch_charge_driver.rs"]
mod latch_charge;

use crossing::{Event, Point, Profile};
use std::{
    error::Error,
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};

fn point(next: &mut impl FnMut() -> f64) -> Point {
    Point {
        collector: next(),
        neighbors: std::array::from_fn(|_| next()),
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    assert_eq!(raw.len(), (crossing::POINTS * 10 + 9) * 8);
    let mut values = raw
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()));
    let mut next = || values.next().unwrap();
    let profile = Profile {
        rising: std::array::from_fn(|_| point(&mut next)),
        tail: std::array::from_fn(|_| std::array::from_fn(|_| next())),
    };
    let observed = point(&mut next);
    let time = next();
    let post = [next(), next()];
    let advance = || {
        profile
            .advance(black_box(observed), time, post)
            .expect("event outside domain")
    };
    if std::env::args().nth(1).as_deref() == Some("bench") {
        const BLOCKS: usize = 2_000;
        let mut times = [0; BLOCKS];
        black_box(advance());
        for elapsed in &mut times {
            let begin = Instant::now();
            black_box(advance());
            *elapsed = begin.elapsed().as_nanos();
        }
        times.sort_unstable();
        println!(
            "{BLOCKS},{},{},{}",
            times[BLOCKS / 2],
            times[BLOCKS * 99 / 100],
            times[BLOCKS - 1]
        );
    } else {
        let Event {
            time_s,
            point,
            tail_correction_a,
        } = advance();
        let mut out = std::io::stdout().lock();
        for v in [
            time_s,
            point.collector,
            point.neighbors[0],
            point.neighbors[1],
            point.neighbors[2],
            point.neighbors[3],
            tail_correction_a,
        ] {
            out.write_all(&v.to_le_bytes())?;
        }
    }
    Ok(())
}
