//! Exercise the attack port pair with the same cell used for timing.
#[path = "rf_d_pilot_attack_cell.rs"]
mod attack;
#[path = "rf_d_pilot_timer_rc.rs"]
mod timer;

use std::{
    error::Error,
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};

use attack::AttackCell::{Filter, Volume};

const PAIR: [attack::AttackCell; 2] = [Volume, Filter];

fn evaluate(cell: attack::AttackCell, latch: f64, timer: f64) -> attack::Ports {
    cell.evaluate(latch, timer)
        .unwrap_or_else(|| panic!("cell at {latch}, {timer}"))
}

fn measure(mut block: impl FnMut()) {
    const PASSES: usize = 2_000;
    let mut times = Vec::with_capacity(PASSES);
    for pass in 0..=PASSES {
        let begin = Instant::now();
        block();
        let elapsed = begin.elapsed().as_nanos();
        if pass > 0 {
            times.push(elapsed);
        }
    }
    times.sort_unstable();
    println!(
        "{PASSES},{},{},{}",
        times[PASSES / 2],
        times[PASSES * 99 / 100],
        times[PASSES - 1]
    );
}

fn coupled_timers(raw: &[u8], bench: bool) -> std::io::Result<()> {
    assert!(raw.len() >= 16 && (raw.len() - 16) % 48 == 0);
    let mut values = raw
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()));
    let initial = [values.next().unwrap(), values.next().unwrap()];
    let rows: Vec<[[f64; 3]; 2]> = (0..(raw.len() - 16) / 48)
        .map(|_| std::array::from_fn(|_| std::array::from_fn(|_| values.next().unwrap())))
        .collect();
    let step = timer::CurrentStep::new(1. / 96_000.);
    let advance = |state: [f64; 2], row: [[f64; 3]; 2]| {
        let current = std::array::from_fn(|i| evaluate(PAIR[i], row[i][0], state[i]).into_timer_a);
        step.advance(
            state,
            current,
            row.map(|[_, decay, follower]| [decay, follower]),
        )
    };
    if bench {
        assert_eq!(rows.len(), 2 * 128);
        measure(|| {
            let mut state = black_box(initial);
            for &row in black_box(&rows) {
                state = advance(state, row);
            }
            black_box(state);
        });
    } else {
        let mut state = initial;
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        for row in rows {
            state = advance(state, row);
            for v in state {
                out.write_all(&v.to_le_bytes())?;
            }
        }
        out.flush()?;
    }
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    let mode = std::env::args().nth(1);
    if matches!(mode.as_deref(), Some("current" | "bench-current")) {
        coupled_timers(&raw, mode.as_deref() == Some("bench-current"))?;
        return Ok(());
    }
    assert_eq!(raw.len() % 32, 0);
    let rows: Vec<_> = raw
        .chunks_exact(32)
        .map(|row| {
            let mut v = row
                .chunks_exact(8)
                .map(|x| f64::from_le_bytes(x.try_into().unwrap()));
            PAIR.map(|_| [v.next().unwrap(), v.next().unwrap()])
        })
        .collect();
    let ports = |row: [[f64; 2]; 2]| {
        PAIR.into_iter()
            .zip(row)
            .map(|(cell, [latch, timer])| evaluate(cell, latch, timer))
    };
    if mode.as_deref() == Some("bench") {
        assert_eq!(rows.len(), 2 * 128);
        measure(|| {
            for &row in black_box(&rows) {
                for port in ports(row) {
                    black_box(port);
                }
            }
        });
    } else {
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        for row in rows {
            for port in ports(row) {
                for v in [
                    port.base_v,
                    port.timer_port_v,
                    port.into_timer_a,
                    port.into_latch_a,
                ] {
                    out.write_all(&v.to_le_bytes())?;
                }
            }
        }
        out.flush()?;
    }
    Ok(())
}
