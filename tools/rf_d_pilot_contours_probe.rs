//! Inspect C2/C5 with charge memory while retaining the local latch topology.
use crate::{
    contour_ports::{Returns, FILTER_NODES, FILTER_PORTS, VOLUME_NODES, VOLUME_PORTS},
    family::Family,
    parameters,
    pilot_contours::{self as contours, Loaded, Ports, C5_PORTS, TIMER_NODES},
    pilot_trigger::{Boundary, State, CORE, N, PORTS},
    solver, voice,
};
use std::{
    error::Error,
    fs,
    io::{BufWriter, Write},
    time::Instant,
};

const H: f64 = 1. / (48_000. * 512.);
const ROW: usize = voice::N;

fn read(path: &str) -> Result<Vec<f64>, Box<dyn Error>> {
    let bytes = fs::read(path)?;
    assert_eq!(bytes.len() % 8, 0);
    Ok(bytes
        .chunks_exact(8)
        .map(|b| f64::from_le_bytes(b.try_into().unwrap()))
        .collect())
}

pub fn capture(path: &str, start: usize, frames: usize, key: f64) -> Result<(), Box<dyn Error>> {
    let data = read(path)?;
    assert_eq!(data.len(), 2 * ROW + 1);
    let mut state = voice::State {
        high: data[..ROW].try_into()?,
        low: data[ROW..2 * ROW].try_into()?,
        optional: false,
    };
    let mut phase = data[2 * ROW];
    let mut model = voice::Parameters::new(parameters()).map_err(|e| format!("{e:?}"))?;
    let family = Family::prepare(-1.6).unwrap();
    let mut workspace = solver::Workspace::new();
    let controls = voice::Controls {
        key,
        optional: false,
        short: false,
    };
    let mut out = BufWriter::new(std::io::stdout().lock());
    let mut write = |state: &voice::State| -> std::io::Result<()> {
        for (a, b) in state.high.into_iter().zip(state.low) {
            out.write_all(&(a + b).to_le_bytes())?;
        }
        Ok(())
    };
    write(&state)?;
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
            write(&row.now)?;
        }
        state = q.stages.chain[1].now;
        phase = q.stages.phase[1];
    }
    out.flush()?;
    Ok(())
}

pub fn replay(path: &str, key: f64, coarse_ports: u64) -> Result<(), Box<dyn Error>> {
    let port_stride = if coarse_ports == 0 { 1 } else { 128 };
    let data = read(path)?;
    let mut rows = data.chunks_exact(ROW);
    let initial = rows.next().ok_or("empty contour input")?;
    assert!(rows.remainder().is_empty());
    let rows: Vec<_> = rows.collect();
    let count = rows.len() / 2;
    assert!(count.is_multiple_of(port_stride) && rows.len() == 2 * count);
    let mut state = Loaded {
        timers: TIMER_NODES.map(|k| initial[k]),
        latch: State(CORE.map(|k| initial[k])),
        returns: Returns {
            volume: VOLUME_NODES.map(|k| initial[k]),
            filter: FILTER_NODES.map(|k| initial[k]),
        },
        q22_base: initial[29],
    };
    let mut previous = Boundary {
        volts: PORTS.map(|k| initial[k]),
        key,
        short: false,
    };
    let mut previous_change = [0.; N];
    let mut max_core = [0_f64; N];
    let mut max_timer = [0_f64; 2];
    let mut max_return = [0_f64; 2];
    let start = Instant::now();
    let mut elapsed_ns = 0;
    let mut max_sample_ns = 0;
    let mut events = Vec::new();
    for i in 0..count {
        let left = i / port_stride * port_stride;
        let first = if left == 0 {
            initial
        } else {
            rows[2 * left - 1]
        };
        let end = rows[2 * (left + port_stride) - 1];
        let at = |j: usize, k: usize| {
            if coarse_ports & (1 << k) == 0 {
                rows[2 * i + j][k]
            } else {
                let fraction = ((i - left) as f64 + [1. / 3., 1.][j]) / port_stride as f64;
                first[k] + fraction * (end[k] - first[k])
            }
        };
        let u = std::array::from_fn(|j| Ports {
            latch: Boundary {
                volts: PORTS.map(|k| if k == 5 { 0. } else { at(j, k) }),
                key,
                short: false,
            },
            volume: VOLUME_PORTS.map(|k| at(j, k)),
            filter: FILTER_PORTS.map(|k| at(j, k)),
            c5: C5_PORTS.map(|k| at(j, k)),
        });
        let time = Instant::now();
        let stages = contours::step(state, u, H, previous, previous_change)
            .map_err(|e| format!("reduced contour at tick {}: {e:?}", i * 8))?;
        elapsed_ns += time.elapsed().as_nanos();
        if i % 512 == 511 {
            max_sample_ns = max_sample_ns.max(elapsed_ns);
            elapsed_ns = 0;
        }
        let before = state.latch.order();
        if stages[1].latch.order() != before {
            events.push([8 * i, 8 * (i + 1), usize::from(stages[1].latch.order())]);
        }
        previous_change = std::array::from_fn(|k| stages[1].latch.0[k] - state.latch.0[k]);
        previous = u[1].latch;
        state = stages[1];
        for (j, stage) in stages.into_iter().enumerate() {
            let reference = rows[2 * i + j];
            for (err, (&node, v)) in max_core.iter_mut().zip(CORE.iter().zip(stage.latch.0)) {
                *err = err.max((v - reference[node]).abs());
            }
            for (err, (&node, v)) in max_timer
                .iter_mut()
                .zip(TIMER_NODES.iter().zip(stage.timers))
            {
                *err = err.max((v - reference[node]).abs());
            }
            let expected = [
                (reference[3] - reference[54]) / 68_000.,
                (reference[55] - reference[37]) / 680.,
            ];
            let currents = stage.returns.currents(u[j].volume[2], u[j].filter[1]);
            for (err, (measured, expected)) in max_return
                .iter_mut()
                .zip(currents.into_iter().zip(expected))
            {
                *err = err.max((measured - expected).abs());
            }
        }
    }
    println!(
        "COST,{count},{},{max_sample_ns}",
        start.elapsed().as_nanos()
    );
    for (node, error) in CORE
        .into_iter()
        .chain(TIMER_NODES)
        .zip(max_core.into_iter().chain(max_timer))
    {
        println!("NODE,{node},{error:.17e}");
    }
    println!("RETURNS,{:.17e},{:.17e}", max_return[0], max_return[1]);
    for [lo, hi, sign] in events {
        println!("SWITCH,{lo},{hi},{sign}");
    }
    Ok(())
}
