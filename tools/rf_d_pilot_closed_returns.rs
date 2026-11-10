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
use std::{
    cell::{Cell, RefCell},
    io::{BufWriter, Read, Write},
};

#[path = "../crates/rf-d-circuit/src/prepared_chain_charge.rs"]
mod chain;
#[path = "rf_d_pilot_contour_clock.rs"]
mod clock;
#[path = "rf_d_pilot_reduced_audio.rs"]
mod reduced_audio;

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
type Failure = (&'static str, StepError);
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
    reduced: Option<reduced_audio::Map>,
    reuse: bool,
    warm: bool,
    tangent: RefCell<Option<Lu<INTERFACE>>>,
    builds: Cell<usize>,
    reused: Cell<usize>,
    diagnostic_recovery: bool,
    fallback_calls: Cell<usize>,
    verify_reduced: bool,
    checked_proposals: Cell<usize>,
}

fn voltage(state: chain::State, node: usize) -> f64 {
    state.high[node] + state.low[node]
}

impl Audio {
    fn new(
        old: chain::State,
        family: &Family,
        phase: f64,
        h: f64,
        wires: [f64; 2],
        reduce_audio: bool,
        reuse: bool,
        warm: bool,
        diagnostic_recovery: bool,
        verify_reduced: bool,
    ) -> Result<Self, StepError> {
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
        let lu = Lu::factor_contour(lhs)?;
        let reduced = if reduce_audio {
            Some(reduced_audio::Map::new(
                old,
                wires,
                [bus.currents_a[2], bus.bus_dbus],
                params,
                &stamp,
                &lu,
                h,
            )?)
        } else {
            None
        };
        Ok(Self {
            params,
            lu,
            reduced,
            reuse,
            warm,
            tangent: RefCell::new(None),
            builds: Cell::new(0),
            reused: Cell::new(0),
            diagnostic_recovery,
            fallback_calls: Cell::new(0),
            verify_reduced,
            checked_proposals: Cell::new(0),
        })
    }

