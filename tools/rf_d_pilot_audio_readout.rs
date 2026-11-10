//! 96 kHz closure of the reduced audio map and the two return cells.
use super::{chain, contour_ports, voltage, Audio, Family, Returns, StepError, LOAD, PAIR, SIZE};
use crate::{
    graph,
    reduced_lu::{maximum, Lu},
};
use std::{
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};

#[cfg(pilot_stage_feedback)]
#[path = "rf_d_pilot_audio_feedback.rs"]
mod feedback;
#[cfg(pilot_stage_feedback)]
pub use feedback::run as run_feedback;

const H: f64 = 1. / 96_000.;
const LOAD_TOLERANCE_V: f64 = 1e-10;
const LOAD_PROBE_V: f64 = 1e-6;
type Stage = [f64; 3]; // C2, x34 and either x4 (imposed) or x27 (closed).
                       // Endpoint audio and returns, x4/CR6 at both stages, then first-stage x3 and VCA base.
type Output = [f64; 13];

#[derive(Clone, Copy)]
struct History {
    audio: chain::State,
    cells: Returns,
    cv: f64,
    phase: f64,
}

fn solve_cells(
    cells: &mut [Returns; 2],
    stages: [Stage; 2],
    loads: [[f64; 2]; 2],
    collector: f64,
) -> Result<(), String> {
    for i in 0..2 {
        let [c2, sum, cv] = stages[i];
        let [base, tail] = loads[i];
        cells[i].volume = contour_ports::volume(cells[i].volume, c2, [collector, cv, base])
            .map_err(|error| format!("R59 cell: {error:?}"))?;
        cells[i].filter = contour_ports::filter(cells[i].filter, [sum, tail])
            .map_err(|error| format!("R60 cell: {error:?}"))?;
    }
    Ok(())
}

fn load_tangent(
    map: &Audio,
    cells: [Returns; 2],
    stages: [Stage; 2],
    loads: [[f64; 2]; 2],
    input: [[f64; 2]; 2],
    collector: f64,
) -> Result<(Lu<4>, [f64; 4]), String> {
    let mut slope = [0.; 4];
    for i in 0..2 {
        let [c2, sum, cv] = stages[i];
        let [base, tail] = loads[i];
        let shifted_volume =
            contour_ports::volume(cells[i].volume, c2, [collector, cv, base + LOAD_PROBE_V])
                .map_err(|error| format!("R59 tangent: {error:?}"))?;
        let shifted_filter = contour_ports::filter(cells[i].filter, [sum, tail + LOAD_PROBE_V])
            .map_err(|error| format!("R60 tangent: {error:?}"))?;
        slope[2 * i] = (shifted_volume[2] - input[i][0]) / LOAD_PROBE_V;
        slope[2 * i + 1] = (shifted_filter[2] - input[i][1]) / LOAD_PROBE_V;
    }
    Ok((load_factor(map, slope)?, slope))
}

fn load_factor(map: &Audio, slope: [f64; 4]) -> Result<Lu<4>, String> {
    let response = map.reduced.as_ref().expect("audio map").load_response();
    let jacobian = std::array::from_fn(|r| {
        std::array::from_fn(|c| f64::from(r == c) - response[r][c] * slope[c])
    });
    Lu::factor(jacobian).map_err(|error| format!("load tangent: {error:?}"))
}

