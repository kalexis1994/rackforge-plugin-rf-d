//! Isolated Model D board-3 headphone circuit 11, implicit Euler.
//!
//! Connectivity: SVC-9 Fig. 9-8, PDF p. 10. BJT and diode parameters are
//! imposed laboratory values, not measurements of a vintage unit.
//! The processing path uses fixed stack arrays and has no I/O or allocation.

pub mod circuit66;
pub mod circuit71;
pub mod cutoff;
pub mod cutoff_ladder_output;
pub mod ladder_recovery_output;
pub mod loudness_follower;
pub mod output;
pub mod output_conversion;
pub mod output_conversion_c4;
pub mod mixer_on;
pub mod mixer_c27;
pub mod panel;
pub mod recovery_vca_output;
pub mod vca1_output;
pub mod vca2_output;

const N: usize = 12;
const J7: usize = 11;
const C19: f64 = 2.5e-6;
const C15: f64 = 220e-12;
const C21: f64 = 400e-6;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;
const KCL_TOLERANCE_A: f64 = 1e-10;
const MAX_ITERATIONS: usize = 16;
const MAX_HALVINGS: usize = 16;

/// Node order matches `evidence/headphone_board3_port_vectors.json`.
pub const NODE_NAMES: [&str; N] = [
    "Q16_BASE",
    "Q16_EMITTER_DIODE_TOP",
    "DIODE_MIDDLE",
    "DIODE_BOTTOM",
    "Q11_BASE",
    "Q11_COLLECTOR",
    "Q11_EMITTER",
    "Q10_BASE",
    "Q10_COLLECTOR",
    "Q10_EMITTER",
    "AMP_OUTPUT_BEFORE_C21",
    "J7_TIP_RING",
];

