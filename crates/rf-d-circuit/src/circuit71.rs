//! Simultaneous Q3/Q2/CR6 -> R59 -> Q18 -> full chain through J7.
//! Board2 C2 and reset base stay imposed; the latch is not integrated.
//! SVC-9 Figs.9-7/9-11/9-17 PDF pp.9/13/19. Fixed 71-node arrays.

use crate::circuit66::{self, Boundary as ChainBoundary, Parameters as ChainParameters};
use crate::loudness_follower::{self, Parameters as FollowerParameters};
use crate::output::main_load;
use crate::output_conversion::{
    max_abs, solve_linear_many, solve_linear_sparse, Parameters as ConversionParameters,
};
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

const N: usize = 71;
const G59: f64 = 1.0 / 68000.0;

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    /// `chain.recovery.vca.loudness_v` is replaced by the solved board2 output.
    pub chain: ChainBoundary,
    pub c2_v: f64,
    pub reset_base_v: f64,
    pub supply_v: f64,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub chain: circuit66::State,
    /// Board2 nodes in loudness_follower::NODE_NAMES order.
    pub follower_v: [f64; 5],
    pub previous_follower_v: [f64; 5],
    /// Last imposed sources, for observable fixed-history continuation.
    pub c2_v: f64,
    pub reset_base_v: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Result71 {
    pub chain: circuit66::Result66,
    pub max_physical_kcl_a: f64,
    pub correction_v: f64,
    pub timing_current_a: f64,
    pub reset_current_a: f64,
    pub r59_current_a: f64,
    /// Includes failed predictor solves inside this successful call.
    pub solves: usize,
    /// Newton rounds visited, including convergence checks and failed retries.
    pub total_iterations: usize,
}

#[derive(Clone, Copy, Debug)]
pub struct Preparation {
    pub state: State,
    pub solves: usize,
    pub total_iterations: usize,
    pub max_physical_kcl_a: f64,
}

/// Joint current port seen at the two exposed board2 terminals. Indices are
/// [C2, reset base]; all derivatives keep incoming capacitor histories fixed.
#[derive(Clone, Copy, Debug)]
pub struct PortResponse {
    /// Provisional candidate only; the caller's incoming state is immutable.
    pub next_state: State,
    pub result: Result71,
    pub current_a: [f64; 2],
    /// d(current_i)/d(source_j), S. The active network is not reciprocal.
    pub admittance_s: [[f64; 2]; 2],
    /// Natural documentary node order, d(node_i)/d(source_j), V/V.
    pub node_gradient_v_per_v: [[f64; 2]; N],
}

