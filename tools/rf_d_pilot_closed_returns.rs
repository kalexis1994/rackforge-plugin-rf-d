//! Close the pilot contour and audio ports at the same Radau stage times.
use crate::{
    contour_ports::{self, Returns, FILTER_NODES, FILTER_PORTS, VOLUME_NODES, VOLUME_PORTS},
    family::Family,
    graph, parameters,
    pilot_contours::{self as contours, Loaded, Ports, TIMER_NODES},
    pilot_trigger::{self as latch, Boundary, State, CORE, N, PORTS},
    reduced_lu::{maximum, Lu},
    voice, StepError,
};
use std::io::{BufWriter, Read, Write};

#[path = "../crates/rf-d-circuit/src/prepared_chain_charge.rs"]
mod chain;

const R59: f64 = 68_000.;
const R60: f64 = 680.;
const B: [[f64; 2]; 2] = graph::B;
const A: [[f64; 2]; 2] = [[5. / 12., -1. / 12.], [3. / 4., 1. / 4.]];
const SIZE: usize = 64;
const PAIR: usize = 2 * SIZE;
const LOAD: [usize; 2] = [32, 5];
const CV: usize = latch::pin(4) - N;
const TAIL: usize = latch::pin(55) - N;
const INTERFACE: usize = 6;
const fn local(k: usize) -> usize {
    if k < 62 {
        k
    } else {
        k + 4
    }
}

struct Audio {
    params: chain::Parameters,
    lu: Lu<PAIR>,
}

fn voltage(state: chain::State, node: usize) -> f64 {
    state.high[node] + state.low[node]
}

impl Audio {
    fn new(old: chain::State, family: &Family, phase: f64, h: f64) -> Result<Self, StepError> {
        let mut p = parameters();
        p.boundary.recovery.vca.loudness_v = 0.;
        let params = chain::Parameters::new(p)?;
        let stamp = chain::linearize_prevalidated::<true>(
            params,
            [0.; 5],
            old,
            chain::State::from_nodes([0.; chain::N]),
            h,
            old,
        )?;
        let bus = family
            .observe(voltage(old, chain::BUS), phase)
            .map_err(|_| StepError::InvalidInput)?;
        let mut g = stamp.dc_jacobian;
        g[LOAD[0]][LOAD[0]] += 1. / R59;
        g[LOAD[1]][LOAD[1]] += 1. / R60;
        g[chain::BUS][chain::BUS] += bus.bus_dbus;
        // The omitted phase derivative only preconditions the correction.
        // The stage residual below always reevaluates the H128 port.
        let lhs = std::array::from_fn(|r| {
            std::array::from_fn(|c| {
                let (i, j) = (r / SIZE, c / SIZE);
                let (row, column) = (local(r % SIZE), local(c % SIZE));
                B[i][j] * stamp.mass_over_h[row][column] + if i == j { g[row][column] } else { 0. }
            })
        });
        Ok(Self {
            params,
            lu: Lu::factor_contour(lhs)?,
        })
    }

    fn step(
        &self,
        old: chain::State,
        input: [[f64; 2]; 2],
        family: &Family,
        phase: f64,
        h: f64,
        mut delta: [chain::State; 2],
    ) -> Result<([chain::State; 2], f64, [chain::State; 2], usize), StepError> {
        for iteration in 1..=12 {
            let now = delta.map(|d| old.advanced(d.high).advanced(d.low));
            let bus = now.map(|x| voltage(x, chain::BUS));
            let f = bus.map(|x| family.frequency(x).map(|pair| pair.0));
            let f = [
                f[0].as_ref().map_err(|_| StepError::InvalidInput)?,
                f[1].as_ref().map_err(|_| StepError::InvalidInput)?,
            ];
            let stages = A.map(|row| (phase + h * (row[0] * f[0] + row[1] * f[1])).rem_euclid(1.));
            let mut p = [
                chain::linearize_prevalidated::<false>(
                    self.params,
                    [0.; 5],
                    old,
                    delta[0],
                    h,
                    now[0],
                )?,
                chain::linearize_prevalidated::<false>(
                    self.params,
                    [0.; 5],
                    old,
                    delta[1],
                    h,
                    now[1],
                )?,
            ];
            for i in 0..2 {
                for (j, resistance) in [R59, R60].into_iter().enumerate() {
                    let node = LOAD[j];
                    p[i].dc[node] +=
                        ((now[i].high[node] - input[i][j]) + now[i].low[node]) / resistance;
                }
                p[i].dc[chain::BUS] += family
                    .observe(bus[i], stages[i])
                    .map_err(|_| StepError::InvalidInput)?
                    .currents_a[2];
            }
            let residual = std::array::from_fn(|r| {
                let i = r / SIZE;
                let row = local(r % SIZE);
                p[i].dc[row] + B[i][0] * p[0].charge_over_h[row] + B[i][1] * p[1].charge_over_h[row]
            });
            let change = self.lu.solve(residual.map(|v| -v))?;
            if maximum(&residual) <= 2e-13 && maximum(&change) <= 2e-9 {
                return Ok((now, stages[1], delta, iteration));
            }
            for i in 0..2 {
                let d = std::array::from_fn(|k| match k {
                    0..=61 => change[i * SIZE + k],
                    66..=67 => change[i * SIZE + k - 4],
                    _ => 0.,
                });
                delta[i] = delta[i].advanced(d);
            }
        }
        Err(StepError::IterationBudget)
    }
}