#[derive(Clone, Copy, Debug)]
pub struct Parameters {
    pub transistor_is_a: f64,
    pub beta_forward: f64,
    pub beta_reverse: f64,
    pub temperature_k: f64,
    pub diode_is_a: f64,
    pub diode_ideality: f64,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub node_v: [f64; N],
    /// C19 pin7-to-Q16 base, C15 Q10 base-to-collector, C21 pre-out-to-J7.
    pub capacitor_v: [f64; 3],
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StepError {
    InvalidInput,
    ExponentialDomain,
    SingularJacobian,
    NoDecrease,
    IterationBudget,
}

#[derive(Clone, Copy, Debug)]
pub struct StepDiagnostics {
    pub iterations: usize,
    pub max_kcl_residual_a: f64,
    pub line_search_halvings: usize,
}

/// Dynamic C19 input port at board-3 pin 7. Current is positive into C19
/// from the upstream R21 wiper; conductance is its local derivative with
/// respect to pin-7 voltage while the previous capacitor state is held fixed.
#[derive(Clone, Copy, Debug)]
pub struct InputPortResponse {
    pub next_state: State,
    pub diagnostics: StepDiagnostics,
    pub current_a: f64,
    pub conductance_s: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct SolverBudget {
    pub iterations: usize,
    pub line_search_halvings: usize,
}

impl Default for SolverBudget {
    fn default() -> Self {
        Self {
            iterations: 16,
            line_search_halvings: 16,
        }
    }
}

fn finite_positive(value: f64) -> bool {
    value.is_finite() && value > 0.0
}

fn validate(
    state: &State,
    p: Parameters,
    pin7_v: f64,
    dt_s: f64,
    tip_load_ohm: Option<f64>,
    ring_load_ohm: Option<f64>,
    budget: SolverBudget,
) -> Result<f64, StepError> {
    if !pin7_v.is_finite()
        || !finite_positive(dt_s)
        || budget.iterations == 0
        || budget.line_search_halvings == 0
        || budget.iterations > MAX_ITERATIONS
        || budget.line_search_halvings > MAX_HALVINGS
        || state
            .node_v
            .iter()
            .chain(state.capacitor_v.iter())
            .any(|v| !v.is_finite())
        || !finite_positive(p.transistor_is_a)
        || !finite_positive(p.beta_forward)
        || !finite_positive(p.beta_reverse)
        || !finite_positive(p.temperature_k)
        || !finite_positive(p.diode_is_a)
        || !finite_positive(p.diode_ideality)
        || tip_load_ohm.is_some_and(|v| !finite_positive(v))
        || ring_load_ohm.is_some_and(|v| !finite_positive(v))
    {
        return Err(StepError::InvalidInput);
    }
    let mut g = 1.0 / 390.0; // R56 at jack
    if let Some(r) = tip_load_ohm {
        g += 1.0 / r;
    }
    if let Some(r) = ring_load_ohm {
        g += 1.0 / r;
    }
    if !g.is_finite() {
        return Err(StepError::InvalidInput);
    }
    Ok(g)
}

#[derive(Clone, Copy)]
struct Boundary {
    pin7_v: f64,
    dt_s: f64,
    load_g: f64,
    previous_cap_v: [f64; 3],
    p: Parameters,
}

// Explicit terminals keep the schematic stamp auditable against Fig. 9-8.
#[allow(clippy::too_many_arguments)]
fn resistor(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    a: Option<usize>,
    b: Option<usize>,
    fixed_a: f64,
    fixed_b: f64,
    ohm: f64,
) {
    let g = 1.0 / ohm;
    let va = a.map_or(fixed_a, |i| x[i]);
    let vb = b.map_or(fixed_b, |i| x[i]);
    let current = (va - vb) * g;
    if let Some(i) = a {
        r[i] += current;
        j[i][i] += g;
    }
    if let Some(i) = b {
        r[i] -= current;
        j[i][i] += g;
    }
    if let (Some(i), Some(k)) = (a, b) {
        j[i][k] -= g;
        j[k][i] -= g;
    }
}

#[allow(clippy::too_many_arguments)]
fn transistor(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    b: usize,
    c: Option<usize>,
    e: usize,
    fixed_collector: f64,
    polarity: f64,
    p: Parameters,
    vt: f64,
) -> Result<(), StepError> {
    let vc = c.map_or(fixed_collector, |i| x[i]);
    let xbe = polarity * (x[b] - x[e]) / vt;
    let xbc = polarity * (x[b] - vc) / vt;
    if !xbe.is_finite() || !xbc.is_finite() || xbe.max(xbc) > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    let f = p.transistor_is_a * xbe.exp_m1();
    let rev = p.transistor_is_a * xbc.exp_m1();
    let ib = f / p.beta_forward + rev / p.beta_reverse;
    let ic = f - (1.0 + 1.0 / p.beta_reverse) * rev;
    r[b] += polarity * ib;
    if let Some(ci) = c {
        r[ci] += polarity * ic;
    }
    r[e] -= polarity * (ib + ic);
    let gf = p.transistor_is_a * xbe.exp() / vt;
    let gr = p.transistor_is_a * xbc.exp() / vt;
    let columns = [Some(b), c, Some(e)];
    let rows = [Some(b), c, Some(e)];
    let slopes = [
        [
            gf / p.beta_forward + gr / p.beta_reverse,
            -gr / p.beta_reverse,
            -gf / p.beta_forward,
        ],
        [
            gf - (1.0 + 1.0 / p.beta_reverse) * gr,
            (1.0 + 1.0 / p.beta_reverse) * gr,
            -gf,
        ],
        [
            -(1.0 + 1.0 / p.beta_forward) * gf + gr,
            -gr,
            (1.0 + 1.0 / p.beta_forward) * gf,
        ],
    ];
    for (row, derivatives) in rows.into_iter().zip(slopes) {
        if let Some(i) = row {
            for (column, slope) in columns.into_iter().zip(derivatives) {
                if let Some(k) = column {
                    j[i][k] += slope;
                }
            }
        }
    }
    Ok(())
}

fn diode(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    anode: usize,
    cathode: usize,
    p: Parameters,
    vt: f64,
) -> Result<(), StepError> {
    let exponent = (x[anode] - x[cathode]) / (p.diode_ideality * vt);
    if !exponent.is_finite() || exponent > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    let current = p.diode_is_a * exponent.exp_m1();
    let g = p.diode_is_a * exponent.exp() / (p.diode_ideality * vt);
    r[anode] += current;
    r[cathode] -= current;
    j[anode][anode] += g;
    j[cathode][cathode] += g;
    j[anode][cathode] -= g;
    j[cathode][anode] -= g;
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn capacitor(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    left: Option<usize>,
    right: usize,
    fixed_left: f64,
    old_v: f64,
    farad: f64,
    dt_s: f64,
) {
    let g = farad / dt_s;
    let vl = left.map_or(fixed_left, |i| x[i]);
    let current = g * (vl - x[right] - old_v);
    if let Some(i) = left {
        r[i] += current;
        j[i][i] += g;
        j[i][right] -= g;
        j[right][i] -= g;
    }
    r[right] -= current;
    j[right][right] += g;
}

fn evaluate(x: &[f64; N], boundary: Boundary) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let mut r = [0.0; N];
    let mut j = [[0.0; N]; N];
    let vt = K_B * boundary.p.temperature_k / Q_E;
    let p = boundary.p;
    // SVC-9 Fig. 9-8, circuit 11. Rails are ideal -10, -20 and 0 V.
    resistor(x, &mut r, &mut j, Some(0), None, 0.0, -10.0, 6200.0); // R50
    resistor(x, &mut r, &mut j, Some(0), None, 0.0, 0.0, 24000.0); // R53
    resistor(x, &mut r, &mut j, Some(1), Some(4), 0.0, 0.0, 390.0); // R36
    resistor(x, &mut r, &mut j, None, Some(5), -20.0, 0.0, 10.0); // R44
    resistor(x, &mut r, &mut j, Some(6), Some(10), 0.0, 0.0, 4.7); // R33
    resistor(x, &mut r, &mut j, Some(10), Some(9), 0.0, 0.0, 4.7); // R32
    resistor(x, &mut r, &mut j, Some(3), Some(7), 0.0, 0.0, 390.0); // R35
    resistor(x, &mut r, &mut j, Some(3), None, 0.0, 0.0, 1200.0); // R49
    resistor(x, &mut r, &mut j, Some(8), None, 0.0, 0.0, 10.0); // R40
    transistor(x, &mut r, &mut j, 0, None, 1, -20.0, -1.0, p, vt)?; // Q16
    transistor(x, &mut r, &mut j, 4, Some(5), 6, 0.0, -1.0, p, vt)?; // Q11
    transistor(x, &mut r, &mut j, 7, Some(8), 9, 0.0, 1.0, p, vt)?; // Q10
    diode(x, &mut r, &mut j, 2, 1, p, vt)?; // CR2
    diode(x, &mut r, &mut j, 3, 2, p, vt)?; // CR1
    r[J7] += boundary.load_g * x[J7];
    j[J7][J7] += boundary.load_g;
    capacitor(
        x,
        &mut r,
        &mut j,
        None,
        0,
        boundary.pin7_v,
        boundary.previous_cap_v[0],
        C19,
        boundary.dt_s,
    );
    capacitor(
        x,
        &mut r,
        &mut j,
        Some(7),
        8,
        0.0,
        boundary.previous_cap_v[1],
        C15,
        boundary.dt_s,
    );
    capacitor(
        x,
        &mut r,
        &mut j,
        Some(10),
        J7,
        0.0,
        boundary.previous_cap_v[2],
        C21,
        boundary.dt_s,
    );
    if r.iter().any(|v| !v.is_finite()) || j.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

fn max_abs(values: &[f64; N]) -> f64 {
    values.iter().fold(0.0_f64, |acc, v| acc.max(v.abs()))
}

fn solve(mut j: [[f64; N]; N], mut rhs: [f64; N]) -> Result<[f64; N], StepError> {
    let mut scales = [0.0; N];
    for i in 0..N {
        scales[i] = max_abs(&j[i]);
        if scales[i] == 0.0 {
            return Err(StepError::SingularJacobian);
        }
    }
    for col in 0..N {
        let mut pivot = col;
        let mut best = 0.0;
        for i in col..N {
            let scaled = j[i][col].abs() / scales[i];
            if scaled > best {
                best = scaled;
                pivot = i;
            }
        }
        if best < 1e-12 {
            return Err(StepError::SingularJacobian);
        }
        j.swap(col, pivot);
        rhs.swap(col, pivot);
        scales.swap(col, pivot);
        let diagonal = j[col][col];
        for i in (col + 1)..N {
            let factor = j[i][col] / diagonal;
            j[i][col] = 0.0;
            #[allow(clippy::needless_range_loop)]
            for k in (col + 1)..N {
                j[i][k] -= factor * j[col][k];
            }
            rhs[i] -= factor * rhs[col];
        }
    }
    let mut result = [0.0; N];
    for i in (0..N).rev() {
        let mut value = rhs[i];
        for k in (i + 1)..N {
            value -= j[i][k] * result[k];
        }
        result[i] = value / j[i][i];
    }
    if result.iter().any(|v| !v.is_finite()) {
        return Err(StepError::SingularJacobian);
    }
    Ok(result)
}

/// Advance the isolated board-3 circuit. The caller must supply a DC-consistent
/// initial state, such as the frozen fixture. Failure leaves `state` untouched.
pub fn step(
    state: &mut State,
    p: Parameters,
    pin7_v: f64,
    dt_s: f64,
    tip_load_ohm: Option<f64>,
    ring_load_ohm: Option<f64>,
    budget: SolverBudget,
) -> Result<StepDiagnostics, StepError> {
    let load_g = validate(state, p, pin7_v, dt_s, tip_load_ohm, ring_load_ohm, budget)?;
    let boundary = Boundary {
        pin7_v,
        dt_s,
        load_g,
        previous_cap_v: state.capacitor_v,
        p,
    };
    let mut x = state.node_v;
    let mut halvings = 0;
    for iteration in 0..budget.iterations {
        let (residual, jacobian) = evaluate(&x, boundary)?;
        let error = max_abs(&residual);
        if error < KCL_TOLERANCE_A {
            state.node_v = x;
            state.capacitor_v = [pin7_v - x[0], x[7] - x[8], x[10] - x[J7]];
            return Ok(StepDiagnostics {
                iterations: iteration,
                max_kcl_residual_a: error,
                line_search_halvings: halvings,
            });
        }
        let direction = solve(jacobian, residual.map(|v| -v))?;
        let mut accepted = false;
        for power in 0..budget.line_search_halvings {
            let scale = 0.5_f64.powi(power as i32);
            let trial = std::array::from_fn(|i| x[i] + scale * direction[i]);
            if let Ok((candidate, _)) = evaluate(&trial, boundary) {
                if max_abs(&candidate) < error {
                    x = trial;
                    halvings += power;
                    accepted = true;
                    break;
                }
            }
        }
        if !accepted {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}

/// Solve board 3 as a dynamic input port for a simultaneous upstream solver.
/// The returned state is provisional: an outer Newton iteration must retain
/// the same `previous_state` for every trial and commit only its final result.
pub fn solve_input_port(
    previous_state: &State,
    p: Parameters,
    pin7_v: f64,
    dt_s: f64,
    tip_load_ohm: Option<f64>,
    ring_load_ohm: Option<f64>,
    budget: SolverBudget,
) -> Result<InputPortResponse, StepError> {
    let mut next_state = *previous_state;
    let diagnostics = step(
        &mut next_state,
        p,
        pin7_v,
        dt_s,
        tip_load_ohm,
        ring_load_ohm,
        budget,
    )?;
    let load_g = validate(
        previous_state,
        p,
        pin7_v,
        dt_s,
        tip_load_ohm,
        ring_load_ohm,
        budget,
    )?;
    let boundary = Boundary {
        pin7_v,
        dt_s,
        load_g,
        previous_cap_v: previous_state.capacitor_v,
        p,
    };
    let (_, jacobian) = evaluate(&next_state.node_v, boundary)?;
    let g = C19 / dt_s;
    let mut rhs = [0.0; N];
    rhs[0] = g;
    let response = solve(jacobian, rhs)?;
    let current_a = g * (next_state.capacitor_v[0] - previous_state.capacitor_v[0]);
    let conductance_s = g * (1.0 - response[0]);
    if !current_a.is_finite() || !conductance_s.is_finite() {
        return Err(StepError::ExponentialDomain);
    }
    Ok(InputPortResponse {
        next_state,
        diagnostics,
        current_a,
        conductance_s,
    })
}

/// Solve the conditional DC operating point with pin 7 at zero and J7
/// connected to its 390-ohm shunt. Capacitors are open at DC and receive the
/// voltage difference of their terminals. This is not a vintage calibration.
pub fn initial_state(p: Parameters) -> Result<State, StepError> {
    // The eleven-node seed is documented in the Python DC reference. Its
    // numerical value is only a solver starting point, never an audio constant.
    let mut state = State {
        node_v: [
            -8.0, -7.3, -6.7, -6.1, -7.4, -19.9, -6.7, -6.1, -0.1, -6.8, -6.7, 0.0,
        ],
        capacitor_v: [0.0; 3],
    };
    let budget = SolverBudget::default();
    let load_g = validate(&state, p, 0.0, 1.0, None, None, budget)?;
    // Infinite step opens all capacitors. This is an internal DC stamp; the
    // public transient step requires a finite positive time interval.
    let dc = Boundary {
        pin7_v: 0.0,
        dt_s: f64::INFINITY,
        load_g,
        previous_cap_v: [0.0; 3],
        p,
    };
    let mut x = state.node_v;
    for _ in 0..budget.iterations {
        let (residual, jacobian) = evaluate(&x, dc)?;
        let error = max_abs(&residual);
        if error < 1e-11 {
            state.node_v = x;
            state.capacitor_v = [-x[0], x[7] - x[8], x[10] - x[J7]];
            return Ok(state);
        }
        let direction = solve(jacobian, residual.map(|v| -v))?;
        let mut accepted = false;
        for power in 0..budget.line_search_halvings {
            let scale = 0.5_f64.powi(power as i32);
            let trial = std::array::from_fn(|i| x[i] + scale * direction[i]);
            if let Ok((candidate, _)) = evaluate(&trial, dc) {
                if max_abs(&candidate) < error {
                    x = trial;
                    accepted = true;
                    break;
                }
            }
        }
        if !accepted {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}

pub mod mixer_chain66;

pub mod mixer_chain_port;

pub mod mixer_chain66_direct;
pub mod mixer_chain_port_direct;

pub mod junction_charge;

pub mod vco_bjt;

pub mod vco_jfet;

pub mod lm741;