    fn residual(
        &self,
        old: chain::State,
        input: [[f64; 2]; 2],
        family: &Family,
        phase: f64,
        h: f64,
        delta: [chain::State; 2],
    ) -> Result<([chain::State; 2], f64, [f64; PAIR]), StepError> {
        let now = delta.map(|d| old.advanced(d.high).advanced(d.low));
        let bus = now.map(|x| voltage(x, chain::BUS));
        let f = bus.map(|x| family.frequency(x).map(|pair| pair.0));
        let f = [
            f[0].as_ref().map_err(|_| StepError::InvalidInput)?,
            f[1].as_ref().map_err(|_| StepError::InvalidInput)?,
        ];
        let stages = A.map(|row| (phase + h * (row[0] * f[0] + row[1] * f[1])).rem_euclid(1.));
        let mut p = [
            chain::linearize_prevalidated::<false>(self.params, [0.; 5], old, delta[0], h, now[0])?,
            chain::linearize_prevalidated::<false>(self.params, [0.; 5], old, delta[1], h, now[1])?,
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
        Ok((now, stages[1], residual))
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
        if let Some(map) = &self.reduced {
            match map.step(old, input, family, phase, h, delta) {
                Ok((now, angle, next, iteration, true)) => {
                    return Ok((now, angle, next, iteration))
                }
                Ok((_, _, next, iteration, false)) if self.verify_reduced => {
                    let (now, angle, residual) =
                        self.residual(old, input, family, phase, h, next)?;
                    let correction = self.lu.solve(residual.map(|v| -v))?;
                    if maximum(&residual) <= 2e-13 && maximum(&correction) <= 2e-9 {
                        self.checked_proposals.set(self.checked_proposals.get() + 1);
                        return Ok((now, angle, next, iteration));
                    }
                    return Err(StepError::IterationBudget);
                }
                Err(error) if !matches!(error, StepError::IterationBudget) => return Err(error),
                _ if !self.diagnostic_recovery => return Err(StepError::IterationBudget),
                _ => self.fallback_calls.set(self.fallback_calls.get() + 1),
            }
        }
        let budget = if self.diagnostic_recovery { 24 } else { 12 };
        for iteration in 1..=budget {
            let (now, end_phase, residual) = self.residual(old, input, family, phase, h, delta)?;
            let change = self.lu.solve(residual.map(|v| -v))?;
            if maximum(&residual) <= 2e-13 && maximum(&change) <= 2e-9 {
                return Ok((now, end_phase, delta, iteration));
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
    timer_budget: usize,
}

impl Step<'_> {
    fn evaluate(
        &self,
        v: [f64; INTERFACE],
        seed: [chain::State; 2],
        mut contour_seed: Option<[latch::State; 2]>,
    ) -> Result<Closure, Failure> {
        let mut ports = self.ports;
        for i in 0..2 {
            let [base, tail, cv] = [v[3 * i], v[3 * i + 1], v[3 * i + 2]];
            ports[i].volume[1] = cv;
            ports[i].volume[2] = base;
            ports[i].filter[1] = tail;
            ports[i].latch.volts[CV] = cv;
            ports[i].latch.volts[TAIL] = tail;
        }
        let timer = latch::profile::start();
        let contour = contours::step_with_budget(
            self.contour,
            ports,
            self.h,
            self.previous,
            self.change,
            self.timer_budget,
            self.model.warm.then_some(&mut contour_seed),
        );
        let timer = latch::profile::split(latch::profile::Part::Contours, timer);
        let contour = contour?;
        let drive = contour.map(|s| [s.returns.volume[2], s.returns.filter[2]]);
        let audio = self
            .model
            .step(self.audio, drive, self.family, self.phase, self.h, seed);
        latch::profile::split(latch::profile::Part::Audio, timer);
        let (audio, phase, delta, audio_iterations) = audio.map_err(|error| ("audio", error))?;
        let mut residual = [0.; INTERFACE];
        for i in 0..2 {
            residual[3 * i] = v[3 * i] - voltage(audio[i], LOAD[0]);
            residual[3 * i + 1] = v[3 * i + 1] - voltage(audio[i], LOAD[1]);
            residual[3 * i + 2] = contour_ports::cv_return_residual(
                v[3 * i + 2],
                drive[i][0],
                contour[i].latch.0[latch::pin(27)],
            )
            .map_err(|error| ("CV", error))?;
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

    fn improve(
        &self,
        v: [f64; INTERFACE],
        result: &Closure,
        tangent: &Lu<INTERFACE>,
        attempts: usize,
    ) -> Result<Option<([f64; INTERFACE], Closure)>, StepError> {
        let direction = tangent.solve(result.residual.map(|r| -r))?;
        let norm = maximum(&result.residual);
        for half in 0..attempts {
            let x = std::array::from_fn(|i| v[i] + direction[i] * 0.5_f64.powi(half as i32));
            if let Ok(trial) = self.evaluate(x, result.delta, Some(result.contour.map(|s| s.latch)))
            {
                let next = maximum(&trial.residual);
                if next < norm && (attempts > 1 || next <= 1e-10 || next <= 0.5 * norm) {
                    return Ok(Some((x, trial)));
                }
            }
        }
        Ok(None)
    }

    fn solve(
        &self,
        mut v: [f64; INTERFACE],
        seed: [chain::State; 2],
    ) -> Result<(Closure, usize), Failure> {
        let mut result = self.evaluate(v, seed, None)?;
        let budget = if self.model.diagnostic_recovery || self.model.verify_reduced {
            12
        } else {
            6
        };
        for iteration in 1..=budget {
            if maximum(&result.residual) <= 1e-10 {
                return Ok((result, iteration));
            }
            if self.model.reuse {
                let cached = self.model.tangent.borrow();
                if let Some(factor) = cached.as_ref() {
                    if let Ok(Some(next)) = self.improve(v, &result, factor, 1) {
                        (v, result) = next;
                        self.model.reused.set(self.model.reused.get() + 1);
                        continue;
                    }
                }
            }
            // Differentiate the complete two-stage reaction. Both perturbations
            // reuse the same accepted capacitor history and VCO phase.
            let mut j = [[0.; INTERFACE]; INTERFACE];
            for column in 0..INTERFACE {
                let mut x = v;
                let dv = 1e-6;
                x[column] += dv;
                let probe =
                    self.evaluate(x, result.delta, Some(result.contour.map(|s| s.latch)))?;
                for (row, slopes) in j.iter_mut().enumerate() {
                    slopes[column] =
                        (probe.residual[row] - result.residual[row]) / (x[column] - v[column]);
                }
            }
            self.model.builds.set(self.model.builds.get() + 1);
            let factor = Lu::factor(j).map_err(|error| ("interface tangent", error))?;
            (v, result) = self
                .improve(v, &result, &factor, 12)
                .map_err(|error| ("interface tangent", error))?
                .ok_or(("interface descent", StepError::NoDecrease))?;
            if self.model.reuse {
                self.model.tangent.replace(Some(factor));
            }
        }
        if (self.model.diagnostic_recovery || self.model.verify_reduced)
            && maximum(&result.residual) <= 1e-10
        {
            return Ok((result, budget + 1));
        }
        Err(("interface", StepError::IterationBudget))
    }
}

#[derive(Clone, Copy)]
struct History {
    audio: chain::State,
    contour: Loaded,
    phase: f64,
    previous: Boundary,
    change: [f64; N],
    stride: usize,
}

struct Accepted {
    end: History,
    result: Closure,
    outer_iterations: usize,
    stride: usize,
}

impl History {
    fn advance(
        self,
        model: &Audio,
        family: &Family,
        ports: [Ports; 2],
        stride: usize,
        timer_budget: usize,
    ) -> Result<Accepted, Failure> {
        let [base, tail] = LOAD.map(|k| voltage(self.audio, k));
        let cv = self.previous.volts[CV];
        let change = self
            .change
            .map(|value| value * (stride as f64 / self.stride as f64));
        let step = Step {
            model,
            family,
            audio: self.audio,
            contour: self.contour,
            phase: self.phase,
            h: stride as f64 / (48_000. * 512.),
            previous: self.previous,
            change,
            ports,
            timer_budget,
        };
        let zero = chain::State::from_nodes([0.; chain::N]);
        let (result, outer_iterations) = step.solve([base, tail, cv, base, tail, cv], [zero; 2])?;
        let mut previous = self.previous;
        previous.volts[TAIL] = voltage(result.audio[1], LOAD[1]);
        previous.volts[CV] = result.cv;
        previous.key = ports[1].latch.key;
        let end = History {
            audio: result.audio[1],
            contour: result.contour[1],
            phase: result.phase,
            change: std::array::from_fn(|i| result.contour[1].latch.0[i] - self.contour.latch.0[i]),
            previous,
            stride,
        };
        Ok(Accepted {
            end,
            result,
            outer_iterations,
            stride,
        })
    }
}

fn readout(out: &mut impl Write, accepted: &Accepted, adaptive: bool) -> std::io::Result<()> {
    if adaptive {
        out.write_all(&(accepted.stride as f64).to_le_bytes())?;
    }
    for (audio, contour) in accepted
        .result
        .audio
        .into_iter()
        .zip(accepted.result.contour)
    {
        let [base, tail] = LOAD.map(|k| voltage(audio, k));
        let [r59, r60] = contour.returns.currents(base, tail);
        for value in [
            voltage(audio, 61),
            r59,
            r60,
            contour.timers[0],
            contour.timers[1],
            contour.returns.volume[2],
            contour.returns.filter[2],
            base,
            tail,
            contour.latch.0[latch::pin(26)],
            contour.latch.0[latch::pin(28)],
        ] {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    Ok(())
}

pub fn run(
    path: &str,
    key: f64,
    frames: usize,
    stride: usize,
    timer_budget: usize,
    mode: usize,
    reduce_audio: bool,
    reuse: bool,
    warm: bool,
    diagnostic_recovery: bool,
    verify_reduced: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    assert!(mode <= 5);
    let adaptive = mode != 0;
    let tolerance = match mode {
        2 => clock::PORTS,
        3 => clock::LATCH,
        4 | 5 => clock::COLLECTORS,
        _ => clock::STRICT,
    };
    assert!(stride.is_power_of_two() && stride <= 256 && matches!(timer_budget, 3 | 8));
    let mut bytes = Vec::new();
    std::fs::File::open(path)?.read_to_end(&mut bytes)?;
    let values = bytes
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()))
        .collect::<Vec<_>>();
    assert_eq!(values.len(), 2 * graph::N + 1);
    let x = |k| values[k] + values[k + graph::N];
    let phase = values[2 * graph::N];
    let audio = chain::State {
        high: std::array::from_fn(|k| values[graph::chain_index(k)]),
        low: std::array::from_fn(|k| values[graph::N + graph::chain_index(k)]),
    };
    let contour = Loaded {
        timers: TIMER_NODES.map(x),
        latch: State(CORE.map(x)),
        returns: Returns {
            volume: VOLUME_NODES.map(x),
            filter: FILTER_NODES.map(x),
        },
        q22_base: x(29),
    };
    let negative_score = key == -1. && frames == 128;
    assert!(negative_score || (0. ..=10.).contains(&key));
    let previous = Boundary {
        volts: PORTS.map(x),
        key: if negative_score { 0. } else { key },
        short: false,
    };

    // The x2 slot seeds its local collector solve. Shared CV and TAIL
    // are replaced by the stage voltages during interface iteration.
    let ports = [Ports {
        latch: previous,
        volume: VOLUME_PORTS.map(x),
        filter: FILTER_PORTS.map(x),
    }; 2];
    let family = Family::prepare(-1.6).map_err(|_| "H128 prepare")?;
    let mut state = History {
        audio,
        contour,
        phase,
        previous,
        change: [0.; N],
        stride,
    };
    let mut models = Vec::with_capacity(stride.ilog2() as usize + 1);
    for power in 0..=stride.ilog2() {
        let span = 1 << power;
        let model = if adaptive || span == stride {
            let h = span as f64 / (48_000. * 512.);
            Some(
                Audio::new(
                    audio,
                    &family,
                    phase,
                    h,
                    [x(3), x(37)],
                    reduce_audio,
                    reuse,
                    warm,
                    diagnostic_recovery,
                    verify_reduced,
                )
                .map_err(|e| format!("audio factor: {e:?}"))?,
            )
        } else {
            None
        };
        models.push(model);
    }
    let mut out = BufWriter::new(std::io::stdout().lock());
    let mut peak_ns = 0;
    let mut frame_ns = 0;
    let mut block_ns = 0;
    let mut max_outer = 0;
    let mut max_audio = 0;
    let mut max_residual: f64 = 0.;
    let mut stats = clock::Stats::default();
    let mut tick = 0;
    let mut proposal = stride;
    while tick < frames * 512 {
        let start = std::time::Instant::now();
        let mut input = ports;
        if negative_score {
            let key = if (16..96).contains(&(tick / 512)) {
                10.
            } else {
                0.
            };
            for stage in &mut input {
                stage.latch.key = key;
            }
        }
        let advance = |history: History, span: usize| {
            let model = models[span.ilog2() as usize].as_ref().unwrap();
            history.advance(model, &family, input, span, timer_budget)
        };
        let trial = if adaptive {
            let remaining = stride - tick % stride;
            while proposal > remaining {
                proposal /= 2;
            }
            clock::advance(
                state,
                &advance,
                &mut proposal,
                stride,
                &mut stats,
                tolerance,
                mode >= 4,
                mode == 5,
            )
        } else {
            advance(state, stride).map(|step| [Some(step), None])
        };
        let elapsed = start.elapsed().as_nanos();
        frame_ns += elapsed;
        block_ns += elapsed;
        let steps = trial.map_err(|e| {
            if frames == 128 {
                let fallbacks: usize = models
                    .iter()
                    .flatten()
                    .map(|m| m.fallback_calls.get())
                    .sum();
                let checks: usize = models
                    .iter()
                    .flatten()
                    .map(|m| m.checked_proposals.get())
                    .sum();
                eprintln!("STOP,{},{block_ns},{fallbacks},{checks}", tick / 512);
            }
            format!("loaded ports at tick {}: {e:?}", 8 * tick)
        })?;
        for step in steps.into_iter().flatten() {
            tick += step.stride;
            state = step.end;
            max_outer = max_outer.max(step.outer_iterations);
            max_audio = max_audio.max(step.result.audio_iterations);
            max_residual = max_residual.max(maximum(&step.result.residual));
            readout(&mut out, &step, adaptive)?;
        }
        if tick % 512 == 0 {
            peak_ns = peak_ns.max(frame_ns);
            frame_ns = 0;
        }
    }
    let builds: usize = models.iter().flatten().map(|m| m.builds.get()).sum();
    let reused: usize = models.iter().flatten().map(|m| m.reused.get()).sum();
    let fallbacks: usize = models
        .iter()
        .flatten()
        .map(|m| m.fallback_calls.get())
        .sum();
    let checks: usize = models
        .iter()
        .flatten()
        .map(|m| m.checked_proposals.get())
        .sum();
    latch::profile::report();
    eprintln!(
        "PORTS,{peak_ns},{max_outer},{max_audio},{max_residual:.17e},{},{},{},{:.17e},{builds},{reused},{},{},{},{block_ns},{fallbacks},{checks}",
        stats.solve, stats.defect, stats.switch, stats.worst, stats.trials, stats.reused, stats.whole,
    );
    out.flush()?;
    Ok(())
}
