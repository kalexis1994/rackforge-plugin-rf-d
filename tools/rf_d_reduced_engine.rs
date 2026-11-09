//! The loaded RF-D contour engine for the frozen nominal H128 scene.
use crate::{family::Family, graph::{self, State, B, N}, reduced_audio as audio,
            reduced_lu::{maximum, row_product, Lu}, StepError};

pub const TICKS: usize = 4096;
pub const RATE: usize = 48_000;
pub const BLOCK: usize = 128;
pub const BANKS: usize = if cfg!(sample_contour_clock) { 13 }
    else if cfg!(wide_contour_clock) { 11 } else { 8 };
const FINE: usize = 8;
const VT: f64 = 1.380649e-23 * 298.15 / 1.602176634e-19;
const MOTION: f64 = VT / 32.;
const CURVATURE_LIMIT: f64 = 2e-6;
const CLOCK_ERROR_LIMIT: f64 = 0.05;
const VERIFIED_CLOCK_WIDTH: usize = 1024;
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
    pub clock: ClockCounters,
    #[cfg(profile_reduced)]
    pub profile: [StepProfile; 3],
}

#[derive(Clone, Copy, Default)]
pub struct ClockCounters {
    pub solves: usize,
    pub comparisons: usize,
    pub error_retries: usize,
    pub event_retries: usize,
    pub reused_halves: usize,
    pub reused_siblings: usize,
    pub half_seed_retries: usize,
}

#[derive(Clone, Copy, Default)]
pub struct StepProfile {
    #[cfg(profile_reduced)]
    pub steps: usize,
    #[cfg(profile_reduced)]
    pub fine_steps: usize,
    #[cfg(profile_reduced)]
    pub wall_ns: u128,
    #[cfg(profile_reduced)]
    pub calls: [usize; 3],
    #[cfg(profile_reduced)]
    pub ns: [u128; 3],
    #[cfg(profile_reduced)]
    pub audio_tangents: usize,
}

#[derive(Clone, Copy)]
enum Work { Contour, Audio, Direction, AudioTangent }

impl StepProfile {
    #[inline]
    fn measure<T>(&mut self, part: Work, run: impl FnOnce() -> T) -> T {
        #[cfg(profile_reduced)]
        {
            let start = std::time::Instant::now();
            let result = run();
            let elapsed = start.elapsed().as_nanos();
            if matches!(part, Work::AudioTangent) {
                self.audio_tangents += 1;
                self.ns[Work::Audio as usize] += elapsed;
            } else {
                self.calls[part as usize] += 1;
                self.ns[part as usize] += elapsed;
            }
            result
        }
        #[cfg(not(profile_reduced))]
        {
            let _ = part;
            run()
        }
    }
}


#[derive(Clone, Copy)]
struct Running {
    state: State,
    phase: f64,
    frame: usize,
    proposal: usize,
    junctions: [f64; audio::STAGE_LAWS],
    continuation: Option<Continuation>,
}

#[derive(Clone, Copy)]
struct Continuation {
    // Endpoint derivative of the previous Radau interpolant times its width.
    contour: [f64; C],
    bus: f64,
    width: usize,
    key: f64,
    audio_jacobian: audio::PortJacobian,
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
    curvature: f64,
    iterations: usize,
    residual_a: f64,
    correction_v: f64,
}

struct Halves {
    first: Accepted,
    second: Option<Accepted>,
}

struct StageSeed {
    contour: [f64; 2 * C],
    bus: [f64; 2],
}

fn half_seed(origin: State, coarse: Running, start: State, at: [f64; 2]) -> Option<StageSeed> {
    let prior = coarse.continuation?;
    let increment = |end: State, k: usize| {
        (end.high[k] - origin.high[k]) + (end.low[k] - origin.low[k])
    };
    let weights = at.map(|t| [4.5 * t * (1. - t), 1.5 * t * (t - 1. / 3.)]);
    let project = |k, derivative, [a, b]: [f64; 2]| {
        let last = increment(coarse.state, k);
        let first = (2.5 * last - derivative) / 4.5;
        a * first + b * last - increment(start, k)
    };
    Some(StageSeed {
        contour: std::array::from_fn(|i| project(i % C, prior.contour[i % C], weights[i / C])),
        bus: weights.map(|w| project(BUS, prior.bus, w)),
    })
}

