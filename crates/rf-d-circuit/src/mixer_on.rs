//! Conditional ON panel network, SVC-9 Fig. 9-17 p.19 and Fig.9-11 p.13.
//! Omitted branches are outside the subgraph; they do not model OFF contacts.
//! Alpha is electrical resistance fraction, not a measured knob taper.

pub const SOURCE_NAMES: [&str; 5] = ["OSC1", "OSC2", "OSC3", "NOISE", "EXT"];
const POT_OHM: f64 = 25_000.0;
const SERIES_OHM: [f64; 5] = [33_000.0, 33_000.0, 33_000.0, 11_000.0, 33_000.0];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    InvalidInput,
    FloatingBus,
    ArithmeticDomain,
}

#[derive(Clone, Copy, Debug)]
pub struct OnMixer {
    included: [bool; 5],
    alpha: [f64; 4],
    denominator_ohm: [f64; 5],
    admittance_s: [[f64; 6]; 6],
}

#[derive(Clone, Copy, Debug)]
pub struct PortResponse {
    /// Positive entering the network, source ports first and BUS last.
    pub current_a: [f64; 6],
    /// Sum of physical resistor dissipation, not an audio normalization.
    pub dissipated_power_w: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct ImposedCurrentResponse {
    pub bus_v: f64,
    pub port: PortResponse,
    pub kcl_residual_a: f64,
    pub d_bus_d_source: [f64; 5],
    pub d_bus_d_board_current_ohm: f64,
    pub d_source_current_d_source_s: [[f64; 5]; 5],
    pub d_source_current_d_board_current: [f64; 5],
}

impl OnMixer {
    pub fn new(included_on: [bool; 5], alpha: [f64; 4]) -> Result<Self, Error> {
        if alpha
            .iter()
            .any(|a| !a.is_finite() || !(0.0..=1.0).contains(a))
        {
            return Err(Error::InvalidInput);
        }
        let mut y = [[0.0; 6]; 6];
        let mut denominator = SERIES_OHM;
        for i in 0..5 {
            if !included_on[i] {
                continue;
            }
            let a = if i < 4 { alpha[i] } else { 1.0 };
            let d = if i < 4 {
                SERIES_OHM[i] + POT_OHM * a * (1.0 - a)
            } else {
                SERIES_OHM[i]
            };
            denominator[i] = d;
            let g = 1.0 / d;
            y[i][i] = a * a * g + if i < 4 { 1.0 / POT_OHM } else { 0.0 };
            y[i][5] = -a * g;
            y[5][i] = y[i][5];
            y[5][5] += g;
        }
        Ok(Self {
            included: included_on,
            alpha,
            denominator_ohm: denominator,
            admittance_s: y,
        })
    }

    /// Current stamp / Jacobian in OSC1, OSC2, OSC3, NOISE, EXT, BUS order.
    pub fn admittance_s(&self) -> [[f64; 6]; 6] {
        self.admittance_s
    }

    /// Evaluate with all terminal voltages imposed; no state is published.
    pub fn evaluate(&self, terminal_v: [f64; 6]) -> Result<PortResponse, Error> {
        if terminal_v.iter().any(|v| !v.is_finite()) {
            return Err(Error::InvalidInput);
        }
        let mut current = [0.0; 6];
        let mut power = 0.0;
        for i in 0..5 {
            if !self.included[i] {
                continue;
            }
            current[i] =
                self.admittance_s[i][i] * terminal_v[i] + self.admittance_s[i][5] * terminal_v[5];
            current[5] +=
                self.admittance_s[5][i] * terminal_v[i] + terminal_v[5] / self.denominator_ohm[i];
            let a = if i < 4 { self.alpha[i] } else { 1.0 };
            let drop = terminal_v[5] - a * terminal_v[i];
            power += drop * drop / self.denominator_ohm[i];
            if i < 4 {
                power += terminal_v[i] * terminal_v[i] / POT_OHM;
            }
        }
        if current.iter().any(|i| !i.is_finite()) || !power.is_finite() {
            return Err(Error::ArithmeticDomain);
        }
        Ok(PortResponse {
            current_a: current,
            dissipated_power_w: power,
        })
    }

    /// Board current is imposed, positive leaving BUS toward board 4.
    /// The C27/filter constitutive law is not solved by this operation.
    pub fn solve_imposed_current(
        &self,
        source_v: [f64; 5],
        board_current_a: f64,
    ) -> Result<ImposedCurrentResponse, Error> {
        if source_v.iter().any(|v| !v.is_finite()) || !board_current_a.is_finite() {
            return Err(Error::InvalidInput);
        }
        let g = self.admittance_s[5][5];
        if g == 0.0 {
            return Err(Error::FloatingBus);
        }
        let mut drive = -board_current_a;
        let mut weights = [0.0; 5];
        for i in 0..5 {
            drive -= self.admittance_s[5][i] * source_v[i];
            weights[i] = -self.admittance_s[5][i] / g;
        }
        let bus = drive / g;
        if !bus.is_finite() {
            return Err(Error::ArithmeticDomain);
        }
        let port = self.evaluate([
            source_v[0],
            source_v[1],
            source_v[2],
            source_v[3],
            source_v[4],
            bus,
        ])?;
        let mut reduced = [[0.0; 5]; 5];
        for i in 0..5 {
            for j in 0..5 {
                reduced[i][j] = if i == j { self.admittance_s[i][i] } else { 0.0 }
                    + self.admittance_s[i][5] * weights[j];
            }
        }
        Ok(ImposedCurrentResponse {
            bus_v: bus,
            kcl_residual_a: port.current_a[5] + board_current_a,
            port,
            d_bus_d_source: weights,
            d_bus_d_board_current_ohm: -1.0 / g,
            d_source_current_d_source_s: reduced,
            d_source_current_d_board_current: weights,
        })
    }
}
