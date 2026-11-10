//! 96 kHz closure of the reduced audio map and the two return cells.
use super::{chain, contour_ports, voltage, Audio, Family, Returns, StepError, LOAD};
use crate::graph;
use std::{
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};

const H: f64 = 1. / 96_000.;
const LOAD_TOLERANCE_V: f64 = 1e-10;
type Stage = [f64; 3]; // C2, filter sum x34, volume CV return x4.
type Output = [f64; 7]; // J7, R59, R60, x3, x37, VCA base, TAIL.

#[derive(Clone, Copy)]
struct History {
    audio: chain::State,
    cells: Returns,
    phase: f64,
}

fn advance(
    old: History,
    map: &Audio,
    family: &Family,
    collector: f64,
    stages: [Stage; 2],
) -> Result<(History, Output, usize), String> {
    let mut loads = [LOAD.map(|k| voltage(old.audio, k)); 2];
    let mut cells = [old.cells; 2];
    let mut delta = [chain::State::from_nodes([0.; chain::N]); 2];
    for iteration in 1..=16 {
        for i in 0..2 {
            let [c2, sum, cv] = stages[i];
            let [base, tail] = loads[i];
            cells[i].volume = contour_ports::volume(cells[i].volume, c2, [collector, cv, base])
                .map_err(|error| format!("R59 cell: {error:?}"))?;
            cells[i].filter = contour_ports::filter(cells[i].filter, [sum, tail])
                .map_err(|error| format!("R60 cell: {error:?}"))?;
        }
        let input = cells.map(|s| [s.volume[2], s.filter[2]]);
        let (now, phase, next_delta, _) = map
            .step(old.audio, input, family, old.phase, H, delta)
            .map_err(|error| format!("audio map: {error:?}"))?;
        let next = now.map(|row| LOAD.map(|k| voltage(row, k)));
        let mismatch = next
            .iter()
            .zip(loads)
            .flat_map(|(a, b)| a.iter().zip(b).map(|(x, y)| (x - y).abs()))
            .fold(0_f64, f64::max);
        if mismatch <= LOAD_TOLERANCE_V {
            let [base, tail] = next[1];
            let [r59, r60] = cells[1].currents(base, tail);
            let [x3, x37] = input[1];
            let row = [voltage(now[1], 61), r59, r60, x3, x37, base, tail];
            return Ok((
                History {
                    audio: now[1],
                    cells: cells[1],
                    phase,
                },
                row,
                iteration,
            ));
        }
        loads = next;
        delta = next_delta;
    }
    Err(format!("interface: {:?}", StepError::IterationBudget))
}

fn render(
    mut state: History,
    map: &Audio,
    family: &Family,
    collector: f64,
    stages: &[[Stage; 2]],
    mut emit: impl FnMut(Output),
) -> Result<usize, String> {
    let mut outer = 0;
    for (i, &row) in stages.iter().enumerate() {
        let (next, sample, iterations) = advance(state, map, family, collector, row)
            .map_err(|error| format!("step {i}: {error}"))?;
        state = next;
        outer = outer.max(iterations);
        emit(sample);
    }
    Ok(outer)
}

pub fn run(bench: bool) -> Result<(), Box<dyn std::error::Error>> {
    let mut bytes = Vec::new();
    std::io::stdin().read_to_end(&mut bytes)?;
    assert_eq!(bytes.len() % 8, 0);
    let values = bytes
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()))
        .collect::<Vec<_>>();
    let (high, rest) = values.split_at(graph::N);
    let (low, rest) = rest.split_at(graph::N);
    let x = |k| high[k] + low[k];
    let family = Family::prepare(-1.6).map_err(|_| "H128 prepare")?;
    let mut phase = rest[0];
    let fine_steps = rest[1] as usize;
    assert!(fine_steps <= 768);
    for pair in rest[2..2 + 2 * fine_steps].chunks_exact(2) {
        let f1 = family.frequency(pair[0]).map_err(|_| "prefix BUS stage")?.0;
        let f2 = family
            .frequency(pair[1])
            .map_err(|_| "prefix BUS endpoint")?
            .0;
        phase = (phase + (0.75 * f1 + 0.25 * f2) * (H / 768.)).rem_euclid(1.);
    }
    let rows = &rest[2 + 2 * fine_steps..];
    assert!(!rows.is_empty() && rows.len() % 6 == 0);
    let stages: Vec<[Stage; 2]> = rows
        .chunks_exact(6)
        .map(|row| [row[..3].try_into().unwrap(), row[3..].try_into().unwrap()])
        .collect();
    let initial = History {
        audio: chain::State {
            high: std::array::from_fn(|k| high[graph::chain_index(k)]),
            low: std::array::from_fn(|k| low[graph::chain_index(k)]),
        },
        cells: Returns {
            volume: super::VOLUME_NODES.map(x),
            filter: super::FILTER_NODES.map(x),
        },
        phase,
    };
    let map = Audio::new(
        initial.audio,
        &family,
        phase,
        H,
        [x(3), x(37)],
        true,
        false,
        false,
        false,
        false,
    )
    .map_err(|e| format!("audio factor: {e:?}"))?;
    if bench {
        const RUNS: usize = 200;
        let mut times = [0; RUNS];
        for time in &mut times {
            let start = Instant::now();
            render(black_box(initial), &map, &family, x(2), &stages, |row| {
                black_box(row);
            })?;
            *time = start.elapsed().as_nanos();
        }
        times.sort_unstable();
        println!(
            "{RUNS},{},{},{}",
            times[RUNS / 2],
            times[RUNS * 99 / 100],
            times[RUNS - 1]
        );
    } else {
        let mut samples = Vec::with_capacity(stages.len());
        let outer = render(initial, &map, &family, x(2), &stages, |row| {
            samples.push(row)
        })?;
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        for value in std::iter::once(outer as f64).chain(samples.into_iter().flatten()) {
            out.write_all(&value.to_le_bytes())?;
        }
        out.flush()?;
    }
    Ok(())
}
