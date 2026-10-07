//! ON mixer / C27 reduction, SVC-9 Fig.9-17 p.19, Fig.9-11 p.13.
//! Conditional ideal 10 uF capacitor. Old BASE-minus-BUS voltage stays fixed.
//! This port supplies a ladder stamp; it does not solve the ladder.

use crate::mixer_on::{Error, OnMixer};

const C27_F: f64 = 10e-6;

#[derive(Clone, Copy, Debug)]
pub struct C27OnPort {
    mixer: OnMixer,
    bus_conductance_s: f64,
    weights: [f64; 5],
}

#[derive(Clone, Copy, Debug)]
pub struct Response {
    pub bus_v: f64,
    /// Positive entering network; OSC1, OSC2, OSC3, NOISE, EXT, BASE_Q29.
    pub current_a: [f64; 6],
    pub jacobian_s: [[f64; 6]; 6],
    /// Provisional charge history, BASE minus BUS; caller owns acceptance.
    pub next_capacitor_v: f64,
    /// Computed before adding old voltage, for charge-balance diagnostics.
    pub capacitor_delta_v: f64,
    pub bus_kcl_residual_a: f64,
    pub mixer_dissipated_power_w: f64,
}

impl C27OnPort {
    pub fn new(mixer: OnMixer) -> Result<Self, Error> {
        let open = mixer.solve_imposed_current([0.0; 5], 0.0)?;
        Ok(Self {
            bus_conductance_s: mixer.admittance_s()[5][5],
            weights: open.d_bus_d_source,
            mixer,
        })
    }

    pub fn evaluate(
        &self,
        source_v: [f64; 5],
        base_v: f64,
        previous_capacitor_v: f64,
        dt_s: f64,
    ) -> Result<Response, Error> {
        if source_v.iter().any(|v| !v.is_finite())
            || !base_v.is_finite()
            || !previous_capacitor_v.is_finite()
            || !dt_s.is_finite()
            || dt_s <= 0.0
        {
            return Err(Error::InvalidInput);
        }
        let gc = C27_F / dt_s;
        if !gc.is_finite() || gc <= 0.0 {
            return Err(Error::ArithmeticDomain);
        }
        let g = self.bus_conductance_s;
        let (m, c) = if g <= gc {
            let ratio = g / gc;
            (ratio / (1.0 + ratio), 1.0 / (1.0 + ratio))
        } else {
            let ratio = gc / g;
            (1.0 / (1.0 + ratio), ratio / (1.0 + ratio))
        };
        let open = self.mixer.solve_imposed_current(source_v, 0.0)?.bus_v;
        let drop = base_v - previous_capacitor_v - open;
        let delta = m * drop;
        let bus = open + c * drop;
        let next = previous_capacitor_v + delta;
        if !drop.is_finite() || !bus.is_finite() || !next.is_finite() {
            return Err(Error::ArithmeticDomain);
        }
        let port = self.mixer.evaluate([
            source_v[0], source_v[1], source_v[2], source_v[3], source_v[4], bus,
        ])?;
        let k = g * c;
        let base_current = k * drop;
        let mut currents = port.current_a;
        currents[5] = base_current;
        let y = self.mixer.admittance_s();
        let mut j = [[0.0; 6]; 6];
        for i in 0..5 {
            for column in 0..5 {
                j[i][column] = y[i][column] + y[i][5] * m * self.weights[column];
            }
            j[i][5] = y[i][5] * c;
            j[5][i] = -k * self.weights[i];
        }
        j[5][5] = k;
        if !base_current.is_finite() {
            return Err(Error::ArithmeticDomain);
        }
        Ok(Response {
            bus_v: bus,
            current_a: currents,
            jacobian_s: j,
            next_capacitor_v: next,
            capacitor_delta_v: delta,
            bus_kcl_residual_a: port.current_a[5] - base_current,
            mixer_dissipated_power_w: port.dissipated_power_w,
        })
    }
}