struct Closure {
    audio: [chain::State; 2],
    contour: [Loaded; 2],
    phase: f64,
    delta: [chain::State; 2],
    residual: [f64; INTERFACE],
    cv: f64,
    audio_iterations: usize,
}

struct Step<'a> {
    model: &'a Audio,
    family: &'a Family,
    audio: chain::State,
    contour: Loaded,
    phase: f64,
    h: f64,
    previous: Boundary,
    change: [f64; N],
    ports: [Ports; 2],
}

impl Step<'_> {
    fn evaluate(&self, v: [f64; INTERFACE], seed: [chain::State; 2]) -> Result<Closure, StepError> {
        let mut ports = self.ports;
        for i in 0..2 {
            let [base, tail, cv] = [v[3 * i], v[3 * i + 1], v[3 * i + 2]];
            ports[i].volume[1] = cv;
            ports[i].volume[2] = base;
            ports[i].filter[1] = tail;
            ports[i].latch.volts[CV] = cv;
            ports[i].latch.volts[TAIL] = tail;
        }
        let contour = contours::step(self.contour, ports, self.h, self.previous, self.change)?;
        let drive = contour.map(|s| [s.returns.volume[2], s.returns.filter[2]]);
        let (audio, phase, delta, audio_iterations) =
            self.model
                .step(self.audio, drive, self.family, self.phase, self.h, seed)?;
        let mut residual = [0.; INTERFACE];
        for i in 0..2 {
            residual[3 * i] = v[3 * i] - voltage(audio[i], LOAD[0]);
            residual[3 * i + 1] = v[3 * i + 1] - voltage(audio[i], LOAD[1]);
            residual[3 * i + 2] = contour_ports::cv_return_residual(
                v[3 * i + 2],
                drive[i][0],
                contour[i].latch.0[latch::pin(27)],
            )?;
        }
        Ok(Closure {
            audio,
            contour,
            phase,
            delta,
            residual,
            cv: v[5],
            audio_iterations,
        })
    }

    fn solve(
        &self,
        mut v: [f64; INTERFACE],
        seed: [chain::State; 2],
    ) -> Result<(Closure, usize), StepError> {
        let mut result = self.evaluate(v, seed)?;
        for iteration in 1..=6 {
            if maximum(&result.residual) <= 1e-10 {
                return Ok((result, iteration));
            }
            // Differentiate the complete two-stage reaction. Both perturbations
            // reuse the same accepted capacitor history and VCO phase.
            let mut j = [[0.; INTERFACE]; INTERFACE];
            for column in 0..INTERFACE {
                let mut x = v;
                let dv = 1e-6;
                x[column] += dv;
                let probe = self.evaluate(x, result.delta)?;
                for (row, slopes) in j.iter_mut().enumerate() {
                    slopes[column] =
                        (probe.residual[row] - result.residual[row]) / (x[column] - v[column]);
                }
            }
            let direction = Lu::factor(j)?.solve(result.residual.map(|r| -r))?;
            let mut accepted = None;
            for half in 0..12 {
                let x = std::array::from_fn(|i| v[i] + direction[i] * 0.5_f64.powi(half));
                if let Ok(trial) = self.evaluate(x, result.delta) {
                    if maximum(&trial.residual) < maximum(&result.residual) {
                        accepted = Some((x, trial));
                        break;
                    }
                }
            }
            (v, result) = accepted.ok_or(StepError::NoDecrease)?;
        }
        Err(StepError::IterationBudget)
    }
}