fn advance(
    old: History,
    map: &Audio,
    family: &Family,
    collector: f64,
    stages: [Stage; 2],
) -> Result<(History, Output, usize, f64), String> {
    let mut loads = [LOAD.map(|k| voltage(old.audio, k)); 2];
    let mut cells = [old.cells; 2];
    let mut delta = [chain::State::from_nodes([0.; chain::N]); 2];
    let mut tangent: Option<Lu<4>> = None;
    for iteration in 1..=16 {
        solve_cells(&mut cells, stages, loads, collector)?;
        let input = cells.map(|s| [s.volume[2], s.filter[2]]);
        let (now, phase, next_delta, _) = map
            .step(old.audio, input, family, old.phase, H, delta)
            .map_err(|error| format!("audio map: {error:?}"))?;
        let next = now.map(|row| LOAD.map(|k| voltage(row, k)));
        let residual = std::array::from_fn(|i| next[i / 2][i % 2] - loads[i / 2][i % 2]);
        let mismatch = residual.iter().fold(0_f64, |m, r| m.max(r.abs()));
        if mismatch <= LOAD_TOLERANCE_V {
            let [base, tail] = next[1];
            let [r59, r60] = cells[1].currents(base, tail);
            let [x3, x37] = input[1];
            let row = [
                voltage(now[1], 61),
                r59,
                r60,
                x3,
                x37,
                base,
                tail,
                0.,
                0.,
                0.,
                0.,
                cells[0].volume[2],
                next[0][0],
            ];
            return Ok((
                History {
                    audio: now[1],
                    cells: cells[1],
                    cv: stages[1][2],
                    phase,
                },
                row,
                iteration,
                mismatch,
            ));
        }
        if tangent.is_none() {
            tangent = Some(load_tangent(map, cells, stages, loads, input, collector)?.0);
        }
        let change = tangent
            .as_ref()
            .unwrap()
            .solve(residual)
            .map_err(|error| format!("load direction: {error:?}"))?;
        for i in 0..4 {
            loads[i / 2][i % 2] += change[i];
        }
        delta = next_delta;
    }
    Err(format!("interface: {:?}", StepError::IterationBudget))
}

fn advance_joint(
    old: History,
    map: &Audio,
    family: &Family,
    collector: f64,
    stages: [Stage; 2],
    closed_cv: bool,
) -> Result<(History, Output, usize, f64), String> {
    advance_joint_with(old, map, family, collector, closed_cv, |_, _| Ok(stages))
}

