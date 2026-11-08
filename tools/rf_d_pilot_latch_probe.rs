use crate::{
    family::Family,
    latch_core::{self, State, BOUNDARY, CORE},
    parameters, solver, voice,
};
use std::{
    error::Error,
    fs,
    io::{BufWriter, Write},
    time::Instant,
};

const H: f64 = 1. / (48_000. * 512.);
const WORDS: usize = 21;

fn read(path: &str) -> Result<Vec<f64>, Box<dyn Error>> {
    let bytes = fs::read(path)?;
    assert_eq!(bytes.len() % 8, 0);
    Ok(bytes
        .chunks_exact(8)
        .map(|b| f64::from_le_bytes(b.try_into().unwrap()))
        .collect())
}

fn write(out: &mut impl Write, values: impl IntoIterator<Item = f64>) -> std::io::Result<()> {
    for v in values {
        out.write_all(&v.to_le_bytes())?;
    }
    Ok(())
}

fn node(s: &voice::State, k: usize) -> f64 {
    s.high[k] + s.low[k]
}

pub fn capture(path: &str, start: usize, count: usize, key: f64) -> Result<(), Box<dyn Error>> {
    let data = read(path)?;
    let n = voice::N;
    assert_eq!(data.len(), 2 * n + 1);
    let mut state = voice::State {
        high: data[..n].try_into()?,
        low: data[n..2 * n].try_into()?,
        optional: false,
    };
    let mut phase = data[2 * n];
    let mut model = voice::Parameters::new(parameters()).map_err(|e| format!("{e:?}"))?;
    let family = Family::prepare(-1.6).unwrap();
    let mut workspace = solver::Workspace::new();
    let controls = voice::Controls {
        key,
        optional: false,
        short: false,
    };
    let mut out = BufWriter::new(std::io::stdout().lock());
    write(&mut out, CORE.map(|k| node(&state, k)))?;
    write(&mut out, BOUNDARY.map(|k| node(&state, k)))?;
    write(&mut out, [node(&state, 18)])?;
    for i in 0..count * 512 {
        model.time = (start * 512 + i) as f64 * H;
        let q = voice::radau(
            &mut workspace,
            &family,
            model,
            state,
            phase,
            controls,
            H,
            80,
        )
        .map_err(|e| format!("reference {start}/{i}: {e:?}"))?;
        for row in &q.stages.chain {
            write(&mut out, CORE.map(|k| node(&row.now, k)))?;
            write(&mut out, BOUNDARY.map(|k| node(&row.now, k)))?;
            write(&mut out, CORE.map(|k| row.dc[k]))?;
            write(&mut out, CORE.map(|k| row.dq[k] * H))?;
            write(&mut out, [node(&row.now, 18)])?;
        }
        state = q.stages.chain[1].now;
        phase = q.stages.phase[1];
    }
    out.flush()?;
    Ok(())
}

pub fn replay(path: &str, mode: &str) -> Result<(), Box<dyn Error>> {
    let data = read(path)?;
    let exact = match mode {
        "fine" | "cr8-fine" => 31,
        "pilot" => 0,
        "cr8-pilot" => 7,
        value => value
            .strip_prefix("mixed-")
            .ok_or("invalid replay mode")?
            .parse::<u8>()?,
    };
    assert!(exact <= 31);
    let series_cr8 = mode.starts_with("cr8-");
    let mut state = State(data[..5].try_into()?);
    let initial = state;
    let initial_boundary: [f64; 5] = data[5..10].try_into()?;
    let initial_feed = data[10];
    let rows = &data[11..];
    let count = rows.len() / (2 * WORDS);
    assert_eq!(rows.len(), count * 2 * WORDS);
    assert_eq!(count % 128, 0);
    let get = |step: usize, stage: usize| {
        let k = (step * 2 + stage) * WORDS;
        &rows[k..k + WORDS]
    };
    let mut fine_state = initial;
    let mut dc_error = 0_f64;
    let mut charge_error = 0_f64;
    let mut maximum = 0_f64;
    let mut collector_diff = 0_f64;
    let mut event = Vec::new();
    let start = Instant::now();
    for i in 0..count {
        let first = get(i, 0);
        let last = get(i, 1);
        let left = i / 128 * 128;
        let past = if left == 0 {
            &initial_boundary[..]
        } else {
            &get(left - 1, 1)[5..10]
        };
        let next = &get(left + 127, 1)[5..10];
        let mut drivers: [[f64; 5]; 2] = if exact == 31 {
            [first[5..10].try_into()?, last[5..10].try_into()?]
        } else {
            std::array::from_fn(|j| {
                let phase = ((i - left) as f64 + [1. / 3., 1.][j]) / 128.;
                let row = [first, last][j];
                std::array::from_fn(|k| {
                    if exact & (1 << k) != 0 {
                        row[5 + k]
                    } else {
                        past[k] + phase * (next[k] - past[k])
                    }
                })
            })
        };
        if series_cr8 {
            let previous = if left == 0 {
                initial_feed
            } else {
                get(left - 1, 1)[20]
            };
            for (j, row) in [first, last].into_iter().enumerate() {
                let phase = ((i - left) as f64 + [1. / 3., 1.][j]) / 128.;
                drivers[j][4] = if exact == 31 {
                    row[20]
                } else {
                    previous + phase * (get(left + 127, 1)[20] - previous)
                };
            }
        }
        for row in [first, last] {
            let mut u: [f64; 5] = row[5..10].try_into()?;
            if series_cr8 {
                u[4] = row[20];
            }
            let audit = latch_core::stamp(fine_state, State(row[..5].try_into()?), u, series_cr8)
                .map_err(|e| format!("audit {i}: {e:?}"))?;
            for k in 0..5 {
                dc_error = dc_error.max((audit.dc[k] - row[10 + k]).abs());
                charge_error = charge_error.max((audit.charge_c[k] - row[15 + k]).abs());
            }
        }
        fine_state = State(last[..5].try_into()?);
        let prior = state.order();
        let [_, accepted] = latch_core::step(state, drivers, H, series_cr8)
            .map_err(|e| format!("local {mode}/{i}: {e:?}"))?;
        state = accepted;
        if state.order() != prior {
            event.push([i * 8, (i + 1) * 8, usize::from(state.order())]);
        }
        for k in 0..5 {
            maximum = maximum.max((state.0[k] - last[k]).abs());
        }
        collector_diff =
            collector_diff.max(((state.0[2] - state.0[4]) - (last[2] - last[4])).abs());
    }
    println!("CORE,{mode},{count},{dc_error:.17e},{charge_error:.17e},{maximum:.17e},{collector_diff:.17e},{}",
             start.elapsed().as_nanos());
    for [lo, hi, sign] in event {
        println!("SWITCH,{lo},{hi},{sign}");
    }
    Ok(())
}
