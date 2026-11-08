//! The loaded RF-D contour engine for the frozen nominal H128 scene.
use crate::{family::Family, graph::{self, State, B, N}, reduced_audio as audio,
            reduced_lu::{dot, maximum, Lu}, StepError};

pub const TICKS: usize = 4096;
pub const RATE: usize = 48_000;
pub const BLOCK: usize = 128;
pub const BANKS: usize = 8;
const FINE: usize = 8;
const VT: f64 = 1.380649e-23 * 298.15 / 1.602176634e-19;
const MOTION: f64 = VT / 32.;
const C: usize = 56;
const INNER: usize = 108;
const PORT: [usize; 4] = [54, 55, 54 + C, 55 + C];
const BUS: usize = graph::chain_index(66);
const J7: usize = graph::chain_index(61);
const A: [[f64; 2]; 2] = [[5. / 12., -1. / 12.], [3. / 4., 1. / 4.]];
const COLLECTORS: [usize; 4] = [26, 28, 40, 42];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Switch {
    pub pair: usize,
    pub first_tick: usize,
    pub last_tick: usize,
    pub positive: bool,
}

#[derive(Clone, Copy)]
pub struct Frame {
    pub j7_v: f64,
    pub bus_v: f64,
    pub phase: f64,
    pub returns_a: [f64; 2],
    pub switches: [Option<Switch>; 4],
    #[cfg(laboratory)]
    pub state: State,
}

impl Frame {
    pub const EMPTY: Self = Self {
        j7_v: 0., bus_v: 0., phase: 0., returns_a: [0.; 2], switches: [None; 4],
        #[cfg(laboratory)]
        state: State { high: [0.; N], low: [0.; N], optional: false },
    };
}

#[derive(Clone, Copy, Default)]
pub struct Counters {
    pub widths: [usize; BANKS],
    pub guard_retries: usize,
    pub solver_retries: usize,
    pub iterations: usize,
    pub max_residual_a: f64,
    pub max_correction_v: f64,
}

#[derive(Clone, Copy)]
struct Running {
    state: State,
    phase: f64,
    frame: usize,
    proposal: usize,
}

pub struct Engine {
    maps: Vec<audio::Map>,
    audio_anchor: [f64; audio::NODES],
    family: Family,
    ceiling: usize,
    initial: Running,
    running: Running,
}

struct Evaluation<const FULL: bool> {
    contour: [graph::ContourParts<FULL>; 2],
    response: audio::Response,
    shared: [f64; 6],
    current: [f64; 2 * C],
    panel_j: [[f64; 2]; 2],
    phase: f64,
}

struct Accepted {
    running: Running,
    stage_order: [[bool; 2]; 2],
    movement: f64,
    iterations: usize,
    residual_a: f64,
    correction_v: f64,
}

fn value(s: State, k: usize) -> f64 {
    s.high[k] + s.low[k]
}

fn order(collectors: [f64; 4]) -> [bool; 2] {
    [collectors[0] >= collectors[1], collectors[2] >= collectors[3]]
}

fn inner_index(i: usize) -> usize {
    (i / 54) * C + i % 54
}

fn coefficient(e: &Evaluation<true>, i: usize, j: usize) -> f64 {
    let (a, r) = (i / C, i % C);
    let (b, c) = (j / C, j % C);
    B[a][b] * e.contour[b].mass[r][c]
        + if a == b { e.contour[a].j[r][c] } else { 0. }
}

fn direction(e: &Evaluation<true>) -> Result<([f64; 2 * C], [f64; 2]), StepError> {
    let lu = Lu::<INNER>::factor(std::array::from_fn(|i| std::array::from_fn(|j| {
        coefficient(e, inner_index(i), inner_index(j))
    })))?;
    let particular = lu.solve(std::array::from_fn(|i| -e.current[inner_index(i)]))?;
    let mut lift = [[0.; INNER]; 4];
    for (p, &column) in PORT.iter().enumerate() {
        lift[p] = lu.solve(std::array::from_fn(|i| coefficient(e, inner_index(i), column)))?;
    }
    let mut jacobian = e.response.jacobian;
    let mut current = e.response.current;
    for (p, &row) in PORT.iter().enumerate() {
        let feedback: [f64; INNER] = std::array::from_fn(|i| coefficient(e, row, inner_index(i)));
        current[p] += e.current[row] + dot(&feedback, &particular);
        for (q, &column) in PORT.iter().enumerate() {
            jacobian[p][q] += coefficient(e, row, column) - dot(&feedback, &lift[q]);
        }
    }
    for i in 0..2 {
        for j in 0..2 {
            jacobian[i + 4][j + 4] += e.panel_j[i][j];
        }
    }
    let shared = Lu::factor(jacobian)?.solve(current.map(|v| -v))?;
    let mut change = [0.; 2 * C];
    for (i, &k) in PORT.iter().enumerate() {
        change[k] = shared[i];
    }
    for i in 0..INNER {
        let mut v = particular[i];
        for j in 0..4 {
            v -= lift[j][i] * shared[j];
        }
        change[inner_index(i)] = v;
    }
    Ok((change, [shared[4], shared[5]]))
}