fn value(s: State, k: usize) -> f64 {
    s.high[k] + s.low[k]
}

fn order(collectors: [f64; 4]) -> [bool; 2] {
    [collectors[0] >= collectors[1], collectors[2] >= collectors[3]]
}

// Algebraic rows have no stage cross-coupling. Eliminating them first
// keeps their fill local before the dynamic rows and the two audio ports.
const INNER_ORDER: [usize; 54] = [
    8, 16, 22, 24, 53, 44, 47, 50, 51, 49, 46, 45, 43,
    12, 13, 15, 14, 11, 10, 9, 7, 6,
    0, 1, 2, 3, 4, 29, 30, 31, 32, 33, 35, 36, 37,
    5, 17, 18, 19, 20, 21, 23, 25, 26, 27, 28, 34,
    38, 39, 40, 41, 42, 48, 52,
];

fn inner_index(i: usize) -> usize {
    (i / 54) * C + INNER_ORDER[i % 54]
}

fn coefficient(e: &Evaluation<true>, i: usize, j: usize) -> f64 {
    let (a, r) = (i / C, i % C);
    let (b, c) = (j / C, j % C);
    B[a][b] * e.contour[b].mass[r][c]
        + if a == b { e.contour[a].j[r][c] } else { 0. }
}

fn direction(e: &Evaluation<true>, mut jacobian: audio::PortJacobian) -> Result<([f64; 2 * C], [f64; 2]), StepError> {
    let lu = Lu::<INNER>::factor(std::array::from_fn(|i| std::array::from_fn(|j| {
        coefficient(e, inner_index(i), inner_index(j))
    })))?;
    // One particular solution and four port lifts share the same row pass.
    let interior = lu.solve_batch::<5>(&std::array::from_fn(|i| {
        let row = inner_index(i);
        std::array::from_fn(|k| if k == 0 { -e.current[row] } else { coefficient(e, row, PORT[k - 1]) })
    }))?;
    let mut current = e.response.current;
    for (p, &row) in PORT.iter().enumerate() {
        let feedback: [f64; INNER] = std::array::from_fn(|i| coefficient(e, row, inner_index(i)));
        let response = row_product(&feedback, &interior);
        current[p] += e.current[row] + response[0];
        for (q, &column) in PORT.iter().enumerate() {
            jacobian[p][q] += coefficient(e, row, column) - response[q + 1];
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
        let mut v = interior[i][0];
        for j in 0..4 {
            v -= interior[i][j + 1] * shared[j];
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

fn clock_limit(width: usize) -> f64 {
    // Wide proposals get less local error headroom than the 1024-tick bank.
    CLOCK_ERROR_LIMIT * (VERIFIED_CLOCK_WIDTH as f64 / width as f64).min(1.)
}

fn clock_error(coarse: Running, fine: Running) -> f64 {
    let nodal = (0..N).map(|k| {
        let a = value(coarse.state, k);
        let b = value(fine.state, k);
        (a - b).abs() / (20e-6 + 2e-6 * b.abs())
    }).fold(0_f64, f64::max);
    let returns = graph::currents(coarse.state).into_iter().zip(graph::currents(fine.state))
        .map(|(a, b)| (a - b).abs() / (2e-9 + 2e-5 * b.abs()))
        .fold(0_f64, f64::max);
    let phase = ((coarse.phase - fine.phase + 0.5).rem_euclid(1.) - 0.5).abs() / 1e-7;
    nodal.max(returns).max(phase)
}

fn retryable(error: StepError) -> bool {
    matches!(error, StepError::NoDecrease | StepError::IterationBudget | StepError::ExponentialDomain)
}

impl Engine {
    /// Load the fixed electrical anchor and dyadic maps outside the callback.
    pub fn prepare(mut bytes: &[u8], cap: usize) -> Result<Self, StepError> {
        if !cap.is_power_of_two() || !(TICKS >> (BANKS - 1)..=512).contains(&cap)
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
        let initial = Running {
            state, phase, frame: 0, proposal: ceiling, junctions: [0.; audio::STAGE_LAWS],
            continuation: None,
        };
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
        delta: [f64; 2 * C], bus: [f64; 2], seed: &audio::Junctions, profile: &mut StepProfile,
    ) -> Result<Evaluation<FULL>, StepError> {
        let state = running.state;
        let contour = profile.measure(Work::Contour, || -> Result<_, StepError> { Ok([
            graph::reduced_contour::<FULL>(state, delta[..C].try_into().unwrap(), key, h)?,
            graph::reduced_contour::<FULL>(state, delta[C..].try_into().unwrap(), key, h)?,
        ]) })?;
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
        let mut response = profile.measure(Work::Audio, || map.response(history, &shared, seed))?;
        for i in 0..2 {
            response.current[i + 4] += panel[i].currents_a[2];
        }
        Ok(Evaluation { contour, response, shared, current, panel_j, phase: phases[1] })
    }

    fn step(
        &self, old: Running, key: f64, width: usize, profile: &mut StepProfile,
    ) -> Result<Accepted, StepError> {
        if let Some(prior) = old.continuation.as_ref().filter(|prior| {
            prior.key == key && width <= 2 * prior.width
        }) {
            if let Ok(accepted) = self.solve_step(old, key, width, Some(prior), None, profile) {
                return Ok(accepted);
            }
        }
        self.solve_step(old, key, width, None, None, profile)
    }

    fn solve_step(
        &self, old: Running, key: f64, width: usize,
        prior: Option<&Continuation>, stage_seed: Option<&StageSeed>, profile: &mut StepProfile,
    ) -> Result<Accepted, StepError> {
        let h = width as f64 / (RATE * TICKS) as f64;
        let map = &self.maps[width.trailing_zeros() as usize];
        let offset = std::array::from_fn(|i| value(old.state, audio::NODE[i]) - self.audio_anchor[i]);
        let history = map.history(offset);
        let before = COLLECTORS.map(|k| value(old.state, k));
        let mut delta = [0.; 2 * C];
        let mut bus = [offset[62]; 2];
        if let Some(seed) = stage_seed {
            delta = seed.contour;
            bus = seed.bus.map(|change| offset[62] + change);
        } else if let Some(prior) = prior {
            let ratio = width as f64 / prior.width as f64;
            for (stage, fraction) in [1. / 3., 1.].into_iter().enumerate() {
                let scale = fraction * ratio;
                for (change, tangent) in delta[stage * C..(stage + 1) * C].iter_mut().zip(prior.contour) {
                    *change = scale * tangent;
                }
                bus[stage] += scale * prior.bus;
            }
        }
        if key - value(old.state, 22) > 0.5 {
            let seed = key - 0.5 - old.state.high[22] - old.state.low[22];
            delta[22] = seed;
            delta[22 + C] = seed;
        }
        let mut seed = std::array::from_fn(|i| old.junctions[i % audio::STAGE_LAWS]);
        let mut cached_jacobian = prior.filter(|prior| prior.width == width)
            .map(|prior| prior.audio_jacobian);
        for iterations in 1..=80 {
            let e = self.evaluate::<true>(old, map, &history, key, h, delta, bus, &seed, profile)?;
            let norm = e.norm();
            let mut estimate = cached_jacobian.filter(|_| norm > 1e-12);
            loop {
                let reused = estimate.is_some();
                let jacobian = match estimate.take() {
                    Some(jacobian) => jacobian,
                    None => profile.measure(Work::AudioTangent, || map.jacobian(&e.response))?,
                };
                let (dv, db) = match profile.measure(Work::Direction, || direction(&e, jacobian)) {
                    Ok(change) => change,
                    Err(_) if reused => {
                        cached_jacobian = None;
                        continue;
                    }
                    Err(error) => return Err(error),
                };
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
                    running.junctions.copy_from_slice(&e.response.junctions[audio::STAGE_LAWS..]);
                    running.continuation = Some(Continuation {
                        contour: std::array::from_fn(|k| 2.5 * delta[C + k] - 4.5 * delta[k]),
                        bus: 2.5 * (bus[1] - offset[62]) - 4.5 * (bus[0] - offset[62]),
                        width, key, audio_jacobian: jacobian,
                    });
                    let stages = e.contour.each_ref().map(|s| {
                        COLLECTORS.map(|k| s.now.high[k] + s.now.low[k])
                    });
                    let movement = stages.iter().flat_map(|s| s.iter().zip(before))
                        .fold(0_f64, |m, (v, base)| m.max((v - base).abs()));
                    let curvature = if cfg!(wide_clock_curvature) {
                        INNER_ORDER[35..].iter().copied().chain([14]).map(|k| {
                            let first = e.contour[0].now.high[k] + e.contour[0].now.low[k];
                            let last = e.contour[1].now.high[k] + e.contour[1].now.low[k];
                            ((first - value(old.state, k)) - (last - value(old.state, k)) / 3.).abs()
                        }).fold(0_f64, f64::max)
                    } else {
                        0.
                    };
                    return Ok(Accepted {
                        running, stage_order: stages.map(order), movement, curvature, iterations,
                        residual_a: norm, correction_v: correction,
                    });
                }
                let mut accepted = false;
                let mut scale = 1.;
                for _ in 0..24 {
                    let trial = std::array::from_fn(|i| delta[i] + scale * dv[i]);
                    let trial_bus = std::array::from_fn(|i| bus[i] + scale * db[i]);
                    if let Ok(candidate) = self.evaluate::<false>(
                        old, map, &history, key, h, trial, trial_bus, &e.response.junctions, profile,
                    ) {
                        if candidate.norm() < norm.max(1e-12) {
                            delta = trial;
                            bus = trial_bus;
                            seed = candidate.response.junctions;
                            accepted = true;
                            break;
                        }
                    }
                    scale *= 0.5;
                }
                if accepted {
                    break;
                }
                if !reused {
                    return Err(StepError::NoDecrease);
                }
                cached_jacobian = None;
            }
        }
        Err(StepError::IterationBudget)
    }

    fn solve_half(
        &self, old: Running, key: f64, width: usize, seed: Option<StageSeed>,
        profile: &mut StepProfile, clock: &mut ClockCounters,
    ) -> Result<Accepted, StepError> {
        clock.solves += 1;
        if let Some(seed) = seed {
            let prior = old.continuation.as_ref().filter(|p| p.key == key && width <= 2 * p.width);
            if let Ok(step) = self.solve_step(old, key, width, prior, Some(&seed), profile) {
                return Ok(step);
            }
            clock.half_seed_retries += 1;
            clock.solves += 1;
        }
        self.step(old, key, width, profile)
    }

    /// Return None when either of the two finer trajectories brackets an event.
    fn compare_clock(
        &self, old: Running, key: f64, width: usize, coarse: Running,
        initial: [bool; 2], profile: &mut StepProfile, clock: &mut ClockCounters,
        halves: &mut Option<Halves>,
    ) -> Result<Option<f64>, StepError> {
        clock.comparisons += 1;
        let middle_seed = half_seed(old.state, coarse, old.state, [1. / 6., 0.5]);
        let middle = self.solve_half(old, key, width / 2, middle_seed, profile, clock)?;
        let crossed = middle.stage_order.iter().any(|stage| *stage != initial);
        let midpoint = middle.running;
        let halves = halves.insert(Halves { first: middle, second: None });
        if crossed {
            return Ok(None);
        }
        let end_seed = half_seed(old.state, coarse, midpoint.state, [2. / 3., 1.]);
        let fine = self.solve_half(midpoint, key, width / 2, end_seed, profile, clock)?;
        let crossed = fine.stage_order.iter().any(|stage| *stage != initial);
        let endpoint = fine.running;
        halves.second = Some(fine);
        Ok((!crossed).then(|| clock_error(coarse, endpoint)))
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
            let mut next_sibling = None;
            while within < TICKS {
                let tick = candidate.frame * TICKS + within;
                let initial = order(COLLECTORS.map(|k| value(candidate.state, k)));
                let mut width = candidate.proposal;
                while tick % width != 0 || width > TICKS - within {
                    width /= 2;
                }
                #[cfg(profile_reduced)]
                let profile = &mut stats.profile[match candidate.frame {
                    0..74 => 0,
                    74..83 => 1,
                    _ => 2,
                }];
                #[cfg(not(profile_reduced))]
                let profile = &mut StepProfile::default();
                #[cfg(profile_reduced)]
                let start = std::time::Instant::now();
                let mut sibling = next_sibling.take().filter(|(w, _)| *w == width);
                let mut halves: Option<Halves> = None;
                let (q, grow, second_half) = loop {
                    let (q, second_half) = if let Some(pair) = halves.take() {
                        // The last comparison began at the same state and KEY.
                        stats.clock.reused_halves += 1;
                        (pair.first, pair.second)
                    } else if let Some((_, trial)) = sibling.take() {
                        stats.clock.reused_siblings += 1;
                        (trial, None)
                    } else {
                        stats.clock.solves += 1;
                        match self.step(candidate, key, width, profile) {
                            Ok(q) => (q, None),
                            Err(error) if width > 1 && retryable(error) => {
                                stats.solver_retries += 1;
                                width /= 2;
                                continue;
                            }
                            Err(error) => return Err(error),
                        }
                    };
                    if cfg!(adaptive_contour_clock) {
                        if width <= FINE {
                            break (q, true, second_half);
                        }
                        let order_changed = q.stage_order.iter().any(|stage| *stage != initial);
                        let error = if order_changed {
                            Ok(None)
                        } else {
                            self.compare_clock(
                                candidate, key, width, q.running, initial, profile, &mut stats.clock,
                                &mut halves,
                            )
                        };
                        match error {
                            Ok(Some(value)) if value <= clock_limit(width) => {
                                break (q, value * 16. <= clock_limit((2 * width).min(self.ceiling)), second_half);
                            }
                            Ok(Some(_)) => stats.clock.error_retries += 1,
                            Ok(None) => stats.clock.event_retries += 1,
                            Err(error) if retryable(error) => stats.solver_retries += 1,
                            Err(error) => return Err(error),
                        }
                        stats.guard_retries += 1;
                        width /= 2;
                        continue;
                    }
                    if width > FINE && (q.movement > MOTION || q.curvature > CURVATURE_LIMIT
                        || q.stage_order.iter().any(|stage| *stage != initial))
                    {
                        stats.guard_retries += 1;
                        width /= 2;
                        continue;
                    }
                    let grow = q.movement < MOTION / 4. && q.curvature < CURVATURE_LIMIT / 4.;
                    break (q, grow, second_half);
                };
                #[cfg(profile_reduced)]
                {
                    profile.wall_ns += start.elapsed().as_nanos();
                    profile.steps += 1;
                    profile.fine_steps += usize::from(width <= FINE);
                }
                for (pair, (&previous, &next)) in initial.iter().zip(&q.stage_order[1]).enumerate() {
                    if previous != next {
                        *switches.get_mut(switch_count).ok_or(StepError::IterationBudget)? = Some(Switch {
                            pair, first_tick: tick, last_tick: tick + width, positive: next,
                        });
                        switch_count += 1;
                    }
                }
                // Reuse the second half only if its exact predecessor was
                // just published. A finer replacement discards this sibling.
                next_sibling = second_half.map(|trial| (width, trial));
                candidate = q.running;
                candidate.proposal = if grow { (2 * width).min(self.ceiling) } else { width };
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
