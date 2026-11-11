//! Monolithic Radau reference of audio, follower and Q15 charge.
use super::{
    latch_charge_driver, linear, maximum, original_volume, receiver, Audio, StepError, AUDIO, B,
    R59,
};
use std::io::Write;

const BOARD: [usize; 7] = [0, 1, 2, 3, 4, 27, 28];
const N: usize = AUDIO + BOARD.len();
const PAIR: usize = 2 * N;

#[derive(Clone, Copy)]
struct State {
    audio: Audio,
    board: [f64; 7],
}

fn q15_charge(old: &[f64; 7], now: &[f64; 7]) -> Result<([f64; 2], [[f64; 2]; 2]), StepError> {
    latch_charge_driver::terminal([(old[5], 0.), (old[6], 0.)], [(now[5], 0.), (now[6], 0.)])
}

fn board_stamp<const FULL: bool>(
    board: [f64; 7],
    [_, c2, _, q25_base, q25_collector, cr8_anode]: [f64; 6],
    [vca_high, vca_low]: [f64; 2],
) -> Result<original_volume::Stamp<FULL>, StepError> {
    let mut nodes = [0.; original_volume::N];
    nodes[6] = 9.3;
    nodes[7] = 9.3;
    for (node, voltage) in BOARD.into_iter().zip(board) {
        nodes[node] = voltage;
    }
    nodes[5] = c2;
    nodes[24] = cr8_anode;
    nodes[25] = q25_base;
    nodes[26] = q25_collector;
    nodes[29] = vca_high;
    let mut low = [0.; original_volume::N];
    low[29] = vca_low;
    original_volume::linearize::<FULL>(nodes, low, 0., true, false)
}

fn stamp(
    old: State,
    trial: [State; 2],
    input: [[f64; 6]; 2],
    h: f64,
) -> Result<([State; 2], [f64; PAIR], [[f64; PAIR]; PAIR]), StepError> {
    let stages = [0, 1].map(|i| {
        let [signal, _, filter, _, _, _] = input[i];
        let board = trial[i].board;
        let audio = receiver::stage(
            old.audio,
            trial[i].audio,
            [signal, board[3], filter],
            h,
            true,
        )?;
        let stamp = board_stamp::<true>(
            board,
            input[i],
            [audio.candidate.high[32], audio.candidate.low[32]],
        )?;
        let (charge, mass) = q15_charge(&old.board, &board)?;
        Ok::<_, StepError>((audio, stamp, charge, mass))
    });
    let [first, last] = stages;
    let stages = [first?, last?];
    let residual = std::array::from_fn(|k| {
        let (i, row) = (k / N, k % N);
        let stage = &stages[i];
        if row < AUDIO {
            stage.0.dc[row]
                + B[i][0] * stages[0].0.charge_over_h[row]
                + B[i][1] * stages[1].0.charge_over_h[row]
        } else {
            let r = row - AUDIO;
            let dc = stage.1.dc[BOARD[r]];
            if r >= 5 {
                dc + (B[i][0] * stages[0].2[r - 5] + B[i][1] * stages[1].2[r - 5]) / h
            } else {
                dc
            }
        }
    });
    let jacobian = std::array::from_fn(|k| {
        let (i, row) = (k / N, k % N);
        std::array::from_fn(|l| {
            let (j, col) = (l / N, l % N);
            if row < AUDIO && col < AUDIO {
                B[i][j] * stages[j].0.mass_over_h[row][col]
                    + if i == j {
                        stages[i].0.dc_jacobian[row][col]
                    } else {
                        0.
                    }
            } else if row >= AUDIO && col >= AUDIO {
                let (r, c) = (row - AUDIO, col - AUDIO);
                let dc = if i == j {
                    stages[i].1.jacobian[BOARD[r]][BOARD[c]]
                } else {
                    0.
                };
                if r >= 5 && c >= 5 {
                    dc + B[i][j] * stages[j].3[r - 5][c - 5] / h
                } else {
                    dc
                }
            } else if i == j && ((row == 32 && col == AUDIO + 3) || (row == AUDIO + 3 && col == 32))
            {
                -1. / R59
            } else {
                0.
            }
        })
    });
    let states = std::array::from_fn(|i| State {
        audio: stages[i].0.candidate,
        board: trial[i].board,
    });
    Ok((states, residual, jacobian))
}

