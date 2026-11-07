pub use rf_d_circuit::{junction_charge, StepError};
#[path = "FAMILY_KERNEL_PATH"] mod family;
#[path = "COUPLED_PATH"] mod voice;
#[path = "GRAPH_PATH"] mod graph;
#[path = "DENSE_PATH"] mod dense;
#[path = "SOLVER_PATH"] mod solver;
#[path = "INCIDENCE_PATH"] mod incidence;
#[path = "PATCH_PATH"] mod patch;

use std::{error::Error, fs, io::{self, BufRead}, time::{Duration, Instant}};
use family::Family;
use voice::{Accepted, Controls, Parameters, State, B, BASE, BUS, J7, N};

fn parameters() -> rf_d_circuit::chain_charge::Parameters {
    let (circuit, conversion, headphone) = patch::lab_parameters();
    rf_d_circuit::chain_charge::Parameters {
        circuit, conversion, headphone, boundary: patch::controlled_boundary(0, true),
        mixer: rf_d_circuit::mixer_on::OnMixer::new([false; 5], [0.5; 4]).unwrap(),
    }
}

fn ports() -> Result<(), Box<dyn Error>> {
    for line in io::stdin().lock().lines() {
        let line = line?;
        let values: Vec<f64> = line.split_whitespace().map(str::parse).collect::<Result<_, _>>()?;
        let [cv, bus, phase] = values[..] else { return Err("CV BUS phase expected".into()); };
        if let Ok(p) = Family::prepare(cv).and_then(|f| f.observe(bus, phase)) {
            let data = [
                p.frequency_hz, p.frequency_dbus, p.saw_v, p.saw_dphase, p.currents_a[0],
                p.currents_a[1], p.currents_a[2], p.bus_dbus, p.bus_dphase, p.dissipated_w,
            ];
            print!("PORT");
            for value in data { print!(",{value:.17e}"); }
            println!();
        } else {
            println!("REJECT");
        }
    }
    Ok(())
}

fn value(s: State, k: usize) -> f64 { s.high[k] + s.low[k] }

fn charge_row(s: State, h: f64) -> f64 {
    1e-5 * ((s.high[BUS] - s.high[BASE]) + (s.low[BUS] - s.low[BASE])) / h
}

fn dense_state(s: State) -> dense::State {
    dense::State { high: s.high, low: s.low, optional: s.optional }
}

fn audit(
    model: &Family, p: Parameters, old: State, phase: f64, controls: Controls, h: f64, q: &Accepted,
) -> Result<[f64; 5], String> {
    let original = dense::Parameters::new(parameters()).map_err(|e| format!("{e:?}"))?;
    let old_dense = dense_state(old);
    let control = dense::Controls { key: controls.key, short: controls.short, optional: controls.optional };
    let mut current_error = 0_f64;
    let mut charge_error = 0_f64;
    let mut c27_error = 0_f64;
    let mut derivative_error = 0_f64;
    let mut panel_residual = 0_f64;
    for j in 0..2 {
        let saved = &q.stages.chain[j];
        let open = graph::parts::<true>(p, old, q.delta[j], controls, h, p.time)
            .map_err(|e| format!("{e:?}"))?;
        let reference = dense::parts(original, old_dense, dense_state(q.delta[j]), control, h, p.time)
            .map_err(|e| format!("{e:?}"))?;
        let bus = value(saved.now, BUS);
        let saw = q.stages.ports[j].saw_v;
        let wiper = (saw / 12500. + bus / 33000.) / (2. / 12500. + 1. / 33000.);
        let panel = (bus - wiper) / 33000.;
        for k in 0..N {
            assert_eq!(saved.dq[k].to_bits(), open.dq[k].to_bits());
            let other = reference.dc[k] + if k == BUS { panel } else { 0. };
            current_error = current_error.max((saved.dc[k] - other).abs());
            charge_error = charge_error.max((saved.dq[k] - reference.dq[k]).abs());
        }
        c27_error = c27_error.max((saved.dq[BUS] - charge_row(q.delta[j], h)).abs());
        panel_residual = panel_residual.max((q.stages.ports[j].currents_a[2] - panel).abs());

        let epsilon = 1e-5;
        let at = |change| {
            let mut d = q.delta;
            d[j] = d[j].advanced(std::array::from_fn(|k| if k == BUS { change } else { 0. }));
            voice::stages::<false>(model, p, old, phase, d, controls, h).map_err(|e| format!("{e:?}"))
        };
        let left = at(-epsilon)?;
        let right = at(epsilon)?;
        let get = |s: &graph::Parts| s.tangent.entries(BUS)
            .find_map(|(k, g, m)| (k == BUS).then_some((g, m))).unwrap();
        let (g, m) = get(saved);
        let (g0, m0) = get(&open);
        for (i, row) in B.iter().enumerate() {
            let finite = (right.ports[i].currents_a[2] - left.ports[i].currents_a[2]) / (2. * epsilon);
            let jacobian = if i == j { g - g0 } else { 0. } + row[j] * (m - m0);
            let err = (finite - jacobian).abs();
            derivative_error = derivative_error.max(err / (2e-11 + 2e-5 * finite.abs()));
        }
    }
    Ok([current_error, charge_error, c27_error, derivative_error, panel_residual])
}