fn advance_joint_with(
    old: History,
    map: &Audio,
    family: &Family,
    collector: f64,
    closed_cv: bool,
    mut stages_at: impl FnMut([[f64; 2]; 2], bool) -> Result<[Stage; 2], String>,
) -> Result<(History, Output, usize, f64), String> {
    let reduced = map.reduced.as_ref().expect("audio map");
    let anchor = reduced.anchor();
    let (base, offset) = reduced.joint_history(old.audio);
    let mut x = [offset; 2];
    let mut cells = [old.cells; 2];
    let mut cv = [[old.cv, 0.]; 2];
    let mut tangent: Option<(Lu<4>, [f64; 4])> = None;
    let mut use_nodal = false;
    const BUDGET: usize = 16;
    for iteration in 1..=BUDGET {
        let loads = x.map(|row| LOAD.map(|k| voltage(anchor, k) + row[k]));
        let exact_stages = use_nodal || iteration == BUDGET;
        let stages = stages_at(loads, exact_stages)?;
        let mut slope = [0.; 4];
        for i in 0..2 {
            let [c2, sum, drive] = stages[i];
            let port = if closed_cv {
                contour_ports::Cv::Closed {
                    seed: cv[i][0],
                    cathode: drive,
                }
            } else {
                contour_ports::Cv::Fixed(drive)
            };
            let (next, [volume, filter], readout) = contour_ports::joint_cells(
                cells[i],
                [c2, sum],
                port,
                loads[i],
                collector,
                tangent.is_none(),
            )
            .map_err(|error| format!("joint return cells: {error:?}"))?;
            cells[i] = next;
            cv[i] = readout;
            slope[2 * i] = volume;
            slope[2 * i + 1] = filter;
        }
        if tangent.is_none() {
            tangent = Some((load_factor(map, slope)?, slope));
        }
        let input = cells.map(|s| [s.volume[2], s.filter[2]]);
        let current = |r: usize| x[r / SIZE][super::local(r % SIZE)];
        let mut response = [0.; PAIR];
        if !use_nodal {
            let (defect, _) = reduced
                .defects(&x, family, old.phase, H)
                .map_err(|error| format!("joint defects: {error:?}"))?;
            response = reduced.joint_response(&base, input, &defect);
            if !response.iter().all(|v| v.is_finite()) {
                return Err(format!("joint response: {:?}", StepError::InvalidInput));
            }
            let error = std::array::from_fn::<_, PAIR, _>(|r| response[r] - current(r));
            use_nodal = maximum(&error) <= 2e-12;
        }
        if use_nodal || iteration == BUDGET {
            let delta =
                x.map(|row| chain::State::from_nodes(anchor.advanced(row).difference(old.audio)));
            let (now, phase, current_error, direction) = map
                .direction(old.audio, input, family, old.phase, H, delta)
                .map_err(|error| format!("joint nodal direction: {error:?}"))?;
            let load_error: [f64; 4] =
                std::array::from_fn(|i| direction[i / 2 * SIZE + LOAD[i % 2]]);
            let mismatch = maximum(&load_error);
            if current_error <= 2e-13 && maximum(&direction) <= 2e-9 && mismatch <= LOAD_TOLERANCE_V
            {
                // An approximate stage is useful for the defect iteration only.
                // Recheck the exact drivers before publishing either history.
                if !exact_stages && stages_at(loads, true)? != stages {
                    continue;
                }
                let [base, tail] = loads[1];
                let [r59, r60] = cells[1].currents(base, tail);
                let [x3, x37] = input[1];
                let [[cv1, diode1], [cv2, diode2]] = cv;
                let row = [
                    voltage(now[1], 61),
                    r59,
                    r60,
                    x3,
                    x37,
                    base,
                    tail,
                    cv1,
                    cv2,
                    diode1,
                    diode2,
                    input[0][0],
                    loads[0][0],
                ];
                return Ok((
                    History {
                        audio: now[1],
                        cells: cells[1],
                        cv: cv2,
                        phase,
                    },
                    row,
                    iteration,
                    mismatch,
                ));
            }
            if iteration == BUDGET {
                return Err(format!(
                    "joint KCL: {current_error:.6e} A, direction {:.6e} V, loads {mismatch:.6e} V",
                    maximum(&direction)
                ));
            }
            map.checked_proposals.set(map.checked_proposals.get() + 1);
            response = std::array::from_fn(|r| current(r) + direction[r]);
        }
        let load_error = std::array::from_fn(|i| {
            let row = i / 2 * SIZE + LOAD[i % 2];
            response[row] - current(row)
        });
        let (factor, slope) = tangent.as_ref().unwrap();
        let load_change = factor
            .solve(load_error)
            .map_err(|error| format!("joint direction: {error:?}"))?;
        reduced.correct_wires(
            &mut response,
            std::array::from_fn(|i| slope[i] * load_change[i]),
        );
        for (r, value) in response.into_iter().enumerate() {
            x[r / SIZE][super::local(r % SIZE)] = value;
        }
    }
    Err(format!("joint interface: {:?}", StepError::IterationBudget))
}

fn render(
    mut state: History,
    map: &Audio,
    family: &Family,
    collector: f64,
    stages: &[[Stage; 2]],
    joint: bool,
    closed_cv: bool,
    mut emit: impl FnMut(Output),
) -> Result<(usize, f64), String> {
    let mut outer = 0;
    let mut closure_error = 0_f64;
    for (i, &row) in stages.iter().enumerate() {
        let result = if joint {
            advance_joint(state, map, family, collector, row, closed_cv)
        } else {
            advance(state, map, family, collector, row)
        };
        let (next, sample, iterations, mismatch) =
            result.map_err(|error| format!("step {i}: {error}"))?;
        state = next;
        outer = outer.max(iterations);
        closure_error = closure_error.max(mismatch);
        emit(sample);
    }
    Ok((outer, closure_error))
}