impl<const FULL: bool> Evaluation<FULL> {
    fn norm(&self) -> f64 {
        let mut residual = self.current;
        for (i, &row) in PORT.iter().enumerate() {
            residual[row] += self.response.current[i];
        }
        maximum(&residual).max(maximum(&self.response.current[4..]))
    }
}

impl Engine {
    /// Load the fixed electrical anchor and dyadic maps outside the callback.
    pub fn prepare(mut bytes: &[u8], cap: usize) -> Result<Self, StepError> {
        if !matches!(cap, 32 | 64 | 128 | 256 | 512)
            || bytes.len() != (2 * N + 1) * 8 + BANKS * audio::Map::BYTES
        {
            return Err(StepError::InvalidInput);
        }
        let state = State {
            high: audio::read_array(&mut bytes), low: audio::read_array(&mut bytes), optional: false,
        };
        let [phase] = audio::read_array(&mut bytes);
        if !state.valid() || !(0. ..1.).contains(&phase) {
            return Err(StepError::InvalidInput);
        }
        let mut maps = Vec::with_capacity(BANKS);
        for _ in 0..BANKS {
            maps.push(audio::Map::read(&mut bytes));
        }
        let ceiling = TICKS / cap;
        let initial = Running { state, phase, frame: 0, proposal: ceiling };
        Ok(Self {
            maps, initial, running: initial, ceiling,
            audio_anchor: audio::NODE.map(|k| value(state, k)),
            family: Family::prepare(-1.6).map_err(|_| StepError::InvalidInput)?,
        })
    }

    pub fn reset(&mut self) {
        self.running = self.initial;
    }

    pub fn position(&self) -> Frame {
        Self::observe(self.running, [None; 4])
    }

    fn observe(running: Running, switches: [Option<Switch>; 4]) -> Frame {
        Frame {
            j7_v: value(running.state, J7),
            bus_v: value(running.state, BUS),
            phase: running.phase,
            returns_a: graph::currents(running.state),
            switches,
            #[cfg(laboratory)]
            state: running.state,
        }
    }

    fn evaluate<const FULL: bool>(
        &self, running: Running, map: &audio::Map, history: &audio::History, key: f64, h: f64,
        delta: [f64; 2 * C], bus: [f64; 2],
    ) -> Result<Evaluation<FULL>, StepError> {
        let state = running.state;
        let contour = [
            graph::reduced_contour::<FULL>(state, delta[..C].try_into().unwrap(), key, h)?,
            graph::reduced_contour::<FULL>(state, delta[C..].try_into().unwrap(), key, h)?,
        ];
        let shared = std::array::from_fn(|i| {
            if i >= 4 {
                bus[i - 4]
            } else {
                let k = PORT[i] % C;
                let local = if k == 54 { 32 } else { 5 };
                value(state, k) - self.audio_anchor[local] + delta[PORT[i]]
            }
        });
        let bus = bus.map(|offset| offset + self.audio_anchor[62]);
        let rate = [
            self.family.frequency(bus[0]).map_err(|_| StepError::ExponentialDomain)?,
            self.family.frequency(bus[1]).map_err(|_| StepError::ExponentialDomain)?,
        ];
        let phases = A.map(|a| (running.phase + h * (a[0] * rate[0].0 + a[1] * rate[1].0)).rem_euclid(1.));
        let panel = [
            self.family.observe(bus[0], phases[0]).map_err(|_| StepError::ExponentialDomain)?,
            self.family.observe(bus[1], phases[1]).map_err(|_| StepError::ExponentialDomain)?,
        ];
        let panel_j = std::array::from_fn(|i| std::array::from_fn(|j| {
            (if i == j { panel[i].bus_dbus } else { 0. })
                + panel[i].bus_dphase * A[i][j] * h * rate[j].1
        }));
        let current = std::array::from_fn(|i| {
            let stage = i / C;
            let row = i % C;
            contour[stage].dc[row] + B[stage][0] * contour[0].dq[row] + B[stage][1] * contour[1].dq[row]
        });
        let mut response = map.response::<FULL>(history, &shared)?;
        for i in 0..2 {
            response.current[i + 4] += panel[i].currents_a[2];
        }
        Ok(Evaluation { contour, response, shared, current, panel_j, phase: phases[1] })
    }

