//! Close both R59 stage loads while advancing the receiver and latch histories.
use super::{advance_joint_with, prepare, read_values, Audio, Family, History, Output, Stage, H};
use crate::{
    bistable::{self, Drive, State},
    graph,
    handoff::{Knot, Profile, POINTS},
    StepError,
};
use std::{hint::black_box, io::Write, time::Instant};

const R59: f64 = 68_000.;
const OBS: usize = 21;

type Pair = [[f64; 6]; 2]; // C2, x34, x27, x17, x24, x14
type Latch = [Option<(State, Drive)>; 2];

struct Event {
    slot: usize,
    seconds: f64,
    c2: f64,
    weights: [f64; 2],
    front: Profile,
    tail: Profile,
}

fn profile(values: &[f64], intervals: u8) -> Result<Profile, StepError> {
    let mut rows = values.chunks_exact(1 + 15 * 5);
    Profile::new(
        std::array::from_fn(|_| {
            let row = rows.next().unwrap();
            Knot {
                seconds: row[0],
                coefficients: std::array::from_fn(|i| {
                    row[1 + 15 * i..1 + 15 * (i + 1)].try_into().unwrap()
                }),
            }
        }),
        intervals,
    )
}

fn trial(
    old: State,
    event: Option<&Event>,
    slot: usize,
    inputs: Pair,
    bases: [f64; 2],
) -> Result<Latch, StepError> {
    let mut drives = std::array::from_fn(|i| {
        let [c2, _, _, x17, x24, x14] = inputs[i];
        Drive {
            c2,
            vca_base: bases[i],
            x17,
            x24,
            x14,
            x6: 0.,
            x9: 0.,
        }
    });
    if let Some(event) = event {
        if slot < event.slot {
            return Ok([None; 2]);
        }
        if slot == event.slot {
            drives[1].c2 = event.c2;
            let edge = event
                .front
                .at(H - event.seconds, event.weights, drives[1])?;
            return Ok([None, Some((edge, drives[1]))]);
        }
        if slot == event.slot + 1 {
            let ages = [(1. + 1. / 3.) * H - event.seconds, 2. * H - event.seconds];
            let (states, drives) = event
                .tail
                .project_c2(event.c2, ages, event.weights, drives)?;
            return Ok(std::array::from_fn(|i| Some((states[i], drives[i]))));
        }
    }
    let states = bistable::loads_step(old, drives, Some(H))?;
    Ok(std::array::from_fn(|i| Some((states[i], drives[i]))))
}

fn render(
    mut audio: History,
    mut latch: State,
    map: &Audio,
    family: &Family,
    collector: f64,
    inputs: &[Pair],
    event: Option<&Event>,
    mut emit: impl FnMut(Output, Latch),
) -> Result<[f64; 4], String> {
    let mut stats = [0_f64; 4];
    for (slot, &input) in inputs.iter().enumerate() {
        let mut previous = None;
        let mut candidate = [None; 2];
        let base_inputs: [Stage; 2] = input.map(|u| [u[0], u[1], u[2]]);
        let (next, output, iterations, mismatch) =
            advance_joint_with(audio, map, family, collector, true, |loads| {
                let bases = loads.map(|load| load[0]);
                if previous != Some(bases) {
                    candidate = trial(latch, event, slot, input, bases)
                        .map_err(|e| format!("latch step {slot}: {e:?}"))?;
                    previous = Some(bases);
                    stats[3] += f64::from(candidate[1].is_some());
                }
                Ok(std::array::from_fn(|i| match candidate[i] {
                    Some((state, u)) => [u.c2, input[i][1], state.nodes[2]],
                    None => base_inputs[i],
                }))
            })
            .map_err(|e| format!("coupled step {slot}: {e}"))?;
        stats[0] = stats[0].max(iterations as f64);
        stats[1] = stats[1].max(mismatch);
        for (entry, (x3, base)) in candidate
            .iter()
            .zip([(output[11], output[12]), (output[3], output[5])])
        {
            if let Some((state, drive)) = entry {
                let source = (state.volume[2] - drive.vca_base) / R59;
                let receiver = (x3 - base) / R59;
                stats[2] = stats[2].max((source - receiver).abs());
            }
        }
        if stats[2] > 2e-12 {
            return Err(format!("R59 step {slot}: {} A", stats[2]));
        }
        audio = next;
        if let Some((state, _)) = candidate[1] {
            latch = state;
        }
        emit(output, candidate);
    }
    Ok(stats)
}

pub fn run(bench: bool) -> Result<(), Box<dyn std::error::Error>> {
    const TABLE: usize = POINTS * (1 + 15 * 5);
    let values = read_values()?;
    let (initial, map, family, collector, rows) = prepare(&values)?;
    let x = |i| values[i] + values[graph::N + i];
    let latch = State {
        nodes: [25, 26, 27, 28, 23].map(x),
        volume: [0, 1, 3, 2, 4].map(x),
        attack: [6, 8].map(x),
        decay: [9, 10, 11].map(x),
    };
    let [slot, seconds, c2, a, b] = rows[..5].try_into()?;
    let (event, rows) = if slot == -1. {
        (None, &rows[5..])
    } else {
        if !(0. ..H).contains(&seconds)
            || slot < 0.
            || slot != slot.floor()
            || rows.len() < 5 + 2 * TABLE
        {
            return Err("invalid C4 event".into());
        }
        let front = profile(&rows[5..5 + TABLE], 1).map_err(|e| format!("front: {e:?}"))?;
        let tail =
            profile(&rows[5 + TABLE..5 + 2 * TABLE], 2).map_err(|e| format!("tail: {e:?}"))?;
        (
            Some(Event {
                slot: slot as usize,
                seconds,
                c2,
                weights: [a, b],
                front,
                tail,
            }),
            &rows[5 + 2 * TABLE..],
        )
    };
    if rows.is_empty() || rows.len() % 12 != 0 || !rows.iter().all(|v| v.is_finite()) {
        return Err("invalid coupled stages".into());
    }
    let inputs: Vec<Pair> = rows
        .chunks_exact(12)
        .map(|row| [row[..6].try_into().unwrap(), row[6..].try_into().unwrap()])
        .collect();
    if event
        .as_ref()
        .is_some_and(|e| e.slot >= inputs.len().saturating_sub(1))
    {
        return Err("C4 event must precede the projected interval".into());
    }
    if bench {
        const PASSES: usize = 200;
        let mut times = [0; PASSES];
        for elapsed in &mut times {
            let begin = Instant::now();
            black_box(render(
                black_box(initial),
                latch,
                &map,
                &family,
                collector,
                &inputs,
                event.as_ref(),
                |_, _| {},
            )?);
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
        let mut samples = Vec::new();
        let stats = render(
            initial,
            latch,
            &map,
            &family,
            collector,
            &inputs,
            event.as_ref(),
            |audio, stages| {
                samples.extend(audio);
                for stage in stages {
                    if let Some((state, drive)) = stage {
                        samples.extend(bistable::observations(state, drive));
                        samples.push(drive.c2);
                    } else {
                        samples.extend([0.; OBS]);
                    }
                }
            },
        )?;
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        for value in stats.into_iter().chain(samples) {
            out.write_all(&value.to_le_bytes())?;
        }
        out.flush()?;
    }
    Ok(())
}