pub fn run(bench: bool, joint: bool, closed_cv: bool) -> Result<(), Box<dyn std::error::Error>> {
    run_mode(bench, joint, closed_cv, false)
}

pub fn run_stage_loads() -> Result<(), Box<dyn std::error::Error>> {
    run_mode(false, true, true, true)
}

fn run_mode(
    bench: bool,
    joint: bool,
    closed_cv: bool,
    stage_loads: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let values = read_values()?;
    let (initial, map, family, collector, rows) = prepare(&values)?;
    assert!(!rows.is_empty() && rows.len() % 6 == 0);
    let stages: Vec<[Stage; 2]> = rows
        .chunks_exact(6)
        .map(|row| [row[..3].try_into().unwrap(), row[3..].try_into().unwrap()])
        .collect();
    render_fixture(
        initial,
        &map,
        &family,
        collector,
        &stages,
        bench,
        joint,
        closed_cv,
        stage_loads,
    )
}

fn read_values() -> Result<Vec<f64>, Box<dyn std::error::Error>> {
    let mut bytes = Vec::new();
    std::io::stdin().read_to_end(&mut bytes)?;
    assert_eq!(bytes.len() % 8, 0);
    Ok(bytes
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()))
        .collect())
}

fn prepare(
    values: &[f64],
) -> Result<(History, Audio, Family, f64, &[f64]), Box<dyn std::error::Error>> {
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
    let initial = History {
        audio: chain::State {
            high: std::array::from_fn(|k| high[graph::chain_index(k)]),
            low: std::array::from_fn(|k| low[graph::chain_index(k)]),
        },
        cells: Returns {
            volume: super::VOLUME_NODES.map(x),
            filter: super::FILTER_NODES.map(x),
        },
        cv: x(4),
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
        true,
    )
    .map_err(|e| format!("audio factor: {e:?}"))?;
    Ok((initial, map, family, x(2), rows))
}

fn render_fixture(
    initial: History,
    map: &Audio,
    family: &Family,
    collector: f64,
    stages: &[[Stage; 2]],
    bench: bool,
    joint: bool,
    closed_cv: bool,
    stage_loads: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if bench {
        const RUNS: usize = 200;
        let mut times = [[0; RUNS]; 2];
        let paired = joint && !closed_cv;
        for i in 0..RUNS {
            for candidate in [closed_cv || (paired && i % 2 == 1), paired && i % 2 == 0]
                .into_iter()
                .take(if paired { 2 } else { 1 })
            {
                let start = Instant::now();
                render(
                    black_box(initial),
                    map,
                    family,
                    collector,
                    stages,
                    candidate,
                    closed_cv,
                    |row| {
                        black_box(row);
                    },
                )?;
                times[usize::from(candidate)][i] = start.elapsed().as_nanos();
            }
        }
        for group in times
            .iter_mut()
            .skip(usize::from(closed_cv))
            .take(if paired { 2 } else { 1 })
        {
            group.sort_unstable();
            println!(
                "{RUNS},{},{},{}",
                group[RUNS / 2],
                group[RUNS * 99 / 100],
                group[RUNS - 1]
            );
        }
    } else {
        let mut samples = Vec::with_capacity(stages.len());
        let (outer, mismatch) = render(
            initial,
            map,
            family,
            collector,
            stages,
            joint,
            closed_cv,
            |row| samples.push(row),
        )?;
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        let columns = if stage_loads {
            13
        } else if closed_cv {
            11
        } else {
            7
        };
        for value in [outer as f64, mismatch, map.checked_proposals.get() as f64]
            .into_iter()
            .chain(
                samples
                    .into_iter()
                    .flat_map(|row| row.into_iter().take(columns)),
            )
        {
            out.write_all(&value.to_le_bytes())?;
        }
        out.flush()?;
    }
    Ok(())
}