    fn step(&self, old: Running, key: f64, width: usize) -> Result<Accepted, StepError> {
        let h = width as f64 / (RATE * TICKS) as f64;
        let map = &self.maps[width.trailing_zeros() as usize];
        let offset = std::array::from_fn(|i| value(old.state, audio::NODE[i]) - self.audio_anchor[i]);
        let history = map.history(offset);
        let before = COLLECTORS.map(|k| value(old.state, k));
        let mut delta = [0.; 2 * C];
        if key - value(old.state, 22) > 0.5 {
            let seed = key - 0.5 - old.state.high[22] - old.state.low[22];
            delta[22] = seed;
            delta[22 + C] = seed;
        }
        let mut bus = [offset[62]; 2];
        for iterations in 1..=80 {
            let e = self.evaluate::<true>(old, map, &history, key, h, delta, bus)?;
            let norm = e.norm();
            let (dv, db) = direction(&e)?;
            let correction = maximum(&dv).max(maximum(&db));
            if correction <= 2e-9 && norm <= 1e-12 {
                let end = map.endpoint(&history, &e.shared, &e.response);
                let mut state = old.state;
                state.high[..C].copy_from_slice(&e.contour[1].now.high);
                state.low[..C].copy_from_slice(&e.contour[1].now.low);
                let mut running = old;
                // Publish the contour's compensated charge coordinates at shared nodes.
                for (i, &k) in audio::NODE.iter().enumerate() {
                    if k >= C {
                        state.high[k] = self.audio_anchor[i] + end[i];
                        state.low[k] = 0.;
                    }
                }
                if !state.valid() {
                    return Err(StepError::ExponentialDomain);
                }
                running.state = state;
                running.phase = e.phase;
                let stages = e.contour.each_ref().map(|s| {
                    COLLECTORS.map(|k| s.now.high[k] + s.now.low[k])
                });
                let movement = stages.iter().flat_map(|s| s.iter().zip(before))
                    .fold(0_f64, |m, (v, base)| m.max((v - base).abs()));
                return Ok(Accepted {
                    running, stage_order: stages.map(order), movement, iterations,
                    residual_a: norm, correction_v: correction,
                });
            }
            let mut accepted = false;
            let mut scale = 1.;
            for _ in 0..24 {
                let trial = std::array::from_fn(|i| delta[i] + scale * dv[i]);
                let trial_bus = std::array::from_fn(|i| bus[i] + scale * db[i]);
                if self.evaluate::<false>(old, map, &history, key, h, trial, trial_bus)
                    .is_ok_and(|e| e.norm() < norm.max(1e-12))
                {
                    delta = trial;
                    bus = trial_bus;
                    accepted = true;
                    break;
                }
                scale *= 0.5;
            }
            if !accepted {
                return Err(StepError::NoDecrease);
            }
        }
        Err(StepError::IterationBudget)
    }

    /// A rejected block publishes neither samples nor electrical history.
    pub fn render(&mut self, keys: &[f64], output: &mut [Frame]) -> Result<Counters, StepError> {
        if keys.is_empty() || keys.len() > BLOCK || keys.len() != output.len()
            || keys.iter().any(|key| !(0. ..=10.).contains(key))
            || self.running.frame > usize::MAX / TICKS - BLOCK
        {
            return Err(StepError::InvalidInput);
        }
        let mut candidate = self.running;
        let mut frames = [Frame::EMPTY; BLOCK];
        let mut stats = Counters::default();
        for (frame, &key) in frames.iter_mut().zip(keys) {
            let mut within = 0;
            let mut switch_count = 0;
            let mut switches = [None; 4];
            while within < TICKS {
                let tick = candidate.frame * TICKS + within;
                let initial = order(COLLECTORS.map(|k| value(candidate.state, k)));
                let mut width = candidate.proposal;
                while tick % width != 0 || width > TICKS - within {
                    width /= 2;
                }
                let q = loop {
                    match self.step(candidate, key, width) {
                        Ok(q) if width > FINE && (q.movement > MOTION || q.stage_order.iter().any(|x| *x != initial)) => {
                            stats.guard_retries += 1;
                            width /= 2;
                        }
                        Ok(q) => break q,
                        Err(error) if width > 1 && matches!(error, StepError::NoDecrease
                            | StepError::IterationBudget | StepError::ExponentialDomain) =>
                        {
                            stats.solver_retries += 1;
                            width /= 2;
                        }
                        Err(error) => return Err(error),
                    }
                };
                for (pair, (&previous, &next)) in initial.iter().zip(&q.stage_order[1]).enumerate() {
                    if previous != next {
                        *switches.get_mut(switch_count).ok_or(StepError::IterationBudget)? = Some(Switch {
                            pair, first_tick: tick, last_tick: tick + width, positive: next,
                        });
                        switch_count += 1;
                    }
                }
                candidate = q.running;
                candidate.proposal = if q.movement < MOTION / 4. { (2 * width).min(self.ceiling) } else { width };
                stats.widths[width.trailing_zeros() as usize] += 1;
                stats.iterations += q.iterations;
                stats.max_residual_a = stats.max_residual_a.max(q.residual_a);
                stats.max_correction_v = stats.max_correction_v.max(q.correction_v);
                within += width;
            }
            candidate.frame += 1;
            *frame = Self::observe(candidate, switches);
        }
        output.copy_from_slice(&frames[..keys.len()]);
        self.running = candidate;
        Ok(stats)
    }
}