fn dump(frame: usize, phase: f64, state: State) {
    let loads = graph::currents(state);
    print!("GRID,{frame},{phase:.17e},{:.17e},{:.17e}", loads[0], loads[1]);
    for part in state.high.into_iter().chain(state.low) {
        print!(",{:016x}", part.to_bits());
    }
    println!();
}

fn branch(path: &str, which: &str, subdivisions: usize) -> Result<(), Box<dyn Error>> {
    if !matches!(which, "negative" | "positive") || !matches!(subdivisions, 32 | 64 | 128 | 256 | 512) {
        return Err("branch/subdivisions outside this bench".into());
    }
    let bytes = fs::read(path)?;
    assert_eq!(bytes.len(), 2 * N * 8);
    let read = |k: usize| f64::from_le_bytes(bytes[8 * k..8 * k + 8].try_into().unwrap());
    let mut state = State {
        high: std::array::from_fn(read), low: std::array::from_fn(|k| read(N + k)), optional: false,
    };
    let mut phase = if which == "positive" { 0. } else { 0.37 };
    let family = Family::prepare(-1.6).unwrap();
    let mut workspace = solver::Workspace::new();
    let mut p = Parameters::new(parameters()).map_err(|e| format!("{e:?}"))?;
    let h = 1. / (48000 * subdivisions) as f64;
    let (mut elapsed, mut max_residual, mut max_correction) = (Duration::ZERO, 0_f64, 0_f64);
    let mut bus = [value(state, BUS); 2];
    let mut iterations = 0;
    let mut worst_audit = [0_f64; 5];
    dump(0, phase, state);
    let mut retries = 0;
    let mut deepest = 0;
    const UNITS: usize = 8;
    for frame in 0..128 {
        let key = if which == "negative" && (16..96).contains(&frame) { 10. } else { 0. };
        let controls = Controls { key, optional: false, short: false };
        for sub in 0..subdivisions {
            let mut completed = 0;
            let mut width = UNITS;
            while completed < UNITS {
                let tick = (frame * subdivisions + sub) * UNITS + completed;
                p.time = tick as f64 * (h / UNITS as f64);
                let step = h * width as f64 / UNITS as f64;
                let timer = Instant::now();
                let q = voice::radau(&mut workspace, &family, p, state, phase, controls, step, 80);
                elapsed += timer.elapsed();
                let q = match q {
                    Ok(q) => q,
                    Err(StepError::NoDecrease | StepError::IterationBudget) if width > 1 => {
                        width /= 2;
                        retries += 1;
                        deepest = deepest.max(UNITS.ilog2() - width.ilog2());
                        continue;
                    }
                    Err(e) => return Err(format!("branch={which} frame={frame} sub={sub} width={width}: {e:?}").into()),
                };
                if sub == 0 && completed == 0 && [0, 15, 16, 48, 95, 96, 127].contains(&frame) {
                    for (maximum, measured) in worst_audit.iter_mut().zip(
                        audit(&family, p, state, phase, controls, step, &q)?)
                    {
                        *maximum = maximum.max(measured);
                    }
                }
                for s in &q.stages.chain {
                    bus[0] = bus[0].min(value(s.now, BUS));
                    bus[1] = bus[1].max(value(s.now, BUS));
                }
                state = q.stages.chain[1].now;
                phase = q.stages.phase[1];
                iterations += q.iterations;
                max_residual = max_residual.max(q.residual_a);
                max_correction = max_correction.max(q.correction_v);
                completed += width;
            }
        }
        dump(frame + 1, phase, state);
    }
    let [current, charge, c27, tangent, panel] = worst_audit;
    println!("END,{subdivisions},{iterations},{:.17e},{max_residual:.17e},{max_correction:.17e},\
        {:.17e},{:.17e},{:.17e},{current:.17e},{charge:.17e},{c27:.17e},{tangent:.17e},{panel:.17e},{retries},{deepest}",
        elapsed.as_secs_f64(), bus[0], bus[1], value(state, J7));
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("ports") => ports(),
        Some("branch") if args.len() == 5 => branch(&args[2], &args[3], args[4].parse()?),
        _ => Err("ports | branch STATE CASE SUBDIVISIONS".into()),
    }
}
