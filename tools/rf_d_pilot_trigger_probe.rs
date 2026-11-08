//! Compare the compact trigger with the coupled 118-node solver.
use crate::{
    family::Family,
    parameters,
    pilot_trigger::{self as local, Boundary, State, CORE, N, PORTS},
    solver, voice,
};
use std::{
    error::Error,
    fs,
    io::{BufWriter, Write},
    time::Instant,
};

const H: f64 = 1. / (48_000. * 512.);
const P: usize = PORTS.len();
const HEADER: usize = N + P;
const ROW: usize = 3 * N + P;

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

pub fn capture(path: &str, start: usize, frames: usize, key: f64) -> Result<(), Box<dyn Error>> {
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
    write(&mut out, PORTS.map(|k| node(&state, k)))?;
    for i in 0..frames * 512 {
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
            write(&mut out, PORTS.map(|k| node(&row.now, k)))?;
            write(&mut out, CORE.map(|k| row.dc[k]))?;
            write(&mut out, CORE.map(|k| row.dq[k] * H))?;
        }
        state = q.stages.chain[1].now;
        phase = q.stages.phase[1];
    }
    out.flush()?;
    Ok(())
}

fn boundary(volts: &[f64], key: f64) -> Boundary {
    Boundary {
        volts: volts.try_into().unwrap(),
        key,
        short: false,
    }
}

pub fn replay(
    path: &str,
    key: f64,
    port_stride: usize,
    step_stride: usize,
    fine_ports: u8,
) -> Result<(), Box<dyn Error>> {
    let data = read(path)?;
    let initial = State(data[..N].try_into()?);
    let rows = &data[HEADER..];
    let count = rows.len() / (2 * ROW);
    assert_eq!(rows.len(), count * 2 * ROW);
    assert!(count.is_multiple_of(port_stride) && port_stride.is_multiple_of(step_stride));
    assert!(fine_ports < 1 << P && (step_stride == 1 || fine_ports == 0));
    let get = |step: usize, stage: usize| {
        let i = (step * 2 + stage) * ROW;
        &rows[i..i + ROW]
    };
    let mut fine = initial;
    let (mut dc_error, mut charge_error, mut direction_ratio) = (0_f64, 0_f64, 0_f64);
    for i in 0..count {
        for j in 0..2 {
            let row = get(i, j);
            let change = std::array::from_fn(|k| row[k] - fine.0[k]);
            let s = local::stamp::<true>(fine, change, boundary(&row[N..HEADER], key))
                .map_err(|e| format!("stamp {i}/{j}: {e:?}"))?;
            for k in 0..N {
                dc_error = dc_error.max((s.dc[k] - row[HEADER + k]).abs());
                charge_error = charge_error.max((s.charge_c[k] - row[HEADER + N + k]).abs());
            }
        }
        if port_stride == 1 {
            let candidates = std::array::from_fn(|j| State(get(i, j)[..N].try_into().unwrap()));
            let u = std::array::from_fn(|j| boundary(&get(i, j)[N..HEADER], key));
            let ratio = local::audit_direction(fine, candidates, u, H)
                .map_err(|e| format!("direction audit {i}: {e:?}"))?;
            direction_ratio = direction_ratio.max(ratio);
        }
        fine = State(get(i, 1)[..N].try_into()?);
    }
    let mut state = initial;
    let mut previous_change = [0.; N];
    let mut previous_boundary = boundary(&data[N..HEADER], key);
    let mut maximum = [0_f64; N];
    let mut event = Vec::new();
    let start = Instant::now();
    for i in (0..count).step_by(step_stride) {
        let left = i / port_stride * port_stride;
        let previous = if left == 0 {
            &data[N..HEADER]
        } else {
            &get(left - 1, 1)[N..HEADER]
        };
        let right = &get(left + port_stride - 1, 1)[N..HEADER];
        let u = std::array::from_fn(|j| {
            if port_stride == 1 {
                boundary(&get(i, j)[N..HEADER], key)
            } else {
                let phase = ((i - left) as f64 + step_stride as f64 * [1. / 3., 1.][j])
                    / port_stride as f64;
                let volts: [f64; P] = std::array::from_fn(|k| {
                    if fine_ports & (1 << k) != 0 {
                        get(i, j)[N + k]
                    } else {
                        previous[k] + phase * (right[k] - previous[k])
                    }
                });
                boundary(&volts, key)
            }
        });
        let prior = state.order();
        let [_, accepted] = local::step(state, u, H * step_stride as f64, previous_boundary, previous_change)
            .map_err(|e| {
                let (node, error) = CORE.into_iter().zip(maximum).max_by(|a, b| a.1.total_cmp(&b.1)).unwrap();
                let row = [get(i + step_stride - 1, 0), get(i + step_stride - 1, 1)];
                let target = row.map(|r| State(r[..N].try_into().unwrap()));
                let at_reference = local::trial_diagnostic(state, target, u, H * step_stride as f64);
                let target_span = target.map(|s| CORE.into_iter().zip(s.0.into_iter().zip(state.0))
                    .map(|(k,(v,a))| (k,v-a)).max_by(|a,b| a.1.abs().total_cmp(&b.1.abs())).unwrap());
                format!("local {port_stride}/{step_stride} at fine step {i}: {e:?}; prior {node} {error:.9e} V; stamps {dc_error:.9e} A {charge_error:.9e} C; reference guess {at_reference:?} span {target_span:?}")
            })?;
        previous_change = std::array::from_fn(|k| accepted.0[k] - state.0[k]);
        state = accepted;
        previous_boundary = u[1];
        if state.order() != prior {
            event.push([i * 8, (i + step_stride) * 8, usize::from(state.order())]);
        }
        let reference = get(i + step_stride - 1, 1);
        for k in 0..N {
            maximum[k] = maximum[k].max((state.0[k] - reference[k]).abs());
        }
    }
    if port_stride == 1 {
        println!("DIRECTION,{direction_ratio:.17e}");
    }
    println!(
        "CORE,{count},{dc_error:.17e},{charge_error:.17e},{}",
        start.elapsed().as_nanos()
    );
    for (k, value) in CORE.into_iter().zip(maximum) {
        println!("NODE,{k},{value:.17e}");
    }
    for [lo, hi, sign] in event {
        println!("SWITCH,{lo},{hi},{sign}");
    }
    Ok(())
}