fn step(old: State, input: [[f64; 6]; 2], h: f64) -> Result<State, StepError> {
    let mut trial = [State {
        audio: Audio::from_nodes([0.; AUDIO]),
        board: old.board,
    }; 2];
    let mut evaluation = stamp(old, trial, input, h)?;
    for _ in 0..24 {
        let (states, r, j) = evaluation;
        let d = linear::solve_linear_sparse(j, r.map(|v| -v))?;
        let error = maximum(&r);
        if error <= 1e-13 && maximum(&d) <= 2e-9 {
            return Ok(states[1]);
        }
        let mut accepted = None;
        for power in 0..24 {
            let scale = 0.5_f64.powi(power);
            let proposal = std::array::from_fn(|i| State {
                audio: trial[i]
                    .audio
                    .advanced(std::array::from_fn(|k| scale * d[i * N + k])),
                board: std::array::from_fn(|k| trial[i].board[k] + scale * d[i * N + AUDIO + k]),
            });
            if let Ok(candidate) = stamp(old, proposal, input, h) {
                if maximum(&candidate.1) < error.max(1e-13) {
                    accepted = Some((proposal, candidate));
                    break;
                }
            }
        }
        (trial, evaluation) = accepted.ok_or(StepError::NoDecrease)?;
    }
    Err(StepError::IterationBudget)
}

pub(super) fn render(
    values: &[f64],
    rate: f64,
    out: &mut impl Write,
) -> Result<(), Box<dyn std::error::Error>> {
    assert!(values.len() >= 149 && (values.len() - 149) % 12 == 0);
    let initial = State {
        audio: Audio {
            high: values[..68].try_into()?,
            low: values[68..136].try_into()?,
        },
        board: values[136..143].try_into()?,
    };
    let mut state = initial;
    for (tick, row) in values[149..].chunks_exact(12).enumerate() {
        state = step(
            state,
            [row[..6].try_into()?, row[6..].try_into()?],
            1. / rate,
        )
        .map_err(|error| format!("coupled Q15 step {tick}: {error:?}"))?;
        let v = |node| state.audio.high[node] + state.audio.low[node];
        let cr6 =
            1e-8 * ((state.board[4] - state.board[5]) / (1.5 * latch_charge_driver::VT)).exp_m1();
        let (charge, _) = q15_charge(&initial.board, &state.board)
            .map_err(|error| format!("Q15 charge {tick}: {error:?}"))?;
        for value in [
            v(61),
            v(66),
            v(6) - v(66),
            (v(66) - 0.5 * row[6]) / 39_250.,
            (state.board[3] - v(32)) / R59,
            (v(5) - row[8]) / 680.,
            v(32),
            v(5),
        ]
        .into_iter()
        .chain(state.board)
        .chain([cr6])
        .chain(charge)
        {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    Ok(())
}

pub(super) fn audit(
    values: &[f64],
    out: &mut impl Write,
) -> Result<(), Box<dyn std::error::Error>> {
    assert!(values.len() >= 149 && (values.len() - 149) % 16 == 0);
    let mut old: [f64; 7] = values[136..143].try_into()?;
    let mut older: Option<[f64; 2]> = None;
    for (tick, row) in values[149..].chunks_exact(16).enumerate() {
        let board = row[7..14].try_into()?;
        let stamp = board_stamp::<false>(board, row[..6].try_into()?, [row[6], 0.])
            .map_err(|error| format!("board stamp {tick}: {error:?}"))?;
        let (delta, _) =
            q15_charge(&old, &board).map_err(|error| format!("Q15 charge {tick}: {error:?}"))?;
        let dynamic = match older {
            Some(previous) => std::array::from_fn(|i| (3. * delta[i] - previous[i]) * 48_000.),
            None => delta.map(|value| value * 96_000.),
        };
        let follower = maximum(&stamp.dc[..5]);
        for value in [
            follower,
            stamp.dc[27] + dynamic[0],
            stamp.dc[28] + dynamic[1],
            delta[0] - row[14],
            delta[1] - row[15],
        ] {
            out.write_all(&value.to_le_bytes())?;
        }
        older = Some(delta);
        old = board;
    }
    Ok(())
}
