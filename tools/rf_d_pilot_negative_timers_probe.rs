//! Native parity and isolated edge cost for the negative C7 clock.
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
#[path = "rf_d_pilot_negative_timers.rs"]
mod negative;
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
    profile: &negative::Profile,
    initial: [f64; 7],
    key: f64,
    steps: usize,
    mut emit: impl FnMut(negative::Sample),
) -> Option<()> {
    let mut clock = profile.start(initial, key)?;
    emit(clock.observe()?);
    for _ in 0..steps {
        clock.advance()?;
        emit(clock.observe()?);
    }
    Some(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    assert_eq!(
        raw.len(),
        (negative::POINTS * (negative::NODES * 5 + 1) + 12) * 8
    );
    let mut values = raw
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()));
    let mut next = || values.next().unwrap();
    let profile = negative::Profile {
        direction: next(),
        nominal_timers: [next(), next()],
        knots: std::array::from_fn(|_| negative::Knot {
            progress: next(),
            nominal: std::array::from_fn(|_| next()),
            linear: std::array::from_fn(|_| std::array::from_fn(|_| next())),
            quadratic: std::array::from_fn(|_| std::array::from_fn(|_| next())),
        }),
    };
    let initial = std::array::from_fn(|_| next());
    let key = next();
    let steps = next() as usize;
    let mode = std::env::args().nth(1);
    if mode.as_deref() == Some("cv-stages") {
        let mut clock = profile.start(initial, key).ok_or("edge outside domain")?;
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        for _ in 0..steps {
            for fraction in [1. / 3., 1.] {
                let voltage = clock.cathode(fraction).ok_or("CV stage outside domain")?;
                out.write_all(&voltage.to_le_bytes())?;
            }
            clock.advance().ok_or("interval outside domain")?;
        }
        out.flush()?;
    } else if mode.as_deref() == Some("stage-sum") {
        let mut clock = profile.start(initial, key).ok_or("edge outside domain")?;
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        for _ in 0..steps {
            let sum = clock.stage_filter_sum().ok_or("stage outside domain")?;
            out.write_all(&sum.to_le_bytes())?;
            clock.advance().ok_or("interval outside domain")?;
        }
        out.flush()?;
    } else if mode.as_deref() == Some("bench") {
        const PASSES: usize = 2_000;
        let mut times = [0; PASSES];
        for elapsed in &mut times {
            let begin = Instant::now();
            render(&profile, black_box(initial), key, steps, |sample| {
                black_box(sample);
            })
            .expect("edge outside domain");
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
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        let mut samples = Vec::new();
        render(&profile, initial, key, steps, |sample| samples.push(sample))
            .expect("edge outside domain");
        for sample in samples {
            for value in sample
                .timers
                .into_iter()
                .chain([sample.c7, sample.key_port])
                .chain(sample.currents.into_iter().flatten())
            {
                out.write_all(&value.to_le_bytes())?;
            }
            if mode.as_deref() == Some("returns") {
                out.write_all(&sample.filter_sum.to_le_bytes())?;
            }
        }
    }
    Ok(())
}
