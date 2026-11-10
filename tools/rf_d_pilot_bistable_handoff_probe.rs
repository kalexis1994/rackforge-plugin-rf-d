//! Native C4-to-Radau handoff with externally supplied stage boundaries.
use crate::{
    bistable::{self, Drive, State},
    clock::PERIOD_S,
    handoff::{Knot, Profile, POINTS},
    StepError,
};
use std::{hint::black_box, io::Write, time::Instant};

fn profile(values: &mut impl Iterator<Item = f64>, intervals: u8) -> Result<Profile, StepError> {
    Profile::new(
        std::array::from_fn(|_| Knot {
            seconds: values.next().unwrap(),
            coefficients: std::array::from_fn(|_| std::array::from_fn(|_| values.next().unwrap())),
        }),
        intervals,
    )
}

fn drive([c2, vca_base, x17, x24, x14]: [f64; 5]) -> Drive {
    Drive {
        c2,
        vca_base,
        x17,
        x24,
        x14,
        x6: 0.,
        x9: 0.,
    }
}

fn advance(
    event: [f64; 7],
    front: &Profile,
    tail: &Profile,
    drives: &[[Drive; 2]],
    mut emit: impl FnMut(State, Drive),
) -> Result<State, StepError> {
    let [slot, seconds, c2, _, _, a, b] = event;
    let slot = slot as usize;
    let (extra, rest) = drives
        .get(slot + 1..)
        .and_then(|span| span.split_first())
        .ok_or(StepError::InvalidInput)?;
    let start = Drive {
        c2,
        ..drives[slot][1]
    };
    let weights = [a, b];
    let edge = front.at(PERIOD_S - seconds, weights, start)?;
    emit(edge, start);
    let [u1, u2] = *extra;
    let stage = tail.at((1. + 1. / 3.) * PERIOD_S - seconds, weights, u1)?;
    let mut state = tail.at(2. * PERIOD_S - seconds, weights, u2)?;
    emit(stage, u1);
    emit(state, u2);
    for &drive in rest {
        let [stage, end] = bistable::loads_step(state, drive, Some(PERIOD_S))?;
        emit(stage, drive[0]);
        emit(end, drive[1]);
        state = end;
    }
    Ok(state)
}

pub fn run(
    mut values: impl ExactSizeIterator<Item = f64>,
    clock: impl Fn() -> Option<[f64; 7]>,
    bench: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    const TABLE: usize = POINTS * (1 + 15 * 5);
    let Some(event) = clock() else {
        if values.len() != 0 || bench {
            return Err("C4 event required for positive handoff".into());
        }
        return Ok(());
    };
    if values.len() < 2 * TABLE || (values.len() - 2 * TABLE) % 10 != 0 {
        return Err("invalid native handoff fixture length".into());
    }
    let front = profile(&mut values, 1).map_err(|e| format!("event curve: {e:?}"))?;
    let tail = profile(&mut values, 2).map_err(|e| format!("delayed curve: {e:?}"))?;
    let drives: Vec<_> = (0..values.len() / 10)
        .map(|_| std::array::from_fn(|_| drive(std::array::from_fn(|_| values.next().unwrap()))))
        .collect();
    if bench {
        const PASSES: usize = 2_000;
        let mut times = [0; PASSES];
        for elapsed in &mut times {
            let begin = Instant::now();
            let event = black_box(clock()).ok_or("unstable C4 event")?;
            black_box(
                advance(event, &front, &tail, black_box(&drives), |_, _| {})
                    .map_err(|e| format!("handoff: {e:?}"))?,
            );
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
        let mut rows = Vec::new();
        advance(event, &front, &tail, &drives, |state, drive| {
            rows.extend(bistable::observations(state, drive));
        })
        .map_err(|e| format!("handoff: {e:?}"))?;
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        for value in event.into_iter().chain(rows) {
            out.write_all(&value.to_le_bytes())?;
        }
        out.flush()?;
    }
    Ok(())
}
