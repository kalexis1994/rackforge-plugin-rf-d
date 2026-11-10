//! Close both R59 stage loads while advancing the receiver and latch histories.
use super::{
    advance_joint_with, prepare, read_values, Audio, DefectBlocks, Family, History, JointGuess,
    Output, Stage, H,
};
use crate::{
    bistable::{self, Drive, State},
    clock_fixture, graph,
    handoff::{Knot, Profile, POINTS},
    StepError,
};
use std::{hint::black_box, io::Write, time::Instant};

const R59: f64 = 68_000.;
const OBS: usize = 21;
const BLOCK_STEPS: usize = 256;

type Pair = [[f64; 6]; 2]; // C2, x34, x27, x17, x24, x14
type Latch = [Option<(State, Drive)>; 2];

#[derive(Clone, Copy)]
enum Candidate<'a> {
    Exact,
    Frozen,
    Packed(&'a DefectBlocks),
    Seeded(&'a DefectBlocks),
    Accelerated(&'a DefectBlocks),
    Vector(&'a DefectBlocks),
    EarlyNewton(&'a DefectBlocks, usize),
}

#[derive(Clone, Copy)]
enum Matrix {
    Scalar,
    Packed,
    Seeded,
    Accelerated,
    Vector,
    Block(usize),
}

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
    candidate_mode: Candidate<'_>,
    mut emit: impl FnMut(Output, Latch),
) -> Result<[f64; 7], String> {
    let frozen = !matches!(candidate_mode, Candidate::Exact);
    let packed = match candidate_mode {
        Candidate::Packed(blocks)
        | Candidate::Seeded(blocks)
        | Candidate::Accelerated(blocks)
        | Candidate::Vector(blocks)
        | Candidate::EarlyNewton(blocks, _) => Some(blocks),
        _ => None,
    };
    let seeded = matches!(candidate_mode, Candidate::Seeded(_));
    let accelerate = matches!(candidate_mode, Candidate::Accelerated(_));
    let vector_residual = matches!(
        candidate_mode,
        Candidate::Vector(_) | Candidate::EarlyNewton(_, _)
    );
    let newton_after = match candidate_mode {
        Candidate::EarlyNewton(_, iterations) => iterations,
        _ => 0,
    };
    let mut previous_audio = None;
    // Maximum iterations, voltage/current mismatch, latch calls, total iterations, seeds, retries.
    let mut stats = [0_f64; 7];
    for (slot, &input) in inputs.iter().enumerate() {
        let base_inputs: [Stage; 2] = input.map(|u| [u[0], u[1], u[2]]);
        let predict = seeded && event.is_none_or(|event| slot != event.slot);
        let mut guess = JointGuess {
            packed,
            previous: previous_audio.as_ref().filter(|_| predict),
            accelerate,
            vector_residual,
            newton_after,
        };
        stats[5] += f64::from(guess.previous.is_some() || accelerate);
        let (next, output, iterations, mismatch, candidate) = loop {
            let mut previous = None;
            let mut candidate = [None; 2];
            let result = advance_joint_with(
                audio,
                map,
                family,
                collector,
                true,
                guess,
                |loads, exact| {
                    let bases = loads.map(|load| load[0]);
                    if previous.is_none() || ((!frozen || exact) && previous != Some(bases)) {
                        candidate = trial(latch, event, slot, input, bases)
                            .map_err(|e| format!("latch step {slot}: {e:?}"))?;
                        previous = Some(bases);
                        stats[3] += f64::from(candidate[1].is_some());
                    }
                    Ok(std::array::from_fn(|i| match candidate[i] {
                        Some((state, u)) => [u.c2, input[i][1], state.nodes[2]],
                        None => base_inputs[i],
                    }))
                },
            );
            match result {
                Ok((next, output, iterations, mismatch)) => {
                    break (next, output, iterations, mismatch, candidate)
                }
                Err(_) if guess.previous.is_some() || guess.accelerate => {
                    guess.previous = None;
                    guess.accelerate = false;
                    stats[6] += 1.;
                }
                Err(error) => return Err(format!("coupled step {slot}: {error}")),
            }
        };
        stats[4] += iterations as f64;
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
        previous_audio = Some(audio.audio);
        audio = next;
        if let Some((state, _)) = candidate[1] {
            latch = state;
        }
        emit(output, candidate);
    }
    Ok(stats)
}

fn render_driven(
    audio: History,
    latch: State,
    map: &Audio,
    family: &Family,
    collector: f64,
    inputs: &[Pair],
    event: Option<&mut Event>,
    clock: Option<&clock_fixture::Fixture>,
    candidate: Candidate<'_>,
    emit: impl FnMut(Output, Latch),
) -> Result<[f64; 7], String> {
    let Some(clock) = clock else {
        return render(
            audio,
            latch,
            map,
            family,
            collector,
            inputs,
            event.as_deref(),
            candidate,
            emit,
        );
    };
    let event = event.ok_or("missing block profiles")?;
    let mut boundary = [0.; 64];
    let mut cv = [[0.; 3]; 64];
    let mut count = 0;
    let mut stages = 0;
    let [slot, seconds, c2, _, _, a, b] = clock
        .render(
            |timers, _, _| {
                boundary[count] = timers[0];
                count += 1;
            },
            |row| {
                cv[stages] = row;
                stages += 1;
            },
        )
        .ok_or("C4 event outside block domain")?;
    let slot = slot as usize;
    if slot + 1 != count || count != stages || !cv[..count].iter().flatten().all(|v| v.is_finite())
    {
        return Err("C4 stages incomplete at block handoff".into());
    }
    event.slot = slot;
    event.seconds = seconds;
    event.c2 = c2;
    event.weights = [a, b];
    let mut driven: [Pair; BLOCK_STEPS] = inputs.try_into().map_err(|_| "expected 128 frames")?;
    for i in 0..=slot {
        driven[i][0][0] = cv[i][2];
        driven[i][0][2] = cv[i][0];
        if i < slot {
            driven[i][1][0] = boundary[i + 1];
            driven[i][1][2] = cv[i][1];
        }
    }
    render(
        audio,
        latch,
        map,
        family,
        collector,
        &driven,
        Some(event),
        candidate,
        emit,
    )
}

pub fn run_block(bench: bool) -> Result<(), Box<dyn std::error::Error>> {
    let newton_after = match std::env::args().nth(2) {
        Some(value) => {
            let iterations: usize = value
                .strip_prefix("--newton-after=")
                .ok_or("expected --newton-after=N")?
                .parse()?;
            if !(1..=16).contains(&iterations) {
                return Err("Newton threshold must be between 1 and 16".into());
            }
            iterations
        }
        None => 0,
    };
    run_mode(
        bench,
        true,
        newton_after > 0 && bench,
        Matrix::Block(newton_after),
    )
}

pub fn run(bench: bool, frozen: bool, compare: bool) -> Result<(), Box<dyn std::error::Error>> {
    run_mode(bench, frozen, compare, Matrix::Scalar)
}

pub fn run_packed(bench: bool) -> Result<(), Box<dyn std::error::Error>> {
    run_mode(bench, true, bench, Matrix::Packed)
}

pub fn run_packed_profile() -> Result<(), Box<dyn std::error::Error>> {
    run_mode(true, true, false, Matrix::Packed)
}

pub fn run_vector(bench: bool, compare: bool) -> Result<(), Box<dyn std::error::Error>> {
    run_mode(bench, true, compare, Matrix::Vector)
}

pub fn run_seeded(bench: bool) -> Result<(), Box<dyn std::error::Error>> {
    run_mode(bench, true, bench, Matrix::Seeded)
}

pub fn run_accelerated(bench: bool) -> Result<(), Box<dyn std::error::Error>> {
    run_mode(bench, true, bench, Matrix::Accelerated)
}

fn run_mode(
    bench: bool,
    frozen: bool,
    compare: bool,
    matrix: Matrix,
) -> Result<(), Box<dyn std::error::Error>> {
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
    let block = matches!(matrix, Matrix::Block(_));
    let (clock, rows) = if block {
        let (source, rest) = rows
            .split_at_checked(clock_fixture::WORDS)
            .ok_or("missing clock fixture")?;
        (
            Some(clock_fixture::Fixture::read(source.iter().copied())),
            rest,
        )
    } else {
        (None, rows)
    };
    let [slot, seconds, c2, a, b] = if block {
        [0.; 5]
    } else {
        rows[..5].try_into()?
    };
    let metadata = if block { 0 } else { 5 };
    let (mut event, rows) = if slot == -1. {
        (None, &rows[5..])
    } else {
        if !(0. ..H).contains(&seconds)
            || slot < 0.
            || slot != slot.floor()
            || rows.len() < metadata + 2 * TABLE
        {
            return Err("invalid C4 event".into());
        }
        let front =
            profile(&rows[metadata..metadata + TABLE], 1).map_err(|e| format!("front: {e:?}"))?;
        let tail = profile(&rows[metadata + TABLE..metadata + 2 * TABLE], 2)
            .map_err(|e| format!("tail: {e:?}"))?;
        (
            Some(Event {
                slot: slot as usize,
                seconds,
                c2,
                weights: [a, b],
                front,
                tail,
            }),
            &rows[metadata + 2 * TABLE..],
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
    if block && inputs.len() != BLOCK_STEPS {
        return Err("expected 128 frames at 48 kHz".into());
    }
    let blocks = (!matches!(matrix, Matrix::Scalar))
        .then(|| map.reduced.as_ref().expect("receiver map").pack_defects());
    let (control, variant) = match (matrix, blocks.as_ref()) {
        (Matrix::Packed, Some(blocks)) => (Candidate::Frozen, Candidate::Packed(blocks)),
        (Matrix::Seeded, Some(blocks)) => (Candidate::Packed(blocks), Candidate::Seeded(blocks)),
        (Matrix::Accelerated, Some(blocks)) => {
            (Candidate::Packed(blocks), Candidate::Accelerated(blocks))
        }
        (Matrix::Block(iterations), Some(blocks)) if iterations > 0 => (
            Candidate::Vector(blocks),
            Candidate::EarlyNewton(blocks, iterations),
        ),
        (Matrix::Vector | Matrix::Block(_), Some(blocks)) => {
            (Candidate::Packed(blocks), Candidate::Vector(blocks))
        }
        _ => (Candidate::Exact, Candidate::Frozen),
    };
    if bench {
        const PASSES: usize = 200;
        let passes = if block { 64 } else { PASSES };
        let mut times = [[0; PASSES]; 2];
        let mut stats = [[0.; 7]; 2];
        for i in 0..passes {
            for candidate in [if compare { i % 2 == 1 } else { frozen }, i % 2 == 0]
                .into_iter()
                .take(if compare { 2 } else { 1 })
            {
                let begin = Instant::now();
                stats[usize::from(candidate)] = black_box(render_driven(
                    black_box(initial),
                    latch,
                    &map,
                    &family,
                    collector,
                    &inputs,
                    event.as_mut(),
                    clock.as_ref(),
                    if candidate { variant } else { control },
                    |_, _| {},
                )?);
                times[usize::from(candidate)][i] = begin.elapsed().as_nanos();
            }
        }
        for group in times
            .iter_mut()
            .skip(usize::from(frozen && !compare))
            .take(if compare { 2 } else { 1 })
        {
            let group = &mut group[..passes];
            group.sort_unstable();
            println!(
                "{passes},{},{},{}",
                group[passes / 2],
                group[passes * 99 / 100],
                group[passes - 1]
            );
        }
        let label = match matrix {
            Matrix::Seeded => Some("SEEDS"),
            Matrix::Accelerated => Some("MIX"),
            _ => None,
        };
        if let Some(label) = label {
            for group in stats {
                println!("{label},{},{},{}", group[4], group[5], group[6]);
            }
        }
        super::profile::report_receiver();
    } else {
        let mut samples = Vec::new();
        let stats = render_driven(
            initial,
            latch,
            &map,
            &family,
            collector,
            &inputs,
            event.as_mut(),
            clock.as_ref(),
            if frozen { variant } else { control },
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
        if block {
            let event = event.as_ref().unwrap();
            for value in [
                event.slot as f64,
                event.seconds,
                event.c2,
                event.weights[0],
                event.weights[1],
            ] {
                out.write_all(&value.to_le_bytes())?;
            }
        }
        for value in stats.into_iter().take(4).chain(samples) {
            out.write_all(&value.to_le_bytes())?;
        }
        out.flush()?;
    }
    Ok(())
}