/// Solve the whole loaded network and its two source tangents without
/// publishing history. `None` opens capacitors for DC; `Some` represents one
/// implicit-Euler step at the immutable incoming eighteen capacitor voltages.
/// No source continuation or branch selection is hidden in this port.
pub fn solve_port(
    seed: [f64; N],
    previous: Option<&State>,
    p: ChainParameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    f: FollowerParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<PortResponse, StepError> {
    let mut work = Work::default();
    let root = solve(seed, previous, p, c, h, f, b, budget, &mut work)?;
    let (_, j) = linearize(previous, p, c, h, f, b, &root.x)?;
    work.evaluations += 1;
    let nvt = f.diode_ideality * 1.380649e-23 * f.temperature_k / 1.602176634e-19;
    let gd = f.germanium_is_a * ((root.x[70] - b.reset_base_v) / nvt).exp() / nvt;
    let mut rhs = [[0.0; 2]; N];
    rhs[66][0] = 1.0 / 10000.0;
    rhs[70][1] = gd;
    let dx = solve_linear_many(j, rhs)?;
    let admittance = std::array::from_fn(|i| {
        std::array::from_fn(|k| {
            let indicator = if i == k { 1.0 } else { 0.0 };
            if i == 0 {
                (indicator - dx[66][k]) / 10000.0
            } else {
                -gd * (dx[70][k] - indicator)
            }
        })
    });
    let mut next = previous.copied().unwrap_or_else(|| dc_state(root.x, b));
    let result = publish(&mut next, root, p, f, b, work, false)?;
    Ok(PortResponse {
        next_state: next,
        result,
        current_a: [result.timing_current_a, result.reset_current_a],
        admittance_s: admittance,
        node_gradient_v_per_v: dx,
    })
}

fn nodes(s: &State) -> [f64; N] {
    std::array::from_fn(|i| {
        if i < 66 {
            s.chain.node_v[i]
        } else {
            s.follower_v[i - 66]
        }
    })
}

fn chain_boundary(mut b: Boundary, x: &[f64; N]) -> ChainBoundary {
    b.chain.recovery.vca.loudness_v = x[69];
    b.chain
}

fn physical_max(r: &[f64; N], b: Boundary) -> f64 {
    let lower = b.chain.recovery.vca.second.output.output.r21_lower_ohm;
    r.iter()
        .enumerate()
        .filter(|(i, _)| *i != 49 || (lower > 0.0 && lower < 5000.0))
        .fold(0.0_f64, |a, (_, v)| a.max(v.abs()))
}

/// Documentary order: first 66 audio/control nodes, then five board2 nodes.
/// R21 endpoint row49 is V; all remaining rows are physical outgoing KCL, A.
pub fn linearize(
    previous: Option<&State>,
    p: ChainParameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    f: FollowerParameters,
    b: Boundary,
    x: &[f64; N],
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    if x.iter().any(|v| !v.is_finite()) || previous.is_some_and(|s| !valid_state(s)) {
        return Err(StepError::InvalidInput);
    }
    let xx = std::array::from_fn(|i| x[i]);
    let cb = chain_boundary(b, x);
    let (r66, j66) = if let Some(old) = previous {
        circuit66::linearize(&old.chain, p, c, h, cb, &xx)?
    } else {
        circuit66::linearize_dc(p, c, h, cb, &xx)?
    };
    let fb = loudness_follower::Boundary {
        c2_v: b.c2_v,
        reset_base_v: b.reset_base_v,
        supply_v: b.supply_v,
        load_conductance_s: G59,
        load_reference_v: x[32],
    };
    let (rf, jf) = loudness_follower::linearize(std::array::from_fn(|i| x[66 + i]), f, fb)?;
    let r = std::array::from_fn(|i| if i < 66 { r66[i] } else { rf[i - 66] });
    let mut j = [[0.0; N]; N];
    for i in 0..66 {
        j[i][..66].copy_from_slice(&j66[i]);
    }
    for i in 0..5 {
        j[66 + i][66..].copy_from_slice(&jf[i]);
    }
    // Each subsystem already includes its own diagonal G59; add the other
    // terminal's derivative exactly once. Base voltage is no longer a source.
    j[32][69] = -G59;
    j[69][32] = -G59;
    Ok((r, j))
}

fn valid_state(s: &State) -> bool {
    s.chain
        .node_v
        .iter()
        .chain(s.chain.previous_node_v.iter())
        .chain(s.chain.capacitor_v.iter())
        .chain(s.follower_v.iter())
        .chain(s.previous_follower_v.iter())
        .all(|v| v.is_finite())
        && s.chain.c10_capacitor_v.is_finite()
        && s.c2_v.is_finite()
        && s.reset_base_v.is_finite()
}

fn valid_budget(b: SolverBudget) -> bool {
    (1..=16).contains(&b.iterations) && (1..=16).contains(&b.line_search_halvings)
}

struct Root {
    x: [f64; N],
    iterations: usize,
    kcl_a: f64,
    correction_v: f64,
    residual: [f64; N],
}

#[derive(Default)]
struct Work {
    solves: usize,
    iterations: usize,
    evaluations: usize,
}

fn solve(
    mut x: [f64; N],
    old: Option<&State>,
    p: ChainParameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    f: FollowerParameters,
    b: Boundary,
    budget: SolverBudget,
    work: &mut Work,
) -> Result<Root, StepError> {
    if !valid_budget(budget) {
        return Err(StepError::InvalidInput);
    }
    work.solves += 1;
    let mut cached = None;
    for iteration in 0..budget.iterations {
        work.iterations += 1;
        let (r, d) = match cached.take() {
            Some(value) => value,
            None => {
                work.evaluations += 1;
                let (r, j) = linearize(old, p, c, h, f, b, &x)?;
                let d = solve_linear_sparse(j, r.map(|v| -v))?;
                (r, d)
            }
        };
        let error = max_abs(&r);
        let correction = max_abs(&d);
        if error < 1e-11 && correction < 1e-8 {
            return Ok(Root {
                x,
                iterations: iteration,
                kcl_a: physical_max(&r, b),
                correction_v: correction,
                residual: r,
            });
        }
        let mut accepted = None;
        for power in 0..budget.line_search_halvings {
            let factor = 0.5_f64.powi(power as i32);
            let trial = std::array::from_fn(|i| x[i] + factor * d[i]);
            work.evaluations += 1;
            if let Ok((rt, jt)) = linearize(old, p, c, h, f, b, &trial) {
                let Ok(dt) = solve_linear_sparse(jt, rt.map(|v| -v)) else {
                    continue;
                };
                let next_error = max_abs(&rt);
                let decreases = if error < 1e-11 {
                    next_error < 1e-11 && max_abs(&dt) < correction
                } else {
                    next_error < error
                };
                if decreases {
                    accepted = Some((trial, rt, dt));
                    break;
                }
            }
        }
        if let Some((trial, rt, dt)) = accepted {
            x = trial;
            cached = Some((rt, dt));
        } else {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}

fn dc_state(x: [f64; N], b: Boundary) -> State {
    let chain = std::array::from_fn(|i| x[i]);
    let follower = std::array::from_fn(|i| x[66 + i]);
    State {
        chain: circuit66::State {
            node_v: chain,
            previous_node_v: chain,
            capacitor_v: circuit66::charges(&chain, chain_boundary(b, &x)),
            c10_capacitor_v: x[22] - x[7],
        },
        follower_v: follower,
        previous_follower_v: follower,
        c2_v: b.c2_v,
        reset_base_v: b.reset_base_v,
    }
}

/// Direct preparation from a complete numerical seed. All audio capacitors
/// open at DC; their voltages are reconstructed only after the requested root.
pub fn initial_state_from_nodes(
    seed: [f64; N],
    p: ChainParameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    f: FollowerParameters,
    b: Boundary,
) -> Result<Preparation, StepError> {
    let mut work = Work::default();
    let root = solve(
        seed,
        None,
        p,
        c,
        h,
        f,
        b,
        SolverBudget::default(),
        &mut work,
    )?;
    Ok(Preparation {
        state: dc_state(root.x, b),
        solves: 1,
        total_iterations: work.iterations,
        max_physical_kcl_a: root.kcl_a,
    })
}

/// Explicit offline numerical preparation: close at C2=3.2V, then 64 DC
/// source stages to the actual target. This anchor is not a contour peak or
/// calibration. Reset base and supplies stay at the requested boundaries.
/// `seed66` must be an audio-chain root near the 3.2V anchor (about 2V at
/// R59). A cold guess reconstructed from a switched-off root may fail;
/// use `initial_state_from_nodes` when a complete joint seed is available.
pub fn initial_state(
    seed66: [f64; 66],
    p: ChainParameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    f: FollowerParameters,
    b: Boundary,
) -> Result<Preparation, StepError> {
    let mut stage = Boundary { c2_v: 3.2, ..b };
    let guess = loudness_follower::initial_guess(loudness_follower::Boundary {
        c2_v: 3.2,
        reset_base_v: b.reset_base_v,
        supply_v: b.supply_v,
        load_conductance_s: G59,
        load_reference_v: seed66[32],
    });
    let seed = std::array::from_fn(|i| if i < 66 { seed66[i] } else { guess[i - 66] });
    let mut work = Work::default();
    let mut root = solve(
        seed,
        None,
        p,
        c,
        h,
        f,
        stage,
        SolverBudget::default(),
        &mut work,
    )?;
    let mut kcl = root.kcl_a;
    for i in 1..=64 {
        stage.c2_v = if i == 64 {
            b.c2_v
        } else {
            3.2 + (b.c2_v - 3.2) * i as f64 / 64.0
        };
        root = solve(
            root.x,
            None,
            p,
            c,
            h,
            f,
            stage,
            SolverBudget::default(),
            &mut work,
        )?;
        kcl = kcl.max(root.kcl_a);
    }
    Ok(Preparation {
        state: dc_state(root.x, b),
        solves: 65,
        total_iterations: work.iterations,
        max_physical_kcl_a: kcl,
    })
}

fn publish(
    state: &mut State,
    root: Root,
    p: ChainParameters,
    f: FollowerParameters,
    b: Boundary,
    work: Work,
    fallback: bool,
) -> Result<Result71, StepError> {
    let cb = chain_boundary(b, &root.x);
    let ob = cb.recovery.vca.second.output.output;
    let main = main_load(ob)?;
    let mut next = *state;
    let i10 = if let Some(r14) = cb.r14_ohm {
        let series = r14 + 1000.0 - (p.r30_ohm - 330.0);
        let gc = 10e-6 / ob.dt_s;
        gc / (1.0 + gc * series) * (root.x[22] - root.x[7] - state.chain.c10_capacitor_v)
    } else {
        0.0
    };
    let control = root.residual[62..66]
        .iter()
        .fold(0.0_f64, |a, v| a.max(v.abs()));
    let chain_kcl = root.residual[..66]
        .iter()
        .enumerate()
        .filter(|(i, _)| *i != 49 || (ob.r21_lower_ohm > 0.0 && ob.r21_lower_ohm < 5000.0))
        .fold(0.0_f64, |a, (_, v)| a.max(v.abs()));
    let chain = circuit66::publish_step(
        &mut next.chain,
        p,
        cb,
        main,
        (
            std::array::from_fn(|i| root.x[i]),
            root.iterations,
            chain_kcl,
            i10,
            control,
        ),
        fallback,
        work.evaluations,
    );
    next.previous_follower_v = state.follower_v;
    next.follower_v = std::array::from_fn(|i| root.x[66 + i]);
    next.c2_v = b.c2_v;
    next.reset_base_v = b.reset_base_v;
    let nvt = f.diode_ideality * 1.380649e-23 * f.temperature_k / 1.602176634e-19;
    let result = Result71 {
        chain,
        max_physical_kcl_a: root.kcl_a,
        correction_v: root.correction_v,
        timing_current_a: (b.c2_v - root.x[66]) / 10000.0,
        reset_current_a: -f.germanium_is_a * ((root.x[70] - b.reset_base_v) / nvt).exp_m1(),
        r59_current_a: (root.x[69] - root.x[32]) * G59,
        solves: work.solves,
        total_iterations: work.iterations,
    };
    *state = next;
    Ok(result)
}

/// One physical implicit-Euler step, predictor/old-root retry, atomic on failure.
pub fn step(
    state: &mut State,
    p: ChainParameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    f: FollowerParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<Result71, StepError> {
    if !valid_state(state) || !valid_budget(budget) {
        return Err(StepError::InvalidInput);
    }
    let old = nodes(state);
    let predicted = std::array::from_fn(|i| {
        2.0 * old[i]
            - if i < 66 {
                state.chain.previous_node_v[i]
            } else {
                state.previous_follower_v[i - 66]
            }
    });
    let mut work = Work::default();
    let (root, fallback) = match solve(predicted, Some(state), p, c, h, f, b, budget, &mut work) {
        Ok(root) => (root, false),
        Err(_) => (
            solve(old, Some(state), p, c, h, f, b, budget, &mut work)?,
            true,
        ),
    };
    publish(state, root, p, f, b, work, fallback)
}

/// Explicit numerical continuation of imposed C2/reset sources at ONE time
/// step. Every stage retains the original eighteen capacitor histories, BUS,
/// dt, panel, and supply. No stage publishes a physical intermediate state.
pub fn step_continued(
    state: &mut State,
    p: ChainParameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    f: FollowerParameters,
    b: Boundary,
    stages: usize,
    budget: SolverBudget,
) -> Result<Result71, StepError> {
    if !valid_state(state) || !valid_budget(budget) || !(1..=64).contains(&stages) {
        return Err(StepError::InvalidInput);
    }
    let mut stage = Boundary {
        c2_v: state.c2_v,
        reset_base_v: state.reset_base_v,
        ..b
    };
    let mut work = Work::default();
    let mut root = solve(
        nodes(state),
        Some(state),
        p,
        c,
        h,
        f,
        stage,
        budget,
        &mut work,
    )?;
    for i in 1..=stages {
        if i == stages {
            stage = b;
        } else {
            stage.c2_v = state.c2_v + (b.c2_v - state.c2_v) * i as f64 / stages as f64;
            stage.reset_base_v = state.reset_base_v
                + (b.reset_base_v - state.reset_base_v) * i as f64 / stages as f64;
        }
        root = solve(root.x, Some(state), p, c, h, f, stage, budget, &mut work)?;
    }
    publish(state, root, p, f, b, work, true)
}
