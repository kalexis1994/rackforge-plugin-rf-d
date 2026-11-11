//! Exercise the coupled Q15 endpoint and measure the native cost.
use crate::{
    fast_r59,
    latch_charge::terminal,
    plant,
    probe::ALLOCS,
    q15,
    q15_r59::{self, Frame, State},
};
use std::{
    hint::black_box,
    io::{Read, Write},
    sync::atomic::Ordering::Relaxed,
    time::Instant,
};

const BLOCK: usize = 256;

fn render(
    mut state: State,
    input: &[[f64; 6]],
    offset: usize,
    mut observe: impl FnMut(State, Frame, [f64; 6]) -> Result<(), Box<dyn std::error::Error>>,
    #[cfg(pilot_r59_profile)] profile: &mut fast_r59::Profile,
) -> Result<State, Box<dyn std::error::Error>> {
    for (i, &drive) in input.iter().enumerate() {
        let tick = i + offset;
        let (next, frame) = q15_r59::advance(
            state,
            drive,
            tick % BLOCK == 0,
            #[cfg(pilot_r59_profile)]
            profile,
        )
            .map_err(|error| format!("Q15 at tick {tick}: {error:?}"))?;
        observe(next, frame, drive)?;
        state = next;
    }
    Ok(state)
}

pub(crate) fn initial_state(values: &[f64; 149]) -> Result<State, Box<dyn std::error::Error>> {
    let audio = plant::State::from_nodal(
        &values[..68].try_into()?,
        &values[68..136].try_into()?,
        0.,
        plant::Drive::default(),
    )
    .map_err(|e| format!("initial audio: {e:?}"))?;
    let [q3, q2, collector, loudness, reset, base, q15_collector]: [f64; 7] =
        values[136..143].try_into()?;
    let vca_base = values[32] + values[100];
    let [_, c2, _, q25_base, q25_collector, cr8_anode]: [f64; 6] = values[143..149].try_into()?;
    let (cr6, _) =
        crate::contour_ports::germanium(reset - base).map_err(|e| format!("initial CR6: {e:?}"))?;
    let q15_v = [base, q15_collector];
    let (q15_current_a, _) = q15::conduction(
        q15_v,
        q15::Drive {
            c2,
            vca_base,
            q25_base,
            q25_collector,
            cr8_anode,
        },
        cr6,
        0.,
    )
    .map_err(|e| format!("initial Q15: {e:?}"))?;
    assert!(q15_current_a.iter().all(|i| i.abs() <= 2e-15));
    Ok(State {
        audio: fast_r59::State {
            audio,
            volume: [q3, q2, loudness, collector, reset],
            vca_base,
            gradient: None,
            #[cfg(pilot_r59_reuse_cr6)]
            cr6: None,
            #[cfg(pilot_r59_predict_base_drift)]
            base_drift_v: 0.,
            #[cfg(pilot_r59_junction_predictor)]
            junction_direction: None,
            follower: None,
        },
        q15_v,
        previous_charge_increment_c: None,
        #[cfg(pilot_r59_predict_q15_charge)]
        charge_mass_f: None,
    })
}

pub fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mode = std::env::args().nth(1).ok_or("64, 128 or bench")?;
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    assert_eq!(raw.len() % 8, 0);
    let values: Vec<_> = raw
        .chunks_exact(8)
        .map(|b| f64::from_le_bytes(b.try_into().unwrap()))
        .collect();
    assert_eq!(values.len(), 149 + 2 * BLOCK * 6);
    let initial = initial_state(values[..149].try_into()?)?;
    let input: Vec<[f64; 6]> = values[149..]
        .chunks_exact(6)
        .map(|b| b.try_into().unwrap())
        .collect();
    let mut out = std::io::BufWriter::new(std::io::stdout().lock());
    #[cfg(pilot_r59_profile)]
    let mut profile = fast_r59::Profile::default();
    if mode == "bench" {
        let warm = render(
            initial,
            &input[..BLOCK],
            0,
            |_, _, _| Ok(()),
            #[cfg(pilot_r59_profile)]
            &mut profile,
        )?;
        #[cfg(pilot_r59_profile)]
        let mut profile = fast_r59::Profile::default();
        let mut elapsed = [0; 64];
        let mut allocations = 0;
        for time in &mut elapsed {
            let before = ALLOCS.load(Relaxed);
            let start = Instant::now();
            black_box(render(
                black_box(warm),
                &input[BLOCK..],
                BLOCK,
                |_, frame, _| {
                    black_box(frame);
                    Ok(())
                },
                #[cfg(pilot_r59_profile)]
                &mut profile,
            )?);
            *time = start.elapsed().as_nanos();
            allocations += ALLOCS.load(Relaxed) - before;
        }
        elapsed.sort_unstable();
        writeln!(out, "64,{},{},{}", elapsed[32], elapsed[63], allocations)?;
        #[cfg(pilot_r59_profile)]
        crate::probe::write_profile(&mut out, &profile)?;
        return Ok(());
    }
    let ticks = mode.parse::<usize>()? * 2;
    assert!(matches!(ticks, 128 | 256));
    let mut state = initial;
    for (block, chunk) in input.chunks(ticks).enumerate() {
        let mut write_frame = |next: State, frame: Frame, _| {
            let (charge, _) = terminal(initial.q15_v.map(|v| (v, 0.)), next.q15_v.map(|v| (v, 0.)))
                .map_err(|e| format!("Q15 charge: {e:?}"))?;
            let audio = frame.audio;
            let p = audio.ports;
            let [q3, q2, loudness, collector, reset] = audio.volume;
            for value in [
                p.j7_v,
                p.bus_v,
                p.base_v - p.bus_v,
                p.panel_a,
                p.returns_a[0],
                p.returns_a[1],
                p.loads_v[0],
                p.loads_v[1],
                q3,
                q2,
                collector,
                loudness,
                reset,
                next.q15_v[0],
                next.q15_v[1],
                audio.reset_port.current_a,
                charge[0],
                charge[1],
                frame.charge_increment_c[0],
                frame.charge_increment_c[1],
                frame.residual_a[0],
                frame.residual_a[1],
                frame.trials as f64,
                audio.mismatch_a,
                audio.mismatch_v,
                frame.receiver_iterations as f64,
            ] {
                out.write_all(&value.to_le_bytes())?;
            }
            Ok(())
        };
        state = render(
            state,
            chunk,
            block * ticks,
            &mut write_frame,
            #[cfg(pilot_r59_profile)]
            &mut profile,
        )?;
    }
    for charge in state.audio.audio.capacitor_charge_offsets_c() {
        out.write_all(&charge.to_le_bytes())?;
    }
    Ok(())
}