pub fn run(
    path: &str,
    key: f64,
    frames: usize,
    stride: usize,
) -> Result<(), Box<dyn std::error::Error>> {
    assert!(stride.is_power_of_two() && stride <= 256);
    let mut bytes = Vec::new();
    std::fs::File::open(path)?.read_to_end(&mut bytes)?;
    let values = bytes
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()))
        .collect::<Vec<_>>();
    assert_eq!(values.len(), 2 * graph::N + 1);
    let x = |k| values[k] + values[k + graph::N];
    let mut phase = values[2 * graph::N];
    let mut audio = chain::State {
        high: std::array::from_fn(|k| values[graph::chain_index(k)]),
        low: std::array::from_fn(|k| values[graph::N + graph::chain_index(k)]),
    };
    let mut contour = Loaded {
        timers: TIMER_NODES.map(x),
        latch: State(CORE.map(x)),
        returns: Returns {
            volume: VOLUME_NODES.map(x),
            filter: FILTER_NODES.map(x),
        },
        q22_base: x(29),
    };
    let mut previous = Boundary {
        volts: PORTS.map(x),
        key,
        short: false,
    };
    let mut change = [0.; N];
    // The two shared CV terminals still belong to the keyboard source.
    // Their error under a constant anchor is checked against the full trajectory.
    let ports = [Ports {
        latch: previous,
        volume: VOLUME_PORTS.map(x),
        filter: FILTER_PORTS.map(x),
    }; 2];
    let family = Family::prepare(-1.6).map_err(|_| "H128 prepare")?;
    let h = stride as f64 / (48_000. * 512.);
    let model = Audio::new(audio, &family, phase, h).map_err(|e| format!("audio factor: {e:?}"))?;
    let mut out = BufWriter::new(std::io::stdout().lock());
    let mut peak_ns = 0;
    let mut frame_ns = 0;
    let mut max_outer = 0;
    let mut max_audio = 0;
    let mut max_residual: f64 = 0.;
    for k in 0..frames * 512 / stride {
        let start = std::time::Instant::now();
        let [base, tail] = LOAD.map(|k| voltage(audio, k));
        let cv = previous.volts[CV];
        let guess = [base, tail, cv, base, tail, cv];
        let zero = chain::State::from_nodes([0.; chain::N]);
        let step = Step {
            model: &model,
            family: &family,
            audio,
            contour,
            phase,
            h,
            previous,
            change,
            ports,
        };
        let (result, iterations) = step
            .solve(guess, [zero; 2])
            .map_err(|e| format!("loaded ports at tick {}: {e:?}", 8 * k * stride))?;
        frame_ns += start.elapsed().as_nanos();
        if (k + 1) % (512 / stride) == 0 {
            peak_ns = peak_ns.max(frame_ns);
            frame_ns = 0;
        }
        max_outer = max_outer.max(iterations);
        max_audio = max_audio.max(result.audio_iterations);
        max_residual = max_residual.max(maximum(&result.residual));
        for i in 0..2 {
            let a = result.audio[i];
            let c = result.contour[i];
            let [base, tail] = LOAD.map(|k| voltage(a, k));
            let [r59, r60] = c.returns.currents(base, tail);
            let v = [
                voltage(a, 61),
                r59,
                r60,
                c.timers[0],
                c.timers[1],
                c.returns.volume[2],
                c.returns.filter[2],
                base,
                tail,
                c.latch.0[latch::pin(26)],
                c.latch.0[latch::pin(28)],
            ];
            for x in v {
                out.write_all(&x.to_le_bytes())?;
            }
        }
        change = std::array::from_fn(|i| result.contour[1].latch.0[i] - contour.latch.0[i]);
        contour = result.contour[1];
        audio = result.audio[1];
        phase = result.phase;
        previous.volts[TAIL] = voltage(audio, LOAD[1]);
        previous.volts[CV] = result.cv;
    }
    eprintln!("PORTS,{peak_ns},{max_outer},{max_audio},{max_residual:.17e}");
    out.flush()?;
    Ok(())
}
